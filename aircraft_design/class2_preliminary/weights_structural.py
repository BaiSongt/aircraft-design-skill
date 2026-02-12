from __future__ import annotations

from dataclasses import dataclass
from math import pi, cos


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

    w_wing_lb = (
        0.0051
        * (w_fw_lb * nz) ** 0.557
        * (s_w_ft2) ** 0.649
        * (aspect_ratio) ** 0.5
        * (t_c) ** (-0.4)
        * (1.0 + taper_ratio) ** 0.1
        * (1.0 / cos(sweep_rad)) ** 1.0
    )

    # Composite correction (Theory 03: 25% reduction for 55% utilization)
    reduction_factor = 0.25 * (composite_fraction / 0.55)
    w_wing_lb *= 1.0 - reduction_factor

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
    fuselage_height_m: float,  # Used as diameter/width
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
    nz = 1.5 * n_limit  # Ultimate load factor
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
    term6 = (d_ft / l_fus_ft) ** 0.1
    term7 = (q_lb_ft2 / 100.0) ** 0.28

    w_fus_lb = term1 * term2 * term3 * term4 * term5 * term6 * term7

    # Composite correction (Theory 03: 10% reduction for 55% utilization)
    reduction_factor = 0.10 * (composite_fraction / 0.55)
    w_fus_lb *= 1.0 - reduction_factor

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

    w_ht_lb = (
        0.016 * (nz * w_fw_lb) ** 0.414 * (s_ht_ft2) ** 0.896 * (100.0 * t_c_ht) ** (-0.12) * (aspect_ratio_ht) ** 0.043
    )  # Weak dependence

    # Composite correction (Theory 03: 25% reduction for 55% utilization)
    reduction_factor = 0.25 * (composite_fraction / 0.55)
    w_ht_lb *= 1.0 - reduction_factor

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

    w_vt_lb = (
        0.073
        * ht_hv_factor
        * (nz * w_fw_lb) ** 0.376
        * (s_vt_ft2) ** 0.873
        * (aspect_ratio_vt) ** 0.354
        * (taper_ratio_vt) ** 0.039
    )

    # Composite correction (Theory 03: 25% reduction for 55% utilization)
    reduction_factor = 0.25 * (composite_fraction / 0.55)
    w_vt_lb *= 1.0 - reduction_factor

    w_vt_kg = w_vt_lb / 2.20462
    return StructuralWeightResult(w_struct_kg=w_vt_kg, details={})


def calculate_landing_gear_weight(
    *,
    max_takeoff_weight_kg: float,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    """
    Calculates landing gear weight using Theory 03 (Nicolai) formula.

    Formula: W_landing_gear = 0.043 * (W_FW)^0.882
    """
    if max_takeoff_weight_kg <= 0.0:
        return StructuralWeightResult(w_struct_kg=0.0, details={})

    w_fw_lb = max_takeoff_weight_kg * 2.20462

    # Nicolai Formula
    w_lg_lb = 0.043 * (w_fw_lb) ** 0.882

    # Composite correction (Theory 03: 8% reduction for 55% utilization)
    reduction_factor = 0.08 * (composite_fraction / 0.55)
    w_lg_lb *= 1.0 - reduction_factor

    w_lg_kg = w_lg_lb * 0.453592

    return StructuralWeightResult(
        w_struct_kg=w_lg_kg,
        details={
            "formula": "Theory 03 (Nicolai)",
            "w_fw_lb": w_fw_lb,
            "w_lg_lb": w_lg_lb,
        },
    )


def calculate_nacelle_group_weight(
    *,
    thrust_sl_n: float,
    num_engines: int,
    max_takeoff_weight_kg: float,
    is_supersonic: bool = False,
) -> StructuralWeightResult:
    """
    Calculates nacelle group weight.

    Formula (Nicolai / Raymer approx):
    W_nacelle = 0.065 * W_engine_dry (approx) or specific formula.
    Raymer GA: 0.6724 * K_n * N_L^0.1 * W_eng^0.598...
    Nicolai Theory 03: Part of propulsion group C_eng?
    Theory 03 says "Propulsion System Total Weight" includes inlet/nozzle.
    If we use C_eng in weights_system.py, we might double count if we add nacelle here.
    However, "Nacelle Group" is usually Group 1 (Structure).
    Let's assume for this model, if C_eng is used in Propulsion System, Nacelle Structure is minimal or included there.
    BUT, standard weight breakdown usually separates Nacelle (Structure) from Propulsion (System).
    Let's provide a specific formula for Nacelle Structure and ensure C_eng in Propulsion doesn't double count.

    Raymer Fighter:
    W_nacelle = 0.6724 * K_n * N_L^0.1 * S_n^0.294 * N_z^0.119 * W_eng^0.611
    """
    # For now, let's use a simple fraction of engine weight if geometric details are missing
    # W_nacelle ~ 0.04 * MTOW or 0.15 * W_engine

    # Let's use a simplified Raymer correlation
    # W_nacelle_lb = 0.15 * W_engine_lb (approx)

    # We need W_engine. Estimate from Thrust if not passed?
    # T/W_eng ~ 6.0
    w_engine_lb = (thrust_sl_n * 0.224809) / 6.0 / num_engines
    if is_supersonic:
        # Supersonic nacelles are heavier
        w_nac_lb = 0.3 * w_engine_lb * num_engines
    else:
        w_nac_lb = 0.15 * w_engine_lb * num_engines

    w_nac_kg = w_nac_lb * 0.453592

    return StructuralWeightResult(
        w_struct_kg=w_nac_kg, details={"method": "Factor of Engine Weight", "w_engine_est_lb": w_engine_lb}
    )


def calculate_tail_structural_weight(
    *,
    s_ht_m2: float,
    s_vt_m2: float,
    max_takeoff_weight_kg: float,
    n_limit: float = 4.5,
    composite_fraction: float = 0.0,
) -> StructuralWeightResult:
    """
    Wrapper to calculate total tail weight (HT + VT).
    """
    # Assumptions for detailed calls
    # L_tail ~ derived from earlier?
    # We just need a reasonable estimate.

    w_ht = calculate_horizontal_tail_structural_weight(
        s_ht_m2=s_ht_m2,
        aspect_ratio_ht=4.0,  # Default
        tail_arm_m=1.0,  # Not used strongly in GA formula
        t_c_ht=0.10,
        c_wing_m=1.0,
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        n_limit=n_limit,
        composite_fraction=composite_fraction,
    )

    w_vt = calculate_vertical_tail_structural_weight(
        s_vt_m2=s_vt_m2,
        aspect_ratio_vt=1.5,
        taper_ratio_vt=0.5,
        sweep_quarter_chord_deg=30.0,
        tail_arm_m=1.0,
        c_wing_m=1.0,
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        n_limit=n_limit,
        composite_fraction=composite_fraction,
    )

    total = w_ht.w_struct_kg + w_vt.w_struct_kg
    return StructuralWeightResult(w_struct_kg=total, details={"w_ht_kg": w_ht.w_struct_kg, "w_vt_kg": w_vt.w_struct_kg})


def calculate_surface_controls_weight(
    *,
    max_takeoff_weight_kg: float,
) -> StructuralWeightResult:
    """
    Calculates surface controls weight (if not included in wing/tail).
    Usually these are Actuators (System) or Surface Structure (Wing).
    We'll return 0 for now to avoid double counting if unclear,
    or a small fraction.
    """
    return StructuralWeightResult(w_struct_kg=0.0, details={"note": "Assumed in Wing/Systems"})


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
        s_wing_m2=s_wing_m2,
        aspect_ratio=aspect_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        taper_ratio=taper_ratio,
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        n_limit=n_limit,
    )
    w_fus = calculate_fuselage_structural_weight(
        fuselage_length_m=fuselage_length_m,
        fuselage_height_m=fuselage_height_m,
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        n_limit=n_limit,
    )
    w_ht = calculate_horizontal_tail_structural_weight(
        s_ht_m2=s_ht_m2,
        aspect_ratio_ht=4.0,
        tail_arm_m=fuselage_length_m * 0.45,
        t_c_ht=0.10,
        c_wing_m=1.0,
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        n_limit=n_limit,
    )
    w_vt = calculate_vertical_tail_structural_weight(
        s_vt_m2=s_vt_m2,
        aspect_ratio_vt=1.5,
        taper_ratio_vt=0.5,
        sweep_quarter_chord_deg=25.0,
        tail_arm_m=fuselage_length_m * 0.45,
        c_wing_m=1.0,
        max_takeoff_weight_kg=max_takeoff_weight_kg,
        n_limit=n_limit,
    )
    w_lg = calculate_landing_gear_weight(max_takeoff_weight_kg=max_takeoff_weight_kg)

    return {
        "wing": w_wing.w_struct_kg,
        "fuselage": w_fus.w_struct_kg,
        "ht": w_ht.w_struct_kg,
        "vt": w_vt.w_struct_kg,
        "landing_gear": w_lg.w_struct_kg,
    }
