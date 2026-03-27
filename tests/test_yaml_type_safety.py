"""Tests for YAML type safety across config parsing.

YAML has two gotchas that cause crashes or silent misbehavior:

1. ``null`` / ``~`` for a present key makes ``dict.get(key, default)``
   return ``None`` instead of the default — ``.lower()`` crashes.

2. Bare ``off``/``on``/``yes``/``no`` are parsed as booleans, not strings.
   String comparisons like ``!= "off"`` silently pass.
"""

import pytest

# ── Null coalescing (config.get returns None) ─────────────────────────

from tools.tts_tool import _get_provider, DEFAULT_PROVIDER


class TestNullGuard:

    def test_tts_null_provider_returns_default(self):
        result = _get_provider({"provider": None})
        assert result == DEFAULT_PROVIDER.lower().strip()

    def test_tts_missing_provider_returns_default(self):
        result = _get_provider({})
        assert result == DEFAULT_PROVIDER.lower().strip()

    def test_tts_valid_provider_passed_through(self):
        assert _get_provider({"provider": "OPENAI"}) == "openai"

    def test_mcp_null_auth_does_not_crash(self):
        config = {"auth": None, "timeout": 30}
        auth_type = (config.get("auth") or "").lower().strip()
        assert auth_type == ""

    def test_web_null_backend_does_not_crash(self):
        from unittest.mock import patch
        with patch("tools.web_tools._load_web_config", return_value={"backend": None}):
            from tools.web_tools import _get_backend
            result = _get_backend()
            assert isinstance(result, str)

    def test_compressor_null_base_url_does_not_crash(self):
        from trajectory_compressor import CompressionConfig, TrajectoryCompressor
        config = CompressionConfig()
        config.base_url = None
        compressor = TrajectoryCompressor.__new__(TrajectoryCompressor)
        compressor.config = config
        result = compressor._detect_provider()
        assert result == ""

    def test_compressor_config_null_base_url_keeps_default(self):
        from trajectory_compressor import CompressionConfig
        from hermes_constants import OPENROUTER_BASE_URL
        config = CompressionConfig()
        data = {"summarization": {"base_url": None}}
        config.base_url = data["summarization"].get("base_url") or config.base_url
        assert config.base_url == OPENROUTER_BASE_URL


# ── Boolean coercion (YAML off → False) ──────────────────────────────

from gateway.config import StreamingConfig, PlatformConfig


class TestBooleanCoercion:

    def test_streaming_transport_false_becomes_off(self):
        config = StreamingConfig.from_dict({"enabled": True, "transport": False})
        assert config.transport == "off"

    def test_streaming_transport_true_becomes_edit(self):
        config = StreamingConfig.from_dict({"enabled": True, "transport": True})
        assert config.transport == "edit"

    def test_streaming_transport_string_off_preserved(self):
        config = StreamingConfig.from_dict({"enabled": True, "transport": "off"})
        assert config.transport == "off"

    def test_streaming_transport_missing_defaults_to_edit(self):
        config = StreamingConfig.from_dict({"enabled": True})
        assert config.transport == "edit"

    def test_reply_to_mode_false_becomes_off(self):
        config = PlatformConfig.from_dict({"reply_to_mode": False})
        assert config.reply_to_mode == "off"

    def test_reply_to_mode_string_off_preserved(self):
        config = PlatformConfig.from_dict({"reply_to_mode": "off"})
        assert config.reply_to_mode == "off"

    def test_reply_to_mode_string_first_preserved(self):
        config = PlatformConfig.from_dict({"reply_to_mode": "first"})
        assert config.reply_to_mode == "first"

    def test_reply_to_mode_missing_defaults_to_first(self):
        config = PlatformConfig.from_dict({})
        assert config.reply_to_mode == "first"
