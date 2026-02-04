# AI提供商指南

本指南详细说明了ChatUI飞机设计系统支持的所有AI提供商、配置方法和最佳实践。

## 目录

1. [支持的AI提供商](#支持的ai提供商)
2. [国外AI提供商](#国外ai提供商)
3. [国内AI提供商](#国内ai提供商)
4. [本地AI模型](#本地ai模型)
5. [配置方法](#配置方法)
6. [成本优化](#成本优化)
7. [故障排除](#故障排除)

---

## 支持的AI提供商

### 国外模型

| 提供商 | 模型 | 最大令牌 | 视觉 | 代码 | 数学 |
|--------|------|----------|------|------|------|
| OpenAI | GPT-4, GPT-4 Turbo | 8192 | ✅ | ✅ | ✅ |
| Anthropic | Claude 3 Opus, Sonnet | 200000 | ✅ | ✅ | ✅ |
| Google | Gemini Pro | 32768 | ✅ | ✅ | ✅ |

### 国内模型

| 提供商 | 模型 | 最大令牌 | 视觉 | 代码 | 数学 |
|--------|------|----------|------|------|------|
| 通义千问 | 通义千问 | 8192 | ✅ | ✅ | ✅ |
| 智谱AI | GLM-4 | 8192 | ❌ | ✅ | ✅ |
| 月之暗面 | V1 | 8192 | ✅ | ✅ | ✅ |
| DeepSeek | Chat | 32768 | ❌ | ✅ | ✅ |

### 本地模型

| 提供商 | 模型 | 最大令牌 | 视觉 | 代码 | 数学 |
|--------|------|----------|------|------|------|
| Ollama | Llama3 | 4096 | ❌ | ✅ | ❌ |
| LocalAI | 自定义 | 4096 | ❌ | ✅ | ❌ |
| vLLM | 自定义 | 4096 | ❌ | ✅ | ❌ |

---

## 国外AI提供商

### OpenAI

**API Key获取**：
1. 访问 https://platform.openai.com/api-keys
2. 登录或注册OpenAI账户
3. 点击"Create new secret key"
4. 复制生成的API Key

**配置参数**：
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

**支持模型**：
- `gpt-4`：最强大的模型，支持8192令牌
- `gpt-4-turbo`：更快速的模型，支持4096令牌

**最佳实践**：
- 使用`gpt-4-turbo`进行快速迭代
- 使用`gpt-4`进行复杂计算和代码生成
- 设置合理的`temperature`值（0.5-1.0）
- 使用`maxTokens`控制成本

**成本估算**：
- GPT-4：约$0.03/1K令牌
- GPT-4 Turbo：约$0.01/1K令牌

---

### Anthropic Claude

**API Key获取**：
1. 访问 https://console.anthropic.com/
2. 登录或注册Anthropic账户
3. 点击"Create Key"
4. 复制生成的API Key

**配置参数**：
```json
{
  "provider": "anthropic",
  "apiKey": "sk-ant-...",
  "baseUrl": "https://api.anthropic.com",
  "model": "claude-3-sonnet-20240229",
  "temperature": 0.7,
  "maxTokens": 4096,
  "topP": 1.0
}
```

**支持模型**：
- `claude-3-opus-20240229`：最强大的模型，支持200000令牌
- `claude-3-sonnet-20240229`：平衡的模型，支持200000令牌

**最佳实践**：
- Claude在长文本处理方面表现优秀
- 适合代码生成和复杂推理
- 使用较低的`temperature`（0.3-0.7）

**成本估算**：
- Claude 3 Opus：约$0.015/1K令牌
- Claude 3 Sonnet：约$0.003/1K令牌

---

### Google Gemini

**API Key获取**：
1. 访问 https://makersuite.google.com/app/apikey
2. 登录Google账户
3. 创建新的API Key
4. 复制生成的API Key

**配置参数**：
```json
{
  "provider": "google",
  "apiKey": "AIza...",
  "baseUrl": "https://generativelanguage.googleapis.com",
  "model": "gemini-pro",
  "temperature": 0.7,
  "maxTokens": 32768,
  "topP": 1.0
}
```

**支持模型**：
- `gemini-pro`：强大的多模态模型，支持32768令牌

**最佳实践**：
- Gemini在多模态任务方面表现优秀
- 适合图像理解和代码生成
- 支持长上下文

**成本估算**：
- Gemini Pro：免费（有限制）

---

## 国内AI提供商

### 通义千问

**API Key获取**：
1. 访问 https://dashscope.aliyuncs.com/
2. 登录阿里云账户
3. 创建API Key
4. 复制生成的API Key

**配置参数**：
```json
{
  "provider": "tongyi",
  "apiKey": "sk-...",
  "baseUrl": "https://dashscope.aliyuncs.com/api/v1",
  "model": "tongyi-qianwen",
  "temperature": 0.7,
  "maxTokens": 8192,
  "topP": 1.0
}
```

**支持模型**：
- `tongyi-qianwen`：通义千问模型
- `qwen-turbo`：更快速的模型
- `qwen-max`：更强大的模型

**最佳实践**：
- 通义千问在中文理解方面表现优秀
- 适合中文代码生成和文档处理
- 支持长上下文

**成本估算**：
- 通义千问：约¥0.008/1K令牌

---

### 智谱AI

**API Key获取**：
1. 访问 https://open.bigmodel.cn/
2. 登录智谱AI账户
3. 创建API Key
4. 复制生成的API Key

**配置参数**：
```json
{
  "provider": "zhipu",
  "apiKey": "sk-...",
  "baseUrl": "https://open.bigmodel.cn/api/paas/v4",
  "model": "glm-4",
  "temperature": 0.7,
  "maxTokens": 8192,
  "topP": 1.0
}
```

**支持模型**：
- `glm-4`：智谱GLM-4模型
- `glm-3-turbo`：更快速的模型
- `glm-4v`：多模态模型

**最佳实践**：
- 智谱AI在中文代码生成方面表现优秀
- 适合技术文档和代码生成
- 支持长上下文

**成本估算**：
- GLM-4：约¥0.1/1K令牌

---

### 月之暗面

**API Key获取**：
1. 访问 https://platform.moonshot.cn/
2. 登录月之暗面账户
3. 创建API Key
4. 复制生成的API Key

**配置参数**：
```json
{
  "provider": "moonshot",
  "apiKey": "sk-...",
  "baseUrl": "https://api.moonshot.cn/v1",
  "model": "moonshot-v1-8k",
  "temperature": 0.7,
  "maxTokens": 8192,
  "topP": 1.0
}
```

**支持模型**：
- `moonshot-v1-8k`：月之暗面V1模型，支持8192令牌
- `moonshot-v1-32k`：月之暗面V1模型，支持32768令牌
- `moonshot-v1-128k`：月之暗面V1模型，支持128000令牌

**最佳实践**：
- 月之暗面在长文本处理方面表现优秀
- 适合文档生成和长对话
- 支持超长上下文

**成本估算**：
- Moonshot V1：约¥0.012/1K令牌

---

### DeepSeek

**API Key获取**：
1. 访问 https://platform.deepseek.com/
2. 登录DeepSeek账户
3. 创建API Key
4. 复制生成的API Key

**配置参数**：
```json
{
  "provider": "deepseek",
  "apiKey": "sk-...",
  "baseUrl": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "temperature": 0.7,
  "maxTokens": 32768,
  "topP": 1.0
}
```

**支持模型**：
- `deepseek-chat`：DeepSeek Chat模型，支持32768令牌
- `deepseek-coder`：DeepSeek Coder模型，适合代码生成

**最佳实践**：
- DeepSeek在代码生成方面表现优秀
- 适合技术文档和代码生成
- 支持长上下文

**成本估算**：
- DeepSeek Chat：约¥0.001/1K令牌

---

## 本地AI模型

### Ollama

**安装Ollama**：
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
winget install ollama
```

**配置参数**：
```json
{
  "provider": "ollama",
  "apiKey": "ollama",
  "baseUrl": "http://localhost:11434/v1",
  "model": "llama3",
  "temperature": 0.7,
  "maxTokens": 4096,
  "topP": 1.0
}
```

**支持模型**：
- `llama3`：Llama 3模型
- `llama2`：Llama 2模型
- `mistral`：Mistral模型
- `codellama`：代码专用模型

**最佳实践**：
- 确保Ollama服务正在运行
- 使用适当的模型大小
- 监控内存使用情况

**成本**：
- 免费（本地运行）

---

### LocalAI

**安装LocalAI**：
```bash
# Docker
docker run -p 8080:8080 localai/localai:latest

# 或使用本地二进制文件
# 下载：https://github.com/mudler/LocalAI/releases
```

**配置参数**：
```json
{
  "provider": "localai",
  "apiKey": "localai",
  "baseUrl": "http://localhost:8080/v1",
  "model": "localai-model",
  "temperature": 0.7,
  "maxTokens": 4096,
  "topP": 1.0
}
```

**支持模型**：
- 支持多种开源模型
- 可以自定义模型

**最佳实践**：
- 确保LocalAI服务正在运行
- 使用适当的模型大小
- 监控内存使用情况

**成本**：
- 免费（本地运行）

---

### vLLM

**安装vLLM**：
```bash
# 使用pip安装
pip install vllm

# 或使用Docker
docker run --gpus all -p 5000:5000 vllm/vllm-openai:latest
```

**配置参数**：
```json
{
  "provider": "vllm",
  "apiKey": "vllm",
  "baseUrl": "http://localhost:5000/v1",
  "model": "vllm-model",
  "temperature": 0.7,
  "maxTokens": 4096,
  "topP": 1.0
}
```

**支持模型**：
- 支持多种开源模型
- 支持GPU加速

**最佳实践**：
- 确保vLLM服务正在运行
- 使用适当的模型大小
- 监控GPU使用情况

**成本**：
- 免费（本地运行）

---

## 配置方法

### 通过Web界面配置

1. 打开ChatUI飞机设计系统
2. 点击右上角的AI模型选择器
3. 选择AI提供商
4. 输入API Key
5. （可选）自定义Base URL和模型名称
6. 点击"保存配置"

### 通过API配置

```bash
curl -X POST http://localhost:8000/api/ai/configure \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "apiKey": "sk-...",
    "model": "gpt-4"
  }'
```

### 通过环境变量配置

```bash
# 创建.env文件
cat > .env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
TONGYI_API_KEY=sk-...
ZHIPU_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
MOONSHOT_API_KEY=sk-...
EOF

# 启动应用时加载环境变量
export $(cat .env | xargs)
```

---

## 成本优化

### 令牌优化

1. **使用合适的模型**
   - 简单任务：使用较小的模型
   - 复杂任务：使用较大的模型

2. **控制令牌数量**
   - 设置合理的`maxTokens`
   - 避免不必要的重复

3. **使用流式输出**
   - 减少等待时间
   - 实时显示结果

4. **缓存结果**
   - 避免重复计算
   - 使用本地存储

### 提供商选择

1. **国外模型**
   - OpenAI：适合通用任务
   - Anthropic：适合长文本和代码
   - Google：适合多模态任务

2. **国内模型**
   - 通义千问：适合中文任务
   - 智谱AI：适合代码生成
   - 月之暗面：适合长文本
   - DeepSeek：性价比高

3. **本地模型**
   - Ollama：适合轻量级任务
   - LocalAI：适合自定义模型
   - vLLM：适合高性能任务

---

## 故障排除

### 常见问题

#### 1. API Key无效

**症状**：配置后无法调用AI

**解决方案**：
- 检查API Key是否正确
- 确认API Key未过期
- 检查API Key权限

#### 2. 连接超时

**症状**：API调用超时

**解决方案**：
- 检查网络连接
- 增加超时时间
- 使用更快的模型

#### 3. 令牌不足

**症状**：API返回令牌不足错误

**解决方案**：
- 减少`maxTokens`
- 清理历史记录
- 使用更小的模型

#### 4. 模型不支持

**症状**：API返回模型不支持错误

**解决方案**：
- 检查模型名称
- 使用支持的模型
- 更新系统配置

#### 5. 本地模型无法连接

**症状**：无法连接到本地模型

**解决方案**：
- 检查本地服务是否运行
- 检查端口是否正确
- 检查防火墙设置

### 调试技巧

1. **启用日志**
   - 查看浏览器控制台
   - 检查网络请求
   - 查看错误消息

2. **测试连接**
   - 使用测试端点验证配置
   - 检查API响应

3. **监控使用情况**
   - 查看令牌使用情况
   - 查看API调用次数
   - 查看错误率

---

## 最佳实践

### 安全性

1. **保护API Key**
   - 不要在代码中硬编码API Key
   - 使用环境变量或配置文件
   - 定期轮换API Key
   - 使用最小权限原则

2. **数据隐私**
   - 不要发送敏感数据到AI
   - 清理历史记录
   - 使用加密存储

### 性能优化

1. **使用缓存**
   - 缓存常用结果
   - 使用本地存储
   - 避免重复计算

2. **异步处理**
   - 使用WebSocket实时通信
   - 使用后台任务处理
   - 显示进度条

3. **错误处理**
   - 实现重试机制
   - 提供友好的错误消息
   - 记录错误日志

---

## 更新日志

- **v1.0.0** (2024-01-15)
  - 初始版本
  - 支持10+ AI模型
  - 完整的API文档
  - WebSocket实时通信
