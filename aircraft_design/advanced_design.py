from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from math import pi

from .aero_drag_buildup import (
    DragBuildUpResult,
    GeometryAssumptions,
    estimate_cd0_drag_buildup,
    calculate_wave_drag,
    calculate_compressibility_drag,
    calculate_induced_drag,
    calculate_total_drag,
    generate_drag_mach_curve,
)
from .constraints import AeroPolar
from .propulsion import (
    PropulsionModel,
    thrust_available_n,
    fuel_flow_n_s,
    build_propulsion_model,
)
from .mission import (
    mission_fuel_breakdown,
    generate_mission_envelope,
)
from .stability_control import (
    StaticStabilityResult,
    estimate_static_margin_and_trim,
    tail_areas_from_volume_coefficients,
    calculate_subsonic_downwash_gradient,
    calculate_supersonic_downwash_gradient,
)
from .structures_loads import (
    WingRootLoads,
    StructuralWeightResult,
    estimate_wing_root_loads,
    estimate_structural_weight_feedback,
)
from .atmosphere import isa_tropopause
from .units import CONST


@dataclass(frozen=True)
class Stage2AeroResult:
    cd0: float
    cd0_breakdown: dict
    wave_drag: float
    compressibility_drag: float
    induced_drag: float
    cd_total: float
    mach: float
    reynolds_numbers: dict


@dataclass(frozen=True)
class Stage3PropulsionResult:
    thrust_available_cruise: float
    thrust_available_climb: float
    thrust_margin_cruise: float
    thrust_margin_climb: float
    sfc_cruise: float
    sfc_climb: float
    fuel_flow_cruise: float
    fuel_flow_climb: float


@dataclass(frozen=True)
class Stage4MissionResult:
    total_fuel_fraction: float
    total_fuel_kg: float
    segment_breakdown: list[dict]
    mission_time_s: float
    mission_distance_m: float


@dataclass(frozen=True)
class Stage5StabilityResult:
    static_margin: float
    trim_tail_cl: float
    x_np_cbar: float
    x_cg_cbar: float
    downwash_deda: float
    tail_volume_coefficient: float
    tail_area_ht_m2: float
    tail_area_vt_m2: float


@dataclass(frozen=True)
class Stage6StructuresResult:
    wing_root_moment: float
    wing_root_shear: float
    structural_weight_kg: float
    spar_cap_area_root_m2: float
    wingbox_height_m: float
    relief_factor: float


@dataclass(frozen=True)
class Stage7OptimizationResult:
    best_design_point: dict
    feasible_designs: list[dict]
    sensitivity_analysis: dict
    recommendations: list[str]


@dataclass(frozen=True)
class AdvancedDesignResult:
    stage2_aero: Stage2AeroResult
    stage3_propulsion: Stage3PropulsionResult
    stage4_mission: Stage4MissionResult
    stage5_stability: Stage5StabilityResult
    stage6_structures: Stage6StructuresResult
    stage7_optimization: Stage7OptimizationResult | None = None


def execute_stage2_aero(
    *,
    cruise_altitude_m: float,
    cruise_speed_m_s: float,
    s_ref_m2: float,
    b_m: float,
    cbar_m: float,
    wing_t_c: float,
    fuselage_length_m: float,
    fuselage_diameter_m: float,
    sweep_quarter_chord_deg: float,
    aspect_ratio: float,
    taper_ratio: float,
    cl_cruise: float,
    mach_crit: float = 0.8,
    mach_dd: float = 1.2,
    assumptions: GeometryAssumptions | None = None,
) -> Stage2AeroResult:
    if assumptions is None:
        assumptions = GeometryAssumptions(
            fuselage_length_m=fuselage_length_m,
            fuselage_diameter_m=fuselage_diameter_m,
            wetted_area_factor=4.0,
            wing_t_c=wing_t_c,
            tail_area_ratio=0.5,
        )

    drag_result = estimate_cd0_drag_buildup(
        cruise_altitude_m=cruise_altitude_m,
        cruise_speed_m_s=cruise_speed_m_s,
        s_ref_m2=s_ref_m2,
        b_m=b_m,
        cbar_m=cbar_m,
        assumptions=assumptions,
    )

    mach = drag_result.breakdown["mach"]

    cd_wave = calculate_wave_drag(
        mach=mach,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        thickness_ratio=wing_t_c,
        aspect_ratio=aspect_ratio,
    )

    cd_comp = calculate_compressibility_drag(
        mach=mach,
        mach_crit=mach_crit,
        mach_dd=mach_dd,
        cd0_subsonic=drag_result.cd0,
        cd0_supersonic=drag_result.cd0 + cd_wave,
    )

    cd_i = calculate_induced_drag(
        cl=cl_cruise,
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
    )

    cd_total = drag_result.cd0 + cd_wave + cd_comp + cd_i

    return Stage2AeroResult(
        cd0=drag_result.cd0,
        cd0_breakdown=drag_result.breakdown,
        wave_drag=cd_wave,
        compressibility_drag=cd_comp,
        induced_drag=cd_i,
        cd_total=cd_total,
        mach=mach,
        reynolds_numbers={
            "fuselage": drag_result.breakdown.get("re_fuselage", 0),
            "wing": drag_result.breakdown.get("re_wing", 0),
        },
    )


def execute_stage3_propulsion(
    *,
    propulsion_in: dict,
    mtow_kg: float,
    cruise_altitude_m: float,
    cruise_speed_m_s: float,
    climb_altitude_m: float,
    climb_speed_m_s: float,
    thrust_required_cruise_n: float,
    thrust_required_climb_n: float,
    isa_delta_c: float = 0.0,
) -> Stage3PropulsionResult:
    propulsion = build_propulsion_model(propulsion_in, mtow_kg=mtow_kg)

    thrust_avail_cruise = thrust_available_n(
        propulsion,
        altitude_m=cruise_altitude_m,
        speed_m_s=cruise_speed_m_s,
        isa_delta_c=isa_delta_c,
        rating="cruise",
    )

    thrust_avail_climb = thrust_available_n(
        propulsion,
        altitude_m=climb_altitude_m,
        speed_m_s=climb_speed_m_s,
        isa_delta_c=isa_delta_c,
        rating="mto",
    )

    fuel_flow_cruise = fuel_flow_n_s(
        propulsion,
        thrust_n=thrust_required_cruise_n,
        altitude_m=cruise_altitude_m,
        speed_m_s=cruise_speed_m_s,
        isa_delta_c=isa_delta_c,
    )

    fuel_flow_climb = fuel_flow_n_s(
        propulsion,
        thrust_n=thrust_required_climb_n,
        altitude_m=climb_altitude_m,
        speed_m_s=climb_speed_m_s,
        isa_delta_c=isa_delta_c,
    )

    sfc_cruise = fuel_flow_cruise / thrust_required_cruise_n if thrust_required_cruise_n > 0 else 0
    sfc_climb = fuel_flow_climb / thrust_required_climb_n if thrust_required_climb_n > 0 else 0

    thrust_margin_cruise = (thrust_avail_cruise - thrust_required_cruise_n) / thrust_avail_cruise if thrust_avail_cruise > 0 else 0
    thrust_margin_climb = (thrust_avail_climb - thrust_required_climb_n) / thrust_avail_climb if thrust_avail_climb > 0 else 0

    return Stage3PropulsionResult(
        thrust_available_cruise=thrust_avail_cruise,
        thrust_available_climb=thrust_avail_climb,
        thrust_margin_cruise=thrust_margin_cruise,
        thrust_margin_climb=thrust_margin_climb,
        sfc_cruise=sfc_cruise,
        sfc_climb=sfc_climb,
        fuel_flow_cruise=fuel_flow_cruise,
        fuel_flow_climb=fuel_flow_climb,
    )


def execute_stage4_mission(
    *,
    w0_kg: float,
    s_m2: float,
    polar: AeroPolar,
    propulsion: PropulsionModel,
    mission: dict,
    isa_delta_c: float = 0.0,
) -> Stage4MissionResult:
    breakdown = mission_fuel_breakdown(
        w0_kg=w0_kg,
        s_m2=s_m2,
        polar=polar,
        propulsion=propulsion,
        mission=mission,
        isa_delta_c=isa_delta_c,
    )

    total_fuel_kg = w0_kg * breakdown["fuel_fraction_total"] / (1.0 - breakdown.get("reserve_fraction", 0.0))

    mission_time_s = 0.0
    mission_distance_m = 0.0

    for segment in breakdown["segments"]:
        details = segment.get("details", {})
        mission_time_s += details.get("time_s", 0.0)
        mission_distance_m += details.get("distance_m", 0.0)

    return Stage4MissionResult(
        total_fuel_fraction=breakdown["fuel_fraction_total"],
        total_fuel_kg=total_fuel_kg,
        segment_breakdown=breakdown["segments"],
        mission_time_s=mission_time_s,
        mission_distance_m=mission_distance_m,
    )


def execute_stage5_stability(
    *,
    x_ac_w_cbar: float,
    x_cg_cbar: float,
    vh_coeff: float,
    vv_coeff: float,
    s_wing_m2: float,
    b_wing_m: float,
    c_bar_wing_m: float,
    l_ht_m: float,
    l_vt_m: float,
    aspect_ratio_wing: float,
    sweep_quarter_chord_deg: float,
    mach: float,
    cl_cruise: float,
    tail_efficiency: float = 0.9,
    z_ht_m: float = 0.0,
) -> Stage5StabilityResult:
    tail_areas = tail_areas_from_volume_coefficients(
        s_wing_m2=s_wing_m2,
        b_wing_m=b_wing_m,
        c_bar_wing_m=c_bar_wing_m,
        l_ht_m=l_ht_m,
        l_vt_m=l_vt_m,
        vh_coeff=vh_coeff,
        vv_coeff=vv_coeff,
    )

    if mach < 1.0:
        downwash_deda = calculate_subsonic_downwash_gradient(
            s_wing_m2=s_wing_m2,
            b_wing_m=b_wing_m,
            l_ht_m=l_ht_m,
            aspect_ratio_wing=aspect_ratio_wing,
            sweep_quarter_chord_deg=sweep_quarter_chord_deg,
            z_ht_m=z_ht_m,
        )
    else:
        downwash_deda = calculate_supersonic_downwash_gradient(
            s_wing_m2=s_wing_m2,
            b_wing_m=b_wing_m,
            l_ht_m=l_ht_m,
            aspect_ratio_wing=aspect_ratio_wing,
            sweep_quarter_chord_deg=sweep_quarter_chord_deg,
            mach=mach,
        )

    stability_result = estimate_static_margin_and_trim(
        x_ac_w_cbar=x_ac_w_cbar,
        x_cg_cbar=x_cg_cbar,
        vh=vh_coeff,
        tail_efficiency=tail_efficiency,
        downwash_deda=downwash_deda,
        cl_cruise=cl_cruise,
    )

    return Stage5StabilityResult(
        static_margin=stability_result.static_margin,
        trim_tail_cl=stability_result.trim_tail_cl,
        x_np_cbar=stability_result.x_np_cbar,
        x_cg_cbar=stability_result.x_cg_cbar,
        downwash_deda=downwash_deda,
        tail_volume_coefficient=vh_coeff,
        tail_area_ht_m2=tail_areas["s_ht_m2"],
        tail_area_vt_m2=tail_areas["s_vt_m2"],
    )


def execute_stage6_structures(
    *,
    mtow_kg: float,
    b_m: float,
    s_m2: float,
    wing_t_c: float,
    n_limit: float,
    ultimate_factor: float = 1.5,
    sigma_allow_pa: float = 250e6,
    density_kg_m3: float = 2700.0,
    relief_factor: float = 0.8,
) -> Stage6StructuresResult:
    loads = estimate_wing_root_loads(
        w0_kg=mtow_kg,
        b_m=b_m,
        n_limit=n_limit,
        lift_distribution="elliptic",
    )

    weight_result = estimate_structural_weight_feedback(
        loads=loads,
        s_m2=s_m2,
        t_c=wing_t_c,
        ultimate_factor=ultimate_factor,
        sigma_allow_pa=sigma_allow_pa,
        density_kg_m3=density_kg_m3,
        relief_factor=relief_factor,
    )

    return Stage6StructuresResult(
        wing_root_moment=loads.m_root_n_m,
        wing_root_shear=loads.shear_root_n,
        structural_weight_kg=weight_result.w_struct_kg,
        spar_cap_area_root_m2=weight_result.details.get("spar_cap_area_root_m2", 0),
        wingbox_height_m=weight_result.details.get("h_box_m", 0),
        relief_factor=relief_factor,
    )


def execute_stage7_optimization(
    *,
    design_variables: dict,
    constraints: dict,
    objective: str,
    objective_direction: str = "minimize",
    n_iterations: int = 100,
) -> Stage7OptimizationResult:
    feasible_designs = []
    best_design = None
    best_objective_value = float("inf") if objective_direction == "minimize" else float("-inf")

    sensitivity_data = {var: [] for var in design_variables.keys()}

    for i in range(n_iterations):
        design_point = {}
        for var_name, var_range in design_variables.items():
            import random
            design_point[var_name] = random.uniform(var_range[0], var_range[1])

        is_feasible = True
        for constraint_name, constraint_func in constraints.items():
            if not constraint_func(design_point):
                is_feasible = False
                break

        if is_feasible:
            feasible_designs.append(design_point)

            objective_value = design_point.get(objective, 0)
            if objective_direction == "minimize":
                if objective_value < best_objective_value:
                    best_objective_value = objective_value
                    best_design = design_point.copy()
            else:
                if objective_value > best_objective_value:
                    best_objective_value = objective_value
                    best_design = design_point.copy()

            for var_name in design_variables.keys():
                sensitivity_data[var_name].append(design_point[var_name])

    sensitivity_analysis = {}
    for var_name, values in sensitivity_data.items():
        if values:
            import statistics
            sensitivity_analysis[var_name] = {
                "mean": statistics.mean(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
            }

    recommendations = []
    if best_design:
        recommendations.append(f"Best design point found with {objective} = {best_objective_value:.4f}")
        recommendations.append(f"Number of feasible designs: {len(feasible_designs)}")

        if len(feasible_designs) > 0:
            for var_name in design_variables.keys():
                values = [d[var_name] for d in feasible_designs]
                import statistics
                recommendations.append(f"{var_name}: mean = {statistics.mean(values):.4f}, std = {statistics.stdev(values) if len(values) > 1 else 0:.4f}")

    return Stage7OptimizationResult(
        best_design_point=best_design or {},
        feasible_designs=feasible_designs,
        sensitivity_analysis=sensitivity_analysis,
        recommendations=recommendations,
    )


def execute_advanced_design(
    *,
    design_input: dict,
    mission_input: dict,
    propulsion_input: dict,
    geometry_input: dict,
    stability_input: dict,
    structures_input: dict,
    optimization_input: dict | None = None,
    isa_delta_c: float = 0.0,
) -> AdvancedDesignResult:
    cruise_altitude_m = design_input["cruise_altitude_m"]
    cruise_speed_m_s = design_input["cruise_speed_m_s"]
    mtow_kg = design_input["mtow_kg"]
    s_ref_m2 = geometry_input["s_ref_m2"]
    b_m = geometry_input["b_m"]
    cbar_m = geometry_input["cbar_m"]
    wing_t_c = geometry_input["wing_t_c"]
    fuselage_length_m = geometry_input["fuselage_length_m"]
    fuselage_diameter_m = geometry_input["fuselage_diameter_m"]
    sweep_quarter_chord_deg = geometry_input["sweep_quarter_chord_deg"]
    aspect_ratio = geometry_input["aspect_ratio"]
    taper_ratio = geometry_input["taper_ratio"]
    cl_cruise = design_input.get("cl_cruise", 0.6)

    stage2_result = execute_stage2_aero(
        cruise_altitude_m=cruise_altitude_m,
        cruise_speed_m_s=cruise_speed_m_s,
        s_ref_m2=s_ref_m2,
        b_m=b_m,
        cbar_m=cbar_m,
        wing_t_c=wing_t_c,
        fuselage_length_m=fuselage_length_m,
        fuselage_diameter_m=fuselage_diameter_m,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        cl_cruise=cl_cruise,
    )

    cd_total = stage2_result.cd_total
    lift_required_n = cl_cruise * 0.5 * 1.225 * (cruise_speed_m_s ** 2) * s_ref_m2
    drag_required_n = cd_total * 0.5 * 1.225 * (cruise_speed_m_s ** 2) * s_ref_m2

    climb_altitude_m = mission_input.get("climb_altitude_m", cruise_altitude_m * 0.6)
    climb_speed_m_s = mission_input.get("climb_speed_m_s", cruise_speed_m_s * 0.8)

    stage3_result = execute_stage3_propulsion(
        propulsion_in=propulsion_input,
        mtow_kg=mtow_kg,
        cruise_altitude_m=cruise_altitude_m,
        cruise_speed_m_s=cruise_speed_m_s,
        climb_altitude_m=climb_altitude_m,
        climb_speed_m_s=climb_speed_m_s,
        thrust_required_cruise_n=drag_required_n,
        thrust_required_climb_n=drag_required_n * 1.5,
        isa_delta_c=isa_delta_c,
    )

    propulsion = build_propulsion_model(propulsion_input, mtow_kg=mtow_kg)

    polar = AeroPolar(
        cd0=stage2_result.cd0,
        e=0.8,
        ar=aspect_ratio,
    )

    stage4_result = execute_stage4_mission(
        w0_kg=mtow_kg,
        s_m2=s_ref_m2,
        polar=polar,
        propulsion=propulsion,
        mission=mission_input,
        isa_delta_c=isa_delta_c,
    )

    x_ac_w_cbar = stability_input.get("x_ac_w_cbar", 0.25)
    x_cg_cbar = stability_input.get("x_cg_cbar", 0.22)
    vh_coeff = stability_input.get("vh_coeff", 0.5)
    vv_coeff = stability_input.get("vv_coeff", 0.04)
    l_ht_m = stability_input.get("l_ht_m", fuselage_length_m * 0.5)
    l_vt_m = stability_input.get("l_vt_m", fuselage_length_m * 0.45)
    z_ht_m = stability_input.get("z_ht_m", 0.0)

    stage5_result = execute_stage5_stability(
        x_ac_w_cbar=x_ac_w_cbar,
        x_cg_cbar=x_cg_cbar,
        vh_coeff=vh_coeff,
        vv_coeff=vv_coeff,
        s_wing_m2=s_ref_m2,
        b_wing_m=b_m,
        c_bar_wing_m=cbar_m,
        l_ht_m=l_ht_m,
        l_vt_m=l_vt_m,
        aspect_ratio_wing=aspect_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        mach=stage2_result.mach,
        cl_cruise=cl_cruise,
        z_ht_m=z_ht_m,
    )

    n_limit = structures_input.get("n_limit", 4.0)
    ultimate_factor = structures_input.get("ultimate_factor", 1.5)
    sigma_allow_pa = structures_input.get("sigma_allow_pa", 250e6)
    density_kg_m3 = structures_input.get("density_kg_m3", 2700.0)
    relief_factor = structures_input.get("relief_factor", 0.8)

    stage6_result = execute_stage6_structures(
        mtow_kg=mtow_kg,
        b_m=b_m,
        s_m2=s_ref_m2,
        wing_t_c=wing_t_c,
        n_limit=n_limit,
        ultimate_factor=ultimate_factor,
        sigma_allow_pa=sigma_allow_pa,
        density_kg_m3=density_kg_m3,
        relief_factor=relief_factor,
    )

    stage7_result = None
    if optimization_input:
        stage7_result = execute_stage7_optimization(
            design_variables=optimization_input.get("design_variables", {}),
            constraints=optimization_input.get("constraints", {}),
            objective=optimization_input.get("objective", "mtow_kg"),
            objective_direction=optimization_input.get("objective_direction", "minimize"),
            n_iterations=optimization_input.get("n_iterations", 100),
        )

    return AdvancedDesignResult(
        stage2_aero=stage2_result,
        stage3_propulsion=stage3_result,
        stage4_mission=stage4_result,
        stage5_stability=stage5_result,
        stage6_structures=stage6_result,
        stage7_optimization=stage7_result,
    )
