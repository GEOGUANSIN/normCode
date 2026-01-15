# Docker Strategy for NormCode Server

A detailed plan for containerizing NormCode Server.

---

## Design Goals

| Goal | Why |
|------|-----|
| **Single container** | Simple deployment, everything in one place |
| **Small image** | Fast pulls, less storage |
| **Fast builds** | Good developer experience |
| **Persistent data** | Survive restarts, data outside container |
| **Configurable** | Environment variables, no image rebuilds |
| **Debuggable** | Logs accessible, health checks |

---

## Container Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTAINER                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /app/                        Application code                   │
│  ├── server/                  FastAPI backend                    │
│  ├── frontend/dist/           Built React app (static)           │
│  └── infra/                   NormCode core (symlink or copy)    │
│                                                                  │
│  /data/                       Mounted volume (persistent)        │
│  ├── plans/                   Deployed plan packages             │
│  ├── provisions/              Shared prompts, paradigms          │
│  ├── runs/                    Per-run SQLite + artifacts         │
│  └── config/                  Server + agent configuration       │
│                                                                  │
│  Process: uvicorn server:app                                     │
│  Port: 8000                                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Multi-Stage Dockerfile

```dockerfile
# ============================================================================
# Stage 1: Frontend Builder
# ============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Copy package files first (better caching)
COPY canvas_app/frontend/package*.json ./
RUN npm ci

# Copy source and build
COPY canvas_app/frontend/ ./
RUN npm run build

# ============================================================================
# Stage 2: Python Dependencies
# ============================================================================
FROM python:3.11-slim AS python-deps

WORKDIR /deps

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY canvas_app/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install infra package
COPY infra/ /tmp/infra/
COPY setup.py pyproject.toml /tmp/
WORKDIR /tmp
RUN pip install --no-cache-dir -e . || pip install --no-cache-dir .

# ============================================================================
# Stage 3: Final Runtime Image
# ============================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For MCP npm-based servers (optional)
    nodejs \
    npm \
    # Health check
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=python-deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy infra package
COPY infra/ ./infra/

# Copy backend
COPY canvas_app/backend/ ./server/

# Copy built frontend
COPY --from=frontend-builder /build/dist ./frontend/dist/

# Create data directories
RUN mkdir -p /data/plans /data/provisions /data/runs /data/config

# Copy default configuration
COPY deployment/config/default-server.yaml /data/config/server.yaml
COPY deployment/config/default-agents.yaml /data/config/agents.yaml

# Set environment
ENV NORMCODE_DATA_DIR=/data
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## docker-compose.yaml

### Development Mode

```yaml
# docker-compose.dev.yaml
version: '3.8'

services:
  normcode:
    build:
      context: ..
      dockerfile: deployment/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      # Persistent data
      - normcode-data:/data
      # Mount source for hot reload (dev only)
      - ../canvas_app/backend:/app/server:ro
      - ../infra:/app/infra:ro
    environment:
      # LLM API Keys
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      # Dev settings
      - NORMCODE_ENV=development
      - LOG_LEVEL=DEBUG
    command: >
      uvicorn server.main:app 
      --host 0.0.0.0 
      --port 8000 
      --reload 
      --reload-dir /app/server
    restart: unless-stopped

volumes:
  normcode-data:
```

### Production Mode

```yaml
# docker-compose.yaml (production)
version: '3.8'

services:
  normcode:
    image: normcode/server:latest
    # Or build locally:
    # build:
    #   context: ..
    #   dockerfile: deployment/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      # Persistent data only
      - normcode-data:/data
      # Optional: mount custom config
      - ./config:/data/config:ro
    environment:
      # LLM API Keys (from .env or secrets manager)
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      # Production settings
      - NORMCODE_ENV=production
      - LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  normcode-data:
```

---

## Configuration Files

### default-server.yaml

```yaml
# /data/config/server.yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 1  # Increase for production
  
storage:
  plans_dir: "/data/plans"
  runs_dir: "/data/runs"
  provisions_dir: "/data/provisions"

execution:
  max_concurrent_runs: 10
  default_max_cycles: 100
  checkpoint_frequency: 5

logging:
  level: "${LOG_LEVEL:-INFO}"
  format: "json"  # or "text" for development
```

### default-agents.yaml

```yaml
# /data/config/agents.yaml
agents:
  qwen-plus:
    provider: dashscope
    model: qwen-plus
    api_key_env: DASHSCOPE_API_KEY
    
  qwen-turbo:
    provider: dashscope
    model: qwen-turbo-latest
    api_key_env: DASHSCOPE_API_KEY
    
  gpt-4o:
    provider: openai
    model: gpt-4o
    api_key_env: OPENAI_API_KEY
    
  gpt-4o-mini:
    provider: openai
    model: gpt-4o-mini
    api_key_env: OPENAI_API_KEY
    
  claude-sonnet:
    provider: anthropic
    model: claude-3-sonnet-20240229
    api_key_env: ANTHROPIC_API_KEY

  demo:
    provider: mock
    description: "Mock LLM for testing (no API calls)"

default_agent: qwen-plus
```

---

## Volume Strategy

### What Goes in /data (Persisted)

| Path | Content | Why Persist |
|------|---------|-------------|
| `/data/plans/` | Deployed plan packages | Plans survive restarts |
| `/data/runs/` | SQLite DBs, artifacts | Run history, checkpoints |
| `/data/provisions/` | Shared prompts, paradigms | Custom provisions |
| `/data/config/` | Server + agent config | Custom configuration |

### What Stays in Container (Ephemeral)

| Path | Content | Why Ephemeral |
|------|---------|---------------|
| `/app/server/` | Backend code | Updated via image |
| `/app/frontend/` | Built UI | Updated via image |
| `/app/infra/` | Core library | Updated via image |

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `DASHSCOPE_API_KEY` | API key for Qwen models |
| `OPENAI_API_KEY` | API key for GPT models |
| `ANTHROPIC_API_KEY` | API key for Claude models |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `NORMCODE_DATA_DIR` | `/data` | Base data directory |
| `NORMCODE_ENV` | `production` | Environment (development/production) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PORT` | `8000` | Server port |

---

## Build & Run Commands

### Development

```powershell
# Build and run with hot reload
cd normCode
docker-compose -f deployment/docker-compose.dev.yaml up --build

# View logs
docker-compose -f deployment/docker-compose.dev.yaml logs -f

# Stop
docker-compose -f deployment/docker-compose.dev.yaml down
```

### Production

```powershell
# Build image
docker build -t normcode/server:latest -f deployment/Dockerfile .

# Run with compose
docker-compose -f deployment/docker-compose.yaml up -d

# Or run directly
docker run -d \
  --name normcode \
  -p 8000:8000 \
  -v normcode-data:/data \
  -e DASHSCOPE_API_KEY=$env:DASHSCOPE_API_KEY \
  normcode/server:latest

# View logs
docker logs -f normcode

# Shell into container
docker exec -it normcode /bin/bash
```

---

## Health Check Endpoint

Add to the server:

```python
# server/main.py

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "data_dir": os.getenv("NORMCODE_DATA_DIR", "/data"),
        "plans_count": len(plan_registry.list_all()) if plan_registry else 0,
        "active_runs": len(execution_manager.list_active_runs()) if execution_manager else 0
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check - is the server ready to accept requests?"""
    # Check if essential components are initialized
    checks = {
        "plan_registry": plan_registry is not None,
        "execution_manager": execution_manager is not None,
        "data_dir_exists": os.path.exists(os.getenv("NORMCODE_DATA_DIR", "/data"))
    }
    
    all_ready = all(checks.values())
    
    if not all_ready:
        raise HTTPException(status_code=503, detail={"ready": False, "checks": checks})
    
    return {"ready": True, "checks": checks}
```

---

## Directory Structure After Implementation

```
normCode/
├── deployment/
│   ├── Dockerfile
│   ├── docker-compose.yaml          # Production
│   ├── docker-compose.dev.yaml      # Development
│   ├── config/
│   │   ├── default-server.yaml
│   │   └── default-agents.yaml
│   ├── DEPLOYMENT_VISION.md
│   ├── DOCKER_STRATEGY.md           # This file
│   ├── MCP_INTEGRATION.md
│   └── NORMCODE_VS_MCP.md
│
├── canvas_app/                       # Becomes /app in container
│   ├── backend/                      # → /app/server
│   └── frontend/                     # → /app/frontend (built)
│
├── infra/                            # → /app/infra
│
└── ... (other project files)
```

---

## Image Optimization

### Current Approach (Multi-stage)

```
Stage 1: frontend-builder  (~500MB, discarded)
Stage 2: python-deps       (~800MB, discarded)
Stage 3: runtime           (~400MB, final image)
```

### Size Reduction Tips

1. **Use slim base**: `python:3.11-slim` instead of `python:3.11`
2. **Multi-stage builds**: Don't include build tools in final image
3. **Clean up in same layer**: `apt-get install && rm -rf /var/lib/apt/lists/*`
4. **Use .dockerignore**: Exclude unnecessary files

### .dockerignore

```
# .dockerignore
.git
.gitignore
*.md
!deployment/*.md
__pycache__
*.pyc
.pytest_cache
.venv
venv
node_modules
.env
*.log
.DS_Store
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/docker.yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: deployment/Dockerfile
          push: true
          tags: |
            normcode/server:latest
            normcode/server:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## Summary

| Aspect | Decision |
|--------|----------|
| **Base image** | `python:3.11-slim` |
| **Build** | Multi-stage (frontend → python deps → runtime) |
| **Data persistence** | Volume mount at `/data` |
| **Configuration** | YAML files in `/data/config` + env vars |
| **Secrets** | Environment variables |
| **Health checks** | `/health` and `/ready` endpoints |
| **Logging** | JSON format, stdout |
| **Development** | Hot reload via mounted volumes |

---

## Next Steps

1. Create `deployment/config/` with default YAML files
2. Create `deployment/Dockerfile` (from this document)
3. Create `deployment/docker-compose.yaml` and `docker-compose.dev.yaml`
4. Add `/health` and `/ready` endpoints to backend
5. Create `.dockerignore`
6. Test build and run locally

