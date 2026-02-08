
import json
import math
from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design
from aircraft_design.atmosphere import isa_tropopause
from aircraft_design.units import CONST


def generate_j58_map():
    machs = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.2, 3.5, 4.0, 5.0]
    alts = [0, 5000, 10000, 15000, 20000, 25000, 30000, 40000] # meters
    
    values = []
    t_sl = 150000.0 # 150 kN
    
    for m in machs:
        row = []
        for h in alts:
            atm = isa_tropopause(h)
            sigma = atm.rho_kg_m3 / CONST.rho0_kg_m3
            
            # Mach effect (Ram recovery)
            # T ~ sigma * (1 + 0.6 * M^2)
            # Cutoff > 3.5
            mach_factor = 1.0 + 0.6 * (m**2)
            if m > 3.5:
                mach_factor *= max(0.0, 1.0 - (m - 3.5))
            
            t = t_sl * sigma * mach_factor
            row.append(t)
        values.append(row)
        
    return {
        "mach_points": machs,
        "altitude_points_m": alts,
        "values": values
    }


def run_mach4_design():
    print("Running Mach 4 Hypersonic Concept Design...")
    
    # Inputs for a Mach 4 Recon/Strike Aircraft (SR-71 class but modernized)
    cruise_mach = 4.0
    cruise_altitude_m = 26000.0
    
    # Calculate cruise speed from Mach and Altitude
    atm = isa_tropopause(cruise_altitude_m)
    cruise_speed_m_s = cruise_mach * atm.a_m_s
    
    pmap = generate_j58_map()
    
    inputs = {
        "mission": {
            "cruise_mach": cruise_mach,
            "cruise_altitude_m": cruise_altitude_m,  # 85,000 ft
            "cruise_speed_m_s": cruise_speed_m_s,
            "range_m": 5000000.0,  # 5000 km
            "reserve_fuel_fraction": 0.05,
            "v_stall_m_s": 80.0, # Landing speed constraint
            "v_climb_m_s": 300.0, # High speed climb to avoid induced drag penalty
            "assumed_climb_rate_m_s": 60.0 # Realistic for Mach 4 aircraft
        },
        "payload": {
            "payload_kg": 2000.0  # Sensors or small payload
        },
        "crew": {
                    "count": 1,
                    "weight_per_crew_kg": 100.0,
                    "crew_kg": 100.0
                },
        "propulsion": {
            "type": "jet",
            "count": 2,
            "jet_model_method": "turbo_ramjet",  # New High Speed Model
            "thrust_sl_n": 150000.0,  # 150 kN per engine (34k lbf) - similar to J58
            "tsfc_1_s": 5.38e-5,  # ~1.9 lb/lbf/hr (Mass Flow SFC: kg/N/s)
            "bypass_ratio": 0.0,
            "mct_to_mto_ratio": 0.9,
            "thrust_map": pmap
        },
        "aero": {
            "aspect_ratio": 2.0,  # Low AR for Mach 4
            "sweep_deg": 65.0,    # High sweep
            "taper_ratio": 0.1,
            "airfoil_thickness": 0.04, # Very thin
            "e": 0.25, # Oswald Efficiency reduced for Supersonic Wave Drag due to Lift (approx K ~ 0.6)
            "lift_slope_method": "supersonic", # Implicit
            "cl_max": 1.2 # Low aspect ratio delta wing, maybe with vortex lift
        },
        "sizing": {
                    "initial_mtow_kg": 40000.0,
                    "wing_loading_pa": 4000.0,  # Low wing loading for high altitude? 
                    "thrust_to_weight": 0.5, # Static T/W. 
                    "aspect_ratio": 2.0
                },
        "geometry_shape": {
            "layout": {"views": ["top", "side", "front", "iso"]},
            "fuselage": {
                "axis": {"length_m": 30.0},
                "profile": {
                    "mode": "parametric",
                    "max_radius_m": 1.0,
                    "nose_fineness_ratio": 4.0,
                    "tail_fineness_ratio": 3.0
                }
            },
            "wing": {
                "airfoil": {"code": "0004"}
            }
        },
        "geometry_parametric": {
            "wing": {
                "aspect_ratio": 2.0,
                "taper_ratio": 0.1,
                "sweep_quarter_chord_deg": 65.0,
                "t_c": 0.04,
                "area_m2": 200.0 # Initial guess, will be resized
            },
            "fuselage": {
                "length_m": 30.0,
                "diameter_m": 2.0
            },
            "tail": {
                "area_ratio_to_wing": 0.0 # Tailless or Canard handled separately?
            }
        },
        "systems": {
            "avionics": {"weight_kg": 500.0},
            "ecs": {"type": "cycle", "weight_kg": 400.0} # Heavy cooling needed
        },
        "weights": {
                    # Fighter/Supersonic defaults
                    # We = a * W0^b. For W0=40000, We=20000 -> a=0.5, b=1.0
                    "empty_a": 0.45, 
                    "empty_b": 1.0,
                    "w0_guess_kg": 40000.0,
                    "method": "class2" # Force class 2
                }
    }
    
    # Run Design Loop
    result = run_fixed_wing_overall_design(inputs)
    
    # Output critical params
    print("\n--- Design Result ---")
    weights_res = result.get('weights', {})
    mtow = weights_res.get('w0_kg', 0.0)
    print(f"MTOW: {mtow:.1f} kg")
    print(f"Empty Weight: {weights_res.get('we_kg', 0.0):.1f} kg")
    print(f"Fuel Weight: {weights_res.get('wf_kg', 0.0):.1f} kg")
    print(f"Wing Area: {result.get('geometry', {}).get('s_m2', 0.0):.1f} m2")
    
    print("\n--- Aerodynamics at Cruise ---")
    aero_res = result.get("aero", {})
    print(f"Cruise L/D: {aero_res.get('ld_cruise', 0.0):.2f}")
    # Calculate CD from CD0 + K*CL^2 if available, or just print CD0 and K
    print(f"Cruise CD0: {aero_res.get('cd0', 0.0):.4f}")
    print(f"Wave Drag CD: {aero_res.get('wave_drag_cd', 0.0):.4f}")
    
    # Check Constraints
    print("\n--- Constraints ---")
    constraints = result.get("constraints_check", {})
    print(f"T/W Margin: {constraints.get('takeoff_tw_margin', 0.0):.2f}")
    
    # Check if we converged
    print(f"\nConverged: {result.get('converged', False)}")

if __name__ == "__main__":
    run_mach4_design()
