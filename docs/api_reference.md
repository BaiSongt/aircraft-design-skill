# API参考文档

本文档提供了ChatUI飞机设计系统所有API端点的详细说明。

## 目录

1. [AI提供商API](#ai-providers-api)
2. [SKILL调用API](#skill-calls-api)
3. [可视化API](#visualization-api)
4. [包络图API](#envelope-api)
5. [WebSocket API](#websocket-api)

---

## AI提供商API

### 列出所有AI提供商

**端点**：`GET /api/ai/providers`

**描述**：列出所有可用的AI提供商

**请求**：无

**响应**：
```json
{
  "name": "openai",
  "enabled": true,
  "model": "gpt-4",
  "baseUrl": "https://api.openai.com/v1"
}
```

**字段说明**：
- `name`：提供商名称
- `enabled`：是否已启用
- `model`：默认模型名称
- `baseUrl`：API基础URL

---

### 配置AI提供商

**端点**：`POST /api/ai/configure`

**描述**：配置AI提供商

**请求**：
```json
{
  "provider": "openai",
  "apiKey": "sk-...",
  "baseUrl": "https://api.openai.com/v1",
  "model": "gpt-4",
  "temperature": 0.7,
  "maxTokens": 4096,
  "topP": 1.0
}
```

**字段说明**：
- `provider`：提供商名称（必填）
- `apiKey`：API密钥（必填）
- `baseUrl`：自定义基础URL（可选）
- `model`：模型名称（可选）
- `temperature`：温度参数（可选，默认0.7）
- `maxTokens`：最大令牌数（可选，默认4096）
- `topP`：Top-P采样参数（可选，默认1.0）

**响应**：
```json
{
  "success": true,
  "message": "Provider configured successfully",
  "result": {
    "provider": "openai",
    "model": "gpt-4",
    "enabled": true
  }
}
```

---

### 获取AI提供商能力

**端点**：`GET /api/ai/capabilities/{provider_name}`

**描述**：获取AI提供商的能力信息

**请求**：无

**响应**：
```json
{
  "supportsVision": true,
  "supportsCode": true,
  "supportsMath": true,
  "supportsStreaming": true
}
```

**字段说明**：
- `supportsVision`：是否支持视觉功能
- `supportsCode`：是否支持代码生成
- `supportsMath`：是否支持数学计算
- `supportsStreaming`：是否支持流式输出

---

### 与AI聊天

**端点**：`POST /api/ai/chat`

**描述**：与AI进行聊天

**请求**：
```json
{
  "role": "user",
  "content": "设计一架机翼，面积30m²，展弦比8.0",
  "metadata": {
    "provider": "openai"
  }
}
```

**字段说明**：
- `role`：角色（user/assistant/system）
- `content`：消息内容
- `metadata`：元数据（可选）

**响应**：
```json
{
  "success": true,
  "response": "AI生成的响应内容",
  "provider": "openai",
  "model": "gpt-4"
}
```

---

### 删除AI提供商配置

**端点**：`DELETE /api/ai/provider/{provider_name}`

**描述**：删除AI提供商配置

**请求**：无

**响应**：
```json
{
  "success": true,
  "message": "Provider openai deleted successfully"
}
```

---

### 测试AI提供商连接

**端点**：`GET /api/ai/test/{provider_name}`

**描述**：测试AI提供商连接

**请求**：无

**响应**：
```json
{
  "success": true,
  "message": "Provider openai connection successful",
  "response": "测试响应内容..."
}
```

---

## SKILL调用API

### 调用SKILL模块

**端点**：`POST /api/skill/call`

**描述**：调用SKILL模块

**请求**：
```json
{
  "skill": "geometry_modeling",
  "method": "create_wing",
  "parameters": {
    "area": 30.0,
    "aspect_ratio": 8.0,
    "taper_ratio": 0.6,
    "sweep_quarter_chord": 25.0
  },
  "provider": "openai",
  "withProgress": true
}
```

**字段说明**：
- `skill`：SKILL模块名称（必填）
- `method`：方法名称（必填）
- `parameters`：方法参数（必填）
- `provider`：AI提供商（可选，默认openai）
- `withProgress`：是否需要进度（可选，默认false）

**响应**：
```json
{
  "success": true,
  "taskId": "uuid",
  "result": {
    "wing": {
      "area": 30.0,
      "span": 15.49,
      ...
    }
  }
}
```

---

### 获取SKILL任务进度

**端点**：`GET /api/skill/progress/{task_id}`

**描述**：获取SKILL计算任务进度

**请求**：无

**响应**：
```json
{
  "success": true,
  "progress": {
    "progress": 50,
    "status": "Processing",
    "currentStep": "Generating 3D model"
  }
}
```

**字段说明**：
- `progress`：进度百分比（0-100）
- `status`：当前状态
- `currentStep`：当前步骤描述

---

### 获取SKILL任务结果

**端点**：`GET /api/skill/result/{task_id}`

**描述**：获取SKILL计算任务结果

**请求**：无

**响应**：
```json
{
  "success": true,
  "result": {
    "wing": {
      "area": 30.0,
      "span": 15.49,
      ...
    }
  },
  "error": null
}
```

---

### 取消SKILL任务

**端点**：`POST /api/skill/cancel/{task_id}`

**描述**：取消SKILL计算任务

**请求**：无

**响应**：
```json
{
  "success": true,
  "message": "Task uuid cancelled successfully"
}
```

---

### 获取所有活动任务

**端点**：`GET /api/skill/active`

**描述**：获取所有活动的SKILL任务

**请求**：无

**响应**：
```json
{
  "success": true,
  "tasks": {
    "task_id_1": {
      "skill": "geometry_modeling",
      "method": "create_wing",
      "status": "running",
      "progress": 50
    }
  },
  "count": 1
}
```

---

### 清除已完成任务

**端点**：`DELETE /api/skill/completed`

**描述**：清除所有已完成的SKILL任务

**请求**：无

**响应**：
```json
{
  "success": true,
  "message": "Completed tasks cleared"
}
```

---

### 列出所有SKILL模块

**端点**：`GET /api/skill/modules`

**描述**：列出所有可用的SKILL模块

**请求**：无

**响应**：
```json
{
  "success": true,
  "modules": {
    "airfoil_library": {
      "name": "翼型库",
      "description": "NACA 4/5/6系列翼型生成",
      "methods": [
        "generate_naca4_airfoil",
        "generate_naca5_airfoil",
        "generate_naca6_airfoil",
        "load_airfoil_file",
        "scale_airfoil",
        "generate_airfoil_library"
      ]
    },
    "geometry_modeling": {
      "name": "几何建模",
      "description": "机翼、机身、尾翼等几何参数创建",
      "methods": [
        "create_wing",
        "create_fuselage",
        "create_horizontal_tail",
        "create_vertical_tail",
        "create_engine",
        "create_landing_gear",
        "assemble_aircraft",
        "translate_geometry",
        "rotate_geometry",
        "scale_geometry",
        "mirror_geometry"
      ]
    }
  }
}
```

---

## 可视化API

### 生成3D模型

**端点**：`POST /api/visualization/3d`

**描述**：生成3D模型

**请求**：
```json
{
  "parameters": {
    "wing": {
      "area": 30.0,
      "aspect_ratio": 8.0
    }
  },
  "format": "obj",
  "optimize": true,
  "resolution": "medium"
}
```

**字段说明**：
- `parameters`：模型参数（必填）
- `format`：模型格式（可选，默认obj）
- `optimize`：是否优化（可选，默认true）
- `resolution`：分辨率（可选，默认medium）

**响应**：
```json
{
  "success": true,
  "modelId": "uuid",
  "url": "/static/models/uuid.obj",
  "format": "obj",
  "vertices": 1000,
  "triangles": 500
}
```

---

### 获取3D模型

**端点**：`GET /api/visualization/3d/{model_id}`

**描述**：获取3D模型

**请求**：无

**响应**：
```json
{
  "success": true,
  "model": {
    "model_id": "uuid",
    "parameters": {...},
    "format": "obj",
    "created_at": "2024-01-15T10:00:00Z",
    "status": "generated"
  }
}
```

---

### 删除3D模型

**端点**：`DELETE /api/visualization/3d/{model_id}`

**描述**：删除3D模型

**请求**：无

**响应**：
```json
{
  "success": true,
  "message": "Model uuid deleted successfully"
}
```

---

### 列出所有3D模型

**端点**：`GET /api/visualization/3d`

**描述**：列出所有3D模型

**请求**：无

**响应**：
```json
{
  "success": true,
  "models": {
    "model_id_1": {...},
    "model_id_2": {...}
  },
  "count": 2
}
```

---

### 导出3D模型

**端点**：`POST /api/visualization/3d/{model_id}/export`

**描述**：导出3D模型

**请求**：
```json
{
  "format": "gltf"
}
```

**响应**：
```json
{
  "success": true,
  "url": "/static/models/uuid.gltf",
  "format": "gltf"
}
```

---

### 列出支持的3D模型格式

**端点**：`GET /api/visualization/formats`

**描述**：列出支持的3D模型格式

**请求**：无

**响应**：
```json
{
  "success": true,
  "formats": [
    {
      "format": "obj",
      "name": "Wavefront OBJ",
      "description": "通用3D模型格式",
      "extensions": [".obj"]
    },
    {
      "format": "gltf",
      "name": "GL Transmission Format",
      "description": "现代3D模型格式，支持动画",
      "extensions": [".gltf", ".glb"]
    },
    {
      "format": "stl",
      "name": "Stereolithography",
      "description": "3D打印常用格式",
      "extensions": [".stl"]
    }
  ]
}
```

---

## 包络图API

### 生成包络图

**端点**：`POST /api/envelope/generate`

**描述**：生成包络图

**请求**：
```json
{
  "xAxis": "w_s",
  "yAxis": "t_w",
  "xData": [100, 150, 200, 250, 300],
  "yData": [0.25, 0.30, 0.35, 0.40, 0.45],
  "xLabel": "Wing Loading (N/m²)",
  "yLabel": "Thrust-to-Weight Ratio",
  "title": "Constraint Envelope",
  "showGrid": true,
  "showLegend": true
}
```

**字段说明**：
- `xAxis`：X轴参数名称（必填）
- `yAxis`：Y轴参数名称（必填）
- `xData`：X轴数据数组（必填）
- `yData`：Y轴数据数组（必填）
- `xLabel`：X轴标签（必填）
- `yLabel`：Y轴标签（必填）
- `title`：图表标题（必填）
- `showGrid`：是否显示网格（可选，默认true）
- `showLegend`：是否显示图例（可选，默认true）

**响应**：
```json
{
  "success": true,
  "envelopeId": "uuid",
  "plotlyCode": "<!-- Plotly.js HTML代码 -->",
  "plotlyData": {
    "xAxis": "w_s",
    "yAxis": "t_w",
    "xData": [...],
    "yData": [...],
    ...
  }
}
```

---

### 获取包络图数据

**端点**：`GET /api/envelope/data/{envelope_id}`

**描述**：获取包络图数据

**请求**：无

**响应**：
```json
{
  "success": true,
  "data": {
    "envelope_id": "uuid",
    "xAxis": "w_s",
    "yAxis": "t_w",
    "xData": [...],
    "yData": [...],
    ...
  }
}
```

---

### 删除包络图数据

**端点**：`DELETE /api/envelope/data/{envelope_id}`

**描述**：删除包络图数据

**请求**：无

**响应**：
```json
{
  "success": true,
  "message": "Envelope uuid deleted successfully"
}
```

---

### 列出所有包络图

**端点**：`GET /api/envelope`

**描述**：列出所有包络图

**请求**：无

**响应**：
```json
{
  "success": true,
  "envelopes": {
    "envelope_id_1": {...},
    "envelope_id_2": {...}
  },
  "count": 2
}
```

---

### 创建预设包络图

**端点**：`POST /api/envelope/preset`

**描述**：创建预设包络图

**请求**：无

**响应**：
```json
{
  "success": true,
  "envelopeId": "uuid",
  "message": "Preset envelope created successfully"
}
```

---

### 列出预设包络图

**端点**：`GET /api/envelope/presets`

**描述**：列出预设包络图

**请求**：无

**响应**：
```json
{
  "success": true,
  "presets": [
    {
      "envelope_id": "uuid",
      "xAxis": "w_s",
      "yAxis": "t_w",
      ...
    }
  ],
  "count": 1
}
```

---

### 导出包络图

**端点**：`POST /api/envelope/export/{envelope_id}`

**描述**：导出包络图

**请求**：
```json
{
  "format": "png"
}
```

**响应**：
```json
{
  "success": true,
  "url": "/static/envelopes/uuid.png",
  "format": "png"
}
```

---

### 列出支持的导出格式

**端点**：`GET /api/envelope/formats`

**描述**：列出支持的导出格式

**请求**：无

**响应**：
```json
{
  "success": true,
  "formats": [
    {
      "format": "png",
      "name": "PNG Image",
      "description": "高质量图像格式",
      "extension": ".png"
    },
    {
      "format": "svg",
      "name": "SVG Vector",
      "description": "可缩放矢量格式",
      "extension": ".svg"
    },
    {
      "format": "html",
      "name": "HTML Interactive",
      "description": "交互式HTML格式",
      "extension": ".html"
    },
    {
      "format": "json",
      "name": "JSON Data",
      "description": "原始数据格式",
      "extension": ".json"
    }
  ]
}
```

---

## WebSocket API

### WebSocket连接

**端点**：`WS /ws/chat`

**描述**：建立WebSocket连接进行实时通信

**连接**：
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat')
```

**消息类型**：

#### 1. 聊天消息
```json
{
  "type": "message",
  "role": "user",
  "content": "设计一架机翼",
  "metadata": {
    "provider": "openai"
  }
}
```

#### 2. SKILL调用
```json
{
  "type": "skill_call",
  "skill": "geometry_modeling",
  "method": "create_wing",
  "parameters": {
    "area": 30.0,
    "aspect_ratio": 8.0
  },
  "provider": "openai"
}
```

#### 3. 进度请求
```json
{
  "type": "progress_request",
  "taskId": "uuid"
}
```

#### 4. 取消任务
```json
{
  "type": "cancel_task",
  "taskId": "uuid"
}
```

**服务器消息**：

#### 1. 聊天响应
```json
{
  "type": "message",
  "role": "assistant",
  "content": "AI生成的响应内容",
  "provider": "openai"
}
```

#### 2. 任务开始
```json
{
  "type": "task_started",
  "taskId": "uuid",
  "skill": "geometry_modeling",
  "method": "create_wing"
}
```

#### 3. 进度更新
```json
{
  "type": "progress",
  "taskId": "uuid",
  "progress": 50,
  "status": "Processing",
  "currentStep": "Generating 3D model"
}
```

#### 4. 任务完成
```json
{
  "type": "task_completed",
  "taskId": "uuid",
  "result": {
    "wing": {...}
  }
}
```

#### 5. 任务取消
```json
{
  "type": "task_cancelled",
  "taskId": "uuid",
  "message": "Task uuid cancelled successfully"
}
```

#### 6. 错误消息
```json
{
  "type": "error",
  "message": "Error processing request: ...",
  "taskId": "uuid"
}
```

---

## 错误码

所有API端点可能返回以下错误码：

| 错误码 | HTTP状态码 | 描述 |
|---------|------------|------|
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未授权 |
| 403 | Forbidden | 禁止访问 |
| 404 | Not Found | 资源未找到 |
| 500 | Internal Server Error | 服务器内部错误 |

**错误响应格式**：
```json
{
  "success": false,
  "error": "错误描述"
}
```

---

## 使用示例

### Python示例

```python
import requests

# 配置AI提供商
response = requests.post('http://localhost:8000/api/ai/configure', json={
    'provider': 'openai',
    'apiKey': 'sk-...',
    'model': 'gpt-4'
})
print(response.json())

# 调用SKILL模块
response = requests.post('http://localhost:8000/api/skill/call', json={
    'skill': 'geometry_modeling',
    'method': 'create_wing',
    'parameters': {
        'area': 30.0,
        'aspect_ratio': 8.0,
        'taper_ratio': 0.6,
        'sweep_quarter_chord': 25.0
    },
    'withProgress': True
})
print(response.json())

# 获取任务进度
task_id = response.json()['taskId']
response = requests.get(f'http://localhost:8000/api/skill/progress/{task_id}')
print(response.json())
```

### JavaScript示例

```javascript
// 配置AI提供商
const response = await fetch('http://localhost:8000/api/ai/configure', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        provider: 'openai',
        apiKey: 'sk-...',
        model: 'gpt-4'
    })
})
const data = await response.json()
console.log(data)

// 调用SKILL模块
const response = await fetch('http://localhost:8000/api/skill/call', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        skill: 'geometry_modeling',
        method': 'create_wing',
        parameters: {
            area: 30.0,
            aspect_ratio: 8.0
        }
    })
})
const data = await response.json()
console.log(data)
```

### cURL示例

```bash
# 配置AI提供商
curl -X POST http://localhost:8000/api/ai/configure \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "apiKey": "sk-...",
    "model": "gpt-4"
  }'

# 调用SKILL模块
curl -X POST http://localhost:8000/api/skill/call \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "geometry_modeling",
    "method": "create_wing",
    "parameters": {
      "area": 30.0,
      "aspect_ratio": 8.0
    }
  }'

# 获取任务进度
curl http://localhost:8000/api/skill/progress/uuid
```

---

## 最佳实践

1. **错误处理**
   - 始终检查响应中的`success`字段
   - 处理所有可能的错误码
   - 实现重试机制

2. **性能优化**
   - 使用连接池
   - 实现请求缓存
   - 使用分页处理大量数据

3. **安全性**
   - 使用HTTPS（生产环境）
   - 实现API Key轮换
   - 不要在客户端暴露API Key

4. **WebSocket连接**
   - 实现断线重连
   - 实现心跳检测
   - 处理连接错误

---

## 更新日志

- **v1.0.0** (2024-01-15)
  - 初始版本
  - 所有核心API端点
  - WebSocket实时通信
  - 完整的错误处理
