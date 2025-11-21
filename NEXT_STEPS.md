# Next Steps - Resolving 503 Errors

## Current Situation

✅ **Working:**
- Gateway is running on port 8002
- Gateway code is functional
- All tests passed
- Model registry updated with 5 models

❌ **Issues:**
- Gateway returning 503 errors: "llama-server is not running (status: stopped)"
- External llama-server is running on port 8080 (conflicts with gateway)
- Docker app at 10.0.0.102 getting 503 errors
- No model loaded through gateway admin API

## Root Cause

The gateway is designed to **manage llama-server as a subprocess**. It needs full control to:
- Start llama-server with specific models
- Stop/restart when switching models
- Monitor health and status

Your external llama-server running on port 8080 prevents the gateway from starting its own managed instance.

## Resolution Steps

### Step 1: Stop External llama-server

**On your AMD AI machine (10.0.0.181):**

```bash
# Find the running llama-server process
ps aux | grep llama-server

# Stop it
pkill llama-server

# Verify it's stopped
curl http://10.0.0.181:8080/health
# Should return: curl: (7) Failed to connect to 10.0.0.181 port 8080: Connection refused
```

### Step 2: Verify Gateway is Running

```bash
# Check gateway status
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8002/health | jq

# Expected output:
# {
#   "status": "ok",
#   "version": "2.0.0",
#   "llama_server": {
#     "status": "stopped",
#     "healthy": false
#   }
# }
```

### Step 3: Load a Model via Admin API

**Start with smaller model for testing (faster to load):**

```bash
curl -X POST http://10.0.0.181:8002/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "apertus-8b-q8"
  }'
```

**Or load your main Apertus 70B model:**

```bash
curl -X POST http://10.0.0.181:8002/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "apertus-70b-q4"
  }'
```

**Expected output:**
```json
{
  "status": "loaded",
  "model_id": "apertus-70b-q4",
  "message": "Model loaded successfully",
  "process_status": "running",
  "health_status": "healthy"
}
```

**Note:** Loading takes 30-120 seconds. The API waits for model to be ready.

### Step 4: Verify Model is Running

```bash
# Check active model
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8002/admin/models/active | jq

# Check llama-server health directly
curl http://10.0.0.181:8080/health
# Should now return: {"status": "ok", ...}
```

### Step 5: Test Chat Completion

```bash
curl -X POST http://10.0.0.181:8002/v1/chat/completions \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello! Please respond with just hi."}
    ],
    "max_tokens": 50
  }' | jq
```

**Expected output:**
```json
{
  "id": "chatcmpl-...",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Hi!"
      }
    }
  ],
  ...
}
```

### Step 6: Update Docker App Configuration

Your Docker app at 10.0.0.102 is requesting `llama-3.2-3b-instruct` model, but this model is not in your models/ folder.

**Option A: Use existing model**

Update your Docker app to use one of these available models:
- `apertus-8b-q8` - Similar size to 3B, fast inference
- `apertus-70b-q4` - Larger, higher quality
- `qwen2.5-coder-32b-q4` - If you need coding capabilities

**Option B: Download llama-3.2-3b-instruct**

```bash
cd /path/to/lmstudio-lan-api/models
# Download the model using your preferred method
# Then add it to models/registry.json
```

## Monitoring Model Loading

You can watch the loading progress in real-time:

```bash
# Terminal 1: Stream debug events
curl -N -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8002/debug/stream

# Terminal 2: Load model
curl -X POST http://10.0.0.181:8002/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "apertus-70b-q4"}'
```

## Updated Model Registry

I've updated `models/registry.json` with these models:

1. **apertus-70b-q4** - Main 70B model (Q4_K_L quantization)
2. **apertus-70b-q6** - Higher quality 70B (Q6_K)
3. **apertus-8b-q8** - Smaller, faster 8B model
4. **qwen2.5-coder-32b-q4** - Code generation specialist
5. **deepseek-r1-distill-qwen-32b-q4** - Advanced reasoning

**Key change:** Now using single-file versions (not split files) for better compatibility.

## Port Configuration

All documentation and scripts now use **port 8002** as you requested:
- ✅ [API_REFERENCE.md](API_REFERENCE.md) - Updated all examples
- ✅ [.env](.env) - GATEWAY_PORT=8002
- ✅ [start_gateway.sh](start_gateway.sh) - --port 8002

## Quick Reference Commands

```bash
# Stop external llama-server
pkill llama-server

# Load a model
curl -X POST http://10.0.0.181:8002/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "apertus-8b-q8"}'

# Check status
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8002/debug/status | jq

# Test chat
curl -X POST http://10.0.0.181:8002/v1/chat/completions \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hi"}]}' | jq
```

## Troubleshooting

### Still getting 503 errors after loading model?

1. Check gateway logs:
   ```bash
   # If running via start_gateway.sh, check terminal output
   # Or check debug logs:
   curl -H "X-API-Key: change-me-please" \
     "http://10.0.0.181:8002/debug/logs?lines=50" | jq
   ```

2. Check if llama-server process is running:
   ```bash
   ps aux | grep llama-server
   ```

3. Check llama-server health directly:
   ```bash
   curl http://10.0.0.181:8080/health
   ```

### Model loading takes too long?

- Large models (70B) can take 2+ minutes to load
- Use smaller model for testing: `apertus-8b-q8`
- Monitor loading: `curl -N http://10.0.0.181:8002/debug/stream`

### Model file not found?

- Verify path in `models/registry.json` matches actual file
- Check: `ls -lh models/bartowski/...`
- Ensure you're using single-file versions (not split -00001-of-00002)

## Summary

**Before:**
- External llama-server running independently on port 8080
- Gateway couldn't manage it
- No model loaded through gateway
- 503 errors

**After (once you follow steps above):**
- Gateway manages llama-server as subprocess
- Model loaded via admin API
- llama-server healthy and responding
- Docker app can make requests successfully

**Main action required:** Stop your external llama-server and load a model via the admin API.

---

For detailed API usage, see: [API_REFERENCE.md](API_REFERENCE.md)

For model loading guide, see: [LOADING_MODELS.md](LOADING_MODELS.md)
