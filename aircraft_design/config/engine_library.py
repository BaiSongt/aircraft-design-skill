from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EngineType:
    name: str
    category: str
    mtow_range_min: float
    mtow_range_max: float
    cruise_speed_range_min: float
    cruise_speed_range_max: float


@dataclass(frozen=True)
class EngineModel:
    name: str
    engine_type: str
    max_thrust_kn: float | None
    max_power_kw: float | None
    sfc_kg_kn_hr: float | None
    tsfc_kg_kn_hr: float | None
    weight_kg: float
    diameter_m: float
    length_m: float
    bypass_ratio: float | None = None
    pressure_ratio: float | None = None
    dry: bool = True
    notes: str = ""


ENGINE_TYPES = [
    EngineType(
        name="piston",
        category="reciprocating",
        mtow_range_min=0,
        mtow_range_max=2000,
        cruise_speed_range_min=0,
        cruise_speed_range_max=100,
    ),
    EngineType(
        name="turboprop",
        category="gas_turbine",
        mtow_range_min=2000,
        mtow_range_max=8000,
        cruise_speed_range_min=100,
        cruise_speed_range_max=250,
    ),
    EngineType(
        name="turbofan",
        category="gas_turbine",
        mtow_range_min=8000,
        mtow_range_max=500000,
        cruise_speed_range_min=200,
        cruise_speed_range_max=350,
    ),
    EngineType(
        name="turbojet",
        category="gas_turbine",
        mtow_range_min=5000,
        mtow_range_max=200000,
        cruise_speed_range_min=250,
        cruise_speed_range_max=600,
    ),
]


PISTON_ENGINES = [
    EngineModel(
        name="Lycoming O-320",
        engine_type="piston",
        max_thrust_kn=None,
        max_power_kw=118,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=None,
        weight_kg=115,
        diameter_m=0.76,
        length_m=0.94,
        notes="Common in light GA aircraft",
    ),
    EngineModel(
        name="Lycoming O-540",
        engine_type="piston",
        max_thrust_kn=None,
        max_power_kw=195,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=None,
        weight_kg=195,
        diameter_m=0.88,
        length_m=1.17,
        notes="Higher power variant",
    ),
    EngineModel(
        name="Continental IO-550",
        engine_type="piston",
        max_thrust_kn=None,
        max_power_kw=224,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=None,
        weight_kg=230,
        diameter_m=0.90,
        length_m=1.02,
        notes="High-performance piston engine",
    ),
]


TURBOPROP_ENGINES = [
    EngineModel(
        name="Pratt & Whitney PT6A-60",
        engine_type="turboprop",
        max_thrust_kn=None,
        max_power_kw=950,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=0.65,
        weight_kg=340,
        diameter_m=0.50,
        length_m=1.98,
        bypass_ratio=None,
        pressure_ratio=8.5,
        notes="Popular turboprop for GA aircraft",
    ),
    EngineModel(
        name="GE CT7-8",
        engine_type="turboprop",
        max_thrust_kn=None,
        max_power_kw=1864,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=0.58,
        weight_kg=544,
        diameter_m=0.70,
        length_m=2.39,
        bypass_ratio=None,
        pressure_ratio=16.0,
        notes="High-power turboprop for larger aircraft",
    ),
    EngineModel(
        name="Rolls-Royce AE2100",
        engine_type="turboprop",
        max_thrust_kn=None,
        max_power_kw=3100,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=0.55,
        weight_kg=735,
        diameter_m=0.76,
        length_m=2.77,
        bypass_ratio=None,
        pressure_ratio=14.0,
        notes="Large turboprop for regional aircraft",
    ),
]


TURBOFAN_ENGINES = [
    EngineModel(
        name="CFM56-7B",
        engine_type="turbofan",
        max_thrust_kn=120,
        max_power_kw=None,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=0.55,
        weight_kg=2367,
        diameter_m=1.73,
        length_m=2.41,
        bypass_ratio=5.5,
        pressure_ratio=32.0,
        notes="Popular narrowbody engine",
    ),
    EngineModel(
        name="GE CF34-10",
        engine_type="turbofan",
        max_thrust_kn=69,
        max_power_kw=None,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=0.58,
        weight_kg=1452,
        diameter_m=1.32,
        length_m=2.44,
        bypass_ratio=5.0,
        pressure_ratio=30.0,
        notes="Regional jet engine",
    ),
    EngineModel(
        name="Pratt & Whitney PW1500G",
        engine_type="turbofan",
        max_thrust_kn=103,
        max_power_kw=None,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=0.50,
        weight_kg=2495,
        diameter_m=1.68,
        length_m=2.95,
        bypass_ratio=12.0,
        pressure_ratio=50.0,
        notes="GTF engine with high bypass ratio",
    ),
    EngineModel(
        name="GE GE90-115B",
        engine_type="turbofan",
        max_thrust_kn=512,
        max_power_kw=None,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=0.52,
        weight_kg=8284,
        diameter_m=3.40,
        length_m=5.57,
        bypass_ratio=9.0,
        pressure_ratio=42.0,
        notes="Large high-thrust engine",
    ),
]


TURBOJET_ENGINES = [
    EngineModel(
        name="GE J85-GE-21",
        engine_type="turbojet",
        max_thrust_kn=17,
        max_power_kw=None,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=1.2,
        weight_kg=334,
        diameter_m=0.50,
        length_m=2.64,
        bypass_ratio=0.0,
        pressure_ratio=6.0,
        notes="Small turbojet for military aircraft",
    ),
    EngineModel(
        name="Pratt & Whitney J58",
        engine_type="turbojet",
        max_thrust_kn=150,
        max_power_kw=None,
        sfc_kg_kn_hr=None,
        tsfc_kg_kn_hr=1.5,
        weight_kg=2608,
        diameter_m=1.45,
        length_m=5.23,
        bypass_ratio=0.0,
        pressure_ratio=8.5,
        notes="High-thrust turbojet",
    ),
]


ALL_ENGINES = {
    "piston": PISTON_ENGINES,
    "turboprop": TURBOPROP_ENGINES,
    "turbofan": TURBOFAN_ENGINES,
    "turbojet": TURBOJET_ENGINES,
}


def get_engine_type_by_mtow(mtow_kg: float) -> str:
    best_type = "piston"
    best_overlap = 0

    for engine_type in ENGINE_TYPES:
        if engine_type.mtow_range_min <= mtow_kg <= engine_type.mtow_range_max:
            overlap = engine_type.mtow_range_max - engine_type.mtow_range_min
            if overlap > best_overlap:
                best_overlap = overlap
                best_type = engine_type.name
        elif mtow_kg < engine_type.mtow_range_max:
            if engine_type.mtow_range_max > best_overlap:
                best_overlap = engine_type.mtow_range_max
                best_type = engine_type.name

    return best_type


def recommend_engines(
    mtow_kg: float,
    cruise_speed_ktas: float,
    num_engines: int = 1,
) -> dict[str, Any]:
    engine_type = get_engine_type_by_mtow(mtow_kg)

    engines = ALL_ENGINES.get(engine_type, [])

    if not engines:
        return {
            "recommended_type": engine_type,
            "candidates": [],
            "message": f"No engines found for type: {engine_type}",
        }

    candidates = []
    required_power_per_engine = mtow_kg * 9.81 / num_engines / 3.0

    for engine in engines:
        power_kw = engine.max_power_kw if engine.max_power_kw else engine.max_thrust_kn * 150
        thrust_kn = engine.max_thrust_kn if engine.max_thrust_kn else engine.max_power_kw / 150

        score = 0.0
        if power_kw >= required_power_per_engine:
            score += 0.5
        else:
            score -= 0.5

        if engine.tsfc_kg_kn_hr:
            if engine.tsfc_kg_kn_hr < 0.6:
                score += 0.3
            elif engine.tsfc_kg_kn_hr < 0.8:
                score += 0.1

        weight_ratio = engine.weight_kg / mtow_kg
        if weight_ratio < 0.05:
            score += 0.2
        elif weight_ratio < 0.08:
            score += 0.1

        candidates.append({
            "engine": engine,
            "score": score,
            "power_kw": power_kw,
            "thrust_kn": thrust_kn,
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    return {
        "recommended_type": engine_type,
        "candidates": [
            {
                "name": c["engine"].name,
                "type": c["engine"].engine_type,
                "max_power_kw": c["engine"].max_power_kw,
                "max_thrust_kn": c["engine"].max_thrust_kn,
                "weight_kg": c["engine"].weight_kg,
                "tsfc_kg_kn_hr": c["engine"].tsfc_kg_kn_hr,
                "diameter_m": c["engine"].diameter_m,
                "length_m": c["engine"].length_m,
                "score": c["score"],
                "notes": c["engine"].notes,
            }
            for c in candidates[:5]
        ],
        "required_power_per_engine_kw": required_power_per_engine,
    }


def get_engine_by_name(engine_name: str) -> EngineModel | None:
    for engines in ALL_ENGINES.values():
        for engine in engines:
            if engine.name == engine_name:
                return engine
    return None


def parse_engine_config(engine_dict: dict, path: str) -> dict[str, Any]:
    if not isinstance(engine_dict, dict):
        raise ValueError(f"{path}.engine must be an object.")

    result: dict[str, Any] = {}

    engine_type = engine_dict.get("type", "piston").strip().lower()
    if engine_type not in {"piston", "turboprop", "turbofan", "turbojet"}:
        raise ValueError(f"Unknown engine type: {engine_type}")
    result["type"] = engine_type

    num_engines = engine_dict.get("num_engines", 1)
    if not isinstance(num_engines, int) or num_engines < 1:
        raise ValueError(f"{path}.num_engines must be a positive integer.")
    result["num_engines"] = num_engines

    engine_name = engine_dict.get("model_name")
    if engine_name:
        result["model_name"] = str(engine_name)
        engine = get_engine_by_name(engine_name)
        if engine:
            result["max_thrust_kn"] = engine.max_thrust_kn
            result["max_power_kw"] = engine.max_power_kw
            result["tsfc_kg_kn_hr"] = engine.tsfc_kg_kn_hr
            result["weight_kg"] = engine.weight_kg
            result["diameter_m"] = engine.diameter_m
            result["length_m"] = engine.length_m
    else:
        if "max_thrust_kn" in engine_dict:
            val = engine_dict.get("max_thrust_kn")
            if val is not None:
                result["max_thrust_kn"] = None
            elif not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(f"{path}.max_thrust_kn must be positive.")
            else:
                result["max_thrust_kn"] = float(val)

        if "max_power_kw" in engine_dict:
            val = engine_dict.get("max_power_kw")
            if val is not None:
                result["max_power_kw"] = None
            elif not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(f"{path}.max_power_kw must be positive.")
            else:
                result["max_power_kw"] = float(val)

        if "tsfc_kg_kn_hr" in engine_dict:
            val = engine_dict.get("tsfc_kg_kn_hr")
            if val is not None:
                result["tsfc_kg_kn_hr"] = None
            elif not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(f"{path}.tsfc_kg_kn_hr must be positive.")
            else:
                result["tsfc_kg_kn_hr"] = float(val)

        if "weight_kg" in engine_dict:
            val = engine_dict.get("weight_kg")
            if val is not None:
                result["weight_kg"] = None
            elif not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(f"{path}.weight_kg must be positive.")
            else:
                result["weight_kg"] = float(val)

        if "diameter_m" in engine_dict:
            val = engine_dict.get("diameter_m")
            if val is not None:
                result["diameter_m"] = None
            elif not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(f"{path}.diameter_m must be positive.")
            else:
                result["diameter_m"] = float(val)

        if "length_m" in engine_dict:
            val = engine_dict.get("length_m")
            if val is not None:
                result["length_m"] = None
            elif not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(f"{path}.length_m must be positive.")
            else:
                result["length_m"] = float(val)

    mount_location = engine_dict.get("mount_location", "wing")
    if mount_location not in {"wing", "fuselage", "tail"}:
        raise ValueError(f"Unknown mount location: {mount_location}")
    result["mount_location"] = mount_location

    return result


def validate_engine_config(
    engine: dict[str, Any],
    mtow_kg: float,
) -> list[dict[str, Any]]:
    violations = []

    engine_type = engine.get("type", "unknown")
    num_engines = engine.get("num_engines", 1)
    max_thrust_kn = engine.get("max_thrust_kn")
    max_power_kw = engine.get("max_power_kw")
    tsfc_kg_kn_hr = engine.get("tsfc_kn_hr")

    if max_thrust_kn and max_power_kw:
        violations.append({
            "component": "engine",
            "error": f"Engine has both thrust ({max_thrust_kn} kN) and power ({max_power_kw} kW) defined",
            "severity": "warning"
        })

    if engine_type == "piston" and max_thrust_kn:
        violations.append({
            "component": "engine",
            "error": "Piston engines should use power (kW), not thrust (kN)",
            "severity": "error"
        })

    if engine_type == "turbojet" and max_power_kw:
        violations.append({
            "component": "engine",
            "error": "Turbojet engines should use thrust (kN), not power (kW)",
            "severity": "error"
        })

    if max_thrust_kn:
        total_thrust = max_thrust_kn * num_engines
        thrust_to_weight = total_thrust * 1000 / (mtow_kg * 9.81)

        if thrust_to_weight < 0.2:
            violations.append({
                "component": "engine",
                "error": f"Thrust-to-weight ratio ({thrust_to_weight:.2f}) is below recommended minimum of 0.2",
                "severity": "warning"
            })
        elif thrust_to_weight > 1.0:
            violations.append({
                "component": "engine",
                "error": f"Thrust-to-weight ratio ({thrust_to_weight:.2f}) is above typical maximum of 1.0",
                "severity": "warning"
            })

    if max_power_kw:
        total_power = max_power_kw * num_engines
        power_to_weight = total_power / (mtow_kg * 9.81)

        if power_to_weight < 0.1:
            violations.append({
                "component": "engine",
                "error": f"Power-to-weight ratio ({power_to_weight:.2f} kW/N) is below recommended minimum of 0.1",
                "severity": "warning"
            })
        elif power_to_weight > 0.5:
            violations.append({
                "component": "engine",
                "error": f"Power-to-weight ratio ({power_to_weight:.2f} kW/N) is above typical maximum of 0.5",
                "severity": "warning"
            })

    if tsfc_kg_kn_hr and tsfc_kg_kn_hr > 2.0:
        violations.append({
            "component": "engine",
            "error": f"TSFC ({tsfc_kg_kn_hr} kg/kN-hr) is unusually high",
            "severity": "warning"
        })

    return violations
