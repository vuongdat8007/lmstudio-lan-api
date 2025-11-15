# LM Studio LAN Gateway

Production-ready LAN gateway for LM Studio's OpenAI-compatible API, enabling secure local network access to LM Studio's language model capabilities.

## Features

- **Admin API**: Load, unload, and activate models with custom configurations
- **Transparent Proxy**: Forward all `/v1/*` OpenAI-compatible endpoints to LM Studio
- **Security**: API key authentication and IP/CIDR-based access control
- **Real-time Debugging**: Server-Sent Events (SSE) for live model loading and inference monitoring
- **Model Management**: Advanced model control via LM Studio Python SDK
- **Production-Ready**: Comprehensive error handling, structured logging, clean lifecycle management

## Quick Start

### Prerequisites

- Python 3.11 or higher
- LM Studio installed and running on the same machine
- LM Studio API server enabled (typically on http://127.0.0.1:1234)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lmstudio-lan-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run the gateway**
   ```bash
   uvicorn lmstudio_gateway.main:app --host 0.0.0.0 --port 8001
   ```

## Configuration

Key environment variables in `.env`:

```bash
# LM Studio API URL
LMSTUDIO_BASE_URL=http://127.0.0.1:1234

# Gateway settings
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8001

# Security (REQUIRED for production)
GATEWAY_API_KEY=your-secret-key-here
IP_ALLOWLIST=192.168.0.0/24,10.0.0.0/24

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

### Admin API

- `GET /admin/models` - List available models
- `POST /admin/models/load` - Load model with configuration
- `POST /admin/models/unload` - Unload model
- `POST /admin/models/activate` - Activate model as default

### Debug API (Real-time Monitoring)

- `GET /debug/stream` - SSE stream for real-time events
- `GET /debug/status` - Current status snapshot
- `GET /debug/metrics` - Performance metrics

### Proxy API

- `POST /v1/chat/completions` - Chat completions (OpenAI-compatible)
- `POST /v1/completions` - Text completions (OpenAI-compatible)
- All other `/v1/*` endpoints are transparently proxied

### Health Check

- `GET /health` - Basic health check

## Usage Examples

### Load a Model

```bash
curl -X POST http://localhost:8001/admin/models/load \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{
    "model_key": "qwen2.5-7b-instruct",
    "load_config": {"contextLength": 8192},
    "activate": true
  }'
```

### Chat Completion

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.0.10:8001/v1",
    api_key="your-secret-key"
)

response = client.chat.completions.create(
    model="qwen2.5-7b-instruct",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### Real-time Debug Monitoring

```javascript
const eventSource = new EventSource('http://192.168.0.10:8001/debug/stream', {
  headers: { 'X-API-Key': 'your-secret-key' }
});

eventSource.addEventListener('model_load_progress', (event) => {
  const data = JSON.parse(event.data);
  console.log(`Loading: ${(data.progress * 100).toFixed(1)}%`);
});
```

## Development

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lmstudio_gateway --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type check
mypy src/
```

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t lmstudio-lan-gateway .

# Run container
docker run -d \
  --name lmstudio-gateway \
  -p 8001:8001 \
  --env-file .env \
  lmstudio-lan-gateway
```

### Docker Compose

```bash
docker-compose up -d
```

## Security Considerations

1. **Always set `GATEWAY_API_KEY`** in production environments
2. **Use IP allow-listing** to restrict access to known LAN subnets
3. **Never expose to public internet** - LAN only (use VPN for remote access)
4. **Rotate API keys regularly** using secrets management tools
5. **Keep dependencies updated** with `pip list --outdated`

## Documentation

- [CLAUDE.md](CLAUDE.md) - Comprehensive guide for AI assistants
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Phased implementation plan
- [API Documentation](http://localhost:8001/docs) - Interactive API docs (when running)

## Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌──────────────┐
│ LAN Clients │ ──────> │  Gateway (8001)  │ ──────> │  LM Studio   │
│  (OpenAI)   │  HTTP   │  - Auth/Security │  HTTP   │   (1234)     │
│             │ <────── │  - Admin API     │ <────── │              │
└─────────────┘         │  - Debug API     │         └──────────────┘
                        │  - Proxy /v1/*   │
                        └──────────────────┘
```

## Contributing

Contributions are welcome! Please:

1. Follow the code conventions in [CLAUDE.md](CLAUDE.md)
2. Write tests for new features
3. Ensure all tests pass and coverage meets targets
4. Follow conventional commit messages

## License

MIT License - See LICENSE file for details

## Troubleshooting

### LM Studio Connection Failed

- Verify LM Studio is running
- Check `LMSTUDIO_BASE_URL` in `.env` (default: http://127.0.0.1:1234)
- Ensure LM Studio API server is enabled in LM Studio settings

### 401 Unauthorized

- Verify `X-API-Key` header matches `GATEWAY_API_KEY` in `.env`
- Check `.env` file is loaded correctly

### 403 Forbidden

- Verify client IP is in `IP_ALLOWLIST`
- Check CIDR notation is correct (e.g., 192.168.0.0/24)

## Project Status

**Version**: 1.0.0
**Status**: Production-ready
**Python**: 3.11+

---

**Built with FastAPI, Pydantic, and the LM Studio Python SDK**
