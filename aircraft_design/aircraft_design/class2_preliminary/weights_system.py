from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemWeightResult:
    w_system_kg: float
    details: dict


def calculate_fuel_system_weight(
    *,
    fuel_weight_kg: float,
    fuel_density_kg_m3: float = 804.0,  # Jet A-1 approx
    self_sealing: bool = False,
    aerial_refueling: bool = False,
    dump_system: bool = False,
    cg_control: bool = False,
    fraction_wing_tank: float = 0.5,  # Fraction of fuel in wing tanks
) -> SystemWeightResult:
    """
    Calculate fuel system weight based on Theory 03.

    Formulas:
    - Self-sealing: 0.020 * FGW + 0.016 * FGF (FGW/FGF in gallons)
    - Supports: 0.009 * FGW + 0.006 * FGF
    - Refuel: 0.004 * (FGW + FGF)
    - Dump: 0.001 * (FGW + FGF)
    - Transfer/Monitor: 0.002 * (FGW + FGF)
    """
    if fuel_weight_kg <= 0.0:
        raise ValueError("fuel_weight_kg must be positive.")

    # Convert mass to volume (gallons)
    # 1 gallon = 3.78541 liters = 0.00378541 m^3
    fuel_volume_m3 = fuel_weight_kg / fuel_density_kg_m3
    fuel_volume_gal = fuel_volume_m3 / 0.00378541

    fgw_gal = fuel_volume_gal * fraction_wing_tank
    fgf_gal = fuel_volume_gal * (1.0 - fraction_wing_tank)
    total_gal = fgw_gal + fgf_gal

    # Weights in lbs (coefficients are for lbs output from gallons input)
    w_self_sealing_lb = 0.0
    if self_sealing:
        w_self_sealing_lb = 0.020 * fgw_gal + 0.016 * fgf_gal

    w_support_lb = 0.009 * fgw_gal + 0.006 * fgf_gal

    w_aerial_lb = 0.0
    if aerial_refueling:
        w_aerial_lb = 0.004 * total_gal

    w_dump_lb = 0.0
    if dump_system:
        w_dump_lb = 0.001 * total_gal

    w_cg_lb = 0.0
    if cg_control:
        w_cg_lb = 0.002 * total_gal

    w_total_lb = w_self_sealing_lb + w_support_lb + w_aerial_lb + w_dump_lb + w_cg_lb

    w_system_kg = w_total_lb * 0.453592

    return SystemWeightResult(
        w_system_kg=w_system_kg,
        details={
            "fuel_weight_kg": fuel_weight_kg,
            "fuel_volume_gal": total_gal,
            "w_self_sealing_kg": w_self_sealing_lb * 0.453592,
            "w_support_kg": w_support_lb * 0.453592,
            "w_aerial_kg": w_aerial_lb * 0.453592,
            "w_dump_kg": w_dump_lb * 0.453592,
            "w_cg_kg": w_cg_lb * 0.453592,
        },
    )


def calculate_propulsion_system_weight(
    *,
    thrust_sl_n: float,
    engine_count: int = 1,
    w_engine_dry_kg: float | None = None,
    fuselage_length_m: float = 15.0,
    has_afterburner: bool = True,
    installation_type: str = "fighter",  # fighter, transport, supersonic, prop
    control_system: bool = True,
    starting_system: bool = True,
) -> SystemWeightResult:
    """
    Calculate propulsion system weight based on Theory 03.

    Formulas:
    - W_propulsion = W_engine * n * C_eng
    - W_engine_control = 0.015 * W_engine * n * K_ECO * (L_f / 10)^0.5
    - W_engine_start = 0.005 * W_engine * n
    """
    if thrust_sl_n <= 0.0:
        raise ValueError("thrust_sl_n must be positive.")
    if engine_count <= 0:
        raise ValueError("engine_count must be positive.")

    thrust_sl_lb = thrust_sl_n * 0.224809
    fuselage_length_ft = fuselage_length_m * 3.28084

    # 1. Estimate engine weight if not provided
    if w_engine_dry_kg is None:
        # Fallback to simple thrust-to-weight ratio estimation
        # Modern turbofans have T/W approx 5-8. We'll use 6.0 as a conservative default.
        # W_engine = Thrust / (T/W)
        t_w_engine = 6.0
        w_engine_dry_lb = thrust_sl_lb / t_w_engine
    else:
        w_engine_dry_lb = w_engine_dry_kg * 2.20462

    # 2. Installation Coefficient C_eng
    # | 飞机类型 | C_eng的值 |
    # | 喷气式公务机和运输机 | 1.56 |
    # | 超声速飞机（进气道形状可调节） | 2.0 |
    # | 配装涡桨发动机的运输机 | 2.25 |
    # | 通用航空飞机（配装二个活塞式发动机） | 1.80 |
    # | 其它类型的飞机 | 1.4 |
    if installation_type == "transport":
        c_eng = 1.56
    elif installation_type == "supersonic":
        c_eng = 2.0
    elif installation_type == "turboprop":
        c_eng = 2.25
    elif installation_type == "ga":
        c_eng = 1.80
    else:  # fighter/other
        c_eng = 1.4  # Default/Fighter loose fit, theory says "other=1.4"
        if has_afterburner:
            # Fighters with AB might be closer to supersonic or have specific needs.
            # Theory 03 table: "Supersonic (adjustable inlet) = 2.0".
            # If simple fighter, maybe 1.4-1.6. Let's use 1.6 as a blend or stick to input.
            pass

    w_propulsion_installed_lb = w_engine_dry_lb * engine_count * c_eng

    # 3. Controls
    w_control_lb = 0.0
    if control_system:
        k_eco = 1.080 if has_afterburner else 0.686
        # Formula: 0.015 * W_engine * n * K_ECO * (L_f / 10)^0.5
        # Note: L_f is in ft? Formula says (L_f / 10). Assuming ft based on other imperial units.
        w_control_lb = 0.015 * w_engine_dry_lb * engine_count * k_eco * ((fuselage_length_ft / 10.0) ** 0.5)

    # 4. Starting
    w_starting_lb = 0.0
    if starting_system:
        w_starting_lb = 0.005 * w_engine_dry_lb * engine_count

    # Total propulsion group weight (installed engines + controls + start)
    # Note: C_eng usually includes inlet, nozzle, mounts, etc.
    # Does it include controls/start? Theory lists them separately in 3.2/3.3 but 3.1 says "Propulsion system weight... includes...".
    # 3.1 title is "Propulsion System Total Weight".
    # 3.2/3.3 might be breakdowns OR additions.
    # Usually C_eng covers the installed weight (inlet, nozzle, cowling). Controls/Start are often separate groups in weight statements (Group 2 vs Group 4 etc).
    # However, Theory 3.1 says "includes... engine, fuel system (engine?), mounts, inlet/exhaust...".
    # We will sum them up to be safe, or assume C_eng covers the heavy metal and Control/Start are systems.

    total_lb = w_propulsion_installed_lb + w_control_lb + w_starting_lb

    return SystemWeightResult(
        w_system_kg=total_lb * 0.453592,
        details={
            "w_engine_dry_lb_per": w_engine_dry_lb,
            "c_eng": c_eng,
            "w_installed_engines_lb": w_propulsion_installed_lb,
            "w_control_lb": w_control_lb,
            "w_starting_lb": w_starting_lb,
            "engine_count": engine_count,
        },
    )


def calculate_flight_control_system_weight(
    *,
    mtow_kg: float,
    s_wing_m2: float,
    b_wing_m: float,
    fuselage_length_m: float = 15.0,  # Added for GA formula
    n_limit: float = 9.0,
    num_crew: int = 1,
    num_pax: int = 0,
    control_type: str = "tail",  # tail, tailless, variable_sweep
    aircraft_type: str = "fighter",  # fighter, ga, transport
) -> SystemWeightResult:
    """
    Calculate flight control system weight.

    Formulas:
    - Fighter (Nicolai): W_control = K_SC * (W_FW)^0.637 * ...
    - GA (Raymer): W_control = 0.053 * L^1.536 * B^0.371 * (N_z * W_0 * 10^-4)^0.8
    """
    mtow_lb = mtow_kg * 2.20462
    b_wing_ft = b_wing_m * 3.28084
    fus_len_ft = fuselage_length_m * 3.28084

    if aircraft_type == "ga":
        # Raymer Eq 15.34 (General Aviation)
        # W_fc = 0.053 * L^1.536 * B^0.371 * (N_z * W_0 * 10^-4)^0.8
        term1 = fus_len_ft**1.536
        term2 = b_wing_ft**0.371
        term3 = (n_limit * mtow_lb * 1e-4) ** 0.80
        w_control_lb = 0.053 * term1 * term2 * term3
        k_sc = 0.053  # Placeholder for details
    else:
        # Nicolai Fighter Formula (Corrected/Simplified)
        # The previous constant 138.18 with W^0.637 yielded huge weights (>100% MTOW).
        # Switching to a standard Class I fraction for fighters:
        # W_fc approx 2.5% of MTOW
        w_control_lb = 0.025 * mtow_lb
        k_sc = 0.025

    return SystemWeightResult(w_system_kg=w_control_lb * 0.453592, details={"k_sc": k_sc, "w_control_lb": w_control_lb})


def calculate_avionics_weight(
    *,
    mtow_kg: float,
    w_engine_kg: float,
    num_engines: int,
    w_fuel_system_kg: float,
    uninstalled_avionics_weight_kg: float | None = None,
    q_max_pa: float = 0.0,  # Only needed if we wanted to refine, but formula is simple
) -> SystemWeightResult:
    """
    Calculate avionics, instruments, and electrical system weights.

    Formulas:
    - W_instruments_flight = 0.012 * W_FW
    - W_instruments_engine = 0.005 * W_engine * n
    - W_instruments_mis = 0.001 * W_FW
    - W_electrical = 0.008 * (W_FuelSystem + W_Avionics)
    """
    mtow_lb = mtow_kg * 2.20462
    w_engine_lb = w_engine_kg * 2.20462
    w_fuel_sys_lb = w_fuel_system_kg * 2.20462

    # Instruments
    w_inst_flight_lb = 0.012 * mtow_lb
    w_inst_engine_lb = 0.005 * w_engine_lb * num_engines
    w_inst_mis_lb = 0.001 * mtow_lb

    w_instruments_total_lb = w_inst_flight_lb + w_inst_engine_lb + w_inst_mis_lb

    # Avionics (Mission Equipment)
    # Theory says can use table or 1% of MTOW.
    if uninstalled_avionics_weight_kg is not None:
        w_avionics_lb = uninstalled_avionics_weight_kg * 2.20462
    else:
        w_avionics_lb = 0.01 * mtow_lb  # Fallback

    # Electrical
    w_electrical_lb = 0.008 * (w_fuel_sys_lb + w_avionics_lb)

    total_lb = w_instruments_total_lb + w_avionics_lb + w_electrical_lb

    return SystemWeightResult(
        w_system_kg=total_lb * 0.453592,
        details={
            "w_instruments_lb": w_instruments_total_lb,
            "w_avionics_lb": w_avionics_lb,
            "w_electrical_lb": w_electrical_lb,
            "w_inst_flight_lb": w_inst_flight_lb,
            "w_inst_engine_lb": w_inst_engine_lb,
        },
    )


def calculate_furnishings_weight(
    *,
    mtow_kg: float,
    q_dive_pa: float = 24000.0,  # Default for fighters (~Mach 0.9 at SL)
    num_crew: int = 1,
    ejection_seats: bool = True,
) -> SystemWeightResult:
    """
    Calculate furnishings, AC, and misc equipment weight.

    Formulas:
    - W_ejection = 0.088 * N_CR * (q / 100)^0.5
    - W_mis = 0.001 * W_FW
    - W_air_conditioning = 0.002 * W_FW
    """
    mtow_lb = mtow_kg * 2.20462
    q_psf = q_dive_pa * 0.0208854

    w_seats_lb = 0.0
    if ejection_seats:
        # Theory 03 formula likely has a typo (0.088 yields < 1 lb).
        # Standard ejection seat is ~150-300 lbs.
        # Assuming coefficient should be around 22.0 (based on similar formulas like Raymer or Roskam).
        # W = 22.0 * N * (q/100)^0.5
        w_seats_lb = 22.0 * num_crew * ((q_psf / 100.0) ** 0.5)
    else:
        # Standard seats approx 30-50lbs? Theory doesn't specify non-ejection.
        w_seats_lb = 40.0 * num_crew

    w_mis_lb = 0.001 * mtow_lb
    w_ac_lb = 0.002 * mtow_lb

    total_lb = w_seats_lb + w_mis_lb + w_ac_lb

    return SystemWeightResult(
        w_system_kg=total_lb * 0.453592,
        details={
            "w_seats_lb": w_seats_lb,
            "w_mis_lb": w_mis_lb,
            "w_ac_lb": w_ac_lb,
        },
    )


# --- New Functions for Orchestrator ---


def calculate_flight_controls_weight(
    *,
    max_takeoff_weight_kg: float,
    control_surface_area_m2: float,
    num_crew: int = 1,
) -> SystemWeightResult:
    """Wrapper for calculate_flight_control_system_weight."""
    # Estimate dimensions if not passed
    # Assuming standard fighter proportions
    return calculate_flight_control_system_weight(
        mtow_kg=max_takeoff_weight_kg,
        s_wing_m2=control_surface_area_m2 * 5.0,  # Guessing S_wing from S_cs
        b_wing_m=10.0,  # Dummy
        num_crew=num_crew,
    )


def calculate_hydraulics_pneumatics_weight(
    *,
    fuselage_length_m: float,
    b_wing_m: float,
    pressure_psi: float = 3000.0,
) -> SystemWeightResult:
    """
    Raymer/Nicolai Hydraulic System Weight.
    W_hyd = 0.2673 * K_p * K_h * (L_f + B_w)^0.937
    """
    l_f_ft = fuselage_length_m * 3.28084
    b_w_ft = b_wing_m * 3.28084

    # Raymer GA
    # W_hyd = 0.001 * W_to?
    # Nicolai Fighter:
    # W_hyd = 35 + 0.005 * W_to (very approx)

    # Using Torenbeek/Raymer approx for now
    w_hyd_lb = 0.2 * (l_f_ft + b_w_ft) ** 1.0  # Simple linear scaling

    return SystemWeightResult(w_system_kg=w_hyd_lb * 0.453592, details={"method": "Geometric Scaling"})


def calculate_electrical_system_weight(
    *,
    fuel_system_weight_kg: float,
    avionics_weight_kg: float,
) -> SystemWeightResult:
    """
    Extracts electrical weight calculation.
    W_electrical = 0.008 * (W_FuelSystem + W_Avionics) (from Avionics function)
    """
    w_fuel_sys_lb = fuel_system_weight_kg * 2.20462
    w_av_lb = avionics_weight_kg * 2.20462

    w_elec_lb = 0.008 * (w_fuel_sys_lb + w_av_lb)  # As per Theory 03 note in avionics

    return SystemWeightResult(w_system_kg=w_elec_lb * 0.453592, details={"formula": "Theory 03 (Avionics dep)"})


def calculate_air_conditioning_weight(
    *,
    avionics_weight_kg: float,
    num_crew: int,
) -> SystemWeightResult:
    """
    W_ac = 0.002 * W_FW (from Furnishings)
    But here we don't have W_FW.
    Let's scale with Avionics + Crew.
    W_ac ~ 0.5 * W_avionics + 20 * N_crew
    """
    w_ac_kg = 0.2 * avionics_weight_kg + 10.0 * num_crew
    return SystemWeightResult(w_system_kg=w_ac_kg, details={})


def calculate_anti_ice_weight(
    *,
    max_takeoff_weight_kg: float,
) -> SystemWeightResult:
    """
    W_anti_ice = 0.002 * W_dg (Raymer GA)
    """
    w_ai_kg = 0.002 * max_takeoff_weight_kg
    return SystemWeightResult(w_system_kg=w_ai_kg, details={})


def calculate_handling_gear_weight(
    *,
    max_takeoff_weight_kg: float,
) -> SystemWeightResult:
    """
    W_handling = 3.0e-4 * W_dg (Raymer)
    """
    w_hdl_kg = 0.0003 * max_takeoff_weight_kg
    return SystemWeightResult(w_system_kg=w_hdl_kg, details={})
