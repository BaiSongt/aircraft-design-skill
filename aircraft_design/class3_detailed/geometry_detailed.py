from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from math import cos, pi, sin, sqrt


from ..config.airfoil_library import generate_naca4_airfoil


def naca4_coordinates_wrapper(*, code: str | None = None, n: int = 100, num_points: int | None = None, **kwargs) -> Any:
    if num_points is not None:
        n = num_points

    if code is not None:
        # Parse code mode
        s_code = str(code).strip()
        if len(s_code) != 4 or not s_code.isdigit():
            s_code = "0012"
        m = int(s_code[0]) / 100.0
        p = int(s_code[1]) / 10.0
        t = int(s_code[2:]) / 100.0
        if p <= 0.0:
            p = 0.4

        return generate_naca4_airfoil(max_camber=m, max_camber_location=p, max_thickness=t, num_points=n)
    else:
        # Pass through mode
        if "num_points" not in kwargs:
            kwargs["num_points"] = n
        return generate_naca4_airfoil(**kwargs)


# Alias for compatibility if needed
naca4_coordinates = naca4_coordinates_wrapper


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

    @property
    def mean_aerodynamic_chord(self) -> float:
        t = self.taper_ratio
        c_root = 2 * self.area / (self.span * (1 + t))
        return (2 / 3) * c_root * (1 + t + t**2) / (1 + t)

    def wetted_area(self) -> float:
        # Estimate: S_wet = 2 * S_ref * (1 + 0.2 * t/c)
        return 2.0 * self.area * (1.0 + 0.2 * self.thickness_to_chord_root)


@dataclass
class FuselageStation:
    x_m: float
    radius_m: float


@dataclass
class DetailedFuselage:
    length: float
    diameter: float
    stations: list[FuselageStation] = field(default_factory=list)
    control_points: list[dict] = field(default_factory=list)  # x_rel, radius_rel

    def ensure_stations(self, n_axial: int = 20):
        """Generates stations from control points or default shape if stations are missing."""
        if self.stations:
            return

        L = self.length
        D = self.diameter

        # Generate stations from control points if stations are empty but control points exist
        if self.control_points:
            # Basic linear interpolation for now
            # Sort control points by x_rel
            cps = sorted(self.control_points, key=lambda p: p["x_rel"])
            xs_rel = [p["x_rel"] for p in cps]
            rs_rel = [p["radius_rel"] for p in cps]

            import numpy as np

            x_eval = np.linspace(0, 1, n_axial)
            r_eval = np.interp(x_eval, xs_rel, rs_rel)

            self.stations = [FuselageStation(x_m=x * L, radius_m=r * D / 2.0) for x, r in zip(x_eval, r_eval)]
            return

        # If still no stations, use default cigar shape
        import numpy as np

        x_eval = np.linspace(0, 1, n_axial)
        # Cigar shape: r = R * sin(acos(abs(2x-1))) -> r = R * sqrt(1 - (2x-1)^2)
        r_eval = (D / 2.0) * np.sqrt(1 - (2 * x_eval - 1) ** 2)
        self.stations = [FuselageStation(x_m=x * L, radius_m=r) for x, r in zip(x_eval, r_eval)]

    def wetted_area(self) -> float:
        self.ensure_stations()
        area = 0.0
        for i in range(len(self.stations) - 1):
            s1 = self.stations[i]
            s2 = self.stations[i + 1]
            dx = s2.x_m - s1.x_m
            r1 = s1.radius_m
            r2 = s2.radius_m
            area += pi * (r1 + r2) * sqrt(dx**2 + (r2 - r1) ** 2)
        return area


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
    ht_thickness_ratio: float = 0.12
    vt_thickness_ratio: float = 0.12
    ht_airfoil: str = "naca0012"
    vt_airfoil: str = "naca0012"
    ht_x_le: float | None = None
    vt_x_le: float | None = None
    ht_z_le: float | None = None
    vt_z_le: float | None = None

    @property
    def ht_mean_aerodynamic_chord(self) -> float:
        if self.ht_area <= 0:
            return 0.0
        b = sqrt(self.ht_area * self.ht_aspect_ratio)
        t = self.ht_taper
        c_root = 2 * self.ht_area / (b * (1 + t))
        return (2 / 3) * c_root * (1 + t + t**2) / (1 + t)

    @property
    def vt_mean_aerodynamic_chord(self) -> float:
        if self.vt_area <= 0:
            return 0.0
        b = sqrt(self.vt_area * self.vt_aspect_ratio)
        t = self.vt_taper
        c_root = 2 * self.vt_area / (b * (1 + t))
        return (2 / 3) * c_root * (1 + t + t**2) / (1 + t)

    def ht_wetted_area(self) -> float:
        return 2.0 * self.ht_area * (1.0 + 0.2 * self.ht_thickness_ratio)

    def vt_wetted_area(self) -> float:
        return 2.0 * self.vt_area * (1.0 + 0.2 * self.vt_thickness_ratio)


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
            "vtail": self._mesh_vtail(),
        }
        return mesh_data

    def _mesh_fuselage(self, n_radial: int = 16, n_axial: int = 20) -> dict:
        self.fuselage.ensure_stations(n_axial)
        stations = self.fuselage.stations

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
            color="#42A5F5",
            airfoil_root=self.wing.airfoil_root,
            airfoil_tip=self.wing.airfoil_tip,
        )

    def _mesh_htail(self) -> dict:
        # Estimate tail arm and area
        if self.tail.ht_area > 0:
            s_ht = self.tail.ht_area
        else:
            # S_ht ~ 0.2 S_w (if only ratio provided, we assume ~75% of total tail area ratio is HT)
            s_ht = self.wing.area * self.tail.area_ratio_to_wing * 0.75

        x_ht = self.tail.ht_x_le if self.tail.ht_x_le is not None else self.fuselage.length * 0.90
        z_ht = self.tail.ht_z_le if self.tail.ht_z_le is not None else 0.5

        return self._mesh_lifting_surface(
            area=s_ht,
            ar=self.tail.ht_aspect_ratio,
            taper=self.tail.ht_taper,
            sweep=self.tail.ht_sweep,
            x_offset=x_ht,  # LE approx
            z_offset=z_ht,  # T-tail or conventional
            dihedral=0.0,
            color="#FFCA28",
            airfoil_root=self.tail.ht_airfoil,
            airfoil_tip=self.tail.ht_airfoil,
        )

    def _mesh_vtail(self) -> dict:
        if self.tail.vt_area > 0:
            s_vt = self.tail.vt_area
        else:
            s_vt = self.wing.area * self.tail.area_ratio_to_wing * 0.25

        x_vt = self.tail.vt_x_le if self.tail.vt_x_le is not None else self.fuselage.length * 0.85
        z_vt = self.tail.vt_z_le if self.tail.vt_z_le is not None else 0.0

        # Generate as a right semi-span wing
        # To simulate a vertical tail of height b_vt and area S_vt using a "full wing" generator:
        # We need "Right Wing" dimensions to match VT.
        # "Right Wing" has span b_semi = b_gen / 2. We want b_semi = b_vt.
        # So b_gen = 2 * b_vt.
        # "Right Wing" has area S_semi = S_gen / 2. We want S_semi = S_vt.
        # So S_gen = 2 * S_vt.
        # We pass area = 2 * S_vt.
        # AR_gen = b_gen^2 / S_gen = (2*b_vt)^2 / (2*S_vt) = 4*b_vt^2 / 2*S_vt = 2 * (b_vt^2 / S_vt).
        # Standard AR definition for VT is AR_vt = b_vt^2 / S_vt.
        # So AR_gen = 2 * AR_vt.

        ar_gen = self.tail.vt_aspect_ratio * 2
        area_gen = s_vt * 2

        # Use _mesh_lifting_surface with symmetric=False
        # x_offset=0, z_offset=0 because we will rotate/translate manually
        mesh = self._mesh_lifting_surface(
            area=area_gen,
            ar=ar_gen,
            taper=self.tail.vt_taper,
            sweep=self.tail.vt_sweep,
            x_offset=0.0,
            z_offset=0.0,
            dihedral=0.0,
            color="#EF5350",
            airfoil_root=self.tail.vt_airfoil,
            airfoil_tip=self.tail.vt_airfoil,
            symmetric=False,
        )

        # Rotate vertices: +Y (Right) -> +Z (Up)
        # +Z (Thickness) -> -Y (Left/Right Thickness)
        # +X (Chord) -> +X

        vertices = mesh["vertices"]
        new_vertices = []
        for v in vertices:
            x, y, z = v
            new_x = x + x_vt
            new_y = -z  # Thickness becomes Y
            new_z = y + z_vt  # Span becomes Z
            new_vertices.append([new_x, new_y, new_z])

        mesh["vertices"] = new_vertices
        return mesh

    def _mesh_lifting_surface(
        self,
        area: float,
        ar: float,
        taper: float,
        sweep: float,
        x_offset: float,
        z_offset: float,
        dihedral: float,
        color: str,
        airfoil_root: str = "naca2412",
        airfoil_tip: str = "naca0012",
        twist: float = 0.0,
        incidence: float = 0.0,
        symmetric: bool = True,
    ) -> dict:
        import numpy as np

        b = sqrt(area * ar)
        c_root = 2 * area / (b * (1 + taper))
        c_tip = c_root * taper

        sweep_rad = np.radians(sweep)
        dihedral_rad = np.radians(dihedral)
        dx_tip = (b / 2) * np.tan(sweep_rad)
        dy_tip = (b / 2) * cos(dihedral_rad)
        dz_tip = (b / 2) * sin(dihedral_rad)

        def get_airfoil_coords(code: str) -> tuple[np.ndarray, np.ndarray]:
            try:
                # Extract 4 digits if string looks like "naca2412"
                digits = "".join(filter(str.isdigit, code))
                if len(digits) != 4:
                    digits = "0012"  # Fallback

                # Parse digits
                m = int(digits[0]) / 100.0
                p = int(digits[1]) / 10.0
                t = int(digits[2:]) / 100.0

                geom = generate_naca4_airfoil(
                    max_camber=m,
                    max_camber_location=p if p > 0 else 0.4,  # avoid 0.0 for p
                    max_thickness=t,
                    num_points=40,  # Reduced points for performance in 3D view
                )
                return geom.coordinates.x, geom.coordinates.y
            except Exception:
                # Fallback to 0012
                geom = generate_naca4_airfoil(max_thickness=0.12, num_points=40)
                return geom.coordinates.x, geom.coordinates.y

        x_root_norm, y_root_norm = get_airfoil_coords(airfoil_root)
        x_tip_norm, y_tip_norm = get_airfoil_coords(airfoil_tip)

        # Helper to transform section to global 3D
        def transform_section(x_norm, y_norm, c, x_le, y_le, z_le, rot_x_deg, rot_y_deg, rot_z_deg):
            # 1. Scale
            xs = x_norm * c
            ys = y_norm * c  # Airfoil Y is actually Z in aircraft frame usually, but let's keep local first
            # Local airfoil frame: X is chordwise, Y is thickness-wise (up).
            # In aircraft frame: X is longitudinal, Z is vertical (up), Y is spanwise.
            # So Airfoil Y -> Aircraft Z. Airfoil X -> Aircraft X.

            # Apply incidence/twist (Rotation about Y axis - pitch)
            # Actually, standard aircraft coordinates: X back, Y right, Z up?
            # Or X back, Y right, Z down?
            # Let's assume standard visualization: X+ back/right?, Z+ up.
            # Usually X is longitudinal axis.

            # Let's map:
            # Local X (chord) -> Global X
            # Local Y (thickness) -> Global Z

            # Rotation matrix for incidence (about Y axis)
            theta = np.radians(rot_y_deg)  # Pitch

            x_rot = xs * cos(theta) - ys * sin(theta)
            z_rot = xs * sin(theta) + ys * cos(theta)
            y_rot = np.zeros_like(xs)  # No spanwise thickness

            # Translate
            x_global = x_rot + x_le
            y_global = y_rot + y_le
            z_global = z_rot + z_le

            return x_global, y_global, z_global

        # Root Section
        xr, yr, zr = transform_section(x_root_norm, y_root_norm, c_root, x_offset, 0, z_offset, 0, incidence, 0)

        # Right Tip Section
        xt_r, yt_r, zt_r = transform_section(
            x_tip_norm, y_tip_norm, c_tip, x_offset + dx_tip, dy_tip, z_offset + dz_tip, 0, incidence + twist, 0
        )

        # Left Tip Section
        if symmetric:
            xt_l, yt_l, zt_l = transform_section(
                x_tip_norm, y_tip_norm, c_tip, x_offset + dx_tip, -dy_tip, z_offset + dz_tip, 0, incidence + twist, 0
            )

        vertices = []
        faces = []

        n_points = len(xr)

        # Add vertices
        # 0 to n-1: Root
        for i in range(n_points):
            vertices.append([xr[i], yr[i], zr[i]])

        # n to 2n-1: Right Tip
        for i in range(n_points):
            vertices.append([xt_r[i], yt_r[i], zt_r[i]])

        # 2n to 3n-1: Left Tip
        if symmetric:
            for i in range(n_points):
                vertices.append([xt_l[i], yt_l[i], zt_l[i]])

        # Triangulate Root to Right Tip
        for i in range(n_points - 1):
            # Quad: R[i], R[i+1], T[i+1], T[i]
            p1 = i
            p2 = i + 1
            p3 = n_points + i + 1
            p4 = n_points + i

            faces.append([p1, p2, p3])
            faces.append([p1, p3, p4])

        # Triangulate Root to Left Tip
        if symmetric:
            for i in range(n_points - 1):
                # Quad: R[i], R[i+1], T[i+1], T[i]
                p1 = i
                p2 = i + 1
                p3 = 2 * n_points + i + 1
                p4 = 2 * n_points + i

                # Check normals? For left wing, we are extruding in -Y.
                # If we keep same order, normal might be inverted.
                # But usually double-sided rendering handles it.
                # Let's keep consistent winding.
                faces.append([p1, p3, p2])  # Swap to flip normal?
                faces.append([p1, p4, p3])

        return {"vertices": vertices, "faces": faces, "color": color}


def estimate_wing_fuel_volume(
    area_m2: float,
    span_m: float,
    t_c_root: float,
    t_c_tip: float,
    taper: float,
    tank_fraction: float = 0.7,  # Fraction of wing span/area available for fuel
) -> float:
    """
    Estimates available fuel volume in the wing.
    Volume ~ Area * Avg_Thickness * Tank_Fraction * Efficiency
    """
    if span_m <= 0:
        return 0.0

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

    s_ref = 20.0  # Default fallback
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
        airfoil_tip=airfoil_tip,
    )

    # Fuselage
    # Check for detailed fuselage inputs
    fus_len = guess.get("fuselage_length", span * 0.8)
    fus_dia = guess.get("fuselage_diameter", fus_len / 8.0)

    fus_cps = guess.get("fuselage_control_points", [])
    if not fus_cps:
        # Default control points if none provided (Basic cigar shape)
        fus_cps = [
            {"x_rel": 0.0, "radius_rel": 0.0},
            {"x_rel": 0.05, "radius_rel": 0.3},
            {"x_rel": 0.2, "radius_rel": 0.8},
            {"x_rel": 0.4, "radius_rel": 1.0},
            {"x_rel": 0.7, "radius_rel": 0.8},
            {"x_rel": 1.0, "radius_rel": 0.0},
        ]

    fuselage = DetailedFuselage(length=fus_len, diameter=fus_dia, control_points=fus_cps)

    # Tail
    # Area ratio: HT ~ 0.2 Wing, VT ~ 0.1 Wing => Total ~ 0.3
    ht_area = guess.get("ht_area", 0.0)
    vt_area = guess.get("vt_area", 0.0)

    tail = DetailedTail(
        area_ratio_to_wing=0.3,
        ht_area=ht_area,
        vt_area=vt_area,
        ht_aspect_ratio=guess.get("ht_aspect_ratio", 4.0),
        vt_aspect_ratio=guess.get("vt_aspect_ratio", 1.5),
        ht_taper=guess.get("ht_taper", 0.5),
        vt_taper=guess.get("vt_taper", 0.6),
        ht_sweep=guess.get("ht_sweep", 20.0),
        vt_sweep=guess.get("vt_sweep", 30.0),
        ht_thickness_ratio=guess.get("ht_thickness_ratio", 0.12),
        vt_thickness_ratio=guess.get("vt_thickness_ratio", 0.12),
        ht_airfoil=guess.get("ht_airfoil", "naca0012"),
        vt_airfoil=guess.get("vt_airfoil", "naca0012"),
        ht_x_le=guess.get("ht_x_le", None),
        vt_x_le=guess.get("vt_x_le", None),
        ht_z_le=guess.get("ht_z_le", None),
        vt_z_le=guess.get("vt_z_le", None),
    )

    return ParametricGeometry(wing=wing, fuselage=fuselage, tail=tail)
