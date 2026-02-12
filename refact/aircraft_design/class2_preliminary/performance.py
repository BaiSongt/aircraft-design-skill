from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from ..common.atmosphere import qbar_pa
from .constraints import AeroPolar
from ..common.units import CONST


@dataclass(frozen=True)
class CruisePoint:
    h_m: float
    v_m_s: float
    rho_kg_m3: float
    q_pa: float
    cl: float
    cd: float
    lift_to_drag: float


def cruise_point(
    *,
    rho_kg_m3: float,
    v_m_s: float,
    w_kg: float,
    s_m2: float,
    polar: AeroPolar,
) -> CruisePoint:
    if rho_kg_m3 <= 0.0 or v_m_s <= 0.0:
        raise ValueError("Invalid cruise atmosphere inputs.")
    if w_kg <= 0.0 or s_m2 <= 0.0:
        raise ValueError("Invalid weight/area inputs.")

    q = qbar_pa(rho_kg_m3, v_m_s)
    w_n = w_kg * CONST.g0_m_s2
    cl = w_n / (q * s_m2)
    cd = polar.cd(cl)
    ld = cl / cd if cd > 0.0 else 0.0
    return CruisePoint(
        h_m=0.0,
        v_m_s=v_m_s,
        rho_kg_m3=rho_kg_m3,
        q_pa=q,
        cl=cl,
        cd=cd,
        lift_to_drag=ld,
    )


def required_thrust_newton(
    *,
    rho_kg_m3: float,
    v_m_s: float,
    w_kg: float,
    s_m2: float,
    polar: AeroPolar,
) -> float:
    cp = cruise_point(rho_kg_m3=rho_kg_m3, v_m_s=v_m_s, w_kg=w_kg, s_m2=s_m2, polar=polar)
    d_n = cp.q_pa * s_m2 * cp.cd
    return d_n


def climb_rate_m_s(
    *,
    thrust_n: float,
    rho_kg_m3: float,
    v_m_s: float,
    w_kg: float,
    s_m2: float,
    polar: AeroPolar,
) -> float:
    d_n = required_thrust_newton(rho_kg_m3=rho_kg_m3, v_m_s=v_m_s, w_kg=w_kg, s_m2=s_m2, polar=polar)
    w_n = w_kg * CONST.g0_m_s2
    excess_thrust = max(0.0, thrust_n - d_n)
    return excess_thrust * v_m_s / w_n


def calculate_service_ceiling(
    *,
    thrust_sl_n: float,
    weight_kg: float,
    s_m2: float,
    polar: AeroPolar,
    jet_lapse_exp: float = 0.7,
    min_climb_rate: float = 0.508,
    isa_delta_c: float = 0.0,
) -> dict:
    from ..common.atmosphere import isa_tropopause
    from .propulsion import PropulsionModel

    if thrust_sl_n <= 0.0 or weight_kg <= 0.0 or s_m2 <= 0.0:
        raise ValueError("Invalid thrust, weight, or area inputs.")

    low_alt = 0.0
    high_alt = 30000.0

    for _ in range(100):
        mid_alt = (low_alt + high_alt) / 2.0

        atm = isa_tropopause(mid_alt, delta_t_k=float(isa_delta_c))

        model = PropulsionModel(
            type="jet",
            thrust_sl_n=thrust_sl_n,
            power_sl_w=None,
            tsfc_1_s=None,
            sfc_1_s=None,
            prop_efficiency=None,
            jet_lapse_exp=jet_lapse_exp,
            prop_power_lapse_exp=1.0,
        )

        from .propulsion import thrust_available_n

        thrust_n = thrust_available_n(model, altitude_m=mid_alt, speed_m_s=atm.a_m_s * 0.7)

        rc = climb_rate_m_s(
            thrust_n=thrust_n,
            rho_kg_m3=atm.rho_kg_m3,
            v_m_s=atm.a_m_s * 0.7,
            w_kg=weight_kg,
            s_m2=s_m2,
            polar=polar,
        )

        if rc < min_climb_rate:
            high_alt = mid_alt
        else:
            low_alt = mid_alt

        if high_alt - low_alt < 10.0:
            break

    service_ceiling_m = low_alt

    return {
        "service_ceiling_m": service_ceiling_m,
        "min_climb_rate_m_s": min_climb_rate,
        "climb_rate_at_ceiling_m_s": rc,
        "weight_kg": weight_kg,
        "s_m2": s_m2,
    }


def calculate_turn_radius(
    *,
    v_m_s: float,
    load_factor: float,
) -> float:
    if v_m_s <= 0.0:
        raise ValueError("v_m_s must be positive.")
    if load_factor < 1.0:
        raise ValueError("load_factor must be >= 1.0.")

    turn_radius_m = (v_m_s**2) / (CONST.g0_m_s2 * (load_factor**2 - 1.0) ** 0.5)

    return turn_radius_m


def calculate_turn_rate(
    *,
    v_m_s: float,
    load_factor: float,
) -> float:
    if v_m_s <= 0.0:
        raise ValueError("v_m_s must be positive.")
    if load_factor < 1.0:
        raise ValueError("load_factor must be >= 1.0.")

    turn_rate_rad_s = (CONST.g0_m_s2 * (load_factor**2 - 1.0) ** 0.5) / v_m_s

    return turn_rate_rad_s


def calculate_sustained_turn_load(
    *,
    thrust_n: float,
    weight_kg: float,
    s_m2: float,
    polar: AeroPolar,
    rho_kg_m3: float,
    v_m_s: float,
    cl_max: float | None = None,
    max_load_factor: float | None = None,
) -> dict:
    if thrust_n <= 0.0 or weight_kg <= 0.0 or s_m2 <= 0.0 or v_m_s <= 0.0:
        raise ValueError("Invalid thrust, weight, area, or speed inputs.")

    w_n = weight_kg * CONST.g0_m_s2
    q = 0.5 * rho_kg_m3 * v_m_s**2

    # Thrust limit calculation
    # Thrust = Drag = q * S * (CD0 + K * CL^2)
    # CL = n * W / (q * S)
    # T = q * S * CD0 + q * S * K * (n * W / (q * S))^2
    # n^2 = (T - q * S * CD0) * (q * S) / (K * W^2)

    drag_parasitic = q * s_m2 * polar.cd0
    excess_thrust_for_lift = thrust_n - drag_parasitic

    if excess_thrust_for_lift <= 0.0:
        # Cannot even sustain level flight at this speed (or just parasitic drag is too high)
        n_thrust = 0.0
    else:
        k = polar.k
        n_sq = (excess_thrust_for_lift * q * s_m2) / (k * w_n**2)
        n_thrust = sqrt(n_sq)

    # Aerodynamic limit (Stall)
    # CL = n * W / (q * S) <= CL_max -> n <= CL_max * q * S / W
    n_aero = float("inf")
    if cl_max is not None:
        n_aero = cl_max * q * s_m2 / w_n

    # Structural limit
    n_struct = float("inf")
    if max_load_factor is not None:
        n_struct = max_load_factor

    # Combined limit
    n_sustained = min(n_thrust, n_aero, n_struct)

    # Calculate resulting CL and CD
    cl_sustained = n_sustained * w_n / (q * s_m2) if n_sustained > 0 else 0.0
    cd_sustained = polar.cd(cl_sustained)

    return {
        "n_sustained": n_sustained,
        "n_thrust_limited": n_thrust,
        "n_aero_limited": n_aero if n_aero != float("inf") else None,
        "n_struct_limited": n_struct if n_struct != float("inf") else None,
        "cl": cl_sustained,
        "cd": cd_sustained,
        "lift_to_drag": cl_sustained / cd_sustained if cd_sustained > 0.0 else 0.0,
        "thrust_n": thrust_n,
        "weight_kg": weight_kg,
        "v_m_s": v_m_s,
    }


def calculate_horizontal_acceleration(
    *,
    thrust_n: float,
    weight_kg: float,
    s_m2: float,
    polar: AeroPolar,
    rho_kg_m3: float,
    v_m_s: float,
) -> dict:
    if thrust_n <= 0.0 or weight_kg <= 0.0 or s_m2 <= 0.0:
        raise ValueError("Invalid thrust, weight, or area inputs.")

    d_n = required_thrust_newton(
        rho_kg_m3=rho_kg_m3,
        v_m_s=v_m_s,
        w_kg=weight_kg,
        s_m2=s_m2,
        polar=polar,
    )

    excess_thrust = thrust_n - d_n

    acceleration_m_s2 = excess_thrust / weight_kg

    return {
        "acceleration_m_s2": acceleration_m_s2,
        "excess_thrust_n": excess_thrust,
        "drag_n": d_n,
        "thrust_n": thrust_n,
        "weight_kg": weight_kg,
    }


def generate_performance_envelope(
    *,
    thrust_sl_n: float,
    weight_kg: float,
    s_m2: float,
    polar: AeroPolar,
    jet_lapse_exp: float = 0.7,
    mach_range: list[float],
    altitude_range: list[float],
    isa_delta_c: float = 0.0,
) -> dict:
    from ..common.atmosphere import isa_tropopause
    from .propulsion import PropulsionModel, thrust_available_n

    climb_rate_grid: list[list[float]] = []
    turn_radius_grid: list[list[float]] = []
    n_sustained_grid: list[list[float]] = []

    model = PropulsionModel(
        type="jet",
        thrust_sl_n=thrust_sl_n,
        power_sl_w=None,
        tsfc_1_s=None,
        sfc_1_s=None,
        prop_efficiency=None,
        jet_lapse_exp=jet_lapse_exp,
        prop_power_lapse_exp=1.0,
    )

    for mach in mach_range:
        climb_rate_row: list[float] = []
        turn_radius_row: list[float] = []
        n_sustained_row: list[float] = []

        for altitude in altitude_range:
            atm = isa_tropopause(altitude, delta_t_k=float(isa_delta_c))
            v_m_s = mach * atm.a_m_s

            thrust_n = thrust_available_n(model, altitude_m=altitude, speed_m_s=v_m_s)

            rc = climb_rate_m_s(
                thrust_n=thrust_n,
                rho_kg_m3=atm.rho_kg_m3,
                v_m_s=v_m_s,
                w_kg=weight_kg,
                s_m2=s_m2,
                polar=polar,
            )

            sustained_result = calculate_sustained_turn_load(
                thrust_n=thrust_n,
                weight_kg=weight_kg,
                s_m2=s_m2,
                polar=polar,
                rho_kg_m3=atm.rho_kg_m3,
                v_m_s=v_m_s,
            )

            turn_radius = calculate_turn_radius(v_m_s=v_m_s, load_factor=sustained_result["n_sustained"])

            climb_rate_row.append(rc)
            turn_radius_row.append(turn_radius)
            n_sustained_row.append(sustained_result["n_sustained"])

        climb_rate_grid.append(climb_rate_row)
        turn_radius_grid.append(turn_radius_row)
        n_sustained_grid.append(n_sustained_row)

    return {
        "mach": mach_range,
        "altitude_m": altitude_range,
        "climb_rate_m_s": climb_rate_grid,
        "turn_radius_m": turn_radius_grid,
        "n_sustained": n_sustained_grid,
    }
