# src/lmstudio_gateway/debug.py
"""
Debug API router for real-time monitoring.
Provides SSE streaming, status snapshots, and performance metrics.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from .dependencies import get_debug_state

logger = logging.getLogger("lmstudio_gateway.debug")

router = APIRouter(prefix="/debug", tags=["debug"])

# Global event queue for broadcasting debug events
debug_event_queue: asyncio.Queue = asyncio.Queue()


async def debug_event_generator() -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generator that yields debug events from the queue.
    Clients connect and receive all events in real-time.

    Yields:
        Debug event dictionaries
    """
    while True:
        event = await debug_event_queue.get()
        yield event


async def broadcast_debug_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Broadcast a debug event to all connected SSE clients.

    Args:
        event_type: Type of event (model_load_start, inference_progress, etc.)
        data: Event data dictionary
    """
    await debug_event_queue.put({
        "type": event_type,
        "data": {
            **data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    })


@router.get("/stream")
async def stream_debug_events(request: Request) -> EventSourceResponse:
    """
    SSE endpoint for real-time debug information.
    Streams model loading progress and inference metrics.

    Args:
        request: FastAPI request object

    Returns:
        Server-Sent Events response
    """
    async def event_stream() -> AsyncGenerator[Dict[str, str], None]:
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
                # Check if client is still connected
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
            logger.exception("Error in debug stream: %s", e)

    return EventSourceResponse(event_stream())


@router.get("/status")
async def get_debug_status(request: Request) -> Dict[str, Any]:
    """
    Get current debug status snapshot.

    Args:
        request: FastAPI request object

    Returns:
        Current status dictionary with operation info
    """
    debug_state = get_debug_state(request)
    active_model = getattr(request.app.state, "active_model", {})

    return {
        "status": debug_state.get("status", "idle"),
        "current_operation": debug_state.get("current_operation"),
        "active_model": active_model,
        "recent_requests": debug_state.get("recent_requests", [])[-10:],
        "total_requests": debug_state.get("total_requests", 0),
        "total_errors": debug_state.get("total_errors", 0),
    }


@router.get("/metrics")
async def get_debug_metrics(request: Request) -> Dict[str, Any]:
    """
    Get performance metrics.

    Args:
        request: FastAPI request object

    Returns:
        Performance and system metrics
    """
    import psutil

    debug_state = get_debug_state(request)
    active_model = getattr(request.app.state, "active_model", {})

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    # Try to get GPU info (may not be available)
    gpu_info = {}
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_info = {
            "gpu_memory_used_mb": gpu_mem.used // (1024 * 1024),
            "gpu_memory_total_mb": gpu_mem.total // (1024 * 1024),
            "gpu_utilization_percent": gpu_util.gpu,
        }
        pynvml.nvmlShutdown()
    except Exception:
        # GPU info not available
        pass

    return {
        "model_info": {
            "model_key": active_model.get("model_key"),
            "instance_id": active_model.get("instance_id"),
        },
        "performance": {
            "total_requests": debug_state.get("total_requests", 0),
            "total_errors": debug_state.get("total_errors", 0),
        },
        "system": {
            "cpu_percent": cpu_percent,
            "ram_used_mb": memory.used // (1024 * 1024),
            "ram_total_mb": memory.total // (1024 * 1024),
            "ram_percent": memory.percent,
            **gpu_info,
        },
    }
