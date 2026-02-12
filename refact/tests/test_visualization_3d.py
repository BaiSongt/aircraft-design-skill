import unittest

from aircraft_design.utils.visualization_3d import (
    build_fuselage_cylinder,
    build_tail_mesh,
    build_wing_mesh,
    mesh_to_obj,
    render_geometry_viewer_html,
)


class TestVisualization3D(unittest.TestCase):
    def test_mesh_and_html_render(self):
        fus = build_fuselage_cylinder(length_m=8.0, diameter_m=1.2)
        wings = build_wing_mesh(
            s_ref_m2=12.0,
            aspect_ratio=9.0,
            taper_ratio=0.45,
            sweep_quarter_chord_deg=5.0,
            t_c=0.12,
            x_offset_m=0.0,
            z_offset_m=0.0,
        )
        tails = build_tail_mesh(
            wing_s_ref_m2=12.0,
            wing_aspect_ratio=9.0,
            wing_taper_ratio=0.45,
            sweep_quarter_chord_deg=5.0,
            t_c=0.12,
            tail_area_ratio_to_wing=0.22,
            fuselage_length_m=8.0,
            fuselage_diameter_m=1.2,
        )
        parts = [fus, *wings, *tails]
        self.assertGreater(len(parts), 2)
        html = render_geometry_viewer_html(parts=parts, title="T")
        self.assertIn("<html", html.lower())
        self.assertIn("three.min.js", html)
        self.assertIn("降级渲染", html)
        self.assertIn("cv_top", html)
        self.assertIn("cv_side", html)
        self.assertIn("cv_front", html)
        self.assertIn("cv_iso", html)
        self.assertIn("const layout", html)
        obj = mesh_to_obj(parts)
        self.assertIn("\no fuselage\n", "\n" + obj)
        self.assertIn("\nv ", "\n" + obj)
        self.assertIn("\nf ", "\n" + obj)


if __name__ == "__main__":
    unittest.main()
