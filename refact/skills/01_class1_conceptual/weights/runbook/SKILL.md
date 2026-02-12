---
name: "fixed_wing_weights_runbook"
description: "执行固定翼 Class I 重量闭合（W0/We/Wf）并输出收敛信息。当总体闭环需要重量结果或燃油/空重异常时调用。"
stage: "class1_conceptual"
code_module: "aircraft_design/class1_conceptual/weights_class1.py"
dependencies:
  - "fixed_wing_weights_spec"
---

# 固定翼重量闭合执行（Runbook）

## 角色定位（统一入口）

- 本技能默认由 `fixed_wing_overall_sizing_runbook` 闭环驱动，不建议作为独立入口。
- 单独调用用于回答“为什么 MTOW 不收敛/燃油分数过高/空重过高”这类重量侧问题。

## 目标

- 对给定任务与气动/推进假设，完成 MTOW 闭合
- 输出可回馈总体与性能的重量结果

## 入口与数据字段

- 统一入口：`fixed_wing_overall_sizing_runbook`（内部完成重量闭合）
- 若做“重量侧诊断”，重点关注输入：
  - 航程/任务：`requirements.range_m`、巡航点（Mach/高度）
  - 推进：`initial_guess.sfc_cruise_1_s`（以及推进类型假设）
  - 气动：`initial_guess.cd0`、`initial_guess.oswald_e`、`initial_guess.aspect_ratio`
  - 空重模型：当前版本在 `run_sizing` 闭环中为内置假设（后续可扩展为显式参数）

## 步骤

1. 运行总体入口，获取 `output/<project>_*/design_data.json`。
2. 读取 `outputs.mtow_kg / empty_weight_kg / fuel_weight_kg` 与迭代历史（若有）。
3. 如果燃油/空重异常，按优先级排查：推进耗油单位 → `L/D`（`cd0/e/AR`）→ 任务指标是否过激。

## 重心与平衡分析

完成重量闭合后，调用 `aircraft_design/weight_balance.py` 进行重心包线分析：

1.  定义各部件重量与力臂（Component）。
2.  定义装载方案（LoadingScenario）。
3.  生成重心包线并校核是否在许用范围内。

```python
from aircraft_design.weight_balance import WeightBalanceAnalyzer
# ... 实例化 analyzer ...
envelope = analyzer.analyze()
```
