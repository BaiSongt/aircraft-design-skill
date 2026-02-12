---
name: "fixed_wing_constraints_spec"
description: "固定翼约束分析方案：失速/巡航/爬升/起降距离等约束线与设计点选择。当需要用约束分析确定 W/S 与 T/W 设计点时调用。"
stage: "class1_conceptual"
code_module: "aircraft_design/class2_preliminary/constraints.py"
dependencies:
  - "fixed_wing_overall_sizing_runbook"
---

# 固定翼约束分析（Spec）

## 目标

- 形成可扩展的约束分析框架，用于选择总体设计点
- 输出设计点处每条约束的需求与余度

## 与统一入口的字段映射

- 约束分析在 `fixed_wing_overall_sizing_runbook` 的闭环中用于修正/验证设计点。
- 字段来源：
  - 工况与需求：`requirements.*`
  - 初猜与几何假设：`initial_guess.*`

## 输入（统一 JSON 视角）

- 巡航点：`requirements.cruise_altitude_m`、`requirements.cruise_mach`
- 起降距离：`requirements.takeoff_distance_m`、`requirements.landing_distance_m`
- 载荷因子：`requirements.max_load_factor`
- 气动初猜：`initial_guess.cd0`、`initial_guess.oswald_e`、`initial_guess.aspect_ratio`
- 设计变量初猜：`initial_guess.wing_loading_pa`、`initial_guess.thrust_to_weight`
- 高升力（当前版本默认假设，后续可参数化）：`CLmax` 量级

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
