"""
LM Studio SDK Client Service.
Singleton service for LM Studio SDK client with connection management and retry logic.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from .settings import settings

logger = logging.getLogger("lmstudio_gateway.lm_studio_client")

# Import LM Studio SDK
try:
    import lmstudio as lms
    HAS_SDK = True
except ImportError:
    HAS_SDK = False
    logger.warning("LM Studio Python SDK not found. Install with: pip install lmstudio")


class LMStudioClientService:
    """
    Singleton service for LM Studio SDK client.

    Equivalent to TypeScript lmStudioClient.ts service.
    Provides connection management, retry logic, and model operations.
    """

    _instance: Optional[LMStudioClientService] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if LMStudioClientService._initialized:
            return

        self.client: Optional[Any] = None
        self._connecting: Optional[asyncio.Task] = None
        self.max_retries = 3
        self.retry_delay_ms = 2000
        LMStudioClientService._initialized = True
        logger.info("LMStudioClientService initialized")

    async def get_client(self) -> Any:
        """
        Get or create LMStudioClient connection.

        Returns:
            Connected LMStudioClient instance

        Raises:
            ConnectionError: If connection fails after retries
            RuntimeError: If SDK is not available
        """
        if not HAS_SDK:
            raise RuntimeError(
                "LM Studio Python SDK not found. Install with: pip install lmstudio"
            )

        # Return existing client if connected
        if self.client is not None:
            return self.client

        # Wait for existing connection attempt
        if self._connecting is not None:
            await self._connecting
            return self.client

        # Start new connection
        self._connecting = asyncio.create_task(self._connect())
        await self._connecting
        self._connecting = None

        return self.client

    async def _connect(self) -> Any:
        """Connect to LM Studio with retry logic."""
        base_url = str(settings.LMSTUDIO_BASE_URL)

        # Convert HTTP URL to WebSocket URL for SDK connection
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "Connecting to LM Studio SDK (attempt %d/%d)",
                    attempt,
                    self.max_retries,
                    extra={
                        "url": ws_url,
                        "attempt": attempt,
                        "max_retries": self.max_retries
                    }
                )

                # Use default client which connects to local LM Studio
                client = lms.get_default_client()

                # Test connection by listing downloaded models
                try:
                    await asyncio.to_thread(client.system.list_downloaded_models)
                except Exception as test_error:
                    logger.warning("Connection test failed: %s", test_error)
                    raise

                logger.info(
                    "Successfully connected to LM Studio SDK",
                    extra={"url": ws_url, "attempt": attempt}
                )

                self.client = client
                return client

            except Exception as error:
                logger.warning(
                    "Failed to connect to LM Studio SDK",
                    extra={
                        "url": ws_url,
                        "attempt": attempt,
                        "max_retries": self.max_retries,
                        "error": str(error)
                    }
                )

                if attempt < self.max_retries:
                    delay_sec = self.retry_delay_ms / 1000
                    logger.info("Retrying in %.1fs...", delay_sec)
                    await asyncio.sleep(delay_sec)
                else:
                    error_msg = (
                        f"Failed to connect to LM Studio SDK after {self.max_retries} attempts. "
                        "Ensure LM Studio is running and the API server is enabled."
                    )
                    logger.error(error_msg, extra={"url": ws_url})
                    raise ConnectionError(error_msg) from error

        raise ConnectionError("Connection failed")

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.client is not None

    async def health_check(self) -> bool:
        """
        Verify connection is alive.

        Returns:
            True if connected and responsive, False otherwise
        """
        try:
            if self.client is None:
                return False

            # Test connection by listing downloaded models
            await asyncio.to_thread(self.client.system.list_downloaded_models)
            return True

        except Exception as error:
            logger.warning(
                "LM Studio SDK health check failed: %s",
                error,
                extra={"error": str(error)}
            )

            # Invalidate client on failure
            self.client = None
            self._connecting = None

            return False

    async def disconnect(self):
        """Disconnect from LM Studio."""
        if self.client is not None:
            logger.info("Disconnecting from LM Studio SDK")
            # SDK cleanup if needed
            self.client = None
            self._connecting = None


# Singleton instance getter
def get_lm_studio_client() -> LMStudioClientService:
    """Get singleton LMStudioClientService instance."""
    return LMStudioClientService()
