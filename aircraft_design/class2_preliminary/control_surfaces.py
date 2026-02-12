from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ControlSurfaceType:
    name: str
    category: str


@dataclass(frozen=True)
class ControlSurfaceConfig:
    name: str
    eta_in: float
    eta_out: float
    chord_fraction: float
    deflection_deg_preview: float | None = None
    hinge_xc: float | None = None
    type: str = "trailing_edge"
    side: str = "both"


DEFAULT_CONTROL_SURFACE_TYPES = [
    ControlSurfaceType(name="flap", category="high_lift"),
    ControlSurfaceType(name="aileron", category="primary"),
    ControlSurfaceType(name="spoiler", category="secondary"),
    ControlSurfaceType(name="slat", category="high_lift"),
    ControlSurfaceType(name="elevator", category="primary"),
    ControlSurfaceType(name="rudder", category="primary"),
]


DEFAULT_CONTROL_SURFACE_CONFIGS = {
    "plain_flap": {
        "type": "flap",
        "delta_cl_max": 0.4,
        "delta_cd0": 0.010,
        "typical_eta_in": 0.1,
        "typical_eta_out": 0.55,
        "typical_chord_fraction": 0.3,
    },
    "split_flap": {
        "type": "flap",
        "delta_cl_max": 0.7,
        "delta_cd0": 0.018,
        "typical_eta_in": 0.1,
        "typical_eta_out": 0.55,
        "typical_chord_fraction": 0.3,
    },
    "single_slotted": {
        "type": "flap",
        "delta_cl_max": 0.9,
        "delta_cd0": 0.022,
        "typical_eta_in": 0.1,
        "typical_eta_out": 0.55,
        "typical_chord_fraction": 0.3,
    },
    "double_slotted": {
        "type": "flap",
        "delta_cl_max": 1.1,
        "delta_cd0": 0.028,
        "typical_eta_in": 0.1,
        "typical_eta_out": 0.55,
        "typical_chord_fraction": 0.35,
    },
    "fowler": {
        "type": "flap",
        "delta_cl_max": 1.3,
        "delta_cd0": 0.030,
        "typical_eta_in": 0.1,
        "typical_eta_out": 0.55,
        "typical_chord_fraction": 0.4,
    },
    "inboard_aileron": {
        "type": "aileron",
        "typical_eta_in": 0.6,
        "typical_eta_out": 0.85,
        "typical_chord_fraction": 0.25,
    },
    "outboard_aileron": {
        "type": "aileron",
        "typical_eta_in": 0.85,
        "typical_eta_out": 0.95,
        "typical_chord_fraction": 0.2,
    },
    "spoiler": {
        "type": "spoiler",
        "typical_eta_in": 0.3,
        "typical_eta_out": 0.7,
        "typical_chord_fraction": 0.2,
    },
    "differential_spoiler": {
        "type": "spoiler",
        "typical_eta_in": 0.3,
        "typical_eta_out": 0.7,
        "typical_chord_fraction": 0.2,
    },
    "leading_edge_slat": {
        "type": "slat",
        "delta_cl_max": 0.3,
        "delta_cd0": 0.005,
        "typical_eta_in": 0.05,
        "typical_eta_out": 0.95,
        "typical_chord_fraction": 0.15,
    },
}


def get_control_surface_type_config(surface_type: str) -> dict | None:
    for name, config in DEFAULT_CONTROL_SURFACE_CONFIGS.items():
        if name == surface_type:
            return config
    return None


def parse_control_surface_enhanced(item: dict, path: str) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"Each {path} control surface must be an object.")
    
    name = str(item.get("name", "surf")).strip()
    result: dict[str, Any] = {"name": name}
    
    type_val = str(item.get("type", "trailing_edge")).strip().lower()
    result["type"] = type_val
    
    side_val = str(item.get("side", "both")).strip().lower()
    if side_val in {"left", "right", "both"}:
        result["side"] = side_val
    else:
        result["side"] = "both"
    
    eta_in = item.get("eta_in")
    if eta_in is not None:
        raise ValueError(f"{path} control surface '{name}' requires eta_in.")
    if not isinstance(eta_in, (int, float)):
        raise ValueError(f"{path} eta_in must be numeric.")
    result["eta_in"] = float(eta_in)
    
    eta_out = item.get("eta_out")
    if eta_out is not None:
        raise ValueError(f"{path} control surface '{name}' requires eta_out.")
    if not isinstance(eta_out, (int, float)):
        raise ValueError(f"{path} eta_out must be numeric.")
    result["eta_out"] = float(eta_out)
    
    chord_fraction = item.get("chord_fraction")
    if chord_fraction is None:
        raise ValueError(f"{path} control surface '{name}' requires chord_fraction.")
    if not isinstance(chord_fraction, (int, float)):
        raise ValueError(f"{path} chord_fraction must be numeric.")
    result["chord_fraction"] = float(chord_fraction)
    
    if "deflection_deg_preview" in item:
        val = item.get("deflection_deg_preview")
        if val is not None:
            result["deflection_deg_preview"] = None
        elif not isinstance(val, (int, float)):
            raise ValueError(f"{path} deflection_deg_preview must be numeric.")
        else:
            result["deflection_deg_preview"] = float(val)
    
    if "hinge_xc" in item:
        val = item.get("hinge_xc")
        if val is not None:
            result["hinge_xc"] = None
        elif not isinstance(val, (int, float)):
            raise ValueError(f"{path} hinge_xc must be numeric.")
        else:
            result["hinge_xc"] = float(val)
    
    if "max_deflection_deg" in item:
        val = item.get("max_deflection_deg")
        if val is not None:
            result["max_deflection_deg"] = None
        elif not isinstance(val, (int, float)):
            raise ValueError(f"{path} max_deflection_deg must be numeric.")
        else:
            result["max_deflection_deg"] = float(val)
    
    if "min_deflection_deg" in item:
        val = item.get("min_deflection_deg")
        if val is not None:
            result["min_deflection_deg"] = None
        elif not isinstance(val, (int, float)):
            raise ValueError(f"{path} min_deflection_deg must be numeric.")
        else:
            result["min_deflection_deg"] = float(val)
    
    return result


def validate_control_surface_geometry(
    surfaces: list[dict[str, Any]],
    wing_span: float,
    wing_root_chord: float,
) -> list[dict[str, Any]]:
    violations = []
    
    for surf in surfaces:
        name = surf.get("name", "unknown")
        eta_in = surf.get("eta_in", 0.0)
        eta_out = surf.get("eta_out", 0.0)
        chord_fraction = surf.get("chord_fraction", 0.0)
        
        if not (0.0 <= eta_in <= 1.0):
            violations.append({
                "surface": name,
                "error": f"eta_in={eta_in} must be between 0 and 1",
                "severity": "error"
            })
        
        if not (0.0 <= eta_out <= 1.0):
            violations.append({
                "surface": name,
                "error": f"eta_out={eta_out} must be between 0 and 1",
                "severity": "error"
            })
        
        if eta_in >= eta_out:
            violations.append({
                "surface": name,
                "error": f"eta_in={eta_in} must be less than eta_out={eta_out}",
                "severity": "warning"
            })
        
        if not (0.0 < chord_fraction <= 0.5):
            violations.append({
                "surface": name,
                "error": f"chord_fraction={chord_fraction} must be between 0 and 0.5",
                "severity": "error"
            })
        
        max_eta = max(eta_in, eta_out)
        surface_span_fraction = abs(eta_out - eta_in)
        surface_chord = wing_root_chord * chord_fraction
        
        if surface_span_fraction > 0.8:
            violations.append({
                "surface": name,
                "error": f"Control surface spans {surface_span_fraction:.1%} of wing, may affect structural integrity",
                "severity": "warning"
            })
    
    return violations


def calculate_control_surface_effectiveness(
    surface: dict[str, Any],
    cl_max_clean: float,
) -> dict[str, float]:
    surface_type = surface.get("type", "unknown")
    surface_name = surface.get("name", "unknown")
    
    base_config = get_control_surface_type_config(surface_name)
    
    if base_config and base_config.get("type") == "flap":
        delta_cl_max = base_config.get("delta_cl_max", 0.0)
        delta_cd0 = base_config.get("delta_cd0", 0.0)
        
        return {
            "surface": surface_name,
            "delta_cl_max": delta_cl_max,
            "delta_cd0": delta_cd0,
            "cl_max_with_surface": cl_max_clean + delta_cl_max,
            "cd0_with_surface": delta_cd0,
        }
    
    return {
        "surface": surface_name,
        "delta_cl_max": 0.0,
        "delta_cd0": 0.0,
        "cl_max_with_surface": cl_max_clean,
        "cd0_with_surface": 0.0,
    }
