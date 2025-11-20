# llama-server LAN Gateway

Production-ready LAN gateway for **llama-server** (llama.cpp), enabling secure local network access with advanced process management and monitoring capabilities.

## Overview

This gateway provides a secure, feature-rich interface to llama-server running on your LAN. It manages llama-server as a subprocess, allowing dynamic model loading, comprehensive monitoring, and transparent proxying of OpenAI-compatible endpoints.

### Key Features

- **Process Management**: Full lifecycle control of llama-server (start/stop/restart)
- **Model Registry**: Manage multiple model configurations with per-model settings
- **Admin API**: Load, unload, and manage models via REST API
- **Transparent Proxy**: Forward all `/v1/*` OpenAI-compatible endpoints to llama-server
- **Security**: API key authentication and IP/CIDR-based access control
- **Real-time Monitoring**: Server-Sent Events (SSE) for live debugging and metrics
- **Production-Ready**: Comprehensive error handling, structured logging, graceful shutdown

### Architecture

```
┌──────────────┐
│ LAN Clients  │
│   (OpenAI)   │
└──────┬───────┘
       │ HTTP
       ▼
┌──────────────────────┐
│  Gateway (10.0.0.181:8001)  │
│  ├─ Admin API        │
│  ├─ Debug API        │
│  ├─ Security Layer   │
│  └─ Proxy /v1/*      │
└─────────┬────────────┘
          │ subprocess control
          ▼
┌──────────────────────┐
│ llama-server (local) │
│   (10.0.0.181:8080)  │
│   ├─ Model Loading   │
│   ├─ Inference       │
│   └─ OpenAI API      │
└──────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- llama-server binary (from llama.cpp) installed on the system
- Model files in GGUF format

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

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Configure your models**
   Edit `models/registry.json` to add your model configurations:
   ```json
   {
     "models": [
       {
         "model_id": "apertus-70b-q8",
         "name": "Apertus 70B Q8",
         "path": "models/path/to/model.gguf",
         "config": {
           "context_length": 8192,
           "n_gpu_layers": 999,
           "batch_size": 2048,
           "host": "10.0.0.181",
           "port": 8080,
           "flash_attention": true,
           "no_mmap": true
         }
       }
     ]
   }
   ```

6. **Run the gateway**
   ```bash
   uvicorn llama_gateway.main:app --host 10.0.0.181 --port 8001
   ```

## Configuration

### Environment Variables

Key settings in `.env`:

```bash
# Gateway settings
GATEWAY_HOST=10.0.0.181
GATEWAY_PORT=8001

# llama-server settings
LLAMA_SERVER_HOST=10.0.0.181
LLAMA_SERVER_PORT=8080
LLAMA_SERVER_BINARY=llama-server
MODEL_REGISTRY_PATH=models/registry.json

# Security (REQUIRED for production)
GATEWAY_API_KEY=your-secret-key-here
IP_ALLOWLIST=192.168.0.0/24,10.0.0.0/24

# Process management
STARTUP_TIMEOUT=120
SHUTDOWN_TIMEOUT=30
HEALTH_CHECK_INTERVAL=5

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

### Model Registry

The `models/registry.json` file stores model configurations:

```json
{
  "models": [
    {
      "model_id": "unique-model-id",
      "name": "Human-readable name",
      "description": "Model description",
      "path": "path/to/model.gguf",
      "config": {
        "context_length": 8192,
        "n_gpu_layers": 999,
        "batch_size": 2048,
        "host": "10.0.0.181",
        "port": 8080,
        "flash_attention": true,
        "no_mmap": true,
        "parallel": 1,
        "timeout": 600,
        "additional_args": []
      },
      "default_inference": {
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 0.95
      }
    }
  ]
}
```

## API Endpoints

### Admin API (`/admin`)

#### List Models
```bash
GET /admin/models
```
Returns all models in the registry.

#### Get Active Model
```bash
GET /admin/models/active
```
Returns currently loaded model information.

#### Load Model
```bash
POST /admin/models/load
Content-Type: application/json

{
  "model_id": "apertus-70b-q8"
}
```
Loads a model by ID. Stops current model if running.

#### Unload Model
```bash
POST /admin/models/unload
```
Stops the currently running llama-server.

#### Reload Model
```bash
POST /admin/models/reload
```
Restarts llama-server with the current model.

#### Register Model
```bash
POST /admin/models/register
Content-Type: application/json

{
  "model_id": "new-model",
  "name": "New Model",
  ...
}
```
Adds a new model to the registry.

#### Update Model
```bash
PUT /admin/models/{model_id}
```
Updates an existing model configuration.

#### Delete Model
```bash
DELETE /admin/models/{model_id}
```
Removes a model from the registry (must be unloaded first).

### Debug API (`/debug`)

#### Status
```bash
GET /debug/status
```
Returns current gateway and llama-server status.

#### Stream Events (SSE)
```bash
GET /debug/stream
```
Server-Sent Events stream for real-time monitoring.

#### Logs
```bash
GET /debug/logs?lines=50
```
Returns recent llama-server stdout/stderr logs.

#### Metrics
```bash
GET /debug/metrics
```
Proxies Prometheus metrics from llama-server.

#### Slots
```bash
GET /debug/slots
```
Returns llama-server slot information.

#### Props
```bash
GET /debug/props
```
Returns llama-server properties.

### Proxy API (`/v1/*`)

All OpenAI-compatible endpoints are transparently proxied:

- `POST /v1/chat/completions` - Chat completions
- `POST /v1/completions` - Text completions
- `POST /v1/embeddings` - Embeddings
- `GET /v1/models` - List models
- And all other `/v1/*` endpoints

### Health Check

```bash
GET /health
```
Returns gateway and llama-server health status.

## Usage Examples

### Load a Model

```bash
curl -X POST http://10.0.0.181:8001/admin/models/load \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{
    "model_id": "apertus-70b-q8"
  }'
```

### Chat Completion

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://10.0.0.181:8001/v1",
    api_key="your-secret-key"
)

response = client.chat.completions.create(
    model="apertus-70b-q8",  # Model name is informational
    messages=[
        {"role": "user", "content": "Hello! Tell me about quantum computing."}
    ]
)

print(response.choices[0].message.content)
```

### Monitor Debug Stream

```javascript
const eventSource = new EventSource('http://10.0.0.181:8001/debug/stream', {
  headers: { 'X-API-Key': 'your-secret-key' }
});

eventSource.addEventListener('connected', (event) => {
  console.log('Connected to debug stream');
});

eventSource.addEventListener('debug', (event) => {
  const data = JSON.parse(event.data);
  console.log('Debug event:', data);
});
```

### Check Status

```bash
curl -H "X-API-Key: your-secret-key" \
  http://10.0.0.181:8001/debug/status | jq
```

## Development

### Project Structure

```
llama-gateway/
├── src/
│   └── llama_gateway/
│       ├── __init__.py
│       ├── settings.py           # Configuration
│       ├── logging_config.py     # Logging setup
│       ├── middleware.py         # Security
│       ├── model_registry.py     # Model configs
│       ├── command_builder.py    # CLI generation
│       ├── process_manager.py    # Subprocess control
│       ├── admin_models.py       # Admin API
│       ├── proxy.py              # Proxy API
│       ├── debug.py              # Debug API
│       └── main.py               # FastAPI app
├── models/
│   └── registry.json             # Model definitions
├── logs/                         # Log files
├── tests/                        # Test suite
├── .env                          # Configuration
├── requirements.txt              # Dependencies
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=llama_gateway --cov-report=html
```

### Code Quality

```bash
# Format
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

## Security Considerations

1. **Always set `GATEWAY_API_KEY`** in production
2. **Use IP allow-listing** to restrict to known LAN subnets
3. **Never expose to public internet** - LAN only
4. **Rotate API keys regularly**
5. **Monitor logs** for unauthorized access attempts
6. **Keep dependencies updated**

## Troubleshooting

### llama-server won't start

- Verify `LLAMA_SERVER_BINARY` is correct and llama-server is in PATH
- Check model path in registry.json is correct
- Review logs in `logs/llama-server-stderr.log`
- Ensure GPU drivers are installed (for GPU inference)

### 503 Service Unavailable

- llama-server may still be starting (check `/debug/status`)
- Model loading can take 30-120 seconds depending on size
- Check llama-server logs for errors

### 401 Unauthorized

- Verify `X-API-Key` header matches `GATEWAY_API_KEY`
- Ensure `.env` file is loaded

### 403 Forbidden

- Check client IP is in `IP_ALLOWLIST`
- Verify CIDR notation (e.g., `192.168.0.0/24`)

## Process Management Details

### Model Loading Flow

1. Client sends `POST /admin/models/load` with `model_id`
2. Gateway looks up model in registry
3. If llama-server is running, gateway stops it gracefully
4. Gateway builds llama-server command from model config
5. Gateway starts llama-server as subprocess
6. Gateway monitors health endpoint until ready
7. Returns success when model is loaded and healthy

### Graceful Shutdown

1. Gateway sends SIGTERM to llama-server
2. Waits up to `SHUTDOWN_TIMEOUT` seconds
3. If still running, sends SIGKILL
4. Cleans up resources

### Health Monitoring

- Gateway continuously monitors llama-server `/health` endpoint
- Interval controlled by `HEALTH_CHECK_INTERVAL`
- Automatic error detection and status updates

## Performance Notes

- **Model switch time**: 30-60 seconds (full process restart)
- **One model at a time**: Cannot run multiple models simultaneously
- **Memory usage**: Full model loaded into RAM/VRAM on each load
- **Inference performance**: Native C++ llama-server performance

## Documentation

- [CLAUDE.md](CLAUDE.md) - AI assistant development guide
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [Interactive API Docs](http://10.0.0.181:8001/docs) - Swagger UI (when running)

## Project Status

- **Version**: 2.0.0
- **Status**: Production-ready
- **Python**: 3.11+
- **llama.cpp**: Compatible with latest llama-server

---

**Built with FastAPI, Pydantic, and llama.cpp**

**Designed for AMD Ryzen AI and other modern hardware**
