import unittest
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aircraft_design.class3_detailed.geometry_shape import fuselage_stations_from_control_points
from aircraft_design.utils.visualization_3d import build_fuselage_loft


class TestGeometrySuperEllipse(unittest.TestCase):
    def test_parameter_parsing(self):
        # Test that 'n' is parsed and interpolated correctly
        cps = [
            {"x_rel": 0.0, "radius_rel": 0.5, "n": 2.0},
            {"x_rel": 0.5, "radius_rel": 1.0, "n": 4.0},
            {"x_rel": 1.0, "radius_rel": 0.2, "n": 2.0},
        ]
        stations = fuselage_stations_from_control_points(
            length_m=10.0, max_radius_y_m=1.0, max_radius_z_m=1.0, control_points=cps, n_stations=5
        )

        # Expected xs: 0.0, 0.25, 0.5, 0.75, 1.0 -> 0, 2.5, 5.0, 7.5, 10.0 m
        # Expected ns: 2.0, 3.0, 4.0, 3.0, 2.0 (linear interp)

        self.assertEqual(len(stations), 5)
        self.assertAlmostEqual(stations[0]["n"], 2.0)
        self.assertAlmostEqual(stations[1]["n"], 3.0)
        self.assertAlmostEqual(stations[2]["n"], 4.0)
        self.assertAlmostEqual(stations[4]["n"], 2.0)

    def test_visualization_geometry(self):
        # Generate mesh for n=2 (circle) and n=4 (rounded square)
        # Use simple cylinder stations
        stations_n2 = [{"x_m": 0.0, "radius_m": 1.0, "n": 2.0}, {"x_m": 1.0, "radius_m": 1.0, "n": 2.0}]
        stations_n4 = [{"x_m": 0.0, "radius_m": 1.0, "n": 4.0}, {"x_m": 1.0, "radius_m": 1.0, "n": 4.0}]

        mesh_n2 = build_fuselage_loft(stations=stations_n2, n_circ=8)  # 8 points -> 45 deg increments
        mesh_n4 = build_fuselage_loft(stations=stations_n4, n_circ=8)

        # Points at indices 0 (0 deg), 1 (45 deg), 2 (90 deg)...
        # 0 deg: cos=1, sin=0. y=1, z=0. Should be same for both.
        # 45 deg: cos=0.707, sin=0.707.
        # n=2: y = 0.707
        # n=4: y = 0.707^(2/4) = sqrt(0.707) = 0.84

        # Vertex layout: [x, y, z] flat array.
        # First ring (x=0) is first (n_circ) vertices.
        # Index 0: 0 deg. Index 1: 45 deg.

        def get_yz(mesh, ring_idx, point_idx):
            # 3 coords per vertex
            # ring_idx * n_circ + point_idx
            offset = (ring_idx * 8 + point_idx) * 3
            return mesh.vertices[offset + 1], mesh.vertices[offset + 2]

        y2_0, z2_0 = get_yz(mesh_n2, 0, 0)
        y4_0, z4_0 = get_yz(mesh_n4, 0, 0)

        self.assertAlmostEqual(y2_0, 1.0)
        self.assertAlmostEqual(y4_0, 1.0)  # Should be same at 0 deg

        y2_45, z2_45 = get_yz(mesh_n2, 0, 1)  # 45 deg
        y4_45, z4_45 = get_yz(mesh_n4, 0, 1)

        # n=4 should be "larger" (more boxy) than n=2 at 45 deg
        self.assertGreater(abs(y4_45), abs(y2_45))
        self.assertGreater(abs(z4_45), abs(z2_45))

        # Verify n=1 (diamond)
        stations_n1 = [{"x_m": 0.0, "radius_m": 1.0, "n": 1.0}, {"x_m": 1.0, "radius_m": 1.0, "n": 1.0}]
        mesh_n1 = build_fuselage_loft(stations=stations_n1, n_circ=8)
        y1_45, z1_45 = get_yz(mesh_n1, 0, 1)

        # n=1 should be smaller (flat diagonal)
        self.assertLess(abs(y1_45), abs(y2_45))


if __name__ == "__main__":
    unittest.main()
