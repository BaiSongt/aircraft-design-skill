import json
import unittest
from pathlib import Path
from aircraft_design.design_loop_orchestrator import DesignOrchestrator

class TestDesignOrchestrator(unittest.TestCase):
    def test_detailed_sizing_loop(self):
        # Use absolute path or relative to project root
        example = Path("examples/fixed_wing_ga_single.json")
        if not example.exists():
            # Fallback for running from tests dir
            example = Path("../examples/fixed_wing_ga_single.json")
            
        with example.open("r", encoding="utf-8") as f:
            inputs = json.load(f)
            
        orchestrator = DesignOrchestrator(inputs)
        
        # 1. Run Initial Sizing (Class I)
        initial_state = orchestrator.run_initial_sizing()
        print(f"\nClass I MTOW: {initial_state.mtow_kg:.2f} kg")
        self.assertGreater(initial_state.mtow_kg, 1000.0)
        
        # 2. Run Detailed Sizing Loop (Class II)
        final_state = orchestrator.run_detailed_sizing_loop(max_iter=10)
        print(f"Class II MTOW: {final_state.mtow_kg:.2f} kg")
        print(f"Fuel Fraction: {final_state.performance_margins.get('mission_fuel_fraction', 0.0):.4f}")
        print(f"L/D Cruise: {final_state.performance_margins.get('l_d_cruise', 0.0):.2f}")
        
        self.assertGreater(final_state.mtow_kg, 1000.0)
        self.assertIn("mission_fuel_fraction", final_state.performance_margins)
        
        # Check that we have detailed weights
        self.assertIn("wing", final_state.component_weights)
        self.assertIn("propulsion", final_state.component_weights)
        
        # Check reasonable fuel fraction
        ff = final_state.performance_margins.get('mission_fuel_fraction', 0.0)
        self.assertGreater(ff, 0.05)
        self.assertLess(ff, 0.6)

if __name__ == "__main__":
    unittest.main()
