# LM Studio LAN Gateway - Quick Start Guide

## Prerequisites

1. **Python 3.11+** installed (Python 3.13 recommended)
2. **LM Studio** running on `http://127.0.0.1:1234`
3. Virtual environment activated (`.venv`)

## Installation

```bash
# 1. Clone or download the repository
cd lmstudio-lan-api

# 2. Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Unix/Linux/macOS
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Install development tools
pip install -r requirements-dev.txt

# 5. Configure environment
cp .env.example .env
# Edit .env with your settings
```

## Quick Start

### Starting the Server

**Windows:**
```cmd
start.bat
```

**Unix/Linux/macOS:**
```bash
./start.sh
```

**Manual:**
```bash
# Windows
set PYTHONPATH=src
python -m uvicorn lmstudio_gateway.main:app --host 0.0.0.0 --port 8001

# Unix/Linux/macOS
export PYTHONPATH=src
python -m uvicorn lmstudio_gateway.main:app --host 0.0.0.0 --port 8001
```

### Stopping the Server

**Windows:**
```cmd
stop.bat
```

**Unix/Linux/macOS:**
```bash
./stop.sh
```

**Manual:**
Press `Ctrl+C` in the terminal where the server is running.

## Testing the Installation

### 1. Health Check (No authentication required by default)
```bash
curl http://localhost:8001/health
# Expected: {"status":"ok"}
```

### 2. List Available Models (Requires API key)
```bash
curl -H "X-API-Key: change-me-please" http://localhost:8001/admin/models
# Returns list of available LM Studio models
```

### 3. Load a Model
```bash
curl -X POST http://localhost:8001/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "model_key": "your-model-name",
    "activate": true
  }'
```

### 4. Chat Completion (OpenAI-compatible)
```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## Configuration

Edit `.env` file to customize:

```env
# LM Studio API URL
LMSTUDIO_BASE_URL=http://127.0.0.1:1234

# Gateway settings
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8001

# Security: API key (CHANGE THIS!)
GATEWAY_API_KEY=change-me-please

# Security: IP allow-list
# "*" = allow all (development only)
# "192.168.0.0/24" = allow subnet
# "10.0.0.2,10.0.0.3" = specific IPs
IP_ALLOWLIST=*

# Health endpoint authentication
REQUIRE_AUTH_FOR_HEALTH=false

# Logging level
LOG_LEVEL=INFO
```

## Running Tests

```bash
# Set PYTHONPATH
export PYTHONPATH=src  # Unix/Linux/macOS
set PYTHONPATH=src     # Windows

# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=lmstudio_gateway --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

## Development

### Code Formatting
```bash
black src/
```

### Linting
```bash
ruff check src/
```

### Type Checking
```bash
mypy src/
```

## API Endpoints

### Admin Endpoints
- `GET /admin/models` - List available models
- `POST /admin/models/load` - Load a model with configuration
- `POST /admin/models/unload` - Unload a model
- `POST /admin/models/activate` - Activate a model as default

### Debug Endpoints
- `GET /debug/stream` - Real-time Server-Sent Events stream
- `GET /debug/status` - Current status snapshot
- `GET /debug/metrics` - Performance metrics

### Proxy Endpoints
- `POST /v1/chat/completions` - OpenAI-compatible chat
- `POST /v1/completions` - OpenAI-compatible completions
- All other `/v1/*` endpoints are proxied to LM Studio

### Health Check
- `GET /health` - Simple health check

## Security Best Practices

### For Development
- Use `IP_ALLOWLIST=*` to allow all IPs
- Use a simple API key like `change-me-please`
- Keep `REQUIRE_AUTH_FOR_HEALTH=false` for easy testing

### For Production
1. **Generate a strong API key:**
   ```bash
   # Unix/Linux/macOS
   openssl rand -hex 32

   # Windows PowerShell
   -join (1..32 | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
   ```

2. **Restrict IP access:**
   ```env
   # Allow only your LAN subnet
   IP_ALLOWLIST=192.168.0.0/24

   # Or specific IPs
   IP_ALLOWLIST=192.168.0.10,192.168.0.11,192.168.0.12
   ```

3. **Enable health check authentication:**
   ```env
   REQUIRE_AUTH_FOR_HEALTH=true
   ```

4. **Use HTTPS** (set up reverse proxy with nginx/Traefik)

5. **Never expose to public internet** - LAN only!

## Troubleshooting

### Server won't start - "ModuleNotFoundError: No module named 'lmstudio_gateway'"
**Solution:** Set `PYTHONPATH=src` before running

### Server won't start - "Address already in use"
**Solution:** Stop any existing server on port 8001:
- Windows: `stop.bat`
- Unix: `./stop.sh`

### "403 Forbidden" errors
**Cause:** Your IP is not in the allowlist
**Solution:**
- For development: Set `IP_ALLOWLIST=*` in `.env`
- For production: Add your IP/subnet to `IP_ALLOWLIST`

### "401 Unauthorized" errors
**Cause:** Missing or incorrect API key
**Solution:** Include header: `-H "X-API-Key: your-api-key"`

### "503 Service Unavailable" when calling admin endpoints
**Cause:** LM Studio is not running or not accessible
**Solution:**
1. Start LM Studio
2. Verify it's running on `http://127.0.0.1:1234`
3. Check `LMSTUDIO_BASE_URL` in `.env`

### Tests failing with "AssertionError: assert 'change-me-please' == ''"
**Cause:** Environment variables are set in your shell
**Solution:** Unset them before running tests:
```bash
unset GATEWAY_API_KEY IP_ALLOWLIST
python -m pytest
```

## Project Structure

```
lmstudio-lan-api/
├── src/
│   └── lmstudio_gateway/
│       ├── __init__.py
│       ├── main.py              # FastAPI app
│       ├── settings.py          # Configuration
│       ├── middleware.py        # Security middleware
│       ├── dependencies.py      # Shared dependencies
│       ├── admin_models.py      # Admin API
│       ├── debug.py             # Debug/monitoring API
│       ├── proxy.py             # Proxy to LM Studio
│       └── logging_config.py    # Logging setup
├── tests/
│   └── unit/
│       ├── test_settings.py
│       └── test_middleware.py
├── .env                         # Your configuration (not in git)
├── .env.example                 # Template configuration
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Dev dependencies
├── start.sh / start.bat         # Start server scripts
├── stop.sh / stop.bat           # Stop server scripts
├── README.md                    # Full documentation
├── CLAUDE.md                    # AI assistant guide
└── QUICKSTART.md               # This file
```

## Next Steps

1. **Start LM Studio** if not already running
2. **Start the gateway** using `start.bat` or `./start.sh`
3. **Test the endpoints** using the examples above
4. **Load a model** using the admin API
5. **Make requests** to the `/v1/*` endpoints
6. **Monitor in real-time** using `/debug/stream`

## Getting Help

- Read the full documentation in [README.md](README.md)
- Check the AI assistant guide in [CLAUDE.md](CLAUDE.md)
- Review implementation plan in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

## License

See [LICENSE](LICENSE) file for details.
