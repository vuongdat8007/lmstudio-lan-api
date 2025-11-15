# src/lmstudio_gateway/settings.py
"""
Settings module for LM Studio LAN Gateway.
Uses Pydantic Settings for environment variable configuration.
"""
from __future__ import annotations

from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be configured via .env file or environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # LM Studio configuration
    LMSTUDIO_BASE_URL: AnyHttpUrl = "http://127.0.0.1:1234"  # type: ignore

    # Gateway bind settings
    GATEWAY_HOST: str = "0.0.0.0"
    GATEWAY_PORT: int = 8001

    # Security: API key authentication
    GATEWAY_API_KEY: str = ""  # Empty string disables API key auth

    # Security: IP allow-listing
    # Comma-separated list of IPs, CIDR ranges, or "*" for all
    IP_ALLOWLIST: str = "*"

    # Health endpoint authentication
    REQUIRE_AUTH_FOR_HEALTH: bool = False

    # Logging configuration
    LOG_LEVEL: str = "INFO"

    @property
    def ip_allowlist_items(self) -> List[str]:
        """
        Parse IP_ALLOWLIST into a list of items.

        Returns:
            List of IP addresses, CIDR ranges, or "*"
        """
        raw = (self.IP_ALLOWLIST or "").strip()
        if not raw:
            return []
        return [x.strip() for x in raw.split(",") if x.strip()]

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """
        Validate LOG_LEVEL is a valid Python logging level.

        Args:
            v: Log level string

        Returns:
            Uppercase log level

        Raises:
            ValueError: If log level is invalid
        """
        v = v.upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in valid_levels:
            raise ValueError(
                f"LOG_LEVEL must be one of {valid_levels}, got '{v}'"
            )
        return v

    @property
    def api_key_enabled(self) -> bool:
        """Check if API key authentication is enabled."""
        return bool(self.GATEWAY_API_KEY)


# Global settings instance
settings = Settings()
