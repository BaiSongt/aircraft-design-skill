import unittest

from aircraft_design.geometry_detailed import geometry_detailed_from_inputs, naca4_coordinates


class TestGeometryDetailed(unittest.TestCase):
    def test_naca4_coords(self):
        pts = naca4_coordinates(code="2412", n=81)
        self.assertGreater(len(pts), 100)
        self.assertTrue(all(len(p) == 2 for p in pts))

    def test_geometry_detailed_parsing(self):
        inputs = {
            "geometry_detailed": {
                "wing": {"airfoil": {"type": "naca4", "code": "0012", "n": 61}},
                "fuselage": {"stations": [{"x_m": 0.0, "radius_m": 0.0}, {"x_m": 1.0, "radius_m": 0.5}]},
            }
        }
        gd = geometry_detailed_from_inputs(inputs)
        self.assertIsInstance(gd, dict)
        self.assertIn("wing", gd)
        self.assertIn("fuselage", gd)
        self.assertEqual(gd["wing"]["airfoil"]["code"], "0012")


if __name__ == "__main__":
    unittest.main()
