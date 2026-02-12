# 用于测试WorkflowManager的临时脚本

import json
import os
import sys
from src.workflow_manager import WorkflowManager

def create_mock_forces_data(case_path):
    """在案例目录中创建一个模拟的forces.dat文件用于测试。"""
    forces_dir = os.path.join(case_path, "postProcessing/forces/0")
    os.makedirs(forces_dir, exist_ok=True)
    forces_file = os.path.join(forces_dir, "forces.dat")
    
    mock_data = """
# Time       Cm         Cd         Cl         Cl(f)      Cl(r)
1          0.1        0.01       0.2        0.1        0.1
2          0.11       0.012      0.25       0.12       0.13
3          0.12       0.014      0.30       0.15       0.15
4          0.125      0.015      0.33       0.16       0.17
5          0.128      0.016      0.35       0.17       0.18
6          0.129      0.0165     0.36       0.18       0.18
7          0.130      0.0168     0.365      0.18       0.185
8          0.130      0.017      0.368      0.182      0.186
9          0.130      0.0171     0.370      0.183      0.187
10         0.130      0.0172     0.371      0.184      0.187
"""
    with open(forces_file, "w") as f:
        f.write(mock_data)
    print(f"Created mock forces.dat at {forces_file}")


def test_workflow_end_to_end():
    """
    测试端到端的完整工作流（使用模拟求解器和模拟结果）。
    """
    python_executable = sys.executable.replace('\\', '/')

    # 1. 定义测试输入
    test_params = {
        "case_name": "test_case_final_01",
        "geometry": {
            "type": "file",
            "path": "assets/simple_cube.obj"
        },
        "solver_settings": {
            "solver": f"{python_executable} ../../mock_solver.py",
            "endTime": 500, "deltaT": 0.5, "timeout": 30
        }
    }

    # 2. 实例化并运行工作流 (不包括分析)
    manager = WorkflowManager(case_params=test_params)
    try:
        manager.run_workflow()
        
        # 3. 手动创建模拟的求解器输出
        create_mock_forces_data(manager.case_path)
        
        # 4. 单独运行并测试分析步骤
        manager.analyze_results()

        print("\\n--- E2E Test Verification ---")
        report_path = os.path.join(manager.case_path, "REPORT.md")
        figure_path = os.path.join(manager.case_path, "report_figures", "convergence_history.png")

        print(f"Checking for {report_path}... {'Exists' if os.path.exists(report_path) else 'Not Found'}")
        print(f"Checking for {figure_path}... {'Exists' if os.path.exists(figure_path) else 'Not Found'}")

        if os.path.exists(report_path) and os.path.exists(figure_path):
            print("\\nTest successful! End-to-end workflow completed and report generated.")
        else:
            raise AssertionError("Report or figure not generated.")

    except Exception as e:
        print(f"\\nTest failed: {e}")
        # Re-raise exception to make it clear the test failed
        raise

if __name__ == "__main__":
    test_workflow_end_to_end()
