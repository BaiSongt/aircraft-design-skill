from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WingtipType:
    name: str
    category: str


@dataclass(frozen=True)
class WingtipConfig:
    name: str
    type: str
    efficiency_gain: float
    weight_factor: float


DEFAULT_WINGTIP_TYPES = [
    WingtipType(name="none", category="standard"),
    WingtipType(name="winglet", category="drag_reduction"),
    WingtipType(name="tip_fence", category="drag_reduction"),
    WingtipType(name="blended", category="drag_reduction"),
    WingtipType(name="canted", category="drag_reduction"),
]


DEFAULT_WINGTIP_CONFIGS = {
    "none": {
        "type": "none",
        "efficiency_gain": 0.0,
        "weight_factor": 1.0,
        "description": "Standard rounded wingtip",
    },
    "small_winglet": {
        "type": "winglet",
        "efficiency_gain": 0.02,
        "weight_factor": 1.02,
        "height_m": 0.5,
        "sweep_deg": 30.0,
        "cant_deg": 45.0,
        "description": "Small winglet for modest drag reduction",
    },
    "medium_winglet": {
        "type": "winglet",
        "efficiency_gain": 0.04,
        "weight_factor": 1.03,
        "height_m": 1.0,
        "sweep_deg": 30.0,
        "cant_deg": 50.0,
        "description": "Medium winglet for moderate drag reduction",
    },
    "large_winglet": {
        "type": "winglet",
        "efficiency_gain": 0.06,
        "weight_factor": 1.05,
        "height_m": 1.5,
        "sweep_deg": 35.0,
        "cant_deg": 55.0,
        "description": "Large winglet for significant drag reduction",
    },
    "tip_fence": {
        "type": "tip_fence",
        "efficiency_gain": 0.015,
        "weight_factor": 1.01,
        "height_m": 0.3,
        "description": "Wing tip fence for vortex control",
    },
    "blended": {
        "type": "blended",
        "efficiency_gain": 0.05,
        "weight_factor": 1.04,
        "height_m": 1.2,
        "sweep_deg": 25.0,
        "cant_deg": 0.0,
        "description": "Blended wingtip for drag reduction",
    },
    "canted": {
        "type": "canted",
        "efficiency_gain": 0.03,
        "weight_factor": 1.02,
        "height_m": 0.8,
        "sweep_deg": 20.0,
        "cant_deg": 60.0,
        "description": "Canted wingtip for drag reduction",
    },
}


def get_wingtip_config(wingtip_type: str) -> dict | None:
    for name, config in DEFAULT_WINGTIP_CONFIGS.items():
        if name == wingtip_type:
            return config
    return None


def parse_wingtip(wingtip_dict: dict, path: str) -> dict[str, Any]:
    if not isinstance(wingtip_dict, dict):
        raise ValueError(f"{path}.wingtip must be an object.")

    wingtip_type = wingtip_dict.get("type", "none")
    if not isinstance(wingtip_type, str):
        raise ValueError(f"{path}.wingtip.type must be a string.")

    wingtip_type = wingtip_type.lower().strip()
    if wingtip_type == "none":
        return {"type": "none"}

    base_config = get_wingtip_config(wingtip_type)
    if base_config is None:
        raise ValueError(f"Unknown wingtip type: {wingtip_type}")

    result: dict[str, Any] = {"type": wingtip_type}

    if "height_m" in wingtip_dict:
        val = wingtip_dict.get("height_m")
        if val is not None:
            result["height_m"] = None
        elif not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"{path}.wingtip.height_m must be positive.")
        else:
            result["height_m"] = float(val)
    else:
        result["height_m"] = base_config.get("height_m", 0.5)

    if "sweep_deg" in wingtip_dict:
        val = wingtip_dict.get("sweep_deg")
        if val is not None:
            result["sweep_deg"] = None
        elif not isinstance(val, (int, float)):
            raise ValueError(f"{path}.wingtip.sweep_deg must be numeric.")
        else:
            result["sweep_deg"] = float(val)
    else:
        result["sweep_deg"] = base_config.get("sweep_deg", 30.0)

    if "cant_deg" in wingtip_dict:
        val = wingtip_dict.get("cant_deg")
        if val is not None:
            result["cant_deg"] = None
        elif not isinstance(val, (int, float)):
            raise ValueError(f"{path}.wingtip.cant_deg must be numeric.")
        else:
            result["cant_deg"] = float(val)
    else:
        result["cant_deg"] = base_config.get("cant_deg", 45.0)

    if "blend_length_m" in wingtip_dict:
        val = wingtip_dict.get("blend_length_m")
        if val is not None:
            result["blend_length_m"] = None
        elif not isinstance(val, (int, float)) or val < 0:
            raise ValueError(f"{path}.wingtip.blend_length_m must be non-negative.")
        else:
            result["blend_length_m"] = float(val)

    if "tip_chord_fraction" in wingtip_dict:
        val = wingtip_dict.get("tip_chord_fraction")
        if val is not None:
            result["tip_chord_fraction"] = None
        elif not isinstance(val, (int, float)) or val <= 0 or val > 1:
            raise ValueError(f"{path}.wingtip.tip_chord_fraction must be between 0 and 1.")
        else:
            result["tip_chord_fraction"] = float(val)

    return result


def calculate_wingtip_effectiveness(
    wingtip: dict[str, Any],
    wing_aspect_ratio: float,
) -> dict[str, float]:
    wingtip_type = wingtip.get("type", "none")

    base_config = get_wingtip_config(wingtip_type)
    if base_config is None:
        base_config = DEFAULT_WINGTIP_CONFIGS["none"]

    efficiency_gain = base_config.get("efficiency_gain", 0.0)
    weight_factor = base_config.get("weight_factor", 1.0)

    effective_aspect_ratio = wing_aspect_ratio * (1.0 + efficiency_gain)

    induced_drag_reduction = 1.0 - 1.0 / (1.0 + efficiency_gain)

    return {
        "wingtip_type": wingtip_type,
        "base_aspect_ratio": wing_aspect_ratio,
        "effective_aspect_ratio": effective_aspect_ratio,
        "efficiency_gain": efficiency_gain,
        "induced_drag_reduction": induced_drag_reduction,
        "weight_factor": weight_factor,
    }


def validate_wingtip_geometry(
    wingtip: dict[str, Any],
    wing_span: float,
    wing_tip_chord: float,
) -> list[dict[str, Any]]:
    violations = []
    wingtip_type = wingtip.get("type", "none")

    if wingtip_type == "none":
        return violations

    height_m = wingtip.get("height_m", 0.0)
    sweep_deg = wingtip.get("sweep_deg", 0.0)
    cant_deg = wingtip.get("cant_deg", 0.0)

    if height_m <= 0:
        violations.append({
            "component": "wingtip",
            "error": f"wingtip height_m={height_m} must be positive",
            "severity": "error"
        })

    if height_m > wing_span * 0.2:
        violations.append({
            "component": "wingtip",
            "error": f"wingtip height_m={height_m} is more than 20% of wing span",
            "severity": "warning"
        })

    if sweep_deg < 0 or sweep_deg > 60:
        violations.append({
            "component": "wingtip",
            "error": f"wingtip sweep_deg={sweep_deg} should be between 0 and 60 degrees",
            "severity": "warning"
        })

    if cant_deg < 0 or cant_deg > 90:
        violations.append({
            "component": "wingtip",
            "error": f"wingtip cant_deg={cant_deg} should be between 0 and 90 degrees",
            "severity": "warning"
        })

    blend_length_m = wingtip.get("blend_length_m", 0.0)
    if blend_length_m > wing_tip_chord * 0.5:
        violations.append({
            "component": "wingtip",
            "error": f"wingtip blend_length_m={blend_length_m} is more than 50% of tip chord",
            "severity": "warning"
        })

    return violations
