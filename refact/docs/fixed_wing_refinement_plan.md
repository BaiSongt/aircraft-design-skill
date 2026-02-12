# 固定翼细化计划（记录 + 任务清单）

更新时间：2026-01-31

## 已完成（A1+A2→B1→C1→D2+E1）

- 尾翼布局类型参数化（如常规/T 尾/V 尾/双垂尾）的几何派生入口已接入流水线
- 尾翼布局派生字段已收敛输出（`geometry_shape_derived.tail`、`geometry_reference.installs.tail_surfaces`），OpenVSP 导出应用尾翼安装角
- 机翼/尾翼剖面放样支持跨展向控制点（如厚度缩放、前缘偏移、上下偏移等）并能体现在网格输出
- 机身放样支持椭圆截面（`radius_y_m`/`radius_z_m`）并保持向后兼容（缺省回退到圆截面）
- OpenVSP 脚本导出与派生几何输出已统一到同一条产线（结果可追溯）

## 后续细化路线图（阶段 2–7）

### 阶段 2：气动阻力分解与构型增量

- 目标：由几何与构型假设生成 `cd0`，并输出可追溯的分解表
- 输出：`aero.cd0_buildup` 及分项表（机翼/机身/尾翼/干扰/附面层等）
- 验收：报告能解释 `cd0` 来源，且随几何变化趋势合理

### 阶段 3：推进随工况变化

- 目标：提供 `T_avail(h,V)` / `P_avail(h,V)` 一级模型，支撑巡航/爬升余度
- 输出：关键工况下 `available_thrust` / `available_power` 与余度
- 验收：高空巡航能力随高度/速度衰减趋势合理，约束校核一致

### 阶段 4：任务剖面耗油

- 目标：将燃油估算拆分为 taxi/climb/cruise/descent/reserve 分段并闭合
- 输出：`mission_breakdown`
- 验收：分段耗油与总耗油闭合、可追溯

### 阶段 5：稳定与配平（建议先做 5.1/5.2）

#### 5.1 统一坐标系与安装基准（第 1 个执行任务）

- 目标：为翼/尾/机身统一“安装基准/偏置/旋转”语义，避免不同模块各自定义坐标导致的累积偏差
- 输出：结果中明确写出基准与关键参考点（如各部件安装参考点、姿态角定义）
- 验收：相同输入在不同导出（网格/OpenVSP）下的部件相对位置一致

#### 5.2 尾翼布局规则补全（与 5.1 同批推进）

- 目标：将尾翼布局类型（T 尾/V 尾/双垂尾等）变为“规则驱动”的几何派生，而非零散分支
- 输出：尾翼派生字段（水平尾/垂尾面积、安装位置/高度、V 尾分解参数等）
- 验收：不同布局切换时，派生字段和几何输出连续、无反常跳变

#### 5.3 静稳定裕度与配平量级（阶段 5 的核心输出）

- 输出：`stability.static_margin`、`trim_tail_cl`（或等价量）
- 验收：随 CG/尾容积变化趋势正确

### 阶段 6：结构与载荷

- 目标：估算翼根弯矩剪力量级，并回馈结构重量接口
- 输出：`structures.wing_root_moment_n_m`、`structural_weight_kg`
- 验收：随翼展/载荷因子变化趋势正确

### 阶段 7：迭代与敏感性/优化

- 目标：在约束过滤基础上搜索可行解并输出推荐设计点
- 输出：`design_loop.best_sizing` 与候选集摘要
- 验收：能在给定网格内找到可行最优解并输出可读报告摘要

## 计划任务清单（可逐步勾选）

- [x] 任务 1：统一几何坐标与安装基准输出（阶段 5.1）
- [x] 任务 2：尾翼布局规则补全与派生字段收敛（阶段 5.2）
- [x] 任务 3：静稳定裕度与配平量级一级闭环（阶段 5.3）
- [x] 任务 9：控制面预布局几何生成（Phase 5.3 New）
  - 已支持在 input 中定义控制面（eta_in/out, deflection 等）
  - 已实现 3D 网格生成时的控制面切割与偏转预览

## 高级气动外形细化（Phase 8-10）

详见 [固定翼气动外形深度细化计划](fixed_wing_advanced_shape_plan.md)

- 目标：引入超椭圆截面、面积律分析与内部约束驱动设计
- 重点：从“参数化几何”进化为“准工程级外形”
- [x] 任务 4：阻力分解 `cd0_buildup` 接入报告与敏感性检查（阶段 2）
  - 已增强 GeometryAssumptions，支持机身/机翼/尾翼详细浸润面积与 t/c 输入
  - 已在 fixed_wing_overall 中自动从 geometry_detailed 提取机身浸润面积
  - 已在 report 中输出 cd0_fuselage/wing/tail/misc 分解表与雷诺数信息
- [x] 任务 5：推进随高度/速度模型与推力余度输出（阶段 3）
  - 已增强 PropulsionModel，增加 mct_to_mto_ratio (Max Continuous / Takeoff)
  - 已增加 jet_mach_factor 支持速度修正 (1 + factor * M)
  - 已在 overall_design 中区分爬升/巡航工况的推力 Rating (MCT/Cruise vs MTO)
- [x] 任务 6：任务剖面分段耗油闭合（阶段 4）
  - 已改进 Climb 阶段计算：引入平均爬升高度 (0.6*h_cruise) 与爬升梯度阻力 (D+Wsin(gamma))
  - 已实现航程闭合逻辑：Cruise Range = Total Range - Climb Dist - Descent Dist (估算 19:1)
  - 已更新 mission_fuel_breakdown 输出包含各段距离与推力需求
- [x] 任务 7：结构载荷量级与结构重量回馈接口（阶段 6）
  - 已增强 WingRootLoads 计算，包含惯性卸载因子 (relief_factor)
  - 已实现 Analytical Wing Weight 方法：分别估算翼梁缘条 (bending)、腹板 (shear) 和蒙皮/次结构 (surface) 重量
  - 已引入材料许用应力 (sigma_allow) 与密度参数，不再仅依赖 Class I 统计公式
- [x] 任务 8：约束过滤 + 设计点网格搜索与敏感性（阶段 7）
  - 已增强 grid_search_design_point，支持无可行解时的回退逻辑（选择违反约束最少的点）
  - 已实现 Top N 候选排序与灵敏度分析（围绕 Best 点的 +/- 步长扰动）
  - 已在 report 中输出设计迭代摘要（Candidates, Top 10, Sensitivity）
