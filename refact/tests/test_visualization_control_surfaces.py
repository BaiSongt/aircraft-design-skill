import unittest
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aircraft_design.utils.visualization_3d import build_wing_airfoil_loft_mesh


class TestVisualizationControlSurfaces(unittest.TestCase):
    def setUp(self):
        # Basic airfoil: diamond shape
        self.airfoil = [[0.0, 0.0], [0.5, 0.1], [1.0, 0.0], [0.5, -0.1], [0.0, 0.0]]
        # Make sure it has enough points (visualization requires >=10 points usually for safety,
        # though the code says >=10 in validation)
        # Let's generate a simple NACA 0012-like dummy with more points
        self.airfoil = []
        for i in range(11):
            x = i / 10.0
            y = 0.12 * 5.0 * (0.2969 * x**0.5 - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)
            self.airfoil.append([x, y])
        # Bottom surface (symmetric)
        for i in range(9, -1, -1):
            x = i / 10.0
            y = -0.12 * 5.0 * (0.2969 * x**0.5 - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)
            self.airfoil.append([x, y])

    def test_control_surface_mesh_split(self):
        # Case 1: No control surfaces
        parts_no_cs = build_wing_airfoil_loft_mesh(
            root_airfoil_coords=self.airfoil,
            tip_airfoil_coords=self.airfoil,
            s_ref_m2=10.0,
            aspect_ratio=10.0,
            taper_ratio=1.0,
            sweep_quarter_chord_deg=0.0,
            x_offset_m=0.0,
            z_offset_m=0.0,
            control_surfaces=[],
        )

        # Case 2: With control surfaces (should split mesh spanwise)
        # Aileron from eta 0.7 to 0.95
        cs_def = [
            {"name": "aileron", "eta_in": 0.7, "eta_out": 0.95, "chord_fraction": 0.25, "deflection_deg_preview": 0.0}
        ]
        parts_with_cs = build_wing_airfoil_loft_mesh(
            root_airfoil_coords=self.airfoil,
            tip_airfoil_coords=self.airfoil,
            s_ref_m2=10.0,
            aspect_ratio=10.0,
            taper_ratio=1.0,
            sweep_quarter_chord_deg=0.0,
            x_offset_m=0.0,
            z_offset_m=0.0,
            control_surfaces=cs_def,
        )

        # We expect more vertices/triangles in parts_with_cs because of extra spanwise cuts
        # Check number of vertices in Right wing (index 0 usually R, index 1 L)
        # parts_no_cs has default sections at eta=0 and 1. (plus maybe others if control points exist)
        # parts_with_cs should have sections at 0, 0.7, 0.95, 1.0

        # Verify vertex count
        # Each section has N points. 2 sections = 2N points (approx, + cap).
        # 4 sections = 4N points.

        v_no = len(parts_no_cs[0].vertices)
        v_cs = len(parts_with_cs[0].vertices)

        self.assertGreater(v_cs, v_no, "Mesh with control surfaces should have more vertices due to splits.")

    def test_control_surface_deflection(self):
        # Verify that deflection actually changes geometry

        # Aileron deflected 20 degrees down
        cs_def = [
            {
                "name": "aileron",
                "eta_in": 0.5,  # large section
                "eta_out": 1.0,
                "chord_fraction": 0.3,
                "deflection_deg_preview": 20.0,
            }
        ]

        parts_deflected = build_wing_airfoil_loft_mesh(
            root_airfoil_coords=self.airfoil,
            tip_airfoil_coords=self.airfoil,
            s_ref_m2=10.0,
            aspect_ratio=10.0,
            taper_ratio=1.0,
            sweep_quarter_chord_deg=0.0,
            x_offset_m=0.0,
            z_offset_m=0.0,
            control_surfaces=cs_def,
        )

        parts_undeflected = build_wing_airfoil_loft_mesh(
            root_airfoil_coords=self.airfoil,
            tip_airfoil_coords=self.airfoil,
            s_ref_m2=10.0,
            aspect_ratio=10.0,
            taper_ratio=1.0,
            sweep_quarter_chord_deg=0.0,
            x_offset_m=0.0,
            z_offset_m=0.0,
            control_surfaces=[{**cs_def[0], "deflection_deg_preview": 0.0}],
        )

        # Check vertices in the deflected region (eta > 0.5)
        # Since it's a constant chord wing with 0 sweep, geometry is simple.
        # Deflected wing should have different Z values near Trailing Edge.

        # Let's compare bounding boxes or specific points
        def get_bounds(part):
            zs = part.vertices[2::3]  # every 3rd starting at 2
            return min(zs), max(zs)

        min_z_un, max_z_un = get_bounds(parts_undeflected[0])
        min_z_def, max_z_def = get_bounds(parts_deflected[0])

        # With 20 deg deflection (TE down?), the Z range should likely expand downwards or change.
        # If original is symmetric, min_z ~ -max_z.
        # If deflected down, min_z should decrease (more negative).

        self.assertNotAlmostEqual(min_z_def, min_z_un, delta=1e-4, msg="Deflection should change Z bounds")

        # Also check that Leading Edge (x < hinge) is NOT moved
        # Hinge is at 1-0.3 = 0.7 chord.
        # Check a point at LE (x ~ 0)
        # Vertices are flat list.
        # This is harder to check on raw mesh without knowing indices.
        # But global bounds check confirms *something* moved.


if __name__ == "__main__":
    unittest.main()
