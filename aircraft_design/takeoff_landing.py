from __future__ import annotations

from dataclasses import dataclass
from math import radians, sqrt, tan

from .units import CONST


@dataclass(frozen=True)
class TakeoffLandingInputs:
    wing_loading_pa: float
    rho_kg_m3: float
    cl_max: float


def _stall_speed_squared(wing_loading_pa: float, rho_kg_m3: float, cl_max: float) -> float:
    if wing_loading_pa <= 0.0 or rho_kg_m3 <= 0.0 or cl_max <= 0.0:
        raise ValueError("Invalid inputs.")
    return 2.0 * wing_loading_pa / (rho_kg_m3 * cl_max)


def takeoff_ground_roll_m(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    cl_max_takeoff: float,
    thrust_to_weight: float,
    mu_roll: float = 0.04,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.2,
    ground_factor: float = 1.15,
) -> float:
    eff = thrust_to_weight - mu_roll - runway_slope
    if eff <= 1e-6:
        return float("inf")
    vs2 = _stall_speed_squared(wing_loading_pa, rho_kg_m3, cl_max_takeoff)
    v_air = v_factor * sqrt(vs2)
    v_ground = max(1.0, v_air - headwind_m_s)
    v2 = v_ground * v_ground
    s = ground_factor * v2 / (2.0 * CONST.g0_m_s2 * eff)
    return s


def landing_distance_m(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    cl_max_landing: float,
    decel_g: float = 0.4,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.3,
    ground_factor: float = 1.3,
) -> float:
    if decel_g <= 0.0:
        raise ValueError("decel_g must be positive.")
    vs2 = _stall_speed_squared(wing_loading_pa, rho_kg_m3, cl_max_landing)
    v_air = v_factor * sqrt(vs2)
    v_ground = max(1.0, v_air - headwind_m_s)
    v2 = v_ground * v_ground
    decel_eff = decel_g + runway_slope
    if decel_eff <= 1e-6:
        return float("inf")
    s = ground_factor * v2 / (2.0 * CONST.g0_m_s2 * decel_eff)
    return s


def takeoff_distance_over_obstacle_m(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    cl_max_takeoff: float,
    thrust_to_weight: float,
    obstacle_height_m: float = 15.24,
    climb_gradient: float = 0.024,
    mu_roll: float = 0.04,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.2,
    ground_factor: float = 1.15,
) -> float:
    s_g = takeoff_ground_roll_m(
        wing_loading_pa=wing_loading_pa,
        rho_kg_m3=rho_kg_m3,
        cl_max_takeoff=cl_max_takeoff,
        thrust_to_weight=thrust_to_weight,
        mu_roll=mu_roll,
        runway_slope=runway_slope,
        headwind_m_s=headwind_m_s,
        v_factor=v_factor,
        ground_factor=ground_factor,
    )
    if obstacle_height_m <= 0.0:
        return s_g
    if climb_gradient <= 0.0:
        return float("inf")
    s_air = obstacle_height_m / climb_gradient
    return s_g + s_air


def landing_distance_over_obstacle_m(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    cl_max_landing: float,
    obstacle_height_m: float = 15.24,
    approach_angle_deg: float = 3.0,
    decel_g: float = 0.4,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.3,
    ground_factor: float = 1.3,
) -> float:
    s_g = landing_distance_m(
        wing_loading_pa=wing_loading_pa,
        rho_kg_m3=rho_kg_m3,
        cl_max_landing=cl_max_landing,
        decel_g=decel_g,
        runway_slope=runway_slope,
        headwind_m_s=headwind_m_s,
        v_factor=v_factor,
        ground_factor=ground_factor,
    )
    if obstacle_height_m <= 0.0:
        return s_g
    if approach_angle_deg <= 0.0:
        raise ValueError("approach_angle_deg must be positive.")
    s_app = obstacle_height_m / max(1e-6, tan(radians(approach_angle_deg)))
    return s_app + s_g


def required_clmax_for_takeoff_distance(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    thrust_to_weight: float,
    takeoff_distance_m: float,
    mu_roll: float = 0.04,
    v_factor: float = 1.2,
    ground_factor: float = 1.15,
) -> float:
    if takeoff_distance_m <= 0.0:
        raise ValueError("takeoff_distance_m must be positive.")
    if thrust_to_weight <= mu_roll + 1e-6:
        return float("inf")
    num = ground_factor * (v_factor * v_factor) * wing_loading_pa
    den = rho_kg_m3 * CONST.g0_m_s2 * (thrust_to_weight - mu_roll) * takeoff_distance_m
    return num / den


def required_clmax_for_takeoff_distance_numeric(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    thrust_to_weight: float,
    takeoff_distance_m: float,
    obstacle_height_m: float = 15.24,
    climb_gradient: float = 0.024,
    mu_roll: float = 0.04,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.2,
    ground_factor: float = 1.15,
    cl_min: float = 0.6,
    cl_max: float = 4.0,
) -> float:
    if takeoff_distance_m <= 0.0:
        raise ValueError("takeoff_distance_m must be positive.")
    lo = cl_min
    hi = cl_max
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        s = takeoff_distance_over_obstacle_m(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=rho_kg_m3,
            cl_max_takeoff=mid,
            thrust_to_weight=thrust_to_weight,
            obstacle_height_m=obstacle_height_m,
            climb_gradient=climb_gradient,
            mu_roll=mu_roll,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor=v_factor,
            ground_factor=ground_factor,
        )
        if s > takeoff_distance_m:
            lo = mid
        else:
            hi = mid
    return hi


def required_clmax_for_landing_distance(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    landing_distance_m: float,
    decel_g: float = 0.4,
    v_factor: float = 1.3,
    ground_factor: float = 1.3,
) -> float:
    if landing_distance_m <= 0.0:
        raise ValueError("landing_distance_m must be positive.")
    num = ground_factor * (v_factor * v_factor) * wing_loading_pa
    den = rho_kg_m3 * CONST.g0_m_s2 * decel_g * landing_distance_m
    return num / den


def required_clmax_for_landing_distance_numeric(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    landing_distance_m: float,
    obstacle_height_m: float = 15.24,
    approach_angle_deg: float = 3.0,
    decel_g: float = 0.4,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.3,
    ground_factor: float = 1.3,
    cl_min: float = 0.6,
    cl_max: float = 4.0,
) -> float:
    if landing_distance_m <= 0.0:
        raise ValueError("landing_distance_m must be positive.")
    lo = cl_min
    hi = cl_max
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        s = landing_distance_over_obstacle_m(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=rho_kg_m3,
            cl_max_landing=mid,
            obstacle_height_m=obstacle_height_m,
            approach_angle_deg=approach_angle_deg,
            decel_g=decel_g,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor=v_factor,
            ground_factor=ground_factor,
        )
        if s > landing_distance_m:
            lo = mid
        else:
            hi = mid
    return hi


def required_thrust_to_weight_for_takeoff_distance(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    cl_max_takeoff: float,
    takeoff_distance_m: float,
    mu_roll: float = 0.04,
    v_factor: float = 1.2,
    ground_factor: float = 1.15,
) -> float:
    if takeoff_distance_m <= 0.0:
        raise ValueError("takeoff_distance_m must be positive.")
    if wing_loading_pa <= 0.0 or rho_kg_m3 <= 0.0 or cl_max_takeoff <= 0.0:
        raise ValueError("Invalid inputs.")
    term = (
        ground_factor
        * (v_factor * v_factor)
        * wing_loading_pa
        / (rho_kg_m3 * CONST.g0_m_s2 * cl_max_takeoff * takeoff_distance_m)
    )
    return mu_roll + term


def required_thrust_to_weight_for_takeoff_distance_numeric(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    cl_max_takeoff: float,
    takeoff_distance_m: float,
    obstacle_height_m: float = 15.24,
    climb_gradient: float = 0.024,
    mu_roll: float = 0.04,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.2,
    ground_factor: float = 1.15,
    tw_min: float = 0.05,
    tw_max: float = 2.5,
) -> float:
    if takeoff_distance_m <= 0.0:
        raise ValueError("takeoff_distance_m must be positive.")
    lo = tw_min
    hi = tw_max
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        s = takeoff_distance_over_obstacle_m(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=rho_kg_m3,
            cl_max_takeoff=cl_max_takeoff,
            thrust_to_weight=mid,
            obstacle_height_m=obstacle_height_m,
            climb_gradient=climb_gradient,
            mu_roll=mu_roll,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor=v_factor,
            ground_factor=ground_factor,
        )
        if s > takeoff_distance_m:
            lo = mid
        else:
            hi = mid
    return hi


def max_wing_loading_for_landing_distance_numeric_pa(
    *,
    rho_kg_m3: float,
    cl_max_landing: float,
    landing_distance_m: float,
    obstacle_height_m: float = 15.24,
    approach_angle_deg: float = 3.0,
    decel_g: float = 0.4,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.3,
    ground_factor: float = 1.3,
    ws_min_pa: float = 50.0,
    ws_max_pa: float = 20000.0,
) -> float:
    if landing_distance_m <= 0.0:
        raise ValueError("landing_distance_m must be positive.")
    lo = ws_min_pa
    hi = ws_max_pa
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        s = landing_distance_over_obstacle_m(
            wing_loading_pa=mid,
            rho_kg_m3=rho_kg_m3,
            cl_max_landing=cl_max_landing,
            obstacle_height_m=obstacle_height_m,
            approach_angle_deg=approach_angle_deg,
            decel_g=decel_g,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor=v_factor,
            ground_factor=ground_factor,
        )
        if s > landing_distance_m:
            hi = mid
        else:
            lo = mid
    return lo


def max_wing_loading_for_landing_distance_pa(
    *,
    rho_kg_m3: float,
    cl_max_landing: float,
    landing_distance_m: float,
    decel_g: float = 0.4,
    v_factor: float = 1.3,
    ground_factor: float = 1.3,
) -> float:
    if landing_distance_m <= 0.0:
        raise ValueError("landing_distance_m must be positive.")
    if rho_kg_m3 <= 0.0 or cl_max_landing <= 0.0:
        raise ValueError("Invalid inputs.")
    return (
        rho_kg_m3
        * CONST.g0_m_s2
        * decel_g
        * landing_distance_m
        * cl_max_landing
        / (ground_factor * (v_factor * v_factor))
    )
