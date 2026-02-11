from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import math
from typing import Any

from .atmosphere import isa_tropopause
from .units import CONST


class UnifiedReportGenerator:
    def __init__(self, project_name: str = "Aircraft Design Project", timestamp: str | None = None):
        self.project_name = project_name
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_report(self, output_data: dict, output_dir: str | Path) -> tuple[str, dict]:
        output_dir = Path(output_dir)
        inputs = output_data.get("inputs", {}) if isinstance(output_data.get("inputs", {}), dict) else {}
        requirements = inputs.get("requirements", {}) if isinstance(inputs.get("requirements", {}), dict) else {}
        initial_guess = inputs.get("initial_guess", {}) if isinstance(inputs.get("initial_guess", {}), dict) else {}
        outputs = output_data.get("outputs", {}) if isinstance(output_data.get("outputs", {}), dict) else {}
        geometry = outputs.get("geometry", {}) if isinstance(outputs.get("geometry", {}), dict) else {}
        performance = outputs.get("performance", {}) if isinstance(outputs.get("performance", {}), dict) else {}
        weight_breakdown = outputs.get("weight_breakdown", {}) if isinstance(outputs.get("weight_breakdown", {}), dict) else {}

        mtow_kg = self._num(outputs.get("mtow_kg"))
        wing_area_m2 = self._num(outputs.get("wing_area_m2"))
        thrust_sl_n = self._num(outputs.get("thrust_sl_n"))

        w_s = self._safe_div(mtow_kg * CONST.g0_m_s2, wing_area_m2)
        t_w = self._safe_div(thrust_sl_n, mtow_kg * CONST.g0_m_s2)

        sea_level = isa_tropopause(0.0)
        cl_max = float(geometry.get("cl_max", 1.6)) if isinstance(geometry.get("cl_max", 1.6), (int, float)) else 1.6
        v_stall_m_s = self._safe_sqrt(self._safe_div(2.0 * mtow_kg * CONST.g0_m_s2, sea_level.rho_kg_m3 * wing_area_m2 * cl_max))

        figures = self._collect_figures(output_dir)
        advanced_path, advanced_data = self._load_latest_advanced_results(output_dir)

        report_json = self._build_report_json(
            output_data=output_data,
            requirements=requirements,
            initial_guess=initial_guess,
            outputs=outputs,
            geometry=geometry,
            performance=performance,
            weight_breakdown=weight_breakdown,
            metrics={
                "wing_loading_pa": w_s,
                "thrust_to_weight": t_w,
                "v_stall_m_s": v_stall_m_s,
            },
            figures=figures,
            advanced_path=advanced_path,
            advanced_data=advanced_data,
        )

        report_md = self._build_report_markdown(
            requirements=requirements,
            initial_guess=initial_guess,
            outputs=outputs,
            geometry=geometry,
            performance=performance,
            weight_breakdown=weight_breakdown,
            metrics={
                "wing_loading_pa": w_s,
                "thrust_to_weight": t_w,
                "v_stall_m_s": v_stall_m_s,
            },
            figures=figures,
            advanced_path=advanced_path,
            advanced_data=advanced_data,
        )

        return report_md, report_json

    def _build_report_markdown(
        self,
        *,
        requirements: dict,
        initial_guess: dict,
        outputs: dict,
        geometry: dict,
        performance: dict,
        weight_breakdown: dict,
        metrics: dict,
        figures: list[dict],
        advanced_path: str | None,
        advanced_data: dict | None,
    ) -> str:
        sections: list[str] = []
        sections.append(
            "\n".join(
                [
                    "# 统一格式设计报告",
                    "",
                    f"**项目名称**: {self.project_name}",
                    f"**生成日期**: {self.timestamp}",
                    "",
                    "---",
                ]
            )
        )

        sections.append(self._section_requirements_input(requirements, initial_guess))
        sections.append(self._section_requirements_analysis(requirements, metrics, performance))
        sections.append(self._section_stage1_results(outputs, geometry))
        sections.append(self._section_stage1_analysis(metrics, weight_breakdown, figures))
        sections.append(self._section_stage2_results(advanced_path, advanced_data))
        sections.append(self._section_stage2_analysis(advanced_data))
        sections.append(self._section_improvements(outputs, metrics, advanced_data))

        return "\n\n".join(sections)

    def _section_requirements_input(self, requirements: dict, initial_guess: dict) -> str:
        req_rows = self._dict_table_rows(
            [
                ("航程 range_m", requirements.get("range_m"), "m"),
                ("载荷 payload_kg", requirements.get("payload_kg"), "kg"),
                ("巡航马赫 cruise_mach", requirements.get("cruise_mach"), "-"),
                ("巡航高度 cruise_altitude_m", requirements.get("cruise_altitude_m"), "m"),
                ("起飞距离 takeoff_distance_m", requirements.get("takeoff_distance_m"), "m"),
                ("着陆距离 landing_distance_m", requirements.get("landing_distance_m"), "m"),
                ("最大过载 max_load_factor", requirements.get("max_load_factor"), "g"),
                ("持续盘旋过载 sustained_turn_g", requirements.get("sustained_turn_g"), "g"),
                ("实用升限 service_ceiling_m", requirements.get("service_ceiling_m"), "m"),
            ]
        )
        guess_rows = self._dict_table_rows(
            [
                ("推重比 thrust_to_weight", initial_guess.get("thrust_to_weight"), "-"),
                ("翼载 wing_loading_pa", initial_guess.get("wing_loading_pa"), "Pa"),
                ("展弦比 aspect_ratio", initial_guess.get("aspect_ratio"), "-"),
                ("后掠角 sweep_deg", initial_guess.get("sweep_deg"), "deg"),
                ("梯形比 taper_ratio", initial_guess.get("taper_ratio"), "-"),
                ("厚度比 thickness_ratio", initial_guess.get("thickness_ratio"), "-"),
                ("巡航耗油率 sfc_cruise_1_s", initial_guess.get("sfc_cruise_1_s"), "1/s"),
                ("零升阻力系数 cd0", initial_guess.get("cd0"), "-"),
                ("奥斯瓦尔德效率 oswald_e", initial_guess.get("oswald_e"), "-"),
            ]
        )
        return "\n".join(
            [
                "## 1. 输入设计需求",
                "",
                "### 1.1 需求参数",
                "| 参数 | 数值 | 单位 |",
                "|:---|:---:|:---:|",
                *req_rows,
                "",
                "### 1.2 初始猜测参数",
                "| 参数 | 数值 | 单位 |",
                "|:---|:---:|:---:|",
                *guess_rows,
                "",
                "---",
            ]
        )

    def _section_requirements_analysis(self, requirements: dict, metrics: dict, performance: dict) -> str:
        wing_loading_pa = metrics.get("wing_loading_pa")
        thrust_to_weight = metrics.get("thrust_to_weight")
        v_stall_m_s = metrics.get("v_stall_m_s")
        actual_range_m = performance.get("actual_range_m")

        formulas = [
            "$$\\frac{W}{S}=\\frac{W_0 g}{S}$$",
            "$$\\frac{T}{W}=\\frac{T_{SL}}{W_0 g}$$",
            "$$V_{stall}=\\sqrt{\\frac{2W_0 g}{\\rho S C_{L\\max}}}$$",
        ]
        if isinstance(actual_range_m, (int, float)):
            formulas.append("$$R=\\frac{V}{c}\\frac{L}{D}\\ln\\left(\\frac{W_i}{W_f}\\right)$$")

        lines = [
            "## 2. 需求分析",
            "",
            "### 2.1 关键指标计算",
            "| 指标 | 数值 | 单位 |",
            "|:---|:---:|:---:|",
            f"| 翼载 $W/S$ | {self._fmt_num(wing_loading_pa)} | Pa |",
            f"| 推重比 $T/W$ | {self._fmt_num(thrust_to_weight)} | - |",
            f"| 失速速度 $V_{{stall}}$ | {self._fmt_num(v_stall_m_s)} | m/s |",
        ]
        if isinstance(actual_range_m, (int, float)):
            lines.append(f"| 实际航程 | {self._fmt_num(actual_range_m)} | m |")

        lines.extend(
            [
                "",
                "### 2.2 计算公式",
                *formulas,
                "",
                "---",
            ]
        )
        return "\n".join(lines)

    def _section_stage1_results(self, outputs: dict, geometry: dict) -> str:
        rows = self._dict_table_rows(
            [
                ("是否收敛", outputs.get("converged"), "-"),
                ("最大起飞重量 mtow_kg", outputs.get("mtow_kg"), "kg"),
                ("空机重量 empty_weight_kg", outputs.get("empty_weight_kg"), "kg"),
                ("燃油重量 fuel_weight_kg", outputs.get("fuel_weight_kg"), "kg"),
                ("翼面积 wing_area_m2", outputs.get("wing_area_m2"), "m²"),
                ("海平面推力 thrust_sl_n", outputs.get("thrust_sl_n"), "N"),
            ]
        )
        geo_rows = self._dict_table_rows(
            [
                ("翼展 span_m", geometry.get("span_m"), "m"),
                ("展弦比 aspect_ratio", geometry.get("aspect_ratio"), "-"),
                ("后掠角 sweep_deg", geometry.get("sweep_deg"), "deg"),
                ("机身长度 fuselage_length_m", geometry.get("fuselage_length_m"), "m"),
                ("机身直径 fuselage_diameter_m", geometry.get("fuselage_diameter_m"), "m"),
                ("平尾面积 s_ht_m2", geometry.get("s_ht_m2"), "m²"),
                ("垂尾面积 s_vt_m2", geometry.get("s_vt_m2"), "m²"),
            ]
        )
        return "\n".join(
            [
                "## 3. 一阶段设计结果",
                "",
                "### 3.1 总体结果",
                "| 指标 | 数值 | 单位 |",
                "|:---|:---:|:---:|",
                *rows,
                "",
                "### 3.2 几何汇总",
                "| 参数 | 数值 | 单位 |",
                "|:---|:---:|:---:|",
                *geo_rows,
                "",
                "---",
            ]
        )

    def _section_stage1_analysis(self, metrics: dict, weight_breakdown: dict, figures: list[dict]) -> str:
        weight_rows = self._flatten_weight_rows(weight_breakdown)
        figure_lines = []
        for fig in figures:
            figure_lines.append(f"**{fig['title']}**")
            figure_lines.append(f"![]({fig['file']})")
            figure_lines.append("")

        return "\n".join(
            [
                "## 4. 一阶段设计内容分析",
                "",
                "### 4.1 关键计算结果",
                "| 指标 | 数值 | 单位 |",
                "|:---|:---:|:---:|",
                f"| 翼载 $W/S$ | {self._fmt_num(metrics.get('wing_loading_pa'))} | Pa |",
                f"| 推重比 $T/W$ | {self._fmt_num(metrics.get('thrust_to_weight'))} | - |",
                f"| 失速速度 $V_{{stall}}$ | {self._fmt_num(metrics.get('v_stall_m_s'))} | m/s |",
                "",
                "### 4.2 重量分解",
                "| 部件 | 重量 | 单位 |",
                "|:---|:---:|:---:|",
                *weight_rows,
                "",
                "### 4.3 计算公式",
                "$$\\frac{W}{S}=\\frac{W_0 g}{S}$$",
                "$$\\frac{T}{W}=\\frac{T_{SL}}{W_0 g}$$",
                "$$V_{stall}=\\sqrt{\\frac{2W_0 g}{\\rho S C_{L\\max}}}$$",
                "",
                "### 4.4 曲线图",
                *figure_lines if figure_lines else ["未生成可用曲线图。"],
                "---",
            ]
        )

    def _section_stage2_results(self, advanced_path: str | None, advanced_data: dict | None) -> str:
        if not advanced_data:
            return "\n".join(
                [
                    "## 5. 二阶段设计结果",
                    "",
                    "未生成二阶段结果或结果文件不可用。",
                    "",
                    "---",
                ]
            )

        stage_lines = []
        for key in [
            "stage2_aero",
            "stage3_propulsion",
            "stage4_mission",
            "stage5_stability",
            "stage6_structures",
            "stage7_optimization",
        ]:
            data = advanced_data.get(key, None) if isinstance(advanced_data, dict) else None
            if isinstance(data, dict):
                stage_lines.append(f"### {key}")
                stage_lines.append("| 参数 | 数值 |")
                stage_lines.append("|:---|:---:|")
                for k, v in data.items():
                    stage_lines.append(f"| {k} | {self._fmt_val(v)} |")
                stage_lines.append("")

        return "\n".join(
            [
                "## 5. 二阶段设计结果",
                "",
                f"结果文件: {advanced_path}" if advanced_path else "结果文件: 未定位",
                "",
                *stage_lines,
                "---",
            ]
        )

    def _section_stage2_analysis(self, advanced_data: dict | None) -> str:
        if not advanced_data:
            return "\n".join(
                [
                    "## 6. 二阶段阶段内容分析",
                    "",
                    "未生成二阶段分析数据。",
                    "",
                    "---",
                ]
            )

        constraints = advanced_data.get("geometry_constraints", [])
        constraint_lines = []
        if isinstance(constraints, list) and constraints:
            constraint_lines.append("| 约束 | 是否通过 | 实际值 | 限值 | 裕度 |")
            constraint_lines.append("|:---|:---:|:---:|:---:|:---:|")
            for c in constraints:
                if isinstance(c, dict):
                    constraint_lines.append(
                        f"| {c.get('name')} | {c.get('passed')} | {self._fmt_val(c.get('actual_value'))} | {self._fmt_val(c.get('limit_value'))} | {self._fmt_val(c.get('margin'))} |"
                    )
        else:
            constraint_lines.append("未提供几何约束检查结果。")

        return "\n".join(
            [
                "## 6. 二阶段阶段内容分析",
                "",
                "### 6.1 关键公式",
                "$$C_D=C_{D0}+kC_L^2$$",
                "$$R=\\frac{V}{c}\\frac{L}{D}\\ln\\left(\\frac{W_i}{W_f}\\right)$$",
                "$$V_h=\\frac{S_h l_h}{S\\bar{c}},\\quad V_v=\\frac{S_v l_v}{Sb}$$",
                "$$M\\approx\\frac{nWb}{4}$$",
                "",
                "### 6.2 几何约束检查",
                *constraint_lines,
                "",
                "---",
            ]
        )

    def _section_improvements(self, outputs: dict, metrics: dict, advanced_data: dict | None) -> str:
        suggestions = []
        converged = outputs.get("converged")
        if converged is not True:
            suggestions.append("迭代未收敛：提高推重比或降低翼载后重新迭代。")
        if isinstance(metrics.get("thrust_to_weight"), (int, float)) and metrics.get("thrust_to_weight") < 0.3:
            suggestions.append("推重比偏低：建议提升发动机推力或降低结构重量。")
        if isinstance(metrics.get("wing_loading_pa"), (int, float)) and metrics.get("wing_loading_pa") > 8000:
            suggestions.append("翼载偏高：建议增大翼面积或提高高升力能力。")
        if advanced_data:
            constraints = advanced_data.get("geometry_constraints", [])
            if isinstance(constraints, list):
                failed = [c for c in constraints if isinstance(c, dict) and c.get("passed") is False]
                if failed:
                    suggestions.append("几何约束未通过：优化机翼展弦比或燃油容积配置。")
        if not suggestions:
            suggestions.append("总体指标满足要求：建议进行气动细化和结构轻量化优化。")

        return "\n".join(
            [
                "## 7. 后续改进意见",
                "",
                *[f"- {s}" for s in suggestions],
                "",
                "---",
            ]
        )

    def _collect_figures(self, output_dir: Path) -> list[dict]:
        candidates = [
            ("aero_cl_alpha.png", "升力曲线"),
            ("aero_drag_polar.png", "阻力极曲线"),
            ("perf_thrust_curves.png", "推力需求/可用推力曲线"),
            ("perf_flight_envelope.png", "飞行包线"),
            ("struct_vn_diagram.png", "V-n 图"),
            ("view_top_static.png", "三视图-俯视"),
            ("view_side_static.png", "三视图-侧视"),
        ]
        figures: list[dict] = []
        for filename, title in candidates:
            path = output_dir / filename
            if path.exists():
                figures.append({"file": filename, "title": title})
        return figures

    def _load_latest_advanced_results(self, output_dir: Path) -> tuple[str | None, dict | None]:
        candidates = sorted(output_dir.glob("advanced_design_results_*.json"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            return None, None
        latest = candidates[-1]
        try:
            with open(latest, "r", encoding="utf-8") as f:
                data = json.load(f)
            return latest.name, data if isinstance(data, dict) else None
        except Exception:
            return latest.name, None

    def _build_report_json(
        self,
        *,
        output_data: dict,
        requirements: dict,
        initial_guess: dict,
        outputs: dict,
        geometry: dict,
        performance: dict,
        weight_breakdown: dict,
        metrics: dict,
        figures: list[dict],
        advanced_path: str | None,
        advanced_data: dict | None,
    ) -> dict:
        return {
            "project_name": self.project_name,
            "timestamp": self.timestamp,
            "inputs": {
                "requirements": requirements,
                "initial_guess": initial_guess,
            },
            "outputs": outputs,
            "geometry": geometry,
            "performance": performance,
            "weight_breakdown": weight_breakdown,
            "metrics": metrics,
            "figures": figures,
            "advanced_results": {"file": advanced_path, "data": advanced_data},
            "raw_output": output_data,
        }

    def _dict_table_rows(self, items: list[tuple[str, Any, str]]) -> list[str]:
        rows = []
        for name, value, unit in items:
            rows.append(f"| {name} | {self._fmt_val(value)} | {unit} |")
        return rows

    def _flatten_weight_rows(self, weight_breakdown: dict) -> list[str]:
        rows = []
        for k, v in weight_breakdown.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    rows.append(f"| {k} - {sub_k} | {self._fmt_val(sub_v)} | kg |")
            else:
                rows.append(f"| {k} | {self._fmt_val(v)} | kg |")
        if not rows:
            rows.append("| - | - | - |")
        return rows

    def _fmt_val(self, value: Any) -> str:
        if isinstance(value, bool):
            return "是" if value else "否"
        if isinstance(value, (int, float)):
            return self._fmt_num(float(value))
        return str(value) if value is not None else "-"

    def _fmt_num(self, value: float | None) -> str:
        if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
            return "-"
        if abs(value) >= 1000:
            return f"{value:.2f}"
        if abs(value) >= 10:
            return f"{value:.3f}"
        return f"{value:.4f}"

    def _safe_div(self, numerator: float | None, denominator: float | None) -> float | None:
        if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
            return None
        if abs(denominator) < 1e-9:
            return None
        return float(numerator) / float(denominator)

    def _safe_sqrt(self, value: float | None) -> float | None:
        if not isinstance(value, (int, float)):
            return None
        if value < 0:
            return None
        return float(math.sqrt(value))

    def _num(self, value: Any) -> float | None:
        return float(value) if isinstance(value, (int, float)) else None
