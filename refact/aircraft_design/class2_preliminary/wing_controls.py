from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WingControlConfig:
    name: str
    type: str
    eta_in: float
    eta_out: float
    chord_fraction: float
    deflection_deg: float | None = None
    hinge_xc: float | None = None


DEFAULT_WING_CONTROLS = {
    "aileron": {
        "type": "aileron",
        "eta_in": 0.75,
        "eta_out": 0.95,
        "chord_fraction": 0.25,
        "deflection_deg": 20.0,
    },
    "flap": {
        "type": "flap",
        "eta_in": 0.1,
        "eta_out": 0.6,
        "chord_fraction": 0.3,
        "deflection_deg": 30.0,
    },
    "spoiler": {
        "type": "spoiler",
        "eta_in": 0.4,
        "eta_out": 0.8,
        "chord_fraction": 0.2,
        "deflection_deg": 45.0,
    },
}


def parse_wing_controls_config(config: dict, path: str = "wing_controls") -> dict:
    if not isinstance(config, dict):
        return {}
    
    result = {}
    for key, value in config.items():
        if isinstance(value, dict):
            result[key] = WingControlConfig(
                name=key,
                type=str(value.get("type", key)),
                eta_in=float(value.get("eta_in", 0.1)),
                eta_out=float(value.get("eta_out", 0.95)),
                chord_fraction=float(value.get("chord_fraction", 0.25)),
                deflection_deg=float(value.get("deflection_deg", None)),
                hinge_xc=float(value.get("hinge_xc", None)),
            )
        elif isinstance(value, WingControlConfig):
            result[key] = value
    
    return result


def validate_wing_controls(controls: dict, wing_span: float, wing_chord: float) -> list[str]:
    violations = []
    
    for name, ctrl in controls.items():
        if not isinstance(ctrl, WingControlConfig):
            continue
        
        if not (0.0 <= ctrl.eta_in <= 1.0):
            violations.append(f"{name}: eta_in must be in [0, 1]")
        if not (0.0 <= ctrl.eta_out <= 1.0):
            violations.append(f"{name}: eta_out must be in [0, 1]")
        if ctrl.eta_out <= ctrl.eta_in:
            violations.append(f"{name}: eta_out must be > eta_in")
        if not (0.0 < ctrl.chord_fraction <= 1.0):
            violations.append(f"{name}: chord_fraction must be in (0, 1]")
    
    return violations


def calculate_control_surface_weight(
    controls: dict,
    wing_span: float,
    wing_chord: float,
    density_kg_m3: float = 2700.0,
    thickness_fraction: float = 0.1,
) -> float:
    total_weight = 0.0
    
    for ctrl in controls.values():
        if not isinstance(ctrl, WingControlConfig):
            continue
        
        span = (ctrl.eta_out - ctrl.eta_in) * wing_span
        chord = ctrl.chord_fraction * wing_chord
        area = span * chord
        volume = area * (chord * thickness_fraction)
        weight = volume * density_kg_m3
        total_weight += weight
    
    return total_weight
