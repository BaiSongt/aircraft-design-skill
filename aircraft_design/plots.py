from __future__ import annotations

from math import isfinite


def render_constraints_ws_tw_svg(
    *,
    plot_data: dict,
    design_point: dict | None = None,
    width: int = 880,
    height: int = 420,
) -> str:
    if not plot_data or plot_data.get("schema") != "ws-tw-v1":
        return ""

    ws_values = [float(x) for x in plot_data.get("wing_loading_pa_values", []) if isinstance(x, (int, float))]
    tw_curves = [c for c in plot_data.get("curves", []) if c.get("type") == "tw_vs_ws"]
    ws_max_curves = [c for c in plot_data.get("curves", []) if c.get("type") == "ws_max"]
    ws_limit = plot_data.get("ws_limit_pa", None)

    dp = plot_data.get("design_point", {}) or {}
    if design_point:
        dp = {**design_point, **dp}
    dp_ws = float(dp.get("wing_loading_pa", 0.0) or 0.0)
    dp_tw = float(dp.get("thrust_to_weight", dp.get("thrust_to_weight_available", 0.0)) or 0.0)

    ws = [x for x in ws_values if isfinite(x) and x > 0.0]
    if len(ws) < 2 or not tw_curves:
        return ""

    tw_by_name: dict[str, list[float]] = {}
    for c in tw_curves:
        name = str(c.get("name", "curve"))
        x = [float(v) for v in c.get("x", []) if isinstance(v, (int, float))]
        y = [float(v) for v in c.get("y", []) if isinstance(v, (int, float))]
        if len(x) != len(y) or not x:
            continue
        y_map = {float(xi): float(yi) for xi, yi in zip(x, y)}
        ys = [y_map.get(v, float("nan")) for v in ws]
        if any(isfinite(v) for v in ys):
            tw_by_name[name] = ys

    if not tw_by_name:
        return ""

    env = plot_data.get("envelope", {}) or {}
    x_env = [float(v) for v in env.get("x", []) if isinstance(v, (int, float))]
    y_env = [float(v) for v in env.get("y", []) if isinstance(v, (int, float))]
    if len(x_env) == len(ws) and all(abs(a - b) < 1e-6 for a, b in zip(x_env, ws)):
        y_env = [v if isfinite(v) else float("nan") for v in y_env]
    else:
        y_env = []
        for i in range(len(ws)):
            vals = [tw_by_name[n][i] for n in tw_by_name.keys() if isfinite(tw_by_name[n][i])]
            y_env.append(max(vals) if vals else float("nan"))

    y_vals = [v for v in y_env if isfinite(v)]
    if isfinite(dp_tw):
        y_vals.append(dp_tw)
    y_min = min(y_vals) if y_vals else 0.0
    y_max = max(y_vals) if y_vals else 1.0
    y_min = max(0.0, y_min * 0.8)
    y_max = max(y_max * 1.2, y_min + 0.05)

    x_min = min(ws)
    x_max = max(ws)

    margin_l = 70
    margin_r = 20
    margin_t = 20
    margin_b = 50
    px_w = width - margin_l - margin_r
    px_h = height - margin_t - margin_b

    def x_px(xv: float) -> float:
        return margin_l + (xv - x_min) / max(1e-9, (x_max - x_min)) * px_w

    def y_px(yv: float) -> float:
        return margin_t + (y_max - yv) / max(1e-9, (y_max - y_min)) * px_h

    def polyline_points(xs: list[float], ys: list[float]) -> str:
        pts = []
        for xv, yv in zip(xs, ys):
            if not (isfinite(xv) and isfinite(yv)):
                continue
            pts.append(f"{x_px(xv):.2f},{y_px(yv):.2f}")
        return " ".join(pts)

    colors = {
        "cruise": "#1f77b4",
        "climb_gradient": "#2ca02c",
        "takeoff_distance": "#ff7f0e",
        "takeoff_climb_gradient": "#d62728",
    }

    svg_lines: list[str] = []
    svg_lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    )
    svg_lines.append('<rect x="0" y="0" width="100%" height="100%" fill="white"/>')
    svg_lines.append(
        f'<line x1="{margin_l}" y1="{margin_t + px_h}" x2="{margin_l + px_w}" y2="{margin_t + px_h}" stroke="#333" stroke-width="1"/>'
    )
    svg_lines.append(
        f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t + px_h}" stroke="#333" stroke-width="1"/>'
    )

    if any(isfinite(v) for v in y_env):
        ws_shade = ws
        y_shade = y_env
        if ws_limit is not None and isfinite(float(ws_limit)):
            i_last = max([i for i, xv in enumerate(ws) if xv <= float(ws_limit)], default=None)
            if i_last is not None and i_last >= 1:
                ws_shade = ws[: i_last + 1]
                y_shade = y_env[: i_last + 1]
        pts_env = polyline_points(ws_shade, y_shade)
        pts_poly = f"{x_px(ws_shade[0]):.2f},{y_px(y_max):.2f} {pts_env} {x_px(ws_shade[-1]):.2f},{y_px(y_max):.2f}"
        svg_lines.append(f'<polygon points="{pts_poly}" fill="#f0f0f0" stroke="none"/>')

    for c in ws_max_curves:
        ws_m = c.get("ws_max", None)
        if isinstance(ws_m, (int, float)) and isfinite(float(ws_m)):
            xv = float(ws_m)
            if xv < x_min or xv > x_max:
                continue
            svg_lines.append(
                f'<line x1="{x_px(xv):.2f}" y1="{margin_t}" x2="{x_px(xv):.2f}" y2="{margin_t + px_h}" stroke="#888" stroke-dasharray="4 4" stroke-width="1"/>'
            )

    for name, ys in tw_by_name.items():
        col = colors.get(name, "#444")
        pts = polyline_points(ws, ys)
        if pts:
            svg_lines.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"/>')

    if isfinite(dp_ws) and isfinite(dp_tw) and x_min <= dp_ws <= x_max and y_min <= dp_tw <= y_max:
        svg_lines.append(f'<circle cx="{x_px(dp_ws):.2f}" cy="{y_px(dp_tw):.2f}" r="5" fill="#111"/>')

    svg_lines.append(
        f'<text x="{margin_l + px_w / 2:.2f}" y="{height - 12}" font-size="12" text-anchor="middle" fill="#333">W/S (Pa)</text>'
    )
    svg_lines.append(
        f'<text x="16" y="{margin_t + px_h / 2:.2f}" font-size="12" text-anchor="middle" fill="#333" transform="rotate(-90 16 {margin_t + px_h / 2:.2f})">T/W</text>'
    )

    legend_x = margin_l + 10
    legend_y = margin_t + 14
    for i, name in enumerate(tw_by_name.keys()):
        col = colors.get(name, "#444")
        y0 = legend_y + i * 16
        svg_lines.append(
            f'<line x1="{legend_x}" y1="{y0}" x2="{legend_x + 18}" y2="{y0}" stroke="{col}" stroke-width="3"/>'
        )
        svg_lines.append(f'<text x="{legend_x + 24}" y="{y0 + 4}" font-size="12" fill="#333">{name}</text>')
    svg_lines.append(f'<circle cx="{legend_x + 6}" cy="{legend_y + len(tw_by_name) * 16 + 10}" r="5" fill="#111"/>')
    svg_lines.append(
        f'<text x="{legend_x + 24}" y="{legend_y + len(tw_by_name) * 16 + 14}" font-size="12" fill="#333">design_point</text>'
    )

    svg_lines.append("</svg>")
    return "\n".join(svg_lines)
