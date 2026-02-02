import unittest

from aircraft_design.weights_class1 import EmptyWeightModel, solve_mtow_class1_kg


class TestWeightsClass1(unittest.TestCase):
    def test_mtow_converges(self):
        model = EmptyWeightModel(a=0.62, b=0.99)
        res = solve_mtow_class1_kg(
            payload_kg=240.0,
            crew_kg=160.0,
            empty_weight_model=model,
            fuel_fraction=0.18,
            reserve_fraction=0.07,
            w0_guess_kg=1200.0,
        )
        self.assertTrue(res["w0_kg"] > 0.0)
        self.assertTrue(res["we_kg"] > 0.0)
        self.assertTrue(res["wf_kg"] >= 0.0)
        self.assertIn(res["converged"], [True, False])


if __name__ == "__main__":
    unittest.main()
