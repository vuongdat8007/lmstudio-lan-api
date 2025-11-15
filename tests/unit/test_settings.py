# tests/unit/test_settings.py
"""Unit tests for settings module."""
import pytest
from pydantic import ValidationError

from lmstudio_gateway.settings import Settings


def test_settings_default_values():
    """Test that settings load with default values."""
    settings = Settings(_env_file=None)  # Don't load .env file

    assert str(settings.LMSTUDIO_BASE_URL) == "http://127.0.0.1:1234/"
    assert settings.GATEWAY_HOST == "0.0.0.0"
    assert settings.GATEWAY_PORT == 8001
    assert settings.GATEWAY_API_KEY == ""
    assert settings.IP_ALLOWLIST == "*"
    assert settings.REQUIRE_AUTH_FOR_HEALTH is False
    assert settings.LOG_LEVEL == "INFO"


def test_settings_log_level_validation():
    """Test that LOG_LEVEL validation works correctly."""
    # Valid log levels
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        settings = Settings(_env_file=None, LOG_LEVEL=level)
        assert settings.LOG_LEVEL == level

    # Case insensitive
    settings = Settings(_env_file=None, LOG_LEVEL="debug")
    assert settings.LOG_LEVEL == "DEBUG"

    # Invalid log level
    with pytest.raises(ValidationError):
        Settings(_env_file=None, LOG_LEVEL="INVALID")


def test_settings_ip_allowlist_items():
    """Test IP allowlist parsing."""
    # Wildcard
    settings = Settings(_env_file=None, IP_ALLOWLIST="*")
    assert settings.ip_allowlist_items == ["*"]

    # Single IP
    settings = Settings(_env_file=None, IP_ALLOWLIST="192.168.0.1")
    assert settings.ip_allowlist_items == ["192.168.0.1"]

    # Multiple IPs
    settings = Settings(
        _env_file=None,
        IP_ALLOWLIST="192.168.0.1,10.0.0.1,172.16.0.1"
    )
    assert settings.ip_allowlist_items == ["192.168.0.1", "10.0.0.1", "172.16.0.1"]

    # CIDR ranges
    settings = Settings(
        _env_file=None,
        IP_ALLOWLIST="192.168.0.0/24,10.0.0.0/16"
    )
    assert settings.ip_allowlist_items == ["192.168.0.0/24", "10.0.0.0/16"]

    # Empty allowlist
    settings = Settings(_env_file=None, IP_ALLOWLIST="")
    assert settings.ip_allowlist_items == []

    # Whitespace handling
    settings = Settings(
        _env_file=None,
        IP_ALLOWLIST="  192.168.0.1  ,  10.0.0.1  "
    )
    assert settings.ip_allowlist_items == ["192.168.0.1", "10.0.0.1"]


def test_settings_api_key_enabled():
    """Test api_key_enabled property."""
    # API key disabled (empty string)
    settings = Settings(_env_file=None, GATEWAY_API_KEY="")
    assert settings.api_key_enabled is False

    # API key enabled
    settings = Settings(_env_file=None, GATEWAY_API_KEY="secret-key")
    assert settings.api_key_enabled is True
