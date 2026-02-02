from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aircraft_design.geometry_parametric import ParametricGeometry


def _ensure_project_root() -> None:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def _build_geom_fallback(inputs: dict) -> ParametricGeometry | None:
    _ensure_project_root()
    from aircraft_design.geometry_parametric import (
        Fuselage,
        ParametricGeometry,
        Tail,
        WingPlanform,
        geometry_from_inputs,
    )

    geom = geometry_from_inputs(inputs)
    if geom is not None:
        return geom
    if not isinstance(inputs.get("geometry", None), dict) or not isinstance(inputs.get("sizing", None), dict):
        return None
    g = inputs.get("geometry", {})
    s = inputs.get("sizing", {})
    ar = s.get("aspect_ratio", None)
    if not isinstance(ar, (int, float)):
        return None
    return ParametricGeometry(
        wing=WingPlanform(
            aspect_ratio=float(ar),
            taper_ratio=float(s.get("taper_ratio", 0.45)),
            sweep_quarter_chord_deg=float(s.get("sweep_quarter_chord_deg", 0.0)),
            t_c=float(g.get("wing_t_c", 0.12)),
        ),
        fuselage=Fuselage(
            length_m=float(g.get("fuselage_length_m", 7.5)), diameter_m=float(g.get("fuselage_diameter_m", 1.2))
        ),
        tail=Tail(area_ratio_to_wing=float(g.get("tail_area_ratio", 0.22))),
    )


def main() -> int:
    _ensure_project_root()
    from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design
    from aircraft_design.input_schema import normalize_inputs, validate_run_inputs
    from aircraft_design.openvsp_bridge import run_openvsp_script, write_openvsp_script

    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_openvsp_script.py <input.json> [--out <path>] [--run]")
        return 2

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        print(f"Input not found: {input_path}")
        return 2

    out_path = None
    run_flag = False
    i = 2
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == "--out" and i + 1 < len(sys.argv):
            out_path = Path(sys.argv[i + 1]).resolve()
            i += 2
            continue
        if a == "--run":
            run_flag = True
            i += 1
            continue
        print(f"Unknown arg: {a}")
        return 2

    inputs = json.loads(input_path.read_text(encoding="utf-8"))
    try:
        if not inputs.get("_normalized", False):
            inputs, _warnings = normalize_inputs(inputs)
    except Exception as e:
        print(f"Input normalization failed: {e}")
        return 2
    validation = validate_run_inputs(inputs)
    if validation.get("warnings"):
        print("Input validation warnings:")
        for w in validation["warnings"]:
            print(f"- {w}")
    if validation.get("errors"):
        print("Input validation failed:")
        for err in validation["errors"]:
            print(f"- {err}")
        return 2
    geom = _build_geom_fallback(inputs)
    if geom is None:
        print("No geometry available. Provide geometry_parametric, or provide legacy geometry + sizing.aspect_ratio.")
        return 2

    results = run_fixed_wing_overall_design(inputs)
    s_ref = results.get("sizing", {}).get("s_m2", None)
    if not isinstance(s_ref, (int, float)) or float(s_ref) <= 0.0:
        print("Could not determine sizing.s_m2 from overall design results.")
        return 2

    if out_path is None:
        out_dir = Path("out").resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "openvsp_generate.py"

    p = write_openvsp_script(geom=geom, s_ref_m2=float(s_ref), out_path=out_path)
    print(f"Wrote: {p}")

    if run_flag:
        try:
            run_openvsp_script(script_path=p)
            print("Ran OpenVSP script successfully.")
        except Exception as e:
            print(f"Failed to run OpenVSP script: {e}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
