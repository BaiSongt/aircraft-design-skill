# SKILL使用教程

本教程介绍如何使用SKILL（固定翼飞机设计技能）进行飞机设计和分析。

## 目录

1. [翼型库教程](#1-翼型库教程)
2. [几何建模教程](#2-几何建模教程)
3. [退化几何教程](#3-退化几何教程)
4. [寄生阻力教程](#4-寄生阻力教程)
5. [表面分析教程](#5-表面分析教程)
6. [载荷分析教程](#6-载荷分析教程)
7. [旋翼机分析教程](#7-旋翼机分析教程)
8. [VSPAERO接口教程](#8-vspaero接口教程)

---

## 1. 翼型库教程

### 1.1 概述

翼型库模块提供了生成和操作翼型的功能，包括NACA系列翼型生成、自定义翼型加载、翼型格式转换等。

### 1.2 主要功能

- 生成NACA 4位数翼型
- 生成NACA 5位数翼型
- 生成NACA 6系列翼型
- 加载自定义翼型文件
- 翼型格式转换
- 翼型缩放
- 生成翼型库

### 1.3 使用示例

```python
from aircraft_design.airfoil_library import (
    generate_naca4_airfoil,
    generate_naca5_airfoil,
    generate_naca6_airfoil,
    scale_airfoil,
    generate_airfoil_library,
)

# 生成NACA 4位数翼型
naca4 = generate_naca4_airfoil(
    max_camber=0.02,
    max_camber_location=0.4,
    max_thickness=0.12,
    num_points=100,
)

# 生成NACA 5位数翼型
naca5 = generate_naca5_airfoil(
    design_lift_coeff=0.3,
    max_thickness=0.12,
    num_points=100,
)

# 生成NACA 6系列翼型
naca6 = generate_naca6_airfoil(
    series_char="63",
    max_thickness=0.12,
    design_lift_coeff=0.3,
    num_points=100,
)

# 翼型缩放
scaled_naca4 = scale_airfoil(
    airfoil=naca4,
    chord=1.5,
)

# 生成翼型库
library = generate_airfoil_library(
    naca4_params=[
        {"max_camber": 0.02, "max_camber_location": 0.4, "max_thickness": 0.12},
    ],
    naca5_params=[
        {"design_lift_coeff": 0.3, "max_thickness": 0.12},
    ],
    naca6_params=[
        {"series_char": "63", "max_thickness": 0.12, "design_lift_coeff": 0.3},
    ],
)
```

### 1.4 输出说明

- `AirfoilGeometry`：翼型几何参数对象
  - `coordinates`：翼型坐标（x, y）
  - `chord`：弦长
  - `max_thickness`：最大厚度
  - `max_thickness_location`：最大厚度位置
  - `max_camber`：最大弯度
  - `max_camber_location`：最大弯度位置
  - `leading_edge_radius`：前缘半径
  - `trailing_edge_angle`：后缘角

### 1.5 注意事项

- NACA 4位数翼型的弯度参数范围：0.0-0.1
- NACA 5位数翼型的设计升力系数范围：0.0-0.5
- NACA 6系列翼型的系列字符：63、64、65、66、67
- 翼型文件支持SELIG和DAT格式

---

## 2. 几何建模教程

### 2.1 概述

几何建模模块提供了创建和操作飞机几何的功能，包括机翼、机身、尾翼、发动机、起落架等组件。

### 2.2 主要功能

- 创建机翼
- 创建机身
- 创建平尾
- 创建垂尾
- 创建发动机
- 创建起落架
- 组装飞机
- 几何变换（平移、旋转、缩放、镜像）

### 2.3 使用示例

```python
from aircraft_design.geometry_modeling import (
    create_wing,
    create_fuselage,
    create_horizontal_tail,
    create_vertical_tail,
    create_engine,
    create_landing_gear,
    assemble_aircraft,
    translate_geometry,
    rotate_geometry,
    scale_geometry,
    mirror_geometry,
)
import numpy as np

# 创建机翼
wing = create_wing(
    area=30.0,
    aspect_ratio=8.0,
    taper_ratio=0.6,
    sweep_quarter_chord=25.0,
    twist_root=0.0,
    twist_tip=-2.0,
    dihedral=5.0,
    incidence=2.0,
    airfoil_root="NACA0012",
    airfoil_tip="NACA0012",
    position=np.array([0.0, 0.0, 0.0]),
)

# 创建机身
fuselage = create_fuselage(
    length=15.0,
    diameter=2.0,
    fineness_ratio=7.5,
    nose_length=4.5,
    tail_length=4.5,
    position=np.array([0.0, 0.0, 0.0]),
)

# 创建平尾
h_tail = create_horizontal_tail(
    area=8.0,
    aspect_ratio=5.0,
    taper_ratio=0.5,
    sweep_quarter_chord=30.0,
    incidence=0.0,
    airfoil="NACA0012",
    position=np.array([-5.0, 0.0, 0.0]),
)

# 创建垂尾
v_tail = create_vertical_tail(
    area=5.0,
    aspect_ratio=2.0,
    taper_ratio=0.6,
    sweep_quarter_chord=35.0,
    airfoil="NACA0012",
    position=np.array([-5.0, 0.0, 0.0]),
)

# 组装飞机
aircraft = assemble_aircraft(
    wing=wing,
    fuselage=fuselage,
    h_tail=h_tail,
    v_tail=v_tail,
)

# 几何变换
translated_wing = translate_geometry(
    geometry=wing,
    dx=1.0,
    dy=0.0,
    dz=0.0,
)

rotated_wing = rotate_geometry(
    geometry=wing,
    axis="z",
    angle_deg=10.0,
)

scaled_wing = scale_geometry(
    geometry=wing,
    scale_factor=1.1,
)

mirrored_wing = mirror_geometry(
    geometry=wing,
    axis="y",
)
```

### 2.4 输出说明

- `WingGeometry`：机翼几何参数
  - `area`：参考面积（m²）
  - `span`：翼展（m）
  - `chord_root`：根弦长（m）
  - `chord_tip`：梢弦长（m）
  - `sweep_quarter_chord`：1/4弦线后掠角（deg）
  - `taper_ratio`：梯形比
  - `twist_root`：根部扭转角（deg）
  - `twist_tip`：梢部扭转角（deg）
  - `dihedral`：上反角（deg）
  - `incidence`：安装角（deg）
  - `airfoil_root`：根部翼型
  - `airfoil_tip`：梢部翼型
  - `position`：位置（x, y, z）

- `FuselageGeometry`：机身几何参数
  - `length`：长度（m）
  - `diameter`：直径（m）
  - `fineness_ratio`：长径比
  - `nose_length`：机头长度（m）
  - `tail_length`：机尾长度（m）
  - `position`：位置（x, y, z）

### 2.5 注意事项

- 所有长度单位为米（m）
- 所有角度单位为度（deg）
- 所有面积单位为平方米（m²）
- 位置坐标为（x, y, z）

---

## 3. 退化几何教程

### 3.1 概述

退化几何模块提供了将复杂几何简化为简单几何的功能，包括升力面退化、机身退化、螺旋桨退化等。

### 3.2 主要功能

- 将机翼退化为平板
- 将机翼退化为梁
- 将机身退化为圆柱
- 将螺旋桨退化为圆盘
- 计算质量属性

### 3.3 使用示例

```python
from aircraft_design.degenerate_geometry import (
    degenerate_wing_to_plate,
    degenerate_wing_to_stick,
    degenerate_fuselage_to_cylinder,
    degenerate_propeller_to_disk,
    calculate_mass_properties,
)

# 将机翼退化为平板
plate = degenerate_wing_to_plate(
    wing=wing,
    num_chordwise=10,
    num_spanwise=5,
)

# 将机翼退化为梁
stick = degenerate_wing_to_stick(
    wing=wing,
    num_sections=10,
)

# 将机身退化为圆柱
cylinder = degenerate_fuselage_to_cylinder(
    fuselage=fuselage,
    num_sections=20,
)

# 将螺旋桨退化为圆盘
disk = degenerate_propeller_to_disk(
    diameter=2.0,
    position=np.array([5.0, 0.0, 0.0]),
    normal=np.array([0.0, 0.0, 1.0]),
)

# 计算质量属性
mass_props = calculate_mass_properties(
    geometry=plate,
    density=2700.0,
)
```

### 3.4 输出说明

- `DegenPlate`：退化平板
  - `x`, `y`, `z`：网格坐标
  - `nx`, `ny`, `nz`：法向量
  - `area`：面积网格
  - `centroid`：重心

- `DegenStick`：退化梁
  - `le`：前缘点
  - `te`：后缘点
  - `cg_shell`：壳重心
  - `cg_solid`：实体重心
  - `toc`：厚度
  - `chord`：弦长数组
  - `i_shell`：壳惯性矩
  - `i_solid`：实体惯性矩

- `MassProperties`：质量属性
  - `area`：面积（m²）
  - `volume`：体积（m³）
  - `centroid`：重心（x, y, z）
  - `ixx`, `iyy`, `izz`：惯性矩（kg·m²）
  - `ixy`, `ixz`, `iyz`：惯性积（kg·m²）
  - `mass`：质量（kg）

### 3.5 注意事项

- 退化几何用于简化计算，不是精确建模
- 质量属性计算假设均匀密度
- 网格密度影响计算精度

---

## 4. 寄生阻力教程

### 4.1 概述

寄生阻力模块提供了详细的阻力分解和计算功能，包括摩擦阻力、形状阻力、干扰阻力等。

### 4.2 主要功能

- 计算雷诺数
- 计算层流摩擦系数
- 计算湍流摩擦系数
- 计算形状因子
- 计算干扰因子
- 计算浸润面积
- 计算寄生阻力
- 寄生阻力扫描
- 寄生阻力包络

### 4.3 使用示例

```python
from aircraft_design.parasite_drag_enhanced import (
    calculate_parasite_drag_enhanced,
    calculate_parasite_drag_sweep,
    generate_parasite_drag_envelope,
)

# 计算寄生阻力
result = calculate_parasite_drag_enhanced(
    geometry=wing,
    velocity=200.0,
    altitude_m=10000.0,
    sref=30.0,
    surface_roughness=0.0,
    isa_delta_c=0.0,
)

# 寄生阻力扫描
sweep_result = calculate_parasite_drag_sweep(
    geometry=wing,
    velocity_range=[100.0, 150.0, 200.0],
    altitude_range=[0.0, 5000.0, 10000.0],
    sref=30.0,
    surface_roughness=0.0,
    isa_delta_c=0.0,
)

# 寄生阻力包络
envelope = generate_parasite_drag_envelope(
    geometry=wing,
    sref=30.0,
    mach_range=[0.3, 0.5, 0.7],
    altitude_range=[0.0, 5000.0, 10000.0],
    surface_roughness=0.0,
    isa_delta_c=0.0,
)
```

### 4.4 输出说明

- `ParasiteDragResult`：寄生阻力结果
  - `cd0_total`：总阻力系数
  - `cd0_fric`：摩擦阻力系数
  - `cd0_form`：形状阻力系数
  - `cd0_interf`：干扰阻力系数
  - `reynolds_number`：雷诺数
  - `cf_laminar`：层流摩擦系数
  - `cf_turbulent`：湍流摩擦系数
  - `component_breakdown`：组件分解

### 4.5 注意事项

- 阻力系数基于参考面积
- 雷诺数基于特征长度
- 表面粗糙度影响摩擦系数
- ISA偏差影响大气参数

---

## 5. 表面分析教程

### 5.1 概述

表面分析模块提供了表面网格生成、法向量计算、曲率分析等功能。

### 5.2 主要功能

- 生成表面网格
- 计算法向量
- 计算曲率（主曲率、高斯曲率）
- 计算表面积
- 计算表面重心
- 计算表面体积

### 5.3 使用示例

```python
from aircraft_design.surface_analysis import (
    generate_surface_mesh,
    calculate_normals,
    calculate_curvature,
    calculate_surface_area,
    calculate_surface_centroid,
    calculate_surface_volume,
)

# 生成表面网格
mesh = generate_surface_mesh(
    geometry=plate,
    num_u=10,
    num_v=5,
)

# 计算法向量
normals = calculate_normals(mesh=mesh)

# 计算曲率
curvature = calculate_curvature(mesh=mesh)

# 计算表面积
area = calculate_surface_area(mesh=mesh)

# 计算表面重心
centroid = calculate_surface_centroid(mesh=mesh)

# 计算表面体积
volume = calculate_surface_volume(mesh=mesh)
```

### 5.4 输出说明

- `SurfaceMesh`：表面网格
  - `x`, `y`, `z`：网格坐标
  - `nx`, `ny`, `nz`：法向量
  - `area`：面积网格
  - `centroid`：重心

- `CurvatureResult`：曲率结果
  - `principal_curvature_1`：主曲率1
  - `principal_curvature_2`：主曲率2
  - `gaussian_curvature`：高斯曲率
  - `mean_curvature`：平均曲率
  - `principal_direction_1`：主方向1
  - `principal_direction_2`：主方向2

### 5.5 注意事项

- 网格密度影响计算精度
- 曲率计算需要足够的网格密度
- 法向量归一化

---

## 6. 载荷分析教程

### 6.1 概述

载荷分析模块提供了气动载荷、惯性载荷、结构载荷的计算功能。

### 6.2 主要功能

- 计算气动载荷
- 计算惯性载荷
- 计算结构载荷（弯矩、剪力、扭矩）
- 载荷包络
- 颤振分析

### 6.3 使用示例

```python
from aircraft_design.loads_analysis import (
    calculate_aerodynamic_loads,
    calculate_inertial_loads,
    calculate_structural_loads,
    calculate_load_envelope,
    calculate_flutter_analysis,
)

# 计算气动载荷
aero_loads = calculate_aerodynamic_loads(
    geometry=aircraft,
    velocity=200.0,
    altitude_m=10000.0,
    alpha_deg=0.0,
    beta_deg=0.0,
    sref=30.0,
)

# 计算惯性载荷
inertial_loads = calculate_inertial_loads(
    mass=10000.0,
    cg=np.array([0.0, 0.0, 0.0]),
    acceleration=np.array([0.0, 0.0, 9.81]),
)

# 计算结构载荷
struct_loads = calculate_structural_loads(
    geometry=aircraft,
    aerodynamic_loads=aero_loads,
    inertial_loads=inertial_loads,
    material_yield_strength=270.0e6,
    safety_factor=1.5,
)

# 载荷包络
envelope = calculate_load_envelope(
    geometry=aircraft,
    velocity_range=[100.0, 150.0, 200.0],
    altitude_range=[0.0, 5000.0, 10000.0],
    alpha_range=[0.0, 5.0],
    material_yield_strength=270.0e6,
    safety_factor=1.5,
)

# 颤振分析
flutter = calculate_flutter_analysis(
    geometry=aircraft,
    velocity=200.0,
    altitude_m=10000.0,
)
```

### 6.4 输出说明

- `AerodynamicLoad`：气动载荷
  - `lift`：升力（N）
  - `drag`：阻力（N）
  - `moment_pitch`：俯仰力矩（N·m）
  - `moment_roll`：滚转力矩（N·m）
  - `moment_yaw`：偏航力矩（N·m）
  - `cl`：升力系数
  - `cd`：阻力系数
  - `cm`：俯仰力矩系数
  - `cn`：法向力系数
  - `cy`：侧向力系数

- `InertialLoad`：惯性载荷
  - `mass`：质量（kg）
  - `inertia`：惯性矩（kg·m²）
  - `cg`：重心（x, y, z）
  - `acceleration`：加速度（x, y, z）
  - `force`：惯性力（N）
  - `moment`：惯性力矩（N·m）

- `StructuralLoad`：结构载荷
  - `bending_moment`：弯矩数组（N·m）
  - `shear_force`：剪力数组（N）
  - `torque`：扭矩（N·m）
  - `von_mises_stress`：冯·米塞斯应力（Pa）
  - `safety_factor`：安全系数

### 6.5 注意事项

- 结构载荷计算假设均匀分布
- 安全系数应大于1.0
- 颤振分析需要准确的惯性矩

---

## 7. 旋翼机分析教程

### 7.1 概述

旋翼机分析模块提供了旋翼气动力和性能计算的功能。

### 7.2 主要功能

- 计算旋翼气动力
- 计算旋翼性能
- 旋翼性能包络
- 计算旋翼所需功率
- 计算旋翼盘载荷
- 计算旋翼功率载荷

### 7.3 使用示例

```python
from aircraft_design.rotorcraft_analysis import (
    calculate_rotor_aerodynamics,
    calculate_rotor_performance,
    calculate_rotor_performance_envelope,
    calculate_rotor_power_required,
    calculate_rotor_disk_loading,
    calculate_rotor_power_loading,
)

# 计算旋翼气动力
rotor_aero = calculate_rotor_aerodynamics(
    rotor_diameter=10.0,
    rotor_speed_rpm=300.0,
    blade_pitch_deg=10.0,
    num_blades=4,
    air_density=1.225,
    altitude_m=0.0,
    isa_delta_c=0.0,
)

# 计算旋翼性能
performance = calculate_rotor_performance(
    rotor_aero=rotor_aero,
    gross_weight=5000.0,
    engine_power=1000.0,
    drag_coefficient=0.02,
    parasite_area=10.0,
    fuel_capacity=500.0,
    sfc=0.5,
    altitude_m=0.0,
    isa_delta_c=0.0,
)

# 旋翼性能包络
envelope = calculate_rotor_performance_envelope(
    rotor_diameter=10.0,
    rotor_speed_rpm=300.0,
    blade_pitch_deg=10.0,
    num_blades=4,
    gross_weight_range=[4000.0, 5000.0, 6000.0],
    engine_power_range=[800.0, 1000.0, 1200.0],
    altitude_range=[0.0, 3000.0, 6000.0],
    drag_coefficient=0.02,
    parasite_area=10.0,
    fuel_capacity=500.0,
    sfc=0.5,
    isa_delta_c=0.0,
)

# 计算旋翼所需功率
power_required = calculate_rotor_power_required(
    gross_weight=5000.0,
    climb_rate=5.0,
    drag_coefficient=0.02,
    parasite_area=10.0,
    altitude_m=0.0,
    isa_delta_c=0.0,
)

# 计算旋翼盘载荷
disk_loading = calculate_rotor_disk_loading(
    thrust=rotor_aero.thrust,
    rotor_diameter=10.0,
)

# 计算旋翼功率载荷
power_loading = calculate_rotor_power_loading(
    power=rotor_aero.power,
    rotor_diameter=10.0,
)
```

### 7.4 输出说明

- `RotorAerodynamics`：旋翼气动力
  - `thrust`：推力（N）
  - `torque`：扭矩（N·m）
  - `power`：功率（W）
  - `induced_velocity`：诱导速度（m/s）
  - `figure_of_merit`：功重比（N/W）
  - `power_loading`：功率载荷（W/m²）
  - `disk_loading`：盘载荷（N/m²）

- `RotorPerformance`：旋翼性能
  - `hover_ceiling`：悬停升限（m）
  - `max_forward_speed`：最大前飞速度（m/s）
  - `climb_rate`：爬升率（m/min）
  - `endurance`：续航（s）
  - `range`：航程（km）
  - `service_ceiling`：实用升限（m）
  - `max_continuous_power`：最大连续功率（W）

### 7.5 注意事项

- 旋翼性能计算假设理想条件
- 功重比越高，效率越高
- 盘载荷影响悬停性能

---

## 8. VSPAERO接口教程

### 8.1 概述

VSPAERO接口模块提供了与OpenVSP的VSPAERO分析工具的集成功能。

### 8.2 主要功能

- 生成VSPAERO输入文件
- 解析VSPAERO输出文件
- 计算升力分布
- 计算阻力分布
- 计算力矩系数
- VSPAERO扫描

### 8.3 使用示例

```python
from aircraft_design.vspaero_interface import (
    generate_vspaero_input,
    parse_vspaero_output,
    calculate_lift_distribution,
    calculate_drag_distribution,
    calculate_moment_coefficients,
    generate_vspaero_sweep,
)

# 生成VSPAERO输入文件
generate_vspaero_input(
    geometry=aircraft,
    output_file="vspaero_input.txt",
    mach=0.7,
    alpha_deg=0.0,
    beta_deg=0.0,
    num_spanwise=20,
    num_chordwise=10,
)

# 解析VSPAERO输出文件
result = parse_vspaero_output(output_file="vspaero_output.txt")

# 计算升力分布
lift_dist = calculate_lift_distribution(
    vspaero_results=result,
    geometry=aircraft,
)

# 计算阻力分布
drag_dist = calculate_drag_distribution(
    vspaero_results=result,
    geometry=aircraft,
)

# 计算力矩系数
moments = calculate_moment_coefficients(vspaero_results=result)

# VSPAERO扫描
sweep = generate_vspaero_sweep(
    geometry=aircraft,
    mach_range=[0.5, 0.7],
    alpha_range=[0.0, 5.0],
    output_prefix="vspaero_sweep",
)
```

### 8.4 输出说明

- `VSPAEROResult`：VSPAERO结果
  - `cl`：升力系数
  - `cd`：阻力系数
  - `cm`：俯仰力矩系数
  - `cn`：法向力系数
  - `cy`：侧向力系数
  - `cl_alpha`：升力线斜率
  - `cd_alpha`：阻力线斜率
  - `lift_distribution`：升力分布
  - `drag_distribution`：阻力分布
  - `moment_coefficients`：力矩系数

### 8.5 注意事项

- VSPAERO需要安装OpenVSP
- 输入文件格式必须符合VSPAERO要求
- 输出文件格式可能因版本而异

---

## 总结

本教程介绍了SKILL的主要功能模块和使用方法。通过这些模块，您可以：

1. 生成和操作翼型
2. 创建和操作飞机几何
3. 简化复杂几何为简单几何
4. 计算详细的阻力分解
5. 分析表面几何特性
6. 计算气动、惯性、结构载荷
7. 分析旋翼机性能
8. 与VSPAERO集成进行气动分析

更多信息和示例，请参考：
- [examples/](../examples/)：使用示例
- [tests/integration_tests.py](../tests/integration_tests.py)：集成测试
- [docs/openvsp_analysis.md](openvsp_analysis.md)：OpenVSP功能分析
- [docs/openvsp_skill_enhancement_plan.md](openvsp_skill_enhancement_plan.md)：SKILL增强发展计划
