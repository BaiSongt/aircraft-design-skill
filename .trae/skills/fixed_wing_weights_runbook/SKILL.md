---
name: "fixed_wing_weights_runbook"
description: "执行固定翼 Class I 重量闭合并输出重量分解。当需要在总体迭代中快速收敛 MTOW/燃油重量时调用。"
---

# 固定翼重量闭合执行（Runbook）

## 目标

- 对给定任务与气动/推进假设，完成 MTOW 闭合
- 输出可回馈总体与性能的重量结果

## 入口与数据字段

- 推荐通过总体一键脚本执行：`scripts/run_fixed_wing_design.py`
- 若单独使用重量模块，核心输入字段：
  - `weights.empty_a`, `weights.empty_b`
  - `weights.reserve_fraction`
  - `propulsion.type` 与对应 `SFC/TSFC/η`
  - `mission.range_m` 与巡航点 `L/D`（由气动模块给出）

## 步骤

1. 给出空重统计模型参数与燃油储备分数
2. 使用 Breguet 得到任务燃油分数
3. 用迭代闭合方程求解 `W0`
4. 输出 `W0/We/Wf` 与迭代收敛信息

