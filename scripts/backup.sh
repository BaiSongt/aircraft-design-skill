#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/$DATE"

mkdir -p $BACKUP_DIR

echo "Starting backup at $(date)"

docker-compose exec redis redis-cli --rdb /data/redis_backup_$DATE.rdb
docker cp $(docker-compose ps -q redis):/data/redis_backup_$DATE.rdb $BACKUP_DIR/

docker-compose exec -T backend tar -czf - /app/static > $BACKUP_DIR/app_data.tar.gz

docker-compose logs --no-log-prefix > $BACKUP_DIR/docker_logs.txt

find /backup -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null

echo "Backup completed: $BACKUP_DIR"
echo "Backup size: $(du -sh $BACKUP_DIR | cut -f1)"
