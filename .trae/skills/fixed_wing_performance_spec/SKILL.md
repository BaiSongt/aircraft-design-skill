---
name: "fixed_wing_performance_spec"
description: "固定翼性能快算方案：巡航配平、所需推力、爬升率等一级性能校核。当需要对总体方案做快速性能余度检查时调用。"
---

# 固定翼性能快算方案（Spec）

## 目标

- 对总体方案做一级性能校核（巡航与爬升为第一优先）
- 将性能约束与总体设计点、气动模型保持一致

## 与统一入口的字段映射

- 性能快算由 `fixed_wing_overall_sizing_runbook` 统一调用，典型字段来源：
  - 任务工况：`requirements.cruise_altitude_m`、`requirements.cruise_mach`
  - 气动初猜：`initial_guess.cd0`、`initial_guess.oswald_e`、`initial_guess.aspect_ratio`
  - 设计点：`initial_guess.thrust_to_weight`、`initial_guess.wing_loading_pa`
  - 闭环重量/几何：`outputs.mtow_kg`、`outputs.wing_area_m2`

## 输入（概念层）

- 重量：MTOW 或任务工况重量
- 几何：机翼参考面积与展弦比
- 气动：`CD0` 与诱导阻力项
- 推进：推力等级（或可用推力随高度/速度模型）

## 输出

- `cruise_required_thrust_n`
- `climb_rate_m_s`
- 性能余度与不满足项列表（后续扩展）
