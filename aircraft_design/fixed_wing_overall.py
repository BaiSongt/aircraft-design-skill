from __future__ import annotations

from math import pi, sqrt
from typing import Any
from .atmosphere import isa_tropopause
from .aero_drag_buildup import GeometryAssumptions, estimate_cd0_drag_buildup
from .constraints import (
    AeroPolar,
    ConstraintCheck,
    build_constraints_plot_data,
    check_constraints_at_design_point,
    stall_wing_loading_max_pa,
)
from .mission import mission_fuel_breakdown
from .performance import climb_rate_m_s, required_thrust_newton
from .propulsion import build_propulsion_model, thrust_available_n
from .sizing import wing_geometry_from_loading
from .stability_control import estimate_static_margin_and_trim, estimate_static_margin_and_trim_envelope
from .structures_loads import estimate_structural_weight_feedback, estimate_wing_root_loads
from .tail_sizing import tail_areas_from_volume_coefficients
from .units import CONST
from .weights_class1 import (
    EmptyWeightModel,
    solve_mtow_class1_kg,
)
from .config import DEFAULT_UNCERTAINTY_CASES
from .input_schema import normalize_inputs
from .geometry_detailed import geometry_detailed_from_inputs
from .geometry_shape import geometry_shape_from_inputs
from .geometry_parametric import geometry_from_inputs


def _get_required(d: dict, key: str):
    if key not in d:
        raise KeyError(f"Missing required input key: {key}")
    return d[key]


def _get_optional(d: dict, key: str, default):
    return d[key] if key in d else default


def run_fixed_wing_overall_design(inputs: dict) -> dict:
    if not inputs.get("_normalized", False):
        inputs, _warnings = normalize_inputs(inputs)
    geometry_detailed = geometry_detailed_from_inputs(inputs) or {}
    geometry_shape = geometry_shape_from_inputs(inputs) or {}
    mission = _get_required(inputs, "mission")
    payload = _get_required(inputs, "payload")
    crew = _get_required(inputs, "crew")
    aero_in = _get_required(inputs, "aero")
    sizing_in = _get_required(inputs, "sizing")
    weights_in = _get_required(inputs, "weights")
    propulsion_in = _get_required(inputs, "propulsion")
    atmosphere_in = _get_optional(inputs, "atmosphere", {})
    isa_delta_c = float(atmosphere_in.get("isa_delta_c", 0.0)) if isinstance(atmosphere_in, dict) else 0.0

    aircraft_role = _get_optional(inputs, "aircraft_role", "fixed_wing")
    propulsion_type = _get_required(propulsion_in, "type")

    range_m = float(_get_required(mission, "range_m"))
    cruise_altitude_m = float(_get_required(mission, "cruise_altitude_m"))
    cruise_speed_m_s = float(_get_required(mission, "cruise_speed_m_s"))
    v_stall_m_s = float(_get_required(mission, "v_stall_m_s"))

    payload_kg = float(_get_required(payload, "payload_kg"))
    crew_kg = float(_get_required(crew, "crew_kg"))

    cd0_in = aero_in.get("cd0", None)
    e = float(_get_required(aero_in, "e"))
    cl_max = float(_get_required(aero_in, "cl_max"))

    wing_loading_pa_guess = float(_get_required(sizing_in, "wing_loading_pa"))
    aspect_ratio = float(_get_required(sizing_in, "aspect_ratio"))
    thrust_to_weight = float(_get_required(sizing_in, "thrust_to_weight"))

    empty_a = float(_get_required(weights_in, "empty_a"))
    empty_b = float(_get_required(weights_in, "empty_b"))
    reserve_fraction = float(_get_optional(weights_in, "reserve_fraction", 0.06))
    w0_guess_kg = float(_get_optional(weights_in, "w0_guess_kg", payload_kg + crew_kg + 500.0))

    sea = isa_tropopause(0.0, delta_t_k=isa_delta_c)
    wing_loading_pa_max = stall_wing_loading_max_pa(rho_kg_m3=sea.rho_kg_m3, v_stall_m_s=v_stall_m_s, cl_max=cl_max)
    wing_loading_pa = min(wing_loading_pa_guess, wing_loading_pa_max)

    cruise_atm = isa_tropopause(cruise_altitude_m, delta_t_k=isa_delta_c)

    aero_buildup_out: dict = {}

    # Extract advanced parameters
    interference_fuse = float(aero_in.get("interference_factor_fuselage", 1.0))
    interference_wing = float(aero_in.get("interference_factor_wing", 1.0))
    interference_tail = float(aero_in.get("interference_factor_tail", 1.0))

    # Helper to calculate fuselage wetted area
    fus_wet = None
    if geometry_detailed.get("fuselage", {}).get("stations"):
        stations = geometry_detailed["fuselage"]["stations"]
        area = 0.0
        for i in range(len(stations) - 1):
            s1 = stations[i]
            s2 = stations[i + 1]
            dx = float(s2["x_m"]) - float(s1["x_m"])
            r1 = float(s1.get("radius_m", (float(s1.get("radius_y_m", 0)) + float(s1.get("radius_z_m", 0))) / 2))
            r2 = float(s2.get("radius_m", (float(s2.get("radius_y_m", 0)) + float(s2.get("radius_z_m", 0))) / 2))
            area += pi * (r1 + r2) * sqrt(dx**2 + (r2 - r1) ** 2)
        if area > 0:
            fus_wet = area

    # Helper to extract tail details
    ht_ratio = None
    vt_ratio = None
    ht_tc = None
    vt_tc = None

    if geometry_shape.get("tail"):
        tail_cfg = geometry_shape["tail"]
        if isinstance(tail_cfg, dict):
            if tail_cfg.get("horizontal"):
                ht = tail_cfg["horizontal"]
                if isinstance(ht, dict):
                    pf = ht.get("planform", {})
                    if isinstance(pf, dict):
                        if pf.get("area_ratio_to_wing"):
                            ht_ratio = float(pf["area_ratio_to_wing"])
                        if pf.get("t_c"):
                            ht_tc = float(pf["t_c"])
            if tail_cfg.get("vertical"):
                vt = tail_cfg["vertical"]
                if isinstance(vt, dict):
                    pf = vt.get("planform", {})
                    if isinstance(pf, dict):
                        if pf.get("area_ratio_to_wing"):
                            vt_ratio = float(pf["area_ratio_to_wing"])
                        if pf.get("t_c"):
                            vt_tc = float(pf["t_c"])

    if "geometry" in inputs:
        geom_in = _get_required(inputs, "geometry")
        assumptions = GeometryAssumptions(
            fuselage_length_m=float(_get_optional(geom_in, "fuselage_length_m", 7.5)),
            fuselage_diameter_m=float(_get_optional(geom_in, "fuselage_diameter_m", 1.2)),
            wetted_area_factor=float(_get_optional(geom_in, "wetted_area_factor", 3.4)),
            wing_t_c=float(_get_optional(geom_in, "wing_t_c", 0.12)),
            tail_area_ratio=float(_get_optional(geom_in, "tail_area_ratio", 0.22)),
            fuselage_wetted_area_m2=fus_wet,
            interference_factor_fuselage=interference_fuse,
            interference_factor_wing=interference_wing,
            interference_factor_tail=interference_tail,
            htail_area_ratio=ht_ratio,
            vtail_area_ratio=vt_ratio,
            htail_t_c=ht_tc,
            vtail_t_c=vt_tc,
        )
    else:
        assumptions = None

    geom_param = geometry_from_inputs(inputs)
    if geom_param is not None:
        # If we have parametric geometry, it might be better than the simple "geometry" dict
        # But we want to preserve the advanced overrides we just calculated
        base_asm = geom_param.to_drag_buildup_assumptions()
        # Create new assumptions combining base and overrides
        assumptions = GeometryAssumptions(
            fuselage_length_m=base_asm.fuselage_length_m,
            fuselage_diameter_m=base_asm.fuselage_diameter_m,
            wetted_area_factor=base_asm.wetted_area_factor,
            wing_t_c=base_asm.wing_t_c,
            tail_area_ratio=base_asm.tail_area_ratio,
            fuselage_wetted_area_m2=fus_wet,
            interference_factor_fuselage=interference_fuse,
            interference_factor_wing=interference_wing,
            interference_factor_tail=interference_tail,
            htail_area_ratio=ht_ratio,
            vtail_area_ratio=vt_ratio,
            htail_t_c=ht_tc,
            vtail_t_c=vt_tc,
        )

    cd0: float
    if assumptions is not None:
        w0_temp_kg = max(1.0, w0_guess_kg)
        geom_temp = wing_geometry_from_loading(
            w0_kg=w0_temp_kg, wing_loading_pa=wing_loading_pa, aspect_ratio=aspect_ratio
        )
        bu = estimate_cd0_drag_buildup(
            cruise_altitude_m=cruise_altitude_m,
            cruise_speed_m_s=cruise_speed_m_s,
            s_ref_m2=geom_temp.s_m2,
            b_m=geom_temp.b_m,
            cbar_m=geom_temp.cbar_m,
            assumptions=assumptions,
            isa_delta_c=isa_delta_c,
        )
        cd0 = float(cd0_in) if isinstance(cd0_in, (int, float)) else float(bu.cd0)
        aero_buildup_out = {"cd0_buildup": bu.cd0, "breakdown": bu.breakdown}
    else:
        if not isinstance(cd0_in, (int, float)):
            raise KeyError("Missing required input key: cd0")
        cd0 = float(cd0_in)

    polar = AeroPolar(cd0=cd0, e=e, ar=aspect_ratio)

    empty_model = EmptyWeightModel(a=empty_a, b=empty_b)
    structures_in = inputs.get("structures", None)
    enable_struct_feedback = (
        bool(structures_in.get("enable_weight_feedback", False)) if isinstance(structures_in, dict) else False
    )
    baseline_struct_frac = (
        float(structures_in.get("baseline_struct_frac", 0.30)) if isinstance(structures_in, dict) else 0.30
    )
    struct_feedback_gain = float(structures_in.get("feedback_gain", 1.0)) if isinstance(structures_in, dict) else 1.0
    n_limit_feedback = float(structures_in.get("n_limit", 3.8)) if isinstance(structures_in, dict) else 3.8
    t_c_feedback = float(structures_in.get("wing_t_c", 0.12)) if isinstance(structures_in, dict) else 0.12
    max_empty_additional_fraction = (
        float(structures_in.get("max_empty_additional_fraction", 0.08)) if isinstance(structures_in, dict) else 0.08
    )

    w0_iter = max(1.0, w0_guess_kg)
    empty_additional_kg = 0.0
    for _ in range(25):
        geom_temp = wing_geometry_from_loading(
            w0_kg=w0_iter, wing_loading_pa=wing_loading_pa, aspect_ratio=aspect_ratio
        )

        if assumptions is not None:
            bu = estimate_cd0_drag_buildup(
                cruise_altitude_m=cruise_altitude_m,
                cruise_speed_m_s=cruise_speed_m_s,
                s_ref_m2=geom_temp.s_m2,
                b_m=geom_temp.b_m,
                cbar_m=geom_temp.cbar_m,
                assumptions=assumptions,
                isa_delta_c=isa_delta_c,
            )
            cd0 = float(_get_optional(aero_in, "cd0", bu.cd0))
            polar = AeroPolar(cd0=cd0, e=e, ar=aspect_ratio)
            aero_buildup_out = {"cd0_buildup": bu.cd0, "breakdown": bu.breakdown}

        w_cruise_kg = 0.97 * w0_iter
        q = 0.5 * cruise_atm.rho_kg_m3 * cruise_speed_m_s * cruise_speed_m_s
        cl = (w_cruise_kg * CONST.g0_m_s2) / (q * geom_temp.s_m2)
        cd = polar.cd(cl)
        ld = cl / cd

        propulsion_model_temp = build_propulsion_model(
            propulsion_in, mtow_kg=w0_iter, thrust_to_weight=thrust_to_weight
        )
        mission_breakdown_temp = mission_fuel_breakdown(
            w0_kg=w0_iter,
            s_m2=geom_temp.s_m2,
            polar=polar,
            propulsion=propulsion_model_temp,
            mission=mission,
            isa_delta_c=isa_delta_c,
        )
        fuel_frac = float(mission_breakdown_temp["fuel_fraction_total"])

        empty_additional_kg = 0.0
        if enable_struct_feedback:
            loads = estimate_wing_root_loads(w0_kg=w0_iter, b_m=geom_temp.b_m, n_limit=n_limit_feedback)
            w_struct = estimate_structural_weight_feedback(loads=loads, s_m2=geom_temp.s_m2, t_c=t_c_feedback)
            baseline_struct_kg = max(0.0, baseline_struct_frac * empty_model.we_kg(w0_iter))
            raw = max(0.0, struct_feedback_gain * (w_struct.w_struct_kg - baseline_struct_kg))
            empty_additional_kg = min(raw, 0.25 * w0_iter)

        mtow = solve_mtow_class1_kg(
            payload_kg=payload_kg,
            crew_kg=crew_kg,
            empty_weight_model=empty_model,
            empty_additional_kg=empty_additional_kg,
            fuel_fraction=fuel_frac,
            reserve_fraction=reserve_fraction,
            w0_guess_kg=w0_iter,
        )
        w0_next = float(mtow["w0_kg"])
        rel = abs(w0_next - w0_iter) / max(1e-9, w0_next)
        w0_iter = w0_next
        if rel < 1e-4:
            break

    w0_kg = float(mtow["w0_kg"])
    mtow["empty_additional_kg"] = empty_additional_kg
    mtow["structural_feedback_enabled"] = enable_struct_feedback
    mtow["max_empty_additional_fraction"] = max_empty_additional_fraction
    geom = wing_geometry_from_loading(w0_kg=w0_kg, wing_loading_pa=wing_loading_pa, aspect_ratio=aspect_ratio)
    propulsion_model = build_propulsion_model(propulsion_in, mtow_kg=w0_kg, thrust_to_weight=thrust_to_weight)
    mission_breakdown = mission_fuel_breakdown(
        w0_kg=w0_kg, s_m2=geom.s_m2, polar=polar, propulsion=propulsion_model, mission=mission, isa_delta_c=isa_delta_c
    )

    aero_out = {
        "cd0": cd0,
        "e": e,
        "ar": aspect_ratio,
        "k": polar.k,
        "cl_max": cl_max,
        "ld_cruise": ld,
    }
    if aero_buildup_out:
        aero_out.update(aero_buildup_out)

    sizing_out = {
        "wing_loading_pa": wing_loading_pa,
        "wing_loading_pa_max_from_stall": wing_loading_pa_max,
        "aspect_ratio": aspect_ratio,
        "thrust_to_weight": thrust_to_weight,
        "s_m2": geom.s_m2,
        "b_m": geom.b_m,
        "cbar_m": geom.cbar_m,
        "mtow_n": w0_kg * CONST.g0_m_s2,
        "thrust_required_takeoff_n": thrust_to_weight * w0_kg * CONST.g0_m_s2,
    }

    cruise_required_thrust_n = required_thrust_newton(
        rho_kg_m3=cruise_atm.rho_kg_m3, v_m_s=cruise_speed_m_s, w_kg=0.97 * w0_kg, s_m2=geom.s_m2, polar=polar
    )

    v_climb_m_s = float(_get_optional(mission, "v_climb_m_s", 1.3 * v_stall_m_s))
    climb_gradient = float(_get_optional(mission, "climb_gradient", 0.024))
    takeoff_climb_gradient = _get_optional(mission, "takeoff_climb_gradient", climb_gradient)
    takeoff_distance_m = _get_optional(mission, "takeoff_distance_m", None)
    landing_distance_m = _get_optional(mission, "landing_distance_m", None)
    mu_takeoff = float(_get_optional(mission, "mu_takeoff", 0.04))
    landing_decel_g = float(_get_optional(mission, "landing_decel_g", 0.4))
    obstacle_height_m = float(_get_optional(mission, "obstacle_height_m", 15.24))
    landing_approach_angle_deg = float(_get_optional(mission, "landing_approach_angle_deg", 3.0))
    runway_slope = float(_get_optional(mission, "runway_slope", 0.0))
    headwind_m_s = float(_get_optional(mission, "headwind_m_s", 0.0))
    high_lift_takeoff = _get_optional(mission, "high_lift_takeoff", None)
    high_lift_landing = _get_optional(mission, "high_lift_landing", None)
    climb_atm = sea
    thrust_avail_climb_n = thrust_available_n(
        propulsion_model, altitude_m=0.0, speed_m_s=v_climb_m_s, isa_delta_c=isa_delta_c, rating="mct"
    )
    climb_rate = climb_rate_m_s(
        thrust_n=thrust_avail_climb_n,
        rho_kg_m3=climb_atm.rho_kg_m3,
        v_m_s=v_climb_m_s,
        w_kg=w0_kg,
        s_m2=geom.s_m2,
        polar=polar,
    )

    thrust_avail_cruise_n = thrust_available_n(
        propulsion_model,
        altitude_m=cruise_altitude_m,
        speed_m_s=cruise_speed_m_s,
        isa_delta_c=isa_delta_c,
        rating="cruise",
    )
    perf_out = {
        "cruise_required_thrust_n": cruise_required_thrust_n,
        "cruise_available_thrust_n": thrust_avail_cruise_n,
        "climb_rate_m_s": climb_rate,
        "climb_available_thrust_n": thrust_avail_climb_n,
    }

    sl_atm = sea
    cruise_sigma = cruise_atm.rho_kg_m3 / CONST.rho0_kg_m3
    sl_sigma = sl_atm.rho_kg_m3 / CONST.rho0_kg_m3
    propulsion_out = {
        "type": propulsion_model.type,
        "thrust_sl_n": propulsion_model.thrust_sl_n,
        "power_sl_w": propulsion_model.power_sl_w,
        "tsfc_1_s": propulsion_model.tsfc_1_s,
        "sfc_1_s": propulsion_model.sfc_1_s,
        "prop_efficiency": propulsion_model.prop_efficiency,
        "jet_lapse_exp": propulsion_model.jet_lapse_exp,
        "prop_power_lapse_exp": propulsion_model.prop_power_lapse_exp,
        "points": {
            "sea_level": {
                "altitude_m": 0.0,
                "speed_m_s": v_climb_m_s,
                "sigma": sl_sigma,
                "thrust_available_n": float(thrust_avail_climb_n),
            },
            "cruise": {
                "altitude_m": cruise_altitude_m,
                "speed_m_s": cruise_speed_m_s,
                "sigma": cruise_sigma,
                "thrust_available_n": float(thrust_avail_cruise_n),
                "thrust_required_n": float(cruise_required_thrust_n),
            },
        },
    }

    constraint_checks = check_constraints_at_design_point(
        wing_loading_pa=wing_loading_pa,
        thrust_to_weight_available=thrust_to_weight,
        polar=polar,
        stall_ws_max_pa=wing_loading_pa_max,
        cruise_rho_kg_m3=cruise_atm.rho_kg_m3,
        cruise_v_m_s=cruise_speed_m_s,
        climb_rho_kg_m3=climb_atm.rho_kg_m3,
        climb_v_m_s=v_climb_m_s,
        climb_gradient=climb_gradient,
        sea_level_rho_kg_m3=sea.rho_kg_m3,
        cl_max_clean=cl_max,
        takeoff_distance_m=float(takeoff_distance_m) if takeoff_distance_m is not None else None,
        landing_distance_m_limit_m=float(landing_distance_m) if landing_distance_m is not None else None,
        mu_takeoff=mu_takeoff,
        landing_decel_g=landing_decel_g,
        takeoff_climb_gradient=float(takeoff_climb_gradient) if takeoff_distance_m is not None else None,
        obstacle_height_m=obstacle_height_m,
        landing_approach_angle_deg=landing_approach_angle_deg,
        runway_slope=runway_slope,
        headwind_m_s=headwind_m_s,
        high_lift_takeoff_preferred=str(high_lift_takeoff) if high_lift_takeoff is not None else None,
        high_lift_landing_preferred=str(high_lift_landing) if high_lift_landing is not None else None,
    )

    empty_additional_ratio = empty_additional_kg / max(1.0, w0_kg)
    constraint_checks = [
        *constraint_checks,
        ConstraintCheck(
            name="struct_feedback",
            metric="dWe/W0",
            required=float(empty_additional_ratio),
            available=float(max_empty_additional_fraction),
            details={
                "empty_additional_kg": float(empty_additional_kg),
                "w0_kg": float(w0_kg),
                "limit_fraction": float(max_empty_additional_fraction),
            },
        ),
    ]

    def _linspace(a: float, b: float, n: int) -> list[float]:
        if n <= 1:
            return [a]
        step = (b - a) / (n - 1)
        return [a + i * step for i in range(n)]

    ws_upper = max(1.2 * wing_loading_pa_max, 1.2 * wing_loading_pa)
    ws_lower = max(1.0, 0.35 * wing_loading_pa_max)
    ws_plot = _linspace(ws_lower, ws_upper, 31)
    ws_values_f = [float(x) for x in ws_plot]

    plot_data = build_constraints_plot_data(
        wing_loading_pa_values=ws_values_f,
        polar=polar,
        cruise_rho_kg_m3=cruise_atm.rho_kg_m3,
        cruise_v_m_s=cruise_speed_m_s,
        climb_rho_kg_m3=climb_atm.rho_kg_m3,
        climb_v_m_s=v_climb_m_s,
        climb_gradient=climb_gradient,
        stall_ws_max_pa=wing_loading_pa_max,
        sea_level_rho_kg_m3=sea.rho_kg_m3,
        cl_max_clean=cl_max,
        takeoff_distance_m=float(takeoff_distance_m) if takeoff_distance_m is not None else None,
        landing_distance_m=float(landing_distance_m) if landing_distance_m is not None else None,
        mu_takeoff=mu_takeoff,
        obstacle_height_m=obstacle_height_m,
        landing_approach_angle_deg=landing_approach_angle_deg,
        takeoff_climb_gradient=float(takeoff_climb_gradient) if takeoff_distance_m is not None else None,
        runway_slope=runway_slope,
        headwind_m_s=headwind_m_s,
    )
    plot_data["design_point"] = {"wing_loading_pa": wing_loading_pa, "thrust_to_weight": thrust_to_weight}

    constraints_out: dict[str, Any] = {
        "design_point": {"wing_loading_pa": wing_loading_pa, "thrust_to_weight_available": thrust_to_weight},
        "inputs": {
            "stall_ws_max_pa": wing_loading_pa_max,
            "climb_gradient": climb_gradient,
            "cruise_altitude_m": cruise_altitude_m,
            "cruise_speed_m_s": cruise_speed_m_s,
            "climb_speed_m_s": v_climb_m_s,
            "takeoff_distance_m": takeoff_distance_m,
            "landing_distance_m": landing_distance_m,
        },
        "plot_data": plot_data,
        "checks": [
            {
                "name": c.name,
                "metric": c.metric,
                "required": c.required,
                "available": c.available,
                "margin": c.margin,
                "details": c.details,
            }
            for c in constraint_checks
        ],
    }
    _margins = [c for c in constraints_out.get("checks", []) if isinstance(c.get("margin", None), (int, float))]
    constraints_out["feasible"] = all(float(c.get("margin", 0.0)) >= 0.0 for c in _margins) if _margins else False
    if _margins:
        _w = min(_margins, key=lambda x: float(x.get("margin", 0.0)))
        constraints_out["worst"] = {
            "name": _w.get("name", ""),
            "metric": _w.get("metric", ""),
            "required": _w.get("required", None),
            "available": _w.get("available", None),
            "margin": _w.get("margin", None),
        }
    else:
        constraints_out["worst"] = {}

    def _pick_check(name: str) -> dict | None:
        for c in constraints_out.get("checks", []):
            if isinstance(c, dict) and c.get("name") == name:
                return c
        return None

    conditions_out: dict[str, Any] = {"cases": []}
    cruise_check = _pick_check("cruise")
    if isinstance(cruise_check, dict):
        conditions_out["cases"].append(
            {
                "id": "cruise",
                "label": "巡航",
                "metric": cruise_check.get("metric"),
                "required": cruise_check.get("required"),
                "available": cruise_check.get("available"),
                "margin": cruise_check.get("margin"),
                "formula": "constraints.required_thrust_to_weight",
                "sources": {
                    "inputs": {
                        "mission.cruise_altitude_m": cruise_altitude_m,
                        "mission.cruise_speed_m_s": cruise_speed_m_s,
                    },
                    "models": ["constraints.required_thrust_to_weight", "propulsion.thrust_available_n"],
                },
            }
        )
    climb_check = _pick_check("climb_gradient")
    if isinstance(climb_check, dict):
        conditions_out["cases"].append(
            {
                "id": "climb_gradient",
                "label": "爬升",
                "metric": climb_check.get("metric"),
                "required": climb_check.get("required"),
                "available": climb_check.get("available"),
                "margin": climb_check.get("margin"),
                "formula": "constraints.required_thrust_to_weight",
                "sources": {
                    "inputs": {
                        "mission.climb_gradient": climb_gradient,
                        "mission.v_climb_m_s": v_climb_m_s,
                    },
                    "models": ["constraints.required_thrust_to_weight", "propulsion.thrust_available_n"],
                },
            }
        )
    takeoff_check = _pick_check("takeoff_distance")
    if isinstance(takeoff_check, dict):
        conditions_out["cases"].append(
            {
                "id": "takeoff_distance",
                "label": "起飞距离",
                "metric": takeoff_check.get("metric"),
                "required": takeoff_check.get("required"),
                "available": takeoff_check.get("available"),
                "margin": takeoff_check.get("margin"),
                "formula": "constraints.takeoff_distance_over_obstacle_m",
                "sources": {
                    "inputs": {
                        "mission.takeoff_distance_m": takeoff_distance_m,
                        "mission.obstacle_height_m": obstacle_height_m,
                        "mission.runway_slope": runway_slope,
                        "mission.headwind_m_s": headwind_m_s,
                    },
                    "models": [
                        "constraints.required_clmax_for_takeoff_distance_numeric",
                        "constraints.takeoff_distance_over_obstacle_m",
                    ],
                },
            }
        )
    takeoff_climb_check = _pick_check("takeoff_climb_gradient")
    if isinstance(takeoff_climb_check, dict):
        conditions_out["cases"].append(
            {
                "id": "takeoff_climb_gradient",
                "label": "起飞爬升",
                "metric": takeoff_climb_check.get("metric"),
                "required": takeoff_climb_check.get("required"),
                "available": takeoff_climb_check.get("available"),
                "margin": takeoff_climb_check.get("margin"),
                "formula": "constraints.required_thrust_to_weight",
                "sources": {
                    "inputs": {
                        "mission.takeoff_climb_gradient": takeoff_climb_gradient,
                        "mission.v_climb_m_s": v_climb_m_s,
                    },
                    "models": ["constraints.required_thrust_to_weight", "propulsion.thrust_available_n"],
                },
            }
        )

    tail_out: dict = {}
    if "tail" in inputs:
        tail_in = _get_required(inputs, "tail")
        vh = float(_get_required(tail_in, "vh"))
        vv = float(_get_required(tail_in, "vv"))
        lh_m = float(_get_required(tail_in, "lh_m"))
        lv_m = float(_get_required(tail_in, "lv_m"))
        tail = tail_areas_from_volume_coefficients(
            vh=vh,
            vv=vv,
            s_m2=geom.s_m2,
            cbar_m=geom.cbar_m,
            b_m=geom.b_m,
            lh_m=lh_m,
            lv_m=lv_m,
        )
        tail_out = {"sh_m2": tail.sh_m2, "sv_m2": tail.sv_m2}

    stability_out: dict = {}
    if "stability" in inputs and "tail" in inputs:
        stab_in = _get_required(inputs, "stability")
        x_ac_w_cbar = float(_get_optional(stab_in, "x_ac_w_cbar", 0.25))
        x_cg_cbar = float(_get_optional(stab_in, "x_cg_cbar", 0.30))
        x_cg_fwd_cbar = _get_optional(stab_in, "x_cg_fwd_cbar", None)
        x_cg_aft_cbar = _get_optional(stab_in, "x_cg_aft_cbar", None)
        cm0_w = float(_get_optional(stab_in, "cm0_w", 0.0))
        tail_eff = float(_get_optional(stab_in, "tail_efficiency", 0.9))
        downwash = float(_get_optional(stab_in, "downwash_deda", 0.35))
        a_ratio = float(_get_optional(stab_in, "a_ratio", 0.9))
        q = 0.5 * cruise_atm.rho_kg_m3 * cruise_speed_m_s * cruise_speed_m_s
        cl_cruise = (0.97 * w0_kg * CONST.g0_m_s2) / (q * geom.s_m2)
        vh_in = float(_get_required(_get_required(inputs, "tail"), "vh"))
        sm = estimate_static_margin_and_trim(
            x_ac_w_cbar=x_ac_w_cbar,
            x_cg_cbar=x_cg_cbar,
            vh=vh_in,
            tail_efficiency=tail_eff,
            downwash_deda=downwash,
            a_ratio=a_ratio,
            cm0_w=cm0_w,
            cl_cruise=cl_cruise,
        )
        stability_out = {
            "x_np_cbar": sm.x_np_cbar,
            "x_cg_cbar": sm.x_cg_cbar,
            "static_margin": sm.static_margin,
            "trim_tail_cl": sm.trim_tail_cl,
            "details": sm.details,
        }
        if x_cg_fwd_cbar is not None and x_cg_aft_cbar is not None:
            cl_min = float(_get_optional(stab_in, "cl_min", 0.8 * cl_cruise))
            cl_max_env = float(_get_optional(stab_in, "cl_max_env", 1.2 * cl_cruise))
            env = estimate_static_margin_and_trim_envelope(
                x_ac_w_cbar=x_ac_w_cbar,
                x_cg_fwd_cbar=float(x_cg_fwd_cbar),
                x_cg_aft_cbar=float(x_cg_aft_cbar),
                vh=vh_in,
                tail_efficiency=tail_eff,
                downwash_deda=downwash,
                a_ratio=a_ratio,
                cm0_w=cm0_w,
                cl_min=cl_min,
                cl_max=cl_max_env,
            )
            stability_out["envelope"] = env
            stability_out["cg_range"] = {"x_cg_fwd_cbar": float(x_cg_fwd_cbar), "x_cg_aft_cbar": float(x_cg_aft_cbar)}
            stability_out["static_margin_range"] = {
                **env["static_margin_range"],
                "min": env["static_margin_range"]["min"],
                "max": env["static_margin_range"]["max"],
            }
            stability_out["trim_tail_cl_range"] = {
                **env["trim_tail_cl_range"],
                "min": env["trim_tail_cl_range"]["min"],
                "max": env["trim_tail_cl_range"]["max"],
            }
        cg_min = float(x_cg_fwd_cbar) if x_cg_fwd_cbar is not None else float(x_cg_cbar) - 0.05
        cg_max = float(x_cg_aft_cbar) if x_cg_aft_cbar is not None else float(x_cg_cbar) + 0.05
        cg_min = max(0.05, min(0.60, cg_min))
        cg_max = max(0.05, min(0.60, cg_max))
        if cg_max < cg_min:
            cg_min, cg_max = cg_max, cg_min
        cg_points = int(_get_optional(stab_in, "regression_points", 5))
        cg_values = _linspace(cg_min, cg_max, max(2, cg_points))
        trend_rows = []
        for cg in cg_values:
            sm_i = estimate_static_margin_and_trim(
                x_ac_w_cbar=x_ac_w_cbar,
                x_cg_cbar=float(cg),
                vh=vh_in,
                tail_efficiency=tail_eff,
                downwash_deda=downwash,
                a_ratio=a_ratio,
                cm0_w=cm0_w,
                cl_cruise=cl_cruise,
            )
            trend_rows.append(
                {"x_cg_cbar": float(cg), "static_margin": sm_i.static_margin, "trim_tail_cl": sm_i.trim_tail_cl}
            )
        stability_out["trend_static_margin"] = trend_rows

    structures_out: dict = {}
    if "structures" in inputs:
        st_in = _get_required(inputs, "structures")
        n_limit = float(_get_optional(st_in, "n_limit", 3.8))
        t_c = float(_get_optional(st_in, "wing_t_c", 0.12))
        loads = estimate_wing_root_loads(w0_kg=w0_kg, b_m=geom.b_m, n_limit=n_limit)
        w_struct = estimate_structural_weight_feedback(loads=loads, s_m2=geom.s_m2, t_c=t_c)
        structures_out = {
            "n_limit": n_limit,
            "wing_root_moment_n_m": loads.m_root_n_m,
            "wing_root_shear_n": loads.shear_root_n,
            "structural_weight_kg": w_struct.w_struct_kg,
            "details": w_struct.details,
        }
        n_min = min(1.0, n_limit)
        n_max = max(1.0, n_limit)
        n_points = int(_get_optional(st_in, "regression_points", 5))
        n_values = _linspace(float(n_min), float(n_max), max(2, n_points))
        trend_rows = []
        for n in n_values:
            loads_n = estimate_wing_root_loads(w0_kg=w0_kg, b_m=geom.b_m, n_limit=float(n))
            trend_rows.append(
                {
                    "n_limit": float(n),
                    "wing_root_moment_n_m": loads_n.m_root_n_m,
                    "wing_root_shear_n": loads_n.shear_root_n,
                }
            )
        structures_out["trend_wing_root_moment"] = trend_rows

    uncertainty_out: dict = {}
    uncertainty_in = inputs.get("uncertainty", None)
    if (
        not inputs.get("_skip_uncertainty", False)
        and isinstance(uncertainty_in, dict)
        and bool(uncertainty_in.get("enabled", False))
    ):

        def _deepcopy_inputs(d: dict) -> dict:
            out = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    out[k] = _deepcopy_inputs(v)
                else:
                    out[k] = v
            return out

        def _apply_path_delta(inp: dict, path: str, spec):
            keys = path.split(".")
            cur = inp
            for k in keys[:-1]:
                cur[k] = dict(cur.get(k, {}))
                cur = cur[k]
            last = keys[-1]
            base = cur.get(last, None)
            if isinstance(spec, dict) and "mul" in spec:
                if isinstance(base, (int, float)):
                    cur[last] = float(base) * float(spec["mul"])
            elif isinstance(spec, dict) and "add" in spec:
                if isinstance(base, (int, float)):
                    cur[last] = float(base) + float(spec["add"])
            else:
                cur[last] = spec

        base_inputs = {k: v for k, v in inputs.items() if k not in {"uncertainty", "_skip_uncertainty"}}
        default_cases = DEFAULT_UNCERTAINTY_CASES
        cases_in = uncertainty_in.get("cases", None)
        cases = cases_in if isinstance(cases_in, list) and cases_in else default_cases

        base_metrics = {
            "feasible": all(float(c.get("margin", 0.0)) >= 0.0 for c in constraints_out.get("checks", [])),
            "driver": min(constraints_out.get("checks", []), key=lambda x: float(x.get("margin", 0.0))).get("name", "")
            if constraints_out.get("checks", [])
            else "",
            "worst_margin": min(float(c.get("margin", 0.0)) for c in constraints_out.get("checks", []))
            if constraints_out.get("checks", [])
            else float("-inf"),
            "w0_kg": w0_kg,
            "fuel_fraction_total": float(mission_breakdown.get("fuel_fraction_total", 0.0)),
            "ld_cruise": float(aero_out.get("ld_cruise", 0.0)),
        }

        out_cases = []
        for c in cases:
            name = str(c.get("name", "case"))
            deltas = c.get("deltas", {})
            inp = _deepcopy_inputs(base_inputs)
            inp["_skip_uncertainty"] = True
            if isinstance(deltas, dict):
                for pth, spec in deltas.items():
                    _apply_path_delta(inp, str(pth), spec)
            try:
                r = run_fixed_wing_overall_design(inp)
                checks_r = r.get("constraints", {}).get("checks", [])
                worst_margin = min(float(x.get("margin", 0.0)) for x in checks_r) if checks_r else float("-inf")
                driver = min(checks_r, key=lambda x: float(x.get("margin", 0.0))).get("name", "") if checks_r else ""
                feasible = worst_margin >= 0.0
                out_cases.append(
                    {
                        "name": name,
                        "deltas": deltas,
                        "feasible": feasible,
                        "driver": driver,
                        "worst_margin": worst_margin,
                        "w0_kg": r.get("weights", {}).get("w0_kg", None),
                        "fuel_fraction_total": r.get("mission_breakdown", {}).get("fuel_fraction_total", None),
                        "ld_cruise": r.get("aero", {}).get("ld_cruise", None),
                    }
                )
            except Exception as e:
                out_cases.append({"name": name, "deltas": deltas, "feasible": False, "error": str(e)})

        uncertainty_out = {"base": base_metrics, "cases": out_cases, "config": uncertainty_in}

    validation_snapshot = inputs.get("_validation_snapshot", None)
    validation_warnings = inputs.get("_validation_warnings", None)
    report_config = inputs.get("report", {}) if isinstance(inputs.get("report", {}), dict) else {}
    return {
        "summary": {"aircraft_role": aircraft_role, "propulsion_type": propulsion_type},
        "inputs_config": validation_snapshot
        if isinstance(validation_snapshot, dict)
        else {"atmosphere": atmosphere_in, "report": report_config},
        "input_warnings": validation_warnings if isinstance(validation_warnings, list) else [],
        "mission": {
            "range_m": range_m,
            "cruise_altitude_m": cruise_altitude_m,
            "cruise_speed_m_s": cruise_speed_m_s,
            "v_stall_m_s": v_stall_m_s,
        },
        "mission_breakdown": mission_breakdown,
        "constraints": constraints_out,
        "conditions": conditions_out,
        "sizing": sizing_out,
        "aero": aero_out,
        "weights": mtow,
        "performance": perf_out,
        "propulsion": propulsion_out,
        "tail": tail_out,
        "stability": stability_out,
        "structures": structures_out,
        "uncertainty": uncertainty_out,
        "geometry_detailed": geometry_detailed,
        "geometry_shape": geometry_shape,
    }
