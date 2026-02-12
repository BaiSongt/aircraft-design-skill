from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from ..common.units import CONST


@dataclass(frozen=True)
class WingGeometry:
    s_m2: float
    ar: float
    b_m: float
    cbar_m: float


def wing_geometry_from_loading(
    *,
    w0_kg: float,
    wing_loading_pa: float,
    aspect_ratio: float,
) -> WingGeometry:
    if w0_kg <= 0.0:
        raise ValueError("w0_kg must be positive.")
    if wing_loading_pa <= 0.0:
        raise ValueError("wing_loading_pa must be positive.")
    if aspect_ratio <= 0.0:
        raise ValueError("aspect_ratio must be positive.")

    w0_n = w0_kg * CONST.g0_m_s2
    s = w0_n / wing_loading_pa
    b = sqrt(aspect_ratio * s)
    cbar = s / b
    return WingGeometry(s_m2=s, ar=aspect_ratio, b_m=b, cbar_m=cbar)
