---
name: "fixed_wing_advanced_overall_runbook"
description: "执行包含高级分析与机身几何的固定翼总体设计流程。初步分析收敛后调用，含高级分析、几何约束与机身外形。"
stage: "entry"
code_module: "aircraft_design/run_sizing.py, aircraft_design/class2_preliminary/advanced_design.py"
dependencies:
  - "fixed_wing_overall_sizing_runbook"
  - "fixed_wing_shape_parametric_runbook"
  - "fixed_wing_geometry_integrated_spec"
---

# 固定翼高级总体设计执行步骤（Runbook）

## 角色定位（统一入口）

- 本技能不是第二套入口；计算入口固定为 `fixed_wing_overall_sizing_runbook`（`python -m aircraft_design.run_sizing`）。
- 本 Runbook 说明如何在同一份输入 JSON 中补齐几何与约束字段，让总体入口在收敛后输出：
  - 阶段 2–7 扩展分析结果（advanced_design_results / advanced_design_report）
  - 几何一致性检查（geometry_constraints）
  - 外形资产（OpenVSP 脚本、OBJ、交互图表）

## 目标

首次设计即包含：
- 机身外形/翼身布局参与
- 几何高级分析（几何一致性校核、面积分布等）
- 约束/重量/气动/性能/稳定/结构/推进的一体化输出
- 先完成 Class 1 收敛，再自动进入 Class 2 高级设计

## 必要输入补强（在首次方案中加入）

1. `geometry` 与 `geometry_shape`
   - `geometry.fuselage_length_m`、`geometry.fuselage_diameter_m`
   - `geometry_shape.fuselage.axis.length_m`
   - `geometry_shape.fuselage.profile`（控制点或半径）
2. `geometry_shape.wing.planform`
   - 确保翼展弦比/翼面积可由 `sizing` 或 `geometry_shape` 推导
3. `geometry_constraints`（可选但推荐）
   - 用于燃油容积/展弦比等几何一致性校核，结果会写入 `advanced_design_results_*.json`

## 快速步骤

1. 在输入 JSON 的 `requirements`、`initial_guess` 基础上，补齐 `geometry_shape` 与（可选）`geometry_constraints`。
2. 可选启动可视化（不启动则用 `--no-viz` 纯计算）：

```bash
python -m aircraft_design.gui.server
```

3. 运行（Class I 收敛后自动进入阶段 2–7 扩展分析）：

```bash
python -m aircraft_design.run_sizing sizing_input_advanced.json --project-name AdvancedRun

# 纯计算（不启用 GUI）
python -m aircraft_design.run_sizing sizing_input_advanced.json --project-name AdvancedRun --no-viz
```

## 输出检查

- `output/AdvancedRun_*/design_data.json`：总体设计结果
- `output/AdvancedRun_*/design_report_v2.md`：报告
- `output/AdvancedRun_*/advanced_design_results_*.json`：高级设计结果
- `output/AdvancedRun_*/advanced_design_report.md`：高级设计报告
- `output/AdvancedRun_*/model.vspscript`：OpenVSP 脚本
- `output/AdvancedRun_*/interactive_charts.html`：交互图表

## GUI 显示前置条件

- GUI Web3D 优先依赖 `geometry_shape` 或含 `vertices/faces` 的 mesh 字段
- 若仅有参数化字段（如 `aspect_ratio`、`s_wing`），则需要通过 `geometry_shape_from_inputs` 生成外形才能稳定显示

## GUI 消息契约示例

更新消息（包含几何）：

```json
{
  "type": "update",
  "iteration": 0,
  "mtow": 2784.0,
  "error": 0.0,
  "geometry": {
    "fuselage_length_m": 4.5,
    "fuselage_diameter_m": 0.5,
    "s_wing": 9.1,
    "aspect_ratio": 3.5,
    "sweep_deg": 45.0,
    "taper_ratio": 0.3
  },
  "__protocol__": "json",
  "__version__": 1
}
```

报告消息（用于加载报告与图像）：

```json
{
  "type": "report_generated",
  "path": "output/AdvancedRun_20260208_153139"
}
```

## 迭代建议

- 机身外形不合理：调整 `geometry_shape.fuselage.profile` 控制点与长度/半径
- 约束不过：先改 `sizing`（W/S、AR、T/W），再优化 `aero` 与 `propulsion`
- 高级几何警告：补齐或修正 `geometry_constraints`
