
from typing import Optional, Dict
from langchain_core.tools import tool
from aircraft_design.aero_lift_slope import calculate_lift_slope_subsonic, LiftSlopeResult

@tool
def calculate_lift_slope(
    aspect_ratio: float,
    sweep_quarter_chord_deg: float,
    sweep_max_thickness_deg: float,
    mach: float = 0.0,
    fuselage_diameter_m: float = 0.0,
    wing_span_m: float = 0.0,
) -> Dict:
    """
    Calculate the subsonic lift slope (CL_alpha) of a wing.
    
    Args:
        aspect_ratio (float): Wing aspect ratio (b^2/S).
        sweep_quarter_chord_deg (float): Sweep angle at quarter chord in degrees.
        sweep_max_thickness_deg (float): Sweep angle at max thickness line in degrees.
        mach (float): Mach number (default 0.0).
        fuselage_diameter_m (float, optional): Fuselage diameter in meters.
        wing_span_m (float, optional): Wing span in meters.
        
    Returns:
        Dict: Dictionary containing 'cl_alpha' (per radian) and calculation details.
    """
    try:
        result: LiftSlopeResult = calculate_lift_slope_subsonic(
            aspect_ratio=aspect_ratio,
            sweep_quarter_chord_deg=sweep_quarter_chord_deg,
            sweep_max_thickness_deg=sweep_max_thickness_deg,
            mach=mach,
            fuselage_diameter_m=fuselage_diameter_m,
            wing_span_m=wing_span_m
        )
        
        return {
            "cl_alpha": result.cl_alpha,
            "details": result.details
        }
    except Exception as e:
        return {"error": str(e)}
