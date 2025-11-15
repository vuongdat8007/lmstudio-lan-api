# src/lmstudio_gateway/dependencies.py
"""
Shared dependencies for LM Studio LAN Gateway.
Manages HTTP client lifecycle, LM Studio SDK client, and application state.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

import httpx
import lmstudio as lms
from fastapi import FastAPI, Request

from .settings import settings

logger = logging.getLogger("lmstudio_gateway.dependencies")


# LM Studio Python client (global; SDK manages its own resources)
lm_client = lms.get_default_client()


async def create_http_client(app: FastAPI) -> None:
    """
    Initialize and attach HTTP client & application state to app.state.
    Call this in startup event.

    Args:
        app: FastAPI application instance
    """
    logger.info(
        "Creating HTTP client for LM Studio at %s",
        settings.LMSTUDIO_BASE_URL,
    )

    # Create httpx client for LM Studio HTTP requests
    app.state.http_client = httpx.AsyncClient(
        base_url=str(settings.LMSTUDIO_BASE_URL),
        timeout=60.0,
    )

    # Initialize active model state
    app.state.active_model = {
        "model_key": None,
        "instance_id": None,
        "default_inference": {},
    }

    # Initialize debug state
    app.state.debug_state = {
        "status": "idle",  # idle | loading_model | processing_inference | error
        "current_operation": None,
        "recent_requests": [],
        "total_requests": 0,
        "total_errors": 0,
    }

    logger.info("Application state initialized")


async def close_http_client(app: FastAPI) -> None:
    """
    Close HTTP client and clean up resources.
    Call this in shutdown event.

    Args:
        app: FastAPI application instance
    """
    client: httpx.AsyncClient = getattr(app.state, "http_client", None)
    if client is not None:
        logger.info("Closing HTTP client")
        await client.aclose()


def get_http_client(request: Request) -> httpx.AsyncClient:
    """
    Dependency to retrieve HTTP client from app state.

    Args:
        request: FastAPI request object

    Returns:
        HTTP client instance

    Raises:
        RuntimeError: If HTTP client is not initialized
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise RuntimeError("HTTP client not initialized")
    return client


def get_active_model(request: Request) -> Dict[str, Any]:
    """
    Dependency to retrieve active model state from app state.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary containing model_key, instance_id, and default_inference
    """
    active_model = getattr(request.app.state, "active_model", None)
    if active_model is None:
        active_model = {
            "model_key": None,
            "instance_id": None,
            "default_inference": {},
        }
        request.app.state.active_model = active_model
    return active_model


def get_debug_state(request: Request) -> Dict[str, Any]:
    """
    Dependency to retrieve debug state from app state.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary containing debug state information
    """
    debug_state = getattr(request.app.state, "debug_state", None)
    if debug_state is None:
        debug_state = {
            "status": "idle",
            "current_operation": None,
            "recent_requests": [],
            "total_requests": 0,
            "total_errors": 0,
        }
        request.app.state.debug_state = debug_state
    return debug_state
