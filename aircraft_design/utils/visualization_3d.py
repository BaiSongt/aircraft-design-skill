from __future__ import annotations

import json
from dataclasses import dataclass
from math import cos, pi, sin, sqrt, tan
from typing import Any


@dataclass(frozen=True)
class MeshPart:
    name: str
    color: str
    vertices: list[float]
    indices: list[int]


def _triangulate_quad(a: int, b: int, c: int, d: int) -> list[int]:
    return [a, b, c, a, c, d]


def _append_part(
    parts: list[MeshPart], *, name: str, color: str, verts: list[list[float]], tris: list[list[int]]
) -> None:
    flat = []
    for v in verts:
        flat.extend([float(v[0]), float(v[1]), float(v[2])])
    idx = []
    for t in tris:
        idx.extend([int(t[0]), int(t[1]), int(t[2])])
    parts.append(MeshPart(name=name, color=color, vertices=flat, indices=idx))


def _coerce_airfoil_coords(obj: Any, *, field_name: str) -> list[list[float]]:
    if obj is None:
        raise ValueError(f"{field_name} must not be None.")

    if isinstance(obj, list):
        pts: list[list[float]] = []
        for p in obj:
            if isinstance(p, dict) and "x" in p and "y" in p:
                pts.append([float(p["x"]), float(p["y"])])
                continue
            if isinstance(p, (list, tuple)) and len(p) == 2:
                pts.append([float(p[0]), float(p[1])])
                continue
            raise ValueError(f"Each airfoil coordinate in {field_name} must be [x, y] or {{x, y}}.")
        return pts

    if hasattr(obj, "coordinates"):
        coords = getattr(obj, "coordinates")
        if hasattr(coords, "x") and hasattr(coords, "y"):
            xs = list(getattr(coords, "x"))
            ys = list(getattr(coords, "y"))
            if len(xs) != len(ys):
                raise ValueError(f"{field_name} has mismatched x/y lengths.")
            return [[float(x), float(y)] for x, y in zip(xs, ys)]

    if hasattr(obj, "x") and hasattr(obj, "y"):
        xs = list(getattr(obj, "x"))
        ys = list(getattr(obj, "y"))
        if len(xs) != len(ys):
            raise ValueError(f"{field_name} has mismatched x/y lengths.")
        return [[float(x), float(y)] for x, y in zip(xs, ys)]

    if isinstance(obj, dict) and "x" in obj and "y" in obj:
        xs = list(obj["x"])
        ys = list(obj["y"])
        if len(xs) != len(ys):
            raise ValueError(f"{field_name} has mismatched x/y lengths.")
        return [[float(x), float(y)] for x, y in zip(xs, ys)]

    raise ValueError(f"{field_name} must be a list of points or an airfoil geometry object.")


def _three_js_loader_script(resource_config: dict | None, *, include_orbit: bool) -> str:
    cfg = resource_config if isinstance(resource_config, dict) else {}
    prefer_local = bool(cfg.get("prefer_local", False))
    local_base_url = cfg.get("local_base_url", None)
    cdn_base_url = cfg.get("cdn_base_url", None)
    local_base = local_base_url.rstrip("/") if isinstance(local_base_url, str) and local_base_url else ""
    cdn_base = (
        cdn_base_url.rstrip("/")
        if isinstance(cdn_base_url, str) and cdn_base_url
        else "https://unpkg.com/three@0.147.0"
    )

    # Check for unminified option
    use_unminified = bool(cfg.get("use_unminified", False))
    three_filename = "three.js" if use_unminified else "three.min.js"

    local_three = f"{local_base}/{three_filename}" if local_base else ""
    local_orbit = f"{local_base}/OrbitControls.js" if local_base else ""
    cdn_three = f"{cdn_base}/build/{three_filename}"
    cdn_orbit = f"{cdn_base}/examples/js/controls/OrbitControls.js"
    prefer_flag = "true" if prefer_local and local_base else "false"
    orbit_flag = "true" if include_orbit else "false"
    return f"""<script>
(function(){{
  const preferLocal = {prefer_flag};
  const localThree = {json.dumps(local_three)};
  const localOrbit = {json.dumps(local_orbit)};
  const cdnThree = {json.dumps(cdn_three)};
  const cdnOrbit = {json.dumps(cdn_orbit)};
  function loadScript(src, onload, onerror){{
    if (!src) return;
    const s = document.createElement("script");
    s.src = src;
    if (onload) s.onload = onload;
    if (onerror) s.onerror = onerror;
    document.head.appendChild(s);
  }}
  function loadCdn(){{
    loadScript(cdnThree, function(){{ if ({orbit_flag}) loadScript(cdnOrbit, null, null); }}, function(){{}});
  }}
  if (preferLocal && localThree) {{
    loadScript(localThree, function(){{ if ({orbit_flag}) loadScript(localOrbit, null, function(){{ loadCdn(); }}); }}, function(){{ loadCdn(); }});
    setTimeout(function(){{ if (!window.THREE) loadCdn(); }}, 1500);
  }} else {{
    loadCdn();
  }}
}})();
</script>"""


def build_fuselage_cylinder(*, length_m: float, diameter_m: float, n_circ: int = 28, n_len: int = 16) -> MeshPart:
    if length_m <= 0.0 or diameter_m <= 0.0:
        raise ValueError("Invalid fuselage dimensions.")
    r = 0.5 * float(diameter_m)
    n_c = max(8, int(n_circ))
    n_x = max(2, int(n_len))

    verts: list[list[float]] = []
    for ix in range(n_x + 1):
        x = -0.15 * length_m + (length_m * 1.15) * (ix / n_x)
        for ic in range(n_c):
            ang = 2.0 * 3.141592653589793 * (ic / n_c)
            y = r * float(__import__("math").cos(ang))
            z = r * float(__import__("math").sin(ang))
            verts.append([x, y, z])

    tris: list[list[int]] = []
    for ix in range(n_x):
        for ic in range(n_c):
            a = ix * n_c + ic
            b = ix * n_c + (ic + 1) % n_c
            c = (ix + 1) * n_c + (ic + 1) % n_c
            d = (ix + 1) * n_c + ic
            tris.append([a, b, c])
            tris.append([a, c, d])

    return MeshPart(
        name="fuselage",
        color="#888888",
        vertices=[c for v in verts for c in v],
        indices=[i for t in tris for i in t],
    )


def build_fuselage_loft(*, stations: list[dict], n_circ: int = 28) -> MeshPart:
    if not isinstance(stations, list) or not stations:
        raise ValueError("stations must be a non-empty list.")
    n_c = max(8, int(n_circ))

    xs = []
    ry = []
    rz = []
    ns = []
    for s in stations:
        if not isinstance(s, dict):
            raise ValueError("Each station must be an object.")
        x = s.get("x_m", None)
        r = s.get("radius_m", None)
        ry_m = s.get("radius_y_m", None)
        rz_m = s.get("radius_z_m", None)
        n_val = s.get("n", 2.0)

        if not isinstance(x, (int, float)):
            raise ValueError("Each station requires numeric x_m.")
        if not isinstance(n_val, (int, float)):
            raise ValueError("station.n must be numeric.")

        if r is not None:
            if not isinstance(r, (int, float)):
                raise ValueError("station.radius_m must be numeric when provided.")
            if float(r) < 0.0:
                raise ValueError("radius_m must be non-negative.")
            ry_v = float(r)
            rz_v = float(r)
        else:
            if not isinstance(ry_m, (int, float)) or not isinstance(rz_m, (int, float)):
                raise ValueError("Each station requires radius_m or both radius_y_m and radius_z_m.")
            if float(ry_m) < 0.0 or float(rz_m) < 0.0:
                raise ValueError("radius_y_m and radius_z_m must be non-negative.")
            ry_v = float(ry_m)
            rz_v = float(rz_m)
        xs.append(float(x))
        ry.append(ry_v)
        rz.append(rz_v)
        ns.append(float(n_val))

    if len(xs) < 2:
        raise ValueError("stations must have at least 2 items.")
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    xs = [xs[i] for i in order]
    ry = [ry[i] for i in order]
    rz = [rz[i] for i in order]
    ns = [ns[i] for i in order]

    verts: list[list[float]] = []
    for x, r_y, r_z, n_exp in zip(xs, ry, rz, ns):
        exponent = 2.0 / max(1e-9, n_exp)
        for ic in range(n_c):
            ang = 2.0 * pi * (ic / n_c)
            c = cos(ang)
            s_val = sin(ang)
            sign_c = 1.0 if c >= 0 else -1.0
            sign_s = 1.0 if s_val >= 0 else -1.0

            # Super-ellipse: |y/a|^n + |z/b|^n = 1
            # y = a * sgn(cos) * |cos|^(2/n)
            # z = b * sgn(sin) * |sin|^(2/n)

            y_base = sign_c * (abs(c) ** exponent)
            z_base = sign_s * (abs(s_val) ** exponent)

            y = r_y * y_base
            z = r_z * z_base
            verts.append([x, y, z])

    tris: list[list[int]] = []
    for ix in range(len(xs) - 1):
        for ic in range(n_c):
            a = ix * n_c + ic
            b = ix * n_c + (ic + 1) % n_c
            c = (ix + 1) * n_c + (ic + 1) % n_c
            d = (ix + 1) * n_c + ic
            tris.append([a, b, c])
            tris.append([a, c, d])

    return MeshPart(
        name="fuselage",
        color="#888888",
        vertices=[c for v in verts for c in v],
        indices=[i for t in tris for i in t],
    )


def build_wing_airfoil_mesh(
    *,
    airfoil_coords: Any,
    s_ref_m2: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
    x_offset_m: float,
    z_offset_m: float,
    name_prefix: str = "wing",
    color: str = "#2c7fb8",
) -> list[MeshPart]:
    airfoil_pts = _coerce_airfoil_coords(airfoil_coords, field_name="airfoil_coords")
    if len(airfoil_pts) < 10:
        raise ValueError("airfoil_coords must be a list with at least 10 points.")
    s = float(s_ref_m2)
    ar = float(aspect_ratio)
    taper = float(taper_ratio)
    if s <= 0.0 or ar <= 0.0:
        raise ValueError("Invalid wing reference area or aspect ratio.")
    if not (0.05 <= taper <= 1.0):
        raise ValueError("taper_ratio must be in [0.05, 1.0].")

    pts2 = []
    for p in airfoil_pts:
        pts2.append((float(p[0]), float(p[1])))

    b = sqrt(ar * s)
    half_span = 0.5 * b
    c_root = 2.0 * s / (b * (1.0 + taper))
    c_tip = taper * c_root

    sweep_rad = float(__import__("math").radians(float(sweep_quarter_chord_deg)))
    x_qc_tip = float(x_offset_m) + tan(sweep_rad) * half_span
    x_le_root = float(x_offset_m)
    x_le_tip = x_qc_tip - 0.25 * c_tip

    parts: list[MeshPart] = []
    for sign, name in [(+1.0, f"{name_prefix}_R"), (-1.0, f"{name_prefix}_L")]:
        y_root = 0.0
        y_tip = sign * half_span
        verts: list[list[float]] = []
        for x, y in pts2:
            verts.append([x_le_root + x * c_root, y_root, float(z_offset_m) + y * c_root])
        for x, y in pts2:
            verts.append([x_le_tip + x * c_tip, y_tip, float(z_offset_m) + y * c_tip])

        n = len(pts2)
        tris: list[list[int]] = []
        for i in range(n):
            j = (i + 1) % n
            a = i
            b0 = j
            c0 = n + j
            d0 = n + i
            tris.append([a, b0, c0])
            tris.append([a, c0, d0])

        def cap(offset: int, flip: bool) -> None:
            cx = 0.0
            cy = 0.0
            cz = 0.0
            for i in range(n):
                cx += verts[offset + i][0]
                cy += verts[offset + i][1]
                cz += verts[offset + i][2]
            cx /= n
            cy /= n
            cz /= n
            c_idx = len(verts)
            verts.append([cx, cy, cz])
            for i in range(n):
                j = (i + 1) % n
                if flip:
                    tris.append([c_idx, offset + j, offset + i])
                else:
                    tris.append([c_idx, offset + i, offset + j])

        cap(0, flip=(sign < 0))
        cap(n, flip=(sign > 0))
        _append_part(parts, name=name, color=color, verts=verts, tris=tris)
    return parts


def build_wing_airfoil_loft_mesh(
    *,
    root_airfoil_coords: Any,
    tip_airfoil_coords: Any | None,
    s_ref_m2: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
    x_offset_m: float,
    y_offset_m: float = 0.0,
    z_offset_m: float,
    dihedral_deg: float = 0.0,
    incidence_deg: float = 0.0,
    spanwise_control_points: list[dict] | None = None,
    control_surfaces: list[dict] | None = None,
    name_prefix: str = "wing",
    color: str = "#2c7fb8",
) -> list[MeshPart]:
    root_airfoil_pts = _coerce_airfoil_coords(root_airfoil_coords, field_name="root_airfoil_coords")
    if len(root_airfoil_pts) < 10:
        raise ValueError("root_airfoil_coords must be a list with at least 10 points.")
    if tip_airfoil_coords is not None:
        tip_airfoil_pts = _coerce_airfoil_coords(tip_airfoil_coords, field_name="tip_airfoil_coords")
        if len(tip_airfoil_pts) != len(root_airfoil_pts):
            raise ValueError("tip_airfoil_coords must have the same number of points as root_airfoil_coords.")
    else:
        tip_airfoil_pts = None

    s = float(s_ref_m2)
    ar = float(aspect_ratio)
    taper = float(taper_ratio)
    if s <= 0.0 or ar <= 0.0:
        raise ValueError("Invalid wing reference area or aspect ratio.")
    if not (0.05 <= taper <= 1.0):
        raise ValueError("taper_ratio must be in [0.05, 1.0].")

    root_pts = [(float(p[0]), float(p[1])) for p in root_airfoil_pts]
    tip_pts = [(float(p[0]), float(p[1])) for p in tip_airfoil_pts] if tip_airfoil_pts is not None else None

    cps = []
    if spanwise_control_points:
        for p in spanwise_control_points:
            if not isinstance(p, dict):
                raise ValueError("Each spanwise control point must be an object.")
            eta = p.get("eta", None)
            if not isinstance(eta, (int, float)):
                raise ValueError("spanwise control point requires numeric eta.")
            item = {"eta": min(max(float(eta), 0.0), 1.0)}
            if "twist_deg" in p:
                if not isinstance(p.get("twist_deg"), (int, float)):
                    raise ValueError("twist_deg must be numeric.")
                item["twist_deg"] = float(p["twist_deg"])
            if "chord_scale" in p:
                if not isinstance(p.get("chord_scale"), (int, float)):
                    raise ValueError("chord_scale must be numeric.")
                item["chord_scale"] = float(p["chord_scale"])
            if "thickness_scale" in p:
                if not isinstance(p.get("thickness_scale"), (int, float)):
                    raise ValueError("thickness_scale must be numeric.")
                item["thickness_scale"] = float(p["thickness_scale"])
            if "x_le_offset_m" in p:
                if not isinstance(p.get("x_le_offset_m"), (int, float)):
                    raise ValueError("x_le_offset_m must be numeric.")
                item["x_le_offset_m"] = float(p["x_le_offset_m"])
            if "z_offset_m" in p:
                if not isinstance(p.get("z_offset_m"), (int, float)):
                    raise ValueError("z_offset_m must be numeric.")
                item["z_offset_m"] = float(p["z_offset_m"])
            if "control_surface" in p:
                item["control_surface"] = p["control_surface"]
            cps.append(item)
    cps.sort(key=lambda t: t["eta"])

    def _interp(key: str, eta: float, default: float) -> float:
        pts = [(0.0, default), (1.0, default)]
        for p in cps:
            if key in p:
                pts.append((float(p["eta"]), float(p[key])))
        pts.sort(key=lambda t: t[0])
        if eta <= pts[0][0]:
            return pts[0][1]
        if eta >= pts[-1][0]:
            return pts[-1][1]
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= eta <= x1:
                t = (eta - x0) / max(1e-9, (x1 - x0))
                return y0 * (1.0 - t) + y1 * t
        return default

    etas = [0.0, 1.0]
    for p in cps:
        e = float(p["eta"])
        if 0.0 < e < 1.0:
            etas.append(e)

    # Collect control surface boundaries (eta_in, eta_out) to split mesh
    # This is a simplified approach: just add eta cuts.
    # Control surfaces data structure:
    # "control_surfaces": [{"name": "aileron", "eta_in": 0.7, "eta_out": 0.95, "chord_fraction": 0.25, "deflection_deg_preview": 0.0}]

    cs_list = control_surfaces if control_surfaces is not None else []

    for cs in cs_list:
        if isinstance(cs, dict):
            if "eta_in" in cs:
                etas.append(max(0.0, min(1.0, float(cs["eta_in"]))))
            if "eta_out" in cs:
                etas.append(max(0.0, min(1.0, float(cs["eta_out"]))))

    etas = sorted(set(etas))

    b = sqrt(ar * s)
    half_span = 0.5 * b
    c_root = 2.0 * s / (b * (1.0 + taper))
    c_tip = taper * c_root

    sweep_rad = float(__import__("math").radians(float(sweep_quarter_chord_deg)))
    dihedral_rad = float(__import__("math").radians(float(dihedral_deg)))
    n = len(root_pts)

    def section_coords(eta: float) -> list[tuple[float, float]]:
        if tip_pts is None:
            return root_pts
        out = []
        for (xr, zr), (xt, zt) in zip(root_pts, tip_pts):
            out.append((xr * (1.0 - eta) + xt * eta, zr * (1.0 - eta) + zt * eta))
        return out

    def get_cs_deflection(eta: float) -> tuple[float, float, float]:
        """Returns (deflection_deg, chord_fraction, hinge_xc) for a given eta."""
        # Find active control surface
        for cs in cs_list:
            ei = float(cs.get("eta_in", 0.0))
            eo = float(cs.get("eta_out", 0.0))
            # Epsilon for inclusion
            if ei <= eta + 1e-6 and eta <= eo + 1e-6:
                return (
                    float(cs.get("deflection_deg_preview", 0.0)),
                    float(cs.get("chord_fraction", 0.25)),
                    float(cs.get("hinge_xc", 0.75)),  # Default hinge at 0.75c if not spec
                )
        return 0.0, 0.0, 0.75

    def apply_twist_and_deflection(xn: float, zn: float, twist_deg: float, eta: float) -> tuple[float, float]:
        defl, c_frac, h_xc = get_cs_deflection(eta)

        # Apply deflection if xn > hinge line (and deflection != 0)
        # Simplified: rotate point around hinge
        # hinge is at h_xc
        xn_local = xn
        zn_local = zn

        if defl != 0.0 and xn > h_xc:
            # Rotate (xn, zn) around (h_xc, 0) by defl degrees
            # Deflection: + is trailing edge down usually?
            # Standard sign: Aileron: right up/left down?
            # Let's assume + deflection = TE down (positive camber increase) -> z decreases?
            # Actually standard convention: + deflection is trailing edge DOWN.
            # Rotation around Y axis (spanwise).
            # If + defl is TE down, then we rotate clockwise looking from right?
            # Coordinate system: X back, Z up.
            # TE down means Z decreases.
            # Rotation center (h_xc, 0).
            dx = xn - h_xc
            dz = zn
            rad = float(__import__("math").radians(defl))
            # If +defl is TE down (Z decreases), then for positive dx, new dz should be negative.
            # Rotation matrix for +angle usually gives +Z for +X?
            # x' = x cos - z sin
            # z' = x sin + z cos
            # If we want +X -> -Z, we need sin to be negative?
            # Let's use simple trig:
            # Rot angle alpha. x' = x cos(alpha) - z sin(alpha). z' = x sin(alpha) + z cos(alpha).
            # If alpha > 0, z' becomes positive for x > 0. That is TE UP.
            # So +defl => TE down => alpha should be negative?
            # Or we define +defl as TE down.

            # Usually +delta_e -> TE down.
            # Let's try: x' = dx cos(a) + dz sin(a), z' = -dx sin(a) + dz cos(a) (Clockwise)

            c_d = float(__import__("math").cos(rad))
            s_d = float(__import__("math").sin(rad))

            xn_local = h_xc + (dx * c_d - dz * s_d)  # wait, this is standard CCW if Z is up, X is right? No.
            # X is back. Z is up.
            # Right hand rule around Y (right wing, pointing right).
            # Thumb Y. Fingers X->Z.
            # +Rotation moves X to Z (TE Up).
            # So +defl (TE down) should be -Rotation.

            # Let's assume defl input is "TE down is positive" (common for flaps).
            # Then rotation angle = +defl.
            # X -> Z is + rotation. We want X -> -Z. So angle = +defl.
            # Wait.
            # If I rotate +X vector by +90 deg around +Y, it goes to -Z (down)?
            # Cross product X x Y = Z.
            # X=(1,0,0), Y=(0,1,0). Z=(0,0,1).
            # Rotate 1,0,0 around 0,1,0 by 90deg?
            # X becomes Z? No.
            # X cross Y = Z.
            # Right hand rule: X -> Y -> Z.
            # Rotating X towards Z is negative rotation around Y?
            # Let's stick to 2D: X horizontal, Z vertical.
            # +Angle = CCW. X -> Z.
            # TE Down = X -> -Z. That is CW. That is negative angle.

            rot = -rad

            c_r = float(__import__("math").cos(rot))
            s_r = float(__import__("math").sin(rot))

            dx_new = dx * c_r - dz * s_r
            dz_new = dx * s_r + dz * c_r

            xn_local = h_xc + dx_new
            zn_local = dz_new

        th = float(__import__("math").radians(float(twist_deg)))
        c = float(__import__("math").cos(th))
        s_ = float(__import__("math").sin(th))
        x0 = xn_local - 0.25
        z0 = zn_local
        x1 = x0 * c - z0 * s_
        z1 = x0 * s_ + z0 * c
        return x1 + 0.25, z1

    parts: list[MeshPart] = []
    for sign, name in [(+1.0, f"{name_prefix}_R"), (-1.0, f"{name_prefix}_L")]:
        verts: list[list[float]] = []
        for eta in etas:
            y_local = sign * half_span * eta
            y = float(y_offset_m) + y_local
            chord = (c_root * (1.0 - eta) + c_tip * eta) * _interp("chord_scale", eta, 1.0)
            twist = _interp("twist_deg", eta, 0.0) + float(incidence_deg)
            thickness_scale = _interp("thickness_scale", eta, 1.0)
            x_le_offset = _interp("x_le_offset_m", eta, 0.0)
            z_extra = _interp("z_offset_m", eta, 0.0)
            x_qc = float(x_offset_m) + tan(sweep_rad) * abs(y)
            x_le = x_qc - 0.25 * chord + x_le_offset
            sec = section_coords(eta)
            z_base = float(z_offset_m) + tan(dihedral_rad) * abs(y_local) + z_extra

            # For left wing, we might want to invert deflection for antisymmetric controls (ailerons)
            # But symmetric controls (flaps/elevators) stay same.
            # We don't have "type" in input yet.
            # Assuming symmetric for now, or user provides "aileron_L" / "aileron_R" separately?
            # The input is "control_surfaces" list. Usually defined on one side and mirrored?
            # Or defined with "side": "both" | "left" | "right".
            # Default "both" -> symmetric deflection?
            # Ailerons usually have anti-symmetric deflection.
            # But this is just "preview". If user sets defl=10, they see both down.
            # If they want aileron check, they might set one up one down?
            # Let's keep it simple: apply deflection as given.
            # If it's aileron, user can't easily visualize roll unless we have more logic.
            # BUT: for "both", we apply same deflection.

            # Actually, `get_cs_deflection` uses `cs_list`.
            # If we want distinct L/R, we need to know which side we are building.
            # But `cs_list` is global for the wing.
            # Let's just apply it symmetrically for preview.

            for xn, zn in sec:
                xt, zt = apply_twist_and_deflection(xn, zn, twist, eta)
                verts.append([x_le + xt * chord, y, z_base + (zt * thickness_scale) * chord])

        tris: list[list[int]] = []
        n_sec = len(etas)
        for k in range(n_sec - 1):
            o0 = k * n
            o1 = (k + 1) * n
            for i in range(n):
                j = (i + 1) % n
                a = o0 + i
                b0 = o0 + j
                c0 = o1 + j
                d0 = o1 + i
                tris.append([a, b0, c0])
                tris.append([a, c0, d0])

        def cap(offset: int, flip: bool) -> None:
            cx = 0.0
            cy = 0.0
            cz = 0.0
            for i in range(n):
                cx += verts[offset + i][0]
                cy += verts[offset + i][1]
                cz += verts[offset + i][2]
            cx /= n
            cy /= n
            cz /= n
            c_idx = len(verts)
            verts.append([cx, cy, cz])
            for i in range(n):
                j = (i + 1) % n
                if flip:
                    tris.append([c_idx, offset + j, offset + i])
                else:
                    tris.append([c_idx, offset + i, offset + j])

        cap(0, flip=(sign < 0))
        cap((n_sec - 1) * n, flip=(sign > 0))
        _append_part(parts, name=name, color=color, verts=verts, tris=tris)

    return parts


def build_system_box(name: str, x: float, y: float, z: float, size: float = 0.2, color: str = "#ef4444") -> MeshPart:
    hs = size * 0.5
    local_verts = [
        [-hs, -hs, -hs],
        [hs, -hs, -hs],
        [hs, hs, -hs],
        [-hs, hs, -hs],
        [-hs, -hs, hs],
        [hs, -hs, hs],
        [hs, hs, hs],
        [-hs, hs, hs],
    ]
    verts = [[v[0] + x, v[1] + y, v[2] + z] for v in local_verts]
    indices = [
        0,
        1,
        2,
        0,
        2,
        3,
        4,
        5,
        6,
        4,
        6,
        7,
        0,
        1,
        5,
        0,
        5,
        4,
        1,
        2,
        6,
        1,
        6,
        5,
        2,
        3,
        7,
        2,
        7,
        6,
        3,
        0,
        4,
        3,
        4,
        7,
    ]
    flat_verts = []
    for v in verts:
        flat_verts.extend(v)
    return MeshPart(name=name, color=color, vertices=flat_verts, indices=indices)


def build_mesh_parts_from_geometry(geometry: dict) -> list[MeshPart]:
    mesh_parts: list[MeshPart] = []

    # Systems visualization
    systems = geometry.get("systems", {})
    if isinstance(systems, dict):
        groups = systems.get("groups", {})
        for g_name, grp in groups.items():
            comps = grp.get("components", [])
            for c in comps:
                c_name = c.get("name", "Unknown")
                color = "#94a3b8"
                if "Propulsion" in g_name:
                    color = "#ef4444"
                elif "Systems" in g_name:
                    color = "#f59e0b"
                elif "Structure" in g_name:
                    color = "#3b82f6"
                elif "Payload" in g_name:
                    color = "#10b981"

                mesh_parts.append(
                    build_system_box(
                        name=f"{g_name}: {c_name}",
                        x=float(c.get("cg_x_m", 0.0)),
                        y=float(c.get("cg_y_m", 0.0)),
                        z=float(c.get("cg_z_m", 0.0)),
                        size=0.15,
                        color=color,
                    )
                )

    components = ["fuselage", "wing", "htail", "vtail", "horizontal_tail", "vertical_tail"]
    for name in components:
        comp = geometry.get(name)
        if not isinstance(comp, dict):
            continue
        verts = comp.get("vertices")
        faces = comp.get("faces")
        if not isinstance(verts, list) or not isinstance(faces, list):
            continue
        flat_vertices: list[float] = []
        for v in verts:
            if not isinstance(v, (list, tuple)) or len(v) < 3:
                continue
            flat_vertices.extend([float(v[0]), float(v[1]), float(v[2])])
        indices: list[int] = []
        for f in faces:
            if isinstance(f, (list, tuple)) and len(f) >= 3:
                indices.extend([int(f[0]), int(f[1]), int(f[2])])
        if flat_vertices and indices:
            mesh_parts.append(
                MeshPart(
                    name=str(name),
                    color=str(comp.get("color", "#c7d2fe")),
                    vertices=flat_vertices,
                    indices=indices,
                )
            )
    if mesh_parts:
        return mesh_parts
    fus_st = geometry.get("fuselage", {}).get("stations")
    if fus_st:
        mesh_parts.append(build_fuselage_loft(stations=fus_st, n_circ=48))

    wing = geometry.get("wing", {})
    wing_pf = wing.get("planform")
    if wing_pf:
        root_af = wing.get("root_airfoil", {}).get("coords")
        tip_af = wing.get("tip_airfoil", {}).get("coords")
        if not root_af:
            from .geometry_detailed import naca4_coordinates

            # Try to get code from definition (root_airfoil or airfoil)
            af_def = wing.get("root_airfoil")
            if not af_def:
                af_def = wing.get("airfoil", {})

            code = af_def.get("code", "0012") if isinstance(af_def, dict) else "0012"
            print(f"[Visualizer] Generating wing root airfoil with code={code}")

            af_obj = naca4_coordinates(code=code)
            if hasattr(af_obj, "coordinates"):
                xs = af_obj.coordinates.x
                ys = af_obj.coordinates.y
                root_af = [[float(x), float(y)] for x, y in zip(xs, ys)]
            else:
                root_af = af_obj

        mesh_parts.extend(
            build_wing_airfoil_loft_mesh(
                root_airfoil_coords=root_af,
                tip_airfoil_coords=tip_af,
                s_ref_m2=wing_pf.get("s_ref_m2", 10.0),
                aspect_ratio=wing_pf.get("aspect_ratio", 6.0),
                taper_ratio=wing_pf.get("taper_ratio", 1.0),
                sweep_quarter_chord_deg=wing_pf.get("sweep_quarter_chord_deg", 0.0),
                x_offset_m=wing_pf.get("x_offset_m", 0.0),
                y_offset_m=wing_pf.get("y_offset_m", 0.0),
                z_offset_m=wing_pf.get("z_offset_m", 0.0),
                dihedral_deg=wing_pf.get("dihedral_deg", 0.0),
                incidence_deg=wing_pf.get("incidence_deg", 0.0),
                spanwise_control_points=wing.get("controls", {}).get("spanwise_control_points"),
                control_surfaces=wing.get("controls", {}).get("control_surfaces"),
                name_prefix="wing",
            )
        )

    tail = geometry.get("tail", {})
    for surf in tail.get("surfaces", []):
        source = surf.get("source", "horizontal")
        src_def = tail.get(source, {})
        root_af_t = src_def.get("root_airfoil", {}).get("coords")
        tip_af_t = src_def.get("tip_airfoil", {}).get("coords")
        ctrl_t = src_def.get("controls", {})
        spanwise_cps_t = ctrl_t.get("spanwise_control_points") if isinstance(ctrl_t, dict) else None
        control_surfaces_t = ctrl_t.get("control_surfaces") if isinstance(ctrl_t, dict) else None

        if not root_af_t:
            from .geometry_detailed import naca4_coordinates

            # Try to get code from definition
            af_def = src_def.get("root_airfoil", {})
            code = af_def.get("code", "0012") if isinstance(af_def, dict) else "0012"
            print(f"[Visualizer] Generating tail ({source}) root airfoil with code={code}")

            af_obj = naca4_coordinates(code=code)
            if hasattr(af_obj, "coordinates"):
                xs = af_obj.coordinates.x
                ys = af_obj.coordinates.y
                root_af_t = [[float(x), float(y)] for x, y in zip(xs, ys)]
            else:
                root_af_t = af_obj

        builder = surf.get("builder", "wing_loft")

        if builder == "wing_loft":
            mesh_parts.extend(
                build_wing_airfoil_loft_mesh(
                    root_airfoil_coords=root_af_t,
                    tip_airfoil_coords=tip_af_t,
                    s_ref_m2=surf.get("s_ref_m2", 1.0),
                    aspect_ratio=surf.get("aspect_ratio", 4.0),
                    taper_ratio=surf.get("taper_ratio", 0.6),
                    sweep_quarter_chord_deg=surf.get("sweep_quarter_chord_deg", 0.0),
                    x_offset_m=surf.get("x_offset_m", 0.0),
                    y_offset_m=surf.get("y_offset_m", 0.0),
                    z_offset_m=surf.get("z_offset_m", 0.0),
                    dihedral_deg=surf.get("dihedral_deg", 0.0),
                    incidence_deg=surf.get("incidence_deg", 0.0),
                    spanwise_control_points=spanwise_cps_t,
                    control_surfaces=control_surfaces_t,
                    name_prefix=surf.get("name_prefix", "tail"),
                    color="#e377c2",
                )
            )
        elif builder == "vertical_loft":
            mesh_parts.append(
                build_vertical_tail_airfoil_loft_mesh(
                    root_airfoil_coords=root_af_t,
                    tip_airfoil_coords=tip_af_t,
                    s_ref_m2=surf.get("s_ref_m2", 1.0),
                    aspect_ratio=surf.get("aspect_ratio", 1.8),
                    taper_ratio=surf.get("taper_ratio", 0.7),
                    sweep_quarter_chord_deg=surf.get("sweep_quarter_chord_deg", 0.0),
                    x_offset_m=surf.get("x_offset_m", 0.0),
                    y_offset_m=surf.get("y_offset_m", 0.0),
                    z_offset_m=surf.get("z_offset_m", 0.0),
                    spanwise_control_points=spanwise_cps_t,
                    name=surf.get("name", "vtail"),
                    color="#fd8d3c",
                )
            )

    return mesh_parts


def _normalize_web_config(web_config: dict | None) -> dict:
    base: dict = web_config if isinstance(web_config, dict) else {}
    layout_value = base.get("layout")
    layout = layout_value if isinstance(layout_value, dict) else {}
    layout_type = layout.get("type")
    if not isinstance(layout_type, str) or not layout_type:
        layout_type = "2x2"
    grid_enabled = base.get("grid_enabled")
    if grid_enabled is None:
        grid_enabled = True
    default_zoom = base.get("default_zoom")
    if default_zoom is None:
        default_zoom = 1.0
    sky = base.get("sky")
    if not isinstance(sky, str) or not sky.strip():
        sky = "linear-gradient(180deg, #7cc6ff 0%, #cbe9ff 45%, #f6fbff 100%)"
    return {
        "layout": {"type": layout_type},
        "grid_enabled": bool(grid_enabled),
        "default_zoom": float(default_zoom),
        "sky": sky,
    }


def render_three_view_html_from_parts(
    parts: list[MeshPart],
    resource_config: dict | None = None,
    web_config: dict | None = None,
) -> str:
    rc = resource_config if isinstance(resource_config, dict) else None
    parts_data = []
    for p in parts:
        parts_data.append({"name": p.name, "color": p.color, "vertices": p.vertices, "indices": p.indices})

    parts_json = json.dumps(parts_data)
    config = _normalize_web_config(web_config)
    config_json = json.dumps(config)

    html_template = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <script>
    window.onerror = function(msg, url, line, col, error) {
        var div = document.createElement("div");
        div.style.position = "absolute";
        div.style.top = "10px";
        div.style.left = "10px";
        div.style.backgroundColor = "rgba(255, 0, 0, 0.9)";
        div.style.color = "white";
        div.style.padding = "10px";
        div.style.zIndex = "10000";
        div.style.maxWidth = "90%";
        div.style.wordWrap = "break-word";
        div.style.fontFamily = "monospace";
        div.innerHTML = "<strong>JS Error:</strong> " + msg + "<br>URL: " + url + "<br>Line: " + line;
        if(document.body) document.body.appendChild(div);
        else window.addEventListener('DOMContentLoaded', () => document.body.appendChild(div));
        return false;
    };
  </script>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Aircraft Geometry Analysis</title>
  <style>
    :root { --bg: SKY_PLACEHOLDER; --panel: rgba(7, 20, 38, 0.55); --text: #eaf4ff; --accent: #38bdf8; --card: rgba(255,255,255,0.14); --card-border: rgba(255,255,255,0.25); }
    body { margin: 0; background: var(--bg); color: var(--text); font-family: 'Segoe UI', Roboto, sans-serif; overflow: hidden; height: 100vh; display: flex; flex-direction: column; }

    #toolbar {
        height: 48px; background: var(--panel); border-bottom: 1px solid rgba(255,255,255,0.18);
        display: flex; align-items: center; padding: 0 16px; gap: 16px; font-size: 14px;
        backdrop-filter: blur(10px);
    }
    .btn {
        background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.25); color: #fff; padding: 6px 12px; border-radius: 8px; cursor: pointer; transition: background 0.2s, border-color 0.2s;
    }
    .btn:hover { background: rgba(255,255,255,0.28); border-color: rgba(255,255,255,0.4); }
    .btn.active { background: var(--accent); }
    .info-tag { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; color: #dbeafe; }
    .mode-group { display: flex; gap: 8px; align-items: center; }
    .mode-card {
        background: var(--card); color: #e6f3ff; border: 1px solid var(--card-border); border-radius: 10px;
        padding: 6px 12px; cursor: pointer; transition: all 0.2s; min-width: 64px; text-align: center;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
    }
    .mode-card.active {
        background: rgba(56,189,248,0.3); color: #ffffff; border-color: rgba(56,189,248,0.8);
        box-shadow: 0 0 0 2px rgba(56,189,248,0.35);
    }

    #workspace {
        flex: 1; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 2px; background: rgba(255,255,255,0.15);
    }
    .view-container { position: relative; background: rgba(255,255,255,0.08); overflow: hidden; }
    .view-label {
        position: absolute; left: 8px; top: 8px;
        background: rgba(10,24,40,0.55); color: #eaf4ff; padding: 4px 10px; border-radius: 8px;
        font-size: 12px; pointer-events: none; user-select: none; border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(6px);
    }
    canvas { display: block; width: 100%; height: 100%; outline: none; }

    #loader {
        position: fixed; inset: 0; background: var(--bg); display: flex; justify-content: center; align-items: center; z-index: 999; transition: opacity 0.5s;
    }
  </style>
</head>
<body>
  <div id="loader">Loading Geometry...</div>

  <div id="toolbar">
    <b>Aircraft Viz</b>
    <span class="info-tag" id="dims"></span>
    <div style="flex:1"></div>
    <div class="mode-group">
      <button class="mode-card active" id="btn-mode-solid">实体</button>
      <button class="mode-card" id="btn-mode-wire">线框</button>
    </div>
    <button class="btn" id="btn-grid" title="Toggle Grid (G)">Grid</button>
    <button class="btn" id="btn-reset" title="Reset Views (R)">Reset</button>
  </div>

  <div id="workspace">
    <div class="view-container">
        <div class="view-label">Top (X-Y)</div>
        <canvas id="cv_top"></canvas>
    </div>
    <div class="view-container">
        <div class="view-label">Side (X-Z)</div>
        <canvas id="cv_side"></canvas>
    </div>
    <div class="view-container">
        <div class="view-label">Front (Y-Z)</div>
        <canvas id="cv_front"></canvas>
    </div>
    <div class="view-container">
        <div class="view-label">Perspective</div>
        <canvas id="cv_iso"></canvas>
    </div>
  </div>

  LOADER_PLACEHOLDER
  <script>
    (function() {
    const loaderEl = document.getElementById('loader');
    function showLoaderError(text) {
        if (!loaderEl) return;
        loaderEl.textContent = text || '加载失败';
    }
    function hideLoader() {
        if (!loaderEl) return;
        loaderEl.style.opacity = 0;
        setTimeout(() => {
            if (loaderEl && loaderEl.parentElement) {
                loaderEl.remove();
            }
        }, 500);
    }

    const parts = PARAMS_PLACEHOLDER;
    const config = CONFIG_PLACEHOLDER || {};
    const workspaceEl = document.getElementById('workspace');
    const layoutCfg = config.layout || { type: "2x2" };
    function applyLayout() {
        const type = (layoutCfg.type || "2x2").toLowerCase();
        const items = [
          { id: "cv_top", el: document.getElementById("cv_top")?.parentElement },
          { id: "cv_side", el: document.getElementById("cv_side")?.parentElement },
          { id: "cv_front", el: document.getElementById("cv_front")?.parentElement },
          { id: "cv_iso", el: document.getElementById("cv_iso")?.parentElement },
        ];
        function setGrid(cols, rows) {
            if (workspaceEl) {
                workspaceEl.style.gridTemplateColumns = cols.map(v => `${v}fr`).join(' ');
                workspaceEl.style.gridTemplateRows = rows.map(v => `${v}fr`).join(' ');
            }
        }
        function place(el, colStart, colSpan, rowStart, rowSpan) {
            if (!el) return;
            el.style.gridColumn = `${colStart} / span ${colSpan}`;
            el.style.gridRow = `${rowStart} / span ${rowSpan}`;
        }
        items.forEach(it => { if (it.el) { it.el.style.gridColumn = ""; it.el.style.gridRow = ""; } });
        if (type === "2x2") {
            setGrid([1,1], [1,1]);
            place(items[0].el, 1, 1, 1, 1);
            place(items[1].el, 2, 1, 1, 1);
            place(items[2].el, 1, 1, 2, 1);
            place(items[3].el, 2, 1, 2, 1);
        } else {
            setGrid([1,1,1], [1,1]);
            if (type === "top_first") {
                place(items[0].el, 1, 3, 1, 1);
                place(items[1].el, 1, 1, 2, 1);
                place(items[2].el, 2, 1, 2, 1);
                place(items[3].el, 3, 1, 2, 1);
            } else if (type === "side_first") {
                place(items[1].el, 1, 3, 1, 1);
                place(items[0].el, 1, 1, 2, 1);
                place(items[2].el, 2, 1, 2, 1);
                place(items[3].el, 3, 1, 2, 1);
            } else if (type === "front_first") {
                place(items[2].el, 1, 3, 1, 1);
                place(items[0].el, 1, 1, 2, 1);
                place(items[1].el, 2, 1, 2, 1);
                place(items[3].el, 3, 1, 2, 1);
            } else if (type === "iso_first") {
                place(items[3].el, 1, 3, 1, 1);
                place(items[0].el, 1, 1, 2, 1);
                place(items[1].el, 2, 1, 2, 1);
                place(items[2].el, 3, 1, 2, 1);
            } else {
                setGrid([1,1], [1,1]);
            }
        }
    }
    applyLayout();

    function computeBounds() {
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;
        let minZ = Infinity, maxZ = -Infinity;
        let has = false;
        parts.forEach(p => {
            for (let i = 0; i < p.vertices.length; i += 3) {
                const x = p.vertices[i], y = p.vertices[i + 1], z = p.vertices[i + 2];
                minX = Math.min(minX, x); maxX = Math.max(maxX, x);
                minY = Math.min(minY, y); maxY = Math.max(maxY, y);
                minZ = Math.min(minZ, z); maxZ = Math.max(maxZ, z);
                has = true;
            }
        });
        if (!has) return null;
        return { minX, maxX, minY, maxY, minZ, maxZ };
    }

    function projectPoint(v, type) {
        const x = v[0], y = v[1], z = v[2];
        if (type === "top") return [x, y];
        if (type === "side") return [x, z];
        if (type === "front") return [y, z];
        const ang = -Math.PI / 4;
        const cosA = Math.cos(ang), sinA = Math.sin(ang);
        const x1 = x * cosA - y * sinA;
        const y1 = x * sinA + y * cosA;
        const pitch = 0.6;
        const cosP = Math.cos(pitch), sinP = Math.sin(pitch);
        const y2 = y1 * cosP - z * sinP;
        return [x1, y2];
    }

    function projectedBounds(type) {
        let minU = Infinity, maxU = -Infinity;
        let minV = Infinity, maxV = -Infinity;
        let has = false;
        parts.forEach(p => {
            for (let i = 0; i < p.vertices.length; i += 3) {
                const u = projectPoint([p.vertices[i], p.vertices[i + 1], p.vertices[i + 2]], type);
                minU = Math.min(minU, u[0]); maxU = Math.max(maxU, u[0]);
                minV = Math.min(minV, u[1]); maxV = Math.max(maxV, u[1]);
                has = true;
            }
        });
        if (!has) return null;
        return { minU, maxU, minV, maxV };
    }

    function renderFallbackView(canvas, type) {
        if (!canvas) return;
        const rect = canvas.parentElement.getBoundingClientRect();
        const w = Math.max(1, Math.floor(rect.width));
        const h = Math.max(1, Math.floor(rect.height));
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        ctx.clearRect(0, 0, w, h);
        const pb = projectedBounds(type);
        if (!pb) return;
        const du = Math.max(1e-6, pb.maxU - pb.minU);
        const dv = Math.max(1e-6, pb.maxV - pb.minV);
        const scale = 0.9 * Math.min(w / du, h / dv);
        const cu = 0.5 * (pb.minU + pb.maxU);
        const cv = 0.5 * (pb.minV + pb.maxV);
        ctx.strokeStyle = "rgba(15, 25, 40, 0.7)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        parts.forEach(p => {
            const verts = p.vertices;
            const idx = p.indices;
            for (let i = 0; i < idx.length; i += 3) {
                const a = idx[i] * 3;
                const b = idx[i + 1] * 3;
                const c = idx[i + 2] * 3;
                const pa = projectPoint([verts[a], verts[a + 1], verts[a + 2]], type);
                const pbp = projectPoint([verts[b], verts[b + 1], verts[b + 2]], type);
                const pc = projectPoint([verts[c], verts[c + 1], verts[c + 2]], type);
                const ax = (pa[0] - cu) * scale + w / 2;
                const ay = h / 2 - (pa[1] - cv) * scale;
                const bx = (pbp[0] - cu) * scale + w / 2;
                const by = h / 2 - (pbp[1] - cv) * scale;
                const cx = (pc[0] - cu) * scale + w / 2;
                const cy = h / 2 - (pc[1] - cv) * scale;
                ctx.moveTo(ax, ay); ctx.lineTo(bx, by);
                ctx.lineTo(cx, cy); ctx.lineTo(ax, ay);
            }
        });
        ctx.stroke();
    }

    function startFallback(reason) {
        const b = computeBounds();
        if (!b) {
            showLoaderError("无可用几何数据");
            return;
        }
        if (reason) {
            showLoaderError(reason);
        }
        const dims = document.getElementById('dims');
        if (dims) {
            dims.textContent = `L:${(b.maxX - b.minX).toFixed(2)}m W:${(b.maxY - b.minY).toFixed(2)}m H:${(b.maxZ - b.minZ).toFixed(2)}m`;
        }
        renderFallbackView(document.getElementById("cv_top"), "top");
        renderFallbackView(document.getElementById("cv_side"), "side");
        renderFallbackView(document.getElementById("cv_front"), "front");
        renderFallbackView(document.getElementById("cv_iso"), "iso");
        hideLoader();
        window.addEventListener("resize", () => {
            renderFallbackView(document.getElementById("cv_top"), "top");
            renderFallbackView(document.getElementById("cv_side"), "side");
            renderFallbackView(document.getElementById("cv_front"), "front");
            renderFallbackView(document.getElementById("cv_iso"), "iso");
        });
    }

    if (!window.THREE) {
        startFallback('Three.js 未加载（可能网络受限或被拦截）');
        return;
    }
    if (!window.THREE.OrbitControls) {
        window.THREE.OrbitControls = function(camera, domElement) {
            this.object = camera;
            this.domElement = domElement;
            this.enableRotate = true;
            this.enablePan = true;
            this.enableZoom = true;
            this.enableDamping = false;
            this.mouseButtons = {};
            this.update = function(){};
            this.reset = function(){};
        };
    }

    // State
    const state = {
        displayMode: "solid",
        showGrid: config.grid_enabled !== false
    };

    // Scene Setup
    const scenes = {
        ortho: new THREE.Scene(),
        iso: new THREE.Scene()
    };
    scenes.ortho.background = null;
    scenes.iso.background = null;

    // Lights
    function setupLights(scene) {
        const ambient = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambient);
        const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 0.6);
        hemi.position.set(0, 0, 20);
        scene.add(hemi);
        const dir = new THREE.DirectionalLight(0xffffff, 1.0);
        dir.position.set(10, -20, 30);
        scene.add(dir);
    }
    setupLights(scenes.ortho);
    setupLights(scenes.iso);

    // Geometry Processing
    const materials = [];
    const edgeLines = [];
    const mainGroup = new THREE.Group();

    // Calculate bounds
    let bounds = {minX:Infinity, maxX:-Infinity, minY:Infinity, maxY:-Infinity, minZ:Infinity, maxZ:-Infinity};

    parts.forEach(p => {
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(p.vertices), 3));
        geo.setIndex(new THREE.BufferAttribute(new Uint32Array(p.indices), 1));
        geo.computeVertexNormals();

        const mat = new THREE.MeshStandardMaterial({
            color: new THREE.Color(p.color),
            metalness: 0.1,
            roughness: 0.7,
            side: THREE.DoubleSide,
            polygonOffset: true,
            polygonOffsetFactor: 1,
            polygonOffsetUnits: 1
        });
        materials.push(mat);

        const mesh = new THREE.Mesh(geo, mat);
        mainGroup.add(mesh);

        // Edges for better definition
        const edges = new THREE.EdgesGeometry(geo, 30);
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35 }));
        line.name = "mesh-edge";
        mesh.add(line);
        edgeLines.push(line);

        // Bounds calc
        for(let i=0; i<p.vertices.length; i+=3) {
            const x=p.vertices[i], y=p.vertices[i+1], z=p.vertices[i+2];
            bounds.minX = Math.min(bounds.minX, x); bounds.maxX = Math.max(bounds.maxX, x);
            bounds.minY = Math.min(bounds.minY, y); bounds.maxY = Math.max(bounds.maxY, y);
            bounds.minZ = Math.min(bounds.minZ, z); bounds.maxZ = Math.max(bounds.maxZ, z);
        }
    });

    // Center geometry
    let size = new THREE.Vector3(bounds.maxX-bounds.minX, bounds.maxY-bounds.minY, bounds.maxZ-bounds.minZ);
    let center = new THREE.Vector3((bounds.minX+bounds.maxX)*0.5, (bounds.minY+bounds.maxY)*0.5, (bounds.minZ+bounds.maxZ)*0.5);
    if (!Number.isFinite(size.x) || !Number.isFinite(size.y) || !Number.isFinite(size.z) || (size.x + size.y + size.z) <= 1e-9) {
        size = new THREE.Vector3(1, 1, 1);
        center = new THREE.Vector3(0, 0, 0);
        document.getElementById('dims').textContent = "无可用几何数据";
    }
    mainGroup.position.sub(center); // Center at origin

    // Clone for both scenes
    scenes.iso.add(mainGroup);
    scenes.ortho.add(mainGroup.clone());

    // Info Update
    if (!document.getElementById('dims').textContent) {
        document.getElementById('dims').textContent = `L:${size.x.toFixed(2)}m W:${size.y.toFixed(2)}m H:${size.z.toFixed(2)}m`;
    }

    // Helpers (Grids/Axes)
    const helpersOrtho = new THREE.Group();
    const gridColor = 0x333333;
    const axisSize = Math.max(size.x, size.y, size.z) * 1.5;

    // Top Grid (XY)
    const gridXY = new THREE.GridHelper(axisSize, 20, 0x555555, gridColor);
    gridXY.rotation.x = Math.PI/2;
    helpersOrtho.add(gridXY);

    // Axes
    helpersOrtho.add(new THREE.AxesHelper(axisSize * 0.1));

    scenes.ortho.add(helpersOrtho);
    const helpersIso = helpersOrtho.clone();
    scenes.iso.add(helpersIso);

    // Cameras & Renderers
    const viewRadius = Math.max(size.x, size.y, size.z, 1.0) * 0.9;
    const baseZoom = Math.max(0.2, Number(config.default_zoom || 1.0));

    const views = [
        { id: 'cv_top',   type: 'ortho', axis: [0, 0, 1], up: [0,1,0], pos: [0,0,viewRadius*2.2] },
        { id: 'cv_side',  type: 'ortho', axis: [0, -1, 0], up: [0,0,1], pos: [0,-viewRadius*2.2,0] },
        { id: 'cv_front', type: 'ortho', axis: [1, 0, 0], up: [0,0,1], pos: [viewRadius*2.2,0,0] },
        { id: 'cv_iso',   type: 'persp', pos: [viewRadius*1.6, -viewRadius*1.6, viewRadius*1.2] }
    ];

    const renderMap = {};
    const syncState = { syncing: false, orthoZoom: baseZoom };

    views.forEach(v => {
        const cv = document.getElementById(v.id);
        const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setClearColor(0x000000, 0);

        let camera;
        if (v.type === 'ortho') {
            camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10000);
            camera.zoom = baseZoom;
        } else {
            camera = new THREE.PerspectiveCamera(45, 1, 0.1, 10000);
        }

        camera.up.set(...(v.up || [0,0,1]));
        camera.position.set(...v.pos);
        camera.lookAt(0,0,0);

        const controls = { target: new THREE.Vector3(0,0,0) };

        renderMap[v.id] = {
            renderer,
            camera,
            controls,
            scene: v.type === 'persp' ? scenes.iso : scenes.ortho,
            axis: v.axis || null,
            up: v.up || [0,0,1]
        };
    });

    function attachManualControls(id) {
        const item = renderMap[id];
        const cv = item.renderer.domElement;
        let dragging = false;
        let lastX = 0, lastY = 0, btn = 0;
        cv.addEventListener('mousedown', (e) => { dragging = true; lastX = e.clientX; lastY = e.clientY; btn = e.button; e.preventDefault(); });
        window.addEventListener('mouseup', () => { dragging = false; });
        cv.addEventListener('mousemove', (e) => {
            if (!dragging) return;
            const dx = e.clientX - lastX;
            const dy = e.clientY - lastY;
            lastX = e.clientX; lastY = e.clientY;
            if (btn === 0) {
                if (item.camera.isOrthographicCamera) {
                    const axisVec = item.axis ? new THREE.Vector3(item.axis[0], item.axis[1], item.axis[2]).normalize() : new THREE.Vector3(0,0,1);
                    const angle = dx * 0.005;
                    const q = new THREE.Quaternion().setFromAxisAngle(axisVec, angle);
                    const pos = item.camera.position.clone().sub(item.controls.target);
                    pos.applyQuaternion(q);
                    item.camera.position.copy(pos.add(item.controls.target));
                    item.camera.lookAt(item.controls.target);
                } else {
                    const target = item.controls.target;
                    const offset = item.camera.position.clone().sub(target);
                    const sph = new THREE.Spherical().setFromVector3(offset);
                    sph.theta -= dx * 0.005;
                    sph.phi = Math.max(0.01, Math.min(Math.PI - 0.01, sph.phi - dy * 0.005));
                    offset.setFromSpherical(sph);
                    item.camera.position.copy(target.clone().add(offset));
                    item.camera.lookAt(target);
                }
            } else if (btn === 2) {
                const dir = item.camera.getWorldDirection(new THREE.Vector3());
                const right = new THREE.Vector3().crossVectors(dir, item.camera.up).normalize();
                const upv = item.camera.up.clone().normalize();
                const scale = 0.001 * Math.max(viewRadius, 1.0);
                const pan = right.multiplyScalar(-dx * scale).add(upv.multiplyScalar(dy * scale));
                item.controls.target.add(pan);
                item.camera.position.add(pan);
            }
            item.camera.updateProjectionMatrix();
            syncViews(id);
        });
        cv.addEventListener('wheel', (e) => {
            e.preventDefault();
            if (item.camera.isOrthographicCamera) {
                const factor = e.deltaY > 0 ? 0.92 : 1.08;
                item.camera.zoom = Math.max(0.2, Math.min(10.0, item.camera.zoom * factor));
            } else {
                const target = item.controls.target;
                const offset = item.camera.position.clone().sub(target);
                const dolly = e.deltaY > 0 ? 1.08 : 0.92;
                offset.multiplyScalar(dolly);
                item.camera.position.copy(target.clone().add(offset));
            }
            item.camera.updateProjectionMatrix();
            syncViews(id);
        }, { passive: false });
        cv.addEventListener('contextmenu', (e) => e.preventDefault());
    }

    function syncViews(sourceId) {
        if (syncState.syncing) return;
        const source = renderMap[sourceId];
        if (!source) return;
        const target = source.controls.target.clone();
        if (source.camera.isOrthographicCamera) {
            syncState.orthoZoom = source.camera.zoom;
        }
        syncState.syncing = true;
        const sourceDistance = source.camera.position.distanceTo(target);
        Object.entries(renderMap).forEach(([id, item]) => {
            if (id === sourceId) return;
            item.controls.target.copy(target);
            if (item.camera.isOrthographicCamera) {
                item.camera.zoom = syncState.orthoZoom;
                if (item.axis) {
                    const axisVec = new THREE.Vector3(item.axis[0], item.axis[1], item.axis[2]).normalize();
                    item.camera.position.copy(axisVec.multiplyScalar(sourceDistance).add(target));
                    item.camera.up.set(item.up[0], item.up[1], item.up[2]);
                    item.camera.lookAt(target);
                }
            } else {
                if (source.camera.isPerspectiveCamera) {
                    item.camera.position.copy(source.camera.position);
                    item.camera.quaternion.copy(source.camera.quaternion);
                } else {
                    const offset = item.camera.position.clone().sub(item.controls.target);
                    item.camera.position.copy(target.clone().add(offset));
                    item.camera.lookAt(target);
                }
            }
            item.camera.updateProjectionMatrix();
        });
        syncState.syncing = false;
    }

    // Resize Handling
    function handleResize() {
        views.forEach(v => {
            const item = renderMap[v.id];
            const cv = item.renderer.domElement;
            const width = cv.parentElement.clientWidth;
            const height = cv.parentElement.clientHeight;

            item.renderer.setSize(width, height, false);

            if (item.camera.isOrthographicCamera) {
                const aspect = width / height;
                const frustumSize = viewRadius * 2.8;
                item.camera.left = -frustumSize * aspect / 2;
                item.camera.right = frustumSize * aspect / 2;
                item.camera.top = frustumSize / 2;
                item.camera.bottom = -frustumSize / 2;
            } else {
                item.camera.aspect = width / height;
            }
            item.camera.updateProjectionMatrix();
        });
    }

    window.addEventListener('resize', handleResize);
    // Initial size
    setTimeout(handleResize, 50);

    // Loop
    function animate() {
        requestAnimationFrame(animate);
        Object.values(renderMap).forEach(item => {
            item.renderer.render(item.scene, item.camera);
        });
    }
    animate();

    // UI Logic
    hideLoader();

    // Wireframe Toggle
    function setDisplayMode(mode) {
        state.displayMode = mode;
        const isWire = mode === "wire";
        materials.forEach(m => {
            m.wireframe = isWire;
            m.transparent = false;
            m.opacity = 1.0;
        });
        function setEdgesVisible(scene, v) { scene.traverse(obj => { if (obj.isLineSegments && obj.name === "mesh-edge") obj.visible = v; }); }
        setEdgesVisible(scenes.iso, isWire);
        setEdgesVisible(scenes.ortho, isWire);
        document.getElementById('btn-mode-solid').classList.toggle('active', mode === "solid");
        document.getElementById('btn-mode-wire').classList.toggle('active', mode === "wire");
    }
    document.getElementById('btn-mode-solid').onclick = () => setDisplayMode("solid");
    document.getElementById('btn-mode-wire').onclick = () => setDisplayMode("wire");

    // Grid Toggle
    helpersOrtho.visible = state.showGrid;
    helpersIso.visible = state.showGrid;
    document.getElementById('btn-grid').classList.toggle('active', state.showGrid);
    function toggleGrid() {
        state.showGrid = !state.showGrid;
        helpersOrtho.visible = state.showGrid;
        helpersIso.visible = state.showGrid;
        document.getElementById('btn-grid').classList.toggle('active', state.showGrid);
    }
    document.getElementById('btn-grid').onclick = toggleGrid;

    // Reset
    document.getElementById('btn-reset').onclick = () => {
        views.forEach(v => {
            const item = renderMap[v.id];
            item.controls.target.set(0,0,0);
            item.camera.position.set(...v.pos);
            item.camera.lookAt(0,0,0);
            if (item.camera.isOrthographicCamera) item.camera.zoom = baseZoom;
            item.camera.updateProjectionMatrix();
        });
        syncViews('cv_iso');
        handleResize();
    };

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
        if (e.key.toLowerCase() === 'w') setDisplayMode(state.displayMode === "wire" ? "solid" : "wire");
        if (e.key.toLowerCase() === 'g') toggleGrid();
        if (e.key.toLowerCase() === 'r') document.getElementById('btn-reset').click();
    });

    Object.keys(renderMap).forEach(id => attachManualControls(id));
    Object.values(renderMap).forEach(item => { item.controls.target.set(0,0,0); });

    setDisplayMode("solid");
    })();
  </script>
</body>
</html>"""

    html = html_template.replace("PARAMS_PLACEHOLDER", parts_json)
    html = html.replace("CONFIG_PLACEHOLDER", config_json)
    html = html.replace("SKY_PLACEHOLDER", config["sky"])
    html = html.replace("LOADER_PLACEHOLDER", _three_js_loader_script(rc, include_orbit=True))
    return html


def render_three_view_html_from_geometry(
    geometry: dict, resource_config: dict | None = None, web_config: dict | None = None
) -> str:
    rc = resource_config if isinstance(resource_config, dict) else None
    if rc is None and isinstance(geometry.get("resources"), dict):
        rc = geometry.get("resources")
    mesh_parts = build_mesh_parts_from_geometry(geometry)
    return render_three_view_html_from_parts(mesh_parts, rc, web_config)


def generate_three_view_html(
    geometry: dict, output_path: str, resource_config: dict | None = None, web_config: dict | None = None
):
    html = render_three_view_html_from_geometry(geometry, resource_config, web_config)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def build_vertical_tail_airfoil_loft_mesh(
    *,
    root_airfoil_coords: Any,
    tip_airfoil_coords: Any | None,
    s_ref_m2: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
    x_offset_m: float,
    y_offset_m: float,
    z_offset_m: float,
    spanwise_control_points: list[dict] | None = None,
    name: str = "vtail",
    color: str = "#fd8d3c",
) -> MeshPart:
    root_airfoil_pts = _coerce_airfoil_coords(root_airfoil_coords, field_name="root_airfoil_coords")
    if len(root_airfoil_pts) < 10:
        raise ValueError("root_airfoil_coords must be a list with at least 10 points.")
    if tip_airfoil_coords is not None:
        tip_airfoil_pts = _coerce_airfoil_coords(tip_airfoil_coords, field_name="tip_airfoil_coords")
        if len(tip_airfoil_pts) != len(root_airfoil_pts):
            raise ValueError("tip_airfoil_coords must have the same number of points as root_airfoil_coords.")
    else:
        tip_airfoil_pts = None

    s = float(s_ref_m2)
    ar = float(aspect_ratio)
    taper = float(taper_ratio)
    if s <= 0.0 or ar <= 0.0:
        raise ValueError("Invalid tail reference area or aspect ratio.")
    if not (0.05 <= taper <= 1.0):
        raise ValueError("taper_ratio must be in [0.05, 1.0].")

    root_pts = [(float(p[0]), float(p[1])) for p in root_airfoil_pts]
    tip_pts = [(float(p[0]), float(p[1])) for p in tip_airfoil_pts] if tip_airfoil_pts is not None else None
    n = len(root_pts)

    cps = []
    if spanwise_control_points:
        for p in spanwise_control_points:
            if not isinstance(p, dict):
                raise ValueError("Each spanwise control point must be an object.")
            eta = p.get("eta", None)
            if not isinstance(eta, (int, float)):
                raise ValueError("spanwise control point requires numeric eta.")
            item = {"eta": min(max(float(eta), 0.0), 1.0)}
            if "twist_deg" in p:
                if not isinstance(p.get("twist_deg"), (int, float)):
                    raise ValueError("twist_deg must be numeric.")
                item["twist_deg"] = float(p["twist_deg"])
            if "chord_scale" in p:
                if not isinstance(p.get("chord_scale"), (int, float)):
                    raise ValueError("chord_scale must be numeric.")
                item["chord_scale"] = float(p["chord_scale"])
            if "thickness_scale" in p:
                if not isinstance(p.get("thickness_scale"), (int, float)):
                    raise ValueError("thickness_scale must be numeric.")
                item["thickness_scale"] = float(p["thickness_scale"])
            if "x_le_offset_m" in p:
                if not isinstance(p.get("x_le_offset_m"), (int, float)):
                    raise ValueError("x_le_offset_m must be numeric.")
                item["x_le_offset_m"] = float(p["x_le_offset_m"])
            if "y_offset_m" in p:
                if not isinstance(p.get("y_offset_m"), (int, float)):
                    raise ValueError("y_offset_m must be numeric.")
                item["y_offset_m"] = float(p["y_offset_m"])
            cps.append(item)
    cps.sort(key=lambda t: t["eta"])

    def _interp(key: str, eta: float, default: float) -> float:
        pts = [(0.0, default), (1.0, default)]
        for p in cps:
            if key in p:
                pts.append((float(p["eta"]), float(p[key])))
        pts.sort(key=lambda t: t[0])
        if eta <= pts[0][0]:
            return pts[0][1]
        if eta >= pts[-1][0]:
            return pts[-1][1]
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= eta <= x1:
                t = (eta - x0) / max(1e-9, (x1 - x0))
                return y0 * (1.0 - t) + y1 * t
        return default

    etas = [0.0, 1.0]
    for p in cps:
        e = float(p["eta"])
        if 0.0 < e < 1.0:
            etas.append(e)
    etas = sorted(set(etas))

    span = sqrt(ar * s)
    c_root = 2.0 * s / (span * (1.0 + taper))
    c_tip = taper * c_root

    sweep_rad = float(__import__("math").radians(float(sweep_quarter_chord_deg)))

    def section_coords(eta: float) -> list[tuple[float, float]]:
        if tip_pts is None:
            return root_pts
        out = []
        for (xr, yr), (xt, yt) in zip(root_pts, tip_pts):
            out.append((xr * (1.0 - eta) + xt * eta, yr * (1.0 - eta) + yt * eta))
        return out

    def apply_twist(xn: float, yn: float, twist_deg: float) -> tuple[float, float]:
        th = float(__import__("math").radians(float(twist_deg)))
        c = float(__import__("math").cos(th))
        s_ = float(__import__("math").sin(th))
        x0 = xn - 0.25
        y0 = yn
        x1 = x0 * c - y0 * s_
        y1 = x0 * s_ + y0 * c
        return x1 + 0.25, y1

    verts: list[list[float]] = []
    for eta in etas:
        z = float(z_offset_m) + span * eta
        chord = (c_root * (1.0 - eta) + c_tip * eta) * _interp("chord_scale", eta, 1.0)
        thickness_scale = _interp("thickness_scale", eta, 1.0)
        x_le_offset = _interp("x_le_offset_m", eta, 0.0)
        y_extra = _interp("y_offset_m", eta, 0.0)
        twist = _interp("twist_deg", eta, 0.0)
        x_qc = float(x_offset_m) + tan(sweep_rad) * (z - float(z_offset_m))
        x_le = x_qc - 0.25 * chord + x_le_offset
        sec = section_coords(eta)
        for xn, yn in sec:
            xt, yt = apply_twist(xn, yn, twist)
            verts.append([x_le + xt * chord, float(y_offset_m) + y_extra + (yt * thickness_scale) * chord, z])

    tris: list[list[int]] = []
    n_sec = len(etas)
    for k in range(n_sec - 1):
        o0 = k * n
        o1 = (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            a = o0 + i
            b0 = o0 + j
            c0 = o1 + j
            d0 = o1 + i
            tris.append([a, b0, c0])
            tris.append([a, c0, d0])

    def cap(offset: int, flip: bool) -> None:
        cx = 0.0
        cy = 0.0
        cz = 0.0
        for i in range(n):
            cx += verts[offset + i][0]
            cy += verts[offset + i][1]
            cz += verts[offset + i][2]
        cx /= n
        cy /= n
        cz /= n
        c_idx = len(verts)
        verts.append([cx, cy, cz])
        for i in range(n):
            j = (i + 1) % n
            if flip:
                tris.append([c_idx, offset + j, offset + i])
            else:
                tris.append([c_idx, offset + i, offset + j])

    cap(0, flip=False)
    cap((n_sec - 1) * n, flip=True)
    part_list: list[MeshPart] = []
    _append_part(part_list, name=name, color=color, verts=verts, tris=tris)
    return part_list[0]


def build_extruded_trapezoid(
    *,
    root_le: list[float],
    root_te: list[float],
    tip_le: list[float],
    tip_te: list[float],
    half_thickness_m: float,
) -> tuple[list[list[float]], list[list[int]]]:
    ht = float(half_thickness_m)
    rle = [float(root_le[0]), float(root_le[1]), float(root_le[2])]
    rte = [float(root_te[0]), float(root_te[1]), float(root_te[2])]
    tle = [float(tip_le[0]), float(tip_le[1]), float(tip_le[2])]
    tte = [float(tip_te[0]), float(tip_te[1]), float(tip_te[2])]

    top = [
        [rle[0], rle[1], rle[2] + ht],
        [rte[0], rte[1], rte[2] + ht],
        [tte[0], tte[1], tte[2] + ht],
        [tle[0], tle[1], tle[2] + ht],
    ]
    bot = [
        [rle[0], rle[1], rle[2] - ht],
        [rte[0], rte[1], rte[2] - ht],
        [tte[0], tte[1], tte[2] - ht],
        [tle[0], tle[1], tle[2] - ht],
    ]

    verts = [*top, *bot]
    tris: list[list[int]] = []

    tris.extend([[0, 1, 2], [0, 2, 3]])
    tris.extend([[6, 5, 4], [7, 6, 4]])

    tris.extend([[0, 4, 5], [0, 5, 1]])
    tris.extend([[1, 5, 6], [1, 6, 2]])
    tris.extend([[2, 6, 7], [2, 7, 3]])
    tris.extend([[3, 7, 4], [3, 4, 0]])

    return verts, tris


def build_wing_mesh(
    *,
    s_ref_m2: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord_deg: float,
    t_c: float,
    x_offset_m: float,
    z_offset_m: float,
) -> list[MeshPart]:
    s = float(s_ref_m2)
    ar = float(aspect_ratio)
    taper = float(taper_ratio)
    if s <= 0.0 or ar <= 0.0:
        raise ValueError("Invalid wing reference area or aspect ratio.")
    if not (0.05 <= taper <= 1.0):
        raise ValueError("taper_ratio must be in [0.05, 1.0].")
    if t_c <= 0.0:
        raise ValueError("t_c must be positive.")

    b = (ar * s) ** 0.5
    half_span = 0.5 * b
    c_root = 2.0 * s / (b * (1.0 + taper))
    c_tip = taper * c_root

    sweep_rad = float(__import__("math").radians(float(sweep_quarter_chord_deg)))
    x_qc_tip = float(x_offset_m) + tan(sweep_rad) * half_span
    x_le_root = float(x_offset_m)
    x_le_tip = x_qc_tip - 0.25 * c_tip
    x_te_root = x_le_root + c_root
    x_te_tip = x_le_tip + c_tip

    ht = 0.5 * float(t_c) * c_root * 0.12

    parts: list[MeshPart] = []
    for sign, name in [(+1.0, "wing_R"), (-1.0, "wing_L")]:
        y0 = 0.0
        y1 = sign * half_span
        verts, tris = build_extruded_trapezoid(
            root_le=[x_le_root, y0, float(z_offset_m)],
            root_te=[x_te_root, y0, float(z_offset_m)],
            tip_le=[x_le_tip, y1, float(z_offset_m)],
            tip_te=[x_te_tip, y1, float(z_offset_m)],
            half_thickness_m=ht,
        )
        _append_part(parts, name=name, color="#2c7fb8", verts=verts, tris=tris)
    return parts


def build_tail_mesh(
    *,
    wing_s_ref_m2: float,
    wing_aspect_ratio: float,
    wing_taper_ratio: float,
    sweep_quarter_chord_deg: float,
    t_c: float,
    tail_area_ratio_to_wing: float,
    fuselage_length_m: float,
    fuselage_diameter_m: float,
) -> list[MeshPart]:
    s_tail = float(wing_s_ref_m2) * max(0.0, float(tail_area_ratio_to_wing))
    ar = float(wing_aspect_ratio)
    if s_tail <= 0.0:
        return []
    x_offset = 0.55 * float(fuselage_length_m)
    z_offset = 0.35 * float(fuselage_diameter_m)
    return build_wing_mesh(
        s_ref_m2=s_tail,
        aspect_ratio=ar,
        taper_ratio=float(wing_taper_ratio),
        sweep_quarter_chord_deg=float(sweep_quarter_chord_deg),
        t_c=float(t_c),
        x_offset_m=x_offset,
        z_offset_m=z_offset,
    )


def mesh_to_obj(parts: list[MeshPart]) -> str:
    lines: list[str] = []
    v_offset = 1
    for p in parts:
        lines.append(f"o {p.name}")
        verts = p.vertices
        for i in range(0, len(verts), 3):
            lines.append(f"v {verts[i]:.6f} {verts[i + 1]:.6f} {verts[i + 2]:.6f}")
        idx = p.indices
        for i in range(0, len(idx), 3):
            a = v_offset + idx[i]
            b = v_offset + idx[i + 1]
            c = v_offset + idx[i + 2]
            lines.append(f"f {a} {b} {c}")
        v_offset += len(verts) // 3
    return "\n".join(lines) + "\n"


def parse_obj_to_parts(path: str) -> list[MeshPart]:
    parts: list[MeshPart] = []
    if not isinstance(path, str) or not path:
        return parts
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception:
        return parts

    global_verts: list[float] = []
    objects: list[tuple[str, list[int]]] = []
    current_name = "object"
    current_faces: list[int] = []

    def finalize_object():
        nonlocal current_name, current_faces
        if current_faces:
            objects.append((current_name, current_faces))
        current_faces = []

    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts_str = ln.split()
        if not parts_str:
            continue

        k = parts_str[0].lower()
        if k == "v":
            try:
                x, y, z = float(parts_str[1]), float(parts_str[2]), float(parts_str[3])
                global_verts.extend([x, y, z])
            except Exception:
                pass
        elif k == "o" or k == "g":
            finalize_object()
            current_name = " ".join(parts_str[1:]) if len(parts_str) > 1 else "object"
        elif k == "f":
            try:
                poly_verts = []
                for v_str in parts_str[1:]:
                    v_idx_raw = int(v_str.split("/")[0])
                    if v_idx_raw > 0:
                        v_idx = v_idx_raw - 1
                    else:
                        v_idx = (len(global_verts) // 3) + v_idx_raw
                    poly_verts.append(v_idx)

                if len(poly_verts) >= 3:
                    for i in range(1, len(poly_verts) - 1):
                        current_faces.extend([poly_verts[0], poly_verts[i], poly_verts[i + 1]])
            except Exception:
                pass

    finalize_object()

    for name, faces in objects:
        if not faces:
            continue

        used_indices = sorted(list(set(faces)))
        if not used_indices:
            continue

        idx_map = {global_idx: local_idx for local_idx, global_idx in enumerate(used_indices)}

        local_verts = []
        for global_idx in used_indices:
            base = global_idx * 3
            if base + 2 < len(global_verts):
                local_verts.extend(global_verts[base : base + 3])
            else:
                local_verts.extend([0.0, 0.0, 0.0])

        local_indices = [idx_map[idx] for idx in faces]
        parts.append(MeshPart(name=name, color="#c7d2fe", vertices=local_verts, indices=local_indices))

    return parts


def render_geometry_viewer_html(
    *,
    parts: list[MeshPart],
    title: str = "Geometry Viewer",
    layout: dict | None = None,
    resource_config: dict | None = None,
) -> str:
    payload = [{"name": p.name, "color": p.color, "vertices": p.vertices, "indices": p.indices} for p in parts]
    mesh_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    layout_json = json.dumps(
        layout or {"views": ["top", "side", "front", "iso"], "grid": {"rows": 2, "cols": 2}}, ensure_ascii=False
    )
    rc = (
        resource_config
        if isinstance(resource_config, dict)
        else {"prefer_local": True, "local_base_url": "assets", "cdn_base_url": "https://unpkg.com/three@0.147.0"}
    )
    loader_script = _three_js_loader_script(rc, include_orbit=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <script>
    window.onerror = function(msg, url, line, col, error) {{
        var div = document.createElement("div");
        div.style.position = "absolute";
        div.style.top = "10px";
        div.style.left = "10px";
        div.style.backgroundColor = "rgba(255, 0, 0, 0.9)";
        div.style.color = "white";
        div.style.padding = "10px";
        div.style.zIndex = "10000";
        div.style.maxWidth = "90%";
        div.style.wordWrap = "break-word";
        div.style.fontFamily = "monospace";
        div.innerHTML = "<strong>JS Error:</strong> " + msg + "<br>URL: " + url + "<br>Line: " + line;
        if(document.body) document.body.appendChild(div);
        else window.addEventListener('DOMContentLoaded', () => document.body.appendChild(div));
        return false;
    }};
  </script>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{title}</title>
  <style>
    html,body{{height:100%;margin:0;}}
    body{{background:linear-gradient(180deg,#7cc6ff 0%,#cbe9ff 45%,#f6fbff 100%);}}
    #views{{position:fixed;inset:0;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:1px;background:rgba(255,255,255,0.2);}}
    .view{{position:relative;background:rgba(255,255,255,0.08);overflow:hidden;}}
    .label{{position:absolute;left:10px;top:10px;color:#eaf4ff;font:12px/1.2 system-ui,Segoe UI,Roboto,Helvetica,Arial;background:rgba(10,24,40,0.55);padding:6px 10px;border-radius:10px;border:1px solid rgba(255,255,255,0.2);z-index:2;backdrop-filter:blur(6px);}}
    canvas{{display:block;width:100%;height:100%;outline:none;}}
    #hud{{position:fixed;left:12px;top:12px;color:#eaf4ff;font:12px/1.4 system-ui,Segoe UI,Roboto,Helvetica,Arial;max-width:520px;}}
    #hud .box{{background:rgba(7,20,38,0.55);padding:10px 12px;border:1px solid rgba(255,255,255,0.18);border-radius:12px;backdrop-filter:blur(10px);}}
    #hud code{{background:rgba(255,255,255,0.18);padding:2px 6px;border-radius:6px;}}
    #status{{margin-top:6px;opacity:0.9;}}
    #log-console{{margin-top:10px;max-height:200px;overflow-y:auto;font-family:monospace;font-size:10px;background:rgba(0,0,0,0.5);padding:4px;border-radius:4px;display:none;pointer-events:auto;user-select:text;}}
    #log-console div{{border-bottom:1px solid rgba(255,255,255,0.1);padding:1px 0;}}
  </style>
</head>
<body>
  <div id="views">
    <div class="view" id="view_top"><div class="label">俯视 Top (X-Y)</div><canvas id="cv_top"></canvas></div>
    <div class="view" id="view_side"><div class="label">侧视 Side (X-Z)</div><canvas id="cv_side"></canvas></div>
    <div class="view" id="view_front"><div class="label">正视 Front (Y-Z)</div><canvas id="cv_front"></canvas></div>
    <div class="view" id="view_iso"><div class="label">轴测 Iso (3D)</div><canvas id="cv_iso"></canvas></div>
  </div>
  <div id="hud"><div class="box">
    <div><b>{title}</b></div>
    <div>操作：三视图<code>拖动</code>平移/缩放；轴测<code>左键</code>旋转、<code>右键</code>平移、<code>滚轮</code>缩放</div>
    <div id="info"></div>
    <div id="status">加载中…</div>
    <div id="log-console"></div>
  </div></div>
  <noscript>
    <div style="position:fixed;inset:12px;color:#fff;background:#000;padding:12px;border-radius:10px;max-width:560px;">
      需要启用 JavaScript 才能显示三维预览。
    </div>
  </noscript>
  {loader_script}
  <script>
    (function(){{
        var logEl = document.getElementById('log-console');
        var oldLog = console.log;
        var oldWarn = console.warn;
        var oldError = console.error;
        function appendLog(msg, color) {{
            if(!logEl) logEl = document.getElementById('log-console');
            if(logEl) {{
                logEl.style.display = 'block';
                var d = document.createElement('div');
                d.textContent = "> " + String(msg);
                d.style.color = color || '#ccc';
                logEl.appendChild(d);
                logEl.scrollTop = logEl.scrollHeight;
            }}
        }}
        window.log = function(msg) {{ appendLog(msg, '#fff'); }};
        console.log = function(msg) {{ oldLog.apply(console, arguments); appendLog(msg, '#fff'); }};
        console.warn = function(msg) {{ oldWarn.apply(console, arguments); appendLog(msg, '#fc0'); }};
        console.error = function(msg) {{ oldError.apply(console, arguments); appendLog(msg, '#f44'); }};
    }})();

    const parts = {mesh_json};
    const layout = {layout_json};
    const statusEl = document.getElementById('status');
    function setStatus(s) {{
      if (statusEl) statusEl.textContent = String(s || '');
    }}

    function applyLayout() {{
      const viewsEl = document.getElementById('views');
      const grid = (layout && layout.grid) ? layout.grid : {{}};
      const rows = Math.max(1, Number(grid.rows || 2));
      const cols = Math.max(1, Number(grid.cols || 2));
      viewsEl.style.gridTemplateColumns = `repeat(${{cols}}, 1fr)`;
      viewsEl.style.gridTemplateRows = `repeat(${{rows}}, 1fr)`;

      const viewEls = {{
        top: document.getElementById('view_top'),
        side: document.getElementById('view_side'),
        front: document.getElementById('view_front'),
        iso: document.getElementById('view_iso')
      }};
      const requested = (layout && Array.isArray(layout.views)) ? layout.views.map(v => String(v).toLowerCase()) : ['top','side','front','iso'];
      const allow = new Set(requested);
      for (const k of Object.keys(viewEls)) {{
        const el = viewEls[k];
        if (!el) continue;
        el.style.display = allow.has(k) ? 'block' : 'none';
      }}
    }}
    applyLayout();

    function computeBounds() {{
      let minX=Infinity,minY=Infinity,minZ=Infinity,maxX=-Infinity,maxY=-Infinity,maxZ=-Infinity;
      for (const p of parts) {{
        const v = p.vertices || [];
        for (let i=0;i<v.length;i+=3) {{
          const x=v[i], y=v[i+1], z=v[i+2];
          if (x<minX) minX=x; if (x>maxX) maxX=x;
          if (y<minY) minY=y; if (y>maxY) maxY=y;
          if (z<minZ) minZ=z; if (z>maxZ) maxZ=z;
        }}
      }}
      if (!isFinite(minX)) return null;
      return {{minX,minY,minZ,maxX,maxY,maxZ}};
    }}

    function startThree() {{
      console.log("Starting Three.js initialization...");
      if (!parts || parts.length === 0) console.warn("No parts to render!");
      else console.log("Rendering " + parts.length + " parts.");

      const scene = new THREE.Scene();
      scene.background = null;

      const ambient = new THREE.AmbientLight(0xffffff, 0.6);
      scene.add(ambient);
      const dir = new THREE.DirectionalLight(0xffffff, 0.9);
      dir.position.set(10, -12, 14);
      scene.add(dir);

      const group = new THREE.Group();
      scene.add(group);

      function addPart(p) {{
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(p.vertices), 3));
        geo.setIndex(new THREE.BufferAttribute(new Uint32Array(p.indices), 1));
        geo.computeVertexNormals();
        geo.computeBoundingBox();
        const mat = new THREE.MeshStandardMaterial({{
          color: new THREE.Color(p.color || '#cccccc'),
          metalness: 0.0,
          roughness: 0.85,
          side: THREE.DoubleSide
        }});
        const mesh = new THREE.Mesh(geo, mat);
        mesh.name = p.name;
        group.add(mesh);
        return geo.boundingBox;
      }}

      let bb = null;
      for (const p of parts) {{
        const b = addPart(p);
        if (b) {{
          if (!bb) bb = b.clone();
          else bb.union(b);
        }}
      }}

      let radius = 5.0;
      if (bb) {{
        const center = new THREE.Vector3();
        bb.getCenter(center);
        const size = new THREE.Vector3();
        bb.getSize(size);
        group.position.sub(center);
        radius = Math.max(size.x, size.y, size.z) * 0.65 + 0.5;
        document.getElementById('info').textContent = `包围盒尺寸：${{size.x.toFixed(2)}}×${{size.y.toFixed(2)}}×${{size.z.toFixed(2)}} m`;
      }}

      const canvases = {{
        top: document.getElementById('cv_top'),
        side: document.getElementById('cv_side'),
        front: document.getElementById('cv_front'),
        iso: document.getElementById('cv_iso')
      }};
      const renderers = {{
        top: new THREE.WebGLRenderer({{canvas: canvases.top, antialias:true, alpha:true}}),
        side: new THREE.WebGLRenderer({{canvas: canvases.side, antialias:true, alpha:true}}),
        front: new THREE.WebGLRenderer({{canvas: canvases.front, antialias:true, alpha:true}}),
        iso: new THREE.WebGLRenderer({{canvas: canvases.iso, antialias:true, alpha:true}})
      }};
      for (const k of Object.keys(renderers)) {{
        renderers[k].setPixelRatio(window.devicePixelRatio || 1);
        renderers[k].setClearColor(0x000000, 0);
      }}

      const dist = radius * 3.0;
      const cams = {{
        top: new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 1e6),
        side: new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 1e6),
        front: new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 1e6),
        iso: new THREE.PerspectiveCamera(55, 1, 0.01, 1e6)
      }};

      const center = new THREE.Vector3(0,0,0);
      let zoom = 1.0;

      function updateCameras() {{
        const keys = ['top','side','front','iso'];
        for (const k of keys) {{
          const r = renderers[k];
          const cv = canvases[k];
          const rect = cv.getBoundingClientRect();
          const w = Math.max(1, Math.floor(rect.width));
          const h = Math.max(1, Math.floor(rect.height));
          r.setSize(w, h, false);
          const aspect = w / h;
          if (k === 'iso') {{
            cams.iso.aspect = aspect;
            cams.iso.updateProjectionMatrix();
          }} else {{
            const span = radius * 1.35 / zoom;
            cams[k].left = -span * aspect;
            cams[k].right = span * aspect;
            cams[k].top = span;
            cams[k].bottom = -span;
            cams[k].updateProjectionMatrix();
          }}
        }}

        cams.top.up.set(0, 1, 0);
        cams.top.position.set(center.x, center.y, center.z + dist);
        cams.top.lookAt(center);

        cams.side.up.set(0, 0, 1);
        cams.side.position.set(center.x, center.y - dist, center.z);
        cams.side.lookAt(center);

        cams.front.up.set(0, 0, 1);
        cams.front.position.set(center.x + dist, center.y, center.z);
        cams.front.lookAt(center);
      }}

      const grids = {{
        top: new THREE.GridHelper(40, 40, 0x333333, 0x222222),
        side: new THREE.GridHelper(40, 40, 0x333333, 0x222222),
        front: new THREE.GridHelper(40, 40, 0x333333, 0x222222),
      }};
      grids.top.rotation.x = Math.PI / 2;
      grids.side.rotation.y = Math.PI / 2;
      grids.front.rotation.z = Math.PI / 2;
      scene.add(grids.top);
      scene.add(grids.side);
      scene.add(grids.front);

      const axes = new THREE.AxesHelper(5);
      scene.add(axes);

      function attachControls(canvas) {{
        let dragging = false;
        let lastX = 0;
        let lastY = 0;
        canvas.addEventListener('mousedown', (e)=>{{ dragging=true; lastX=e.clientX; lastY=e.clientY; }});
        window.addEventListener('mouseup', ()=>dragging=false);
        window.addEventListener('mousemove', (e)=>{{
          if (!dragging) return;
          const dx = e.clientX - lastX;
          const dy = e.clientY - lastY;
          lastX = e.clientX;
          lastY = e.clientY;
          const rect = canvas.getBoundingClientRect();
          const w = Math.max(1, rect.width);
          const h = Math.max(1, rect.height);
          const span = radius * 1.35 / zoom;
          const sx = (2 * span * (w/h)) / w;
          const sy = (2 * span) / h;
          center.x -= dx * sx;
          center.y += dy * sy;
          updateCameras();
        }});
        canvas.addEventListener('wheel', (e)=>{{
          e.preventDefault();
          zoom *= (e.deltaY > 0 ? 1.08 : 0.92);
          zoom = Math.max(0.2, Math.min(10.0, zoom));
          updateCameras();
        }}, {{passive:false}});
      }}
      attachControls(canvases.top);
      attachControls(canvases.side);
      attachControls(canvases.front);

      let isoYaw = -1.0;
      let isoPitch = 0.55;
      let isoDist = dist * 1.1;
      let isoPan = new THREE.Vector3(0, 0, 0);
      function updateIsoCamera() {{
        const x = isoDist * Math.cos(isoPitch) * Math.cos(isoYaw);
        const y = isoDist * Math.cos(isoPitch) * Math.sin(isoYaw);
        const z = isoDist * Math.sin(isoPitch);
        cams.iso.position.set(center.x + isoPan.x + x, center.y + isoPan.y + y, center.z + isoPan.z + z);
        cams.iso.up.set(0, 0, 1);
        cams.iso.lookAt(new THREE.Vector3(center.x + isoPan.x, center.y + isoPan.y, center.z + isoPan.z));
      }}
      updateIsoCamera();
      (function attachIso(canvas) {{
        let dragging = false;
        let lastX = 0;
        let lastY = 0;
        canvas.addEventListener('mousedown', (e)=>{{ dragging=true; lastX=e.clientX; lastY=e.clientY; }});
        window.addEventListener('mouseup', ()=>dragging=false);
        window.addEventListener('mousemove', (e)=>{{
          if (!dragging) return;
          const dx = e.clientX - lastX;
          const dy = e.clientY - lastY;
          lastX = e.clientX;
          lastY = e.clientY;
          if (e.buttons === 2) {{
            const scale = (isoDist / 800.0) * radius;
            isoPan.add(new THREE.Vector3(-dx * scale * 0.01, dy * scale * 0.01, 0));
          }} else {{
            isoYaw -= dx * 0.006;
            isoPitch = Math.max(-1.35, Math.min(1.35, isoPitch + dy * 0.006));
          }}
          updateIsoCamera();
        }});
        canvas.addEventListener('contextmenu', (e)=>e.preventDefault());
        canvas.addEventListener('wheel', (e)=>{{
          e.preventDefault();
          isoDist *= (e.deltaY > 0 ? 1.08 : 0.92);
          isoDist = Math.max(radius * 0.6, Math.min(radius * 80.0, isoDist));
          updateIsoCamera();
        }}, {{passive:false}});
      }})(canvases.iso);

      window.addEventListener('resize', updateCameras);
      updateCameras();

      setStatus("Three.js 四视图渲染");
      function animate() {{
        requestAnimationFrame(animate);
        renderers.top.render(scene, cams.top);
        renderers.side.render(scene, cams.side);
        renderers.front.render(scene, cams.front);
        renderers.iso.render(scene, cams.iso);
      }}
      animate();
    }}

    function startFallback(reason) {{
      const bounds = computeBounds();
      if (!bounds) {{
        setStatus("无可渲染数据");
        return;
      }}
      setStatus("降级渲染（Three.js 不可用）：" + String(reason || ''));
      const cx = 0.5*(bounds.minX + bounds.maxX);
      const cy = 0.5*(bounds.minY + bounds.maxY);
      const cz = 0.5*(bounds.minZ + bounds.maxZ);
      const sx = bounds.maxX - bounds.minX;
      const sy = bounds.maxY - bounds.minY;
      const sz = bounds.maxZ - bounds.minZ;
      const baseTop = Math.max(sx, sy) || 1.0;
      const baseSide = Math.max(sx, sz) || 1.0;
      const baseFront = Math.max(sy, sz) || 1.0;

      const canvases = {{
        top: document.getElementById('cv_top'),
        side: document.getElementById('cv_side'),
        front: document.getElementById('cv_front'),
        iso: document.getElementById('cv_iso')
      }};
      const ctx = {{
        top: canvases.top.getContext('2d'),
        side: canvases.side.getContext('2d'),
        front: canvases.front.getContext('2d'),
        iso: canvases.iso.getContext('2d')
      }};

      let zoom = 1.0;
      let panX = 0.0;
      let panY = 0.0;

      function resize() {{
        for (const k of Object.keys(canvases)) {{
          const cv = canvases[k];
          const r = cv.getBoundingClientRect();
          const dpr = window.devicePixelRatio || 1;
          cv.width = Math.max(1, Math.floor(r.width * dpr));
          cv.height = Math.max(1, Math.floor(r.height * dpr));
        }}
      }}
      window.addEventListener('resize', resize);
      resize();

      function attachControls(canvas) {{
        let dragging = false;
        let lastX = 0;
        let lastY = 0;
        canvas.addEventListener('mousedown', (e)=>{{ dragging=true; lastX=e.clientX; lastY=e.clientY; }});
        window.addEventListener('mouseup', ()=>dragging=false);
        window.addEventListener('mousemove', (e)=>{{
          if (!dragging) return;
          const dx = e.clientX - lastX;
          const dy = e.clientY - lastY;
          lastX = e.clientX;
          lastY = e.clientY;
          panX += dx;
          panY += dy;
        }});
        canvas.addEventListener('wheel', (e)=>{{
          e.preventDefault();
          zoom *= (e.deltaY > 0 ? 1.08 : 0.92);
          zoom = Math.max(0.2, Math.min(10.0, zoom));
        }}, {{passive:false}});
      }}
      attachControls(canvases.top);
      attachControls(canvases.side);
      attachControls(canvases.front);
      attachControls(canvases.iso);

      let isoYaw = -1.0;
      let isoPitch = 0.6;
      (function attachIso(canvas){{
        let dragging=false; let lastX=0; let lastY=0;
        canvas.addEventListener('mousedown',(e)=>{{dragging=true;lastX=e.clientX;lastY=e.clientY;}});
        window.addEventListener('mouseup',()=>dragging=false);
        window.addEventListener('mousemove',(e)=>{{
          if(!dragging) return;
          const dx=e.clientX-lastX, dy=e.clientY-lastY;
          lastX=e.clientX; lastY=e.clientY;
          isoYaw -= dx*0.006;
          isoPitch = Math.max(-1.35, Math.min(1.35, isoPitch + dy*0.006));
        }});
      }})(canvases.iso);

      function drawOne(kind) {{
        const c = canvases[kind];
        const g = ctx[kind];
        if (!g) return;
        g.save();
        g.setTransform(1,0,0,1,0,0);
        g.clearRect(0,0,c.width,c.height);
        g.fillStyle = "#111";
        g.fillRect(0,0,c.width,c.height);
        g.strokeStyle = "rgba(220,220,220,0.55)";
        g.lineWidth = 1;

        const base = kind==='top' ? baseTop : (kind==='side' ? baseSide : (kind==='front' ? baseFront : Math.max(baseTop, baseSide, baseFront)));
        const scale = (Math.min(c.width, c.height) / base) * zoom * 0.86;
        const ox = c.width * 0.5 + panX * (window.devicePixelRatio || 1);
        const oy = c.height * 0.5 + panY * (window.devicePixelRatio || 1);

        function proj(x,y,z) {{
          if (kind==='top') return [ (x - cx)*scale + ox, -(y - cy)*scale + oy ];
          if (kind==='side') return [ (x - cx)*scale + ox, -(z - cz)*scale + oy ];
          if (kind==='front') return [ (y - cy)*scale + ox, -(z - cz)*scale + oy ];
          const dx = x - cx;
          const dy = y - cy;
          const dz = z - cz;
          const cyaw = Math.cos(isoYaw), syaw = Math.sin(isoYaw);
          const cp = Math.cos(isoPitch), sp = Math.sin(isoPitch);
          const x1 = cyaw*dx - syaw*dy;
          const y1 = syaw*dx + cyaw*dy;
          const z1 = dz;
          const y2 = cp*y1 - sp*z1;
          return [ x1*scale + ox, -y2*scale + oy ];
        }}

        for (const p of parts) {{
          const v = p.vertices || [];
          const idx = p.indices || [];
          const pv = new Array(v.length/3);
          for (let i=0;i<v.length;i+=3) {{
            pv[i/3] = proj(v[i], v[i+1], v[i+2]);
          }}
          g.beginPath();
          for (let i=0;i<idx.length;i+=3) {{
            const a = pv[idx[i]];
            const b = pv[idx[i+1]];
            const c2 = pv[idx[i+2]];
            if (!a || !b || !c2) continue;
            g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]);
            g.moveTo(b[0], b[1]); g.lineTo(c2[0], c2[1]);
            g.moveTo(c2[0], c2[1]); g.lineTo(a[0], a[1]);
          }}
          g.stroke();
        }}
        g.restore();
      }}

      function draw() {{
        requestAnimationFrame(draw);
        drawOne('top');
        drawOne('side');
        drawOne('front');
        drawOne('iso');
      }}
      draw();
    }}

    window.addEventListener('load', () => {{
      console.log("Page loaded. Checking dependencies...");
      try {{
        if (window.THREE && window.THREE.WebGLRenderer) {{
          console.log("Three.js found. Version: " + THREE.REVISION);
          startThree();
        }} else {{
          console.error("Three.js missing!");
          startFallback("THREE 未加载（可能网络/CDN被拦截，或在受限环境中打开）");
        }}
      }} catch (e) {{
        console.error("Exception in load: " + e);
        startFallback(e && e.message ? e.message : String(e));
      }}
    }});
  </script>
</body>
</html>
"""
