
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .geometry_parametric import ParametricGeometry
from .geometry_detailed import ParametricGeometry as DetailedParametricGeometry
from .openvsp_interface import OpenVSPInterface


def can_import_openvsp() -> bool:
    return OpenVSPInterface().is_available()


def update_vsp_model(geom: dict | ParametricGeometry | DetailedParametricGeometry, s_ref_m2: float | None = None) -> bool:
    """
    Directly updates the OpenVSP model using the Python API.
    Returns True if successful, False otherwise.
    """
    vsp_interface = OpenVSPInterface()
    if not vsp_interface.is_available():
        return False
        
    vsp = vsp_interface.vsp
    
    # Convert to dict if necessary (reuse logic from write_openvsp_script)
    # Ideally we should refactor the dict conversion logic into a separate helper
    # For now, let's assume we pass a dict or handle it simply
    
    geom_dict = {}
    if isinstance(geom, dict):
        geom_dict = geom
    # TODO: Refactor the conversion logic from write_openvsp_script to be reusable
    
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
            b = math.sqrt(s * ar)
            vsp.SetParmVal(wid, "TotalArea", "WingGeom", s)
            vsp.SetParmVal(wid, "TotalSpan", "WingGeom", b)
            vsp.SetParmVal(wid, "X_Location", "XForm", wing.get("x_m", 0.0))
            
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
) -> Path | str:
    """
    Write OpenVSP script.
    """
    script = ""
    if isinstance(geom, ParametricGeometry):
        # Convert ParametricGeometry to a rich dict for the unified generator
        if s_ref_m2 is None:
            raise ValueError("s_ref_m2 required for ParametricGeometry")
        
        # Derive dimensions
        b = math.sqrt(geom.wing.aspect_ratio * s_ref_m2)
        c_root = 2 * s_ref_m2 / (b * (1 + geom.wing.taper_ratio))
        c_tip = c_root * geom.wing.taper_ratio
        
        # Estimate tail sizes
        # Assume 20% area for tail total, split 75% HT, 25% VT
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
                "x_m": geom.fuselage.length_m * 0.4, # Approx wing location
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
                "y_rot_deg": 90.0
            },
            # Add default nacelle if not specified? 
            # We'll assume integrated nacelles are part of detailed design
            # but for visualization, we add simple pods
            "nacelles": [
                {"x_m": geom.fuselage.length_m * 0.4, "y_m": 2.0, "z_m": -0.5, "length_m": 3.0, "diameter_m": 0.8},
                {"x_m": geom.fuselage.length_m * 0.4, "y_m": -2.0, "z_m": -0.5, "length_m": 3.0, "diameter_m": 0.8}
            ]
        }
        
        # Merge xform overrides if provided
        if xform:
            # Simple merge logic could be added here
            pass
            
        script = _geometry_dict_to_vsp_script(geom_dict, include_visualization)

    elif isinstance(geom, DetailedParametricGeometry):
        # Convert DetailedParametricGeometry to dict
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
                "x_m": geom.wing.x_le_root if hasattr(geom.wing, 'x_le_root') else geom.fuselage.length * 0.4,
                "y_m": geom.wing.y_root if hasattr(geom.wing, 'y_root') else 0.0,
                "z_m": geom.wing.z_root if hasattr(geom.wing, 'z_root') else 0.0,
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
                "y_rot_deg": 90.0
            }
        }
        
        # Add nacelles if available (placeholder)
        geom_dict["nacelles"] = []
        
        script = _geometry_dict_to_vsp_script(geom_dict, include_visualization)

    else:
        script = _geometry_dict_to_vsp_script(geom, include_visualization)

    if out_path is None:
        return script

    p = Path(out_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(script, encoding="utf-8")
    return p


def _geometry_dict_to_vsp_script(g: dict, include_vis: bool = True) -> str:
    lines = [
        "import openvsp as vsp",
        "import os",
        "",
        "vsp.ClearVSPModel()",
        "vsp.SetDefaultUnits( vsp.VSP_UNITS_SI )",
        ""
    ]

    # --- Fuselage ---
    fus = g.get("fuselage", {})
    if fus:
        l = fus.get("length_m", 10.0)
        d = fus.get("diameter_m", 1.0)
        lines.append("# Fuselage")
        lines.append("fuse_id = vsp.AddGeom('FUSELAGE')")
        lines.append(f"vsp.SetParmVal(fuse_id, 'Length', 'Design', {l})")
        lines.append(f"vsp.SetParmVal(fuse_id, 'Diameter', 'Design', {d})")
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
        lines.append(f"vsp.SetParmVal(wing_id, 'ThickChord', 'XSec_1', {tc})")
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
        l = nac.get("length_m", 3.0)
        d = nac.get("diameter_m", 1.0)
        lines.append(f"# Nacelle {i}")
        lines.append(f"nac_{i} = vsp.AddGeom('FUSELAGE')")
        lines.append(f"vsp.SetParmVal(nac_{i}, 'Length', 'Design', {l})")
        lines.append(f"vsp.SetParmVal(nac_{i}, 'Diameter', 'Design', {d})")
        lines.append(f"vsp.SetParmVal(nac_{i}, 'X_Location', 'XForm', {nac.get('x_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(nac_{i}, 'Y_Location', 'XForm', {nac.get('y_m', 0.0)})")
        lines.append(f"vsp.SetParmVal(nac_{i}, 'Z_Location', 'XForm', {nac.get('z_m', 0.0)})")
        lines.append("")

    lines.append("vsp.Update()")
    lines.append("")
    lines.append("vsp.WriteVSPFile('generated.vsp3')")
    
    if include_vis:
        # Add screenshot generation logic
        lines.append("")
        lines.append("# Visualization")
        lines.append("try:")
        lines.append("    vsp.SetWindowSize(1920, 1080)")
        lines.append("    # Iso View")
        lines.append("    vsp.SetViewAxis(2, 1, 1)")
        lines.append("    vsp.ViewFit()")
        lines.append("    vsp.WindowSnapshot('view_iso.png', 2)")
        lines.append("    # Top View")
        lines.append("    vsp.SetViewAxis(0, 0, 1)")
        lines.append("    vsp.ViewFit()")
        lines.append("    vsp.WindowSnapshot('view_top.png', 2)")
        lines.append("    # Side View")
        lines.append("    vsp.SetViewAxis(0, 1, 0)")
        lines.append("    vsp.ViewFit()")
        lines.append("    vsp.WindowSnapshot('view_side.png', 2)")
        lines.append("except:")
        lines.append("    print('Warning: Visualization failed (headless?)')")

    return "\n".join(lines)
