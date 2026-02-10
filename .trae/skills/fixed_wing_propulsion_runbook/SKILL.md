---
name: "fixed_wing_propulsion_runbook"
description: "校核推进一级假设（SFC/TSFC/η）是否可用于航程与重量闭合。当总体闭环需要推进输入或航程/燃油异常时调用。"
---

# 固定翼推进执行（Runbook）

## 角色定位（统一入口）

- 本技能默认由 `fixed_wing_overall_sizing_runbook` 闭环驱动，不建议作为独立入口。
- 单独调用用于检查“推进输入是否缺失/单位是否错误/数量级是否不合理”，避免燃油分数发散。

## 目标

- 确保推进输入可用于 Breguet 航程与重量闭合

## 输入检查

- 螺桨/涡桨（prop）：必需 `sfc_1_s`、`prop_efficiency`
- 喷气（jet）：必需 `tsfc_1_s`

## 常见错误（优先排查）

- `sfc/tsfc` 单位不一致：本仓库倾向使用 `1/s`（例如 `0.8/3600 ≈ 2.22e-4 1/s`）
- 把 `kg/(N·h)` 或 `lb/(lbf·h)` 直接当 `1/s` 用，导致航程/燃油严重异常
- 螺桨效率缺失或填了 >1 的数

## 推荐入口

- 统一入口：`fixed_wing_overall_sizing_runbook`
