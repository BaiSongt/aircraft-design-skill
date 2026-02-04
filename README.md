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

| 提供商 | 模型 | 最大令牌 | 视觉 | 代码 | 数学 |
|--------|------|----------|------|------|-----|
| OpenAI | GPT-4, GPT-4 Turbo | 8192 | ✅ | ✅ | ✅ |
| Anthropic | Claude 3 Opus, Sonnet | 200000 | ✅ | ✅ | ✅ |
| Google | Gemini Pro | 32768 | ✅ | ✅ | ✅ |

#### 国内模型

| 提供商 | 模型 | 最大令牌 | 视觉 | 代码 | 数学 |
|--------|------|----------|------|------|-----|
| 通义千问 | 通义千问 | 8192 | ✅ | ✅ | ✅ |
| 智谱AI | GLM-4 | 8192 | ❌ | ✅ | ✅ |
| 月之暗面 | V1 | 8192 | ✅ | ✅ | ✅ |
| DeepSeek | Chat | 32768 | ❌ | ✅ | ✅ |

#### 本地模型

| 提供商 | 模型 | 最大令牌 | 视觉 | 代码 | 数学 |
|--------|------|----------|------|------|-----|
| Ollama | Llama3 | 4096 | ❌ | ✅ | ❌ |
| LocalAI | 自定义 | 4096 | ❌ | ✅ | ❌ |
| vLLM | 自定义 | 4096 | ❌ | ✅ | ❌ |

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
│   │   ├── main.tsx           # React入口
│   │   └── index.css          # 全局样式
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── postcss.config.js
├── backend/                     # FastAPI后端
│   ├── app.py                  # FastAPI应用入口
│   ├── api/                    # API路由
│   ├── services/                # 业务服务
│   ├── websocket/               # WebSocket管理
│   ├── config/                  # 配置文件
│   └── requirements.txt         # Python依赖
├── tests/                       # 集成测试
├── docs/                       # 文档
├── aircraft_design/             # SKILL模块
├── config/                     # 配置文件
└── README.md                   # 本文件
```

## 快速开始

### 前置要求

- Node.js 18+
- Python 3.12+
- Redis (用于任务队列)
- Git
- Docker (可选，用于生产部署)

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

### 开发环境启动

#### 前端开发服务器
```bash
cd frontend
npm run dev
```
访问：http://localhost:3000

#### 后端开发服务器
```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```
访问：http://localhost:8000

#### 启动Celery Worker
```bash
cd backend
celery -A app worker --loglevel=info
```

### 访问应用
- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

## Docker部署

### Docker Compose配置

项目包含完整的Docker Compose配置，可以一键启动所有服务。

#### 使用Docker Compose启动

```bash
# 克隆仓库
git clone https://github.com/yourusername/aircraft-design-skill.git
cd aircraft-design-skill

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart backend
```

#### Docker Compose服务说明

| 服务 | 说明 | 端口 |
|------|------|------|
| frontend | 前端应用 | 3000:80 |
| backend | 后端API服务器 | 8000:8000 |
| redis | Redis数据库 | 6379:6379 |
| celery | Celery任务队列 | 8001 |
| nginx | Nginx反向代理 | 80:80 |

### Dockerfile说明

#### 前端Dockerfile

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine AS runner

WORKDIR /app

COPY --from=builder /app/dist ./dist

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 后端Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Celery Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "app", "worker", "--loglevel=info"]
```

### Nginx配置

#### Nginx配置文件

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10M;

    # 前端静态文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket代理
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态文件
    location /static/ {
        proxy_pass http://backend;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml+rss text/javascript image/svg+xml;
}
```

#### SSL/TLS配置

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # 其他配置与HTTP相同
    # ...
}
```

### 环境变量配置

#### 创建.env文件

```bash
# 创建环境变量文件
cat > .env << EOF
# AI提供商API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
TONGYI_API_KEY=sk-...
ZHIPU_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
MOONSHOT_API_KEY=sk-...

# Redis配置
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=

# Celery配置
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND_URL=redis://redis:6379/0
CELERY_TASK_TRACKS_DB=redis://redis:6379/0

# 应用配置
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# CORS配置
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
CORS_ALLOW_CREDENTIALS=True

# 文件存储
STATIC_FILES_DIR=/app/static
MODELS_DIR=/app/static/models
ENVELOPES_DIR=/app/static/envelopes
LOGS_DIR=/app/logs
EOF
```

#### 在Docker Compose中使用环境变量

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - TONGYI_API_KEY=${TONGYI_API_KEY}
      - ZHIPU_API_KEY=${ZHIPU_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - MOONSHOT_API_KEY=${MOONSHOT_API_KEY}
    volumes:
      - ./backend/static:/app/static
      - ./backend/logs:/app/logs
    depends_on:
      - redis
      - celery
    restart: unless-stopped

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.celery
    environment:
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND_URL=redis://redis:6379/0
      - CELERY_TASK_TRACKS_DB=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

### 生产环境部署

#### 1. 构建前端

```bash
cd frontend
npm run build
```

#### 2. 部署前端到服务器

```bash
# 使用rsync部署
rsync -avz --delete ./dist/ user@your-server:/var/www/html/

# 或使用scp部署
scp -r ./dist/* user@your-server:/var/www/html/

# 或使用git部署
cd frontend
git push origin main
# 在服务器上拉取最新代码
cd /var/www/html
git pull origin main
```

#### 3. 配置Nginx

```bash
# 复制Nginx配置
sudo cp nginx/nginx.conf /etc/nginx/sites-available/aircraft-design

# 启用站点
sudo ln -s /etc/nginx/sites-available/aircraft-design /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

#### 4. 启动后端服务

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用Gunicorn启动
gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/aircraft-design/access.log \
  --error-logfile /var/log/aircraft-design/error.log \
  --log-level info

# 启动Celery Worker
celery -A app worker --loglevel=info --concurrency=4
```

#### 5. 配置Systemd服务

```bash
# 创建systemd服务文件
sudo cat > /etc/systemd/system/aircraft-design-backend.service << EOF
[Unit]
Description=Aircraft Design Backend
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/aircraft-design/backend
ExecStart=/var/www/aircraft-design/venv/bin/gunicorn app:app --workers 4 --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl enable aircraft-design-backend
sudo systemctl start aircraft-design-backend
```

### SSL/TLS配置

#### 1. 使用Let's Encrypt获取免费SSL证书

```bash
# 安装certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 证书位置
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

#### 2. 自动续期

```bash
# 添加cron任务
sudo crontab -e "0 2 * * * /path/to/certbot renew --dry-run"
```

### 监控和日志

#### 1. 应用监控

```bash
# 查看应用日志
docker-compose logs -f backend

# 查看Celery日志
docker-compose logs -f celery

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

#### 2. 性能监控

```bash
# 使用htop监控资源
htop

# 使用docker stats监控容器
docker stats

# 查看Redis状态
redis-cli info
```

#### 3. 日志管理

```bash
# 日志轮转配置
# 在backend/config/app_config.py中配置日志轮转

# 查看日志文件
ls -lh /app/logs/

# 清理旧日志
find /app/logs -name "*.log" -mtime +30 -delete
```

### 备份和恢复

#### 1. 数据库备份

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/$DATE"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份Redis
redis-cli --rdb /backup/redis_$DATE.rdb

# 备份应用数据
tar -czf $BACKUP_DIR/app_data.tar.gz /app/static

# 保留最近7天的备份
find /backup -type f -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x backup.sh

# 设置定时任务
crontab -e "0 2 * * * /path/to/backup.sh"
```

#### 2. 恢复流程

```bash
# 恢复Redis
redis-cli --rdb /backup/redis_20240115_120000.rdb

# 恢复应用数据
tar -xzf /backup/app_data_20240115_120000.tar.gz -C /app/static

# 重启服务
docker-compose restart
```

### 故障排除

#### 常见问题

##### 1. Docker容器无法启动

**症状**：`docker-compose up`失败

**解决方案**：
```bash
# 检查端口占用
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
netstat -tulpn | grep :6379

# 停止占用端口的进程
sudo kill -9 <PID>

# 清理Docker缓存
docker system prune -a
```

##### 2. 前端无法访问

**症状**：无法访问http://localhost:3000

**解决方案**：
```bash
# 检查前端容器状态
docker-compose ps frontend

# 查看前端日志
docker-compose logs -f frontend

# 重启前端容器
docker-compose restart frontend
```

##### 3. 后端API无法访问

**症状**：无法访问http://localhost:8000

**解决方案**：
```bash
# 检查后端容器状态
docker-compose ps backend

# 查看后端日志
docker-compose logs -f backend

# 检查Redis连接
docker-compose exec backend python -c "import redis; print(redis.ping())"

# 重启后端容器
docker-compose restart backend
```

##### 4. Redis连接失败

**症状**：后端无法连接Redis

**解决方案**：
```bash
# 检查Redis容器状态
docker-compose ps redis

# 重启Redis容器
docker-compose restart redis

# 检查Redis日志
docker-compose logs -f redis

# 测试Redis连接
docker-compose exec redis redis-cli ping
```

##### 5. Celery Worker无法启动

**症状**：Celery任务无法执行

**解决方案**：
```bash
# 检查Celery容器状态
docker-compose ps celery

# 查看Celery日志
docker-compose logs -f celery

# 重启Celery容器
docker-compose restart celery

# 检查Celery任务
docker-compose exec celery celery -A app inspect active
```

##### 6. Nginx配置错误

**症状**：Nginx无法启动

**解决方案**：
```bash
# 测试Nginx配置
sudo nginx -t

# 查看Nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 重启Nginx
sudo systemctl restart nginx
```

### 性能优化

#### 1. 数据库优化

```python
# backend/models/database.py
from sqlalchemy import create_engine, Index
from sqlalchemy.orm import sessionmaker

# 创建索引
engine = create_engine('sqlite:///app.db')
Base.metadata.create_all(engine)

# 使用连接池
engine = create_engine(
    'sqlite:///app.db',
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600
)

SessionLocal = sessionmaker(bind=engine)
```

#### 2. 缓存策略

```python
# backend/utils/cache.py
from functools import lru_cache
import redis
import json

# 创建Redis客户端
redis_client = redis.Redis(host='redis', port=6379, db=0)

# 缓存装饰器
@lru_cache(maxsize=1000)
def get_cached_data(key):
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None

def set_cached_data(key, data, expire=3600):
    redis_client.setex(key, json.dumps(data), expire)
```

#### 3. 负载均衡

```nginx
# nginx/nginx.conf
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 安全加固

#### 1. API速率限制

```python
# backend/middleware/rate_limit.py
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

# 创建速率限制器
limiter = Limiter(key_func=lambda r: get_remote_address(r), rate="10/minute")

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    try:
        return await limiter(request)
    except Exception as e:
        raise HTTPException(status_code=429, detail="Too many requests")
```

#### 2. 请求验证

```python
# backend/middleware/validation.py
from fastapi import HTTPException
from pydantic import BaseModel, validator

class APIKeyModel(BaseModel):
    api_key: str

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v.startswith('sk-'):
            raise ValueError('Invalid API key format')
        return v
```

#### 3. CSRF保护

```python
# backend/middleware/csrf.py
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware

# 创建CSRF令牌
import secrets

def generate_csrf_token():
    return secrets.token_hex(16)

# 添加CSRF中间件
@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    if request.method in ["POST", "PUT", "DELETE"]:
        token = request.headers.get("X-CSRF-Token")
        if not validate_csrf_token(token):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")
    response = await call_next(request)
    response.headers["X-CSRF-Token"] = generate_csrf_token()
    return response
```

#### 4. 数据加密

```python
# backend/utils/encryption.py
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

# 创建加密器
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# 加密敏感数据
def encrypt_data(data: str) -> str:
    return cipher_suite.encrypt(data.encode()).decode()

# 解密敏感数据
def decrypt_data(encrypted_data: str) -> str:
    return cipher_suite.decrypt(encrypted_data.encode()).decode()
```

### 维护和更新

#### 1. 更新流程

```bash
# 创建更新脚本
cat > update.sh << 'EOF'
#!/bin/bash

# 1. 备份当前版本
./backup.sh

# 2. 拉取最新代码
git pull origin main

# 3. 更新依赖
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 4. 重新构建
cd frontend && npm run build

# 5. 重启服务
docker-compose down
docker-compose up -d

echo "Update completed"
EOF

chmod +x update.sh
```

#### 2. 回滚流程

```bash
# 创建回滚脚本
cat > rollback.sh << 'EOF'
#!/bin/bash

# 1. 停止服务
docker-compose down

# 2. 回滚到上一个版本
git checkout <previous-commit-hash>

# 3. 重新构建
cd frontend && npm run build

# 4. 重启服务
docker-compose up -d

echo "Rollback completed"
EOF

chmod +x rollback.sh
```

### 监控告警

#### 1. Prometheus监控

```python
# backend/metrics/prometheus.py
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client.core import CollectorRegistry

# 创建指标
registry = CollectorRegistry()

api_requests_total = Counter('api_requests_total', 'Total API requests', registry=registry)
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration', registry=registry)
active_connections = Gauge('active_connections', 'Active connections', registry=registry)
memory_usage = Gauge('memory_usage_bytes', 'Memory usage', registry=registry)
cpu_usage = Gauge('cpu_usage_percent', 'CPU usage', registry=registry)

# 记录指标
def record_api_request():
    api_requests_total.inc()

def record_request_duration(duration):
    api_request_duration.observe(duration)

def update_active_connections(count):
    active_connections.set(count)

def update_memory_usage(usage):
    memory_usage.set(usage)

def update_cpu_usage(usage):
    cpu_usage.set(usage)
```

#### 2. 告警配置

```python
# backend/alerts/email_alerts.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_alert(subject, body):
    msg = MIMEMultipart()
    msg['From'] = 'alerts@your-domain.com'
    msg['To'] = 'admin@your-domain.com'
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.your-domain.com', 587) as server:
        server.login('alerts@your-domain.com', 'password')
        server.send_message(msg)
        server.quit()

def check_alerts():
    # 检查API失败率
    if api_failure_rate > 0.1:
        send_email_alert("API failure rate too high", f"Current rate: {api_failure_rate}")

    # 检查响应时间
    if avg_response_time > 5.0:
        send_email_alert("Response time too slow", f"Average time: {avg_response_time}s")

    # 检查资源使用
    if cpu_usage > 80.0:
        send_email_alert("CPU usage too high", f"Current usage: {cpu_usage}%")

    if memory_usage > 80.0:
        send_email_alert("Memory usage too high", f"Current usage: {memory_usage}%")
```

## 使用指南

### 1. 配置AI提供商

1. 打开应用，进入"设置"页面
2. 选择AI提供商（OpenAI、Anthropic等）
3. 输入API Key
4. （可选）自定义Base URL和模型名称
5. 点击"保存配置"

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

### 5. 查看历史记录

1. 点击"历史"标签页
2. 查看所有设计历史
3. 搜索和筛选历史记录
4. 导出历史数据

## 开发指南

### 前端开发

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev

# 运行测试
npm run test

# 代码检查
npm run lint

# 构建生产版本
npm run build
```

### 后端开发

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 启动开发服务器
uvicorn app:app --reload

# 运行测试
pytest

# 启动Celery Worker
celery -A app worker
```

## 文档

- [架构文档](docs/chatui_architecture.md) - 完整的架构说明
- [API参考](docs/api_reference.md) - 所有API端点文档
- [AI提供商指南](docs/ai_providers_guide.md) - AI模型配置指南
- [部署指南](docs/deployment_guide.md) - Docker部署详细指南

## 贡献指南

### 开发流程

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 遵循Python PEP 8和TypeScript最佳实践
- 使用有意义的变量名和函数名
- 添加适当的注释和文档字符串
- 保持代码简洁和可读性

### 提交规范

- 提交信息应该清晰描述更改
- 使用`feat:`、`fix:`、`docs:`、`style:`、`refactor:`、`test:`等前缀
- 一个提交应该只做一件事

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
