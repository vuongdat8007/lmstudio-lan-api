"""Application settings using Pydantic Settings."""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Gateway settings
    GATEWAY_HOST: str = Field(default="10.0.0.181", description="Gateway bind host")
    GATEWAY_PORT: int = Field(default=8001, ge=1, le=65535, description="Gateway bind port")

    # llama-server settings
    LLAMA_SERVER_HOST: str = Field(default="10.0.0.181", description="llama-server host")
    LLAMA_SERVER_PORT: int = Field(default=8080, ge=1, le=65535, description="llama-server port")
    LLAMA_SERVER_BINARY: str = Field(default="llama-server", description="Path to llama-server binary")
    MODEL_REGISTRY_PATH: str = Field(default="models/registry.json", description="Path to model registry JSON")

    # Security settings
    GATEWAY_API_KEY: Optional[str] = Field(default=None, description="API key for authentication")
    IP_ALLOWLIST: str = Field(default="*", description="Comma-separated IP addresses or CIDR ranges")
    REQUIRE_AUTH_FOR_HEALTH: bool = Field(default=False, description="Require authentication for /health endpoint")

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_DIR: str = Field(default="logs", description="Directory for log files")

    # Process management settings
    STARTUP_TIMEOUT: int = Field(default=120, ge=10, description="Max seconds to wait for llama-server startup")
    SHUTDOWN_TIMEOUT: int = Field(default=30, ge=5, description="Max seconds to wait for graceful shutdown")
    HEALTH_CHECK_INTERVAL: int = Field(default=5, ge=1, description="Health check interval in seconds")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper

    @property
    def llama_server_base_url(self) -> str:
        """Get the base URL for llama-server."""
        return f"http://{self.LLAMA_SERVER_HOST}:{self.LLAMA_SERVER_PORT}"

    @property
    def is_api_key_enabled(self) -> bool:
        """Check if API key authentication is enabled."""
        return self.GATEWAY_API_KEY is not None and len(self.GATEWAY_API_KEY.strip()) > 0


# Global settings instance
settings = Settings()
