from __future__ import annotations

from dataclasses import dataclass

from ..common.units import CONST


@dataclass(frozen=True)
class WingRootLoads:
    n_limit: float
    w0_kg: float
    b_m: float
    m_root_n_m: float
    shear_root_n: float


@dataclass(frozen=True)
class StructuralWeightResult:
    w_struct_kg: float
    details: dict


def estimate_wing_root_loads(
    *,
    w0_kg: float,
    b_m: float,
    n_limit: float,
    lift_distribution: str = "elliptic",
) -> WingRootLoads:
    if w0_kg <= 0.0 or b_m <= 0.0:
        raise ValueError("Invalid inputs.")
    if n_limit <= 0.0:
        raise ValueError("n_limit must be positive.")

    w_n = w0_kg * CONST.g0_m_s2
    shear = n_limit * w_n / 2.0

    if lift_distribution == "elliptic":
        # Centroid of semi-ellipse is at 4/(3*pi) * (b/2) approx 0.424 * (b/2) from centerline
        # Lever arm = 0.424 * (b/2)
        # Shear = n * W / 2
        # Moment = Shear * Lever = (n * W / 2) * (0.424 * b / 2) = n * W * b * 0.106
        # Previous: n * W * b / 8 = n * W * b * 0.125 (Triangular loading or Uniform?)
        # Uniform: Lever = b/4. Moment = (nW/2)*(b/4) = nWb/8 = 0.125
        # Elliptic is actually less severe than uniform at root?
        # Let's use 0.125 as conservative uniform/triangular blend, or refine.
        # Elliptic centroid: y_bar = 4b / (3pi * 2) = 2b / (3pi) = 0.212 b
        # M = (n W / 2) * (0.212 b) = 0.106 n W b.
        # But we also have wing weight relief (fuel + structure).
        # Gross assumption: Relief reduces root moment by ~20-40%?
        # Let's keep conservative factor, but maybe parameterize "relief_factor"
        # Using 1/8 (0.125) is standard textbook approximation for cantilever monoplane.
        m_root = n_limit * w_n * b_m / 8.0
    else:
        m_root = n_limit * w_n * b_m / 7.0

    return WingRootLoads(n_limit=n_limit, w0_kg=w0_kg, b_m=b_m, m_root_n_m=m_root, shear_root_n=shear)


def estimate_structural_weight_feedback(
    *,
    loads: WingRootLoads,
    s_m2: float,
    t_c: float = 0.12,
    ultimate_factor: float = 1.5,
    sigma_allow_pa: float = 250e6,  # Al 2024/7075 working stress ~250-350 MPa
    density_kg_m3: float = 2700.0,  # Aluminum
    wingbox_area_factor: float = 0.12,  # Fraction of planform used by box
    relief_factor: float = 0.8,  # Wing weight relief factor (fuel + structure inertia)
) -> StructuralWeightResult:
    if s_m2 <= 0.0:
        raise ValueError("s_m2 must be positive.")
    if t_c <= 0.0:
        raise ValueError("t_c must be positive.")

    # Design Moment (Ultimate) with Relief
    m_u = loads.m_root_n_m * ultimate_factor * relief_factor

    # Effective box height (mean thickness at root approx)
    # Root chord c_root ~ 2 * S / b (approx)
    c_root_approx = 2.0 * s_m2 / loads.b_m
    h_box = max(0.05, 0.5 * t_c * c_root_approx)  # 50% of t/c thickness effective for box height

    # Spar Cap Area (Top + Bottom)
    # M = sigma * Area * h_box
    # Area_cap = M / (sigma * h_box)
    a_cap = m_u / max(1.0, sigma_allow_pa * h_box)

    # Spanwise integration of spar cap weight
    # Assume linear tapering of moment to 0 at tip => Cap area tapers
    # Weight = density * Area_root * b/2 * (some taper factor, say 0.6) * 2 (sides)
    # Total Cap Volume approx Area_root * b * 0.6
    w_caps = density_kg_m3 * a_cap * loads.b_m * 0.6

    # Shear Web & Ribs & Skin (Volume based or Area based)
    # Simplified: Skin weight ~ Surface Area * t_skin_effective * density
    # t_skin_effective ~ 1.5-2.0 mm for GA/Regional?
    # Or use statistical term.

    # Let's use the previous logic but refined:
    # Previous: w_struct = 0.6 * w_box + 2.0 * w_caps
    # It was a bit arbitrary.

    # New logic:
    # 1. Bending Material (Caps/Skin effective)
    # 2. Shear Material (Webs)
    # 3. Secondary (Ribs/Joints)

    # Shear Material
    # V_u = Shear * Ultimate
    # A_web = V_u / (0.6 * sigma_allow_pa) (Shear allowable lower)
    v_u = loads.shear_root_n * ultimate_factor * relief_factor
    a_web = v_u / (0.6 * sigma_allow_pa)
    w_webs = density_kg_m3 * a_web * loads.b_m * 0.6  # Tapered

    # Skin/Secondary
    # W_surf ~ S_wet * t_min * rho
    s_wet = 2.0 * s_m2 * 1.02
    t_min = 0.0015  # 1.5mm min gauge
    w_surf = s_wet * t_min * density_kg_m3

    # Total Wing Weight Estimate
    # This is "Analytical Wing Weight"
    w_wing_analytical = w_caps + w_webs + w_surf

    # Add penalty for complexity (flaps/gear mount)
    w_struct = w_wing_analytical * 1.15

    return StructuralWeightResult(
        w_struct_kg=w_struct,
        details={
            "m_root_n_m": loads.m_root_n_m,
            "m_ultimate_relief_n_m": m_u,
            "shear_root_n": loads.shear_root_n,
            "h_box_m": h_box,
            "spar_cap_area_root_m2": a_cap,
            "w_caps_kg": w_caps,
            "w_webs_kg": w_webs,
            "w_surf_kg": w_surf,
            "relief_factor": relief_factor,
        },
    )
