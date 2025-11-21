"""Debug and monitoring endpoints."""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

import httpx
from fastapi import APIRouter, Request, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from .logging_config import get_logger
from .process_manager import LlamaServerManager, ProcessStatus
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
        Current status information
    """
    logger.debug("Getting debug status")

    try:
        manager: LlamaServerManager = request.app.state.process_manager
        process_status = manager.get_status()

        return {
            "gateway": {
                "status": "running",
                "version": "2.0.0",
                "uptime_seconds": None,  # TODO: Track gateway uptime
            },
            "llama_server": {
                "status": process_status["status"],
                "model": process_status["model"],
                "started_at": process_status["started_at"],
                "uptime_seconds": process_status["uptime_seconds"],
                "pid": process_status["pid"],
                "error_message": process_status["error_message"],
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
                    "message": "Debug stream connected"
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


@router.get("/logs")
async def get_logs(request: Request, lines: int = 50) -> Dict[str, Any]:
    """
    Get recent llama-server logs.

    Args:
        lines: Number of log lines to return (default: 50)

    Returns:
        Recent stdout and stderr logs
    """
    logger.debug(f"Getting logs (lines={lines})")

    try:
        manager: LlamaServerManager = request.app.state.process_manager
        logs = manager.get_logs(lines=lines)

        return {
            "lines": lines,
            "stdout": logs["stdout"],
            "stderr": logs["stderr"]
        }

    except Exception as e:
        logger.exception(f"Error getting logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )


@router.get("/metrics")
async def get_metrics(request: Request) -> Dict[str, Any]:
    """
    Get metrics from llama-server or return empty metrics if not running.

    Returns:
        Metrics data or empty metrics structure
    """
    logger.debug("Getting metrics")

    try:
        manager: LlamaServerManager = request.app.state.process_manager

        # If llama-server is not running, return empty metrics
        if manager.status != ProcessStatus.RUNNING:
            return {
                "llama_server_running": False,
                "model": None,
                "metrics": None,
                "message": "llama-server is not running - load a model first"
            }

        # Try to proxy to llama-server /metrics
        try:
            http_client: httpx.AsyncClient = request.app.state.http_client
            response = await http_client.get(
                f"{settings.llama_server_base_url}/metrics",
                timeout=10.0
            )

            if response.status_code == 404:
                return {
                    "llama_server_running": True,
                    "model": manager.current_model.model_id if manager.current_model else None,
                    "metrics": None,
                    "message": "llama-server metrics endpoint not available"
                }

            response.raise_for_status()
            return {
                "llama_server_running": True,
                "model": manager.current_model.model_id if manager.current_model else None,
                "metrics": response.text,
                "message": None
            }

        except httpx.RequestError as e:
            logger.warning(f"Failed to fetch metrics from llama-server: {e}")
            return {
                "llama_server_running": True,
                "model": manager.current_model.model_id if manager.current_model else None,
                "metrics": None,
                "message": f"Failed to fetch metrics: {str(e)}"
            }

    except Exception as e:
        logger.exception(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/slots")
async def get_slots(request: Request) -> Dict[str, Any]:
    """
    Get llama-server slots information.

    Returns:
        Slot information or empty response if not running
    """
    logger.debug("Getting slots")

    try:
        manager: LlamaServerManager = request.app.state.process_manager

        if manager.status != ProcessStatus.RUNNING:
            return {
                "llama_server_running": False,
                "slots": [],
                "message": "llama-server is not running - load a model first"
            }

        try:
            http_client: httpx.AsyncClient = request.app.state.http_client
            response = await http_client.get(
                f"{settings.llama_server_base_url}/slots",
                timeout=10.0
            )
            response.raise_for_status()
            return {
                "llama_server_running": True,
                "slots": response.json(),
                "message": None
            }
        except httpx.RequestError as e:
            logger.warning(f"Failed to fetch slots: {e}")
            return {
                "llama_server_running": True,
                "slots": [],
                "message": f"Failed to fetch slots: {str(e)}"
            }

    except Exception as e:
        logger.exception(f"Error getting slots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get slots: {str(e)}"
        )


@router.get("/props")
async def get_props(request: Request) -> Dict[str, Any]:
    """
    Get llama-server properties.

    Returns:
        Server properties or empty response if not running
    """
    logger.debug("Getting props")

    try:
        manager: LlamaServerManager = request.app.state.process_manager

        if manager.status != ProcessStatus.RUNNING:
            return {
                "llama_server_running": False,
                "props": None,
                "message": "llama-server is not running - load a model first"
            }

        try:
            http_client: httpx.AsyncClient = request.app.state.http_client
            response = await http_client.get(
                f"{settings.llama_server_base_url}/props",
                timeout=10.0
            )
            response.raise_for_status()
            return {
                "llama_server_running": True,
                "props": response.json(),
                "message": None
            }
        except httpx.RequestError as e:
            logger.warning(f"Failed to fetch props: {e}")
            return {
                "llama_server_running": True,
                "props": None,
                "message": f"Failed to fetch props: {str(e)}"
            }

    except Exception as e:
        logger.exception(f"Error getting props: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get props: {str(e)}"
        )
