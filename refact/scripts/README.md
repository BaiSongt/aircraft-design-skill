# Deployment Scripts

This directory contains utility scripts for managing the ChatUI Aircraft Design System deployment.

## Available Scripts

### backup.sh

Creates a backup of the application data including:
- Redis database
- Application static files
- Docker logs

**Usage:**
```bash
./scripts/backup.sh
```

**What it does:**
1. Creates a timestamped backup directory in `/backup/`
2. Dumps Redis data to RDB file
3. Creates tarball of application data
4. Saves Docker logs
5. Removes backups older than 7 days

**Output:**
```
/backup/20240115_120000/
├── redis_backup_20240115_120000.rdb
├── app_data.tar.gz
└── docker_logs.txt
```

### update.sh

Updates the application to the latest version.

**Usage:**
```bash
./scripts/update.sh
```

**What it does:**
1. Runs backup script
2. Pulls latest code from git
3. Updates backend dependencies
4. Updates frontend dependencies
5. Rebuilds frontend
6. Restarts all Docker services

### rollback.sh

Rolls back to a specific git commit.

**Usage:**
```bash
./scripts/rollback.sh <commit-hash>
```

**Example:**
```bash
./scripts/rollback.sh abc123def456
```

**What it does:**
1. Stops all Docker services
2. Checks out the specified commit
3. Rebuilds frontend
4. Restarts all Docker services

## Setting Up Automated Backups

### Using Cron

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/aircraft-design-skill/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### Using Systemd Timer

Create `/etc/systemd/system/aircraft-backup.service`:
```ini
[Unit]
Description=Aircraft Design Backup
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/aircraft-design-skill
ExecStart=/path/to/aircraft-design-skill/scripts/backup.sh
```

Create `/etc/systemd/system/aircraft-backup.timer`:
```ini
[Unit]
Description=Run Aircraft Design Backup Daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the timer:
```bash
sudo systemctl enable aircraft-backup.timer
sudo systemctl start aircraft-backup.timer
```

## Monitoring Backups

### Check Backup Size

```bash
du -sh /backup/*
```

### List Recent Backups

```bash
ls -lht /backup/
```

### Verify Backup Integrity

```bash
# Check Redis backup
redis-cli --rdb /backup/20240115_120000/redis_backup_20240115_120000.rdb

# Check application data backup
tar -tzf /backup/20240115_120000/app_data.tar.gz | head -20
```

## Troubleshooting

### Permission Denied

```bash
chmod +x scripts/backup.sh
chmod +x scripts/update.sh
chmod +x scripts/rollback.sh
```

### Backup Directory Doesn't Exist

```bash
sudo mkdir -p /backup
sudo chown $USER:$USER /backup
```

### Docker Compose Not Found

```bash
# Make sure docker-compose is in PATH
export PATH=$PATH:/usr/local/bin

# Or use full path
/usr/local/bin/docker-compose up -d
```

### Git Pull Fails

```bash
# Check git status
git status

# Stash local changes
git stash

# Then run update again
./scripts/update.sh
```

## Customization

### Change Backup Retention

Edit `backup.sh` and modify this line:
```bash
find /backup -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null
```

Change `7` to desired number of days.

### Change Backup Location

Edit `backup.sh` and modify this line:
```bash
BACKUP_DIR="/backup/$DATE"
```

Change `/backup` to desired location.

### Add Additional Backup Items

Edit `backup.sh` and add after the Redis backup:
```bash
# Backup custom directory
docker-compose exec -T backend tar -czf - /app/custom > $BACKUP_DIR/custom.tar.gz
```

## Best Practices

1. **Test Backups Regularly**: Periodically test restoring from backups
2. **Monitor Disk Space**: Ensure sufficient disk space for backups
3. **Offsite Backups**: Consider copying backups to offsite storage
4. **Encryption**: Encrypt sensitive backups
5. **Documentation**: Keep backup and restore procedures documented

## Support

For issues with these scripts:
- Check logs in `/var/log/backup.log`
- Verify Docker Compose is running: `docker-compose ps`
- Check disk space: `df -h`
