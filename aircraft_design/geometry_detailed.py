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


@dataclass
class FuselageStation:
    x_m: float
    radius_m: float


@dataclass
class DetailedFuselage:
    length: float
    diameter: float
    stations: list[FuselageStation] = field(default_factory=list)

@dataclass
class DetailedTail:
    area_ratio_to_wing: float
    ht_aspect_ratio: float = 4.0
    vt_aspect_ratio: float = 1.5

@dataclass
class ParametricGeometry:
    wing: DetailedWing
    fuselage: DetailedFuselage
    tail: DetailedTail

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
        thickness_to_chord_root=tc
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
