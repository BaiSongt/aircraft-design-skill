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
- 先完成 Class 1 收敛，再自动进入 Class 2 高级设计

## 入口

- 输入文件：JSON
- 执行脚本：`python -m aircraft_design.run_sizing`

## 流程约束

- 必须先完成 Class 1 收敛，且参数合理时自动进入 Class 2
- GUI 可视化为必要条件，仅在显示错误时才可关闭

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

1. 基于 sizing 输入复制并修改：

```bash
cp ./sizing_input.json ./sizing_input_advanced.json
```

2. 在新文件中补齐首次高级设计字段：
   - `geometry` + `geometry_shape`（含机身与机翼/尾翼）
   - `geometry_constraints`（如允许的最小翼身间距、翼梁厚度等）
   - `openvsp.enabled=true`
   - `uncertainty.enabled=true`

3. 启动 GUI（必要，除非显示错误）：

**注意：** 建议先关闭旧的服务器窗口，或指定新端口以确保加载最新代码。

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
# 方法 A：启动默认服务器
python -m aircraft_design.gui.server

# 方法 B：指定端口启动
python -m aircraft_design.gui.server --port 10001
```

4. 运行（默认 Class 1 收敛后自动进入 Class 2）：

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
# 连接默认端口 9999
python -m aircraft_design.run_sizing sizing_input_advanced.json --project-name AdvancedRun

# 或连接指定端口
python -m aircraft_design.run_sizing sizing_input_advanced.json --project-name AdvancedRun --viz-port 10001
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
