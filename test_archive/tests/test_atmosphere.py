import unittest

from aircraft_design.atmosphere import isa_tropopause


class TestAtmosphere(unittest.TestCase):
    def test_isa_sea_level(self):
        s = isa_tropopause(0.0)
        self.assertAlmostEqual(s.t_k, 288.15, places=2)
        self.assertAlmostEqual(s.p_pa, 101325.0, delta=200.0)
        self.assertAlmostEqual(s.rho_kg_m3, 1.225, delta=0.01)


if __name__ == "__main__":
    unittest.main()
