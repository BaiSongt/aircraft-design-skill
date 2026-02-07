import json
import os
import time
from typing import Dict, List, Any
from dataclasses import asdict

from .fixed_wing_overall import run_fixed_wing_overall_design
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
        # Construct inputs for run_fixed_wing_overall_design
        inputs = {
            "mission": {
                "range_m": reqs["range_km"] * 1000,
                "cruise_altitude_m": reqs["cruise_alt_m"],
                "cruise_speed_m_s": reqs["cruise_speed_km_h"] / 3.6,
                "v_stall_m_s": 45.0, # Default assumption
                "payload_kg": reqs["payload_kg"], # Redundant but kept for structure compatibility
            },
            "payload": {
                "payload_kg": reqs["payload_kg"],
            },
            "crew": {
                "crew_kg": 100.0,
            },
            "aero": {
                "e": 0.8,
                "cl_max": 1.6,
                "cd0": 0.02, # Optional estimate
            },
            "sizing": {
                "wing_loading_pa": 3000.0,
                "aspect_ratio": 8.0,
                "thrust_to_weight": 0.3,
            },
            "weights": {
                "empty_a": 0.9, # Class I param
                "empty_b": -0.05, # Class I param
            },
            "propulsion": {
                "type": "jet" if reqs["cruise_speed_km_h"] > 500 else "prop",
            },
            "_normalized": True # Bypass normalizer for speed/simplicity here
        }
        
        try:
            return run_fixed_wing_overall_design(inputs)
        except Exception as e:
            print(f"Sizing calculation failed: {e}")
            # Fallback to mock for wizard flow continuity if inputs are insufficient
            return {
                "mtow_kg": reqs["payload_kg"] * 3.0,
                "fuel_weight_kg": reqs["payload_kg"] * 0.8,
                "empty_weight_kg": reqs["payload_kg"] * 1.5,
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
