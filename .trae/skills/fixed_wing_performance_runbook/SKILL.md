---
name: "fixed_wing_performance_runbook"
description: "执行固定翼一级性能校核（巡航所需推力、爬升率/余度）。当总体闭环需要性能判据或要定位性能不满足原因时调用。"
---

# 固定翼性能快算执行（Runbook）

## 角色定位（统一入口）

- 本技能默认由 `fixed_wing_overall_sizing_runbook` 闭环驱动，不建议作为独立入口。
- 单独调用仅用于回答“当前几何/重量/气动假设下，巡航与爬升余度是否为正，以及主要驱动项是什么”。

## 典型输入来源（按闭环输出对齐）

- 设计点：`initial_guess.thrust_to_weight`、`initial_guess.wing_loading_pa`
- 气动：`initial_guess.cd0`、`initial_guess.oswald_e`、`initial_guess.aspect_ratio`
- 任务工况：`requirements.cruise_altitude_m`、`requirements.cruise_mach`
- 重量/几何：来自闭环结果（`design_data.json.outputs.mtow_kg`、`wing_area_m2` 等）

## 输出解读（用于迭代决策）

- `cruise_required_thrust_n`：巡航点阻力对应的所需推力
- `climb_rate_m_s`：基于推力等级与阻力模型的一级爬升率估算

## 迭代建议（把“症状”映射到“该改什么”）

- 巡航所需推力过大：优先降低 `cd0` 或提高 `e/AR`，其次提高推重比或降低重量
- 爬升率不足：优先提高 `thrust_to_weight`，其次降低重量/阻力（`cd0`、`e`）
