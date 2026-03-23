"""Tests for browser_navigate URL scheme and SSRF validation."""

import json
from unittest.mock import patch

from tools.browser_tool import browser_navigate


class TestBrowserUrlSchemeValidation:
    """browser_navigate must reject non-http(s) schemes."""

    def test_file_scheme_blocked(self):
        result = json.loads(browser_navigate("file:///etc/shadow"))
        assert result["success"] is False
        assert "scheme" in result["error"].lower()

    def test_javascript_scheme_blocked(self):
        result = json.loads(browser_navigate("javascript:alert(1)"))
        assert result["success"] is False
        assert "scheme" in result["error"].lower()

    def test_data_scheme_blocked(self):
        result = json.loads(browser_navigate("data:text/html,<h1>pwned</h1>"))
        assert result["success"] is False
        assert "scheme" in result["error"].lower()

    def test_ftp_scheme_blocked(self):
        result = json.loads(browser_navigate("ftp://evil.com/malware"))
        assert result["success"] is False
        assert "scheme" in result["error"].lower()

    def test_http_scheme_allowed(self):
        """http URLs should pass scheme check (may fail later on browser connect)."""
        with patch("tools.browser_tool._run_browser_command",
                    return_value={"success": True, "data": {"title": "Test", "url": "http://example.com"}}):
            with patch("tools.browser_tool.check_website_access", return_value=None):
                with patch("tools.browser_tool._get_session_info", return_value={"_first_nav": False}):
                    result = json.loads(browser_navigate("http://example.com"))
                    assert result.get("success") is True or "error" not in result or "scheme" not in result.get("error", "")

    def test_https_scheme_allowed(self):
        """https URLs should pass scheme check."""
        with patch("tools.browser_tool._run_browser_command",
                    return_value={"success": True, "data": {"title": "Test", "url": "https://example.com"}}):
            with patch("tools.browser_tool.check_website_access", return_value=None):
                with patch("tools.browser_tool._get_session_info", return_value={"_first_nav": False}):
                    result = json.loads(browser_navigate("https://example.com"))
                    assert "scheme" not in result.get("error", "")
