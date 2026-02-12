# 过程监控、日志与错误处理

一个健壮的自动化系统必须能够监控其执行的任务，并在出现问题时做出响应。对于耗时较长的CFD计算尤其如此。

## 1. 实时过程监控

我们不能使用简单的`subprocess.run()`，因为它会阻塞直到命令结束。必须使用`subprocess.Popen`来启动求解器，这样主Python脚本可以并行地执行监控任务。

```python
# 在 WorkflowManager 类中的 execute_solver 方法
import subprocess
import time
import re

def execute_solver(self):
    """执行CFD求解器并实时监控"""
    log_file_path = os.path.join(self.case_path, "solver.log")
    solver_process = None

    with open(log_file_path, "w") as log_file:
        # 启动求解器进程，并将stdout和stderr重定向到日志文件
        solver_process = subprocess.Popen(
            [self.params["solver_settings"]["solver"]],
            cwd=self.case_path,
            stdout=log_file,
            stderr=subprocess.STDOUT
        )

    # 监控循环
    while solver_process.poll() is None:
        self.monitor_convergence(log_file_path)
        self.check_for_errors(log_file_path)
        
        # 添加超时检查
        # if time.time() - start_time > self.params.get("timeout", 3600):
        #     solver_process.kill()
        #     self.log("Error: Solver timed out.")
        #     return "TIMEOUT"

        time.sleep(10) # 每10秒检查一次

    # 检查最终退出码
    if solver_process.returncode != 0:
        self.log(f"Error: Solver exited with code {solver_process.returncode}")
        return "FAILED"
    
    self.log("Solver finished successfully.")
    return "SUCCESS"

```

## 2. 收敛性监控

监控的核心是解析求解器输出的残差（residuals）。

```python
# 在 WorkflowManager 类中添加 monitor_convergence 方法
def monitor_convergence(self, log_file_path):
    """解析日志文件，检查残差"""
    # 正则表达式用于匹配OpenFOAM的残差输出行
    # Initial residual (p): 0.9, Final residual: 1e-5
    residual_pattern = re.compile(r"Initial residual for (\w+), Final residual = ([\d.eE+-]+)")
    
    with open(log_file_path, "r") as f:
        # 只读取最后几行以提高效率
        lines = f.readlines()[-20:] 
    
    residuals = {}
    for line in lines:
        match = residual_pattern.search(line)
        if match:
            variable = match.group(1)
            residual_value = float(match.group(2))
            residuals[variable] = residual_value
    
    if residuals:
        self.log(f"Current Residuals: {residuals}")
        # 在这里可以添加更复杂的收敛判断逻辑
        # 例如，如果连续N次迭代残差没有下降，则认为停滞
```

## 3. 错误处理

*   **求解器崩溃**: `solver_process.poll()`会返回一个非零的退出码。这是最直接的失败信号。
*   **NaN (Not a Number) 错误**: 求解器输出中出现"NaN"是计算发散的明确信号。可以在`check_for_errors`中实现。

```python
# 在 WorkflowManager 类中添加 check_for_errors 方法
def check_for_errors(self, log_file_path):
    with open(log_file_path, 'r') as f:
        content = f.read()
    if "NaN" in content:
        # 发现NaN，立即终止进程
        solver_process.kill()
        self.log("Error: NaN detected in solver output. Terminating.")
        raise RuntimeError("Solver diverged with NaN")
```

## 4. 日志系统

使用Python内置的`logging`模块，而不是简单的`print()`。这允许你：
*   控制日志级别（DEBUG, INFO, WARNING, ERROR）。
*   将日志同时输出到控制台和文件。
*   格式化日志输出，包含时间戳和模块名。

**配置示例 `logger.py`:**
```python
import logging

def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger

# 在主脚本中:
# logger = setup_logger('AICFD_Agent', 'agent.log')
# logger.info('Starting new case...')
```

通过这套机制，Agent不仅能执行任务，还能“感知”任务的执行状态，从而做出判断，保证了自动化流程的稳定性和可靠性。
