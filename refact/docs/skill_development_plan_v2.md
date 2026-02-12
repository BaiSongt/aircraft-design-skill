# 飞机总体设计能力发展规划 - 第二阶段（详细分析与优化）

本文档详细规划了将现有 Class I（初步估算）能力扩展至 Class II（详细分析）级别的技术路线图。本计划参考了 Raymer、Roskam、Nicolai 等权威飞机设计教材，以及 OpenVSP、VSPAERO 等开源工具的最佳实践。

## 1. 总体目标与架构

**目标**：在初步总体方案（Class I）收敛的基础上，引入基于物理模型的详细分析模块，替代统计学经验公式，提高设计结果的可信度，并支持气动-结构-稳定性耦合分析。

**核心模块扩展**：
1.  **详细重量估算 (Class II Weights)**：从全机统计公式转向基于几何参数的部件级重量累加。
2.  **高保真气动分析 (High-Fidelity Aero)**：集成 VSPAERO (Vortex Lattice Method) 进行升力线斜率、气动中心及压力分布计算。
3.  **稳定性与控制 (Stability & Control)**：基于 VLM 结果进行静稳定裕度校核、操纵面配平与尺寸设计。
4.  **成本分析 (Cost Analysis)**：引入 DAPCA IV 模型进行全寿命周期成本（LCC）估算。
5.  **推进系统集成 (Propulsion Integration)**：考虑进气道/喷管安装效应及详细油耗模型。

---

## 2. 详细实施计划

### 2.1 模块 A：Class II 重量估算 (Detailed Weight Estimation)

**现状**：目前使用 Nicolai/Raymer 的 Class I 全机或大部件统计公式，对几何细节不敏感。
**目标**：建立基于部件几何特征（如翼梁深度、蒙皮面积、机身框距）的物理/半经验公式模型。

**技术细节**：
*   **机翼组 (Wing Group)**：
    *   依据 GD (General Dynamics) 或 Torenbeek 方法。
    *   输入：设计过载 $N_z$、展弦比 $AR$、厚度比 $t/c$、后掠角 $\Lambda$、结构材料属性。
    *   输出：翼梁、肋、蒙皮重量。
*   **机身组 (Fuselage Group)**：
    *   基于机身湿面积 $S_{wet}$、长度 $L$、最大压差 $\Delta P$（用于增压舱）。
    *   考虑加强框、纵梁、蒙皮的重量分布。
*   **起落架 (Landing Gear)**：
    *   基于着陆重量 $W_{land}$ 和起落架长度、下沉速度 $V_{sink}$。
*   **系统设备 (Systems)**：
    *   液压、电气、环控、航电系统基于功率需求和体积估算。

**开发任务**：
1.  复用并扩展现有模块：`aircraft_design/weights_structural.py`、`aircraft_design/weights_system.py`。
2.  补充部件级详细重量函数（翼/机身/尾翼/起落装置），统一接口返回细分项与形心位置。
3.  新增 CG 计算与汇总：基于各部件形心坐标，输出空重与任务各阶段 CG（%MAC）。

### 2.2 模块 B：高保真气动分析 (VSPAERO Integration)

**现状**：使用抛物线极曲线 ($C_D = C_{D0} + K C_L^2$)，参数基于统计值。
**目标**：通过涡格法 (VLM) 计算具体的 $C_{L\alpha}$、气动中心 (AC)、$C_{m\alpha}$ 及诱导阻力因子 $e$。

**技术细节**：
*   **自动化流程**：
    1.  **DegenGeom 生成**：调用 OpenVSP API 导出模型的 `DegenGeom` (CSV/M 格式)。
    2.  **输入文件构建**：自动生成 `.vspaero` 输入文件（定义马赫数、攻角序列、参考面积）。
    3.  **求解器调用**：通过 Python `subprocess` 调用 `vspaero` 可执行文件（支持多线程）。
    4.  **结果解析**：解析 `.polar` (极曲线) 和 `.history` (迭代历史) 文件。
*   **分析工况**：
    *   **巡航状态**：计算 $L/D$、最佳巡航升力系数。
    *   **高升力状态**：估算襟翼偏转下的 $\Delta C_L$（需配合经验修正）。
    *   **稳定性导数**：计算 $C_{L\alpha}, C_{m\alpha}, C_{n\beta}$。

**开发任务**：
1.  完善 `aircraft_design/vspaero_interface.py`：生成输入、调用求解、解析输出。
2.  引入 `VSPAEROManager` 风格的管理类（文件IO与批量工况扫掠），与现有接口对齐。
3.  将 VLM 结果回馈到设计循环：更新极曲线、升力线斜率、气动中心、诱导因子。

### 2.3 模块 C：稳定性与控制 (Stability & Control)

**现状**：仅基于尾容量系数 (Tail Volume Coefficient) 进行初略定尺寸。
**目标**：确保飞机在各重心位置下的静稳定性，并完成操纵面（副翼、升降舵、方向舵）的物理定尺寸。

**技术细节**：
*   **静稳定裕度 (Static Margin)**：
    *   $SM = \frac{X_{NP} - X_{CG}}{\bar{c}}$
    *   结合 VSPAERO 计算的整机中性点 $X_{NP}$ 和 Class II 重量估算的 $X_{CG}$。
*   **配平分析 (Trim Analysis)**：
    *   建立纵向力矩平衡方程：$C_m = C_{m0} + C_{m\alpha}\alpha + C_{m\delta_e}\delta_e = 0$。
    *   解算巡航和着陆构型下的配平攻角 $\alpha_{trim}$ 和升降舵偏角 $\delta_{e,trim}$。
*   **操纵面设计**：
    *   **副翼**：基于滚转速率要求（如 $P_{ss} \ge 60^\circ/s$）。
    *   **方向舵**：基于单发失效 (OEI) 平衡或侧风着陆要求。

**开发任务**：
1.  创建 `aircraft_design/stability/` 模块。
2.  开发配平求解器 (Trim Solver)。
3.  在 OpenVSP 模型中参数化操纵面（Control Surfaces）。

### 2.4 模块 D：成本分析 (Cost Analysis - DAPCA IV)

**现状**：无成本估算。
**目标**：估算飞机的研发成本 (RDT&E) 和生产成本。

**技术细节**：
*   **DAPCA IV 模型** (Rand Corporation)：
    *   基于空重 ($W_e$)、最大速度 ($V$)、产量 ($Q$) 和材料因子。
    *   **工程工时**：$H_E = 4.86 W_e^{0.777} V^{0.894} Q^{0.163}$
    *   **工装工时**：$H_T = 5.99 W_e^{0.777} V^{0.696} Q^{0.263}$
    *   **制造工时**：$H_M = 7.37 W_e^{0.82} V^{0.484} Q^{0.641}$
    *   **质量控制**：$H_Q \approx 0.13 H_M$
    *   **材料成本**：$C_{mat} = 22.1 W_e^{0.921} V^{0.621} Q^{0.799}$
    *   **发动机与航电**：独立估算。
*   **修正因子**：
    *   复合材料修正 (1.1 - 1.5)。
    *   隐身技术修正。

**开发任务**：
1.  创建 `aircraft_design/cost/dapca_model.py`。
2.  集成到 `run_sizing.py` 的最终报告生成环节。

---

## 3. 工作流集成方案

为了保持系统的连贯性，新增模块将作为 "Stage 2" 自动触发，或通过参数 `--detailed-analysis` 显式开启。

```python
# 伪代码：集成逻辑
def execute_detailed_analysis(sized_aircraft, requirements):
    # 1. 生成详细几何 (已完成)
    geom = generate_detailed_geometry(sized_aircraft)
    
    # 2. Class II 重量重心计算
    weights_c2 = calculate_class2_weights(geom)
    sized_aircraft.update_weights(weights_c2) # 更新重量数据
    
    # 3. 运行 VSPAERO 气动分析
    vsp_data = run_vspaero_analysis(geometry=geom, mach=requirements.cruise_mach)
    
    # 4. 稳定性校核
    stability = check_stability(weights_c2.cg, vsp_data.neutral_point)
    if stability.static_margin < 0.05:
        print("警告：静稳定裕度不足，建议增大平尾面积或前移重心")
        
    # 5. 成本估算
    cost = calculate_dapca_cost(sized_aircraft.empty_weight_kg, requirements.max_speed, quantity=500)
    
    return DetailedAnalysisResult(weights_c2, vsp_data, stability, cost)
```

## 4. 依赖项与环境

*   **OpenVSP**: 需安装 OpenVSP 3.30+，并确保 `vsp` Python 库可被调用。
*   **VSPAERO**: 需确保 `vspaero` 可执行文件在系统路径中。
*   **Python 库**: `numpy`, `scipy` (用于配平求解), `pandas` (数据处理)。

## 5. 里程碑 (Milestones)

1.  **M1 (本周)**: 完成 `weights_class2.py`，实现机翼和机身的详细重量公式。
2.  **M2 (下周)**: 完成 `vspaero_interface.py` 扫掠与解析链路，打通 OpenVSP -> VSPAERO -> Python。
3.  **M3 (下周)**: 实现稳定性校核逻辑，并在报告中输出 Trim Diagram。
4.  **M4 (后续)**: 集成 DAPCA IV 成本模型，输出经济性分析报告。

---

## 6. 下一批阶段推进计划（Stage 2–7 扩展）

### 阶段 2：气动阻力分解与构型增量
- 目标：由几何与构型假设生成 `cd0` 与可追溯分解
- 输出：`aero.cd0_buildup` 与分解表
- 验收：报告可解释 `cd0` 来源，且随几何变化趋势合理

### 阶段 3：推进随工况变化
- 目标：提供 `T_avail(h,V)` 或 `P_avail(h,V)` 的一级模型
- 输出：巡航/爬升工况下 `available_thrust` 与余度
- 验收：高空巡航推力衰减合理，约束校核一致

### 阶段 4：任务剖面耗油
- 目标：将燃油分数拆分为 taxi/climb/cruise/descent/reserve 等
- 输出：`mission_breakdown`
- 验收：分段耗油和总耗油闭合、可追溯

### 阶段 5：稳定与配平
- 目标：输出静稳定裕度与配平量级
- 输出：`stability.static_margin`、`trim_tail_cl`
- 验收：随 CG/尾容积变化趋势正确

### 阶段 6：结构与载荷
- 目标：估算翼根弯矩剪力与结构重量回馈接口
- 输出：`structures.wing_root_moment_n_m`、`structural_weight_kg`
- 验收：随翼展/载荷因子变化趋势正确

### 阶段 7：迭代与敏感性/优化
- 目标：基于约束过滤，搜索可行解并给出推荐设计点
- 输出：`design_loop.best_sizing` 与候选集
- 验收：在给定网格内找到可行最优解并输出报告摘要

### 新增里程碑（M5–M10）
5.  **M5**：完成阻力分解模块与报告分解表输出
6.  **M6**：完成推进随高度/速度变化接口与约束一致性校核
7.  **M7**：完成任务剖面分段耗油闭合与可视化
8.  **M8**：完成 Trim Solver 与静稳定裕度报告
9.  **M9**：完成载荷估算与结构重量回馈接口
10. **M10**：完成迭代优化与敏感性分析并输出推荐设计点
