from dataclasses import dataclass
from math import sqrt


@dataclass
class DynamicStabilityResults:
    # Longitudinal
    short_period_natural_frequency: float  # rad/s
    short_period_damping_ratio: float
    phugoid_natural_frequency: float  # rad/s
    phugoid_damping_ratio: float

    # Lateral-Directional
    dutch_roll_natural_frequency: float  # rad/s
    dutch_roll_damping_ratio: float
    spiral_time_constant: float  # s (doubling time if unstable, halving if stable)
    roll_time_constant: float  # s

    # Qualities (Levels based on MIL-STD-1797 or similar, simplified)
    short_period_level: int
    phugoid_level: int
    dutch_roll_level: int


class DynamicStabilityAnalyzer:
    """
    Analyzes dynamic stability modes using linearized equations of motion approximations.
    References: Nelson, R.C., "Flight Stability and Automatic Control".
    """

    def analyze(
        self,
        velocity_tas: float,  # m/s
        density: float,  # kg/m^3
        wing_span: float,  # m
        wing_chord: float,  # m (mean aerodynamic chord)
        wing_area: float,  # m^2
        mass: float,  # kg
        ixx: float,  # kg*m^2
        iyy: float,  # kg*m^2
        izz: float,  # kg*m^2
        cla: float,  # Lift curve slope (1/rad)
        cma: float,  # Pitch moment due to alpha (1/rad)
        cmq: float,  # Pitch moment due to pitch rate (1/rad)
        cnb: float,  # Yaw moment due to beta (1/rad)
        clb: float,  # Roll moment due to beta (1/rad)
        clp: float,  # Roll moment due to roll rate (1/rad)
        cnr: float,  # Yaw moment due to yaw rate (1/rad)
        cwr: float = 0.0,  # Optional: Weathercock stability parameter? No, Cnr is damping.
    ) -> DynamicStabilityResults:

        # 1. Longitudinal Modes
        # ---------------------

        # Short Period Approximation
        # omega_n_sp ~= sqrt(Z_alpha * M_q / U - M_alpha)
        # But using non-dimensional derivatives:
        # M_alpha_dim = (rho * V^2 * S * c / (2 * Iyy)) * Cma
        # M_q_dim = (rho * V * S * c^2 / (4 * Iyy)) * Cmq
        # Z_alpha_dim = - (rho * V * S / (2 * m)) * Cla

        q_dyn = 0.5 * density * velocity_tas**2

        # Dimensional derivatives
        m_alpha = (q_dyn * wing_area * wing_chord / iyy) * cma
        m_q = (q_dyn * wing_area * wing_chord**2 / (2 * velocity_tas * iyy)) * cmq
        z_alpha = -(q_dyn * wing_area / mass) * cla

        # Short Period Natural Frequency & Damping
        # omega_n^2 ~= -M_alpha + Z_alpha * M_q / V (approx) -> usually dominated by M_alpha
        # More accurate approx: omega_n^2 = Z_alpha*M_q/V - M_alpha.
        # Note: M_q is usually negative, Z_alpha is negative. So Z_alpha*M_q/V is positive. M_alpha is negative for stability.
        # So -M_alpha is positive.

        wn_sp_sq = -m_alpha + (z_alpha * m_q / velocity_tas)  # Check signs carefully. Mq is damping (neg).
        # Actually standard approx: omega_n_sp = sqrt(-M_alpha + Z_alpha*M_q/u0) is common?
        # Let's use Nelson's approx:
        # omega_n_sp = sqrt( (Z_alpha * M_q / u0) - M_alpha )

        # Ensure positive under root
        if wn_sp_sq < 0:
            wn_sp = 0.0  # Unstable statically?
        else:
            wn_sp = sqrt(wn_sp_sq)

        # Damping: 2 * zeta * omega_n = -(M_q + Z_alpha/u0 + M_alpha_dot...)
        # Simplified: 2 * zeta * wn = -(M_q + Z_alpha / velocity_tas) -> Wait, Z_alpha is force/mass = accel.
        # Z_w = Z_alpha / u0.
        # 2*zeta*wn = -(M_q + Z_w)

        z_w = z_alpha / velocity_tas
        damping_term = -(m_q + z_w)
        zeta_sp = damping_term / (2 * wn_sp) if wn_sp > 0 else 0.0

        # Phugoid Approximation
        # omega_n_ph = sqrt(2) * g / V0
        g = 9.81
        wn_ph = sqrt(2) * g / velocity_tas
        zeta_ph = 0.04  # Typical low damping, hard to estimate without drag polar derivatives (C_D_u)

        # 2. Lateral-Directional Modes
        # ----------------------------

        # Dutch Roll Approximation
        # omega_n_dr = sqrt( (N_beta * Y_v - N_v * Y_beta) ... )
        # Simplified: omega_n_dr ~= sqrt(N_beta)
        # N_beta_dim = (q * S * b / Izz) * Cnb

        n_beta = (q_dyn * wing_area * wing_span / izz) * cnb

        if n_beta > 0:
            wn_dr = sqrt(n_beta)
        else:
            wn_dr = 0.0  # Directionally unstable

        # Damping: 2*zeta*wn ~= - (N_r + Y_v)
        # N_r_dim = (q * S * b^2 / (2 * V * Izz)) * Cnr
        # Y_v approx - (q * S / (m * V)) * Cy_beta (usually small) -> Let's ignore Y_v for damping approx or assume Cy_beta
        # Let's use 2*zeta*wn ~= -N_r_dim

        n_r = (q_dyn * wing_area * wing_span**2 / (2 * velocity_tas * izz)) * cnr
        zeta_dr = -n_r / (2 * wn_dr) if wn_dr > 0 else 0.0

        # Roll Mode (Subsidence)
        # tau_roll ~= -1 / L_p
        # L_p_dim = (q * S * b^2 / (2 * V * Ixx)) * Clp

        l_p = (q_dyn * wing_area * wing_span**2 / (2 * velocity_tas * ixx)) * clp
        if l_p != 0:
            tau_roll = -1.0 / l_p
        else:
            tau_roll = 999.9

        # Spiral Mode
        # Determine stability from L_beta * N_r - L_r * N_beta
        # Time constant is complex, often very large.
        # Placeholder
        tau_spiral = 100.0  # Typical value, positive if stable (convergent), negative if unstable (divergent)
        # Actually usually defined as T_double or T_half.
        # Let's approximate: T_s = ln(2) / lambda_s
        # lambda_s ~= (L_beta * N_r - L_r * N_beta) / (L_p * N_beta + ...)

        # 3. Determine Levels (Simplified)
        # --------------------------------

        # Short Period Level 1 (Transport): 0.3 < zeta < 2.0 ?
        sp_level = 1 if 0.3 <= zeta_sp <= 2.0 else (2 if 0.2 <= zeta_sp <= 3.0 else 3)

        # Phugoid Level 1: zeta > 0.04
        ph_level = 1 if zeta_ph >= 0.04 else 2

        # Dutch Roll Level 1: zeta > 0.08 (from template) & zeta*wn > 0.15
        dr_level = 1 if zeta_dr >= 0.08 and zeta_dr * wn_dr >= 0.15 else (2 if zeta_dr >= 0.02 else 3)

        return DynamicStabilityResults(
            short_period_natural_frequency=wn_sp,
            short_period_damping_ratio=zeta_sp,
            phugoid_natural_frequency=wn_ph,
            phugoid_damping_ratio=zeta_ph,
            dutch_roll_natural_frequency=wn_dr,
            dutch_roll_damping_ratio=zeta_dr,
            spiral_time_constant=tau_spiral,
            roll_time_constant=tau_roll,
            short_period_level=sp_level,
            phugoid_level=ph_level,
            dutch_roll_level=dr_level,
        )
