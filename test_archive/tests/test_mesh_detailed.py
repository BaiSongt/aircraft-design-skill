import unittest

from aircraft_design.geometry_detailed import naca4_coordinates
from aircraft_design.visualization_3d import (
    build_fuselage_loft,
    build_vertical_tail_airfoil_loft_mesh,
    build_wing_airfoil_loft_mesh,
    build_wing_airfoil_mesh,
)


class TestMeshDetailed(unittest.TestCase):
    def test_fuselage_loft_mesh(self):
        fus = build_fuselage_loft(
            stations=[{"x_m": 0.0, "radius_m": 0.0}, {"x_m": 1.0, "radius_m": 0.5}, {"x_m": 2.0, "radius_m": 0.0}]
        )
        self.assertGreater(len(fus.vertices), 0)
        self.assertGreater(len(fus.indices), 0)

    def test_fuselage_loft_mesh_ellipse(self):
        fus = build_fuselage_loft(
            stations=[
                {"x_m": 0.0, "radius_y_m": 0.0, "radius_z_m": 0.0},
                {"x_m": 1.0, "radius_y_m": 0.6, "radius_z_m": 0.4},
                {"x_m": 2.0, "radius_y_m": 0.0, "radius_z_m": 0.0},
            ]
        )
        self.assertGreater(len(fus.vertices), 0)
        self.assertGreater(len(fus.indices), 0)

    def test_wing_airfoil_mesh(self):
        af = naca4_coordinates(code="0012", n=61)
        parts = build_wing_airfoil_mesh(
            airfoil_coords=af,
            s_ref_m2=12.0,
            aspect_ratio=9.0,
            taper_ratio=0.45,
            sweep_quarter_chord_deg=5.0,
            x_offset_m=0.0,
            z_offset_m=0.0,
            name_prefix="wing",
        )
        self.assertEqual(len(parts), 2)
        self.assertGreater(len(parts[0].vertices), 0)
        self.assertGreater(len(parts[0].indices), 0)

    def test_wing_airfoil_loft_mesh_tip_and_controls(self):
        root = naca4_coordinates(code="2412", n=81)
        tip = naca4_coordinates(code="0012", n=81)
        parts = build_wing_airfoil_loft_mesh(
            root_airfoil_coords=root,
            tip_airfoil_coords=tip,
            s_ref_m2=12.0,
            aspect_ratio=9.0,
            taper_ratio=0.45,
            sweep_quarter_chord_deg=5.0,
            x_offset_m=0.0,
            z_offset_m=0.0,
            dihedral_deg=3.0,
            incidence_deg=2.0,
            spanwise_control_points=[
                {"eta": 0.0, "twist_deg": 2.0, "thickness_scale": 1.0},
                {
                    "eta": 1.0,
                    "twist_deg": -3.0,
                    "chord_scale": 1.0,
                    "thickness_scale": 0.8,
                    "x_le_offset_m": 0.02,
                    "z_offset_m": 0.01,
                },
            ],
            name_prefix="wing",
        )
        self.assertEqual(len(parts), 2)
        self.assertGreater(len(parts[0].vertices), 0)
        self.assertGreater(len(parts[0].indices), 0)

    def test_vertical_tail_airfoil_loft_mesh(self):
        root = naca4_coordinates(code="0012", n=81)
        tip = naca4_coordinates(code="0008", n=81)
        part = build_vertical_tail_airfoil_loft_mesh(
            root_airfoil_coords=root,
            tip_airfoil_coords=tip,
            s_ref_m2=1.0,
            aspect_ratio=1.8,
            taper_ratio=0.7,
            sweep_quarter_chord_deg=25.0,
            x_offset_m=4.0,
            y_offset_m=0.0,
            z_offset_m=0.0,
            spanwise_control_points=[{"eta": 0.0, "twist_deg": 0.0}, {"eta": 1.0, "twist_deg": 5.0}],
            name="vtail",
        )
        self.assertGreater(len(part.vertices), 0)
        self.assertGreater(len(part.indices), 0)


if __name__ == "__main__":
    unittest.main()
