"""Tests for local file exfiltration guard in extract_local_files.

extract_local_files scans model responses for bare file paths and sends
matching files as chat attachments. Without restriction, a prompt
injection can exfiltrate any local media file by making the model
mention its path. The guard restricts extraction to agent-managed
directories (tmp, image/audio/document caches).
"""

import os
import tempfile
from pathlib import Path

from gateway.platforms.base import (
    BasePlatformAdapter,
    get_image_cache_dir,
    get_audio_cache_dir,
    DOCUMENT_CACHE_DIR,
)


class TestLocalFileExfilGuard:

    def test_private_home_photo_blocked(self):
        """Files in ~/Pictures or other home dirs must not be extracted."""
        photo_dir = Path.home() / "Pictures"
        photo_dir.mkdir(exist_ok=True)
        photo = photo_dir / "_test_exfil_guard.jpg"
        photo.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 50)
        try:
            files, _ = BasePlatformAdapter.extract_local_files(
                f"Check out {photo}"
            )
            assert files == [], "private file outside safe dirs should be blocked"
        finally:
            photo.unlink(missing_ok=True)

    def test_tmp_file_allowed(self):
        """Files in /tmp (agent-generated) should be allowed."""
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
        tmp.close()
        try:
            files, _ = BasePlatformAdapter.extract_local_files(
                f"Chart saved to {tmp.name}"
            )
            assert len(files) == 1
            assert files[0] == os.path.realpath(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_image_cache_allowed(self):
        """Files in the hermes image cache should be allowed."""
        cache = get_image_cache_dir()
        test_file = cache / "test_guard.png"
        test_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
        try:
            files, _ = BasePlatformAdapter.extract_local_files(
                f"Here is the image: {test_file}"
            )
            assert len(files) == 1
        finally:
            test_file.unlink()

    def test_arbitrary_absolute_path_blocked(self):
        """Absolute paths outside safe dirs must be blocked."""
        secret_dir = Path.home() / ".test_exfil_guard"
        secret_dir.mkdir(exist_ok=True)
        secret = secret_dir / "secret_screenshot.png"
        secret.write_bytes(b"\x89PNG" + b"\x00" * 50)
        try:
            files, _ = BasePlatformAdapter.extract_local_files(
                f"Found an interesting file at {secret}"
            )
            assert files == [], "arbitrary absolute path should be blocked"
        finally:
            secret.unlink(missing_ok=True)
            secret_dir.rmdir()

    def test_no_files_returns_empty(self):
        """Response with no paths returns empty list."""
        files, cleaned = BasePlatformAdapter.extract_local_files(
            "Hello, how can I help you today?"
        )
        assert files == []
        assert "Hello" in cleaned
