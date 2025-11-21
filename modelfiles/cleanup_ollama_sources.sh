#!/bin/bash
# cleanup_ollama_sources.sh
# Safely delete source GGUF files after successful Ollama import
#
# IMPORTANT: Run this script on the server where Ollama is running
# Default mode: DRY RUN (shows what would be deleted, but doesn't delete)
# To actually delete files, use: ./cleanup_ollama_sources.sh --execute
#
# This script will:
# 1. Verify each Ollama model exists before attempting deletion
# 2. Show file sizes and calculate total space savings
# 3. Only delete source files for successfully imported models
# 4. Keep source files for models that failed to import

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default mode: dry run
DRY_RUN=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --execute)
            DRY_RUN=false
            shift
            ;;
        --help)
            echo "Usage: $0 [--execute]"
            echo ""
            echo "Options:"
            echo "  --execute    Actually delete files (default: dry-run)"
            echo "  --help       Show this help message"
            echo ""
            echo "Default behavior is DRY RUN - shows what would be deleted without deleting."
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "================================================"
echo "Ollama Source Files Cleanup Script"
echo "================================================"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}MODE: DRY RUN (simulation only)${NC}"
    echo -e "${YELLOW}No files will be deleted. Use --execute to actually delete.${NC}"
else
    echo -e "${RED}MODE: EXECUTION (will delete files!)${NC}"
fi

echo ""

# Check if ollama command exists
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}ERROR: 'ollama' command not found${NC}"
    echo "Please ensure Ollama is installed and in your PATH"
    exit 1
fi

echo "================================================"
echo "Step 1: Verifying Ollama models exist..."
echo "================================================"
echo ""

# Model mappings: Ollama model name -> source GGUF file path
declare -A MODEL_MAPPINGS=(
    ["qwen3-30b-q8:latest"]="/home/boxwoodtech/models/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-Q8_0.gguf"
    ["apertus-8b-q2kxl:latest"]="/home/boxwoodtech/models/unsloth/Apertus-8B-Instruct-2509-GGUF/Apertus-8B-Instruct-2509-UD-Q2_K_XL.gguf"
    ["apertus-8b-bf16-unsloth:latest"]="/home/boxwoodtech/models/unsloth/Apertus-8B-Instruct-2509-GGUF/Apertus-8B-Instruct-2509-BF16.gguf"
    ["deepseek-r1-1.5b-q8:latest"]="/home/boxwoodtech/models/mradermacher/DeepSeek-R1-Distill-Qwen-1.5B-GRPO-SpeculativeReasoner-GGUF/DeepSeek-R1-Distill-Qwen-1.5B-GRPO-SpeculativeReasoner.Q8_0.gguf"
    ["qwen3-coder-30b-q8:latest"]="/home/boxwoodtech/models/lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-GGUF/Qwen3-Coder-30B-A3B-Instruct-Q8_0.gguf"
    ["apertus-70b-q4km:latest"]="/home/boxwoodtech/models/giladgd/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509.Q4_K_M.gguf"
    ["apertus-8b-bf16:latest"]="/home/boxwoodtech/models/bartowski/swiss-ai_Apertus-8B-Instruct-2509-GGUF/swiss-ai_Apertus-8B-Instruct-2509-bf16.gguf"
    ["apertus-70b-q4kl:latest"]="/home/boxwoodtech/models/bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q4_K_L.gguf"
    ["qwen2-1.5b-function-calling:latest"]="/home/boxwoodtech/models/alexwirrell/Qwen2-1.5B-Instruct-Function-Calling-v1-Q4_K_M-GGUF/qwen2-1.5b-instruct-function-calling-v1-q4_k_m.gguf"
)

# Arrays to track results
declare -a VERIFIED_MODELS=()
declare -a VERIFIED_FILES=()
declare -a MISSING_MODELS=()
declare -a MISSING_FILES=()

# Verify each model and its source file
for model_name in "${!MODEL_MAPPINGS[@]}"; do
    source_file="${MODEL_MAPPINGS[$model_name]}"

    # Check if Ollama model exists
    if ollama list | grep -q "^${model_name}"; then
        # Check if source file exists
        if [ -f "$source_file" ]; then
            file_size=$(du -h "$source_file" | cut -f1)
            echo -e "${GREEN}✓${NC} ${CYAN}$model_name${NC}"
            echo -e "  Source: $source_file (${file_size})"
            VERIFIED_MODELS+=("$model_name")
            VERIFIED_FILES+=("$source_file")
        else
            echo -e "${YELLOW}⚠${NC} ${CYAN}$model_name${NC} - Ollama model exists"
            echo -e "  ${YELLOW}Source file NOT FOUND:${NC} $source_file"
            MISSING_FILES+=("$source_file")
        fi
    else
        echo -e "${RED}✗${NC} ${CYAN}$model_name${NC} - NOT FOUND in Ollama"
        echo -e "  ${RED}Keeping source file:${NC} $source_file"
        MISSING_MODELS+=("$model_name")
    fi
    echo ""
done

echo "================================================"
echo "Verification Summary"
echo "================================================"
echo ""
echo -e "${GREEN}Models verified:${NC} ${#VERIFIED_MODELS[@]}"
echo -e "${RED}Models missing:${NC} ${#MISSING_MODELS[@]}"
echo -e "${YELLOW}Source files missing:${NC} ${#MISSING_FILES[@]}"
echo ""

# If any models are missing, warn and optionally abort
if [ ${#MISSING_MODELS[@]} -gt 0 ]; then
    echo -e "${YELLOW}WARNING: The following models are missing from Ollama:${NC}"
    for model in "${MISSING_MODELS[@]}"; do
        echo -e "  - $model"
    done
    echo ""
    echo -e "${YELLOW}Their source files will NOT be deleted.${NC}"
    echo ""
fi

# If no verified models, exit
if [ ${#VERIFIED_MODELS[@]} -eq 0 ]; then
    echo -e "${RED}ERROR: No verified models found. Nothing to delete.${NC}"
    exit 1
fi

echo "================================================"
echo "Step 2: Calculating space to be freed..."
echo "================================================"
echo ""

# Calculate total size
TOTAL_BYTES=0
for file in "${VERIFIED_FILES[@]}"; do
    file_bytes=$(du -b "$file" | cut -f1)
    file_size=$(du -h "$file" | cut -f1)
    TOTAL_BYTES=$((TOTAL_BYTES + file_bytes))
    echo "  $(basename "$file"): $file_size"
done

# Convert total bytes to human-readable format
TOTAL_SIZE_GB=$(echo "scale=2; $TOTAL_BYTES / 1024 / 1024 / 1024" | bc)

echo ""
echo -e "${GREEN}Total space to be freed: ${TOTAL_SIZE_GB} GB${NC}"
echo ""

# Show disk usage before
echo "Current disk usage:"
df -h /home/boxwoodtech/models/ | grep -v Filesystem
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "================================================"
    echo "DRY RUN - Files that WOULD be deleted:"
    echo "================================================"
    echo ""
    for i in "${!VERIFIED_MODELS[@]}"; do
        model="${VERIFIED_MODELS[$i]}"
        file="${VERIFIED_FILES[$i]}"
        file_size=$(du -h "$file" | cut -f1)
        echo -e "${CYAN}$model${NC}"
        echo -e "  Would delete: $file (${file_size})"
        echo ""
    done
    echo "================================================"
    echo -e "${YELLOW}This was a DRY RUN - no files were deleted${NC}"
    echo -e "${YELLOW}To actually delete files, run with: $0 --execute${NC}"
    echo "================================================"
    exit 0
fi

# Real execution mode - ask for confirmation
echo "================================================"
echo -e "${RED}READY TO DELETE FILES${NC}"
echo "================================================"
echo ""
echo "This will permanently delete ${#VERIFIED_FILES[@]} source GGUF files"
echo "and free approximately ${TOTAL_SIZE_GB} GB of disk space."
echo ""
echo -e "${RED}This action CANNOT be undone!${NC}"
echo ""
echo -e "${YELLOW}Type 'DELETE' (in uppercase) to confirm, or Ctrl+C to cancel:${NC}"
read -r confirmation

if [ "$confirmation" != "DELETE" ]; then
    echo ""
    echo -e "${YELLOW}Deletion cancelled.${NC}"
    exit 0
fi

echo ""
echo "================================================"
echo "Step 3: Deleting source files..."
echo "================================================"
echo ""

# Create log file
LOG_FILE="/tmp/ollama_cleanup_$(date +%Y%m%d_%H%M%S).log"
echo "Logging operations to: $LOG_FILE"
echo ""

# Log header
{
    echo "Ollama Source Files Cleanup Log"
    echo "Started: $(date)"
    echo "User: $(whoami)"
    echo "Host: $(hostname)"
    echo ""
    echo "Files deleted:"
    echo "=============="
} > "$LOG_FILE"

# Delete each file
DELETED_COUNT=0
FAILED_COUNT=0

for i in "${!VERIFIED_MODELS[@]}"; do
    model="${VERIFIED_MODELS[$i]}"
    file="${VERIFIED_FILES[$i]}"
    file_size=$(du -h "$file" | cut -f1)

    echo -e "${CYAN}Deleting source for: $model${NC}"
    echo "  File: $file (${file_size})"

    if rm -v "$file" 2>&1 | tee -a "$LOG_FILE"; then
        echo -e "  ${GREEN}✓ Deleted successfully${NC}"
        DELETED_COUNT=$((DELETED_COUNT + 1))
    else
        echo -e "  ${RED}✗ Failed to delete${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    echo ""
done

# Log footer
{
    echo ""
    echo "Summary:"
    echo "========"
    echo "Files deleted: $DELETED_COUNT"
    echo "Files failed: $FAILED_COUNT"
    echo "Total space freed: ${TOTAL_SIZE_GB} GB"
    echo ""
    echo "Completed: $(date)"
} >> "$LOG_FILE"

echo "================================================"
echo "Cleanup Complete!"
echo "================================================"
echo ""
echo -e "${GREEN}Successfully deleted: $DELETED_COUNT files${NC}"
if [ $FAILED_COUNT -gt 0 ]; then
    echo -e "${RED}Failed to delete: $FAILED_COUNT files${NC}"
fi
echo -e "${GREEN}Space freed: ${TOTAL_SIZE_GB} GB${NC}"
echo ""

# Show disk usage after
echo "Disk usage after cleanup:"
df -h /home/boxwoodtech/models/ | grep -v Filesystem
echo ""

echo "================================================"
echo "Log saved to: $LOG_FILE"
echo "================================================"
echo ""

# Show models still in Ollama
echo "Ollama models (should still be available):"
echo "==========================================="
ollama list | grep -E "$(IFS=\|; echo "${VERIFIED_MODELS[*]}")" || echo "No matching models found (this might be normal)"
echo ""

echo -e "${GREEN}Done! Your Ollama models are still available and working.${NC}"
echo -e "${GREEN}Only the source GGUF files have been deleted.${NC}"
echo ""
