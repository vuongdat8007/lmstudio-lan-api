#!/bin/bash
# Script to merge split GGUF files
# Run this on the server in /home/boxwoodtech/models

set -e

echo "Merging split GGUF models..."
echo ""

# Apertus 70B Q6_K (bartowski)
echo "Merging Apertus 70B Q6_K (bartowski)..."
cat bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K-00001-of-00002.gguf \
    bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K-00002-of-00002.gguf \
    > bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K.gguf
echo "✓ Created swiss-ai_Apertus-70B-Instruct-2509-Q6_K.gguf"

# Apertus 70B Q8_0 (bartowski)
echo "Merging Apertus 70B Q8_0 (bartowski)..."
cat bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0-00001-of-00002.gguf \
    bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0-00002-of-00002.gguf \
    > bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0.gguf
echo "✓ Created swiss-ai_Apertus-70B-Instruct-2509-Q8_0.gguf"

# Apertus 70B Q6_K_XL (unsloth)
echo "Merging Apertus 70B Q6_K_XL (unsloth)..."
cat unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL-00001-of-00002.gguf \
    unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL-00002-of-00002.gguf \
    > unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL.gguf
echo "✓ Created Apertus-70B-Instruct-2509-UD-Q6_K_XL.gguf"

# Kimi-Dev 72B Q6_K_XL
echo "Merging Kimi-Dev 72B Q6_K_XL..."
cat unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL-00001-of-00002.gguf \
    unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL-00002-of-00002.gguf \
    > unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL.gguf
echo "✓ Created Kimi-Dev-72B-UD-Q6_K_XL.gguf"

# Qwen3 30B BF16
echo "Merging Qwen3 30B BF16..."
cat unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16-00001-of-00002.gguf \
    unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16-00002-of-00002.gguf \
    > unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16.gguf
echo "✓ Created Qwen3-30B-A3B-Instruct-2507-BF16.gguf"

# Qwen3 Coder 30B 1M BF16
echo "Merging Qwen3 Coder 30B 1M BF16..."
cat unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16-00001-of-00002.gguf \
    unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16-00002-of-00002.gguf \
    > unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16.gguf
echo "✓ Created Qwen3-Coder-30B-A3B-Instruct-1M-BF16.gguf"

echo ""
echo "✓ All models merged successfully!"
echo ""
echo "Merged files:"
ls -lh bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q6_K.gguf
ls -lh bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF/swiss-ai_Apertus-70B-Instruct-2509-Q8_0.gguf
ls -lh unsloth/Apertus-70B-Instruct-2509-GGUF/Apertus-70B-Instruct-2509-UD-Q6_K_XL.gguf
ls -lh unsloth/Kimi-Dev-72B-GGUF/Kimi-Dev-72B-UD-Q6_K_XL.gguf
ls -lh unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/Qwen3-30B-A3B-Instruct-2507-BF16.gguf
ls -lh unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF/Qwen3-Coder-30B-A3B-Instruct-1M-BF16.gguf
