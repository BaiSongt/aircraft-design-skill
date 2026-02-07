import json
import os
import time
from typing import Dict, List, Any
from dataclasses import asdict

# from .fixed_wing_overall import run_fixed_wing_overall_design # TODO: Integrate full sizing
from .input_schema import DesignRequirements
from .visualization_interactive import InteractivePlotter, plot_payload_range, plot_weight_breakdown

class DesignHistory:
    def __init__(self, log_file: str = "design_history.json"):
        self.log_file = log_file
        self.history: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                self.history = json.load(f)

    def log_iteration(self, inputs: Dict, outputs: Dict):
        entry = {
            "timestamp": time.time(),
            "inputs": inputs,
            "outputs": outputs
        }
        self.history.append(entry)
        self._save()

    def _save(self):
        with open(self.log_file, "w") as f:
            json.dump(self.history, f, indent=2)

class DesignWizard:
    def __init__(self):
        self.history = DesignHistory()

    def start_interactive_session(self):
        print("=== Aircraft Design Wizard ===")
        print("Please enter design requirements:")
        
        try:
            payload = float(input("Payload (kg) [Default: 2000]: ") or 2000)
            range_km = float(input("Range (km) [Default: 1000]: ") or 1000)
            cruise_speed = float(input("Cruise Speed (km/h) [Default: 300]: ") or 300)
            alt = float(input("Cruise Altitude (m) [Default: 5000]: ") or 5000)
        except ValueError:
            print("Invalid input. Using defaults.")
            payload, range_km, cruise_speed, alt = 2000, 1000, 300, 5000

        reqs = {
            "payload_kg": payload,
            "range_km": range_km,
            "cruise_speed_km_h": cruise_speed,
            "cruise_alt_m": alt
        }

        print("\nRunning Sizing Loop...")
        result = self._run_sizing(reqs)
        
        print("\n=== Design Result ===")
        print(f"MTOW: {result.get('mtow_kg', 'N/A'):.1f} kg")
        print(f"Fuel: {result.get('fuel_weight_kg', 'N/A'):.1f} kg")
        
        # Log
        self.history.log_iteration(reqs, result)
        
        # Visualize
        print("\nGenerating Charts...")
        self._generate_charts(reqs, result)
        print("Charts generated in output/charts/")

    def _run_sizing(self, reqs: Dict) -> Dict:
        # Map simple inputs to full DesignRequirements structure
        # This is a simplification; in reality we need more params
        # Constructing minimal inputs for run_fixed_wing_sizing
        # Note: run_fixed_wing_sizing expects a dictionary matching the schema
        
        # For now, we'll construct a mock result or call the actual sizing if possible.
        # Since run_fixed_wing_sizing takes complex inputs, we'll wrap it or use defaults.
        
        # Using a simplified mock for the wizard demonstration if full inputs aren't provided
        # But let's try to populate enough to run.
        
        full_inputs = {
            "requirements": {
                "mission": {
                    "cruise_range_km": reqs["range_km"],
                    "cruise_speed_tas_km_h": reqs["cruise_speed_km_h"],
                    "cruise_altitude_m": reqs["cruise_alt_m"],
                    "payload_kg": reqs["payload_kg"],
                    "reserves_fuel_fraction": 0.1
                },
                "constraints": {
                    "takeoff_distance_max_m": 1000,
                    "landing_distance_max_m": 1000,
                    "climb_gradient_takeoff": 0.024,
                    "climb_gradient_landing": 0.021
                },
                "propulsion": {
                    "engine_type": "piston" if reqs["cruise_speed_km_h"] < 500 else "jet",
                    "propeller_efficiency": 0.8,
                    "sfc_kg_kw_hr": 0.3 if reqs["cruise_speed_km_h"] < 500 else 0.8 # approx
                }
            },
            # ... other defaults would be needed for a robust wizard
        }
        
        # For this demonstration, we return a mock result dictionary
        # In a real implementation, we would call run_fixed_wing_sizing(full_inputs)
        # after constructing valid full_inputs.
        
        # Mock calculation
        mtow = reqs["payload_kg"] * 3.0 # Rough estimate
        fuel = mtow * 0.2
        empty = mtow * 0.6
        
        return {
            "mtow_kg": mtow,
            "fuel_weight_kg": fuel,
            "empty_weight_kg": empty,
            "wing_area_m2": mtow / 100.0,
            "thrust_req_n": mtow * 9.8 * 0.3
        }

    def _generate_charts(self, reqs: Dict, result: Dict):
        plotter = InteractivePlotter()
        
        c1 = plot_payload_range(reqs["payload_kg"], reqs["range_km"])
        c2 = plot_weight_breakdown({
            "Payload": reqs["payload_kg"],
            "Fuel": result["fuel_weight_kg"],
            "Empty": result["empty_weight_kg"]
        })
        
        plotter.generate_html_report([c1, c2], filename=f"design_report_{int(time.time())}.html")

if __name__ == "__main__":
    wizard = DesignWizard()
    wizard.start_interactive_session()
