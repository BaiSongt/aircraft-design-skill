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
    mu_roll: float = 0.025,  # Theory 05 default for concrete
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.12,  # VLOF = 1.12 * VS
    ground_factor: float = 1.15,
) -> float:
    """
    Calculate takeoff ground roll distance.
    
    Theory 05:
    - VLOF = 1.12 * VS
    - mu_roll = 0.025
    - a = (T - D - mu(W-L)) / m
    """
    # Simple effective acceleration approximation
    # eff = T/W - mu - slope
    # This assumes L=0 and D=0 or they cancel/are small relative to T?
    # Actually, as v increases, D increases and L increases.
    # a_mean approx 0.7 * a_initial? Or use the effective T/W at 0.7 VLOF?
    # For now, we stick to the simple T/W - mu model but with updated defaults.
    # Ideally we should integrate, but this is a sizing tool.
    
    eff = thrust_to_weight - mu_roll - runway_slope
    if eff <= 1e-6:
        return float("inf")
    
    vs2 = _stall_speed_squared(wing_loading_pa, rho_kg_m3, cl_max_takeoff)
    v_lof_air = v_factor * sqrt(vs2)
    v_lof_ground = max(1.0, v_lof_air - headwind_m_s)
    v2 = v_lof_ground * v_lof_ground
    
    # S = v^2 / (2 * a_mean)
    # a_mean = g * (T/W - mu - D/W + mu*L/W)_mean
    # The 'ground_factor' 1.15 accounts for the drag/friction integration effects.
    
    s = ground_factor * v2 / (2.0 * CONST.g0_m_s2 * eff)
    return s


def landing_distance_m(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    cl_max_landing: float,
    mu_braking: float = 0.4,  # Theory 05 default
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor_approach: float = 1.2,  # Va = 1.2 * VS
    v_factor_touchdown: float = 1.1, # VTD = 1.1 * VS
    obstacle_height_m: float = 15.24, # 50 ft
    ground_factor: float = 1.3,
    approach_angle_deg: float = 3.0,
    decel_g: float | None = None,
) -> float:
    """
    Calculate landing distance (Air segment + Ground roll).
    
    Theory 05:
    - Va = 1.2 * VS (Approach)
    - VTD = 1.1 * VS (Touchdown)
    - mu_braking = 0.4
    - Air distance from 50ft
    """
    vs2 = _stall_speed_squared(wing_loading_pa, rho_kg_m3, cl_max_landing)
    vs = sqrt(vs2)
    
    v_a = v_factor_approach * vs
    v_td = v_factor_touchdown * vs
    
    # 1. Air Segment (Flare)
    # Approx: S_air = (Va^2 - Vtd^2) / (2g * n_flare_avg?) + linear distance?
    # Simple approx: S_air ~ R * sin(gamma)? 
    # Or standard estimation: S_air ~ 0.5 * Va * t_flare?
    # Let's use a simplified energy/obstacle approach often used in Class I:
    # S_air = (ObsHeight - 0) / tan(gamma_eff)? 
    # Usually S_air is approx 300-500m for transport, less for fighters.
    # Raymer/Roskam approximation: S_air ~ 300-450m?
    # Or calculate from energy bleed.
    # Let's use a simplified geometric approach assuming ~3 deg glide slope (gamma ~ 0.052)
    # S_air_approach = obstacle_height_m / 0.052  (~300m for 15m height)
    # But flare consumes distance too.
    # Theory doesn't give explicit S_air formula, just says "from 15m...".
    # We will use a standard Class I approximation for S_air based on obstacle height and glide.
    
    if approach_angle_deg <= 0.0:
         # Fallback to default if invalid
         gamma = radians(3.0)
    else:
         gamma = radians(approach_angle_deg)
         
    s_air = obstacle_height_m / tan(gamma)
    
    # 2. Ground Roll (Braking)
    # V_start_brake = VTD
    v_td_ground = max(1.0, v_td - headwind_m_s)
    
    # Decel = mu * g (assuming Lift~0 after spoil, Thrust~0)
    # If reversers/spoilers, decel is higher. mu=0.4 implies heavy braking.
    if decel_g is not None:
        eff_decel_g = decel_g
    else:
        eff_decel_g = mu_braking + runway_slope
        
    if eff_decel_g <= 1e-6:
        return float("inf")
        
    s_ground = ground_factor * (v_td_ground**2) / (2.0 * CONST.g0_m_s2 * eff_decel_g)
    
    return s_air + s_ground


def takeoff_distance_over_obstacle_m(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    cl_max_takeoff: float,
    thrust_to_weight: float,
    obstacle_height_m: float = 15.24,
    climb_gradient: float = 0.024,
    mu_roll: float = 0.025,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.12,
    ground_factor: float = 1.15,
) -> float:
    """
    Calculate total takeoff distance over obstacle.
    """
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
    
    # S_air = h_obs / gamma
    # Gamma should be calculated at V2?
    # If climb_gradient provided, use it.
    if climb_gradient <= 0.0:
        return float("inf")
        
    # Arc distance for transition + climb?
    # Simple approx: S_air = h / gamma
    s_air = obstacle_height_m / climb_gradient
    
    return s_g + s_air


def landing_distance_over_obstacle_m(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    cl_max_landing: float,
    mu_braking: float = 0.4,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor_approach: float = 1.2,
    v_factor_touchdown: float = 1.1,
    obstacle_height_m: float = 15.24,
    ground_factor: float = 1.3,
    approach_angle_deg: float = 3.0,
    decel_g: float | None = None,
) -> float:
    """
    Calculate landing distance over an obstacle.
    """
    return landing_distance_m(
        wing_loading_pa=wing_loading_pa,
        rho_kg_m3=rho_kg_m3,
        cl_max_landing=cl_max_landing,
        mu_braking=mu_braking,
        runway_slope=runway_slope,
        headwind_m_s=headwind_m_s,
        v_factor_approach=v_factor_approach,
        v_factor_touchdown=v_factor_touchdown,
        obstacle_height_m=obstacle_height_m,
        ground_factor=ground_factor,
        approach_angle_deg=approach_angle_deg,
        decel_g=decel_g,
    )


def required_clmax_for_landing_distance_numeric(
    *,
    target_landing_distance_m: float,
    wing_loading_pa: float,
    rho_kg_m3: float,
    mu_braking: float = 0.4,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor_approach: float = 1.2,
    v_factor_touchdown: float = 1.1,
    obstacle_height_m: float = 15.24,
    ground_factor: float = 1.3,
    approach_angle_deg: float = 3.0,
    decel_g: float | None = None,
    tolerance: float = 1e-3,
    max_iter: int = 20,
) -> float:
    """
    Numerically solve for required CL_max to achieve a given landing distance.
    """
    
    # Alias to avoid shadowing
    # func = landing_distance_m
    
    # Bounds for CL_max
    low, high = 0.1, 10.0
    
    # Check bounds
    # Distance decreases as CL increases
    try:
        d_low = landing_distance_m(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=rho_kg_m3,
            cl_max_landing=low,
            mu_braking=mu_braking,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor_approach=v_factor_approach,
            v_factor_touchdown=v_factor_touchdown,
            obstacle_height_m=obstacle_height_m,
            ground_factor=ground_factor,
            approach_angle_deg=approach_angle_deg,
            decel_g=decel_g,
        )
        d_high = landing_distance_m(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=rho_kg_m3,
            cl_max_landing=high,
            mu_braking=mu_braking,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor_approach=v_factor_approach,
            v_factor_touchdown=v_factor_touchdown,
            obstacle_height_m=obstacle_height_m,
            ground_factor=ground_factor,
            approach_angle_deg=approach_angle_deg,
            decel_g=decel_g,
        )
    except ValueError:
        # Likely invalid inputs to helper
        return float("inf")

    if d_low < target_landing_distance_m:
         return low
    if d_high > target_landing_distance_m:
         return float("inf")
         
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        d_mid = landing_distance_m(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=rho_kg_m3,
            cl_max_landing=mid,
            mu_braking=mu_braking,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor_approach=v_factor_approach,
            v_factor_touchdown=v_factor_touchdown,
            obstacle_height_m=obstacle_height_m,
            ground_factor=ground_factor,
            approach_angle_deg=approach_angle_deg,
            decel_g=decel_g,
        )
        
        # d_mid can be float("inf") if something goes wrong, but usually valid.
        
        if abs(d_mid - target_landing_distance_m) < tolerance:
            return mid
        
        # Distance decreases as CL increases
        if d_mid > target_landing_distance_m:
            # Need higher CL to reduce distance
            low = mid
        else:
            high = mid
            
    return (low + high) / 2.0


def required_clmax_for_takeoff_distance_numeric(
    *,
    takeoff_distance_m: float,
    wing_loading_pa: float,
    rho_kg_m3: float,
    thrust_to_weight: float,
    obstacle_height_m: float = 15.24,
    climb_gradient: float = 0.024,
    mu_roll: float = 0.025,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.12,
    ground_factor: float = 1.15,
    tolerance: float = 1e-3,
    max_iter: int = 20,
) -> float:
    """
    Numerically solve for required CL_max to achieve a given takeoff distance.
    """
    func = takeoff_distance_over_obstacle_m
    
    # Distance decreases as CL increases (lower stall speed -> earlier liftoff)
    # Bounds
    low, high = 0.1, 10.0
    
    # Check bounds
    try:
        d_low = func(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=rho_kg_m3,
            cl_max_takeoff=low,
            thrust_to_weight=thrust_to_weight,
            obstacle_height_m=obstacle_height_m,
            climb_gradient=climb_gradient,
            mu_roll=mu_roll,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor=v_factor,
            ground_factor=ground_factor,
        )
        d_high = func(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=rho_kg_m3,
            cl_max_takeoff=high,
            thrust_to_weight=thrust_to_weight,
            obstacle_height_m=obstacle_height_m,
            climb_gradient=climb_gradient,
            mu_roll=mu_roll,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor=v_factor,
            ground_factor=ground_factor,
        )
    except ValueError:
        return float("inf")
        
    if d_low < takeoff_distance_m:
        return low
    if d_high > takeoff_distance_m:
        return float("inf") # Cannot achieve even with high CL
        
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        d_mid = func(
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
        
        if abs(d_mid - takeoff_distance_m) < tolerance:
            return mid
            
        if d_mid > takeoff_distance_m:
            # Need higher CL (lower distance)
            low = mid
        else:
            high = mid
            
    return (low + high) / 2.0


def required_thrust_to_weight_for_takeoff_distance_numeric(
    *,
    takeoff_distance_m: float,
    wing_loading_pa: float,
    rho_kg_m3: float,
    cl_max_takeoff: float,
    obstacle_height_m: float = 15.24,
    climb_gradient: float = 0.024,
    mu_roll: float = 0.025,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor: float = 1.12,
    ground_factor: float = 1.15,
    tolerance: float = 1e-3,
    max_iter: int = 20,
) -> float:
    """
    Numerically solve for required T/W to achieve a given takeoff distance.
    """
    func = takeoff_distance_over_obstacle_m
    
    # Distance decreases as T/W increases (higher acceleration)
    # Bounds
    low, high = 0.01, 2.0
    
    # Check bounds
    try:
        d_low = func(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=rho_kg_m3,
            cl_max_takeoff=cl_max_takeoff,
            thrust_to_weight=low,
            obstacle_height_m=obstacle_height_m,
            climb_gradient=climb_gradient,
            mu_roll=mu_roll,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor=v_factor,
            ground_factor=ground_factor,
        )
        d_high = func(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=rho_kg_m3,
            cl_max_takeoff=cl_max_takeoff,
            thrust_to_weight=high,
            obstacle_height_m=obstacle_height_m,
            climb_gradient=climb_gradient,
            mu_roll=mu_roll,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor=v_factor,
            ground_factor=ground_factor,
        )
    except ValueError:
        return float("inf")
        
    if d_high > takeoff_distance_m:
        # Even with T/W=2.0, distance is too long?
        return float("inf")
    if d_low < takeoff_distance_m:
        # Even with T/W=0.01, distance is short enough? (Unlikely)
        return low
        
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        d_mid = func(
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
        
        if abs(d_mid - takeoff_distance_m) < tolerance:
            return mid
            
        if d_mid > takeoff_distance_m:
            # Need higher T/W (lower distance)
            low = mid
        else:
            high = mid
            
    return (low + high) / 2.0


def max_wing_loading_for_landing_distance_numeric_pa(
    *,
    target_landing_distance_m: float,
    rho_kg_m3: float,
    cl_max_landing: float,
    mu_braking: float = 0.4,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    v_factor_approach: float = 1.2,
    v_factor_touchdown: float = 1.1,
    obstacle_height_m: float = 15.24,
    ground_factor: float = 1.3,
    approach_angle_deg: float = 3.0,
    decel_g: float | None = None,
    tolerance: float = 1.0, # Pa
    max_iter: int = 20,
) -> float:
    """
    Numerically solve for maximum Wing Loading (Pa) to achieve a given landing distance.
    """
    
    # Distance increases as W/S increases (higher stall speed)
    # Bounds (Pa)
    low, high = 100.0, 10000.0 # 10 kg/m2 to 1000 kg/m2 approx
    
    # Check bounds
    try:
        d_low = landing_distance_m(
            wing_loading_pa=low,
            rho_kg_m3=rho_kg_m3,
            cl_max_landing=cl_max_landing,
            mu_braking=mu_braking,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor_approach=v_factor_approach,
            v_factor_touchdown=v_factor_touchdown,
            obstacle_height_m=obstacle_height_m,
            ground_factor=ground_factor,
            approach_angle_deg=approach_angle_deg,
            decel_g=decel_g,
        )
        d_high = landing_distance_m(
            wing_loading_pa=high,
            rho_kg_m3=rho_kg_m3,
            cl_max_landing=cl_max_landing,
            mu_braking=mu_braking,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor_approach=v_factor_approach,
            v_factor_touchdown=v_factor_touchdown,
            obstacle_height_m=obstacle_height_m,
            ground_factor=ground_factor,
            approach_angle_deg=approach_angle_deg,
            decel_g=decel_g,
        )
    except ValueError:
        return 0.0
        
    if d_low > target_landing_distance_m:
        # Even with very low W/S, distance is too long (e.g. huge obstacle?)
        return 0.0
    if d_high < target_landing_distance_m:
        # Even with very high W/S, distance is short enough (huge runway?)
        return high
        
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        d_mid = landing_distance_m(
            wing_loading_pa=mid,
            rho_kg_m3=rho_kg_m3,
            cl_max_landing=cl_max_landing,
            mu_braking=mu_braking,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
            v_factor_approach=v_factor_approach,
            v_factor_touchdown=v_factor_touchdown,
            obstacle_height_m=obstacle_height_m,
            ground_factor=ground_factor,
            approach_angle_deg=approach_angle_deg,
            decel_g=decel_g,
        )
        
        if abs(d_mid - target_landing_distance_m) < tolerance:
            return mid
            
        if d_mid > target_landing_distance_m:
            # Need lower W/S (lower distance)
            high = mid
        else:
            low = mid
            
    return (low + high) / 2.0
