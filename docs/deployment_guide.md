# 部署指南

本指南详细说明了如何部署ChatUI飞机设计系统到生产环境。

## 目录

1. [系统要求](#系统要求)
2. [开发环境部署](#开发环境部署)
3. [生产环境部署](#生产环境部署)
4. [Docker部署](#docker部署)
5. [Nginx配置](#nginx配置)
6. [环境变量配置](#环境变量配置)
7. [监控和日志](#监控和日志)
8. [故障排除](#故障排除)

---

## 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 存储 | 20GB | 50GB SSD |
| 网络 | 100Mbps | 1Gbps |

### 软件要求

| 软件 | 版本要求 |
|------|----------|
| 操作系统 | Ubuntu 20.04+ / CentOS 8+ / macOS 12+ |
| Python | 3.12+ |
| Node.js | 18+ |
| Redis | 7.0+ |
| Nginx | 1.20+ |
| Docker | 20.10+ |

### 网络端口

| 端口 | 用途 | 协议 |
|------|------|------|
| 3000 | 前端开发服务器 | HTTP |
| 8000 | 后端API服务器 | HTTP |
| 6379 | Redis | TCP |
| 8080 | Celery Worker | TCP |

---

## 开发环境部署

### 前端开发

1. **安装依赖**
   ```bash
   cd frontend
   npm install
   ```

2. **启动开发服务器**
   ```bash
   npm run dev
   ```

3. **访问应用**
   - 前端：http://localhost:3000
   - API文档：http://localhost:8000/docs

### 后端开发

1. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **安装依赖**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **启动Redis**
   ```bash
   redis-server
   ```

4. **启动Celery Worker**
   ```bash
   cd backend
   celery -A app worker --loglevel=info
   ```

5. **启动FastAPI服务器**
   ```bash
   cd backend
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 生产环境部署

### 前端部署

1. **构建生产版本**
   ```bash
   cd frontend
   npm run build
   ```

2. **部署到Web服务器**
   ```bash
   # 使用Nginx
   sudo cp -r dist/* /var/www/html/
   sudo chown -R www-data:www-data /var/www/html/
   ```

3. **配置Nginx**（见[Nginx配置](#nginx配置)）

### 后端部署

1. **创建生产环境**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **安装生产依赖**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   # 创建.env文件
   cat > .env << EOF
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND_URL=redis://localhost:6379/0
   EOF
   ```

4. **使用Gunicorn启动**
   ```bash
   cd backend
   gunicorn app:app \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8000 \
     --access-logfile /var/log/access.log \
     --error-logfile /var/log/error.log \
     --log-level info
   ```

---

## Docker部署

### Docker Compose配置

创建`docker-compose.yml`文件：

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - NODE_ENV=production
    depends_on:
      - backend
    restart: unless-stopped

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
    volumes:
      - ./backend/static:/app/static
      - ./backend/logs:/app/logs
    depends_on:
      - redis
      - celery
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.celery
    environment:
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND_URL=redis://redis:6379/0
    depends_on:
      - redis
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

volumes:
  redis_data:
```

### 前端Dockerfile

创建`frontend/Dockerfile`：

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

### 后端Dockerfile

创建`backend/Dockerfile`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Celery Dockerfile

创建`backend/Dockerfile.celery`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "app", "worker", "--loglevel=info"]
```

### 启动Docker服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启特定服务
docker-compose restart backend
```

---

## Nginx配置

### 基本配置

创建`nginx/nginx.conf`：

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
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;
}
```

### SSL配置

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

---

## 环境变量配置

### 后端环境变量

创建`.env`文件：

```bash
# AI提供商API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
TONGYI_API_KEY=sk-...
ZHIPU_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
MOONSHOT_API_KEY=sk-...

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND_URL=redis://localhost:6379/0
CELERY_TASK_TRACKS_DB=redis://localhost:6379/0

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
```

### 前端环境变量

创建`frontend/.env.production`：

```bash
# API配置
VITE_API_URL=https://api.your-domain.com
VITE_WS_URL=wss://api.your-domain.com/ws/chat

# 应用配置
VITE_APP_NAME=飞机设计系统
VITE_APP_VERSION=1.0.0
```

---

## 监控和日志

### 应用监控

1. **健康检查端点**
   - 端点：`/health`
   - 返回：`{"status": "healthy", "version": "1.0.0"}`
   - 使用：负载均衡器健康检查

2. **Prometheus监控**
   ```python
   # backend/metrics.py
   from prometheus_client import Counter, Histogram

   # 创建指标
   api_requests = Counter('api_requests_total', 'Total API requests')
   api_duration = Histogram('api_request_duration_seconds', 'API request duration')

   # 记录指标
   @app.middleware("http")
   async def track_requests(request, call_next):
       start_time = time.time()
       response = await call_next(request)
       duration = time.time() - start_time
       api_requests.inc()
       api_duration.observe(duration)
       return response
   ```

3. **Grafana仪表板**
   - 配置Prometheus数据源
   - 创建自定义仪表板
   - 设置告警规则

### 日志管理

1. **应用日志**
   ```python
   # backend/utils/logger.py
   import logging
   from logging.handlers import RotatingFileHandler

   logger = logging.getLogger(__name__)
   logger.setLevel(logging.INFO)

   # 文件处理器
   file_handler = RotatingFileHandler(
       'logs/app.log',
       maxBytes=10485760,  # 100MB
       backupCount=5
   )
   file_handler.setFormatter(logging.Formatter(
       '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   ))

   logger.addHandler(file_handler)

   # 控制台处理器
   console_handler = logging.StreamHandler()
   console_handler.setFormatter(logging.Formatter(
       '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   ))
   logger.addHandler(console_handler)
   ```

2. **访问日志**
   ```nginx
   # nginx.conf
   log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                     '$status $body_bytes_sent "$http_referer" '
                     '"$http_user_agent" "$http_x_forwarded_for"';

   access_log /var/log/nginx/access.log main;
   error_log /var/log/nginx/error.log;
   ```

3. **Celery日志**
   ```python
   # backend/celery_config.py
   from celery.utils.log import get_task_logger

   task_logger = get_task_logger(__name__)
   task_logger.setLevel(logging.INFO)

   # 配置文件处理器
   file_handler = RotatingFileHandler(
       'logs/celery.log',
       maxBytes=10485760,
       backupCount=5
   )
   file_handler.setFormatter(logging.Formatter(
       '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   ))
   task_logger.addHandler(file_handler)
   ```

---

## 故障排除

### 常见问题

#### 1. 前端无法访问

**症状**：无法访问前端页面

**解决方案**：
- 检查Nginx是否运行
- 检查防火墙设置
- 检查DNS解析
- 查看Nginx错误日志

#### 2. 后端API无法访问

**症状**：API请求失败

**解决方案**：
- 检查后端服务是否运行
- 检查Redis是否运行
- 检查Celery Worker是否运行
- 查看后端日志

#### 3. WebSocket连接失败

**症状**：WebSocket无法连接

**解决方案**：
- 检查Nginx WebSocket代理配置
- 检查防火墙WebSocket端口
- 检查后端WebSocket处理
- 查看浏览器控制台错误

#### 4. AI API调用失败

**症状**：AI提供商API调用失败

**解决方案**：
- 检查API Key是否正确
- 检查API Key是否过期
- 检查网络连接
- 检查API提供商状态

#### 5. 内存不足

**症状**：应用崩溃或变慢

**解决方案**：
- 增加服务器内存
- 优化数据库查询
- 使用缓存减少内存使用
- 配置Celery并发数

#### 6. 磁盘空间不足

**症状**：无法保存文件

**解决方案**：
- 清理日志文件
- 清理临时文件
- 增加磁盘空间
- 配置日志轮转

### 性能优化

1. **数据库优化**
   - 使用连接池
   - 添加适当的索引
   - 优化查询语句

2. **缓存策略**
   - 使用Redis缓存常用数据
   - 实现API响应缓存
   - 使用CDN加速静态文件

3. **负载均衡**
   - 使用多个后端实例
   - 配置Nginx负载均衡
   - 实现健康检查

4. **自动扩展**
   - 配置自动扩展策略
   - 监控CPU和内存使用
   - 根据负载自动扩展

---

## 安全配置

### 1. 防火墙配置

```bash
# 允许必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 6379/tcp
sudo ufw allow 8080/tcp

# 启用防火墙
sudo ufw enable
```

### 2. SSL/TLS配置

```bash
# 使用Let's Encrypt获取免费SSL证书
sudo certbot certonly --standalone -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 3. 安全头配置

```nginx
# nginx.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

---

## 备份和恢复

### 数据库备份

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

### 恢复流程

```bash
# 恢复Redis
redis-cli --rdb /backup/redis_20240115_120000.rdb

# 恢复应用数据
tar -xzf /backup/app_data_20240115_120000.tar.gz -C /app/static/

# 重启服务
docker-compose restart
```

---

## 更新和回滚

### 更新流程

```bash
# 1. 备份当前版本
./backup.sh

# 2. 拉取最新代码
git pull origin main

# 3. 更新依赖
cd frontend && npm install
cd ../backend && pip install -r requirements.txt

# 4. 重新构建
cd frontend && npm run build

# 5. 重启服务
docker-compose down
docker-compose up -d
```

### 回滚流程

```bash
# 1. 停止服务
docker-compose down

# 2. 回滚到上一个版本
git checkout <previous-commit-hash>

# 3. 重新构建
cd frontend && npm run build

# 4. 重启服务
docker-compose up -d
```

---

## 监控告警

### 告警配置

```python
# backend/alerts.py
from prometheus_client import start_http_server
from prometheus_client.core import CollectorRegistry

# 创建告警规则
ALERT_API_FAILURE_RATE = 0.1  # 10%失败率
ALERT_RESPONSE_TIME = 5.0  # 5秒响应时间
ALERT_CPU_USAGE = 80.0  # 80% CPU使用率
ALERT_MEMORY_USAGE = 80.0  # 80%内存使用率

def check_alerts():
    # 检查API失败率
    if api_failure_rate > ALERT_API_FAILURE_RATE:
        send_alert("API failure rate too high")

    # 检查响应时间
    if avg_response_time > ALERT_RESPONSE_TIME:
        send_alert("Response time too slow")

    # 检查资源使用
    if cpu_usage > ALERT_CPU_USAGE:
        send_alert("CPU usage too high")

    if memory_usage > ALERT_MEMORY_USAGE:
        send_alert("Memory usage too high")

def send_alert(message):
    # 发送邮件告警
    send_email(message)

    # 发送Slack告警
    send_slack_message(message)
```

---

## 维护计划

### 定期维护

1. **每日维护**
   - 检查日志错误
   - 监控系统性能
   - 检查磁盘空间

2. **每周维护**
   - 备份数据库
   - 清理临时文件
   - 更新安全补丁

3. **每月维护**
   - 审查安全策略
   - 优化数据库
   - 更新依赖版本

### 紧急维护

1. **系统故障**
   - 立即通知相关人员
   - 启动备用服务器
   - 记录故障详情

2. **安全漏洞**
   - 立即修补漏洞
   - 更新安全配置
   - 通知用户

---

## 最佳实践

1. **使用版本控制**
   - 使用Git管理代码
   - 使用语义化版本号
   - 维护CHANGELOG

2. **自动化部署**
   - 使用CI/CD流水线
   - 自动化测试
   - 自动化部署

3. **监控和告警**
   - 实时监控系统状态
   - 设置合理的告警阈值
   - 及时响应告警

4. **文档维护**
   - 保持文档更新
   - 记录所有变更
   - 提供故障排除指南

5. **安全第一**
   - 定期更新依赖
   - 使用强密码
   - 启用HTTPS
   - 定期安全审计

---

## 更新日志

- **v1.0.0** (2024-01-15)
  - 初始版本
  - 所有核心功能
  - Docker部署支持
  - 完整的文档
