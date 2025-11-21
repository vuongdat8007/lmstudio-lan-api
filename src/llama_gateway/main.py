"""Main FastAPI application for Ollama Gateway."""

import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__, __description__
from .admin_models import router as admin_router
from .debug import router as debug_router
from .proxy import router as proxy_router
from .logging_config import setup_logging, get_logger
from .middleware import ApiKeyMiddleware, IPAllowlistMiddleware
from .ollama_client import OllamaClient
from .model_adapter import ModelAdapter
from .settings import settings

# Setup logging
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Ollama LAN Gateway v{__version__}")
    logger.info("=" * 60)
    logger.info(f"Gateway host: {settings.GATEWAY_HOST}:{settings.GATEWAY_PORT}")
    logger.info(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
    logger.info(f"API key enabled: {settings.is_api_key_enabled}")
    logger.info(f"IP allowlist: {settings.IP_ALLOWLIST}")

    # Initialize HTTP client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.OLLAMA_TIMEOUT, connect=10.0),
        follow_redirects=True,
    )
    app.state.http_client = http_client
    logger.info("HTTP client initialized")

    # Initialize Ollama client
    ollama_client = OllamaClient(
        base_url=settings.OLLAMA_BASE_URL,
        timeout=settings.OLLAMA_TIMEOUT
    )
    app.state.ollama_client = ollama_client
    logger.info("Ollama client initialized")

    # Check Ollama health
    try:
        is_healthy = await ollama_client.is_healthy()
        if is_healthy:
            version = await ollama_client.get_version()
            logger.info(f"Ollama is running (version: {version.get('version', 'unknown')})")

            # List available models
            models = await ollama_client.list_models()
            logger.info(f"Available models: {len(models)}")
        else:
            logger.warning("Ollama health check failed - service may not be running")
            logger.warning(f"Make sure Ollama is running at {settings.OLLAMA_BASE_URL}")
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        logger.warning("Gateway will start but Ollama must be running for API requests")

    # Initialize model registry/adapter (optional)
    if settings.is_registry_enabled:
        try:
            model_adapter = ModelAdapter(registry_path=settings.MODEL_REGISTRY_PATH)
            app.state.model_adapter = model_adapter
            logger.info(f"Model registry loaded: {len(model_adapter.list_models())} models")
        except Exception as e:
            logger.warning(f"Failed to load model registry: {e}")
            logger.warning("Gateway will work without registry (using Ollama models directly)")
            app.state.model_adapter = None
    else:
        logger.info("Model registry disabled - using Ollama models directly")
        app.state.model_adapter = None

    # Initialize active model state
    app.state.active_model_id = None

    logger.info("=" * 60)
    logger.info("Gateway started successfully")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down gateway...")

    # Close Ollama client
    try:
        await ollama_client.close()
        logger.info("Ollama client closed")
    except Exception as e:
        logger.exception(f"Error closing Ollama client: {e}")

    # Close HTTP client
    await http_client.aclose()
    logger.info("HTTP client closed")

    logger.info("Gateway shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="Ollama LAN Gateway",
        description=__description__,
        version=__version__,
        lifespan=lifespan,
    )

    # CORS middleware (optional, configure as needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security middleware
    app.add_middleware(IPAllowlistMiddleware)
    app.add_middleware(ApiKeyMiddleware)

    # Register routers
    app.include_router(admin_router)
    app.include_router(debug_router)
    app.include_router(proxy_router)

    logger.info("FastAPI app created")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "llama_gateway.main:app",
        host=settings.GATEWAY_HOST,
        port=settings.GATEWAY_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )
