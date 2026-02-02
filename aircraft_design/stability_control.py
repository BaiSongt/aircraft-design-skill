from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StaticStabilityResult:
    x_np_cbar: float
    x_cg_cbar: float
    static_margin: float
    trim_tail_cl: float
    details: dict


def estimate_static_margin_and_trim(
    *,
    x_ac_w_cbar: float,
    x_cg_cbar: float,
    vh: float,
    tail_efficiency: float = 0.9,
    downwash_deda: float = 0.35,
    a_ratio: float = 0.9,
    cm0_w: float = 0.0,
    cl_cruise: float = 0.6,
) -> StaticStabilityResult:
    if not (0.0 < tail_efficiency <= 1.0):
        raise ValueError("tail_efficiency must be in (0, 1].")
    if not (0.0 <= downwash_deda < 1.0):
        raise ValueError("downwash_deda must be in [0, 1).")
    if vh <= 0.0:
        raise ValueError("vh must be positive.")

    x_np = x_ac_w_cbar + tail_efficiency * a_ratio * (1.0 - downwash_deda) * vh
    sm = x_np - x_cg_cbar

    trim_tail_cl = (cm0_w + (x_cg_cbar - x_ac_w_cbar) * cl_cruise) / max(1e-6, vh)

    return StaticStabilityResult(
        x_np_cbar=x_np,
        x_cg_cbar=x_cg_cbar,
        static_margin=sm,
        trim_tail_cl=trim_tail_cl,
        details={
            "x_ac_w_cbar": x_ac_w_cbar,
            "vh": vh,
            "tail_efficiency": tail_efficiency,
            "downwash_deda": downwash_deda,
            "a_ratio": a_ratio,
            "cm0_w": cm0_w,
            "cl_cruise": cl_cruise,
        },
    )


def estimate_cg_range_cbar(
    *,
    x_cg_fwd_cbar: float,
    x_cg_aft_cbar: float,
) -> dict:
    if x_cg_fwd_cbar > x_cg_aft_cbar:
        raise ValueError("x_cg_fwd_cbar must be <= x_cg_aft_cbar.")
    return {"x_cg_fwd_cbar": x_cg_fwd_cbar, "x_cg_aft_cbar": x_cg_aft_cbar}


def estimate_static_margin_and_trim_envelope(
    *,
    x_ac_w_cbar: float,
    x_cg_fwd_cbar: float,
    x_cg_aft_cbar: float,
    vh: float,
    tail_efficiency: float = 0.9,
    downwash_deda: float = 0.35,
    a_ratio: float = 0.9,
    cm0_w: float = 0.0,
    cl_min: float = 0.4,
    cl_max: float = 0.8,
) -> dict:
    cg = [float(x_cg_fwd_cbar), float(x_cg_aft_cbar)]
    cls = [float(cl_min), float(cl_max)]
    cases = []
    sm_values = []
    trim_values = []
    for xcg in cg:
        for cl in cls:
            r = estimate_static_margin_and_trim(
                x_ac_w_cbar=x_ac_w_cbar,
                x_cg_cbar=xcg,
                vh=vh,
                tail_efficiency=tail_efficiency,
                downwash_deda=downwash_deda,
                a_ratio=a_ratio,
                cm0_w=cm0_w,
                cl_cruise=cl,
            )
            cases.append({"x_cg_cbar": xcg, "cl": cl, "static_margin": r.static_margin, "trim_tail_cl": r.trim_tail_cl})
            sm_values.append(float(r.static_margin))
            trim_values.append(float(r.trim_tail_cl))
    return {
        "x_cg_fwd_cbar": float(x_cg_fwd_cbar),
        "x_cg_aft_cbar": float(x_cg_aft_cbar),
        "cl_min": float(cl_min),
        "cl_max": float(cl_max),
        "static_margin_range": {"min": min(sm_values), "max": max(sm_values)},
        "trim_tail_cl_range": {"min": min(trim_values), "max": max(trim_values)},
        "cases": cases,
    }
