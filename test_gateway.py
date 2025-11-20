#!/usr/bin/env python3
"""Test script for llama-server LAN Gateway."""

import sys
sys.path.insert(0, 'src')

def test_imports():
    """Test all module imports."""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)

    try:
        from llama_gateway import __version__
        from llama_gateway.settings import settings
        from llama_gateway.logging_config import setup_logging, get_logger
        from llama_gateway.middleware import IPAllowlistMiddleware, ApiKeyMiddleware
        from llama_gateway.model_registry import ModelRegistry, Model
        from llama_gateway.command_builder import build_llama_server_command
        from llama_gateway.process_manager import LlamaServerManager
        from llama_gateway.admin_models import router as admin_router
        from llama_gateway.proxy import router as proxy_router
        from llama_gateway.debug import router as debug_router
        from llama_gateway.main import create_app

        print("✅ All module imports successful")
        print(f"   Package version: {__version__}")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_settings():
    """Test settings configuration."""
    print("\n" + "=" * 60)
    print("TEST 2: Settings Configuration")
    print("=" * 60)

    try:
        from llama_gateway.settings import settings

        print(f"✅ Settings loaded successfully")
        print(f"   Gateway: {settings.GATEWAY_HOST}:{settings.GATEWAY_PORT}")
        print(f"   llama-server: {settings.llama_server_base_url}")
        print(f"   Binary: {settings.LLAMA_SERVER_BINARY}")
        print(f"   Model registry: {settings.MODEL_REGISTRY_PATH}")
        print(f"   API key enabled: {settings.is_api_key_enabled}")
        print(f"   IP allowlist: {settings.IP_ALLOWLIST}")
        print(f"   Log level: {settings.LOG_LEVEL}")
        return True
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False


def test_model_registry():
    """Test model registry."""
    print("\n" + "=" * 60)
    print("TEST 3: Model Registry")
    print("=" * 60)

    try:
        from llama_gateway.model_registry import ModelRegistry

        registry = ModelRegistry()
        models = registry.list_models()

        print(f"✅ Model registry loaded: {len(models)} model(s)")
        for model in models:
            print(f"\n   Model: {model.model_id}")
            print(f"   Name: {model.name}")
            print(f"   Path: {model.path}")
            print(f"   Config:")
            print(f"     - Context: {model.config.context_length}")
            print(f"     - GPU layers: {model.config.n_gpu_layers}")
            print(f"     - Batch size: {model.config.batch_size}")
            print(f"     - Host: {model.config.host}")
            print(f"     - Port: {model.config.port}")
            print(f"     - Flash attention: {model.config.flash_attention}")
            print(f"     - No mmap: {model.config.no_mmap}")

        return True
    except Exception as e:
        print(f"❌ Model registry test failed: {e}")
        return False


def test_command_builder():
    """Test command builder."""
    print("\n" + "=" * 60)
    print("TEST 4: Command Builder")
    print("=" * 60)

    try:
        from llama_gateway.model_registry import ModelRegistry
        from llama_gateway.command_builder import build_llama_server_command, command_to_string

        registry = ModelRegistry()
        models = registry.list_models()

        if not models:
            print("⚠️  No models in registry to test")
            return True

        model = models[0]
        cmd = build_llama_server_command(model)
        cmd_str = command_to_string(cmd)

        print(f"✅ Command built for model: {model.model_id}")
        print(f"\n   Command:")
        print(f"   {cmd_str}")

        # Verify key parameters
        assert "-m" in cmd, "Missing model path flag"
        assert "-c" in cmd, "Missing context flag"
        assert "-ngl" in cmd, "Missing GPU layers flag"
        assert "--host" in cmd, "Missing host flag"
        assert "--port" in cmd, "Missing port flag"

        print(f"\n   ✅ All required flags present")
        return True
    except Exception as e:
        print(f"❌ Command builder test failed: {e}")
        return False


def test_middleware():
    """Test security middleware."""
    print("\n" + "=" * 60)
    print("TEST 5: Security Middleware")
    print("=" * 60)

    try:
        from llama_gateway.middleware import parse_ip_allowlist, is_ip_allowed

        # Test allowlist parsing
        allowlist = parse_ip_allowlist("192.168.0.0/24,10.0.0.0/24")
        print(f"✅ IP allowlist parsed: {allowlist}")

        # Test IP validation
        test_cases = [
            ("192.168.0.100", ["192.168.0.0/24"], True, "Local subnet"),
            ("10.0.0.181", ["10.0.0.0/24"], True, "AMD AI machine"),
            ("8.8.8.8", ["192.168.0.0/24"], False, "External IP"),
            ("any-ip", ["*"], True, "Wildcard"),
        ]

        all_passed = True
        for ip, allowlist, expected, description in test_cases:
            result = is_ip_allowed(ip, allowlist)
            status = "✅" if result == expected else "❌"
            print(f"   {status} {ip:15} → {result:5} ({description})")
            if result != expected:
                all_passed = False

        return all_passed
    except Exception as e:
        print(f"❌ Middleware test failed: {e}")
        return False


def test_fastapi_app():
    """Test FastAPI application."""
    print("\n" + "=" * 60)
    print("TEST 6: FastAPI Application")
    print("=" * 60)

    try:
        from llama_gateway.main import create_app

        app = create_app()

        print(f"✅ FastAPI app created successfully")
        print(f"   Title: {app.title}")
        print(f"   Version: {app.version}")
        print(f"\n   Registered routes:")

        admin_routes = []
        debug_routes = []
        proxy_routes = []
        other_routes = []

        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                path = route.path
                if path.startswith('/admin'):
                    admin_routes.append((path, route.methods))
                elif path.startswith('/debug'):
                    debug_routes.append((path, route.methods))
                elif path.startswith('/v1'):
                    proxy_routes.append((path, route.methods))
                elif path in ['/health', '/openapi.json', '/docs', '/redoc']:
                    other_routes.append((path, route.methods))

        print(f"\n   Admin API ({len(admin_routes)} endpoints):")
        for path, methods in sorted(admin_routes):
            print(f"     {path}")

        print(f"\n   Debug API ({len(debug_routes)} endpoints):")
        for path, methods in sorted(debug_routes):
            print(f"     {path}")

        print(f"\n   Proxy API ({len(proxy_routes)} endpoints):")
        for path, methods in sorted(proxy_routes):
            print(f"     {path}")

        print(f"\n   Other ({len(other_routes)} endpoints):")
        for path, methods in sorted(other_routes):
            print(f"     {path}")

        # Verify expected routes exist
        expected_admin = [
            '/admin/models',
            '/admin/models/active',
            '/admin/models/load',
            '/admin/models/unload',
            '/admin/models/reload',
        ]

        admin_paths = [path for path, _ in admin_routes]
        for expected_path in expected_admin:
            if expected_path in admin_paths:
                print(f"   ✅ {expected_path} registered")
            else:
                print(f"   ❌ {expected_path} missing")
                return False

        return True
    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "🧪 " * 30)
    print("llama-server LAN Gateway - Test Suite")
    print("🧪 " * 30 + "\n")

    tests = [
        ("Imports", test_imports),
        ("Settings", test_settings),
        ("Model Registry", test_model_registry),
        ("Command Builder", test_command_builder),
        ("Middleware", test_middleware),
        ("FastAPI App", test_fastapi_app),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {name}")

    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! Gateway is ready to use.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure")
        print("2. Update models/registry.json with your model paths")
        print("3. Run: uvicorn llama_gateway.main:app --host 10.0.0.181 --port 8001")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
