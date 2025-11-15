# CLAUDE.md - AI Assistant Guide for lmstudio-lan-api

## Project Overview

**lmstudio-lan-api** (also known as **LM Studio LAN Gateway**) is a production-ready LAN-based API gateway for LM Studio, enabling secure local network access to LM Studio's language model capabilities.

### Project Purpose
- Provide a secure gateway between LAN clients and LM Studio's OpenAI-compatible API
- Enable remote model management via admin endpoints (load, unload, activate models)
- Support load-time parameters (context length, GPU offload, TTL)
- Add security features: API key authentication, IP allow-listing
- Transparently proxy all `/v1/...` requests to LM Studio's local API
- Provide structured logging and clean resource management

### Key Features
- **Admin API**: Load models with custom configurations, unload models, activate defaults
- **Transparent Proxy**: Forward all `/v1/*` endpoints (chat, completions, etc.) to LM Studio
- **Security**: API key authentication and IP/CIDR-based access control
- **Model Management**: Use LM Studio Python SDK for advanced model control
- **Production-Ready**: Proper error handling, logging, startup/shutdown lifecycle

## Repository Structure

```
lmstudio-lan-api/
├── src/
│   └── lmstudio_gateway/
│       ├── __init__.py
│       ├── settings.py           # Pydantic-based configuration
│       ├── logging_config.py     # Structured logging setup
│       ├── middleware.py         # API key & IP allowlist middleware
│       ├── dependencies.py       # Shared httpx client & LM Studio SDK
│       ├── admin_models.py       # /admin router for model management
│       ├── proxy.py              # /v1 proxy router
│       └── main.py               # FastAPI app assembly
├── tests/
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── fixtures/                 # Test fixtures and mocks
├── docs/                         # Additional documentation
├── scripts/                      # Deployment and utility scripts
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore
├── Dockerfile                    # Docker container definition
├── docker-compose.yml            # Docker Compose setup
├── pyproject.toml                # Optional: Python packaging config
└── README.md                     # Project documentation
```

## Technology Stack

### Core Technologies
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Server**: Uvicorn (ASGI server)
- **HTTP Client**: httpx (async)
- **LM Studio Integration**: lmstudio-python SDK
- **Configuration**: Pydantic Settings with python-dotenv
- **Validation**: Pydantic models

### Development Tools
- **Linting**: Ruff or Flake8 + Black
- **Type Checking**: mypy
- **Testing**: pytest + pytest-asyncio
- **Code Formatting**: Black
- **Documentation**: Google-style or NumPy-style docstrings

## Development Workflow

### Initial Setup

1. **Create Python virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Set up development tools** (optional)
   ```bash
   pip install -r requirements-dev.txt  # if you create one
   # or install manually:
   pip install black ruff mypy pytest pytest-asyncio pytest-cov
   ```

### Development Commands

**Run the server:**
```bash
# Development mode with auto-reload
uvicorn lmstudio_gateway.main:app --reload --host 0.0.0.0 --port 8001

# Or using environment variables
uvicorn lmstudio_gateway.main:app \
  --host "${GATEWAY_HOST:-0.0.0.0}" \
  --port "${GATEWAY_PORT:-8001}" \
  --reload
```

**Testing:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lmstudio_gateway --cov-report=html

# Run specific test file
pytest tests/unit/test_middleware.py

# Run with verbose output
pytest -v
```

**Code Quality:**
```bash
# Format code
black src/

# Lint code
ruff check src/

# Type check
mypy src/
```

### Git Workflow
- **Main branch**: `main` - production-ready code
- **Feature branches**: `feature/description` - new features
- **Bug fixes**: `fix/description` - bug fixes
- **Claude branches**: `claude/claude-md-*` - AI assistant work

### Commit Conventions
Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test additions/modifications
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements
- `security:` - Security fixes

## Key Architectural Decisions

### 1. Gateway Pattern
- **Separation of Concerns**: Gateway handles security, routing, and coordination; LM Studio handles model inference
- **LM Studio Assumption**: Runs on same machine at `http://127.0.0.1:1234` (configurable)
- **No GUI Management**: Out of scope - assumes LM Studio is already running

### 2. API Design

#### Admin Endpoints (`/admin`)
- `GET /admin/models` - List available models
- `POST /admin/models/load` - Load model with configuration
- `POST /admin/models/unload` - Unload model
- `POST /admin/models/activate` - Set active default model

#### Proxy Endpoints (`/v1/*`)
- All OpenAI-compatible endpoints: `/v1/chat/completions`, `/v1/completions`, etc.
- Automatically inject active model and default inference params if missing
- Transparent pass-through to LM Studio

#### Health Check
- `GET /health` - Simple health check (optionally bypass auth)

### 3. Security Architecture

**API Key Authentication:**
- Header-based: `X-API-Key: your-secret-key`
- Configurable via `GATEWAY_API_KEY` env var
- Disabled if env var is empty (NOT recommended for production)

**IP Allow-listing:**
- Support for single IPs, CIDR ranges, or wildcard `*`
- Examples: `192.168.0.0/24`, `10.0.0.2,10.0.0.3`
- Configured via `IP_ALLOWLIST` env var

**Middleware Order:**
1. CORS middleware (if enabled)
2. IP allowlist check
3. API key validation
4. Route handlers

### 4. Model Management

**LM Studio Python SDK:**
- Use `lmstudio.get_default_client()` for model operations
- Support for load config: context length, GPU settings, etc.
- TTL (time-to-live) for automatic unloading
- Multiple model instances via `instance_id`

**Active Model State:**
- Gateway maintains current "active" model in `app.state`
- Auto-inject active model into `/v1` requests if `model` field is missing
- Apply default inference parameters (temperature, max_tokens, etc.)

### 5. HTTP Client Management

**httpx AsyncClient:**
- Single shared client for all LM Studio HTTP requests
- Created in startup event, closed in shutdown event
- Base URL: `LMSTUDIO_BASE_URL` from config
- Default timeout: 60 seconds

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# LM Studio API URL (typically localhost)
LMSTUDIO_BASE_URL=http://127.0.0.1:1234

# Gateway bind settings
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8001

# Security: API key (REQUIRED for production)
GATEWAY_API_KEY=change-me-please

# Security: IP allow-list
# Examples:
#   "*" - allow all (dev only)
#   "192.168.0.0/24" - allow subnet
#   "10.0.0.2,10.0.0.3" - specific IPs
IP_ALLOWLIST=192.168.0.0/24,10.0.0.0/24

# Allow unauthenticated /health checks
REQUIRE_AUTH_FOR_HEALTH=false

# Logging level
LOG_LEVEL=INFO
```

### Settings Implementation Pattern

**Always use Pydantic Settings:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    LMSTUDIO_BASE_URL: AnyHttpUrl = "http://127.0.0.1:1234"
    GATEWAY_HOST: str = "0.0.0.0"
    GATEWAY_PORT: int = 8001
    # ... etc
```

## Code Conventions

### Python Style Guide

**Follow PEP 8 with Black formatting:**
- Line length: 88 characters (Black default)
- Indentation: 4 spaces
- Imports: stdlib → third-party → local, separated by blank lines
- Use type hints for all function signatures

### Naming Conventions

- **Files/Modules**: `snake_case.py` (e.g., `admin_models.py`)
- **Classes**: `PascalCase` (e.g., `LoadModelRequest`, `ApiKeyMiddleware`)
- **Functions/Methods**: `snake_case` (e.g., `load_model`, `get_http_client`)
- **Variables**: `snake_case` (e.g., `active_model`, `http_client`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private members**: `_leading_underscore` (e.g., `_validate_ip`)

### Type Hints

**Always use type hints:**
```python
from typing import Optional, Dict, Any, List
from fastapi import Request

async def get_active_model(request: Request) -> Dict[str, Any]:
    """
    Retrieve the active model configuration from app state.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary containing model_key, instance_id, and default_inference
    """
    active_model = getattr(request.app.state, "active_model", None)
    if active_model is None:
        active_model = {
            "model_key": None,
            "instance_id": None,
            "default_inference": {},
        }
        request.app.state.active_model = active_model
    return active_model
```

### Error Handling

**Use FastAPI HTTPException:**
```python
from fastapi import HTTPException, status

# For expected errors
if not model_key:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="model_key is required"
    )

# For external service errors
try:
    response = await http_client.get("/api/v0/models")
    response.raise_for_status()
except httpx.RequestError as e:
    logger.exception("Error connecting to LM Studio: %s", e)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="LM Studio API unreachable"
    )
```

**Logging with context:**
```python
import logging

logger = logging.getLogger("lmstudio_gateway.admin")

logger.info("Loading model_key=%s instance_id=%s", model_key, instance_id)
logger.warning("Forbidden IP %s tried to access %s", client_ip, path)
logger.exception("Failed to load model: %s", e)  # Includes traceback
```

### Pydantic Models

**Use for request/response validation:**
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class LoadModelRequest(BaseModel):
    model_key: str = Field(..., description="LM Studio model key")
    instance_id: Optional[str] = None
    load_config: Optional[Dict[str, Any]] = None
    ttl_seconds: Optional[int] = Field(default=None, ge=0)
    activate: bool = True

    class Config:
        extra = "forbid"  # or "allow" if you need flexibility
        json_schema_extra = {
            "example": {
                "model_key": "qwen2.5-7b-instruct",
                "instance_id": "primary-qwen",
                "load_config": {"contextLength": 8192},
                "activate": True
            }
        }
```

### Middleware Pattern

**Use FastAPI/Starlette BaseHTTPMiddleware:**
```python
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response

class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check conditions
        if not self._should_check_auth(request):
            return await call_next(request)

        # Validate
        if not self._is_valid(request):
            return Response(content="Unauthorized", status_code=401)

        # Continue
        return await call_next(request)
```

## Testing Standards

### Test Structure

**Use pytest with async support:**
```python
import pytest
from httpx import AsyncClient
from lmstudio_gateway.main import create_app

@pytest.fixture
async def client():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

### Test Naming Convention

```python
def test_<function_name>_<condition>_<expected_result>():
    """
    Test that <function_name> returns <expected_result> when <condition>.
    """
    pass

# Examples:
def test_load_model_with_valid_key_returns_success():
    """Test that load_model returns success with valid model key."""

def test_api_key_middleware_with_invalid_key_returns_401():
    """Test that API key middleware returns 401 with invalid key."""

def test_ip_allowlist_with_blocked_ip_returns_403():
    """Test that IP allowlist returns 403 for blocked IPs."""
```

### Mocking

**Mock external dependencies:**
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_list_models_success():
    mock_response = AsyncMock()
    mock_response.json.return_value = {"models": ["model1", "model2"]}
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        result = await list_models(mock_http_client)
        assert "models" in result
```

### Coverage Target

- **Minimum**: 80% overall coverage
- **Critical paths**: 95%+ (authentication, proxy logic, model management)
- **Utilities**: 90%+

## API Endpoints Reference

### Admin API

#### List Models
```http
GET /admin/models
Headers:
  X-API-Key: your-secret-key

Response: 200 OK
{
  "models": [
    {"name": "qwen2.5-7b-instruct", ...},
    ...
  ]
}
```

#### Load Model
```http
POST /admin/models/load
Headers:
  X-API-Key: your-secret-key
  Content-Type: application/json

Body:
{
  "model_key": "qwen2.5-7b-instruct",
  "instance_id": "primary-qwen",
  "load_config": {
    "contextLength": 8192,
    "gpu": {"ratio": 1.0}
  },
  "ttl_seconds": 3600,
  "default_inference": {
    "temperature": 0.4,
    "max_tokens": 2048
  },
  "activate": true
}

Response: 200 OK
{
  "status": "loaded",
  "model_key": "qwen2.5-7b-instruct",
  "instance_id": "primary-qwen",
  "activated": true,
  ...
}
```

#### Unload Model
```http
POST /admin/models/unload
Headers:
  X-API-Key: your-secret-key
  Content-Type: application/json

Body:
{
  "model_key": "qwen2.5-7b-instruct",
  "instance_id": null
}

Response: 200 OK
{
  "status": "unloaded",
  "model_key": "qwen2.5-7b-instruct"
}
```

#### Activate Model
```http
POST /admin/models/activate
Headers:
  X-API-Key: your-secret-key
  Content-Type: application/json

Body:
{
  "model_key": "qwen2.5-7b-instruct",
  "instance_id": "primary-qwen",
  "default_inference": {
    "temperature": 0.3
  }
}

Response: 200 OK
{
  "status": "activated",
  "model_key": "qwen2.5-7b-instruct",
  ...
}
```

### Proxy API (OpenAI-compatible)

All `/v1/*` endpoints are proxied to LM Studio with automatic model injection:

```http
POST /v1/chat/completions
Headers:
  X-API-Key: your-secret-key
  Content-Type: application/json

Body:
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
  // "model" is auto-injected from active model if missing
  // default inference params are auto-injected if missing
}
```

## Security Best Practices

### Critical Security Rules

1. **ALWAYS set `GATEWAY_API_KEY` in production** - never run without authentication
2. **Use IP allow-listing** - restrict to known LAN subnets
3. **Never expose to public internet** - LAN only, use VPN if remote access needed
4. **Keep secrets in environment variables** - never commit to git
5. **Use HTTPS in production** - terminate SSL at reverse proxy (nginx/Traefik)
6. **Rotate API keys regularly** - use secrets management (Vault, AWS Secrets Manager)
7. **Validate all inputs** - Pydantic models handle this automatically
8. **Log security events** - unauthorized access attempts, IP blocks
9. **Keep dependencies updated** - run `pip list --outdated` regularly
10. **Never log sensitive data** - API keys, user prompts (if private)

### .gitignore Essential Entries

```gitignore
# Environment
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
```

## Dependencies Management

### Core Dependencies (`requirements.txt`)

```text
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
httpx>=0.26.0
lmstudio-python>=0.1.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
```

### Development Dependencies (optional `requirements-dev.txt`)

```text
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
black>=24.0.0
ruff>=0.1.0
mypy>=1.8.0
```

### Keeping Dependencies Updated

```bash
# Check for outdated packages
pip list --outdated

# Update all packages (with caution)
pip install --upgrade -r requirements.txt

# Check for security vulnerabilities
pip-audit  # install with: pip install pip-audit
```

## Performance Considerations

### Optimization Guidelines

1. **Async all the way**: Use `async/await` for all I/O operations
2. **Connection reuse**: Single httpx.AsyncClient for all LM Studio requests
3. **Streaming support**: Proxy streaming responses from LM Studio as-is
4. **Request timeout**: Set appropriate timeouts (default: 60s, configurable)
5. **Uvicorn workers**: Use `--workers N` for CPU-bound operations (usually 1 is fine)
6. **Caching**: Cache model list if it doesn't change frequently

### Monitoring & Observability

**Structured Logging:**
```python
logger.info(
    "Request processed",
    extra={
        "endpoint": request.url.path,
        "method": request.method,
        "client_ip": request.client.host,
        "response_time_ms": elapsed_ms,
        "status_code": response.status_code,
    }
)
```

**Future Enhancements:**
- Prometheus metrics via `prometheus-fastapi-instrumentator`
- Distributed tracing (OpenTelemetry)
- Health check improvements (check LM Studio connectivity)

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "lmstudio_gateway.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### docker-compose.yml

```yaml
version: "3.9"

services:
  lmstudio-gateway:
    build: .
    ports:
      - "8001:8001"
    env_file:
      - .env
    restart: unless-stopped
    # Note: LM Studio must be running on the host
    # Use host.docker.internal:1234 on Docker Desktop
    # or host network mode on Linux
```

## Common Pitfalls to Avoid

### ❌ Don't Do This

```python
# Using synchronous blocking calls
import requests  # DON'T use synchronous library
response = requests.get(url)  # Blocks the event loop!

# Missing type hints
def process_data(data):  # No types!
    return data

# Bare except clauses
try:
    result = await do_something()
except:  # Too broad!
    pass

# Hardcoded secrets
API_KEY = "my-secret-key"  # NEVER!

# Missing validation
@router.post("/endpoint")
async def endpoint(data: dict):  # Use Pydantic model!
    pass
```

### ✅ Do This

```python
# Async HTTP client
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# Proper type hints
def process_data(data: Dict[str, Any]) -> ProcessedData:
    return ProcessedData(**data)

# Specific exception handling
try:
    result = await do_something()
except httpx.RequestError as e:
    logger.exception("Request failed: %s", e)
    raise HTTPException(status_code=503, detail="Service unavailable")

# Environment-based secrets
from .settings import settings
api_key = settings.GATEWAY_API_KEY

# Pydantic validation
@router.post("/endpoint")
async def endpoint(data: RequestModel) -> ResponseModel:
    return ResponseModel(...)
```

## Debugging Tips

### Common Issues

1. **LM Studio connection failed**
   ```
   Error: Service unavailable / Connection refused

   Solutions:
   - Verify LM Studio is running
   - Check LMSTUDIO_BASE_URL in .env (default: http://127.0.0.1:1234)
   - Ensure LM Studio API server is enabled in LM Studio settings
   - Test manually: curl http://127.0.0.1:1234/v1/models
   ```

2. **401 Unauthorized**
   ```
   Error: Unauthorized

   Solutions:
   - Check X-API-Key header matches GATEWAY_API_KEY in .env
   - Verify .env file is loaded (try printing settings.GATEWAY_API_KEY)
   - For /health, check REQUIRE_AUTH_FOR_HEALTH setting
   ```

3. **403 Forbidden**
   ```
   Error: Forbidden

   Solutions:
   - Check client IP is in IP_ALLOWLIST
   - Verify CIDR notation is correct (e.g., 192.168.0.0/24)
   - Try IP_ALLOWLIST=* for testing (NOT for production)
   ```

4. **Module import errors**
   ```
   Error: ModuleNotFoundError: No module named 'lmstudio_gateway'

   Solutions:
   - Ensure PYTHONPATH includes src directory
   - Use: PYTHONPATH=src uvicorn lmstudio_gateway.main:app
   - Or run from project root with package mode
   ```

### Logging for Debugging

```bash
# Enable DEBUG level logging
LOG_LEVEL=DEBUG uvicorn lmstudio_gateway.main:app --reload

# Use uvicorn's access log
uvicorn lmstudio_gateway.main:app --access-log

# Python logging in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

## AI Assistant Guidelines

### When Working on This Project

1. **Architecture First**: Understand the gateway pattern - don't bypass LM Studio SDK
2. **Security Paranoia**: Always validate inputs, never skip authentication in production code
3. **Async Always**: Use `async/await` for all I/O operations
4. **Type Everything**: Use type hints for all function signatures
5. **Test Coverage**: Write tests for new features, aim for 80%+ coverage
6. **Error Context**: Always log errors with context (what, where, why)
7. **Pydantic Models**: Use for all request/response validation
8. **Documentation**: Update docstrings and this CLAUDE.md when making changes

### Before Committing

- [ ] Code follows Black formatting (`black src/`)
- [ ] Linting passes (`ruff check src/`)
- [ ] Type checking passes (`mypy src/`)
- [ ] All tests pass (`pytest`)
- [ ] Coverage meets target (`pytest --cov`)
- [ ] No secrets or sensitive data in code
- [ ] .env.example updated if new env vars added
- [ ] CLAUDE.md updated if architecture changed
- [ ] Commit message follows conventions

### Code Review Checklist

**For any pull request, verify:**
- [ ] Type hints on all functions
- [ ] Pydantic models for request/response validation
- [ ] Proper error handling with specific exceptions
- [ ] Security: authentication not bypassed
- [ ] Logging with appropriate levels
- [ ] Tests for happy path and error cases
- [ ] No blocking I/O operations
- [ ] Documentation updated

### Communication Patterns

When implementing features:
1. **Clarify requirements** - Ask about edge cases upfront
2. **Explain trade-offs** - Discuss security vs. convenience, performance vs. simplicity
3. **Suggest improvements** - Point out refactoring opportunities
4. **Highlight risks** - Call out security or performance concerns

## Resources

### Official Documentation

- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **HTTPX**: https://www.python-httpx.org/
- **Uvicorn**: https://www.uvicorn.org/
- **LM Studio Python SDK**: https://github.com/lmstudio-ai/lmstudio-python

### Python Best Practices

- **Python Type Hints**: https://docs.python.org/3/library/typing.html
- **PEP 8 Style Guide**: https://peps.python.org/pep-0008/
- **Async Python**: https://docs.python.org/3/library/asyncio.html

### Testing & Quality

- **pytest**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **Black**: https://black.readthedocs.io/
- **Ruff**: https://beta.ruff.rs/docs/

### Security

- **OWASP API Security Top 10**: https://owasp.org/www-project-api-security/
- **Python Security Best Practices**: https://python.readthedocs.io/en/stable/library/security_warnings.html

## Version History

### Latest Update
- **Date**: 2025-11-15
- **Version**: 1.0.0
- **Status**: Production-ready specification integrated
- **Changes**:
  - Complete rewrite from Node.js/TypeScript to Python/FastAPI
  - Added production-ready architecture based on official specification
  - Detailed security, middleware, and proxy implementation guidelines
  - Comprehensive code examples and patterns
  - Docker deployment configuration
  - Enhanced testing and debugging sections

### Next Steps
1. Initialize Python package structure
2. Implement core modules (settings, logging, middleware)
3. Create admin API endpoints
4. Implement proxy router
5. Add comprehensive tests
6. Create Docker setup
7. Write comprehensive README.md

---

**Note for AI Assistants**: This document reflects the **production-ready specification** for the LM Studio LAN Gateway. All code must follow these patterns. Update this document when architectural decisions change, new patterns emerge, or security considerations evolve. This is a **Python/FastAPI project**, not Node.js/TypeScript.
