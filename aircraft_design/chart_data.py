from typing import Dict, List, Any, Optional
import math
from .design_loop_orchestrator import SizedAircraft
from .atmosphere import isa_tropopause


class ChartDataGenerator:
    """
    Generates data structures for interactive charts.
    """

    def get_lift_curve_data(self, ac: SizedAircraft, alpha_range_deg: Optional[List[float]] = None) -> Dict[str, Any]:
        if alpha_range_deg is None:
            alpha_range_deg = list(range(-5, 20, 1))

        ar = ac.geometry.get("aspect_ratio", 8.0)
        cla = 2 * math.pi * ar / (ar + 2.0)  # 1/rad
        alpha0 = -2.0  # deg, assumed
        cl_max = 1.5  # assumed

        data = []
        for alpha in alpha_range_deg:
            # Linear range
            cl = cla * math.radians(alpha - alpha0)

            # Stall behavior (simplified)
            if cl > cl_max:
                cl = cl_max - 0.1 * (math.radians(alpha) - math.radians(15))  # Drop off

            data.append({"alpha": alpha, "CL": max(-0.5, cl)})

        return {"title": "Lift Curve (CL vs Alpha)", "x_axis": "Alpha (deg)", "y_axis": "CL", "data": data}

    def get_drag_polar_data(self, ac: SizedAircraft, cl_range: Optional[List[float]] = None) -> Dict[str, Any]:
        if cl_range is None:
            cl_range = [x * 0.1 for x in range(-5, 20)]

        cd0 = ac.geometry.get("cd0", 0.02)
        e = ac.geometry.get("oswald_e", 0.8)
        ar = ac.geometry.get("aspect_ratio", 8.0)
        k = 1.0 / (math.pi * e * ar)

        data = []
        for cl in cl_range:
            cd = cd0 + k * cl**2
            ld = cl / cd if cd > 0 else 0
            data.append({"CL": cl, "CD": cd, "L_D": ld})

        return {"title": "Drag Polar", "x_axis": "CD", "y_axis": "CL", "data": data}

    def get_climb_performance_data(self, ac: SizedAircraft) -> Dict[str, Any]:
        altitudes = range(0, 16000, 1000)  # m
        data = []

        # Need thrust model and drag model
        # Simplified: Thrust drops with sigma^0.7 (Turbofan) or sigma (Prop)
        # Drag increases as rho drops for constant CAS, or use cruise speed schedule

        thrust_sl = ac.thrust_sl_n
        w_kg = ac.mtow_kg  # MTOW climb
        s_ref = ac.wing_area_m2
        cd0 = ac.geometry.get("cd0", 0.02)
        e = ac.geometry.get("oswald_e", 0.8)
        ar = ac.geometry.get("aspect_ratio", 8.0)
        k = 1.0 / (math.pi * e * ar)

        for alt in altitudes:
            atm = isa_tropopause(alt)
            sigma = atm.sigma

            # Thrust available
            # Turbofan approx
            thrust_avail = thrust_sl * (sigma**0.7)

            # Best climb speed (approx)
            # V_y approx where L/D max? No, slightly faster.
            # L/D max speed:
            v_ldmax = math.sqrt((2 * w_kg * 9.81) / (atm.rho_kg_m3 * s_ref) * math.sqrt(k / cd0)) if cd0 > 0 else 100

            # Rate of climb = (T - D) * V / W
            # At V_ldmax, D is minimum? No D = W / (L/D)max
            ld_max = 0.5 * math.sqrt(math.pi * ar * e / cd0)
            d_min = (w_kg * 9.81) / ld_max

            roc = (thrust_avail - d_min) * v_ldmax / (w_kg * 9.81)

            data.append({"altitude_m": alt, "roc_m_s": max(0, roc)})

        return {
            "title": "Rate of Climb vs Altitude",
            "x_axis": "Altitude (m)",
            "y_axis": "Rate of Climb (m/s)",
            "data": data,
        }

    def get_weight_pie_data(self, ac: SizedAircraft) -> Dict[str, Any]:
        wb = ac.weight_breakdown
        # Group small items?
        data = []
        for k, v in wb.items():
            if isinstance(v, (int, float)):
                data.append({"name": k, "value": v})
            elif isinstance(v, dict):
                # Maybe sum subgroups or just top level
                total_sub = sum(val for val in v.values() if isinstance(val, (int, float)))
                data.append({"name": k, "value": total_sub})

        # Add fuel and payload if not in breakdown (usually they are separate in SizedAircraft properties)
        data.append({"name": "Fuel", "value": ac.fuel_weight_kg})
        # Payload?
        # Usually payload is not part of OEW breakdown but part of MTOW.
        # Check if we want MTOW breakdown.
        payload = ac.mtow_kg - ac.empty_weight_kg - ac.fuel_weight_kg
        data.append({"name": "Payload", "value": payload})

        return {"title": "Weight Breakdown", "type": "pie", "data": data}
