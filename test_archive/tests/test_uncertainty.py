import json
import unittest
from pathlib import Path

from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design


class TestUncertainty(unittest.TestCase):
    def test_uncertainty_cases_exist_when_enabled(self):
        example = Path("examples/fixed_wing_ga_single.json")
        with example.open("r", encoding="utf-8") as f:
            inputs = json.load(f)
        inputs["uncertainty"] = {"enabled": True}
        res = run_fixed_wing_overall_design(inputs)
        unc = res.get("uncertainty", {})
        self.assertIsInstance(unc, dict)
        self.assertIn("cases", unc)
        self.assertGreaterEqual(len(unc.get("cases", [])), 1)


if __name__ == "__main__":
    unittest.main()
