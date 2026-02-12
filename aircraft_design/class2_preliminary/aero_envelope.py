from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class AeroEnvelopeResult:
    envelope_data: dict
    details: dict


def generate_aero_envelope(
    *,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    sweep_max_thickness_deg: float,
    cd0: float,
    taper_ratio: float,
    thickness_ratio: float,
    mach_range: list[float],
    cl_range: list[float],
    fuselage_diameter_m: float = 0.0,
    wing_span_m: float = 0.0,
    mach_crit: float = 0.8,
    mach_dd: float = 1.2,
) -> AeroEnvelopeResult:
    from .aero_lift_slope import (
        calculate_oswald_efficiency,
        generate_cl_alpha_curve,
        generate_lift_drag_polar,
    )
    from .aero_drag_buildup import (
        generate_drag_mach_curve,
    )

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

    oswald_efficiency = calculate_oswald_efficiency(
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
    )

    drag_mach_curve = generate_drag_mach_curve(
        cl=0.5,
        cd0_subsonic=cd0,
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        mach_range=mach_range,
        mach_crit=mach_crit,
        mach_dd=mach_dd,
        thickness_ratio=thickness_ratio,
    )

    envelope_data = {
        "cl_alpha_curve": cl_alpha_curve,
        "lift_drag_polar": polar,
        "drag_mach_curve": drag_mach_curve,
        "oswald_efficiency": oswald_efficiency,
    }

    details = {
        "aspect_ratio": aspect_ratio,
        "sweep_quarter_chord_deg": sweep_quarter_chord_deg,
        "sweep_max_thickness_deg": sweep_max_thickness_deg,
        "cd0": cd0,
        "taper_ratio": taper_ratio,
        "thickness_ratio": thickness_ratio,
        "mach_crit": mach_crit,
        "mach_dd": mach_dd,
    }

    return AeroEnvelopeResult(envelope_data=envelope_data, details=details)


def generate_l_d_max_envelope(
    *,
    cd0: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
    cl_max: float = 1.5,
    cl_min: float = -0.5,
    cl_steps: int = 100,
) -> dict:
    from .aero_lift_slope import calculate_lift_induced_drag_factor

    k = calculate_lift_induced_drag_factor(
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
    )

    cl_values = []
    cd_values = []
    l_d_values = []

    for i in range(cl_steps):
        cl = cl_min + (cl_max - cl_min) * i / (cl_steps - 1)
        cd = cd0 + k * cl**2
        l_d = cl / cd if cd > 0 else 0.0

        cl_values.append(cl)
        cd_values.append(cd)
        l_d_values.append(l_d)

    l_d_max = max(l_d_values)
    l_d_max_cl = cl_values[l_d_values.index(l_d_max)]
    l_d_max_cd = cd_values[l_d_values.index(l_d_max)]

    return {
        "cl": cl_values,
        "cd": cd_values,
        "l_d": l_d_values,
        "l_d_max": l_d_max,
        "l_d_max_cl": l_d_max_cl,
        "l_d_max_cd": l_d_max_cd,
        "k": k,
        "cd0": cd0,
    }


def generate_mach_cd_envelope(
    *,
    cd0_subsonic: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
    thickness_ratio: float,
    mach_range: list[float],
    cl_range: list[float],
    mach_crit: float = 0.8,
    mach_dd: float = 1.2,
) -> dict:
    from .aero_drag_buildup import generate_drag_mach_curve

    cl_curves: dict[str, list[float]] = {}
    cd_curves: dict[str, list[float]] = {}

    for cl in cl_range:
        drag_curve = generate_drag_mach_curve(
            cl=cl,
            cd0_subsonic=cd0_subsonic,
            aspect_ratio=aspect_ratio,
            taper_ratio=taper_ratio,
            sweep_quarter_chord_deg=sweep_quarter_chord_deg,
            mach_range=mach_range,
            mach_crit=mach_crit,
            mach_dd=mach_dd,
            thickness_ratio=thickness_ratio,
        )

        cl_key = f"cl_{cl:.2f}"
        cl_curves[cl_key] = drag_curve["cd_total"]
        cd_curves[cl_key] = drag_curve["cd_total"]

    return {
        "mach": mach_range,
        "cl_curves": cl_curves,
        "cd_curves": cd_curves,
    }


def generate_cl_alpha_mach_envelope(
    *,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    sweep_max_thickness_deg: float,
    mach_range: list[float],
    fuselage_diameter_m: float = 0.0,
    wing_span_m: float = 0.0,
) -> dict:
    from .aero_lift_slope import (
        calculate_lift_slope_subsonic,
        calculate_lift_slope_supersonic,
        calculate_lift_slope_transonic,
    )

    cl_alpha_values = []

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
        elif mach > 1.3:
            result = calculate_lift_slope_supersonic(
                aspect_ratio=aspect_ratio,
                sweep_leading_edge_deg=sweep_quarter_chord_deg,
                taper_ratio=1.0,
                mach=mach,
            )
        else:
            result = calculate_lift_slope_transonic(
                aspect_ratio=aspect_ratio,
                sweep_quarter_chord_deg=sweep_quarter_chord_deg,
                sweep_max_thickness_deg=sweep_max_thickness_deg,
                mach=mach,
                fuselage_diameter_m=fuselage_diameter_m,
                wing_span_m=wing_span_m,
            )

        cl_alpha_values.append(result.cl_alpha)

    return {
        "mach": mach_range,
        "cl_alpha": cl_alpha_values,
    }


def generate_comprehensive_aero_envelope(
    *,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    sweep_max_thickness_deg: float,
    cd0: float,
    taper_ratio: float,
    thickness_ratio: float,
    mach_range: list[float],
    cl_range: list[float],
    fuselage_diameter_m: float = 0.0,
    wing_span_m: float = 0.0,
    mach_crit: float = 0.8,
    mach_dd: float = 1.2,
) -> dict:
    envelope = generate_aero_envelope(
        aspect_ratio=aspect_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        sweep_max_thickness_deg=sweep_max_thickness_deg,
        cd0=cd0,
        taper_ratio=taper_ratio,
        thickness_ratio=thickness_ratio,
        mach_range=mach_range,
        cl_range=cl_range,
        fuselage_diameter_m=fuselage_diameter_m,
        wing_span_m=wing_span_m,
        mach_crit=mach_crit,
        mach_dd=mach_dd,
    )

    l_d_max = generate_l_d_max_envelope(
        cd0=cd0,
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        cl_max=max(cl_range),
        cl_min=min(cl_range),
        cl_steps=len(cl_range),
    )

    mach_cd_envelope = generate_mach_cd_envelope(
        cd0_subsonic=cd0,
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        thickness_ratio=thickness_ratio,
        mach_range=mach_range,
        cl_range=cl_range,
        mach_crit=mach_crit,
        mach_dd=mach_dd,
    )

    cl_alpha_mach_envelope = generate_cl_alpha_mach_envelope(
        aspect_ratio=aspect_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        sweep_max_thickness_deg=sweep_max_thickness_deg,
        mach_range=mach_range,
        fuselage_diameter_m=fuselage_diameter_m,
        wing_span_m=wing_span_m,
    )

    return {
        "basic_envelope": envelope.envelope_data,
        "l_d_max_envelope": l_d_max,
        "mach_cd_envelope": mach_cd_envelope,
        "cl_alpha_mach_envelope": cl_alpha_mach_envelope,
        "details": envelope.details,
    }
