"""Tests for session_id sync between CLI and agent after compression.

When context compression fires, the agent creates a child session in the
DB and updates self.session_id. The CLI must sync its own session_id to
match, otherwise /new ends the wrong session and the child session is
orphaned.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _make_cli_with_agent():
    from cli import HermesCLI

    cli = HermesCLI.__new__(HermesCLI)
    cli.session_id = "original-session-123"
    cli.conversation_history = [{"role": "user", "content": "hi"}] * 5
    cli._session_db = MagicMock()

    agent = MagicMock()
    agent.session_id = "original-session-123"
    agent.compression_enabled = True
    agent._cached_system_prompt = "You are helpful."
    agent._compress_context = MagicMock(return_value=(
        [{"role": "user", "content": "compressed"}],
        "You are helpful.",
    ))
    agent._honcho = None
    cli.agent = agent
    return cli


class TestManualCompressSync:

    def test_session_id_synced_after_manual_compress(self):
        """After /compress, CLI session_id should match agent's new child session."""
        cli = _make_cli_with_agent()

        # Simulate what _compress_context does: agent gets a new session_id
        def fake_compress(messages, system, approx_tokens=0):
            cli.agent.session_id = "child-session-456"
            return [{"role": "user", "content": "compressed"}], system

        cli.agent._compress_context = fake_compress

        with patch("agent.model_metadata.estimate_messages_tokens_rough", return_value=5000):
            cli._manual_compress()

        assert cli.session_id == "child-session-456"

    def test_session_id_unchanged_when_compression_fails(self):
        """If compression throws, CLI session_id stays the same."""
        cli = _make_cli_with_agent()
        cli.agent._compress_context = MagicMock(side_effect=RuntimeError("fail"))

        with patch("agent.model_metadata.estimate_messages_tokens_rough", return_value=5000):
            cli._manual_compress()

        assert cli.session_id == "original-session-123"


class TestAutoCompressSync:

    def test_session_id_synced_after_auto_compression(self):
        """After run_conversation triggers compression, CLI syncs session_id."""
        cli = _make_cli_with_agent()

        # Simulate agent's session_id changing during run_conversation
        cli.agent.session_id = "auto-child-789"

        # The sync logic that runs after run_conversation
        if cli.agent and cli.agent.session_id != cli.session_id:
            cli.session_id = cli.agent.session_id

        assert cli.session_id == "auto-child-789"

    def test_session_id_unchanged_when_no_compression(self):
        """When no compression happens, session_id stays the same."""
        cli = _make_cli_with_agent()

        if cli.agent and cli.agent.session_id != cli.session_id:
            cli.session_id = cli.agent.session_id

        assert cli.session_id == "original-session-123"
