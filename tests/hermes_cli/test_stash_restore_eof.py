"""Tests for EOFError handling in _restore_stashed_changes prompts.

When ``hermes update`` runs in a non-TTY environment (CI, systemd, piped
stdin), ``input()`` raises ``EOFError``.  The prompts inside
``_restore_stashed_changes`` must catch this and default to skipping the
restore rather than crashing.
"""

from pathlib import Path
from unittest.mock import patch
import pytest

from hermes_cli.main import _restore_stashed_changes


class TestRestoreStashEOFError:
    """hermes_cli/main.py — _restore_stashed_changes()"""

    @patch("builtins.input", side_effect=EOFError)
    def test_eof_on_restore_prompt_skips_restore(self, _input):
        """EOFError on 'Restore local changes?' defaults to skip."""
        result = _restore_stashed_changes(
            git_cmd=["git"],
            cwd=Path("/tmp"),
            stash_ref="stash@{0}",
            prompt_user=True,
        )
        assert result is False

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_keyboard_interrupt_on_restore_prompt_skips(self, _input):
        """KeyboardInterrupt on 'Restore local changes?' defaults to skip."""
        result = _restore_stashed_changes(
            git_cmd=["git"],
            cwd=Path("/tmp"),
            stash_ref="stash@{0}",
            prompt_user=True,
        )
        assert result is False
