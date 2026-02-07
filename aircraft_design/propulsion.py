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
    sfc_1_s = propulsion_in.get("sfc_1_s", None)
    eta_prop = propulsion_in.get("prop_efficiency", None)

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
        term2 = (delta / (theta**0.8))**0.7
        alpha = term1 * term2
    else:
        # α_mil = (1 - 0.6M + 0.1M^2) * (δ / θ^0.8)^0.7
        term1 = 1.0 - 0.6 * m_val + 0.1 * (m_val**2)
        term2 = (delta / (theta**0.8))**0.7
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
            
            use_ab = (rating == "mto")
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
    
    m_minus_1 = mach - 1.0
    
    if afterburner:
        # SFC_ab = SFC_SL * (1 + 0.5(M-1)) * θ^0.5
        factor = (1.0 + 0.5 * m_minus_1) * (theta**0.5)
    else:
        # SFC_mil = SFC_SL * (1 - 0.3(M-1) + 0.1(M-1)^2) * θ^0.5
        factor = (1.0 - 0.3 * m_minus_1 + 0.1 * (m_minus_1**2)) * (theta**0.5)
        
    return factor


def fuel_flow_n_s(model: PropulsionModel, *, thrust_n: float, shaft_power_w: float | None = None, altitude_m: float = 0.0, speed_m_s: float = 0.0, isa_delta_c: float = 0.0) -> float:
    if model.type == "jet":
        if model.tsfc_1_s is None:
            raise ValueError("Jet model requires tsfc_1_s.")
        
        sfc = model.tsfc_1_s
        
        # Calculate throttle setting for SFC correction
        # We need available thrust at this condition
        try:
            t_avail = thrust_available_n(model, altitude_m=altitude_m, speed_m_s=speed_m_s, isa_delta_c=isa_delta_c, rating="mto")
            throttle = min(1.0, max(0.0, thrust_n / t_avail)) if t_avail > 1e-6 else 1.0
        except Exception:
            # Fallback if thrust calculation fails or circular dependency (though unlikely here)
            throttle = 1.0

        if model.jet_model_method == "mattingly_low_bypass":
            # Adjust SFC based on conditions
            atm = isa_tropopause(altitude_m, delta_t_k=float(isa_delta_c))
            mach = speed_m_s / atm.a_m_s
            theta = atm.t_k / 288.15
            
            # Use Mattingly SFC factor for Mach/Altitude
            factor = _calculate_mattingly_sfc_factor(mach, theta, afterburner=False)
            sfc = model.tsfc_1_s * factor
            
            # Apply partial power correction (approximate)
            # SFC typically increases at lower throttle settings
            # Using a simple linear approximation or the heuristic: SFC ~ SFC_ref * (1 + 0.2 * (1 - throttle))?
            # calculate_turbofan_sfc uses (1 + 0.5 * (1 - throttle)) which is quite strong.
            # Mattingly Eq 6.22 (Ed 2) suggests for non-AB:
            # C/C_max ~ ... complex function of T/T_max.
            # Let's use a milder correction for low-bypass:
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
    envelope = {
        "mach": mach_range,
        "altitude_m": altitude_range,
        "thrust_n": [],
    }
    
    for mach in mach_range:
        thrust_row = []
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
        envelope["thrust_n"].append(thrust_row)
    
    return envelope


def generate_sfc_envelope(
    *,
    sfc_sl: float,
    mach_range: list[float],
    altitude_range: list[float],
    throttle_position: float = 1.0,
    bypass_ratio: float = 6.0,
    isa_delta_c: float = 0.0,
) -> dict:
    envelope = {
        "mach": mach_range,
        "altitude_m": altitude_range,
        "sfc": [],
    }
    
    for mach in mach_range:
        sfc_row = []
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
        envelope["sfc"].append(sfc_row)
    
    return envelope
