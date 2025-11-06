.PHONY: help dev prod up down restart logs clean build test

# Default target
help:
	@echo "Stack Lab Demo - Docker Commands"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev          - Start development environment (hot-reload)"
	@echo "  make dev-build    - Build and start development environment"
	@echo "  make dev-down     - Stop development environment"
	@echo "  make dev-restart  - Restart development environment"
	@echo "  make dev-logs     - Show development logs"
	@echo ""
	@echo "Production Commands:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-build   - Build and start production environment"
	@echo "  make prod-down    - Stop production environment"
	@echo ""
	@echo "Service Management:"
	@echo "  make restart-backend   - Restart backend service"
	@echo "  make restart-frontend  - Restart frontend service"
	@echo "  make logs-backend      - Show backend logs"
	@echo "  make logs-frontend     - Show frontend logs"
	@echo ""
	@echo "Database Commands:"
	@echo "  make db-shell     - Access PostgreSQL shell"
	@echo "  make db-backup    - Backup database"
	@echo "  make db-reset     - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean        - Remove all containers, volumes, and images"
	@echo "  make ps           - Show running containers"
	@echo "  make shell-backend   - Access backend container shell"
	@echo "  make shell-frontend  - Access frontend container shell"

# Development environment
dev:
	docker-compose -f docker-compose.dev.yml up

dev-build:
	docker-compose -f docker-compose.dev.yml up --build

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-restart:
	docker-compose -f docker-compose.dev.yml restart

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Production environment
prod:
	docker-compose up

prod-build:
	docker-compose up --build -d

prod-down:
	docker-compose down

# Service management
restart-backend:
	docker-compose -f docker-compose.dev.yml restart backend

restart-frontend:
	docker-compose -f docker-compose.dev.yml restart frontend

logs-backend:
	docker-compose -f docker-compose.dev.yml logs -f backend

logs-frontend:
	docker-compose -f docker-compose.dev.yml logs -f frontend

# Database commands
db-shell:
	docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d quant_investment_db

db-backup:
	docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U postgres quant_investment_db > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up to backup_$$(date +%Y%m%d_%H%M%S).sql"

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose -f docker-compose.dev.yml up -d postgres
	@echo "Database reset complete"

# Shell access
shell-backend:
	docker-compose -f docker-compose.dev.yml exec backend bash

shell-frontend:
	docker-compose -f docker-compose.dev.yml exec frontend sh

# Utility commands
ps:
	docker-compose -f docker-compose.dev.yml ps

clean:
	@echo "WARNING: This will remove all containers, volumes, and images!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose -f docker-compose.dev.yml down -v --rmi all
	docker system prune -a --volumes -f
	@echo "Cleanup complete"

# Quick rebuild
rebuild-backend:
	docker-compose -f docker-compose.dev.yml build --no-cache backend
	docker-compose -f docker-compose.dev.yml up -d backend

rebuild-frontend:
	docker-compose -f docker-compose.dev.yml build --no-cache frontend
	docker-compose -f docker-compose.dev.yml up -d frontend
