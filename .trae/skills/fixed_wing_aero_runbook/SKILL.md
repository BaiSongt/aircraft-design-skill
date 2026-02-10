---
name: "fixed_wing_aero_runbook"
description: "执行固定翼气动一级模型（CD0/e/k、巡航L/D）。当总体闭环需要气动输入或要诊断航程/爬升受阻时调用。"
---

# 固定翼气动执行（Runbook）

## 角色定位（统一入口）

- 本技能默认由 `fixed_wing_overall_sizing_runbook` 闭环驱动，不建议作为独立入口。
- 仅在需要解释/诊断“气动假设如何影响重量闭合与性能余度”时单独调用本 Runbook。

## 当前模型边界

- 极曲线：`CD = CD0 + k * CL^2`
- 诱导项：`k` 由 `AR` 与 `e` 得到（一级估算）
- 巡航点：基于巡航工况与重量/翼面积得到 `CL`，进而估算巡航 `L/D`

## 你该怎么用（在闭环中）

1. 在输入中给出或更新气动假设：`initial_guess.cd0`、`initial_guess.oswald_e`、`initial_guess.aspect_ratio`。
2. 运行总体入口并读取输出目录下的 `design_data.json` 与 `design_report_v2.md`。
3. 若航程/爬升不满足，用下面的“诊断路径”定位是 `cd0`、`e/AR`、还是推进耗油模型导致的。

## 诊断路径（优先级从高到低）

- `cd0` 过大通常直接损害航程与爬升：优先检查外形阻力与构型增量假设
- `e` 偏低会显著增大诱导阻力：优先检查 AR、翼尖与布局干扰
- `cl_max` 决定失速约束上界：与高升力装置策略联动调整
