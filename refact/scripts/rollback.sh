#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <commit-hash>"
    echo "Example: $0 abc123def456"
    exit 1
fi

COMMIT_HASH=$1

echo "Starting rollback to commit $COMMIT_HASH at $(date)"

echo "Stopping services..."
docker-compose down

echo "Rolling back code..."
git checkout $COMMIT_HASH

echo "Rebuilding frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Restarting services..."
docker-compose up -d

echo "Waiting for services to start..."
sleep 10

echo "Checking service status..."
docker-compose ps

echo "Rollback completed at $(date)"
echo "Current commit: $(git rev-parse HEAD)"
