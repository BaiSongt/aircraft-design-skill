import json
import unittest
from pathlib import Path

from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design
from aircraft_design.geometry_parametric import Fuselage, ParametricGeometry, Tail, WingPlanform
from aircraft_design.openvsp_bridge import write_openvsp_script


class TestOpenVSPScript(unittest.TestCase):
    def test_openvsp_script_is_written(self):
        raw = json.loads(Path("examples/fixed_wing_ga_single.json").read_text(encoding="utf-8"))
        res = run_fixed_wing_overall_design(raw)
        s_ref = res.get("sizing", {}).get("s_m2", None)
        self.assertIsInstance(s_ref, (int, float))
        geom = ParametricGeometry(
            wing=WingPlanform(
                aspect_ratio=float(raw["sizing"]["aspect_ratio"]),
                taper_ratio=0.45,
                sweep_quarter_chord_deg=5.0,
                t_c=0.12,
            ),
            fuselage=Fuselage(length_m=7.5, diameter_m=1.2),
            tail=Tail(area_ratio_to_wing=0.22),
        )
        out_path = Path("out/openvsp_generate_test_artifact.py").resolve()
        p = write_openvsp_script(geom=geom, s_ref_m2=float(s_ref), out_path=out_path)
        txt = p.read_text(encoding="utf-8")
        self.assertIn("import openvsp as vsp", txt)
        self.assertIn("vsp.AddGeom('WING')", txt)
        self.assertIn("vsp.WriteVSPFile('generated.vsp3')", txt)


if __name__ == "__main__":
    unittest.main()
