from __future__ import annotations

import math
from pathlib import Path

from .geometry_parametric import ParametricGeometry


def can_import_openvsp() -> bool:
    try:
        import openvsp  # noqa: F401

        return True
    except Exception:
        return False


def write_openvsp_script(
    *,
    geom: ParametricGeometry | dict,
    s_ref_m2: float | None = None,
    out_path: str | Path | None = None,
    xform: dict | None = None,
) -> Path | str:
    """
    Write OpenVSP script.
    If geom is dict (geometry_shape format), generates a script from it.
    If geom is ParametricGeometry, uses its method.
    If out_path is None, returns the script string.
    """
    script = ""
    if isinstance(geom, dict):
        script = _geometry_dict_to_vsp_script(geom)
    else:
        if s_ref_m2 is None:
            raise ValueError("s_ref_m2 required for ParametricGeometry")
        script = geom.to_openvsp_script(s_ref_m2=s_ref_m2, xform=xform)

    if out_path is None:
        return script

    p = Path(out_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(script, encoding="utf-8")
    return p


def _geometry_dict_to_vsp_script(g: dict) -> str:
    lines = ["import openvsp as vsp", "", "vsp.ClearVSPModel()", "vsp.SetDefaultUnits( vsp.VSP_UNITS_SI )", ""]

    # Fuselage
    fus = g.get("fuselage", {})
    st = fus.get("stations", [])
    if st:
        lines.append("fuse_id = vsp.AddGeom('FUSELAGE')")
        # To do advanced fuselage in VSP, we usually add FUSELAGE and set sections.
        # But VSP python API for sections is complex (Cut/Paste sections).
        # Simplified: Set Length/Diameter and let it be default shape, OR just basic params.
        # For this demo, let's just set overall L/D if possible.
        # But we have stations.
        # Let's just create a simple fuselage with Length and Diameter based on max.

        # Find length and max diameter
        xs = [s["x_m"] for s in st]
        rys = [s["radius_y_m"] for s in st]
        length_m = max(xs) - min(xs)
        d = max(rys) * 2.0

        lines.append(f"vsp.SetParmVal(fuse_id, 'Length', 'Design', {length_m})")
        lines.append(f"vsp.SetParmVal(fuse_id, 'Diameter', 'Design', {d})")
        lines.append(f"vsp.SetParmVal(fuse_id, 'X_Location', 'XForm', {min(xs)})")
        lines.append("")

    # Wing
    wing = g.get("wing", {})
    pf = wing.get("planform", {})
    if pf:
        lines.append("wing_id = vsp.AddGeom('WING')")
        lines.append(
            f"vsp.SetParmVal(wing_id, 'Span', 'XSec_1', {math.sqrt(pf.get('s_ref_m2', 10) * pf.get('aspect_ratio', 6))})"
        )
        # Root/Tip chord approx
        b = math.sqrt(pf.get("s_ref_m2") * pf.get("aspect_ratio"))
        tr = pf.get("taper_ratio", 1.0)
        c_root = 2 * pf.get("s_ref_m2") / (b * (1 + tr))
        c_tip = c_root * tr

        lines.append(f"vsp.SetParmVal(wing_id, 'Root_Chord', 'XSec_1', {c_root})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Tip_Chord', 'XSec_1', {c_tip})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Sweep', 'XSec_1', {pf.get('sweep_quarter_chord_deg', 0)})")
        lines.append("vsp.SetParmVal(wing_id, 'ThickChord', 'XSec_1', 0.12)")  # Default
        lines.append(f"vsp.SetParmVal(wing_id, 'X_Location', 'XForm', {pf.get('x_offset_m', 0)})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Y_Location', 'XForm', {pf.get('y_offset_m', 0)})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Z_Location', 'XForm', {pf.get('z_offset_m', 0)})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Y_Rotation', 'XForm', {pf.get('incidence_deg', 0)})")
        lines.append("")

    lines.append("vsp.Update()")
    lines.append("")
    lines.append("vsp.WriteVSPFile('generated.vsp3')")

    return "\n".join(lines)


def run_openvsp_script(*, script_path: str | Path) -> None:
    try:
        import openvsp as vsp
    except Exception as e:
        raise RuntimeError(
            "openvsp python module not available. Install OpenVSP and use its Python environment."
        ) from e

    p = Path(script_path).resolve()
    code = p.read_text(encoding="utf-8")
    scope = {"vsp": vsp}
    exec(compile(code, str(p), "exec"), scope, scope)
