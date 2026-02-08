from __future__ import annotations

from dataclasses import dataclass
from math import log10, pi, cos

from .atmosphere import isa_tropopause
from .aero_lift_slope import (
    calculate_lift_induced_drag_factor,
    calculate_lift_slope_subsonic,
    calculate_lift_slope_supersonic,
)


def calculate_lift_slope(
    *,
    mach: float,
    aspect_ratio: float,
    sweep_max_thickness_deg: float,
    s_ref_m2: float,
    s_exposed_m2: float,
    fuselage_diameter_m: float,
    span_m: float,
) -> float:
    """
    Calculates the Lift Slope (CLa) for the wing using aero_lift_slope module.
    """

    if mach < 1.0:
        res = calculate_lift_slope_subsonic(
            aspect_ratio=aspect_ratio,
            sweep_quarter_chord_deg=sweep_max_thickness_deg,  # Approx
            sweep_max_thickness_deg=sweep_max_thickness_deg,
            mach=mach,
            fuselage_diameter_m=fuselage_diameter_m,
            wing_span_m=span_m,
        )
        cla = res.cl_alpha
    else:
        # For supersonic, we use the simple approximation from aero_lift_slope
        # But wait, aero_lift_slope_supersonic signature is different.
        # calculate_lift_slope_supersonic(aspect_ratio, sweep_leading_edge_deg, taper_ratio, mach, exposed_area_ratio)

        # We don't have taper_ratio or sweep_LE passed in easily here?
        # Let's approximate sweep_LE from sweep_max_t.
        # tan(L_le) = tan(L_max_t) + ...
        # For now, pass sweep_max_thickness_deg as sweep_leading_edge_deg approximation or 0.0

        # Actually, let's keep the simple logic for supersonic here if the other module is too complex or different.
        # But better to use the module.

        # Let's assume taper=1.0 for approximation if unknown.
        res = calculate_lift_slope_supersonic(
            aspect_ratio=aspect_ratio,
            sweep_leading_edge_deg=sweep_max_thickness_deg,  # Approx
            taper_ratio=1.0,  # Default
            mach=mach,
            exposed_area_ratio=s_exposed_m2 / s_ref_m2,
        )
        cla = res.cl_alpha

    # Area correction (Se/Sref) is usually handled inside the specialized functions or here.
    # calculate_lift_slope_subsonic returns 3D lift slope * fuselage factor.
    # It doesn't explicitly multiply by Se/Sref.
    # So we apply it here.
    cla = cla * (s_exposed_m2 / s_ref_m2)

    return cla


@dataclass(frozen=True)
class GeometryAssumptions:
    fuselage_length_m: float
    fuselage_diameter_m: float
    wetted_area_factor: float
    wing_t_c: float
    tail_area_ratio: float

    # Advanced / Detailed overrides
    fuselage_wetted_area_m2: float | None = None
    wing_wetted_area_m2: float | None = None
    tail_wetted_area_m2: float | None = None

    fuselage_form_factor: float | None = None
    wing_form_factor: float | None = None
    tail_form_factor: float | None = None

    interference_factor_fuselage: float = 1.0
    interference_factor_wing: float = 1.0
    interference_factor_tail: float = 1.0

    # Detailed tail breakdown
    htail_area_ratio: float | None = None
    vtail_area_ratio: float | None = None
    htail_t_c: float | None = None
    vtail_t_c: float | None = None


@dataclass(frozen=True)
class DragBuildUpResult:
    cd0: float
    breakdown: dict


def _mu_sutherland_pa_s(t_k: float) -> float:
    mu0 = 1.716e-5
    t0 = 273.15
    s = 110.4
    return mu0 * (t_k / t0) ** 1.5 * (t0 + s) / (t_k + s)


def _cf_turbulent(re: float, mach: float) -> float:
    if re <= 1e3:
        return 0.0
    cf = 0.455 / ((log10(re) ** 2.58) * ((1.0 + 0.144 * mach * mach) ** 0.65))
    return cf


def estimate_cd0_drag_buildup(
    *,
    cruise_altitude_m: float,
    cruise_speed_m_s: float,
    s_ref_m2: float,
    b_m: float,
    cbar_m: float,
    assumptions: GeometryAssumptions,
    isa_delta_c: float = 0.0,
) -> DragBuildUpResult:
    if s_ref_m2 <= 0.0 or cruise_speed_m_s <= 0.0:
        raise ValueError("Invalid reference area or speed.")
    if assumptions.fuselage_length_m <= 0.0 or assumptions.fuselage_diameter_m <= 0.0:
        raise ValueError("Invalid fuselage geometry.")

    atm = isa_tropopause(cruise_altitude_m, delta_t_k=float(isa_delta_c))
    mu = _mu_sutherland_pa_s(atm.t_k)
    mach = cruise_speed_m_s / atm.a_m_s

    s_wet_fuse = (
        float(assumptions.fuselage_wetted_area_m2)
        if assumptions.fuselage_wetted_area_m2 is not None
        else (assumptions.wetted_area_factor * assumptions.fuselage_length_m * assumptions.fuselage_diameter_m)
    )
    re_fuse = atm.rho_kg_m3 * cruise_speed_m_s * assumptions.fuselage_length_m / mu
    cf_fuse = _cf_turbulent(re_fuse, mach)

    ff_fuse = (
        float(assumptions.fuselage_form_factor)
        if assumptions.fuselage_form_factor is not None
        else (
            1.0
            + 60.0 / (assumptions.fuselage_length_m / assumptions.fuselage_diameter_m) ** 3
            + (assumptions.fuselage_length_m / assumptions.fuselage_diameter_m) / 400.0
        )
    )
    cd0_fuse = cf_fuse * ff_fuse * float(assumptions.interference_factor_fuselage) * (s_wet_fuse / s_ref_m2)

    s_wet_wing = (
        float(assumptions.wing_wetted_area_m2)
        if assumptions.wing_wetted_area_m2 is not None
        else (2.0 * s_ref_m2 * (1.0 + 0.25 * assumptions.wing_t_c))
    )
    re_wing = atm.rho_kg_m3 * cruise_speed_m_s * cbar_m / mu
    cf_wing = _cf_turbulent(re_wing, mach)

    ff_wing = (
        float(assumptions.wing_form_factor)
        if assumptions.wing_form_factor is not None
        else (
            (1.0 + 0.6 / cbar_m * assumptions.wing_t_c + 100.0 * (assumptions.wing_t_c**4))
            * (1.34 * (mach**0.18) if mach > 0.0 else 1.0)
        )
    )
    cd0_wing = cf_wing * ff_wing * float(assumptions.interference_factor_wing) * (s_wet_wing / s_ref_m2)

    cd0_tail = 0.0
    s_wet_tail_total = 0.0

    if assumptions.htail_area_ratio is not None or assumptions.vtail_area_ratio is not None:
        # Detailed tail calculation
        # HT
        if assumptions.htail_area_ratio:
            s_ht = float(assumptions.htail_area_ratio) * s_ref_m2
            tc_ht = float(assumptions.htail_t_c) if assumptions.htail_t_c is not None else assumptions.wing_t_c
            sw_ht = 2.0 * s_ht * (1.0 + 0.25 * tc_ht)
            s_wet_tail_total += sw_ht
            re_ht = atm.rho_kg_m3 * cruise_speed_m_s * (cbar_m * 0.6) / mu  # approx chord
            cf_ht = _cf_turbulent(re_ht, mach)
            ff_ht = (
                float(assumptions.tail_form_factor)
                if assumptions.tail_form_factor is not None
                else (
                    (1.0 + 0.6 / (cbar_m * 0.6) * tc_ht + 100.0 * (tc_ht**4))
                    * (1.34 * (mach**0.18) if mach > 0.0 else 1.0)
                )
            )
            cd0_tail += cf_ht * ff_ht * float(assumptions.interference_factor_tail) * (sw_ht / s_ref_m2)

        # VT
        if assumptions.vtail_area_ratio:
            s_vt = float(assumptions.vtail_area_ratio) * s_ref_m2
            tc_vt = float(assumptions.vtail_t_c) if assumptions.vtail_t_c is not None else assumptions.wing_t_c
            sw_vt = 2.0 * s_vt * (1.0 + 0.25 * tc_vt)
            s_wet_tail_total += sw_vt
            re_vt = atm.rho_kg_m3 * cruise_speed_m_s * (cbar_m * 0.6) / mu
            cf_vt = _cf_turbulent(re_vt, mach)
            ff_vt = (
                float(assumptions.tail_form_factor)
                if assumptions.tail_form_factor is not None
                else (
                    (1.0 + 0.6 / (cbar_m * 0.6) * tc_vt + 100.0 * (tc_vt**4))
                    * (1.34 * (mach**0.18) if mach > 0.0 else 1.0)
                )
            )
            cd0_tail += cf_vt * ff_vt * float(assumptions.interference_factor_tail) * (sw_vt / s_ref_m2)
    else:
        # Fallback to generic tail ratio
        s_tail_ref = float(assumptions.tail_area_ratio) * s_ref_m2
        s_wet_tail = (
            float(assumptions.tail_wetted_area_m2)
            if assumptions.tail_wetted_area_m2 is not None
            else (2.0 * s_tail_ref * (1.0 + 0.25 * assumptions.wing_t_c))
        )
        s_wet_tail_total = s_wet_tail
        re_tail = atm.rho_kg_m3 * cruise_speed_m_s * max(0.5, 0.5 * cbar_m) / mu
        cf_tail = _cf_turbulent(re_tail, mach)
        ff_tail = float(assumptions.tail_form_factor) if assumptions.tail_form_factor is not None else ff_wing
        cd0_tail = cf_tail * ff_tail * float(assumptions.interference_factor_tail) * (s_wet_tail / s_ref_m2)

    cd0_misc = 0.002
    cd0 = cd0_fuse + cd0_wing + cd0_tail + cd0_misc

    breakdown = {
        "cd0_fuselage": cd0_fuse,
        "cd0_wing": cd0_wing,
        "cd0_tail": cd0_tail,
        "cd0_misc": cd0_misc,
        "mach": mach,
        "re_fuselage": re_fuse,
        "re_wing": re_wing,
    }

    return DragBuildUpResult(cd0=cd0, breakdown=breakdown)


def calculate_wave_drag(
    *,
    mach: float,
    sweep_quarter_chord_deg: float,
    thickness_ratio: float,
    aspect_ratio: float,
) -> float:
    if mach <= 1.0:
        return 0.0

    sweep_rad = sweep_quarter_chord_deg * pi / 180.0

    mach_normal = mach * cos(sweep_rad)

    if mach_normal <= 1.0:
        return 0.0

    cd_wave = 0.002 * (thickness_ratio**2) * (aspect_ratio / 10.0) * ((mach_normal - 1.0) / (mach_normal)) ** 3

    return cd_wave


def calculate_compressibility_drag(
    *,
    mach: float,
    mach_crit: float = 0.8,
    mach_dd: float = 1.2,
    cd0_subsonic: float = 0.02,
    cd0_supersonic: float = 0.04,
) -> float:
    if mach <= mach_crit:
        return 0.0
    elif mach >= mach_dd:
        return cd0_supersonic - cd0_subsonic
    else:
        t = (mach - mach_crit) / (mach_dd - mach_crit)
        cd_comp = (cd0_supersonic - cd0_subsonic) * t
        return cd_comp


def calculate_induced_drag(
    *,
    cl: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
) -> float:
    k = calculate_lift_induced_drag_factor(
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
    )

    cd_i = k * cl**2

    return cd_i


def calculate_total_drag(
    *,
    cl: float,
    cd0: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
    mach: float,
    mach_crit: float = 0.8,
    mach_dd: float = 1.2,
    thickness_ratio: float = 0.12,
) -> dict:
    cd_i = calculate_induced_drag(
        cl=cl,
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
    )

    cd_wave = calculate_wave_drag(
        mach=mach,
        sweep_quarter_chord_deg=sweep_quarter_chord_deg,
        thickness_ratio=thickness_ratio,
        aspect_ratio=aspect_ratio,
    )

    cd_comp = calculate_compressibility_drag(
        mach=mach,
        mach_crit=mach_crit,
        mach_dd=mach_dd,
        cd0_subsonic=cd0,
        cd0_supersonic=cd0 + cd_wave,
    )

    cd_total = cd0 + cd_i + cd_wave + cd_comp

    return {
        "cd0": cd0,
        "cd_i": cd_i,
        "cd_wave": cd_wave,
        "cd_comp": cd_comp,
        "cd_total": cd_total,
        "cl": cl,
        "mach": mach,
    }


def generate_drag_mach_curve(
    *,
    cl: float,
    cd0_subsonic: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
    mach_range: list[float],
    mach_crit: float = 0.8,
    mach_dd: float = 1.2,
    thickness_ratio: float = 0.12,
) -> dict:
    cd0: list[float] = []
    cd_i: list[float] = []
    cd_wave: list[float] = []
    cd_comp: list[float] = []
    cd_total: list[float] = []
    regimes: list[str] = []

    for mach in mach_range:
        drag_result = calculate_total_drag(
            cl=cl,
            cd0=cd0_subsonic,
            aspect_ratio=aspect_ratio,
            taper_ratio=taper_ratio,
            sweep_quarter_chord_deg=sweep_quarter_chord_deg,
            mach=mach,
            mach_crit=mach_crit,
            mach_dd=mach_dd,
            thickness_ratio=thickness_ratio,
        )

        cd0.append(drag_result["cd0"])
        cd_i.append(drag_result["cd_i"])
        cd_wave.append(drag_result["cd_wave"])
        cd_comp.append(drag_result["cd_comp"])
        cd_total.append(drag_result["cd_total"])

        if mach < mach_crit:
            regime = "subsonic"
        elif mach < mach_dd:
            regime = "transonic"
        else:
            regime = "supersonic"
        regimes.append(regime)

    return {
        "mach": mach_range,
        "cd0": cd0,
        "cd_i": cd_i,
        "cd_wave": cd_wave,
        "cd_comp": cd_comp,
        "cd_total": cd_total,
        "regime": regimes,
    }
