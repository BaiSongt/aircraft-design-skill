# 飞机设计SKILL开发计划

## 1. 项目概述

### 1.1 目标
基于《项目中期报告_601关键能力_V2.docx》中的飞机设计理论，完善现有固定翼设计SKILL的实现，建立完整的理论-代码对应关系。

### 1.2 范围
- 覆盖设计参数、气动特性、重量特性、发动机特性、性能特性、操稳特性六大模块
- 实现从理论公式到代码实现的完整映射
- 建立完整的测试和验证体系

### 1.3 原则
- 理论优先：所有实现必须基于理论文档中的公式
- 分阶段实施：按照优先级分P0、P1、P2三个阶段
- 可追溯性：每个实现都能追溯到理论文档的具体章节
- 可测试性：每个实现都有对应的测试用例

## 2. 现状分析

### 2.1 现有SKILL实现状态

| SKILL模块 | 实现状态 | 完成度 | 主要缺失功能 |
|-----------|---------|-------|------------|
| fixed_wing_shape_parametric_spec | ✅ 基本完整 | 90% | 翼型参数详细定义、增升装置详细定义 |
| fixed_wing_aero_spec | ⚠️ 部分实现 | 40% | 详细升力线斜率、阻力分解、涡升力、低速构型 |
| fixed_wing_weights_spec | ⚠️ 部分实现 | 50% | 详细结构重量计算、系统重量计算、复合材料修正 |
| fixed_wing_propulsion_spec | ⚠️ 部分实现 | 40% | 推力随高度/速度变化、详细耗油率模型、油门控制 |
| fixed_wing_performance_spec | ⚠️ 部分实现 | 45% | 起降性能、任务剖面、设计点性能 |
| fixed_wing_stability_control_spec | ⚠️ 部分实现 | 30% | 静稳定性计算、动稳定性分析、操纵性分析 |
| fixed_wing_structures_loads_spec | ⚠️ 部分实现 | 35% | 载荷计算、结构重量回馈 |

### 2.2 现有代码实现状态

| 代码模块 | 实现状态 | 完成度 | 主要缺失功能 |
|---------|---------|-------|------------|
| geometry_parametric.py | ✅ 基本完整 | 85% | 翼型参数化、增升装置参数化 |
| aero_drag_buildup.py | ⚠️ 部分实现 | 45% | 详细阻力分解、升力线斜率 |
| weights_class1.py | ⚠️ 部分实现 | 55% | 详细结构重量公式 |
| propulsion.py | ⚠️ 部分实现 | 40% | 推力/耗油率随工况变化 |
| performance.py | ⚠️ 部分实现 | 50% | 起降性能、任务剖面 |
| stability_control.py | ⚠️ 部分实现 | 35% | 静稳定性、动稳定性 |
| structures_loads.py | ⚠️ 部分实现 | 40% | 载荷计算、重量回馈 |

## 3. 开发计划

### 3.1 阶段划分

#### 阶段1：P0高优先级（核心功能增强）
**时间周期**：4周
**目标**：实现核心的气动、重量、发动机特性计算，支撑基本的总体设计闭环

#### 阶段2：P1中优先级（性能与操稳增强）
**时间周期**：4周
**目标**：实现详细的性能计算和操稳分析，支撑完整的方案评估

#### 阶段3：P2低优先级（高级功能完善）
**时间周期**：4周
**目标**：实现跨声速特性、动稳定性、操纵性等高级功能

### 3.2 阶段1详细计划（P0高优先级）

#### 3.2.1 第1周：气动特性增强

**任务1.1：升力线斜率计算实现**

**参考内容**：
- 理论文档：[02_aerodynamic_characteristics.md](./02_aerodynamic_characteristics.md) 第2.1节
- 公式：亚声速升力线斜率、超声速升力线斜率、跨声速升力线斜率

**实现内容**：
1. 创建 `aircraft_design/aero/lift_slope.py` 模块
2. 实现函数：
   ```python
   def calculate_lift_slope_subsonic(AR, Lambda_maxt, Sref, Se, M, F):
       """
       计算亚声速升力线斜率

       参数:
           AR: 展弦比
           Lambda_maxt: 机翼最大厚度线后掠角（弧度）
           Sref: 机翼参考面积
           Se: 机翼外露投影面积
           M: 马赫数
           F: 机身升力影响系数

       返回:
           CLa: 升力线斜率 (1/rad)

       参考: 02_aerodynamic_characteristics.md 第2.1.1节
       """
       pass

   def calculate_lift_slope_supersonic(AR, Lambda_LE, lambda_taper, Se, Sref, M, F):
       """
       计算超声速升力线斜率

       参数:
           AR: 展弦比
           Lambda_LE: 前缘后掠角（弧度）
           lambda_taper: 梯形比
           Se: 机翼外露投影面积
           Sref: 机翼参考面积
           M: 马赫数
           F: 机身升力影响系数

       返回:
           CLa: 升力线斜率 (1/rad)

       参考: 02_aerodynamic_characteristics.md 第2.1.2节
       """
       pass

   def calculate_lift_slope_transonic(AR, Lambda_maxt, Sref, Se, M, F):
       """
       计算跨声速升力线斜率

       参数:
           AR: 展弦比
           Lambda_maxt: 机翼最大厚度线后掠角（弧度）
           Sref: 机翼参考面积
           Se: 机翼外露投影面积
           M: 马赫数
           F: 机身升力影响系数

       返回:
           CLa: 升力线斜率 (1/rad)

       参考: 02_aerodynamic_characteristics.md 第2.1.3节
       """
       pass
   ```

3. 编写单元测试 `tests/test_aero_lift_slope.py`

**任务1.2：零升阻力分解实现**

**参考内容**：
- 理论文档：[02_aerodynamic_characteristics.md](./02_aerodynamic_characteristics.md) 第3.2节
- 公式：摩擦阻力、形状阻力、干扰阻力、杂项阻力

**实现内容**：
1. 创建 `aircraft_design/aero/drag_buildup_detailed.py` 模块
2. 实现函数：
   ```python
   def calculate_friction_coefficient_laminar(Re):
       """
       计算层流摩擦系数

       参数:
           Re: 雷诺数

       返回:
           Cf_laminar: 层流摩擦系数

       参考: 02_aerodynamic_characteristics.md 第3.2.1节
       """
       pass

   def calculate_friction_coefficient_turbulent(Re, M):
       """
       计算湍流摩擦系数

       参数:
           Re: 雷诺数
           M: 马赫数

       返回:
           Cf_turbulent: 湍流摩擦系数

       参考: 02_aerodynamic_characteristics.md 第3.2.1节
       """
       pass

   def calculate_form_factor_wing(tc, xc, Lambda_m, M):
       """
       计算翼面类部件形状因子

       参数:
           tc: 机翼平均相对厚度
           xc: 翼型最大厚度处的相对位置
           Lambda_m: 最大厚度位置连线的后掠角（弧度）
           M: 马赫数

       返回:
           FF: 形状因子

       参考: 02_aerodynamic_characteristics.md 第3.2.2节
       """
       pass

   def calculate_form_factor_fuselage(f):
       """
       计算机身类部件形状因子

       参数:
           f: 机身长径比

       返回:
           FF: 形状因子

       参考: 02_aerodynamic_characteristics.md 第3.2.2节
       """
       pass

   def calculate_drag_coefficient_zero_lift(components_data):
       """
       计算零升阻力系数

       参数:
           components_data: 各部件数据列表，每个元素包含：
               - name: 部件名称
               - Cf: 摩擦系数
               - Swet: 湿润面积
               - FF: 形状因子
               - Q: 干扰因子

       返回:
           CD0: 零升阻力系数
           breakdown: 阻力分解字典

       参考: 02_aerodynamic_characteristics.md 第3.2节
       """
       pass
   ```

3. 编写单元测试 `tests/test_aero_drag_buildup_detailed.py`

**任务1.3：升致阻力计算实现**

**参考内容**：
- 理论文档：[02_aerodynamic_characteristics.md](./02_aerodynamic_characteristics.md) 第3.3节
- 公式：亚声速升致阻力因子、超声速升致阻力因子

**实现内容**：
1. 在 `aircraft_design/aero/drag_buildup_detailed.py` 中添加函数：
   ```python
   def calculate_induced_drag_factor_subsonic(AR, Lambda_quarter, tc, M, Ne, lambda_taper):
       """
       计算亚声速升致阻力因子

       参数:
           AR: 展弦比
           Lambda_quarter: 1/4弦线后掠角（弧度）
           tc: 机翼平均相对厚度
           M: 马赫数
           Ne: 发动机个数（发动机在机翼上方时设置）
           lambda_taper: 梯形比

       返回:
           K: 升致阻力因子

       参考: 02_aerodynamic_characteristics.md 第3.3.1节
       """
       pass

   def calculate_induced_drag_factor_supersonic(AR, Lambda_quarter, tc, Kw):
       """
       计算超声速升致阻力因子

       参数:
           AR: 展弦比
           Lambda_quarter: 1/4弦线后掠角（弧度）
           tc: 机翼平均相对厚度
           Kw: 经验系数

       返回:
           K: 升致阻力因子

       参考: 02_aerodynamic_characteristics.md 第3.3.1节
       """
       pass

   def calculate_drag_coefficient_induced(CL, CLmin, K):
       """
       计算升致阻力系数

       参数:
           CL: 升力系数
           CLmin: 阻力最小时对应的升力系数
           K: 升致阻力因子

       返回:
           CDi: 升致阻力系数

       参考: 02_aerodynamic_characteristics.md 第3.3节
       """
       pass
   ```

2. 编写单元测试

#### 3.2.2 第2周：重量特性增强

**任务2.1：结构重量计算实现**

**参考内容**：
- 理论文档：[03_weight_characteristics.md](./03_weight_characteristics.md) 第2节
- 公式：机翼重量、机身重量、尾翼重量、起落装置重量

**实现内容**：
1. 创建 `aircraft_design/weights/structural_weights.py` 模块
2. 实现函数：
   ```python
   def calculate_wing_weight(S_wing, W_FW, Lambda_LE, lambda_taper, AR, N, K_var):
       """
       计算机翼结构重量

       参数:
           S_wing: 机翼参考面积 (ft²)
           W_FW: 最大起飞重量 (lb)
           Lambda_LE: 机翼前缘后掠角（弧度）
           lambda_taper: 机翼梯形比
           AR: 机翼展弦比
           N: 极限过载因子
           K_var: 机翼可变后掠角因子

       返回:
           W_wing: 机翼结构重量 (lb)

       参考: 03_weight_characteristics.md 第2.1节
       """
       pass

   def calculate_fuselage_weight(S_fuselage_gross, W_FW, N_z, L, H, K_INL):
       """
       计算机身结构重量

       参数:
           S_fuselage_gross: 机身总表面积 (ft²)
           W_FW: 最大起飞重量 (lb)
           N_z: 极限过载因子
           L: 机身长度 (ft)
           H: 机身最大高度 (ft)
           K_INL: 进气道安装位置因子

       返回:
           W_fuselage: 机身结构重量 (lb)

       参考: 03_weight_characteristics.md 第2.2节
       """
       pass

   def calculate_horizontal_tail_weight(N, S_HT, t_RHT, c_wing, L_t, b_HT):
       """
       计算平尾结构重量

       参数:
           N: 极限过载因子
           S_HT: 平尾参考面积 (ft²)
           t_RHT: 平尾翼根翼型相对厚度
           c_wing: 机翼平均气动弦长 (ft)
           L_t: 平尾尾力臂 (ft)
           b_HT: 尾翼展长 (ft)

       返回:
           W_horizontal_tail: 平尾结构重量 (lb)

       参考: 03_weight_characteristics.md 第2.3.1节
       """
       pass

   def calculate_vertical_tail_weight(h_T_h_V, S_VT, M_0, L_t, S_r, AR, lambda_taper, Lambda_VT):
       """
       计算垂尾结构重量

       参数:
           h_T_h_V: 平尾安装方式
           S_VT: 垂尾参考面积 (ft²)
           M_0: 海平面最大马赫数
           L_t: 垂尾尾力臂 (ft)
           S_r: 方向舵面积 (ft²)
           AR: 垂尾展弦比
           lambda_taper: 垂尾梯形比
           Lambda_VT: 垂尾1/4弦线后掠角（弧度）

       返回:
           W_vertical_tail: 垂尾结构重量 (lb)

       参考: 03_weight_characteristics.md 第2.3.2节
       """
       pass

   def calculate_landing_gear_weight(W_FW):
       """
       计算起落装置重量

       参数:
           W_FW: 最大起飞重量 (lb)

       返回:
           W_landing_gear: 起落装置重量 (lb)

       参考: 03_weight_characteristics.md 第2.4节
       """
       pass
   ```

3. 编写单元测试 `tests/test_weights_structural.py`

**任务2.2：燃油系统重量计算实现**

**参考内容**：
- 理论文档：[03_weight_characteristics.md](./03_weight_characteristics.md) 第2.5节
- 公式：自密封油箱、支撑结构、空中加油、排放系统、重心控制

**实现内容**：
1. 创建 `aircraft_design/weights/fuel_system_weights.py` 模块
2. 实现函数：
   ```python
   def calculate_self_sealing_tank_weight(FGW, FGF):
       """
       计算自密封油箱重量

       参数:
           FGW: 机翼油箱体积 (加仑)
           FGF: 机身油箱体积 (加仑)

       返回:
           W_self_sealing: 自密封油箱重量 (lb)

       参考: 03_weight_characteristics.md 第2.5.1节
       """
       pass

   def calculate_support_structure_weight(FGW, FGF):
       """
       计算油箱支撑结构重量

       参数:
           FGW: 机翼油箱体积 (加仑)
           FGF: 机身油箱体积 (加仑)

       返回:
           W_supports: 油箱支撑结构重量 (lb)

       参考: 03_weight_characteristics.md 第2.5.2节
       """
       pass

   def calculate_refueling_system_weight(FGW, FGF):
       """
       计算空中加油系统重量

       参数:
           FGW: 机翼油箱体积 (加仑)
           FGF: 机身油箱体积 (加仑)

       返回:
           W_refuel: 空中加油系统重量 (lb)

       参考: 03_weight_characteristics.md 第2.5.3节
       """
       pass

   def calculate_dump_and_drain_weight(FGW, FGF):
       """
       计算燃油排放系统重量

       参数:
           FGW: 机翼油箱体积 (加仑)
           FGF: 机身油箱体积 (加仑)

       返回:
           W_dump_and_drain: 燃油排放系统重量 (lb)

       参考: 03_weight_characteristics.md 第2.5.4节
       """
       pass

   def calculate_transfer_pumps_weight(FGW, FGF):
       """
       计算重心控制系统重量

       参数:
           FGW: 机翼油箱体积 (加仑)
           FGF: 机身油箱体积 (加仑)

       返回:
           W_transfer_pumps: 重心控制系统重量 (lb)

       参考: 03_weight_characteristics.md 第2.5.5节
       """
       pass
   ```

3. 编写单元测试 `tests/test_weights_fuel_system.py`

#### 3.2.3 第3周：发动机特性增强

**任务3.1：推力模型实现**

**参考内容**：
- 理论文档：[04_engine_characteristics.md](./04_engine_characteristics.md) 第2节
- 公式：涡扇发动机推力系数、油门杆控制

**实现内容**：
1. 创建 `aircraft_design/propulsion/thrust_model.py` 模块
2. 实现函数：
   ```python
   def calculate_temperature_ratio(T_t, T_SL):
       """
       计算温度比

       参数:
           T_t: 巡航点的总温 (K)
           T_SL: 海平面的静温 (K)

       返回:
           TR: 温度比

       参考: 04_engine_characteristics.md 第2.2.1节
       """
       pass

   def calculate_pressure_ratio(P, P_SL):
       """
       计算压力比

       参数:
           P: 该高度、速度下的总压 (Pa)
           P_SL: 海平面的静压 (Pa)

       返回:
           delta: 压力比

       参考: 04_engine_characteristics.md 第2.2.1节
       """
       pass

   def calculate_thrust_coefficient_afterburner(M, delta, theta):
       """
       计算加力状态推力系数

       参数:
           M: 马赫数
           delta: 压力比
           theta: 温度比

       返回:
           alpha_afterburner: 加力状态推力系数

       参考: 04_engine_characteristics.md 第2.2.2节
       """
       pass

   def calculate_thrust_coefficient_mil(M, delta, theta):
       """
       计算未加力状态推力系数

       参数:
           M: 马赫数
           delta: 压力比
           theta: 温度比

       返回:
           alpha_mil: 未加力状态推力系数

       参考: 04_engine_characteristics.md 第2.2.3节
       """
       pass

   def calculate_thrust(T_SL, M, h, throttle_position, afterburner=False):
       """
       计算发动机推力

       参数:
           T_SL: 海平面静推力 (N)
           M: 马赫数
           h: 高度 (m)
           throttle_position: 油门杆位置 (0-1)
           afterburner: 是否加力

       返回:
           T: 发动机推力 (N)

       参考: 04_engine_characteristics.md 第2节
       """
       pass
   ```

3. 编写单元测试 `tests/test_propulsion_thrust.py`

**任务3.2：耗油率模型实现**

**参考内容**：
- 理论文档：[04_engine_characteristics.md](./04_engine_characteristics.md) 第3节
- 公式：涡扇发动机耗油率、非设计点耗油率

**实现内容**：
1. 创建 `aircraft_design/propulsion/sfc_model.py` 模块
2. 实现函数：
   ```python
   def calculate_sfc_afterburner(SFC_SL, M, theta):
       """
       计算加力状态单位推力耗油率

       参数:
           SFC_SL: 海平面静耗油率 (kg/(N·h))
           M: 马赫数
           theta: 温度比

       返回:
           SFC_afterburner: 加力状态耗油率 (kg/(N·h))

       参考: 04_engine_characteristics.md 第3.2.1节
       """
       pass

   def calculate_sfc_mil(SFC_SL, M, theta):
       """
       计算未加力状态单位推力耗油率

       参数:
           SFC_SL: 海平面静耗油率 (kg/(N·h))
           M: 马赫数
           theta: 温度比

       返回:
           SFC_mil: 未加力状态耗油率 (kg/(N·h))

       参考: 04_engine_characteristics.md 第3.2.2节
       """
       pass

   def calculate_sfc_non_design(SFC_design, throttle_ratio, k_throttle=0.3):
       """
       计算非设计点耗油率

       参数:
           SFC_design: 设计点耗油率 (kg/(N·h))
           throttle_ratio: 油门杆比例 (0-1)
           k_throttle: 经验系数

       返回:
           SFC_non_design: 非设计点耗油率 (kg/(N·h))

       参考: 04_engine_characteristics.md 第3.3节
       """
       pass

   def calculate_sfc(T_SL, M, h, throttle_position, afterburner=False):
       """
       计算发动机耗油率

       参数:
           T_SL: 海平面静推力 (N)
           M: 马赫数
           h: 高度 (m)
           throttle_position: 油门杆位置 (0-1)
           afterburner: 是否加力

       返回:
           SFC: 发动机耗油率 (kg/(N·h))

       参考: 04_engine_characteristics.md 第3节
       """
       pass
   ```

3. 编写单元测试 `tests/test_propulsion_sfc.py`

#### 3.2.4 第4周：集成测试与文档更新

**任务4.1：集成测试**
1. 编写集成测试 `tests/test_integration_p0.py`
2. 测试气动-重量-发动机-性能的闭环
3. 验证与理论文档中示例值的一致性

**任务4.2：文档更新**
1. 更新SKILL文档，说明新增功能
2. 更新理论文档，标记已实现的功能
3. 编写使用示例

**任务4.3：代码审查**
1. 运行ruff和mypy检查
2. 代码审查和优化
3. 性能测试和优化

### 3.3 阶段2详细计划（P1中优先级）

#### 3.3.1 第5-6周：性能特性增强

**任务5.1：起降性能计算实现**

**参考内容**：
- 理论文档：[05_performance_characteristics.md](./05_performance_characteristics.md) 第2节
- 公式：失速速度、起飞性能、着陆性能

**实现内容**：
1. 创建 `aircraft_design/performance/field_performance.py` 模块
2. 实现函数：
   ```python
   def calculate_stall_speed(W, rho, S, CLmax):
       """
       计算失速速度

       参数:
           W: 飞机重量 (N)
           rho: 空气密度 (kg/m³)
           S: 机翼参考面积 (m²)
           CLmax: 最大升力系数

       返回:
           V_stall: 失速速度 (m/s)

       参考: 05_performance_characteristics.md 第2.1.2节
       """
       pass

   def calculate_takeoff_distance(T, D, L, W, mu_g, V_LOF):
       """
       计算起飞距离

       参数:
           T: 推力 (N)
           D: 阻力 (N)
           L: 升力 (N)
           W: 重量 (N)
           mu_g: 地面滚动摩擦系数
           V_LOF: 离地速度 (m/s)

       返回:
           S_takeoff: 起飞距离 (m)
           t_takeoff: 起飞时间 (s)

       参考: 05_performance_characteristics.md 第2.2节
       """
       pass

   def calculate_landing_distance(T, D, L, W, mu_g, V_TD):
       """
       计算着陆距离

       参数:
           T: 推力 (N)
           D: 阻力 (N)
           L: 升力 (N)
           W: 重量 (N)
           mu_g: 地面滚动摩擦系数
           V_TD: 接地速度 (m/s)

       返回:
           S_landing: 着陆距离 (m)
           t_landing: 着陆时间 (s)

       参考: 05_performance_characteristics.md 第2.3节
       """
       pass
   ```

3. 编写单元测试 `tests/test_performance_field.py`

**任务5.2：任务剖面计算实现**

**参考内容**：
- 理论文档：[05_performance_characteristics.md](./05_performance_characteristics.md) 第3节
- 公式：各任务段计算、燃油迭代

**实现内容**：
1. 创建 `aircraft_design/performance/mission_performance.py` 模块
2. 实现函数：
   ```python
   def calculate_climb_segment(W, T, D, V, gamma):
       """
       计算爬升段性能

       参数:
           W: 飞机重量 (N)
           T: 推力 (N)
           D: 阻力 (N)
           V: 速度 (m/s)
           gamma: 爬升角 (rad)

       返回:
           RC: 爬升率 (m/s)
           sin_gamma: 爬升梯度
           fuel_consumed: 燃油消耗 (kg)

       参考: 05_performance_characteristics.md 第3.4节
       """
       pass

   def calculate_cruise_segment(W, SFC, L_D, V, t):
       """
       计算巡航段性能

       参数:
           W: 飞机重量 (N)
           SFC: 耗油率 (kg/(N·h))
           L_D: 升阻比
           V: 速度 (m/s)
           t: 时间 (h)

       返回:
           distance: 航程 (m)
           fuel_consumed: 燃油消耗 (kg)

       参考: 05_performance_characteristics.md 第3.6节
       """
       pass

   def calculate_loiter_segment(W_initial, SFC, L_D, t):
       """
       计算盘旋段性能

       参数:
           W_initial: 初始重量 (N)
           SFC: 耗油率 (kg/(N·h))
           L_D: 升阻比
           t: 时间 (h)

       返回:
           fuel_consumed: 燃油消耗 (kg)

       参考: 05_performance_characteristics.md 第3.9节
       """
       pass

   def calculate_mission_fuel_iteration(mission_profile, initial_fuel_guess):
       """
       计算任务燃油（迭代法）

       参数:
           mission_profile: 任务剖面定义
           initial_fuel_guess: 初始燃油猜测值 (kg)

       返回:
           fuel_required: 所需燃油 (kg)
           converged: 是否收敛
           iterations: 迭代次数

       参考: 05_performance_characteristics.md 第3.10节
       """
       pass
   ```

3. 编写单元测试 `tests/test_performance_mission.py`

**任务5.3：设计点性能计算实现**

**参考内容**：
- 理论文档：[05_performance_characteristics.md](./05_performance_characteristics.md) 第4节
- 公式：爬升率、实用升限、转弯半径

**实现内容**：
1. 创建 `aircraft_design/performance/point_performance.py` 模块
2. 实现函数：
   ```python
   def calculate_climb_rate(W, T_available, T_required, V):
       """
       计算爬升率

       参数:
           W: 飞机重量 (N)
           T_available: 可用推力 (N)
           T_required: 需用推力 (N)
           V: 速度 (m/s)

       返回:
           Vy: 爬升率 (m/s)
           sin_gamma: 爬升梯度

       参考: 05_performance_characteristics.md 第4.1.3节
       """
       pass

   def calculate_service_ceiling(height_Vy_data, Vy_target=0.5):
       """
       计算实用升限

       参数:
           height_Vy_data: 高度-爬升率数据列表 [(h, Vy), ...]
           Vy_target: 目标爬升率 (m/s)

       返回:
           h_service: 实用升限 (m)

       参考: 05_performance_characteristics.md 第4.2.2节
       """
       pass

   def calculate_turn_radius(V, n, g=9.81):
       """
       计算转弯半径

       参数:
           V: 速度 (m/s)
           n: 过载系数
           g: 重力加速度 (m/s²)

       返回:
           R: 转弯半径 (m)

       参考: 05_performance_characteristics.md 第4.3.3节
       """
       pass
   ```

3. 编写单元测试 `tests/test_performance_point.py`

#### 3.3.2 第7-8周：操稳特性增强

**任务6.1：静稳定性计算实现**

**参考内容**：
- 理论文档：[06_stability_control_characteristics.md](./06_stability_control_characteristics.md) 第2节
- 公式：纵向、航向、横向静稳定性

**实现内容**：
1. 创建 `aircraft_design/stability/static_stability.py` 模块
2. 实现函数：
   ```python
   def calculate_longitudinal_static_margin(x_cg, x_np, MAC_wing):
       """
       计算纵向静稳定裕度

       参数:
           x_cg: 重心位置 (m)
           x_np: 中性点位置 (m)
           MAC_wing: 机翼平均气动弦长 (m)

       返回:
           SM: 静稳定裕度

       参考: 06_stability_control_characteristics.md 第2.1.5节
       """
       pass

   def calculate_neutral_point(CLa_wing, x_ac_wing, CLa_ht, x_ac_ht, MAC_wing):
       """
       计算中性点

       参数:
           CLa_wing: 机翼升力线斜率 (1/rad)
           x_ac_wing: 机翼焦点位置 (m)
           CLa_ht: 平尾升力线斜率 (1/rad)
           x_ac_ht: 平尾焦点位置 (m)
           MAC_wing: 机翼平均气动弦长 (m)

       返回:
           x_np: 中性点位置 (m)

       参考: 06_stability_control_characteristics.md 第2.1.5节
       """
       pass

   def calculate_directional_static_stability(Cn_beta):
       """
       计算航向静稳定性

       参数:
           Cn_beta: 偏航力矩系数对侧滑角导数

       返回:
           is_stable: 是否稳定

       参考: 06_stability_control_characteristics.md 第2.2.1节
       """
       pass

   def calculate_lateral_static_stability(Cl_beta):
       """
       计算横向静稳定性

       参数:
           Cl_beta: 滚转力矩系数对侧滑角导数

       返回:
           is_stable: 是否稳定

       参考: 06_stability_control_characteristics.md 第2.3.1节
       """
       pass
   ```

3. 编写单元测试 `tests/test_stability_static.py`

**任务6.2：配平分析实现**

**参考内容**：
- 理论文档：[06_stability_control_characteristics.md](./06_stability_control_characteristics.md) 第4节
- 公式：1g配平、定常拉伸配平、起飞着陆配平

**实现内容**：
1. 创建 `aircraft_design/stability/trim_analysis.py` 模块
2. 实现函数：
   ```python
   def calculate_1g_trim(W, CLa_wing, x_ac_wing, CLa_ht, x_ac_ht, x_cg, MAC_wing):
       """
       计算1g平飞配平

       参数:
           W: 飞机重量 (N)
           CLa_wing: 机翼升力线斜率 (1/rad)
           x_ac_wing: 机翼焦点位置 (m)
           CLa_ht: 平尾升力线斜率 (1/rad)
           x_ac_ht: 平尾焦点位置 (m)
           x_cg: 重心位置 (m)
           MAC_wing: 机翼平均气动弦长 (m)

       返回:
           alpha_trim: 配平迎角 (rad)
           delta_e_trim: 配平升降舵偏角 (rad)

       参考: 06_stability_control_characteristics.md 第4.2.1节
       """
       pass

   def calculate_pullup_trim(n, W, CLa_wing, x_ac_wing, CLa_ht, x_ac_ht, x_cg, MAC_wing):
       """
       计算定常拉伸配平

       参数:
           n: 过载系数
           W: 飞机重量 (N)
           CLa_wing: 机翼升力线斜率 (1/rad)
           x_ac_wing: 机翼焦点位置 (m)
           CLa_ht: 平尾升力线斜率 (1/rad)
           x_ac_ht: 平尾焦点位置 (m)
           x_cg: 重心位置 (m)
           MAC_wing: 机翼平均气动弦长 (m)

       返回:
           alpha_trim: 配平迎角 (rad)
           delta_e_trim: 配平升降舵偏角 (rad)

       参考: 06_stability_control_characteristics.md 第4.2.2节
       """
       pass
   ```

3. 编写单元测试 `tests/test_stability_trim.py`

**任务6.3：集成测试与文档更新**
1. 编写集成测试 `tests/test_integration_p1.py`
2. 更新SKILL文档和理论文档
3. 代码审查和优化

### 3.4 阶段3详细计划（P2低优先级）

#### 3.4.1 第9-10周：高级气动特性

**任务7.1：跨声速特性实现**

**参考内容**：
- 理论文档：[02_aerodynamic_characteristics.md](./02_aerodynamic_characteristics.md) 第2.1.3节、第3.5节
- 公式：跨声速升力线斜率、跨声速压缩性阻力

**任务7.2：超声速波阻实现**

**参考内容**：
- 理论文档：[02_aerodynamic_characteristics.md](./02_aerodynamic_characteristics.md) 第3.4节
- 公式：超声速波阻计算

**任务7.3：涡升力实现**

**参考内容**：
- 理论文档：[02_aerodynamic_characteristics.md](./02_aerodynamic_characteristics.md) 第2.4节
- 公式：前缘涡升力、侧缘涡升力

#### 3.4.2 第11-12周：动稳定性与操纵性

**任务8.1：惯性矩计算实现**

**参考内容**：
- 理论文档：[06_stability_control_characteristics.md](./06_stability_control_characteristics.md) 第3.1节
- 公式：Ix、Iy、Iz计算

**任务8.2：动稳定性分析实现**

**参考内容**：
- 理论文档：[06_stability_control_characteristics.md](./06_stability_control_characteristics.md) 第3.3节、第3.4节
- 公式：纵向动稳定性、横航向动稳定性

**任务8.3：操纵性分析实现**

**参考内容**：
- 理论文档：[06_stability_control_characteristics.md](./06_stability_control_characteristics.md) 第4节、第5节
- 公式：滚转率、响应时间

**任务8.4：集成测试与文档更新**
1. 编写集成测试 `tests/test_integration_p2.py`
2. 更新SKILL文档和理论文档
3. 代码审查和优化
4. 完整回归测试

## 4. 交付物清单

### 4.1 代码交付物

#### 阶段1（P0）
- [ ] `aircraft_design/aero/lift_slope.py` - 升力线斜率计算模块
- [ ] `aircraft_design/aero/drag_buildup_detailed.py` - 详细阻力分解模块
- [ ] `aircraft_design/weights/structural_weights.py` - 结构重量计算模块
- [ ] `aircraft_design/weights/fuel_system_weights.py` - 燃油系统重量计算模块
- [ ] `aircraft_design/propulsion/thrust_model.py` - 推力模型模块
- [ ] `aircraft_design/propulsion/sfc_model.py` - 耗油率模型模块
- [ ] 单元测试套件（约30个测试用例）
- [ ] 集成测试套件（约10个测试用例）

#### 阶段2（P1）
- [ ] `aircraft_design/performance/field_performance.py` - 场域性能计算模块
- [ ] `aircraft_design/performance/mission_performance.py` - 任务性能计算模块
- [ ] `aircraft_design/performance/point_performance.py` - 设计点性能计算模块
- [ ] `aircraft_design/stability/static_stability.py` - 静稳定性计算模块
- [ ] `aircraft_design/stability/trim_analysis.py` - 配平分析模块
- [ ] 单元测试套件（约40个测试用例）
- [ ] 集成测试套件（约15个测试用例）

#### 阶段3（P2）
- [ ] `aircraft_design/aero/transonic_characteristics.py` - 跨声速特性模块
- [ ] `aircraft_design/aero/supersonic_wave_drag.py` - 超声速波阻模块
- [ ] `aircraft_design/aero/vortex_lift.py` - 涡升力模块
- [ ] `aircraft_design/stability/dynamic_stability.py` - 动稳定性分析模块
- [ ] `aircraft_design/stability/controllability.py` - 操纵性分析模块
- [ ] 单元测试套件（约30个测试用例）
- [ ] 集成测试套件（约10个测试用例）

### 4.2 文档交付物

#### 阶段1（P0）
- [ ] 更新 `fixed_wing_aero_spec/SKILL.md` - 气动方案文档
- [ ] 更新 `fixed_wing_weights_spec/SKILL.md` - 重量方案文档
- [ ] 更新 `fixed_wing_propulsion_spec/SKILL.md` - 推进方案文档
- [ ] 更新理论文档，标记已实现功能
- [ ] 编写使用示例和API文档

#### 阶段2（P1）
- [ ] 更新 `fixed_wing_performance_spec/SKILL.md` - 性能方案文档
- [ ] 更新 `fixed_wing_stability_control_spec/SKILL.md` - 操稳方案文档
- [ ] 更新理论文档，标记已实现功能
- [ ] 编写使用示例和API文档

#### 阶段3（P2）
- [ ] 更新所有SKILL文档
- [ ] 更新理论文档，标记已实现功能
- [ ] 编写完整的使用手册和API文档
- [ ] 编写开发者指南

## 5. 质量保证

### 5.1 代码质量标准
- 通过ruff检查（代码风格）
- 通过mypy检查（类型检查）
- 代码覆盖率 > 80%
- 所有函数都有完整的文档字符串
- 所有公式都标注理论来源

### 5.2 测试标准
- 单元测试覆盖率 > 80%
- 集成测试覆盖主要使用场景
- 回归测试确保不破坏现有功能
- 性能测试确保计算效率

### 5.3 文档标准
- 所有函数都有详细的文档字符串
- 所有公式都标注理论文档章节
- 提供使用示例
- 提供API参考文档

## 6. 风险管理

### 6.1 技术风险
- **风险**：理论公式实现复杂，可能存在理解偏差
- **缓解**：仔细阅读理论文档，与领域专家确认，编写详细测试用例

- **风险**：数值计算精度问题
- **缓解**：使用高精度数值计算库，进行数值稳定性测试

### 6.2 进度风险
- **风险**：开发时间不足
- **缓解**：按优先级分阶段实施，确保核心功能优先完成

- **风险**：需求变更
- **缓解**：保持模块化设计，便于调整和扩展

### 6.3 质量风险
- **风险**：测试覆盖不足
- **缓解**：制定详细的测试计划，定期审查测试覆盖率

- **风险**：文档不完整
- **缓解**：将文档编写纳入开发流程，确保同步更新

## 7. 里程碑

### 7.1 阶段1里程碑（第4周）
- ✅ 完成P0高优先级功能开发
- ✅ 通过单元测试和集成测试
- ✅ 更新SKILL文档和理论文档
- ✅ 提交阶段1交付物

### 7.2 阶段2里程碑（第8周）
- ✅ 完成P1中优先级功能开发
- ✅ 通过单元测试和集成测试
- ✅ 更新SKILL文档和理论文档
- ✅ 提交阶段2交付物

### 7.3 阶段3里程碑（第12周）
- ✅ 完成P2低优先级功能开发
- ✅ 通过单元测试和集成测试
- ✅ 更新SKILL文档和理论文档
- ✅ 提交阶段3交付物
- ✅ 完成完整回归测试
- ✅ 提交最终交付物

## 8. 参考资源

### 8.1 理论文档
- [01_design_parameters.md](./01_design_parameters.md)
- [02_aerodynamic_characteristics.md](./02_aerodynamic_characteristics.md)
- [03_weight_characteristics.md](./03_weight_characteristics.md)
- [04_engine_characteristics.md](./04_engine_characteristics.md)
- [05_performance_characteristics.md](./05_performance_characteristics.md)
- [06_stability_control_characteristics.md](./06_stability_control_characteristics.md)

### 8.2 SKILL文档
- [fixed_wing_aero_spec](../../.trae/skills/fixed_wing_aero_spec/SKILL.md)
- [fixed_wing_weights_spec](../../.trae/skills/fixed_wing_weights_spec/SKILL.md)
- [fixed_wing_propulsion_spec](../../.trae/skills/fixed_wing_propulsion_spec/SKILL.md)
- [fixed_wing_performance_spec](../../.trae/skills/fixed_wing_performance_spec/SKILL.md)
- [fixed_wing_stability_control_spec](../../.trae/skills/fixed_wing_stability_control_spec/SKILL.md)
- [fixed_wing_structures_loads_spec](../../.trae/skills/fixed_wing_structures_loads_spec/SKILL.md)

### 8.3 现有代码
- [aircraft_design/aero_drag_buildup.py](../../aircraft_design/aero_drag_buildup.py)
- [aircraft_design/weights_class1.py](../../aircraft_design/weights_class1.py)
- [aircraft_design/performance.py](../../aircraft_design/performance.py)
- [aircraft_design/stability_control.py](../../aircraft_design/stability_control.py)
- [aircraft_design/propulsion.py](../../aircraft_design/propulsion.py)
- [aircraft_design/structures_loads.py](../../aircraft_design/structures_loads.py)

### 8.4 测试框架
- [tests/](../../tests/) - 现有测试用例
- pytest - 测试框架
- pytest-cov - 测试覆盖率工具

## 9. 版本信息

- 版本：1.0
- 创建日期：2026-02-03
- 基于文档：项目中期报告_601关键能力_V2.docx
- 来源：南京远思智能科技有限公司
- 计划周期：12周
- 最后更新：2026-02-03
