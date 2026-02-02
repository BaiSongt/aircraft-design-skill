---
name: "fixed_wing_constraints_spec"
description: "固定翼约束分析方案：失速/巡航/爬升/起降距离等约束线与设计点选择。当需要用约束分析确定 W/S 与 T/W 设计点时调用。"
---

# 固定翼约束分析（Spec）

## 目标

- 形成可扩展的约束分析框架，用于选择总体设计点
- 输出设计点处每条约束的需求与余度

## 输入

- 任务：巡航高度/速度、失速速度、爬升梯度与爬升速度
- 任务（可选）：起飞/着陆距离限制与地面参数
- 气动：`cd0`, `e`, `AR`, `cl_max`
- 设计变量：候选 `wing_loading_pa`、可用 `thrust_to_weight`

## 输出

- 设计点：`wing_loading_pa` 与 `thrust_to_weight_available`
- 约束校核清单：
  - `cruise`：巡航所需 `T/W`
  - `climb_gradient`：爬升梯度所需 `T/W`
  - `stall_ws`：失速约束 `W/S` 上界与裕度
  - `takeoff_distance`：起飞距离约束（由 `T/W` 与高升力 `CLmax` 联合决定）
  - `landing_distance`：着陆距离约束（由高升力 `CLmax` 与制动减速度决定）
  - `takeoff_climb_gradient`：起飞构型爬升梯度（引入高升力构型的 `ΔCD0`）
- 约束线数据结构（后续扩展）：用于绘制 `W/S`–`T/W` 可行域
