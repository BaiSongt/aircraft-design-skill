---
name: "fixed_wing_shape_detail_spec"
description: "定义固定翼外形详细设计（翼型/机身剖面/三视图预览）接口与验收标准。用户需要把外形细化并与总体输入对齐时调用。"
stage: "class3_detailed"
code_module: "aircraft_design/class3_detailed/geometry_detailed.py, aircraft_design/class3_detailed/geometry_modeling.py"
dependencies:
  - "fixed_wing_shape_parametric_spec"
---

# 固定翼外形详细设计（Spec）

本阶段目标：在总体设计闭环已经可跑的前提下，把外形从“参数化占位”推进到“可追溯的详细几何输入”，并且提供可视化（优先三视图），为后续 OpenVSP/VSPAero/更高保真分析做接口准备。

## 与统一入口的接口关系

- 外形资产生成与落盘由 `fixed_wing_overall_sizing_runbook` 统一执行（`python -m aircraft_design.run_sizing`）。
- 统一入口在收敛后会在 `output/<project>_*/` 输出：
  - `geometry_3d.html`、`geometry_mesh.json`、`geometry.obj`
  - `model.vspscript`、`model.obj`
  - `design_report_v2.md`、`design_data.json`

## 1. 输入接口（建议字段）

### 1.1 `geometry_parametric`（已有）

- `wing.aspect_ratio`
- `wing.taper_ratio`
- `wing.sweep_quarter_chord_deg`
- `wing.t_c`
- `fuselage.length_m`
- `fuselage.diameter_m`
- `tail.area_ratio_to_wing`

### 1.2 `geometry_detailed`（新增）

#### 机翼翼型

- `geometry_detailed.wing.airfoil`
  - `type`: `"naca4"`（当前支持）
  - `code`: 例如 `"2412"`
  - `n`: 采样点数（默认 161）

#### 机身剖面（轴对称站位序列）

- `geometry_detailed.fuselage.stations`: list
  - 每项：`{ "x_m": number, "radius_m": number }`
  - 要求：`x_m` 单调递增（系统会排序），`radius_m >= 0`

### 1.3 `geometry_search`（创成式搜索）

- 允许设置范围：`aspect_ratio/taper_ratio/sweep_quarter_chord_deg/t_c/fuselage_length_m/fuselage_diameter_m/tail_area_ratio_to_wing`
- 每项格式：`{ "min": number, "max": number }`

## 2. 输出接口（建议字段）

- 输出以文件为主，写入 `output/<project>_*/`：
  - `geometry_3d.html`：三视图 HTML 预览
  - `geometry_mesh.json`：网格 JSON
  - `geometry.obj`：OBJ 资产
  - `model.vspscript`：OpenVSP 脚本（可选）

## 3. 可视化验收（必须）

- 默认输出为三视图：Top (X-Y)、Side (X-Z)、Front (Y-Z)
- 若 Three.js 加载失败（CDN/离线/受限环境），必须自动降级显示线框投影，保证不“空白”

## 4. 验收标准（可执行）

- 输入仅提供 `geometry_parametric` 时：可生成三视图预览与 OBJ/JSON 资产
- 输入提供 `geometry_detailed` 时：`geometry_mesh.json` 生成成功且可被 `geometry_3d.html` 正常加载
- 所有测试可通过：`python -m unittest discover -s tests`
