from __future__ import annotations

import math
from pathlib import Path

from .geometry_parametric import ParametricGeometry
from .geometry_detailed import ParametricGeometry as DetailedParametricGeometry
from .openvsp_interface import OpenVSPInterface


def can_import_openvsp() -> bool:
    return OpenVSPInterface().is_available()


def _convert_geometry_to_dict(
    geom: ParametricGeometry | DetailedParametricGeometry | dict, s_ref_m2: float | None = None
) -> dict:
    """
    Converts various geometry objects to a unified dictionary format for VSP generation.
    """
    if isinstance(geom, dict):
        return geom

    geom_dict = {}

    if isinstance(geom, ParametricGeometry):
        if s_ref_m2 is None:
            raise ValueError("s_ref_m2 required for ParametricGeometry")

        # Derive dimensions
        tail_area_total = geom.tail.area_ratio_to_wing * s_ref_m2
        ht_area = tail_area_total * 0.75
        vt_area = tail_area_total * 0.25

        # HT placement: 90% of fuselage length
        ht_x = geom.fuselage.length_m * 0.90
        vt_x = geom.fuselage.length_m * 0.85

        geom_dict = {
            "fuselage": {
                "length_m": geom.fuselage.length_m,
                "diameter_m": geom.fuselage.diameter_m,
            },
            "wing": {
                "s_ref_m2": s_ref_m2,
                "aspect_ratio": geom.wing.aspect_ratio,
                "taper_ratio": geom.wing.taper_ratio,
                "sweep_deg": geom.wing.sweep_quarter_chord_deg,
                "t_c": geom.wing.t_c,
                "x_m": geom.fuselage.length_m * 0.4,
            },
            "horizontal_tail": {
                "s_ref_m2": ht_area,
                "aspect_ratio": 4.0,
                "taper_ratio": 0.5,
                "sweep_deg": 20.0,
                "x_m": ht_x,
                "z_m": 0.5,
            },
            "vertical_tail": {
                "s_ref_m2": vt_area,
                "aspect_ratio": 1.5,
                "taper_ratio": 0.6,
                "sweep_deg": 30.0,
                "x_m": vt_x,
                "z_m": 0.5,
                "y_rot_deg": 90.0,
            },
            "nacelles": [
                {"x_m": geom.fuselage.length_m * 0.4, "y_m": 2.0, "z_m": -0.5, "length_m": 3.0, "diameter_m": 0.8},
                {"x_m": geom.fuselage.length_m * 0.4, "y_m": -2.0, "z_m": -0.5, "length_m": 3.0, "diameter_m": 0.8},
            ],
        }

    elif isinstance(geom, DetailedParametricGeometry):
        if s_ref_m2 is None:
            s_ref_m2 = geom.wing.area

        # Tails
        s_wing = geom.wing.area
        tail_area_total = geom.tail.area_ratio_to_wing * s_wing
        ht_area = tail_area_total * 0.75
        vt_area = tail_area_total * 0.25

        ht_x = geom.fuselage.length * 0.85
        vt_x = geom.fuselage.length * 0.85

        geom_dict = {
            "fuselage": {
                "length_m": geom.fuselage.length,
                "diameter_m": geom.fuselage.diameter,
            },
            "wing": {
                "s_ref_m2": geom.wing.area,
                "aspect_ratio": geom.wing.aspect_ratio,
                "taper_ratio": geom.wing.taper_ratio,
                "sweep_deg": geom.wing.sweep_qc,
                "t_c": geom.wing.thickness_to_chord_root,
                "airfoil_root": geom.wing.airfoil_root,
                "airfoil_tip": geom.wing.airfoil_tip,
                "dihedral": geom.wing.dihedral,
                "twist": geom.wing.twist,
                "x_m": geom.wing.x_le_root if hasattr(geom.wing, "x_le_root") else geom.fuselage.length * 0.4,
                "y_m": geom.wing.y_root if hasattr(geom.wing, "y_root") else 0.0,
                "z_m": geom.wing.z_root if hasattr(geom.wing, "z_root") else 0.0,
            },
            "horizontal_tail": {
                "s_ref_m2": ht_area,
                "aspect_ratio": geom.tail.ht_aspect_ratio,
                "taper_ratio": 0.5,
                "sweep_deg": 10.0,
                "x_m": ht_x,
                "z_m": 0.5,
            },
            "vertical_tail": {
                "s_ref_m2": vt_area,
                "aspect_ratio": geom.tail.vt_aspect_ratio,
                "taper_ratio": 0.6,
                "sweep_deg": 30.0,
                "x_m": vt_x,
                "z_m": 0.5,
                "y_rot_deg": 90.0,
            },
            "nacelles": [],
        }

    return geom_dict


def update_vsp_model(
    geom: dict | ParametricGeometry | DetailedParametricGeometry, s_ref_m2: float | None = None
) -> bool:
    """
    Directly updates the OpenVSP model using the Python API.
    Returns True if successful, False otherwise.
    """
    vsp_interface = OpenVSPInterface()
    if not vsp_interface.is_available():
        return False

    vsp = vsp_interface.vsp
    if vsp is None:
        return False

    geom_dict = _convert_geometry_to_dict(geom, s_ref_m2)

    try:
        vsp.ClearVSPModel()
        vsp.SetDefaultUnits(vsp.VSP_UNITS_SI)

        # Fuselage
        fus = geom_dict.get("fuselage", {})
        if fus:
            fid = vsp.AddGeom("FUSELAGE")
            vsp.SetParmVal(fid, "Length", "Design", fus.get("length_m", 10.0))
            vsp.SetParmVal(fid, "Diameter", "Design", fus.get("diameter_m", 1.0))
            vsp.SetParmVal(fid, "X_Location", "XForm", fus.get("x_m", 0.0))
            vsp.SetParmVal(fid, "Y_Location", "XForm", fus.get("y_m", 0.0))
            vsp.SetParmVal(fid, "Z_Location", "XForm", fus.get("z_m", 0.0))

        # Wing
        wing = geom_dict.get("wing", {})
        if wing:
            wid = vsp.AddGeom("WING")
            s = wing.get("s_ref_m2", 20.0)
            ar = wing.get("aspect_ratio", 5.0)
            tr = wing.get("taper_ratio", 1.0)
            sweep = wing.get("sweep_deg", 0.0)
            tc = wing.get("t_c", 0.12)
            b = math.sqrt(s * ar)
            c_root = 2 * s / (b * (1 + tr))
            c_tip = c_root * tr

            vsp.SetParmVal(wid, "Span", "XSec_1", b)
            vsp.SetParmVal(wid, "Root_Chord", "XSec_1", c_root)
            vsp.SetParmVal(wid, "Tip_Chord", "XSec_1", c_tip)
            vsp.SetParmVal(wid, "Sweep", "XSec_1", sweep)
            vsp.SetParmVal(wid, "ThickChord", "XSec_1", tc)
            vsp.SetParmVal(wid, "X_Location", "XForm", wing.get("x_m", 0.0))
            vsp.SetParmVal(wid, "Y_Location", "XForm", wing.get("y_m", 0.0))
            vsp.SetParmVal(wid, "Z_Location", "XForm", wing.get("z_m", 0.0))

        # Tails
        ht = geom_dict.get("horizontal_tail", {})
        if ht:
            s = ht.get("s_ref_m2", 5.0)
            ar = ht.get("aspect_ratio", 4.0)
            tr = ht.get("taper_ratio", 0.5)
            sweep = ht.get("sweep_deg", 10.0)
            tc = ht.get("t_c", 0.10)
            b = math.sqrt(s * ar)
            c_root = 2 * s / (b * (1 + tr))
            c_tip = c_root * tr

            ht_id = vsp.AddGeom("WING")
            vsp.SetParmVal(ht_id, "Span", "XSec_1", b)
            vsp.SetParmVal(ht_id, "Root_Chord", "XSec_1", c_root)
            vsp.SetParmVal(ht_id, "Tip_Chord", "XSec_1", c_tip)
            vsp.SetParmVal(ht_id, "Sweep", "XSec_1", sweep)
            vsp.SetParmVal(ht_id, "ThickChord", "XSec_1", tc)
            vsp.SetParmVal(ht_id, "X_Location", "XForm", ht.get("x_m", 0.0))
            vsp.SetParmVal(ht_id, "Y_Location", "XForm", ht.get("y_m", 0.0))
            vsp.SetParmVal(ht_id, "Z_Location", "XForm", ht.get("z_m", 0.0))

        vt = geom_dict.get("vertical_tail", {})
        if vt:
            s = vt.get("s_ref_m2", 3.0)
            ar = vt.get("aspect_ratio", 1.5)
            tr = vt.get("taper_ratio", 0.6)
            sweep = vt.get("sweep_deg", 20.0)
            tc = vt.get("t_c", 0.10)
            b = math.sqrt(s * ar)
            c_root = 2 * s / (b * (1 + tr))
            c_tip = c_root * tr

            vt_id = vsp.AddGeom("WING")
            vsp.SetParmVal(vt_id, "Span", "XSec_1", b)
            vsp.SetParmVal(vt_id, "Root_Chord", "XSec_1", c_root)
            vsp.SetParmVal(vt_id, "Tip_Chord", "XSec_1", c_tip)
            vsp.SetParmVal(vt_id, "Sweep", "XSec_1", sweep)
            vsp.SetParmVal(vt_id, "ThickChord", "XSec_1", tc)
            vsp.SetParmVal(vt_id, "X_Location", "XForm", vt.get("x_m", 0.0))
            vsp.SetParmVal(vt_id, "Y_Location", "XForm", vt.get("y_m", 0.0))
            vsp.SetParmVal(vt_id, "Z_Location", "XForm", vt.get("z_m", 0.0))
            vsp.SetParmVal(vt_id, "Y_Rotation", "XForm", vt.get("y_rot_deg", 90.0))

        # Nacelles
        for nac in geom_dict.get("nacelles", []):
            nid = vsp.AddGeom("FUSELAGE")
            vsp.SetParmVal(nid, "Length", "Design", nac.get("length_m", 3.0))
            vsp.SetParmVal(nid, "Diameter", "Design", nac.get("diameter_m", 1.0))
            vsp.SetParmVal(nid, "X_Location", "XForm", nac.get("x_m", 0.0))
            vsp.SetParmVal(nid, "Y_Location", "XForm", nac.get("y_m", 0.0))
            vsp.SetParmVal(nid, "Z_Location", "XForm", nac.get("z_m", 0.0))

        vsp.Update()
        return True
    except Exception as e:
        print(f"Error updating VSP model: {e}")
        return False


def write_openvsp_script(
    *,
    geom: ParametricGeometry | dict,
    s_ref_m2: float | None = None,
    out_path: str | Path | None = None,
    xform: dict | None = None,
    include_visualization: bool = True,
    export_obj_path: str | Path | None = None,
) -> Path | str:
    """
    Write OpenVSP script.
    """
    geom_dict = _convert_geometry_to_dict(geom, s_ref_m2)

    # Merge xform overrides if provided
    if xform:
        # Simple merge logic could be added here
        pass

    script = _geometry_dict_to_vsp_script(geom_dict, include_visualization, export_obj_path)

    if out_path is None:
        return script

    p = Path(out_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(script, encoding="utf-8")
    return p


def _geometry_dict_to_vsp_script(g: dict, include_vis: bool = True, export_obj_path: str | Path | None = None) -> str:
    lines = [
        "import openvsp as vsp",
        "import os",
        "",
        "vsp.ClearVSPModel()",
        "vsp.SetDefaultUnits( vsp.VSP_UNITS_SI )",
        "",
    ]

    # --- Fuselage ---
    fus = g.get("fuselage", {})
    if fus:
        fus_length = fus.get("length_m", 10.0)
        fus_diameter = fus.get("diameter_m", 1.0)
        lines.append("# Fuselage")
        lines.append("fuse_id = vsp.AddGeom('FUSELAGE')")
        lines.append(f"vsp.SetParmVal(fuse_id, 'Length', 'Design', {fus_length})")
        lines.append(f"vsp.SetParmVal(fuse_id, 'Diameter', 'Design', {fus_diameter})")
        lines.append(f"vsp.SetParmVal(fuse_id, 'X_Location', 'XForm', {fus.get('x_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(fuse_id, 'Y_Location', 'XForm', {fus.get('y_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(fuse_id, 'Z_Location', 'XForm', {fus.get('z_m', 0.0)})")
        lines.append("")

    # --- Wing ---
    wing = g.get("wing", {})
    if wing:
        s = wing.get("s_ref_m2", 20.0)
        ar = wing.get("aspect_ratio", 5.0)
        tr = wing.get("taper_ratio", 1.0)
        sweep = wing.get("sweep_deg", 0.0)
        tc = wing.get("t_c", 0.12)
        b = math.sqrt(s * ar)
        c_root = 2 * s / (b * (1 + tr))
        c_tip = c_root * tr

        lines.append("# Wing")
        lines.append("wing_id = vsp.AddGeom('WING')")
        lines.append(f"vsp.SetParmVal(wing_id, 'Span', 'XSec_1', {b})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Root_Chord', 'XSec_1', {c_root})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Tip_Chord', 'XSec_1', {c_tip})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Sweep', 'XSec_1', {sweep})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Dihedral', 'XSec_1', {wing.get('dihedral', 0.0)})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Twist', 'XSec_1', {wing.get('twist', 0.0)})")

        # Airfoil handling (NACA 4-digit)
        # We set parameters on the Cross Section Curves (XSecCurve_0 for root, XSecCurve_1 for tip)
        af_root = wing.get("airfoil_root", "naca2412")
        af_tip = wing.get("airfoil_tip", "naca0012")
        tc_default = wing.get("t_c", 0.12)

        def get_naca_params(code):
            if not code.lower().startswith("naca") or len(code) != 8:
                return None
            try:
                digits = code[4:]
                m = int(digits[0]) / 100.0
                p = int(digits[1]) / 10.0
                t = int(digits[2:]) / 100.0
                return m, p, t
            except Exception:
                return None

        # Root Airfoil (Section 0)
        root_params = get_naca_params(af_root)
        if root_params:
            m, p, t = root_params
            lines.append(f"vsp.SetParmVal(wing_id, 'Camber', 'XSecCurve_0', {m})")
            lines.append(f"vsp.SetParmVal(wing_id, 'CamberLoc', 'XSecCurve_0', {p})")
            lines.append(f"vsp.SetParmVal(wing_id, 'ThickChord', 'XSecCurve_0', {t})")
        else:
            lines.append(f"vsp.SetParmVal(wing_id, 'ThickChord', 'XSecCurve_0', {tc_default})")

        # Tip Airfoil (Section 1)
        tip_params = get_naca_params(af_tip)
        if tip_params:
            m, p, t = tip_params
            lines.append(f"vsp.SetParmVal(wing_id, 'Camber', 'XSecCurve_1', {m})")
            lines.append(f"vsp.SetParmVal(wing_id, 'CamberLoc', 'XSecCurve_1', {p})")
            lines.append(f"vsp.SetParmVal(wing_id, 'ThickChord', 'XSecCurve_1', {t})")
        else:
            lines.append(f"vsp.SetParmVal(wing_id, 'ThickChord', 'XSecCurve_1', {tc_default})")

        lines.append(f"vsp.SetParmVal(wing_id, 'X_Location', 'XForm', {wing.get('x_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Y_Location', 'XForm', {wing.get('y_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(wing_id, 'Z_Location', 'XForm', {wing.get('z_m', 0.0)})")
        lines.append("")

    # --- Horizontal Tail ---
    ht = g.get("horizontal_tail", {})
    if ht:
        s = ht.get("s_ref_m2", 5.0)
        ar = ht.get("aspect_ratio", 4.0)
        tr = ht.get("taper_ratio", 0.5)
        sweep = ht.get("sweep_deg", 10.0)
        tc = ht.get("t_c", 0.10)
        b = math.sqrt(s * ar)
        c_root = 2 * s / (b * (1 + tr))
        c_tip = c_root * tr

        lines.append("# Horizontal Tail")
        lines.append("ht_id = vsp.AddGeom('WING')")
        lines.append(f"vsp.SetParmVal(ht_id, 'Span', 'XSec_1', {b})")
        lines.append(f"vsp.SetParmVal(ht_id, 'Root_Chord', 'XSec_1', {c_root})")
        lines.append(f"vsp.SetParmVal(ht_id, 'Tip_Chord', 'XSec_1', {c_tip})")
        lines.append(f"vsp.SetParmVal(ht_id, 'Sweep', 'XSec_1', {sweep})")
        lines.append(f"vsp.SetParmVal(ht_id, 'ThickChord', 'XSec_1', {tc})")
        lines.append(f"vsp.SetParmVal(ht_id, 'X_Location', 'XForm', {ht.get('x_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(ht_id, 'Y_Location', 'XForm', {ht.get('y_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(ht_id, 'Z_Location', 'XForm', {ht.get('z_m', 0.0)})")
        lines.append("")

    # --- Vertical Tail ---
    vt = g.get("vertical_tail", {})
    if vt:
        s = vt.get("s_ref_m2", 3.0)
        ar = vt.get("aspect_ratio", 1.5)
        tr = vt.get("taper_ratio", 0.6)
        sweep = vt.get("sweep_deg", 20.0)
        tc = vt.get("t_c", 0.10)
        b = math.sqrt(s * ar)
        c_root = 2 * s / (b * (1 + tr))
        c_tip = c_root * tr

        lines.append("# Vertical Tail")
        lines.append("vt_id = vsp.AddGeom('WING')")
        lines.append(f"vsp.SetParmVal(vt_id, 'Span', 'XSec_1', {b})")
        lines.append(f"vsp.SetParmVal(vt_id, 'Root_Chord', 'XSec_1', {c_root})")
        lines.append(f"vsp.SetParmVal(vt_id, 'Tip_Chord', 'XSec_1', {c_tip})")
        lines.append(f"vsp.SetParmVal(vt_id, 'Sweep', 'XSec_1', {sweep})")
        lines.append(f"vsp.SetParmVal(vt_id, 'ThickChord', 'XSec_1', {tc})")
        lines.append(f"vsp.SetParmVal(vt_id, 'X_Location', 'XForm', {vt.get('x_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(vt_id, 'Y_Location', 'XForm', {vt.get('y_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(vt_id, 'Z_Location', 'XForm', {vt.get('z_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(vt_id, 'Y_Rotation', 'XForm', {vt.get('y_rot_deg', 90.0)})")
        lines.append("")

    # --- Nacelles ---
    nacelles = g.get("nacelles", [])
    for i, nac in enumerate(nacelles):
        nac_length = nac.get("length_m", 3.0)
        nac_diameter = nac.get("diameter_m", 1.0)
        lines.append(f"# Nacelle {i}")
        lines.append(f"nac_{i} = vsp.AddGeom('FUSELAGE')")
        lines.append(f"vsp.SetParmVal(nac_{i}, 'Length', 'Design', {nac_length})")
        lines.append(f"vsp.SetParmVal(nac_{i}, 'Diameter', 'Design', {nac_diameter})")
        lines.append(f"vsp.SetParmVal(nac_{i}, 'X_Location', 'XForm', {nac.get('x_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(nac_{i}, 'Y_Location', 'XForm', {nac.get('y_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(nac_{i}, 'Z_Location', 'XForm', {nac.get('z_m', 0.0)})")
        lines.append("")

    lines.append("vsp.Update()")
    lines.append("")
    lines.append("vsp.WriteVSPFile('generated.vsp3')")

    if export_obj_path:
        # Escape backslashes for Windows paths if needed, though forward slashes usually work
        obj_path_str = str(export_obj_path).replace("\\", "/")
        lines.append("")
        lines.append(f"# Export OBJ to {obj_path_str}")
        lines.append("try:")
        # Check if EXPORT_OBJ is available, otherwise try numeric (0 is usually Native, OBJ is often 1 or check docs)
        # Safe bet: use the enum if available
        lines.append(f"    vsp.ExportFile('{obj_path_str}', vsp.SET_ALL, vsp.EXPORT_OBJ)")
        lines.append("except Exception as e:")
        lines.append("    print(f'Error exporting OBJ: {e}')")

    if include_vis:
        # Add screenshot generation logic
        lines.append("")
        lines.append("# Visualization")
        lines.append("try:")
        lines.append("    vsp.SetWindowSize(1920, 1080)")
        lines.append("    # Iso View")
        lines.append("    vsp.SetViewAxis(2, 1, 1)")
        lines.append("    vsp.ViewFit()")
        lines.append("    vsp.WindowSnapshot('vsp_iso_view.png', 2)")
        lines.append("    # Top View")
        lines.append("    vsp.SetViewAxis(0, 0, 1)")
        lines.append("    vsp.ViewFit()")
        lines.append("    vsp.WindowSnapshot('vsp_top_view.png', 2)")
        lines.append("    # Side View")
        lines.append("    vsp.SetViewAxis(0, 1, 0)")
        lines.append("    vsp.ViewFit()")
        lines.append("    vsp.WindowSnapshot('vsp_side_view.png', 2)")
        lines.append("except Exception:")
        lines.append("    print('Warning: Visualization failed (headless?)')")

    return "\n".join(lines)
