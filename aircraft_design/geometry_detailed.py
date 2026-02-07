from __future__ import annotations

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


@dataclass
class FuselageStation:
    x_m: float
    radius_m: float


@dataclass
class DetailedFuselage:
    length: float
    diameter: float
    stations: list[FuselageStation] = field(default_factory=list)


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


def geometry_detailed_from_inputs(inputs: dict) -> dict:
    """
    Extracts detailed geometry configuration from standard inputs dict.
    Returns a dictionary suitable for downstream geometry tasks.
    """
    geo_in = inputs.get("geometry", {})
    
    # Wing
    wing_in = geo_in.get("wing", {})
    # Note: If wing parameters are missing, we might use sizing results later,
    # but here we just extract what's provided in inputs or defaults
    wing = {
        "aspect_ratio": float(wing_in.get("aspect_ratio", inputs.get("sizing", {}).get("aspect_ratio", 7.0))),
        "taper_ratio": float(wing_in.get("taper_ratio", 0.3)),
        "sweep_qc": float(wing_in.get("sweep_qc", 0.0)),
        "thickness_to_chord_root": float(wing_in.get("thickness_to_chord_root", 0.12)),
        "dihedral": float(wing_in.get("dihedral", 0.0)),
        "incidence": float(wing_in.get("incidence", 0.0)),
        "twist": float(wing_in.get("twist", 0.0)),
    }

    # Fuselage
    fus_in = geo_in.get("fuselage", {})
    fuselage = {
        "length": float(fus_in.get("length", 10.0)),
        "diameter": float(fus_in.get("diameter", 1.5)),
        "stations": fus_in.get("stations", [])
    }
    
    # Tails
    tails_in = geo_in.get("tails", {})
    
    return {
        "wing": wing,
        "fuselage": fuselage,
        "tails": tails_in
    }
