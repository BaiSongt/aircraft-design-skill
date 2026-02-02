import unittest
import sys
import os
import math

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aircraft_design.geometry_shape import calculate_cross_sectional_area_distribution


class TestGeometryAreaRule(unittest.TestCase):
    def test_area_distribution_simple(self):
        # 1. Setup simple fuselage: Cylinder of radius 1.0 (Area = pi)
        # Length 10m.
        # Stations: x=0 r=1, x=10 r=1.
        stations = [
            {"x_m": 0.0, "radius_y_m": 1.0, "radius_z_m": 1.0, "n": 2.0},
            {"x_m": 10.0, "radius_y_m": 1.0, "radius_z_m": 1.0, "n": 2.0},
        ]

        # 2. Setup simple wing: Rectangular, Chord=1, Span=4, Thickness=0.1
        # Area = Span * Thickness * Chord approx?
        # No, thickness varies. Max thickness t_c=0.1.
        # Cross sectional area of wing at any x in chord:
        # A_wing = 2 * integral(z dy).
        # For rectangular wing, airfoil is same everywhere.
        # A_wing(x) = Span * z_airfoil(x).
        # Max thickness at ~30% chord. z_max = 0.5 * t * c.
        # Wait, z is thickness distribution.

        wing_s_ref = 4.0  # Span 4, Chord 1
        wing_ar = 4.0  # b^2/S = 16/4 = 4
        wing_tr = 1.0  # Rectangular
        wing_sweep = 0.0
        wing_tc = 0.1
        wing_x_off = 4.0  # Wing starts at x=4

        # 3. No tail for simplicity first
        tail_layout = {"surfaces": []}

        dist = calculate_cross_sectional_area_distribution(
            fuselage_stations=stations,
            fuselage_length_m=10.0,
            wing_s_ref_m2=wing_s_ref,
            wing_aspect_ratio=wing_ar,
            wing_taper_ratio=wing_tr,
            wing_sweep_quarter_chord_deg=wing_sweep,
            wing_t_c=wing_tc,
            wing_x_offset_m=wing_x_off,
            tail_layout=tail_layout,
            n_points=21,  # 0.0, 0.5, ..., 10.0
        )

        # Check points
        # x=2.0: Only fuselage. Area = pi * 1 * 1 = 3.14159
        p2 = next(d for d in dist if abs(d["x_m"] - 2.0) < 1e-3)
        self.assertAlmostEqual(p2["area_fuselage_m2"], math.pi, places=2)
        self.assertAlmostEqual(p2["area_wing_m2"], 0.0, places=4)

        # x=4.5: Fuselage + Wing (Mid chord)
        # Wing starts at 4.0, ends at 5.0 (Chord=1).
        # x=4.5 is 50% chord.
        # NACA 0010 thickness at 0.5c.
        # t(0.5) approx...
        # 5 * 0.1 * (0.2969*sqrt(0.5) - 0.1260*0.5 - ...)
        # Let's trust the code calculation but verify it's > 0
        p45 = next(d for d in dist if abs(d["x_m"] - 4.5) < 1e-3)
        self.assertAlmostEqual(p45["area_fuselage_m2"], math.pi, places=2)
        self.assertGreater(p45["area_wing_m2"], 0.0)

        # Wing max thickness is usually around 0.3c (x=4.3)
        # Check integration works (fuselage area constant)
        for p in dist:
            self.assertAlmostEqual(p["area_fuselage_m2"], math.pi, places=2)

    def test_super_ellipse_area(self):
        # Test n=4 (Square-ish)
        # Area should be > pi*a*b
        # Area = 4 * a * b * (Gamma(1.25))^2 / Gamma(1.5) approx 3.7
        # vs Pi = 3.14

        stations = [
            {"x_m": 0.0, "radius_y_m": 1.0, "radius_z_m": 1.0, "n": 4.0},
            {"x_m": 1.0, "radius_y_m": 1.0, "radius_z_m": 1.0, "n": 4.0},
        ]
        dist = calculate_cross_sectional_area_distribution(
            fuselage_stations=stations,
            fuselage_length_m=1.0,
            wing_s_ref_m2=0.0,
            wing_aspect_ratio=1.0,
            wing_taper_ratio=1.0,
            wing_sweep_quarter_chord_deg=0.0,
            wing_t_c=0.1,
            wing_x_offset_m=0.0,
            tail_layout={"surfaces": []},
            n_points=3,
        )

        area_n4 = dist[0]["area_fuselage_m2"]
        self.assertGreater(area_n4, 3.14159)
        self.assertLess(area_n4, 4.0)  # Bounded by square 2x2=4? No, radius is semi-axis.
        # Dimensions are -1 to 1. Width 2, Height 2. Square area = 4.
        # n=infinity -> Square area 4.
        # n=2 -> Circle area 3.14.
        # n=4 -> Between.

        self.assertTrue(3.14 < area_n4 < 4.0)


if __name__ == "__main__":
    unittest.main()
