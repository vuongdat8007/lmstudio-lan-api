#!/bin/bash
# Script to find llama-server binary on your system

echo "================================================"
echo "Finding llama-server binary..."
echo "================================================"
echo ""

# Method 1: Check if it's in PATH
echo "Method 1: Checking PATH..."
if command -v llama-server &> /dev/null; then
    FOUND=$(which llama-server)
    echo "✅ Found in PATH: $FOUND"
    echo ""
else
    echo "❌ Not found in PATH"
    echo ""
fi

# Method 2: Check common installation locations
echo "Method 2: Checking common locations..."
COMMON_PATHS=(
    "/usr/local/bin/llama-server"
    "/usr/bin/llama-server"
    "$HOME/.local/bin/llama-server"
    "$HOME/bin/llama-server"
    "$HOME/llama.cpp/llama-server"
    "$HOME/llama.cpp/build/bin/llama-server"
    "/opt/llama.cpp/llama-server"
)

for path in "${COMMON_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo "✅ Found: $path"
        ls -lh "$path"
    fi
done
echo ""

# Method 3: Search in home directory (slow)
echo "Method 3: Searching in home directory (this may take a moment)..."
find ~ -name "llama-server" -type f 2>/dev/null | head -5
echo ""

# Method 4: Check if there's a running process
echo "Method 4: Checking for running llama-server process..."
ps aux | grep -v grep | grep llama-server
echo ""

echo "================================================"
echo "Instructions:"
echo "================================================"
echo "1. Copy the full path to llama-server (e.g., /usr/local/bin/llama-server)"
echo "2. Update .env file:"
echo "   LLAMA_SERVER_BINARY=/full/path/to/llama-server"
echo "3. Restart the gateway: ./start_gateway.sh"
echo ""
echo "If llama-server is not installed, install llama.cpp:"
echo "   git clone https://github.com/ggerganov/llama.cpp.git"
echo "   cd llama.cpp"
echo "   make LLAMA_VULKAN=1  # For Vulkan support"
echo "   # or"
echo "   make LLAMA_HIPBLAS=1 AMDGPU_TARGETS=gfx1100  # For ROCm support"
echo ""
