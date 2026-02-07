from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt, cos, sin, tan


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
    n_limit: float = 4.5,  # GA/Transport default
    variable_sweep: bool = False,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    if s_wing_m2 <= 0.0 or aspect_ratio <= 0.0:
        raise ValueError("s_wing_m2 and aspect_ratio must be positive.")
    if max_takeoff_weight_kg <= 0.0:
        raise ValueError("max_takeoff_weight_kg must be positive.")
    
    # Raymer General Aviation Wing Weight Equation (Eq 15.46)
    # W_wing = 0.036 * S_w^0.758 * W_fw^0.0035 ... (The one in text was weird)
    # Let's use the standard GA formula:
    # W_wing = 0.0051 * (W_dg * Nz)^0.557 * S_w^0.649 * A^0.5 * (t/c)^-0.4 * (1+lambda)^0.1 * (cos(Lambda))^-1.0 * S_csw^0.1
    
    w_fw_lb = max_takeoff_weight_kg * 2.20462
    nz = 1.5 * n_limit
    s_w_ft2 = s_wing_m2 * 10.7639
    sweep_rad = sweep_quarter_chord_deg * pi / 180.0
    
    # S_csw (Control surface area) approx 0.1 * S_w? Factor S_csw^0.1 approx 1.0.
    
    w_wing_lb = 0.0051 * \
                (w_fw_lb * nz)**0.557 * \
                (s_w_ft2)**0.649 * \
                (aspect_ratio)**0.5 * \
                (t_c)**(-0.4) * \
                (1.0 + taper_ratio)**0.1 * \
                (1.0 / cos(sweep_rad))**1.0
                
    # Composite correction
    reduction_factor = 0.20 * (composite_fraction / 0.50) # Approx 20% savings for 50% composite
    w_wing_lb *= (1.0 - reduction_factor)

    w_wing_kg = w_wing_lb / 2.20462
    
    return StructuralWeightResult(
        w_struct_kg=w_wing_kg,
        details={
            "formula": "Raymer GA",
            "w_fw_lb": w_fw_lb,
            "w_wing_lb": w_wing_lb,
        },
    )


def calculate_fuselage_structural_weight(
    *,
    fuselage_length_m: float,
    fuselage_height_m: float, # Used as diameter/width
    max_takeoff_weight_kg: float,
    mach_cruise: float = 0.8,
    n_limit: float = 4.5,
    inlet_installed: bool = False,
    composite_fraction: float = 0.0,
    q_design_pa: float | None = None,
) -> StructuralWeightResult:
    """
    Calculates fuselage structural weight using Theory 03 (Nicolai-based) formula.
    
    Ref: docs/theory/03_weight_characteristics.md Section 2.2
    Formula: W_fus = 0.039 * S^1.2 * W^0.1 * Nz^0.25 * L^0.5 * (D/L)^0.1 * (q/100)^0.28
    """
    if fuselage_length_m <= 0.0 or fuselage_height_m <= 0.0:
         # Fallback to fraction if geometry is invalid (e.g. initial sizing)
         w_fus_kg = 0.12 * max_takeoff_weight_kg
         return StructuralWeightResult(
            w_struct_kg=w_fus_kg,
            details={"method": "Fraction 0.12 (Invalid Geometry)"},
        )

    w_fw_lb = max_takeoff_weight_kg * 2.20462
    nz = 1.5 * n_limit # Ultimate load factor
    l_fus_ft = fuselage_length_m * 3.28084
    d_ft = fuselage_height_m * 3.28084
    
    # Estimate S_gross (Approx cylinder surface)
    # S = pi * d * l * 0.85 (0.85 for tapering/non-cylindrical shapes)
    s_gross_ft2 = pi * d_ft * l_fus_ft * 0.85
    
    # Dynamic Pressure q
    # If not provided, estimate from Mach at Sea Level (Conservative max q)
    if q_design_pa is None:
        # q = 0.7 * P * M^2. P_sl_lb_ft2 = 2116.
        # q_lb_ft2 = 0.7 * 2116 * mach_cruise**2 = 1481 * M^2
        q_lb_ft2 = 1481.0 * (mach_cruise**2)
    else:
        q_lb_ft2 = q_design_pa * 0.0208854

    # Formula
    # W_fuselage = 0.039 * (S)^1.2 * (W)^0.1 * Nz^0.25 * L^0.5 * (d/L)^0.1 * (q / 100)^0.28
    
    # Note: S^1.2 seems high (Nicolai usually S^0.7-0.9), but following Theory 03 spec.
    # Check if result is reasonable. 
    
    term1 = 0.039
    term2 = s_gross_ft2**1.2
    term3 = w_fw_lb**0.1
    term4 = nz**0.25
    term5 = l_fus_ft**0.5
    term6 = (d_ft / l_fus_ft)**0.1
    term7 = (q_lb_ft2 / 100.0)**0.28
    
    w_fus_lb = term1 * term2 * term3 * term4 * term5 * term6 * term7
    
    # Composite correction
    reduction_factor = 0.20 * (composite_fraction / 0.50)
    w_fus_lb *= (1.0 - reduction_factor)
    
    w_fus_kg = w_fus_lb * 0.453592
    
    # Sanity Check: If result is wildly off (e.g. > 30% MTOW or < 5%), clamp or warn?
    # For Class I/II, let's just return it but log method.
    
    return StructuralWeightResult(
        w_struct_kg=w_fus_kg,
        details={
            "formula": "Theory 03 (Nicolai)",
            "w_fw_lb": w_fw_lb,
            "w_fus_lb": w_fus_lb,
            "s_gross_ft2": s_gross_ft2,
            "q_lb_ft2": q_lb_ft2,
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
    n_limit: float = 4.5,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    # Raymer GA
    # W_ht = 0.016 * (N * W)^0.414 * S_ht^0.896 * ...
    
    w_fw_lb = max_takeoff_weight_kg * 2.20462
    nz = 1.5 * n_limit
    s_ht_ft2 = s_ht_m2 * 10.7639
    
    w_ht_lb = 0.016 * (nz * w_fw_lb)**0.414 * (s_ht_ft2)**0.896 * \
              (100.0 * t_c_ht)**(-0.12) * \
              (aspect_ratio_ht)**0.043 # Weak dependence
              
    w_ht_kg = w_ht_lb / 2.20462
    return StructuralWeightResult(w_struct_kg=w_ht_kg, details={})

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
    n_limit: float = 4.5,
    t_tail_mount: bool = False,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    # Raymer GA
    # W_vt = 0.073 * (1 + 0.2 Ht/Hv) * (N * W)^0.376 * S_vt^0.873
    
    w_fw_lb = max_takeoff_weight_kg * 2.20462
    nz = 1.5 * n_limit
    s_vt_ft2 = s_vt_m2 * 10.7639
    
    ht_hv_factor = 1.0 if not t_tail_mount else 1.2
    
    w_vt_lb = 0.073 * ht_hv_factor * \
              (nz * w_fw_lb)**0.376 * \
              (s_vt_ft2)**0.873 * \
              (aspect_ratio_vt)**0.354 * \
              (taper_ratio_vt)**0.039
              
    w_vt_kg = w_vt_lb / 2.20462
    return StructuralWeightResult(w_struct_kg=w_vt_kg, details={})

def calculate_landing_gear_weight(
    *,
    max_takeoff_weight_kg: float,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    # Raymer GA
    # W_main = 0.095 * (N_land * W)^0.768 ...
    # Simplified: 5.7% of MTOW (Raymer Table)
    
    w_lg_kg = 0.057 * max_takeoff_weight_kg
    return StructuralWeightResult(w_struct_kg=w_lg_kg, details={})

def generate_weight_breakdown(
    *,
    s_wing_m2: float,
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    taper_ratio: float,
    fuselage_length_m: float,
    fuselage_height_m: float,
    s_ht_m2: float,
    s_vt_m2: float,
    max_takeoff_weight_kg: float,
    n_limit: float = 9.0,
) -> dict:
    # Wrapper for orchestrator or tests
    w_wing = calculate_wing_structural_weight(
        s_wing_m2=s_wing_m2, aspect_ratio=aspect_ratio, sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        taper_ratio=taper_ratio, max_takeoff_weight_kg=max_takeoff_weight_kg, n_limit=n_limit
    )
    w_fus = calculate_fuselage_structural_weight(
        fuselage_length_m=fuselage_length_m, fuselage_height_m=fuselage_height_m,
        max_takeoff_weight_kg=max_takeoff_weight_kg, n_limit=n_limit
    )
    w_ht = calculate_horizontal_tail_structural_weight(
        s_ht_m2=s_ht_m2, aspect_ratio_ht=4.0, tail_arm_m=fuselage_length_m*0.45, t_c_ht=0.10, c_wing_m=1.0,
        max_takeoff_weight_kg=max_takeoff_weight_kg, n_limit=n_limit
    )
    w_vt = calculate_vertical_tail_structural_weight(
        s_vt_m2=s_vt_m2, aspect_ratio_vt=1.5, taper_ratio_vt=0.5, sweep_quarter_chord_deg=25.0,
        tail_arm_m=fuselage_length_m*0.45, c_wing_m=1.0, max_takeoff_weight_kg=max_takeoff_weight_kg, n_limit=n_limit
    )
    w_lg = calculate_landing_gear_weight(max_takeoff_weight_kg=max_takeoff_weight_kg)
    
    return {
        "wing": w_wing.w_struct_kg,
        "fuselage": w_fus.w_struct_kg,
        "ht": w_ht.w_struct_kg,
        "vt": w_vt.w_struct_kg,
        "landing_gear": w_lg.w_struct_kg,
    }
