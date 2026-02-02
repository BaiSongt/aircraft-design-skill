---
name: "fixed_wing_overall_sizing_spec"
description: "生成固定翼总体设计方案（需求→约束→设计点→初步尺寸→重量/性能闭合）。当需要给出固定翼总体方案、关键参数范围与决策依据时调用。"
---

# 固定翼总体设计方案（Spec）

## 目的

- 将固定翼总体设计流程标准化输出为可迭代方案
- 给出关键设计变量的推荐取值、约束关系与余度检查

## 输入

使用统一 JSON 输入，建议字段：

- `mission`: 航程、巡航高度/速度、失速速度等
- `payload`, `crew`: 载荷与机组重量
- `aero`: 初猜气动（`cd0`, `e`, `cl_max`）
- `sizing`: 初猜设计变量（`wing_loading_pa`, `aspect_ratio`, `thrust_to_weight`）
- `weights`: 空重统计模型参数与燃油储备
- `propulsion`: 推进类型与耗油/效率模型

## 输出

方案输出建议包含：

- 设计点：`wing_loading_pa`、`thrust_to_weight`
- 主尺度：`S`、`b`、`\bar{c}`
- 气动模型：`cd0`、`k`、巡航 `L/D`
- 重量闭合：`W0`、`We`、`Wf`
- 关键性能余度：巡航所需推力、爬升率

## 关键规则

- 设计点必须满足失速约束上界：`(W/S) <= q * CLmax`
- 重量、气动、性能必须在同一组几何与工况假设下闭合

