---
name: "fixed_wing_systems_spec"
description: "定义固定翼机载系统详细配置（重量/位置/技术因子）。当用户需要指定具体系统参数或覆盖重量估算默认值时调用。"
stage: "cross_stage"
code_module: "aircraft_design/class2_preliminary/weights_system.py"
dependencies:
  - "fixed_wing_weights_spec"
---

# 固定翼机载系统配置（Spec）

本 Spec 定义统一输入 JSON 中 `systems` 字段的配置方式，用于在总体收敛后生成更细粒度的系统重量与（可选）重心信息。

## 与统一入口的接口关系

- 推荐入口：`fixed_wing_overall_sizing_runbook`（`python -m aircraft_design.run_sizing`）
- 输出落盘：`output/<project>_*/design_data.json.outputs.systems`

## 1. 系统参数化输入架构

系统配置作为 `systems` 字段存在于总体输入 JSON 中。

```json
{
  "systems": {
    "landing_gear": {
      "type": "retractable",
      "weight_fraction_override": 0.05,
      "main_gear_location_x_m": 4.5,
      "nose_gear_location_x_m": 0.8
    },
    "avionics": {
      "weight_kg": 120.0,
      "location_x_m": 1.5,
      "power_w": 500.0
    },
    "flight_controls": {
      "type": "mechanical",
      "tech_factor": 0.9
    },
    "furnishings": {
      "weight_kg": 80.0
    },
    "environmental_control": {
        "present": true,
        "weight_kg": 30.0
    },
    "anti_ice": {
        "present": false
    }
  }
}
```

## 2. 约定与行为

- `systems` 用于覆盖或修正系统重量估算的默认假设（例如航电重量、起落架构型等）。
- 未提供的子系统项将采用默认估算逻辑补齐（输出中可追溯到分组）。

## 3. 输出验证

- 确保所有自定义输入的系统都被正确归类（例如 Structure / Systems / Propulsion）。
- 检查重心 (CG) 计算是否使用了用户提供的坐标。
- 验证总重是否正确累加。
