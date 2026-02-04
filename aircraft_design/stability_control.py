from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt, cos, sin


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
    
    w_n = mass_kg * 9.81
    q_bar = 0.5 * 1.225 * (mach * 340.0)**2
    
    omega_sp_rad_s = sqrt(
        (q_bar * s_m2 * cl_alpha * static_margin) / (mass_kg * (s_m2 / 4.0))
    )
    
    t_sp_s = 2.0 * pi / omega_sp_rad_s
    
    omega_ph_rad_s = sqrt(
        (q_bar * s_m2 * cl_alpha) / (mass_kg * (s_m2 / 4.0))
    )
    
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
    
    w_n = mass_kg * 9.81
    q_bar = 0.5 * 1.225 * (mach * 340.0)**2
    
    omega_roll_rad_s = sqrt(
        (q_bar * s_m2 * cl_beta) / (mass_kg * (b_m / 4.0)**2)
    )
    
    t_roll_s = 2.0 * pi / omega_roll_rad_s
    
    omega_dutch_rad_s = sqrt(
        (q_bar * s_m2 * cn_beta) / (mass_kg * (b_m / 4.0)**2)
    )
    
    t_dutch_s = 2.0 * pi / omega_dutch_rad_s
    
    omega_spiral_rad_s = sqrt(
        (q_bar * s_m2 * cn_beta) / (mass_kg * (b_m / 4.0)**2)
    )
    
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
