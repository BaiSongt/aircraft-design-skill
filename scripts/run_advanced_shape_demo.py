import os
import sys
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aircraft_design.geometry_shape import (
    geometry_shape_from_inputs,
    calculate_cross_sectional_area_distribution,
    verify_geometric_constraints,
)
from aircraft_design.visualization_3d import generate_three_view_html
from aircraft_design.openvsp_bridge import write_openvsp_script as generate_openvsp_script


def run_demo():
    print("Running Advanced Shape Design Demo...")

    # 1. Define Input with Advanced Features
    inputs = {
        "project_name": "Advanced Shape Demo",
        "geometry_shape": {
            "layout": {"views": ["top", "side", "front", "iso"]},
            "fuselage": {
                "axis": {"length_m": 12.0},
                "profile": {
                    "mode": "parametric",
                    "max_radius_m": 1.2,
                    "nose_fineness_ratio": 1.8,
                    "tail_fineness_ratio": 3.0,
                    "nose_shape": "ellipsoid",
                    "tail_shape": "conical",
                },
                "modifiers": {
                    "canopy": {"x_rel": 0.18, "length_rel": 0.15, "height_m": 0.35},
                    "wing_fairing": {"radius_m": 0.2},
                },
            },
            "wing": {
                "planform": {
                    "s_ref_m2": 24.0,
                    "aspect_ratio": 6.0,
                    "taper_ratio": 0.5,
                    "sweep_quarter_chord_deg": 15.0,
                    "x_offset_m": 4.5,
                    "dihedral_deg": 3.0,
                },
                "sections": {
                    "root_airfoil": {"type": "naca4", "code": "2412"},
                    "tip_airfoil": {"type": "naca4", "code": "0010"},
                },
            },
            "tail": {
                "layout": {"type": "conventional"},
                "horizontal": {
                    "planform": {
                        "s_ref_m2": 5.0,
                        "aspect_ratio": 4.0,
                        "taper_ratio": 0.6,
                        "sweep_quarter_chord_deg": 10.0,
                    }
                },
                "vertical": {
                    "planform": {
                        "s_ref_m2": 3.0,
                        "aspect_ratio": 1.5,
                        "taper_ratio": 0.6,
                        "sweep_quarter_chord_deg": 20.0,
                    }
                },
            },
        },
    }

    # 2. Process Geometry
    print("Processing geometry...")
    geometry = geometry_shape_from_inputs(inputs)
    if not geometry:
        print("Error: Failed to process geometry inputs.")
        return

    # 3. Calculate Area Distribution (Area Rule)
    print("Calculating area distribution...")
    fus_l = float(inputs["geometry_shape"]["fuselage"]["axis"]["length_m"])
    wing_pf = inputs["geometry_shape"]["wing"]["planform"]

    area_dist = calculate_cross_sectional_area_distribution(
        fuselage_stations=geometry["fuselage"]["stations"],
        fuselage_length_m=fus_l,
        wing_s_ref_m2=float(wing_pf["s_ref_m2"]),
        wing_aspect_ratio=float(wing_pf["aspect_ratio"]),
        wing_taper_ratio=float(wing_pf["taper_ratio"]),
        wing_sweep_quarter_chord_deg=float(wing_pf["sweep_quarter_chord_deg"]),
        wing_t_c=0.12,  # Average t/c
        wing_x_offset_m=float(wing_pf["x_offset_m"]),
        tail_layout=geometry.get("tail", {}),
        n_points=50,
    )

    # 4. Verify Constraints
    print("Verifying constraints...")
    constraints = {
        "hardpoints": {
            "pilot_eye": {"x": 2.5, "y": 0.0, "z": 0.8},  # Inside canopy?
            "engine": {"x": 0.5, "y": 0.0, "z": 0.0},
        }
    }
    violations = verify_geometric_constraints(geometry, constraints)
    if violations:
        print("Constraint violations found:", violations)
    else:
        print("All geometric constraints satisfied.")

    # 5. Generate Outputs
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
    os.makedirs(out_dir, exist_ok=True)

    # Save Results JSON
    results = {
        "inputs": inputs,
        "geometry_processed": geometry,  # This can be large
        "area_distribution": area_dist,
        "constraint_violations": violations,
    }
    with open(os.path.join(out_dir, "advanced_shape_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    # Generate 3D Visualization HTML
    print("Generating 3D HTML...")
    html_path = os.path.join(out_dir, "geometry_3d.html")
    generate_three_view_html(geometry, html_path)

    # Generate OpenVSP Script
    print("Generating OpenVSP script...")
    vsp_path = os.path.join(out_dir, "openvsp_advanced.py")
    generate_openvsp_script(geom=geometry, out_path=vsp_path)

    # Generate Area Distribution Plot (Simple SVG or Markdown Table)
    print("Generating Area Rule Report...")
    report_path = os.path.join(out_dir, "area_rule_report.md")
    with open(report_path, "w") as f:
        f.write("# Area Rule Analysis Report\n\n")
        f.write("| X (m) | Fuselage (m2) | Wing (m2) | Tail (m2) | Total (m2) |\n")
        f.write("|---|---|---|---|---|\n")
        for p in area_dist:
            f.write(
                f"| {p['x_m']:.2f} | {p['area_fuselage_m2']:.4f} | {p['area_wing_m2']:.4f} | {p['area_tail_m2']:.4f} | **{p['area_total_m2']:.4f}** |\n"
            )

    print(f"Done! Outputs saved to {out_dir}")
    print(f"1. {os.path.join(out_dir, 'geometry_3d.html')} (View this for 3D shape)")
    print(f"2. {os.path.join(out_dir, 'area_rule_report.md')} (View this for Area Rule)")
    print(f"3. {os.path.join(out_dir, 'advanced_shape_results.json')}")


if __name__ == "__main__":
    run_demo()
