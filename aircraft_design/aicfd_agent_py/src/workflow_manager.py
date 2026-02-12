import os
import shutil
import subprocess
import shlex
import time
import re
from jinja2 import Environment, FileSystemLoader
from src.result_analyzer import ResultAnalyzer

class WorkflowManager:
    """
    管理单个CFD计算任务的完整工作流。
    """
    def __init__(self, case_params, base_template_dir="templates/template_case_2d", test_mode=False):
        """
        初始化工作流管理器。

        :param case_params: 包含所有计算参数的字典 (从JSON加载)。
        :param base_template_dir: 基础模板案例的路径。
        :param test_mode: 如果为True，则跳过对外部程序的调用（例如gmshToFoam）。
        """
        self.params = case_params
        self.case_name = self.params.get("case_name", "default_case")
        self.case_path = os.path.join("cases", self.case_name)
        self.base_template_dir = base_template_dir
        self.test_mode = test_mode
        
        # 初始化Jinja2模板环境
        self.template_env = Environment(loader=FileSystemLoader(self.base_template_dir))

    def run_workflow(self):
        """
        按顺序执行完整的CFD工作流。
        """
        print(f"--- Starting Workflow for Case: {self.case_name} ---")
        
        # 步骤 1: 创建并配置案例目录
        self.setup_case_directory()
        self.configure_case_files()

        # 步骤 2: 生成几何与网格
        self.generate_mesh()

        # 步骤 3: 运行求解器
        self.execute_solver()
        
        # 步骤 4: 分析结果
        self.analyze_results()

        print(f"--- Workflow for Case: {self.case_name} completed. ---")

    def analyze_results(self):
        """
        初始化并运行ResultAnalyzer。
        """
        analyzer = ResultAnalyzer(case_path=self.case_path, case_params=self.params)
        analyzer.run_analysis()

    def setup_case_directory(self):
        """
        如果已存在旧案例目录，则删除它，并从模板复制一个新的。
        """
        print(f"Setting up case directory at: {self.case_path}")
        if os.path.exists(self.case_path):
            shutil.rmtree(self.case_path)
        shutil.copytree(self.base_template_dir, self.case_path)

    def configure_case_files(self):
        """
        遍历案例目录中的所有文件，使用Jinja2渲染模板，填充参数。
        """
        print("Configuring case files with parameters...")
        config_data = self.params.get('solver_settings', {})
        
        for root, _, files in os.walk(self.case_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                template_rel_path = os.path.relpath(file_path, self.case_path).replace('\\', '/')
                
                try:
                    template = self.template_env.get_template(template_rel_path)
                    rendered_content = template.render(config_data)
                    with open(file_path, "w") as f:
                        f.write(rendered_content)
                except Exception:
                    pass

    def generate_mesh(self):
        """
        使用Gmsh生成几何和网格，并转换为OpenFOAM格式。
        """
        print("Starting mesh generation...")
        geom_params = self.params.get("geometry", {})
        geom_type = geom_params.get("type")
        abs_case_path = os.path.abspath(self.case_path)
        
        try:
            import gmsh
            gmsh.initialize()
            
            if geom_type == 'file':
                file_path = geom_params.get("path")
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(os.path.join(os.getcwd(), file_path))
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Geometry file not found: {file_path}")
                print(f"Loading geometry from: {file_path}")
                gmsh.merge(file_path)
            else:
                raise ValueError(f"Unsupported geometry type for meshing: {geom_type}")

            gmsh.model.occ.synchronize()
            fluid_box = gmsh.model.occ.addBox(-10, -10, -10, 20, 20, 20)
            gmsh.model.occ.synchronize()
            
            print("Generating 3D mesh...")
            gmsh.model.mesh.generate(3)
            mesh_file = os.path.join(abs_case_path, 'geometry.msh')
            print(f"Writing mesh file to: {mesh_file}")
            gmsh.write(mesh_file)
        finally:
            gmsh.finalize()

        if not self.test_mode:
            print("Converting mesh to OpenFOAM format...")
            try:
                subprocess.run(
                    ["gmshToFoam", "geometry.msh"],
                    cwd=abs_case_path, check=True, capture_output=True, text=True
                )
                print("gmshToFoam conversion successful.")
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] gmshToFoam failed! Stderr: {e.stderr}")
                raise
        else:
            print("--- TEST MODE: Skipping gmshToFoam conversion. ---")
            # Manually create the directory that gmshToFoam would have
            os.makedirs(os.path.join(abs_case_path, 'constant', 'polyMesh'), exist_ok=True)

    def execute_solver(self):
        """
        执行CFD求解器，并实时监控其输出。
        """
        print("Executing solver...")
        solver_settings = self.params.get('solver_settings', {})
        solver_cmd_str = solver_settings.get('solver', 'simpleFoam')
        solver_cmd = shlex.split(solver_cmd_str)
        
        log_file_path = os.path.join(self.case_path, "solver.log")
        abs_case_path = os.path.abspath(self.case_path)
        solver_process = None
        
        start_time = time.time()
        timeout = solver_settings.get("timeout", 3600) # 默认1小时超时

        try:
            with open(log_file_path, "w") as log_file:
                solver_process = subprocess.Popen(
                    solver_cmd,
                    cwd=abs_case_path,
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )
            
            print(f"Solver started with PID: {solver_process.pid}")

            while solver_process.poll() is None:
                self.monitor_convergence(log_file_path)
                self.check_for_errors(log_file_path, solver_process)
                
                if time.time() - start_time > timeout:
                    print("[ERROR] Solver timed out.")
                    solver_process.kill()
                    raise RuntimeError("Solver process killed due to timeout.")

                time.sleep(2) # 监控间隔

            if self.test_mode and solver_process.returncode != 0:
                print(f"--- TEST MODE: Solver exited with code {solver_process.returncode}. Ignoring. ---")
            elif not self.test_mode and solver_process.returncode != 0:
                raise RuntimeError(f"Solver exited with non-zero code: {solver_process.returncode}")

            print("Solver finished successfully.")
            return "SUCCESS"
        except Exception as e:
            print(f"[ERROR] An exception occurred during solver execution: {e}")
            if solver_process:
                solver_process.kill()
            raise

    def monitor_convergence(self, log_file_path):
        """解析日志文件，打印最新的残差。"""
        try:
            with open(log_file_path, "r") as f:
                lines = f.readlines()
            
            # 正则表达式匹配OpenFOAM的残差输出
            residual_pattern = re.compile(r"Solving for (\w+), Initial residual = ([\d.eE+-]+)")
            
            # 只关心最后几行，避免重复打印
            last_few_lines = lines[-10:]
            residuals_found = []
            for line in last_few_lines:
                match = residual_pattern.search(line)
                if match:
                    residuals_found.append(f"{match.group(1)}: {float(match.group(2)):.4e}")
            
            if residuals_found:
                print(f"  residuals - {', '.join(residuals_found)}")

        except FileNotFoundError:
            pass # 日志文件可能尚未创建

    def check_for_errors(self, log_file_path, process):
        """检查日志中是否有致命错误，如'NaN'。"""
        try:
            with open(log_file_path, 'r') as f:
                content = f.read()
            if "NaN" in content or "nan" in content:
                print("[ERROR] 'NaN' detected in solver output. Terminating.")
                process.kill()
                raise RuntimeError("Solver diverged with NaN.")
        except FileNotFoundError:
            pass
