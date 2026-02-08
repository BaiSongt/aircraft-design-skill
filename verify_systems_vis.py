from aircraft_design.visualization_3d import build_mesh_parts_from_geometry

def verify():
    # Mock geometry with systems
    geometry = {
        "fuselage": {"length_m": 10.0, "diameter_m": 1.0},
        "systems": {
            "groups": {
                "Systems": {
                    "components": [
                        {"name": "Avionics", "cg_x_m": 2.0, "cg_y_m": 0.0, "cg_z_m": 0.0},
                        {"name": "Landing Gear", "cg_x_m": 5.0, "cg_y_m": 0.0, "cg_z_m": -0.5}
                    ]
                },
                "Propulsion": {
                    "components": [
                        {"name": "Engine", "cg_x_m": 8.0, "cg_y_m": 0.0, "cg_z_m": 0.0}
                    ]
                }
            }
        }
    }
    
    parts = build_mesh_parts_from_geometry(geometry)
    
    print(f"Generated {len(parts)} parts.")
    
    system_parts = [p for p in parts if ":" in p.name] # System names have "Group: Name"
    print(f"System parts found: {len(system_parts)}")
    
    for p in system_parts:
        print(f" - {p.name} (Color: {p.color}, Vertices: {len(p.vertices)//3})")
        
    if len(system_parts) == 3:
        print("PASS: Systems visualization parts generated.")
    else:
        print("FAIL: Incorrect number of system parts.")

if __name__ == "__main__":
    verify()
