---
name: "fixed_wing_propulsion_runbook"
description: "执行固定翼推进一级假设检查并输出燃油估算所需参数。当需要把推进参数接入航程与重量闭合时调用。"
---

# 固定翼推进执行（Runbook）

## 目标

- 确保推进输入可用于 Breguet 航程与重量闭合

## 输入检查

- `propulsion.type == prop`：
  - 必需：`sfc_1_s`, `prop_efficiency`
- `propulsion.type == jet`：
  - 必需：`tsfc_1_s`

## 推荐入口

- 一键总体脚本：`scripts/run_fixed_wing_design.py`

