import json
import unittest
from pathlib import Path

from aircraft_design.input_schema import normalize_inputs
from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design
from aircraft_design.report import render_markdown_report


class TestInputSchema(unittest.TestCase):
    def test_defaults_injected(self):
        raw = json.loads(Path("examples/fixed_wing_ga_single.json").read_text(encoding="utf-8"))
        raw.pop("report", None)
        raw.pop("atmosphere", None)
        raw.pop("uncertainty", None)
        norm, warnings = normalize_inputs(raw)
        self.assertIsInstance(norm.get("report", {}).get("risk_thresholds", None), dict)
        self.assertIn("constraint_margin_ratio", norm["report"]["risk_thresholds"])
        self.assertIsInstance(norm.get("uncertainty", {}), dict)
        self.assertFalse(bool(norm["uncertainty"].get("enabled", True)))
        self.assertIsInstance(warnings, list)

    def test_bad_types_raise(self):
        raw = json.loads(Path("examples/fixed_wing_ga_single.json").read_text(encoding="utf-8"))
        raw["report"] = {"risk_thresholds": {"ld_cruise": {"red": "bad"}}}
        with self.assertRaises(ValueError):
            normalize_inputs(raw)

    def test_report_prints_thresholds(self):
        raw = json.loads(Path("examples/fixed_wing_ga_single.json").read_text(encoding="utf-8"))
        res = run_fixed_wing_overall_design(raw)
        md = render_markdown_report(res)
        self.assertIn("阈值与扰动（可配置）", md)
        self.assertIn("风险阈值", md)
        self.assertIn("constraint_margin_ratio", md)


if __name__ == "__main__":
    unittest.main()
