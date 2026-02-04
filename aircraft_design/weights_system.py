from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemWeightResult:
    w_system_kg: float
    details: dict


def calculate_fuel_system_weight(
    *,
    fuel_weight_kg: float,
    self_sealing: bool = False,
    aerial_refueling: bool = False,
    dump_system: bool = False,
    cg_control: bool = False,
) -> SystemWeightResult:
    if fuel_weight_kg <= 0.0:
        raise ValueError("fuel_weight_kg must be positive.")
    
    w_self_sealing = 0.0
    if self_sealing:
        w_self_sealing = 0.020 * fuel_weight_kg
    
    w_support = 0.016 * fuel_weight_kg
    
    w_aerial = 0.0
    if aerial_refueling:
        w_aerial = 0.006 * fuel_weight_kg
    
    w_dump = 0.0
    if dump_system:
        w_dump = 0.004 * fuel_weight_kg
    
    w_cg = 0.0
    if cg_control:
        w_cg = 0.008 * fuel_weight_kg
    
    w_fuel_system_kg = (
        w_self_sealing +
        w_support +
        w_aerial +
        w_dump +
        w_cg
    )
    
    return SystemWeightResult(
        w_system_kg=w_fuel_system_kg,
        details={
            "fuel_weight_kg": fuel_weight_kg,
            "self_sealing": self_sealing,
            "aerial_refueling": aerial_refueling,
            "dump_system": dump_system,
            "cg_control": cg_control,
            "w_self_sealing_kg": w_self_sealing,
            "w_support_kg": w_support,
            "w_aerial_kg": w_aerial,
            "w_dump_kg": w_dump,
            "w_cg_kg": w_cg,
        },
    )


def calculate_propulsion_system_weight(
    *,
    thrust_sl_n: float,
    engine_count: int = 2,
    control_system: bool = True,
    starting_system: bool = True,
) -> SystemWeightResult:
    if thrust_sl_n <= 0.0:
        raise ValueError("thrust_sl_n must be positive.")
    if engine_count <= 0:
        raise ValueError("engine_count must be positive.")
    
    thrust_sl_lb = thrust_sl_n * 0.224809
    
    w_engine = 0.013 * (thrust_sl_lb * engine_count)**0.8
    
    w_control = 0.0
    if control_system:
        w_control = 0.003 * (thrust_sl_lb * engine_count)**0.8
    
    w_starting = 0.0
    if starting_system:
        w_starting = 0.002 * (thrust_sl_lb * engine_count)**0.8
    
    w_propulsion_system_kg = (w_engine + w_control + w_starting) / 2.20462
    
    return SystemWeightResult(
        w_system_kg=w_propulsion_system_kg,
        details={
            "thrust_sl_n": thrust_sl_n,
            "engine_count": engine_count,
            "control_system": control_system,
            "starting_system": starting_system,
            "w_engine_lb": w_engine,
            "w_control_lb": w_control,
            "w_starting_lb": w_starting,
            "w_propulsion_system_kg": w_propulsion_system_kg,
        },
    )


def calculate_other_systems_weight(
    *,
    mtow_kg: float,
    mission_type: str = "fighter",
) -> SystemWeightResult:
    if mtow_kg <= 0.0:
        raise ValueError("mtow_kg must be positive.")
    
    mtow_lb = mtow_kg * 2.20462
    
    if mission_type == "fighter":
        w_control = 0.015 * mtow_lb
        w_instrument = 0.010 * mtow_lb
        w_avionics = 0.025 * mtow_lb
        w_equipment = 0.015 * mtow_lb
        w_air_conditioning = 0.010 * mtow_lb
        w_electrical = 0.010 * mtow_lb
    elif mission_type == "transport":
        w_control = 0.012 * mtow_lb
        w_instrument = 0.008 * mtow_lb
        w_avionics = 0.020 * mtow_lb
        w_equipment = 0.012 * mtow_lb
        w_air_conditioning = 0.008 * mtow_lb
        w_electrical = 0.008 * mtow_lb
    elif mission_type == "general_aviation":
        w_control = 0.010 * mtow_lb
        w_instrument = 0.008 * mtow_lb
        w_avionics = 0.015 * mtow_lb
        w_equipment = 0.010 * mtow_lb
        w_air_conditioning = 0.006 * mtow_lb
        w_electrical = 0.006 * mtow_lb
    else:
        raise ValueError("mission_type must be 'fighter', 'transport', or 'general_aviation'.")
    
    w_other_systems_kg = (
        w_control +
        w_instrument +
        w_avionics +
        w_equipment +
        w_air_conditioning +
        w_electrical
    ) / 2.20462
    
    return SystemWeightResult(
        w_system_kg=w_other_systems_kg,
        details={
            "mtow_kg": mtow_kg,
            "mission_type": mission_type,
            "w_control_lb": w_control,
            "w_instrument_lb": w_instrument,
            "w_avionics_lb": w_avionics,
            "w_equipment_lb": w_equipment,
            "w_air_conditioning_lb": w_air_conditioning,
            "w_electrical_lb": w_electrical,
            "w_other_systems_kg": w_other_systems_kg,
        },
    )


def generate_system_weight_breakdown(
    *,
    fuel_weight_kg: float,
    self_sealing: bool = False,
    aerial_refueling: bool = False,
    dump_system: bool = False,
    cg_control: bool = False,
    thrust_sl_n: float,
    engine_count: int = 2,
    control_system: bool = True,
    starting_system: bool = True,
    mtow_kg: float,
    mission_type: str = "fighter",
) -> dict:
    fuel_result = calculate_fuel_system_weight(
        fuel_weight_kg=fuel_weight_kg,
        self_sealing=self_sealing,
        aerial_refueling=aerial_refueling,
        dump_system=dump_system,
        cg_control=cg_control,
    )
    
    propulsion_result = calculate_propulsion_system_weight(
        thrust_sl_n=thrust_sl_n,
        engine_count=engine_count,
        control_system=control_system,
        starting_system=starting_system,
    )
    
    other_result = calculate_other_systems_weight(
        mtow_kg=mtow_kg,
        mission_type=mission_type,
    )
    
    total_systems_kg = (
        fuel_result.w_system_kg +
        propulsion_result.w_system_kg +
        other_result.w_system_kg
    )
    
    return {
        "fuel_system": fuel_result,
        "propulsion_system": propulsion_result,
        "other_systems": other_result,
        "total_systems_kg": total_systems_kg,
        "weight_fraction": {
            "fuel_system": fuel_result.w_system_kg / total_systems_kg,
            "propulsion_system": propulsion_result.w_system_kg / total_systems_kg,
            "other_systems": other_result.w_system_kg / total_systems_kg,
        },
    }
