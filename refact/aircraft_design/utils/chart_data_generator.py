from __future__ import annotations

import math
import numpy as np
from typing import Dict, Any

from ..class2_preliminary.design_loop_orchestrator import SizedAircraft, DesignRequirements
from ..common.atmosphere import isa_tropopause
from ..common.units import CONST


class ChartDataGenerator:
    def __init__(self, aircraft: SizedAircraft, requirements: DesignRequirements):
        self.aircraft = aircraft
        self.requirements = requirements

    def generate_lift_curve(self) -> Dict[str, Any]:
        """Generates CL vs Alpha data."""
        # Simple linear model with stall
        # CL = CLa * (alpha - alpha0)
        # Stall at CL_max
        cla = self.aircraft.aero_params.get("cla_per_rad", 5.0)  # default approx
        # convert to per degree
        cla_deg = cla * math.pi / 180.0
        cl_max = self.aircraft.aero_params.get("cl_max_clean", 1.5)
        alpha0 = -2.0  # Zero lift angle (camber)

        # Stall angle
        # CL_max = cla_deg * (alpha_stall - alpha0)
        alpha_stall = (cl_max / cla_deg) + alpha0

        alphas = np.linspace(-5, alpha_stall + 5, 50)
        cls = []
        for a in alphas:
            if a <= alpha_stall:
                cls.append(cla_deg * (a - alpha0))
            else:
                # Post stall drop
                cls.append(cl_max * math.cos(math.radians(a - alpha_stall) * 2))  # Simple drop

        return {"alpha_deg": alphas.tolist(), "cl": cls, "cl_max": cl_max, "alpha_stall": alpha_stall}

    def generate_drag_polar(self) -> Dict[str, Any]:
        """Generates CD vs CL data."""
        # CD = CD0 + k * CL^2
        cd0 = self.aircraft.drag_params.get("cd0", 0.02)
        k = self.aircraft.drag_params.get("k", 0.05)

        cls = np.linspace(-1.0, 2.0, 50)
        cds = [cd0 + k * c**2 for c in cls]

        return {"cl": cls.tolist(), "cd": cds, "cd0": cd0, "k": k}

    def generate_thrust_curves(self, altitude_m: float = 0.0) -> Dict[str, Any]:
        """Generates Thrust Required vs Available data at altitude."""
        atm_state = isa_tropopause(altitude_m)
        rho = atm_state.rho_kg_m3
        s_ref = self.aircraft.geometry.get("s_ref_m2", 20.0)
        cd0 = self.aircraft.drag_params.get("cd0", 0.02)
        k = self.aircraft.drag_params.get("k", 0.05)
        weight_n = self.aircraft.mtow_kg * CONST.g0_m_s2

        # Velocity range: stall to Mach 0.9 or similar
        # V_stall estimate
        cl_max = self.aircraft.aero_params.get("cl_max_clean", 1.5)
        v_stall = math.sqrt(2 * weight_n / (rho * s_ref * cl_max))

        vs = np.linspace(v_stall, v_stall * 4, 50)
        tr = []
        ta = []

        # We need to extract prop params from aircraft inputs if available
        # Assuming simple model for now

        for v in vs:
            # Thrust Required: D = q * S * CD
            q = 0.5 * rho * v**2
            cl = weight_n / (q * s_ref)
            cd = cd0 + k * cl**2
            drag = q * s_ref * cd
            tr.append(drag)

            # Thrust Available
            # This is tricky without the full engine model object.
            # Using simple scaling: T = T0 * (rho/rho0)^n ...
            # Assume T/W given
            t0 = self.aircraft.mtow_kg * self.aircraft.design_point.get("thrust_to_weight", 0.5) * CONST.g0_m_s2
            # Simple approximation for high bypass or jet
            mach = v / atm_state.a_m_s
            # T_avail approx constant for jet, drops for prop
            # Let's assume constant for simplicity or use simplistic model
            thrust = t0 * (rho / 1.225) * (1 - 0.1 * mach)  # very rough
            ta.append(thrust)

        return {"velocity_ms": vs.tolist(), "thrust_req_n": tr, "thrust_avail_n": ta, "altitude_m": altitude_m}

    def generate_flight_envelope(self) -> Dict[str, Any]:
        """Generates H-V envelope data."""
        # 1. Stall Line: V_stall = sqrt(2 W / (rho S CLmax))
        # 2. Max Speed Line: Where T_avail = T_req

        alts = np.linspace(0, self.requirements.service_ceiling_m * 1.2, 50)
        v_stalls: list[float] = []
        v_maxs: list[float | None] = []

        weight_n = self.aircraft.mtow_kg * CONST.g0_m_s2
        s_ref = self.aircraft.geometry.get("s_ref_m2", 20.0)
        cl_max = self.aircraft.aero_params.get("cl_max_clean", 1.5)
        cd0 = self.aircraft.drag_params.get("cd0", 0.02)
        k = self.aircraft.drag_params.get("k", 0.05)
        t0 = self.aircraft.mtow_kg * self.aircraft.design_point.get("thrust_to_weight", 0.5) * CONST.g0_m_s2

        for h in alts:
            atm_state = isa_tropopause(h)
            rho = atm_state.rho_kg_m3

            # Stall
            vs = math.sqrt(2 * weight_n / (rho * s_ref * cl_max))
            v_stalls.append(vs)

            # Max Speed (Iterative or Analytic for parabolic polar + simple thrust)
            # T_avail = D = 0.5 rho V^2 S (CD0 + K (W/(0.5 rho V^2 S))^2)
            # T_avail = 0.5 rho V^2 S CD0 + (K W^2) / (0.5 rho V^2 S)
            # Let q = 0.5 rho V^2. T = q S CD0 + K W^2 / (q S)
            # q^2 S CD0 - q T + K W^2 / S = 0
            # Quadratic in q: A q^2 + B q + C = 0
            # A = S CD0
            # B = -T_avail
            # C = K W^2 / S

            # T_avail at altitude
            t_avail = t0 * (rho / 1.225) ** 0.7  # Approx lapse

            # Solve quadratic
            a_coeff = s_ref * cd0
            b_coeff = -t_avail
            c_coeff = k * weight_n**2 / s_ref

            delta = b_coeff**2 - 4 * a_coeff * c_coeff
            if delta < 0:
                # Cannot fly at this altitude
                v_maxs.append(None)
            else:
                q_sol = (-b_coeff + math.sqrt(delta)) / (2 * a_coeff)
                v_mx = math.sqrt(2 * q_sol / rho)
                v_maxs.append(v_mx)

        # Filter None
        valid_idxs = [i for i, v in enumerate(v_maxs) if v is not None]

        return {
            "v_stall_curve": {
                "velocity_ms": [v_stalls[i] for i in valid_idxs],
                "altitude_m": [alts[i] for i in valid_idxs],
            },
            "v_max_curve": {
                "velocity_ms": [v_maxs[i] for i in valid_idxs],
                "altitude_m": [alts[i] for i in valid_idxs],
            },
            "ceiling_m": self.requirements.service_ceiling_m,
        }

    def generate_vn_diagram(self) -> Dict[str, Any]:
        """Generates V-n diagram data."""
        # n_max = min(n_limit, (V/Vs)^2)
        n_pos_limit = self.requirements.max_load_factor
        n_neg_limit = -self.requirements.max_load_factor * 0.4  # Typical

        rho = 1.225  # SL
        s_ref = self.aircraft.geometry.get("s_ref_m2", 20.0)
        weight_n = self.aircraft.mtow_kg * CONST.g0_m_s2
        cl_max_pos = self.aircraft.aero_params.get("cl_max_clean", 1.5)
        cl_max_neg = -0.8  # approx

        # Stall speeds
        vs_pos = math.sqrt(2 * weight_n / (rho * s_ref * cl_max_pos))
        vs_neg = math.sqrt(2 * weight_n / (rho * s_ref * abs(cl_max_neg)))

        # Dive speed
        vd = self.requirements.cruise_mach * 340.0 * 1.25  # V_dive approx 1.25 V_cruise

        vs = np.linspace(0, vd, 100)
        n_pos = []
        n_neg = []

        for v in vs:
            # Positive
            if v < vs_pos:
                n = 0  # Static? No, usually 0 lift
                # Actually below stall, n is limited by CLmax
                # n = L/W = q S CLmax / W = (V/Vs)^2
                # But wait, Vs is at n=1.
                # n = (V/Vs_1g)^2
                # Avoid div by zero
                n = 0
            else:
                n = (v / vs_pos) ** 2

            n_pos.append(min(n, n_pos_limit))

            # Negative
            if v < vs_neg:
                n = 0
            else:
                n = -((v / vs_neg) ** 2)

            n_neg.append(max(n, n_neg_limit))

        return {"v_ms": vs.tolist(), "n_pos": n_pos, "n_neg": n_neg}
