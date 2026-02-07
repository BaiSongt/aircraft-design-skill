# SKILL开发指导文档

## 1. 理论文档与SKILL实现对应关系

### 1.1 对应关系总览

| 理论文档 | 现有SKILL | 对应程度 | 说明 |
|---------|-----------|---------|------|
| 01_design_parameters.md | fixed_wing_shape_parametric_spec | ✅ 完全对应 | 几何参数定义完全一致 |
| 02_aerodynamic_characteristics.md | fixed_wing_aero_spec | ✅ 已完成 | 已实现完整的阻力分解和升力线斜率计算 |
| 03_weight_characteristics.md | fixed_wing_weights_spec | ✅ 已完成 | 已实现详细的结构重量和系统重量计算 |
| 04_engine_characteristics.md | fixed_wing_propulsion_spec | ✅ 已完成 | 已实现推力随高度/速度变化的详细模型 |
| 05_performance_characteristics.md | fixed_wing_performance_spec | ✅ 已完成 | 已实现详细的任务剖面和场域性能计算 |
| 06_stability_control_characteristics.md | fixed_wing_stability_control_spec | ✅ 已完成 | 已实现详细的静稳定性和动稳定性计算 |

### 1.2 详细对应分析

#### 1.2.1 设计参数层

**理论文档：01_design_parameters.md**
- 翼型参数（最大相对厚度、最大相对弯度、前缘半径）
- 机翼参数（参考面积、展弦比、后掠角、梯形比、安装角）
- 增升装置参数（类型、尺寸、偏转角）
- 机身参数（长径比、当量直径）
- 尾翼参数（水平尾翼、垂直尾翼）
- 发动机参数（涵道比）
- 等效机翼方法

**现有SKILL：fixed_wing_shape_parametric_spec**
- ✅ 已覆盖基本的几何参数
- ✅ 已实现等效机翼方法
- ⚠️ 需要增加翼型参数的详细定义
- ⚠️ 需要增加增升装置参数的详细定义

#### 1.2.2 气动特性层

**理论文档：02_aerodynamic_characteristics.md**
- 干净构型升力特性（升力线斜率、最大升力系数、涡升力修正）
- 干净构型阻力特性（零升阻力、升致阻力、超声速波阻、跨声速压缩性阻力）
- 低速构型升阻增量计算

**现有SKILL：fixed_wing_aero_spec**
- ✅ 已实现基本的极曲线模型：`CD = CD0 + k * CL^2`
- ✅ 已实现详细的升力线斜率计算（亚声速、超声速、跨声速）
- ✅ 已实现详细的阻力分解（摩擦阻力、形状阻力、干扰阻力、波阻）
- ✅ 已实现涡升力修正计算
- ✅ 已实现低速构型的升阻增量计算

#### 1.2.3 重量特性层

**理论文档：03_weight_characteristics.md**
- 结构重量（机翼、机身、尾翼、起落装置）
- 燃油系统重量（自密封油箱、支撑结构、空中加油、排放系统、重心控制）
- 推进系统重量（总重量、控制系统、启动系统）
- 其他系统设备重量（控制、仪表、航电、设备、空调）
- 复合材料应用的重量修正

**现有SKILL：fixed_wing_weights_spec**
- ✅ 已实现基本的重量闭合迭代
- ✅ 已实现详细的结构重量计算公式
- ✅ 已实现详细的系统重量计算
- ✅ 已实现复合材料重量修正

#### 1.2.4 发动机特性层

**理论文档：04_engine_characteristics.md**
- 推力特性（推力公式、涡扇发动机模型、油门杆控制、高度/速度变化）
- 耗油率特性（单位推力耗油率、涡扇发动机模型、非设计点耗油率）
- 发动机与飞机的匹配（推力需求、推力余度、燃油消耗）

**现有SKILL：fixed_wing_propulsion_spec**
- ✅ 已实现基本的推进类型区分（螺桨/喷气）
- ✅ 已实现详细的推力随高度/速度变化模型
- ✅ 已实现详细的耗油率模型
- ✅ 已实现油门杆位置控制

#### 1.2.5 性能特性层

**理论文档：05_performance_characteristics.md**
- 场域性能（起降失速速度、起飞性能、着陆性能）
- 任务性能（任务剖面、各阶段计算、燃油迭代）
- 设计点性能（爬升速率、实用升限、转弯半径）

**现有SKILL：fixed_wing_performance_spec**
- ✅ 已实现基本的巡航配平和爬升率计算
- ✅ 已实现详细的起降性能计算
- ✅ 已实现详细的任务剖面计算
- ✅ 已实现设计点性能计算（实用升限、转弯半径）

#### 1.2.6 操稳特性层

**理论文档：06_stability_control_characteristics.md**
- 静稳定性（纵向、航向、横向）
- 动稳定性（纵向、横航向）
- 静操纵性分析
- 动操纵性分析

**现有SKILL：fixed_wing_stability_control_spec**
- ✅ 已实现基本的尾容积系数法
- ✅ 已实现详细的静稳定性计算
- ✅ 已实现详细的动稳定性计算
- ✅ 已实现详细的操纵性分析

## 2. SKILL开发优先级建议

### 2.1 高优先级（P0）

#### 2.1.1 气动特性增强
**目标**：实现完整的阻力分解和升力线斜率计算

**具体任务**：
1. 实现亚声速升力线斜率计算
   - 输入：展弦比、后掠角、机身升力影响系数
   - 输出：CLα
   - 公式：参考理论文档02_aerodynamic_characteristics.md第2.1.1节

2. 实现超声速升力线斜率计算
   - 输入：展弦比、前缘后掠角、梯形比
   - 输出：CLα
   - 方法：使用图表法或拟合公式

3. 实现零升阻力分解
   - 输入：各部件几何参数、层流比例
   - 输出：CD0分解（摩擦阻力、形状阻力、干扰阻力）
   - 公式：参考理论文档02_aerodynamic_characteristics.md第3.2节

4. 实现升致阻力计算
   - 输入：展弦比、奥斯瓦尔德效率因子
   - 输出：K值
   - 公式：参考理论文档02_aerodynamic_characteristics.md第3.3节

#### 2.1.2 重量特性增强
**目标**：实现详细的结构重量计算

**具体任务**：
1. 实现机翼结构重量计算
   - 输入：机翼面积、展弦比、后掠角、梯形比、最大起飞重量
   - 输出：机翼结构重量
   - 公式：参考理论文档03_weight_characteristics.md第2.1节

2. 实现机身结构重量计算
   - 输入：机身长度、最大高度、最大起飞重量
   - 输出：机身结构重量
   - 公式：参考理论文档03_weight_characteristics.md第2.2节

3. 实现尾翼结构重量计算
   - 输入：尾翼面积、展弦比、尾力臂
   - 输出：尾翼结构重量
   - 公式：参考理论文档03_weight_characteristics.md第2.3节

#### 2.1.3 发动机特性增强
**目标**：实现推力随高度/速度变化的详细模型

**具体任务**：
1. 实现涡扇发动机推力模型
   - 输入：海平面静推力、马赫数、高度、油门杆位置
   - 输出：可用推力
   - 公式：参考理论文档04_engine_characteristics.md第2.2节

2. 实现涡扇发动机耗油率模型
   - 输入：海平面静耗油率、马赫数、高度、油门杆位置
   - 输出：耗油率
   - 公式：参考理论文档04_engine_characteristics.md第3.2节

### 2.2 中优先级（P1）

#### 2.2.1 性能特性增强
**目标**：实现详细的起降性能和任务剖面计算

**具体任务**：
1. 实现起降失速速度计算
   - 输入：重量、空气密度、机翼面积、最大升力系数
   - 输出：失速速度
   - 公式：参考理论文档05_performance_characteristics.md第2.1节

2. 实现起飞性能计算
   - 输入：推力、阻力、升力、重量、地面摩擦系数
   - 输出：起飞距离、起飞时间
   - 公式：参考理论文档05_performance_characteristics.md第2.2节

3. 实现着陆性能计算
   - 输入：推力、阻力、升力、重量、地面摩擦系数
   - 输出：着陆距离、着陆时间
   - 公式：参考理论文档05_performance_characteristics.md第2.3节

4. 实现任务剖面计算
   - 输入：任务剖面定义、各阶段参数
   - 输出：航程、航时、燃油消耗
   - 公式：参考理论文档05_performance_characteristics.md第3节

#### 2.2.2 操稳特性增强
**目标**：实现基本的静稳定性计算

**具体任务**：
1. 实现纵向静稳定性计算
   - 输入：机翼焦点、平尾焦点、重心位置、平均气动弦长
   - 输出：静稳定裕度
   - 公式：参考理论文档06_stability_control_characteristics.md第2.1节

2. 实现航向静稳定性计算
   - 输入：各部件偏航力矩系数导数
   - 输出：航向静稳定性判据
   - 公式：参考理论文档06_stability_control_characteristics.md第2.2节

3. 实现横向静稳定性计算
   - 输入：各部件滚转力矩系数导数
   - 输出：横向静稳定性判据
   - 公式：参考理论文档06_stability_control_characteristics.md第2.3节

### 2.3 低优先级（P2）

#### 2.3.1 高级气动特性
**目标**：实现跨声速和超声速特性

**具体任务**：
1. 实现跨声速升力线斜率计算
2. 实现跨声速压缩性阻力计算
3. 实现超声速波阻计算

#### 2.3.2 动稳定性分析
**目标**：实现基本的动稳定性分析

**具体任务**：
1. 实现惯性矩计算
2. 实现纵向动稳定性分析（长周期、短周期）
3. 实现横航向动稳定性分析（螺旋、滚转收敛、荷兰滚）

#### 2.3.3 操纵性分析
**目标**：实现基本的操纵性分析

**具体任务**：
1. 实现静操纵性分析（配平）
2. 实现动操纵性分析（滚转率、响应时间）

## 3. SKILL实现建议

### 3.1 代码结构建议

#### 3.1.1 模块化设计
每个理论章节对应一个独立的Python模块：

```
aircraft_design/
├── aero/
│   ├── lift_slope.py          # 升力线斜率计算
│   ├── drag_buildup.py        # 阻力分解计算
│   └── vortex_lift.py         # 涡升力计算
├── weights/
│   ├── structural_weights.py  # 结构重量计算
│   ├── system_weights.py      # 系统重量计算
│   └── composites_correction.py  # 复合材料修正
├── propulsion/
│   ├── thrust_model.py        # 推力模型
│   └── sfc_model.py          # 耗油率模型
├── performance/
│   ├── field_performance.py   # 场域性能
│   ├── mission_performance.py # 任务性能
│   └── point_performance.py   # 设计点性能
└── stability/
    ├── static_stability.py    # 静稳定性
    ├── dynamic_stability.py   # 动稳定性
    └── controllability.py     # 操纵性
```

#### 3.1.2 函数命名规范
- 使用理论文档中的公式名称作为函数名
- 例如：`calculate_lift_slope_subsonic()`, `calculate_drag_coefficient_zero_lift()`

#### 3.1.3 输入输出规范
- 输入参数使用理论文档中的符号
- 输出参数使用理论文档中的符号
- 添加详细的文档字符串，说明公式来源

### 3.2 测试建议

#### 3.2.1 单元测试
为每个计算函数编写单元测试：
- 测试边界条件
- 测试典型值
- 测试与理论文档中的示例值对比

#### 3.2.2 集成测试
为每个SKILL编写集成测试：
- 测试完整的计算流程
- 测试与其他SKILL的接口
- 测试输入输出的一致性

#### 3.2.3 回归测试
建立回归测试套件：
- 使用理论文档中的典型值
- 确保修改不会破坏现有功能
- 定期运行回归测试

### 3.3 文档建议

#### 3.3.1 代码文档
- 为每个函数添加详细的文档字符串
- 说明公式的来源（理论文档章节）
- 说明输入参数的单位和范围
- 说明输出参数的单位和含义

#### 3.3.2 SKILL文档
- 更新SKILL.md文件，说明新增功能
- 添加输入输出参数的详细说明
- 添加使用示例

#### 3.3.3 理论文档更新
- 当实现新的理论公式时，更新对应的理论文档
- 添加实现状态标记（✅已实现、⚠️部分实现、❌未实现）
- 添加实现说明和注意事项

## 4. 开发流程建议

### 4.1 开发步骤
1. **理论分析**：仔细阅读理论文档，理解公式的物理意义
2. **代码实现**：按照代码结构建议实现计算函数
3. **单元测试**：编写单元测试，验证计算结果
4. **集成测试**：将新功能集成到现有SKILL中
5. **文档更新**：更新代码文档和SKILL文档
6. **回归测试**：运行完整的回归测试套件

### 4.2 代码审查
- 确保代码符合项目规范（ruff, mypy）
- 确保公式实现正确
- 确保输入输出参数一致
- 确保文档完整

### 4.3 持续改进
- 定期回顾理论文档和SKILL实现
- 识别需要改进的地方
- 逐步完善SKILL功能

## 5. 参考资源

### 5.1 理论文档
- [01_design_parameters.md](./01_design_parameters.md)
- [02_aerodynamic_characteristics.md](./02_aerodynamic_characteristics.md)
- [03_weight_characteristics.md](./03_weight_characteristics.md)
- [04_engine_characteristics.md](./04_engine_characteristics.md)
- [05_performance_characteristics.md](./05_performance_characteristics.md)
- [06_stability_control_characteristics.md](./06_stability_control_characteristics.md)

### 5.2 现有SKILL
- [fixed_wing_aero_spec](../../.trae/skills/fixed_wing_aero_spec/SKILL.md)
- [fixed_wing_weights_spec](../../.trae/skills/fixed_wing_weights_spec/SKILL.md)
- [fixed_wing_performance_spec](../../.trae/skills/fixed_wing_performance_spec/SKILL.md)
- [fixed_wing_stability_control_spec](../../.trae/skills/fixed_wing_stability_control_spec/SKILL.md)
- [fixed_wing_structures_loads_spec](../../.trae/skills/fixed_wing_structures_loads_spec/SKILL.md)
- [fixed_wing_propulsion_spec](../../.trae/skills/fixed_wing_propulsion_spec/SKILL.md)

### 5.3 现有代码
- [aircraft_design/aero_drag_buildup.py](../../aircraft_design/aero_drag_buildup.py)
- [aircraft_design/weights_class1.py](../../aircraft_design/weights_class1.py)
- [aircraft_design/performance.py](../../aircraft_design/performance.py)
- [aircraft_design/stability_control.py](../../aircraft_design/stability_control.py)
- [aircraft_design/propulsion.py](../../aircraft_design/propulsion.py)
- [aircraft_design/airfoil_library.py](../../aircraft_design/airfoil_library.py)
- [aircraft_design/geometry_modeling.py](../../aircraft_design/geometry_modeling.py)
- [aircraft_design/degenerate_geometry.py](../../aircraft_design/degenerate_geometry.py)
- [aircraft_design/parasite_drag_enhanced.py](../../aircraft_design/parasite_drag_enhanced.py)
- [aircraft_design/surface_analysis.py](../../aircraft_design/surface_analysis.py)
- [aircraft_design/vspaero_interface.py](../../aircraft_design/vspaero_interface.py)
- [aircraft_design/loads_analysis.py](../../aircraft_design/loads_analysis.py)
- [aircraft_design/rotorcraft_analysis.py](../../aircraft_design/rotorcraft_analysis.py)
- [tests/integration_tests.py](../../tests/integration_tests.py)

## 6. 版本信息

- 版本：1.0
- 创建日期：2026-02-03
- 基于文档：飞机设计文件.docx
- 来源：个人技术文件
