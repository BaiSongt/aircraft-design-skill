from __future__ import annotations

from dataclasses import dataclass

from .atmosphere import qbar_pa
from .constraints import AeroPolar
from .units import CONST


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
