# refact/aircraft_design/class1_conceptual/__init__.py
import json
from pathlib import Path
from .weights_class1 import solve_mtow_class1_kg, EmptyWeightModel

def execute_stage(input_data: dict, output_dir: Path) -> Path:
    """
    Executes the Class I design stage.
    - Reads high-level requirements.
    - Performs a Class I weight estimation.
    - Returns a JSON file with an initial guess for Class II.
    """
    # Extract relevant inputs
    mission = input_data.get("mission", {})
    payload = input_data.get("payload", {})
    crew = input_data.get("crew", {})
    weights_in = input_data.get("weights", {})
    
    # Perform Class I MTOW estimation
    empty_model = EmptyWeightModel(a=weights_in.get("empty_a", 0.97), b=weights_in.get("empty_b", 0.06))
    mtow_results = solve_mtow_class1_kg(
        payload_kg=payload.get("payload_kg", 1000),
        crew_kg=crew.get("crew_kg", 80),
        empty_weight_model=empty_model,
        fuel_fraction=mission.get("fuel_fraction_class1", 0.4), # A rough initial fuel fraction
        reserve_fraction=weights_in.get("reserve_fraction", 0.05),
        w0_guess_kg=weights_in.get("w0_guess_kg", 10000)
    )

    # Prepare output for Class II
    # This output will serve as the input for the next stage
    output_data = input_data.copy()
    output_data["initial_guess"] = {
        "mtow_kg": mtow_results.get("w0_kg", 10000)
    }
    output_data["class1_results"] = mtow_results

    # Write output file
    output_path = output_dir / "class1_output.json"
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
        
    return output_path
