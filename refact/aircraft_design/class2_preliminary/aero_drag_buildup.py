from __future__ import annotations

from dataclasses import dataclass, field
from math import log10, pi, sqrt, pow

from ..common.atmosphere import isa_tropopause
from .aero_lift_slope import (
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
        res = calculate_lift_slope_supersonic(
            aspect_ratio=aspect_ratio,
            sweep_leading_edge_deg=sweep_max_thickness_deg,  # Approx
            taper_ratio=1.0,  # Default
            mach=mach,
            exposed_area_ratio=s_exposed_m2 / s_ref_m2,
        )
        cla = res.cl_alpha

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
    htail_wetted_area_m2: float | None = None
    vtail_wetted_area_m2: float | None = None

    fuselage_form_factor: float | None = None
    wing_form_factor: float | None = None
    tail_form_factor: float | None = None

    interference_factor_fuselage: float = 1.0
    interference_factor_wing: float = 1.0
    interference_factor_tail: float = 1.05

    # Detailed tail breakdown
    htail_area_ratio: float | None = None
    vtail_area_ratio: float | None = None
    htail_t_c: float | None = None
    vtail_t_c: float | None = None

    # Detailed MAC/Sweep for buildup
    htail_mac_m: float | None = None
    vtail_mac_m: float | None = None
    htail_sweep_rad: float | None = None
    vtail_sweep_rad: float | None = None


@dataclass(frozen=True)
class DragComponent:
    name: str
    swet_m2: float
    cf: float
    form_factor: float
    interference_factor: float
    f_area_m2: float  # Equivalent parasite area f = Cf * FF * Q * Swet
    cd0_component: float  # f / Sref


@dataclass(frozen=True)
class DragBuildUpResult:
    cd0: float
    breakdown: list[DragComponent] = field(default_factory=list)
    reynolds_number_fuselage: float = 0.0
    reynolds_number_wing: float = 0.0
    skin_friction_wing: float = 0.0
    wave_drag_cd: float = 0.0


def calculate_cf_turbulent(re: float, mach: float) -> float:
    """
    Turbulent flat plate skin friction coefficient (Prandtl-Schlichting).
    Adjusted for compressibility (Raymer Eq 12.27).
    """
    if re <= 100.0:  # Avoid log(0) or negative
        return 0.0

    # Incompressible Cf
    cf_inc = 0.455 / (log10(re) ** 2.58)

    # Compressibility Correction
    if mach < 0.1:
        return cf_inc
    else:
        # General approx for subsonic/supersonic
        # Raymer Eq 12.27 for turbulent
        return cf_inc / ((1.0 + 0.144 * mach * mach) ** 0.65)


def calculate_form_factor_fuselage(f_ratio: float) -> float:
    """
    Fuselage Form Factor (Raymer Eq 12.31)
    f = L/D
    FF = 1 + 60/f^3 + f/400
    """
    if f_ratio <= 0:
        return 1.0
    return 1.0 + 60.0 / (f_ratio**3) + f_ratio / 400.0


def calculate_form_factor_wing(t_c: float, sweep_rad: float) -> float:
    """
    Wing/Tail Form Factor (Raymer Eq 12.30 simplified)
    FF = 1 + 1.2(t/c) + 100(t/c)^4
    Assuming sweep is accounted for in t/c or negligible for FF base.
    """
    return 1.0 + 1.2 * t_c + 100.0 * (t_c**4)


def calculate_wave_drag(
    mach: float,
    fuselage_length_m: float,
    fuselage_diameter_m: float,
    s_ref_m2: float,
    wing_volume_m3: float = 0.0,
    efficiency_factor: float = 1.4,
) -> float:
    """
    Estimates Supersonic Wave Drag using Sears-Haack approximation.
    (D/q)_wave = Ew * [128 * V_tot^2 / (pi * L^4)]

    Args:
        mach: Mach number
        fuselage_length_m: Effective length of the body
        fuselage_diameter_m: Max diameter (for volume est)
        s_ref_m2: Reference area to normalize CD
        wing_volume_m3: Additional volume from wing
        efficiency_factor: Ew (1.0 = perfect Sears-Haack, 1.4 = typical clean supersonic)

    Returns:
        CD_wave
    """
    if mach < 1.0:
        return 0.0

    # Estimate Fuselage Volume (assume approximation of a sears-haack or cylinder with taper)
    # V_fus = integral(A(x)dx). For a 3/4 power body or similar:
    # Approx as 0.7 * Cylinder
    vol_fus = 0.7 * pi * pow(fuselage_diameter_m / 2.0, 2) * fuselage_length_m

    vol_tot = vol_fus + wing_volume_m3

    # Sears-Haack D/q
    # D/q = 128 * V^2 / (pi * L^4)
    if fuselage_length_m <= 0:
        return 0.0

    d_q_wave_ideal = 128.0 * pow(vol_tot, 2) / (pi * pow(fuselage_length_m, 4))

    d_q_wave = d_q_wave_ideal * efficiency_factor

    cd_wave = d_q_wave / s_ref_m2

    # Mach Correction
    # Sears-Haack formula gives the wave drag at M=1 (sonic) or close to it,
    # but linear theory suggests CD_wave scales with 1/beta for M > 1.
    # We assume the calculated cd_wave is the peak value around M=1.2

    if mach < 1.0:
        return 0.0
    elif mach < 1.2:
        # Ramp up from M=1.0 to M=1.2
        factor = (mach - 1.0) / 0.2
        return cd_wave * factor
    else:
        # For higher Mach, CD_wave decays with 1/sqrt(M^2 - 1)
        # We normalize to M=1.2
        beta_ref = sqrt(1.2 * 1.2 - 1.0)
        beta_curr = sqrt(mach * mach - 1.0)
        factor = beta_ref / beta_curr
        return cd_wave * factor


def calculate_parasite_drag_buildup(
    *,
    geometry: GeometryAssumptions,
    s_ref_m2: float,
    mach: float,
    altitude_m: float,
    l_char_fuselage_m: float,
    l_char_wing_m: float,
    l_char_tail_m: float,
) -> DragBuildUpResult:
    """
    Calculates CD0 using component buildup method (Raymer) + Wave Drag.
    """

    atm = isa_tropopause(altitude_m)
    rho = atm.rho_kg_m3
    mu = atm.mu_kg_ms
    v = mach * atm.a_m_s

    if v <= 0:
        return DragBuildUpResult(cd0=0.0)

    breakdown = []

    # 1. Fuselage
    re_fus = (rho * v * l_char_fuselage_m) / mu
    cf_fus = calculate_cf_turbulent(re_fus, mach)

    ff_fus = geometry.fuselage_form_factor
    if ff_fus is None:
        f_ratio = (
            geometry.fuselage_length_m / geometry.fuselage_diameter_m if geometry.fuselage_diameter_m > 0 else 10.0
        )
        ff_fus = calculate_form_factor_fuselage(f_ratio)

    swet_fus = geometry.fuselage_wetted_area_m2
    if swet_fus is None:
        # Simple approximation
        swet_fus = pi * geometry.fuselage_diameter_m * geometry.fuselage_length_m * 0.8  # approx

    q_fus = geometry.interference_factor_fuselage

    f_fus = cf_fus * ff_fus * q_fus * swet_fus
    cd0_fus = f_fus / s_ref_m2
    breakdown.append(DragComponent("Fuselage", swet_fus, cf_fus, ff_fus, q_fus, f_fus, cd0_fus))

    # 2. Wing
    re_wing = (rho * v * l_char_wing_m) / mu
    cf_wing = calculate_cf_turbulent(re_wing, mach)

    ff_wing = geometry.wing_form_factor
    if ff_wing is None:
        ff_wing = calculate_form_factor_wing(geometry.wing_t_c, 0.0)  # Assume 0 sweep for form factor if unknown

    swet_wing = geometry.wing_wetted_area_m2
    if swet_wing is None:
        swet_wing = s_ref_m2 * 2.0 * 1.02  # Exposed * 2 * curvature

    q_wing = geometry.interference_factor_wing

    f_wing = cf_wing * ff_wing * q_wing * swet_wing
    cd0_wing = f_wing / s_ref_m2
    breakdown.append(DragComponent("Wing", swet_wing, cf_wing, ff_wing, q_wing, f_wing, cd0_wing))

    # 3. Tails
    # Horizontal
    # Use htail_area_ratio if wetted area not provided
    swet_ht = geometry.htail_wetted_area_m2
    if swet_ht is None and geometry.htail_area_ratio:
        swet_ht = s_ref_m2 * geometry.htail_area_ratio * 2.0 * 1.02
    elif swet_ht is None:
        swet_ht = 0.0

    if swet_ht > 0:
        re_ht = re_wing  # Approximation if mac not given
        if geometry.htail_mac_m:
            re_ht = (rho * v * geometry.htail_mac_m) / mu

        cf_ht = calculate_cf_turbulent(re_ht, mach)

        ff_ht = geometry.tail_form_factor
        if ff_ht is None:
            # Use specific t/c if available, else wing t/c or default 0.12
            tc = geometry.htail_t_c if geometry.htail_t_c else 0.12
            swp = geometry.htail_sweep_rad if geometry.htail_sweep_rad else 0.0
            ff_ht = calculate_form_factor_wing(tc, swp)

        q_ht = geometry.interference_factor_tail
        f_ht = cf_ht * ff_ht * q_ht * swet_ht
        cd0_ht = f_ht / s_ref_m2
        breakdown.append(DragComponent("Horizontal Tail", swet_ht, cf_ht, ff_ht, q_ht, f_ht, cd0_ht))

    # Vertical
    swet_vt = geometry.vtail_wetted_area_m2
    if swet_vt is None and geometry.vtail_area_ratio:
        swet_vt = s_ref_m2 * geometry.vtail_area_ratio * 2.0 * 1.02
    elif swet_vt is None:
        swet_vt = 0.0

    if swet_vt > 0:
        re_vt = re_wing
        if geometry.vtail_mac_m:
            re_vt = (rho * v * geometry.vtail_mac_m) / mu

        cf_vt = calculate_cf_turbulent(re_vt, mach)

        ff_vt = geometry.tail_form_factor
        if ff_vt is None:
            tc = geometry.vtail_t_c if geometry.vtail_t_c else 0.12
            swp = geometry.vtail_sweep_rad if geometry.vtail_sweep_rad else 0.0
            ff_vt = calculate_form_factor_wing(tc, swp)

        q_vt = geometry.interference_factor_tail
        f_vt = cf_vt * ff_vt * q_vt * swet_vt
        cd0_vt = f_vt / s_ref_m2
        breakdown.append(DragComponent("Vertical Tail", swet_vt, cf_vt, ff_vt, q_vt, f_vt, cd0_vt))

    # Sum
    cd0_total = sum(c.cd0_component for c in breakdown)

    # Leakage and Protuberance (Raymer suggest 5-10%)
    cd0_misc = cd0_total * 0.10
    breakdown.append(DragComponent("Misc/Leakage", 0.0, 0.0, 0.0, 0.0, 0.0, cd0_misc))

    # Wave Drag
    wing_vol = s_ref_m2 * geometry.wing_t_c * 0.7
    cd_wave = calculate_wave_drag(
        mach=mach,
        fuselage_length_m=geometry.fuselage_length_m,
        fuselage_diameter_m=geometry.fuselage_diameter_m,
        s_ref_m2=s_ref_m2,
        wing_volume_m3=wing_vol,
    )

    if cd_wave > 0:
        breakdown.append(DragComponent("Wave Drag", 0.0, 0.0, 0.0, 1.0, cd_wave * s_ref_m2, cd_wave))

    return DragBuildUpResult(
        cd0=cd0_total + cd0_misc + cd_wave,
        breakdown=breakdown,
        reynolds_number_fuselage=re_fus,
        reynolds_number_wing=re_wing,
        skin_friction_wing=cf_wing,
        wave_drag_cd=cd_wave,
    )


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
    thickness_ratio: float = 0.1,
) -> dict:
    cd_total: list[float] = []
    for mach in mach_range:
        e = 0.8
        k = 1.0 / (pi * aspect_ratio * e)

        cd = cd0_subsonic + k * cl * cl
        if mach >= mach_crit:
            if mach < mach_dd:
                frac = (mach - mach_crit) / max(mach_dd - mach_crit, 1e-6)
                cd += 0.02 * frac * frac
            else:
                beta_ref = sqrt(mach_dd * mach_dd - 1.0)
                beta_curr = sqrt(mach * mach - 1.0)
                decay = beta_ref / max(beta_curr, 1e-6)
                wave = 0.06 * thickness_ratio * decay
                cd += wave

        cd_total.append(cd)

    return {"mach": mach_range, "cd_total": cd_total}


# Alias for compatibility
estimate_cd0_drag_buildup = calculate_parasite_drag_buildup
