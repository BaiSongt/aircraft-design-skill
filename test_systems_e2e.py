import json
print("Imports starting...")
from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design
print("Imports done.")

def test_systems_integration():
    inputs = {
        "project_name": "Test Systems",
        "mission": { # Moved to top level per schema
             "range_m": 1000000.0, 
             "payload_kg": 500, 
             "cruise_speed_m_s": 83.33,
             "cruise_altitude_m": 3000,
             "v_stall_m_s": 27.78
        },
        "payload": {
            "pax_count": 0,
            "cargo_kg": 500,
            "payload_kg": 500
        },
        "crew": {
            "pilot_count": 1,
            "attendant_count": 0,
            "crew_kg": 100
        },
        "aero": {
             "e": 0.8,
             "cl_max": 1.5,
             "cd0": 0.02
        },
        "propulsion": {
            "type": "prop",
            "engine_count": 1,
            "sfc_1_s": 8e-8,
            "prop_efficiency": 0.8
        },
        "sizing": {
            "max_iterations": 10,
            "wing_loading_pa": 1500.0,
            "aspect_ratio": 8.0,
            "thrust_to_weight": 0.3
        },
        "requirements": {
            "mission": {"range_km": 1000, "payload_kg": 500, "cruise_speed_kmh": 300},
            "constraints": {"takeoff_distance_m": 500, "stall_speed_kmh": 100}
        },
        "weights": {
            "mtow_kg": 3000,
            "empty_a": 0.9,
            "empty_b": -0.05
        }, # Initial guess
        "geometry": {
            "fuselage": {"length_m": 10.0, "diameter_m": 1.2},
            "wing": {"s_ref_m2": 20.0, "aspect_ratio": 8.0}
        },
        "systems": {
            "landing_gear": {
                "type": "fixed",
                "weight_fraction_override": 0.04
            },
            "avionics": {
                "weight_kg": 150.0,
                "location_x_m": 1.5
            },
            "extra_pod": {
                "weight_kg": 50.0,
                "location_x_m": 5.0
            },
            "ecs": {
                "type": "basic",
                "weight_kg": 30.0
            },
            "anti_ice": {
                "type": "tks",
                "weight_kg": 40.0
            },
            "electrical": {
                "weight_kg": 60.0
            }
        }
    }
    
    result = run_fixed_wing_overall_design(inputs)
    
    # Check if systems output exists
    if "systems" not in result:
        print("FAIL: 'systems' key missing in result")
        return
        
    sys = result["systems"]
    print("Total Weight:", sys["total_weight_kg"])
    print("CG X:", sys["cg_x_m"])
    
    groups = sys["groups"]
    
    # Verify Avionics override
    avionics_found = False
    ecs_found = False
    anti_ice_found = False
    elec_found = False
    
    for c in groups.get("Systems", {}).get("components", []):
        if c["name"] == "Avionics":
            avionics_found = True
            print(f"Avionics Weight: {c['weight_kg']} (Expected 150.0)")
            print(f"Avionics Power: {c['power_w']} W")
            if abs(c["weight_kg"] - 150.0) > 0.1:
                print("FAIL: Avionics weight mismatch")
            else:
                print("PASS: Avionics weight correct")
            if c["power_w"] <= 0:
                print("FAIL: Avionics power should be positive")
                
        elif c["name"] == "ECS":
            ecs_found = True
            print(f"ECS Weight: {c['weight_kg']} (Expected 30.0)")
            print(f"ECS Power: {c['power_w']} W")
            if abs(c["weight_kg"] - 30.0) > 0.1:
                print("FAIL: ECS weight mismatch")
            
        elif c["name"] == "Anti-Ice":
            anti_ice_found = True
            print(f"Anti-Ice Weight: {c['weight_kg']} (Expected 40.0)")
            print(f"Anti-Ice Power: {c['power_w']} W")
            if abs(c["weight_kg"] - 40.0) > 0.1:
                print("FAIL: Anti-Ice weight mismatch")
                
        elif c["name"] == "Electrical":
            elec_found = True
            print(f"Electrical Weight: {c['weight_kg']} (Expected 60.0)")
            
    if not avionics_found: print("FAIL: Avionics component not found")
    if not ecs_found: print("FAIL: ECS component not found")
    if not anti_ice_found: print("FAIL: Anti-Ice component not found")
    if not elec_found: print("FAIL: Electrical component not found")

    if avionics_found and ecs_found and anti_ice_found and elec_found:
        print("PASS: All new system components found")

    # Verify Extra Pod

    # Verify Extra Pod
    pod_found = False
    # Extra pod might be in Systems or auto-categorized
    for g_name, grp in groups.items():
        for c in grp["components"]:
            if c["name"] == "Extra Pod":
                pod_found = True
                print(f"Extra Pod found in {g_name}")
                
    if pod_found:
        print("PASS: Extra Pod found")
    else:
        print("FAIL: Extra Pod not found")

    # Check Geometry Injection
    geom = result.get("geometry_detailed", {})
    has_systems = False
    if isinstance(geom, dict):
        has_systems = "systems" in geom
    else:
        has_systems = hasattr(geom, "systems")
        
    if has_systems:
        print("PASS: Systems injected into geometry_detailed")
    else:
        print("FAIL: Systems not injected into geometry_detailed")

if __name__ == "__main__":
    print("Starting test...")
    test_systems_integration()
