import sys
import unittest
from pathlib import Path


def _ensure_project_root() -> None:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


class TestGeometryDerived(unittest.TestCase):
    def test_mac_calculation_simple(self):
        _ensure_project_root()
        from aircraft_design.class3_detailed.geometry_shape import calculate_mac_properties

        # Rectangular wing (taper=1.0, sweep=0)
        # S = 10, AR = 10 => b = 10, c = 1
        # MAC = c = 1
        # Y_MAC = b/4 = 2.5 (from centerline) -> Formula: b/6 * (1+2)/(1+1) = b/6 * 1.5 = b/4
        res = calculate_mac_properties(s_ref_m2=10.0, aspect_ratio=10.0, taper_ratio=1.0, sweep_quarter_chord_deg=0.0)
        self.assertAlmostEqual(res["mac_m"], 1.0)
        self.assertAlmostEqual(res["mac_y_m"], 2.5)
        self.assertAlmostEqual(res["mac_x_le_m"], 0.0)

    def test_mac_calculation_tapered(self):
        _ensure_project_root()
        from aircraft_design.class3_detailed.geometry_shape import calculate_mac_properties

        # Tapered wing (taper=0.0, sweep=0) -> Triangle
        # S=10, AR=10 => b=10, c_root=2
        # MAC = 2/3 * c_root = 4/3 = 1.333
        # Y_MAC = b/6 * (1)/1 = b/6 = 1.666
        res = calculate_mac_properties(s_ref_m2=10.0, aspect_ratio=10.0, taper_ratio=0.0, sweep_quarter_chord_deg=0.0)
        self.assertAlmostEqual(res["mac_m"], 1.3333333)
        self.assertAlmostEqual(res["mac_y_m"], 1.6666667)
        # X_LE_MAC:
        # tan_sweep_le = tan(0) + (1-0)/(10*1) = 0.1
        # x = y * 0.1 = 0.1666
        self.assertAlmostEqual(res["mac_x_le_m"], 0.1666667)

    def test_mac_calculation_swept(self):
        _ensure_project_root()
        from aircraft_design.class3_detailed.geometry_shape import calculate_mac_properties

        # Swept wing
        # AR=8, taper=0.45, sweep=25 deg
        s = 20.0
        ar = 8.0
        taper = 0.45
        sweep = 25.0
        res = calculate_mac_properties(s_ref_m2=s, aspect_ratio=ar, taper_ratio=taper, sweep_quarter_chord_deg=sweep)
        # Just check it runs and gives positive values
        self.assertGreater(res["mac_m"], 0.0)
        self.assertGreater(res["mac_y_m"], 0.0)
        self.assertGreater(res["mac_x_le_m"], 0.0)


if __name__ == "__main__":
    unittest.main()
