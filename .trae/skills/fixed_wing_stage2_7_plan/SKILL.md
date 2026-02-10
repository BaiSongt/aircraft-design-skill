---
name: "fixed_wing_stage2_7_plan"
description: "规划固定翼阶段2-7功能分解、接口字段与验收标准。当需要扩展阻力分解/推进模型/任务剖面/稳定结构/迭代优化时调用。"
---

# 固定翼阶段2-7规划（Spec）

## 与统一入口的接口关系

- 阶段 2–7 由 `fixed_wing_overall_sizing_runbook` 在“Class I 收敛且结果合理”后自动触发（`aircraft_design.run_sizing` 内部调用扩展阶段）。
- 输出以文件为主，写入 `output/<project>_*/advanced_design_results_*.json` 与 `advanced_design_report.md`。

## 阶段 2：气动阻力分解与构型增量

- 目标：由几何与构型假设生成 `cd0` 与可追溯分解
- 输出：`stage2_aero.cd0`、`stage2_aero.cd0_breakdown` 与分解表
- 验收：报告可解释 `cd0` 来源，且随几何变化趋势合理

## 阶段 3：推进随工况变化

- 目标：提供 `T_avail(h,V)` 或 `P_avail(h,V)` 的一级模型
- 输出：`stage3_propulsion.thrust_available_*` 与余度
- 验收：高空巡航推力衰减合理，约束校核一致

## 阶段 4：任务剖面耗油

- 目标：将燃油分数拆分为 taxi/climb/cruise/descent/reserve 等
- 输出：`stage4_mission.mission_breakdown`
- 验收：分段耗油和总耗油闭合、可追溯

## 阶段 5：稳定与配平

- 目标：输出静稳定裕度与配平量级
- 输出：`stage5_stability.static_margin`、`stage5_stability.trim_tail_cl`
- 验收：随 CG/尾容积变化趋势正确

## 阶段 6：结构与载荷

- 目标：估算翼根弯矩剪力与结构重量回馈接口
- 输出：`stage6_structures.*`（载荷量级、结构重量回馈）
- 验收：随翼展/载荷因子变化趋势正确

## 阶段 7：迭代与敏感性/优化

- 目标：基于约束过滤，搜索可行解并给出推荐设计点
- 输出：`stage7_optimization` 与候选集（如启用优化）
- 验收：能在给定网格内找到可行最优解并输出报告摘要
