from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Constants:
    g0_m_s2: float = 9.80665
    rho0_kg_m3: float = 1.225
    p0_pa: float = 101325.0
    t0_k: float = 288.15
    r_air_j_kg_k: float = 287.05287
    gamma_air: float = 1.4


CONST = Constants()
