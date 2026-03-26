"""Tests for ffmpeg binary resolution in tts_tool.

Verifies that _find_ffmpeg() checks Homebrew paths (/opt/homebrew/bin,
/usr/local/bin) when ffmpeg is not on the standard PATH — matching the
pattern from transcription_tools._find_binary().
"""

import os
from unittest.mock import patch
from tools.tts_tool import _find_ffmpeg, _has_ffmpeg


class TestFindFfmpeg:

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    def test_finds_ffmpeg_on_path(self, _which):
        assert _find_ffmpeg() == "/usr/bin/ffmpeg"

    @patch("shutil.which", return_value=None)
    @patch("os.path.isfile", return_value=True)
    @patch("os.access", return_value=True)
    def test_finds_ffmpeg_in_homebrew(self, _access, _isfile, _which):
        result = _find_ffmpeg()
        assert result == "/opt/homebrew/bin/ffmpeg"

    @patch("shutil.which", return_value=None)
    @patch("os.path.isfile", return_value=False)
    def test_returns_none_when_not_found(self, _isfile, _which):
        assert _find_ffmpeg() is None

    @patch("shutil.which", return_value=None)
    def test_checks_usr_local_bin(self, _which):
        """Falls through to /usr/local/bin if /opt/homebrew/bin fails."""
        def fake_isfile(p):
            return p == "/usr/local/bin/ffmpeg"

        with patch("os.path.isfile", side_effect=fake_isfile), \
             patch("os.access", return_value=True):
            assert _find_ffmpeg() == "/usr/local/bin/ffmpeg"


class TestHasFfmpeg:

    @patch("tools.tts_tool._find_ffmpeg", return_value="/usr/bin/ffmpeg")
    def test_true_when_found(self, _find):
        assert _has_ffmpeg() is True

    @patch("tools.tts_tool._find_ffmpeg", return_value=None)
    def test_false_when_not_found(self, _find):
        assert _has_ffmpeg() is False
