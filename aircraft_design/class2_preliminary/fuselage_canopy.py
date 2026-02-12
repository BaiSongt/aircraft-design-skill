from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CanopyType:
    name: str
    category: str


CANOPY_TYPES = [
    CanopyType(name="bubble", category="convex"),
    CanopyType(name="razorback", category="flat"),
    CanopyType(name="teardrop", category="streamlined"),
    CanopyType(name="fighter", category="stepped"),
    CanopyType(name="slab", category="flat"),
]


DEFAULT_CANOPY_CONFIGS = {
    "bubble": {
        "type": "bubble",
        "shape": "ellipsoidal",
        "length_fraction": 0.25,
        "width_fraction": 0.8,
        "height_fraction": 0.5,
        "curvature": 0.6,
        "description": "Bubble canopy with good visibility",
    },
    "razorback": {
        "type": "razorback",
        "shape": "flat",
        "length_fraction": 0.3,
        "width_fraction": 0.7,
        "height_fraction": 0.4,
        "curvature": 0.2,
        "description": "Razorback canopy with flat top",
    },
    "teardrop": {
        "type": "teardrop",
        "shape": "streamlined",
        "length_fraction": 0.35,
        "width_fraction": 0.6,
        "height_fraction": 0.45,
        "curvature": 0.8,
        "description": "Teardrop canopy for low drag",
    },
    "fighter": {
        "type": "fighter",
        "shape": "stepped",
        "length_fraction": 0.4,
        "width_fraction": 0.5,
        "height_fraction": 0.35,
        "curvature": 0.4,
        "description": "Fighter-style stepped canopy",
    },
}


def parse_canopy_config(canopy_dict: dict, path: str) -> dict[str, Any]:
    if not isinstance(canopy_dict, dict):
        raise ValueError(f"{path}.canopy must be an object.")
    
    result: dict[str, Any] = {}
    
    canopy_type = canopy_dict.get("type", "bubble").strip().lower()
    if canopy_type not in {"bubble", "razorback", "teardrop", "fighter", "slab"}:
        raise ValueError(f"Unknown canopy type: {canopy_type}")
    result["type"] = canopy_type
    
    base_config = DEFAULT_CANOPY_CONFIGS.get(canopy_type, {})
    
    if "x_start_rel" in canopy_dict:
        val = canopy_dict.get("x_start_rel")
        if not isinstance(val, (int, float)) or val < 0 or val > 1:
            raise ValueError(f"{path}.x_start_rel must be between 0 and 1.")
        result["x_start_rel"] = float(val)
    else:
        result["x_start_rel"] = 0.0
    
    if "length_fraction" in canopy_dict:
        val = canopy_dict.get("length_fraction")
        if not isinstance(val, (int, float)) or val <= 0 or val > 0.6:
            raise ValueError(f"{path}.length_fraction must be between 0 and 0.6.")
        result["length_fraction"] = float(val)
    else:
        result["length_fraction"] = base_config.get("length_fraction", 0.25)
    
    if "width_fraction" in canopy_dict:
        val = canopy_dict.get("width_fraction")
        if not isinstance(val, (int, float)) or val <= 0 or val > 1.0:
            raise ValueError(f"{path}.width_fraction must be between 0 and 1.")
        result["width_fraction"] = float(val)
    else:
        result["width_fraction"] = base_config.get("width_fraction", 0.8)
    
    if "height_fraction" in canopy_dict:
        val = canopy_dict.get("height_fraction")
        if not isinstance(val, (int, float)) or val <= 0 or val > 1.0:
            raise ValueError(f"{path}.height_fraction must be between 0 and 1.")
        result["height_fraction"] = float(val)
    else:
        result["height_fraction"] = base_config.get("height_fraction", 0.5)
    
    if "curvature" in canopy_dict:
        val = canopy_dict.get("curvature")
        if not isinstance(val, (int, float)) or val < 0 or val > 1.0:
            raise ValueError(f"{path}.curvature must be between 0 and 1.")
        result["curvature"] = float(val)
    else:
        result["curvature"] = base_config.get("curvature", 0.6)
    
    if "y_offset_m" in canopy_dict:
        val = canopy_dict.get("y_offset_m")
        if not isinstance(val, (int, float)):
            raise ValueError(f"{path}.y_offset_m must be numeric.")
        result["y_offset_m"] = float(val)
    else:
        result["y_offset_m"] = 0.0
    
    if "glass_thickness_mm" in canopy_dict:
        val = canopy_dict.get("glass_thickness_mm")
        if val is not None:
            result["glass_thickness_mm"] = None
        elif not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"{path}.glass_thickness_mm must be positive.")
        else:
            result["glass_thickness_mm"] = float(val)
    
    if "frame_material" in canopy_dict:
        result["frame_material"] = str(canopy_dict["frame_material"]).strip()
    
    if "has_wiper" in canopy_dict:
        if not isinstance(canopy_dict["has_wiper"], bool):
            raise ValueError(f"{path}.has_wiper must be a boolean.")
        result["has_wiper"] = canopy_dict["has_wiper"]
    
    if "num_panes" in canopy_dict:
        val = canopy_dict["num_panes"]
        if not isinstance(val, int) or val < 1:
            raise ValueError(f"{path}.num_panes must be a positive integer.")
        result["num_panes"] = val
    
    return result


def validate_canopy_config(
    canopy: dict[str, Any],
    fuselage_length: float,
    fuselage_diameter: float,
) -> list[dict[str, Any]]:
    violations = []
    
    length_fraction = canopy.get("length_fraction", 0.25)
    width_fraction = canopy.get("width_fraction", 0.8)
    height_fraction = canopy.get("height_fraction", 0.5)
    
    canopy_length = fuselage_length * length_fraction
    canopy_width = fuselage_diameter * width_fraction
    canopy_height = fuselage_diameter * height_fraction
    
    if canopy_length < 0.5:
        violations.append({
            "component": "canopy",
            "error": f"Canopy length ({canopy_length:.2f} m) is too short for pilot visibility",
            "severity": "warning"
        })
    elif canopy_length > fuselage_length * 0.5:
        violations.append({
            "component": "canopy",
            "error": f"Canopy length ({canopy_length:.2f} m) exceeds 50% of fuselage length",
            "severity": "warning"
        })
    
    if canopy_width < fuselage_diameter * 0.5:
        violations.append({
            "component": "canopy",
            "error": f"Canopy width ({canopy_width:.2f} m) is less than 50% of fuselage diameter",
            "severity": "warning"
        })
    
    if canopy_height < fuselage_diameter * 0.3:
        violations.append({
            "component": "canopy",
            "error": f"Canopy height ({canopy_height:.2f} m) is less than 30% of fuselage diameter",
            "severity": "warning"
        })
    
    curvature = canopy.get("curvature", 0.6)
    if curvature > 0.8:
        violations.append({
            "component": "canopy",
            "error": f"Canopy curvature ({curvature:.2f}) may cause optical distortion",
            "severity": "warning"
        })
    
    x_start_rel = canopy.get("x_start_rel", 0.0)
    if x_start_rel > 0.15:
        violations.append({
            "component": "canopy",
            "error": f"Canopy position ({x_start_rel:.2%}) may affect forward visibility",
            "severity": "warning"
        })
    
    return violations


def apply_canopy_to_stations(
    stations: list[dict],
    canopy: dict[str, Any],
    fuselage_length: float,
) -> list[dict]:
    x_start_rel = canopy.get("x_start_rel", 0.0)
    length_fraction = canopy.get("length_fraction", 0.25)
    width_fraction = canopy.get("width_fraction", 0.8)
    height_fraction = canopy.get("height_fraction", 0.5)
    curvature = canopy.get("curvature", 0.6)
    y_offset_m = canopy.get("y_offset_m", 0.0)
    
    x_start = x_start_rel * fuselage_length
    x_end = x_start + length_fraction * fuselage_length
    
    canopy_stations = []
    for station in stations:
        if not isinstance(station, dict):
            continue
        
        x = station.get("x_m", 0.0)
        
        if x_start <= x <= x_end:
            progress = (x - x_start) / (x_end - x_start) if x_end > x_start else 0.0
            
            canopy_height_factor = height_fraction * (1.0 - 4.0 * curvature * (progress - 0.5) ** 2)
            canopy_height_factor = max(0.0, canopy_height_factor)
            
            radius_y = station.get("radius_y_m", 0.0)
            radius_z = station.get("radius_z_m", 0.0)
            
            new_radius_y = radius_y * (1.0 + canopy_height_factor * 0.5)
            new_radius_z = radius_z + radius_z * canopy_height_factor
            
            new_station = station.copy()
            new_station["radius_y_m"] = new_radius_y + y_offset_m
            new_station["radius_z_m"] = new_radius_z
            new_station["canopy_height_factor"] = canopy_height_factor
            
            canopy_stations.append(new_station)
        else:
            canopy_stations.append(station)
    
    return canopy_stations


def calculate_canopy_geometry(
    canopy: dict[str, Any],
    fuselage_length: float,
    fuselage_diameter: float,
    num_points: int = 21,
) -> dict[str, Any]:
    x_start_rel = canopy.get("x_start_rel", 0.0)
    length_fraction = canopy.get("length_fraction", 0.25)
    width_fraction = canopy.get("width_fraction", 0.8)
    height_fraction = canopy.get("height_fraction", 0.5)
    curvature = canopy.get("curvature", 0.6)
    
    x_start = x_start_rel * fuselage_length
    x_end = x_start + length_fraction * fuselage_length
    canopy_length = x_end - x_start
    canopy_width = fuselage_diameter * width_fraction
    canopy_height = fuselage_diameter * height_fraction
    
    points = []
    for i in range(num_points):
        x_rel = i / (num_points - 1)
        x = x_start + x_rel * canopy_length
        
        z_rel = 1.0 - 4.0 * curvature * (x_rel - 0.5) ** 2
        z_rel = max(0.0, z_rel)
        
        y_rel = (1.0 - x_rel ** 2) ** 0.5
        
        points.append({
            "x_m": x,
            "y_m": y_rel * canopy_width / 2,
            "z_m": z_rel * canopy_height,
        })
    
    return {
        "x_start_m": x_start,
        "x_end_m": x_end,
        "length_m": canopy_length,
        "width_m": canopy_width,
        "height_m": canopy_height,
        "curvature": curvature,
        "points": points,
    }


def calculate_canopy_weight(
    canopy: dict[str, Any],
    fuselage_diameter: float,
    fuselage_length: float,
    glass_density_kg_m3: float = 2500.0,
) -> dict[str, float]:
    width_fraction = canopy.get("width_fraction", 0.8)
    height_fraction = canopy.get("height_fraction", 0.5)
    length_fraction = canopy.get("length_fraction", 0.25)
    
    canopy_width = fuselage_diameter * width_fraction
    canopy_height = fuselage_diameter * height_fraction
    canopy_length = fuselage_length * length_fraction
    
    glass_thickness_mm = canopy.get("glass_thickness_mm", 10.0) / 1000.0
    
    surface_area = 3.14159 * canopy_width / 2 * canopy_length * 1.5
    
    glass_volume = surface_area * glass_thickness_mm
    glass_weight = glass_volume * glass_density_kg_m3
    
    frame_weight_ratio = 0.15
    frame_weight = glass_weight * frame_weight_ratio
    
    total_weight = glass_weight + frame_weight
    
    return {
        "glass_weight_kg": glass_weight,
        "frame_weight_kg": frame_weight,
        "total_weight_kg": total_weight,
        "surface_area_m2": surface_area,
    }
