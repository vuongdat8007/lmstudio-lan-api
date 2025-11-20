"""Transparent proxy for /v1/* endpoints to llama-server."""

from typing import Optional

import httpx
from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.responses import StreamingResponse

from .logging_config import get_logger
from .process_manager import LlamaServerManager, ProcessStatus
from .settings import settings

logger = get_logger("proxy")

router = APIRouter(tags=["proxy"])


async def check_llama_server_running(manager: LlamaServerManager) -> None:
    """
    Check if llama-server is running.

    Args:
        manager: Process manager instance

    Raises:
        HTTPException: If llama-server is not running
    """
    if manager.status != ProcessStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"llama-server is not running (status: {manager.status.value})"
        )

    if not await manager.is_healthy():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="llama-server is not healthy"
        )


async def proxy_request(
    request: Request,
    path: str,
    http_client: httpx.AsyncClient,
    manager: LlamaServerManager
) -> Response:
    """
    Proxy a request to llama-server.

    Args:
        request: FastAPI request
        path: Request path
        http_client: httpx client
        manager: Process manager

    Returns:
        Proxied response
    """
    # Check if llama-server is running
    await check_llama_server_running(manager)

    # Build target URL
    target_url = f"{settings.llama_server_base_url}{path}"

    # Get request body if present
    body = await request.body()

    # Forward headers (exclude host-related headers)
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in ["host", "x-api-key"]
    }

    logger.debug(f"Proxying {request.method} {path} to {target_url}")

    try:
        # Make the proxied request
        response = await http_client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
            params=request.query_params,
            timeout=300.0,  # 5 minutes for long-running requests
        )

        # Check if response is streaming (SSE or streaming JSON)
        content_type = response.headers.get("content-type", "")
        is_streaming = (
            "text/event-stream" in content_type or
            "application/x-ndjson" in content_type or
            response.headers.get("transfer-encoding") == "chunked"
        )

        if is_streaming:
            # Stream the response
            async def stream_response():
                async for chunk in response.aiter_bytes():
                    yield chunk

            return StreamingResponse(
                stream_response(),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=content_type
            )
        else:
            # Return non-streaming response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=content_type
            )

    except httpx.TimeoutException as e:
        logger.exception(f"Timeout proxying request: {e}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to llama-server timed out"
        )
    except httpx.RequestError as e:
        logger.exception(f"Error proxying request: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to llama-server: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error proxying request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Proxy error: {str(e)}"
        )


@router.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_v1_endpoint(path: str, request: Request) -> Response:
    """
    Proxy all /v1/* endpoints to llama-server.

    Args:
        path: Path after /v1/
        request: FastAPI request

    Returns:
        Proxied response from llama-server
    """
    http_client: httpx.AsyncClient = request.app.state.http_client
    manager: LlamaServerManager = request.app.state.process_manager

    full_path = f"/v1/{path}"
    return await proxy_request(request, full_path, http_client, manager)


@router.get("/health")
async def health_check(request: Request) -> dict:
    """
    Gateway health check endpoint.

    Returns:
        Health status
    """
    manager: LlamaServerManager = request.app.state.process_manager

    is_running = await manager.is_running()
    is_healthy = await manager.is_healthy() if is_running else False

    return {
        "status": "ok",
        "gateway": "running",
        "llama_server": {
            "running": is_running,
            "healthy": is_healthy,
            "status": manager.status.value,
            "model": manager.current_model.model_id if manager.current_model else None
        }
    }
