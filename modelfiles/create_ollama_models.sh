#!/bin/bash
# Script to create all Ollama models from Modelfiles
# Run this from the modelfiles directory on the server

cd "$(dirname "$0")"

echo "Creating Ollama models from Modelfiles..."

# Single-file models
ollama create qwen2-1.5b-function-calling -f qwen2-1.5b-function-calling
ollama create apertus-70b-q4kl -f apertus-70b-q4kl
ollama create apertus-8b-bf16 -f apertus-8b-bf16
ollama create apertus-70b-q4km -f apertus-70b-q4km-giladgd
ollama create qwen3-coder-30b-q8 -f qwen3-coder-30b-q8
ollama create deepseek-r1-1.5b-q8 -f deepseek-r1-1.5b-q8
ollama create apertus-8b-bf16-unsloth -f apertus-8b-bf16-unsloth
ollama create apertus-8b-q2kxl -f apertus-8b-q2kxl
ollama create qwen3-30b-q8 -f qwen3-30b-q8
ollama create qwen3-30b-q8kxl -f qwen3-30b-q8kxl
ollama create qwen3-coder-30b-1m-q8kxl -f qwen3-coder-30b-1m-q8kxl

echo ""
echo "Done! Multi-part models (Q6_K, Q8_0 split files) require manual handling."
echo "Split GGUF files cannot be directly imported to Ollama."
echo ""
echo "Available models:"
ollama list
