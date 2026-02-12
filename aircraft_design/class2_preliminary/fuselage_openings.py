from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from typing import Any


@dataclass(frozen=True)
class OpeningType:
    name: str
    category: str
    min_size_m2: float
    max_size_m2: float


OPENING_TYPES = [
    OpeningType(name="passenger_door", category="entry", min_size_m2=0.5, max_size_m2=2.0),
    OpeningType(name="cargo_door", category="entry", min_size_m2=0.3, max_size_m2=5.0),
    OpeningType(name="service_door", category="entry", min_size_m2=0.2, max_size_m2=1.0),
    OpeningType(name="cockpit_door", category="entry", min_size_m2=0.3, max_size_m2=0.8),
    OpeningType(name="emergency_exit", category="safety", min_size_m2=0.3, max_size_m2=1.5),
    OpeningType(name="passenger_window", category="vision", min_size_m2=0.05, max_size_m2=0.3),
    OpeningType(name="cockpit_window", category="vision", min_size_m2=0.1, max_size_m2=0.5),
    OpeningType(name="inspection_port", category="maintenance", min_size_m2=0.01, max_size_m2=0.2),
    OpeningType(name="fuel_cap", category="maintenance", min_size_m2=0.01, max_size_m2=0.05),
]


def parse_opening_config(opening_dict: dict, path: str) -> dict[str, Any]:
    if not isinstance(opening_dict, dict):
        raise ValueError(f"{path} must be an object.")
    
    result: dict[str, Any] = {}
    
    opening_type = opening_dict.get("type", "passenger_door").strip().lower()
    valid_types = {ot.name for ot in OPENING_TYPES}
    if opening_type not in valid_types:
        raise ValueError(f"Unknown opening type: {opening_type}")
    result["type"] = opening_type
    
    if "name" in opening_dict:
        result["name"] = str(opening_dict["name"]).strip()
    else:
        result["name"] = opening_type
    
    if "x_rel" in opening_dict:
        val = opening_dict.get("x_rel")
        if not isinstance(val, (int, float)) or val < 0 or val > 1:
            raise ValueError(f"{path}.x_rel must be between 0 and 1.")
        result["x_rel"] = float(val)
    else:
        raise ValueError(f"{path}.x_rel is required.")
    
    if "y_rel" in opening_dict:
        val = opening_dict.get("y_rel")
        if not isinstance(val, (int, float)) or val < -1.0 or val > 1.0:
            raise ValueError(f"{path}.y_rel must be between -1 and 1.")
        result["y_rel"] = float(val)
    else:
        result["y_rel"] = 0.0
    
    if "width_m" in opening_dict:
        val = opening_dict.get("width_m")
        if not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"{path}.width_m must be positive.")
        result["width_m"] = float(val)
    else:
        raise ValueError(f"{path}.width_m is required.")
    
    if "height_m" in opening_dict:
        val = opening_dict.get("height_m")
        if not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"{path}.height_m must be positive.")
        result["height_m"] = float(val)
    else:
        raise ValueError(f"{path}.height_m is required.")
    
    if "orientation" in opening_dict:
        orientation = str(opening_dict["orientation"]).strip().lower()
        if orientation not in {"horizontal", "vertical", "radial"}:
            raise ValueError(f"{path}.orientation must be horizontal, vertical, or radial.")
        result["orientation"] = orientation
    else:
        result["orientation"] = "vertical"
    
    if "is_retractable" in opening_dict:
        if not isinstance(opening_dict["is_retractable"], bool):
            raise ValueError(f"{path}.is_retractable must be a boolean.")
        result["is_retractable"] = opening_dict["is_retractable"]
    else:
        result["is_retractable"] = False
    
    if "has_emergency_release" in opening_dict:
        if not isinstance(opening_dict["has_emergency_release"], bool):
            raise ValueError(f"{path}.has_emergency_release must be a boolean.")
        result["has_emergency_release"] = opening_dict["has_emergency_release"]
    
    if "hardpoint_id" in opening_dict:
        result["hardpoint_id"] = str(opening_dict["hardpoint_id"]).strip()
    
    if "frame_material" in opening_dict:
        result["frame_material"] = str(opening_dict["frame_material"]).strip()
    
    if "glass_type" in opening_dict:
        result["glass_type"] = str(opening_dict["glass_type"]).strip()
    
    if "opening_mechanism" in opening_dict:
        mechanism = str(opening_dict["opening_mechanism"]).strip().lower()
        if mechanism not in {"hinge", "sliding", "plug", "blowout"}:
            raise ValueError(f"{path}.opening_mechanism must be hinge, sliding, plug, or blowout.")
        result["opening_mechanism"] = mechanism
    
    return result


def validate_opening_config(
    opening: dict[str, Any],
    fuselage_length: float,
    fuselage_diameter: float,
    stations: list[dict],
) -> list[dict[str, Any]]:
    violations = []
    
    x_rel = opening.get("x_rel", 0.5)
    y_rel = opening.get("y_rel", 0.0)
    width_m = opening.get("width_m", 1.0)
    height_m = opening.get("height_m", 1.5)
    
    x_position = x_rel * fuselage_length
    y_position = y_rel * fuselage_diameter / 2
    
    opening_area = width_m * height_m
    
    opening_type = opening.get("type", "passenger_door")
    opening_info = next((ot for ot in OPENING_TYPES if ot.name == opening_type), None)
    
    if opening_info:
        if opening_area < opening_info.min_size_m2:
            violations.append({
                "component": f"opening.{opening.get('name', 'unknown')}",
                "error": f"Opening area ({opening_area:.2f} m²) is below minimum {opening_info.min_size_m2:.2f} m²",
                "severity": "error"
            })
        elif opening_area > opening_info.max_size_m2:
            violations.append({
                "component": f"opening.{opening.get('name', 'unknown')}",
                "error": f"Opening area ({opening_area:.2f} m²) exceeds maximum {opening_info.max_size_m2:.2f} m²",
                "severity": "error"
            })
    
    if width_m > fuselage_diameter * pi * 0.5:
        violations.append({
            "component": f"opening.{opening.get('name', 'unknown')}",
            "error": f"Opening width ({width_m:.2f} m) exceeds half fuselage circumference",
            "severity": "error"
        })
    
    if height_m > fuselage_diameter * 0.8:
        violations.append({
            "component": f"opening.{opening.get('name', 'unknown')}",
            "error": f"Opening height ({height_m:.2f} m) exceeds 80% of fuselage diameter",
            "severity": "error"
        })
    
    if x_position < 0.5:
        violations.append({
            "component": f"opening.{opening.get('name', 'unknown')}",
            "error": f"Opening position ({x_position:.2f} m) is too close to nose",
            "severity": "warning"
        })
    elif x_position > fuselage_length * 0.9:
        violations.append({
            "component": f"opening.{opening.get('name', 'unknown')}",
            "error": f"Opening position ({x_position:.2f} m) is too close to tail",
            "severity": "warning"
        })
    
    is_retractable = opening.get("is_retractable", False)
    if opening_type == "passenger_door" and not is_retractable:
        violations.append({
            "component": f"opening.{opening.get('name', 'unknown')}",
            "error": "Passenger door should be retractable for ground operations",
            "severity": "warning"
        })
    
    has_emergency_release = opening.get("has_emergency_release")
    if opening_type in {"passenger_door", "emergency_exit"} and has_emergency_release is False:
        violations.append({
            "component": f"opening.{opening.get('name', 'unknown')}",
            "error": "Safety-critical doors should have emergency release",
            "severity": "error"
        })
    
    hardpoint_id = opening.get("hardpoint_id")
    if hardpoint_id:
        hardpoint_valid = check_hardpoint_exists(hardpoint_id, stations)
        if not hardpoint_valid:
            violations.append({
                "component": f"opening.{opening.get('name', 'unknown')}",
                "error": f"Hard point {hardpoint_id} not found in structure",
                "severity": "error"
            })
    
    return violations


def check_hardpoint_exists(hardpoint_id: str, stations: list[dict]) -> bool:
    for station in stations:
        if not isinstance(station, dict):
            continue
        hps = station.get("hardpoints", [])
        if isinstance(hps, list):
            for hp in hps:
                if isinstance(hp, dict) and hp.get("id") == hardpoint_id:
                    return True
    return False


def calculate_opening_weight(
    opening: dict[str, Any],
    fuselage_diameter: float,
    glass_density_kg_m3: float = 2500.0,
    frame_density_kg_m3: float = 2700.0,
) -> dict[str, float]:
    width_m = opening.get("width_m", 1.0)
    height_m = opening.get("height_m", 1.5)
    
    opening_area = width_m * height_m
    opening_type = opening.get("type", "passenger_door")
    
    if "window" in opening_type:
        glass_thickness_mm = opening.get("glass_thickness_mm", 8.0) / 1000.0
        glass_area = opening_area * 0.9
        glass_volume = glass_area * glass_thickness_mm
        glass_weight = glass_volume * glass_density_kg_m3
        
        frame_thickness_mm = opening.get("frame_thickness_mm", 25.0) / 1000.0
        frame_area = opening_area * 0.15
        frame_volume = frame_area * frame_thickness_mm
        frame_weight = frame_volume * frame_density_kg_m3
        
        total_weight = glass_weight + frame_weight
    else:
        door_thickness_mm = opening.get("door_thickness_mm", 20.0) / 1000.0
        door_area = opening_area * 1.1
        
        frame_thickness_mm = opening.get("frame_thickness_mm", 50.0) / 1000.0
        frame_area = opening_area * 0.2
        
        door_volume = door_area * door_thickness_mm
        door_weight = door_volume * frame_density_kg_m3
        
        frame_volume = frame_area * frame_thickness_mm
        frame_weight = frame_volume * frame_density_kg_m3
        
        mechanism_weight = opening_area * 15.0
        
        total_weight = door_weight + frame_weight + mechanism_weight
    
    return {
        "opening_area_m2": opening_area,
        "weight_kg": total_weight,
    }


def apply_openings_to_stations(
    stations: list[dict],
    openings: list[dict],
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
        
        for opening in openings:
            if not isinstance(opening, dict):
                continue
            
            ox_rel = opening.get("x_rel", 0.5)
            ox = ox_rel * fuselage_length
            width_m = opening.get("width_m", 1.0)
            height_m = opening.get("height_m", 1.5)
            
            x_start = ox - width_m / 2
            x_end = ox + width_m / 2
            
            if x_start <= x <= x_end:
                modified_station["has_opening"] = True
                modified_station["opening_type"] = opening.get("type", "unknown")
                modified_station["opening_width_m"] = width_m
                modified_station["opening_height_m"] = height_m
                break
        
        modified_stations.append(modified_station)
    
    return modified_stations


def generate_opening_geometry(
    opening: dict[str, Any],
    fuselage_length: float,
    fuselage_diameter: float,
    num_points: int = 21,
) -> dict[str, Any]:
    x_rel = opening.get("x_rel", 0.5)
    y_rel = opening.get("y_rel", 0.0)
    width_m = opening.get("width_m", 1.0)
    height_m = opening.get("height_m", 1.5)
    orientation = opening.get("orientation", "vertical")
    
    x = x_rel * fuselage_length
    y = y_rel * fuselage_diameter / 2
    z = 0.0
    
    points = []
    for i in range(num_points):
        if orientation == "vertical":
            u = i / (num_points - 1)
            px = x
            py = y - width_m / 2 + u * width_m
            pz = z - height_m / 2 + u * height_m
        elif orientation == "horizontal":
            u = i / (num_points - 1)
            px = x - width_m / 2 + u * width_m
            py = y
            pz = z - height_m / 2 + u * height_m
        else:
            theta = 2 * pi * i / num_points
            px = x
            py = y + width_m / 2 * cos(theta)
            pz = z + height_m / 2 * sin(theta)
        
        points.append({
            "x_m": px,
            "y_m": py,
            "z_m": pz,
        })
    
    return {
        "center_x_m": x,
        "center_y_m": y,
        "center_z_m": z,
        "width_m": width_m,
        "height_m": height_m,
        "orientation": orientation,
        "points": points,
    }


def validate_opening_clearance(
    opening: dict[str, Any],
    other_openings: list[dict],
    fuselage_length: float,
    fuselage_diameter: float,
    min_clearance_m: float = 0.1,
) -> list[dict[str, Any]]:
    violations = []
    
    x_rel = opening.get("x_rel", 0.5)
    y_rel = opening.get("y_rel", 0.0)
    width_m = opening.get("width_m", 1.0)
    height_m = opening.get("height_m", 1.5)
    
    x = x_rel * fuselage_length
    y = y_rel * fuselage_diameter / 2
    
    for other in other_openings:
        if other.get("name") == opening.get("name"):
            continue
        
        ox_rel = other.get("x_rel", 0.5)
        oy_rel = other.get("y_rel", 0.0)
        owidth_m = other.get("width_m", 1.0)
        oheight_m = other.get("height_m", 1.5)
        
        ox = ox_rel * fuselage_length
        oy = oy_rel * fuselage_diameter / 2
        
        dx = abs(x - ox)
        dy = abs(y - oy)
        
        min_x_dist = (width_m + owidth_m) / 2 + min_clearance_m
        min_y_dist = (height_m + oheight_m) / 2 + min_clearance_m
        
        if dx < min_x_dist and dy < min_y_dist:
            violations.append({
                "component": f"opening.{opening.get('name', 'unknown')}",
                "error": f"Insufficient clearance to {other.get('name', 'unknown')}",
                "severity": "error",
                "distance_x_m": dx,
                "distance_y_m": dy,
                "required_x_m": min_x_dist,
                "required_y_m": min_y_dist,
            })
    
    return violations
