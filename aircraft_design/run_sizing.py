import argparse
import json
import sys
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
from aircraft_design.visualization_interactive import InteractivePlotter, plot_payload_range, plot_weight_breakdown

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
        reporter = ReportGeneratorV2(project_name=args.project_name)
        report_content = reporter.generate_report(result, req)
        
        report_path = run_dir / "design_report.md"
        with open(report_path, "w") as f:
            f.write(report_content)
        print(f"Report saved to {report_path}")

        # Generate Interactive Charts
        print("Generating Interactive Charts...")
        plotter = InteractivePlotter(output_dir=str(run_dir))
        
        c1 = plot_payload_range(req.payload_kg, req.range_m / 1000.0)
        c2 = plot_weight_breakdown(result.weight_breakdown)
        
        chart_path = plotter.generate_html_report([c1, c2], filename="interactive_charts.html")
        print(f"Interactive charts saved to {chart_path}")
        
        print("\nSuccess! Design iteration completed.")
        
    except Exception as e:
        print(f"Error during sizing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
