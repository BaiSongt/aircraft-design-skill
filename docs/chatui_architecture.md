# ChatUI飞机设计系统 - 架构文档

## 系统概述

ChatUI飞机设计系统是一个现代化的、基于Web的飞机设计平台，集成了SKILL（固定翼飞机设计技能）、多AI模型支持、实时3D可视化和包络图分析功能。

## 技术架构

### 前端架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端 (React + TypeScript)                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  UI Components │  │   Hooks      │  │   Libraries    │ │
│  │              │  │              │  │              │ │
│  │ - ChatMessage│  │ - useAIProvider│  │ - shadcn/ui   │ │
│  │ - ModelSelect│  │ - useWebSocket│  │ - Plotly.js   │ │
│  │ - ParamInput│  │ - useSkillCalls│  │ - React Three  │ │
│  │ - Envelope   │  │              │  │   Fiber        │ │
│  │ - 3DViewer   │  │              │  │              │ │
│  │ - ResultTable│  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Pages (路由)                    │ │
│  │                                              │ │
│  │ - Main (主页面)                            │ │
│  │ - Settings (设置)                           │ │
│  │ - History (历史)                             │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐ │
│  │              App (应用入口)                    │ │
│  │                                              │ │
│  │ - 状态管理 (Zustand)                        │ │
│  │ - 路由管理                                    │ │
│  │ - 主题切换 (暗色/亮色)                     │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 后端架构

```
┌─────────────────────────────────────────────────────────────────┐
│              后端 (FastAPI + Python 3.12)             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  API Routes   │  │  Services     │  │  WebSocket    │ │
│  │              │  │              │  │              │ │
│  │ - AI Providers│  │ - AI Service  │  │ - Manager     │ │
│  │ - Skill Calls  │  │ - Skill Svc   │  │ - Handlers     │ │
│  │ - Visualization│  │ - Calculation  │  │              │ │
│  │ - Envelope    │  │ - Model Svc    │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Task Queue (Celery + Redis)           │ │
│  │                                              │ │
│  │ - 异步任务队列                                │ │
│  │ - 进度跟踪                                    │ │
│  │ - 结果缓存                                    │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Models (SQLAlchemy)                  │ │
│  │                                              │ │
│  │ - Chat (聊天记录)                             │ │
│  │ - Design (设计方案)                           │ │
│  │ - Envelope (包络图)                           │ │
│  │ - History (历史记录)                            │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Config (配置管理)                    │ │
│  │                                              │ │
│  │ - AI Providers配置                             │ │
│  │ - SKILL配置                                   │ │
│  │ - 应用配置                                     │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 数据流

### 1. 用户聊天流程

```
用户输入消息
    ↓
前端: ChatInterface组件
    ↓
前端: useSkillCalls Hook
    ↓
前端: 调用 /api/skill/call
    ↓
后端: skill_service.py
    ↓
后端: AI Provider Manager
    ↓
后端: LangChain → AI Provider API
    ↓
AI Provider: 返回结果
    ↓
后端: WebSocket推送进度
    ↓
前端: 实时显示进度
    ↓
后端: 返回最终结果
    ↓
前端: ResultTable显示结果
```

### 2. 3D模型生成流程

```
SKILL计算完成
    ↓
前端: 调用 /api/visualization/3d
    ↓
后端: model_service.py
    ↓
后端: 基于SKILL几何参数生成3D模型
    ↓
后端: 生成OBJ/GLTF/STL文件
    ↓
前端: Model3DViewer组件
    ↓
前端: React Three Fiber渲染3D模型
```

### 3. 包络图生成流程

```
SKILL计算完成
    ↓
前端: 调用 /api/envelope/generate
    ↓
后端: envelope.py
    ↓
后端: 生成Plotly.js图表代码
    ↓
前端: EnvelopeChart组件
    ↓
前端: 渲染交互式包络图
```

## 核心模块说明

### 1. AI提供商管理 (frontend/src/hooks/useAIProvider.ts)

**功能**：
- 支持的AI模型：
  - 国外：OpenAI GPT-4、Anthropic Claude、Google Gemini
  - 国内：通义千问、智谱AI、月之暗面、DeepSeek
  - 本地：Ollama、LocalAI、vLLM
- API Key管理
- 模型能力检测（视觉、代码、数学）
- 配置持久化（localStorage）

**接口**：
```typescript
interface AIModel {
  id: string
  name: string
  provider: AIProvider
  maxTokens: number
  supportsVision: boolean
  supportsCode: boolean
  supportsMath: boolean
}
```

### 2. SKILL调用服务 (backend/services/skill_service.py)

**功能**：
- 统一SKILL模块调用接口
- 异步任务管理
- 实时进度推送
- 结果缓存
- 错误处理和重试

**支持的SKILL模块**：
- `aircraft_design.airfoil_library` - 翼型库
- `aircraft_design.geometry_modeling` - 几何建模
- `aircraft_design.degenerate_geometry` - 退化几何
- `aircraft_design.parasite_drag_enhanced` - 寄生阻力
- `aircraft_design.surface_analysis` - 表面分析
- `aircraft_design.vspaero_interface` - VSPAERO接口
- `aircraft_design.loads_analysis` - 载荷分析
- `aircraft_design.rotorcraft_analysis` - 旋翼机分析

### 3. 3D可视化 (frontend/src/components/Model3DViewer.tsx)

**技术栈**：
- React Three Fiber (基于Three.js)
- @react-three/drei (3D组件库)
- 实时模型更新

**功能**：
- 3D模型渲染
- 交互式操作（旋转、缩放、平移）
- 多视图同步（Top、Side、Front、Iso）
- 爆炸视图
- 网格显示/隐藏
- 模型导出（OBJ、GLTF、STL）

### 4. 包络图 (frontend/src/components/EnvelopeChart.tsx)

**技术栈**：
- Plotly.js
- React-Plotly.js

**功能**：
- 交互式包络图
- 多参数包络（W/S vs T/W、高度vs速度）
- 实时数据更新
- 图表缩放和平移
- 数据导出（PNG、SVG、CSV）

### 5. WebSocket实时通信 (backend/websocket/)

**功能**：
- 双向通信
- 消息类型：
  - 聊天消息
  - 计算进度
  - 计算结果
  - 错误通知
- 连接管理
- 心跳检测
- 断线重连

## API端点

### AI提供商相关

```
GET  /api/ai/providers
    → 列出所有可用的AI提供商

POST /api/ai/configure
    → 配置AI提供商
    Body: {
        "provider": "openai",
        "apiKey": "sk-...",
        "baseUrl": "https://api.openai.com/v1",
        "model": "gpt-4",
        "temperature": 0.7,
        "maxTokens": 4096
    }

POST /api/ai/chat
    → 与AI聊天
    Body: {
        "role": "user",
        "content": "设计一架机翼..."
    }
```

### SKILL调用相关

```
POST /api/skill/call
    → 调用SKILL模块
    Body: {
        "skill": "geometry_modeling.create_wing",
        "method": "create_wing",
        "parameters": {
            "area": 30.0,
            "aspect_ratio": 8.0,
            ...
        },
        "withProgress": true
    }
    Response: {
        "success": true,
        "taskId": "uuid",
        "result": {...}
    }

GET /api/skill/progress/{task_id}
    → 获取任务进度
    Response: {
        "success": true,
        "progress": {
            "progress": 50,
            "status": "Processing",
            "currentStep": "Generating 3D model"
        }
    }

GET /api/skill/result/{task_id}
    → 获取任务结果
    Response: {
        "success": true,
        "result": {...}
    }

POST /api/skill/cancel/{task_id}
    → 取消任务
    Response: {
        "success": true,
        "result": "Task cancelled"
    }
```

### 可视化相关

```
POST /api/visualization/3d
    → 生成3D模型
    Body: {
        "parameters": {...},
        "format": "obj",
        "optimize": true
    }
    Response: {
        "success": true,
        "result": {
            "modelId": "uuid",
            "url": "/static/models/xxx.obj"
        }
    }

GET /api/visualization/3d/{model_id}
    → 获取3D模型
    Response: {
        "success": true,
        "model": {...}
    }

POST /api/envelope/generate
    → 生成包络图
    Body: {
        "xAxis": "w_s",
        "yAxis": "t_w",
        "xData": [100, 150, 200],
        "yData": [0.3, 0.5, 0.7],
        "xLabel": "Wing Loading (N/m²)",
        "yLabel": "Thrust-to-Weight Ratio",
        "title": "Constraint Envelope"
    }
    Response: {
        "success": true,
        "result": {
            "envelopeId": "uuid",
            "plotlyCode": "..."
        }
    }

GET /api/envelope/data/{envelope_id}
    → 获取包络图数据
    Response: {
        "success": true,
        "data": {...}
    }
```

## 配置文件

### 前端配置

```json
{
  "name": "aircraft-design-chatui",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.3.1",
    "@radix-ui/react-*": "^1.1.0",
    "plotly.js": "^2.29.1",
    "@react-three/fiber": "^8.17.10",
    "zustand": "^5.0.2",
    "socket.io-client": "^4.8.1"
  }
}
```

### 后端配置

```json
{
  "ai_providers": {
    "openai": {
      "enabled": true,
      "apiKey": "",
      "baseUrl": "https://api.openai.com/v1",
      "model": "gpt-4"
    },
    "anthropic": {
      "enabled": false,
      "apiKey": "",
      "model": "claude-3-sonnet-20240229"
    },
    ...
  },
  "skill": {
    "timeout": 300,
    "max_concurrent_tasks": 5
  },
  "websocket": {
    "heartbeat_interval": 30,
    "reconnection_attempts": 5
  }
}
```

## 部署架构

### 开发环境

```
前端 (Vite Dev Server)
    → http://localhost:3000
    → WebSocket: ws://localhost:3000

后端 (FastAPI + Uvicorn)
    → http://localhost:8000
    → WebSocket: ws://localhost:8000/ws/chat

任务队列 (Celery + Redis)
    → Redis: localhost:6379
    → Celery Worker: localhost:8001
```

### 生产环境

```
Nginx
    → 前端: / (React Build)
    → 后端API: /api/ (FastAPI)
    → WebSocket: /ws/ (WebSocket Proxy)
    → 静态文件: /static/ (3D模型、包络图)

Docker Compose
    ├── frontend (React Build)
    ├── backend (FastAPI)
    ├── redis (Redis)
    └── celery (Celery Worker)
```

## 性能优化策略

### 前端优化

1. **代码分割**
   - 使用React.lazy()延迟加载组件
   - 路由级别的代码分割

2. **3D渲染优化**
   - 使用InstancedMesh减少draw calls
   - 实现LOD（Level of Detail）系统
   - 视锥体剔除
   - 使用WebWorker进行计算

3. **状态管理优化**
   - 使用Zustand的selector避免不必要的重渲染
   - 实现结果缓存

4. **网络优化**
   - 使用WebSocket的binary模式
   - 实现请求去重
   - 使用HTTP/2

### 后端优化

1. **异步处理**
   - 使用asyncio进行异步I/O
   - 使用Celery进行后台任务处理

2. **缓存策略**
   - Redis缓存AI响应
   - 缓存SKILL计算结果
   - 实现结果预计算

3. **数据库优化**
   - 使用连接池
   - 实现查询优化
   - 添加索引

4. **任务队列优化**
   - 实现任务优先级
   - 使用任务分片
   - 实现任务超时处理

## 安全考虑

### 前端安全

1. **API Key保护**
   - 使用localStorage加密存储
   - 不在URL中暴露API Key
   - 实现API Key轮换

2. **输入验证**
   - 所有用户输入进行验证
   - 防止XSS攻击
   - 实现CSRF保护

3. **WebSocket安全**
   - 实现消息认证
   - 使用WSS协议（生产环境）
   - 实现消息加密

### 后端安全

1. **API安全**
   - 实现速率限制
   - 使用JWT认证
   - 实现CORS白名单

2. **AI API安全**
   - API Key加密存储
   - 实现使用量监控
   - 实现成本控制

3. **任务安全**
   - 实现任务权限控制
   - 防止任务注入
   - 实现任务超时

## 扩展性设计

### 前端扩展

1. **插件系统**
   - 支持自定义UI组件
   - 支持自定义AI提供商
   - 支持自定义SKILL模块

2. **主题系统**
   - 支持自定义主题
   - 支持CSS变量覆盖
   - 支持RTL布局

### 后端扩展

1. **微服务架构**
   - AI服务独立部署
   - 计算服务独立部署
   - 可视化服务独立部署

2. **多租户支持**
   - 实现租户隔离
   - 实现资源配额
   - 实现计费系统

## 监控和日志

### 前端监控

1. **性能监控**
   - 使用Web Vitals
   - 实现错误追踪（Sentry）
   - 实现用户行为分析

2. **日志记录**
   - 实现前端日志
   - 实现错误日志
   - 实现调试模式

### 后端监控

1. **应用监控**
   - 使用Prometheus + Grafana
   - 实现健康检查端点
   - 实现性能指标收集

2. **日志记录**
   - 使用结构化日志
   - 实现日志轮转
   - 实现日志级别控制

## 未来规划

### 短期（3个月）

1. 完成所有UI组件开发
2. 实现所有后端API
3. 完成AI提供商集成
4. 实现WebSocket实时通信
5. 完成单元测试和集成测试

### 中期（6个月）

1. 优化3D渲染性能
2. 实现高级包络图分析
3. 添加更多SKILL模块支持
4. 实现用户认证和授权
5. 实现设计方案版本管理

### 长期（12个月）

1. 实现协作功能
2. 实现设计方案分享
3. 实现AI训练和微调
4. 实现多用户协作
5. 实现云端部署和自动扩展

## 总结

ChatUI飞机设计系统采用现代化的技术栈，提供了：

1. **现代化UI**：基于React + TypeScript + shadcn/ui
2. **多AI支持**：支持国内外10+ AI模型
3. **实时通信**：基于WebSocket的双向通信
4. **3D可视化**：基于React Three Fiber的高性能渲染
5. **包络图分析**：基于Plotly.js的交互式图表
6. **SKILL集成**：完整的飞机设计技能调用
7. **可扩展架构**：模块化设计，易于扩展

系统设计遵循最佳实践，具有良好的可维护性、可扩展性和性能。
