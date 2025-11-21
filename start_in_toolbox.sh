#!/bin/bash
# Quick start script for running gateway in AMD Strix Halo toolbox

set -e

echo "========================================"
echo "llama-server LAN Gateway - Toolbox Setup"
echo "========================================"
echo ""

# Detect available toolboxes
HAS_VULKAN=false
HAS_ROCM=false
VULKAN_NAME=""
ROCM_NAME=""

if toolbox list 2>/dev/null | grep -q "llama-vulkan-radv"; then
    HAS_VULKAN=true
    VULKAN_NAME="llama-vulkan-radv"
fi

if toolbox list 2>/dev/null | grep -q "llama-rocm"; then
    HAS_ROCM=true
    ROCM_NAME=$(toolbox list | grep llama-rocm | awk '{print $2}')
fi

# Check if any toolbox is available
if [[ "$HAS_VULKAN" == false ]] && [[ "$HAS_ROCM" == false ]]; then
    echo "❌ No AMD Strix Halo toolbox found!"
    echo ""
    echo "Available toolboxes:"
    toolbox list
    echo ""
    echo "Please set up AMD Strix Halo toolboxes first:"
    echo "https://github.com/kyuz0/amd-strix-halo-toolboxes"
    exit 1
fi

# Choose toolbox
TOOLBOX=""

# Check if user provided choice via command line
if [[ "$1" == "vulkan" ]] || [[ "$1" == "rocm" ]]; then
    if [[ "$1" == "vulkan" ]] && [[ "$HAS_VULKAN" == true ]]; then
        TOOLBOX="$VULKAN_NAME"
        echo "✅ Using Vulkan toolbox: $TOOLBOX"
    elif [[ "$1" == "rocm" ]] && [[ "$HAS_ROCM" == true ]]; then
        TOOLBOX="$ROCM_NAME"
        echo "✅ Using ROCm toolbox: $TOOLBOX"
    else
        echo "❌ Requested toolbox '$1' not available"
        exit 1
    fi
elif [[ "$HAS_VULKAN" == true ]] && [[ "$HAS_ROCM" == true ]]; then
    # Both available, let user choose
    echo "📦 Available toolboxes:"
    echo ""
    echo "  1) $VULKAN_NAME (Vulkan - recommended)"
    echo "     - Faster inference"
    echo "     - Better compatibility"
    echo "     - Lower VRAM usage"
    echo ""
    echo "  2) $ROCM_NAME (ROCm)"
    echo "     - Native AMD compute"
    echo "     - Full GPU features"
    echo ""
    echo -n "Choose toolbox (1 or 2) [1]: "
    read choice

    case "${choice:-1}" in
        1)
            TOOLBOX="$VULKAN_NAME"
            echo "✅ Selected: Vulkan toolbox"
            ;;
        2)
            TOOLBOX="$ROCM_NAME"
            echo "✅ Selected: ROCm toolbox"
            ;;
        *)
            echo "❌ Invalid choice, using Vulkan (default)"
            TOOLBOX="$VULKAN_NAME"
            ;;
    esac
elif [[ "$HAS_VULKAN" == true ]]; then
    TOOLBOX="$VULKAN_NAME"
    echo "✅ Using Vulkan toolbox: $TOOLBOX"
else
    TOOLBOX="$ROCM_NAME"
    echo "✅ Using ROCm toolbox: $TOOLBOX"
fi

echo ""
echo "This will:"
echo "  1. Enter $TOOLBOX"
echo "  2. Stop any running llama-server"
echo "  3. Start the gateway on 10.0.0.181:8002"
echo ""
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Enter toolbox and run commands
toolbox run -c "$TOOLBOX" bash -c "
    echo '========================================'
    echo 'Inside $TOOLBOX'
    echo '========================================'
    echo ''

    # Check llama-server
    if ! command -v llama-server &> /dev/null; then
        echo '❌ llama-server not found in $TOOLBOX!'
        exit 1
    fi

    echo '✅ llama-server found:' \$(which llama-server)
    echo ''

    # Stop any running llama-server
    echo 'Stopping any running llama-server...'
    pkill llama-server 2>/dev/null || true
    sleep 2
    echo ''

    # Navigate to project
    cd /home/boxwoodtech/lmstudio-lan-api

    # Check Python dependencies
    if ! python3 -c 'import fastapi' 2>/dev/null; then
        echo '⚠️  Installing Python dependencies in toolbox...'
        # Install in toolbox-specific venv
        if [ -f .venv-toolbox/bin/activate ]; then
            source .venv-toolbox/bin/activate
            pip install -r requirements.txt
        else
            python3 -m venv .venv-toolbox
            source .venv-toolbox/bin/activate
            pip install -r requirements.txt
        fi
        echo ''
    fi

    # Activate toolbox venv if exists
    if [ -f .venv-toolbox/bin/activate ]; then
        source .venv-toolbox/bin/activate
    fi

    # Set PYTHONPATH
    export PYTHONPATH=\$(pwd)/src:\$PYTHONPATH

    echo '========================================'
    echo 'Starting Gateway'
    echo '========================================'
    echo ''
    echo 'Gateway URL: http://10.0.0.181:8002'
    echo 'API Key: change-me-please'
    echo ''
    echo 'To load a model:'
    echo '  curl -X POST http://10.0.0.181:8002/admin/models/load \\'
    echo '    -H \"X-API-Key: change-me-please\" \\'
    echo '    -H \"Content-Type: application/json\" \\'
    echo '    -d {\\\"model_id\\\": \\\"apertus-8b-q8\\\"}'
    echo ''
    echo 'Press Ctrl+C to stop'
    echo '========================================'
    echo ''

    # Start the server
    uvicorn llama_gateway.main:app \
        --host 10.0.0.181 \
        --port 8002 \
        --log-level info
"
