---
name: "fixed_wing_performance_runbook"
description: "执行固定翼一级性能快算（巡航所需推力、爬升率）并输出性能余度。当需要快速校核方案可行性时调用。"
---

# 固定翼性能快算执行（Runbook）

## 推荐入口

- 一键总体脚本：`scripts/run_fixed_wing_design.py`

## 单独性能校核时的必需输入

- `sizing.s_m2`（或由 `w0_kg` 与 `wing_loading_pa` 推得）
- `aero.cd0`, `aero.e`, `sizing.aspect_ratio`
- `mission.cruise_altitude_m`, `mission.cruise_speed_m_s`
- `sizing.thrust_to_weight`（用于爬升快算的推力等级）

## 输出解读

- `cruise_required_thrust_n`：巡航点阻力对应的所需推力
- `climb_rate_m_s`：基于推力等级与阻力模型的一级爬升率估算

