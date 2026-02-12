import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aircraft_design.class3_detailed.geometry_shape import geometry_shape_from_inputs, verify_geometric_constraints


class TestGeometryAdvancedFeatures(unittest.TestCase):
    def test_parametric_fuselage_and_modifiers(self):
        inputs = {
            "geometry_shape": {
                "layout": {"views": ["top"]},
                "fuselage": {
                    "axis": {"length_m": 10.0},
                    "profile": {
                        "mode": "parametric",
                        "max_radius_m": 1.0,
                        "nose_fineness_ratio": 2.0,  # Nose length 4m (D=2)
                        "tail_fineness_ratio": 2.0,  # Tail length 4m
                        "nose_shape": "ellipsoid",
                        "tail_shape": "conical",
                    },
                    "modifiers": {
                        "canopy": {
                            "x_rel": 0.4,  # Starts at 4m (End of nose)
                            "length_rel": 0.2,  # Length 2m
                            "height_m": 0.5,
                        },
                        "wing_fairing": {"radius_m": 0.2},
                    },
                },
                "wing": {
                    "planform": {
                        "s_ref_m2": 20.0,
                        "aspect_ratio": 5.0,  # b=10
                        "taper_ratio": 1.0,
                        "x_offset_m": 4.0,  # Wing at 4m
                    }
                },
            }
        }

        geom = geometry_shape_from_inputs(inputs)
        self.assertIsNotNone(geom)
        stations = geom["fuselage"]["stations"]

        # 1. Verify Length/Stations
        # 21 stations default.
        self.assertEqual(len(stations), 21)
        self.assertAlmostEqual(stations[-1]["x_m"], 10.0)

        # 2. Verify Nose Shape (x=2.0, half of nose length 4m)
        # Ellipsoid: r = r_max * sqrt(1 - ((L-x)/L)^2)
        # x=2, L=4. (4-2)/4 = 0.5. 0.5^2=0.25. sqrt(0.75)=0.866
        # r_max = 1.0. r=0.866.
        # Find closest station to x=2.0
        s2 = min(stations, key=lambda s: abs(s["x_m"] - 2.0))
        # Note: station generation interpolates control points.
        # With only 5 control points for nose, it might be approximate.
        # But let's check it's reasonable.
        self.assertTrue(0.8 < s2["radius_y_m"] < 0.9)

        # 3. Verify Canopy Bump
        # Canopy at x=4 to 6 (0.4 to 0.6 of 10m).
        # Max bump at x=5. Bump height 0.5.
        # Base radius at x=5 (Cylindrical part? Nose=4, Tail=4. Cyl=2. x=4 to 6 is Cyl.)
        # Wait, Nose 4m, Tail 4m. Cyl is 2m (from 4 to 6).
        # So x=5 is middle of cylinder. Base r=1.0.
        # Canopy adds 0.5 * sin(pi*0.5) = 0.5.
        # So r_z should be 1.5.
        s5 = min(stations, key=lambda s: abs(s["x_m"] - 5.0))
        self.assertAlmostEqual(s5["radius_z_m"], 1.5, delta=0.1)
        # r_y should be unaffected by canopy (only fairing affects y)

        # 4. Verify Wing Fairing
        # Wing at x=4. Chord? b=10, S=20 -> c=2.
        # Wing from x=4 to x=6.
        # Fairing radius 0.2.
        # At x=5, fairing adds bump.
        # r_y base = 1.0. + 0.2 = 1.2.
        self.assertAlmostEqual(s5["radius_y_m"], 1.2, delta=0.1)

    def test_constraints(self):
        geom = {
            "fuselage": {
                "stations": [
                    {"x_m": 0.0, "radius_y_m": 0.0, "radius_z_m": 0.0, "n": 2.0},
                    {"x_m": 5.0, "radius_y_m": 1.0, "radius_z_m": 1.0, "n": 2.0},
                    {"x_m": 10.0, "radius_y_m": 0.0, "radius_z_m": 0.0, "n": 2.0},
                ]
            }
        }

        # Point inside
        constraints_pass = {"hardpoints": {"pilot": {"x": 5.0, "y": 0.0, "z": 0.5}}}
        v_pass = verify_geometric_constraints(geom, constraints_pass)
        self.assertEqual(len(v_pass), 0)

        # Point outside
        constraints_fail = {"hardpoints": {"engine": {"x": 5.0, "y": 2.0, "z": 0.0}}}
        v_fail = verify_geometric_constraints(geom, constraints_fail)
        self.assertEqual(len(v_fail), 1)
        self.assertIn("outside", v_fail[0]["message"])


if __name__ == "__main__":
    unittest.main()
