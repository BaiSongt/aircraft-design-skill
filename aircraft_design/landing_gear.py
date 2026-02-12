from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LandingGearType:
    name: str
    category: str
    num_wheels: int
    is_retractable: bool


LANDING_GEAR_TYPES = [
    LandingGearType(name="fixed", category="simple", num_wheels=2, is_retractable=False),
    LandingGearType(name="tricycle", category="standard", num_wheels=3, is_retractable=True),
    LandingGearType(name="conventional", category="taildragger", num_wheels=3, is_retractable=True),
    LandingGearType(name="bicycle", category="special", num_wheels=2, is_retractable=True),
]


DEFAULT_LANDING_GEAR_CONFIGS = {
    "fixed": {
        "type": "fixed",
        "is_retractable": False,
        "main_wheel_track_ratio": 0.15,
        "main_wheel_cg_offset_x": 0.05,
        "description": "Fixed landing gear for light aircraft",
    },
    "tricycle": {
        "type": "tricycle",
        "is_retractable": True,
        "main_wheel_track_ratio": 0.15,
        "main_wheel_cg_offset_x": 0.05,
        "nose_wheel_cg_offset_x": -0.15,
        "nose_wheel_load_ratio": 0.08,
        "description": "Standard tricycle landing gear",
    },
    "conventional": {
        "type": "conventional",
        "is_retractable": True,
        "main_wheel_track_ratio": 0.12,
        "main_wheel_cg_offset_x": 0.02,
        "tail_wheel_cg_offset_x": -0.35,
        "tail_wheel_load_ratio": 0.03,
        "description": "Tailwheel/conventional landing gear",
    },
}


def parse_landing_gear(gear_dict: dict, path: str) -> dict[str, Any]:
    if not isinstance(gear_dict, dict):
        raise ValueError(f"{path}.landing_gear must be an object.")

    result: dict[str, Any] = {}

    gear_type = gear_dict.get("type", "tricycle").strip().lower()
    if gear_type not in {"fixed", "tricycle", "conventional", "bicycle"}:
        raise ValueError(f"Unknown landing gear type: {gear_type}")
    result["type"] = gear_type

    base_config = DEFAULT_LANDING_GEAR_CONFIGS.get(gear_type, {})

    if "is_retractable" in gear_dict:
        val = gear_dict.get("is_retractable")
        if not isinstance(val, bool):
            raise ValueError(f"{path}.is_retractable must be a boolean.")
        result["is_retractable"] = val
    else:
        result["is_retractable"] = base_config.get("is_retractable", True)

    if "main_wheels" in gear_dict:
        main_wheels = gear_dict["main_wheels"]
        if not isinstance(main_wheels, dict):
            raise ValueError(f"{path}.main_wheels must be an object.")

        main_result = {}

        if "num_wheels" in main_wheels:
            val = main_wheels["num_wheels"]
            if not isinstance(val, int) or val < 2:
                raise ValueError(f"{path}.main_wheels.num_wheels must be an integer >= 2.")
            main_result["num_wheels"] = val
        else:
            main_result["num_wheels"] = 2

        if "x_offset_m" in main_wheels:
            val = main_wheels["x_offset_m"]
            if val is not None:
                main_result["x_offset_m"] = None
            elif not isinstance(val, (int, float)):
                raise ValueError(f"{path}.main_wheels.x_offset_m must be numeric.")
            else:
                main_result["x_offset_m"] = float(val)
        else:
            main_result["x_offset_m"] = base_config.get("main_wheel_cg_offset_x", 0.05)

        if "y_offset_m" in main_wheels:
            val = main_wheels["y_offset_m"]
            if val is not None:
                main_result["y_offset_m"] = None
            elif not isinstance(val, (int, float)):
                raise ValueError(f"{path}.main_wheels.y_offset_m must be numeric.")
            else:
                main_result["y_offset_m"] = float(val)

        if "z_offset_m" in main_wheels:
            val = main_wheels["z_offset_m"]
            if val is not None:
                main_result["z_offset_m"] = None
            elif not isinstance(val, (int, float)):
                raise ValueError(f"{path}.main_wheels.z_offset_m must be numeric.")
            else:
                main_result["z_offset_m"] = float(val)
        else:
            main_result["z_offset_m"] = 0.0

        if "track_m" in main_wheels:
            val = main_wheels["track_m"]
            if val is not None:
                main_result["track_m"] = None
            elif not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(f"{path}.main_wheels.track_m must be positive.")
            else:
                main_result["track_m"] = float(val)

        if "diameter_m" in main_wheels:
            val = main_wheels["diameter_m"]
            if val is not None:
                main_result["diameter_m"] = None
            elif not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(f"{path}.main_wheels.diameter_m must be positive.")
            else:
                main_result["diameter_m"] = float(val)

        result["main_wheels"] = main_result
    else:
        result["main_wheels"] = {
            "num_wheels": 2,
            "x_offset_m": base_config.get("main_wheel_cg_offset_x", 0.05),
            "y_offset_m": 0.0,
            "z_offset_m": 0.0,
        }

    if gear_type in {"tricycle", "conventional"}:
        nose_or_tail_key = "nose_wheel" if gear_type == "tricycle" else "tail_wheel"
        base_offset_key = "nose_wheel_cg_offset_x" if gear_type == "tricycle" else "tail_wheel_cg_offset_x"

        if nose_or_tail_key in gear_dict:
            wheel_dict = gear_dict[nose_or_tail_key]
            if not isinstance(wheel_dict, dict):
                raise ValueError(f"{path}.{nose_or_tail_key} must be an object.")

            wheel_result = {}

            if "x_offset_m" in wheel_dict:
                val = wheel_dict["x_offset_m"]
                if val is not None:
                    wheel_result["x_offset_m"] = None
                elif not isinstance(val, (int, float)):
                    raise ValueError(f"{path}.{nose_or_tail_key}.x_offset_m must be numeric.")
                else:
                    wheel_result["x_offset_m"] = float(val)
            else:
                wheel_result["x_offset_m"] = base_config.get(base_offset_key, -0.15)

            if "y_offset_m" in wheel_dict:
                val = wheel_dict["y_offset_m"]
                if val is not None:
                    wheel_result["y_offset_m"] = None
                elif not isinstance(val, (int, float)):
                    raise ValueError(f"{path}.{nose_or_tail_key}.y_offset_m must be numeric.")
                else:
                    wheel_result["y_offset_m"] = float(val)
            else:
                wheel_result["y_offset_m"] = 0.0

            if "z_offset_m" in wheel_dict:
                val = wheel_dict["z_offset_m"]
                if val is not None:
                    wheel_result["z_offset_m"] = None
                elif not isinstance(val, (int, float)):
                    raise ValueError(f"{path}.{nose_or_tail_key}.z_offset_m must be numeric.")
                else:
                    wheel_result["z_offset_m"] = float(val)
            else:
                wheel_result["z_offset_m"] = 0.0

            if "diameter_m" in wheel_dict:
                val = wheel_dict["diameter_m"]
                if val is not None:
                    wheel_result["diameter_m"] = None
                elif not isinstance(val, (int, float)) or val <= 0:
                    raise ValueError(f"{path}.{nose_or_tail_key}.diameter_m must be positive.")
                else:
                    wheel_result["diameter_m"] = float(val)

            result[nose_or_tail_key] = wheel_result

    if "strut_length_m" in gear_dict:
        val = gear_dict["strut_length_m"]
        if val is not None:
            result["strut_length_m"] = None
        elif not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"{path}.strut_length_m must be positive.")
        else:
            result["strut_length_m"] = float(val)

    if "shock_absorber" in gear_dict:
        val = gear_dict["shock_absorber"]
        if not isinstance(val, str) or val.lower() not in {"oleo", "rubber", "spring", "air", "hydraulic"}:
            raise ValueError(f"{path}.shock_absorber must be one of: oleo, rubber, spring, air, hydraulic")
        result["shock_absorber"] = val.lower()

    if "tire_pressure_bar" in gear_dict:
        val = gear_dict["tire_pressure_bar"]
        if val is not None:
            result["tire_pressure_bar"] = None
        elif not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"{path}.tire_pressure_bar must be positive.")
        else:
            result["tire_pressure_bar"] = float(val)

    return result


def validate_landing_gear(
    gear: dict[str, Any],
    fuselage_length: float,
    wing_span: float,
    mtow_kg: float,
) -> list[dict[str, Any]]:
    violations = []

    gear_type = gear.get("type", "unknown")

    main_wheels = gear.get("main_wheels", {})
    track_m = main_wheels.get("track_m")

    if track_m is not None:
        if track_m < wing_span * 0.05:
            violations.append({
                "component": "landing_gear",
                "error": f"Main wheel track ({track_m:.2f} m) is less than 5% of wing span",
                "severity": "warning"
            })
        elif track_m > wing_span * 0.3:
            violations.append({
                "component": "landing_gear",
                "error": f"Main wheel track ({track_m:.2f} m) is more than 30% of wing span",
                "severity": "warning"
            })

    main_x_offset = main_wheels.get("x_offset_m", 0.0)
    main_diameter = main_wheels.get("diameter_m", 0.5)
    strut_length = gear.get("strut_length_m", main_diameter * 1.5)

    main_z_ground = -main_diameter / 2 - strut_length
    main_x_position = main_x_offset * fuselage_length

    if gear_type == "tricycle":
        nose_wheel = gear.get("nose_wheel", {})
        nose_x_offset = nose_wheel.get("x_offset_m", -0.15)
        nose_diameter = nose_wheel.get("diameter_m", 0.4)

        nose_x_position = nose_x_offset * fuselage_length

        wheelbase = abs(nose_x_position - main_x_position)

        if wheelbase < fuselage_length * 0.2:
            violations.append({
                "component": "landing_gear",
                "error": f"Wheelbase ({wheelbase:.2f} m) is less than 20% of fuselage length",
                "severity": "warning"
            })
        elif wheelbase > fuselage_length * 0.4:
            violations.append({
                "component": "landing_gear",
                "error": f"Wheelbase ({wheelbase:.2f} m) is more than 40% of fuselage length",
                "severity": "warning"
            })

        static_margin = nose_x_position - main_x_position

        if static_margin < 0:
            violations.append({
                "component": "landing_gear",
                "error": f"Static margin ({static_margin:.2f} m) is negative, aircraft may tip forward",
                "severity": "error"
            })

        nose_load_ratio = gear.get("nose_wheel_load_ratio", 0.08)
        if nose_load_ratio < 0.05:
            violations.append({
                "component": "landing_gear",
                "error": f"Nose wheel load ratio ({nose_load_ratio:.2%}) is below recommended 5%",
                "severity": "warning"
            })
        elif nose_load_ratio > 0.15:
            violations.append({
                "component": "landing_gear",
                "error": f"Nose wheel load ratio ({nose_load_ratio:.2%}) is above recommended 15%",
                "severity": "warning"
            })

    elif gear_type == "conventional":
        tail_wheel = gear.get("tail_wheel", {})
        tail_x_offset = tail_wheel.get("x_offset_m", -0.35)
        tail_diameter = tail_wheel.get("diameter_m", 0.3)

        tail_x_position = tail_x_offset * fuselage_length

        wheelbase = abs(tail_x_position - main_x_position)

        if wheelbase < fuselage_length * 0.25:
            violations.append({
                "component": "landing_gear",
                "error": f"Wheelbase ({wheelbase:.2f} m) is less than 25% of fuselage length",
                "severity": "warning"
            })

        tail_to_cg_ratio = abs(tail_x_position) / fuselage_length
        if tail_to_cg_ratio < 0.2:
            violations.append({
                "component": "landing_gear",
                "error": f"Tail wheel position ({tail_x_position:.2f} m) is too close to CG",
                "severity": "warning"
            })

    if gear.get("is_retractable"):
        bay_depth = strut_length + main_diameter * 0.5
        if bay_depth > fuselage_length * 0.08:
            violations.append({
                "component": "landing_gear",
                "error": f"Landing gear bay depth ({bay_depth:.2f} m) is more than 8% of fuselage length",
                "severity": "warning"
            })

    return violations


def calculate_landing_gear_weight(
    gear: dict[str, Any],
    mtow_kg: float,
) -> dict[str, float]:
    gear_type = gear.get("type", "tricycle")
    is_retractable = gear.get("is_retractable", False)

    if gear_type == "fixed":
        base_weight_ratio = 0.015
    else:
        base_weight_ratio = 0.025

    if is_retractable:
        retractable_factor = 1.5
    else:
        retractable_factor = 1.0

    gear_weight = mtow_kg * base_weight_ratio * retractable_factor

    return {
        "landing_gear_weight_kg": gear_weight,
        "weight_ratio": gear_weight / mtow_kg,
        "type": gear_type,
        "is_retractable": is_retractable,
    }


def get_ground_clearance(
    gear: dict[str, Any],
    fuselage_diameter: float,
) -> dict[str, float]:
    main_wheels = gear.get("main_wheels", {})
    main_diameter = main_wheels.get("diameter_m", 0.5)
    strut_length = gear.get("strut_length_m", main_diameter * 1.5)

    main_wheel_ground_z = -main_diameter / 2 - strut_length

    fuselage_ground_clearance = abs(main_wheel_ground_z) - fuselage_diameter / 2

    return {
        "fuselage_ground_clearance_m": fuselage_ground_clearance,
        "main_wheel_z_m": main_wheel_ground_z,
        "minimum_clearance_required_m": fuselage_diameter * 0.1,
    }
