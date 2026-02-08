---
name: "fixed_wing_overall_sizing_runbook"
description: "执行固定翼总体设计闭环计算并输出 results.json/report.md 以及 PySide6 可视化 App 数据。当需要从输入需求一键得到可计算方案、详细报告与可视化结果时调用。"
---

# Fixed Wing Overall Sizing Runbook

此技能用于执行固定翼飞机 Class I 总体设计闭环流程。它将调用 `aircraft_design/run_sizing.py` 脚本，基于输入需求进行迭代计算，直到 MTOW 收敛，并生成符合标准模板的报告及 PySide6 可视化 App 需要的实时数据。

## 适用场景
*   用户提供了一组设计需求（如航程、载荷、速度），希望快速得到飞机总体参数。
*   用户希望验证当前设计代码是否能针对特定需求收敛。
*   需要生成总体设计报告 (`report.md`) 并在 PySide6 可视化 App 中查看实时迭代过程。

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

### 2. 启动 PySide6 可视化服务（必须在设计前启动）

可视化服务必须先启动，Sizing Loop 仅负责连接已有服务并推送数据。

**启动服务**：
在单独终端中执行以下命令：

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m aircraft_design.gui.server
```

保持可视化窗口运行，然后再执行设计流程。

### 3. 执行 Sizing Loop（连接可视化）

**基本用法**：
使用 `RunCommand` 工具执行以下命令：

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m aircraft_design.run_sizing sizing_input.json --project-name MyDesign
```

**可选参数**：
*   `--no-viz`: 如果不需要实时可视化（例如在纯后台模式运行），可添加此参数关闭图形界面。

**可视化交互说明**：
*   **先启动服务**：未先启动 `aircraft_design.gui.server` 会导致可视化连接失败，脚本会退出。
*   **监控**：用户可以实时观察 MTOW 收敛情况、约束分析图以及飞机的 3D 几何变化。
*   **结束**：脚本执行完成后可视化窗口仍保持打开，用户可手动关闭。

### 4. 未收敛时的处理指引（必须给出）

1.  **固定迭代上限输出**：读取 `output/<project>_*/design_data.json`，使用最后一次迭代的 MTOW、Wf、We 作为“当前可行估计”反馈。
2.  **调整初猜并重跑**：
    *   提高 `thrust_to_weight` 或降低 `wing_loading_pa`，优先保证推力余度为正。
    *   如果燃油分数过高，降低 `cruise_mach` 或调整 `sfc_cruise_1_s` 到合理范围。
    *   收敛不稳时，先缩短 `range_m` 做可行性验证，再逐步拉高。
3.  **保存诊断**：提示用户查看 `design_report.md` 和 `design_data.json` 的迭代曲线与重量分解，定位发散来源（推进、结构或燃油）。

### 5. 检查结果


1.  **检查退出码**：
    *   `0`: 成功且收敛。
    *   `2`: 运行完成但**未收敛**（需警告用户）。
    *   `1`: 发生错误（需调试）。

2.  **定位输出目录**：
    输出位于 `output/` 目录下以 `MyDesign_` 开头的时间戳文件夹中。使用 `LS` 工具找到最新的文件夹。

3.  **读取报告**：
    使用 `Read` 工具读取生成的 `design_report.md` 文件内容。

4.  **反馈用户**：
    将 `design_report.md` 的核心内容（MTOW、T/W、W/S、关键重量分解、操稳特性摘要）总结给用户，并提示用户在可视化 App 中查看迭代与约束。
