from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TailSizingResult:
    sh_m2: float
    sv_m2: float


def tail_areas_from_volume_coefficients(
    *,
    vh: float,
    vv: float,
    s_m2: float,
    cbar_m: float,
    b_m: float,
    lh_m: float,
    lv_m: float,
) -> TailSizingResult:
    if any(x <= 0.0 for x in [vh, vv, s_m2, cbar_m, b_m, lh_m, lv_m]):
        raise ValueError("All tail sizing inputs must be positive.")
    sh = vh * s_m2 * cbar_m / lh_m
    sv = vv * s_m2 * b_m / lv_m
    return TailSizingResult(sh_m2=sh, sv_m2=sv)
