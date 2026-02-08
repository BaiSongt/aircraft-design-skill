---
name: "fixed_wing_overall_sizing_runbook"
description: "执行固定翼总体设计闭环计算并输出 results.json/report.md 以及 PySide6 可视化 App 数据。每次都要调用，能从输入需求一键得到可计算方案、详细报告与可视化结果。"
---

# Fixed Wing Overall Sizing Runbook

此技能用于执行固定翼飞机 Class I 总体设计闭环流程。它将调用 `aircraft_design/run_sizing.py` 脚本，基于输入需求进行迭代计算，直到 MTOW 收敛。Class I 收敛且参数合理时自动进入 Class II 高级设计，并生成标准模板报告与 PySide6 可视化 App 需要的实时数据。

## 适用场景
*   用户提供了一组设计需求（如航程、载荷、速度），希望快速得到飞机总体参数。
*   用户希望验证当前设计代码是否能针对特定需求收敛。
*   需要生成总体设计报告 (`report.md`) 并在 PySide6 可视化 App 中查看实时迭代过程。

## 入口与需求模板（必须先生成提示词）

当用户给出需求时，先按模板补齐信息并生成“需求提示词”，再进入后续步骤。

**需求模板**：

```
项目名称：
任务类型：军用/民用/无人机/通航/客运/货运
任务指标：
  航程 range_m：
  载荷 payload_kg：
  巡航马赫 cruise_mach：
  巡航高度 cruise_altitude_m：
  起飞距离 takeoff_distance_m：
  着陆距离 landing_distance_m：
约束与性能：
  最大过载 max_load_factor：
  持续盘旋过载 sustained_turn_g：
  实用升限 service_ceiling_m：
推进与能耗假设：
  推进类型：jet/prop
  sfc_cruise_1_s：
  cd0：
  oswald_e：
几何与布局偏好：
  展弦比 aspect_ratio：
  后掠角 sweep_deg：
  梯形比 taper_ratio：
  厚度比 thickness_ratio：
  尾翼布局 tail_layout：conventional/t_tail/v_tail/twin_fin
可视化与几何输入：
  geometry_shape：有/无
  mesh：有/无
输出偏好：
  报告：标准/扩展
  GUI：启用/禁用
风险与不确定性：
  允许参数浮动：是/否
```

**提示词生成规则**：
1. 将用户输入映射到模板字段；缺失字段用“默认值”标记并说明将采用轻型战斗机默认值。
2. 输出“需求提示词”，必须包含以下结构化段落：
   - 项目与任务类型
   - 任务指标（带单位）
   - 约束与性能指标
   - 推进与能耗假设
   - 几何与布局偏好
   - 可视化与几何输入状态
   - 输出偏好与风险声明
3. 提示词末尾追加一句：已生成模板化需求，将进入 sizing_input.json 构建与总体设计闭环流程。

## 执行步骤

### 0. 环境检查与虚拟环境准备

在运行设计流程前，先完成虚拟环境创建与依赖检查，确认无误后再进行后续步骤。

**创建并进入虚拟环境**：

```bash
python3 -m venv venv
source venv/bin/activate
```

**安装与检查依赖**：

```bash
pip install -r requirements.txt
python -c "import PySide6, numpy, scipy, pyvista, pyvistaqt; import PySide6.QtWebEngineWidgets"
```

若依赖检查通过，继续后续步骤；如有错误，先修复依赖问题。

### 1. 准备输入文件 (`sizing_input.json`)

首先，根据用户提供的信息构建 JSON 输入文件。如果用户未提供某些字段，使用以下**轻型战斗机默认值**：

```json
{
  "requirements": {
    "range_m": 2000000.0,
    "payload_kg": 1000.0,
    "cruise_mach": 0.8,
    "cruise_altitude_m": 11000.0,
    "assumed_climb_rate_m_s": 50.0,
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

### 2. 启动可视化服务器（可选，推荐）

如果需要实时查看迭代曲线和 3D 模型，请在**另一个独立的终端**中启动可视化服务器。

**注意：** 如果之前已经启动了 `aircraft_design.gui.server`，请先关闭它（Ctrl+C），或者在新终端中使用不同的端口，以确保加载最新的代码逻辑。

```bash
# 方法 A：启动默认服务器（推荐先关闭旧窗口）
python -m aircraft_design.gui.server

# 方法 B：指定端口启动（避免端口冲突）
python -m aircraft_design.gui.server --port 10001
```

等待服务器启动并显示 "Visualization Server listening on localhost:..." 后，保持该窗口开启。

### 3. 执行设计闭环

在主终端中运行 `run_sizing.py`。

**基本运行**（自动尝试连接默认端口 9999）：

```bash
python -m aircraft_design.run_sizing sizing_input.json --project-name "ProjectName"
```

**指定端口运行**（如果服务器使用了非默认端口）：

```bash
python -m aircraft_design.run_sizing sizing_input.json --project-name "ProjectName" --viz-port 10001
```

**无可视化运行**（纯计算模式）：

```bash
python -m aircraft_design.run_sizing sizing_input.json --no-viz
```

**可视化交互说明**：
*   **先启动服务**：未先启动 `aircraft_design.gui.server` 会导致可视化连接失败，脚本会退出。
*   **监控**：用户可以实时观察 MTOW 收敛情况、约束分析图以及飞机的 3D 几何变化。
*   **结束**：脚本执行完成后可视化窗口仍保持打开，用户可手动关闭。
*   **Web3D 前置条件**：为了稳定显示 3D，输入应包含 `geometry_shape` 或 mesh（`vertices`/`faces`）数据；仅参数化字段时需要由 `geometry_shape_from_inputs` 推导几何。
*   **流程约束**：必须先完成 Class I 收敛并参数合理，才会自动进入 Class II 高级设计。

**消息示例**：

更新消息（含几何）：

```json
{
  "type": "update",
  "iteration": 5,
  "mtow": 4800.0,
  "error": 0.02,
  "geometry": {
    "fuselage_length_m": 6.8,
    "fuselage_diameter_m": 0.9,
    "s_wing": 16.0,
    "aspect_ratio": 6.0,
    "sweep_deg": 20.0,
    "taper_ratio": 0.4
  },
  "__protocol__": "json",
  "__version__": 1
}
```

约束消息：

```json
{
  "type": "constraints",
  "data": {"stall": {"margin": 0.12}},
  "design_point": {"wing_loading_pa": 3200, "thrust_to_weight": 0.42}
}
```

### 4. 未收敛时的处理指引（必须给出）

1.  **固定迭代上限输出**：读取 `output/<project>_*/design_data.json`，使用最后一次迭代的 MTOW、Wf、We 作为“当前可行估计”反馈。
2.  **调整初猜并重跑**：
    *   提高 `thrust_to_weight` 或降低 `wing_loading_pa`，优先保证推力余度为正。
    *   如果燃油分数过高，降低 `cruise_mach` 或调整 `sfc_cruise_1_s` 到合理范围。
    *   收敛不稳时，先缩短 `range_m` 做可行性验证，再逐步拉高。
3.  **保存诊断**：提示用户查看 `design_report_v2.md` 和 `design_data.json` 的迭代曲线与重量分解，定位发散来源（推进、结构或燃油）。

### 5. 检查结果


1.  **检查退出码**：
    *   `0`: 成功且收敛。
    *   `2`: 运行完成但**未收敛**（需警告用户）。
    *   `1`: 发生错误（需调试）。

2.  **定位输出目录**：
    输出位于 `output/` 目录下以 `MyDesign_` 开头的时间戳文件夹中。使用 `LS` 工具找到最新的文件夹。

3.  **读取报告**：
    使用 `Read` 工具读取生成的 `design_report_v2.md` 文件内容。

4.  **反馈用户**：
    将 `design_report_v2.md` 的核心内容（MTOW、T/W、W/S、关键重量分解、操稳特性摘要）总结给用户，并提示用户在可视化 App 中查看迭代与约束。
