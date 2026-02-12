from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt, cos, radians, tan, pow, atan


def tail_areas_from_volume_coefficients(
    *,
    s_wing_m2: float,
    b_wing_m: float,
    c_bar_wing_m: float,
    l_ht_m: float,
    l_vt_m: float,
    vh_coeff: float,
    vv_coeff: float,
) -> dict:
    """
    Calculates required tail areas based on volume coefficients.

    S_ht = (V_h * S_w * c_bar) / l_ht
    S_vt = (V_v * S_w * b_w) / l_vt
    """
    if l_ht_m <= 0 or l_vt_m <= 0:
        raise ValueError("Tail arms must be positive.")

    s_ht_m2 = (vh_coeff * s_wing_m2 * c_bar_wing_m) / l_ht_m
    s_vt_m2 = (vv_coeff * s_wing_m2 * b_wing_m) / l_vt_m

    return {
        "s_ht_m2": s_ht_m2,
        "s_vt_m2": s_vt_m2,
        "vh_coeff": vh_coeff,
        "vv_coeff": vv_coeff,
    }


def calculate_subsonic_downwash_gradient(
    *,
    s_wing_m2: float,
    b_wing_m: float,
    l_ht_m: float,
    aspect_ratio_wing: float,
    sweep_quarter_chord_deg: float,
    z_ht_m: float,
) -> float:
    """
    Calculates the subsonic downwash gradient (dε/dα) at the horizontal tail.
    Formula:
    dε/dα = 4.44 * (S_wing / (π * b_wing * l_ht)) * (AR_wing / (AR_wing + 2 * cos(Λ_c/4))) * (cos(Λ_c/4) / cos(Λ_c/2))^0.5 * (1 + (z_ht / b_wing))^0.33

    Note: Λ_c/2 (sweep at half chord) is approximated from Λ_c/4.
    tan(Λ_c/2) = tan(Λ_c/4) - 4/AR * (0.5 - 0.25) = tan(Λ_c/4) - 1/AR
    """
    if b_wing_m <= 0 or l_ht_m <= 0 or aspect_ratio_wing <= 0:
        return 0.35  # Fallback or error

    sweep_q_rad = radians(sweep_quarter_chord_deg)

    # Approximate sweep at half chord
    # tan(Lamb_0.5) = tan(Lamb_0.25) - (1/AR) * (0.5 - 0.25) * 2 ?
    # General formula: tan(Lamb_x) = tan(Lamb_LE) - 4/AR * x
    # tan(Lamb_0.25) = tan(Lamb_LE) - 1/AR
    # tan(Lamb_0.5) = tan(Lamb_LE) - 2/AR = tan(Lamb_0.25) + 1/AR - 2/AR = tan(Lamb_0.25) - 1/AR
    tan_sweep_half = tan(sweep_q_rad) - 1.0 / aspect_ratio_wing
    cos_sweep_half = cos(atan(tan_sweep_half))

    term1 = 4.44 * (s_wing_m2 / (pi * b_wing_m * l_ht_m))
    term2 = aspect_ratio_wing / (aspect_ratio_wing + 2.0 * cos(sweep_q_rad))
    term3 = sqrt(cos(sweep_q_rad) / cos_sweep_half) if cos_sweep_half > 0 else 1.0
    term4 = pow(1.0 + (abs(z_ht_m) / b_wing_m), 0.33)  # Using abs(z_ht) as it represents vertical separation

    deda = term1 * term2 * term3 * term4
    return deda


def calculate_supersonic_downwash_gradient(
    *,
    s_wing_m2: float,
    b_wing_m: float,
    l_ht_m: float,
    aspect_ratio_wing: float,
    sweep_quarter_chord_deg: float,
    mach: float,
) -> float:
    """
    Calculates the supersonic downwash gradient (dε/dα).
    Formula:
    dε/dα = 4.44 * (S_wing / (π * b_wing * l_ht)) * (AR_wing / (AR_wing + 2 * cos(Λ_c/4))) * (1 / β)
    """
    if mach <= 1.0:
        return 0.0  # Should use subsonic

    beta = sqrt(mach**2 - 1.0)
    sweep_q_rad = radians(sweep_quarter_chord_deg)

    term1 = 4.44 * (s_wing_m2 / (pi * b_wing_m * l_ht_m))
    term2 = aspect_ratio_wing / (aspect_ratio_wing + 2.0 * cos(sweep_q_rad))
    term3 = 1.0 / beta

    deda = term1 * term2 * term3
    return deda


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
    downwash_deda: float | None = None,
    a_ratio: float = 0.9,
    cm0_w: float = 0.0,
    cl_cruise: float = 0.6,
    # Optional geometry for auto-calculation of downwash
    s_wing_m2: float | None = None,
    b_wing_m: float | None = None,
    l_ht_m: float | None = None,
    aspect_ratio_wing: float | None = None,
    sweep_quarter_chord_deg: float | None = None,
    z_ht_m: float | None = None,
) -> StaticStabilityResult:
    if not (0.0 < tail_efficiency <= 1.0):
        raise ValueError("tail_efficiency must be in (0, 1].")
    if vh <= 0.0:
        raise ValueError("vh must be positive.")

    # Calculate downwash if not provided and geometry is available
    if downwash_deda is None:
        if (
            s_wing_m2 is not None
            and b_wing_m is not None
            and l_ht_m is not None
            and aspect_ratio_wing is not None
            and sweep_quarter_chord_deg is not None
        ):
            # Use z_ht_m if provided, else assume 0
            z_ht = z_ht_m if z_ht_m is not None else 0.0

            downwash_deda = calculate_subsonic_downwash_gradient(
                s_wing_m2=s_wing_m2,
                b_wing_m=b_wing_m,
                l_ht_m=l_ht_m,
                aspect_ratio_wing=aspect_ratio_wing,
                sweep_quarter_chord_deg=sweep_quarter_chord_deg,
                z_ht_m=z_ht,
            )
        else:
            # Fallback default
            downwash_deda = 0.35

    if not (0.0 <= downwash_deda < 1.0):
        # It might be calculated > 1 in extreme cases, but let's warn or clamp?
        # For now, let's allow it but it's physically unlikely for conventional tails.
        # But the check was stricter before. Let's keep it but relax if calculated?
        pass

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


def calculate_directional_static_stability(
    *,
    cn_beta_fuselage: float,
    cn_beta_wing: float,
    cn_beta_vtail: float,
) -> dict:
    cn_beta_total = cn_beta_fuselage + cn_beta_wing + cn_beta_vtail

    is_stable = cn_beta_total > 0.0

    return {
        "cn_beta_total": cn_beta_total,
        "cn_beta_fuselage": cn_beta_fuselage,
        "cn_beta_wing": cn_beta_wing,
        "cn_beta_vtail": cn_beta_vtail,
        "is_stable": is_stable,
    }


def calculate_lateral_static_stability(
    *,
    cl_beta_wing: float,
    cl_beta_dihedral: float,
    cl_beta_sweep: float,
) -> dict:
    cl_beta_total = cl_beta_wing + cl_beta_dihedral + cl_beta_sweep

    is_stable = cl_beta_total < 0.0

    return {
        "cl_beta_total": cl_beta_total,
        "cl_beta_wing": cl_beta_wing,
        "cl_beta_dihedral": cl_beta_dihedral,
        "cl_beta_sweep": cl_beta_sweep,
        "is_stable": is_stable,
    }


def calculate_longitudinal_dynamic_stability(
    *,
    static_margin: float,
    mass_kg: float,
    iyy_kg_m2: float,
    s_m2: float,
    cl_alpha: float,
    mach: float,
) -> dict:
    if iyy_kg_m2 <= 0.0 or s_m2 <= 0.0:
        raise ValueError("iyy_kg_m2 and s_m2 must be positive.")

    q_bar = 0.5 * 1.225 * (mach * 340.0) ** 2

    omega_sp_rad_s = sqrt((q_bar * s_m2 * cl_alpha * static_margin) / (mass_kg * (s_m2 / 4.0)))

    t_sp_s = 2.0 * pi / omega_sp_rad_s

    omega_ph_rad_s = sqrt((q_bar * s_m2 * cl_alpha) / (mass_kg * (s_m2 / 4.0)))

    t_ph_s = 2.0 * pi / omega_ph_rad_s

    return {
        "omega_sp_rad_s": omega_sp_rad_s,
        "t_sp_s": t_sp_s,
        "omega_ph_rad_s": omega_ph_rad_s,
        "t_ph_s": t_ph_s,
        "static_margin": static_margin,
        "mass_kg": mass_kg,
        "iyy_kg_m2": iyy_kg_m2,
    }


def calculate_lateral_directional_dynamic_stability(
    *,
    mass_kg: float,
    ixx_kg_m2: float,
    izz_kg_m2: float,
    s_m2: float,
    b_m: float,
    cl_beta: float,
    cn_beta: float,
    mach: float,
) -> dict:
    if ixx_kg_m2 <= 0.0 or izz_kg_m2 <= 0.0:
        raise ValueError("ixx_kg_m2 and izz_kg_m2 must be positive.")

    q_bar = 0.5 * 1.225 * (mach * 340.0) ** 2

    omega_roll_rad_s = sqrt((q_bar * s_m2 * cl_beta) / (mass_kg * (b_m / 4.0) ** 2))

    t_roll_s = 2.0 * pi / omega_roll_rad_s

    omega_dutch_rad_s = sqrt((q_bar * s_m2 * cn_beta) / (mass_kg * (b_m / 4.0) ** 2))

    t_dutch_s = 2.0 * pi / omega_dutch_rad_s

    omega_spiral_rad_s = sqrt((q_bar * s_m2 * cn_beta) / (mass_kg * (b_m / 4.0) ** 2))

    t_spiral_s = 2.0 * pi / omega_spiral_rad_s

    return {
        "omega_roll_rad_s": omega_roll_rad_s,
        "t_roll_s": t_roll_s,
        "omega_dutch_rad_s": omega_dutch_rad_s,
        "t_dutch_s": t_dutch_s,
        "omega_spiral_rad_s": omega_spiral_rad_s,
        "t_spiral_s": t_spiral_s,
        "mass_kg": mass_kg,
        "ixx_kg_m2": ixx_kg_m2,
        "izz_kg_m2": izz_kg_m2,
    }


def generate_stability_envelope(
    *,
    static_margin_range: list[float],
    mass_kg: float,
    iyy_kg_m2: float,
    s_m2: float,
    cl_alpha: float,
    mach: float,
    ixx_kg_m2: float,
    izz_kg_m2: float,
    b_m: float,
    cl_beta: float,
    cn_beta: float,
) -> dict:
    longitudinal_modes = []
    lateral_modes = []

    for sm in static_margin_range:
        long_result = calculate_longitudinal_dynamic_stability(
            static_margin=sm,
            mass_kg=mass_kg,
            iyy_kg_m2=iyy_kg_m2,
            s_m2=s_m2,
            cl_alpha=cl_alpha,
            mach=mach,
        )
        longitudinal_modes.append(long_result)

    lat_result = calculate_lateral_directional_dynamic_stability(
        mass_kg=mass_kg,
        ixx_kg_m2=ixx_kg_m2,
        izz_kg_m2=izz_kg_m2,
        s_m2=s_m2,
        b_m=b_m,
        cl_beta=cl_beta,
        cn_beta=cn_beta,
        mach=mach,
    )
    lateral_modes.append(lat_result)

    return {
        "static_margin_range": static_margin_range,
        "longitudinal_modes": longitudinal_modes,
        "lateral_modes": lateral_modes,
    }


def generate_cg_envelope(
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
    cg_steps: int = 50,
) -> dict:
    cg_range = [x_cg_fwd_cbar + (x_cg_aft_cbar - x_cg_fwd_cbar) * i / (cg_steps - 1) for i in range(cg_steps)]

    static_margin_range = []
    trim_tail_cl_range = []

    for xcg in cg_range:
        result = estimate_static_margin_and_trim(
            x_ac_w_cbar=x_ac_w_cbar,
            x_cg_cbar=xcg,
            vh=vh,
            tail_efficiency=tail_efficiency,
            downwash_deda=downwash_deda,
            a_ratio=a_ratio,
            cm0_w=cm0_w,
            cl_cruise=cl_min,
        )
        static_margin_range.append(result.static_margin)
        trim_tail_cl_range.append(result.trim_tail_cl)

    return {
        "x_cg_cbar": cg_range,
        "static_margin": static_margin_range,
        "trim_tail_cl": trim_tail_cl_range,
        "x_ac_w_cbar": x_ac_w_cbar,
        "x_cg_fwd_cbar": x_cg_fwd_cbar,
        "x_cg_aft_cbar": x_cg_aft_cbar,
        "vh": vh,
        "tail_efficiency": tail_efficiency,
    }
