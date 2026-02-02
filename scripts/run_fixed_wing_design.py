from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path


def _ensure_project_root() -> None:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def main() -> int:
    _ensure_project_root()
    from aircraft_design.design_loop import grid_search_design_point
    from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design
    from aircraft_design.geometry_detailed import geometry_detailed_from_inputs
    from aircraft_design.geometry_parametric import (
        Fuselage,
        ParametricGeometry,
        Tail,
        WingPlanform,
        geometry_from_inputs,
    )
    from aircraft_design.geometry_shape import (
        calculate_cross_sectional_area_distribution,
        calculate_mac_properties,
        derive_tail_layout,
        geometry_field_map,
        geometry_shape_from_inputs,
        resolve_geometry_bundle,
        validate_geometry_shape_inputs,
        validate_geometry_shape_outputs,
        verify_geometric_constraints,
    )
    from aircraft_design.input_schema import normalize_inputs, validate_run_inputs
    from aircraft_design.openvsp_bridge import can_import_openvsp, run_openvsp_script, write_openvsp_script
    from aircraft_design.plots import render_constraints_ws_tw_svg
    from aircraft_design.report import render_markdown_report
    from aircraft_design.visualization_3d import (
        MeshPart,
        build_fuselage_cylinder,
        build_fuselage_loft,
        build_tail_mesh,
        build_vertical_tail_airfoil_loft_mesh,
        build_wing_airfoil_loft_mesh,
        build_wing_mesh,
        generate_three_view_html,
        mesh_to_obj,
        render_geometry_viewer_html,
    )

    if len(sys.argv) not in [2, 3]:
        print("Usage: python scripts/run_fixed_wing_design.py <input.json> [--grid-search]")
        print("Grid search reads design_loop.*_grid in input.json")
        return 2

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        print(f"Input not found: {input_path}")
        return 2

    with input_path.open("r", encoding="utf-8") as f:
        inputs = json.load(f)

    try:
        if not inputs.get("_normalized", False):
            inputs, _warnings = normalize_inputs(inputs)
    except Exception as e:
        print(f"Input normalization failed: {e}")
        return 2
    validation = validate_run_inputs(inputs)
    if validation.get("warnings"):
        print("Input validation warnings:")
        for w in validation["warnings"]:
            print(f"- {w}")
    if validation.get("errors"):
        print("Input validation failed:")
        for err in validation["errors"]:
            print(f"- {err}")
        return 2

    input_geometry_validation = validate_geometry_shape_inputs(inputs)

    if len(sys.argv) == 3 and sys.argv[2] == "--grid-search":

        def _grid_numbers(value: object, name: str) -> list[float]:
            if isinstance(value, list) and value:
                if not all(isinstance(x, (int, float)) for x in value):
                    raise ValueError(f"design_loop.{name} must be an array of numbers.")
                return [float(x) for x in value]
            raise ValueError(f"design_loop.{name} must be a non-empty array of numbers.")

        dl = inputs.get("design_loop", {}) if isinstance(inputs.get("design_loop", None), dict) else {}
        ws_grid = _grid_numbers(dl.get("wing_loading_pa_grid", [1200.0, 1500.0, 1800.0]), "wing_loading_pa_grid")
        ar_grid = _grid_numbers(dl.get("aspect_ratio_grid", [7.5, 8.5, 9.5]), "aspect_ratio_grid")
        tw_grid = _grid_numbers(dl.get("thrust_to_weight_grid", [0.24, 0.28, 0.32]), "thrust_to_weight_grid")
        objective = inputs.get("design_loop", {}).get("objective", "min_w0_kg")
        top_n = int(inputs.get("design_loop", {}).get("top_n", 10))
        sensitivity_steps = inputs.get("design_loop", {}).get("sensitivity_steps", None)
        loop = grid_search_design_point(
            base_inputs=inputs,
            wing_loading_pa_grid=[float(x) for x in ws_grid],
            aspect_ratio_grid=[float(x) for x in ar_grid],
            thrust_to_weight_grid=[float(x) for x in tw_grid],
            objective=str(objective),
            top_n=top_n,
            sensitivity_steps=sensitivity_steps,
        )
        results = {
            **loop.best_results,
            "design_loop": {
                "objective": objective,
                "best_sizing": loop.best_inputs.get("sizing", {}),
                "candidates": loop.candidates,
                "top_candidates": loop.top_candidates,
                "sensitivity": loop.sensitivity,
            },
        }
    else:
        results = run_fixed_wing_overall_design(inputs)

    out_root = Path("out").resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = out_root / f"run_{run_stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    results_dir = out_dir / "results"
    report_dir = out_dir / "report"
    geometry_dir = out_dir / "geometry"
    mesh_dir = out_dir / "mesh"
    openvsp_dir = out_dir / "openvsp"
    for d in [results_dir, report_dir, geometry_dir, mesh_dir, openvsp_dir]:
        d.mkdir(parents=True, exist_ok=True)

    def _rel_out(path: Path) -> str:
        try:
            return str(path.relative_to(out_dir))
        except ValueError:
            return str(path)

    results_path = results_dir / "results.json"
    report_path = report_dir / "report.md"
    plot_path = report_dir / "constraints_ws_tw.svg"
    geom_html_path = geometry_dir / "geometry_3d.html"
    geom_obj_path = geometry_dir / "geometry.obj"
    geom_json_path = mesh_dir / "geometry_mesh.json"
    advanced_results_path = geometry_dir / "advanced_shape_results.json"
    area_rule_report_path = report_dir / "area_rule_report.md"
    openvsp_advanced_path = openvsp_dir / "openvsp_advanced.py"

    def _build_geometry_shape_fallback(*, geom: ParametricGeometry, sizing: dict | None) -> dict:
        s_ref_val = None
        if isinstance(sizing, dict) and isinstance(sizing.get("s_m2", None), (int, float)):
            s_ref_val = float(sizing["s_m2"])

        wing_planform = {
            "aspect_ratio": float(geom.wing.aspect_ratio),
            "taper_ratio": float(geom.wing.taper_ratio),
            "sweep_quarter_chord_deg": float(geom.wing.sweep_quarter_chord_deg),
        }
        if isinstance(s_ref_val, (int, float)):
            wing_planform["s_ref_m2"] = float(s_ref_val)

        tail_ratio = float(geom.tail.area_ratio_to_wing)
        h_ratio = max(0.0, tail_ratio * 0.7)
        v_ratio = max(0.0, tail_ratio * 0.3)

        return {
            "layout": {"views": ["top", "side", "front", "iso"]},
            "fuselage": {
                "axis": {"length_m": float(geom.fuselage.length_m)},
                "profile": {
                    "mode": "parametric",
                    "max_radius_m": 0.5 * float(geom.fuselage.diameter_m),
                    "nose_fineness_ratio": 2.0,
                    "tail_fineness_ratio": 3.0,
                    "nose_shape": "ellipsoid",
                    "tail_shape": "conical",
                },
            },
            "wing": {"planform": wing_planform},
            "tail": {
                "layout": {"type": "conventional"},
                "horizontal": {
                    "planform": {
                        "area_ratio_to_wing": float(h_ratio),
                        "aspect_ratio": 4.0,
                        "taper_ratio": 0.6,
                        "sweep_quarter_chord_deg": 10.0,
                    }
                },
                "vertical": {
                    "planform": {
                        "area_ratio_to_wing": float(v_ratio),
                        "aspect_ratio": 1.8,
                        "taper_ratio": 0.7,
                        "sweep_quarter_chord_deg": 25.0,
                    }
                },
            },
        }

    geom = geometry_from_inputs(inputs)
    if geom is None and isinstance(inputs.get("geometry", None), dict) and isinstance(inputs.get("sizing", None), dict):
        g = inputs.get("geometry", {})
        s = inputs.get("sizing", {})
        ar = s.get("aspect_ratio", None)
        if isinstance(ar, (int, float)):
            geom = ParametricGeometry(
                wing=WingPlanform(
                    aspect_ratio=float(ar),
                    taper_ratio=float(s.get("taper_ratio", 0.45)),
                    sweep_quarter_chord_deg=float(s.get("sweep_quarter_chord_deg", 0.0)),
                    t_c=float(g.get("wing_t_c", 0.12)),
                ),
                fuselage=Fuselage(
                    length_m=float(g.get("fuselage_length_m", 7.5)), diameter_m=float(g.get("fuselage_diameter_m", 1.2))
                ),
                tail=Tail(area_ratio_to_wing=float(g.get("tail_area_ratio", 0.22))),
            )
    if geom is not None:
        detailed = geometry_detailed_from_inputs(inputs) or {}
        shape_inputs = inputs.get("geometry_shape", None)
        if not isinstance(shape_inputs, dict):
            sizing_for_shape = results.get("sizing", {}) if isinstance(results.get("sizing", None), dict) else {}
            inputs["geometry_shape"] = _build_geometry_shape_fallback(geom=geom, sizing=sizing_for_shape)
            input_geometry_validation = validate_geometry_shape_inputs(inputs)
        try:
            shape = geometry_shape_from_inputs(inputs) or {}
        except Exception:
            sizing_for_shape = results.get("sizing", {}) if isinstance(results.get("sizing", None), dict) else {}
            inputs["geometry_shape"] = _build_geometry_shape_fallback(geom=geom, sizing=sizing_for_shape)
            input_geometry_validation = validate_geometry_shape_inputs(inputs)
            shape = geometry_shape_from_inputs(inputs) or {}

        layout = shape.get("layout", None) if isinstance(shape, dict) else None

        wing_airfoil = None
        wing_tip_airfoil = None
        wing_spanwise_cps = None
        wing_control_surfaces = None
        wing_planform = None
        fus_stations = None
        if isinstance(shape, dict):
            fus = shape.get("fuselage", None)
            if isinstance(fus, dict):
                fus_stations = fus.get("stations", None)
            wing = shape.get("wing", None)
            if isinstance(wing, dict):
                root = wing.get("root_airfoil", None)
                if isinstance(root, dict):
                    wing_airfoil = root.get("coords", None)
                tip = wing.get("tip_airfoil", None)
                if isinstance(tip, dict):
                    wing_tip_airfoil = tip.get("coords", None)
                controls = wing.get("controls", None)
                if isinstance(controls, dict):
                    wing_spanwise_cps = controls.get("spanwise_control_points", None)
                    wing_control_surfaces = controls.get("control_surfaces", None)
                pf = wing.get("planform", None)
                if isinstance(pf, dict):
                    wing_planform = pf
        if wing_airfoil is None or fus_stations is None:
            if isinstance(detailed, dict):
                w = detailed.get("wing", None)
                if isinstance(w, dict):
                    af = w.get("airfoil", None)
                    if isinstance(af, dict) and wing_airfoil is None:
                        wing_airfoil = af.get("coords", None)
                f = detailed.get("fuselage", None)
                if isinstance(f, dict) and fus_stations is None:
                    fus_stations = f.get("stations", None)

        sizing = results.get("sizing", {})
        s_ref = sizing.get("s_m2", None)
        shape_inputs = inputs.get("geometry_shape", None)
        advanced_area_dist = None
        advanced_constraints = None
        if isinstance(shape, dict) and shape and isinstance(shape_inputs, dict):
            fuselage_length_m = None
            fuselage_cfg = shape_inputs.get("fuselage", {})
            if isinstance(fuselage_cfg, dict):
                axis_cfg = fuselage_cfg.get("axis", {})
                if isinstance(axis_cfg, dict) and isinstance(axis_cfg.get("length_m", None), (int, float)):
                    fuselage_length_m = float(axis_cfg.get("length_m"))
            if fuselage_length_m is None:
                fus_shape = shape.get("fuselage", {})
                stations = fus_shape.get("stations", None) if isinstance(fus_shape, dict) else None
                if isinstance(stations, list) and stations:
                    xs = [
                        float(s.get("x_m", 0.0))
                        for s in stations
                        if isinstance(s, dict) and isinstance(s.get("x_m", None), (int, float))
                    ]
                    if xs:
                        fuselage_length_m = float(max(xs) - min(xs))

            wing_pf = None
            wing_cfg = shape.get("wing", {}) if isinstance(shape, dict) else {}
            if isinstance(wing_cfg, dict) and isinstance(wing_cfg.get("planform", None), dict):
                wing_pf = wing_cfg.get("planform", {})
            if wing_pf is None and isinstance(shape_inputs, dict):
                wing_cfg = shape_inputs.get("wing", {})
                if isinstance(wing_cfg, dict) and isinstance(wing_cfg.get("planform", None), dict):
                    wing_pf = wing_cfg.get("planform", {})

            def _get_pf_value(key: str, fallback: float | None) -> float | None:
                if isinstance(wing_pf, dict) and isinstance(wing_pf.get(key, None), (int, float)):
                    return float(wing_pf.get(key))
                return fallback

            s_ref_pf = _get_pf_value("s_ref_m2", float(s_ref) if isinstance(s_ref, (int, float)) else None)
            ar_pf = _get_pf_value("aspect_ratio", float(geom.wing.aspect_ratio))
            taper_pf = _get_pf_value("taper_ratio", float(geom.wing.taper_ratio))
            sweep_pf = _get_pf_value("sweep_quarter_chord_deg", float(geom.wing.sweep_quarter_chord_deg))
            wing_x_offset = _get_pf_value("x_offset_m", 0.0)
            wing_t_c = inputs.get("geometry", {}).get("wing_t_c", None)
            if not isinstance(wing_t_c, (int, float)):
                wing_t_c = float(geom.wing.t_c)

            if isinstance(fuselage_length_m, (int, float)) and isinstance(s_ref_pf, (int, float)) and s_ref_pf > 0.0:
                advanced_area_dist = calculate_cross_sectional_area_distribution(
                    fuselage_stations=shape.get("fuselage", {}).get("stations", []),
                    fuselage_length_m=float(fuselage_length_m),
                    wing_s_ref_m2=float(s_ref_pf),
                    wing_aspect_ratio=float(ar_pf),
                    wing_taper_ratio=float(taper_pf),
                    wing_sweep_quarter_chord_deg=float(sweep_pf),
                    wing_t_c=float(wing_t_c),
                    wing_x_offset_m=float(wing_x_offset or 0.0),
                    tail_layout=shape.get("tail", {}),
                    n_points=50,
                )

            constraints_cfg = None
            if isinstance(shape_inputs.get("constraints", None), dict):
                constraints_cfg = shape_inputs.get("constraints")
            elif isinstance(inputs.get("geometry_constraints", None), dict):
                constraints_cfg = inputs.get("geometry_constraints")
            if isinstance(constraints_cfg, dict):
                advanced_constraints = verify_geometric_constraints(shape, constraints_cfg)

            if advanced_area_dist is not None or advanced_constraints is not None:
                advanced_results = {
                    "inputs": inputs,
                    "geometry_processed": shape,
                    "area_distribution": advanced_area_dist,
                    "constraint_violations": advanced_constraints,
                }
                with advanced_results_path.open("w", encoding="utf-8") as f:
                    json.dump(advanced_results, f, ensure_ascii=False, indent=2)
                if isinstance(advanced_area_dist, list):
                    with area_rule_report_path.open("w", encoding="utf-8") as f:
                        f.write("# Area Rule Analysis Report\n\n")
                        f.write("| X (m) | Fuselage (m2) | Wing (m2) | Tail (m2) | Total (m2) |\n")
                        f.write("|---|---|---|---|---|\n")
                        for p in advanced_area_dist:
                            f.write(
                                f"| {p['x_m']:.2f} | {p['area_fuselage_m2']:.4f} | {p['area_wing_m2']:.4f} | {p['area_tail_m2']:.4f} | **{p['area_total_m2']:.4f}** |\n"
                            )
                try:
                    write_openvsp_script(geom=shape, out_path=openvsp_advanced_path)
                except Exception:
                    pass
                results["advanced_shape"] = {
                    "area_distribution": advanced_area_dist,
                    "constraint_violations": advanced_constraints,
                    "artifacts": {
                        "advanced_shape_results": _rel_out(advanced_results_path),
                        "area_rule_report": _rel_out(area_rule_report_path) if area_rule_report_path.exists() else None,
                        "openvsp_advanced_script": _rel_out(openvsp_advanced_path)
                        if openvsp_advanced_path.exists()
                        else None,
                    },
                }
                results["artifacts"] = {
                    **(results.get("artifacts", {}) if isinstance(results.get("artifacts", {}), dict) else {}),
                    "advanced_shape_results": _rel_out(advanced_results_path),
                    "area_rule_report": _rel_out(area_rule_report_path) if area_rule_report_path.exists() else None,
                    "openvsp_advanced_script": _rel_out(openvsp_advanced_path)
                    if openvsp_advanced_path.exists()
                    else None,
                }
        if isinstance(s_ref, (int, float)) and float(s_ref) > 0.0:
            parts: list[MeshPart] = []
            if isinstance(fus_stations, list) and fus_stations:
                parts.append(build_fuselage_loft(stations=fus_stations))
            else:
                parts.append(
                    build_fuselage_cylinder(length_m=geom.fuselage.length_m, diameter_m=geom.fuselage.diameter_m)
                )

            wing_x = 0.0
            wing_y = 0.0
            wing_z = 0.0
            wing_dihedral = 0.0
            wing_incidence = 0.0
            if isinstance(wing_planform, dict):
                if isinstance(wing_planform.get("x_offset_m"), (int, float)):
                    wing_x = float(wing_planform["x_offset_m"])
                if isinstance(wing_planform.get("y_offset_m"), (int, float)):
                    wing_y = float(wing_planform["y_offset_m"])
                if isinstance(wing_planform.get("z_offset_m"), (int, float)):
                    wing_z = float(wing_planform["z_offset_m"])
                if isinstance(wing_planform.get("dihedral_deg"), (int, float)):
                    wing_dihedral = float(wing_planform["dihedral_deg"])
                if isinstance(wing_planform.get("incidence_deg"), (int, float)):
                    wing_incidence = float(wing_planform["incidence_deg"])

            derived_tail = None
            tail_cfg = shape.get("tail", None) if isinstance(shape, dict) else None
            if isinstance(wing_airfoil, list) and wing_airfoil:
                parts.extend(
                    build_wing_airfoil_loft_mesh(
                        root_airfoil_coords=wing_airfoil,
                        tip_airfoil_coords=wing_tip_airfoil
                        if isinstance(wing_tip_airfoil, list) and wing_tip_airfoil
                        else None,
                        s_ref_m2=float(s_ref),
                        aspect_ratio=geom.wing.aspect_ratio,
                        taper_ratio=geom.wing.taper_ratio,
                        sweep_quarter_chord_deg=geom.wing.sweep_quarter_chord_deg,
                        x_offset_m=wing_x,
                        y_offset_m=wing_y,
                        z_offset_m=wing_z,
                        dihedral_deg=wing_dihedral,
                        incidence_deg=wing_incidence,
                        spanwise_control_points=wing_spanwise_cps if isinstance(wing_spanwise_cps, list) else None,
                        control_surfaces=wing_control_surfaces if isinstance(wing_control_surfaces, list) else None,
                        name_prefix="wing",
                        color="#2c7fb8",
                    )
                )
                if isinstance(tail_cfg, dict) and (
                    tail_cfg.get("horizontal") or tail_cfg.get("vertical") or tail_cfg.get("layout")
                ):
                    derived = derive_tail_layout(
                        tail_cfg=tail_cfg,
                        wing_s_ref_m2=float(s_ref),
                        fuselage_length_m=float(geom.fuselage.length_m),
                        fuselage_diameter_m=float(geom.fuselage.diameter_m),
                    )
                    derived_tail = derived
                    for sf in derived.get("surfaces", []):
                        if not isinstance(sf, dict):
                            continue
                        src = sf.get("source", None)
                        sec = tail_cfg.get(src, None) if isinstance(src, str) else None
                        if not isinstance(sec, dict):
                            continue
                        root = (
                            sec.get("root_airfoil", None) if isinstance(sec.get("root_airfoil", None), dict) else None
                        )
                        tip = sec.get("tip_airfoil", None) if isinstance(sec.get("tip_airfoil", None), dict) else None
                        ctrl = sec.get("controls", None) if isinstance(sec.get("controls", None), dict) else None
                        cps = ctrl.get("spanwise_control_points", None) if isinstance(ctrl, dict) else None
                        css = ctrl.get("control_surfaces", None) if isinstance(ctrl, dict) else None
                        root_coords = root.get("coords", None) if isinstance(root, dict) else None
                        if not isinstance(root_coords, list) or not root_coords:
                            continue

                        builder = sf.get("builder", None)
                        if builder == "wing_loft":
                            name_prefix = str(sf.get("name_prefix", "tail"))
                            color = "#9e9ac8" if name_prefix == "vtail" else "#a1d99b"
                            parts.extend(
                                build_wing_airfoil_loft_mesh(
                                    root_airfoil_coords=root_coords,
                                    tip_airfoil_coords=tip.get("coords", None) if isinstance(tip, dict) else None,
                                    s_ref_m2=float(sf.get("s_ref_m2", 0.0)),
                                    aspect_ratio=float(sf.get("aspect_ratio", 4.0)),
                                    taper_ratio=float(sf.get("taper_ratio", 0.6)),
                                    sweep_quarter_chord_deg=float(sf.get("sweep_quarter_chord_deg", 10.0)),
                                    x_offset_m=float(sf.get("x_offset_m", 0.0)),
                                    y_offset_m=float(sf.get("y_offset_m", 0.0)),
                                    z_offset_m=float(sf.get("z_offset_m", 0.0)),
                                    dihedral_deg=float(sf.get("dihedral_deg", 0.0)),
                                    incidence_deg=float(sf.get("incidence_deg", 0.0)),
                                    spanwise_control_points=cps if isinstance(cps, list) else None,
                                    control_surfaces=css if isinstance(css, list) else None,
                                    name_prefix=name_prefix,
                                    color=color,
                                )
                            )
                        elif builder == "vertical_loft":
                            name = str(sf.get("name", "vtail"))
                            parts.append(
                                build_vertical_tail_airfoil_loft_mesh(
                                    root_airfoil_coords=root_coords,
                                    tip_airfoil_coords=tip.get("coords", None) if isinstance(tip, dict) else None,
                                    s_ref_m2=float(sf.get("s_ref_m2", 0.0)),
                                    aspect_ratio=float(sf.get("aspect_ratio", 1.8)),
                                    taper_ratio=float(sf.get("taper_ratio", 0.7)),
                                    sweep_quarter_chord_deg=float(sf.get("sweep_quarter_chord_deg", 25.0)),
                                    x_offset_m=float(sf.get("x_offset_m", 0.0)),
                                    y_offset_m=float(sf.get("y_offset_m", 0.0)),
                                    z_offset_m=float(sf.get("z_offset_m", 0.0)),
                                    spanwise_control_points=cps if isinstance(cps, list) else None,
                                    name=name,
                                    color="#fd8d3c",
                                )
                            )
                else:
                    s_tail = float(s_ref) * max(0.0, float(geom.tail.area_ratio_to_wing))
                    if s_tail > 0.0:
                        parts.extend(
                            build_wing_airfoil_loft_mesh(
                                root_airfoil_coords=wing_airfoil,
                                tip_airfoil_coords=None,
                                s_ref_m2=s_tail,
                                aspect_ratio=geom.wing.aspect_ratio,
                                taper_ratio=geom.wing.taper_ratio,
                                sweep_quarter_chord_deg=geom.wing.sweep_quarter_chord_deg,
                                x_offset_m=0.55 * float(geom.fuselage.length_m),
                                y_offset_m=0.0,
                                z_offset_m=0.35 * float(geom.fuselage.diameter_m),
                                dihedral_deg=0.0,
                                incidence_deg=0.0,
                                spanwise_control_points=None,
                                name_prefix="tail",
                                color="#a1d99b",
                            )
                        )
            else:
                parts.extend(
                    build_wing_mesh(
                        s_ref_m2=float(s_ref),
                        aspect_ratio=geom.wing.aspect_ratio,
                        taper_ratio=geom.wing.taper_ratio,
                        sweep_quarter_chord_deg=geom.wing.sweep_quarter_chord_deg,
                        t_c=geom.wing.t_c,
                        x_offset_m=wing_x,
                        z_offset_m=wing_z,
                    )
                )
                parts.extend(
                    build_tail_mesh(
                        wing_s_ref_m2=float(s_ref),
                        wing_aspect_ratio=geom.wing.aspect_ratio,
                        wing_taper_ratio=geom.wing.taper_ratio,
                        sweep_quarter_chord_deg=geom.wing.sweep_quarter_chord_deg,
                        t_c=geom.wing.t_c,
                        tail_area_ratio_to_wing=geom.tail.area_ratio_to_wing,
                        fuselage_length_m=geom.fuselage.length_m,
                        fuselage_diameter_m=geom.fuselage.diameter_m,
                    )
                )

            geom_json_path.write_text(
                json.dumps(
                    [{"name": p.name, "color": p.color, "vertices": p.vertices, "indices": p.indices} for p in parts],
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            html_written = False
            if isinstance(shape, dict) and shape:
                try:
                    generate_three_view_html(shape, str(geom_html_path))
                    html_written = True
                except Exception:
                    html_written = False
            if not html_written:
                geom_html_path.write_text(
                    render_geometry_viewer_html(parts=parts, title="Aircraft Geometry", layout=layout), encoding="utf-8"
                )
            geom_obj_path.write_text(mesh_to_obj(parts), encoding="utf-8")
            results["artifacts"] = {
                **(results.get("artifacts", {}) if isinstance(results.get("artifacts", {}), dict) else {}),
                "geometry_3d_html": _rel_out(geom_html_path),
                "geometry_obj": _rel_out(geom_obj_path),
                "geometry_mesh_json": _rel_out(geom_json_path),
            }

            def _planform_derived(*, s_m2: float, ar: float, taper: float, sweep: float = 0.0) -> dict:
                b = math.sqrt(max(1e-9, float(ar) * float(s_m2)))
                c_root = 2.0 * float(s_m2) / (b * (1.0 + float(taper)))
                c_tip = float(taper) * c_root

                mac_props = calculate_mac_properties(
                    s_ref_m2=float(s_m2),
                    aspect_ratio=float(ar),
                    taper_ratio=float(taper),
                    sweep_quarter_chord_deg=float(sweep),
                )

                return {
                    "s_ref_m2": float(s_m2),
                    "aspect_ratio": float(ar),
                    "taper_ratio": float(taper),
                    "b_m": b,
                    "c_root_m": c_root,
                    "c_tip_m": c_tip,
                    "mac_m": mac_props["mac_m"],
                    "mac_x_le_m": mac_props["mac_x_le_m"],
                    "mac_y_m": mac_props["mac_y_m"],
                }

            geo_shape_derived = {}
            if isinstance(fus_stations, list) and fus_stations:
                xs = [
                    float(s.get("x_m", 0.0))
                    for s in fus_stations
                    if isinstance(s, dict) and isinstance(s.get("x_m", None), (int, float))
                ]
                if xs:
                    geo_shape_derived["fuselage"] = {
                        "x_min_m": float(min(xs)),
                        "x_max_m": float(max(xs)),
                        "length_m": float(max(xs) - min(xs)),
                    }
            if "fuselage" not in geo_shape_derived:
                geo_shape_derived["fuselage"] = {
                    "length_m": float(geom.fuselage.length_m),
                    "diameter_m": float(geom.fuselage.diameter_m),
                }

            geo_shape_derived["wing"] = {
                **_planform_derived(
                    s_m2=float(s_ref),
                    ar=float(geom.wing.aspect_ratio),
                    taper=float(geom.wing.taper_ratio),
                    sweep=float(geom.wing.sweep_quarter_chord_deg),
                ),
                "sweep_quarter_chord_deg": float(geom.wing.sweep_quarter_chord_deg),
                "x_offset_m": float(wing_x),
                "y_offset_m": float(wing_y),
                "z_offset_m": float(wing_z),
                "dihedral_deg": float(wing_dihedral),
                "incidence_deg": float(wing_incidence),
            }

            if isinstance(derived_tail, dict):
                surfaces_out = []
                for sf in derived_tail.get("surfaces", []):
                    if not isinstance(sf, dict):
                        continue
                    s_m2 = float(sf.get("s_ref_m2", 0.0))
                    ar = float(sf.get("aspect_ratio", 0.0))
                    taper = float(sf.get("taper_ratio", 0.0))
                    sweep = float(sf.get("sweep_quarter_chord_deg", 0.0))
                    entry = {**sf}
                    if s_m2 > 0.0 and ar > 0.0 and taper > 0.0:
                        entry["derived"] = _planform_derived(s_m2=s_m2, ar=ar, taper=taper, sweep=sweep)
                    surfaces_out.append(entry)
                geo_shape_derived["tail"] = {
                    "layout": derived_tail.get("layout", {}),
                    "equivalent": derived_tail.get("equivalent", {}),
                    "horizontal": derived_tail.get("horizontal", None),
                    "vertical": derived_tail.get("vertical", None),
                    "surfaces": surfaces_out,
                }
            elif isinstance(tail_cfg, dict):
                t_out = {}
                ht = tail_cfg.get("horizontal", None)
                if isinstance(ht, dict):
                    pf = ht.get("planform", {}) if isinstance(ht.get("planform", {}), dict) else {}
                    s_ht = None
                    if isinstance(pf.get("s_ref_m2"), (int, float)):
                        s_ht = float(pf["s_ref_m2"])
                    elif isinstance(pf.get("area_ratio_to_wing"), (int, float)):
                        s_ht = float(s_ref) * max(0.0, float(pf["area_ratio_to_wing"]))
                    if (
                        s_ht is not None
                        and s_ht > 0.0
                        and isinstance(pf.get("aspect_ratio", None), (int, float))
                        and isinstance(pf.get("taper_ratio", None), (int, float))
                    ):
                        t_out["horizontal"] = {
                            **_planform_derived(
                                s_m2=float(s_ht), ar=float(pf["aspect_ratio"]), taper=float(pf["taper_ratio"])
                            ),
                            "sweep_quarter_chord_deg": float(pf.get("sweep_quarter_chord_deg", 0.0))
                            if isinstance(pf.get("sweep_quarter_chord_deg", None), (int, float))
                            else 0.0,
                            "x_offset_m": float(pf.get("x_offset_m", 0.0))
                            if isinstance(pf.get("x_offset_m", None), (int, float))
                            else 0.0,
                            "y_offset_m": float(pf.get("y_offset_m", 0.0))
                            if isinstance(pf.get("y_offset_m", None), (int, float))
                            else 0.0,
                            "z_offset_m": float(pf.get("z_offset_m", 0.0))
                            if isinstance(pf.get("z_offset_m", None), (int, float))
                            else 0.0,
                            "dihedral_deg": float(pf.get("dihedral_deg", 0.0))
                            if isinstance(pf.get("dihedral_deg", None), (int, float))
                            else 0.0,
                            "incidence_deg": float(pf.get("incidence_deg", 0.0))
                            if isinstance(pf.get("incidence_deg", None), (int, float))
                            else 0.0,
                        }
                vt = tail_cfg.get("vertical", None)
                if isinstance(vt, dict):
                    pf = vt.get("planform", {}) if isinstance(vt.get("planform", {}), dict) else {}
                    s_vt = None
                    if isinstance(pf.get("s_ref_m2"), (int, float)):
                        s_vt = float(pf["s_ref_m2"])
                    elif isinstance(pf.get("area_ratio_to_wing"), (int, float)):
                        s_vt = float(s_ref) * max(0.0, float(pf["area_ratio_to_wing"]))
                    if (
                        s_vt is not None
                        and s_vt > 0.0
                        and isinstance(pf.get("aspect_ratio", None), (int, float))
                        and isinstance(pf.get("taper_ratio", None), (int, float))
                    ):
                        t_out["vertical"] = {
                            **_planform_derived(
                                s_m2=float(s_vt), ar=float(pf["aspect_ratio"]), taper=float(pf["taper_ratio"])
                            ),
                            "sweep_quarter_chord_deg": float(pf.get("sweep_quarter_chord_deg", 0.0))
                            if isinstance(pf.get("sweep_quarter_chord_deg", None), (int, float))
                            else 0.0,
                            "x_offset_m": float(pf.get("x_offset_m", 0.0))
                            if isinstance(pf.get("x_offset_m", None), (int, float))
                            else 0.0,
                            "y_offset_m": float(pf.get("y_offset_m", 0.0))
                            if isinstance(pf.get("y_offset_m", None), (int, float))
                            else 0.0,
                            "z_offset_m": float(pf.get("z_offset_m", 0.0))
                            if isinstance(pf.get("z_offset_m", None), (int, float))
                            else 0.0,
                        }
                if t_out:
                    geo_shape_derived["tail"] = t_out

            results["geometry_shape_derived"] = geo_shape_derived

            tail_x = 0.55 * float(geom.fuselage.length_m)
            tail_y = 0.0
            tail_z = 0.35 * float(geom.fuselage.diameter_m)
            tail_inc = 0.0
            tail_surfaces_installs = []
            if isinstance(derived_tail, dict):
                ref_sf = None
                for sf in derived_tail.get("surfaces", []):
                    if isinstance(sf, dict) and sf.get("builder") == "wing_loft" and sf.get("name_prefix") == "htail":
                        ref_sf = sf
                        break
                if ref_sf is None:
                    for sf in derived_tail.get("surfaces", []):
                        if (
                            isinstance(sf, dict)
                            and sf.get("builder") == "wing_loft"
                            and sf.get("name_prefix") == "vtail"
                        ):
                            ref_sf = sf
                            break
                if ref_sf is None:
                    for sf in derived_tail.get("surfaces", []):
                        if isinstance(sf, dict) and sf.get("builder") == "vertical_loft" and sf.get("name") == "vtail":
                            ref_sf = sf
                            break
                if ref_sf is None:
                    sfs = derived_tail.get("surfaces", [])
                    ref_sf = sfs[0] if isinstance(sfs, list) and sfs and isinstance(sfs[0], dict) else None

                if isinstance(ref_sf, dict):
                    tail_x = float(ref_sf.get("x_offset_m", tail_x))
                    tail_y = float(ref_sf.get("y_offset_m", tail_y))
                    tail_z = float(ref_sf.get("z_offset_m", tail_z))
                    if isinstance(ref_sf.get("incidence_deg", None), (int, float)):
                        tail_inc = float(ref_sf.get("incidence_deg"))

                for sf in derived_tail.get("surfaces", []):
                    if not isinstance(sf, dict):
                        continue
                    sid = sf.get("name", None) if sf.get("builder") == "vertical_loft" else sf.get("name_prefix", None)
                    tail_surfaces_installs.append(
                        {
                            "id": str(sid) if isinstance(sid, str) else "tail",
                            "builder": str(sf.get("builder", "")),
                            "x_m": float(sf.get("x_offset_m", 0.0)),
                            "y_m": float(sf.get("y_offset_m", 0.0)),
                            "z_m": float(sf.get("z_offset_m", 0.0)),
                            "incidence_deg": float(sf.get("incidence_deg", 0.0))
                            if isinstance(sf.get("incidence_deg", None), (int, float))
                            else 0.0,
                            "dihedral_deg": float(sf.get("dihedral_deg", 0.0))
                            if isinstance(sf.get("dihedral_deg", None), (int, float))
                            else 0.0,
                        }
                    )
            elif isinstance(tail_cfg, dict):
                ht_cfg = tail_cfg.get("horizontal", None)
                if isinstance(ht_cfg, dict):
                    pf = ht_cfg.get("planform", {}) if isinstance(ht_cfg.get("planform", {}), dict) else {}
                    if isinstance(pf.get("x_offset_m", None), (int, float)):
                        tail_x = float(pf["x_offset_m"])
                    if isinstance(pf.get("y_offset_m", None), (int, float)):
                        tail_y = float(pf["y_offset_m"])
                    if isinstance(pf.get("z_offset_m", None), (int, float)):
                        tail_z = float(pf["z_offset_m"])
                    if isinstance(pf.get("incidence_deg", None), (int, float)):
                        tail_inc = float(pf["incidence_deg"])

            results["geometry_reference"] = {
                "units": {"length": "m", "angle": "deg"},
                "axes": {
                    "x": "forward",
                    "y": "right",
                    "z": "up",
                },
                "origin": "aircraft_body_reference",
                "installs": {
                    "fuselage": {"x_m": 0.0, "y_m": 0.0, "z_m": 0.0},
                    "wing": {
                        "x_m": float(wing_x),
                        "y_m": float(wing_y),
                        "z_m": float(wing_z),
                        "incidence_deg": float(wing_incidence),
                        "dihedral_deg": float(wing_dihedral),
                    },
                    "tail": {
                        "x_m": float(tail_x),
                        "y_m": float(tail_y),
                        "z_m": float(tail_z),
                        "incidence_deg": float(tail_inc),
                    },
                    "tail_surfaces": tail_surfaces_installs,
                },
            }
            results["geometry"] = {
                "shape": shape,
                "derived": geo_shape_derived,
                "reference": results["geometry_reference"],
            }

            results["geometry_validation"] = {
                "input": input_geometry_validation,
                "output": validate_geometry_shape_outputs(
                    shape=shape, derived=geo_shape_derived, reference=results["geometry_reference"]
                ),
            }
            results["geometry_field_map"] = geometry_field_map()

            openvsp_cfg = inputs.get("openvsp", None)
            if isinstance(openvsp_cfg, dict) and (openvsp_cfg.get("enabled") or openvsp_cfg.get("script_out_path")):
                p = None
                try:
                    out_p = openvsp_cfg.get("script_out_path", None)
                    script_path = (
                        Path(out_p).resolve()
                        if isinstance(out_p, str) and out_p.strip()
                        else (openvsp_dir / "openvsp_generate.py").resolve()
                    )
                    geom_bundle = resolve_geometry_bundle(results)
                    geom_ref = geom_bundle.get("reference", {}) if isinstance(geom_bundle, dict) else {}
                    ref_installs = (
                        geom_ref.get("installs", {}) if isinstance(geom_ref.get("installs", None), dict) else {}
                    )
                    fus_ref = (
                        ref_installs.get("fuselage", {}) if isinstance(ref_installs.get("fuselage", None), dict) else {}
                    )
                    wing_ref = ref_installs.get("wing", {}) if isinstance(ref_installs.get("wing", None), dict) else {}
                    tail_ref = ref_installs.get("tail", {}) if isinstance(ref_installs.get("tail", None), dict) else {}
                    xform = {
                        "fuselage": {
                            "x_m": float(fus_ref.get("x_m", 0.0)),
                            "y_m": float(fus_ref.get("y_m", 0.0)),
                            "z_m": float(fus_ref.get("z_m", 0.0)),
                        },
                        "wing": {
                            "x_m": float(wing_ref.get("x_m", wing_x)),
                            "y_m": float(wing_ref.get("y_m", wing_y)),
                            "z_m": float(wing_ref.get("z_m", wing_z)),
                            "y_rot_deg": float(wing_ref.get("incidence_deg", wing_incidence)),
                        },
                        "tail": {
                            "x_m": float(tail_ref.get("x_m", tail_x)),
                            "y_m": float(tail_ref.get("y_m", tail_y)),
                            "z_m": float(tail_ref.get("z_m", tail_z)),
                            "y_rot_deg": float(tail_ref.get("incidence_deg", tail_inc)),
                        },
                    }
                    p = write_openvsp_script(geom=geom, s_ref_m2=float(s_ref), out_path=script_path, xform=xform)
                    results["artifacts"]["openvsp_script"] = _rel_out(Path(p))
                    results["openvsp"] = {
                        "script_path": _rel_out(Path(p)),
                        "can_import_openvsp": can_import_openvsp(),
                        "ran": False,
                        "xform": xform,
                    }
                    if openvsp_cfg.get("run", False):
                        try:
                            run_openvsp_script(script_path=p)
                            results["openvsp"]["ran"] = True
                        except Exception as e:
                            results["openvsp"]["error"] = str(e)
                except Exception as e:
                    results["openvsp"] = {"error": str(e)}

            # Calculate Derived Geometric Stability Parameters
            if "wing" in geo_shape_derived:
                w_d = geo_shape_derived["wing"]
                mac_x_le = w_d.get("mac_x_le_m", 0.0)
                # Wing MAC global LE X = wing_x + mac_x_le (assuming no sweep/dihedral effect on mac local position?
                # actually mac_x_le_m from calculate_mac_properties is relative to root LE.
                # So global X = wing_x + mac_x_le_m.
                # If wing has sweep, it is already accounted for in mac_x_le_m (tan_sweep_le).

                # Update inputs.stability with derived values if not present
                if "stability" not in inputs:
                    inputs["stability"] = {}

                # Estimate X_AC_W (Aerodynamic Center of Wing) ~ 0.25 MAC
                # Global X_AC = Wing_X + MAC_X_LE + 0.25 * MAC
                mac = w_d.get("mac_m", 1.0)
                x_ac_w_global = float(wing_x) + mac_x_le + 0.25 * mac

                # Convert to normalized cbar (relative to wing LE or MAC LE?)
                # Usually inputs.stability.x_ac_w_cbar is relative to MAC LE.
                # If user provided x_ac_w_cbar, we assume it's relative to MAC LE.
                # If not, we set default 0.25.
                # But we need to check if we can calculate Tail Arm (lh).

                if "tail" in geo_shape_derived:
                    t_d = geo_shape_derived["tail"]
                    # Find Horizontal Tail MAC
                    ht_mac_x_global = None
                    ht_s_m2 = 0.0

                    # Try to find from surfaces
                    surfaces = t_d.get("surfaces", [])
                    for sf in surfaces:
                        if sf.get("name_prefix") == "htail" and "derived" in sf:
                            d = sf["derived"]
                            mac_t = d.get("mac_m", 0.0)
                            mac_x_le_t = d.get("mac_x_le_m", 0.0)
                            # Global X
                            tx = float(sf.get("x_offset_m", 0.0))
                            ht_mac_x_global = tx + mac_x_le_t + 0.25 * mac_t
                            ht_s_m2 = float(sf.get("s_ref_m2", 0.0))
                            break

                    if ht_mac_x_global is None and t_d.get("horizontal"):
                        # Fallback to horizontal dict
                        ht = t_d["horizontal"]
                        tx = float(ht.get("x_offset_m", 0.0))
                        d = ht.get("derived", {})  # Might not be populated if only using tail_cfg
                        # But we populated t_out["horizontal"] with _planform_derived
                        mac_t = float(ht.get("mac_m", 0.0))
                        mac_x_le_t = float(ht.get("mac_x_le_m", 0.0))
                        ht_mac_x_global = tx + mac_x_le_t + 0.25 * mac_t
                        ht_s_m2 = float(ht.get("s_ref_m2", 0.0))

                    if ht_mac_x_global is not None:
                        lh = ht_mac_x_global - x_ac_w_global
                        # Update inputs.tail.lh_m if not present or let stability use it
                        # The stability module uses inputs["tail"]["lh_m"]? No, it uses Vh.
                        # But tail_sizing.py uses lh_m.

                        # We should update Vh in stability input if possible?
                        # Vh = (S_h * lh) / (S_w * c_mac)
                        if ht_s_m2 > 0.0 and float(s_ref) > 0.0 and mac > 0.0:
                            vh_derived = (ht_s_m2 * lh) / (float(s_ref) * mac)
                            # Store derived stability params in results for reference
                            results.setdefault("stability_derived", {})["vh_geometric"] = vh_derived
                            results["stability_derived"]["lh_m"] = lh
                            results["stability_derived"]["x_ac_w_global_m"] = x_ac_w_global

                            # If stability input missing Vh, we could suggest or patch it?
                            # Currently run_fixed_wing_overall_design reads Vh from inputs["tail"]["vh"].
                            # If we want to close the loop, we should probably update inputs["tail"]["vh"] if it was just a placeholder.
                            # But inputs["tail"]["vh"] is typically an INPUT target.
                            # If we have a geometry, the geometry dictates Vh.
                            # So we should probably override inputs["tail"]["vh"] with derived Vh for the stability calculation step?
                            # But run_fixed_wing_overall_design is already called.

                            # We can re-run stability estimate with derived Vh
                            pass

    constraints = results.get("constraints", {})
    plot = constraints.get("plot_data", {})
    design_point = constraints.get("design_point", {})
    svg = render_constraints_ws_tw_svg(plot_data=plot, design_point=design_point)
    if svg:
        with plot_path.open("w", encoding="utf-8") as f:
            f.write(svg + "\n")

    report_md = render_markdown_report(results)
    with report_path.open("w", encoding="utf-8") as f:
        f.write(report_md)

    with results_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Wrote: {results_path}")
    print(f"Wrote: {report_path}")
    if svg:
        print(f"Wrote: {plot_path}")
    if geom is not None and geom_html_path.exists():
        print(f"Wrote: {geom_html_path}")
        print(f"Wrote: {geom_obj_path}")
        print(f"Wrote: {geom_json_path}")
    if advanced_results_path.exists():
        print(f"Wrote: {advanced_results_path}")
    if area_rule_report_path.exists():
        print(f"Wrote: {area_rule_report_path}")
    if openvsp_advanced_path.exists():
        print(f"Wrote: {openvsp_advanced_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
