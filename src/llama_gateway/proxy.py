"""Transparent proxy for /v1/* endpoints to Ollama."""

from typing import Optional

import httpx
from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.responses import StreamingResponse

from .logging_config import get_logger
from .ollama_client import OllamaClient
from .settings import settings

logger = get_logger("proxy")

router = APIRouter(tags=["proxy"])


async def check_ollama_running(ollama_client: OllamaClient) -> None:
    """
    Check if Ollama service is running.

    Args:
        ollama_client: Ollama client instance

    Raises:
        HTTPException: If Ollama is not accessible
    """
    if not await ollama_client.is_healthy():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama service is not running or not accessible"
        )


async def proxy_request(
    request: Request,
    path: str,
    http_client: httpx.AsyncClient,
    ollama_client: OllamaClient
) -> Response:
    """
    Proxy a request to Ollama.

    Args:
        request: FastAPI request
        path: Request path
        http_client: httpx client
        ollama_client: Ollama client

    Returns:
        Proxied response
    """
    # Check if Ollama is running
    await check_ollama_running(ollama_client)

    # Build target URL
    target_url = f"{settings.OLLAMA_BASE_URL}{path}"

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
            timeout=settings.OLLAMA_TIMEOUT,
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
            detail="Request to Ollama timed out"
        )
    except httpx.RequestError as e:
        logger.exception(f"Error proxying request: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Ollama: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error proxying request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Proxy error: {str(e)}"
        )


@router.get("/v1/models")
async def list_models_endpoint(request: Request) -> dict:
    """
    List models in OpenAI-compatible format.

    Returns:
        Model list response compatible with OpenAI API format
    """
    ollama_client: OllamaClient = request.app.state.ollama_client

    try:
        # Get models from Ollama
        ollama_models = await ollama_client.list_models()

        # Convert to OpenAI format
        openai_models = []
        for model in ollama_models:
            model_name = model.get("name", "")
            openai_models.append({
                "id": model_name,
                "object": "model",
                "created": int(model.get("modified_at", "0").timestamp()) if hasattr(model.get("modified_at", "0"), 'timestamp') else 0,
                "owned_by": "ollama",
                "permission": [],
                "root": model_name,
                "parent": None,
            })

        return {
            "object": "list",
            "data": openai_models
        }

    except Exception as e:
        logger.exception(f"Error listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


@router.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_v1_endpoint(path: str, request: Request) -> Response:
    """
    Proxy all /v1/* endpoints to Ollama.

    Ollama provides OpenAI-compatible endpoints at /v1/*.

    Args:
        path: Path after /v1/
        request: FastAPI request

    Returns:
        Proxied response from Ollama
    """
    http_client: httpx.AsyncClient = request.app.state.http_client
    ollama_client: OllamaClient = request.app.state.ollama_client

    full_path = f"/v1/{path}"
    return await proxy_request(request, full_path, http_client, ollama_client)


@router.get("/health")
async def health_check(request: Request) -> dict:
    """
    Gateway health check endpoint.

    Returns:
        Health status of gateway and Ollama
    """
    ollama_client: OllamaClient = request.app.state.ollama_client

    # Check Ollama health
    is_healthy = await ollama_client.is_healthy()

    # Get running models
    running_models = []
    active_model_id = getattr(request.app.state, 'active_model_id', None)

    if is_healthy:
        try:
            running = await ollama_client.list_running_models()
            running_models = [m.get("name") for m in running]
        except Exception as e:
            logger.warning(f"Could not get running models: {e}")

    return {
        "status": "ok" if is_healthy else "degraded",
        "gateway": "running",
        "ollama": {
            "healthy": is_healthy,
            "running_models": running_models,
            "active_model": active_model_id
        }
    }
