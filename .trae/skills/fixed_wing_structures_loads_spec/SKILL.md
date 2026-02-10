---
name: "fixed_wing_structures_loads_spec"
description: "固定翼结构与载荷方案：载荷因子/突风、弯矩剪力量级、一级定尺寸与结构重量回馈。当需要将结构可行性纳入总体迭代时调用。"
---

# 固定翼结构与载荷方案（Spec）

## 目标

- 在总体设计阶段给出结构载荷与结构重量的一致性接口
- 输出一级结构可行性约束（强度/刚度/屈曲的量级校核，后续细化）

## 与统一入口的字段映射

- 本 Spec 的输入字段应与统一输入 JSON 对齐，并在收敛后阶段 2–7（结构/载荷）中使用：
  - 结构与载荷假设：`structures.*`
  - 几何：来自 `geometry_shape/geometry_detailed` 或闭环输出 `outputs.geometry.*`
  - 重量：来自闭环输出 `outputs.mtow_kg`

## 输入（统一 JSON 视角）

- `structures.n_limit`：设计载荷因子
- `structures.wing_t_c`：翼厚比（或由 `initial_guess.thickness_ratio` 推导）
- `structures.enable_weight_feedback`：是否把结构重量修正回馈到重量闭合
- 其它结构参数：`baseline_struct_frac`、`feedback_gain` 等（用于量级模型）

## 输出

- 关键载荷量级：翼根弯矩/剪力
- 一级结构尺寸建议（量级）
- 结构重量修正建议（回馈重量闭合）
