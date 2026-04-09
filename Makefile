.PHONY: help up down remove logs test test-all test-unit test-integration clean

help:
	@echo "context-pipe - Local Development Commands"
	@echo ""
	@echo "Docker Compose:"
	@echo "  make up              Start Redis and PostgreSQL containers"
	@echo "  make down            Stop containers (data persists)"
	@echo "  make remove          Remove containers and volumes (data deleted)"
	@echo "  make logs            View container logs (Ctrl+C to exit)"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests (unit + integration)"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests (requires services running)"
	@echo "  make clean           Clean test artifacts and containers"
	@echo ""

up:
	@echo "Starting Redis and PostgreSQL containers..."
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 3
	docker-compose ps
	@echo ""
	@echo "✓ Services ready!"
	@echo "  Redis:      localhost:6379"
	@echo "  PostgreSQL: localhost:5432 (user: context_pipe_test, pass: test_password)"
	@echo ""
	@echo "Environment variables (for tests):"
	@echo "  REDIS_URL=redis://localhost:6379/0"
	@echo "  DATABASE_URL=postgresql://context_pipe_test:test_password@localhost:5432/context_pipe_test"

down:
	@echo "Stopping containers..."
	docker-compose down
	@echo "✓ Containers stopped (data persisted)"

remove:
	@echo "Removing containers and volumes..."
	docker-compose down -v
	@echo "✓ Containers and volumes removed"

logs:
	docker-compose logs -f

test: up test-all

test-all:
	@echo "Running all tests..."
	uv run pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	uv run pytest tests/test_models.py tests/test_compaction.py -v

test-integration: up
	@echo "Running integration tests..."
	uv run pytest tests/test_memory_backend.py tests/test_redis_backend.py tests/test_sqlalchemy_backend.py -v

clean: remove
	@echo "Cleaning test artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

shell-redis:
	docker-compose exec redis redis-cli

shell-postgres:
	docker-compose exec postgres psql -U postgres -d context_pipe

status:
	@echo "Container Status:"
	docker-compose ps
