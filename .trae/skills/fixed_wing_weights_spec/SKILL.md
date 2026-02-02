---
name: "fixed_wing_weights_spec"
description: "固定翼重量方案（Class I）：空重统计模型 + 航程燃油估算 + MTOW 迭代闭合。当需要建立重量闭合与敏感性分析时调用。"
---

# 固定翼重量方案（Spec）

## 目标

- 在总体设计早期实现 MTOW（W0）快速闭合
- 输出空重、燃油重量与闭合迭代信息，为性能与结构提供一致重量

## 输入

- 载荷/机组重量
- 空重模型参数：`We = a * W0^b`
- 航程燃油估算：Breguet（喷气/螺桨）
- 储备油分数：`reserve_fraction`

## 输出

- `w0_kg`: MTOW
- `we_kg`: 空重
- `wf_kg`: 燃油
- `fuel_fraction_total`: 总燃油分数（含储备）
- `converged`, `iterations`: 闭合信息

