"""Tests for read-path deny list on sensitive credential files."""

import os
from pathlib import Path
from unittest.mock import patch

from tools.file_operations import _is_read_denied


_HOME = str(Path.home())


class TestIsReadDenied:
    def test_hermes_env_blocked(self):
        assert _is_read_denied(os.path.join(_HOME, ".hermes", ".env")) is True

    def test_hermes_auth_json_blocked(self):
        assert _is_read_denied(os.path.join(_HOME, ".hermes", "auth.json")) is True

    def test_ssh_private_key_blocked(self):
        assert _is_read_denied(os.path.join(_HOME, ".ssh", "id_rsa")) is True
        assert _is_read_denied(os.path.join(_HOME, ".ssh", "id_ed25519")) is True

    def test_etc_shadow_blocked(self):
        assert _is_read_denied("/etc/shadow") is True

    def test_aws_credentials_blocked(self):
        assert _is_read_denied(os.path.join(_HOME, ".aws", "credentials")) is True

    def test_gnupg_dir_blocked(self):
        assert _is_read_denied(os.path.join(_HOME, ".gnupg", "private-keys-v1.d", "key")) is True

    def test_kube_config_blocked(self):
        assert _is_read_denied(os.path.join(_HOME, ".kube", "config")) is True

    def test_normal_project_file_allowed(self):
        assert _is_read_denied("/tmp/test.py") is False

    def test_relative_path_allowed(self):
        assert _is_read_denied("src/main.py") is False

    def test_tilde_expansion_blocked(self):
        assert _is_read_denied("~/.hermes/.env") is True

    def test_traversal_to_shadow_blocked(self):
        assert _is_read_denied("/tmp/../etc/shadow") is True

    def test_netrc_blocked(self):
        assert _is_read_denied(os.path.join(_HOME, ".netrc")) is True

    def test_hermes_config_yaml_allowed(self):
        """config.yaml is not a secret — should be readable."""
        assert _is_read_denied(os.path.join(_HOME, ".hermes", "config.yaml")) is False

    def test_hermes_sessions_allowed(self):
        """Session files should be readable."""
        assert _is_read_denied(os.path.join(_HOME, ".hermes", "sessions", "test.json")) is False
