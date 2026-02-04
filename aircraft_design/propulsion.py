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
    )


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


def fuel_flow_n_s(model: PropulsionModel, *, thrust_n: float, shaft_power_w: float | None = None) -> float:
    if model.type == "jet":
        if model.tsfc_1_s is None:
            raise ValueError("Jet model requires tsfc_1_s.")
        return model.tsfc_1_s * max(0.0, thrust_n)
    if model.type == "prop":
        if model.sfc_1_s is None:
            raise ValueError("Prop model requires sfc_1_s.")
        if shaft_power_w is None:
            raise ValueError("Prop model requires shaft_power_w for fuel flow.")
        return model.sfc_1_s * max(0.0, shaft_power_w)
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
