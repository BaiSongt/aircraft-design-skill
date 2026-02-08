import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ChartData:
    title: str
    x_label: str
    y_label: str
    series: List[Dict[str, Any]]  # [{"name": "Series1", "data": [{"x": 1, "y": 2}, ...]}]
    chart_type: str = "line"  # line, pie, scatter


class InteractivePlotter:
    def __init__(self, output_dir: str = "output/charts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_html_report(self, charts: List[ChartData], filename: str = "interactive_charts.html"):
        html_content = self._get_html_template(charts)
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return path

    def _get_html_template(self, charts: List[ChartData]) -> str:
        # Prepare data for JS
        charts_config: List[Dict[str, Any]] = []
        for i, chart in enumerate(charts):
            config: Dict[str, Any] = {
                "type": chart.chart_type,
                "data": {
                    "labels": [p["x"] for p in chart.series[0]["data"]]
                    if chart.chart_type == "line"
                    else [s["name"] for s in chart.series],
                    "datasets": [],
                },
                "options": {
                    "responsive": True,
                    "plugins": {"title": {"display": True, "text": chart.title}},
                    "scales": {
                        "x": {"title": {"display": True, "text": chart.x_label}},
                        "y": {"title": {"display": True, "text": chart.y_label}},
                    },
                },
            }

            if chart.chart_type == "line":
                for s in chart.series:
                    config["data"]["datasets"].append(
                        {
                            "label": s["name"],
                            "data": [p["y"] for p in s["data"]],
                            "borderColor": s.get("color", self._random_color()),
                            "fill": False,
                        }
                    )
            elif chart.chart_type == "pie":
                config["data"] = {
                    "labels": [s["name"] for s in chart.series],
                    "datasets": [
                        {
                            "data": [s["value"] for s in chart.series],
                            "backgroundColor": [self._random_color() for _ in chart.series],
                        }
                    ],
                }
                # Remove scales for pie
                del config["options"]["scales"]

            charts_config.append({"id": f"chart_{i}", "config": config})

        # HTML Template
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Aircraft Design Interactive Charts</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: sans-serif; padding: 20px; }
        .chart-container { width: 45%; display: inline-block; margin: 10px; border: 1px solid #ddd; padding: 10px; }
        h1 { text-align: center; }
    </style>
</head>
<body>
    <h1>Aircraft Design Analysis Results</h1>
"""
        for c in charts_config:
            html += f'<div class="chart-container"><canvas id="{c["id"]}"></canvas></div>\n'

        html += """
    <script>
"""
        for c in charts_config:
            html += f'new Chart(document.getElementById("{c["id"]}"), {json.dumps(c["config"])});\n'

        html += """
    </script>
</body>
</html>
"""
        return html

    def _random_color(self) -> str:
        import random

        return f"hsl({random.randint(0, 360)}, 70%, 50%)"


# Helper for standard plots
def plot_payload_range(payload_kg: float, range_km: float) -> ChartData:
    # Simplified payload range diagram
    data = [{"x": 0, "y": payload_kg}, {"x": range_km * 0.5, "y": payload_kg}, {"x": range_km, "y": 0}]
    return ChartData(
        title="Payload-Range Diagram",
        x_label="Range (km)",
        y_label="Payload (kg)",
        series=[{"name": "Design Point", "data": data}],
        chart_type="line",
    )


def plot_weight_breakdown(breakdown: Dict[str, float]) -> ChartData:
    series = [{"name": k, "value": v} for k, v in breakdown.items()]
    return ChartData(title="Weight Breakdown", x_label="", y_label="Weight (kg)", series=series, chart_type="pie")
