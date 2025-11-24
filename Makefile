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
	@echo "EC2 Production Commands:"
	@echo "  make ec2          - Start EC2 production environment (foreground)"
	@echo "  make ec2-build    - Build and start EC2 production environment (background)"
	@echo "  make ec2-down     - Stop EC2 production environment"
	@echo "  make ec2-restart  - Restart EC2 production environment"
	@echo "  make ec2-logs     - Show EC2 production logs"
	@echo ""
	@echo "Service Management:"
	@echo "  make restart-backend   - Restart backend service"
	@echo "  make restart-frontend  - Restart frontend service"
	@echo "  make restart-chatbot   - Restart chatbot service"
	@echo "  make logs-backend      - Show backend logs"
	@echo "  make logs-frontend     - Show frontend logs"
	@echo "  make logs-chatbot      - Show chatbot logs"
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
	@echo "  make shell-chatbot   - Access chatbot container shell"

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

# EC2 Production environment
ec2:
	docker-compose -f docker-compose.ec2.yml --env-file .env.production up

ec2-build:
	docker-compose -f docker-compose.ec2.yml --env-file .env.production up --build -d

ec2-down:
	docker-compose -f docker-compose.ec2.yml down

ec2-restart:
	docker-compose -f docker-compose.ec2.yml restart

ec2-logs:
	docker-compose -f docker-compose.ec2.yml logs -f

# Service management
restart-backend:
	docker-compose -f docker-compose.dev.yml restart backend

restart-frontend:
	docker-compose -f docker-compose.dev.yml restart frontend

restart-chatbot:
	docker-compose -f docker-compose.dev.yml restart chatbot

logs-backend:
	docker-compose -f docker-compose.dev.yml logs -f backend

logs-frontend:
	docker-compose -f docker-compose.dev.yml logs -f frontend

logs-chatbot:
	docker-compose -f docker-compose.dev.yml logs -f chatbot

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

shell-chatbot:
	docker-compose -f docker-compose.dev.yml exec chatbot bash

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

rebuild-chatbot:
	docker-compose -f docker-compose.dev.yml build --no-cache chatbot
	docker-compose -f docker-compose.dev.yml up -d chatbot

# EC2 Service management
ec2-restart-backend:
	docker-compose -f docker-compose.ec2.yml restart backend

ec2-restart-frontend:
	docker-compose -f docker-compose.ec2.yml restart frontend

ec2-restart-chatbot:
	docker-compose -f docker-compose.ec2.yml restart chatbot

ec2-logs-backend:
	docker-compose -f docker-compose.ec2.yml logs -f backend

ec2-logs-frontend:
	docker-compose -f docker-compose.ec2.yml logs -f frontend

ec2-logs-chatbot:
	docker-compose -f docker-compose.ec2.yml logs -f chatbot

ec2-ps:
	docker-compose -f docker-compose.ec2.yml ps
