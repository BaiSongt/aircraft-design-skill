---
name: "fixed_wing_overall_sizing_runbook"
description: "执行固定翼总体设计闭环计算并输出 results.json/report.md 以及交互式图表。当需要从输入需求一键得到可计算方案、详细报告与可视化结果时调用。"
---

# Fixed Wing Overall Sizing Runbook

此技能用于执行固定翼飞机 Class I 总体设计闭环流程。它将调用 `aircraft_design/run_sizing.py` 脚本，基于输入需求进行迭代计算，直到 MTOW 收敛，并生成符合标准模板的报告及交互式图表。

## 适用场景
*   用户提供了一组设计需求（如航程、载荷、速度），希望快速得到飞机总体参数。
*   用户希望验证当前设计代码是否能针对特定需求收敛。
*   需要生成总体设计报告 (`report.md`) 和可视化分析 (`interactive_charts.html`)。

## 执行步骤

### 1. 准备输入文件 (`sizing_input.json`)

首先，根据用户提供的信息构建 JSON 输入文件。如果用户未提供某些字段，使用以下**轻型战斗机默认值**：

```json
{
  "requirements": {
    "range_m": 2000000.0,
    "payload_kg": 1000.0,
    "cruise_mach": 0.8,
    "cruise_altitude_m": 11000.0,
    "takeoff_distance_m": 1000.0,
    "landing_distance_m": 1000.0,
    "max_load_factor": 7.33,
    "sustained_turn_g": 2.0,
    "service_ceiling_m": 15000.0
  },
  "initial_guess": {
    "thrust_to_weight": 0.6,
    "wing_loading_pa": 3000.0,
    "aspect_ratio": 3.5,
    "sweep_deg": 45.0,
    "taper_ratio": 0.3,
    "thickness_ratio": 0.08,
    "sfc_cruise_1_s": 0.000222, 
    "cd0": 0.02,
    "oswald_e": 0.8
  }
}
```

*注意：`sfc_cruise_1_s` = 0.8 / 3600 ≈ 0.000222*

使用 `Write` 工具创建 `sizing_input.json` 文件。

### 2. 执行 Sizing Loop

使用 `RunCommand` 工具执行以下命令：

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 aircraft_design/run_sizing.py sizing_input.json --output results.json --report report.md
```

### 3. 检查结果

1.  **检查退出码**：
    *   `0`: 成功且收敛。
    *   `2`: 运行完成但**未收敛**（需警告用户）。
    *   `1`: 发生错误（需调试）。

2.  **读取报告**：
    使用 `Read` 工具读取生成的 `report.md` 文件内容。

3.  **反馈用户**：
    将 `design_report.md` 的核心内容（MTOW、T/W、W/S、关键重量分解、操稳特性摘要）总结给用户，并提示用户可以在输出目录查看交互式图表 `interactive_charts.html`。
