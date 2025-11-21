#!/bin/bash
# Script to merge split GGUF files with optional auto-cleanup
# Run this on the server in /home/boxwoodtech/models
#
# Usage:
#   ./merge_split_models.sh                     # Merge only, keep split files (safe mode)
#   ./merge_split_models.sh --delete-sources    # Merge and delete split files after verification
#   ./merge_split_models.sh -d --dry-run        # Test what would be deleted
#   ./merge_split_models.sh --help              # Show help

set -e

# Configuration
DELETE_SOURCES=false
DRY_RUN=false

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--delete-sources)
            DELETE_SOURCES=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Merge split GGUF model files and optionally delete source files."
            echo ""
            echo "Options:"
            echo "  -d, --delete-sources    Delete split files after successful merge"
            echo "      --dry-run           Show what would be deleted without deleting"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                      # Safe mode: merge only, keep split files"
            echo "  $0 --delete-sources     # Merge and auto-delete split files"
            echo "  $0 -d --dry-run         # Test mode: show what would be deleted"
            echo ""
            echo "Safety features:"
            echo "  - Verifies merged file size matches sum of split files (±1% tolerance)"
            echo "  - Only deletes if verification passes"
            echo "  - Stops immediately on any error"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper function to get file size (cross-platform: macOS and Linux)
get_file_size() {
    local file="$1"
    # Try macOS stat first, fall back to Linux stat
    stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null
}

# Helper function to verify merge and optionally delete source files
verify_and_cleanup() {
    local merged_file="$1"
    shift
    local source_files=("$@")

    echo -e "  ${CYAN}Verifying merged file...${NC}"

    # Check merged file exists
    if [ ! -f "$merged_file" ]; then
        echo -e "  ${RED}ERROR: Merged file not created: $merged_file${NC}"
        exit 1
    fi

    # Get merged file size
    merged_size=$(get_file_size "$merged_file")

    # Calculate expected size (sum of source files)
    expected_size=0
    for src in "${source_files[@]}"; do
        if [ ! -f "$src" ]; then
            echo -e "  ${RED}ERROR: Source file not found: $src${NC}"
            exit 1
        fi
        src_size=$(get_file_size "$src")
        expected_size=$((expected_size + src_size))
    done

    # Verify size (allow 1% tolerance for filesystem overhead)
    min_size=$((expected_size * 99 / 100))
    max_size=$((expected_size * 101 / 100))

    if [ "$merged_size" -lt "$min_size" ] || [ "$merged_size" -gt "$max_size" ]; then
        echo -e "  ${RED}ERROR: Size verification failed!${NC}"
        echo -e "  ${RED}Expected: ~$expected_size bytes${NC}"
        echo -e "  ${RED}Got: $merged_size bytes${NC}"
        echo -e "  ${RED}Skipping cleanup for safety.${NC}"
        exit 1
    fi

    # Convert to human-readable format
    merged_size_mb=$(echo "scale=2; $merged_size / 1024 / 1024" | bc)
    echo -e "  ${GREEN}✓ Verification passed${NC} (size: ${merged_size_mb} MB)"

    # Delete source files if requested
    if [ "$DELETE_SOURCES" = true ]; then
        if [ "$DRY_RUN" = true ]; then
            echo -e "  ${YELLOW}[DRY RUN] Would delete:${NC}"
            for src in "${source_files[@]}"; do
                src_size=$(get_file_size "$src")
                src_size_mb=$(echo "scale=2; $src_size / 1024 / 1024" | bc)
                echo -e "    ${YELLOW}- $(basename "$src") (${src_size_mb} MB)${NC}"
            done
        else
            echo -e "  ${CYAN}Deleting source files...${NC}"
            for src in "${source_files[@]}"; do
                rm -f "$src"
                echo -e "    ${GREEN}✓ Deleted: $(basename "$src")${NC}"
            done
        fi
    fi
    echo ""
}

# Print header
echo "================================================"
echo "GGUF Split Files Merge Script"
echo "================================================"
echo ""
if [ "$DELETE_SOURCES" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Mode: DRY RUN (simulation only)${NC}"
    else
        echo -e "${YELLOW}Mode: Merge and DELETE split files${NC}"
    fi
else
    echo -e "${GREEN}Mode: Merge only (keep split files)${NC}"
fi
echo ""

# Apertus 70B Q6_K (bartowski)
echo "1/6: Merging Apertus 70B Q6_K (bartowski)..."
PART1="bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K-00001-of-00002.gguf"
PART2="bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K-00002-of-00002.gguf"
MERGED="bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K.gguf"
cat "$PART1" "$PART2" > "$MERGED"
echo -e "${GREEN}✓ Created swiss-ai_Apertus-70B-Instruct-2509-Q6_K.gguf${NC}"
verify_and_cleanup "$MERGED" "$PART1" "$PART2"

# Apertus 70B Q8_0 (bartowski)
echo "2/6: Merging Apertus 70B Q8_0 (bartowski)..."
PART1="bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0-00001-of-00002.gguf"
PART2="bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0-00002-of-00002.gguf"
MERGED="bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0.gguf"
cat "$PART1" "$PART2" > "$MERGED"
echo -e "${GREEN}✓ Created swiss-ai_Apertus-70B-Instruct-2509-Q8_0.gguf${NC}"
verify_and_cleanup "$MERGED" "$PART1" "$PART2"

# Apertus 70B Q6_K_XL (unsloth)
echo "3/6: Merging Apertus 70B Q6_K_XL (unsloth)..."
PART1="unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL-00001-of-00002.gguf"
PART2="unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL-00002-of-00002.gguf"
MERGED="unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL.gguf"
cat "$PART1" "$PART2" > "$MERGED"
echo -e "${GREEN}✓ Created Apertus-70B-Instruct-2509-UD-Q6_K_XL.gguf${NC}"
verify_and_cleanup "$MERGED" "$PART1" "$PART2"

# Kimi-Dev 72B Q6_K_XL
echo "4/6: Merging Kimi-Dev 72B Q6_K_XL..."
PART1="unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL-00001-of-00002.gguf"
PART2="unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL-00002-of-00002.gguf"
MERGED="unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL.gguf"
cat "$PART1" "$PART2" > "$MERGED"
echo -e "${GREEN}✓ Created Kimi-Dev-72B-UD-Q6_K_XL.gguf${NC}"
verify_and_cleanup "$MERGED" "$PART1" "$PART2"

# Qwen3 30B BF16
echo "5/6: Merging Qwen3 30B BF16..."
PART1="unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16-00001-of-00002.gguf"
PART2="unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16-00002-of-00002.gguf"
MERGED="unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16.gguf"
cat "$PART1" "$PART2" > "$MERGED"
echo -e "${GREEN}✓ Created Qwen3-30B-A3B-Instruct-2507-BF16.gguf${NC}"
verify_and_cleanup "$MERGED" "$PART1" "$PART2"

# Qwen3 Coder 30B 1M BF16
echo "6/6: Merging Qwen3 Coder 30B 1M BF16..."
PART1="unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16-00001-of-00002.gguf"
PART2="unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16-00002-of-00002.gguf"
MERGED="unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16.gguf"
cat "$PART1" "$PART2" > "$MERGED"
echo -e "${GREEN}✓ Created Qwen3-Coder-30B-A3B-Instruct-1M-BF16.gguf${NC}"
verify_and_cleanup "$MERGED" "$PART1" "$PART2"

echo "================================================"
echo "All Operations Complete!"
echo "================================================"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}This was a DRY RUN - no files were deleted${NC}"
    echo -e "${YELLOW}To actually delete files, run with: $0 --delete-sources${NC}"
    echo ""
elif [ "$DELETE_SOURCES" = true ]; then
    echo -e "${GREEN}✓ All models merged and split files deleted${NC}"
    echo ""
else
    echo -e "${GREEN}✓ All models merged successfully${NC}"
    echo -e "${CYAN}Split files have been kept (safe mode)${NC}"
    echo ""
    echo "To delete split files and save space, run:"
    echo "  $0 --delete-sources"
    echo ""
fi

echo "Merged files:"
ls -lh bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K.gguf 2>/dev/null || true
ls -lh bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0.gguf 2>/dev/null || true
ls -lh unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL.gguf 2>/dev/null || true
ls -lh unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL.gguf 2>/dev/null || true
ls -lh unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16.gguf 2>/dev/null || true
ls -lh unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16.gguf 2>/dev/null || true
echo ""
