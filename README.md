

# Aircraft Design Skill System

一个基于 Python 的现代固定翼飞机总体设计与分析系统，集成了参数化几何建模、实时可视化和 AI 辅助设计功能。

## 🚀 核心功能

### 1. 总体设计 (Overall Sizing)
- **Class I/II 重量估算**：基于统计学公式与物理模型的迭代收敛。
- **约束分析 (Constraint Analysis)**：起飞、爬升、巡航、机动、着陆等多约束下的设计点选择。
- **任务性能分析**：载荷-航程图 (Payload-Range) 与飞行包络线 (Flight Envelope) 计算。

### 2. 几何建模 (Geometry Modeling)
- **参数化建模**：支持机翼（后掠、上反、扭转）、机身、尾翼的参数化定义。
- **详细外形生成**：自动生成翼型坐标、LOFT 曲面与三视图。
- **OpenVSP 集成**：自动生成 OpenVSP 脚本并导出 OBJ 模型，支持高精度气动分析接口。

### 3. 实时可视化 (Real-time Visualization)
- **交互式仪表盘**：
  - **左侧**：动态 MTOW 收敛图、约束分析图、载荷航程图。
  - **中间**：PyVista 高性能 3D 渲染视图 + 标准三视图（严格对齐）。
  - **右侧**：设计报告图表库 (Report Gallery)。
- **拖拽式布局**：基于 PySide6 的可拖拽分栏设计，支持多屏适配与自定义布局。
- **图表联动**：支持点击图表数据点查看详细状态。

### 4. AI 技能集成 (Skill Integration)
- 内置多个设计技能 (Skill) 定义，支持 AI 代理通过自然语言调用设计流程。
- 覆盖气动、结构、重量、推进、稳定性等多个学科模块。

## 🛠️ 技术栈

- **核心计算**: `Python 3.12`, `NumPy`, `SciPy`
- **可视化**: `PySide6 (Qt)`, `PyVista (VTK)`, `Matplotlib`
- **数据交互**: `Socket`, `Pickle` (进程间通信)
- **几何引擎**: 自研参数化引擎 + `OpenVSP` 桥接

## 📦 安装指南

1. **克隆仓库**
   ```bash
   git clone https://github.com/baisongtao/aircraft-design-skill.git
   cd aircraft-design-skill
   ```

2. **创建虚拟环境 (推荐)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # venv\Scripts\activate   # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

## 🖥️ 使用方法

### 运行总体设计流程

使用 `run_sizing` 模块启动设计迭代。如需实时可视化，请**先在另一个独立的终端**启动可视化服务器：

```bash
# 终端 1：启动可视化服务器 (可选)
python -m aircraft_design.gui.server

# 终端 2：运行总体设计流程
python -m aircraft_design.run_sizing sizing_input.json --project-name "ProjectName"
```

**参数说明**:
- `input_file`: 输入配置文件路径 (如 `sizing_input.json`)
- `--project-name` / `-n`: 项目名称 (默认: aircraft_sizing)
- `--output-dir` / `-o`: 输出目录 (默认: output)
- `--viz-port`: 可视化服务器端口 (默认: 9999)
- `--no-viz`: 禁用实时可视化界面

### 示例输入文件 (sizing_input.json)

```json
{
    "requirements": {
        "range_m": 2000000,
        "payload_kg": 1000.0,
        "cruise_mach": 0.8,
        "cruise_altitude_m": 11000.0,
        "takeoff_distance_m": 800.0,
        "landing_distance_m": 800.0
    },
    "initial_guess": {
        "mtow": 10000.0,
        "wing_loading": 3000.0,
        "thrust_to_weight": 0.5
    }
}
```

## 📂 项目结构

```
aircraft-design-skill/
├── aircraft_design/           # 核心代码包
│   ├── gui/                  # PySide6 可视化界面
│   ├── geometry_*.py         # 几何建模模块
│   ├── sizing.py             # 总体设计算法
│   ├── analysis/             # 学科分析模块 (气动/结构/推进)
│   └── run_sizing.py         # 主程序入口
├── skills/                   # AI Skill 定义文件
├── docs/                     # 文档与教程
├── examples/                 # 示例文件
├── output/                   # 运行结果输出目录
├── requirements.txt          # 项目依赖
└── README.md                 # 项目说明
```

## 📚 文档资源

- [Skill Development Guide](docs/theory/SKILL_development_guide.md): 技能开发指南
- [Visualization Manual](docs/visualization_manual.md): 可视化模块说明
