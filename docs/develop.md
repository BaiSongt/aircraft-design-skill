# 飞机设计 Skill 系统分析与任务规划

> 本文档基于对 `.trae/skills/` 的全面审查生成，旨在规划从“概念验证”迈向“工程实用”的演进路径。

## 1. 系统架构现状分析

当前系统是一个由 LLM 驱动的 **混合 Class I/II 飞机概念设计框架**。其核心架构分为三层：

### 1.1 编排层 (The Orchestration Layer)
*   **设计理念**：“Spec-First” 开发模式。每个能力（Skill）都由严格的输入/输出契约（JSON）和执行手册（Runbook）定义。
*   **数据流**：`用户需求` -> `sizing_input.json` -> `总体迭代闭环` -> `results.json` -> `报告/可视化`。
*   **核心 Skill**：
    *   `fixed_wing_overall_sizing`: 主入口，管理全生命周期。
    *   `fixed_wing_design_loop`: 迭代求解器，确保 MTOW 收敛。
    *   `fixed_wing_advanced_overall`: 连接高保真分析（几何、详细报告）的桥梁。

### 1.2 物理核心层 (The Physics Core - Class I/II)
目前实现了教科书级（Raymer/Roskam）的经验方法，并逐步向 Class II 演进：
*   **气动 (`aero_spec`)**：
    *   实现了基于几何湿面积的寄生阻力分解 (`aero_drag_buildup`)，替代了纯猜测的 $C_{D0}$。
    *   仍使用抛物线极曲线 ($C_D = C_{D0} + k C_L^2$)。
*   **重量 (`weights_spec`)**：
    *   **已升级到 Class II**：实现了基于部件（机翼、机身、起落架等）的半解析重量估算公式。
    *   **系统架构**：支持详细的子系统（航电、ECS、防冰等）配置、重量与功耗 (`power_w`) 追踪。
    *   仍保留 Breguet 航程公式用于初步燃油估算。
*   **性能 (`performance_spec`)**：设计点性能校核（巡航推力、爬升率、失速速度）。
*   **约束 (`constraints_spec`)**：$T/W$ 与 $W/S$ 约束分析（失速、起降、巡航、爬升）。

### 1.3 几何与可视化层 (The Geometry Layer - Class I.5)
这是相对于典型 Class I 代码最先进的部分，**已完成深度参数化**：
*   **参数化几何 (`shape_parametric_spec`)**：使用工程参数定义外形 ($AR, \lambda, \Lambda, L_{fuse}, D_{fuse}$)。
*   **详细几何 (`shape_detail_spec`)**：
    *   支持详细翼型定义（NACA 4系列）、扭转角分布。
    *   实现了 V 尾 (V-Tail) 的非对称网格生成与控制。
    *   实现了精确的湿面积 ($S_{wet}$) 计算，反哺气动阻力模型。
    *   支持将系统布局（Systems Layout）注入几何对象。
*   **Web 3D**：基于 PySide6 + Three.js 的实时可视化（待进一步集成生成的详细网格）。
*   **OpenVSP 集成**：支持生成 `.vspscript` 用于外部高保真分析。

---

## 2. 差距分析 (Gap Analysis)

基于 `fixed_wing_stage2_7_plan` 和当前实现，识别出以下关键差距：

### 2.1 关键逻辑缺失 (Planned but not implemented)
*   **推进图谱 (Propulsion Maps - Stage 3)**：推力目前被视为常数或简单缩放。缺失 $T_{avail} = f(h, M, \text{throttle})$ 图谱，无法准确评估非设计点性能。
*   **任务仿真 (Mission Analysis - Stage 4)**：燃油计算仅使用简单分数法。缺失基于时间步长的任务仿真（滑行 -> 起飞 -> 爬升 -> 巡航 -> 下滑 -> 盘旋）。
*   **稳定与配平 (Stability & Trim - Stage 5)**：`stability_control_spec` 仅关注尾容量系数。缺失基于详细几何的静稳定裕度计算 ($X_{np} - X_{cg}$) 和配平阻力估算。

### 2.2 系统工程缺失 (Not in current plan)
*   **成本分析**：无 LCC（全寿命周期成本）或 DOC（直接运行成本）模型。
*   **内部布置**：虽然有了系统重量和位置，但尚未进行可视化的内部体积校核（燃油箱容积 vs 需油量，起落架收放空间）。

### 2.3 优化能力缺失
*   **自动权衡研究 (Trade Studies)**：`design_loop` 仅收敛*单个*点。无法自动扫描 $W/S$ 和 $T/W$ 生成“地毯图”以寻找全局最优解。

---

## 3. 近期成就 (Recent Achievements)

*   **[Done] 全流程高级设计闭环 (Stage 2-7)**：成功打通了从基础尺寸到高级分析的完整链路，生成了包含七个阶段的详细设计报告。
    *   **气动 (Stage 2)**：集成了波阻 (Wave Drag) 与详细部件阻力分解。
    *   **推进 (Stage 3)**：实现了推力/耗油率随高度速度变化的 Map 模型。
    *   **任务 (Stage 4)**：初步实现了基于任务段的燃油分解（*需调试巡航油耗逻辑*）。
    *   **稳定 (Stage 5)**：实现了基于详细几何的静稳定裕度计算与配平分析。
    *   **结构 (Stage 6)**：实现了翼根载荷估算与结构重量校核。
    *   **优化 (Stage 7)**：实现了基于设计变量（展弦比、后掠角等）的灵敏度分析与局部寻优。
*   **[Done] 高级气动建模 (Wave Drag)**：在 `aero_drag_buildup` 中实现了基于 Sears-Haack 理论的波阻估算，支持跨音速/超音速 ($M > 1.0$) 飞机设计。
*   **[Done] 推进系统图谱 (Propulsion Maps)**：实现了 `thrust_map` 和 `sfc_map` 的双线性插值支持，允许导入 $T = f(M, h)$ 发动机数据。
*   **[Done] 系统架构参数化**：实现了 `SystemComponent` 和 `SystemGroup`，支持用户覆盖子系统重量、位置及技术因子。
*   **[Done] Class II 重量估算**：集成了 Raymer/Roskam 经验公式，根据几何参数估算结构与系统重量。

## 3.1 当前已知问题与调试重点 (Current Issues & Focus)

基于最新设计迭代 (2026-02-08) 发现的问题：
1.  **[已解决] 推力不足 (Thrust Deficit)**：通过调整推重比 ($T/W=0.8$) 和翼载 ($W/S=3500$)，巡航推力余度已达 30.7%，爬升余度 47.1%。
2.  **[已解决] 巡航油耗异常**：修复了 `mission.py` 中 `fuel_flow_n_s` 缺省参数导致的计算错误，现显示正常的巡航油耗 (127.3 kg)。
3.  **[已解决] 诱导阻力异常高**：之前报告显示 $C_{Di}$ 占比 > 75% 系两个原因导致：(1) `run_sizing.py` 中硬编码了 $C_L=0.6$，已修复为动态计算（实际 $C_L \approx 0.06$）；(2) 报告生成脚本硬编码了旧结论。现已修复，实际诱导阻力占比约 3.5%。
4.  **[已解决] 静稳定度过大**：之前报告硬编码显示 SM > 30%。实际计算结果为 10.76% MAC，处于合理范围 (5-15%)。报告生成逻辑已修复。
5.  **[新发现] 波阻主导**：在 M=2.0 时，波阻占总零升阻力的 ~60%。这是一个物理上合理的现象，但提示可以通过优化后掠角（建议 50° vs 当前 65°）或减小厚度比来进一步降低阻力。
6.  **[优化成功] 波阻降低**：通过将后掠角从 45° 增加至 60° 并减小厚度比 (0.08 -> 0.05)，波阻系数降低了约 31%，总阻力降低约 19%。
7.  **[Bug修复] 爬升燃油异常**：修复了 `run_sizing.py` 中未传递 `assumed_climb_rate_m_s` 导致爬升率默认为 3m/s 从而耗尽燃油的问题。

---

## 4. 详细任务规划 (Detailed Roadmap)

### 阶段 1：深化物理模型 (Phase 1: Deepen Physics)
**目标**：用基于几何的物理估算替代用户猜测，实现“所见即所算”。

#### 任务 1.1：高级气动建模 (`fixed_wing_aero_buildup`) [大部分完成]
*   **状态**：已实现 $C_{D0}$ 叠加逻辑和波阻 (Wave Drag) 估算。
*   **待办**：
    1.  完善雷诺数 $Re$ 和摩擦系数 $C_f$ 计算器（目前可能使用了简化值）。
    2.  输出更详细的气动数据报告（极曲线图表等）。

#### 任务 1.2：推进系统图谱 (`fixed_wing_propulsion_map`) [已完成]
*   **功能**：实现推力和耗油率随高度、速度变化的详细模型。
*   **状态**：已在 `propulsion.py` 中实现基于 Map 的插值，并支持 Mach 4 设计。
*   **已实现**：
    1.  通用高度/速度双线性插值。
    2.  支持导入数据表。
    3.  已在性能计算中替换简单估算。

#### 任务 1.3：稳定性初探 (`fixed_wing_stability_analysis`) [中优先级]
*   **功能**：评估静稳定裕度。
*   **输入**：详细机翼/尾翼几何（已就绪），重心位置（已就绪）。
*   **输出**：全机气动中心 $X_{np}$，静稳定裕度 $SM$。
*   **步骤**：
    1.  计算平均气动弦长 (MAC) 及其位置。
    2.  估算机身对气动中心的修正。
    3.  计算 $SM = (X_{np} - X_{cg}) / MAC$。

---

### 阶段 2：可视化与报告 (Phase 2: Visualization & Reporting)
**目标**：将计算结果转化为直观的设计资产。

#### 任务 2.1：3D 资产生成 (`fixed_wing_visualization`) [高优先级]
*   **功能**：生成通用 3D 格式文件。
*   **输出**：GLB/OBJ 文件（包含机身、机翼、尾翼及关键内部系统占位符）。
*   **用途**：用于 Web 前端展示或导入 CAD 软件。

#### 任务 2.2：详细设计报告
*   **功能**：生成包含三视图、重量分解饼图、阻力分解图的 HTML/PDF 报告。

---

### 阶段 3：系统与任务仿真 (Phase 3: System & Mission)
**目标**：从“飞行物”进化为“具备作战/运营能力的飞机”。

#### 任务 2.1：任务剖面仿真 (`fixed_wing_mission_sim`)
*   **功能**：基于时间步长的多阶段任务积分。
*   **输入**：详细任务剖面（高度、速度、距离/时间序列）。
*   **输出**：精确的燃油消耗量，任务历程图表。
*   **步骤**：
    1.  定义标准任务段（Climb, Cruise, Loiter, Descent）。
    2.  实现 ODE 积分器求解 $dW/dt = -SFC \cdot T$。
    3.  支持多段巡航和备降任务。

#### 任务 2.2：成本模型 (`fixed_wing_cost`)
*   **功能**：估算飞机的研发与制造成本。
*   **模型**：DAPCA IV 或类似统计模型。
*   **输出**：单机价格，研发总投入。

---

### 阶段 3：优化与综合 (Phase 3: Optimization & MDO)
**目标**：实现自动化设计综合与寻优。

#### 任务 3.1：参数扫描与地毯图 (`fixed_wing_trade_studies`)
*   **功能**：批量执行 Sizing Loop。
*   **输入**：设计变量范围（如 $W/S \in [200, 400]$, $T/W \in [0.3, 0.6]$）。
*   **输出**：地毯图数据，Pareto 前沿，推荐的最优设计点。

---

## 4. 推荐目录结构扩展

```
.trae/skills/
├── fixed_wing_aero_buildup_spec/       [Phase 1]
├── fixed_wing_aero_buildup_runbook/    [Phase 1]
├── fixed_wing_propulsion_map_spec/     [Phase 1]
├── fixed_wing_stability_analysis_spec/ [Phase 1]
├── fixed_wing_mission_sim_spec/        [Phase 2]
├── fixed_wing_mission_sim_runbook/     [Phase 2]
├── fixed_wing_cost_spec/               [Phase 2]
├── fixed_wing_trade_studies_spec/      [Phase 3]
└── ...
```
