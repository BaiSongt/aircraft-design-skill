from dataclasses import dataclass
from typing import List, Dict
import os


@dataclass
class Requirement:
    chapter: str
    section: str
    description: str
    keywords: List[str]
    status: str = "Pending"
    implemented_in: str = ""


class GapAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.requirements = self._load_requirements()
        self.code_files = self._load_code_files()

    def _load_requirements(self) -> List[Requirement]:
        return [
            Requirement("1", "引言", "项目背景, 目标, 依据", ["background", "objective", "regulations"]),
            Requirement(
                "2", "设计要求", "总体指标, 气动, 性能, 任务剖面", ["requirements", "mission_profile", "mtow", "range"]
            ),
            Requirement(
                "3", "总体方案", "布局选型, 主要参数, 三面图", ["configuration", "layout", "three_view", "geometry"]
            ),
            Requirement(
                "4", "气动设计", "翼型, 升阻特性, 极曲线", ["airfoil", "lift", "drag", "polar", "aerodynamics"]
            ),
            Requirement(
                "5",
                "重量重心",
                "重量估算, 重心包线, 转动惯量",
                ["weight", "cg", "balance", "inertia", "center_of_gravity"],
            ),
            Requirement(
                "6",
                "飞行性能",
                "起降, 爬升, 巡航, 续航",
                ["performance", "takeoff", "landing", "climb", "cruise", "endurance"],
            ),
            Requirement("7", "结构设计", "载荷, 材料, 结构选型", ["structure", "load", "material", "vn_diagram"]),
            Requirement(
                "8", "动力系统", "发动机选型, 推力, 进排气", ["propulsion", "engine", "thrust", "inlet", "nozzle"]
            ),
            Requirement("9", "系统设备", "航电, 飞控, 环控", ["avionics", "flight_control", "environmental", "system"]),
            Requirement(
                "10",
                "操稳特性",
                "静稳定, 动稳定, 尾翼",
                ["stability", "control", "static_margin", "dynamic_stability", "tail_sizing"],
            ),
            Requirement("11", "人机工效", "座舱, 视野, 舒适性", ["ergonomics", "cockpit", "human_factor"]),
            Requirement("12", "适航符合性", "条款, 验证", ["airworthiness", "certification", "compliance"]),
            Requirement("13", "经济性", "DOC, 运营成本", ["economics", "cost", "doc", "operating_cost"]),
            Requirement("14", "结论", "总结, 建议", ["conclusion", "summary"]),
        ]

    def _load_code_files(self) -> Dict[str, str]:
        files = {}
        for root, _, filenames in os.walk(os.path.join(self.root_dir, "aircraft_design")):
            for f in filenames:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", encoding="utf-8") as file:
                        files[f] = file.read()
        return files

    def analyze(self):
        for req in self.requirements:
            for fname, content in self.code_files.items():
                # Check for keywords in content (case insensitive)
                if any(k.lower() in content.lower() for k in req.keywords):
                    req.status = "Implemented"
                    if req.implemented_in:
                        req.implemented_in += f", {fname}"
                    else:
                        req.implemented_in = fname

            # Special manual checks or overrides
            if req.chapter == "11" or req.chapter == "12":  # Known gaps
                req.status = "Missing"
                req.implemented_in = ""

    def generate_report(self) -> str:
        report = "# Functional Gap Analysis Report\n\n"
        report += "| Chapter | Section | Status | Implemented In | Keywords |\n"
        report += "|---|---|---|---|---|\n"

        missing_count = 0
        for req in self.requirements:
            status_icon = "✅" if req.status == "Implemented" else "❌"
            if req.status != "Implemented":
                missing_count += 1
            report += f"| {req.chapter} | {req.section} | {status_icon} {req.status} | {req.implemented_in} | {', '.join(req.keywords)} |\n"

        report += f"\n**Total Requirements**: {len(self.requirements)}\n"
        report += f"**Missing**: {missing_count}\n"
        report += f"**Coverage**: {((len(self.requirements) - missing_count) / len(self.requirements)) * 100:.1f}%\n"

        report += "\n## Missing Features & Development Plan\n"
        for req in self.requirements:
            if req.status != "Implemented":
                report += f"\n### {req.chapter}. {req.section}\n"
                report += f"- **Description**: {req.description}\n"
                report += "- **Priority**: High\n"
                report += f"- **Action Plan**: Create module `aircraft_design/chapter_{req.chapter}_{req.keywords[0]}.py` implementing {req.description}.\n"

        return report


if __name__ == "__main__":
    analyzer = GapAnalyzer(os.getcwd())
    analyzer.analyze()
    print(analyzer.generate_report())
