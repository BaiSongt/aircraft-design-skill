from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..common.atmosphere import isa_tropopause


@dataclass(frozen=True)
class RotorAerodynamics:
    thrust: float
    torque: float
    power: float
    induced_velocity: float
    figure_of_merit: float
    power_loading: float
    disk_loading: float


@dataclass(frozen=True)
class RotorPerformance:
    hover_ceiling: float
    max_forward_speed: float
    climb_rate: float
    endurance: float
    range: float
    service_ceiling: float
    max_continuous_power: float


def calculate_rotor_aerodynamics(
    *,
    rotor_diameter: float,
    rotor_speed_rpm: float,
    blade_pitch_deg: float,
    num_blades: int = 4,
    air_density: float = 1.225,
    altitude_m: float = 0.0,
    isa_delta_c: float = 0.0,
) -> RotorAerodynamics:
    if rotor_diameter <= 0.0:
        raise ValueError("rotor_diameter must be positive.")
    if rotor_speed_rpm <= 0.0:
        raise ValueError("rotor_speed_rpm must be positive.")
    if num_blades < 2:
        raise ValueError("num_blades must be >= 2.")

    atm = isa_tropopause(altitude_m, delta_t_k=float(isa_delta_c))
    rho = atm.rho_kg_m3

    rotor_radius = rotor_diameter / 2.0
    rotor_area = pi * rotor_radius**2
    tip_speed = rotor_speed_rpm * 2.0 * pi / 60.0 * rotor_radius

    omega = rotor_speed_rpm * 2.0 * pi / 60.0

    blade_pitch_rad = blade_pitch_deg * pi / 180.0

    solidity = (num_blades * blade_pitch_rad) / (pi * rotor_diameter)

    ct = 0.008 + 0.006 * solidity
    cq = 0.004 + 0.003 * solidity

    induced_velocity = sqrt((ct * 9.81) / (2.0 * solidity))

    thrust = ct * rho * rotor_area * (tip_speed**2)
    torque = cq * rho * rotor_area * rotor_radius * (tip_speed**2)
    power = torque * omega

    figure_of_merit = thrust / power

    power_loading = power / rotor_area
    disk_loading = thrust / rotor_area

    return RotorAerodynamics(
        thrust=thrust,
        torque=torque,
        power=power,
        induced_velocity=induced_velocity,
        figure_of_merit=figure_of_merit,
        power_loading=power_loading,
        disk_loading=disk_loading,
    )


def calculate_rotor_performance(
    *,
    rotor_aero: RotorAerodynamics,
    gross_weight: float,
    engine_power: float,
    drag_coefficient: float = 0.02,
    parasite_area: float = 10.0,
    fuel_capacity: float = 1000.0,
    sfc: float = 0.5,
    altitude_m: float = 0.0,
    isa_delta_c: float = 0.0,
) -> RotorPerformance:
    if gross_weight <= 0.0:
        raise ValueError("gross_weight must be positive.")
    if engine_power <= 0.0:
        raise ValueError("engine_power must be positive.")

    atm = isa_tropopause(altitude_m, delta_t_k=float(isa_delta_c))
    rho = atm.rho_kg_m3

    thrust_available = rotor_aero.thrust

    hover_thrust_required = gross_weight * 9.81
    hover_ceiling = 0.0
    if thrust_available > hover_thrust_required:
        excess_thrust = thrust_available - hover_thrust_required
        climb_rate = excess_thrust / gross_weight * 60.0
        hover_ceiling = climb_rate * 60.0 / 3.0
    else:
        hover_ceiling = 0.0

    max_continuous_power = engine_power * 0.85

    max_forward_speed = 0.0
    for speed in np.linspace(0, 100, 100):
        drag = 0.5 * drag_coefficient * parasite_area * rho * speed**2
        thrust_required = drag + gross_weight * 9.81 * 0.1

        if thrust_available > thrust_required:
            max_forward_speed = speed
            break

    service_ceiling = max_forward_speed * 60.0 / 3.0

    endurance = 0.0
    range_km = 0.0

    cruise_speed = max_forward_speed * 0.7
    cruise_power = 0.5 * drag_coefficient * parasite_area * rho * cruise_speed**3

    if engine_power > cruise_power:
        excess_power = engine_power - cruise_power
        endurance_hours = fuel_capacity / (sfc * excess_power)
        endurance = endurance_hours * 3600.0
        range_km = cruise_speed * endurance_hours / 1000.0

    climb_rate = 0.0
    if thrust_available > gross_weight * 9.81:
        excess_thrust = thrust_available - gross_weight * 9.81
        climb_rate = excess_thrust / gross_weight * 60.0

    return RotorPerformance(
        hover_ceiling=hover_ceiling,
        max_forward_speed=max_forward_speed,
        climb_rate=climb_rate,
        endurance=endurance,
        range=range_km,
        service_ceiling=service_ceiling,
        max_continuous_power=max_continuous_power,
    )


def calculate_rotor_performance_envelope(
    *,
    rotor_diameter: float,
    rotor_speed_rpm: float,
    blade_pitch_deg: float,
    num_blades: int = 4,
    gross_weight_range: list[float],
    engine_power_range: list[float],
    altitude_range: list[float],
    drag_coefficient: float = 0.02,
    parasite_area: float = 10.0,
    fuel_capacity: float = 1000.0,
    sfc: float = 0.5,
    isa_delta_c: float = 0.0,
) -> dict:
    hover_ceiling_grid: list[list[list[float]]] = []
    max_forward_speed_grid: list[list[list[float]]] = []
    climb_rate_grid: list[list[list[float]]] = []
    endurance_grid: list[list[list[float]]] = []
    range_grid: list[list[list[float]]] = []

    for gross_weight in gross_weight_range:
        hover_ceiling_row: list[list[float]] = []
        max_forward_speed_row: list[list[float]] = []
        climb_rate_row: list[list[float]] = []
        endurance_row: list[list[float]] = []
        range_row: list[list[float]] = []

        for engine_power in engine_power_range:
            hover_ceiling_col: list[float] = []
            max_forward_speed_col: list[float] = []
            climb_rate_col: list[float] = []
            endurance_col: list[float] = []
            range_col: list[float] = []

            for altitude in altitude_range:
                rotor_aero = calculate_rotor_aerodynamics(
                    rotor_diameter=rotor_diameter,
                    rotor_speed_rpm=rotor_speed_rpm,
                    blade_pitch_deg=blade_pitch_deg,
                    num_blades=num_blades,
                    air_density=1.225,
                    altitude_m=altitude,
                    isa_delta_c=isa_delta_c,
                )

                performance = calculate_rotor_performance(
                    rotor_aero=rotor_aero,
                    gross_weight=gross_weight,
                    engine_power=engine_power,
                    drag_coefficient=drag_coefficient,
                    parasite_area=parasite_area,
                    fuel_capacity=fuel_capacity,
                    sfc=sfc,
                    altitude_m=altitude,
                    isa_delta_c=isa_delta_c,
                )

                hover_ceiling_col.append(performance.hover_ceiling)
                max_forward_speed_col.append(performance.max_forward_speed)
                climb_rate_col.append(performance.climb_rate)
                endurance_col.append(performance.endurance)
                range_col.append(performance.range)

            hover_ceiling_row.append(hover_ceiling_col)
            max_forward_speed_row.append(max_forward_speed_col)
            climb_rate_row.append(climb_rate_col)
            endurance_row.append(endurance_col)
            range_row.append(range_col)

        hover_ceiling_grid.append(hover_ceiling_row)
        max_forward_speed_grid.append(max_forward_speed_row)
        climb_rate_grid.append(climb_rate_row)
        endurance_grid.append(endurance_row)
        range_grid.append(range_row)

    return {
        "gross_weight": gross_weight_range,
        "engine_power": engine_power_range,
        "altitude_m": altitude_range,
        "hover_ceiling": hover_ceiling_grid,
        "max_forward_speed": max_forward_speed_grid,
        "climb_rate": climb_rate_grid,
        "endurance": endurance_grid,
        "range": range_grid,
    }


def calculate_rotor_power_required(
    *,
    gross_weight: float,
    climb_rate: float,
    drag_coefficient: float = 0.02,
    parasite_area: float = 10.0,
    altitude_m: float = 0.0,
    isa_delta_c: float = 0.0,
) -> float:
    atm = isa_tropopause(altitude_m, delta_t_k=float(isa_delta_c))
    rho = atm.rho_kg_m3

    climb_thrust = gross_weight * 9.81 + gross_weight * climb_rate / 60.0
    climb_drag = 0.5 * drag_coefficient * parasite_area * rho * (climb_rate / 60.0) ** 2

    total_thrust = climb_thrust + climb_drag

    return total_thrust


def calculate_rotor_disk_loading(
    *,
    thrust: float,
    rotor_diameter: float,
) -> float:
    rotor_area = pi * (rotor_diameter / 2.0) ** 2
    disk_loading = thrust / rotor_area
    return disk_loading


def calculate_rotor_power_loading(
    *,
    power: float,
    rotor_diameter: float,
) -> float:
    rotor_area = pi * (rotor_diameter / 2.0) ** 2
    power_loading = power / rotor_area
    return power_loading
