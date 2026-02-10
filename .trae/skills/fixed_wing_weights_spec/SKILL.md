---
name: "fixed_wing_weights_spec"
description: "固定翼重量方案（Class I）：空重统计模型 + 航程燃油估算 + MTOW 迭代闭合。当需要建立重量闭合与敏感性分析时调用。"
---

# 固定翼重量方案（Spec）

## 目标

- 在总体设计早期实现 MTOW（W0）快速闭合
- 输出空重、燃油重量与闭合迭代信息，为性能与结构提供一致重量

## 与统一入口的字段映射

- 重量闭合由 `fixed_wing_overall_sizing_runbook` 统一驱动，输入来自同一份 JSON：
  - 航程/任务：`requirements.range_m`
  - 推进耗油：`initial_guess.sfc_cruise_1_s`
  - 气动极曲线参数：`initial_guess.cd0`、`initial_guess.oswald_e`、`initial_guess.aspect_ratio`
  - 载荷：`requirements.payload_kg`

## 输入（概念层）

- 空重估算：统计模型/半经验模型（由代码实现决定）
- 航程燃油：Breguet（与气动/推进假设一致）
- 储备油：由闭环内部假设或扩展字段提供（当前版本为固定默认）

## 输出

- `outputs.mtow_kg`、`outputs.empty_weight_kg`、`outputs.fuel_weight_kg`
- `outputs.converged` 与迭代历史（若写入）
