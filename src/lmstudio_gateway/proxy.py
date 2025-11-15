# src/lmstudio_gateway/proxy.py
"""
Proxy router for /v1/* endpoints.
Transparently forwards all requests to LM Studio with model injection.
"""
from __future__ import annotations

import json
import logging
from typing import Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from .dependencies import get_active_model, get_http_client

logger = logging.getLogger("lmstudio_gateway.proxy")

router = APIRouter(tags=["proxy"])


@router.api_route(
    "/v1/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_v1(
    full_path: str,
    request: Request,
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> Response:
    """
    Generic proxy for any /v1/... endpoint to LM Studio's /v1 server.

    For POST JSON bodies, injects default model and inference params if missing.

    Args:
        full_path: Path after /v1/
        request: FastAPI request object
        http_client: HTTP client for LM Studio

    Returns:
        Response from LM Studio

    Raises:
        HTTPException: On errors
    """
    method = request.method
    lm_path = f"/v1/{full_path}"
    query_params = dict(request.query_params)

    # Copy and sanitize headers
    headers: Dict[str, str] = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in {
            "host",
            "content-length",
            "connection",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
            "x-api-key",  # Don't forward gateway's API key
        }
    }

    body_bytes = await request.body()
    content_type = request.headers.get("content-type", "")

    # Patch JSON body for POST/PUT/PATCH
    if method in {"POST", "PUT", "PATCH"} and "application/json" in content_type.lower():
        try:
            data = json.loads(body_bytes.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON body on %s %s", method, request.url.path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON body",
            )

        if isinstance(data, dict):
            active_model = get_active_model(request)
            model_key = active_model.get("model_key")
            default_inf = active_model.get("default_inference") or {}

            # Inject default model if absent
            if "model" not in data and model_key:
                data["model"] = model_key
                logger.debug("Injected model: %s", model_key)

            # Inject default inference params
            for k, v in default_inf.items():
                if k not in data:
                    data[k] = v

            body_bytes = json.dumps(data).encode("utf-8")

    # Forward request to LM Studio
    try:
        lm_response = await http_client.request(
            method=method,
            url=lm_path,
            params=query_params,
            headers=headers,
            content=body_bytes,
        )
    except httpx.RequestError as e:
        logger.exception("Error forwarding to LM Studio: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error forwarding request to LM Studio",
        ) from e

    # Pass through status code and body
    response_headers = {
        k: v
        for k, v in lm_response.headers.items()
        if k.lower() not in {"content-length", "transfer-encoding", "connection"}
    }

    return Response(
        content=lm_response.content,
        status_code=lm_response.status_code,
        headers=response_headers,
        media_type=lm_response.headers.get("content-type"),
    )
