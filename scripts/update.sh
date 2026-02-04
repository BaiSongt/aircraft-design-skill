#!/bin/bash

echo "Starting update at $(date)"

./scripts/backup.sh

echo "Pulling latest code..."
git pull origin main

echo "Updating backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

echo "Updating frontend dependencies..."
cd frontend
npm install
cd ..

echo "Building frontend..."
cd frontend
npm run build
cd ..

echo "Restarting services..."
docker-compose down
docker-compose up -d

echo "Waiting for services to start..."
sleep 10

echo "Checking service status..."
docker-compose ps

echo "Update completed at $(date)"
