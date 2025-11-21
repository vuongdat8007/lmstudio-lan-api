#!/bin/bash
# Script to create Ollama models from merged GGUF files
# Run this on the server in /home/boxwoodtech/models/modelfiles
#
# These models were created after merging split GGUF files using merge_split_models.sh
#
# Usage:
#   ./create_ollama_models_from_merged_models.sh                    # Create all models
#   ./create_ollama_models_from_merged_models.sh --verify-only      # Only verify files exist
#   ./create_ollama_models_from_merged_models.sh --help             # Show help

set -e

# Configuration
VERIFY_ONLY=false

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Create Ollama models from merged GGUF files."
            echo ""
            echo "Options:"
            echo "  --verify-only    Only verify merged files exist, don't create models"
            echo "  -h, --help       Show this help message"
            echo ""
            echo "Prerequisites:"
            echo "  - Run merge_split_models.sh first to create merged GGUF files"
            echo "  - Ensure Ollama is installed and running"
            echo "  - Run from the modelfiles directory"
            echo ""
            echo "Models created:"
            echo "  1. apertus-70b-q6k             (Apertus 70B Q6_K - bartowski)"
            echo "  2. apertus-70b-q8              (Apertus 70B Q8_0 - bartowski)"
            echo "  3. apertus-70b-q6kxl           (Apertus 70B Q6_K_XL - unsloth)"
            echo "  4. kimi-dev-72b-q6kxl          (Kimi-Dev 72B Q6_K_XL)"
            echo "  5. qwen3-30b-bf16              (Qwen3 30B BF16)"
            echo "  6. qwen3-coder-30b-1m-bf16     (Qwen3 Coder 30B 1M BF16)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Move to script directory (should be modelfiles/)
cd "$(dirname "$0")"

# Print header
echo "================================================"
echo "Ollama Model Creation from Merged GGUF Files"
echo "================================================"
echo ""

if [ "$VERIFY_ONLY" = true ]; then
    echo -e "${CYAN}Mode: VERIFICATION ONLY (no models will be created)${NC}"
else
    echo -e "${GREEN}Mode: Creating Ollama models${NC}"
fi
echo ""

# Base path for models (adjust if needed)
MODELS_BASE_PATH="/home/boxwoodtech/models"

# Define model configurations
# Format: "modelfile_name:gguf_relative_path:ollama_model_name:description"
MODELS=(
    "apertus-70b-q6k:bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K.gguf:apertus-70b-q6k:Apertus 70B Q6_K (bartowski)"
    "apertus-70b-q8:bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0.gguf:apertus-70b-q8:Apertus 70B Q8_0 (bartowski)"
    "apertus-70b-q6kxl:unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL.gguf:apertus-70b-q6kxl:Apertus 70B Q6_K_XL (unsloth)"
    "kimi-dev-72b-q6kxl:unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL.gguf:kimi-dev-72b-q6kxl:Kimi-Dev 72B Q6_K_XL"
    "qwen3-30b-bf16:unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16.gguf:qwen3-30b-bf16:Qwen3 30B BF16"
    "qwen3-coder-30b-1m-bf16:unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16.gguf:qwen3-coder-30b-1m-bf16:Qwen3 Coder 30B 1M BF16"
)

# Verification phase
echo -e "${CYAN}Step 1: Verifying merged GGUF files exist...${NC}"
echo ""

VERIFICATION_FAILED=false
for model_config in "${MODELS[@]}"; do
    IFS=':' read -r modelfile gguf_path model_name description <<< "$model_config"
    full_gguf_path="${MODELS_BASE_PATH}/${gguf_path}"

    # Check if Modelfile exists
    if [ ! -f "$modelfile" ]; then
        echo -e "${RED}✗ Modelfile missing: $modelfile${NC}"
        VERIFICATION_FAILED=true
    else
        echo -e "${GREEN}✓ Modelfile exists: $modelfile${NC}"
    fi

    # Check if merged GGUF file exists
    if [ ! -f "$full_gguf_path" ]; then
        echo -e "${RED}✗ GGUF file missing: $gguf_path${NC}"
        echo -e "${RED}  Run merge_split_models.sh first!${NC}"
        VERIFICATION_FAILED=true
    else
        # Get file size
        if command -v stat &> /dev/null; then
            file_size=$(stat -f%z "$full_gguf_path" 2>/dev/null || stat -c%s "$full_gguf_path" 2>/dev/null)
            file_size_gb=$(echo "scale=2; $file_size / 1024 / 1024 / 1024" | bc)
            echo -e "${GREEN}✓ GGUF exists: $gguf_path (${file_size_gb} GB)${NC}"
        else
            echo -e "${GREEN}✓ GGUF exists: $gguf_path${NC}"
        fi
    fi
    echo ""
done

if [ "$VERIFICATION_FAILED" = true ]; then
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}VERIFICATION FAILED!${NC}"
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}Some required files are missing.${NC}"
    echo -e "${YELLOW}Make sure you've run merge_split_models.sh first.${NC}"
    exit 1
fi

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✓ All files verified successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Exit if verify-only mode
if [ "$VERIFY_ONLY" = true ]; then
    echo -e "${CYAN}Verification complete. Run without --verify-only to create models.${NC}"
    exit 0
fi

# Model creation phase
echo -e "${CYAN}Step 2: Creating Ollama models...${NC}"
echo ""

# Check if ollama is available
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}ERROR: ollama command not found!${NC}"
    echo -e "${RED}Please install Ollama first: https://ollama.ai${NC}"
    exit 1
fi

# Create each model
COUNT=0
TOTAL=${#MODELS[@]}
SUCCESS_COUNT=0
FAILED_COUNT=0

for model_config in "${MODELS[@]}"; do
    COUNT=$((COUNT + 1))
    IFS=':' read -r modelfile gguf_path model_name description <<< "$model_config"

    echo -e "${CYAN}[$COUNT/$TOTAL] Creating: $model_name${NC}"
    echo -e "  Description: $description"
    echo -e "  Modelfile: $modelfile"
    echo -e "  GGUF: $gguf_path"

    # Create the model
    if ollama create "$model_name" -f "$modelfile"; then
        echo -e "${GREEN}✓ Successfully created: $model_name${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "${RED}✗ Failed to create: $model_name${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    echo ""
done

# Summary
echo "================================================"
echo "Model Creation Complete!"
echo "================================================"
echo ""
echo -e "${GREEN}Successfully created: $SUCCESS_COUNT models${NC}"
if [ $FAILED_COUNT -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED_COUNT models${NC}"
fi
echo ""

# List all Ollama models
echo "All Ollama models:"
ollama list
echo ""

echo -e "${CYAN}Models created from merged files:${NC}"
echo "  • apertus-70b-q6k          (54 GB)"
echo "  • apertus-70b-q8           (70 GB)"
echo "  • apertus-70b-q6kxl        (58 GB)"
echo "  • kimi-dev-72b-q6kxl       (63 GB)"
echo "  • qwen3-30b-bf16           (57 GB)"
echo "  • qwen3-coder-30b-1m-bf16  (57 GB)"
echo ""

if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
fi
