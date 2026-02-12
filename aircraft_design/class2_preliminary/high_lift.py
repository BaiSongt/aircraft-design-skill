from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HighLiftConfig:
    name: str
    delta_cl_max: float
    delta_cd0: float


DEFAULT_CANDIDATES: list[HighLiftConfig] = [
    HighLiftConfig(name="clean", delta_cl_max=0.0, delta_cd0=0.0),
    HighLiftConfig(name="plain_flap", delta_cl_max=0.4, delta_cd0=0.010),
    HighLiftConfig(name="split_flap", delta_cl_max=0.7, delta_cd0=0.018),
    HighLiftConfig(name="single_slotted", delta_cl_max=0.9, delta_cd0=0.022),
    HighLiftConfig(name="double_slotted", delta_cl_max=1.1, delta_cd0=0.028),
]


def select_high_lift_for_required_clmax(
    *,
    cl_max_clean: float,
    cl_max_required: float,
    candidates: list[HighLiftConfig] | None = None,
) -> dict:
    if cl_max_clean <= 0.0:
        raise ValueError("cl_max_clean must be positive.")
    if cl_max_required <= 0.0:
        raise ValueError("cl_max_required must be positive.")

    cands = candidates if candidates is not None else DEFAULT_CANDIDATES
    best = None
    for c in cands:
        cl_max = cl_max_clean + c.delta_cl_max
        if cl_max >= cl_max_required:
            if best is None or c.delta_cd0 < best.delta_cd0:
                best = c

    if best is None:
        max_c = max(cands, key=lambda x: x.delta_cl_max)
        return {
            "selected": max_c.name,
            "cl_max_achievable": cl_max_clean + max_c.delta_cl_max,
            "cl_max_required": cl_max_required,
            "delta_cd0": max_c.delta_cd0,
            "feasible": False,
        }

    return {
        "selected": best.name,
        "cl_max_achievable": cl_max_clean + best.delta_cl_max,
        "cl_max_required": cl_max_required,
        "delta_cd0": best.delta_cd0,
        "feasible": True,
    }


def max_high_lift_config(candidates: list[HighLiftConfig] | None = None) -> HighLiftConfig:
    cands = candidates if candidates is not None else DEFAULT_CANDIDATES
    return max(cands, key=lambda x: x.delta_cl_max)


def high_lift_config_by_name(name: str, candidates: list[HighLiftConfig] | None = None) -> HighLiftConfig | None:
    cands = candidates if candidates is not None else DEFAULT_CANDIDATES
    for c in cands:
        if c.name == name:
            return c
    return None


def select_high_lift_for_required_clmax_with_preference(
    *,
    cl_max_clean: float,
    cl_max_required: float,
    preferred: str | None = None,
    candidates: list[HighLiftConfig] | None = None,
) -> dict:
    cands = candidates if candidates is not None else DEFAULT_CANDIDATES
    if preferred:
        pref = high_lift_config_by_name(preferred, cands)
        if pref is not None:
            cl_max = cl_max_clean + pref.delta_cl_max
            if cl_max >= cl_max_required:
                return {
                    "selected": pref.name,
                    "cl_max_achievable": cl_max,
                    "cl_max_required": cl_max_required,
                    "delta_cd0": pref.delta_cd0,
                    "feasible": True,
                }
    return select_high_lift_for_required_clmax(
        cl_max_clean=cl_max_clean, cl_max_required=cl_max_required, candidates=cands
    )
