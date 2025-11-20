"""Main FastAPI application."""

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
from .model_registry import ModelRegistry
from .process_manager import LlamaServerManager
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
    logger.info(f"llama-server LAN Gateway v{__version__}")
    logger.info("=" * 60)
    logger.info(f"Gateway host: {settings.GATEWAY_HOST}:{settings.GATEWAY_PORT}")
    logger.info(f"llama-server: {settings.llama_server_base_url}")
    logger.info(f"API key enabled: {settings.is_api_key_enabled}")
    logger.info(f"IP allowlist: {settings.IP_ALLOWLIST}")

    # Initialize HTTP client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(300.0, connect=10.0),
        follow_redirects=True,
    )
    app.state.http_client = http_client
    logger.info("HTTP client initialized")

    # Initialize model registry
    try:
        model_registry = ModelRegistry()
        app.state.model_registry = model_registry
        logger.info(f"Model registry loaded: {len(model_registry.list_models())} models")
    except Exception as e:
        logger.exception(f"Failed to load model registry: {e}")
        raise

    # Initialize process manager
    process_manager = LlamaServerManager()
    app.state.process_manager = process_manager
    logger.info("Process manager initialized")

    logger.info("=" * 60)
    logger.info("Gateway started successfully")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down gateway...")

    # Stop llama-server if running
    try:
        if await process_manager.is_running():
            logger.info("Stopping llama-server...")
            await process_manager.stop()
            logger.info("llama-server stopped")
    except Exception as e:
        logger.exception(f"Error stopping llama-server: {e}")

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
        title="llama-server LAN Gateway",
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
