from __future__ import annotations

import json

try:
    from typing import TypeGuard
except ImportError:
    from typing import Any

    # Fallback for Python < 3.10
    TypeGuard = Any  # type: ignore

from .config import DEFAULT_RISK_THRESHOLDS, DEFAULT_UNCERTAINTY_CASES


def _is_number(x) -> TypeGuard[int | float]:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _deepcopy(obj):
    if isinstance(obj, dict):
        return {k: _deepcopy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deepcopy(v) for v in obj]
    return obj


def _merge_dicts(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_dicts(out[k], v)
        else:
            out[k] = v
    return out


def _require_dict(d: dict, key: str) -> dict:
    if key not in d:
        raise ValueError(f"Missing required input key: {key}")
    v = d[key]
    if not isinstance(v, dict):
        raise ValueError(f"Input key '{key}' must be an object.")
    return v


def _normalize_risk_thresholds(report: dict, *, warnings: list[str]) -> dict:
    rt_in = report.get("risk_thresholds", None)
    if rt_in is None:
        return dict(DEFAULT_RISK_THRESHOLDS)
    if not isinstance(rt_in, dict):
        raise ValueError("report.risk_thresholds must be an object.")
    rt = _merge_dicts(DEFAULT_RISK_THRESHOLDS, rt_in)
    for group, spec in rt.items():
        if isinstance(spec, dict):
            for kk, vv in spec.items():
                if not _is_number(vv):
                    raise ValueError(f"report.risk_thresholds.{group}.{kk} must be a number.")
        else:
            warnings.append(f"report.risk_thresholds.{group} is not an object; kept as-is.")
    return rt


def _normalize_uncertainty(inputs: dict, *, warnings: list[str]) -> dict:
    unc = inputs.get("uncertainty", None)
    if unc is None:
        return {"enabled": False}
    if not isinstance(unc, dict):
        raise ValueError("uncertainty must be an object.")
    enabled = bool(unc.get("enabled", False))
    cases_in = unc.get("cases", None)
    if cases_in is None:
        cases = _deepcopy(DEFAULT_UNCERTAINTY_CASES)
    else:
        if not isinstance(cases_in, list):
            raise ValueError("uncertainty.cases must be an array.")
        cases = cases_in
    norm_cases = []
    for i, c in enumerate(cases):
        if not isinstance(c, dict):
            raise ValueError(f"uncertainty.cases[{i}] must be an object.")
        name = c.get("name", None)
        if not isinstance(name, str) or not name:
            raise ValueError(f"uncertainty.cases[{i}].name must be a non-empty string.")
        deltas = c.get("deltas", None)
        if not isinstance(deltas, dict) or not deltas:
            raise ValueError(f"uncertainty.cases[{i}].deltas must be a non-empty object.")
        norm_deltas = {}
        for path, spec in deltas.items():
            if not isinstance(path, str) or not path:
                raise ValueError(f"uncertainty.cases[{i}].deltas keys must be non-empty strings.")
            if isinstance(spec, dict):
                if "mul" in spec:
                    if not _is_number(spec["mul"]):
                        raise ValueError(f"uncertainty.cases[{i}].deltas['{path}'].mul must be a number.")
                    norm_deltas[path] = {"mul": float(spec["mul"])}
                elif "add" in spec:
                    if not _is_number(spec["add"]):
                        raise ValueError(f"uncertainty.cases[{i}].deltas['{path}'].add must be a number.")
                    norm_deltas[path] = {"add": float(spec["add"])}
                else:
                    raise ValueError(f"uncertainty.cases[{i}].deltas['{path}'] must contain 'add' or 'mul'.")
            else:
                if not _is_number(spec):
                    raise ValueError(f"uncertainty.cases[{i}].deltas['{path}'] must be a number or an object.")
                norm_deltas[path] = {"add": float(spec)}
        norm_cases.append({"name": name, "deltas": norm_deltas})
    out = dict(unc)
    out["enabled"] = enabled
    out["cases"] = norm_cases
    if enabled and not norm_cases:
        warnings.append("uncertainty.enabled=true but no cases defined.")
    return out


def _normalize_design_loop(inputs: dict, *, warnings: list[str]) -> dict | None:
    dl = inputs.get("design_loop", None)
    if dl is None:
        return None
    if not isinstance(dl, dict):
        raise ValueError("design_loop must be an object.")
    out = dict(dl)
    grid = dl.get("grid_ws_tw", None)
    if isinstance(grid, dict):

        def _pick(keys: list[str]) -> list | None:
            for k in keys:
                v = grid.get(k, None)
                if isinstance(v, list):
                    return v
            return None

        mappings = [
            ("wing_loading_pa_grid", ["wing_loading_pa_grid", "wing_loading_pa", "ws_grid", "ws"]),
            ("aspect_ratio_grid", ["aspect_ratio_grid", "aspect_ratio", "ar_grid", "ar"]),
            ("thrust_to_weight_grid", ["thrust_to_weight_grid", "thrust_to_weight", "tw_grid", "tw"]),
        ]
        for target, keys in mappings:
            if target not in out:
                v = _pick(keys)
                if isinstance(v, list):
                    out[target] = v
    elif isinstance(grid, list):
        ws_vals: list[float] = []
        ar_vals: list[float] = []
        tw_vals: list[float] = []
        for item in grid:
            if not isinstance(item, dict):
                continue
            ws = item.get("wing_loading_pa", item.get("ws", None))
            ar = item.get("aspect_ratio", item.get("ar", None))
            tw = item.get("thrust_to_weight", item.get("tw", None))
            if _is_number(ws):
                ws_vals.append(float(ws))
            if _is_number(ar):
                ar_vals.append(float(ar))
            if _is_number(tw):
                tw_vals.append(float(tw))
        if "wing_loading_pa_grid" not in out and ws_vals:
            out["wing_loading_pa_grid"] = list(dict.fromkeys(ws_vals))
        if "aspect_ratio_grid" not in out and ar_vals:
            out["aspect_ratio_grid"] = list(dict.fromkeys(ar_vals))
        if "thrust_to_weight_grid" not in out and tw_vals:
            out["thrust_to_weight_grid"] = list(dict.fromkeys(tw_vals))
        if grid and not (ws_vals and ar_vals and tw_vals):
            warnings.append("design_loop.grid_ws_tw missing ws/ar/tw entries")
    return out


def _normalize_geometry_bundle(inputs: dict, *, warnings: list[str]) -> None:
    geometry = inputs.get("geometry", None)
    if not isinstance(geometry, dict):
        return
    mappings = {
        "shape": "geometry_shape",
        "derived": "geometry_shape_derived",
        "reference": "geometry_reference",
        "parametric": "geometry_parametric",
        "detailed": "geometry_detailed",
        "search": "geometry_search",
    }
    for src, dst in mappings.items():
        v = geometry.get(src, None)
        if not isinstance(v, dict):
            continue
        if dst not in inputs:
            inputs[dst] = v
        elif isinstance(inputs.get(dst), dict) and inputs.get(dst) is not v:
            warnings.append(f"geometry.{src} ignored because {dst} already provided.")


def _normalize_geometry_parametric(inputs: dict) -> None:
    def _num(value: object, default: float) -> float:
        return float(value) if _is_number(value) else float(default)

    if isinstance(inputs.get("geometry_parametric", None), dict):
        return
    g = inputs.get("geometry", None)
    s = inputs.get("sizing", None)
    if not isinstance(g, dict) or not isinstance(s, dict):
        return
    ar = s.get("aspect_ratio", None)
    if not _is_number(ar):
        return
    inputs["geometry_parametric"] = {
        "wing": {
            "aspect_ratio": float(ar),
            "taper_ratio": _num(s.get("taper_ratio", 0.45), 0.45),
            "sweep_quarter_chord_deg": _num(s.get("sweep_quarter_chord_deg", 0.0), 0.0),
            "t_c": _num(g.get("wing_t_c", 0.12), 0.12),
        },
        "fuselage": {
            "length_m": _num(g.get("fuselage_length_m", 7.5), 7.5),
            "diameter_m": _num(g.get("fuselage_diameter_m", 1.2), 1.2),
        },
        "tail": {"area_ratio_to_wing": _num(g.get("tail_area_ratio", 0.22), 0.22)},
    }


def validate_run_inputs(inputs: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(inputs, dict):
        return {"errors": ["inputs must be an object."], "warnings": warnings}

    def _req_dict(name: str) -> dict | None:
        v = inputs.get(name, None)
        if not isinstance(v, dict):
            errors.append(f"{name} must be an object.")
            return None
        return v

    def _req_num(obj: dict | None, key: str, label: str, *, min_value: float | None, allow_zero: bool) -> None:
        if not isinstance(obj, dict):
            return
        v = obj.get(key, None)
        if not _is_number(v):
            errors.append(f"{label} must be a number.")
            return
        v_f = float(v)
        if min_value is None:
            return
        if allow_zero:
            if v_f < min_value:
                errors.append(f"{label} must be >= {min_value}.")
        else:
            if v_f <= min_value:
                errors.append(f"{label} must be > {min_value}.")

    mission = _req_dict("mission")
    payload = _req_dict("payload")
    crew = _req_dict("crew")
    aero = _req_dict("aero")
    sizing = _req_dict("sizing")
    weights = _req_dict("weights")
    propulsion = _req_dict("propulsion")

    _req_num(mission, "range_m", "mission.range_m", min_value=0.0, allow_zero=False)
    _req_num(mission, "cruise_altitude_m", "mission.cruise_altitude_m", min_value=0.0, allow_zero=True)
    _req_num(mission, "cruise_speed_m_s", "mission.cruise_speed_m_s", min_value=0.0, allow_zero=False)
    _req_num(mission, "v_stall_m_s", "mission.v_stall_m_s", min_value=0.0, allow_zero=False)

    _req_num(payload, "payload_kg", "payload.payload_kg", min_value=0.0, allow_zero=True)
    _req_num(crew, "crew_kg", "crew.crew_kg", min_value=0.0, allow_zero=True)

    _req_num(aero, "e", "aero.e", min_value=0.0, allow_zero=False)
    _req_num(aero, "cl_max", "aero.cl_max", min_value=0.0, allow_zero=False)
    if isinstance(aero, dict) and "cd0" in aero and not _is_number(aero.get("cd0", None)):
        errors.append("aero.cd0 must be a number.")
    if isinstance(aero, dict) and "cd0" not in aero:
        if not isinstance(inputs.get("geometry", None), dict) and not isinstance(
            inputs.get("geometry_parametric", None), dict
        ):
            errors.append("aero.cd0 missing and no geometry provided for drag buildup.")

    _req_num(sizing, "wing_loading_pa", "sizing.wing_loading_pa", min_value=0.0, allow_zero=False)
    _req_num(sizing, "aspect_ratio", "sizing.aspect_ratio", min_value=0.0, allow_zero=False)
    _req_num(sizing, "thrust_to_weight", "sizing.thrust_to_weight", min_value=0.0, allow_zero=False)

    _req_num(weights, "empty_a", "weights.empty_a", min_value=0.0, allow_zero=False)
    _req_num(weights, "empty_b", "weights.empty_b", min_value=0.0, allow_zero=False)
    if isinstance(weights, dict) and "reserve_fraction" in weights:
        v = weights.get("reserve_fraction", None)
        if _is_number(v):
            if float(v) < 0.0 or float(v) >= 1.0:
                errors.append("weights.reserve_fraction must be in [0, 1).")
        else:
            errors.append("weights.reserve_fraction must be a number.")
    if isinstance(weights, dict) and "w0_guess_kg" in weights and not _is_number(weights.get("w0_guess_kg", None)):
        errors.append("weights.w0_guess_kg must be a number.")

    if isinstance(propulsion, dict):
        ptype = propulsion.get("type", None)
        if not isinstance(ptype, str) or not ptype.strip():
            errors.append("propulsion.type must be a non-empty string.")
        if "sfc_1_s" in propulsion and not _is_number(propulsion.get("sfc_1_s", None)):
            errors.append("propulsion.sfc_1_s must be a number.")
        if "prop_efficiency" in propulsion and not _is_number(propulsion.get("prop_efficiency", None)):
            errors.append("propulsion.prop_efficiency must be a number.")
    else:
        errors.append("propulsion must be an object.")

    return {"errors": errors, "warnings": warnings}


def normalize_inputs(raw_inputs: dict) -> tuple[dict, list[str]]:
    if not isinstance(raw_inputs, dict):
        raise ValueError("Inputs must be a JSON object.")
    inputs = _deepcopy(raw_inputs)
    warnings: list[str] = []

    for k in ["mission", "payload", "crew", "aero", "sizing", "weights", "propulsion"]:
        _require_dict(inputs, k)

    atmosphere = inputs.get("atmosphere", {})
    if atmosphere is None:
        atmosphere = {}
    if not isinstance(atmosphere, dict):
        raise ValueError("atmosphere must be an object.")
    if "isa_delta_c" in atmosphere and not _is_number(atmosphere["isa_delta_c"]):
        raise ValueError("atmosphere.isa_delta_c must be a number.")
    atmosphere.setdefault("isa_delta_c", 0.0)
    inputs["atmosphere"] = atmosphere

    report = inputs.get("report", {})
    if report is None:
        report = {}
    if not isinstance(report, dict):
        raise ValueError("report must be an object.")
    report["risk_thresholds"] = _normalize_risk_thresholds(report, warnings=warnings)
    inputs["report"] = report

    inputs["uncertainty"] = _normalize_uncertainty(inputs, warnings=warnings)
    design_loop = _normalize_design_loop(inputs, warnings=warnings)
    if design_loop is not None:
        inputs["design_loop"] = design_loop
    _normalize_geometry_bundle(inputs, warnings=warnings)
    _normalize_geometry_parametric(inputs)

    unknown_top = [
        k
        for k in inputs.keys()
        if k
        not in {
            "mission",
            "payload",
            "crew",
            "aero",
            "sizing",
            "weights",
            "propulsion",
            "geometry",
            "geometry_parametric",
            "geometry_detailed",
            "geometry_shape",
            "geometry_shape_derived",
            "geometry_reference",
            "geometry_search",
            "geometry_constraints",
            "openvsp",
            "tail",
            "stability",
            "structures",
            "design_loop",
            "aircraft_role",
            "atmosphere",
            "report",
            "uncertainty",
            "_skip_uncertainty",
        }
        and not str(k).startswith("_")
    ]
    if unknown_top:
        warnings.append("Unknown top-level keys: " + ", ".join(sorted(unknown_top)))

    inputs["_normalized"] = True
    inputs["_validation_warnings"] = warnings
    inputs["_validation_snapshot"] = json.loads(
        json.dumps(
            {
                "atmosphere": inputs.get("atmosphere"),
                "report": inputs.get("report"),
                "uncertainty": inputs.get("uncertainty"),
            },
            ensure_ascii=False,
        )
    )
    return inputs, warnings
