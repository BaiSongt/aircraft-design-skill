import argparse
import json
import sys
import socket
import pickle
import struct
from dataclasses import asdict
from pathlib import Path
from datetime import datetime

from aircraft_design.design_loop_orchestrator import (
    DesignRequirements,
    InitialGuess,
    sizing_loop,
    SizedAircraft
)
from aircraft_design.report_generator_v2 import ReportGeneratorV2
from aircraft_design.report_generator_extended import ReportGeneratorExtended
from aircraft_design.visualization_interactive import InteractivePlotter, plot_payload_range, plot_weight_breakdown
from aircraft_design.visualization_static import StaticPlotter
from aircraft_design.chart_data_generator import ChartDataGenerator
from aircraft_design.geometry_detailed import geometry_detailed_from_inputs, ParametricGeometry
from aircraft_design.openvsp_bridge import write_openvsp_script

def send_report_path_to_gui(path: Path):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1.0) # Short timeout
        client.connect(('localhost', 9999))
        
        msg = {'type': 'report_generated', 'path': str(path)}
        data = pickle.dumps(msg)
        length = struct.pack('>I', len(data))
        
        client.sendall(length + data)
        client.close()
        print(f"Sent report path to GUI: {path}")
    except Exception as e:
        # It's normal if GUI is closed or not running
        pass

def setup_output_directory(base_dir: str = "output", project_name: str = "design") -> Path:
    """
    Creates a timestamped output directory for the current run.
    Format: output/{project_name}_{YYYYMMDD_HHMMSS}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"{project_name}_{timestamp}"
    output_path = Path(base_dir) / dir_name
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Run Fixed Wing Class I Sizing Loop")
    parser.add_argument("input_file", type=Path, help="Path to input JSON file")
    parser.add_argument("--project-name", "-n", type=str, default="aircraft_sizing", help="Name of the project")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("output"), help="Base directory for outputs")
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: Input file {args.input_file} not found.")
        sys.exit(1)

    print("=" * 60)
    print("  Fixed Wing Sizing - Interactive Mode Available")
    print("=" * 60)
    print("  To enable real-time visualization and results gallery:")
    print("    1. Open a new terminal.")
    print("    2. Run: python -m aircraft_design.gui.server")
    print("    3. Keep that window open.")
    print("  Then run this script.")
    print("=" * 60)
        
    try:
        # Create output directory
        run_dir = setup_output_directory(args.output_dir, args.project_name)
        print(f"Output directory created: {run_dir}")
        
        with open(args.input_file, "r") as f:
            data = json.load(f)
            
        req_data = data.get("requirements", {})
        guess_data = data.get("initial_guess", {})
        
        # Requirements defaults (Light Fighter)
        req = DesignRequirements(
            range_m=req_data.get("range_m", 2000e3),
            payload_kg=req_data.get("payload_kg", 1000.0),
            cruise_mach=req_data.get("cruise_mach", 0.8),
            cruise_altitude_m=req_data.get("cruise_altitude_m", 11000.0),
            takeoff_distance_m=req_data.get("takeoff_distance_m", 1000.0),
            landing_distance_m=req_data.get("landing_distance_m", 1000.0),
            max_load_factor=req_data.get("max_load_factor", 7.33),
            sustained_turn_g=req_data.get("sustained_turn_g", 2.0),
            service_ceiling_m=req_data.get("service_ceiling_m", 15000.0),
        )
        
        # Guess defaults
        guess = InitialGuess(
            mtow_kg=guess_data.get("mtow_kg", 10000.0),
            thrust_to_weight=guess_data.get("thrust_to_weight", 0.6),
            wing_loading_pa=guess_data.get("wing_loading_pa", 3000.0),
            aspect_ratio=guess_data.get("aspect_ratio", 3.5),
            sweep_deg=guess_data.get("sweep_deg", 45.0),
            taper_ratio=guess_data.get("taper_ratio", 0.3),
            thickness_ratio=guess_data.get("thickness_ratio", 0.08),
            sfc_cruise_1_s=guess_data.get("sfc_cruise_1_s", 0.8 / 3600.0),
            cd0=guess_data.get("cd0", 0.02),
            oswald_e=guess_data.get("oswald_e", 0.8),
        )
        
        print("Starting Sizing Loop...")
        
        result = sizing_loop(req, guess)
        
        # Save JSON Data
        output_data = {
            "project_name": args.project_name,
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "requirements": asdict(req),
                "initial_guess": asdict(guess)
            },
            "outputs": {
                "converged": result.converged,
                "mtow_kg": result.mtow_kg,
                "empty_weight_kg": result.empty_weight_kg,
                "fuel_weight_kg": result.fuel_weight_kg,
                "wing_area_m2": result.wing_area_m2,
                "thrust_sl_n": result.thrust_sl_n,
                "geometry": result.geometry,
                "weight_breakdown": result.weight_breakdown,
                "performance": {
                    "actual_range_m": result.actual_range_m,
                    "takeoff_distance_m": result.takeoff_distance_m,
                    "landing_distance_m": result.landing_distance_m
                },
                "iterations": result.iterations
            }
        }
        
        json_path = run_dir / "design_data.json"
        with open(json_path, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"Data saved to {json_path}")
        
        # Generate Professional Report (V2)
        reporter_v2 = ReportGeneratorV2(project_name=args.project_name)
        report_content_v2 = reporter_v2.generate_report(result, req)
        
        report_path_v2 = run_dir / "design_report_v2.md"
        with open(report_path_v2, "w") as f:
            f.write(report_content_v2)
        print(f"Standard Report saved to {report_path_v2}")

        # --- Extended Workflow ---
        print("\nStarting Extended Workflow (Detailed Geometry & Analysis)...")
        
        # 1. Detailed Geometry
        # Merge requirements and initial guess into inputs for geometry extraction
        inputs_for_geom = data.copy()
        if "requirements" not in inputs_for_geom:
            inputs_for_geom["requirements"] = asdict(req)
        if "initial_guess" not in inputs_for_geom:
             inputs_for_geom["initial_guess"] = asdict(guess)

        detailed_geom = geometry_detailed_from_inputs(inputs_for_geom, result)
        result.geometry_detailed = detailed_geom # Attach to result if needed
        
        # 2. Chart Data Generation
        chart_gen = ChartDataGenerator(result, req)
        lift_data = chart_gen.generate_lift_curve()
        drag_data = chart_gen.generate_drag_polar()
        thrust_data = chart_gen.generate_thrust_curves()
        envelope_data = chart_gen.generate_flight_envelope()
        vn_data = chart_gen.generate_vn_diagram()
        
        # 3. Static Visualization
        static_plotter = StaticPlotter(run_dir)
        plot_paths = {}
        
        plot_paths["lift_curve"] = str(static_plotter.plot_lift_curve(**lift_data))
        plot_paths["drag_polar"] = str(static_plotter.plot_drag_polar(**drag_data))
        plot_paths["thrust_curve"] = str(static_plotter.plot_thrust_curves(**thrust_data))
        plot_paths["flight_envelope"] = str(static_plotter.plot_flight_envelope(**envelope_data))
        plot_paths["vn_diagram"] = str(static_plotter.plot_vn_diagram(**vn_data))
        
        # 3-View Plots
        # Prepare geometry dict for plotting
        geom_dict = {
            "fuselage": {
                "length_m": detailed_geom.fuselage.length,
                "diameter_m": detailed_geom.fuselage.diameter,
                "x_m": 0.0,
                "y_m": 0.0
            },
            "wing": {
                "s_ref_m2": detailed_geom.wing.area,
                "aspect_ratio": detailed_geom.wing.aspect_ratio,
                "taper_ratio": detailed_geom.wing.taper_ratio,
                "sweep_deg": detailed_geom.wing.sweep_qc,
                "x_m": detailed_geom.wing.x_le_root,
                "y_m": detailed_geom.wing.y_root,
                "z_m": detailed_geom.wing.z_root
            }
        }
        
        # Add Tail info if available
        # DetailedTail only has ratios, so we estimate dimensions
        if detailed_geom.tail:
            s_wing = detailed_geom.wing.area
            # HT
            s_ht = s_wing * detailed_geom.tail.area_ratio_to_wing * 0.75 # Assume 75% of tail area is HT
            ar_ht = detailed_geom.tail.ht_aspect_ratio
            geom_dict["horizontal_tail"] = {
                "s_ref_m2": s_ht,
                "aspect_ratio": ar_ht,
                "taper_ratio": 0.5, # default
                "sweep_deg": 10.0, # default
                "x_m": detailed_geom.fuselage.length * 0.85 # default placement
            }
            # VT
            s_vt = s_wing * detailed_geom.tail.area_ratio_to_wing * 0.25 # Assume 25% is VT
            ar_vt = detailed_geom.tail.vt_aspect_ratio
            geom_dict["vertical_tail"] = {
                "s_ref_m2": s_vt,
                "aspect_ratio": ar_vt,
                "taper_ratio": 0.6,
                "sweep_deg": 20.0,
                "x_m": detailed_geom.fuselage.length * 0.85,
                "z_m": detailed_geom.fuselage.diameter / 2.0
            }

        view_paths = static_plotter.plot_3view(geom_dict)
        plot_paths.update(view_paths)

        # 4. OpenVSP Script
        vsp_script_path = run_dir / "model.vspscript"
        write_openvsp_script(
            geom=detailed_geom,
            s_ref_m2=result.wing_area_m2,
            out_path=vsp_script_path,
            include_visualization=True
        )
        print(f"OpenVSP script saved to {vsp_script_path}")
        
        # 5. Extended Report
        reporter_ext = ReportGeneratorExtended(project_name=args.project_name)
        report_content_ext = reporter_ext.generate_report(result, req, plot_paths)
        
        report_path_ext = run_dir / "technical_roadmap_report.md"
        with open(report_path_ext, "w") as f:
            f.write(report_content_ext)
        print(f"Technical Roadmap Report saved to {report_path_ext}")

        # Generate Interactive Charts
        print("Generating Interactive Charts...")
        plotter = InteractivePlotter(output_dir=str(run_dir))
        
        c1 = plot_payload_range(req.payload_kg, req.range_m / 1000.0)
        c2 = plot_weight_breakdown(result.weight_breakdown)
        
        chart_path = plotter.generate_html_report([c1, c2], filename="interactive_charts.html")
        print(f"Interactive charts saved to {chart_path}")
        
        # Notify GUI
        send_report_path_to_gui(run_dir)
        
        print("\nSuccess! Design iteration completed.")
        
    except Exception as e:
        print(f"Error during sizing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
