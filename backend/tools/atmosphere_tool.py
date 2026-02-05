from typing import Dict, Optional
from langchain.tools import tool
from aircraft_design.atmosphere import isa_tropopause

@tool
def calculate_atmosphere(altitude_m: float, delta_t_k: float = 0.0) -> Dict[str, float]:
    """
    Calculate International Standard Atmosphere (ISA) properties for a given altitude.
    
    Args:
        altitude_m: Altitude in meters (geometric height).
        delta_t_k: Temperature offset from standard atmosphere in Kelvin. Default is 0.
        
    Returns:
        Dictionary containing:
        - altitude_m: Input altitude
        - temperature_k: Temperature in Kelvin
        - pressure_pa: Pressure in Pascals
        - density_kg_m3: Density in kg/m^3
        - speed_of_sound_m_s: Speed of sound in m/s
    """
    state = isa_tropopause(h_m=altitude_m, delta_t_k=delta_t_k)
    return {
        "altitude_m": state.h_m,
        "temperature_k": state.t_k,
        "pressure_pa": state.p_pa,
        "density_kg_m3": state.rho_kg_m3,
        "speed_of_sound_m_s": state.a_m_s
    }
