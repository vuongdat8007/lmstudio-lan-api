# src/lmstudio_gateway/main.py
"""
Main FastAPI application for LM Studio LAN Gateway.
Assembles all routers, middleware, and lifecycle events.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .admin_models import router as admin_router
from .debug import router as debug_router
from .dependencies import close_http_client, create_http_client
from .logging_config import configure_logging
from .middleware import ApiKeyMiddleware, IPAllowlistMiddleware
from .proxy import router as proxy_router
from .settings import settings

# Configure logging first
configure_logging()
logger = logging.getLogger("lmstudio_gateway.main")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="LM Studio LAN Gateway",
        description="Production-ready LAN gateway for LM Studio's OpenAI-compatible API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware (configure origins as needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security middleware (order matters!)
    app.add_middleware(IPAllowlistMiddleware)
    app.add_middleware(ApiKeyMiddleware)

    # Register routers
    app.include_router(admin_router)
    app.include_router(debug_router)
    app.include_router(proxy_router)

    # Startup event
    @app.on_event("startup")
    async def on_startup() -> None:
        """Initialize resources on application startup."""
        logger.info("Starting LM Studio LAN Gateway v1.0.0")
        logger.info("LM Studio URL: %s", settings.LMSTUDIO_BASE_URL)
        logger.info("Gateway: %s:%s", settings.GATEWAY_HOST, settings.GATEWAY_PORT)
        logger.info("API Key Auth: %s", "enabled" if settings.api_key_enabled else "disabled")
        logger.info("IP Allowlist: %s", settings.ip_allowlist_items or ["*"])

        await create_http_client(app)
        logger.info("LM Studio LAN Gateway started successfully")

    # Shutdown event
    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        """Clean up resources on application shutdown."""
        logger.info("Shutting down LM Studio LAN Gateway")
        await close_http_client(app)
        logger.info("LM Studio LAN Gateway stopped")

    # Health endpoint
    @app.get("/health", tags=["health"])
    async def health() -> dict:
        """
        Health check endpoint.

        Returns:
            Health status dictionary
        """
        return {"status": "ok"}

    return app


# Create app instance
app = create_app()
