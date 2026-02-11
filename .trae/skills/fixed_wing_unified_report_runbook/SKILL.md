---
name: "fixed_wing_unified_report_runbook"
description: "统一格式报告生成：基于最终设计参数与输出目录生成统一 Markdown/JSON 报告。用户要求报告格式统一、与参数匹配、需要输出改进建议时调用。"
---

# Fixed Wing Unified Report Runbook

当用户要求“统一格式、与输出参数一致”的设计报告时调用。本技能以最终的 `design_data.json` 与输出目录中的曲线图为输入，生成统一格式报告与结构化 JSON。

## 适用场景
* 需要修正现有报告内容与参数不一致的问题。
* 需要在一个统一模板中汇总一阶段与二阶段结果。
* 需要输出可结构化读取的报告 JSON。

## 输入
* `output/<project>_YYYYMMDD_HHMMSS/` 目录
* `design_data.json`
* 曲线图文件（如 `aero_cl_alpha.png`、`perf_thrust_curves.png`）
* 二阶段结果文件（如 `advanced_design_results_*.json`，可选）

## 输出
* `design_report_unified.md`
* `design_report_unified.json`

## 执行步骤
1. 运行总体设计入口 `python -m aircraft_design.run_sizing <input.json>`，脚本会在输出目录自动生成统一格式报告。
2. 若需基于已有输出目录重新生成，执行以下脚本：

```python
from pathlib import Path
import json
from aircraft_design.report_generator_unified import UnifiedReportGenerator

output_dir = Path("output/<project>_YYYYMMDD_HHMMSS")
with open(output_dir / "design_data.json", "r", encoding="utf-8") as f:
    output_data = json.load(f)

reporter = UnifiedReportGenerator(project_name=output_data.get("project_name", "Design"))
report_md, report_json = reporter.generate_report(output_data, output_dir)

(output_dir / "design_report_unified.md").write_text(report_md, encoding="utf-8")
with open(output_dir / "design_report_unified.json", "w", encoding="utf-8") as f:
    json.dump(report_json, f, ensure_ascii=False, indent=2)
```

## 报告结构要求
* 输入设计需求
* 需求分析
* 一阶段设计结果
* 一阶段设计内容分析
* 二阶段设计结果
* 二阶段阶段内容分析
* 后续改进意见

## 必须包含
* 按计算分支附上 LaTeX 公式
* 输出目录中的曲线图
* 与最终设计参数一致的数值
