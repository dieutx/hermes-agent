"""Tests for session counter preservation across agent re-init.

Commands like /reasoning, /prompt, and /personality need to change agent
config without wiping token counters and cost data. /reasoning updates
the agent in place; /prompt and /personality use _reinit_agent_preserve_counters.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _make_cli_stub():
    """Build a minimal CLI object with the counter-preservation methods."""
    from cli import HermesCLI

    cli = HermesCLI.__new__(HermesCLI)
    cli._pending_counter_restore = None

    # Fake agent with some usage
    agent = MagicMock()
    agent.session_total_tokens = 5000
    agent.session_input_tokens = 3000
    agent.session_output_tokens = 2000
    agent.session_prompt_tokens = 3000
    agent.session_completion_tokens = 2000
    agent.session_cache_read_tokens = 100
    agent.session_cache_write_tokens = 500
    agent.session_reasoning_tokens = 0
    agent.session_api_calls = 3
    agent.session_estimated_cost_usd = 0.25
    agent.session_cost_status = "estimated"
    agent.session_cost_source = "official_docs_snapshot"
    agent.reasoning_config = None
    cli.agent = agent
    return cli


class TestReasoningUpdatesInPlace:

    def test_reasoning_config_set_on_existing_agent(self):
        """When agent exists, /reasoning should update config in place, not destroy."""
        cli = _make_cli_stub()
        old_agent = cli.agent

        # Simulate what the /reasoning handler does
        parsed = {"enabled": True, "effort": "high"}
        cli.reasoning_config = parsed
        if cli.agent:
            cli.agent.reasoning_config = parsed

        assert cli.agent is old_agent  # same object, not destroyed
        assert cli.agent.reasoning_config == {"enabled": True, "effort": "high"}
        assert cli.agent.session_total_tokens == 5000  # counters preserved


class TestReinitPreservesCounters:

    def test_counters_saved_before_destroy(self):
        cli = _make_cli_stub()
        cli._reinit_agent_preserve_counters()

        assert cli.agent is None
        assert cli._pending_counter_restore["session_total_tokens"] == 5000
        assert cli._pending_counter_restore["session_api_calls"] == 3

    def test_counters_restored_onto_new_agent(self):
        cli = _make_cli_stub()
        cli._reinit_agent_preserve_counters()

        cli.agent = SimpleNamespace(
            session_total_tokens=0, session_input_tokens=0, session_output_tokens=0,
            session_prompt_tokens=0, session_completion_tokens=0,
            session_cache_read_tokens=0, session_cache_write_tokens=0,
            session_reasoning_tokens=0, session_api_calls=0,
            session_estimated_cost_usd=0.0, session_cost_status="unknown",
            session_cost_source="none",
        )
        cli._restore_counters_if_pending()

        assert cli.agent.session_total_tokens == 5000
        assert cli.agent.session_api_calls == 3

    def test_no_pending_restore_is_noop(self):
        cli = _make_cli_stub()
        cli._restore_counters_if_pending()
        assert cli.agent.session_total_tokens == 5000

    def test_restore_clears_pending(self):
        cli = _make_cli_stub()
        cli._reinit_agent_preserve_counters()
        cli.agent = SimpleNamespace(**{f: 0 for f in cli._SESSION_COUNTER_FIELDS})
        cli._restore_counters_if_pending()
        assert cli._pending_counter_restore is None
