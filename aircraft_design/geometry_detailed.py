from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from math import acos, cos, pi, sin, sqrt


@dataclass(frozen=True)
class AirfoilSpec:
    type: str
    code: str
    n: int = 161


@dataclass
class DetailedWing:
    area: float
    span: float
    aspect_ratio: float
    taper_ratio: float
    sweep_qc: float
    thickness_to_chord_root: float
    dihedral: float = 0.0
    incidence: float = 0.0
    twist: float = 0.0
    x_le_root: float = 0.0
    y_root: float = 0.0
    z_root: float = 0.0
    airfoil_root: str = "naca2412"
    airfoil_tip: str = "naca0012"


@dataclass
class FuselageStation:
    x_m: float
    radius_m: float


@dataclass
class DetailedFuselage:
    length: float
    diameter: float
    stations: list[FuselageStation] = field(default_factory=list)
    control_points: list[dict] = field(default_factory=list) # x_rel, radius_rel

@dataclass
class DetailedTail:
    area_ratio_to_wing: float = 0.0
    ht_area: float = 0.0
    vt_area: float = 0.0
    ht_aspect_ratio: float = 4.0
    vt_aspect_ratio: float = 1.5
    # Additional tail parameters
    ht_taper: float = 0.5
    ht_sweep: float = 20.0
    vt_taper: float = 0.6
    vt_sweep: float = 30.0

@dataclass
class ParametricGeometry:
    wing: DetailedWing
    fuselage: DetailedFuselage
    tail: DetailedTail
    
    def generate_mesh(self) -> dict:
        """
        Generates mesh data (vertices and faces) for the geometry.
        Returns a dictionary suitable for 3D visualization.
        """
        mesh_data = {
            "fuselage": self._mesh_fuselage(),
            "wing": self._mesh_wing(),
            "htail": self._mesh_htail(),
            "vtail": self._mesh_vtail()
        }
        return mesh_data
        
    def _mesh_fuselage(self, n_radial: int = 16, n_axial: int = 20) -> dict:
        L = self.fuselage.length
        D = self.fuselage.diameter
        stations = self.fuselage.stations
        
        # Generate stations from control points if stations are empty but control points exist
        if not stations and self.fuselage.control_points:
             # Basic linear interpolation for now
             # Sort control points by x_rel
             cps = sorted(self.fuselage.control_points, key=lambda p: p['x_rel'])
             xs_rel = [p['x_rel'] for p in cps]
             rs_rel = [p['radius_rel'] for p in cps]
             
             import numpy as np
             x_eval = np.linspace(0, 1, n_axial)
             r_eval = np.interp(x_eval, xs_rel, rs_rel)
             
             stations = [FuselageStation(x_m=x * L, radius_m=r * D / 2.0) for x, r in zip(x_eval, r_eval)]
        
        # If still no stations, use default cigar shape
        if not stations:
             import numpy as np
             x_eval = np.linspace(0, 1, n_axial)
             # Cigar shape: r = R * sin(acos(abs(2x-1))) -> r = R * sqrt(1 - (2x-1)^2)
             r_eval = (D / 2.0) * np.sqrt(1 - (2 * x_eval - 1)**2)
             stations = [FuselageStation(x_m=x * L, radius_m=r) for x, r in zip(x_eval, r_eval)]

        vertices = []
        faces = []
        
        for i, st in enumerate(stations):
            x = st.x_m
            r = st.radius_m
            for j in range(n_radial):
                theta = 2 * pi * j / n_radial
                y = r * cos(theta)
                z = r * sin(theta)
                vertices.append([x, y, z])
                
        # Generate faces (quads split into triangles)
        n_stations = len(stations)
        for i in range(n_stations - 1):
            for j in range(n_radial):
                p1 = i * n_radial + j
                p2 = i * n_radial + (j + 1) % n_radial
                p3 = (i + 1) * n_radial + (j + 1) % n_radial
                p4 = (i + 1) * n_radial + j
                
                # Triangle 1
                faces.append([p1, p2, p3])
                # Triangle 2
                faces.append([p1, p3, p4])
                
        return {"vertices": vertices, "faces": faces, "color": "#E0E0E0"}

    def _mesh_wing(self) -> dict:
        return self._mesh_lifting_surface(
            area=self.wing.area,
            ar=self.wing.aspect_ratio,
            taper=self.wing.taper_ratio,
            sweep=self.wing.sweep_qc,
            x_offset=self.fuselage.length * 0.4,
            z_offset=0.0,
            dihedral=self.wing.dihedral,
            color="#42A5F5"
        )
        
    def _mesh_htail(self) -> dict:
        # Estimate tail arm and area
        if self.tail.ht_area > 0:
            s_ht = self.tail.ht_area
        else:
            # S_ht ~ 0.2 S_w (if only ratio provided, we assume ~75% of total tail area ratio is HT)
            s_ht = self.wing.area * self.tail.area_ratio_to_wing * 0.75
            
        x_ht = self.fuselage.length * 0.90
        
        return self._mesh_lifting_surface(
            area=s_ht,
            ar=self.tail.ht_aspect_ratio,
            taper=self.tail.ht_taper,
            sweep=self.tail.ht_sweep,
            x_offset=x_ht, # LE approx
            z_offset=0.5, # T-tail or conventional
            dihedral=0.0,
            color="#FFCA28"
        )

    def _mesh_vtail(self) -> dict:
        if self.tail.vt_area > 0:
            s_vt = self.tail.vt_area
        else:
            s_vt = self.wing.area * self.tail.area_ratio_to_wing * 0.25
            
        x_vt = self.fuselage.length * 0.85
        
        # Vertical tail is symmetric but mounted vertically. 
        # We can reuse lifting surface logic but need rotation.
        # Simplified: Generate flat plate in XZ
        
        b = sqrt(s_vt * self.tail.vt_aspect_ratio)
        c_root = 2 * s_vt / (b * (1 + self.tail.vt_taper))
        c_tip = c_root * self.tail.vt_taper
        
        import numpy as np
        sweep_rad = np.radians(self.tail.vt_sweep)
        dx_tip = b * np.tan(sweep_rad)
        
        # Vertices (1 side)
        # Root LE, Root TE, Tip TE, Tip LE
        v = [
            [x_vt, 0, 0],
            [x_vt + c_root, 0, 0],
            [x_vt + dx_tip + c_tip, 0, b],
            [x_vt + dx_tip, 0, b]
        ]
        
        # Double side for thickness visual
        width = 0.05
        vertices = []
        for p in v:
            vertices.append([p[0], width, p[2]])
        for p in v:
            vertices.append([p[0], -width, p[2]])
            
        # Simple box faces
        faces = [
            [0, 1, 2], [0, 2, 3], # Right
            [4, 7, 6], [4, 6, 5], # Left
            [0, 3, 7], [0, 7, 4], # Leading Edge
            [1, 5, 6], [1, 6, 2], # Trailing Edge
            [3, 2, 6], [3, 6, 7], # Tip
        ]
        
        return {"vertices": vertices, "faces": faces, "color": "#EF5350"}

    def _mesh_lifting_surface(self, area, ar, taper, sweep, x_offset, z_offset, dihedral, color) -> dict:
        import numpy as np
        b = sqrt(area * ar)
        c_root = 2 * area / (b * (1 + taper))
        c_tip = c_root * taper
        
        sweep_rad = np.radians(sweep)
        dihedral_rad = np.radians(dihedral)
        
        dx_tip = (b/2) * np.tan(sweep_rad)
        dy_tip = (b/2) * cos(dihedral_rad)
        dz_tip = (b/2) * sin(dihedral_rad)
        
        # Generate airfoil sections (simplified as flat hexagonal or diamond for now, or just thick plate)
        # To look "perfected", we should use NACA coordinates, but for 3D view speed, a thick plate is better.
        # Let's use a simple diamond airfoil shape.
        
        def section_coords(c, x_le, y, z):
            # 5 points: LE, Top, TE, Bottom, LE (loop)
            # Thickness 12%
            tc = 0.12
            h = c * tc * 0.5
            return [
                [x_le, y, z],
                [x_le + c*0.3, y, z + h], # Max thickness at 30%
                [x_le + c, y, z],
                [x_le + c*0.3, y, z - h]
            ]
            
        root_sect = section_coords(c_root, x_offset, 0, z_offset)
        
        # Right Tip
        right_tip_sect = section_coords(c_tip, x_offset + dx_tip, dy_tip, z_offset + dz_tip)
        
        # Left Tip
        left_tip_sect = section_coords(c_tip, x_offset + dx_tip, -dy_tip, z_offset + dz_tip)
        
        vertices = []
        faces = []
        
        # Add vertices
        # 0-3: Root
        vertices.extend(root_sect)
        # 4-7: Right Tip
        vertices.extend(right_tip_sect)
        # 8-11: Left Tip
        vertices.extend(left_tip_sect)
        
        # Faces (Root to Right Tip)
        # 4 quads -> 8 triangles
        # LE to Top
        faces.append([0, 4, 5]); faces.append([0, 5, 1])
        # Top to TE
        faces.append([1, 5, 6]); faces.append([1, 6, 2])
        # TE to Bottom
        faces.append([2, 6, 7]); faces.append([2, 7, 3])
        # Bottom to LE
        faces.append([3, 7, 4]); faces.append([3, 4, 0])
        
        # Faces (Root to Left Tip) - slightly tricky with ordering to keep normals out?
        # Just standard triangulation
        faces.append([0, 1, 9]); faces.append([0, 9, 8])
        faces.append([1, 2, 10]); faces.append([1, 10, 9])
        faces.append([2, 3, 11]); faces.append([2, 11, 10])
        faces.append([3, 0, 8]); faces.append([3, 8, 11])
        
        # Close tips? (Optional)
        
        return {"vertices": vertices, "faces": faces, "color": color}


def naca4_coordinates(*, code: str, n: int = 161, finite_te: bool = True) -> list[list[float]]:
    c = str(code).strip()
    if len(c) != 4 or not c.isdigit():
        raise ValueError("NACA 4-digit code must be 4 digits, e.g., '2412'.")
    m = int(c[0]) / 100.0
    p = int(c[1]) / 10.0
    t = int(c[2:]) / 100.0
    if n < 21:
        raise ValueError("n must be >= 21.")

    a0 = 0.2969
    a1 = -0.1260
    a2 = -0.3516
    a3 = 0.2843
    a4 = -0.1015 if finite_te else -0.1036

    xs = []
    for i in range(n):
        beta = pi * i / (n - 1)
        x = 0.5 * (1.0 - cos(beta))
        xs.append(x)

    def yc_dyc(x: float) -> tuple[float, float]:
        if p <= 0.0 or m <= 0.0:
            return 0.0, 0.0
        if x < p:
            yc = m / (p * p) * (2.0 * p * x - x * x)
            dyc = 2.0 * m / (p * p) * (p - x)
            return yc, dyc
        yc = m / ((1.0 - p) * (1.0 - p)) * ((1.0 - 2.0 * p) + 2.0 * p * x - x * x)
        dyc = 2.0 * m / ((1.0 - p) * (1.0 - p)) * (p - x)
        return yc, dyc

    upper = []
    lower = []
    for x in xs:
        yt = 5.0 * t * (a0 * sqrt(max(0.0, x)) + a1 * x + a2 * x * x + a3 * x * x * x + a4 * x * x * x * x)
        yc, dyc = yc_dyc(x)
        th = acos(1.0 / sqrt(1.0 + dyc * dyc))
        if dyc < 0:
            th = -th
        xu = x - yt * sin(th)
        yu = yc + yt * cos(th)
        xl = x + yt * sin(th)
        yl = yc - yt * cos(th)
        upper.append([xu, yu])
        lower.append([xl, yl])

    pts = [*upper[::-1], *lower[1:]]
    return pts


def estimate_wing_fuel_volume(
    area_m2: float,
    span_m: float,
    t_c_root: float,
    t_c_tip: float,
    taper: float,
    tank_fraction: float = 0.7 # Fraction of wing span/area available for fuel
) -> float:
    """
    Estimates available fuel volume in the wing.
    Volume ~ Area * Avg_Thickness * Tank_Fraction * Efficiency
    """
    if span_m <= 0: return 0.0
    
    t_c_avg = (t_c_root + t_c_tip) / 2.0
    cr = 2 * area_m2 / (span_m * (1 + taper))
    integral_c2 = span_m * (cr**2) * (1 + taper + taper**2) / 3.0
    volume_total = 0.68 * t_c_avg * integral_c2
    
    return volume_total * tank_fraction


def geometry_detailed_from_inputs(inputs: dict, sizing_result: Any = None) -> ParametricGeometry:
    """
    Extracts detailed geometry configuration from standard inputs dict.
    Returns a ParametricGeometry object.
    """
    req = inputs.get("requirements", {})
    guess = inputs.get("initial_guess", {})
    
    # Wing
    # Use sizing result if available, otherwise guess
    ar = guess.get("aspect_ratio", 7.0)
    taper = guess.get("taper_ratio", 0.4)
    sweep = guess.get("sweep_deg", 0.0)
    tc = guess.get("thickness_ratio", 0.12)
    dihedral = guess.get("dihedral_deg", 0.0)
    twist = guess.get("twist_deg", 0.0)
    airfoil_root = guess.get("airfoil_root", "naca2412")
    airfoil_tip = guess.get("airfoil_tip", "naca0012")
    
    s_ref = 20.0 # Default fallback
    if sizing_result:
        s_ref = sizing_result.wing_area_m2
    
    span = sqrt(ar * s_ref)
    
    wing = DetailedWing(
        area=s_ref,
        span=span,
        aspect_ratio=ar,
        taper_ratio=taper,
        sweep_qc=sweep,
        thickness_to_chord_root=tc,
        dihedral=dihedral,
        twist=twist,
        airfoil_root=airfoil_root,
        airfoil_tip=airfoil_tip
    )

    # Fuselage
    # Simple sizing rule if not provided: L ~ 0.8 * Span (Glider/Transport) or 1.0*Span (Fighter)
    # Let's use simple estimate: L = 1.0 * Span for fighter/UAV
    fus_len = span * 0.8 
    fus_dia = fus_len / 8.0 # Fineness ratio 8
    
    fuselage = DetailedFuselage(
        length=fus_len,
        diameter=fus_dia
    )
    
    # Tail
    # Area ratio: HT ~ 0.2 Wing, VT ~ 0.1 Wing => Total ~ 0.3
    tail = DetailedTail(
        area_ratio_to_wing=0.3
    )
    
    return ParametricGeometry(
        wing=wing,
        fuselage=fuselage,
        tail=tail
    )
