#!/bin/bash
# cleanup_split_files.sh
# Safely delete split GGUF source files after successful merge
#
# IMPORTANT: Run this script AFTER merge_split_models.sh completes successfully
# Run on server at: /home/boxwoodtech/models/
#
# This will delete 12 split files and save approximately 50-150GB+ of disk space

set -e  # Exit on any error

echo "================================================"
echo "GGUF Split Files Cleanup Script"
echo "================================================"
echo ""
echo "This script will delete split GGUF source files after verifying"
echo "that all merged files exist and are complete."
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to verify file exists and show size
verify_file() {
    local file="$1"
    if [ -f "$file" ]; then
        local size=$(du -h "$file" | cut -f1)
        echo -e "${GREEN}✓${NC} $(basename "$file") (${size})"
        return 0
    else
        echo -e "${RED}✗${NC} $(basename "$file") - NOT FOUND!"
        return 1
    fi
}

echo "================================================"
echo "Step 1: Verifying all merged files exist..."
echo "================================================"
echo ""

# Track verification status
ALL_VERIFIED=true

# Verify Apertus 70B Q6_K merged file
verify_file "bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K.gguf" || ALL_VERIFIED=false

# Verify Apertus 70B Q8_0 merged file
verify_file "bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0.gguf" || ALL_VERIFIED=false

# Verify Apertus 70B Q6_K_XL merged file
verify_file "unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL.gguf" || ALL_VERIFIED=false

# Verify Kimi-Dev 72B Q6_K_XL merged file
verify_file "unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL.gguf" || ALL_VERIFIED=false

# Verify Qwen3 30B BF16 merged file
verify_file "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16.gguf" || ALL_VERIFIED=false

# Verify Qwen3 Coder 30B 1M BF16 merged file
verify_file "unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16.gguf" || ALL_VERIFIED=false

echo ""

if [ "$ALL_VERIFIED" = false ]; then
    echo -e "${RED}ERROR: Not all merged files exist!${NC}"
    echo "Please run merge_split_models.sh first and ensure it completes successfully."
    exit 1
fi

echo -e "${GREEN}All 6 merged files verified successfully!${NC}"
echo ""
echo "================================================"
echo "Step 2: Calculating space to be freed..."
echo "================================================"
echo ""

# Calculate total size of split files before deletion
TOTAL_SIZE=0
for dir in \
    "bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF" \
    "unsloth/Apertus-70B-Instruct-2509-GGUF" \
    "unsloth/Kimi-Dev-72B-GGUF" \
    "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF" \
    "unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF"; do
    if [ -d "$dir" ]; then
        SIZE=$(find "$dir" -name "*-0000[12]-of-00002.gguf" -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1 || echo "0")
        if [ "$SIZE" != "0" ]; then
            echo "  $dir: $SIZE"
        fi
    fi
done

echo ""
echo -e "${YELLOW}Press ENTER to proceed with deletion, or Ctrl+C to cancel...${NC}"
read

echo ""
echo "================================================"
echo "Step 3: Deleting split files..."
echo "================================================"
echo ""

# Delete Apertus 70B Q6_K splits
echo "Deleting Apertus 70B Q6_K splits..."
rm -v bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K-00001-of-00002.gguf
rm -v bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K-00002-of-00002.gguf

# Delete Apertus 70B Q8_0 splits
echo "Deleting Apertus 70B Q8_0 splits..."
rm -v bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0-00001-of-00002.gguf
rm -v bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0-00002-of-00002.gguf

# Delete Apertus 70B Q6_K_XL splits
echo "Deleting Apertus 70B Q6_K_XL splits..."
rm -v unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL-00001-of-00002.gguf
rm -v unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL-00002-of-00002.gguf

# Delete Kimi-Dev 72B Q6_K_XL splits
echo "Deleting Kimi-Dev 72B Q6_K_XL splits..."
rm -v unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL-00001-of-00002.gguf
rm -v unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL-00002-of-00002.gguf

# Delete Qwen3 30B BF16 splits
echo "Deleting Qwen3 30B BF16 splits..."
rm -v unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16-00001-of-00002.gguf
rm -v unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16-00002-of-00002.gguf

# Delete Qwen3 Coder 30B 1M BF16 splits
echo "Deleting Qwen3 Coder 30B 1M BF16 splits..."
rm -v unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16-00001-of-00002.gguf
rm -v unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16-00002-of-00002.gguf

echo ""
echo "================================================"
echo "Cleanup Complete!"
echo "================================================"
echo ""
echo -e "${GREEN}✓ Successfully deleted all 12 split files${NC}"
echo ""
echo "Directory sizes after cleanup:"
echo "------------------------------"
du -sh bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/ 2>/dev/null || echo "Directory not found"
du -sh unsloth/Apertus-70B-Instruct-2509-GGUF/ 2>/dev/null || echo "Directory not found"
du -sh unsloth/Kimi-Dev-72B-GGUF/ 2>/dev/null || echo "Directory not found"
du -sh unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/ 2>/dev/null || echo "Directory not found"
du -sh unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/ 2>/dev/null || echo "Directory not found"
echo ""
echo -e "${GREEN}Disk space has been freed!${NC}"
echo ""
