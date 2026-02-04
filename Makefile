.PHONY: help build up down restart logs clean backup update rollback install-deps test lint

help:
	@echo "Available commands:"
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make clean          - Remove all containers and volumes"
	@echo "  make backup         - Backup application data"
	@echo "  make update         - Update and restart services"
	@echo "  make rollback       - Rollback to previous commit"
	@echo "  make install-deps   - Install development dependencies"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run code linting"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-celery:
	docker-compose logs -f celery

logs-redis:
	docker-compose logs -f redis

logs-nginx:
	docker-compose logs -f nginx

clean:
	docker-compose down -v
	docker system prune -a

backup:
	./scripts/backup.sh

update:
	./scripts/update.sh

rollback:
	@if [ -z "$(COMMIT)" ]; then \
		echo "Usage: make rollback COMMIT=<commit-hash>"; \
		exit 1; \
	fi
	./scripts/rollback.sh $(COMMIT)

install-deps:
	cd frontend && npm install
	cd backend && pip install -r requirements.txt

test:
	cd backend && pytest
	cd frontend && npm test

lint:
	ruff check .
	ruff format --check .
	mypy aircraft_design/

lint-fix:
	ruff check --fix .
	ruff format .
	mypy aircraft_design/

ps:
	docker-compose ps

stats:
	docker stats

shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

shell-redis:
	docker-compose exec redis redis-cli

shell-celery:
	docker-compose exec celery /bin/bash

db-shell:
	docker-compose exec redis redis-cli

prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

dev-up:
	docker-compose -f docker-compose.dev.yml up -d

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f
