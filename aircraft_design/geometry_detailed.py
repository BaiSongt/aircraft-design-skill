from __future__ import annotations

from dataclasses import dataclass
from math import acos, cos, pi, sin, sqrt


@dataclass(frozen=True)
class AirfoilSpec:
    type: str
    code: str
    n: int = 161


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


@dataclass(frozen=True)
class FuselageStation:
    x_m: float
    radius_m: float

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
    Avg Thickness approx (t_c_root * c_root + t_c_tip * c_tip) / 2 ? No.
    Volume of wing Vw ~ S * t_c_avg * c_avg ?
    
    Better approx: Vw = Integral(t(y) * c(y) * dy)
    c(y) linear from c_root to c_tip.
    t(y) = t_c(y) * c(y).
    t_c(y) often linear or constant. Assume linear.
    
    Vw = span/2 * (A_root + A_tip + sqrt(A_root*A_tip)) / 3 (Pyramid frustum approx for area distribution?)
    Area of airfoil section ~ 0.7 * t * c (approx)
    """
    if span_m <= 0: return 0.0
    
    # Geometry
    # S = b * (cr + ct) / 2
    # ct = taper * cr
    # S = b * cr * (1 + taper) / 2
    # cr = 2 * S / (b * (1 + taper))
    # ct = taper * cr
    
    c_root = 2 * area_m2 / (span_m * (1 + taper))
    c_tip = taper * c_root
    
    # Section areas
    # Area ~ 0.7 * t * c
    a_root = 0.7 * (t_c_root * c_root) * c_root
    a_tip = 0.7 * (t_c_tip * c_tip) * c_tip
    
    # Total volume (Pyramidal frustum for linear taper)
    # V = h/3 * (A1 + A2 + sqrt(A1*A2))
    # Here h = b (total span, sum of two halves)
    # Actually integral is better.
    # But let's use the formula: V = b * (A_root + A_tip + sqrt(A_root*A_tip)) / 3
    # This assumes A(y) is quadratic? A(y) ~ c(y)^2. c(y) is linear. So A(y) is quadratic. Correct.
    
    vol_total = span_m * (a_root + a_tip + sqrt(a_root * a_tip)) / 3.0
    
    return vol_total * tank_fraction * 0.85 # 0.85 for structure/systems loss

def check_geometry_constraints(
    inputs: dict,
    required_fuel_vol_m3: float = 0.0
) -> list[str]:
    """
    Checks geometric constraints.
    """
    warnings = []
    
    gd = inputs.get("geometry_detailed", {})
    gp = inputs.get("geometry", {}) # Fallback to simple geometry
    
    # 1. Fuel Volume Check
    if required_fuel_vol_m3 > 0:
        # Try detailed first
        if "wing" in gd:
            # Need parameters. If not fully detailed, fallback to parametric
            pass
        
        # Use parametric estimation
        s_ref = float(gp.get("wing_area_m2", 0)) if "wing_area_m2" in gp else 0.0
        if s_ref == 0:
            s_ref = float(inputs.get("wing_area_m2", 0)) # Try top level
            
        span = float(gp.get("span_m", 0))
        if span == 0 and "aspect_ratio" in gp and s_ref > 0:
            span = sqrt(float(gp["aspect_ratio"]) * s_ref)
            
        t_c = float(gp.get("taper_ratio", 0.12)) # Wait, t_c not taper
        # Assuming t_c is in inputs or default
        t_c = 0.12 # Default
        if "thickness_ratio" in inputs.get("initial_guess", {}):
            t_c = float(inputs["initial_guess"]["thickness_ratio"])
            
        taper = float(gp.get("taper_ratio", 0.4))
        
        avail_vol = estimate_wing_fuel_volume(s_ref, span, t_c, t_c, taper)
        
        if avail_vol < required_fuel_vol_m3:
            warnings.append(f"Fuel Volume Insufficient: Required {required_fuel_vol_m3:.2f} m3, Est. Available {avail_vol:.2f} m3")

    # 2. Aspect Ratio Check (Structural/Aero limits)
    ar = float(gp.get("aspect_ratio", 0))
    if ar > 14 and "glider" not in str(inputs.get("name", "")).lower():
        warnings.append(f"High Aspect Ratio ({ar:.1f}) may require advanced materials.")
    if ar < 2 and ar > 0:
        warnings.append(f"Low Aspect Ratio ({ar:.1f}) may have high induced drag.")

    return warnings


def geometry_detailed_from_inputs(inputs: dict) -> dict | None:
    gd = inputs.get("geometry_detailed", None)
    if gd is None:
        return None
    if not isinstance(gd, dict):
        raise ValueError("geometry_detailed must be an object.")

    out: dict = {}

    wing = gd.get("wing", None)
    if wing is not None:
        if not isinstance(wing, dict):
            raise ValueError("geometry_detailed.wing must be an object.")
        af = wing.get("airfoil", None)
        if af is not None:
            if not isinstance(af, dict):
                raise ValueError("geometry_detailed.wing.airfoil must be an object.")
            aft = str(af.get("type", "naca4")).strip().lower()
            code = str(af.get("code", "")).strip()
            n = int(af.get("n", 161))
            if aft == "naca4":
                coords = naca4_coordinates(code=code, n=n)
                out["wing"] = {"airfoil": {"type": "naca4", "code": code, "n": n, "coords": coords}}
            else:
                raise ValueError(f"Unsupported airfoil type: {aft}")

    fus = gd.get("fuselage", None)
    if fus is not None:
        if not isinstance(fus, dict):
            raise ValueError("geometry_detailed.fuselage must be an object.")
        stations = fus.get("stations", None)
        if stations is not None:
            if not isinstance(stations, list) or not stations:
                raise ValueError("geometry_detailed.fuselage.stations must be a non-empty list.")
            parsed = []
            for s in stations:
                if not isinstance(s, dict):
                    raise ValueError("Each fuselage station must be an object.")
                x = s.get("x_m", None)
                r = s.get("radius_m", None)
                ry = s.get("radius_y_m", None)
                rz = s.get("radius_z_m", None)
                if not isinstance(x, (int, float)):
                    raise ValueError("Fuselage station requires numeric x_m.")
                if r is not None:
                    if not isinstance(r, (int, float)):
                        raise ValueError("Fuselage station radius_m must be numeric when provided.")
                    if float(r) < 0.0:
                        raise ValueError("Fuselage station radius_m must be non-negative.")
                    parsed.append({"x_m": float(x), "radius_m": float(r)})
                else:
                    if not isinstance(ry, (int, float)) or not isinstance(rz, (int, float)):
                        raise ValueError("Fuselage station requires radius_m or both radius_y_m and radius_z_m.")
                    if float(ry) < 0.0 or float(rz) < 0.0:
                        raise ValueError("Fuselage station radii must be non-negative.")
                    parsed.append({"x_m": float(x), "radius_y_m": float(ry), "radius_z_m": float(rz)})
            parsed_sorted = sorted(parsed, key=lambda t: t["x_m"])
            out["fuselage"] = {"stations": parsed_sorted}

    return out
