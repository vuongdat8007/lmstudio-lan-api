#!/bin/bash
# Script to cleanup merged GGUF source files after Ollama models have been created
# Run this on the server in /home/boxwoodtech/models/modelfiles
#
# This script safely deletes the merged GGUF files that were already imported into Ollama
#
# Usage:
#   ./cleanup_merged_sources.sh                    # Delete source files (with confirmation)
#   ./cleanup_merged_sources.sh --dry-run          # Show what would be deleted
#   ./cleanup_merged_sources.sh --force            # Delete without confirmation
#   ./cleanup_merged_sources.sh --help             # Show help

set -e

# Configuration
DRY_RUN=false
FORCE=false

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Cleanup merged GGUF source files after Ollama models have been created."
            echo ""
            echo "Options:"
            echo "      --dry-run    Show what would be deleted without deleting"
            echo "      --force      Delete without confirmation prompt"
            echo "  -h, --help       Show this help message"
            echo ""
            echo "Safety features:"
            echo "  - Verifies each Ollama model exists before deleting its source"
            echo "  - Shows total space to be freed before proceeding"
            echo "  - Requires confirmation unless --force is used"
            echo "  - Skips any file if its Ollama model doesn't exist"
            echo ""
            echo "Files that will be deleted:"
            echo "  1. swiss-ai_Apertus-70B-Instruct-2509-Q6_K.gguf          (54 GB)"
            echo "  2. swiss-ai_Apertus-70B-Instruct-2509-Q8_0.gguf          (70 GB)"
            echo "  3. Apertus-70B-Instruct-2509-UD-Q6_K_XL.gguf             (58 GB)"
            echo "  4. Kimi-Dev-72B-UD-Q6_K_XL.gguf                          (63 GB)"
            echo "  5. Qwen3-30B-A3B-Instruct-2507-BF16.gguf                 (57 GB)"
            echo "  6. Qwen3-Coder-30B-A3B-Instruct-1M-BF16.gguf             (57 GB)"
            echo ""
            echo "Total space savings: ~360 GB"
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
echo "Cleanup Merged GGUF Source Files"
echo "================================================"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Mode: DRY RUN (simulation only - no files will be deleted)${NC}"
else
    echo -e "${YELLOW}Mode: DELETE source GGUF files${NC}"
    echo -e "${YELLOW}⚠️  This will free up ~360 GB of disk space${NC}"
fi
echo ""

# Base path for models (adjust if needed)
MODELS_BASE_PATH="/home/boxwoodtech/models"

# Helper function to get file size (cross-platform: macOS and Linux)
get_file_size() {
    local file="$1"
    # Try macOS stat first, fall back to Linux stat
    stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null
}

# Define source files to delete
# Format: "gguf_relative_path:ollama_model_name:description"
SOURCE_FILES=(
    "bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K.gguf:apertus-70b-q6k:Apertus 70B Q6_K (54 GB)"
    "bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0.gguf:apertus-70b-q8:Apertus 70B Q8_0 (70 GB)"
    "unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL.gguf:apertus-70b-q6kxl:Apertus 70B Q6_K_XL (58 GB)"
    "unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL.gguf:kimi-dev-72b-q6kxl:Kimi-Dev 72B (63 GB)"
    "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16.gguf:qwen3-30b-bf16:Qwen3 30B (57 GB)"
    "unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16.gguf:qwen3-coder-30b-1m-bf16:Qwen3 Coder 30B 1M (57 GB)"
)

# Step 1: Verify all Ollama models exist and all source files exist
echo -e "${CYAN}Step 1: Verifying Ollama models and source files...${NC}"
echo ""

VERIFICATION_FAILED=false
ESTIMATED_SPACE=0
FILES_TO_DELETE=()

for file_config in "${SOURCE_FILES[@]}"; do
    IFS=':' read -r gguf_path model_name description <<< "$file_config"
    full_gguf_path="${MODELS_BASE_PATH}/${gguf_path}"

    # Check if Ollama model exists (match with :latest or any tag)
    model_exists=false
    if ollama list | grep -q "^${model_name}:"; then
        echo -e "${GREEN}✓ Ollama model exists: $model_name${NC}"
        model_exists=true
    else
        echo -e "${YELLOW}⚠ Ollama model NOT found: $model_name${NC}"
        echo -e "${YELLOW}  Skipping this file (model was not created).${NC}"
    fi

    # Check if source file exists
    if [ ! -f "$full_gguf_path" ]; then
        echo -e "${YELLOW}⚠ Source file already deleted: $(basename "$gguf_path")${NC}"
    elif [ "$model_exists" = true ]; then
        # Only add to deletion list if both model exists AND file exists
        file_size=$(get_file_size "$full_gguf_path")
        file_size_gb=$(echo "scale=2; $file_size / 1024 / 1024 / 1024" | bc)
        echo -e "${CYAN}  Source file exists: $(basename "$gguf_path") (${file_size_gb} GB)${NC}"
        echo -e "${GREEN}  → Will be deleted${NC}"
        ESTIMATED_SPACE=$((ESTIMATED_SPACE + file_size))
        FILES_TO_DELETE+=("$full_gguf_path:$model_name:$description:$file_size")
    else
        # File exists but model doesn't - keep the file
        file_size=$(get_file_size "$full_gguf_path")
        file_size_gb=$(echo "scale=2; $file_size / 1024 / 1024 / 1024" | bc)
        echo -e "${CYAN}  Source file exists: $(basename "$gguf_path") (${file_size_gb} GB)${NC}"
        echo -e "${YELLOW}  → Keeping file (model not imported)${NC}"
    fi
    echo ""
done

# Note: We removed the VERIFICATION_FAILED check since we now gracefully skip files
# whose models don't exist, rather than failing entirely

if [ ${#FILES_TO_DELETE[@]} -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}All source files have already been deleted!${NC}"
    echo -e "${GREEN}================================================${NC}"
    exit 0
fi

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✓ Verification complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Show summary
estimated_space_gb=$(echo "scale=2; $ESTIMATED_SPACE / 1024 / 1024 / 1024" | bc)
echo -e "${CYAN}Files ready to delete: ${#FILES_TO_DELETE[@]}${NC}"
echo -e "${CYAN}Total space to free: ${estimated_space_gb} GB${NC}"
echo ""
echo -e "${YELLOW}Note: Only deleting files whose Ollama models were successfully created.${NC}"
echo -e "${YELLOW}Files for non-imported models will be kept safe.${NC}"
echo ""

# Step 2: Confirmation (unless --force or --dry-run)
if [ "$DRY_RUN" != true ] && [ "$FORCE" != true ]; then
    echo -e "${YELLOW}⚠️  WARNING: This will permanently delete ${#FILES_TO_DELETE[@]} GGUF files!${NC}"
    echo -e "${YELLOW}⚠️  Total space freed: ${estimated_space_gb} GB${NC}"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirmation
    echo ""

    if [ "$confirmation" != "yes" ]; then
        echo -e "${YELLOW}Deletion cancelled by user.${NC}"
        echo ""
        echo "To see what would be deleted, run:"
        echo "  $0 --dry-run"
        exit 0
    fi
fi

# Step 3: Delete files
echo -e "${CYAN}Step 2: Deleting source files...${NC}"
echo ""

COUNT=0
TOTAL=${#FILES_TO_DELETE[@]}
DELETED_COUNT=0
TOTAL_SPACE_FREED=0

for file_info in "${FILES_TO_DELETE[@]}"; do
    COUNT=$((COUNT + 1))
    IFS=':' read -r full_path model_name description file_size <<< "$file_info"
    file_size_gb=$(echo "scale=2; $file_size / 1024 / 1024 / 1024" | bc)

    echo -e "${CYAN}[$COUNT/$TOTAL] Processing: $(basename "$full_path")${NC}"
    echo -e "  Description: $description"
    echo -e "  Ollama model: $model_name"

    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${YELLOW}[DRY RUN] Would delete: $(basename "$full_path") (${file_size_gb} GB)${NC}"
        DELETED_COUNT=$((DELETED_COUNT + 1))
    else
        # Double-check model still exists (match with :latest or any tag)
        if ! ollama list | grep -q "^${model_name}:"; then
            echo -e "  ${RED}ERROR: Ollama model no longer found!${NC}"
            echo -e "  ${RED}Skipping deletion for safety.${NC}"
        else
            rm -f "$full_path"
            echo -e "  ${GREEN}✓ Deleted: $(basename "$full_path") (freed ${file_size_gb} GB)${NC}"
            DELETED_COUNT=$((DELETED_COUNT + 1))
            TOTAL_SPACE_FREED=$((TOTAL_SPACE_FREED + file_size))
        fi
    fi
    echo ""
done

# Summary
echo "================================================"
echo "Cleanup Complete!"
echo "================================================"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would have deleted: $DELETED_COUNT files${NC}"
    echo -e "${YELLOW}Estimated space savings: ${estimated_space_gb} GB${NC}"
    echo ""
    echo -e "${YELLOW}This was a DRY RUN - no files were deleted${NC}"
    echo -e "${YELLOW}To actually delete files, run with:${NC}"
    echo "  $0"
    echo "  or"
    echo "  $0 --force    # Skip confirmation"
else
    echo -e "${GREEN}Successfully deleted: $DELETED_COUNT files${NC}"
    if [ $TOTAL_SPACE_FREED -gt 0 ]; then
        space_freed_gb=$(echo "scale=2; $TOTAL_SPACE_FREED / 1024 / 1024 / 1024" | bc)
        echo -e "${GREEN}Total space freed: ${space_freed_gb} GB${NC}"
    fi
    echo ""
    echo -e "${GREEN}✓ All source GGUF files have been deleted!${NC}"
fi

echo ""
echo "Your Ollama models are still available:"
ollama list
