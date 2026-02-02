import json
import unittest
from pathlib import Path

from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design
from aircraft_design.report import render_markdown_report


class TestFixedWingEndToEnd(unittest.TestCase):
    def test_example_runs(self):
        example = Path("examples/fixed_wing_ga_single.json")
        with example.open("r", encoding="utf-8") as f:
            inputs = json.load(f)

        res = run_fixed_wing_overall_design(inputs)
        self.assertIn("weights", res)
        self.assertIn("sizing", res)
        self.assertIn("aero", res)
        self.assertIn("constraints", res)
        self.assertIn("mission_breakdown", res)
        self.assertIn("structures", res)
        self.assertTrue(res["weights"]["w0_kg"] > 0.0)
        self.assertTrue(res["sizing"]["s_m2"] > 0.0)
        names = [c["name"] for c in res["constraints"]["checks"]]
        self.assertIn("takeoff_distance", names)
        self.assertIn("landing_distance", names)
        self.assertIn("takeoff_climb_gradient", names)

        md = render_markdown_report(res)
        self.assertIn("风险矩阵", md)
        self.assertIn("推荐调参方向", md)
        self.assertIn("AI 专家解读", md)


if __name__ == "__main__":
    unittest.main()
