---
name: "fixed_wing_shape_parametric_runbook"
description: "落地固定翼外形参数化（geometry_shape/geometry_detailed）并生成可视化资产。当用户要逐步细化外形输入并保证可重建/可复现时调用。"
stage: "class3_detailed"
code_module: "aircraft_design/class3_detailed/geometry_parametric.py, aircraft_design/class3_detailed/geometry_shape.py"
dependencies:
  - "fixed_wing_shape_parametric_spec"
---

# 固定翼全外形参数化（Runbook）

## 角色定位（统一入口）

- 本技能不提供“第二套总体流程”。外形参数化的落盘与报告统一由 `fixed_wing_overall_sizing_runbook` 完成。
- 本 Runbook 负责把外形输入从“少量参数”推进到“可完整重建外形的参数字典”，并指导如何验证可复现。

## 0) 目标

- 先统一“外形可重建的参数字典”（geometry_shape / geometry_detailed）
- 再逐步增加自由度（控制点），并在每步都能输出可视化资产

## 1) 起步：只用 `geometry_detailed`

输入：

- `geometry_detailed.wing.airfoil`（NACA4）
- `geometry_detailed.fuselage.stations`（站位）

运行：

```bash
python -m aircraft_design.run_sizing ./sizing_input.json --project-name "GeomStep1"
```

查看：

- `output/GeomStep1_*/` 下的报告与资产（例如 `design_report_v2.md`、`geometry_3d.html`、`geometry_mesh.json`、`geometry.obj`，收敛后还会输出 OpenVSP/交互图表等）

## 2) 升级：把站位改为控制点（建议）

将机身 profile 改为控制点模式（`x_rel/radius_rel`），派生为 `stations` 后再网格化。

## 3) 翼型升级

- 根/梢不同翼型：`root_airfoil` 与 `tip_airfoil`
- 增加 spanwise 控制点：扭转/弦长/厚度比沿展向变化

## 4) 可视化布局参数化

按需选择视图集合与网格：

- `views`: `['top','side','front','iso']`
- `grid`: `{rows:2, cols:2}`

## 5) 验证

```bash
python -m unittest discover -s tests
```

## 6) 细化清单（建议推进顺序）

- 布局/坐标系：机翼安装角、上反角、机翼位置（x/z）、尾翼类型与位置
- 机翼：根/梢不同翼型、展向扭转与弦长控制点、襟副翼段落与铰线
- 机身：轴对称站位→控制点→（可选）非轴对称截面、座舱罩/整流罩
- 尾翼：平尾/垂尾分别的剖面与控制点、V 尾/双垂尾布局
- 外形一致性：翼身干扰、尾翼与机身过渡（简化 fillet）
- 资产输出：OBJ/JSON/OpenVSP 脚本、四视图/多视图布局、候选集对比页
