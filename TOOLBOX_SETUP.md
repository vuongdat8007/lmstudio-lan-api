# Running Gateway in AMD Strix Halo Toolbox

Based on the [AMD Strix Halo Toolboxes](https://github.com/kyuz0/amd-strix-halo-toolboxes) setup.

## Quick Setup

**On your AMD AI machine (10.0.0.181):**

### Step 1: Identify Your Toolbox

```bash
# List available toolboxes
toolbox list

# You should see:
# - llama-vulkan-radv (Vulkan-accelerated, recommended)
# - llama-rocm-7.1-rocwmma (ROCm-accelerated)
```

### Step 2: Enter the Toolbox with llama-server

```bash
# Enter the Vulkan toolbox (recommended - faster, more compatible)
toolbox enter llama-vulkan-radv

# Or enter the ROCm toolbox
toolbox enter llama-rocm-7.1-rocwmma
```

**Recommendation:** Use `llama-vulkan-radv` for better compatibility and performance.

### Step 3: Verify llama-server is Available

```bash
# Inside the toolbox, check llama-server
which llama-server
# Should show: /usr/local/bin/llama-server or similar

# Test it
llama-server --version
```

### Step 4: Navigate to Project Directory

```bash
# Your home directory is shared between host and toolbox
cd /home/boxwoodtech/lmstudio-lan-api
```

### Step 5: Install Python Dependencies (if needed)

```bash
# Check if dependencies are installed
python3 -m pip list | grep fastapi

# If not installed, install them:
pip install -r requirements.txt

# Or use the virtual environment:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 6: Update .env for Toolbox

Since llama-server is in the toolbox PATH, you can keep it simple:

```bash
# Edit .env
nano .env

# Keep it as:
LLAMA_SERVER_BINARY=llama-server

# Or use full path if needed:
# LLAMA_SERVER_BINARY=/usr/local/bin/llama-server
```

### Step 7: Stop Any External llama-server

```bash
# Inside toolbox, check for running llama-server
ps aux | grep llama-server

# If running, stop it
pkill llama-server
```

### Step 8: Start the Gateway

```bash
# Inside toolbox, start the gateway
./start_gateway.sh
```

The gateway will now run inside the toolbox and can access llama-server directly!

---

## Alternative: Run Gateway on Host with Toolbox Command

If you prefer to run the gateway on the host but execute llama-server inside the toolbox:

### On Host (outside toolbox)

```bash
# Edit .env
nano /home/boxwoodtech/lmstudio-lan-api/.env

# Change LLAMA_SERVER_BINARY to use toolbox run command:
LLAMA_SERVER_BINARY=toolbox run -c llama-vulkan-radv llama-server
# or
LLAMA_SERVER_BINARY=toolbox run -c llama-rocm-7.1-rocwmma llama-server
```

**Note:** This approach adds overhead but allows you to run the gateway on the host system.

---

## Testing the Setup

### Inside Toolbox (or from host)

```bash
# 1. Load a model
curl -X POST http://10.0.0.181:8002/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "apertus-8b-q8"}'

# 2. Wait 30-60 seconds for model to load, then test
curl -X POST http://10.0.0.181:8002/v1/chat/completions \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }' | jq
```

---

## Important Notes

### GPU Access
The toolbox is already configured with GPU access (Vulkan or ROCm). When llama-server runs inside the toolbox, it will automatically use GPU acceleration.

### Network Ports
Ports are shared between host and toolbox. The gateway listening on `10.0.0.181:8002` inside the toolbox is accessible from your LAN.

### File System
Your home directory (`/home/boxwoodtech/`) is shared between host and toolbox. Your models and project files are accessible from both.

### Persistent Sessions
To keep the gateway running even after you exit the toolbox terminal, use `screen` or `systemd`:

#### Option A: Using screen (simple)
```bash
# Inside toolbox
screen -S gateway
./start_gateway.sh

# Detach with: Ctrl+A, then D
# Reattach with: screen -r gateway
```

#### Option B: Using systemd (production)
```bash
# Create systemd service (as root on host)
sudo nano /etc/systemd/system/llama-gateway.service
```

```ini
[Unit]
Description=llama-server LAN Gateway
After=network.target

[Service]
Type=simple
User=boxwoodtech
WorkingDirectory=/home/boxwoodtech/lmstudio-lan-api
ExecStart=/usr/bin/toolbox run -c llama-vulkan-radv /home/boxwoodtech/lmstudio-lan-api/.venv/bin/uvicorn llama_gateway.main:app --host 10.0.0.181 --port 8002
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable llama-gateway
sudo systemctl start llama-gateway

# Check status
sudo systemctl status llama-gateway

# View logs
sudo journalctl -u llama-gateway -f
```

---

## Troubleshooting

### Gateway can't find llama-server
- Make sure you're inside the correct toolbox: `toolbox enter vulkan-toolbox`
- Verify llama-server exists: `which llama-server`
- Check PATH: `echo $PATH`

### Models not loading
- Verify model paths in `models/registry.json` are absolute or relative to project root
- Check GPU memory: `vulkaninfo` or `rocm-smi`
- Review logs: `curl -H "X-API-Key: change-me-please" http://10.0.0.181:8002/debug/logs?lines=50 | jq`

### Port already in use
- Check if another process is using port 8002: `ss -tulpn | grep 8002`
- Kill it: `pkill -f "port 8002"`

### Can't connect from another machine
- Check firewall on host (not inside toolbox):
  ```bash
  # On host
  sudo ufw status
  sudo ufw allow 8002/tcp
  ```

---

## Recommended Setup

**For simplicity and best performance:**

1. Run gateway **inside** the toolbox (llama-vulkan-radv or llama-rocm-7.1-rocwmma)
2. Use `screen` to keep it running
3. Access from LAN at `http://10.0.0.181:8002`

This ensures:
- ✅ Gateway can find llama-server
- ✅ Direct access to GPU drivers
- ✅ No overhead from toolbox wrapper commands
- ✅ Full compatibility with AMD Strix Halo setup

---

## Next Steps

1. Enter toolbox: `toolbox enter llama-vulkan-radv`
2. Navigate: `cd /home/boxwoodtech/lmstudio-lan-api`
3. Stop any external llama-server: `pkill llama-server`
4. Start gateway: `./start_gateway.sh`
5. Load model: Use curl command above
6. Test: Make a chat completion request

See [NEXT_STEPS.md](NEXT_STEPS.md) for model loading and testing instructions.
