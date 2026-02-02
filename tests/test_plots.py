import json
import unittest
from pathlib import Path

from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design
from aircraft_design.plots import render_constraints_ws_tw_svg


class TestPlots(unittest.TestCase):
    def test_constraints_svg_renders(self):
        example = Path("examples/fixed_wing_ga_single.json")
        with example.open("r", encoding="utf-8") as f:
            inputs = json.load(f)

        res = run_fixed_wing_overall_design(inputs)
        constraints = res.get("constraints", {})
        svg = render_constraints_ws_tw_svg(
            plot_data=constraints.get("plot_data", {}),
            design_point=constraints.get("design_point", {}),
        )
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("design_point", svg)


if __name__ == "__main__":
    unittest.main()
