"""Tests for SSRF protection in gateway media download functions.

Verifies that cache_image_from_url and cache_audio_from_url block
requests to private/internal addresses before making any HTTP call.
"""

import asyncio
from unittest.mock import patch, AsyncMock
import pytest

from gateway.platforms.base import cache_image_from_url, cache_audio_from_url


# ── Image download ────────────────────────────────────────────────────────

def test_image_blocks_metadata_endpoint():
    with pytest.raises(ValueError, match="private/internal"):
        asyncio.run(cache_image_from_url("http://169.254.169.254/latest/meta-data/"))


def test_image_blocks_localhost():
    with pytest.raises(ValueError, match="private/internal"):
        asyncio.run(cache_image_from_url("http://127.0.0.1:8080/secret.jpg"))


def test_image_blocks_private_network():
    with pytest.raises(ValueError, match="private/internal"):
        asyncio.run(cache_image_from_url("http://192.168.1.1/admin/logo.png"))


def test_image_blocks_link_local():
    with pytest.raises(ValueError, match="private/internal"):
        asyncio.run(cache_image_from_url("http://169.254.1.1/internal"))


@patch("gateway.platforms.base._is_safe_url", return_value=True)
def test_image_allows_public_url(_safe):
    """Public URLs proceed to the HTTP call (mocked)."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b"\x89PNG\r\n\x1a\n"
    mock_response.raise_for_status = lambda: None

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(cache_image_from_url("https://example.com/photo.jpg"))
        assert result.endswith(".jpg")


# ── Audio download ────────────────────────────────────────────────────────

def test_audio_blocks_metadata_endpoint():
    with pytest.raises(ValueError, match="private/internal"):
        asyncio.run(cache_audio_from_url("http://169.254.169.254/latest/meta-data/"))


def test_audio_blocks_localhost():
    with pytest.raises(ValueError, match="private/internal"):
        asyncio.run(cache_audio_from_url("http://127.0.0.1:9000/internal.ogg"))


@patch("gateway.platforms.base._is_safe_url", return_value=True)
def test_audio_allows_public_url(_safe):
    """Public URLs proceed to the HTTP call (mocked)."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b"OggS\x00\x02"
    mock_response.raise_for_status = lambda: None

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(cache_audio_from_url("https://example.com/voice.ogg"))
        assert result.endswith(".ogg")
