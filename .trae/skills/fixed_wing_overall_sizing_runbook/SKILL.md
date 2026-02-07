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

### 2. 执行 Sizing Loop（带可视化）

Sizing Loop 内置了自动可视化功能。默认情况下，它会自动检测并启动可视化服务器，在独立窗口中显示收敛曲线、约束图和飞机几何预览。

**基本用法**：
使用 `RunCommand` 工具执行以下命令：

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m aircraft_design.run_sizing sizing_input.json --project-name MyDesign
```

**可选参数**：
*   `--no-viz`: 如果不需要实时可视化（例如在纯后台模式运行），可添加此参数关闭图形界面。

**可视化交互说明**：
*   **自动启动**：脚本运行时会自动弹出一个 3D 可视化窗口（无需手动开启服务器）。
*   **监控**：用户可以实时观察 MTOW 收敛情况、约束分析图以及飞机的 3D 几何变化。
*   **结束**：脚本执行完成后会自动退出，但可视化窗口会**保持打开**状态，以便用户继续查看结果。用户可随时手动关闭窗口。

### 3. 检查结果


1.  **检查退出码**：
    *   `0`: 成功且收敛。
    *   `2`: 运行完成但**未收敛**（需警告用户）。
    *   `1`: 发生错误（需调试）。

2.  **定位输出目录**：
    输出位于 `output/` 目录下以 `MyDesign_` 开头的时间戳文件夹中。使用 `LS` 工具找到最新的文件夹。

3.  **读取报告**：
    使用 `Read` 工具读取生成的 `design_report.md` 文件内容。

4.  **反馈用户**：
    将 `design_report.md` 的核心内容（MTOW、T/W、W/S、关键重量分解、操稳特性摘要）总结给用户，并提示用户可以在输出目录查看交互式图表 `interactive_charts.html`。
