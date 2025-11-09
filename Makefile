# Schedule SaaS Docker Management
.PHONY: help build up down logs clean dev prod test

# Default target
help:
	@echo "Available targets:"
	@echo "  help     - Show this help message"
	@echo "  build    - Build all Docker images"
	@echo "  up       - Start all services (production)"
	@echo "  dev      - Start development environment"
	@echo "  down     - Stop all services"
	@echo "  logs     - Show logs from all services"
	@echo "  clean    - Remove all containers, volumes, and images"
	@echo "  test     - Run tests in containers"
	@echo "  backup   - Backup database"
	@echo "  restore  - Restore database from backup"

# Build all images
build:
	docker-compose build --no-cache

# Start production environment
up:
	docker-compose -f docker-compose.yml up -d

# Start development environment
dev:
	docker-compose -f docker-compose.dev.yml up -d
	@echo ""
	@echo "🚀 Development environment started!"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/api/v1/docs"
	@echo ""

# Start production environment
prod:
	@if [ ! -f .env.prod ]; then \
		echo "❌ .env.prod file not found!"; \
		echo "   Copy .env.prod.example to .env.prod and configure it."; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
	@echo ""
	@echo "🚀 Production environment started!"
	@echo "   Application: http://localhost"
	@echo "   API:         http://localhost/api/v1/docs"
	@echo ""

# Stop all services
down:
	docker-compose down
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.prod.yml down

# Show logs
logs:
	docker-compose logs -f

# Show development logs
logs-dev:
	docker-compose -f docker-compose.dev.yml logs -f

# Show production logs
logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f

# Clean everything
clean:
	@echo "⚠️  This will remove all containers, volumes, and images!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		docker-compose down -v --rmi all; \
		docker-compose -f docker-compose.dev.yml down -v --rmi all; \
		docker-compose -f docker-compose.prod.yml down -v --rmi all; \
		docker system prune -f; \
		echo "✅ Cleanup completed!"; \
	else \
		echo ""; \
		echo "❌ Cleanup cancelled."; \
	fi

# Run backend tests
test:
	docker-compose -f docker-compose.dev.yml exec backend poetry run pytest tests/ -v

# Run linting
lint:
	docker-compose -f docker-compose.dev.yml exec backend poetry run black app/ --check
	docker-compose -f docker-compose.dev.yml exec backend poetry run isort app/ --check-only

# Format code
format:
	docker-compose -f docker-compose.dev.yml exec backend poetry run black app/
	docker-compose -f docker-compose.dev.yml exec backend poetry run isort app/

# Database backup
backup:
	@mkdir -p ./backups
	docker-compose exec database pg_dump -U schedule_user schedule_saas > ./backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created in ./backups/"

# Database restore (requires backup file)
restore:
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Please specify backup file: make restore FILE=./backups/backup_20241101_120000.sql"; \
		exit 1; \
	fi
	docker-compose exec -T database psql -U schedule_user -d schedule_saas < $(FILE)
	@echo "✅ Database restored from $(FILE)"

# Run database migrations
migrate:
	docker-compose -f docker-compose.dev.yml exec backend poetry run alembic upgrade head

# Create new migration
migration:
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Please specify migration message: make migration MSG='Add new table'"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.dev.yml exec backend poetry run alembic revision --autogenerate -m "$(MSG)"

# Seed database with demo data
seed:
	docker-compose -f docker-compose.dev.yml exec backend poetry run python scripts/seed.py

# Show system status
status:
	docker-compose ps
	@echo ""
	docker system df

# Shell into backend container
shell-backend:
	docker-compose -f docker-compose.dev.yml exec backend /bin/bash

# Shell into frontend container
shell-frontend:
	docker-compose -f docker-compose.dev.yml exec frontend /bin/sh

# Shell into database container
shell-db:
	docker-compose exec database psql -U schedule_user -d schedule_saas

# Monitor logs
monitor:
	@echo "Monitoring all services logs (Ctrl+C to exit)..."
	docker-compose -f docker-compose.dev.yml logs -f --tail=100

# Health check
health:
	@echo "🔍 Checking service health..."
	@curl -f http://localhost:8000/health || echo "❌ Backend health check failed"
	@curl -f http://localhost:3000/ || echo "❌ Frontend health check failed"
	@echo "✅ Health check completed"

# Install dependencies in development
install:
	docker-compose -f docker-compose.dev.yml exec backend poetry install
	docker-compose -f docker-compose.dev.yml exec frontend pnpm install
