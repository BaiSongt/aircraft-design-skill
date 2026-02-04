# Docker Deployment Guide

This guide provides step-by-step instructions for deploying the ChatUI Aircraft Design System using Docker.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- 20GB free disk space

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/aircraft-design-skill.git
cd aircraft-design-skill
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file and add your AI provider API keys:

```bash
# AI Provider API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
# ... other API keys
```

### 3. Start All Services

```bash
docker-compose up -d
```

### 4. Verify Deployment

```bash
docker-compose ps
```

You should see all services running:
- frontend (port 3000)
- backend (port 8000)
- redis (port 6379)
- celery
- nginx (port 80, 443)

### 5. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Service Architecture

```
┌─────────────┐
│   Nginx     │ (Port 80/443)
│  (Proxy)    │
└──────┬──────┘
       │
       ├─────────────┬─────────────┐
       │             │             │
┌──────▼──────┐ ┌───▼────┐ ┌────▼─────┐
│  Frontend   │ │Backend │ │  Redis   │
│  (React)    │ │(FastAPI)│ │ (Cache)  │
└─────────────┘ └───┬────┘ └──────────┘
                   │
              ┌────▼────┐
              │ Celery  │
              │ (Tasks) │
              └─────────┘
```

## Docker Compose Services

### Frontend Service

- **Image**: Built from `frontend/Dockerfile`
- **Port**: 3000:80
- **Dependencies**: backend
- **Restart Policy**: unless-stopped

### Backend Service

- **Image**: Built from `backend/Dockerfile`
- **Port**: 8000:8000
- **Dependencies**: redis, celery
- **Environment Variables**:
  - `PYTHONUNBUFFERED=1`
  - `REDIS_URL=redis://redis:6379/0`
  - `CELERY_BROKER_URL=redis://redis:6379/0`
  - `CELERY_RESULT_BACKEND_URL=redis://redis:6379/0`
  - AI provider API keys
- **Volumes**:
  - `./backend/static:/app/static`
  - `./backend/logs:/app/logs`
- **Restart Policy**: unless-stopped

### Celery Service

- **Image**: Built from `backend/Dockerfile.celery`
- **Dependencies**: redis
- **Concurrency**: 4 workers
- **Restart Policy**: unless-stopped

### Redis Service

- **Image**: redis:7-alpine
- **Port**: 6379:6379
- **Volume**: redis_data:/data
- **Persistence**: AOF enabled
- **Restart Policy**: unless-stopped

### Nginx Service

- **Image**: nginx:alpine
- **Ports**: 80:80, 443:443
- **Volumes**:
  - `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`
  - `./nginx/ssl:/etc/nginx/ssl:ro`
  - `./frontend/dist:/usr/share/nginx/html:ro`
- **Dependencies**: frontend, backend
- **Restart Policy**: unless-stopped

## Management Commands

### Start Services

```bash
docker-compose up -d
```

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery
```

### Restart Services

```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
```

### Update Services

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build
```

### Remove All Data

```bash
docker-compose down -v
```

**Warning**: This will delete all data including Redis data!

## SSL/TLS Configuration

### Generate Self-Signed Certificate (Development)

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### Use Let's Encrypt (Production)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
```

### Auto-Renewal

```bash
# Add to crontab
sudo crontab -e
```

Add this line:
```
0 2 * * * certbot renew --quiet --post-hook "docker-compose restart nginx"
```

## Backup and Restore

### Backup

```bash
./scripts/backup.sh
```

This will:
1. Create a timestamped backup directory
2. Backup Redis data
3. Backup application data
4. Backup Docker logs
5. Remove backups older than 7 days

### Restore

```bash
# Restore Redis
docker cp /backup/20240115_120000/redis_backup_20240115_120000.rdb \
  $(docker-compose ps -q redis):/data/dump.rdb
docker-compose restart redis

# Restore application data
docker cp /backup/20240115_120000/app_data.tar.gz .
docker-compose exec -T backend tar -xzf /tmp/app_data.tar.gz -C /app
```

## Monitoring

### Check Service Status

```bash
docker-compose ps
```

### View Resource Usage

```bash
docker stats
```

### Check Logs

```bash
# Backend logs
docker-compose logs -f backend

# Celery logs
docker-compose logs -f celery

# Nginx logs
docker-compose logs -f nginx
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Redis health
docker-compose exec redis redis-cli ping
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Check port conflicts
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
netstat -tulpn | grep :6379

# Clean up Docker resources
docker system prune -a
```

### Backend Can't Connect to Redis

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec backend python -c "import redis; r = redis.Redis(host='redis', port=6379); print(r.ping())"

# Restart Redis
docker-compose restart redis
```

### Frontend Build Fails

```bash
# Clear node_modules
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Permission Issues

```bash
# Fix volume permissions
sudo chown -R $USER:$USER backend/static backend/logs
```

### Out of Disk Space

```bash
# Clean up Docker resources
docker system prune -a --volumes

# Remove old backups
find /backup -type d -mtime +30 -exec rm -rf {} \;
```

## Performance Optimization

### Increase Worker Count

Edit `docker-compose.yml`:

```yaml
celery:
  # ... other config
  command: celery -A app worker --loglevel=info --concurrency=8
```

### Adjust Memory Limits

Edit `docker-compose.yml`:

```yaml
backend:
  # ... other config
  deploy:
    resources:
      limits:
        memory: 2G
      reservations:
        memory: 1G
```

### Enable Redis Persistence

Already enabled in the default configuration with AOF (Append Only File).

## Security Hardening

### Change Default Secrets

Edit `.env`:

```bash
SECRET_KEY=generate-a-strong-random-key-here
```

### Enable Rate Limiting

Configure in `backend/config/app_config.py`.

### Use Firewall

```bash
# Allow only necessary ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Regular Updates

```bash
# Update base images
docker-compose pull
docker-compose up -d --build
```

## Production Deployment

### 1. Prepare Server

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Configure Domain

Point your domain to the server IP address.

### 3. Setup SSL

Follow the SSL/TLS Configuration section above.

### 4. Deploy

```bash
# Clone repository
git clone https://github.com/yourusername/aircraft-design-skill.git
cd aircraft-design-skill

# Configure environment
cp .env.example .env
nano .env

# Start services
docker-compose up -d
```

### 5. Setup Monitoring

```bash
# Add monitoring tools
# Consider using Prometheus + Grafana
# Or use cloud provider monitoring
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend
docker-compose up -d --scale backend=3

# Scale celery
docker-compose up -d --scale celery=4
```

### Load Balancing

Update `nginx/nginx.conf` to use multiple backend instances.

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/aircraft-design-skill/issues
- Documentation: https://github.com/yourusername/aircraft-design-skill/docs
