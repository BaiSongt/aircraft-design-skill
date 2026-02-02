import json
import unittest
from pathlib import Path

from aircraft_design.geometry_parametric import geometry_from_inputs
from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design


class TestGeometryParametric(unittest.TestCase):
    def test_geometry_from_inputs(self):
        inputs = {
            "geometry_parametric": {
                "wing": {"aspect_ratio": 9.0, "taper_ratio": 0.5, "sweep_quarter_chord_deg": 5.0, "t_c": 0.12},
                "fuselage": {"length_m": 8.0, "diameter_m": 1.3},
                "tail": {"area_ratio_to_wing": 0.22},
            }
        }
        g = geometry_from_inputs(inputs)
        self.assertIsNotNone(g)
        d = g.derived_from_sref(s_ref_m2=12.0)
        self.assertGreater(d.b_m, 0.0)

    def test_overall_design_accepts_geometry_parametric(self):
        raw = json.loads(Path("examples/fixed_wing_ga_single.json").read_text(encoding="utf-8"))
        raw["geometry_parametric"] = {
            "wing": {
                "aspect_ratio": float(raw["sizing"]["aspect_ratio"]),
                "taper_ratio": 0.45,
                "sweep_quarter_chord_deg": 0.0,
                "t_c": 0.12,
            },
            "fuselage": {"length_m": 7.5, "diameter_m": 1.2},
            "tail": {"area_ratio_to_wing": 0.22},
        }
        res = run_fixed_wing_overall_design(raw)
        self.assertIn("aero", res)
        self.assertIn("cd0_buildup", res.get("aero", {}))


if __name__ == "__main__":
    unittest.main()
