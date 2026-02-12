# 自动化CFD工作流的核心逻辑

自动化工作流是Agent的骨架，它将手动操作的步骤代码化、流程化。核心是编写一个Python类或模块来管理整个流程。

## 1. 基础模板案例 (Template Case)

在项目中创建一个`template_case`目录。这个目录是一个基础的、可运行的OpenFOAM案例，但其关键参数将被作为占位符。

例如，`template_case/system/controlDict` 文件可以包含：

```text
...
endTime         {{endTime}};
deltaT          {{deltaT}};
...
```

`template_case/0/U` (速度边界条件) 文件可以包含：

```text
...
inlet
{
    type            fixedValue;
    value           uniform ({{Ux}} 0 0);
}
...
```

我们使用`{{placeholder}}`作为占位符格式，方便后续用Python进行替换。

## 2. 工作流管理器 (WorkflowManager Class)

创建一个`WorkflowManager` Python类，负责处理单个计算任务。

```python
import os
import shutil
import subprocess
from jinja2 import Environment, FileSystemLoader # 使用Jinja2模板引擎

class WorkflowManager:
    def __init__(self, case_params, base_template_dir="template_case"):
        self.params = case_params
        self.case_name = self.params.get("case_name", "default_case")
        self.case_path = os.path.join("cases", self.case_name)
        self.base_template_dir = base_template_dir

    def run_workflow(self):
        """主执行流程"""
        self.setup_case_directory()
        self.generate_mesh()
        self.configure_case_files()
        self.execute_solver()
        # ... 后续调用分析和报告模块

    def setup_case_directory(self):
        """1. 创建案例目录"""
        if os.path.exists(self.case_path):
            shutil.rmtree(self.case_path)
        shutil.copytree(self.base_template_dir, self.case_path)

    def generate_mesh(self):
        """2. 几何与网格生成 (支持参数化与文件输入)"""
        geom_params = self.params.get("geometry", {})
        geom_type = geom_params.get("type")

        gmsh.initialize()

        if geom_type == 'file':
            # --- 新增逻辑：处理文件输入 ---
            file_path = geom_params.get("path")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Geometry file not found: {file_path}")
            
            gmsh.open(file_path)

            if 'transform' in geom_params:
                rotation = geom_params['transform']
                if 'rotate_y_deg' in rotation:
                    angle_rad = rotation['rotate_y_deg'] * 3.14159 / 180.0
                    gmsh.model.occ.rotate([(3, 1)], 0, 0, 0, 0, 1, 0, angle_rad)

        elif geom_type == 'airfoil':
            # --- 原有逻辑：参数化生成 ---
            # ... 此处为根据翼型名称等参数生成几何的代码 ...
            pass
        
        else:
            gmsh.finalize()
            raise ValueError(f"Unsupported geometry type: {geom_type}")

        # --- 后续流程 (创建流场域, 布尔运算, 生成网格) ---
        # ...
        gmsh.model.mesh.generate(3) # 伪代码：实际需要定义流场域和网格尺寸

        mesh_path = os.path.join(self.case_path, "geometry.msh")
        gmsh.write(mesh_path)
        gmsh.finalize()
        
        subprocess.run(["gmshToFoam", "geometry.msh"], cwd=self.case_path, check=True)


    def configure_case_files(self):
        """3. 配置文件参数替换"""
        env = Environment(loader=FileSystemLoader(self.case_path))
        for root, _, files in os.walk(self.case_path):
            for file in files:
                try:
                    template = env.get_template(os.path.relpath(os.path.join(root, file), self.case_path))
                    rendered_content = template.render(self.params)
                    with open(os.path.join(root, file), "w") as f:
                        f.write(rendered_content)
                except Exception:
                    # 忽略二进制文件或非模板文件
                    continue

    def execute_solver(self):
        """4. 执行CFD求解器"""
        # 这一步将在 "过程监控" 部分详细阐述
        # 需要使用 subprocess.Popen 启动进程，以便实时监控
        pass

```

## 3. 输入参数 (Input JSON)

Agent的输入是一个定义清晰的JSON对象。它支持两种主要的几何输入方式：

**A) 参数化生成 (示例 `input_parametric.json`):**
```json
{
    "case_name": "NACA0012_A5_M0.5",
    "geometry": {
        "type": "airfoil",
        "name": "NACA0012"
    },
    "transform": {
        "rotate_y_deg": 5.0
    },
    "flow_conditions": {
        "mach": 0.5,
        "temperature": 288.15,
        "pressure": 101325
    },
    "solver_settings": {
        "solver": "rhoSimpleFoam",
        "endTime": 2000,
        "deltaT": 0.01,
        "turbulence_model": "kOmegaSST"
    }
}
```

**B) 从文件输入 (示例 `input_file.json`):**
这是对接你OpenVSP等外部设计软件的推荐方式。

```json
{
    "case_name": "MyVSP_Model_AoA5_Mach0.7",
    "geometry": {
        "type": "file",
        "path": "D:/code/MyAircraft/vsp_model_v3.obj",
        "format": "obj",
        "transform": {
            "rotate_y_deg": 5.0
        }
    },
    "flow_conditions": {
        "mach": 0.7,
        "altitude_km": 10
    },
    "solver_settings": {
        "solver": "rhoSimpleFoam",
        "endTime": 2000,
        "turbulence_model": "kOmegaSST"
    }
}
```
*   在文件输入模式下，`geometry.transform`对象定义了对整个加载的几何体应用的变换，从而方便地设置迎角和侧滑角。

## 4. 流程执行逻辑

1.  **实例化**: `manager = WorkflowManager(case_params=read_from_json('input.json'))`
2.  **执行**: `manager.run_workflow()`
    *   **`setup_case_directory`**: 复制`template_case`到`cases/NACA0012_A5_M0.5`。
    *   **`generate_mesh`**: 根据`geometry`参数，调用Gmsh API生成机翼几何和网格。
    *   **`configure_case_files`**: 读取`flow_conditions`和`solver_settings`，使用Jinja2或简单的字符串替换，填充案例文件夹中所有文件的`{{...}}`占位符。
    *   **`execute_solver`**: 调用CFD求解器开始计算。

通过这种方式，整个CFD准备过程被完全自动化，为后续的计算和监控做好了准备。
