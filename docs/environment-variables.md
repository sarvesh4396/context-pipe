# Environment Variables Reference

This document ensures environment variables are **synchronized** between local docker-compose and CI/CD pipelines.

## ✅ Synced Configuration

### CI/CD (.github/workflows/ci.yml)
```yaml
env:
  REDIS_URL: redis://localhost:6379/0
  DATABASE_URL: postgresql://context_pipe_test:test_password@localhost:5432/context_pipe_test

services:
  postgres:
    env:
      POSTGRES_USER: context_pipe_test
      POSTGRES_PASSWORD: test_password
      POSTGRES_DB: context_pipe_test
```

### Local Docker Compose (docker-compose.yml)
```yaml
services:
  redis:
    # No special config needed (default port 6379)
    
  postgres:
    environment:
      POSTGRES_USER: context_pipe_test
      POSTGRES_PASSWORD: test_password
      POSTGRES_DB: context_pipe_test
```

### Local .env.local
```bash
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://context_pipe_test:test_password@localhost:5432/context_pipe_test
```

## Credentials

| Service | User | Password | Database |
|---------|------|----------|----------|
| **Redis** | (none) | (none) | 0 |
| **PostgreSQL** | `context_pipe_test` | `test_password` | `context_pipe_test` |

## Usage

### Start Services
```bash
make up
```

Output shows environment variables:
```
✓ Services ready!
  Redis:      localhost:6379
  PostgreSQL: localhost:5432 (user: context_pipe_test, pass: test_password)

Environment variables (for tests):
  REDIS_URL=redis://localhost:6379/0
  DATABASE_URL=postgresql://context_pipe_test:test_password@localhost:5432/context_pipe_test
```

### Run Tests (Automatically Uses These Variables)
```bash
# Inherits env variables from docker-compose and .env.local
make test-unit        # Unit tests only
make test             # All tests with services
make test-integration # Integration tests only
```

### Verify Connectivity

```bash
# Redis
docker-compose exec redis redis-cli PING
# Expected output: PONG

# PostgreSQL  
docker-compose exec postgres psql -U context_pipe_test -d context_pipe_test -c "SELECT 'OK';"
# Expected output: OK
```
