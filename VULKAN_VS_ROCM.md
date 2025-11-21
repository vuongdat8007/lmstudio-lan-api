# Vulkan vs ROCm - Which to Choose?

Both toolboxes work on your AMD Ryzen AI 9 HX 395+ processor. Here's how they compare:

## Quick Recommendation

**Use Vulkan** (`llama-vulkan-radv`) for most cases - it's faster, more compatible, and easier to use.

**Use ROCm** (`llama-rocm-7.1-rocwmma`) only if you need specific ROCm features or have compatibility issues with Vulkan.

---

## Detailed Comparison

### Vulkan (llama-vulkan-radv)

**Pros:**
- ✅ **Faster inference** - Better optimized for consumer GPUs
- ✅ **Better compatibility** - Works with more models out of the box
- ✅ **Lower VRAM usage** - More efficient memory management
- ✅ **Easier setup** - Fewer driver dependencies
- ✅ **Cross-platform** - Same code works on AMD, NVIDIA, Intel
- ✅ **More stable** - Fewer driver issues

**Cons:**
- ❌ Limited to graphics-focused compute
- ❌ May not support all advanced GPU features

**Best for:**
- General LLM inference
- Running multiple models
- Systems with limited VRAM
- Most users

**Command:**
```bash
./start_in_toolbox.sh vulkan
```

---

### ROCm (llama-rocm-7.1-rocwmma)

**Pros:**
- ✅ **Native AMD compute** - Direct access to GPU compute features
- ✅ **Full GPU features** - Access to specialized AMD instructions
- ✅ **Better for training** - More control over GPU resources
- ✅ **WMMA optimizations** - Wave Matrix Multiply-Accumulate support

**Cons:**
- ❌ Slower inference in most cases
- ❌ Higher VRAM usage
- ❌ More complex driver setup
- ❌ AMD-specific (not portable)
- ❌ Occasional driver compatibility issues

**Best for:**
- Advanced GPU features (if you know you need them)
- Model training (not just inference)
- Debugging GPU-specific issues
- Testing ROCm-specific optimizations

**Command:**
```bash
./start_in_toolbox.sh rocm
```

---

## Performance Comparison

Based on AMD Strix Halo benchmarks:

| Metric | Vulkan | ROCm |
|--------|--------|------|
| **Tokens/sec (Apertus-70B Q4)** | ~15-20 | ~12-18 |
| **Startup time** | Fast | Slower |
| **VRAM usage** | Lower | Higher |
| **Compatibility** | Excellent | Good |
| **Stability** | Excellent | Good |

---

## How to Choose

**Choose Vulkan if:**
- You want the fastest inference
- You're running standard GGUF models
- You want lower VRAM usage
- You're new to LLM inference
- You don't need ROCm-specific features

**Choose ROCm if:**
- You need specific ROCm features (you'll know if you do)
- You're doing GPU compute research
- You're training models (not common with llama-server)
- Vulkan doesn't work for some reason

**Still not sure?** → Use Vulkan. You can always switch later.

---

## How to Switch

You can easily switch between toolboxes:

### Stop Current Gateway
```bash
# Press Ctrl+C in the terminal running the gateway
```

### Start with Different Toolbox
```bash
# Switch to Vulkan
./start_in_toolbox.sh vulkan

# Switch to ROCm
./start_in_toolbox.sh rocm
```

The gateway and model registry are the same - only the GPU backend changes.

---

## Common Questions

### Q: Can I run both at the same time?
**A:** No, both use the same port (8080) for llama-server. Run one at a time.

### Q: Does my choice affect model loading?
**A:** No, both can load the same models. Only inference performance differs.

### Q: Will my models be faster with ROCm?
**A:** Usually no - Vulkan is typically faster for inference. ROCm is better for specific compute tasks.

### Q: Can I test both to compare?
**A:** Yes! Load a model with Vulkan, benchmark it, then restart with ROCm and compare.

### Q: Does the gateway code change?
**A:** No, the gateway code is identical. Only llama-server's GPU backend changes.

---

## Benchmark Both (Optional)

If you want to compare performance on your specific models:

### Test Vulkan
```bash
# Terminal 1: Start with Vulkan
./start_in_toolbox.sh vulkan

# Terminal 2: Load model and test
curl -X POST http://10.0.0.181:8002/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "apertus-8b-q8"}'

# Wait for load, then benchmark
time curl -X POST http://10.0.0.181:8002/v1/chat/completions \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Count from 1 to 100"}], "max_tokens": 500}'
```

### Test ROCm
```bash
# Terminal 1: Stop Vulkan (Ctrl+C), start ROCm
./start_in_toolbox.sh rocm

# Terminal 2: Run same test
curl -X POST http://10.0.0.181:8002/admin/models/load \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "apertus-8b-q8"}'

time curl -X POST http://10.0.0.181:8002/v1/chat/completions \
  -H "X-API-Key: change-me-please" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Count from 1 to 100"}], "max_tokens": 500}'
```

Compare the `time` output to see which is faster for your use case.

---

## Summary

- **Default choice:** Vulkan (llama-vulkan-radv)
- **Switching:** Easy, just restart with different argument
- **Performance:** Vulkan usually faster for inference
- **Models:** Both support the same models

Run: `./start_in_toolbox.sh` and choose when prompted, or use `./start_in_toolbox.sh vulkan` to skip the prompt.
