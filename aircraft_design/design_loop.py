from __future__ import annotations

from dataclasses import dataclass

from .fixed_wing_overall import run_fixed_wing_overall_design


@dataclass(frozen=True)
class DesignLoopResult:
    best_inputs: dict
    best_results: dict
    candidates: list[dict]
    top_candidates: list[dict]
    sensitivity: list[dict]


def _objective_score(results: dict, objective: str) -> float:
    if objective == "min_w0_kg":
        return float(results.get("weights", {}).get("w0_kg", float("inf")))
    if objective == "min_wf_kg":
        return float(results.get("weights", {}).get("wf_kg", float("inf")))
    if objective == "max_ld":
        ld = float(results.get("aero", {}).get("ld_cruise", 0.0))
        return -ld
    if objective == "max_min_margin":
        margins = [float(c.get("margin", 0.0)) for c in results.get("constraints", {}).get("checks", [])]
        return -min(margins) if margins else float("inf")
    raise ValueError(f"Unknown objective: {objective}")


def _feasible_and_driver(results: dict) -> tuple[bool, str, float]:
    checks = results.get("constraints", {}).get("checks", [])
    worst = None
    for c in checks:
        m = float(c.get("margin", 0.0))
        if worst is None or m < worst[1]:
            worst = (str(c.get("name", "")), m)
    if worst is None:
        return False, "no_constraints", float("-inf")
    feasible = worst[1] >= 0.0
    return feasible, worst[0], worst[1]


def sensitivity_around_sizing(
    *,
    base_inputs: dict,
    sizing: dict,
    objective: str,
    steps: dict | None = None,
) -> list[dict]:
    step = steps or {"wing_loading_pa": 100.0, "aspect_ratio": 0.5, "thrust_to_weight": 0.02}
    out: list[dict] = []

    def eval_at(delta: dict) -> dict:
        inputs = {**base_inputs}
        inputs["_skip_uncertainty"] = True
        s = {**inputs.get("sizing", {}), **sizing}
        for k, dv in delta.items():
            s[k] = float(s.get(k, 0.0)) + float(dv)
        inputs["sizing"] = s
        res = run_fixed_wing_overall_design(inputs)
        feasible, driver, worst_margin = _feasible_and_driver(res)
        score = _objective_score(res, objective)
        return {"delta": delta, "score": score, "feasible": feasible, "driver": driver, "worst_margin": worst_margin}

    base = eval_at({})
    out.append({**base, "name": "base"})
    for k in ["wing_loading_pa", "aspect_ratio", "thrust_to_weight"]:
        if k in step:
            out.append({**eval_at({k: +float(step[k])}), "name": f"{k}+"})
            out.append({**eval_at({k: -float(step[k])}), "name": f"{k}-"})
    return out


def grid_search_design_point(
    *,
    base_inputs: dict,
    wing_loading_pa_grid: list[float],
    aspect_ratio_grid: list[float],
    thrust_to_weight_grid: list[float],
    objective: str = "min_w0_kg",
    require_constraints: bool = True,
    top_n: int = 10,
    sensitivity_steps: dict | None = None,
) -> DesignLoopResult:
    candidates: list[dict] = []
    best_inputs: dict | None = None
    best_results: dict | None = None
    best_score: float | None = None

    for ws in wing_loading_pa_grid:
        for ar in aspect_ratio_grid:
            for tw in thrust_to_weight_grid:
                inputs = {**base_inputs}
                inputs["_skip_uncertainty"] = True
                inputs["sizing"] = {
                    **inputs.get("sizing", {}),
                    "wing_loading_pa": ws,
                    "aspect_ratio": ar,
                    "thrust_to_weight": tw,
                }
                try:
                    res = run_fixed_wing_overall_design(inputs)
                except Exception as e:
                    candidates.append({"inputs": inputs["sizing"], "feasible": False, "error": str(e)})
                    continue

                feasible, driver, worst_margin = _feasible_and_driver(res)
                if require_constraints and not feasible:
                    pass

                score = _objective_score(res, objective)
                cand = {
                    "inputs": inputs["sizing"],
                    "feasible": feasible,
                    "objective": objective,
                    "score": score,
                    "driver": driver,
                    "worst_margin": worst_margin,
                    "w0_kg": res.get("weights", {}).get("w0_kg", None),
                    "ld_cruise": res.get("aero", {}).get("ld_cruise", None),
                    "climb_rate_m_s": res.get("performance", {}).get("climb_rate_m_s", None),
                }
                candidates.append(cand)

                if not feasible:
                    continue

                if best_score is None or score < best_score:
                    best_score = score
                    best_inputs = inputs
                    best_results = res

    if best_inputs is None or best_results is None:
        # Fallback to best infeasible (least violated)
        infeasible = [c for c in candidates if not c.get("feasible") and c.get("worst_margin") is not None]
        if not infeasible:
            raise ValueError("No valid candidates found (all errors or empty grid).")
        best_cand = max(infeasible, key=lambda x: float(x.get("worst_margin", float("-inf"))))
        inputs = {**base_inputs}
        inputs["sizing"] = best_cand["inputs"]
        # Re-run to get full results
        res = run_fixed_wing_overall_design(inputs)
        best_inputs = inputs
        best_results = res
        best_score = float("inf")

    feasible_sorted = sorted(
        [c for c in candidates if c.get("feasible")], key=lambda x: float(x.get("score", float("inf")))
    )
    if not feasible_sorted:
        # Sort infeasible by margin
        feasible_sorted = sorted([c for c in candidates], key=lambda x: -float(x.get("worst_margin", float("-inf"))))

    top_candidates = feasible_sorted[: max(0, int(top_n))]
    if best_inputs is None or best_results is None:
        raise ValueError("No valid candidates found (best result missing).")
    sensitivity = sensitivity_around_sizing(
        base_inputs=base_inputs,
        sizing=best_inputs.get("sizing", {}),
        objective=objective,
        steps=sensitivity_steps,
    )

    return DesignLoopResult(
        best_inputs=best_inputs,
        best_results=best_results,
        candidates=candidates,
        top_candidates=top_candidates,
        sensitivity=sensitivity,
    )
