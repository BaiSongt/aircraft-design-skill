---
name: "fixed_wing_shape_detail_runbook"
description: "生成固定翼外形资产（翼型/机身剖面/网格预览/OpenVSP脚本）并支持外形候选搜索。当用户要产出可视化资产或做外形候选对比时调用。"
stage: "class3_detailed"
code_module: "aircraft_design/class3_detailed/geometry_detailed.py, aircraft_design/class3_detailed/geometry_modeling.py"
dependencies:
  - "fixed_wing_shape_detail_spec"
---

# 固定翼外形详细设计（Runbook）

## 角色定位（统一入口）

- “总体闭环计算与落盘”入口固定为 `fixed_wing_overall_sizing_runbook`（输出到 `output/`）。
- 本 Runbook 负责两类事情：
  - 让总体入口在收敛后输出**可复用外形资产**（OpenVSP/OBJ/图表）
  - 通过 `scripts/shape_search.py` 生成**候选外形集合**用于对比筛选（输出到 `out/`）

## 目标

- 从单一输入 JSON 出发，生成可复用外形资产与可视化
- 支持创成式外形搜索（候选集 + 每个候选的三视图预览）
- 支持 OpenVSP 脚本导出（若 OpenVSP/VSPAERO 可用则可进一步分析）

## 一键运行

### 1) 用总体入口生成外形资产（推荐）

```bash
python -m aircraft_design.run_sizing ./sizing_input.json --project-name "ShapeAssets"
```

产物（`output/ShapeAssets_*/`，收敛后才会进入扩展阶段输出资产）：

- `design_report_v2.md`：总体报告（Class I）
- `design_data.json`：输入快照与输出汇总
- `geometry_3d.html`：三视图预览（离线可打开）
- `geometry_mesh.json`：网格 JSON
- `geometry.obj`：OBJ 资产（网格导出）
- `model.vspscript`：OpenVSP 脚本
- `model.obj`：OBJ 导出目标（脚本包含导出指令）
- `interactive_charts.html`：交互图表
- `technical_roadmap_report.md`：扩展阶段技术报告（含图表引用）

### 2) 创成式外形搜索（候选集）

```bash
python ./scripts/shape_search.py ./examples/fixed_wing_ga_single.json --n 32 --seed 1
```

产物（`out/`）：

- `shape_search_report.md`：Top 候选表格（含 3D 链接）
- `shape_search_results.json`：全部候选与可行集
- `shapes/shape_*.html`：每个候选的三视图预览

## GUI 关系说明

- 总体入口可选开启 GUI 做实时可视化；离线候选搜索不会推送到 GUI。
- 若希望 GUI 稳定显示 3D，请确保输入包含 `geometry_shape`（或提供 mesh 顶点/面片数据）。

## 输入片段示例（用于 GUI 兼容）

```json
{
  "geometry_shape": {
    "fuselage": {
      "axis": {"length_m": 10.0},
      "profile": {"mode": "parametric", "max_radius_m": 1.2}
    },
    "wing": {
      "planform": {
        "s_ref_m2": 24.0,
        "aspect_ratio": 6.0,
        "taper_ratio": 0.5,
        "sweep_quarter_chord_deg": 15.0
      }
    }
  }
}
```

## 验证

```bash
python -m unittest discover -s tests
```
