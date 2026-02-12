# SKILL增强发展计划

本文档基于OpenVSP功能分析，制定了SKILL（固定翼飞机设计技能）的功能增强发展计划。

## 一、发展目标

### 1.1 总体目标
将SKILL从当前的固定翼飞机设计技能，扩展为支持更全面的飞机设计和分析能力，包括：

- 完整的几何建模能力
- 详细的气动分析能力
- 退化几何分析能力
- 载荷分析能力
- 旋翼机分析能力
- 与OpenVSP的集成能力

### 1.2 具体目标
- **几何建模**：实现参数化几何建模、翼型库、几何变换和组合
- **气动分析**：实现详细的阻力分解、表面分析、VSPAERO集成
- **退化几何**：实现升力面退化、机身退化、质量属性计算
- **载荷分析**：实现气动载荷、惯性载荷、结构载荷计算
- **旋翼分析**：实现旋翼气动力和性能分析
- **集成测试**：实现与OpenVSP的集成测试

## 二、发展路线图

### 阶段1：几何建模增强（P0 - 高优先级）

#### 2.1.1 翼型库模块
**模块名称**：`aircraft_design/airfoil_library.py`

**功能描述**：
- 实现NACA 4位数翼型生成
- 实现NACA 5位数翼型生成
- 实现NACA 6系列翼型生成
- 支持自定义翼型导入（SELIG、BEZIER格式）
- 实现翼型数据格式转换

**关键函数**：
```python
def generate_naca4_airfoil(
    max_camber: float,
    max_camber_location: float,
    max_thickness: float,
    num_points: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """生成NACA 4位数翼型"""

def generate_naca5_airfoil(
    design_lift_coeff: float,
    max_thickness: float,
    num_points: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """生成NACA 5位数翼型"""

def generate_naca6_airfoil(
    series_char: str,
    max_thickness: float,
    design_lift_coeff: float,
    num_points: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """生成NACA 6系列翼型"""

def load_airfoil_file(
    file_path: str,
) -> tuple[np.ndarray, np.ndarray]:
    """加载翼型文件（SELIG、BEZIER格式）"""

def convert_airfoil_format(
    x: np.ndarray,
    y: np.ndarray,
    from_format: str,
    to_format: str,
) -> tuple[np.ndarray, np.ndarray]:
    """转换翼型数据格式"""
```

**验收标准**：
- 能够生成标准的NACA 4位数、5位数、6系列翼型
- 能够加载和转换SELIG、BEZIER格式翼型文件
- 单元测试覆盖率 >= 80%

#### 2.1.2 几何建模模块
**模块名称**：`aircraft_design/geometry_modeling.py`

**功能描述**：
- 实现参数化几何建模函数
- 支持机翼、机身、尾翼、发动机、起落架等组件
- 实现几何变换（平移、旋转、缩放）
- 实现几何组合（组件组装、布尔运算）

**关键函数**：
```python
@dataclass(frozen=True)
class WingGeometry:
    """机翼几何参数"""
    area: float
    span: float
    chord_root: float
    chord_tip: float
    sweep_quarter_chord: float
    taper_ratio: float
    twist_root: float
    twist_tip: float
    dihedral: float
    incidence: float
    airfoil_root: str
    airfoil_tip: str

@dataclass(frozen=True)
class FuselageGeometry:
    """机身几何参数"""
    length: float
    diameter: float
    fineness_ratio: float
    nose_length: float
    tail_length: float

@dataclass(frozen=True)
class HorizontalTailGeometry:
    """平尾几何参数"""
    area: float
    span: float
    chord_root: float
    chord_tip: float
    sweep_quarter_chord: float
    taper_ratio: float
    incidence: float
    airfoil: str

@dataclass(frozen=True)
class VerticalTailGeometry:
    """垂尾几何参数"""
    area: float
    span: float
    chord_root: float
    chord_tip: float
    sweep_quarter_chord: float
    taper_ratio: float
    airfoil: str

def translate_geometry(
    geometry: Any,
    dx: float,
    dy: float,
    dz: float,
) -> Any:
    """平移几何"""

def rotate_geometry(
    geometry: Any,
    axis: str,
    angle_deg: float,
) -> Any:
    """旋转几何"""

def scale_geometry(
    geometry: Any,
    scale_factor: float,
) -> Any:
    """缩放几何"""

def mirror_geometry(
    geometry: Any,
    axis: str,
) -> Any:
    """镜像几何"""

def assemble_aircraft(
    wing: WingGeometry,
    fuselage: FuselageGeometry,
    h_tail: HorizontalTailGeometry,
    v_tail: VerticalTailGeometry,
) -> dict:
    """组装飞机几何"""
```

**验收标准**：
- 能够定义完整的机翼、机身、尾翼几何参数
- 能够进行几何变换（平移、旋转、缩放、镜像）
- 能够组装多个组件成完整飞机
- 单元测试覆盖率 >= 80%

#### 2.1.3 退化几何模块
**模块名称**：`aircraft_design/degenerate_geometry.py`

**功能描述**：
- 实现升力面退化算法（平板、梁）
- 实现机身退化算法（圆柱、圆锥）
- 实现圆盘退化算法（螺旋桨）
- 实现质量属性计算（面积、体积、惯性质、重心）

**关键函数**：
```python
@dataclass(frozen=True)
class DegenPlate:
    """退化平板"""
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    nx: np.ndarray
    ny: np.ndarray
    nz: np.ndarray
    area: float
    centroid: np.ndarray

@dataclass(frozen=True)
class DegenStick:
    """退化梁"""
    le: np.ndarray
    te: np.ndarray
    cg_shell: np.ndarray
    cg_solid: np.ndarray
    toc: float
    chord: np.ndarray
    i_shell: np.ndarray
    i_solid: np.ndarray

@dataclass(frozen=True)
class DegenDisk:
    """退化圆盘"""
    diameter: float
    position: np.ndarray
    normal: np.ndarray

def degenerate_wing_to_plate(
    wing: WingGeometry,
    num_chordwise: int = 20,
    num_spanwise: int = 10,
) -> DegenPlate:
    """将机翼退化为平板"""

def degenerate_wing_to_stick(
    wing: WingGeometry,
    num_sections: int = 10,
) -> DegenStick:
    """将机翼退化为梁"""

def degenerate_fuselage_to_cylinder(
    fuselage: FuselageGeometry,
    num_sections: int = 20,
) -> DegenPlate:
    """将机身退化为圆柱"""

def degenerate_propeller_to_disk(
    diameter: float,
    position: np.ndarray,
    normal: np.ndarray,
) -> DegenDisk:
    """将螺旋桨退化为圆盘"""

def calculate_mass_properties(
    geometry: Any,
    density: float = 2700.0,
) -> dict:
    """计算质量属性（面积、体积、惯性质、重心）"""
```

**验收标准**：
- 能够将机翼退化为平板和梁
- 能够将机身退化为圆柱
- 能够将螺旋桨退化为圆盘
- 能够计算质量属性（面积、体积、惯性质、重心）
- 单元测试覆盖率 >= 80%

### 阶段2：气动分析增强（P1 - 中优先级）

#### 2.2.1 增强寄生阻力模块
**模块名称**：`aircraft_design/parasite_drag_enhanced.py`

**功能描述**：
- 实现详细的阻力分解（摩擦、形状、干扰）
- 实现雷诺数计算
- 实现层流/湍流摩擦系数
- 实现表面粗糙度修正

**关键函数**：
```python
@dataclass(frozen=True)
class ParasiteDragResult:
    """寄生阻力结果"""
    cd0_total: float
    cd0_fric: float
    cd0_form: float
    cd0_interf: float
    reynolds_number: float
    cf_laminar: float
    cf_turbulent: float
    component_breakdown: dict

def calculate_reynolds_number(
    velocity: float,
    length: float,
    kinematic_viscosity: float,
) -> float:
    """计算雷诺数"""

def calculate_friction_coefficient_laminar(
    reynolds_number: float,
) -> float:
    """计算层流摩擦系数（Blasius公式）"""

def calculate_friction_coefficient_turbulent(
    reynolds_number: float,
    roughness_ratio: float = 0.0,
) -> float:
    """计算湍流摩擦系数（Schlichting公式）"""

def calculate_form_factor(
    thickness_ratio: float,
    sweep_angle_deg: float,
    mach: float,
) -> float:
    """计算形状因子"""

def calculate_interference_factor(
    component_type: str,
    geometry: Any,
) -> float:
    """计算干扰因子"""

def calculate_parasite_drag_enhanced(
    geometry: Any,
    velocity: float,
    altitude: float,
    surface_roughness: float = 0.0,
    isa_delta_c: float = 0.0,
) -> ParasiteDragResult:
    """计算增强的寄生阻力"""
```

**验收标准**：
- 能够计算详细的阻力分解（摩擦、形状、干扰）
- 能够计算雷诺数
- 能够计算层流和湍流摩擦系数
- 能够应用表面粗糙度修正
- 单元测试覆盖率 >= 80%

#### 2.2.2 表面分析模块
**模块名称**：`aircraft_design/surface_analysis.py`

**功能描述**：
- 实现表面网格生成
- 实现法向量计算
- 实现曲率分析（主曲率、高斯曲率）

**关键函数**：
```python
@dataclass(frozen=True)
class SurfaceMesh:
    """表面网格"""
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    nx: np.ndarray
    ny: np.ndarray
    nz: np.ndarray
    area: np.ndarray
    centroid: np.ndarray

@dataclass(frozen=True)
class CurvatureResult:
    """曲率结果"""
    principal_curvature_1: np.ndarray
    principal_curvature_2: np.ndarray
    gaussian_curvature: np.ndarray
    mean_curvature: np.ndarray

def generate_surface_mesh(
    geometry: Any,
    num_u: int = 20,
    num_v: int = 10,
) -> SurfaceMesh:
    """生成表面网格"""

def calculate_normals(
    mesh: SurfaceMesh,
) -> SurfaceMesh:
    """计算法向量"""

def calculate_curvature(
    mesh: SurfaceMesh,
) -> CurvatureResult:
    """计算曲率（主曲率、高斯曲率）"""
```

**验收标准**：
- 能够生成参数化表面网格
- 能够计算表面法向量
- 能够计算主曲率和高斯曲率
- 单元测试覆盖率 >= 80%

#### 2.2.3 VSPAERO接口模块
**模块名称**：`aircraft_design/vspaero_interface.py`

**功能描述**：
- 实现VSPAERO输入文件生成
- 实现VSPAERO输出解析
- 实现升力分布计算

**关键函数**：
```python
def generate_vspaero_input(
    geometry: Any,
    output_file: str,
    mach: float = 0.7,
    alpha_deg: float = 0.0,
) -> None:
    """生成VSPAERO输入文件"""

def parse_vspaero_output(
    output_file: str,
) -> dict:
    """解析VSPAERO输出文件"""

def calculate_lift_distribution(
    vspaero_results: dict,
) -> dict:
    """计算升力分布"""
```

**验收标准**：
- 能够生成VSPAERO输入文件
- 能够解析VSPAERO输出文件
- 能够计算升力分布
- 单元测试覆盖率 >= 80%

### 阶段3：载荷分析增强（P2 - 低优先级）

#### 2.3.1 载荷分析模块
**模块名称**：`aircraft_design/loads_analysis.py`

**功能描述**：
- 实现气动载荷计算
- 实现惯性载荷计算
- 实现结构载荷计算（弯矩、剪力、扭矩）

**关键函数**：
```python
@dataclass(frozen=True)
class AerodynamicLoad:
    """气动载荷"""
    lift: float
    drag: float
    moment_pitch: float
    moment_roll: float
    moment_yaw: float

@dataclass(frozen=True)
class InertialLoad:
    """惯性载荷"""
    mass: float
    inertia: np.ndarray
    cg: np.ndarray

@dataclass(frozen=True)
class StructuralLoad:
    """结构载荷"""
    bending_moment: np.ndarray
    shear_force: np.ndarray
    torque: float

def calculate_aerodynamic_loads(
    geometry: Any,
    velocity: float,
    altitude: float,
    alpha_deg: float = 0.0,
) -> AerodynamicLoad:
    """计算气动载荷"""

def calculate_inertial_loads(
    mass: float,
    cg: np.ndarray,
    acceleration: np.ndarray,
) -> InertialLoad:
    """计算惯性载荷"""

def calculate_structural_loads(
    geometry: Any,
    aerodynamic_loads: AerodynamicLoad,
    inertial_loads: InertialLoad,
) -> StructuralLoad:
    """计算结构载荷（弯矩、剪力、扭矩）"""
```

**验收标准**：
- 能够计算气动载荷（升力、阻力、力矩）
- 能够计算惯性载荷（质量、惯性质、重心）
- 能够计算结构载荷（弯矩、剪力、扭矩）
- 单元测试覆盖率 >= 80%

#### 2.3.2 旋翼机分析模块
**模块名称**：`aircraft_design/rotorcraft_analysis.py`

**功能描述**：
- 实现旋翼气动力计算
- 实现旋翼性能分析（悬停、前飞、爬升）

**关键函数**：
```python
@dataclass(frozen=True)
class RotorAerodynamics:
    """旋翼气动力"""
    thrust: float
    torque: float
    power: float
    induced_velocity: float

@dataclass(frozen=True)
class RotorPerformance:
    """旋翼性能"""
    hover_ceiling: float
    max_forward_speed: float
    climb_rate: float
    endurance: float
    range: float

def calculate_rotor_aerodynamics(
    rotor_diameter: float,
    rotor_speed: float,
    blade_pitch: float,
    air_density: float = 1.225,
) -> RotorAerodynamics:
    """计算旋翼气动力"""

def calculate_rotor_performance(
    rotor_aero: RotorAerodynamics,
    gross_weight: float,
    engine_power: float,
) -> RotorPerformance:
    """计算旋翼性能（悬停、前飞、爬升）"""
```

**验收标准**：
- 能够计算旋翼气动力（推力、扭矩、功率）
- 能够计算旋翼性能（悬停升限、最大前飞速度、爬升率、续航、航程）
- 单元测试覆盖率 >= 80%

### 阶段4：集成与测试（P3 - 低优先级）

#### 2.4.1 集成测试模块
**模块名称**：`tests/integration_tests.py`

**功能描述**：
- 实现OpenVSP与SKILL的集成测试
- 实现端到端测试

**关键测试**：
```python
def test_airfoil_library():
    """测试翼型库模块"""

def test_geometry_modeling():
    """测试几何建模模块"""

def test_degenerate_geometry():
    """测试退化几何模块"""

def test_parasite_drag_enhanced():
    """测试增强寄生阻力模块"""

def test_surface_analysis():
    """测试表面分析模块"""

def test_vspaero_interface():
    """测试VSPAERO接口模块"""

def test_loads_analysis():
    """测试载荷分析模块"""

def test_rotorcraft_analysis():
    """测试旋翼机分析模块"""

def test_openvsp_integration():
    """测试OpenVSP集成"""

def test_end_to_end():
    """测试端到端流程"""
```

**验收标准**：
- 所有模块单元测试覆盖率 >= 80%
- 集成测试通过率 >= 90%
- 端到端测试通过率 >= 90%

#### 2.4.2 文档更新
**更新内容**：
- 更新SKILL开发指导文档
- 创建使用示例
- 创建教程

## 三、优先级排序

### 3.1 优先级P0（高优先级）
- 翼型库模块
- 几何建模模块
- 退化几何模块

**预计时间**：2-3周

### 3.2 优先级P1（中优先级）
- 增强寄生阻力模块
- 表面分析模块
- VSPAERO接口模块

**预计时间**：3-4周

### 3.3 优先级P2（低优先级）
- 载荷分析模块
- 旋翼机分析模块
- 集成测试模块
- 文档更新

**预计时间**：4-5周

## 四、风险评估

### 4.1 技术风险
- **OpenVSP API复杂性**：OpenVSP的Python API可能存在兼容性问题
- **性能风险**：复杂的几何计算可能影响性能
- **精度风险**：数值计算可能存在精度问题

### 4.2 缓解措施
- **API兼容性**：充分测试OpenVSP API，确保兼容性
- **性能优化**：使用NumPy向量化计算，提高性能
- **精度控制**：使用双精度浮点数，控制计算精度

## 五、成功标准

### 5.1 功能标准
- 所有计划模块实现完成
- 所有模块单元测试覆盖率 >= 80%
- 集成测试通过率 >= 90%
- 端到端测试通过率 >= 90%

### 5.2 文档标准
- 所有模块有完整的API文档
- 所有模块有使用示例
- 有完整的教程文档

### 5.3 质量标准
- 代码符合PEP 8规范
- 代码通过类型检查（mypy）
- 代码通过代码质量检查（ruff）

## 六、参考资料

- OpenVSP官方文档：https://openvsp.org/
- OpenVSP Python API文档：/OpenVSP-3.47.0-MacOS/python/openvsp/doc/
- OpenVSP示例脚本：/OpenVSP-3.47.0-MacOS/scripts/
- CHARM文档：/OpenVSP-3.47.0-MacOS/python/CHARM/charm/
- VSPAERO文档：/OpenVSP-3.47.0-MacOS/vspaero_ex/
- 现有SKILL文档：/docs/theory/
