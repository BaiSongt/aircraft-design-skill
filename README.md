# ChatUI飞机设计系统

基于SKILL和AI技术的现代化飞机设计平台，支持多AI模型、实时3D可视化和包络图分析。

## 功能特性

### 核心功能
- 🤖 **智能聊天界面**：现代化的ChatUI，支持Markdown和代码高亮
- 🤖 **多AI模型支持**：支持10+ AI模型（国内外+本地）
- 🤖 **实时3D可视化**：基于React Three Fiber的高性能3D渲染
- 🤖 **包络图分析**：交互式包络图，支持多参数分析
- 🤖 **SKILL集成**：完整的飞机设计技能调用
- 🤖 **实时进度跟踪**：WebSocket实时通信
- 🤖 **暗色模式**：支持亮色/暗色主题切换

### 支持的AI模型

#### 国外模型
- OpenAI GPT-4 / GPT-4 Turbo
- Anthropic Claude 3 Opus / Sonnet
- Google Gemini Pro

#### 国内模型
- 通义千问
- 智谱AI GLM-4
- 月之暗面 V1
- DeepSeek Chat

#### 本地模型
- Ollama (Llama3)
- LocalAI
- vLLM

### 支持的SKILL模块

- 翼型库（NACA 4/5/6系列）
- 几何建模（机翼、机身、尾翼等）
- 退化几何（平板、梁、圆盘）
- 寄生阻力（摩擦、形状、干扰）
- 表面分析（网格、法向量、曲率）
- VSPAERO接口（输入/输出解析）
- 载荷分析（气动、惯性、结构）
- 旋翼机分析（气动力、性能）

## 技术栈

### 前端
- **框架**：React 18 + TypeScript
- **构建工具**：Vite
- **UI组件**：shadcn/ui (Radix UI)
- **3D渲染**：React Three Fiber (Three.js)
- **图表**：Plotly.js
- **状态管理**：Zustand
- **实时通信**：Socket.IO Client
- **样式**：Tailwind CSS

### 后端
- **框架**：FastAPI (Python 3.12)
- **AI集成**：LangChain
- **任务队列**：Celery + Redis
- **WebSocket**：Socket.IO
- **数据库**：SQLite

## 项目结构

```
aircraft-design-skill/
├── frontend/                    # React前端
│   ├── src/
│   │   ├── components/         # UI组件
│   │   ├── hooks/              # 自定义Hooks
│   │   ├── lib/                # 工具库
│   │   ├── pages/              # 页面
│   │   ├── App.tsx             # 应用入口
│   │   └── main.tsx           # React入口
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
├── backend/                     # FastAPI后端
│   ├── app.py                  # FastAPI应用入口
│   ├── api/                    # API路由
│   ├── services/                # 业务服务
│   ├── models/                  # 数据模型
│   ├── websocket/               # WebSocket管理
│   ├── tasks/                  # 异步任务
│   ├── config/                  # 配置文件
│   └── utils/                  # 工具函数
├── aircraft_design/             # SKILL模块
├── docs/                       # 文档
├── config/                     # 配置文件
└── README.md                   # 本文件
```

## 快速开始

### 前置要求

- Node.js 18+
- Python 3.12+
- Redis (用于任务队列)
- Git

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/aircraft-design-skill.git
cd aircraft-design-skill
```

2. 安装前端依赖
```bash
cd frontend
npm install
```

3. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

4. 启动Redis（用于任务队列）
```bash
redis-server
```

5. 配置AI提供商
- 在前端设置页面配置AI API Key
- 或编辑 `config/ai_providers.json`

6. 启动开发服务器

前端（开发模式）：
```bash
cd frontend
npm run dev
```

后端（开发模式）：
```bash
cd backend
uvicorn app:app --reload
```

7. 访问应用
- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

## 使用指南

### 1. 配置AI提供商

1. 打开应用，进入"设置"页面
2. 选择AI提供商（OpenAI、Anthropic等）
3. 输入API Key
4. （可选）配置自定义Base URL和模型名称
5. 点击"保存"

### 2. 设计飞机

1. 在聊天界面输入设计需求，例如：
   ```
   设计一架机翼，面积30m²，展弦比8.0，梯形比0.6
   ```
2. AI会调用相应的SKILL模块
3. 实时查看计算进度
4. 查看计算结果

### 3. 查看包络图

1. 点击"包络图"标签页
2. 选择X轴和Y轴参数
3. 查看交互式包络图
4. 可以缩放、平移图表
5. 导出图表数据

### 4. 查看3D模型

1. 点击"3D模型"标签页
2. 查看实时生成的3D模型
3. 使用鼠标旋转、缩放、平移模型
4. 切换不同视图（Top、Side、Front、Iso）
5. 导出模型文件

## 开发指南

### 前端开发

```bash
cd frontend
npm run dev          # 启动开发服务器
npm run build        # 构建生产版本
npm run lint         # 代码检查
npm run preview      # 预览生产构建
```

### 后端开发

```bash
cd backend
uvicorn app:app --reload    # 启动开发服务器
celery -A tasks worker   # 启动Celery Worker
pytest                    # 运行测试
```

## API文档

完整的API文档请访问：http://localhost:8000/docs

主要端点：
- `GET /api/ai/providers` - 列出AI提供商
- `POST /api/ai/configure` - 配置AI提供商
- `POST /api/ai/chat` - 与AI聊天
- `POST /api/skill/call` - 调用SKILL模块
- `GET /api/skill/progress/{task_id}` - 获取任务进度
- `GET /api/skill/result/{task_id}` - 获取任务结果
- `POST /api/visualization/3d` - 生成3D模型
- `POST /api/envelope/generate` - 生成包络图

## 架构文档

详细的架构文档请参考：[docs/chatui_architecture.md](docs/chatui_architecture.md)

## 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证。

## 联系方式

- 项目主页：[https://github.com/yourusername/aircraft-design-skill](https://github.com/yourusername/aircraft-design-skill)
- 问题反馈：[Issues](https://github.com/yourusername/aircraft-design-skill/issues)
- 文档：[docs/](docs/)

## 致谢

- SKILL团队 - 固定翼飞机设计技能
- LangChain团队 - AI应用框架
- shadcn/ui团队 - 现代化UI组件
- React Three Fiber团队 - 3D渲染库
- Plotly.js团队 - 交互式图表库
