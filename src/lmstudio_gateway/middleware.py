# src/lmstudio_gateway/middleware.py
"""
Middleware for LM Studio LAN Gateway.
Implements IP allow-listing and API key authentication.
"""
from __future__ import annotations

import ipaddress
import logging
from typing import Iterable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .settings import settings

logger = logging.getLogger("lmstudio_gateway.middleware")


def _ip_in_allowlist(client_ip: str, allowlist: Iterable[str]) -> bool:
    """
    Check if client IP is in the allowlist.

    Supports:
    - "*" (allow all)
    - CIDR ranges (e.g., "192.168.0.0/24")
    - Single IPs (e.g., "192.168.0.10")

    Args:
        client_ip: Client IP address to check
        allowlist: Iterable of allowlist entries

    Returns:
        True if IP is allowed, False otherwise
    """
    if not allowlist:
        return True

    for entry in allowlist:
        if entry == "*":
            return True

        try:
            if "/" in entry:
                # CIDR range
                network = ipaddress.ip_network(entry, strict=False)
                if ipaddress.ip_address(client_ip) in network:
                    return True
            else:
                # Single IP
                if client_ip == entry:
                    return True
        except (ValueError, TypeError) as e:
            logger.warning(
                "Invalid IP allowlist entry '%s': %s",
                entry,
                e,
            )
            continue

    return False


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce IP allow-listing.

    Checks if the client IP is in the configured allowlist.
    Returns 403 Forbidden if not allowed.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Check client IP against allowlist.

        Args:
            request: FastAPI request object
            call_next: Next middleware in chain

        Returns:
            Response from next middleware or 403 if forbidden
        """
        client_host = request.client.host if request.client else "unknown"

        if not _ip_in_allowlist(client_host, settings.ip_allowlist_items):
            logger.warning(
                "Forbidden IP %s tried to access %s",
                client_host,
                request.url.path,
            )
            return Response(
                content="Forbidden",
                status_code=403,
                media_type="text/plain",
            )

        return await call_next(request)


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce API key authentication.

    Validates the X-API-Key header against configured API key.
    Returns 401 Unauthorized if invalid or missing.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Validate API key in request header.

        Args:
            request: FastAPI request object
            call_next: Next middleware in chain

        Returns:
            Response from next middleware or 401 if unauthorized
        """
        # Allow unauthenticated /health if configured
        if (
            not settings.REQUIRE_AUTH_FOR_HEALTH
            and request.url.path == "/health"
        ):
            return await call_next(request)

        # Skip auth if API key is not enabled
        if not settings.api_key_enabled:
            return await call_next(request)

        # Validate API key
        api_key = request.headers.get("X-API-Key")
        if api_key != settings.GATEWAY_API_KEY:
            logger.warning(
                "Unauthorized request from %s to %s",
                request.client.host if request.client else "unknown",
                request.url.path,
            )
            return Response(
                content="Unauthorized",
                status_code=401,
                media_type="text/plain",
            )

        return await call_next(request)
