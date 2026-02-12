# 固定翼几何特征整合技能使用说明

## 概述

本技能提供了飞机几何特征的统一配置解析、验证与可视化框架，整合了8个核心模块：

1. **机翼控制面模块** (wing_controls) - 副翼、襟翼、缝翼、扰流板
2. **翼尖装置模块** (wingtip) - 翼尖小翼、翼尖挂架
3. **起落架模块** (landing_gear) - 主起落架、前轮起落架
4. **发动机类型库模块** (engine_library) - 涡扇、涡桨、活塞发动机
5. **发动机短舱模块** (nacelle) - 短舱外形与阻力
6. **驾驶舱盖模块** (fuselage_canopy) - 风挡、舱盖几何
7. **舱门舷窗模块** (fuselage_openings) - 舱门、舷窗开口
8. **硬点验证模块** (hardpoint_validation) - 武器挂点、设备安装点

## 快速开始

### 1. 安装依赖

```bash
pip install numpy scipy
```

### 2. 准备输入配置

创建JSON配置文件，包含 `geometry_integrated` 配置段：

```json
{
  "geometry_integrated": {
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
      }
    },
    "wingtip": {
      "type": "winglet",
      "height_m": 1.5,
      "cant_angle_deg": 45.0
    }
  },
  "geometry": {
    "fuselage": {
      "length_m": 10.0,
      "diameter_m": 1.5
    },
    "wing": {
      "span_m": 10.0,
      "root_chord_m": 2.0
    }
  }
}
```

### 3. 使用统一接口

```python
from aircraft_design.geometry_shape import (
    parse_geometry_integrated_config,
    validate_geometry_integrated,
    calculate_geometry_integrated_performance,
    generate_geometry_integrated_visualization,
    generate_geometry_integrated_mesh
)

# 解析配置
with open('config.json', 'r') as f:
    config = json.load(f)

integrated_config = parse_geometry_integrated_config(config['geometry_integrated'])

# 验证配置
validation_result = validate_geometry_integrated(
    integrated_config,
    config['geometry']
)

if not validation_result['is_valid']:
    print(f"发现 {validation_result['critical_violations']} 个严重违规")
    for violation in validation_result['violations']:
        print(f"  - {violation['message']}")
else:
    print("配置验证通过")

# 计算性能
performance = calculate_geometry_integrated_performance(
    integrated_config,
    config['geometry']
)

print(f"总重量: {performance['total_geometry_integrated_weight_kg']:.2f} kg")

# 生成可视化
html_path = generate_geometry_integrated_visualization(
    integrated_config,
    config['geometry'],
    'geometry_3d.html'
)

mesh_path = generate_geometry_integrated_mesh(
    integrated_config,
    config['geometry'],
    'geometry_mesh.json'
)

print(f"可视化文件: {html_path}")
print(f"网格文件: {mesh_path}")
```

## 详细配置说明

### 机翼控制面配置

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

**参数说明**:
- `enabled`: 是否启用该控制面
- `count`: 控制面数量
- `chord_fraction`: 弦长比例（相对于机翼根弦长）
- `span_fraction`: 展向位置比例（相对于半翼展）
- `max_deflection_deg`: 最大偏转角度（度）
- `type`: 襟翼类型（plain/split/fowler）

### 翼尖装置配置

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

**参数说明**:
- `type`: 翼尖类型（winglet/tip_tank/none）
- `height_m`: 翼尖高度（米）
- `cant_angle_deg`: 后掠角（度）
- `toe_angle_deg`: 前掠角（度）
- `chord_fraction`: 弦长比例
- `sweep_deg`: 后掠角（度）

### 起落架配置

```json
{
  "landing_gear": {
    "main": {
      "type": "tricycle",
      "count": 2,
      "wheel_diameter_m": 0.5,
      "track_m": 3.0,
      "position_x_m": 0.0,
      "position_y_m": 1.5,
      "position_z_m": -1.0
    },
    "nose": {
      "wheel_diameter_m": 0.3,
      "position_x_m": -2.0,
      "position_y_m": 0.0,
      "position_z_m": -0.5,
      "steering_angle_deg": 30.0
    }
  }
}
```

**参数说明**:
- `type`: 起落架类型（tricycle/taildragger）
- `count`: 起落架数量
- `wheel_diameter_m`: 轮子直径（米）
- `track_m`: 轮距（米）
- `position_x_m/y_m/z_m`: 位置坐标（米）
- `steering_angle_deg`: 转向角度（度）

### 发动机类型库配置

```json
{
  "engine_library": {
    "type": "turbofan",
    "selected_engine": "GE_F404",
    "custom_engine": {
      "sea_level_thrust_kn": 50.0,
      "bypass_ratio": 0.3,
      "turbine_inlet_temp_k": 1600.0,
      "dry_weight_kg": 1000.0,
      "diameter_m": 0.8
    }
  }
}
```

**参数说明**:
- `type`: 发动机类型（turbofan/turbopiston/piston）
- `selected_engine`: 选择的发动机型号
- `custom_engine`: 自定义发动机参数
- `sea_level_thrust_kn`: 海平面推力（千牛）
- `bypass_ratio`: 涵道比
- `turbine_inlet_temp_k`: 涡轮进口温度（开尔文）
- `dry_weight_kg`: 发动机干重（千克）
- `diameter_m`: 发动机直径（米）

### 发动机短舱配置

```json
{
  "nacelle": {
    "length_m": 3.5,
    "diameter_m": 1.2,
    "inlet_length_ratio": 0.2,
    "nozzle_length_ratio": 0.15,
    "position_x_m": 2.0,
    "position_y_m": 0.0,
    "position_z_m": -0.5
  }
}
```

**参数说明**:
- `length_m`: 短舱长度（米）
- `diameter_m`: 短舱直径（米）
- `inlet_length_ratio`: 进气道长度比例
- `nozzle_length_ratio`: 喷管长度比例
- `position_x_m/y_m/z_m`: 位置坐标（米）

### 驾驶舱盖配置

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

**参数说明**:
- `type`: 类型（flat/curved）
- `thickness_m`: 厚度（米）
- `forward_angle_deg`: 前向角度（度）
- `side_angle_deg`: 侧面角度（度）
- `curvature_radius_m`: 曲率半径（米）

### 舱门舷窗配置

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

**参数说明**:
- `enabled`: 是否启用
- `type`: 类型（ramp/hatch/door）
- `width_m`: 宽度（米）
- `height_m`: 高度（米）
- `position_x_m`: 位置坐标（米）
- `count`: 数量
- `pitch_m`: 间距（米）

### 硬点验证配置

```json
{
  "hardpoint_validation": {
    "wing_hardpoints": {
      "outer_stations": {
        "count": 4,
        "max_load_kg": 1000.0,
        "position_y_m": 4.0,
        "position_x_m": 0.5,
        "position_z_m": 0.0
      },
      "center_stations": {
        "count": 2,
        "max_load_kg": 2000.0,
        "position_y_m": 2.0,
        "position_x_m": 0.0,
        "position_z_m": 0.0
      }
    },
    "fuselage_hardpoints": {
      "centerline_station": {
        "max_load_kg": 3000.0,
        "position_x_m": 2.0,
        "position_y_m": 0.0,
        "position_z_m": 0.0
      }
    }
  }
}
```

**参数说明**:
- `count`: 硬点数量
- `max_load_kg`: 最大载荷（千克）
- `position_x_m/y_m/z_m`: 位置坐标（米）

## API参考

### parse_geometry_integrated_config

解析几何特征整合配置。

**参数**:
- `integrated_dict` (dict[str, Any]): 包含所有几何特征模块的配置字典
- `path` (str): 配置路径前缀，默认为 "geometry_integrated"

**返回值**:
- dict[str, Any]: 解析后的几何特征配置字典

### validate_geometry_integrated

验证几何特征整合配置。

**参数**:
- `integrated_config` (dict[str, Any]): 解析后的几何特征配置
- `geometry` (dict[str, Any]): 基础几何参数

**返回值**:
- dict[str, Any]: 验证结果字典，包含：
  - `violations` (list): 违规列表
  - `total_violations` (int): 总违规数
  - `critical_violations` (int): 严重违规数
  - `warning_violations` (int): 警告违规数
  - `is_valid` (bool): 是否有效（无严重违规）

### calculate_geometry_integrated_performance

计算几何特征综合性能。

**参数**:
- `integrated_config` (dict[str, Any]): 解析后的几何特征配置
- `geometry` (dict[str, Any]): 基础几何参数

**返回值**:
- dict[str, Any]: 性能计算结果字典，包含：
  - `weights` (dict): 重量分解
  - `total_geometry_integrated_weight_kg` (float): 总重量
  - `nacelle_drag_N` (float): 短舱阻力（牛）
  - `nacelle_cd0` (float): 短舱阻力系数
  - `induced_drag_reduction` (float): 诱导阻力减少系数

### generate_geometry_integrated_visualization

生成几何特征3D可视化HTML文件。

**参数**:
- `integrated_config` (dict[str, Any]): 解析后的几何特征配置
- `geometry` (dict[str, Any]): 基础几何参数
- `output_path` (str): 输出HTML文件路径，默认为 "geometry_integrated_3d.html"

**返回值**:
- str: 生成的HTML文件路径

### generate_geometry_integrated_mesh

生成几何特征网格数据JSON文件。

**参数**:
- `integrated_config` (dict[str, Any]): 解析后的几何特征配置
- `geometry` (dict[str, Any]): 基础几何参数
- `output_path` (str): 输出JSON文件路径，默认为 "geometry_integrated_mesh.json"

**返回值**:
- str: 生成的JSON文件路径

### generate_geometry_integrated_obj

生成几何特征OBJ模型文件。

**参数**:
- `integrated_config` (dict[str, Any]): 解析后的几何特征配置
- `geometry` (dict[str, Any]): 基础几何参数
- `output_path` (str): 输出OBJ文件路径，默认为 "geometry_integrated.obj"

**返回值**:
- str: 生成的OBJ文件路径

## 错误处理

### 配置错误

当配置参数不符合要求时，解析函数会抛出 `ValueError` 异常。

**常见错误**:
- 缺少必需参数
- 参数类型错误
- 参数超出有效范围

### 验证错误

验证函数会返回违规列表，每个违规包含：

```python
{
    "name": "违规名称",
    "message": "违规描述",
    "severity": "critical" | "warning",
    "suggestion": "修正建议"
}
```

## 与总体设计流程集成

本技能可以与 `fixed_wing_overall_sizing_runbook` 集成：

```python
# 在输入JSON中添加geometry_integrated配置
input_config = {
    "requirements": { /* ... */ },
    "initial_guess": { /* ... */ },
    "geometry_integrated": { /* ... */ }
}

# 运行总体设计流程
# Class I 收敛后会自动触发几何特征详细设计
```

## 输出文件说明

### geometry_integrated_3d.html

3D可视化HTML文件，包含：
- 交互式3D模型预览
- 显示控制面板
- 统计信息显示
- 支持鼠标旋转和缩放

### geometry_integrated_mesh.json

网格数据JSON文件，包含：
- 基础几何网格数据
- 各特征模块网格数据
- 元数据和版本信息

### geometry_integrated.obj

OBJ模型文件，可导入到：
- OpenVSP
- Blender
- 其他3D建模软件

## 常见问题

**Q: 如何添加新的几何特征模块？**

A: 按照以下步骤：
1. 在对应模块文件中实现解析、验证、计算函数
2. 在 `geometry_shape.py` 中添加导入语句
3. 在 `parse_geometry_integrated_config` 中添加解析逻辑
4. 在 `validate_geometry_integrated` 中添加验证逻辑
5. 在 `calculate_geometry_integrated_performance` 中添加计算逻辑

**Q: 如何调整验证规则的严格程度？**

A: 验证规则在各模块的验证函数中定义，可以通过修改这些函数来调整严格程度。

**Q: 可视化文件无法正常显示怎么办？**

A: 检查以下几点：
- 确保网络连接正常（需要加载Three.js库）
- 检查浏览器是否支持WebGL
- 查看浏览器控制台是否有错误信息

## 性能优化建议

1. **配置解析缓存**: 对于重复使用的配置，可以缓存解析结果
2. **增量验证**: 对于大型配置，可以分模块进行验证
3. **并行计算**: 性能计算可以并行执行
4. **网格简化**: 对于可视化，可以使用简化网格提高性能

## 扩展阅读

- [固定翼总体设计方案](fixed_wing_overall_sizing_spec)
- [固定翼外形详细设计](fixed_wing_shape_detail_spec)
- [固定翼阶段2-7规划](fixed_wing_stage2_7_plan)

## 版本历史

- **v1.0** (2026-02-12): 初始版本，整合8个几何特征模块
