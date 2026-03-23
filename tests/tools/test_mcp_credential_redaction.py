"""Tests for MCP credential redaction in both error and success paths."""

from tools.mcp_tool import _sanitize_error


class TestCredentialRedaction:
    def test_redacts_openai_key(self):
        assert "[REDACTED]" in _sanitize_error("key is sk-abc123def456")

    def test_redacts_github_pat(self):
        assert "[REDACTED]" in _sanitize_error("token: ghp_xxxxxxxxxxxx")

    def test_redacts_bearer_token(self):
        assert "[REDACTED]" in _sanitize_error("Authorization: Bearer eyJhbGci")

    def test_redacts_token_param(self):
        assert "[REDACTED]" in _sanitize_error("url?token=secret123&foo=bar")

    def test_redacts_password_param(self):
        assert "[REDACTED]" in _sanitize_error("password=hunter2")

    def test_preserves_normal_text(self):
        text = "Query returned 42 rows from users table"
        assert _sanitize_error(text) == text

    def test_redacts_multiple_credentials(self):
        text = "key=sk-abc123 and token=ghp_xyz789"
        result = _sanitize_error(text)
        assert "sk-abc123" not in result
        assert "ghp_xyz789" not in result
        assert "[REDACTED]" in result
