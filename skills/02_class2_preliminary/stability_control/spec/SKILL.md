---
name: "fixed_wing_stability_control_spec"
description: "固定翼稳定与操纵方案：尾容积系数定尺寸、静稳定裕度与配平接口。当需要从总体几何推导尾翼与稳定性初算时调用。"
stage: "class2_preliminary"
code_module: "aircraft_design/class2_preliminary/stability_control.py, aircraft_design/class2_preliminary/tail_sizing.py"
dependencies:
  - "fixed_wing_overall_sizing_runbook"
---

# 固定翼稳定与操纵方案（Spec）

## 目标

- 用尾容积系数法给出水平尾翼/垂直尾翼面积初值
- 为配平阻力与 CG 包线分析预留接口（后续扩展）

## 与统一入口的字段映射

- 本 Spec 定义的输入应与统一输入 JSON 对齐，并由 `fixed_wing_overall_sizing_runbook` 在收敛后阶段 2–7 中使用：
  - 尾容积与尾臂：`tail.vh`、`tail.vv`、`tail.lh_m`、`tail.lv_m`
  - 静稳定关键假设：`stability.*`
  - 机翼尺度：来自总体闭环输出（`outputs.wing_area_m2`、`outputs.geometry.*`），或由 `geometry_shape` 派生

## 输入（统一 JSON 视角）

- `tail`：`vh`、`vv`、`lh_m`、`lv_m`
- `stability`（可选）：`x_ac_w_cbar`、`x_cg_cbar`、`x_cg_fwd_cbar`、`x_cg_aft_cbar`、`cm0_w`、`tail_efficiency` 等
- `geometry_shape.tail.*`（可选）：用于把“面积初算”落到可视化/网格/导出层

## 输出

- `Sh`, `Sv`：水平/垂直尾翼面积初算
- 稳定性检查项清单（占位）：静稳定裕度、操纵面余度、配平阻力
