# tests/unit/test_middleware.py
"""Unit tests for middleware module."""
import pytest

from lmstudio_gateway.middleware import _ip_in_allowlist


def test_ip_in_allowlist_wildcard():
    """Test that wildcard allows all IPs."""
    assert _ip_in_allowlist("192.168.0.1", ["*"]) is True
    assert _ip_in_allowlist("10.0.0.1", ["*"]) is True
    assert _ip_in_allowlist("172.16.0.1", ["*"]) is True


def test_ip_in_allowlist_single_ip():
    """Test single IP matching."""
    allowlist = ["192.168.0.10"]

    assert _ip_in_allowlist("192.168.0.10", allowlist) is True
    assert _ip_in_allowlist("192.168.0.11", allowlist) is False
    assert _ip_in_allowlist("10.0.0.1", allowlist) is False


def test_ip_in_allowlist_cidr_range():
    """Test CIDR range matching."""
    allowlist = ["192.168.0.0/24"]

    # IPs in range
    assert _ip_in_allowlist("192.168.0.1", allowlist) is True
    assert _ip_in_allowlist("192.168.0.100", allowlist) is True
    assert _ip_in_allowlist("192.168.0.254", allowlist) is True

    # IPs out of range
    assert _ip_in_allowlist("192.168.1.1", allowlist) is False
    assert _ip_in_allowlist("10.0.0.1", allowlist) is False


def test_ip_in_allowlist_multiple_entries():
    """Test multiple allowlist entries."""
    allowlist = ["192.168.0.0/24", "10.0.0.5", "172.16.0.0/16"]

    # Match first CIDR
    assert _ip_in_allowlist("192.168.0.50", allowlist) is True

    # Match single IP
    assert _ip_in_allowlist("10.0.0.5", allowlist) is True

    # Match second CIDR
    assert _ip_in_allowlist("172.16.10.20", allowlist) is True

    # No match
    assert _ip_in_allowlist("8.8.8.8", allowlist) is False


def test_ip_in_allowlist_empty():
    """Test empty allowlist returns True (allow all)."""
    assert _ip_in_allowlist("192.168.0.1", []) is True
    assert _ip_in_allowlist("10.0.0.1", []) is True


def test_ip_in_allowlist_invalid_entry():
    """Test that invalid entries are skipped with warning."""
    # Invalid CIDR, but has valid IP
    allowlist = ["invalid-cidr", "192.168.0.10"]

    # Should still match valid entry
    assert _ip_in_allowlist("192.168.0.10", allowlist) is True

    # Should not match if only invalid entries
    allowlist_invalid = ["invalid-cidr", "not-an-ip"]
    assert _ip_in_allowlist("192.168.0.1", allowlist_invalid) is False


def test_ip_in_allowlist_ipv4_cidr_notation():
    """Test various CIDR notations."""
    # /32 (single host)
    allowlist = ["192.168.0.10/32"]
    assert _ip_in_allowlist("192.168.0.10", allowlist) is True
    assert _ip_in_allowlist("192.168.0.11", allowlist) is False

    # /16 (large range)
    allowlist = ["10.0.0.0/16"]
    assert _ip_in_allowlist("10.0.0.1", allowlist) is True
    assert _ip_in_allowlist("10.0.255.255", allowlist) is True
    assert _ip_in_allowlist("10.1.0.1", allowlist) is False

    # /8 (class A)
    allowlist = ["172.0.0.0/8"]
    assert _ip_in_allowlist("172.16.0.1", allowlist) is True
    assert _ip_in_allowlist("173.0.0.1", allowlist) is False
