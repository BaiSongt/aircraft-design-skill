# refact/aircraft_design/class2_preliminary/__init__.py
import json
from pathlib import Path
from dataclasses import asdict

from .design_loop_orchestrator import sizing_loop, DesignRequirements, InitialGuess

def execute_stage(input_data: dict, output_dir: Path) -> Path:
    """
    Executes the Class II design stage.
    - Reads requirements and initial guess from the previous stage.
    - Runs the main sizing loop.
    - Saves the converged design results.
    """
    req_data = input_data.get("requirements", {})
    guess_data = input_data.get("initial_guess", {})

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

    guess = InitialGuess(
        mtow_kg=guess_data.get("mtow_kg", 10000.0),
        thrust_to_weight=guess_data.get("thrust_to_weight", 0.6),
        wing_loading_pa=guess_data.get("wing_loading_pa", 3000.0),
    )

    # Run the Class II sizing loop
    result = sizing_loop(req, guess, enable_visualization=False) # Disable viz for non-interactive run

    # Prepare output data
    output_data = {
        "inputs": input_data,
        "class2_results": asdict(result)
    }
    
    # Write output file
    output_path = output_dir / "class2_output.json"
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
        
    return output_path
