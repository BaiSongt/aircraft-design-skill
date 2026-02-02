import json
import unittest
from pathlib import Path

from aircraft_design.geometry_shape import (
    derive_tail_layout,
    fuselage_stations_from_control_points,
    geometry_shape_from_inputs,
)


class TestGeometryShape(unittest.TestCase):
    def test_fuselage_control_points_to_stations(self):
        stations = fuselage_stations_from_control_points(
            length_m=10.0,
            max_radius_y_m=0.5,
            max_radius_z_m=0.5,
            control_points=[
                {"x_rel": 0.0, "radius_rel": 0.0},
                {"x_rel": 0.2, "radius_rel": 1.0},
                {"x_rel": 1.0, "radius_rel": 0.0},
            ],
            n_stations=21,
        )
        self.assertEqual(len(stations), 21)
        self.assertAlmostEqual(stations[0]["x_m"], 0.0)
        self.assertAlmostEqual(stations[-1]["x_m"], 10.0)

    def test_geometry_shape_parsing_example(self):
        raw = json.loads(Path("examples/fixed_wing_ga_single.json").read_text(encoding="utf-8"))
        gs = geometry_shape_from_inputs(raw)
        self.assertIsInstance(gs, dict)
        self.assertIn("layout", gs)
        self.assertIn("fuselage", gs)
        self.assertIn("stations", gs["fuselage"])
        self.assertIn("wing", gs)
        self.assertIn("planform", gs["wing"])
        self.assertIn("tail", gs)
        self.assertIn("horizontal", gs["tail"])
        self.assertIn("vertical", gs["tail"])

    def test_derive_t_tail_sets_horizontal_z_from_vertical_span(self):
        tail_cfg = {
            "layout": {"type": "t_tail"},
            "horizontal": {
                "planform": {
                    "area_ratio_to_wing": 0.2,
                    "aspect_ratio": 4.0,
                    "taper_ratio": 0.6,
                    "x_offset_m": 5.0,
                }
            },
            "vertical": {
                "planform": {
                    "area_ratio_to_wing": 0.08,
                    "aspect_ratio": 2.0,
                    "taper_ratio": 0.7,
                    "x_offset_m": 5.0,
                    "z_offset_m": 0.3,
                }
            },
        }
        derived = derive_tail_layout(
            tail_cfg=tail_cfg, wing_s_ref_m2=20.0, fuselage_length_m=10.0, fuselage_diameter_m=1.2
        )
        span_v = (2.0 * (20.0 * 0.08)) ** 0.5
        self.assertAlmostEqual(float(derived["horizontal"]["z_offset_m"]), 0.3 + span_v, places=6)
        self.assertTrue(
            any(isinstance(s, dict) and s.get("builder") == "vertical_loft" for s in derived.get("surfaces", []))
        )
        self.assertTrue(
            any(isinstance(s, dict) and s.get("builder") == "wing_loft" for s in derived.get("surfaces", []))
        )

    def test_derive_v_tail_creates_single_canted_surface(self):
        tail_cfg = {
            "layout": {"type": "v_tail", "cant_deg": 40.0},
            "horizontal": {
                "planform": {
                    "area_ratio_to_wing": 0.18,
                    "aspect_ratio": 4.0,
                    "taper_ratio": 0.6,
                    "x_offset_m": 5.0,
                    "z_offset_m": 0.4,
                }
            },
        }
        derived = derive_tail_layout(
            tail_cfg=tail_cfg, wing_s_ref_m2=20.0, fuselage_length_m=10.0, fuselage_diameter_m=1.2
        )
        surfaces = derived.get("surfaces", [])
        self.assertEqual(len(surfaces), 1)
        self.assertEqual(surfaces[0].get("builder"), "wing_loft")
        self.assertEqual(surfaces[0].get("name_prefix"), "vtail")
        self.assertAlmostEqual(float(surfaces[0].get("dihedral_deg")), 40.0, places=6)
        self.assertIn("v_tail", derived.get("equivalent", {}))

    def test_derive_twin_fin_creates_two_fins(self):
        tail_cfg = {
            "layout": {"type": "twin_fin", "fin_separation_m": 1.0},
            "vertical": {
                "planform": {
                    "area_ratio_to_wing": 0.1,
                    "aspect_ratio": 1.8,
                    "taper_ratio": 0.7,
                    "x_offset_m": 5.0,
                    "z_offset_m": 0.2,
                }
            },
        }
        derived = derive_tail_layout(
            tail_cfg=tail_cfg, wing_s_ref_m2=20.0, fuselage_length_m=10.0, fuselage_diameter_m=1.2
        )
        surfaces = derived.get("surfaces", [])
        self.assertEqual(len(surfaces), 2)
        ys = sorted(float(s.get("y_offset_m")) for s in surfaces)
        self.assertAlmostEqual(ys[0], -0.5, places=6)
        self.assertAlmostEqual(ys[1], 0.5, places=6)


if __name__ == "__main__":
    unittest.main()
