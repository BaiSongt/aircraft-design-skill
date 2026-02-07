from __future__ import annotations

from dataclasses import dataclass
from math import pi

from .atmosphere import qbar_pa
from .high_lift import (
    max_high_lift_config,
    select_high_lift_for_required_clmax_with_preference,
)
from .takeoff_landing import (
    landing_distance_over_obstacle_m,
    takeoff_distance_over_obstacle_m,
    required_clmax_for_landing_distance_numeric,
    required_clmax_for_takeoff_distance_numeric,
    required_thrust_to_weight_for_takeoff_distance_numeric,
    takeoff_ground_roll_m,
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


def climb_sin_gamma_from_gradient(gradient: float) -> float:
    if gradient < 0.0:
        return 0.0
    if gradient >= 1.0:
        raise ValueError("gradient must be < 1.")
    return gradient


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


def build_constraints_plot_data(
    *,
    wing_loading_pa_values: list[float],
    polar: AeroPolar,
    cruise_rho_kg_m3: float,
    cruise_v_m_s: float,
    climb_rho_kg_m3: float,
    climb_v_m_s: float,
    climb_gradient: float,
    stall_ws_max_pa: float,
    sea_level_rho_kg_m3: float,
    cl_max_clean: float,
    takeoff_distance_m: float | None = None,
    landing_distance_m: float | None = None,
    mu_takeoff: float = 0.04,
    landing_decel_g: float = 0.4,
    obstacle_height_m: float = 15.24,
    landing_approach_angle_deg: float = 3.0,
    takeoff_climb_gradient: float | None = None,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
) -> dict:
    ws = [float(x) for x in wing_loading_pa_values]
    cfg_hl = max_high_lift_config()
    takeoff_grad = float(takeoff_climb_gradient) if takeoff_climb_gradient is not None else climb_gradient
    y_cruise = [
        required_thrust_to_weight(rho_kg_m3=cruise_rho_kg_m3, v_m_s=cruise_v_m_s, wing_loading_pa=x, polar=polar)
        for x in ws
    ]
    y_climb = [
        required_thrust_to_weight(
            rho_kg_m3=climb_rho_kg_m3,
            v_m_s=climb_v_m_s,
            wing_loading_pa=x,
            polar=polar,
            climb_sin_gamma=climb_sin_gamma_from_gradient(climb_gradient),
        )
        for x in ws
    ]
    polar_to = AeroPolar(cd0=polar.cd0 + cfg_hl.delta_cd0, e=polar.e, ar=polar.ar)
    y_takeoff_climb = [
        required_thrust_to_weight(
            rho_kg_m3=sea_level_rho_kg_m3,
            v_m_s=climb_v_m_s,
            wing_loading_pa=x,
            polar=polar_to,
            climb_sin_gamma=climb_sin_gamma_from_gradient(takeoff_grad),
        )
        for x in ws
    ]

    curves: list[dict] = [
        {
            "name": "cruise",
            "type": "tw_vs_ws",
            "x": ws,
            "y": y_cruise,
            "meta": {"rho_kg_m3": cruise_rho_kg_m3, "v_m_s": cruise_v_m_s},
        },
        {
            "name": "climb_gradient",
            "type": "tw_vs_ws",
            "x": ws,
            "y": y_climb,
            "meta": {"rho_kg_m3": climb_rho_kg_m3, "v_m_s": climb_v_m_s, "gradient": climb_gradient},
        },
        {
            "name": "takeoff_climb_gradient",
            "type": "tw_vs_ws",
            "x": ws,
            "y": y_takeoff_climb,
            "meta": {
                "rho_kg_m3": sea_level_rho_kg_m3,
                "v_m_s": climb_v_m_s,
                "gradient": takeoff_grad,
                "delta_cd0": cfg_hl.delta_cd0,
            },
        },
        {"name": "stall_ws", "type": "ws_max", "ws_max": float(stall_ws_max_pa), "meta": {}},
    ]

    if takeoff_distance_m is not None:
        to_curve = constraint_curve_takeoff_distance(
            rho_kg_m3=sea_level_rho_kg_m3,
            takeoff_distance_m=float(takeoff_distance_m),
            wing_loading_pa_values=ws,
            cl_max_clean=cl_max_clean,
            mu_takeoff=mu_takeoff,
            obstacle_height_m=obstacle_height_m,
            climb_gradient=takeoff_grad,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
        )
        curves.append(
            {
                "name": "takeoff_distance",
                "type": "tw_vs_ws",
                "x": [p["wing_loading_pa"] for p in to_curve["points"]],
                "y": [p["thrust_to_weight_required"] for p in to_curve["points"]],
                "meta": {k: v for k, v in to_curve.items() if k != "points"},
            }
        )

    if landing_distance_m is not None:
        ld = constraint_wing_loading_max_from_landing_distance(
            rho_kg_m3=sea_level_rho_kg_m3,
            landing_distance_m=float(landing_distance_m),
            cl_max_clean=cl_max_clean,
            obstacle_height_m=obstacle_height_m,
            approach_angle_deg=landing_approach_angle_deg,
            decel_g=landing_decel_g,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
        )
        curves.append(
            {
                "name": "landing_distance",
                "type": "ws_max",
                "ws_max": float(ld["wing_loading_pa_max"]),
                "meta": {k: v for k, v in ld.items() if k != "wing_loading_pa_max"},
            }
        )

    ws_max_vals: list[float] = []
    for c in curves:
        if c.get("type") != "ws_max":
            continue
        ws_max = c.get("ws_max")
        if isinstance(ws_max, (int, float)):
            ws_max_vals.append(float(ws_max))
    ws_limit = min(ws_max_vals) if ws_max_vals else None

    tw_curves = [c for c in curves if c.get("type") == "tw_vs_ws"]
    y_env: list[float] = []
    for i in range(len(ws)):
        vals = []
        for c in tw_curves:
            ys = c.get("y", [])
            if i < len(ys) and isinstance(ys[i], (int, float)):
                vals.append(float(ys[i]))
        y_env.append(max(vals) if vals else float("nan"))

    return {
        "schema": "ws-tw-v1",
        "x_axis": {"name": "wing_loading_pa", "unit": "Pa"},
        "y_axis": {"name": "thrust_to_weight", "unit": ""},
        "wing_loading_pa_values": ws,
        "curves": curves,
        "envelope": {"x": ws, "y": y_env},
        "ws_limit_pa": ws_limit,
    }


def check_constraints_at_design_point(
    *,
    wing_loading_pa: float,
    thrust_to_weight_available: float,
    polar: AeroPolar,
    stall_ws_max_pa: float,
    cruise_rho_kg_m3: float,
    cruise_v_m_s: float,
    climb_rho_kg_m3: float,
    climb_v_m_s: float,
    climb_gradient: float,
    sea_level_rho_kg_m3: float,
    cl_max_clean: float,
    takeoff_distance_m: float | None = None,
    landing_distance_m_limit_m: float | None = None,
    mu_takeoff: float = 0.04,
    landing_decel_g: float = 0.4,
    takeoff_climb_gradient: float | None = None,
    obstacle_height_m: float = 15.24,
    landing_approach_angle_deg: float = 3.0,
    runway_slope: float = 0.0,
    headwind_m_s: float = 0.0,
    high_lift_takeoff_preferred: str | None = None,
    high_lift_landing_preferred: str | None = None,
) -> list[ConstraintCheck]:
    checks: list[ConstraintCheck] = []

    tw_cruise = required_thrust_to_weight(
        rho_kg_m3=cruise_rho_kg_m3, v_m_s=cruise_v_m_s, wing_loading_pa=wing_loading_pa, polar=polar
    )
    checks.append(
        ConstraintCheck(
            name="cruise",
            metric="T/W",
            required=tw_cruise,
            available=thrust_to_weight_available,
            details={"rho_kg_m3": cruise_rho_kg_m3, "v_m_s": cruise_v_m_s},
        )
    )

    tw_climb = required_thrust_to_weight(
        rho_kg_m3=climb_rho_kg_m3,
        v_m_s=climb_v_m_s,
        wing_loading_pa=wing_loading_pa,
        polar=polar,
        climb_sin_gamma=climb_sin_gamma_from_gradient(climb_gradient),
    )
    checks.append(
        ConstraintCheck(
            name="climb_gradient",
            metric="T/W",
            required=tw_climb,
            available=thrust_to_weight_available,
            details={"rho_kg_m3": climb_rho_kg_m3, "v_m_s": climb_v_m_s, "gradient": climb_gradient},
        )
    )

    checks.append(
        ConstraintCheck(
            name="stall_ws",
            metric="W/S",
            required=wing_loading_pa,
            available=stall_ws_max_pa,
            details={"stall_ws_max_pa": stall_ws_max_pa},
        )
    )

    if takeoff_distance_m is not None:
        takeoff_grad = float(takeoff_climb_gradient) if takeoff_climb_gradient is not None else climb_gradient
        cl_req = required_clmax_for_takeoff_distance_numeric(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=sea_level_rho_kg_m3,
            thrust_to_weight=thrust_to_weight_available,
            takeoff_distance_m=float(takeoff_distance_m),
            obstacle_height_m=obstacle_height_m,
            climb_gradient=takeoff_grad,
            mu_roll=mu_takeoff,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
        )
        sel = select_high_lift_for_required_clmax_with_preference(
            cl_max_clean=cl_max_clean, cl_max_required=cl_req, preferred=high_lift_takeoff_preferred
        )
        cl_to = float(sel["cl_max_achievable"])
        s_to_ground = takeoff_ground_roll_m(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=sea_level_rho_kg_m3,
            cl_max_takeoff=cl_to,
            thrust_to_weight=thrust_to_weight_available,
            mu_roll=mu_takeoff,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
        )
        s_to = takeoff_distance_over_obstacle_m(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=sea_level_rho_kg_m3,
            cl_max_takeoff=cl_to,
            thrust_to_weight=thrust_to_weight_available,
            obstacle_height_m=obstacle_height_m,
            climb_gradient=takeoff_grad,
            mu_roll=mu_takeoff,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
        )
        checks.append(
            ConstraintCheck(
                name="takeoff_distance",
                metric="distance_m",
                required=s_to,
                available=float(takeoff_distance_m),
                details={
                    "cl_max_required": cl_req,
                    "cl_max_achievable": cl_to,
                    "selected_high_lift": sel["selected"],
                    "delta_cd0": sel["delta_cd0"],
                    "mu_takeoff": mu_takeoff,
                    "feasible_high_lift": sel["feasible"],
                    "obstacle_height_m": obstacle_height_m,
                    "climb_gradient": takeoff_grad,
                    "runway_slope": runway_slope,
                    "headwind_m_s": headwind_m_s,
                    "ground_roll_m": s_to_ground,
                    "airborne_distance_m": max(0.0, s_to - s_to_ground),
                },
            )
        )

        if takeoff_climb_gradient is not None:
            tw_takeoff_climb = required_thrust_to_weight(
                rho_kg_m3=sea_level_rho_kg_m3,
                v_m_s=climb_v_m_s,
                wing_loading_pa=wing_loading_pa,
                polar=AeroPolar(cd0=polar.cd0 + float(sel["delta_cd0"]), e=polar.e, ar=polar.ar),
                climb_sin_gamma=climb_sin_gamma_from_gradient(float(takeoff_climb_gradient)),
            )
            checks.append(
                ConstraintCheck(
                    name="takeoff_climb_gradient",
                    metric="T/W",
                    required=tw_takeoff_climb,
                    available=thrust_to_weight_available,
                    details={
                        "gradient": float(takeoff_climb_gradient),
                        "selected_high_lift": sel["selected"],
                        "delta_cd0": sel["delta_cd0"],
                    },
                )
            )

    if landing_distance_m_limit_m is not None:
        cl_req = required_clmax_for_landing_distance_numeric(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=sea_level_rho_kg_m3,
            target_landing_distance_m=float(landing_distance_m_limit_m),
            obstacle_height_m=obstacle_height_m,
            approach_angle_deg=landing_approach_angle_deg,
            decel_g=landing_decel_g,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
        )
        sel = select_high_lift_for_required_clmax_with_preference(
            cl_max_clean=cl_max_clean, cl_max_required=cl_req, preferred=high_lift_landing_preferred
        )
        cl_l = float(sel["cl_max_achievable"])
        s_l = landing_distance_over_obstacle_m(
            wing_loading_pa=wing_loading_pa,
            rho_kg_m3=sea_level_rho_kg_m3,
            cl_max_landing=cl_l,
            obstacle_height_m=obstacle_height_m,
            approach_angle_deg=landing_approach_angle_deg,
            decel_g=landing_decel_g,
            runway_slope=runway_slope,
            headwind_m_s=headwind_m_s,
        )
        checks.append(
            ConstraintCheck(
                name="landing_distance",
                metric="distance_m",
                required=s_l,
                available=float(landing_distance_m_limit_m),
                details={
                    "cl_max_required": cl_req,
                    "cl_max_achievable": cl_l,
                    "selected_high_lift": sel["selected"],
                    "delta_cd0": sel["delta_cd0"],
                    "decel_g": landing_decel_g,
                    "feasible_high_lift": sel["feasible"],
                    "obstacle_height_m": obstacle_height_m,
                    "approach_angle_deg": landing_approach_angle_deg,
                    "runway_slope": runway_slope,
                    "headwind_m_s": headwind_m_s,
                },
            )
        )

    return checks
