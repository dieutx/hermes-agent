"""Tests for Twilio webhook signature validation in the SMS adapter.

Without signature validation, any attacker who discovers the webhook URL
can forge inbound SMS messages from any phone number — a complete
authentication bypass.
"""

import base64
import hashlib
import hmac
import urllib.parse
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from gateway.platforms.sms import SmsAdapter


def _compute_twilio_signature(auth_token: str, url: str, params: dict) -> str:
    """Compute a valid Twilio X-Twilio-Signature for testing."""
    sorted_params = sorted(params.items())
    data_string = url + "".join(k + v for k, v in sorted_params)
    return base64.b64encode(
        hmac.new(auth_token.encode(), data_string.encode(), hashlib.sha1).digest()
    ).decode()


def _make_adapter():
    """Build a minimal SMS adapter with a known auth token."""
    config = MagicMock()
    config.enabled = True
    config.api_key = "test_auth_token_abc123"
    config.extra = {}
    with patch.dict("os.environ", {
        "TWILIO_ACCOUNT_SID": "AC_test",
        "TWILIO_AUTH_TOKEN": "test_auth_token_abc123",
        "TWILIO_PHONE_NUMBER": "+15550001234",
    }):
        adapter = SmsAdapter.__new__(SmsAdapter)
        adapter._account_sid = "AC_test"
        adapter._auth_token = "test_auth_token_abc123"
        adapter._from_number = "+15550001234"
    return adapter


def _make_request(signature: str = "", body_params: dict = None, url: str = "https://example.com/webhooks/twilio"):
    """Build a mock aiohttp request."""
    params = body_params or {"From": "+15559998888", "Body": "hello", "To": "+15550001234", "MessageSid": "SM123"}
    body = urllib.parse.urlencode(params).encode()
    req = MagicMock()
    req.headers = {"X-Twilio-Signature": signature} if signature else {}
    req.scheme = "https"
    req.host = "example.com"
    req.path = "/webhooks/twilio"
    return req, body


class TestTwilioSignatureValidation:

    def test_valid_signature_passes(self):
        adapter = _make_adapter()
        url = "https://example.com/webhooks/twilio"
        params = {"From": "+15559998888", "Body": "hello", "To": "+15550001234", "MessageSid": "SM123"}
        sig = _compute_twilio_signature("test_auth_token_abc123", url, params)
        req, body = _make_request(signature=sig, body_params=params)
        assert adapter._validate_twilio_signature(req, body) is True

    def test_missing_signature_rejected(self):
        adapter = _make_adapter()
        req, body = _make_request(signature="")
        req.headers = {}  # no X-Twilio-Signature header
        assert adapter._validate_twilio_signature(req, body) is False

    def test_invalid_signature_rejected(self):
        adapter = _make_adapter()
        req, body = _make_request(signature="dGhpcyBpcyBmYWtl")  # base64("this is fake")
        assert adapter._validate_twilio_signature(req, body) is False

    def test_no_auth_token_skips_validation(self):
        adapter = _make_adapter()
        adapter._auth_token = ""  # no token configured
        req, body = _make_request(signature="")
        req.headers = {}
        assert adapter._validate_twilio_signature(req, body) is True

    def test_public_url_override(self):
        adapter = _make_adapter()
        custom_url = "https://my-domain.com/sms/inbound"
        params = {"From": "+15559998888", "Body": "test", "To": "+15550001234", "MessageSid": "SM456"}
        sig = _compute_twilio_signature("test_auth_token_abc123", custom_url, params)
        req, body = _make_request(signature=sig, body_params=params)

        with patch.dict("os.environ", {"SMS_WEBHOOK_PUBLIC_URL": custom_url}):
            assert adapter._validate_twilio_signature(req, body) is True
