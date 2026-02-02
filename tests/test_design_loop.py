import json
import unittest
from pathlib import Path

from aircraft_design.design_loop import grid_search_design_point


class TestDesignLoop(unittest.TestCase):
    def test_grid_search_finds_solution(self):
        example = Path("examples/fixed_wing_ga_single.json")
        with example.open("r", encoding="utf-8") as f:
            inputs = json.load(f)

        res = grid_search_design_point(
            base_inputs=inputs,
            wing_loading_pa_grid=[1200.0, 1500.0],
            aspect_ratio_grid=[7.5, 8.5],
            thrust_to_weight_grid=[0.24, 0.28],
        )
        self.assertTrue(res.best_results["weights"]["w0_kg"] > 0.0)
        self.assertTrue(len(res.candidates) > 0)


if __name__ == "__main__":
    unittest.main()
