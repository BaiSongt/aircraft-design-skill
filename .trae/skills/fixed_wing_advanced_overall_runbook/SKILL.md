---
name: "fixed_wing_advanced_overall_runbook"
description: "执行包含高级分析与机身几何的固定翼总体设计流程。用户要求首次方案就含高级分析、几何约束与机身外形时调用。"
---

# 固定翼高级总体设计执行步骤（Runbook）

## 目标

首次设计即包含：
- 机身外形/翼身布局参与
- 几何高级分析（几何一致性校核、面积分布等）
- 约束/重量/气动/性能/稳定/结构/推进的一体化输出

## 入口

- 输入文件：JSON
- 执行脚本：`scripts/run_fixed_wing_design.py`

## 必要输入补强（在首次方案中加入）

1. `geometry` 与 `geometry_shape`
   - `geometry.fuselage_length_m`、`geometry.fuselage_diameter_m`
   - `geometry_shape.fuselage.axis.length_m`
   - `geometry_shape.fuselage.profile`（控制点或半径）
2. `geometry_parametric` 或 `geometry_shape.wing.planform`
   - 确保翼展弦比/翼面积可由 `sizing` 或 `geometry_shape` 推导
3. `geometry_constraints`（可选但推荐）
   - 用于几何一致性/约束校核输出到 `advanced_shape_results.json`
4. `openvsp`
   - `enabled: true` 以生成 OpenVSP 脚本
5. `uncertainty`
   - `enabled: true` 以输出不确定性敏感性结果

## 快速步骤

1. 基于示例输入复制并修改：

```powershell
copy .\examples\fixed_wing_ga_single.json .\examples\fixed_wing_advanced_first.json
```

2. 在新文件中补齐首次高级设计字段：
   - `geometry` + `geometry_shape`（含机身与机翼/尾翼）
   - `geometry_constraints`（如允许的最小翼身间距、翼梁厚度等）
   - `openvsp.enabled=true`
   - `uncertainty.enabled=true`

3. 运行：

```powershell
python .\scripts\run_fixed_wing_design.py .\examples\fixed_wing_advanced_first.json
```

## 输出检查

- `out/results/results.json`：总体设计结果
- `out/report/report.md`：报告
- `out/geometry/advanced_shape_results.json`：高级几何分析结果
- `out/report/area_rule_report.md`：面积分布报告
- `out/openvsp/openvsp_advanced.py`：OpenVSP 脚本
- `out/mesh/geometry_mesh.json`：三维网格

## 迭代建议

- 机身外形不合理：调整 `geometry_shape.fuselage.profile` 控制点与长度/半径
- 约束不过：先改 `sizing`（W/S、AR、T/W），再优化 `aero` 与 `propulsion`
- 高级几何警告：补齐或修正 `geometry_constraints`
