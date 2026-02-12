from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any

from ..common.atmosphere import qbar_pa
from .high_lift import (
    max_high_lift_config,
)
from .takeoff_landing import (
    required_thrust_to_weight_for_takeoff_distance_numeric,
    max_wing_loading_for_landing_distance_numeric_pa,
)


@dataclass(frozen=True)
class AeroPolar:
    cd0: float
    e: float
    ar: float

    @property
    def k(self) -> float:
        return 1.0 / (pi * self.e * self.ar)

    def cd(self, cl: float) -> float:
        return self.cd0 + self.k * cl * cl


@dataclass(frozen=True)
class ConstraintPoint:
    wing_loading_pa: float
    thrust_to_weight_required: float


@dataclass(frozen=True)
class ConstraintCheck:
    name: str
    metric: str
    required: float
    available: float
    details: dict

    @property
    def margin(self) -> float:
        return self.available - self.required


def stall_wing_loading_max_pa(
    *,
    rho_kg_m3: float,
    v_stall_m_s: float,
    cl_max: float,
) -> float:
    return qbar_pa(rho_kg_m3, v_stall_m_s) * cl_max


def required_thrust_to_weight(
    *,
    rho_kg_m3: float,
    v_m_s: float,
    wing_loading_pa: float,
    polar: AeroPolar,
    climb_sin_gamma: float = 0.0,
) -> float:
    q = qbar_pa(rho_kg_m3, v_m_s)
    cl = wing_loading_pa / q
    cd = polar.cd(cl)
    return (q * cd) / wing_loading_pa + climb_sin_gamma


def climb_sin_gamma_from_gradient(gradient: float) -> float:
    if gradient < 0.0:
        return 0.0
    if gradient >= 1.0:
        raise ValueError("gradient must be < 1.")
    return gradient


# --- New Functions ---


def required_thrust_to_weight_for_sustained_turn(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    v_m_s: float,
    load_factor: float,
    polar: AeroPolar,
) -> float:
    """
    Calculate required T/W for sustained turn at specified n.
    T = D = q*S*CD
    L = n*W = q*S*CL -> CL = n*W / (q*S)

    T/W = q*CD0/(W/S) + K*(n^2)/(q/(W/S))
    """
    q = qbar_pa(rho_kg_m3, v_m_s)

    cd0 = polar.cd0
    k = polar.k

    # Term 1: Parasitic Drag
    # D_p / W = (q * S * CD0) / W = q * CD0 / (W/S)
    term1 = q * cd0 / wing_loading_pa

    # Term 2: Induced Drag
    # D_i / W = (q * S * K * CL^2) / W
    # CL = n * W / (q * S) = n * (W/S) / q
    # D_i / W = q * S * K * (n * (W/S) / q)^2 / W
    #         = q * S * K * n^2 * (W/S)^2 / q^2 / W
    #         = K * n^2 * (W/S) / q
    term2 = k * (load_factor**2) * wing_loading_pa / q

    return term1 + term2


def required_thrust_to_weight_for_service_ceiling(
    *,
    wing_loading_pa: float,
    rho_kg_m3: float,
    polar: AeroPolar,
    climb_rate_m_s: float = 0.508,  # 100 ft/min
    jet_lapse_exp: float = 0.7,
    thrust_sl_n: float | None = None,  # Not used for T/W calc directly, but needed if lapse is complex
) -> float:
    """
    Calculate required T_SL/W for service ceiling.
    """
    k = polar.k
    cd0 = polar.cd0

    # Max L/D conditions
    ld_max = 1.0 / (2.0 * (cd0 * k) ** 0.5)
    dw_min = 1.0 / ld_max  # 2 * sqrt(CD0 * K)

    cl_md = (cd0 / k) ** 0.5

    # V_md = sqrt(2 * (W/S) / (rho * CL_md))
    v_md = (2.0 * wing_loading_pa / (rho_kg_m3 * cl_md)) ** 0.5

    # Thrust lapse
    # Simple model: T/T_sl = (rho/rho_sl)^n
    # Assume rho provided is at ceiling.
    rho_sl = 1.225
    sigma = rho_kg_m3 / rho_sl
    lapse = sigma**jet_lapse_exp

    term_rc = climb_rate_m_s / v_md

    tw_sl_req = (term_rc + dw_min) / lapse

    return tw_sl_req


# --- Curve Generators ---


def constraint_curve_cruise(
    *,
    rho_kg_m3: float,
    v_m_s: float,
    wing_loading_pa_values: list[float],
    polar: AeroPolar,
) -> list[ConstraintPoint]:
    pts: list[ConstraintPoint] = []
    for ws in wing_loading_pa_values:
        tw = required_thrust_to_weight(rho_kg_m3=rho_kg_m3, v_m_s=v_m_s, wing_loading_pa=ws, polar=polar)
        pts.append(ConstraintPoint(wing_loading_pa=ws, thrust_to_weight_required=tw))
    return pts


def constraint_curve_climb_gradient(
    *,
    rho_kg_m3: float,
    v_m_s: float,
    wing_loading_pa_values: list[float],
    polar: AeroPolar,
    gradient: float,
) -> list[ConstraintPoint]:
    sin_gamma = climb_sin_gamma_from_gradient(gradient)
    pts: list[ConstraintPoint] = []
    for ws in wing_loading_pa_values:
        tw = required_thrust_to_weight(
            rho_kg_m3=rho_kg_m3,
            v_m_s=v_m_s,
            wing_loading_pa=ws,
            polar=polar,
            climb_sin_gamma=sin_gamma,
        )
        pts.append(ConstraintPoint(wing_loading_pa=ws, thrust_to_weight_required=tw))
    return pts


def constraint_curve_takeoff_distance(
    *,
    rho_kg_m3: float,
    takeoff_distance_m: float,
    wing_loading_pa_values: list[float],
    cl_max_clean: float,
    mu_takeoff: float = 0.04,
    obstacle_height_m: float = 15.24,
    climb_gradient: float = 0.024,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
) -> dict:
    cfg = max_high_lift_config()
    cl_to = cl_max_clean + cfg.delta_cl_max
    pts: list[dict] = []
    for ws in wing_loading_pa_values:
        tw = required_thrust_to_weight_for_takeoff_distance_numeric(
            wing_loading_pa=ws,
            rho_kg_m3=rho_kg_m3,
            cl_max_takeoff=cl_to,
            takeoff_distance_m=takeoff_distance_m,
            obstacle_height_m=obstacle_height_m,
            climb_gradient=climb_gradient,
            mu_roll=mu_takeoff,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
        )
        pts.append({"wing_loading_pa": ws, "thrust_to_weight_required": tw})
    return {
        "assumed_high_lift": cfg.name,
        "cl_max_takeoff": cl_to,
        "delta_cd0": cfg.delta_cd0,
        "obstacle_height_m": obstacle_height_m,
        "climb_gradient": climb_gradient,
        "runway_slope": runway_slope,
        "headwind_m_s": headwind_m_s,
        "points": pts,
    }


def constraint_wing_loading_max_from_landing_distance(
    *,
    rho_kg_m3: float,
    landing_distance_m: float,
    cl_max_clean: float,
    obstacle_height_m: float = 15.24,
    approach_angle_deg: float = 3.0,
    decel_g: float | None = None,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
) -> dict:
    cfg = max_high_lift_config()
    cl_l = cl_max_clean + cfg.delta_cl_max
    ws_max = max_wing_loading_for_landing_distance_numeric_pa(
        rho_kg_m3=rho_kg_m3,
        cl_max_landing=cl_l,
        target_landing_distance_m=landing_distance_m,
        obstacle_height_m=obstacle_height_m,
        approach_angle_deg=approach_angle_deg,
        decel_g=decel_g,
        runway_slope=runway_slope,
        headwind_m_s=headwind_m_s,
    )
    return {
        "assumed_high_lift": cfg.name,
        "cl_max_landing": cl_l,
        "delta_cd0": cfg.delta_cd0,
        "obstacle_height_m": obstacle_height_m,
        "approach_angle_deg": approach_angle_deg,
        "decel_g": decel_g,
        "runway_slope": runway_slope,
        "headwind_m_s": headwind_m_s,
        "wing_loading_pa_max": ws_max,
    }


def constraint_curve_sustained_turn(
    *,
    rho_kg_m3: float,
    v_m_s: float,
    load_factor: float,
    wing_loading_pa_values: list[float],
    polar: AeroPolar,
) -> list[ConstraintPoint]:
    pts: list[ConstraintPoint] = []
    for ws in wing_loading_pa_values:
        tw = required_thrust_to_weight_for_sustained_turn(
            wing_loading_pa=ws,
            rho_kg_m3=rho_kg_m3,
            v_m_s=v_m_s,
            load_factor=load_factor,
            polar=polar,
        )
        pts.append(ConstraintPoint(wing_loading_pa=ws, thrust_to_weight_required=tw))
    return pts


def constraint_curve_service_ceiling(
    *,
    rho_kg_m3: float,
    wing_loading_pa_values: list[float],
    polar: AeroPolar,
    climb_rate_m_s: float = 0.508,
    jet_lapse_exp: float = 0.7,
) -> list[ConstraintPoint]:
    pts: list[ConstraintPoint] = []
    for ws in wing_loading_pa_values:
        tw = required_thrust_to_weight_for_service_ceiling(
            wing_loading_pa=ws,
            rho_kg_m3=rho_kg_m3,
            polar=polar,
            climb_rate_m_s=climb_rate_m_s,
            jet_lapse_exp=jet_lapse_exp,
        )
        pts.append(ConstraintPoint(wing_loading_pa=ws, thrust_to_weight_required=tw))
    return pts


# Placeholders for functions that might be used elsewhere
def check_constraints_at_design_point(
    *,
    wing_loading_pa: float,
    thrust_to_weight_available: float,
    polar: AeroPolar,
    stall_ws_max_pa: float,
    cruise_rho_kg_m3: float = 1.225,
    cruise_v_m_s: float = 100.0,
    climb_rho_kg_m3: float = 1.225,
    climb_v_m_s: float = 100.0,
    climb_gradient: float = 0.0,
    sea_level_rho_kg_m3: float = 1.225,
    cl_max_clean: float = 1.5,
    takeoff_distance_m: float | None = None,
    landing_distance_m_limit_m: float | None = None,
    mu_takeoff: float = 0.02,
    landing_decel_g: float = 0.3,
    takeoff_climb_gradient: float | None = None,
    obstacle_height_m: float = 15.0,
    landing_approach_angle_deg: float = 3.0,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    high_lift_takeoff_preferred: str | None = None,
    high_lift_landing_preferred: str | None = None,
    **kwargs,
) -> list[ConstraintCheck]:
    checks = []

    # 1. Stall Constraint (W/S <= Max)
    # We define margin as (Max - Actual). Positive is good.
    # But ConstraintCheck has 'required' and 'available'.
    # If we interpret 'required' as the Limit and 'available' as Actual...
    # Margin = Available - Required. If Available > Required, Margin > 0.
    # For T/W: Available (Engine) > Required (Drag). Correct.
    # For W/S: Actual (Design) < Limit (Stall).
    # So for W/S, let's treat 'required' as Actual, and 'available' as Limit?
    # Or just adhere to the struct and handle interpretation in UI.
    # Let's use: Required = Limit, Available = Actual.
    # Margin = Available - Required = Actual - Limit.
    # For W/S, we want Margin <= 0.
    checks.append(
        ConstraintCheck(
            name="Stall Speed",
            metric="Wing Loading (Pa)",
            required=stall_ws_max_pa,
            available=wing_loading_pa,
            details={"limit": stall_ws_max_pa, "type": "max_limit"},
        )
    )

    # 2. Climb Constraint (T/W >= Req)
    tw_climb_req = required_thrust_to_weight(
        rho_kg_m3=climb_rho_kg_m3,
        v_m_s=climb_v_m_s,
        wing_loading_pa=wing_loading_pa,
        polar=polar,
        climb_sin_gamma=climb_sin_gamma_from_gradient(climb_gradient),
    )
    checks.append(
        ConstraintCheck(
            name="Climb Gradient",
            metric="T/W",
            required=tw_climb_req,
            available=thrust_to_weight_available,
            details={"gradient": climb_gradient, "type": "min_limit"},
        )
    )

    # 3. Takeoff Distance (T/W >= Req)
    if takeoff_distance_m is not None:
        # Approximate required T/W
        # cl_max_to approx cl_max_clean + 0.5
        tw_to_req = required_thrust_to_weight_for_takeoff_distance_numeric(
            takeoff_distance_m=takeoff_distance_m,
            wing_loading_pa=wing_loading_pa,
            cl_max_takeoff=cl_max_clean + 0.5,
            rho_kg_m3=sea_level_rho_kg_m3,
            # sigma=sea_level_rho_kg_m3 / 1.225, # Not needed if rho is passed
            # bypass_ratio=0.0 # Not in signature
        )
        checks.append(
            ConstraintCheck(
                name="Takeoff Distance",
                metric="T/W",
                required=tw_to_req,
                available=thrust_to_weight_available,
                details={"distance_m": takeoff_distance_m, "type": "min_limit"},
            )
        )

    # 4. Landing Distance (W/S <= Max)
    if landing_distance_m_limit_m is not None:
        # cl_max_land approx cl_max_clean + 1.0
        ws_land_max = max_wing_loading_for_landing_distance_numeric_pa(
            target_landing_distance_m=landing_distance_m_limit_m,
            cl_max_landing=cl_max_clean + 1.0,
            rho_kg_m3=sea_level_rho_kg_m3,
            obstacle_height_m=obstacle_height_m,
        )
        checks.append(
            ConstraintCheck(
                name="Landing Distance",
                metric="Wing Loading (Pa)",
                required=ws_land_max,
                available=wing_loading_pa,
                details={"distance_m": landing_distance_m_limit_m, "type": "max_limit"},
            )
        )

    return checks


def build_constraints_plot_data(
    *,
    wing_loading_pa_values: list[float],
    polar: AeroPolar,
    cl_max_clean: float,
    requirements: Any = None,
    **kwargs: Any,
) -> dict:
    # Basic implementation
    # Just return empty for now
    return {}
