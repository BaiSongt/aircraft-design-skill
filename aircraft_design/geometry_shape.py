from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin, sqrt, tan
from typing import Any

from .geometry_detailed import naca4_coordinates


@dataclass(frozen=True)
class LayoutConfig:
    views: list[str]
    rows: int
    cols: int


def _get_dict(d: dict, key: str) -> dict | None:
    v = d.get(key, None)
    return v if isinstance(v, dict) else None


def _clamp(x: float, lo: float, hi: float) -> float:
    return min(max(float(x), float(lo)), float(hi))


def _linspace(a: float, b: float, n: int) -> list[float]:
    if n <= 1:
        return [float(a)]
    step = (float(b) - float(a)) / (n - 1)
    return [float(a) + i * step for i in range(n)]


def _infer_s_ref_from_tail(tail_cfg: dict) -> float | None:
    for key in ["horizontal", "vertical"]:
        section = tail_cfg.get(key, None)
        if not isinstance(section, dict):
            continue
        pf = section.get("planform", None)
        if not isinstance(pf, dict):
            continue
        s_tail = pf.get("s_ref_m2", None)
        ratio = pf.get("area_ratio_to_wing", None)
        if isinstance(s_tail, (int, float)) and isinstance(ratio, (int, float)) and float(ratio) > 0.0:
            return float(s_tail) / float(ratio)
    return None


def fuselage_stations_from_control_points(
    *, length_m: float, max_radius_y_m: float, max_radius_z_m: float, control_points: list[dict], n_stations: int
) -> list[dict]:
    if length_m <= 0.0:
        raise ValueError("length_m must be positive.")
    if max_radius_y_m <= 0.0 or max_radius_z_m <= 0.0:
        raise ValueError("max_radius_y_m and max_radius_z_m must be positive.")
    if not isinstance(control_points, list) or len(control_points) < 2:
        raise ValueError("control_points must be a list with at least 2 items.")
    n = max(5, int(n_stations))

    cps = []
    for p in control_points:
        if not isinstance(p, dict):
            raise ValueError("Each control point must be an object.")
        xr = p.get("x_rel", None)
        rr = p.get("radius_rel", None)
        ry = p.get("radius_y_rel", None)
        rz = p.get("radius_z_rel", None)
        n_val = p.get("n", 2.0)  # Super-ellipse exponent, default 2.0 (ellipse)

        if not isinstance(xr, (int, float)):
            raise ValueError("Each control point requires numeric x_rel.")
        if not isinstance(n_val, (int, float)):
            raise ValueError("n must be numeric.")

        if rr is not None:
            if not isinstance(rr, (int, float)):
                raise ValueError("radius_rel must be numeric when provided.")
            cps.append((float(xr), float(rr), float(rr), float(n_val)))
        else:
            if not isinstance(ry, (int, float)) or not isinstance(rz, (int, float)):
                raise ValueError("Each control point requires radius_rel or both radius_y_rel and radius_z_rel.")
            cps.append((float(xr), float(ry), float(rz), float(n_val)))
    cps.sort(key=lambda t: t[0])
    xs = [_clamp(x, 0.0, 1.0) for x, _, _, _ in cps]
    rys = [_clamp(r, 0.0, 1.0) for _, r, _, _ in cps]
    rzs = [_clamp(r, 0.0, 1.0) for _, _, r, _ in cps]
    ns = [float(n) for _, _, _, n in cps]

    def interp(xq: float, *, ys: list[float]) -> float:
        if xq <= xs[0]:
            return ys[0]
        if xq >= xs[-1]:
            return ys[-1]
        for i in range(len(xs) - 1):
            if xs[i] <= xq <= xs[i + 1]:
                t = (xq - xs[i]) / max(1e-9, xs[i + 1] - xs[i])
                return ys[i] * (1.0 - t) + ys[i + 1] * t
        return ys[-1]

    stations = []
    for xr in _linspace(0.0, 1.0, n):
        ry = interp(xr, ys=rys) * float(max_radius_y_m)
        rz = interp(xr, ys=rzs) * float(max_radius_z_m)
        n_curr = interp(xr, ys=ns)
        stations.append(
            {"x_m": xr * float(length_m), "radius_y_m": float(ry), "radius_z_m": float(rz), "n": float(n_curr)}
        )
    return stations


def generate_fuselage_control_points_advanced(
    *,
    nose_fineness_ratio: float,
    tail_fineness_ratio: float,
    length_m: float,
    diameter_m: float,
    nose_shape: str = "ellipsoid",
    tail_shape: str = "conical",
) -> list[dict]:
    """
    Generate control points for a fuselage based on fineness ratios.
    """
    if length_m <= 0 or diameter_m <= 0:
        return [{"x_rel": 0.0, "radius_rel": 0.0}, {"x_rel": 1.0, "radius_rel": 0.0}]

    r_max = diameter_m / 2.0
    l_nose = nose_fineness_ratio * diameter_m
    l_tail = tail_fineness_ratio * diameter_m

    # Safety check: if nose+tail > length, scale down
    if l_nose + l_tail > length_m:
        factor = length_m / (l_nose + l_tail)
        l_nose *= factor
        l_tail *= factor
        l_cyl = 0.0
    else:
        l_cyl = length_m - l_nose - l_tail

    pts = []

    # Nose points (0 to l_nose)
    n_nose = 5
    for i in range(n_nose + 1):
        if l_nose <= 0:
            if i == 0:
                pts.append({"x_rel": 0.0, "radius_rel": 0.0, "n": 2.0})
            continue

        x = (i / n_nose) * l_nose
        x_rel = x / length_m

        # Radius profile
        if nose_shape == "conical":
            r = r_max * (x / l_nose)
        else:  # ellipsoid default
            # 1/4 ellipse: x=0->r=0, x=l_nose->r=r_max
            # (r/r_max)^2 + ((l_nose-x)/l_nose)^2 = 1
            r = r_max * sqrt(max(0.0, 1.0 - ((l_nose - x) / l_nose) ** 2))

        pts.append({"x_rel": x_rel, "radius_rel": r / r_max, "n": 2.0})

    # Cylindrical section
    if l_cyl > 0:
        # Add end of cylinder (start is handled by last point of nose)
        x_end = l_nose + l_cyl
        pts.append({"x_rel": x_end / length_m, "radius_rel": 1.0, "n": 2.0})

    # Tail points
    n_tail = 5
    x_start_tail = length_m - l_tail
    for i in range(1, n_tail + 1):
        if l_tail <= 0:
            break
        dt = (i / n_tail) * l_tail
        x = x_start_tail + dt
        x_rel = x / length_m

        if tail_shape == "conical":
            # Linear from r_max to 0
            r = r_max * (1.0 - dt / l_tail)
        else:  # parabolic (smooth match to cylinder)
            # r = r_max * (1 - (dt/l_tail)^2)
            r = r_max * (1.0 - (dt / l_tail) ** 2)

        pts.append({"x_rel": x_rel, "radius_rel": r / r_max, "n": 2.0})

    # Sort and dedup x_rel slightly?
    # Logic guarantees order.
    return pts


def calculate_mac_properties(
    *, s_ref_m2: float, aspect_ratio: float, taper_ratio: float, sweep_quarter_chord_deg: float
) -> dict[str, float]:
    """
    Calculate Mean Aerodynamic Chord (MAC) properties for a trapezoidal planform.

    Returns:
        dict: {
            "mac_m": float,         # MAC length
            "mac_x_le_m": float,    # X offset of MAC leading edge relative to root LE
            "mac_y_m": float        # Y offset of MAC from centerline
        }
    """
    s = float(s_ref_m2)
    ar = float(aspect_ratio)
    lam = float(taper_ratio)
    sweep_qc = radians(float(sweep_quarter_chord_deg))

    if s <= 0.0 or ar <= 0.0:
        return {"mac_m": 0.0, "mac_x_le_m": 0.0, "mac_y_m": 0.0}

    b = sqrt(ar * s)
    c_root = 2.0 * s / (b * (1.0 + lam))

    # MAC length
    # c_mac = (2/3) * c_root * (1 + lambda + lambda^2) / (1 + lambda)
    c_mac = (2.0 / 3.0) * c_root * (1.0 + lam + lam**2) / (1.0 + lam)

    # MAC Y position
    # y_mac = (b/6) * (1 + 2*lambda) / (1 + lambda)
    y_mac = (b / 6.0) * (1.0 + 2.0 * lam) / (1.0 + lam)

    # Calculate sweep of leading edge
    # tan(sweep_le) = tan(sweep_qc) + (1 - lambda)/(AR * (1 + lambda)) * (c_root/c_root cancels out?)
    # Wait, simple geometry:
    # x_qc_root = 0.25 * c_root
    # x_qc_tip = x_qc_root + (b/2) * tan(sweep_qc)
    # x_le_tip = x_qc_tip - 0.25 * (lambda * c_root)
    # tan(sweep_le) = (x_le_tip - 0) / (b/2)
    #               = (0.25*c_root + (b/2)*tan(sweep_qc) - 0.25*lambda*c_root) / (b/2)
    #               = tan(sweep_qc) + 0.25 * c_root * (1 - lambda) / (b/2)
    #               = tan(sweep_qc) + 0.5 * c_root * (1 - lambda) / (b/2) * 0.5 ?? No.
    # tan(sweep_le) = tan(sweep_qc) + (0.25 * c_root * (1 - lambda)) / (b/2)
    # And c_root / (b/2) = 4 / (AR * (1 + lambda))
    # So tan(sweep_le) = tan(sweep_qc) + (1 - lambda) / (AR * (1 + lambda))

    tan_sweep_le = tan(sweep_qc) + (1.0 - lam) / (ar * (1.0 + lam))
    x_le_mac = y_mac * tan_sweep_le

    return {"mac_m": c_mac, "mac_x_le_m": x_le_mac, "mac_y_m": y_mac}


def apply_canopy_bump(stations: list[dict], canopy: dict):
    """
    Modify fuselage stations to include a canopy bump.
    canopy: {x_rel: float, length_rel: float, height_m: float}
    """
    if not stations:
        return

    xs = [s["x_m"] for s in stations]
    if not xs:
        return
    x_min, x_max = min(xs), max(xs)
    l_fus = x_max - x_min

    x_c_start = x_min + float(canopy.get("x_rel", 0.2)) * l_fus
    l_c = float(canopy.get("length_rel", 0.15)) * l_fus
    h_c = float(canopy.get("height_m", 0.3))

    if l_c <= 0:
        return

    for s in stations:
        x = s["x_m"]
        if x_c_start <= x <= x_c_start + l_c:
            xc = (x - x_c_start) / l_c
            # Bubble shape: sin(pi * xc)
            # Add to radius_z
            bump = h_c * sin(3.1415926535 * xc)
            # Assuming radius_z is the vertical extent.
            # Note: This stretches the whole section vertically.
            # Ideally we only lift the top control point, but station is defined by radius_z.
            # Phase 8.1 super-ellipse allows asymmetric? No, currently symmetric radius_z.
            # TODO: Support asymmetric top/bottom radius in future.
            s["radius_z_m"] = float(s["radius_z_m"]) + bump


def apply_wing_body_fairing(stations: list[dict], wing_root_x_le: float, wing_root_c: float, radius_m: float):
    """
    Modify fuselage stations to simulate a wing-body fairing (fillet).
    """
    if not stations or radius_m <= 0:
        return

    x_start = wing_root_x_le - 0.1 * wing_root_c
    x_end = wing_root_x_le + wing_root_c + 0.1 * wing_root_c
    l_fair = x_end - x_start

    if l_fair <= 0:
        return

    for s in stations:
        x = s["x_m"]
        if x_start <= x <= x_end:
            xf = (x - x_start) / l_fair
            # Smooth bump
            bump = radius_m * sin(3.1415926535 * xf)
            s["radius_y_m"] = float(s["radius_y_m"]) + bump


def verify_geometric_constraints(geometry: dict, constraints: dict) -> list[dict]:
    """
    Verify if hardpoints are inside the fuselage.
    Returns list of violations: {constraint_name, message, severity}
    """
    violations = []
    stations = geometry.get("fuselage", {}).get("stations", [])
    if not stations:
        return [{"name": "Global", "message": "No fuselage geometry", "severity": "critical"}]

    # Pre-process stations for fast lookup
    f_xs: list[float] = [float(s["x_m"]) for s in stations]
    f_rys: list[float] = [float(s["radius_y_m"]) for s in stations]
    f_rzs: list[float] = [float(s["radius_z_m"]) for s in stations]
    f_ns: list[float] = [float(s.get("n", 2.0)) for s in stations]

    combined = sorted(zip(f_xs, f_rys, f_rzs, f_ns), key=lambda t: t[0])
    if combined:
        f_xs, f_rys, f_rzs, f_ns = map(list, zip(*combined))
    else:
        f_xs, f_rys, f_rzs, f_ns = [], [], [], []

    def get_props(x):
        if not f_xs:
            return 0, 0, 2
        if x <= f_xs[0] or x >= f_xs[-1]:
            return 0, 0, 2  # Outside
        for i in range(len(f_xs) - 1):
            if f_xs[i] <= x <= f_xs[i + 1]:
                t = (x - f_xs[i]) / (f_xs[i + 1] - f_xs[i])
                return (
                    f_rys[i] * (1 - t) + f_rys[i + 1] * t,
                    f_rzs[i] * (1 - t) + f_rzs[i + 1] * t,
                    f_ns[i] * (1 - t) + f_ns[i + 1] * t,
                )
        return 0, 0, 2

    hardpoints = constraints.get("hardpoints", {})
    for name, point in hardpoints.items():
        px, py, pz = float(point.get("x", 0)), float(point.get("y", 0)), float(point.get("z", 0))

        # Check if inside fuselage at x=px
        ry, rz, n = get_props(px)
        if ry <= 1e-6 or rz <= 1e-6:
            violations.append(
                {
                    "name": name,
                    "message": f"Point at x={px:.2f} is outside fuselage longitudinal range or zero section.",
                    "severity": "error",
                }
            )
            continue

        # Super-ellipse check: (y/ry)^n + (z/rz)^n <= 1
        val = (abs(py) / ry) ** n + (abs(pz) / rz) ** n
        if val > 1.0:
            violations.append(
                {
                    "name": name,
                    "message": f"Point ({px:.2f}, {py:.2f}, {pz:.2f}) is outside fuselage skin (val={val:.2f}).",
                    "severity": "error",
                }
            )

    return violations


def geometry_shape_from_inputs(inputs: dict) -> dict | None:
    gs = inputs.get("geometry_shape", None)
    if gs is None:
        return None
    if not isinstance(gs, dict):
        raise ValueError("geometry_shape must be an object.")

    out: dict[str, Any] = {"raw": gs}

    layout = _get_dict(gs, "layout") or {}
    views = layout.get("views", ["top", "side", "front", "iso"])
    if not isinstance(views, list) or not all(isinstance(v, str) for v in views):
        raise ValueError("geometry_shape.layout.views must be a list of strings.")
    grid = _get_dict(layout, "grid") or {}
    rows = int(grid.get("rows", 2))
    cols = int(grid.get("cols", 2))
    out["layout"] = {"views": views, "grid": {"rows": rows, "cols": cols}}

    res = _get_dict(gs, "resolution") or {}
    fus_n = int(res.get("fuselage_n_stations", 21))
    airfoil_n = int(res.get("airfoil_n_points", 161))
    out["resolution"] = {"fuselage_n_stations": fus_n, "airfoil_n_points": airfoil_n}

    fus = _get_dict(gs, "fuselage") or {}
    axis = _get_dict(fus, "axis") or {}
    length_m = axis.get("length_m", None)
    if not isinstance(length_m, (int, float)):
        raise ValueError("geometry_shape.fuselage.axis.length_m is required and must be numeric.")
    length_m_f = float(length_m)

    profile = _get_dict(fus, "profile") or {}
    mode = str(profile.get("mode", "control_points")).strip().lower()
    if mode == "stations":
        st = profile.get("stations", None)
        if not isinstance(st, list) or not st:
            raise ValueError("geometry_shape.fuselage.profile.stations must be a non-empty list.")
        out["fuselage"] = {"stations": st}
    elif mode == "control_points":
        cps = profile.get("control_points", None)
        if not isinstance(cps, list) or not cps:
            raise ValueError("geometry_shape.fuselage.profile.control_points must be a non-empty list.")
        max_r = profile.get("max_radius_m", None)
        max_ry = profile.get("max_radius_y_m", None)
        max_rz = profile.get("max_radius_z_m", None)
        if max_r is not None:
            if not isinstance(max_r, (int, float)):
                raise ValueError("geometry_shape.fuselage.profile.max_radius_m must be numeric when provided.")
            max_ry_f = float(max_r)
            max_rz_f = float(max_r)
        else:
            if not isinstance(max_ry, (int, float)) or not isinstance(max_rz, (int, float)):
                raise ValueError(
                    "geometry_shape.fuselage.profile requires max_radius_m or both max_radius_y_m and max_radius_z_m."
                )
            max_ry_f = float(max_ry)
            max_rz_f = float(max_rz)
        out["fuselage"] = {
            "stations": fuselage_stations_from_control_points(
                length_m=length_m_f,
                max_radius_y_m=max_ry_f,
                max_radius_z_m=max_rz_f,
                control_points=cps,
                n_stations=fus_n,
            )
        }
    elif mode == "parametric":
        nose_fr = float(profile.get("nose_fineness_ratio", 2.0))
        tail_fr = float(profile.get("tail_fineness_ratio", 3.0))
        nose_sh = str(profile.get("nose_shape", "ellipsoid")).strip().lower()
        tail_sh = str(profile.get("tail_shape", "conical")).strip().lower()

        max_r = profile.get("max_radius_m", None)
        max_ry = profile.get("max_radius_y_m", None)
        max_rz = profile.get("max_radius_z_m", None)

        if max_r is not None:
            if not isinstance(max_r, (int, float)):
                raise ValueError("geometry_shape.fuselage.profile.max_radius_m must be numeric.")
            max_ry_f = float(max_r)
            max_rz_f = float(max_r)
            dia = max_ry_f * 2.0
        else:
            if not isinstance(max_ry, (int, float)) or not isinstance(max_rz, (int, float)):
                raise ValueError(
                    "geometry_shape.fuselage.profile requires max_radius_m or both max_radius_y_m and max_radius_z_m."
                )
            max_ry_f = float(max_ry)
            max_rz_f = float(max_rz)
            dia = max_ry_f * 2.0

        cps = generate_fuselage_control_points_advanced(
            nose_fineness_ratio=nose_fr,
            tail_fineness_ratio=tail_fr,
            length_m=length_m_f,
            diameter_m=dia,
            nose_shape=nose_sh,
            tail_shape=tail_sh,
        )

        out["fuselage"] = {
            "stations": fuselage_stations_from_control_points(
                length_m=length_m_f,
                max_radius_y_m=max_ry_f,
                max_radius_z_m=max_rz_f,
                control_points=cps,
                n_stations=fus_n,
            )
        }
    else:
        raise ValueError(f"Unsupported fuselage profile mode: {mode}")

    def parse_airfoil(af: dict) -> dict:
        aft = str(af.get("type", "naca4")).strip().lower()
        code = str(af.get("code", "")).strip()
        if aft != "naca4":
            raise ValueError(f"Unsupported airfoil type: {aft}")
        
        # Parse NACA 4 digit code
        if len(code) != 4 or not code.isdigit():
             # Default to 0012 if invalid
             code = "0012"
             
        m_code = int(code[0])
        p_code = int(code[1])
        t_code = int(code[2:])
        
        max_camber = m_code / 100.0
        max_camber_location = p_code / 10.0
        max_thickness = t_code / 100.0
        
        # Handle symmetric airfoils where p=0
        if max_camber_location <= 0.0:
            max_camber_location = 0.4 
            
        coords_obj = naca4_coordinates(
            max_camber=max_camber,
            max_camber_location=max_camber_location,
            max_thickness=max_thickness,
            num_points=airfoil_n
        )
        
        xs = coords_obj.coordinates.x
        ys = coords_obj.coordinates.y
        coords = [[float(x), float(y)] for x, y in zip(xs, ys)]
        
        return {"type": "naca4", "code": code, "n": airfoil_n, "coords": coords}

    def parse_controls(ctrl: dict, path: str) -> dict | None:
        out_ctrl = {}

        sps = ctrl.get("spanwise_control_points", None)
        if sps is not None:
            if not isinstance(sps, list):
                raise ValueError(f"{path}.spanwise_control_points must be a list.")
            parsed_sps = []
            for p in sps:
                if not isinstance(p, dict):
                    raise ValueError(f"Each {path} spanwise control point must be an object.")
                eta = p.get("eta", None)
                if not isinstance(eta, (int, float)):
                    raise ValueError(f"{path} spanwise control point requires numeric eta.")
                item: dict[str, Any] = {"eta": _clamp(float(eta), 0.0, 1.0)}
                if "twist_deg" in p:
                    if not isinstance(p.get("twist_deg"), (int, float)):
                        raise ValueError(f"{path}.twist_deg must be numeric.")
                    item["twist_deg"] = float(p["twist_deg"])
                if "chord_scale" in p:
                    if not isinstance(p.get("chord_scale"), (int, float)):
                        raise ValueError(f"{path}.chord_scale must be numeric.")
                    item["chord_scale"] = float(p["chord_scale"])
                if "thickness_scale" in p:
                    if not isinstance(p.get("thickness_scale"), (int, float)):
                        raise ValueError(f"{path}.thickness_scale must be numeric.")
                    item["thickness_scale"] = float(p["thickness_scale"])
                if "x_le_offset_m" in p:
                    if not isinstance(p.get("x_le_offset_m"), (int, float)):
                        raise ValueError(f"{path}.x_le_offset_m must be numeric.")
                    item["x_le_offset_m"] = float(p["x_le_offset_m"])
                if "z_offset_m" in p:
                    if not isinstance(p.get("z_offset_m"), (int, float)):
                        raise ValueError(f"{path}.z_offset_m must be numeric.")
                    item["z_offset_m"] = float(p["z_offset_m"])
                if "y_offset_m" in p:
                    if not isinstance(p.get("y_offset_m"), (int, float)):
                        raise ValueError(f"{path}.y_offset_m must be numeric.")
                    item["y_offset_m"] = float(p["y_offset_m"])
                parsed_sps.append(item)
            parsed_sps.sort(key=lambda t: t["eta"])
            out_ctrl["spanwise_control_points"] = parsed_sps

        cs = ctrl.get("control_surfaces", None)
        if cs is not None:
            if not isinstance(cs, list):
                raise ValueError(f"{path}.control_surfaces must be a list.")
            parsed_cs = []
            for item in cs:
                if not isinstance(item, dict):
                    raise ValueError(f"Each {path} control surface must be an object.")
                name = str(item.get("name", "surf")).strip()
                c: dict[str, Any] = {"name": name}
                for k in ["eta_in", "eta_out", "chord_fraction", "deflection_deg_preview", "hinge_xc"]:
                    if k in item:
                        val = item.get(k)
                        if not isinstance(val, (int, float)):
                            raise ValueError(f"{path}.control_surfaces entry {k} must be numeric.")
                        c[k] = float(val)
                parsed_cs.append(c)
            out_ctrl["control_surfaces"] = parsed_cs

        return out_ctrl if out_ctrl else None

    def parse_planform(pf: dict) -> dict:
        out_pf: dict[str, Any] = {}
        for k in [
            "s_ref_m2",
            "area_ratio_to_wing",
            "aspect_ratio",
            "taper_ratio",
            "sweep_quarter_chord_deg",
            "x_offset_m",
            "y_offset_m",
            "z_offset_m",
            "dihedral_deg",
            "incidence_deg",
        ]:
            if k in pf and isinstance(pf.get(k), (int, float)):
                out_pf[k] = float(pf[k])
        return out_pf

    wing = _get_dict(gs, "wing") or {}
    wing_planform = _get_dict(wing, "planform")
    if wing_planform is not None:
        out.setdefault("wing", {})["planform"] = parse_planform(wing_planform)
    sections = _get_dict(wing, "sections") or {}
    root_af = _get_dict(sections, "root_airfoil") or _get_dict(sections, "airfoil")
    if root_af is not None:
        out.setdefault("wing", {})["root_airfoil"] = parse_airfoil(root_af)
        tip_af = _get_dict(sections, "tip_airfoil")
        if tip_af is not None:
            out["wing"]["tip_airfoil"] = parse_airfoil(tip_af)

    controls = _get_dict(wing, "controls") or {}
    wing_ctrl = parse_controls(controls, "geometry_shape.wing.controls")
    if wing_ctrl is not None:
        out.setdefault("wing", {})["controls"] = wing_ctrl

    tail = _get_dict(gs, "tail")
    if tail is not None:
        out_tail: dict[str, Any] = {}
        layout_cfg = _get_dict(tail, "layout") or {}
        if isinstance(layout_cfg, dict):
            layout_type = str(layout_cfg.get("type", "conventional")).strip().lower()
            if layout_type not in {"conventional", "t_tail", "v_tail", "twin_fin"}:
                raise ValueError(f"Unsupported geometry_shape.tail.layout.type: {layout_type}")
            out_tail["layout"] = {"type": layout_type}
            for k in ["cant_deg", "fin_separation_m", "z_rel"]:
                if k in layout_cfg and isinstance(layout_cfg.get(k), (int, float)):
                    out_tail["layout"][k] = float(layout_cfg[k])
        for key in ["horizontal", "vertical"]:
            tail_section = _get_dict(tail, key)
            if tail_section is None:
                continue
            entry: dict[str, Any] = {}
            pf = _get_dict(tail_section, "planform")
            if pf is not None:
                entry["planform"] = parse_planform(pf)
            sections = _get_dict(tail_section, "sections") or {}
            r = _get_dict(sections, "root_airfoil") or _get_dict(sections, "airfoil")
            if r is not None:
                entry["root_airfoil"] = parse_airfoil(r)
                tip = _get_dict(sections, "tip_airfoil")
                if tip is not None:
                    entry["tip_airfoil"] = parse_airfoil(tip)
            ctrl = _get_dict(tail_section, "controls") or {}
            c = parse_controls(ctrl, f"geometry_shape.tail.{key}.controls")
            if c is not None:
                entry["controls"] = c
            out_tail[key] = entry
        if out_tail:
            out["tail"] = out_tail
            wing_pf = out.get("wing", {}).get("planform", {})
            s_ref = wing_pf.get("s_ref_m2", None) if isinstance(wing_pf, dict) else None
            if not isinstance(s_ref, (int, float)) or float(s_ref) <= 0.0:
                inferred = _infer_s_ref_from_tail(out_tail)
                if inferred is not None and inferred > 0.0:
                    s_ref = float(inferred)
            fus_d = None
            st = out.get("fuselage", {}).get("stations")
            if isinstance(st, list) and st:
                max_r = 0.0
                for s in st:
                    if not isinstance(s, dict):
                        continue
                    ry = s.get("radius_y_m", None)
                    rz = s.get("radius_z_m", None)
                    if isinstance(ry, (int, float)):
                        max_r = max(max_r, float(ry))
                    if isinstance(rz, (int, float)):
                        max_r = max(max_r, float(rz))
                if max_r > 0.0:
                    fus_d = max_r * 2.0
            if isinstance(s_ref, (int, float)) and float(s_ref) > 0.0:
                derived = derive_tail_layout(
                    tail_cfg=out_tail,
                    wing_s_ref_m2=float(s_ref),
                    fuselage_length_m=length_m_f,
                    fuselage_diameter_m=float(fus_d) if isinstance(fus_d, (int, float)) and fus_d > 0.0 else 1.0,
                )
                if isinstance(derived, dict):
                    out_tail["layout"] = derived.get("layout", out_tail.get("layout", {}))
                    if isinstance(derived.get("equivalent", None), dict):
                        out_tail["equivalent"] = derived.get("equivalent", {})
                    if isinstance(derived.get("surfaces", None), list):
                        out_tail["surfaces"] = derived.get("surfaces", [])
                    for key in ["horizontal", "vertical"]:
                        tail_entry = out_tail.get(key, None)
                        base = derived.get(key, None)
                        if isinstance(tail_entry, dict) and isinstance(base, dict):
                            pf = tail_entry.get("planform", None)
                            if isinstance(pf, dict):
                                for k in ["x_offset_m", "y_offset_m", "z_offset_m", "dihedral_deg", "incidence_deg"]:
                                    if k in base and k not in pf:
                                        pf[k] = base[k]

    # Apply Modifiers (Phase 8.2 & 9)
    fus_mods = _get_dict(fus, "modifiers") or {}

    # Wing-Body Fairing
    wf = _get_dict(fus_mods, "wing_fairing")
    if wf and "wing" in out and "stations" in out.get("fuselage", {}):
        wing_pf = out["wing"].get("planform", {})
        s = wing_pf.get("s_ref_m2", 0)
        ar = wing_pf.get("aspect_ratio", 0)
        tr = wing_pf.get("taper_ratio", 0)
        x_off = wing_pf.get("x_offset_m", 0)
        if s > 0 and ar > 0:
            b = sqrt(s * ar)
            c_root = 2 * s / (b * (1 + tr))
            r_fair = float(wf.get("radius_m", 0.0))
            apply_wing_body_fairing(out["fuselage"]["stations"], x_off, c_root, r_fair)

    # Canopy Bump
    canopy = _get_dict(fus_mods, "canopy")
    if canopy and "stations" in out.get("fuselage", {}):
        apply_canopy_bump(out["fuselage"]["stations"], canopy)

    return out


def geometry_field_map() -> dict:
    return {
        "geometry_shape": {
            "layout.views": {"unit": "-", "desc": "视图名称列表"},
            "layout.grid.rows": {"unit": "-", "desc": "视图网格行数"},
            "layout.grid.cols": {"unit": "-", "desc": "视图网格列数"},
            "resolution.fuselage_n_stations": {"unit": "-", "desc": "机身站位采样数"},
            "resolution.airfoil_n_points": {"unit": "-", "desc": "翼型点数"},
            "fuselage.axis.length_m": {"unit": "m", "desc": "机身长度"},
            "fuselage.profile.mode": {"unit": "-", "desc": "机身截面定义模式"},
            "fuselage.profile.max_radius_m": {"unit": "m", "desc": "机身最大半径"},
            "fuselage.profile.max_radius_y_m": {"unit": "m", "desc": "机身最大半径Y"},
            "fuselage.profile.max_radius_z_m": {"unit": "m", "desc": "机身最大半径Z"},
            "fuselage.profile.control_points[].x_rel": {"unit": "-", "desc": "机身控制点相对轴向位置"},
            "fuselage.profile.control_points[].radius_rel": {"unit": "-", "desc": "机身控制点相对半径"},
            "fuselage.profile.control_points[].radius_y_rel": {"unit": "-", "desc": "机身控制点相对半径Y"},
            "fuselage.profile.control_points[].radius_z_rel": {"unit": "-", "desc": "机身控制点相对半径Z"},
            "fuselage.profile.control_points[].n": {"unit": "-", "desc": "超椭圆指数"},
            "fuselage.profile.stations[].x_m": {"unit": "m", "desc": "机身站位X"},
            "fuselage.profile.stations[].radius_y_m": {"unit": "m", "desc": "机身站位半径Y"},
            "fuselage.profile.stations[].radius_z_m": {"unit": "m", "desc": "机身站位半径Z"},
            "fuselage.profile.stations[].n": {"unit": "-", "desc": "机身站位超椭圆指数"},
            "wing.planform.s_ref_m2": {"unit": "m2", "desc": "机翼参考面积"},
            "wing.planform.area_ratio_to_wing": {"unit": "-", "desc": "面积相对机翼比"},
            "wing.planform.aspect_ratio": {"unit": "-", "desc": "展弦比"},
            "wing.planform.taper_ratio": {"unit": "-", "desc": "尖削比"},
            "wing.planform.sweep_quarter_chord_deg": {"unit": "deg", "desc": "四分弦后掠角"},
            "wing.planform.x_offset_m": {"unit": "m", "desc": "机翼安装X"},
            "wing.planform.y_offset_m": {"unit": "m", "desc": "机翼安装Y"},
            "wing.planform.z_offset_m": {"unit": "m", "desc": "机翼安装Z"},
            "wing.planform.dihedral_deg": {"unit": "deg", "desc": "机翼上反角"},
            "wing.planform.incidence_deg": {"unit": "deg", "desc": "机翼安装角"},
            "wing.sections.root_airfoil": {"unit": "-", "desc": "机翼根部翼型"},
            "wing.sections.tip_airfoil": {"unit": "-", "desc": "机翼梢部翼型"},
            "wing.controls.spanwise_control_points": {"unit": "-", "desc": "机翼展向控制点"},
            "wing.controls.control_surfaces": {"unit": "-", "desc": "机翼控制面"},
            "tail.layout.type": {"unit": "-", "desc": "尾翼布局类型"},
            "tail.layout.cant_deg": {"unit": "deg", "desc": "V尾翼外倾角"},
            "tail.layout.fin_separation_m": {"unit": "m", "desc": "双垂尾间距"},
            "tail.layout.z_rel": {"unit": "-", "desc": "T尾翼相对高度"},
            "tail.horizontal.planform.s_ref_m2": {"unit": "m2", "desc": "水平尾翼面积"},
            "tail.vertical.planform.s_ref_m2": {"unit": "m2", "desc": "垂直尾翼面积"},
            "tail.horizontal.planform.aspect_ratio": {"unit": "-", "desc": "水平尾翼展弦比"},
            "tail.vertical.planform.aspect_ratio": {"unit": "-", "desc": "垂直尾翼展弦比"},
            "tail.horizontal.planform.taper_ratio": {"unit": "-", "desc": "水平尾翼尖削比"},
            "tail.vertical.planform.taper_ratio": {"unit": "-", "desc": "垂直尾翼尖削比"},
            "tail.horizontal.planform.sweep_quarter_chord_deg": {"unit": "deg", "desc": "水平尾翼后掠角"},
            "tail.vertical.planform.sweep_quarter_chord_deg": {"unit": "deg", "desc": "垂直尾翼后掠角"},
            "tail.horizontal.planform.x_offset_m": {"unit": "m", "desc": "水平尾翼安装X"},
            "tail.vertical.planform.x_offset_m": {"unit": "m", "desc": "垂直尾翼安装X"},
            "tail.horizontal.planform.y_offset_m": {"unit": "m", "desc": "水平尾翼安装Y"},
            "tail.vertical.planform.y_offset_m": {"unit": "m", "desc": "垂直尾翼安装Y"},
            "tail.horizontal.planform.z_offset_m": {"unit": "m", "desc": "水平尾翼安装Z"},
            "tail.vertical.planform.z_offset_m": {"unit": "m", "desc": "垂直尾翼安装Z"},
            "tail.horizontal.planform.dihedral_deg": {"unit": "deg", "desc": "水平尾翼上反角"},
            "tail.horizontal.planform.incidence_deg": {"unit": "deg", "desc": "水平尾翼安装角"},
            "tail.sections.root_airfoil": {"unit": "-", "desc": "尾翼根部翼型"},
            "tail.sections.tip_airfoil": {"unit": "-", "desc": "尾翼梢部翼型"},
            "tail.controls.spanwise_control_points": {"unit": "-", "desc": "尾翼展向控制点"},
            "tail.controls.control_surfaces": {"unit": "-", "desc": "尾翼控制面"},
        },
        "geometry_shape_derived": {
            "fuselage.length_m": {"unit": "m", "desc": "机身长度"},
            "fuselage.diameter_m": {"unit": "m", "desc": "机身直径"},
            "fuselage.x_min_m": {"unit": "m", "desc": "机身最小X"},
            "fuselage.x_max_m": {"unit": "m", "desc": "机身最大X"},
            "wing.s_ref_m2": {"unit": "m2", "desc": "机翼参考面积"},
            "wing.aspect_ratio": {"unit": "-", "desc": "机翼展弦比"},
            "wing.taper_ratio": {"unit": "-", "desc": "机翼尖削比"},
            "wing.sweep_quarter_chord_deg": {"unit": "deg", "desc": "机翼四分弦后掠角"},
            "wing.b_m": {"unit": "m", "desc": "机翼翼展"},
            "wing.c_root_m": {"unit": "m", "desc": "机翼根弦长"},
            "wing.c_tip_m": {"unit": "m", "desc": "机翼梢弦长"},
            "wing.mac_m": {"unit": "m", "desc": "机翼平均气动弦长"},
            "wing.mac_x_le_m": {"unit": "m", "desc": "机翼MAC前缘X偏移"},
            "wing.mac_y_m": {"unit": "m", "desc": "机翼MAC横向位置"},
            "wing.x_offset_m": {"unit": "m", "desc": "机翼安装X"},
            "wing.y_offset_m": {"unit": "m", "desc": "机翼安装Y"},
            "wing.z_offset_m": {"unit": "m", "desc": "机翼安装Z"},
            "wing.dihedral_deg": {"unit": "deg", "desc": "机翼上反角"},
            "wing.incidence_deg": {"unit": "deg", "desc": "机翼安装角"},
            "tail.layout": {"unit": "-", "desc": "尾翼布局"},
            "tail.equivalent": {"unit": "-", "desc": "等效尾翼参数"},
            "tail.horizontal": {"unit": "-", "desc": "水平尾翼派生"},
            "tail.vertical": {"unit": "-", "desc": "垂直尾翼派生"},
            "tail.surfaces[]": {"unit": "-", "desc": "尾翼表面派生"},
        },
        "geometry_reference": {
            "units.length": {"unit": "-", "desc": "长度单位"},
            "units.angle": {"unit": "-", "desc": "角度单位"},
            "axes.x": {"unit": "-", "desc": "X轴定义"},
            "axes.y": {"unit": "-", "desc": "Y轴定义"},
            "axes.z": {"unit": "-", "desc": "Z轴定义"},
            "origin": {"unit": "-", "desc": "坐标原点基准"},
            "installs.fuselage.x_m": {"unit": "m", "desc": "机身安装X"},
            "installs.fuselage.y_m": {"unit": "m", "desc": "机身安装Y"},
            "installs.fuselage.z_m": {"unit": "m", "desc": "机身安装Z"},
            "installs.wing.x_m": {"unit": "m", "desc": "机翼安装X"},
            "installs.wing.y_m": {"unit": "m", "desc": "机翼安装Y"},
            "installs.wing.z_m": {"unit": "m", "desc": "机翼安装Z"},
            "installs.wing.incidence_deg": {"unit": "deg", "desc": "机翼安装角"},
            "installs.wing.dihedral_deg": {"unit": "deg", "desc": "机翼上反角"},
            "installs.tail.x_m": {"unit": "m", "desc": "尾翼安装X"},
            "installs.tail.y_m": {"unit": "m", "desc": "尾翼安装Y"},
            "installs.tail.z_m": {"unit": "m", "desc": "尾翼安装Z"},
            "installs.tail.incidence_deg": {"unit": "deg", "desc": "尾翼安装角"},
            "installs.tail_surfaces[]": {"unit": "-", "desc": "尾翼表面安装"},
        },
    }


def resolve_geometry_bundle(payload: dict) -> dict:
    out: dict[str, dict[str, Any] | None] = {"shape": None, "derived": None, "reference": None}
    if not isinstance(payload, dict):
        return out
    geometry = payload.get("geometry", None)
    if isinstance(geometry, dict):
        for key in ["shape", "derived", "reference"]:
            v = geometry.get(key, None)
            if isinstance(v, dict):
                out[key] = v
    for key in ["shape", "derived", "reference"]:
        if out[key] is None:
            v = payload.get(key, None)
            if isinstance(v, dict):
                out[key] = v
    if out["shape"] is None:
        v = payload.get("geometry_shape", None)
        if isinstance(v, dict):
            out["shape"] = v
    if out["derived"] is None:
        v = payload.get("geometry_shape_derived", None)
        if isinstance(v, dict):
            out["derived"] = v
    if out["reference"] is None:
        v = payload.get("geometry_reference", None)
        if isinstance(v, dict):
            out["reference"] = v
    return out


def validate_geometry_shape_inputs(inputs: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(inputs, dict):
        return {"errors": ["inputs must be dict"], "warnings": warnings}

    gs = inputs.get("geometry_shape", None)
    if gs is None:
        warnings.append("geometry_shape missing")
        return {"errors": errors, "warnings": warnings}
    if not isinstance(gs, dict):
        return {"errors": ["geometry_shape must be dict"], "warnings": warnings}

    sizing = inputs.get("sizing", {}) if isinstance(inputs.get("sizing", None), dict) else {}
    geometry = inputs.get("geometry", {}) if isinstance(inputs.get("geometry", None), dict) else {}

    wing_pf = None
    wing_cfg = gs.get("wing", None)
    if isinstance(wing_cfg, dict):
        pf = wing_cfg.get("planform", None)
        if isinstance(pf, dict):
            wing_pf = pf

    if isinstance(wing_pf, dict):
        s_ref_gs = wing_pf.get("s_ref_m2", None)
        s_ref_sz = sizing.get("s_m2", None)
        if isinstance(s_ref_gs, (int, float)) and isinstance(s_ref_sz, (int, float)) and float(s_ref_sz) > 0.0:
            if abs(float(s_ref_gs) - float(s_ref_sz)) / float(s_ref_sz) > 0.1:
                warnings.append("wing s_ref_m2 differs from sizing.s_m2 by >10%")

        ar_gs = wing_pf.get("aspect_ratio", None)
        ar_sz = sizing.get("aspect_ratio", None)
        if isinstance(ar_gs, (int, float)) and isinstance(ar_sz, (int, float)) and float(ar_sz) > 0.0:
            if abs(float(ar_gs) - float(ar_sz)) / float(ar_sz) > 0.1:
                warnings.append("wing aspect_ratio differs from sizing.aspect_ratio by >10%")

    fus_len_gs = None
    fus_cfg = gs.get("fuselage", None)
    if isinstance(fus_cfg, dict):
        axis = fus_cfg.get("axis", None)
        if isinstance(axis, dict):
            axis_len = axis.get("length_m", None)
            if isinstance(axis_len, (int, float)):
                fus_len_gs = float(axis_len)
    fus_len_geom = geometry.get("fuselage_length_m", None)
    if isinstance(fus_len_gs, (int, float)) and isinstance(fus_len_geom, (int, float)) and float(fus_len_geom) > 0.0:
        if abs(float(fus_len_gs) - float(fus_len_geom)) / float(fus_len_geom) > 0.1:
            warnings.append("fuselage length differs from geometry.fuselage_length_m by >10%")

    tail_cfg = gs.get("tail", None)
    if isinstance(tail_cfg, dict) and isinstance(wing_pf, dict):
        s_ref_pf = wing_pf.get("s_ref_m2", None)
        if not isinstance(s_ref_pf, (int, float)) or float(s_ref_pf) <= 0.0:
            inferred = _infer_s_ref_from_tail(tail_cfg)
            if inferred is None or inferred <= 0.0:
                warnings.append("tail layout provided but wing planform s_ref_m2 missing")
            else:
                s_ref_sz = sizing.get("s_m2", None)
                if isinstance(s_ref_sz, (int, float)) and float(s_ref_sz) > 0.0:
                    if abs(float(inferred) - float(s_ref_sz)) / float(s_ref_sz) > 0.1:
                        warnings.append("tail-inferred wing s_ref_m2 differs from sizing.s_m2 by >10%")

    tail_ratio_geom = geometry.get("tail_area_ratio", None)
    if isinstance(tail_ratio_geom, (int, float)) and isinstance(tail_cfg, dict):
        ht = tail_cfg.get("horizontal", None)
        if isinstance(ht, dict):
            pf = ht.get("planform", None)
            if isinstance(pf, dict):
                area_ratio = pf.get("area_ratio_to_wing", None)
                if isinstance(area_ratio, (int, float)):
                    if abs(float(area_ratio) - float(tail_ratio_geom)) > 0.1:
                        warnings.append("tail area_ratio_to_wing differs from geometry.tail_area_ratio by >0.1")

    return {"errors": errors, "warnings": warnings}


def validate_geometry_shape_outputs(*, shape: dict | None, derived: dict | None, reference: dict | None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(derived, dict) or not isinstance(reference, dict):
        warnings.append("geometry_shape_derived or geometry_reference missing")
        return {"errors": errors, "warnings": warnings}

    installs = reference.get("installs", {}) if isinstance(reference.get("installs", None), dict) else {}
    wing_ref = installs.get("wing", {}) if isinstance(installs.get("wing", None), dict) else {}
    wing_d = derived.get("wing", {}) if isinstance(derived.get("wing", None), dict) else {}

    def _near(a: object, b: object, rel: float = 0.05, abs_tol: float = 1e-6) -> bool:
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            return True
        return abs(float(a) - float(b)) <= max(abs_tol, rel * max(1e-9, abs(float(b))))

    for k in ["x_offset_m", "y_offset_m", "z_offset_m", "incidence_deg", "dihedral_deg"]:
        a = wing_d.get(k, None)
        b = wing_ref.get(k.replace("_offset_m", "_m"), None) if "offset" in k else wing_ref.get(k, None)
        if not _near(a, b):
            warnings.append(f"wing {k} differs between derived and reference")

    tail_surfaces_ref = installs.get("tail_surfaces", None)
    tail_d = derived.get("tail", {}) if isinstance(derived.get("tail", None), dict) else {}
    tail_surfaces_d = tail_d.get("surfaces", None)

    if isinstance(tail_surfaces_ref, list) and isinstance(tail_surfaces_d, list):
        d_map = {}
        for sf in tail_surfaces_d:
            if not isinstance(sf, dict):
                continue
            sid = sf.get("name_prefix", None) if sf.get("builder") != "vertical_loft" else sf.get("name", None)
            if isinstance(sid, str):
                d_map[sid] = sf
        for inst in tail_surfaces_ref:
            if not isinstance(inst, dict):
                continue
            sid = inst.get("id", None)
            if not isinstance(sid, str):
                continue
            sf = d_map.get(sid, None)
            if sf is None:
                warnings.append(f"tail surface {sid} missing in derived")
                continue
            for k in ["x_offset_m", "y_offset_m", "z_offset_m", "incidence_deg", "dihedral_deg"]:
                a = sf.get(k, None)
                b = inst.get(k.replace("_offset_m", "_m"), None) if "offset" in k else inst.get(k, None)
                if not _near(a, b):
                    warnings.append(f"tail surface {sid} {k} differs between derived and reference")

    if isinstance(shape, dict) and isinstance(shape.get("fuselage", None), dict):
        st = shape.get("fuselage", {}).get("stations", None)
        if isinstance(st, list) and st and isinstance(derived.get("fuselage", None), dict):
            xs = [
                float(s.get("x_m", 0.0))
                for s in st
                if isinstance(s, dict) and isinstance(s.get("x_m", None), (int, float))
            ]
            if xs:
                length = float(max(xs) - min(xs))
                if not _near(length, derived.get("fuselage", {}).get("length_m", None), rel=0.05):
                    warnings.append("fuselage length differs between shape and derived")

    return {"errors": errors, "warnings": warnings}


def calculate_cross_sectional_area_distribution(
    *,
    fuselage_stations: list[dict],
    fuselage_length_m: float,
    wing_s_ref_m2: float,
    wing_aspect_ratio: float,
    wing_taper_ratio: float,
    wing_sweep_quarter_chord_deg: float,
    wing_t_c: float,
    wing_x_offset_m: float,
    tail_layout: dict,
    n_points: int = 100,
) -> list[dict]:
    """
    Calculate cross-sectional area distribution S(x) along the fuselage axis.
    Includes Fuselage, Wing, and Tail contributions.
    """
    length = float(fuselage_length_m)
    xs = _linspace(0.0, length, max(10, int(n_points)))

    # 1. Fuselage Area
    # Integrate stations
    # station: {x_m, radius_y_m, radius_z_m, n}
    # Area of super-ellipse: 4 * a * b * (Gamma(1+1/n))^2 / Gamma(1+2/n)
    # For n=2: pi * a * b
    # We will use numerical integration of the shape for simplicity if n != 2, or approximation
    # Actually, for visualization and area rule, simple integration is enough.

    # Pre-process stations for interpolation
    f_xs: list[float] = [float(s["x_m"]) for s in fuselage_stations]
    f_rys: list[float] = [float(s["radius_y_m"]) for s in fuselage_stations]
    f_rzs: list[float] = [float(s["radius_z_m"]) for s in fuselage_stations]
    f_ns: list[float] = [float(s.get("n", 2.0)) for s in fuselage_stations]

    # Sort by x
    combined = sorted(zip(f_xs, f_rys, f_rzs, f_ns), key=lambda t: t[0])
    if combined:
        f_xs, f_rys, f_rzs, f_ns = map(list, zip(*combined))
    else:
        f_xs, f_rys, f_rzs, f_ns = [], [], [], []

    def get_fuse_props(x: float):
        if not f_xs:
            return 0.0, 0.0, 2.0
        # Linear interp
        if x <= f_xs[0]:
            return f_rys[0], f_rzs[0], f_ns[0]
        if x >= f_xs[-1]:
            return f_rys[-1], f_rzs[-1], f_ns[-1]
        for i in range(len(f_xs) - 1):
            if f_xs[i] <= x <= f_xs[i + 1]:
                t = (x - f_xs[i]) / max(1e-9, f_xs[i + 1] - f_xs[i])
                return (
                    f_rys[i] * (1 - t) + f_rys[i + 1] * t,
                    f_rzs[i] * (1 - t) + f_rzs[i + 1] * t,
                    f_ns[i] * (1 - t) + f_ns[i + 1] * t,
                )
        return 0.0, 0.0, 2.0

    def super_ellipse_area(a, b, n):
        if a <= 0 or b <= 0:
            return 0.0
        if abs(n - 2.0) < 1e-3:
            return 3.1415926535 * a * b
        # Numerical integration: 4 * int_0^a y dx
        # (x/a)^n + (y/b)^n = 1 => y = b * (1 - (x/a)^n)^(1/n)
        # Use Simpson's rule with 10 steps
        steps = 10
        dx = a / steps
        area = 0.0
        for i in range(steps + 1):
            x = i * dx
            if x >= a:
                y = 0.0
            else:
                y = b * (1.0 - (x / a) ** n) ** (1.0 / n)
            w = 1.0
            if i == 0 or i == steps:
                w = 1.0
            elif i % 2 == 1:
                w = 4.0
            else:
                w = 2.0
            area += w * y
        return 4.0 * (dx / 3.0) * area

    # 2. Wing Area
    # Volume distribution of a trapezoidal wing

    def get_wing_area_at_x(x_val):
        return 0.0

    if wing_s_ref_m2 > 0.0 and wing_aspect_ratio > 0.0:
        wing_b = sqrt(wing_s_ref_m2 * wing_aspect_ratio)
        wing_c_root = 2 * wing_s_ref_m2 / (wing_b * (1 + wing_taper_ratio))
        wing_c_tip = wing_taper_ratio * wing_c_root
        wing_tan_sw = tan(radians(wing_sweep_quarter_chord_deg))

        wing_x_le_root = wing_x_offset_m
        wing_x_qc_root = wing_x_le_root + 0.25 * wing_c_root
        wing_x_qc_tip = wing_x_qc_root + (wing_b / 2) * wing_tan_sw
        wing_x_le_tip = wing_x_qc_tip - 0.25 * wing_c_tip
        wing_tan_le = (wing_x_le_tip - wing_x_le_root) / (wing_b / 2)

        def get_wing_area_at_x_impl(x_val):
            # Integrate thickness along span
            # dy steps
            n_y = 20
            dy = (wing_b / 2.0) / n_y
            area = 0.0
            for i in range(n_y):
                y = (i + 0.5) * dy
                c_y = wing_c_root + (wing_c_tip - wing_c_root) * (y / (wing_b / 2))
                x_le_y = wing_x_le_root + y * wing_tan_le
                if x_le_y <= x_val <= x_le_y + c_y:
                    # Normalized coord in airfoil
                    xi = (x_val - x_le_y) / c_y
                    # NACA 00xx thickness distribution approx:
                    thick = (
                        5.0
                        * wing_t_c
                        * (0.2969 * sqrt(xi) - 0.1260 * xi - 0.3516 * (xi**2) + 0.2843 * (xi**3) - 0.1015 * (xi**4))
                    )
                    local_h = thick * c_y
                    area += local_h * dy
            return 2.0 * area  # Left + Right

        get_wing_area_at_x = get_wing_area_at_x_impl

    # 3. Tail Area (Simplified: Treat like wing)
    tails = []
    if tail_layout.get("surfaces"):
        for surf in tail_layout["surfaces"]:
            # Need geometry parameters for each surface
            # Assuming they are similar to wing dict structure
            # Reconstruct basic params
            s_ref = surf.get("s_ref_m2", 0)
            if s_ref <= 0:
                continue
            ar = surf.get("aspect_ratio", 4.0)
            tr = surf.get("taper_ratio", 0.6)
            sw = surf.get("sweep_quarter_chord_deg", 0.0)
            x_off = surf.get("x_offset_m", 0.0)
            # t_c ? use wing t_c default if missing
            tc = 0.12  # default

            b = sqrt(s_ref * ar)
            cr = 2 * s_ref / (b * (1 + tr))
            ct = tr * cr
            tan_sw = tan(radians(sw))
            x_le_r = x_off
            x_qc_r = x_le_r + 0.25 * cr
            x_qc_t = x_qc_r + (b / 2 if surf.get("builder") == "wing_loft" else b) * tan_sw
            # Vertical tail span is full b? 'vertical_loft' uses span=sqrt(ar*s).
            # 'wing_loft' uses half_span=b/2.
            is_vert = surf.get("builder") == "vertical_loft"
            span_eff = b if is_vert else b / 2

            x_le_t = x_qc_t - 0.25 * ct
            tan_le = (x_le_t - x_le_r) / span_eff

            tails.append(
                {
                    "b": b,
                    "span_eff": span_eff,
                    "cr": cr,
                    "ct": ct,
                    "x_le_r": x_le_r,
                    "tan_le": tan_le,
                    "tc": tc,
                    "is_vert": is_vert,
                }
            )

    def get_tail_area_at_x(x_val):
        total = 0.0
        for t in tails:
            n_y = 10
            dy = t["span_eff"] / n_y
            sub_a = 0.0
            for i in range(n_y):
                y = (i + 0.5) * dy
                c_y = t["cr"] + (t["ct"] - t["cr"]) * (y / t["span_eff"])
                x_le_y = t["x_le_r"] + y * t["tan_le"]
                if x_le_y <= x_val <= x_le_y + c_y:
                    xi = (x_val - x_le_y) / c_y
                    thick = (
                        5.0
                        * t["tc"]
                        * (0.2969 * sqrt(xi) - 0.1260 * xi - 0.3516 * (xi**2) + 0.2843 * (xi**3) - 0.1015 * (xi**4))
                    )
                    local_h = thick * c_y
                    sub_a += local_h * dy
            if not t["is_vert"]:
                sub_a *= 2.0  # Horizontal tail usually symmetric
            total += sub_a
        return total

    # Combine
    dist = []
    for x in xs:
        ry, rz, n = get_fuse_props(x)
        a_fuse = super_ellipse_area(ry, rz, n)
        a_wing = get_wing_area_at_x(x)
        a_tail = get_tail_area_at_x(x)
        dist.append(
            {
                "x_m": x,
                "area_fuselage_m2": a_fuse,
                "area_wing_m2": a_wing,
                "area_tail_m2": a_tail,
                "area_total_m2": a_fuse + a_wing + a_tail,
            }
        )

    return dist


def derive_tail_layout(
    *,
    tail_cfg: dict,
    wing_s_ref_m2: float,
    fuselage_length_m: float,
    fuselage_diameter_m: float,
) -> dict:
    if not isinstance(tail_cfg, dict):
        raise ValueError("tail_cfg must be a dict.")

    s_ref = float(wing_s_ref_m2)
    fus_l = float(fuselage_length_m)
    fus_d = float(fuselage_diameter_m)

    layout_in = tail_cfg.get("layout", {}) if isinstance(tail_cfg.get("layout", {}), dict) else {}
    layout_type = str(layout_in.get("type", "conventional")).strip().lower()
    if layout_type not in {"conventional", "t_tail", "v_tail", "twin_fin"}:
        layout_type = "conventional"
    cant_deg = (
        float(layout_in.get("cant_deg", 35.0)) if isinstance(layout_in.get("cant_deg", None), (int, float)) else 35.0
    )
    fin_sep_m = (
        float(layout_in.get("fin_separation_m", 0.6))
        if isinstance(layout_in.get("fin_separation_m", None), (int, float))
        else 0.6
    )

    def _get_pf(key: str) -> dict:
        sec = tail_cfg.get(key, None)
        if not isinstance(sec, dict):
            return {}
        pf = sec.get("planform", None)
        return pf if isinstance(pf, dict) else {}

    pf_h = _get_pf("horizontal")
    pf_v = _get_pf("vertical")

    def _area_from_pf(pf: dict) -> float | None:
        if isinstance(pf.get("s_ref_m2", None), (int, float)):
            return float(pf["s_ref_m2"])
        if isinstance(pf.get("area_ratio_to_wing", None), (int, float)):
            return float(s_ref) * max(0.0, float(pf["area_ratio_to_wing"]))
        return None

    def _defaults_for(kind: str) -> dict:
        if kind == "horizontal":
            return {
                "x_offset_m": 0.55 * fus_l,
                "y_offset_m": 0.0,
                "z_offset_m": 0.35 * fus_d,
                "dihedral_deg": 0.0,
                "incidence_deg": 0.0,
            }
        return {"x_offset_m": 0.55 * fus_l, "y_offset_m": 0.0, "z_offset_m": 0.0}

    def _merged_pf(pf: dict, defaults: dict[str, float]) -> dict[str, float]:
        out: dict[str, float] = dict(defaults)
        for k, v in pf.items():
            if isinstance(v, (int, float)):
                out[k] = float(v)
        return out

    out_h = _merged_pf(pf_h, _defaults_for("horizontal"))
    out_v = _merged_pf(pf_v, _defaults_for("vertical"))

    s_h = _area_from_pf(out_h)
    s_v = _area_from_pf(out_v)

    surfaces: list[dict] = []
    equivalent: dict[str, Any] = {}

    if layout_type == "v_tail":
        if s_h is None or s_h <= 0.0:
            layout_type = "conventional"
        else:
            cant = radians(float(cant_deg))
            equivalent = {
                "v_tail": {
                    "cant_deg": float(cant_deg),
                    "s_total_m2": float(s_h),
                    "s_equiv_horizontal_m2": float(s_h) * float(cos(cant) ** 2),
                    "s_equiv_vertical_m2": float(s_h) * float(sin(cant) ** 2),
                }
            }
            surfaces.append(
                {
                    "builder": "wing_loft",
                    "source": "horizontal",
                    "name_prefix": "vtail",
                    "s_ref_m2": float(s_h),
                    "aspect_ratio": out_h["aspect_ratio"] if "aspect_ratio" in out_h else 4.0,
                    "taper_ratio": out_h["taper_ratio"] if "taper_ratio" in out_h else 0.6,
                    "sweep_quarter_chord_deg": out_h["sweep_quarter_chord_deg"]
                    if "sweep_quarter_chord_deg" in out_h
                    else 10.0,
                    "x_offset_m": out_h["x_offset_m"],
                    "y_offset_m": out_h["y_offset_m"],
                    "z_offset_m": out_h["z_offset_m"],
                    "dihedral_deg": float(cant_deg),
                    "incidence_deg": out_h["incidence_deg"] if "incidence_deg" in out_h else 0.0,
                }
            )

    if layout_type == "twin_fin":
        if s_v is None or s_v <= 0.0:
            layout_type = "conventional"
        else:
            equivalent = {
                "twin_fin": {
                    "fin_separation_m": float(fin_sep_m),
                    "s_total_m2": float(s_v),
                    "s_each_m2": float(s_v) * 0.5,
                }
            }
            y0 = 0.5 * float(fin_sep_m)
            for sgn, nm in [(+1.0, "vtail_R"), (-1.0, "vtail_L")]:
                surfaces.append(
                    {
                        "builder": "vertical_loft",
                        "source": "vertical",
                        "name": nm,
                        "s_ref_m2": float(s_v) * 0.5,
                        "aspect_ratio": out_v["aspect_ratio"] if "aspect_ratio" in out_v else 1.8,
                        "taper_ratio": out_v["taper_ratio"] if "taper_ratio" in out_v else 0.7,
                        "sweep_quarter_chord_deg": out_v["sweep_quarter_chord_deg"]
                        if "sweep_quarter_chord_deg" in out_v
                        else 25.0,
                        "x_offset_m": out_v["x_offset_m"],
                        "y_offset_m": out_v["y_offset_m"] + float(sgn) * float(y0),
                        "z_offset_m": out_v["z_offset_m"],
                    }
                )

    if layout_type == "t_tail":
        if s_h is None or s_h <= 0.0 or s_v is None or s_v <= 0.0:
            layout_type = "conventional"
        else:
            ar_v = out_v["aspect_ratio"] if "aspect_ratio" in out_v else 1.8
            span_v = sqrt(max(1e-9, ar_v * float(s_v)))
            if not isinstance(pf_h.get("z_offset_m", None), (int, float)):
                out_h["z_offset_m"] = out_v["z_offset_m"] + float(span_v)
            equivalent = {"t_tail": {"vt_span_m": float(span_v)}}

    if layout_type == "conventional" and not surfaces:
        if s_v is not None and s_v > 0.0 and isinstance(pf_v, dict) and pf_v:
            surfaces.append(
                {
                    "builder": "vertical_loft",
                    "source": "vertical",
                    "name": "vtail",
                    "s_ref_m2": float(s_v),
                    "aspect_ratio": out_v["aspect_ratio"] if "aspect_ratio" in out_v else 1.8,
                    "taper_ratio": out_v["taper_ratio"] if "taper_ratio" in out_v else 0.7,
                    "sweep_quarter_chord_deg": out_v["sweep_quarter_chord_deg"]
                    if "sweep_quarter_chord_deg" in out_v
                    else 25.0,
                    "x_offset_m": out_v["x_offset_m"],
                    "y_offset_m": out_v["y_offset_m"],
                    "z_offset_m": out_v["z_offset_m"],
                }
            )
        if s_h is not None and s_h > 0.0 and isinstance(pf_h, dict) and pf_h:
            surfaces.append(
                {
                    "builder": "wing_loft",
                    "source": "horizontal",
                    "name_prefix": "htail",
                    "s_ref_m2": float(s_h),
                    "aspect_ratio": out_h["aspect_ratio"] if "aspect_ratio" in out_h else 4.0,
                    "taper_ratio": out_h["taper_ratio"] if "taper_ratio" in out_h else 0.6,
                    "sweep_quarter_chord_deg": out_h["sweep_quarter_chord_deg"]
                    if "sweep_quarter_chord_deg" in out_h
                    else 10.0,
                    "x_offset_m": out_h["x_offset_m"],
                    "y_offset_m": out_h["y_offset_m"],
                    "z_offset_m": out_h["z_offset_m"],
                    "dihedral_deg": out_h["dihedral_deg"] if "dihedral_deg" in out_h else 0.0,
                    "incidence_deg": out_h["incidence_deg"] if "incidence_deg" in out_h else 0.0,
                }
            )

    if layout_type == "t_tail" and not surfaces:
        if s_v is not None and s_v > 0.0:
            surfaces.append(
                {
                    "builder": "vertical_loft",
                    "source": "vertical",
                    "name": "vtail",
                    "s_ref_m2": float(s_v),
                    "aspect_ratio": out_v["aspect_ratio"] if "aspect_ratio" in out_v else 1.8,
                    "taper_ratio": out_v["taper_ratio"] if "taper_ratio" in out_v else 0.7,
                    "sweep_quarter_chord_deg": out_v["sweep_quarter_chord_deg"]
                    if "sweep_quarter_chord_deg" in out_v
                    else 25.0,
                    "x_offset_m": out_v["x_offset_m"],
                    "y_offset_m": out_v["y_offset_m"],
                    "z_offset_m": out_v["z_offset_m"],
                }
            )
        if s_h is not None and s_h > 0.0:
            surfaces.append(
                {
                    "builder": "wing_loft",
                    "source": "horizontal",
                    "name_prefix": "htail",
                    "s_ref_m2": float(s_h),
                    "aspect_ratio": out_h["aspect_ratio"] if "aspect_ratio" in out_h else 4.0,
                    "taper_ratio": out_h["taper_ratio"] if "taper_ratio" in out_h else 0.6,
                    "sweep_quarter_chord_deg": out_h["sweep_quarter_chord_deg"]
                    if "sweep_quarter_chord_deg" in out_h
                    else 10.0,
                    "x_offset_m": out_h["x_offset_m"],
                    "y_offset_m": out_h["y_offset_m"],
                    "z_offset_m": out_h["z_offset_m"],
                    "dihedral_deg": out_h["dihedral_deg"] if "dihedral_deg" in out_h else 0.0,
                    "incidence_deg": out_h["incidence_deg"] if "incidence_deg" in out_h else 0.0,
                }
            )

    return {
        "layout": {"type": layout_type, "cant_deg": float(cant_deg), "fin_separation_m": float(fin_sep_m)},
        "horizontal": out_h if pf_h else None,
        "vertical": out_v if pf_v else None,
        "surfaces": surfaces,
        "equivalent": equivalent,
    }
