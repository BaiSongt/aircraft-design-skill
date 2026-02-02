---
name: "fixed_wing_shape_detail_spec"
description: "定义固定翼外形详细设计（翼型/机身剖面/三视图预览）接口与验收标准。用户需要把外形细化并与总体输入对齐时调用。"
---

# 固定翼外形详细设计（Spec）

本阶段目标：在总体设计闭环已经可跑的前提下，把外形从“参数化占位”推进到“可追溯的详细几何输入”，并且提供可视化（优先三视图），为后续 OpenVSP/VSPAero/更高保真分析做接口准备。

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

- `results.geometry_detailed`
  - `wing.airfoil.coords`：翼型坐标（归一化 chord）
  - `fuselage.stations`：站位剖面输入快照（排序后）
- `results.artifacts`
  - `geometry_3d_html`: 三视图 HTML 文件名
  - `geometry_obj`: OBJ 文件名
  - `geometry_mesh_json`: 网格 JSON 文件名

## 3. 可视化验收（必须）

- 默认输出为三视图：Top (X-Y)、Side (X-Z)、Front (Y-Z)
- 若 Three.js 加载失败（CDN/离线/受限环境），必须自动降级显示线框投影，保证不“空白”

## 4. 验收标准（可执行）

- 输入仅提供 `geometry_parametric` 时：可生成三视图预览与 OBJ/JSON 资产
- 输入提供 `geometry_detailed.wing.airfoil` 时：`results.geometry_detailed.wing.airfoil.coords` 可用且点数正确
- 输入提供 `geometry_detailed.fuselage.stations` 时：结果中包含排序后的 stations
- 所有测试可通过：`python -m unittest discover -s tests`

