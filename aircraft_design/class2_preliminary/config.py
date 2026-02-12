from __future__ import annotations

DEFAULT_RISK_THRESHOLDS: dict = {
    "constraint_margin_ratio": {"red": 0.0, "yellow": 0.05},
    "thrust_margin_ratio": {"red": 0.0, "yellow": 0.05},
    "ws_ratio": {"yellow": 0.95, "red": 1.0},
    "ld_cruise": {"red": 10.0, "yellow": 15.0},
    "fuel_fraction_total": {"yellow_low": 0.15, "yellow_high": 0.40, "red_high": 0.50},
    "static_margin": {"red_low": 0.05, "yellow_low": 0.10, "yellow_high": 0.25},
    "struct_empty_additional_ratio": {"yellow": 0.05, "red": 0.10},
    "robustness": {"yellow_fail_ratio": 0.0, "red_fail_ratio": 0.0},
}


DEFAULT_UNCERTAINTY_CASES: list[dict] = [
    {"name": "cd0+0.004", "deltas": {"aero.cd0": {"add": 0.004}}},
    {"name": "e-0.07", "deltas": {"aero.e": {"add": -0.07}}},
    {"name": "clmax-0.30", "deltas": {"aero.cl_max": {"add": -0.30}}},
    {"name": "isa+15C", "deltas": {"atmosphere.isa_delta_c": {"add": 15.0}}},
    {"name": "isa+30C", "deltas": {"atmosphere.isa_delta_c": {"add": 30.0}}},
    {"name": "thrust-10%", "deltas": {"propulsion.thrust_sl_n": {"mul": 0.9}}},
    {"name": "tsfc+10%", "deltas": {"propulsion.tsfc_1_s": {"mul": 1.1}, "propulsion.sfc_1_s": {"mul": 1.1}}},
    {"name": "prop_eta-10%", "deltas": {"propulsion.prop_efficiency": {"mul": 0.9}}},
    {"name": "tailwind-5mps", "deltas": {"mission.headwind_m_s": {"add": -5.0}}},
    {"name": "runway_slope+0.02", "deltas": {"mission.runway_slope": {"add": 0.02}}},
    {"name": "empty_add_limit-20%", "deltas": {"structures.max_empty_additional_fraction": {"mul": 0.8}}},
]
