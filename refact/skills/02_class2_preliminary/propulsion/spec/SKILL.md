---
name: "fixed_wing_propulsion_spec"
description: "固定翼推进/能量系统方案：推力/功率等级、耗油/效率模型与可用推力随高度速度变化。当需要把推进假设接入总体性能闭环时调用。"
stage: "class2_preliminary"
code_module: "aircraft_design/class2_preliminary/propulsion.py, aircraft_design/config/engine_library.py"
dependencies:
  - "fixed_wing_overall_sizing_runbook"
---

# 固定翼推进方案（Spec）

## 目标

- 给出推进类型（螺桨/喷气）下的一级模型，支撑航程燃油估算与性能校核

## 与统一入口的字段映射

- 统一入口 `fixed_wing_overall_sizing_runbook` 当前对推进的最小输入是：
  - `initial_guess.sfc_cruise_1_s`（统一用 1/s 表达耗油强弱）
  - `initial_guess.thrust_to_weight`（决定推力等级量级）
- 收敛后扩展阶段会进一步输出推力余度与任务耗油分段（阶段 2–7 的推进/任务模块）。

## 输入（概念层）

- 推进类型：喷气/螺桨（决定耗油与可用推力模型形态）
- 耗油模型：SFC/TSFC/效率（当前版本以 `sfc_cruise_1_s` 统一入口字段承载）
- 推力/功率等级：由设计点 `T/W` 与 MTOW 共同确定

## 输出

- 航程/燃油估算可用的耗油参数（与气动/任务一致）
- 推力等级与巡航/爬升推力余度（扩展阶段 `stage3_propulsion.*`）
