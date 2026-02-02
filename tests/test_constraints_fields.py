import json
import unittest
from pathlib import Path

from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design


class TestConstraintsFields(unittest.TestCase):
    def test_constraints_has_feasible_and_worst(self):
        raw = json.loads(Path("examples/fixed_wing_ga_single.json").read_text(encoding="utf-8"))
        res = run_fixed_wing_overall_design(raw)
        c = res.get("constraints", {})
        self.assertIn("feasible", c)
        self.assertIn("worst", c)
        self.assertIsInstance(c.get("worst", None), dict)


if __name__ == "__main__":
    unittest.main()
