import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from aircraft_design.design_loop_orchestrator import (
    DesignRequirements,
    InitialGuess,
    sizing_loop,
    SizedAircraft
)

def main():
    parser = argparse.ArgumentParser(description="Run Fixed Wing Class I Sizing Loop")
    parser.add_argument("input_file", type=Path, help="Path to input JSON file")
    parser.add_argument("--output", "-o", type=Path, default=Path("results.json"), help="Path to output JSON file")
    parser.add_argument("--report", "-r", type=Path, default=Path("report.md"), help="Path to output Markdown report")
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: Input file {args.input_file} not found.")
        sys.exit(1)
        
    try:
        with open(args.input_file, "r") as f:
            data = json.load(f)
            
        req_data = data.get("requirements", {})
        guess_data = data.get("initial_guess", {})
        
        # Fill defaults for missing guess fields if needed, or rely on dataclass defaults if any
        # The dataclasses don't have defaults for all fields, so we expect valid input.
        # But for CLI user friendliness, we can set some sane defaults for a fighter.
        
        # Requirements defaults (Light Fighter)
        req = DesignRequirements(
            range_m=req_data.get("range_m", 2000e3),
            payload_kg=req_data.get("payload_kg", 1000.0),
            cruise_mach=req_data.get("cruise_mach", 0.8),
            cruise_altitude_m=req_data.get("cruise_altitude_m", 11000.0),
            takeoff_distance_m=req_data.get("takeoff_distance_m", 1000.0),
            landing_distance_m=req_data.get("landing_distance_m", 1000.0),
            max_load_factor=req_data.get("max_load_factor", 7.33),
            sustained_turn_g=req_data.get("sustained_turn_g", None),
            service_ceiling_m=req_data.get("service_ceiling_m", None),
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
        print(f"Requirements: {req}")
        print(f"Initial Guess: {guess}")
        
        result = sizing_loop(req, guess)
        
        # Save JSON
        output_data = {
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
        
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
            
        print(f"Results saved to {args.output}")
        
        # Generate Markdown Report
        report_content = f"""# Aircraft Sizing Report

## 1. Summary
- **Converged**: {"Yes" if result.converged else "No"}
- **Iterations**: {result.iterations}
- **MTOW**: {result.mtow_kg:.1f} kg
- **Empty Weight**: {result.empty_weight_kg:.1f} kg
- **Fuel Weight**: {result.fuel_weight_kg:.1f} kg

## 2. Geometry
- **Wing Area**: {result.wing_area_m2:.1f} m2
- **Wing Span**: {result.geometry.get('b_wing', 0):.2f} m
- **Fuselage Length**: {result.geometry.get('l_fus', 0):.2f} m

## 3. Propulsion
- **Thrust (SL Static)**: {result.thrust_sl_n:.1f} N
- **T/W (Takeoff)**: {result.thrust_sl_n / (result.mtow_kg * 9.81):.3f}

## 4. Weight Breakdown
| Component | Weight (kg) |
|-----------|-------------|
| **Structure** | {result.weight_breakdown.get('structure', 0):.1f} |
| **Systems** | {result.weight_breakdown.get('systems', 0):.1f} |
| **Payload** | {result.weight_breakdown.get('payload', 0):.1f} |
| **Fuel** | {result.fuel_weight_kg:.1f} |
| **MTOW** | {result.mtow_kg:.1f} |

## 5. Performance Constraints
- **Range**: {result.actual_range_m/1000:.1f} km (Req: {req.range_m/1000:.1f} km)
- **Takeoff**: {result.takeoff_distance_m:.1f} m (Req: {req.takeoff_distance_m:.1f} m)
- **Landing**: {result.landing_distance_m:.1f} m (Req: {req.landing_distance_m:.1f} m)

"""
        with open(args.report, "w") as f:
            f.write(report_content)
            
        print(f"Report saved to {args.report}")
        
        if not result.converged:
            sys.exit(2)
            
    except Exception as e:
        print(f"Error during sizing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
