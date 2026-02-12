import os
import pandas as pd
import matplotlib.pyplot as plt
import json

class ResultAnalyzer:
    """
    负责提取、分析和报告CFD计算结果。
    """
    def __init__(self, case_path, case_params):
        """
        初始化结果分析器。

        :param case_path: 案例文件夹的路径。
        :param case_params: 本次计算的输入参数，用于报告生成。
        """
        self.case_path = case_path
        self.case_params = case_params
        # 结果文件的典型路径
        self.forces_path = os.path.join(self.case_path, "postProcessing/forces/0/forces.dat")
        self.report_fig_dir = os.path.join(self.case_path, "report_figures")
        os.makedirs(self.report_fig_dir, exist_ok=True)

    def run_analysis(self):
        """
        执行完整的分析和报告流程。
        """
        print("Analyzing results...")
        df = self.extract_forces()
        if df is None:
            print("[Warning] Could not extract forces. Skipping analysis.")
            return

        final_results = self.analyze_convergence(df)
        self.generate_plots(df, final_results)
        self.generate_markdown_report(final_results)
        print(f"Analysis complete. Report generated at {os.path.join(self.case_path, 'REPORT.md')}")

    def extract_forces(self):
        """从forces.dat文件中提取力和力矩系数。"""
        if not os.path.exists(self.forces_path):
            print(f"[Warning] forces.dat not found at {self.forces_path}")
            return None

        try:
            df = pd.read_csv(
                self.forces_path,
                comment='#',
                header=None,
                delim_whitespace=True,
                names=["time", "Cm", "Cd", "Cl", "Cl(f)", "Cl(r)"]
            )
            return df
        except Exception as e:
            print(f"[ERROR] Failed to parse forces.dat: {e}")
            return None

    def analyze_convergence(self, df, stable_fraction=0.4):
        """计算收敛后的平均值。"""
        if df is None or len(df) == 0:
            return {}
        
        stable_start_index = int(len(df) * (1 - stable_fraction))
        stable_df = df.iloc[stable_start_index:]
        
        mean_values = {
            "Cl_mean": stable_df["Cl"].mean(),
            "Cd_mean": stable_df["Cd"].mean(),
            "Cm_mean": stable_df["Cm"].mean(),
        }
        print(f"  Converged results - Cl: {mean_values['Cl_mean']:.4f}, Cd: {mean_values['Cd_mean']:.4f}")
        return mean_values

    def generate_plots(self, df, results):
        """生成收敛历史图并保存。"""
        if df is None:
            return

        plt.figure(figsize=(12, 7))
        plt.plot(df['time'], df['Cl'], label='Cl', color='blue')
        plt.plot(df['time'], df['Cd'], label='Cd', color='red')
        
        plt.axhline(y=results['Cl_mean'], linestyle='--', color='blue', label=f"Cl_mean: {results['Cl_mean']:.4f}")
        plt.axhline(y=results['Cd_mean'], linestyle='--', color='red', label=f"Cd_mean: {results['Cd_mean']:.4f}")

        plt.title(f"Aerodynamic Coefficients Convergence for {self.case_params.get('case_name')}")
        plt.xlabel("Time Step / Iteration")
        plt.ylabel("Coefficient")
        plt.legend()
        plt.grid(True)
        
        fig_path = os.path.join(self.report_fig_dir, "convergence_history.png")
        plt.savefig(fig_path)
        plt.close()

    def generate_markdown_report(self, results):
        """生成Markdown格式的总结报告。"""
        report_path = os.path.join(self.case_path, "REPORT.md")
        
        # 美化输入参数的JSON显示
        params_str = json.dumps(self.case_params, indent=4)
        
        report_content = f"""
# AICFD Calculation Report

**Case Name**: {self.case_params.get('case_name')}

---

## 1. Input Parameters

```json
{params_str}
```

---

## 2. Key Results (Converged)

| Coefficient | Value |
|-------------|:-----:|
| Cl (mean)   | {results.get('Cl_mean', 'N/A'):.5f} |
| Cd (mean)   | {results.get('Cd_mean', 'N/A'):.5f} |
| Cm (mean)   | {results.get('Cm_mean', 'N/A'):.5f} |

---

## 3. Convergence History

![Convergence History](./report_figures/convergence_history.png)

"""
        with open(report_path, "w") as f:
            f.write(report_content)
