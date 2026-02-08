from __future__ import annotations

from dataclasses import dataclass, field
from math import log10, pi, cos, sqrt, pow

from .atmosphere import isa_tropopause, AtmosphereState
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


def calculate_cf_turbulent(re: float, mach: float) -> float:
    """
    Calculate turbulent skin friction coefficient for a flat plate.
    Using Prandtl-Schlichting formula with compressibility correction.
    """
    if re <= 0:
        return 0.0
    
    # Prandtl-Schlichting
    cf_incomp = 0.455 / (log10(re) ** 2.58)
    
    # Compressibility correction (approximate)
    factor = pow(1.0 + 0.144 * mach * mach, 0.65)
    
    return cf_incomp / factor


def calculate_form_factor_fuselage(l_d_ratio: float) -> float:
    """
    Raymer Eq 12.31 for fuselage form factor.
    FF = 1 + 60/(f^3) + f/400  where f = L/d
    """
    f = l_d_ratio
    return 1.0 + 60.0 / (f * f * f) + f / 400.0


def calculate_form_factor_wing(t_c: float, sweep_max_t_rad: float, lift_coeff: float = 0.0) -> float:
    """
    Raymer Eq 12.30 for wing/tail form factor.
    FF = [1 + L(t/c) + 100(t/c)^4] * R_LS
    """
    # Simple version for thickness only
    # Assuming sweep of max thickness line.
    cos_sweep = cos(sweep_max_t_rad)
    return 1.0 + 1.2 * t_c / cos_sweep + 100.0 * pow(t_c / cos_sweep, 4)


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
    Calculates CD0 using component buildup method (Raymer).
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
        f_ratio = geometry.fuselage_length_m / geometry.fuselage_diameter_m if geometry.fuselage_diameter_m > 0 else 10.0
        ff_fus = calculate_form_factor_fuselage(f_ratio)
        
    swet_fus = geometry.fuselage_wetted_area_m2
    if swet_fus is None:
        # Simple approximation
        swet_fus = pi * geometry.fuselage_diameter_m * geometry.fuselage_length_m * 0.8 # approx
        
    q_fus = geometry.interference_factor_fuselage
    
    f_fus = cf_fus * ff_fus * q_fus * swet_fus
    cd0_fus = f_fus / s_ref_m2
    breakdown.append(DragComponent("Fuselage", swet_fus, cf_fus, ff_fus, q_fus, f_fus, cd0_fus))
    
    # 2. Wing
    re_wing = (rho * v * l_char_wing_m) / mu
    cf_wing = calculate_cf_turbulent(re_wing, mach)
    
    ff_wing = geometry.wing_form_factor
    if ff_wing is None:
        ff_wing = calculate_form_factor_wing(geometry.wing_t_c, 0.0) # Assume 0 sweep for form factor if unknown
        
    swet_wing = geometry.wing_wetted_area_m2
    if swet_wing is None:
        swet_wing = s_ref_m2 * 2.0 * 1.02 # Exposed * 2 * curvature
        
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
        re_ht = re_wing # Approximation if mac not given
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
    
    return DragBuildUpResult(
        cd0=cd0_total + cd0_misc,
        breakdown=breakdown,
        reynolds_number_fuselage=re_fus,
        reynolds_number_wing=re_wing,
        skin_friction_wing=cf_wing
    )

# Alias for compatibility if needed, or update caller
estimate_cd0_drag_buildup = calculate_parasite_drag_buildup
