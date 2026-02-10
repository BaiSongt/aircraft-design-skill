---
name: "fixed_wing_overall_sizing_spec"
description: "生成固定翼总体设计方案（需求→约束→设计点→初步尺寸→重量/性能闭合）。当需要给出固定翼总体方案、关键参数范围与决策依据时调用。"
---

# 固定翼总体设计方案（Spec）

## 目的

- 将固定翼总体设计流程标准化输出为可迭代方案
- 给出关键设计变量的推荐取值、约束关系与余度检查

## 统一入口与字段映射

- 本 Spec 只定义“总体方案应该包含哪些输入/输出与判据”，实际计算统一由 `fixed_wing_overall_sizing_runbook` 执行。
- 与统一输入 JSON 的字段对应关系：
  - 任务与约束：`requirements.*`
  - 总体初猜：`initial_guess.*`
  - （可选）外形与约束：`geometry_shape`、`geometry_detailed`、`geometry_constraints`、`systems`

## 输入（统一 JSON 视角）

- `requirements`：航程、载荷、巡航点、起降距离、过载/升限等
- `initial_guess`：`thrust_to_weight`、`wing_loading_pa`、`aspect_ratio`、`sweep_deg`、`taper_ratio`、`thickness_ratio`、`sfc_cruise_1_s`、`cd0`、`oswald_e`

## 输出

方案输出建议包含：

- 设计点：`outputs.design_point.wing_loading_pa`、`outputs.design_point.thrust_to_weight`
- 主尺度：`outputs.wing_area_m2`、`outputs.geometry.span_m`、`outputs.geometry.cbar_m`
- 气动模型：`outputs.aero.*`（或收敛后扩展阶段的 `stage2_aero.*`）
- 重量闭合：`outputs.mtow_kg`、`outputs.empty_weight_kg`、`outputs.fuel_weight_kg`
- 性能余度：`outputs.performance.*`（或扩展阶段的 `stage3_propulsion.*`/`stage4_mission.*`）

## 关键规则

- 设计点必须满足失速约束上界：`(W/S) <= q * CLmax`
- 重量、气动、性能必须在同一组几何与工况假设下闭合
