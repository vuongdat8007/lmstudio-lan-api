# API Quick Reference

API Key: `change-me-please`
Gateway: `http://10.0.0.181:8001`

---

## 🚀 Quick Start

### 1. Start the Gateway
```bash
./start_gateway.sh
```

### 2. Test Connection
```bash
curl -H "X-API-Key: change-me-please" http://10.0.0.181:8001/health
```

---

## 📋 Admin API

### List All Models
```bash
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8001/admin/models | jq
```

### Get Active Model
```bash
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8001/admin/models/active | jq
```

### Load Model (Apertus-70B)
```bash
curl -X POST http://10.0.0.181:8001/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "apertus-70b-q8"}'
```

### Unload Model
```bash
curl -X POST http://10.0.0.181:8001/admin/models/unload \
  -H "X-API-Key: change-me-please"
```

### Reload Model
```bash
curl -X POST http://10.0.0.181:8001/admin/models/reload \
  -H "X-API-Key: change-me-please"
```

---

## 🔍 Debug API

### Check Status
```bash
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8001/debug/status | jq
```

### View Logs (Last 50 Lines)
```bash
curl -H "X-API-Key: change-me-please" \
  "http://10.0.0.181:8001/debug/logs?lines=50" | jq
```

### Get Metrics (Prometheus)
```bash
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8001/debug/metrics
```

### Get Slots Info
```bash
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8001/debug/slots | jq
```

### Get Server Properties
```bash
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8001/debug/props | jq
```

### Stream Debug Events (SSE)
```bash
curl -N -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8001/debug/stream
```

---

## 💬 OpenAI-Compatible API

### Chat Completion
```bash
curl -X POST http://10.0.0.181:8001/v1/chat/completions \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello! Tell me about quantum computing."}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }' | jq
```

### Chat Completion (Streaming)
```bash
curl -N -X POST http://10.0.0.181:8001/v1/chat/completions \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a haiku about AI."}
    ],
    "stream": true
  }'
```

### List Models (OpenAI Format)
```bash
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8001/v1/models | jq
```

---

## 🐍 Python Usage

### Using OpenAI SDK
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://10.0.0.181:8001/v1",
    api_key="change-me-please"
)

# Chat completion
response = client.chat.completions.create(
    model="apertus-70b-q8",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(response.choices[0].message.content)
```

### Using Requests
```python
import requests

headers = {
    "X-API-Key": "change-me-please",
    "Content-Type": "application/json"
}

# Load model
response = requests.post(
    "http://10.0.0.181:8001/admin/models/load",
    headers=headers,
    json={"model_id": "apertus-70b-q8"}
)

print(response.json())

# Chat
response = requests.post(
    "http://10.0.0.181:8001/v1/chat/completions",
    headers=headers,
    json={
        "messages": [{"role": "user", "content": "Hello!"}],
        "max_tokens": 100
    }
)

print(response.json()["choices"][0]["message"]["content"])
```

---

## 🌐 JavaScript Usage

### Using Fetch API
```javascript
const API_KEY = "change-me-please";
const BASE_URL = "http://10.0.0.181:8001";

// Load model
async function loadModel() {
  const response = await fetch(`${BASE_URL}/admin/models/load`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ model_id: "apertus-70b-q8" })
  });

  return await response.json();
}

// Chat completion
async function chat(message) {
  const response = await fetch(`${BASE_URL}/v1/chat/completions`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      messages: [{ role: "user", content: message }],
      max_tokens: 200
    })
  });

  const data = await response.json();
  return data.choices[0].message.content;
}

// Usage
loadModel().then(() => {
  chat("Hello!").then(console.log);
});
```

### Using EventSource (SSE Streaming)
```javascript
const eventSource = new EventSource(
  'http://10.0.0.181:8001/debug/stream',
  { headers: { 'X-API-Key': 'change-me-please' } }
);

eventSource.addEventListener('connected', (event) => {
  console.log('Connected:', JSON.parse(event.data));
});

eventSource.addEventListener('debug', (event) => {
  console.log('Debug event:', JSON.parse(event.data));
});

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
};
```

---

## 🔧 Common Workflows

### Workflow 1: Start Fresh
```bash
# 1. Start gateway
./start_gateway.sh

# 2. In another terminal, load model
curl -X POST http://10.0.0.181:8001/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "apertus-70b-q8"}'

# 3. Wait for model to load (check status)
curl -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8001/debug/status | jq .llama_server.status

# 4. Make a request
curl -X POST http://10.0.0.181:8001/v1/chat/completions \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hi!"}]}' | jq
```

### Workflow 2: Monitor Model Loading
```bash
# Terminal 1: Stream debug events
curl -N -H "X-API-Key: change-me-please" \
  http://10.0.0.181:8001/debug/stream

# Terminal 2: Load model
curl -X POST http://10.0.0.181:8001/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "apertus-70b-q8"}'

# Watch the loading progress in Terminal 1!
```

### Workflow 3: Check llama-server Logs
```bash
# View recent logs
curl -H "X-API-Key: change-me-please" \
  "http://10.0.0.181:8001/debug/logs?lines=100" | jq

# Or check log files directly
tail -f logs/llama-server-stdout.log
tail -f logs/llama-server-stderr.log
```

---

## 📚 Interactive Documentation

Open in browser:
- **Swagger UI**: http://10.0.0.181:8001/docs
- **ReDoc**: http://10.0.0.181:8001/redoc

---

## ⚠️ Security Note

**API Key**: `change-me-please`

⚠️ This is a **development** API key. For production:
1. Generate a strong random key: `openssl rand -hex 32`
2. Update in `.env`: `GATEWAY_API_KEY=<your-strong-key>`
3. Restart the gateway

**IP Allowlist**: Currently allows `192.168.0.0/24` and `10.0.0.0/24`

To restrict to specific IPs, update in `.env`:
```bash
IP_ALLOWLIST=10.0.0.100,10.0.0.101
```

---

## 🆘 Troubleshooting

### Gateway won't start
```bash
# Check Python version (needs 3.11+)
python --version

# Check dependencies
pip install -r requirements.txt

# Check if port is available
lsof -i :8001
```

### Model won't load
```bash
# Check llama-server is in PATH
which llama-server

# Check model file exists
ls -lh models/bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/

# Check logs
curl -H "X-API-Key: change-me-please" \
  "http://10.0.0.181:8001/debug/logs?lines=50" | jq .stderr
```

### Can't connect from another machine
```bash
# Check gateway is listening on correct interface
netstat -an | grep 8001

# Check firewall (Ubuntu)
sudo ufw status
sudo ufw allow 8001/tcp

# Test connectivity
ping 10.0.0.181
telnet 10.0.0.181 8001
```

---

**Gateway Version**: 2.0.0
**Documentation**: See [README.md](README.md)
**Development**: See [CLAUDE.md](CLAUDE.md)
