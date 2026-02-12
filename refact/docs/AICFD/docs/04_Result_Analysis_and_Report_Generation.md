# 结果提取、分析、可视化与报告生成

计算完成后，原始数据是分散在各种文件中的。此阶段的目标是自动地将这些数据转化为有价值、易于理解的信息。

## 1. 结果数据提取

关键的气动力/力矩数据通常在`postProcessing`目录中。

**`ResultAnalyzer` Class:**

```python
import pandas as pd
import os

class ResultAnalyzer:
    def __init__(self, case_path):
        self.case_path = case_path
        self.forces_path = os.path.join(case_path, "postProcessing/forces/0/forces.dat")

    def extract_forces(self):
        """从forces.dat文件中提取力和力矩系数"""
        if not os.path.exists(self.forces_path):
            print("forces.dat not found.")
            return None

        # 使用pandas读取数据，注意跳过注释行并处理空格分隔符
        df = pd.read_csv(
            self.forces_path,
            comment='#',
            header=None,
            delim_whitespace=True,
            names=[
                "time", "Cm", "Cd", "Cl", "Cl(f)", "Cl(r)",
                # 根据OpenFOAM版本和设置，列名可能不同
            ]
        )
        return df
```

## 2. 数据分析

通常我们不关心瞬态值，而是关心计算收敛后的稳态值。

```python
# 在 ResultAnalyzer 类中
def analyze_convergence(self, df, stable_fraction=0.4):
    """计算收敛后的平均值"""
    if df is None or len(df) == 0:
        return {}
    
    # 取最后40%的数据点作为稳定状态
    stable_start_index = int(len(df) * (1 - stable_fraction))
    stable_df = df.iloc[stable_start_index:]
    
    mean_values = {
        "Cl_mean": stable_df["Cl"].mean(),
        "Cd_mean": stable_df["Cd"].mean(),
        "Cm_mean": stable_df["Cm"].mean(),
    }
    return mean_values
```

## 3. 结果可视化

使用`matplotlib`自动生成图表，直观地展示计算过程和结果。

```python
# 在 ResultAnalyzer 类中
import matplotlib.pyplot as plt

def generate_plots(self, df, results):
    """生成收敛历史图并保存"""
    if df is None:
        return

    fig_path = os.path.join(self.case_path, "report_figures")
    os.makedirs(fig_path, exist_ok=True)

    # 绘制Cl, Cd, Cm随时间的收敛历史
    plt.figure(figsize=(12, 8))
    plt.plot(df['time'], df['Cl'], label='Cl')
    plt.plot(df['time'], df['Cd'], label='Cd')
    plt.plot(df['time'], df['Cm'], label='Cm')
    
    # 绘制平均值线
    plt.axhline(y=results['Cl_mean'], linestyle='--', color='blue', label=f"Cl_mean: {results['Cl_mean']:.4f}")
    plt.axhline(y=results['Cd_mean'], linestyle='--', color='orange', label=f"Cd_mean: {results['Cd_mean']:.4f}")

    plt.title("Aerodynamic Coefficients Convergence")
    plt.xlabel("Time Step")
    plt.ylabel("Coefficient")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(fig_path, "convergence_history.png"))
    plt.close()
```

## 4. 自动报告生成

将所有输入、结果和图表汇总到一个文件中，方便归档和查阅。Markdown是一个很好的选择。

```python
# 在 ResultAnalyzer 类中
def generate_markdown_report(self, case_params, results):
    """生成Markdown格式的总结报告"""
    report_path = os.path.join(self.case_path, "REPORT.md")
    
    report_content = f"""
# AICFD Calculation Report

**Case Name**: {case_params.get('case_name')}

## 1. Input Parameters

```json
{case_params}
```

## 2. Key Results

| Coefficient | Value |
|-------------|-------|
| Cl (mean)   | {results.get('Cl_mean', 'N/A'):.4f} |
| Cd (mean)   | {results.get('Cd_mean', 'N/A'):.4f} |
| Cm (mean)   | {results.get('Cm_mean', 'N/A'):.4f} |

## 3. Convergence History

![Convergence History](./report_figures/convergence_history.png)

## 4. Future: Flow Field Visualization

(placeholder for ParaView screenshots)

"""
    with open(report_path, "w") as f:
        f.write(report_content)

```

**集成到主流程**:
在`WorkflowManager`成功执行完求解器后，调用`ResultAnalyzer`。

```python
# ... 在 WorkflowManager.run_workflow() 的末尾
from result_analyzer import ResultAnalyzer # 假设以上代码在 result_analyzer.py

analyzer = ResultAnalyzer(self.case_path)
df = analyzer.extract_forces()
final_results = analyzer.analyze_convergence(df)
analyzer.generate_plots(df, final_results)
analyzer.generate_markdown_report(self.params, final_results)
```

这样，每次计算任务结束后，你都会在对应的案例文件夹中得到一个图文并茂的`REPORT.md`，极大地提高了效率。
