from __future__ import annotations

from dataclasses import dataclass
from math import exp


@dataclass(frozen=True)
class EmptyWeightModel:
    a: float
    b: float

    def we_kg(self, w0_kg: float) -> float:
        return self.a * (w0_kg**self.b)


def fuel_fraction_breguet_jet(
    *,
    range_m: float,
    v_cruise_m_s: float,
    tsfc_1_s: float,
    lift_to_drag: float,
) -> float:
    if range_m <= 0.0:
        return 0.0
    if v_cruise_m_s <= 0.0 or tsfc_1_s <= 0.0 or lift_to_drag <= 0.0:
        raise ValueError("Invalid jet Breguet inputs.")
    wi_over_wf = exp(range_m * tsfc_1_s / (v_cruise_m_s * lift_to_drag))
    return 1.0 - 1.0 / wi_over_wf


def fuel_fraction_breguet_prop(
    *,
    range_m: float,
    sfc_1_s: float,
    prop_efficiency: float,
    lift_to_drag: float,
) -> float:
    if range_m <= 0.0:
        return 0.0
    if sfc_1_s <= 0.0 or prop_efficiency <= 0.0 or lift_to_drag <= 0.0:
        raise ValueError("Invalid prop Breguet inputs.")
    wi_over_wf = exp(range_m * sfc_1_s / (prop_efficiency * lift_to_drag))
    return 1.0 - 1.0 / wi_over_wf


def solve_mtow_class1_kg(
    *,
    payload_kg: float,
    crew_kg: float,
    empty_weight_model: EmptyWeightModel,
    empty_additional_kg: float = 0.0,
    fuel_fraction: float,
    reserve_fraction: float,
    w0_guess_kg: float,
    max_iter: int = 100,
    rtol: float = 1e-6,
) -> dict:
    if payload_kg < 0.0 or crew_kg < 0.0:
        raise ValueError("payload_kg and crew_kg must be non-negative.")
    if not (0.0 <= fuel_fraction < 1.0):
        raise ValueError("fuel_fraction must be in [0, 1).")
    if not (0.0 <= reserve_fraction < 1.0):
        raise ValueError("reserve_fraction must be in [0, 1).")
    if w0_guess_kg <= 0.0:
        raise ValueError("w0_guess_kg must be positive.")
    if empty_additional_kg < 0.0:
        raise ValueError("empty_additional_kg must be non-negative.")

    f_total = 1.0 - (1.0 - fuel_fraction) * (1.0 - reserve_fraction)
    if not (0.0 <= f_total < 1.0):
        raise ValueError("Total fuel fraction must be in [0, 1).")

    w0 = w0_guess_kg
    for i in range(max_iter):
        we = empty_weight_model.we_kg(w0)
        wf = f_total * w0
        w0_next = payload_kg + crew_kg + we + empty_additional_kg + wf
        if w0_next <= 0.0:
            raise ValueError("Non-physical MTOW iteration encountered.")
        rel = abs(w0_next - w0) / w0_next
        w0 = w0_next
        if rel < rtol:
            return {
                "w0_kg": w0,
                "we_kg": we + empty_additional_kg,
                "wf_kg": wf,
                "fuel_fraction_total": f_total,
                "iterations": i + 1,
                "converged": True,
            }

    return {
        "w0_kg": w0,
        "we_kg": empty_weight_model.we_kg(w0) + empty_additional_kg,
        "wf_kg": f_total * w0,
        "fuel_fraction_total": f_total,
        "iterations": max_iter,
        "converged": False,
    }
