from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt, cos, sin


@dataclass(frozen=True)
class StructuralWeightResult:
    w_struct_kg: float
    details: dict


def calculate_wing_structural_weight(
    *,
    s_wing_m2: float,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    taper_ratio: float,
    max_takeoff_weight_kg: float,
    t_c: float = 0.12,
    mach_cruise: float = 0.8,
    n_limit: float = 9.0,
    variable_sweep: bool = False,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    if s_wing_m2 <= 0.0 or aspect_ratio <= 0.0:
        raise ValueError("s_wing_m2 and aspect_ratio must be positive.")
    if max_takeoff_weight_kg <= 0.0:
        raise ValueError("max_takeoff_weight_kg must be positive.")
    
    w_fw_lb = max_takeoff_weight_kg * 2.20462
    
    k_var = 1.175 if variable_sweep else 1.0
    
    sweep_rad = sweep_quarter_chord_deg * pi / 180.0
    
    q_pa = 0.5 * 1.225 * (mach_cruise * 340.0)**2
    q_lb_ft2 = q_pa * 0.020885
    
    w_wing_lb = 0.036 * (s_wing_m2 * 10.7639)**0.758 * (w_fw_lb)**0.0035 * \
                  (aspect_ratio / (cos(sweep_rad)**2))**0.6 * \
                  q_lb_ft2**0.006 * \
                  taper_ratio**0.04 * \
                  (100.0 * t_c / cos(sweep_rad))**(-0.3) * \
                  (n_limit * w_fw_lb / (s_wing_m2 * 10.7639 * 100.0))**0.3
    
    # Composite correction
    # Theory: 25% reduction for 55% usage
    reduction_factor = 0.25 * (composite_fraction / 0.55)
    w_wing_lb *= (1.0 - reduction_factor)

    w_wing_kg = w_wing_lb / 2.20462
    
    return StructuralWeightResult(
        w_struct_kg=w_wing_kg,
        details={
            "s_wing_m2": s_wing_m2,
            "aspect_ratio": aspect_ratio,
            "sweep_quarter_chord_deg": sweep_quarter_chord_deg,
            "taper_ratio": taper_ratio,
            "t_c": t_c,
            "mach_cruise": mach_cruise,
            "n_limit": n_limit,
            "variable_sweep": variable_sweep,
            "k_var": k_var,
            "w_fw_lb": w_fw_lb,
            "q_lb_ft2": q_lb_ft2,
            "w_wing_lb": w_wing_lb,
            "composite_fraction": composite_fraction,
        },
    )


def calculate_fuselage_structural_weight(
    *,
    fuselage_length_m: float,
    fuselage_height_m: float,
    max_takeoff_weight_kg: float,
    mach_cruise: float = 0.8,
    n_limit: float = 9.0,
    inlet_installed: bool = True,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    if fuselage_length_m <= 0.0 or fuselage_height_m <= 0.0:
        raise ValueError("fuselage_length_m and fuselage_height_m must be positive.")
    if max_takeoff_weight_kg <= 0.0:
        raise ValueError("max_takeoff_weight_kg must be positive.")
    
    w_fw_lb = max_takeoff_weight_kg * 2.20462
    l_ft = fuselage_length_m * 3.28084
    h_ft = fuselage_height_m * 3.28084
    
    s_fuselage_gross_ft2 = pi * (h_ft / 2.0)**2 * l_ft
    
    q_pa = 0.5 * 1.225 * (mach_cruise * 340.0)**2
    q_lb_ft2 = q_pa * 0.020885
    
    k_inl = 1.25 if inlet_installed else 1.0
    
    w_fuselage_lb = 0.039 * (s_fuselage_gross_ft2)**1.2 * \
                       (w_fw_lb)**0.1 * \
                       (n_limit)**0.25 * \
                       (l_ft)**0.5 * \
                       (h_ft / l_ft)**0.1 * \
                       (q_lb_ft2 / 100.0)**0.28 * \
                       k_inl
    
    # Composite correction
    # Theory: 10% reduction for 55% usage
    reduction_factor = 0.10 * (composite_fraction / 0.55)
    w_fuselage_lb *= (1.0 - reduction_factor)

    w_fuselage_kg = w_fuselage_lb / 2.20462
    
    return StructuralWeightResult(
        w_struct_kg=w_fuselage_kg,
        details={
            "fuselage_length_m": fuselage_length_m,
            "fuselage_height_m": fuselage_height_m,
            "mach_cruise": mach_cruise,
            "n_limit": n_limit,
            "inlet_installed": inlet_installed,
            "k_inl": k_inl,
            "s_fuselage_gross_ft2": s_fuselage_gross_ft2,
            "w_fw_lb": w_fw_lb,
            "q_lb_ft2": q_lb_ft2,
            "w_fuselage_lb": w_fuselage_lb,
            "composite_fraction": composite_fraction,
        },
    )


def calculate_horizontal_tail_structural_weight(
    *,
    s_ht_m2: float,
    aspect_ratio_ht: float,
    tail_arm_m: float,
    t_c_ht: float,
    c_wing_m: float,
    max_takeoff_weight_kg: float,
    mach_cruise: float = 0.8,
    n_limit: float = 9.0,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    if s_ht_m2 <= 0.0 or aspect_ratio_ht <= 0.0:
        raise ValueError("s_ht_m2 and aspect_ratio_ht must be positive.")
    if tail_arm_m <= 0.0:
        raise ValueError("tail_arm_m must be positive.")
    if max_takeoff_weight_kg <= 0.0:
        raise ValueError("max_takeoff_weight_kg must be positive.")
    
    w_fw_lb = max_takeoff_weight_kg * 2.20462
    s_ht_ft2 = s_ht_m2 * 10.7639
    l_ht_ft = tail_arm_m * 3.28084
    c_wing_ft = c_wing_m * 3.28084
    
    k_var = 1.0
    
    w_ht_lb = 0.0079 * k_var * (1.0 + s_ht_ft2 / l_ht_ft)**(-0.25) * \
               (n_limit * w_fw_lb)**0.339 * \
               (s_ht_ft2)**0.886 * \
               (aspect_ratio_ht)**0.223 * \
               (t_c_ht / c_wing_ft)**(-0.317) * \
               (l_ht_ft / c_wing_ft)**(-0.119)
    
    # Composite correction
    # Theory: 25% reduction for 55% usage
    reduction_factor = 0.25 * (composite_fraction / 0.55)
    w_ht_lb *= (1.0 - reduction_factor)

    w_ht_kg = w_ht_lb / 2.20462
    
    return StructuralWeightResult(
        w_struct_kg=w_ht_kg,
        details={
            "s_ht_m2": s_ht_m2,
            "aspect_ratio_ht": aspect_ratio_ht,
            "tail_arm_m": tail_arm_m,
            "t_c_ht": t_c_ht,
            "c_wing_m": c_wing_m,
            "mach_cruise": mach_cruise,
            "n_limit": n_limit,
            "w_fw_lb": w_fw_lb,
            "w_ht_lb": w_ht_lb,
            "composite_fraction": composite_fraction,
        },
    )


def calculate_vertical_tail_structural_weight(
    *,
    s_vt_m2: float,
    aspect_ratio_vt: float,
    taper_ratio_vt: float,
    sweep_quarter_chord_deg: float,
    tail_arm_m: float,
    c_wing_m: float,
    max_takeoff_weight_kg: float,
    mach_cruise: float = 0.8,
    n_limit: float = 9.0,
    t_tail_mount: bool = False,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    if s_vt_m2 <= 0.0 or aspect_ratio_vt <= 0.0:
        raise ValueError("s_vt_m2 and aspect_ratio_vt must be positive.")
    if tail_arm_m <= 0.0:
        raise ValueError("tail_arm_m must be positive.")
    if max_takeoff_weight_kg <= 0.0:
        raise ValueError("max_takeoff_weight_kg must be positive.")
    
    w_fw_lb = max_takeoff_weight_kg * 2.20462
    s_vt_ft2 = s_vt_m2 * 10.7639
    l_t_ft = tail_arm_m * 3.28084
    c_wing_ft = c_wing_m * 3.28084
    
    sweep_rad = sweep_quarter_chord_deg * pi / 180.0
    
    h_t_over_h_v = 1.0 if t_tail_mount else 0.0
    
    q_pa = 0.5 * 1.225 * (mach_cruise * 340.0)**2
    q_lb_ft2 = q_pa * 0.020885
    
    s_r_over_s_vt = 0.3
    
    w_vt_lb = 0.0026 * (1.0 + h_t_over_h_v)**0.225 * \
              (n_limit * w_fw_lb)**0.556 * \
              (s_vt_ft2)**0.876 * \
              (aspect_ratio_vt)**0.354 * \
              (taper_ratio_vt)**0.019 * \
              (1.0 / cos(sweep_rad))**0.319 * \
              (s_r_over_s_vt)**0.139 * \
              (l_t_ft / c_wing_ft)**(-0.273)
    
    # Composite correction
    # Theory: 25% reduction for 55% usage
    reduction_factor = 0.25 * (composite_fraction / 0.55)
    w_vt_lb *= (1.0 - reduction_factor)

    w_vt_kg = w_vt_lb / 2.20462
    
    return StructuralWeightResult(
        w_struct_kg=w_vt_kg,
        details={
            "s_vt_m2": s_vt_m2,
            "aspect_ratio_vt": aspect_ratio_vt,
            "taper_ratio_vt": taper_ratio_vt,
            "sweep_quarter_chord_deg": sweep_quarter_chord_deg,
            "tail_arm_m": tail_arm_m,
            "c_wing_m": c_wing_m,
            "mach_cruise": mach_cruise,
            "n_limit": n_limit,
            "t_tail_mount": t_tail_mount,
            "h_t_over_h_v": h_t_over_h_v,
            "s_r_over_s_vt": s_r_over_s_vt,
            "w_fw_lb": w_fw_lb,
            "w_vt_lb": w_vt_lb,
            "composite_fraction": composite_fraction,
        },
    )


def calculate_landing_gear_weight(
    *,
    max_takeoff_weight_kg: float,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    if max_takeoff_weight_kg <= 0.0:
        raise ValueError("max_takeoff_weight_kg must be positive.")
    
    w_fw_lb = max_takeoff_weight_kg * 2.20462
    
    w_landing_gear_lb = 0.043 * (w_fw_lb)**0.882
    
    # Composite correction
    # Theory: 8% reduction for 55% usage
    reduction_factor = 0.08 * (composite_fraction / 0.55)
    w_landing_gear_lb *= (1.0 - reduction_factor)
    
    w_landing_gear_kg = w_landing_gear_lb / 2.20462
    
    return StructuralWeightResult(
        w_struct_kg=w_landing_gear_kg,
        details={
            "max_takeoff_weight_kg": max_takeoff_weight_kg,
            "w_fw_lb": w_fw_lb,
            "w_landing_gear_lb": w_landing_gear_lb,
            "composite_fraction": composite_fraction,
        },
    )


def generate_weight_breakdown(
    *,
    s_wing_m2: float,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    taper_ratio: float,
    fuselage_length_m: float,
    fuselage_height_m: float,
    s_ht_m2: float,
    aspect_ratio_ht: float,
    s_vt_m2: float,
    aspect_ratio_vt: float,
    taper_ratio_vt: float,
    sweep_vt_deg: float,
    tail_arm_m: float,
    c_wing_m: float,
    t_c: float,
    max_takeoff_weight_kg: float,
    mach_cruise: float = 0.8,
    n_limit: float = 9.0,
    variable_sweep: bool = False,
    inlet_installed: bool = True,
    t_tail_mount: bool = False,
    composite_fraction: float = 0.0,
) -> dict:
    wing_result = calculate_wing_structural_weight(
        s_wing_m2=s_wing_m2,
        aspect_ratio=aspect_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        taper_ratio=taper_ratio,
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        t_c=t_c,
        mach_cruise=mach_cruise,
        n_limit=n_limit,
        variable_sweep=variable_sweep,
        composite_fraction=composite_fraction,
    )
    
    fuselage_result = calculate_fuselage_structural_weight(
        fuselage_length_m=fuselage_length_m,
        fuselage_height_m=fuselage_height_m,
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        mach_cruise=mach_cruise,
        n_limit=n_limit,
        inlet_installed=inlet_installed,
        composite_fraction=composite_fraction,
    )
    
    ht_result = calculate_horizontal_tail_structural_weight(
        s_ht_m2=s_ht_m2,
        aspect_ratio_ht=aspect_ratio_ht,
        tail_arm_m=tail_arm_m,
        t_c_ht=t_c,
        c_wing_m=c_wing_m,
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        mach_cruise=mach_cruise,
        n_limit=n_limit,
        composite_fraction=composite_fraction,
    )
    
    vt_result = calculate_vertical_tail_structural_weight(
        s_vt_m2=s_vt_m2,
        aspect_ratio_vt=aspect_ratio_vt,
        taper_ratio_vt=taper_ratio_vt,
        sweep_quarter_chord_deg=sweep_vt_deg,
        tail_arm_m=tail_arm_m,
        c_wing_m=c_wing_m,
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        mach_cruise=mach_cruise,
        n_limit=n_limit,
        t_tail_mount=t_tail_mount,
        composite_fraction=composite_fraction,
    )
    
    gear_result = calculate_landing_gear_weight(
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        composite_fraction=composite_fraction,
    )
    
    total_structural_kg = (
        wing_result.w_struct_kg +
        fuselage_result.w_struct_kg +
        ht_result.w_struct_kg +
        vt_result.w_struct_kg +
        gear_result.w_struct_kg
    )
    
    return {
        "wing": wing_result,
        "fuselage": fuselage_result,
        "horizontal_tail": ht_result,
        "vertical_tail": vt_result,
        "landing_gear": gear_result,
        "total_structural_kg": total_structural_kg,
        "weight_fraction": {
            "wing": wing_result.w_struct_kg / total_structural_kg if total_structural_kg > 0 else 0,
            "fuselage": fuselage_result.w_struct_kg / total_structural_kg if total_structural_kg > 0 else 0,
            "horizontal_tail": ht_result.w_struct_kg / total_structural_kg if total_structural_kg > 0 else 0,
            "vertical_tail": vt_result.w_struct_kg / total_structural_kg if total_structural_kg > 0 else 0,
            "landing_gear": gear_result.w_struct_kg / total_structural_kg if total_structural_kg > 0 else 0,
        },
    }


def generate_weight_sensitivity(
    *,
    s_wing_m2: float,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    taper_ratio: float,
    fuselage_length_m: float,
    fuselage_height_m: float,
    s_ht_m2: float,
    s_vt_m2: float,
    tail_arm_m: float,
    c_wing_m: float,
    t_c: float,
    max_takeoff_weight_kg: float,
    mach_cruise: float = 0.8,
    n_limit: float = 9.0,
    mtow_range_kg: list[float] | None = None,
    composite_fraction: float = 0.0,
) -> dict:
    if mtow_range_kg is None:
        mtow_range_kg = [
            max_takeoff_weight_kg * 0.7,
            max_takeoff_weight_kg * 0.85,
            max_takeoff_weight_kg * 1.0,
            max_takeoff_weight_kg * 1.15,
        ]
    
    results = {
        "mtow_kg": mtow_range_kg,
        "wing_weight_kg": [],
        "fuselage_weight_kg": [],
        "ht_weight_kg": [],
        "vt_weight_kg": [],
        "gear_weight_kg": [],
        "total_structural_kg": [],
    }
    
    for mtow in mtow_range_kg:
        breakdown = generate_weight_breakdown(
            s_wing_m2=s_wing_m2,
            aspect_ratio=aspect_ratio,
            sweep_quarter_chord_deg=sweep_quarter_chord_deg,
            taper_ratio=taper_ratio,
            fuselage_length_m=fuselage_length_m,
            fuselage_height_m=fuselage_height_m,
            s_ht_m2=s_ht_m2,
            aspect_ratio_ht=4.0,
            s_vt_m2=s_vt_m2,
            aspect_ratio_vt=1.5,
            taper_ratio_vt=0.5,
            sweep_vt_deg=sweep_quarter_chord_deg,
            tail_arm_m=tail_arm_m,
            c_wing_m=c_wing_m,
            t_c=t_c,
            max_takeoff_weight_kg=mtow,
            mach_cruise=mach_cruise,
            n_limit=n_limit,
            composite_fraction=composite_fraction,
        )
        
        results["wing_weight_kg"].append(breakdown["wing"].w_struct_kg)
        results["fuselage_weight_kg"].append(breakdown["fuselage"].w_struct_kg)
        results["ht_weight_kg"].append(breakdown["horizontal_tail"].w_struct_kg)
        results["vt_weight_kg"].append(breakdown["vertical_tail"].w_struct_kg)
        results["gear_weight_kg"].append(breakdown["landing_gear"].w_struct_kg)
        results["total_structural_kg"].append(breakdown["total_structural_kg"])
    
    return results
