"""Security middleware for API key authentication and IP allowlisting."""

import ipaddress
from typing import List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .logging_config import get_logger
from .settings import settings

logger = get_logger("middleware")


def parse_ip_allowlist(allowlist: str) -> List[str]:
    """
    Parse IP allowlist string into list of IPs/CIDRs.

    Args:
        allowlist: Comma-separated IP addresses or CIDR ranges

    Returns:
        List of IP addresses and CIDR ranges
    """
    if not allowlist or allowlist.strip() == "*":
        return ["*"]

    return [ip.strip() for ip in allowlist.split(",") if ip.strip()]


def is_ip_allowed(client_ip: str, allowlist: List[str]) -> bool:
    """
    Check if client IP is in the allowlist.

    Args:
        client_ip: Client IP address
        allowlist: List of allowed IPs/CIDRs or ["*"]

    Returns:
        True if IP is allowed, False otherwise
    """
    if "*" in allowlist:
        return True

    try:
        client_addr = ipaddress.ip_address(client_ip)

        for allowed in allowlist:
            try:
                # Try as CIDR network
                if "/" in allowed:
                    network = ipaddress.ip_network(allowed, strict=False)
                    if client_addr in network:
                        return True
                # Try as single IP
                else:
                    allowed_addr = ipaddress.ip_address(allowed)
                    if client_addr == allowed_addr:
                        return True
            except ValueError:
                logger.warning(f"Invalid IP/CIDR in allowlist: {allowed}")
                continue

        return False
    except ValueError:
        logger.warning(f"Invalid client IP address: {client_ip}")
        return False


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """Middleware to restrict access based on IP allowlist."""

    def __init__(self, app, allowlist: Optional[List[str]] = None):
        super().__init__(app)
        self.allowlist = allowlist or parse_ip_allowlist(settings.IP_ALLOWLIST)
        logger.info(f"IP allowlist initialized: {self.allowlist}")

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Check if client IP is allowed."""
        client_host = request.client.host if request.client else "unknown"

        if not is_ip_allowed(client_host, self.allowlist):
            logger.warning(
                f"Forbidden: IP {client_host} tried to access {request.url.path}"
            )
            return Response(
                content="Forbidden: IP address not allowed",
                status_code=403,
                media_type="text/plain",
            )

        return await call_next(request)


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""

    def __init__(self, app, api_key: Optional[str] = None):
        super().__init__(app)
        self.api_key = api_key or settings.GATEWAY_API_KEY
        self.is_enabled = settings.is_api_key_enabled

        if self.is_enabled:
            logger.info("API key authentication enabled")
        else:
            logger.warning("API key authentication DISABLED - not recommended for production!")

    def _should_check_auth(self, request: Request) -> bool:
        """Determine if authentication should be checked for this request."""
        path = request.url.path

        # Health endpoint bypass
        if path in ["/health", "/v1/health"]:
            return settings.REQUIRE_AUTH_FOR_HEALTH

        return True

    def _is_valid_api_key(self, request: Request) -> bool:
        """Check if the request has a valid API key."""
        if not self.is_enabled:
            return True

        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")

        if not api_key:
            return False

        return api_key == self.api_key

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Validate API key if enabled."""
        if not self._should_check_auth(request):
            return await call_next(request)

        if not self._is_valid_api_key(request):
            client_host = request.client.host if request.client else "unknown"
            logger.warning(
                f"Unauthorized: {client_host} tried to access {request.url.path} without valid API key"
            )
            return Response(
                content="Unauthorized: Invalid or missing API key",
                status_code=401,
                headers={"WWW-Authenticate": 'ApiKey realm="Gateway"'},
                media_type="text/plain",
            )

        return await call_next(request)
