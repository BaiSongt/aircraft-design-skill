---
name: "fixed_wing_shape_parametric_spec"
description: "定义固定翼全外形参数化（翼/尾/机身/翼型/布局/控制点）输入与派生规则。用户要把外形完全参数化并逐步细化时调用。"
stage: "class3_detailed"
code_module: "aircraft_design/class3_detailed/geometry_parametric.py, aircraft_design/class3_detailed/geometry_shape.py"
dependencies:
  - "fixed_wing_overall_sizing_runbook"
---

# 固定翼全外形参数化（Spec）

目标：把固定翼飞机外形从“少量总体参数”推进为“可完整重建外形的参数集”，并允许局部通过控制点增强自由度，且保持与总体设计闭环输入兼容。

## 与统一入口的接口关系

- 外形输入与派生规则服务于统一入口 `fixed_wing_overall_sizing_runbook`。
- 外形可通过三种层级逐步细化（推荐逐级推进）：
  - `geometry_parametric`（总体级，少字段）
  - `geometry_detailed`（详细级，翼型/站位）
  - `geometry_shape`（完整参数化 + 控制点 + 布局）

## 1. 总体原则

- **分层**：`geometry_parametric`（总体级）→ `geometry_detailed`（详细级）→ `geometry_shape`（全参数化+控制点+布局）。
- **可选项参数化**：所有“可选细节”（翼型、机身站位、尾翼剖面、整流罩/舱盖等）必须能用参数开关启用/禁用，且提供默认值。
- **派生一致性**：详细外形应能派生出用于性能/重量闭环的关键几何量（Sref、AR、t/c、wet area 估算参数等），并可回写到 `results`。
- **可视化可复现**：同一输入必须得到一致的三维网格与四视图预览。

## 2. 建议输入：`geometry_shape`（新增）

### 2.1 全局

- `geometry_shape.units`: `"m"`（默认）
- `geometry_shape.layout`：预览布局参数化（见 5）
- `geometry_shape.resolution`
  - `fuselage_n_stations`（默认 21）
  - `airfoil_n_points`（默认 161）
  - `mesh_n_circ`（默认 28）

### 2.2 机翼（Wing）

- `geometry_shape.wing.planform`
  - `s_ref_m2`（可选：若不给由总体结果提供）
  - `aspect_ratio`
  - `taper_ratio`
  - `sweep_quarter_chord_deg`
  - `dihedral_deg`（可选）
  - `incidence_deg`（可选）
- `geometry_shape.wing.sections`
  - `root_airfoil`：`{type:'naca4', code:'2412'}`
  - `tip_airfoil`：`{type:'naca4', code:'0012'}`（可选，默认同根）
  - `blend`：`'linear'`（默认）
- `geometry_shape.wing.controls`（可选，增强自由度）
  - `spanwise_control_points`: `[{eta:0.0..1.0, twist_deg, chord_scale, t_c}]`

### 2.3 机身（Fuselage）

- `geometry_shape.fuselage.axis`
  - `x0_m`（默认 -0.15*L）
  - `length_m`
- `geometry_shape.fuselage.profile`
  - `mode`: `'stations' | 'control_points'`
  - `'stations'`：直接给 `stations=[{x_m,radius_m}]`
  - `'control_points'`：给控制点 `[{x_rel:0..1, radius_rel:0..1}]` + `max_radius_m`
  - `closure`: `'open'`（默认，允许首尾半径为 0）

### 2.4 尾翼（Tail）

- `geometry_shape.tail.horizontal` 与 `geometry_shape.tail.vertical`（可选）
  - planform + section（可复用 wing 的结构）
  - 或采用相对翼面积/容积系数派生

## 3. 派生产物（统一入口）

- 由 `fixed_wing_overall_sizing_runbook` 在收敛后落盘到 `output/<project>_*/`：
  - `geometry_3d.html`、`geometry_mesh.json`、`geometry.obj`
  - `model.vspscript`（可选）

## 4. 验收标准

- 仅用 `geometry_shape` 就能生成：四视图预览 + OBJ + 网格 JSON
- 关闭控制点（使用默认）时，结果与现有 `geometry_parametric/geometry_detailed` 保持一致（误差在容许范围内）
- 单测覆盖：机身控制点→stations，根/梢翼型→翼网格生成，布局参数→HTML 包含相应视图

## 5. 可视化布局参数化

建议 `geometry_shape.layout` 字段：

- `views`: `['top','side','front','iso']`（默认四视图）
- `grid`: `{rows:2, cols:2}`（默认）
- `enable_axes`: `true|false`
- `enable_grid`: `true|false`
