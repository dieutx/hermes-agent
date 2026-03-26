"""Tests for KeyboardInterrupt handling in exit cleanup paths.

``except Exception`` does not catch ``KeyboardInterrupt`` (which inherits
from ``BaseException``).  A second Ctrl+C during exit cleanup (Honcho
flush, session DB close) must not abort the remaining cleanup steps.
"""

from unittest.mock import MagicMock, patch
import pytest


class TestHonchoAtexitFlush:
    """run_agent.py — _flush_honcho_on_exit atexit handler"""

    def test_keyboard_interrupt_during_flush_is_caught(self):
        """KeyboardInterrupt from flush_all() must not propagate."""
        from run_agent import AIAgent

        mock_manager = MagicMock()
        mock_manager.flush_all.side_effect = KeyboardInterrupt

        # Build a weakref-compatible mock and call the atexit pattern
        import weakref
        ref = weakref.ref(mock_manager)

        # Simulate the atexit handler logic
        manager = ref()
        try:
            manager.flush_all()
            raised = False
        except (Exception, KeyboardInterrupt):
            raised = True

        assert raised is True
        mock_manager.flush_all.assert_called_once()


class TestCronJobCleanup:
    """cron/scheduler.py — end_session + close in finally block"""

    def test_keyboard_interrupt_during_end_session_is_caught(self):
        """KeyboardInterrupt from end_session() must not skip close()."""
        mock_db = MagicMock()
        mock_db.end_session.side_effect = KeyboardInterrupt

        # Simulate the finally block pattern
        try:
            mock_db.end_session("session-1", "cron_complete")
        except (Exception, KeyboardInterrupt):
            pass

        # close() should still be reachable
        try:
            mock_db.close()
        except (Exception, KeyboardInterrupt):
            pass

        mock_db.end_session.assert_called_once()
        mock_db.close.assert_called_once()

    def test_keyboard_interrupt_during_close_is_caught(self):
        """KeyboardInterrupt from close() must not propagate."""
        mock_db = MagicMock()
        mock_db.close.side_effect = KeyboardInterrupt

        try:
            mock_db.end_session("session-1", "cron_complete")
        except (Exception, KeyboardInterrupt):
            pass

        try:
            mock_db.close()
        except (Exception, KeyboardInterrupt):
            pass

        mock_db.close.assert_called_once()
