from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sqrt

from ..class2_preliminary.aero_drag_buildup import GeometryAssumptions


@dataclass(frozen=True)
class WingPlanform:
    aspect_ratio: float
    taper_ratio: float = 0.45
    sweep_quarter_chord_deg: float = 0.0
    t_c: float = 0.12


@dataclass(frozen=True)
class Fuselage:
    length_m: float = 7.5
    diameter_m: float = 1.2


@dataclass(frozen=True)
class Tail:
    area_ratio_to_wing: float = 0.22


@dataclass(frozen=True)
class GeometryDerived:
    s_ref_m2: float
    b_m: float
    cbar_m: float
    s_wet_fuselage_m2: float
    s_wet_wing_m2: float
    s_wet_tail_m2: float
    wetted_area_factor: float


@dataclass(frozen=True)
class ParametricGeometry:
    wing: WingPlanform
    fuselage: Fuselage = Fuselage()
    tail: Tail = Tail()

    def derived_from_sref(self, *, s_ref_m2: float) -> GeometryDerived:
        if s_ref_m2 <= 0.0:
            raise ValueError("s_ref_m2 must be positive.")
        if self.wing.aspect_ratio <= 0.0:
            raise ValueError("wing.aspect_ratio must be positive.")
        if self.fuselage.length_m <= 0.0 or self.fuselage.diameter_m <= 0.0:
            raise ValueError("Invalid fuselage dimensions.")
        if self.wing.t_c <= 0.0:
            raise ValueError("wing.t_c must be positive.")

        b = sqrt(self.wing.aspect_ratio * s_ref_m2)
        cbar = s_ref_m2 / b

        s_wet_fuse = 3.4 * self.fuselage.length_m * self.fuselage.diameter_m
        s_wet_wing = 2.0 * s_ref_m2 * (1.0 + 0.25 * self.wing.t_c)
        s_tail_ref = max(0.0, self.tail.area_ratio_to_wing) * s_ref_m2
        s_wet_tail = 2.0 * s_tail_ref * (1.0 + 0.25 * self.wing.t_c)
        wetted_factor = s_wet_fuse / max(1e-9, self.fuselage.length_m * self.fuselage.diameter_m)

        return GeometryDerived(
            s_ref_m2=s_ref_m2,
            b_m=b,
            cbar_m=cbar,
            s_wet_fuselage_m2=s_wet_fuse,
            s_wet_wing_m2=s_wet_wing,
            s_wet_tail_m2=s_wet_tail,
            wetted_area_factor=wetted_factor,
        )

    def to_drag_buildup_assumptions(self, *, wetted_area_factor: float | None = None) -> GeometryAssumptions:
        waf = float(wetted_area_factor) if wetted_area_factor is not None else 3.4
        return GeometryAssumptions(
            fuselage_length_m=float(self.fuselage.length_m),
            fuselage_diameter_m=float(self.fuselage.diameter_m),
            wetted_area_factor=float(waf),
            wing_t_c=float(self.wing.t_c),
            tail_area_ratio=float(self.tail.area_ratio_to_wing),
        )

    def to_openvsp_script(self, *, s_ref_m2: float, units: str = "SI", xform: dict | None = None) -> str:
        d = self.derived_from_sref(s_ref_m2=s_ref_m2)
        sweep = float(self.wing.sweep_quarter_chord_deg)
        taper = float(self.wing.taper_ratio)
        ar = float(self.wing.aspect_ratio)
        t_c = float(self.wing.t_c)

        fus_l = float(self.fuselage.length_m)
        fus_d = float(self.fuselage.diameter_m)
        tail_ratio = float(self.tail.area_ratio_to_wing)
        tail_s = tail_ratio * s_ref_m2

        ref_span = d.b_m
        root_chord = 2.0 * s_ref_m2 / (ref_span * (1.0 + taper))
        tip_chord = taper * root_chord
        sweep_rad = radians(sweep)
        half_span = 0.5 * ref_span
        te_sweep_offset = half_span * cos(sweep_rad)
        _ = te_sweep_offset

        xform_wing = xform.get("wing", {}) if isinstance(xform, dict) else {}
        xform_tail = xform.get("tail", {}) if isinstance(xform, dict) else {}
        xform_fuselage = xform.get("fuselage", {}) if isinstance(xform, dict) else {}

        def _xform_val(src: dict, key: str) -> float | None:
            v = src.get(key, None)
            if isinstance(v, (int, float)):
                return float(v)
            return None

        fx = _xform_val(xform_fuselage, "x_m")
        fy = _xform_val(xform_fuselage, "y_m")
        fz = _xform_val(xform_fuselage, "z_m")
        wx = _xform_val(xform_wing, "x_m")
        wy = _xform_val(xform_wing, "y_m")
        wz = _xform_val(xform_wing, "z_m")
        wy_rot = _xform_val(xform_wing, "y_rot_deg")
        tx = _xform_val(xform_tail, "x_m")
        ty = _xform_val(xform_tail, "y_m")
        tz = _xform_val(xform_tail, "z_m")
        ty_rot = _xform_val(xform_tail, "y_rot_deg")

        return "\n".join(
            [
                "import openvsp as vsp",
                "",
                "vsp.ClearVSPModel()",
                "",
                "vsp.SetDefaultUnits( vsp.VSP_UNITS_SI )" if units.upper() == "SI" else "",
                "",
                "fuse_id = vsp.AddGeom('FUSELAGE')",
                f"vsp.SetParmVal(fuse_id, 'Length', 'Design', {fus_l})",
                f"vsp.SetParmVal(fuse_id, 'Diameter', 'Design', {fus_d})",
                f"vsp.SetParmVal(fuse_id, 'X_Location', 'XForm', {fx})" if fx is not None else "",
                f"vsp.SetParmVal(fuse_id, 'Y_Location', 'XForm', {fy})" if fy is not None else "",
                f"vsp.SetParmVal(fuse_id, 'Z_Location', 'XForm', {fz})" if fz is not None else "",
                "",
                "wing_id = vsp.AddGeom('WING')",
                f"vsp.SetParmVal(wing_id, 'Span', 'XSec_1', {ref_span})",
                f"vsp.SetParmVal(wing_id, 'Root_Chord', 'XSec_1', {root_chord})",
                f"vsp.SetParmVal(wing_id, 'Tip_Chord', 'XSec_1', {tip_chord})",
                f"vsp.SetParmVal(wing_id, 'Sweep', 'XSec_1', {sweep})",
                f"vsp.SetParmVal(wing_id, 'ThickChord', 'XSec_1', {t_c})",
                f"vsp.SetParmVal(wing_id, 'X_Location', 'XForm', {wx})" if wx is not None else "",
                f"vsp.SetParmVal(wing_id, 'Y_Location', 'XForm', {wy})" if wy is not None else "",
                f"vsp.SetParmVal(wing_id, 'Z_Location', 'XForm', {wz})" if wz is not None else "",
                f"vsp.SetParmVal(wing_id, 'Y_Rotation', 'XForm', {wy_rot})" if wy_rot is not None else "",
                "",
                "tail_id = vsp.AddGeom('WING')",
                f"vsp.SetParmVal(tail_id, 'Span', 'XSec_1', {sqrt(max(1e-9, ar * tail_s))})",
                f"vsp.SetParmVal(tail_id, 'Root_Chord', 'XSec_1', {2.0 * tail_s / (sqrt(max(1e-9, ar * tail_s)) * (1.0 + taper))})",
                f"vsp.SetParmVal(tail_id, 'Tip_Chord', 'XSec_1', {taper * (2.0 * tail_s / (sqrt(max(1e-9, ar * tail_s)) * (1.0 + taper)))})",
                f"vsp.SetParmVal(tail_id, 'Sweep', 'XSec_1', {sweep})",
                f"vsp.SetParmVal(tail_id, 'ThickChord', 'XSec_1', {t_c})",
                f"vsp.SetParmVal(tail_id, 'X_Location', 'XForm', {tx})" if tx is not None else "",
                f"vsp.SetParmVal(tail_id, 'Y_Location', 'XForm', {ty})" if ty is not None else "",
                f"vsp.SetParmVal(tail_id, 'Z_Location', 'XForm', {tz})" if tz is not None else "",
                f"vsp.SetParmVal(tail_id, 'Y_Rotation', 'XForm', {ty_rot})" if ty_rot is not None else "",
                "",
                "vsp.Update()",
                "",
                "vsp.WriteVSPFile('generated.vsp3')",
                "",
            ]
        )


def geometry_from_inputs(inputs: dict) -> ParametricGeometry | None:
    g = inputs.get("geometry_parametric", None)
    if g is None:
        return None
    if not isinstance(g, dict):
        raise ValueError("geometry_parametric must be an object.")
    wing_in = g.get("wing", {})
    if not isinstance(wing_in, dict):
        raise ValueError("geometry_parametric.wing must be an object.")
    ar = wing_in.get("aspect_ratio", None)
    if not isinstance(ar, (int, float)):
        raise ValueError("geometry_parametric.wing.aspect_ratio must be a number.")
    wing = WingPlanform(
        aspect_ratio=float(ar),
        taper_ratio=float(wing_in.get("taper_ratio", 0.45)),
        sweep_quarter_chord_deg=float(wing_in.get("sweep_quarter_chord_deg", 0.0)),
        t_c=float(wing_in.get("t_c", 0.12)),
    )

    fus_in = g.get("fuselage", {})
    if fus_in is None:
        fus_in = {}
    if not isinstance(fus_in, dict):
        raise ValueError("geometry_parametric.fuselage must be an object.")
    fus = Fuselage(length_m=float(fus_in.get("length_m", 7.5)), diameter_m=float(fus_in.get("diameter_m", 1.2)))

    tail_in = g.get("tail", {})
    if tail_in is None:
        tail_in = {}
    if not isinstance(tail_in, dict):
        raise ValueError("geometry_parametric.tail must be an object.")
    tail = Tail(area_ratio_to_wing=float(tail_in.get("area_ratio_to_wing", 0.22)))

    return ParametricGeometry(wing=wing, fuselage=fus, tail=tail)
