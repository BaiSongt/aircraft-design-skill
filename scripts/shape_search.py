from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aircraft_design.geometry_parametric import ParametricGeometry


def _ensure_project_root() -> None:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def _build_geom_fallback(inputs: dict) -> ParametricGeometry | None:
    _ensure_project_root()
    from aircraft_design.geometry_parametric import (
        Fuselage,
        ParametricGeometry,
        Tail,
        WingPlanform,
        geometry_from_inputs,
    )

    geom = geometry_from_inputs(inputs)
    if geom is not None:
        return geom
    if not isinstance(inputs.get("geometry", None), dict) or not isinstance(inputs.get("sizing", None), dict):
        return None
    g = inputs.get("geometry", {})
    s = inputs.get("sizing", {})
    ar = s.get("aspect_ratio", None)
    if not isinstance(ar, (int, float)):
        return None
    return ParametricGeometry(
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


def _get_range(cfg: dict, key: str, default_min: float, default_max: float) -> tuple[float, float]:
    v = cfg.get(key, None)
    if isinstance(v, dict) and isinstance(v.get("min"), (int, float)) and isinstance(v.get("max"), (int, float)):
        return float(v["min"]), float(v["max"])
    return float(default_min), float(default_max)


def _clamp(x: float, lo: float, hi: float) -> float:
    return min(max(float(x), float(lo)), float(hi))


def _candidate_geom(base: ParametricGeometry, cfg: dict, rng: random.Random) -> ParametricGeometry:
    _ensure_project_root()
    from aircraft_design.geometry_parametric import Fuselage, ParametricGeometry, Tail, WingPlanform

    ar_min, ar_max = _get_range(cfg, "aspect_ratio", base.wing.aspect_ratio * 0.8, base.wing.aspect_ratio * 1.2)
    taper_min, taper_max = _get_range(cfg, "taper_ratio", 0.25, 0.65)
    sweep_min, sweep_max = _get_range(cfg, "sweep_quarter_chord_deg", 0.0, 15.0)
    tc_min, tc_max = _get_range(cfg, "t_c", 0.09, 0.15)

    fus_l_min, fus_l_max = _get_range(
        cfg, "fuselage_length_m", base.fuselage.length_m * 0.9, base.fuselage.length_m * 1.1
    )
    fus_d_min, fus_d_max = _get_range(
        cfg, "fuselage_diameter_m", base.fuselage.diameter_m * 0.9, base.fuselage.diameter_m * 1.1
    )
    tail_min, tail_max = _get_range(cfg, "tail_area_ratio_to_wing", 0.16, 0.30)

    wing = WingPlanform(
        aspect_ratio=_clamp(rng.uniform(ar_min, ar_max), 4.0, 16.0),
        taper_ratio=_clamp(rng.uniform(taper_min, taper_max), 0.05, 1.0),
        sweep_quarter_chord_deg=_clamp(rng.uniform(sweep_min, sweep_max), 0.0, 45.0),
        t_c=_clamp(rng.uniform(tc_min, tc_max), 0.05, 0.25),
    )
    fus = Fuselage(
        length_m=_clamp(rng.uniform(fus_l_min, fus_l_max), 1.0, 50.0),
        diameter_m=_clamp(rng.uniform(fus_d_min, fus_d_max), 0.2, 10.0),
    )
    tail = Tail(area_ratio_to_wing=_clamp(rng.uniform(tail_min, tail_max), 0.0, 1.0))
    return ParametricGeometry(wing=wing, fuselage=fus, tail=tail)


def _mesh_html_for_candidate(
    *,
    geom: ParametricGeometry,
    s_ref_m2: float,
    out_path: Path,
    title: str,
    wing_airfoil: list | None,
    wing_tip_airfoil: list | None,
    wing_spanwise_cps: list | None,
    fus_stations: list | None,
) -> None:
    _ensure_project_root()
    from aircraft_design.visualization_3d import (
        MeshPart,
        build_fuselage_cylinder,
        build_fuselage_loft,
        build_tail_mesh,
        build_wing_airfoil_loft_mesh,
        build_wing_mesh,
        render_geometry_viewer_html,
    )

    parts: list[MeshPart] = []
    if isinstance(fus_stations, list) and fus_stations:
        parts.append(build_fuselage_loft(stations=fus_stations))
    else:
        parts.append(build_fuselage_cylinder(length_m=geom.fuselage.length_m, diameter_m=geom.fuselage.diameter_m))

    if isinstance(wing_airfoil, list) and wing_airfoil:
        parts.extend(
            build_wing_airfoil_loft_mesh(
                root_airfoil_coords=wing_airfoil,
                tip_airfoil_coords=wing_tip_airfoil
                if isinstance(wing_tip_airfoil, list) and wing_tip_airfoil
                else None,
                s_ref_m2=float(s_ref_m2),
                aspect_ratio=geom.wing.aspect_ratio,
                taper_ratio=geom.wing.taper_ratio,
                sweep_quarter_chord_deg=geom.wing.sweep_quarter_chord_deg,
                x_offset_m=0.0,
                z_offset_m=0.0,
                spanwise_control_points=wing_spanwise_cps if isinstance(wing_spanwise_cps, list) else None,
                name_prefix="wing",
                color="#2c7fb8",
            )
        )
        s_tail = float(s_ref_m2) * max(0.0, float(geom.tail.area_ratio_to_wing))
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
                    z_offset_m=0.35 * float(geom.fuselage.diameter_m),
                    spanwise_control_points=None,
                    name_prefix="tail",
                    color="#a1d99b",
                )
            )
    else:
        parts.extend(
            build_wing_mesh(
                s_ref_m2=float(s_ref_m2),
                aspect_ratio=geom.wing.aspect_ratio,
                taper_ratio=geom.wing.taper_ratio,
                sweep_quarter_chord_deg=geom.wing.sweep_quarter_chord_deg,
                t_c=geom.wing.t_c,
                x_offset_m=0.0,
                z_offset_m=0.0,
            )
        )
        parts.extend(
            build_tail_mesh(
                wing_s_ref_m2=float(s_ref_m2),
                wing_aspect_ratio=geom.wing.aspect_ratio,
                wing_taper_ratio=geom.wing.taper_ratio,
                sweep_quarter_chord_deg=geom.wing.sweep_quarter_chord_deg,
                t_c=geom.wing.t_c,
                tail_area_ratio_to_wing=geom.tail.area_ratio_to_wing,
                fuselage_length_m=geom.fuselage.length_m,
                fuselage_diameter_m=geom.fuselage.diameter_m,
            )
        )
    out_path.write_text(render_geometry_viewer_html(parts=parts, title=title), encoding="utf-8")


def main() -> int:
    _ensure_project_root()
    from aircraft_design.fixed_wing_overall import run_fixed_wing_overall_design
    from aircraft_design.geometry_detailed import geometry_detailed_from_inputs
    from aircraft_design.geometry_shape import geometry_shape_from_inputs
    from aircraft_design.input_schema import normalize_inputs, validate_run_inputs

    if len(sys.argv) < 2:
        print("Usage: python scripts/shape_search.py <input.json> [--n N] [--seed S]")
        return 2

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        print(f"Input not found: {input_path}")
        return 2

    n = 16
    seed = 0
    i = 2
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == "--n" and i + 1 < len(sys.argv):
            n = int(sys.argv[i + 1])
            i += 2
            continue
        if a == "--seed" and i + 1 < len(sys.argv):
            seed = int(sys.argv[i + 1])
            i += 2
            continue
        print(f"Unknown arg: {a}")
        return 2

    base_inputs = json.loads(input_path.read_text(encoding="utf-8"))
    try:
        if not base_inputs.get("_normalized", False):
            base_inputs, _warnings = normalize_inputs(base_inputs)
    except Exception as e:
        print(f"Input normalization failed: {e}")
        return 2
    validation = validate_run_inputs(base_inputs)
    if validation.get("warnings"):
        print("Input validation warnings:")
        for w in validation["warnings"]:
            print(f"- {w}")
    if validation.get("errors"):
        print("Input validation failed:")
        for err in validation["errors"]:
            print(f"- {err}")
        return 2
    base_geom = _build_geom_fallback(base_inputs)
    if base_geom is None:
        print("No geometry available. Provide geometry_parametric, or provide legacy geometry + sizing.aspect_ratio.")
        return 2

    shape = geometry_shape_from_inputs(base_inputs) or {}
    detailed = geometry_detailed_from_inputs(base_inputs) or {}
    wing_airfoil = None
    wing_tip_airfoil = None
    wing_spanwise_cps = None
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

    cfg = base_inputs.get("geometry_search", {})
    if cfg is None:
        cfg = {}
    if not isinstance(cfg, dict):
        print("geometry_search must be an object.")
        return 2

    rng = random.Random(seed)

    out_dir = Path("out").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    shapes_dir = out_dir / "shapes"
    shapes_dir.mkdir(parents=True, exist_ok=True)

    candidates: list[dict] = []
    for k in range(max(1, n)):
        geom_k = _candidate_geom(base_geom, cfg, rng)
        inp = json.loads(json.dumps(base_inputs, ensure_ascii=False))
        if isinstance(inp.get("aero", None), dict):
            inp["aero"] = dict(inp["aero"])
            inp["aero"].pop("cd0", None)
        inp["geometry_parametric"] = {
            "wing": {
                "aspect_ratio": geom_k.wing.aspect_ratio,
                "taper_ratio": geom_k.wing.taper_ratio,
                "sweep_quarter_chord_deg": geom_k.wing.sweep_quarter_chord_deg,
                "t_c": geom_k.wing.t_c,
            },
            "fuselage": {"length_m": geom_k.fuselage.length_m, "diameter_m": geom_k.fuselage.diameter_m},
            "tail": {"area_ratio_to_wing": geom_k.tail.area_ratio_to_wing},
        }
        inp["_skip_uncertainty"] = True
        try:
            res = run_fixed_wing_overall_design(inp)
            feasible = bool(res.get("constraints", {}).get("feasible", False))
            w0 = res.get("weights", {}).get("w0_kg", None)
            cd0 = res.get("aero", {}).get("cd0_buildup", None)
            s_ref = res.get("sizing", {}).get("s_m2", None)
            worst = res.get("constraints", {}).get("worst", {})
            driver = worst.get("name", "") if isinstance(worst, dict) else ""
            margin = worst.get("margin", None) if isinstance(worst, dict) else None

            html_name = None
            if isinstance(s_ref, (int, float)) and float(s_ref) > 0.0:
                html_name = f"shape_{k:03d}.html"
                _mesh_html_for_candidate(
                    geom=geom_k,
                    s_ref_m2=float(s_ref),
                    out_path=(shapes_dir / html_name),
                    title=f"Candidate {k:03d}",
                    wing_airfoil=wing_airfoil,
                    wing_tip_airfoil=wing_tip_airfoil,
                    wing_spanwise_cps=wing_spanwise_cps,
                    fus_stations=fus_stations,
                )

            candidates.append(
                {
                    "id": k,
                    "feasible": feasible,
                    "objective_w0_kg": w0,
                    "cd0_buildup": cd0,
                    "worst_constraint": {"name": driver, "margin": margin},
                    "geometry_parametric": inp["geometry_parametric"],
                    "artifact_html": f"shapes/{html_name}" if html_name else None,
                }
            )
        except Exception as e:
            candidates.append(
                {"id": k, "feasible": False, "error": str(e), "geometry_parametric": inp.get("geometry_parametric", {})}
            )

    def _score(c: dict) -> float:
        w0 = c.get("objective_w0_kg", None)
        if isinstance(w0, (int, float)):
            return float(w0)
        return float("inf")

    feas = [c for c in candidates if c.get("feasible") is True]
    feas_sorted = sorted(feas, key=_score)[: min(10, len(feas))]

    report_lines: list[str] = []
    report_lines.append("# 外形创成式搜索（简版）")
    report_lines.append("")
    report_lines.append(f"- 样本数：{len(candidates)}")
    report_lines.append(f"- 可行数：{len(feas)}")
    report_lines.append("")

    def _fmt(x, nd=3):
        if x is None:
            return "-"
        if isinstance(x, bool):
            return "true" if x else "false"
        if isinstance(x, (int, float)):
            return f"{float(x):.{nd}f}".rstrip("0").rstrip(".")
        return str(x)

    rows = []
    for c in feas_sorted:
        w0 = c.get("objective_w0_kg", None)
        cd0 = c.get("cd0_buildup", None)
        wc = c.get("worst_constraint", {}) if isinstance(c.get("worst_constraint", {}), dict) else {}
        link = c.get("artifact_html", None)
        rows.append(
            [
                str(c.get("id")),
                _fmt(w0, nd=1),
                _fmt(cd0, nd=4),
                str(wc.get("name", "")),
                _fmt(wc.get("margin", None), nd=3),
                f"[3D]({link})" if isinstance(link, str) else "-",
            ]
        )
    if rows:
        report_lines.append("| id | w0_kg | cd0_buildup | driver | margin | 3D |")
        report_lines.append("| --- | --- | --- | --- | --- | --- |")
        for r in rows:
            report_lines.append("| " + " | ".join(r) + " |")
        report_lines.append("")
    else:
        report_lines.append("- 未找到可行解（可扩大搜索范围或提高推重比/降低翼载等）。")
        report_lines.append("")

    out_json = out_dir / "shape_search_results.json"
    out_md = out_dir / "shape_search_report.md"
    out_json.write_text(
        json.dumps({"candidates": candidates, "top_feasible": feas_sorted}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    out_md.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Wrote: {out_json}")
    print(f"Wrote: {out_md}")
    if feas_sorted:
        print(f"Wrote: {shapes_dir}/*.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
