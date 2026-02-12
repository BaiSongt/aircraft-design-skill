# AI集成与自动循环迭代

这是将项目从“自动化”提升到“智能化”的关键一步。它包含两个方面：为AI模型准备数据，以及利用AI模型进行加速。

## 1. 自动循环迭代 (数据生成)

为了训练AI模型，我们需要大量的“输入-输出”数据对。自动循环迭代框架就是为此设计的。

**`CampaignManager.py` (战役管理器):**
这个脚本负责定义一个计算“战役”（Campaign），即一个参数空间，并为空间中的每一点启动一个CFD计算任务。

```python
import json
from workflow_manager import WorkflowManager # 假设之前的类在这里
import numpy as np

class CampaignManager:
    def __init__(self, campaign_config):
        self.config = campaign_config
        self.results_db = []

    def run_campaign(self):
        # 定义参数空间
        aoa_space = np.arange(
            self.config["parameter_space"]["aoa"]["min"],
            self.config["parameter_space"]["aoa"]["max"],
            self.config["parameter_space"]["aoa"]["step"]
        )
        
        base_params = self.config["base_parameters"]

        for aoa in aoa_space:
            # 1. 为每个参数点创建输入
            case_params = base_params.copy()
            case_params["case_name"] = f"case_aoa_{aoa:.1f}"
            case_params["geometry"]["angle_of_attack"] = float(aoa)
            
            # 2. 调用工作流管理器执行计算
            print(f"--- Running case for AoA = {aoa} ---")
            manager = WorkflowManager(case_params)
            status, results = manager.run_workflow() # run_workflow需要返回最终结果

            # 3. 收集结果
            if status == "SUCCESS":
                entry = {"aoa": aoa, "mach": base_params["flow_conditions"]["mach"], **results}
                self.results_db.append(entry)
        
        # 4. 保存数据集
        self.save_database()

    def save_database(self):
        import pandas as pd
        df = pd.DataFrame(self.results_db)
        df.to_csv("aicfd_database.csv", index=False)
```

**`campaign_config.json`:**
```json
{
    "parameter_space": {
        "aoa": { "min": -4.0, "max": 12.0, "step": 0.5 }
    },
    "base_parameters": {
        "geometry": { "type": "airfoil", "name": "NACA0012" },
        "flow_conditions": { "mach": 0.7 },
        "solver_settings": { ... }
    }
}
```

运行`CampaignManager`后，你将得到一个`aicfd_database.csv`文件，这就是AI模型的“教科书”。

## 2. AI代理模型 (Surrogate Model)

有了数据集，我们就可以训练一个模型来学习`[AoA, Mach] -> [Cl, Cd]`之间的映射。

**`train_surrogate.py`:**
```python
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 1. 加载和预处理数据
df = pd.read_csv("aicfd_database.csv")
features = df[['aoa', 'mach']].values
labels = df[['Cl_mean', 'Cd_mean']].values

X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2)

scaler_X = StandardScaler().fit(X_train)
X_train_scaled = scaler_X.transform(X_train)
X_test_scaled = scaler_X.transform(X_test)

# 2. 定义神经网络 (使用PyTorch)
class SurrogateModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(2, 64), nn.ReLU(),
            nn.Linear(64, 64), nn.ReLU(),
            nn.Linear(64, 2)
        )
    def forward(self, x):
        return self.network(x)

# 3. 训练模型
model = SurrogateModel()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# ... 此处省略标准PyTorch训练循环 ...
# 训练完成后，保存模型权重和scaler
torch.save(model.state_dict(), "surrogate_model.pth")
import joblib
joblib.dump(scaler_X, 'scaler_X.pkl')

```

## 3. AI集成与智能决策

最后，我们将训练好的AI模型集成回`AICFD Agent`。

**更新`AICFD_Agent`的主逻辑:**

```python
class AICFDAgent:
    def __init__(self):
        # 加载AI模型和scaler
        self.surrogate_model = SurrogateModel()
        self.surrogate_model.load_state_dict(torch.load("surrogate_model.pth"))
        self.surrogate_model.eval()
        self.scaler = joblib.load('scaler_X.pkl')

    def run(self, case_params, mode='accurate'):
        if mode == 'fast':
            # 使用AI模型进行快速预测
            return self.predict_with_ai(case_params)
        elif mode == 'accurate':
            # 运行完整CFD流程
            manager = WorkflowManager(case_params)
            return manager.run_workflow()
        else:
            raise ValueError("Mode must be 'fast' or 'accurate'")

    def predict_with_ai(self, case_params):
        # 从输入参数中提取特征
        features = np.array([[
            case_params["geometry"]["angle_of_attack"],
            case_params["flow_conditions"]["mach"]
        ]])
        # 标准化
        features_scaled = self.scaler.transform(features)
        features_tensor = torch.FloatTensor(features_scaled)
        
        # 预测
        with torch.no_grad():
            predictions = self.surrogate_model(features_tensor).numpy()[0]
        
        return {
            "Cl_pred": predictions[0],
            "Cd_pred": predictions[1],
            "status": "PREDICTED_FAST"
        }
```

现在，你的Agent拥有了两种能力：既可以花费数小时进行一次高精度计算，也可以在几毫秒内给出一个相当准确的预测。这为飞行器设计的快速迭代和优化奠定了坚实的基础。
