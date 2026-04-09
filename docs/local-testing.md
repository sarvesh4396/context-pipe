# Local Testing Guide

Quick setup for testing context-pipe locally with Redis and PostgreSQL.

## Prerequisites

- Docker and Docker Compose installed
- `uv` package manager
- Python 3.11+

## Quick Start

### 1. Start Services

```bash
make up
```

This starts Redis and PostgreSQL containers:
- **Redis**: `localhost:6379`
- **PostgreSQL**: `localhost:5432` (user: `postgres`, password: `postgres`)

### 2. Run Tests

#### Unit Tests Only (No Services Required)
```bash
make test-unit
```

#### All Tests (Requires Services)
```bash
make test
```

#### Integration Tests Only
```bash
make test-integration
```

### 3. Stop/Clean Up

```bash
make down      # Stop containers (data persists)
make remove    # Remove containers and volumes
make clean     # Full cleanup including test artifacts
```

## Common Workflows

### Development Cycle

```bash
# Start services once
make up

# Make code changes...

# Run tests repeatedly
make test-unit              # Fast unit tests
uv run pytest tests/ -v     # Single test file
make test-integration       # Test with services
```

### Full Test Suite

```bash
make clean    # Clean everything first
make test     # Restart services and run all tests
```

### Debugging

```bash
# View container logs
make logs

# Access Redis CLI
make shell-redis
redis> KEYS *

# Access PostgreSQL
make shell-postgres
postgres=# SELECT * FROM conversations;

# Check status
make status
```

## Makefile Commands

| Command | Purpose |
|---------|---------|
| `make help` | Show all available commands |
| `make up` | Start containers |
| `make down` | Stop containers (keep data) |
| `make remove` | Remove containers and volumes |
| `make logs` | Stream container logs |
| `make test` | Run all tests with services |
| `make test-unit` | Run unit tests only |
| `make test-integration` | Run integration tests |
| `make clean` | Full cleanup |
| `make shell-redis` | Connect to Redis |
| `make shell-postgres` | Connect to PostgreSQL |
| `make status` | Show container status |

## Docker Compose Details

Services defined in `docker-compose.yml`:

### Redis
- Image: `redis:7-alpine`
- Port: `6379`
- Data: Persisted in `redis_data` volume
- Health check: Every 5s using `redis-cli ping`

### PostgreSQL
- Image: `postgres:16-alpine`
- Port: `5432`
- User: `postgres`
- Password: `postgres`
- Database: `context_pipe`
- Data: Persisted in `postgres_data` volume
- Health check: Every 5s using `pg_isready`

## Environment Variables

For integration tests, these are automatically set:

```bash
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/context_pipe
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 6379
lsof -i :6379
# Kill it
kill -9 <PID>
```

### Containers Won't Start
```bash
# Remove everything and start fresh
make clean
make up
```

### Tests Timeout/Fail
```bash
# Check services are healthy
make status

# View logs
make logs

# Databases may need time to initialize
sleep 5 && make test-integration
```

### PostgreSQL Connection Issues
```bash
# Verify connection
make shell-postgres
# If it fails, check logs
make logs | grep postgres
```

## Performance Tips

1. **First run is slower** (pulls Docker images) — be patient
2. **Tests run fast** after first setup (~0.02s for unit tests)
3. **Integration tests slower** (~1-2s, includes I/O)
4. **Use `make test-unit`** during development for fast feedback

## CI/CD Integration

These same services run in GitHub Actions CI/CD pipeline. See `.github/workflows/ci.yml` for configuration.

## Next Steps

- Read [Algorithms](algorithms.md) to understand compaction strategies
- Check [Contributing](../CONTRIBUTING.md) for development guidelines
- Explore test files in `tests/` for integration examples
