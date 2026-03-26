"""Tests for the running process limit enforced in ProcessRegistry.spawn_local/spawn_via_env."""

import time
import pytest
from unittest.mock import MagicMock, patch

from tools.process_registry import (
    ProcessRegistry,
    ProcessSession,
    MAX_PROCESSES,
)


@pytest.fixture()
def registry():
    return ProcessRegistry()


def _make_running_session(sid: str) -> ProcessSession:
    return ProcessSession(
        id=sid,
        command="sleep 60",
        task_id="t1",
        started_at=time.time(),
        exited=False,
    )


def _fill_running(registry: ProcessRegistry, count: int):
    """Insert `count` sessions directly into _running."""
    for i in range(count):
        s = _make_running_session(f"proc_fill_{i}")
        registry._running[s.id] = s


# =========================================================================
# _check_running_limit unit tests
# =========================================================================

class TestCheckRunningLimit:
    def test_empty_registry_allows_spawn(self, registry):
        """No running processes — limit check should not raise."""
        registry._check_running_limit()  # must not raise

    def test_under_limit_allows_spawn(self, registry):
        """One below MAX_PROCESSES — still allowed."""
        _fill_running(registry, MAX_PROCESSES - 1)
        registry._check_running_limit()  # must not raise

    def test_exactly_at_limit_raises(self, registry):
        """Exactly at MAX_PROCESSES — must be rejected."""
        _fill_running(registry, MAX_PROCESSES)
        with pytest.raises(RuntimeError, match="Cannot spawn"):
            registry._check_running_limit()

    def test_over_limit_raises(self, registry):
        """More than MAX_PROCESSES in _running — must be rejected."""
        _fill_running(registry, MAX_PROCESSES + 1)
        with pytest.raises(RuntimeError, match="Cannot spawn"):
            registry._check_running_limit()

    def test_error_message_mentions_kill(self, registry):
        """Error message should tell the user how to free up slots."""
        _fill_running(registry, MAX_PROCESSES)
        with pytest.raises(RuntimeError, match="kill"):
            registry._check_running_limit()


# =========================================================================
# spawn_local enforces limit
# =========================================================================

class TestSpawnLocalLimit:
    def _make_fake_popen(self):
        proc = MagicMock()
        proc.pid = 12345
        proc.stdout = iter([])
        proc.stdin = MagicMock()
        proc.poll.return_value = None
        return proc

    def test_spawn_local_rejected_at_limit(self, registry):
        """spawn_local raises RuntimeError when the running limit is reached."""
        _fill_running(registry, MAX_PROCESSES)

        with patch("tools.process_registry._find_shell", return_value="/bin/bash"), \
             patch("subprocess.Popen", return_value=self._make_fake_popen()), \
             patch("threading.Thread", return_value=MagicMock()), \
             patch.object(registry, "_write_checkpoint"):
            with pytest.raises(RuntimeError, match="Cannot spawn"):
                registry.spawn_local("echo hi", cwd="/tmp")

    def test_spawn_local_allowed_under_limit(self, registry):
        """spawn_local succeeds when one slot remains."""
        _fill_running(registry, MAX_PROCESSES - 1)

        fake_thread = MagicMock()
        with patch("tools.process_registry._find_shell", return_value="/bin/bash"), \
             patch("subprocess.Popen", return_value=self._make_fake_popen()), \
             patch("threading.Thread", return_value=fake_thread), \
             patch.object(registry, "_write_checkpoint"):
            session = registry.spawn_local("echo hi", cwd="/tmp")

        assert session.id.startswith("proc_")
        assert session.command == "echo hi"

    def test_spawn_local_allowed_with_empty_registry(self, registry):
        """spawn_local succeeds on a fresh registry with no existing processes."""
        fake_thread = MagicMock()
        with patch("tools.process_registry._find_shell", return_value="/bin/bash"), \
             patch("subprocess.Popen", return_value=self._make_fake_popen()), \
             patch("threading.Thread", return_value=fake_thread), \
             patch.object(registry, "_write_checkpoint"):
            session = registry.spawn_local("echo hello", cwd="/tmp")

        assert session.id.startswith("proc_")


# =========================================================================
# spawn_via_env enforces limit
# =========================================================================

class TestSpawnViaEnvLimit:
    def _make_fake_env(self):
        env = MagicMock()
        env.execute.return_value = {"output": "12345"}
        return env

    def test_spawn_via_env_rejected_at_limit(self, registry):
        """spawn_via_env raises RuntimeError when the running limit is reached."""
        _fill_running(registry, MAX_PROCESSES)

        with patch("threading.Thread", return_value=MagicMock()), \
             patch.object(registry, "_write_checkpoint"):
            with pytest.raises(RuntimeError, match="Cannot spawn"):
                registry.spawn_via_env(self._make_fake_env(), "echo hi")

    def test_spawn_via_env_allowed_under_limit(self, registry):
        """spawn_via_env succeeds when one slot remains."""
        _fill_running(registry, MAX_PROCESSES - 1)

        with patch("threading.Thread", return_value=MagicMock()), \
             patch.object(registry, "_write_checkpoint"):
            session = registry.spawn_via_env(self._make_fake_env(), "echo hi")

        assert session.id.startswith("proc_")
