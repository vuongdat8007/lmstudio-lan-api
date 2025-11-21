"""Debug and monitoring endpoints for Ollama."""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

import httpx
from fastapi import APIRouter, Request, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from .logging_config import get_logger
from .ollama_client import OllamaClient
from .settings import settings

logger = get_logger("debug")

router = APIRouter(prefix="/debug", tags=["debug"])

# Global event queue for debug SSE streaming
debug_event_queue: asyncio.Queue = asyncio.Queue()


async def broadcast_debug_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Broadcast a debug event to all SSE clients.

    Args:
        event_type: Type of event
        data: Event data
    """
    await debug_event_queue.put({
        "type": event_type,
        "data": {
            **data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    })


async def debug_event_generator() -> AsyncGenerator[Dict[str, Any], None]:
    """Generate debug events from the queue."""
    while True:
        event = await debug_event_queue.get()
        yield event


@router.get("/status")
async def get_debug_status(request: Request) -> Dict[str, Any]:
    """
    Get current debug status snapshot.

    Returns:
        Current status information including running models
    """
    logger.debug("Getting debug status")

    try:
        ollama_client: OllamaClient = request.app.state.ollama_client

        # Get Ollama health
        is_healthy = await ollama_client.is_healthy()

        # Get running models
        running_models = []
        if is_healthy:
            try:
                running_models = await ollama_client.list_running_models()
            except Exception as e:
                logger.warning(f"Could not get running models: {e}")

        # Get active model
        active_model_id = getattr(request.app.state, 'active_model_id', None)

        return {
            "gateway": {
                "status": "running",
                "version": "3.0.0",  # Updated for Ollama migration
                "backend": "ollama",
            },
            "ollama": {
                "healthy": is_healthy,
                "base_url": settings.OLLAMA_BASE_URL,
                "active_model": active_model_id,
                "running_models": running_models,
                "running_count": len(running_models),
            }
        }

    except Exception as e:
        logger.exception(f"Error getting debug status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get debug status: {str(e)}"
        )


@router.get("/stream")
async def stream_debug_events(request: Request) -> EventSourceResponse:
    """
    Server-Sent Events stream for real-time debug information.

    Returns:
        SSE stream of debug events
    """
    logger.info("Debug stream client connected")

    async def event_stream():
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "message": "Debug stream connected",
                    "backend": "ollama"
                })
            }

            # Stream debug events
            async for event in debug_event_generator():
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("Debug stream client disconnected")
                    break

                yield {
                    "event": event.get("type", "debug"),
                    "data": json.dumps(event.get("data", {}))
                }

        except asyncio.CancelledError:
            logger.info("Debug stream cancelled")
        except Exception as e:
            logger.exception(f"Error in debug stream: {e}")

    return EventSourceResponse(event_stream())


@router.get("/models/running")
async def get_running_models(request: Request) -> Dict[str, Any]:
    """
    Get currently running models with details.

    Returns:
        List of running models with memory usage and timing info
    """
    logger.debug("Getting running models")

    try:
        ollama_client: OllamaClient = request.app.state.ollama_client
        running_models = await ollama_client.list_running_models()

        return {
            "count": len(running_models),
            "models": running_models
        }

    except Exception as e:
        logger.exception(f"Error getting running models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get running models: {str(e)}"
        )


@router.get("/models/{model_name}/info")
async def get_model_info(model_name: str, request: Request) -> Dict[str, Any]:
    """
    Get detailed information about a specific model.

    Args:
        model_name: Ollama model name

    Returns:
        Model details including modelfile, parameters, template
    """
    logger.debug(f"Getting model info for: {model_name}")

    try:
        ollama_client: OllamaClient = request.app.state.ollama_client

        # Resolve model name if it's a custom ID
        if hasattr(request.app.state, 'model_adapter') and request.app.state.model_adapter:
            from .model_adapter import ModelAdapter
            adapter: ModelAdapter = request.app.state.model_adapter
            model_name = adapter.resolve_model_name(model_name)

        model_info = await ollama_client.show_model(model_name)

        return {
            "model_name": model_name,
            "info": model_info
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {model_name}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.get("/version")
async def get_ollama_version(request: Request) -> Dict[str, Any]:
    """
    Get Ollama version information.

    Returns:
        Ollama version details
    """
    logger.debug("Getting Ollama version")

    try:
        ollama_client: OllamaClient = request.app.state.ollama_client
        version_info = await ollama_client.get_version()

        return {
            "ollama": version_info,
            "gateway": {
                "version": "3.0.0",
                "backend": "ollama"
            }
        }

    except Exception as e:
        logger.exception(f"Error getting version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version: {str(e)}"
        )


@router.get("/health")
async def debug_health_check(request: Request) -> Dict[str, Any]:
    """
    Detailed health check with timing information.

    Returns:
        Detailed health status
    """
    logger.debug("Debug health check")

    try:
        ollama_client: OllamaClient = request.app.state.ollama_client

        start_time = datetime.utcnow()
        is_healthy = await ollama_client.is_healthy()
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        result = {
            "gateway": {
                "status": "running",
                "version": "3.0.0"
            },
            "ollama": {
                "healthy": is_healthy,
                "base_url": settings.OLLAMA_BASE_URL,
                "response_time_ms": round(response_time_ms, 2)
            }
        }

        if is_healthy:
            try:
                running_models = await ollama_client.list_running_models()
                result["ollama"]["running_models_count"] = len(running_models)
            except Exception as e:
                logger.warning(f"Could not get running models count: {e}")
                result["ollama"]["running_models_count"] = None

        return result

    except Exception as e:
        logger.exception(f"Error in debug health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


# Note: Logs endpoint removed - Ollama logs are managed by system service
# Users should use:
# - Linux: journalctl -u ollama
# - macOS: Check ~/Library/Logs/ollama.log
# - Windows: Check Event Viewer or Ollama logs directory

# Note: Slots endpoint removed - Ollama uses a different concurrency model
# Use /debug/models/running to see active inference sessions

# Note: Metrics endpoint - Ollama provides metrics via /api/ps
# Use /debug/models/running for performance data
