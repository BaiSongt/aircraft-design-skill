from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NacelleType:
    name: str
    category: str


NACELLE_TYPES = [
    NacelleType(name="podded", category="external"),
    NacelleType(name="integrated", category="fuselage"),
    NacelleType(name="pusher", category="rear"),
    NacelleType(name="turboprop", category="propeller"),
]


DEFAULT_NACELLE_CONFIGS = {
    "small_podded": {
        "type": "podded",
        "length_diameter_ratio": 3.0,
        "inlet_ratio": 0.7,
        "max_radius_position": 0.25,
        "description": "Small podded nacelle for light aircraft",
    },
    "medium_podded": {
        "type": "podded",
        "length_diameter_ratio": 3.5,
        "inlet_ratio": 0.65,
        "max_radius_position": 0.2,
        "description": "Medium podded nacelle for regional aircraft",
    },
    "large_podded": {
        "type": "podded",
        "length_diameter_ratio": 4.0,
        "inlet_ratio": 0.6,
        "max_radius_position": 0.2,
        "description": "Large podded nacelle for commercial aircraft",
    },
    "turboprop": {
        "type": "turboprop",
        "length_diameter_ratio": 2.5,
        "inlet_ratio": 0.0,
        "max_radius_position": 0.3,
        "spinner_ratio": 0.3,
        "description": "Turboprop nacelle with spinner",
    },
}


def parse_nacelle_config(nacelle_dict: dict, path: str) -> dict[str, Any]:
    if not isinstance(nacelle_dict, dict):
        raise ValueError(f"{path}.nacelle must be an object.")

    result: dict[str, Any] = {}

    nacelle_type = nacelle_dict.get("type", "podded").strip().lower()
    if nacelle_type not in {"podded", "integrated", "pusher", "turboprop"}:
        raise ValueError(f"Unknown nacelle type: {nacelle_type}")
    result["type"] = nacelle_type

    if "diameter_m" in nacelle_dict:
        val = nacelle_dict.get("diameter_m")
        if val is not None:
            result["diameter_m"] = None
        elif not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"{path}.diameter_m must be positive.")
        else:
            result["diameter_m"] = float(val)

    if "length_m" in nacelle_dict:
        val = nacelle_dict.get("length_m")
        if val is not None:
            result["length_m"] = None
        elif not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"{path}.length_m must be positive.")
        else:
            result["length_m"] = float(val)
    else:
        diameter = result.get("diameter_m", 1.0)
        base_config = DEFAULT_NACELLE_CONFIGS.get("medium_podded", {})
        length_diameter_ratio = base_config.get("length_diameter_ratio", 3.5)
        result["length_m"] = diameter * length_diameter_ratio

    if "inlet_ratio" in nacelle_dict:
        val = nacelle_dict.get("inlet_ratio")
        if val is not None:
            result["inlet_ratio"] = None
        elif not isinstance(val, (int, float)) or val < 0 or val > 1:
            raise ValueError(f"{path}.inlet_ratio must be between 0 and 1.")
        else:
            result["inlet_ratio"] = float(val)
    else:
        base_config = DEFAULT_NACELLE_CONFIGS.get("medium_podded", {})
        result["inlet_ratio"] = base_config.get("inlet_ratio", 0.65)

    if "max_radius_position" in nacelle_dict:
        val = nacelle_dict.get("max_radius_position")
        if val is not None:
            result["max_radius_position"] = None
        elif not isinstance(val, (int, float)) or val < 0 or val > 1:
            raise ValueError(f"{path}.max_radius_position must be between 0 and 1.")
        else:
            result["max_radius_position"] = float(val)
    else:
        base_config = DEFAULT_NACELLE_CONFIGS.get("medium_podded", {})
        result["max_radius_position"] = base_config.get("max_radius_position", 0.2)

    if "mount_position" in nacelle_dict:
        mount_dict = nacelle_dict["mount_position"]
        if not isinstance(mount_dict, dict):
            raise ValueError(f"{path}.mount_position must be an object.")

        mount_result = {}

        if "wing_span_fraction" in mount_dict:
            val = mount_dict["wing_span_fraction"]
            if val is not None:
                mount_result["wing_span_fraction"] = None
            elif not isinstance(val, (int, float)) or val < 0 or val > 1:
                raise ValueError(f"{path}.mount_position.wing_span_fraction must be between 0 and 1.")
            else:
                mount_result["wing_span_fraction"] = float(val)
        else:
            mount_result["wing_span_fraction"] = 0.33

        if "x_offset_m" in mount_dict:
            val = mount_dict["x_offset_m"]
            if val is not None:
                mount_result["x_offset_m"] = None
            elif not isinstance(val, (int, float)):
                raise ValueError(f"{path}.mount_position.x_offset_m must be numeric.")
            else:
                mount_result["x_offset_m"] = float(val)
        else:
            mount_result["x_offset_m"] = 0.0

        if "z_offset_m" in mount_dict:
            val = mount_dict["z_offset_m"]
            if val is not None:
                mount_result["z_offset_m"] = None
            elif not isinstance(val, (int, float)):
                raise ValueError(f"{path}.mount_position.z_offset_m must be numeric.")
            else:
                mount_result["z_offset_m"] = float(val)
        else:
            mount_result["z_offset_m"] = 0.0

        result["mount_position"] = mount_result

    if nacelle_type == "turboprop":
        if "spinner_ratio" in nacelle_dict:
            val = nacelle_dict.get("spinner_ratio")
            if val is not None:
                result["spinner_ratio"] = None
            elif not isinstance(val, (int, float)) or val < 0 or val > 1:
                raise ValueError(f"{path}.spinner_ratio must be between 0 and 1.")
            else:
                result["spinner_ratio"] = float(val)
        else:
            base_config = DEFAULT_NACELLE_CONFIGS.get("turboprop", {})
            result["spinner_ratio"] = base_config.get("spinner_ratio", 0.3)

        if "propeller_diameter_m" in nacelle_dict:
            val = nacelle_dict.get("propeller_diameter_m")
            if val is not None:
                result["propeller_diameter_m"] = None
            elif not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(f"{path}.propeller_diameter_m must be positive.")
            else:
                result["propeller_diameter_m"] = float(val)

    if "pylon" in nacelle_dict:
        pylon_dict = nacelle_dict["pylon"]
        if not isinstance(pylon_dict, dict):
            raise ValueError(f"{path}.pylon must be an object.")

        pylon_result = {}

        if "length_m" in pylon_dict:
            val = pylon_dict["length_m"]
            if val is not None:
                pylon_result["length_m"] = None
            elif not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(f"{path}.pylon.length_m must be positive.")
            else:
                pylon_result["length_m"] = float(val)
        else:
            pylon_result["length_m"] = 0.0

        if "thickness_m" in pylon_dict:
            val = pylon_dict["thickness_m"]
            if val is not None:
                pylon_result["thickness_m"] = None
            elif not isinstance(val, (int, float)) or val < 0:
                raise ValueError(f"{path}.pylon.thickness_m must be non-negative.")
            else:
                pylon_result["thickness_m"] = float(val)
        else:
            pylon_result["thickness_m"] = 0.0

        result["pylon"] = pylon_result

    return result


def validate_nacelle_config(
    nacelle: dict[str, Any],
    wing_chord: float,
    engine_diameter: float,
) -> list[dict[str, Any]]:
    violations = []

    nacelle_type = nacelle.get("type", "unknown")
    diameter_m = nacelle.get("diameter_m", 1.0)
    length_m = nacelle.get("length_m", 3.5)

    length_diameter_ratio = length_m / diameter_m

    if length_diameter_ratio < 2.0:
        violations.append({
            "component": "nacelle",
            "error": f"Nacelle length-to-diameter ratio ({length_diameter_ratio:.2f}) is below recommended minimum of 2.0",
            "severity": "warning"
        })
    elif length_diameter_ratio > 5.0:
        violations.append({
            "component": "nacelle",
            "error": f"Nacelle length-to-diameter ratio ({length_diameter_ratio:.2f}) is above recommended maximum of 5.0",
            "severity": "warning"
        })

    if diameter_m < engine_diameter * 1.05:
        violations.append({
            "component": "nacelle",
            "error": f"Nacelle diameter ({diameter_m:.2f} m) is too small for engine ({engine_diameter:.2f} m)",
            "severity": "error"
        })

    mount_position = nacelle.get("mount_position", {})
    wing_span_fraction = mount_position.get("wing_span_fraction", 0.33)

    if wing_span_fraction < 0.1 or wing_span_fraction > 0.6:
        violations.append({
            "component": "nacelle",
            "error": f"Mount position ({wing_span_fraction:.2%}) should be between 10% and 60% of wing span",
            "severity": "warning"
        })

    inlet_ratio = nacelle.get("inlet_ratio", 0.65)

    if inlet_ratio > 0.8:
        violations.append({
            "component": "nacelle",
            "error": f"Inlet ratio ({inlet_ratio:.2%}) is above recommended maximum of 80%",
            "severity": "warning"
        })

    if nacelle_type == "turboprop":
        propeller_diameter = nacelle.get("propeller_diameter_m")
        if propeller_diameter:
            tip_clearance = propeller_diameter / 2 - diameter_m / 2
            if tip_clearance < 0.1:
                violations.append({
                    "component": "nacelle",
                    "error": f"Propeller tip clearance ({tip_clearance:.2f} m) is below recommended 0.1 m",
                    "severity": "warning"
                })

    pylon = nacelle.get("pylon", {})
    pylon_length = pylon.get("length_m", 0.0)

    if pylon_length > wing_chord * 0.8:
        violations.append({
            "component": "nacelle",
            "error": f"Pylon length ({pylon_length:.2f} m) is more than 80% of wing chord",
            "severity": "warning"
        })

    return violations


def calculate_nacelle_drag(
    nacelle: dict[str, Any],
    cruise_speed_ktas: float,
    dynamic_pressure: float,
) -> dict[str, float]:
    diameter_m = nacelle.get("diameter_m", 1.0)
    length_m = nacelle.get("length_m", 3.5)
    nacelle_type = nacelle.get("type", "podded")

    wetted_area = 3.14159 * diameter_m * length_m

    if nacelle_type == "podded":
        cd0_nacelle = 0.008
    elif nacelle_type == "turboprop":
        cd0_nacelle = 0.010
    else:
        cd0_nacelle = 0.007

    drag_force = cd0_nacelle * wetted_area * dynamic_pressure

    return {
        "wetted_area_m2": wetted_area,
        "cd0_nacelle": cd0_nacelle,
        "drag_force_n": drag_force,
    }


def generate_nacelle_stations(
    nacelle: dict[str, Any],
    num_stations: int = 21,
) -> list[dict[str, float]]:
    diameter_m = nacelle.get("diameter_m", 1.0)
    length_m = nacelle.get("length_m", 3.5)
    inlet_ratio = nacelle.get("inlet_ratio", 0.65)
    max_radius_position = nacelle.get("max_radius_position", 0.2)

    stations = []

    for i in range(num_stations):
        x_rel = i / (num_stations - 1)
        x_m = x_rel * length_m

        if x_rel < inlet_ratio:
            radius_ratio = 0.5 + 0.5 * (x_rel / inlet_ratio)
        elif x_rel < max_radius_position:
            radius_ratio = 1.0
        else:
            aft_fraction = (x_rel - max_radius_position) / (1.0 - max_radius_position)
            radius_ratio = 1.0 - 0.5 * aft_fraction

        radius_m = radius_ratio * diameter_m / 2

        stations.append({
            "x_m": x_m,
            "radius_m": max(0.0, radius_m),
        })

    return stations


def generate_nacelle_mesh(
    nacelle: dict[str, Any],
    num_stations: int = 21,
    num_circumferential: int = 24,
) -> dict[str, Any]:
    stations = generate_nacelle_stations(nacelle, num_stations)

    vertices = []
    for station in stations:
        x_m = station["x_m"]
        radius_m = station["radius_m"]

        for j in range(num_circumferential):
            theta = 2 * 3.14159 * j / num_circumferential
            y_m = radius_m * 3.14159.cos(theta)
            z_m = radius_m * 3.14159.sin(theta)
            vertices.append([x_m, y_m, z_m])

    faces = []
    for i in range(num_stations - 1):
        for j in range(num_circumferential):
            v0 = i * num_circumferential + j
            v1 = i * num_circumferential + (j + 1) % num_circumferential
            v2 = (i + 1) * num_circumferential + (j + 1) % num_circumferential
            v3 = (i + 1) * num_circumferential + j

            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

    return {
        "vertices": vertices,
        "faces": faces,
        "stations": stations,
    }
