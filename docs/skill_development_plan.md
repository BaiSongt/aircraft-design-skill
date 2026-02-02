# SKILL 能力增强与流程化开发规划

更新时间：2026-02-01

## 1. 目标与范围

本规划面向固定翼总体设计类 SKILL，目标是形成“需求→约束→尺寸→气动→重量→性能→稳定→结构→优化→报告”的流程化体系，并逐步增强可解释、可追溯与可闭环能力。

覆盖范围：

- 飞机总体设计：设计点选择、重量闭合、性能约束与任务剖面
- 飞机气动设计：阻力分解、升阻曲线与高升力影响
- 飞机布局设计：机身/机翼/尾翼布局派生、安装基准与可视化一致性

## 2. 权威参考资料（建议优先体系化吸收）

### 2.1 飞机总体设计

- Raymer, D. P. *Aircraft Design: A Conceptual Approach*, AIAA
- Roskam, J. *Airplane Design* (Parts I–VIII), DARcorporation
- Torenbeek, E. *Synthesis of Subsonic Airplane Design*, Springer
- Gudmundsson, S. *General Aviation Aircraft Design*, Butterworth-Heinemann
- Nicolai, L. M., Carichner, G. E. *Fundamentals of Aircraft and Airship Design*, AIAA

### 2.2 飞机气动设计

- Anderson, J. D. *Fundamentals of Aerodynamics*, McGraw-Hill
- Hoerner, S. F. *Fluid-Dynamic Drag*, Hoerner Fluid Dynamics
- Abbott, I. H., von Doenhoff, A. E. *Theory of Wing Sections*, Dover
- Kuethe, A. M., Chow, C.-Y. *Foundations of Aerodynamics*, Wiley
- USAF *DATCOM*（气动经验公式与构型修正）

### 2.3 飞机布局与构型设计

- Roskam, J. *Airplane Design Part I/II*（任务与构型布局）
- Raymer, D. P. *Aircraft Design: A Conceptual Approach*（布局与布置流程）
- Torenbeek, E. *Synthesis of Subsonic Airplane Design*（总体布局与协同约束）

## 3. 能力地图（模块视角）

能力分层：

- 需求与约束：任务剖面、性能约束线、设计点选择
- 初步尺寸：翼载/推重、几何与尺寸闭合
- 气动模型：阻力分解、极曲线、巡航 L/D
- 推进模型：随高度/速度推力或功率模型
- 重量模型：Class I/II 迭代、燃油分数
- 稳定与配平：静稳定裕度、尾容积、配平需求
- 结构载荷：翼根弯矩、剪力、结构重量回馈
- 优化迭代：设计点网格与敏感性
- 可视化输出：几何渲染、报告与可追溯数据

## 4. 流程化体系（总线式数据流）

流程顺序：

1. 需求输入 → 任务剖面与约束边界
2. 约束分析 → 设计点选取（W/S, T/W）
3. 初步几何 → 布局派生与安装基准
4. 气动模型 → 阻力分解与极曲线
5. 推进模型 → 工况可用推力/功率
6. 重量闭合 → MTOW/燃油迭代
7. 性能核算 → 巡航/爬升/起降余度
8. 稳定与配平 → 静稳定裕度与配平量
9. 结构与载荷 → 翼根载荷与结构重量回馈
10. 迭代优化 → 敏感性与推荐设计点
11. 报告输出 → 结果与可追溯表

## 5. 阶段化增强规划（2–7）

### 阶段 2：气动阻力分解与构型增量

- 目标：由几何与构型假设生成 cd0 分解
- 输出：aero.cd0_buildup（机翼/机身/尾翼/干扰/附面层）
- 验收：随几何变化趋势合理且可追溯

### 阶段 3：推进随工况变化

- 目标：提供 T_avail(h,V) / P_avail(h,V) 模型
- 输出：关键工况可用推力与余度
- 验收：高空巡航推力衰减趋势合理

### 阶段 4：任务剖面耗油

- 目标：分段耗油闭合（taxi/climb/cruise/descent/reserve）
- 输出：mission_breakdown
- 验收：分段与总耗油闭合、可追溯

### 阶段 5：稳定与配平

- 目标：输出静稳定裕度与配平量级
- 输出：stability.static_margin、trim_tail_cl
- 验收：随 CG/尾容积变化趋势正确

### 阶段 6：结构与载荷

- 目标：估算翼根弯矩/剪力并回馈结构重量
- 输出：structures.wing_root_moment_n_m、structural_weight_kg
- 验收：随翼展/载荷因子变化趋势正确

### 阶段 7：迭代与敏感性/优化

- 目标：可行解搜索与推荐设计点
- 输出：design_loop.best_sizing、候选集摘要
- 验收：在给定网格中找到可行最优解并输出摘要

## 6. 当前进度与存在问题

### 6.1 当前进度

- 阶段 2–7 已具备可执行闭环与报告输出能力（阻力分解、推进模型、任务剖面、稳定与结构、网格搜索）
- 尾翼布局派生规则已统一输出到 geometry_shape_derived，并在可视化与 OpenVSP 导出中复用
- 三视图/轴测交互已完善，具备平移、缩放、旋转与重置能力

### 6.2 存在问题

- 输入字段在不同模块之间仍有局部不一致（geometry_shape/geometry_shape_derived/geometry_reference 语义混用）
- [x] 高级几何与总体流程之间缺少“统一入口”与“单一结果总线”
- [x] Three.js 仍依赖外部 CDN，在受限环境下需持续降级渲染
- [x] 尾翼派生依赖 wing.s_ref_m2，当主输入缺失时 surfaces 生成不完整
- [x] 报告与结果的“假设可追溯”仍需统一表格模板与来源字段

## 7. 后续执行任务展开（结合当前问题）

### 7.1 优先级 P0：接口一致性与主流程统一

- 实现清单：
  - [x] 汇总 geometry_shape/geometry_shape_derived/geometry_reference 三者的字段对照表
  - [x] 明确每个字段的语义与单位，统一默认值策略（缺省/派生）
  - [x] 增加字段一致性校验函数（输入端、输出端各一次）
  - [x] 修订报告/可视化/导出模块的字段读取路径
- 交付：
  - 单一字段说明表
  - 一致性校验器（errors + warnings 形式）
  - 统一读取路径的改动说明
- 验收：
  - 同一输入在可视化/OpenVSP/报告三端一致
  - 校验器对典型错误输入给出可解释提示

### 7.2 优先级 P0：总体流程入口融合

- 实现清单：
  - [x] 在 run_fixed_wing_design 中接入高级外形生成与输出聚合
  - [x] 统一输出目录结构与命名规范（results/report/geometry/mesh/openvsp）
  - [x] 统一入口参数与示例输入（兼容原有字段）
  - [x] 添加一键运行脚本说明与参数校验
- 交付：
  - 单入口脚本与标准化输出
  - 示例输入与结果对比
- 验收：
  - 一次运行生成全链路产物
  - 原有示例输入不被破坏

### 7.3 优先级 P1：气动与推进一致性校验

- 实现清单：
  - [x] 定义关键工况表结构（巡航/爬升/起飞）
  - [x] 报告中加入推力余度表与阻力分解表的对齐区块
  - [x] 输出中写入各工况的来源参数与公式标识
- 交付：
  - 报告新增“余度对齐表”
  - results.json 增加工况字段
- 验收：
  - 报告可追溯到输入字段
  - 关键工况余度数值稳定可解释

### 7.4 优先级 P1：稳定与结构闭环验证

- 实现清单：
  - [x] 增加稳定与结构回归用例（参数扫描）
  - [x] 生成趋势表（static_margin vs CG、wing_root_moment vs n）
  - [x] 将趋势表写入测试报告或 json 输出
- 交付：
  - 回归测试与趋势数据
  - 可读的结果表
- 验收：
  - 趋势单调合理
  - 无异常跳变

### 7.5 优先级 P2：几何与可视化离线可用

- 实现清单：
  - [x] 提供本地 three.js 资源目录与加载开关
  - [x] 保留 CDN 作为回退方案
  - [x] 完善降级渲染在无网络环境的提示
- 交付：
  - 本地资源加载方案
  - 兼容线上/离线的可视化模板
- 验收：
  - 离线环境可正常加载
  - 线上环境无性能退化

### 7.6 优先级 P2：报告模板化与可追溯增强

- 实现清单：
  - [x] 统一报告模板，增加“假设来源表”
  - [x] 定义关键结论表的字段与单位
  - [x] 增加敏感性摘要区块（Top N 变量）
- 交付：
  - 模板化 report.md
  - 关键字段追溯表
- 验收：
  - 关键数值可回溯到输入字段
  - 报告结构稳定且可复用

## 8. 接口字段规划（摘要）

### 6.1 输入侧（扩展/统一）

- geometry_shape：fuselage/wing/tail、layout、resolution
- geometry_detailed：外形/翼型/控制面/修正器
- aero：cd0_buildup、cl_alpha、cl_max、high_lift
- propulsion：thrust_model、mct_to_mto_ratio、altitude_factor
- mission：segments、range_nm、cruise_alt_m
- stability：cg_range、tail_volume
- structures：load_factor_limit、material_props
- design_loop：grid_ws_tw、objective

### 6.2 输出侧（闭环字段）

- geometry_reference：安装基准与坐标系
- aero：cd0_buildup、polar、cruise_ld
- propulsion：available_thrust、margin
- mission_breakdown：分段耗油与距离
- stability：static_margin、trim_tail_cl
- structures：wing_root_moment_n_m、structural_weight_kg
- design_loop：best_sizing、candidates
- report：核心表格与关键结论

## 9. 任务清单（可并行推进）

### 7.1 总体设计

- 完善设计点选择策略（约束线自动选点）
- 统一输入/输出字段含义与单位
- 构建跨模块一致的坐标与安装基准

### 7.2 气动设计

- 阻力分解模型标准化与可追溯
- 高升力装置与起降构型修正
- 极曲线与 L/D 评估接口统一

### 7.3 布局设计

- 机身/翼/尾几何派生规则收敛
- 尾翼布局类型规则驱动（T/V/双垂尾）
- 布局结果与可视化一致性校验

### 7.4 性能与任务

- 推进模型随高度/速度衰减
- 任务剖面耗油分段闭合
- 爬升/巡航余度与任务一致性校验

### 7.5 稳定与结构

- 静稳定裕度与配平量级评估
- 结构载荷量级估算与重量回馈
- 可行性红线与敏感性分析

### 7.6 迭代优化

- 网格搜索与目标函数优化
- 可行解集输出与鲁棒性检查
- 报告摘要自动生成

## 10. 近期工作计划（建议）

- 目标：完成 7.1–7.6 任务清单的首轮落地与验收
- 计划：
  - 周 1：统一输入/输出字段含义与单位，补充校验用例
  - 周 2：推进模型随高度/速度衰减 + 任务剖面耗油分段闭合
  - 周 3：稳定/结构敏感性与红线校核，输出报告摘要
  - 周 4：网格搜索与目标函数优化，完善可行解集输出
- 验收：
  - 每周输出可运行样例与报告对比
  - 关键指标趋势可解释、无异常跳变

## 11. 里程碑建议

- M1：输入/输出字段统一 + 约束线选点
- M2：气动/推进/任务剖面闭环
- M3：稳定/结构回馈闭环
- M4：优化迭代与报告自动化

## 12. 交付验收总则

- 可追溯：每一核心输出均能回溯到输入与假设
- 可复现：同一输入输出一致
- 可解释：报告能说明来源与趋势
- 可扩展：模块接口支持新增构型与任务剖面
