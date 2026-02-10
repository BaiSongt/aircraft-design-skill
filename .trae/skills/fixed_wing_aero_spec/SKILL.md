---
name: "fixed_wing_aero_spec"
description: "固定翼气动方案设计：阻力分解、极曲线、升阻比与高升力装置取值范围。当需要建立可用于性能/重量闭合的气动模型时调用。"
---

# 固定翼气动方案（Spec）

## 目标

- 输出可用于总体闭环的气动极曲线模型：`CD = CD0 + k * CL^2`
- 定义起飞/着陆构型下的 `CLmax` 与阻力增量策略（后续细化）

## 与统一入口的字段映射

- 本 Spec 的输入应与统一输入 JSON 对齐，并由 `fixed_wing_overall_sizing_runbook` 在 Class I 闭环与收敛后扩展阶段共同使用：
  - 巡航点：`requirements.cruise_altitude_m`、`requirements.cruise_mach`
  - 气动初猜：`initial_guess.cd0`、`initial_guess.oswald_e`
  - 诱导阻力项：`initial_guess.aspect_ratio`
  - 高升力：当前版本以默认 `CLmax` 假设支撑约束（后续可参数化）

## 输入（概念层）

- 几何初值：`S`, `AR`, `b`, `cbar`
- 任务工况：巡航高度/速度
- 初始气动假设：`cd0`, `e`, `cl_max`

## 输出

- `cd0`：零升阻系数
- `k`：诱导阻力系数（由 `AR` 与 `e` 给出）
- `L/D`：巡航点升阻比估算
- 高升力建议：`cl_max` 与起降构型策略（需要满足失速/起降约束）
