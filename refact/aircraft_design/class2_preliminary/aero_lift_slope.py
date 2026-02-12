from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt, cos, sin, tan


@dataclass(frozen=True)
class LiftSlopeResult:
    cl_alpha: float
    details: dict


@dataclass(frozen=True)
class VortexLiftResult:
    cl_vortex: float
    cl_total: float
    details: dict


def calculate_fuselage_lift_factor(
    *,
    fuselage_diameter_m: float,
    wing_span_m: float,
    aspect_ratio: float,
) -> float:
    if fuselage_diameter_m <= 0.0 or wing_span_m <= 0.0:
        raise ValueError("fuselage_diameter_m and wing_span_m must be positive.")
    if aspect_ratio <= 0.0:
        raise ValueError("aspect_ratio must be positive.")

    d_over_b = fuselage_diameter_m / wing_span_m
    f = 1.0 + (0.025 * (d_over_b**2) * aspect_ratio / (1.0 + (d_over_b**2)))
    return f


def calculate_lift_slope_subsonic(
    *,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    sweep_max_thickness_deg: float,
    mach: float = 0.0,
    fuselage_diameter_m: float = 0.0,
    wing_span_m: float = 0.0,
) -> LiftSlopeResult:
    if aspect_ratio <= 0.0:
        raise ValueError("aspect_ratio must be positive.")

    beta = sqrt(1.0 - mach**2) if mach < 1.0 else 1.0

    sweep_max_thickness_rad = sweep_max_thickness_deg * pi / 180.0
    tan_sweep = tan(sweep_max_thickness_rad)

    denominator = 2.0 + sqrt(4.0 + aspect_ratio**2 * (beta**2 + tan_sweep**2))

    cl_alpha_2d = 2.0 * pi
    cl_alpha_3d = (cl_alpha_2d * aspect_ratio / denominator) * (1.0 / beta)

    f = 1.0
    if fuselage_diameter_m > 0.0 and wing_span_m > 0.0:
        f = calculate_fuselage_lift_factor(
            fuselage_diameter_m=fuselage_diameter_m, wing_span_m=wing_span_m, aspect_ratio=aspect_ratio
        )

    cl_alpha = cl_alpha_3d * f

    return LiftSlopeResult(
        cl_alpha=cl_alpha,
        details={
            "mach": mach,
            "beta": beta,
            "aspect_ratio": aspect_ratio,
            "sweep_max_thickness_deg": sweep_max_thickness_deg,
            "cl_alpha_2d": cl_alpha_2d,
            "cl_alpha_3d": cl_alpha_3d,
            "fuselage_lift_factor": f,
        },
    )


def calculate_lift_slope_supersonic(
    *,
    aspect_ratio: float,
    sweep_leading_edge_deg: float,
    taper_ratio: float,
    mach: float,
    exposed_area_ratio: float = 1.0,
) -> LiftSlopeResult:
    if aspect_ratio <= 0.0 or mach <= 1.0:
        raise ValueError("aspect_ratio must be positive and mach > 1.0 for supersonic.")

    beta = sqrt(mach**2 - 1.0)
    sweep_le_rad = sweep_leading_edge_deg * pi / 180.0

    beta_cot_le = beta * (1.0 / tan(sweep_le_rad))

    if beta_cot_le < 1.0:
        cn_alpha = 4.0 / sqrt(mach**2 - 1.0) * aspect_ratio / (aspect_ratio + 2.0)
    else:
        cn_alpha = 4.0 / beta / aspect_ratio

    cl_alpha = cn_alpha * exposed_area_ratio

    return LiftSlopeResult(
        cl_alpha=cl_alpha,
        details={
            "mach": mach,
            "beta": beta,
            "aspect_ratio": aspect_ratio,
            "sweep_leading_edge_deg": sweep_leading_edge_deg,
            "taper_ratio": taper_ratio,
            "exposed_area_ratio": exposed_area_ratio,
            "cn_alpha": cn_alpha,
        },
    )


def calculate_lift_slope_transonic(
    *,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    sweep_max_thickness_deg: float,
    mach: float,
    fuselage_diameter_m: float = 0.0,
    wing_span_m: float = 0.0,
    exposed_area_ratio: float = 1.0,
) -> LiftSlopeResult:
    if aspect_ratio <= 0.0:
        raise ValueError("aspect_ratio must be positive.")

    if mach < 0.9:
        return calculate_lift_slope_subsonic(
            aspect_ratio=aspect_ratio,
            sweep_quarter_chord_deg=sweep_quarter_chord_deg,
            sweep_max_thickness_deg=sweep_max_thickness_deg,
            mach=mach,
            fuselage_diameter_m=fuselage_diameter_m,
            wing_span_m=wing_span_m,
        )
    elif mach > 1.3:
        result = calculate_lift_slope_supersonic(
            aspect_ratio=aspect_ratio,
            sweep_leading_edge_deg=sweep_quarter_chord_deg,
            taper_ratio=1.0,
            mach=mach,
            exposed_area_ratio=exposed_area_ratio,
        )
        result.details["transition_method"] = "supersonic_direct"
        return result
    else:
        subsonic_result = calculate_lift_slope_subsonic(
            aspect_ratio=aspect_ratio,
            sweep_quarter_chord_deg=sweep_quarter_chord_deg,
            sweep_max_thickness_deg=sweep_max_thickness_deg,
            mach=0.9,
            fuselage_diameter_m=fuselage_diameter_m,
            wing_span_m=wing_span_m,
        )

        supersonic_result = calculate_lift_slope_supersonic(
            aspect_ratio=aspect_ratio,
            sweep_leading_edge_deg=sweep_quarter_chord_deg,
            taper_ratio=1.0,
            mach=1.3,
            exposed_area_ratio=exposed_area_ratio,
        )

        cl_alpha_sub = subsonic_result.cl_alpha
        cl_alpha_sup = supersonic_result.cl_alpha

        t = (mach - 0.9) / (1.3 - 0.9)

        cl_alpha = cl_alpha_sub + t * (cl_alpha_sup - cl_alpha_sub)

        return LiftSlopeResult(
            cl_alpha=cl_alpha,
            details={
                "mach": mach,
                "cl_alpha_subsonic": cl_alpha_sub,
                "cl_alpha_supersonic": cl_alpha_sup,
                "transition_factor": t,
                "transition_method": "linear_interpolation",
            },
        )


def calculate_oswald_efficiency(
    *,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
) -> float:
    if aspect_ratio <= 0.0 or taper_ratio <= 0.0:
        raise ValueError("aspect_ratio and taper_ratio must be positive.")

    sweep_rad = sweep_quarter_chord_deg * pi / 180.0

    e = 1.0 / (1.0 + (aspect_ratio * (1.0 + taper_ratio) / (2.0 * sqrt(aspect_ratio) * cos(sweep_rad)) ** 2))

    return max(0.5, min(0.95, e))


def calculate_lift_induced_drag_factor(
    *,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
) -> float:
    if aspect_ratio <= 0.0 or taper_ratio <= 0.0:
        raise ValueError("aspect_ratio and taper_ratio must be positive.")

    e = calculate_oswald_efficiency(
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
    )

    k = 1.0 / (pi * e * aspect_ratio)

    return k


def calculate_vortex_lift(
    *,
    cl_clean: float,
    alpha_deg: float,
    aspect_ratio: float,
    strake_sweep_deg: float,
    leading_edge_strake: bool = False,
    side_edge_strake: bool = False,
) -> VortexLiftResult:
    if aspect_ratio <= 0.0:
        raise ValueError("aspect_ratio must be positive.")

    alpha_rad = alpha_deg * pi / 180.0

    cl_vortex = 0.0

    if leading_edge_strake:
        ct = 0.8 * aspect_ratio**0.5
        cl_vortex_le = ct * (sin(alpha_rad) ** 2) * cos(alpha_rad)
        cl_vortex += cl_vortex_le

    if side_edge_strake:
        ct = 0.5 * aspect_ratio**0.3
        cl_vortex_se = ct * sin(alpha_rad) * (sin(alpha_rad) ** 2)
        cl_vortex += cl_vortex_se

    cl_total = cl_clean + cl_vortex

    return VortexLiftResult(
        cl_vortex=cl_vortex,
        cl_total=cl_total,
        details={
            "cl_clean": cl_clean,
            "alpha_deg": alpha_deg,
            "aspect_ratio": aspect_ratio,
            "strake_sweep_deg": strake_sweep_deg,
            "leading_edge_strake": leading_edge_strake,
            "side_edge_strake": side_edge_strake,
            "cl_vortex_le": cl_vortex_le if leading_edge_strake else 0.0,
            "cl_vortex_se": cl_vortex_se if side_edge_strake else 0.0,
        },
    )


def generate_cl_alpha_curve(
    *,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    sweep_max_thickness_deg: float,
    mach_range: list[float],
    fuselage_diameter_m: float = 0.0,
    wing_span_m: float = 0.0,
) -> dict:
    mach_values: list[float] = []
    cl_alpha_values: list[float] = []
    regime_values: list[str] = []

    for mach in mach_range:
        if mach < 0.9:
            result = calculate_lift_slope_subsonic(
                aspect_ratio=aspect_ratio,
                sweep_quarter_chord_deg=sweep_quarter_chord_deg,
                sweep_max_thickness_deg=sweep_max_thickness_deg,
                mach=mach,
                fuselage_diameter_m=fuselage_diameter_m,
                wing_span_m=wing_span_m,
            )
            regime = "subsonic"
        elif mach > 1.3:
            result = calculate_lift_slope_supersonic(
                aspect_ratio=aspect_ratio,
                sweep_leading_edge_deg=sweep_quarter_chord_deg,
                taper_ratio=1.0,
                mach=mach,
            )
            regime = "supersonic"
        else:
            result = calculate_lift_slope_transonic(
                aspect_ratio=aspect_ratio,
                sweep_quarter_chord_deg=sweep_quarter_chord_deg,
                sweep_max_thickness_deg=sweep_max_thickness_deg,
                mach=mach,
                fuselage_diameter_m=fuselage_diameter_m,
                wing_span_m=wing_span_m,
            )
            regime = "transonic"

        mach_values.append(mach)
        cl_alpha_values.append(result.cl_alpha)
        regime_values.append(regime)

    return {
        "mach": mach_values,
        "cl_alpha": cl_alpha_values,
        "regime": regime_values,
    }


def generate_lift_drag_polar(
    *,
    cd0: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
    cl_range: list[float],
) -> dict:
    k = calculate_lift_induced_drag_factor(
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
    )

    cd_values: list[float] = []

    for cl in cl_range:
        cd = cd0 + k * cl**2
        cd_values.append(cd)

    return {"cl": cl_range, "cd": cd_values, "cd0": cd0, "k": k}


def generate_aero_envelope(
    *,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    sweep_max_thickness_deg: float,
    cd0: float,
    taper_ratio: float,
    mach_range: list[float],
    cl_range: list[float],
    fuselage_diameter_m: float = 0.0,
    wing_span_m: float = 0.0,
) -> dict:
    cl_alpha_curve = generate_cl_alpha_curve(
        aspect_ratio=aspect_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        sweep_max_thickness_deg=sweep_max_thickness_deg,
        mach_range=mach_range,
        fuselage_diameter_m=fuselage_diameter_m,
        wing_span_m=wing_span_m,
    )

    polar = generate_lift_drag_polar(
        cd0=cd0,
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        cl_range=cl_range,
    )

    return {
        "cl_alpha_curve": cl_alpha_curve,
        "lift_drag_polar": polar,
        "oswald_efficiency": calculate_oswald_efficiency(
            aspect_ratio=aspect_ratio,
            taper_ratio=taper_ratio,
            sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        ),
        "induced_drag_factor": calculate_lift_induced_drag_factor(
            aspect_ratio=aspect_ratio,
            taper_ratio=taper_ratio,
            sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        ),
    }
