from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt

from .units import CONST


@dataclass(frozen=True)
class AtmosphereState:
    h_m: float
    t_k: float
    p_pa: float
    rho_kg_m3: float
    a_m_s: float
    mu_kg_ms: float
    sigma: float


def _mu_sutherland_pa_s(t_k: float) -> float:
    mu0 = 1.716e-5
    t0 = 273.15
    s = 110.4
    return mu0 * (t_k / t0) ** 1.5 * (t0 + s) / (t_k + s)


def isa_tropopause(
    h_m: float,
    *,
    t0_k: float = CONST.t0_k,
    p0_pa: float = CONST.p0_pa,
    lapse_k_m: float = -0.0065,
    h_tropo_m: float = 11000.0,
    delta_t_k: float = 0.0,
) -> AtmosphereState:
    if h_m < 0.0:
        h_m = 0.0

    r = CONST.r_air_j_kg_k

    if h_m <= h_tropo_m:
        t = t0_k + lapse_k_m * h_m
        p = p0_pa * (t / t0_k) ** (-CONST.g0_m_s2 / (lapse_k_m * r))
    else:
        t_tropo = t0_k + lapse_k_m * h_tropo_m
        p_tropo = p0_pa * (t_tropo / t0_k) ** (-CONST.g0_m_s2 / (lapse_k_m * r))
        t = t_tropo
        p = p_tropo * exp(-CONST.g0_m_s2 * (h_m - h_tropo_m) / (r * t))

    t = t + float(delta_t_k)
    rho = p / (r * t)
    a = sqrt(CONST.gamma_air * r * t)
    mu = _mu_sutherland_pa_s(t)
    sigma = rho / CONST.rho0_kg_m3
    return AtmosphereState(h_m=h_m, t_k=t, p_pa=p, rho_kg_m3=rho, a_m_s=a, mu_kg_ms=mu, sigma=sigma)


def qbar_pa(rho_kg_m3: float, v_m_s: float) -> float:
    return 0.5 * rho_kg_m3 * v_m_s * v_m_s
