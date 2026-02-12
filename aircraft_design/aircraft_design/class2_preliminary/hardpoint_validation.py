from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HardpointType:
    name: str
    category: str
    max_load_kg: float
    location_type: str


HARDPOINT_TYPES = [
    HardpointType(name="wing_mount", category="structure", max_load_kg=5000.0, location_type="wing"),
    HardpointType(name="fuselage_frame", category="structure", max_load_kg=10000.0, location_type="fuselage"),
    HardpointType(name="engine_mount", category="power", max_load_kg=3000.0, location_type="engine"),
    HardpointType(name="landing_gear_mount", category="landing", max_load_kg=8000.0, location_type="landing_gear"),
    HardpointType(name="payload_hook", category="cargo", max_load_kg=15000.0, location_type="fuselage"),
    HardpointType(name="external_store", category="armament", max_load_kg=2000.0, location_type="wing"),
    HardpointType(name="antenna_mount", category="avionics", max_load_kg=500.0, location_type="fuselage"),
    HardpointType(name="fuel_tank_mount", category="fuel", max_load_kg=5000.0, location_type="wing"),
    HardpointType(name="sensor_mount", category="avionics", max_load_kg=200.0, location_type="fuselage"),
]


def parse_hardpoint_config(hardpoint_dict: dict, path: str) -> dict[str, Any]:
    if not isinstance(hardpoint_dict, dict):
        raise ValueError(f"{path}.hardpoint must be an object.")
    
    result: dict[str, Any] = {}
    
    hardpoint_type = hardpoint_dict.get("type", "fuselage_frame").strip().lower()
    valid_types = {ht.name for ht in HARDPOINT_TYPES}
    if hardpoint_type not in valid_types:
        raise ValueError(f"Unknown hardpoint type: {hardpoint_type}")
    result["type"] = hardpoint_type
    
    if "id" in hardpoint_dict:
        result["id"] = str(hardpoint_dict["id"]).strip()
    else:
        raise ValueError(f"{path}.id is required.")
    
    if "x_rel" in hardpoint_dict:
        val = hardpoint_dict.get("x_rel")
        if not isinstance(val, (int, float)) or val < 0 or val > 1:
            raise ValueError(f"{path}.x_rel must be between 0 and 1.")
        result["x_rel"] = float(val)
    else:
        raise ValueError(f"{path}.x_rel is required.")
    
    if "y_rel" in hardpoint_dict:
        val = hardpoint_dict.get("y_rel")
        if not isinstance(val, (int, float)) or val < -1.0 or val > 1.0:
            raise ValueError(f"{path}.y_rel must be between -1 and 1.")
        result["y_rel"] = float(val)
    else:
        result["y_rel"] = 0.0
    
    if "z_rel" in hardpoint_dict:
        val = hardpoint_dict.get("z_rel")
        if not isinstance(val, (int, float)) or val < -1.0 or val > 1.0:
            raise ValueError(f"{path}.z_rel must be between -1 and 1.")
        result["z_rel"] = float(val)
    else:
        result["z_rel"] = 0.0
    
    if "max_load_kg" in hardpoint_dict:
        val = hardpoint_dict.get("max_load_kg")
        if not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"{path}.max_load_kg must be positive.")
        result["max_load_kg"] = float(val)
    else:
        type_info = next((ht for ht in HARDPOINT_TYPES if ht.name == hardpoint_type), None)
        if type_info:
            result["max_load_kg"] = type_info.max_load_kg
    
    if "is_primary" in hardpoint_dict:
        if not isinstance(hardpoint_dict["is_primary"], bool):
            raise ValueError(f"{path}.is_primary must be a boolean.")
        result["is_primary"] = hardpoint_dict["is_primary"]
    
    if "attachment_type" in hardpoint_dict:
        attachment = str(hardpoint_dict["attachment_type"]).strip().lower()
        if attachment not in {"bolted", "welded", "bonded", "clamped", "quick_release"}:
            raise ValueError(f"{path}.attachment_type must be bolted, welded, bonded, clamped, or quick_release.")
        result["attachment_type"] = attachment
    
    if "material" in hardpoint_dict:
        result["material"] = str(hardpoint_dict["material"]).strip()
    
    if "reinforcement" in hardpoint_dict:
        if not isinstance(hardpoint_dict["reinforcement"], bool):
            raise ValueError(f"{path}.reinforcement must be a boolean.")
        result["reinforcement"] = hardpoint_dict["reinforcement"]
    
    if "mounting_area_m2" in hardpoint_dict:
        val = hardpoint_dict.get("mounting_area_m2")
        if not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"{path}.mounting_area_m2 must be positive.")
        result["mounting_area_m2"] = float(val)
    
    return result


def validate_hardpoint_config(
    hardpoint: dict[str, Any],
    fuselage_length: float,
    fuselage_diameter: float,
    wing_span: float,
    stations: list[dict],
    other_hardpoints: list[dict],
) -> list[dict[str, Any]]:
    violations = []
    
    x_rel = hardpoint.get("x_rel", 0.5)
    y_rel = hardpoint.get("y_rel", 0.0)
    z_rel = hardpoint.get("z_rel", 0.0)
    max_load_kg = hardpoint.get("max_load_kg", 0.0)
    mounting_area_m2 = hardpoint.get("mounting_area_m2", 0.1)
    
    x_position = x_rel * fuselage_length
    y_position = y_rel * fuselage_diameter / 2
    z_position = z_rel * fuselage_diameter / 2
    
    hardpoint_type = hardpoint.get("type", "fuselage_frame")
    type_info = next((ht for ht in HARDPOINT_TYPES if ht.name == hardpoint_type), None)
    
    if type_info and max_load_kg > type_info.max_load_kg:
        violations.append({
            "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
            "error": f"Hardpoint load ({max_load_kg:.1f} kg) exceeds maximum {type_info.max_load_kg:.1f} kg for type",
            "severity": "error"
        })
    
    stress_kg_m2 = max_load_kg / mounting_area_m2 if mounting_area_m2 > 0 else 0
    if stress_kg_m2 > 100000.0:
        violations.append({
            "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
            "error": f"Mounting stress ({stress_kg_m2:.1f} kg/m²) exceeds structural limit of 100000 kg/m²",
            "severity": "error"
        })
    
    location_type = hardpoint_type
    if location_type == "wing" and abs(y_position) > wing_span * 0.45:
        violations.append({
            "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
            "error": f"Wing hardpoint Y position ({y_position:.2f} m) exceeds 45% of wing span",
            "severity": "error"
        })
    
    if location_type == "fuselage" and abs(y_position) > fuselage_diameter * 0.4:
        violations.append({
            "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
            "error": f"Fuselage hardpoint Y position ({y_position:.2f} m) exceeds 40% of fuselage diameter",
            "severity": "warning"
        })
    
    if x_position < fuselage_length * 0.05:
        violations.append({
            "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
            "error": f"Hardpoint position ({x_position:.2f} m) is too close to nose",
            "severity": "warning"
        })
    elif x_position > fuselage_length * 0.95:
        violations.append({
            "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
            "error": f"Hardpoint position ({x_position:.2f} m) is too close to tail",
            "severity": "warning"
        })
    
    if abs(z_position) > fuselage_diameter * 0.5:
        violations.append({
            "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
            "error": f"Hardpoint Z position ({z_position:.2f} m) exceeds 50% of fuselage diameter",
            "severity": "error"
        })
    
    is_primary = hardpoint.get("is_primary", False)
    attachment_type = hardpoint.get("attachment_type", "bolted")
    
    if max_load_kg > 5000.0 and attachment_type in {"clamped", "bonded"}:
        violations.append({
            "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
            "error": f"High-load hardpoint ({max_load_kg:.1f} kg) should use bolted or welded attachment",
            "severity": "warning"
        })
    
    if is_primary and max_load_kg < 1000.0:
        violations.append({
            "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
            "error": "Primary hardpoint should support minimum load of 1000 kg",
            "severity": "warning"
        })
    
    reinforcement = hardpoint.get("reinforcement", False)
    if max_load_kg > 3000.0 and not reinforcement:
        violations.append({
            "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
            "error": f"High-load hardpoint ({max_load_kg:.1f} kg) should be reinforced",
            "severity": "warning"
        })
    
    for other in other_hardpoints:
        if other.get("id") == hardpoint.get("id"):
            continue
        
        ox_rel = other.get("x_rel", 0.5)
        oy_rel = other.get("y_rel", 0.0)
        oz_rel = other.get("z_rel", 0.0)
        
        ox = ox_rel * fuselage_length
        oy = oy_rel * fuselage_diameter / 2
        oz = oz_rel * fuselage_diameter / 2
        
        dx = abs(x_position - ox)
        dy = abs(y_position - oy)
        dz = abs(z_position - oz)
        
        min_separation = 0.2
        
        if dx < min_separation and dy < min_separation and dz < min_separation:
            violations.append({
                "component": f"hardpoint.{hardpoint.get('id', 'unknown')}",
                "error": f"Insufficient separation from {other.get('id', 'unknown')}",
                "severity": "error",
                "distance_x_m": dx,
                "distance_y_m": dy,
                "distance_z_m": dz,
                "required_separation_m": min_separation,
            })
    
    return violations


def validate_hardpoint_station_alignment(
    hardpoint: dict[str, Any],
    stations: list[dict],
    fuselage_length: float,
) -> dict[str, Any]:
    x_rel = hardpoint.get("x_rel", 0.5)
    x_position = x_rel * fuselage_length
    
    aligned_station = None
    min_distance = float("inf")
    
    for station in stations:
        if not isinstance(station, dict):
            continue
        
        sx = station.get("x_m", 0.0)
        distance = abs(x_position - sx)
        
        if distance < min_distance:
            min_distance = distance
            aligned_station = station
    
    return {
        "hardpoint_x_m": x_position,
        "aligned_station_x_m": aligned_station.get("x_m", 0.0) if aligned_station else None,
        "distance_m": min_distance,
        "is_aligned": min_distance < 0.1,
    }


def calculate_hardpoint_stress(
    hardpoint: dict[str, Any],
    fuselage_diameter: float,
    wing_span: float,
    wing_chord: float,
) -> dict[str, float]:
    max_load_kg = hardpoint.get("max_load_kg", 0.0)
    mounting_area_m2 = hardpoint.get("mounting_area_m2", 0.1)
    
    stress_kg_m2 = max_load_kg / mounting_area_m2 if mounting_area_m2 > 0 else 0
    
    hardpoint_type = hardpoint.get("type", "fuselage_frame")
    
    location_type = hardpoint_type
    bending_moment = 0.0
    
    if location_type == "wing":
        bending_moment = max_load_kg * wing_chord / 2.0
    elif location_type == "fuselage":
        bending_moment = max_load_kg * fuselage_diameter / 2.0
    else:
        bending_moment = max_load_kg * 0.5
    
    shear_force = max_load_kg * 9.81
    
    return {
        "stress_kg_m2": stress_kg_m2,
        "bending_moment_Nm": bending_moment * 9.81,
        "shear_force_N": shear_force,
    }


def add_hardpoints_to_stations(
    stations: list[dict],
    hardpoints: list[dict],
    fuselage_length: float,
    fuselage_diameter: float,
) -> list[dict]:
    modified_stations = []
    
    for station in stations:
        if not isinstance(station, dict):
            modified_stations.append(station)
            continue
        
        x = station.get("x_m", 0.0)
        modified_station = station.copy()
        
        station_hardpoints = []
        for hp in hardpoints:
            if not isinstance(hp, dict):
                continue
            
            hx_rel = hp.get("x_rel", 0.5)
            hx = hx_rel * fuselage_length
            tolerance = 0.05 * fuselage_length
            
            if abs(x - hx) < tolerance:
                hy_rel = hp.get("y_rel", 0.0)
                hz_rel = hp.get("z_rel", 0.0)
                hy = hy_rel * fuselage_diameter / 2
                hz = hz_rel * fuselage_diameter / 2
                
                station_hardpoints.append({
                    "id": hp.get("id", "unknown"),
                    "type": hp.get("type", "unknown"),
                    "x_m": hx,
                    "y_m": hy,
                    "z_m": hz,
                    "max_load_kg": hp.get("max_load_kg", 0.0),
                })
        
        if station_hardpoints:
            modified_station["hardpoints"] = station_hardpoints
        
        modified_stations.append(modified_station)
    
    return modified_stations


def generate_hardpoint_recommendations(
    hardpoints: list[dict],
    fuselage_length: float,
    fuselage_diameter: float,
    wing_span: float,
) -> list[dict[str, Any]]:
    recommendations = []
    
    for hp in hardpoints:
        if not isinstance(hp, dict):
            continue
        
        hp_type = hp.get("type", "unknown")
        max_load = hp.get("max_load_kg", 0.0)
        x_rel = hp.get("x_rel", 0.5)
        
        if hp_type == "payload_hook" and x_rel < 0.4:
            recommendations.append({
                "hardpoint_id": hp.get("id", "unknown"),
                "severity": "info",
                "message": "Payload hook should be positioned aft of 40% fuselage length for better CG control",
            })
        
        if hp_type == "engine_mount" and x_rel < 0.2:
            recommendations.append({
                "hardpoint_id": hp.get("id", "unknown"),
                "severity": "info",
                "message": "Engine mount may benefit from moving aft for better CG balance",
            })
        
        if hp_type == "external_store" and max_load > 1500.0:
            reinforcement = hp.get("reinforcement", False)
            if not reinforcement:
                recommendations.append({
                    "hardpoint_id": hp.get("id", "unknown"),
                    "severity": "warning",
                    "message": "External store hardpoint should be reinforced for loads > 1500 kg",
                })
        
        if hp_type == "fuel_tank_mount":
            attachment = hp.get("attachment_type", "bolted")
            if attachment == "clamped":
                recommendations.append({
                    "hardpoint_id": hp.get("id", "unknown"),
                    "severity": "warning",
                    "message": "Fuel tank mounts should use bolted or welded attachment for safety",
                })
        
        is_primary = hp.get("is_primary", False)
        if is_primary and max_load < 2000.0:
            recommendations.append({
                "hardpoint_id": hp.get("id", "unknown"),
                "severity": "info",
                "message": "Consider increasing primary hardpoint capacity for future upgrades",
            })
    
    return recommendations


def validate_load_distribution(
    hardpoints: list[dict],
    total_load_kg: float,
    safety_factor: float = 1.5,
) -> list[dict[str, Any]]:
    violations = []
    
    total_capacity = 0.0
    primary_capacity = 0.0
    
    for hp in hardpoints:
        if not isinstance(hp, dict):
            continue
        
        max_load = hp.get("max_load_kg", 0.0)
        total_capacity += max_load
        
        is_primary = hp.get("is_primary", False)
        if is_primary:
            primary_capacity += max_load
    
    required_capacity = total_load_kg * safety_factor
    
    if total_capacity < required_capacity:
        violations.append({
            "component": "hardpoint_system",
            "error": f"Total hardpoint capacity ({total_capacity:.1f} kg) is below required {required_capacity:.1f} kg",
            "severity": "error",
            "safety_factor": safety_factor,
        })
    
    if primary_capacity < total_load_kg * 0.5:
        violations.append({
            "component": "hardpoint_system",
            "error": f"Primary hardpoint capacity ({primary_capacity:.1f} kg) is below 50% of total load",
            "severity": "warning",
        })
    
    return violations
