# Loading Models - Quick Guide

## ⚠️ IMPORTANT: Stop External llama-server First

Before using the gateway, you **MUST** stop your existing llama-server running on port 8080:

```bash
# Find and stop the llama-server process
pkill llama-server

# Or find the PID and kill it
ps aux | grep llama-server
kill <PID>

# Verify it's stopped
curl http://10.0.0.181:8080/health
# Should get connection refused
```

**Why?** The gateway is designed to manage llama-server as a subprocess. It needs full control to start/stop/restart the process. Your external llama-server is blocking this.

---

## Available Models

After updating `models/registry.json`, you have these models available:

1. **apertus-70b-q4** - Apertus 70B Q4 (balanced quality/speed)
2. **apertus-70b-q6** - Apertus 70B Q6 (higher quality)
3. **apertus-8b-q8** - Apertus 8B Q8 (faster, smaller)
4. **qwen2.5-coder-32b-q4** - Qwen Coder 32B (code specialist)
5. **deepseek-r1-distill-qwen-32b-q4** - DeepSeek R1 32B (reasoning)

---

## Loading a Model via Admin API

### 1. List Available Models

```bash
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8002/admin/models | jq
```

Response:
```json
{
  "models": [
    {
      "model_id": "apertus-70b-q4",
      "name": "Apertus 70B Instruct Q4",
      ...
    },
    ...
  ]
}
```

### 2. Load a Model

**Example: Load Apertus 8B (fastest to load for testing)**

```bash
curl -X POST http://10.0.0.181:8002/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "apertus-8b-q8"
  }'
```

**Example: Load Apertus 70B Q4 (your main model)**

```bash
curl -X POST http://10.0.0.181:8002/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "apertus-70b-q4"
  }'
```

Expected response:
```json
{
  "status": "loaded",
  "model_id": "apertus-70b-q4",
  "message": "Model loaded successfully",
  "process_status": "running",
  "health_status": "healthy"
}
```

**Note:** Model loading takes 30-120 seconds depending on size. The API will wait for the model to be fully loaded and healthy before returning.

### 3. Check Model Status

```bash
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8002/admin/models/active | jq
```

Response:
```json
{
  "model_id": "apertus-70b-q4",
  "name": "Apertus 70B Instruct Q4",
  "status": "running",
  "loaded_at": "2025-11-20T10:30:00Z"
}
```

### 4. Check Gateway Status

```bash
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8002/debug/status | jq
```

---

## Using the Loaded Model

Once a model is loaded, you can use it via OpenAI-compatible endpoints:

### Chat Completion

```bash
curl -X POST http://10.0.0.181:8002/v1/chat/completions \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello! Tell me about yourself."}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }' | jq
```

### Python Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://10.0.0.181:8002/v1",
    api_key="change-me-please"
)

response = client.chat.completions.create(
    model="apertus-70b-q4",  # Model name is informational
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

---

## Switching Models

To switch to a different model:

1. **Unload current model:**
   ```bash
   curl -X POST http://10.0.0.181:8002/admin/models/unload \
     -H "X-API-Key: change-me-please"
   ```

2. **Load new model:**
   ```bash
   curl -X POST http://10.0.0.181:8002/admin/models/load \
     -H "X-API-Key: change-me-please" \
     -H "Content-Type: application/json" \
     -d '{"model_id": "qwen2.5-coder-32b-q4"}'
   ```

Or just load the new model directly - the gateway will automatically unload the current model first.

---

## Troubleshooting

### 503 Service Unavailable

**Cause:** No model loaded, or llama-server not running

**Solution:**
1. Check if external llama-server is still running (kill it!)
2. Load a model via admin API (see above)
3. Check logs: `curl -H "X-API-Key: change-me-please" http://10.0.0.181:8002/debug/logs?lines=50 | jq`

### Model Load Timeout

**Cause:** Large models take time to load (70B can take 2+ minutes)

**Solution:**
- Use smaller model for testing (apertus-8b-q8)
- Monitor loading: `curl -N -H "X-API-Key: change-me-please" http://10.0.0.181:8002/debug/stream`
- Check GPU memory: `rocm-smi` or `vulkaninfo`

### Model Not Found

**Cause:** Model file doesn't exist at specified path

**Solution:**
- Verify path in `models/registry.json`
- Check file exists: `ls -lh models/bartowski/...`
- Use absolute path if needed

---

## About llama-3.2-3b-instruct

Your Docker app is requesting this model, but it's not in your models/ folder. You have two options:

1. **Download it:**
   ```bash
   cd models
   # Use lmstudio-download or huggingface-cli to get the model
   ```

2. **Update your Docker app** to use one of the available models:
   - `apertus-8b-q8` (similar size, fast inference)
   - `qwen2.5-coder-32b-q4` (if you need coding capabilities)

---

## Next Steps

1. ✅ Stop external llama-server: `pkill llama-server`
2. ✅ Restart gateway: `./start_gateway.sh` (if needed)
3. ✅ Load a model: Use curl command above
4. ✅ Test it: Make a chat completion request
5. ✅ Update Docker app to use correct model name
