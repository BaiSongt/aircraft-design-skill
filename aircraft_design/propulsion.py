from __future__ import annotations

from dataclasses import dataclass

from .atmosphere import isa_tropopause
from .units import CONST


@dataclass(frozen=True)
class PropulsionModel:
    type: str
    thrust_sl_n: float | None
    power_sl_w: float | None
    tsfc_1_s: float | None
    sfc_1_s: float | None
    prop_efficiency: float | None
    jet_lapse_exp: float
    prop_power_lapse_exp: float
    mct_to_mto_ratio: float = 1.0
    jet_mach_factor: float = 0.0  # T = T_sl * sigma^n * (1 + factor * M)
    jet_model_method: str = "simple"  # "simple" or "mattingly_low_bypass"
    bypass_ratio: float = 0.3
    mil_to_ab_sfc_ratio: float = 2.5  # Ratio of AB SFC to Mil SFC (SL)
    tsfc_ab_1_s: float | None = None  # Explicit AB SFC if provided


def build_propulsion_model(
    propulsion_in: dict, *, mtow_kg: float | None = None, thrust_to_weight: float | None = None
) -> PropulsionModel:
    ptype = propulsion_in["type"]
    thrust_sl_n = propulsion_in.get("thrust_sl_n", None)
    power_sl_w = propulsion_in.get("power_sl_w", None)

    if thrust_sl_n is None and mtow_kg is not None and thrust_to_weight is not None:
        thrust_sl_n = thrust_to_weight * mtow_kg * CONST.g0_m_s2

    jet_lapse_exp = float(propulsion_in.get("jet_lapse_exp", 0.7))
    prop_power_lapse_exp = float(propulsion_in.get("prop_power_lapse_exp", 1.0))
    mct_ratio = float(propulsion_in.get("mct_to_mto_ratio", 1.0))
    jet_mach_factor = float(propulsion_in.get("jet_mach_factor", 0.0))

    jet_model_method = propulsion_in.get("jet_model_method", "simple")
    bypass_ratio = float(propulsion_in.get("bypass_ratio", 0.3))

    tsfc_1_s = propulsion_in.get("tsfc_1_s", None)
    tsfc_ab_1_s = propulsion_in.get("tsfc_ab_1_s", None)

    # If explicit AB SFC provided, calculate/override ratio or just store it
    mil_to_ab_sfc_ratio = float(propulsion_in.get("mil_to_ab_sfc_ratio", 2.5))
    if tsfc_1_s is not None and tsfc_ab_1_s is not None and tsfc_1_s > 0:
        mil_to_ab_sfc_ratio = tsfc_ab_1_s / tsfc_1_s

    sfc_1_s = propulsion_in.get("sfc_1_s", None)
    eta_prop = propulsion_in.get("prop_efficiency", None)

    # Defaults for robustness
    if ptype == "jet" and tsfc_1_s is None:
        tsfc_1_s = 2.26e-5  # Approx 0.8 lb/lbf/hr

    if ptype == "prop":
        if sfc_1_s is None:
            sfc_1_s = 8.45e-8  # Approx 0.5 lb/hp/hr
        if eta_prop is None:
            eta_prop = 0.8

    return PropulsionModel(
        type=ptype,
        thrust_sl_n=thrust_sl_n,
        power_sl_w=power_sl_w,
        tsfc_1_s=tsfc_1_s,
        sfc_1_s=sfc_1_s,
        prop_efficiency=eta_prop,
        jet_lapse_exp=jet_lapse_exp,
        prop_power_lapse_exp=prop_power_lapse_exp,
        mct_to_mto_ratio=mct_ratio,
        jet_mach_factor=jet_mach_factor,
        jet_model_method=jet_model_method,
        bypass_ratio=bypass_ratio,
        mil_to_ab_sfc_ratio=mil_to_ab_sfc_ratio,
        tsfc_ab_1_s=tsfc_ab_1_s,
    )


def _calculate_mattingly_thrust_factor(
    mach: float,
    theta: float,
    delta: float,
    afterburner: bool = False,
) -> float:
    # Mattingly low-bypass turbofan model (2000+ technology)
    # Reference: docs/theory/04_engine_characteristics.md

    # theta = T / T_sl
    # delta = P / P_sl
    # TR = theta (approx for static T_sl)

    # The formulas in the theory document use (M-1) which appears to be a typo
    # for M, because at M=0, T should equal T_sl (alpha=1).
    # If we use (M-1), at M=0, alpha != 1.
    # We assume the formulas are polynomials in M.
    m_val = mach

    if afterburner:
        # α_afterburner = (1 - 0.3M + 0.2M^2) * (δ / θ^0.8)^0.7
        term1 = 1.0 - 0.3 * m_val + 0.2 * (m_val**2)
        term2 = (delta / (theta**0.8)) ** 0.7
        alpha = term1 * term2
    else:
        # α_mil = (1 - 0.6M + 0.1M^2) * (δ / θ^0.8)^0.7
        term1 = 1.0 - 0.6 * m_val + 0.1 * (m_val**2)
        term2 = (delta / (theta**0.8)) ** 0.7
        alpha = term1 * term2

    return max(0.0, alpha)


def thrust_available_n(
    model: PropulsionModel, *, altitude_m: float, speed_m_s: float, isa_delta_c: float = 0.0, rating: str = "mto"
) -> float:
    atm = isa_tropopause(altitude_m, delta_t_k=float(isa_delta_c))
    sigma = atm.rho_kg_m3 / CONST.rho0_kg_m3

    # Rating factor
    r_factor = 1.0
    if rating in ["mct", "max_continuous", "cruise", "climb"]:
        r_factor = model.mct_to_mto_ratio

    if model.type == "jet":
        if model.thrust_sl_n is None:
            raise ValueError("Jet model requires thrust_sl_n.")
        mach = speed_m_s / atm.a_m_s

        if model.jet_model_method == "mattingly_low_bypass":
            # Use Mattingly model
            theta = atm.t_k / 288.15
            delta = atm.p_pa / 101325.0

            # Assuming MTO is afterburner if rating is mto? Or just Mil?
            # Usually MTO for fighters implies AB.
            # But let's assume MTO = Max Power.
            # If r_factor < 1.0 (cruise/mct), we use Mil curve scaled?
            # The doc distinguishes "Afterburner" and "Mil" (non-afterburning max).

            # Logic: If rating="mto" and we assume AB capability -> AB curve.
            # If rating="mct" -> Mil curve.
            # Since we don't have an explicit AB flag in model, let's assume:
            # If r_factor == 1.0 -> AB (if applicable) or Mil (if no AB).
            # But the formula gives distinct curves.
            # Let's use Mil curve as baseline for non-AB engines or cruise.
            # Let's assume "mto" uses AB curve if the user selected "mattingly_low_bypass" which implies a fighter engine.

            use_ab = rating == "mto"
            alpha = _calculate_mattingly_thrust_factor(mach, theta, delta, afterburner=use_ab)

            # If rating is cruise (r_factor < 1), we apply r_factor to the calculated alpha?
            # Or should we use Mil curve for cruise?
            # Mil curve is "Maximum Non-Augmented".
            # Cruise is usually part of Mil.
            # So: if use_ab is False (rating != mto), we calculate Mil alpha.
            # Then apply r_factor (e.g. 0.85 for MCT).

            # Refined logic:
            # If rating == "mto": use AB curve.
            # If rating != "mto": use Mil curve * r_factor.

            if not use_ab:
                # Recalculate alpha for Mil
                alpha = _calculate_mattingly_thrust_factor(mach, theta, delta, afterburner=False)
                alpha *= r_factor

            return model.thrust_sl_n * alpha

        else:
            # Simple model
            mach_corr = 1.0 + model.jet_mach_factor * mach
            return model.thrust_sl_n * (sigma**model.jet_lapse_exp) * mach_corr * r_factor

    if model.type == "prop":
        if model.power_sl_w is None:
            if model.thrust_sl_n is None:
                raise ValueError("Prop model requires power_sl_w or thrust_sl_n.")
            # If thrust_sl_n is given, assume it behaves like constant thrust (unlikely for prop) or simplified
            return model.thrust_sl_n * r_factor

        p_avail = model.power_sl_w * (sigma**model.prop_power_lapse_exp) * r_factor
        eta = model.prop_efficiency if model.prop_efficiency is not None else 0.8
        v = max(1.0, speed_m_s)
        return eta * p_avail / v

    raise ValueError("propulsion.type must be 'jet' or 'prop'.")


def _calculate_mattingly_sfc_factor(
    mach: float,
    theta: float,
    afterburner: bool = False,
) -> float:
    # Mattingly low-bypass turbofan SFC model
    # Reference: docs/theory/04_engine_characteristics.md

    # We use M instead of (M-1) to ensure factor=1.0 at M=0 (Static)
    m_val = mach

    if afterburner:
        # SFC_ab = SFC_SL * (1 + 0.5M) * θ^0.5
        factor = (1.0 + 0.5 * m_val) * (theta**0.5)
    else:
        # SFC_mil = SFC_SL * (1 - 0.3M + 0.1M^2) * θ^0.5
        factor = (1.0 - 0.3 * m_val + 0.1 * (m_val**2)) * (theta**0.5)

    return factor


def fuel_flow_n_s(
    model: PropulsionModel,
    *,
    thrust_n: float,
    shaft_power_w: float | None = None,
    altitude_m: float = 0.0,
    speed_m_s: float = 0.0,
    isa_delta_c: float = 0.0,
) -> float:
    if model.type == "jet":
        if model.tsfc_1_s is None:
            raise ValueError("Jet model requires tsfc_1_s.")

        sfc = model.tsfc_1_s

        if model.jet_model_method == "mattingly_low_bypass":
            # Mattingly Model with AB logic
            atm = isa_tropopause(altitude_m, delta_t_k=float(isa_delta_c))
            mach = speed_m_s / atm.a_m_s
            theta = atm.t_k / 288.15

            # Calculate Mil Thrust Available to determine if AB is needed
            # We assume mct_to_mto_ratio represents Mil/AB ratio if AB is present
            try:
                t_mil_avail = thrust_available_n(
                    model, altitude_m=altitude_m, speed_m_s=speed_m_s, isa_delta_c=isa_delta_c, rating="mct"
                )
            except Exception:
                t_mil_avail = 1.0  # Safe fallback

            # Check if we need AB
            if thrust_n > t_mil_avail and t_mil_avail > 1.0:
                # AB Regime
                # Use AB SFC factor
                factor = _calculate_mattingly_sfc_factor(mach, theta, afterburner=True)
                sfc = model.tsfc_1_s * factor * model.mil_to_ab_sfc_ratio
                # We don't apply throttle correction for AB in this simple model
            else:
                # Mil Regime
                throttle = min(1.0, max(0.0, thrust_n / t_mil_avail)) if t_mil_avail > 1.0 else 1.0
                factor = _calculate_mattingly_sfc_factor(mach, theta, afterburner=False)
                sfc = model.tsfc_1_s * factor

                # Throttle correction for Mil (partial power)
                sfc_throttle_factor = 1.0 + 0.2 * (1.0 - throttle)
                sfc *= sfc_throttle_factor

        return sfc * max(0.0, thrust_n) * CONST.g0_m_s2

    if model.type == "prop":
        if model.sfc_1_s is None:
            raise ValueError("Prop model requires sfc_1_s.")
        if shaft_power_w is None:
            raise ValueError("Prop model requires shaft_power_w for fuel flow.")
        return model.sfc_1_s * max(0.0, shaft_power_w) * CONST.g0_m_s2
    raise ValueError("propulsion.type must be 'jet' or 'prop'.")


def calculate_turbofan_thrust(
    *,
    thrust_sl_n: float,
    mach: float,
    altitude_m: float,
    throttle_position: float = 1.0,
    bypass_ratio: float = 6.0,
    isa_delta_c: float = 0.0,
) -> dict:
    from .atmosphere import isa_tropopause
    from .units import CONST

    if thrust_sl_n <= 0.0:
        raise ValueError("thrust_sl_n must be positive.")
    if throttle_position < 0.0 or throttle_position > 1.0:
        raise ValueError("throttle_position must be in [0, 1].")

    atm = isa_tropopause(altitude_m, delta_t_k=float(isa_delta_c))
    sigma = atm.rho_kg_m3 / CONST.rho0_kg_m3

    alpha = 0.7 + 0.1 * (1.0 - bypass_ratio / 10.0)

    thrust_available_n = thrust_sl_n * (sigma**alpha) * throttle_position

    mach_factor = 1.0 + 0.3 * mach
    thrust_available_n *= mach_factor

    return {
        "thrust_available_n": thrust_available_n,
        "thrust_sl_n": thrust_sl_n,
        "mach": mach,
        "altitude_m": altitude_m,
        "throttle_position": throttle_position,
        "sigma": sigma,
        "alpha": alpha,
        "bypass_ratio": bypass_ratio,
    }


def calculate_turbofan_sfc(
    *,
    sfc_sl: float,
    mach: float,
    altitude_m: float,
    throttle_position: float = 1.0,
    bypass_ratio: float = 6.0,
    isa_delta_c: float = 0.0,
) -> dict:
    from .atmosphere import isa_tropopause
    from .units import CONST

    if sfc_sl <= 0.0:
        raise ValueError("sfc_sl must be positive.")
    if throttle_position < 0.0 or throttle_position > 1.0:
        raise ValueError("throttle_position must be in [0, 1].")

    atm = isa_tropopause(altitude_m, delta_t_k=float(isa_delta_c))
    sigma = atm.rho_kg_m3 / CONST.rho0_kg_m3

    beta = 0.8 + 0.1 * (1.0 - bypass_ratio / 10.0)

    sfc_available = sfc_sl * (sigma**beta) * (1.0 + 0.5 * (1.0 - throttle_position))

    mach_factor = 1.0 + 0.2 * mach
    sfc_available *= mach_factor

    return {
        "sfc_available": sfc_available,
        "sfc_sl": sfc_sl,
        "mach": mach,
        "altitude_m": altitude_m,
        "throttle_position": throttle_position,
        "sigma": sigma,
        "beta": beta,
        "bypass_ratio": bypass_ratio,
    }


def generate_thrust_envelope(
    *,
    thrust_sl_n: float,
    mach_range: list[float],
    altitude_range: list[float],
    throttle_position: float = 1.0,
    bypass_ratio: float = 6.0,
    isa_delta_c: float = 0.0,
) -> dict:
    thrust_grid: list[list[float]] = []

    for mach in mach_range:
        thrust_row: list[float] = []
        for altitude in altitude_range:
            result = calculate_turbofan_thrust(
                thrust_sl_n=thrust_sl_n,
                mach=mach,
                altitude_m=altitude,
                throttle_position=throttle_position,
                bypass_ratio=bypass_ratio,
                isa_delta_c=isa_delta_c,
            )
            thrust_row.append(result["thrust_available_n"])
        thrust_grid.append(thrust_row)

    return {
        "mach": mach_range,
        "altitude_m": altitude_range,
        "thrust_n": thrust_grid,
    }


def generate_sfc_envelope(
    *,
    sfc_sl: float,
    mach_range: list[float],
    altitude_range: list[float],
    throttle_position: float = 1.0,
    bypass_ratio: float = 6.0,
    isa_delta_c: float = 0.0,
) -> dict:
    sfc_grid: list[list[float]] = []

    for mach in mach_range:
        sfc_row: list[float] = []
        for altitude in altitude_range:
            result = calculate_turbofan_sfc(
                sfc_sl=sfc_sl,
                mach=mach,
                altitude_m=altitude,
                throttle_position=throttle_position,
                bypass_ratio=bypass_ratio,
                isa_delta_c=isa_delta_c,
            )
            sfc_row.append(result["sfc_available"])
        sfc_grid.append(sfc_row)

    return {
        "mach": mach_range,
        "altitude_m": altitude_range,
        "sfc": sfc_grid,
    }
