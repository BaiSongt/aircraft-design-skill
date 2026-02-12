---
name: "fixed_wing_geometry_integrated_spec"
description: "整合飞机几何特征模块（机翼控制面/翼尖装置/起落架/发动机/短舱/驾驶舱盖/舱门/硬点）并提供统一配置解析与验证接口。当用户需要完整几何特征定义或高级设计验证时调用。"
stage: "class3_detailed"
code_module: "aircraft_design/class2_preliminary/control_surfaces.py, aircraft_design/class2_preliminary/wingtip.py, aircraft_design/class2_preliminary/landing_gear.py, aircraft_design/class2_preliminary/nacelle.py, aircraft_design/class2_preliminary/fuselage_canopy.py, aircraft_design/class2_preliminary/fuselage_openings.py, aircraft_design/class2_preliminary/hardpoint_validation.py"
dependencies:
  - "fixed_wing_shape_detail_spec"
---

# 固定翼几何特征整合方案（Spec）

## 目的

将飞机几何特征的8个核心模块（机翼控制面、翼尖装置、起落架、发动机、短舱、驾驶舱盖、舱门、硬点）整合为统一的配置解析与验证框架，提供：

- 统一的参数化输入接口
- 跨模块约束验证
- 综合性能计算（重量、阻力、应力）
- 几何一致性检查
- 3D可视化支持

## 与统一入口的接口关系

- 本 Spec 定义几何特征的统一配置与验证标准
- 实际计算与集成由 `fixed_wing_overall_sizing_runbook` 统一执行
- 在 Class I 收敛后自动触发几何特征详细设计
- 输出文件写入 `output/<project>_*/geometry_integrated/`

## 模块概览

### 1. 机翼控制面模块 (wing_controls.py)

**功能**: 定义副翼、襟翼、缝翼、扰流板等控制面参数

**输入配置**:
```json
{
  "wing_controls": {
    "ailerons": {
      "enabled": true,
      "count": 2,
      "chord_fraction": 0.25,
      "span_fraction": 0.3,
      "max_deflection_deg": 25.0
    },
    "flaps": {
      "enabled": true,
      "type": "plain",
      "chord_fraction": 0.3,
      "span_fraction": 0.6,
      "max_deflection_deg": 40.0
    },
    "slats": {
      "enabled": false
    },
    "spoilers": {
      "enabled": true,
      "count": 4,
      "chord_fraction": 0.15
    }
  }
}
```

**输出**: 控制面几何参数、重量计算结果

### 2. 翼尖装置模块 (wingtip.py)

**功能**: 定义翼尖小翼、翼尖挂架等翼尖装置

**输入配置**:
```json
{
  "wingtip": {
    "type": "winglet",
    "height_m": 1.5,
    "cant_angle_deg": 45.0,
    "toe_angle_deg": 0.0,
    "chord_fraction": 0.6,
    "sweep_deg": 30.0
  }
}
```

**输出**: 翼尖几何参数、诱导阻力减少系数

### 3. 起落架模块 (landing_gear.py)

**功能**: 定义主起落架、前轮起落架位置与参数

**输入配置**:
```json
{
  "landing_gear": {
    "main": {
      "type": "tricycle",
      "count": 2,
      "wheel_diameter_m": 0.5,
      "track_m": 3.0,
      "position_x_m": 0.0,
      "position_y_m": 1.5
    },
    "nose": {
      "wheel_diameter_m": 0.3,
      "position_x_m": -2.0,
      "steering_angle_deg": 30.0
    }
  }
}
```

**输出**: 起落架几何参数、重量计算结果

### 4. 发动机类型库模块 (engine_library.py)

**功能**: 涡扇、涡桨、活塞发动机参数库与选型

**输入配置**:
```json
{
  "engine_library": {
    "type": "turbofan",
    "selected_engine": "GE_F404",
    "custom_engine": {
      "sea_level_thrust_kn": 50.0,
      "bypass_ratio": 0.3,
      "turbine_inlet_temp_k": 1600.0,
      "dry_weight_kg": 1000.0
    }
  }
}
```

**输出**: 发动机性能曲线、推力衰减模型

### 5. 发动机短舱模块 (nacelle.py)

**功能**: 定义发动机短舱外形与阻力

**输入配置**:
```json
{
  "nacelle": {
    "length_m": 3.5,
    "diameter_m": 1.2,
    "inlet_length_ratio": 0.2,
    "nozzle_length_ratio": 0.15,
    "position_x_m": 2.0,
    "position_z_m": -0.5
  }
}
```

**输出**: 短舱几何参数、阻力系数

### 6. 驾驶舱盖模块 (fuselage_canopy.py)

**功能**: 定义风挡、舱盖几何与光学性能

**输入配置**:
```json
{
  "fuselage_canopy": {
    "windshield": {
      "type": "flat",
      "thickness_m": 0.025,
      "forward_angle_deg": 30.0,
      "side_angle_deg": 45.0
    },
    "canopy": {
      "type": "bubble",
      "length_m": 1.8,
      "width_m": 1.2,
      "height_m": 0.8,
      "curvature_radius_m": 0.6
    }
  }
}
```

**输出**: 驾驶舱盖几何参数、光学透过率、重量

### 7. 舱门舷窗模块 (fuselage_openings.py)

**功能**: 定义货舱门、应急门、登机门、舷窗等开口

**输入配置**:
```json
{
  "fuselage_openings": {
    "cargo_door": {
      "enabled": true,
      "type": "ramp",
      "width_m": 2.0,
      "height_m": 2.5,
      "position_x_m": 3.0
    },
    "passenger_door": {
      "enabled": true,
      "count": 2,
      "width_m": 0.8,
      "height_m": 1.5
    },
    "windows": {
      "enabled": true,
      "count": 20,
      "width_m": 0.3,
      "height_m": 0.25,
      "pitch_m": 0.5
    }
  }
}
```

**输出**: 开口几何参数、结构补强重量

### 8. 硬点验证模块 (hardpoint_validation.py)

**功能**: 武器挂点、设备安装点约束验证与载荷分析

**输入配置**:
```json
{
  "hardpoint_validation": {
    "wing_hardpoints": {
      "outer_stations": {
        "count": 4,
        "max_load_kg": 1000.0,
        "position_y_m": 4.0,
        "position_x_m": 0.5
      },
      "center_stations": {
        "count": 2,
        "max_load_kg": 2000.0,
        "position_y_m": 2.0
      }
    },
    "fuselage_hardpoints": {
      "centerline_station": {
        "max_load_kg": 3000.0,
        "position_x_m": 2.0
      }
    }
  }
}
```

**输出**: 硬点几何参数、载荷分布、应力分析

## 统一输入接口

### 完整配置结构

```json
{
  "geometry_integrated": {
    "wing_controls": { /* 控制面配置 */ },
    "wingtip": { /* 翼尖配置 */ },
    "landing_gear": { /* 起落架配置 */ },
    "engine_library": { /* 发动机配置 */ },
    "nacelle": { /* 短舱配置 */ },
    "fuselage_canopy": { /* 驾驶舱盖配置 */ },
    "fuselage_openings": { /* 舱门配置 */ },
    "hardpoint_validation": { /* 硬点配置 */ }
  },
  "geometry_shape": { /* 基础几何参数 */ },
  "requirements": { /* 设计需求 */ }
}
```

### 可选字段

所有8个模块均为可选，但提供完整配置可获得最准确的验证结果。

## 统一输出接口

### 1. 几何综合报告 (geometry_integrated_report.md)

包含内容：
- 各模块几何参数汇总
- 跨模块几何一致性分析
- 推荐优化建议

### 2. 验证结果报告 (geometry_validation_report.md)

包含内容：
- 各模块约束验证结果
- 违规项详细说明
- 修正建议

### 3. 性能参数汇总 (geometry_performance_summary.json)

```json
{
  "weight_breakdown": {
    "wing_controls_kg": 150.0,
    "wingtip_kg": 30.0,
    "landing_gear_kg": 400.0,
    "nacelle_kg": 80.0,
    "fuselage_canopy_kg": 45.0,
    "fuselage_openings_kg": 120.0,
    "hardpoint_attachments_kg": 60.0
  },
  "drag_breakdown": {
    "nacelle_cd0": 0.0012,
    "wingtip_cd0_reduction": 0.0008
  },
  "validation_status": {
    "total_violations": 0,
    "critical_violations": 0,
    "warning_violations": 0
  }
}
```

### 4. 可视化文件

- `geometry_integrated_3d.html`: 3D几何预览
- `geometry_integrated_mesh.json`: 网格数据
- `geometry_integrated.obj`: OBJ模型文件

## 级联验证规则

### 跨模块约束检查

1. **起落架与机身干涉检查**
   - 起落架收起位置必须在机身轮廓内
   - 起落架放下位置不得与发动机短舱干涉

2. **发动机短舱与翼根干涉检查**
   - 短舱位置不得与翼根结构干涉
   - 短舱与翼根间隙需满足结构要求

3. **硬点与机翼结构干涉检查**
   - 外挂点不得与控制面运动轨迹干涉
   - 硬点载荷需满足机翼结构强度要求

4. **舱门与结构补强检查**
   - 大开口位置需满足结构补强要求
   - 应急门位置需满足逃生距离要求

5. **驾驶舱盖与视野检查**
   - 驾驶舱盖位置需满足前向视野要求
   - 光学透过率需满足飞行安全标准

### 性能级联计算

1. **重量级联计算**
   - 各模块重量累加到空重
   - 影响MTOW迭代收敛

2. **阻力级联计算**
   - 短舱阻力累加到总阻力
   - 翼尖装置影响诱导阻力

3. **重心位置级联计算**
   - 各模块重量与位置影响CG位置
   - 影响静稳定裕度计算

## 验收标准

### 功能验收

- ✅ 所有8个模块参数可独立配置
- ✅ 跨模块约束检查功能正常
- ✅ 综合重量计算误差<5%
- ✅ 阻力计算与实验数据误差<10%
- ✅ 3D可视化模型可正常显示

### 文档验收

- ✅ 使用说明完整清晰
- ✅ 接口文档包含所有参数说明
- ✅ 示例配置文件可用
- ✅ 错误处理说明完整

### 性能验收

- ✅ 配置解析时间<1秒
- ✅ 验证计算时间<5秒
- ✅ 3D可视化生成时间<10秒

## 使用示例

### 快速开始

1. 在输入JSON中添加 `geometry_integrated` 配置段
2. 运行总体设计流程:
   ```bash
   python -m aircraft_design.run_sizing input.json --project-name MyProject
   ```
3. 查看输出目录中的几何特征综合报告

### 最小配置示例

```json
{
  "geometry_integrated": {
    "wing_controls": {
      "ailerons": { "enabled": true }
    }
  }
}
```

### 完整配置示例

```json
{
  "geometry_integrated": {
    "wing_controls": { /* 完整配置 */ },
    "wingtip": { /* 完整配置 */ },
    "landing_gear": { /* 完整配置 */ },
    "engine_library": { /* 完整配置 */ },
    "nacelle": { /* 完整配置 */ },
    "fuselage_canopy": { /* 完整配置 */ },
    "fuselage_openings": { /* 完整配置 */ },
    "hardpoint_validation": { /* 完整配置 */ }
  }
}
```

## 错误处理

### 配置错误

- 缺少必需参数：返回参数名称与示例值
- 参数类型错误：返回期望类型与实际类型
- 参数范围错误：返回有效范围与当前值

### 验证错误

- 几何干涉：返回干涉位置与建议修正方案
- 结构超限：返回超限位置与建议加强方案
- 性能不达标：返回当前值与目标值差距

## 扩展性

### 新增模块

1. 在对应模块文件中实现解析、验证、计算函数
2. 在 `geometry_shape.py` 中添加导入语句
3. 在统一配置接口中添加新模块配置段
4. 更新文档与示例

### 新增验证规则

1. 在对应验证函数中添加新规则
2. 更新级联验证规则说明
3. 添加测试用例覆盖新规则

## 相关技能

- `fixed_wing_overall_sizing_runbook`: 总体设计统一入口
- `fixed_wing_shape_detail_spec`: 外形详细设计规范
- `fixed_wing_constraints_spec`: 约束分析规范
- `fixed_wing_weights_spec`: 重量计算规范
- `fixed_wing_aero_spec`: 气动分析规范

## 版本历史

- **v1.0** (2026-02-12): 初始版本，整合8个几何特征模块
