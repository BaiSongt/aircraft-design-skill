import json
import sys
from pathlib import Path
from datetime import datetime

from aircraft_design.advanced_design import execute_advanced_design
from aircraft_design.atmosphere import isa_tropopause


def load_design_data(results_dir: str):
    results_path = Path(results_dir)
    design_data_file = results_path / "design_data.json"
    
    if not design_data_file.exists():
        raise FileNotFoundError(f"Design data file not found: {design_data_file}")
    
    with open(design_data_file, 'r') as f:
        return json.load(f)


def prepare_advanced_inputs(design_data: dict):
    cruise_altitude_m = design_data["inputs"]["requirements"]["cruise_altitude_m"]
    cruise_mach = design_data["inputs"]["requirements"]["cruise_mach"]
    
    atm = isa_tropopause(cruise_altitude_m)
    cruise_speed_m_s = cruise_mach * atm.a_m_s
    
    geometry = design_data["outputs"]["geometry"]
    outputs = design_data["outputs"]
    
    design_input = {
        "cruise_altitude_m": cruise_altitude_m,
        "cruise_speed_m_s": cruise_speed_m_s,
        "mtow_kg": outputs["mtow_kg"],
        "cl_cruise": 0.3,
    }
    
    mission_input = {
        "cruise_altitude_m": cruise_altitude_m,
        "cruise_speed_m_s": cruise_speed_m_s,
        "range_m": design_data["inputs"]["requirements"]["range_m"],
        "v_stall_m_s": design_data["inputs"]["requirements"].get("stall_speed_m_s") or 100.0,
        "taxi_fraction": 0.01,
        "descent_fraction": 0.01,
        "reserve_fraction": 0.05,
        "loiter_time_s": 1800,
        "alternate_range_m": 50000,
    }
    
    propulsion_input = {
        "type": "jet",
        "thrust_sl_n": outputs["thrust_sl_n"],
        "tsfc_1_s": 1.5e-5,
        "jet_lapse_exp": 0.7,
        "jet_model_method": "simple",
    }
    
    geometry_input = {
        "s_ref_m2": geometry["s_ref_m2"],
        "b_m": geometry["span_m"],
        "cbar_m": geometry["mean_chord_m"],
        "wing_t_c": design_data["inputs"]["initial_guess"]["thickness_ratio"],
        "fuselage_length_m": geometry["fuselage_length_m"],
        "fuselage_diameter_m": geometry["fuselage_diameter_m"],
        "sweep_quarter_chord_deg": geometry["sweep_deg"],
        "aspect_ratio": geometry["aspect_ratio"],
        "taper_ratio": geometry["taper_ratio"],
    }
    
    stability_input = {
        "x_ac_w_cbar": 0.25,
        "x_cg_cbar": 0.22,
        "vh_coeff": 0.5,
        "vv_coeff": 0.04,
        "l_ht_m": geometry["fuselage_length_m"] * 0.5,
        "l_vt_m": geometry["fuselage_length_m"] * 0.45,
        "z_ht_m": 0.0,
    }
    
    structures_input = {
        "n_limit": design_data["inputs"]["requirements"]["max_load_factor"],
        "ultimate_factor": 1.5,
        "sigma_allow_pa": 250e6,
        "density_kg_m3": 2700.0,
        "relief_factor": 0.8,
    }
    
    optimization_input = {
        "design_variables": {
            "aspect_ratio": [1.5, 3.0],
            "sweep_quarter_chord_deg": [55.0, 70.0],
            "wing_t_c": [0.03, 0.06],
        },
        "constraints": {
            "aspect_ratio_constraint": lambda d: 1.5 <= d["aspect_ratio"] <= 3.0,
            "sweep_constraint": lambda d: 55.0 <= d["sweep_quarter_chord_deg"] <= 70.0,
            "thickness_constraint": lambda d: 0.03 <= d["wing_t_c"] <= 0.06,
        },
        "objective": "aspect_ratio",
        "objective_direction": "minimize",
        "n_iterations": 50,
    }
    
    return {
        "design_input": design_input,
        "mission_input": mission_input,
        "propulsion_input": propulsion_input,
        "geometry_input": geometry_input,
        "stability_input": stability_input,
        "structures_input": structures_input,
        "optimization_input": optimization_input,
    }


def run_advanced_design_analysis(results_dir: str):
    print("=" * 60)
    print("  Advanced Design Analysis (Stage 2-7)")
    print("=" * 60)
    
    design_data = load_design_data(results_dir)
    print(f"\nLoaded design data from: {results_dir}")
    print(f"MTOW: {design_data['outputs']['mtow_kg']:.1f} kg")
    print(f"Cruise Mach: {design_data['inputs']['requirements']['cruise_mach']:.2f}")
    
    inputs = prepare_advanced_inputs(design_data)
    
    print("\n" + "-" * 60)
    print("Executing Stage 2-7 Analysis...")
    print("-" * 60)
    
    result = execute_advanced_design(
        design_input=inputs["design_input"],
        mission_input=inputs["mission_input"],
        propulsion_input=inputs["propulsion_input"],
        geometry_input=inputs["geometry_input"],
        stability_input=inputs["stability_input"],
        structures_input=inputs["structures_input"],
        optimization_input=inputs["optimization_input"],
        isa_delta_c=0.0,
    )
    
    print("\n" + "=" * 60)
    print("  Stage 2: Aerodynamic Drag Breakdown")
    print("=" * 60)
    print(f"  CD0: {result.stage2_aero.cd0:.6f}")
    print(f"  Wave Drag: {result.stage2_aero.wave_drag:.6f}")
    print(f"  Compressibility Drag: {result.stage2_aero.compressibility_drag:.6f}")
    print(f"  Induced Drag: {result.stage2_aero.induced_drag:.6f}")
    print(f"  Total CD: {result.stage2_aero.cd_total:.6f}")
    print(f"  Mach: {result.stage2_aero.mach:.3f}")
    print(f"  Re (Fuselage): {result.stage2_aero.reynolds_numbers['fuselage']:.2e}")
    print(f"  Re (Wing): {result.stage2_aero.reynolds_numbers['wing']:.2e}")
    
    print("\n" + "=" * 60)
    print("  Stage 3: Propulsion Performance")
    print("=" * 60)
    print(f"  Thrust Available (Cruise): {result.stage3_propulsion.thrust_available_cruise:.0f} N")
    print(f"  Thrust Available (Climb): {result.stage3_propulsion.thrust_available_climb:.0f} N")
    print(f"  Thrust Margin (Cruise): {result.stage3_propulsion.thrust_margin_cruise*100:.1f}%")
    print(f"  Thrust Margin (Climb): {result.stage3_propulsion.thrust_margin_climb*100:.1f}%")
    print(f"  SFC (Cruise): {result.stage3_propulsion.sfc_cruise:.2e} 1/s")
    print(f"  SFC (Climb): {result.stage3_propulsion.sfc_climb:.2e} 1/s")
    print(f"  Fuel Flow (Cruise): {result.stage3_propulsion.fuel_flow_cruise:.3f} N/s")
    print(f"  Fuel Flow (Climb): {result.stage3_propulsion.fuel_flow_climb:.3f} N/s")
    
    print("\n" + "=" * 60)
    print("  Stage 4: Mission Fuel Breakdown")
    print("=" * 60)
    print(f"  Total Fuel Fraction: {result.stage4_mission.total_fuel_fraction:.4f}")
    print(f"  Total Fuel Weight: {result.stage4_mission.total_fuel_kg:.1f} kg")
    print(f"  Mission Time: {result.stage4_mission.mission_time_s/3600:.2f} hours")
    print(f"  Mission Distance: {result.stage4_mission.mission_distance_m/1000:.1f} km")
    print("\n  Segments:")
    for segment in result.stage4_mission.segment_breakdown:
        name = segment["name"]
        fraction = segment["fuel_fraction"]
        details = segment["details"]
        fuel_kg = details.get("fuel_kg", 0)
        print(f"    {name:15s}: {fraction*100:5.2f}% ({fuel_kg:6.1f} kg)")
    
    print("\n" + "=" * 60)
    print("  Stage 5: Stability & Trim")
    print("=" * 60)
    print(f"  Static Margin: {result.stage5_stability.static_margin*100:.2f}% MAC")
    print(f"  Trim Tail CL: {result.stage5_stability.trim_tail_cl:.4f}")
    print(f"  X_np (cbar): {result.stage5_stability.x_np_cbar:.3f}")
    print(f"  X_cg (cbar): {result.stage5_stability.x_cg_cbar:.3f}")
    print(f"  Downwash dε/dα: {result.stage5_stability.downwash_deda:.3f}")
    print(f"  Tail Volume Coefficient: {result.stage5_stability.tail_volume_coefficient:.3f}")
    print(f"  H-Tail Area: {result.stage5_stability.tail_area_ht_m2:.2f} m²")
    print(f"  V-Tail Area: {result.stage5_stability.tail_area_vt_m2:.2f} m²")
    
    print("\n" + "=" * 60)
    print("  Stage 6: Structural Loads")
    print("=" * 60)
    print(f"  Wing Root Moment: {result.stage6_structures.wing_root_moment/1000:.1f} kN·m")
    print(f"  Wing Root Shear: {result.stage6_structures.wing_root_shear/1000:.1f} kN")
    print(f"  Structural Weight: {result.stage6_structures.structural_weight_kg:.1f} kg")
    print(f"  Spar Cap Area (Root): {result.stage6_structures.spar_cap_area_root_m2*1e4:.2f} cm²")
    print(f"  Wingbox Height: {result.stage6_structures.wingbox_height_m*1000:.1f} mm")
    print(f"  Relief Factor: {result.stage6_structures.relief_factor:.2f}")
    
    if result.stage7_optimization:
        print("\n" + "=" * 60)
        print("  Stage 7: Optimization & Sensitivity")
        print("=" * 60)
        print(f"  Best Design Point: {result.stage7_optimization.best_design_point}")
        print(f"  Number of Feasible Designs: {len(result.stage7_optimization.feasible_designs)}")
        print("\n  Sensitivity Analysis:")
        for var_name, stats in result.stage7_optimization.sensitivity_analysis.items():
            print(f"    {var_name:20s}: mean={stats['mean']:.4f}, std={stats['std']:.4f}")
        print("\n  Recommendations:")
        for rec in result.stage7_optimization.recommendations:
            print(f"    - {rec}")
    
    return result


def save_advanced_results(result, output_dir: str):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    result_dict = {
        "stage2_aero": {
            "cd0": result.stage2_aero.cd0,
            "cd0_breakdown": result.stage2_aero.cd0_breakdown,
            "wave_drag": result.stage2_aero.wave_drag,
            "compressibility_drag": result.stage2_aero.compressibility_drag,
            "induced_drag": result.stage2_aero.induced_drag,
            "cd_total": result.stage2_aero.cd_total,
            "mach": result.stage2_aero.mach,
            "reynolds_numbers": result.stage2_aero.reynolds_numbers,
        },
        "stage3_propulsion": {
            "thrust_available_cruise": result.stage3_propulsion.thrust_available_cruise,
            "thrust_available_climb": result.stage3_propulsion.thrust_available_climb,
            "thrust_margin_cruise": result.stage3_propulsion.thrust_margin_cruise,
            "thrust_margin_climb": result.stage3_propulsion.thrust_margin_climb,
            "sfc_cruise": result.stage3_propulsion.sfc_cruise,
            "sfc_climb": result.stage3_propulsion.sfc_climb,
            "fuel_flow_cruise": result.stage3_propulsion.fuel_flow_cruise,
            "fuel_flow_climb": result.stage3_propulsion.fuel_flow_climb,
        },
        "stage4_mission": {
            "total_fuel_fraction": result.stage4_mission.total_fuel_fraction,
            "total_fuel_kg": result.stage4_mission.total_fuel_kg,
            "segment_breakdown": result.stage4_mission.segment_breakdown,
            "mission_time_s": result.stage4_mission.mission_time_s,
            "mission_distance_m": result.stage4_mission.mission_distance_m,
        },
        "stage5_stability": {
            "static_margin": result.stage5_stability.static_margin,
            "trim_tail_cl": result.stage5_stability.trim_tail_cl,
            "x_np_cbar": result.stage5_stability.x_np_cbar,
            "x_cg_cbar": result.stage5_stability.x_cg_cbar,
            "downwash_deda": result.stage5_stability.downwash_deda,
            "tail_volume_coefficient": result.stage5_stability.tail_volume_coefficient,
            "tail_area_ht_m2": result.stage5_stability.tail_area_ht_m2,
            "tail_area_vt_m2": result.stage5_stability.tail_area_vt_m2,
        },
        "stage6_structures": {
            "wing_root_moment": result.stage6_structures.wing_root_moment,
            "wing_root_shear": result.stage6_structures.wing_root_shear,
            "structural_weight_kg": result.stage6_structures.structural_weight_kg,
            "spar_cap_area_root_m2": result.stage6_structures.spar_cap_area_root_m2,
            "wingbox_height_m": result.stage6_structures.wingbox_height_m,
            "relief_factor": result.stage6_structures.relief_factor,
        },
    }
    
    if result.stage7_optimization:
        result_dict["stage7_optimization"] = {
            "best_design_point": result.stage7_optimization.best_design_point,
            "feasible_designs": result.stage7_optimization.feasible_designs,
            "sensitivity_analysis": result.stage7_optimization.sensitivity_analysis,
            "recommendations": result.stage7_optimization.recommendations,
        }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_path / f"advanced_design_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(result_dict, f, indent=2)
    
    print(f"\nAdvanced design results saved to: {output_file}")
    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_advanced_design.py <results_directory>")
        print("Example: python run_advanced_design.py output/Supersonic4Mach_20260207_191125")
        sys.exit(1)
    
    results_dir = sys.argv[1]
    
    try:
        result = run_advanced_design_analysis(results_dir)
        
        output_dir = Path(results_dir)
        save_advanced_results(result, str(output_dir))
        
        print("\n" + "=" * 60)
        print("  Advanced Design Analysis Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
