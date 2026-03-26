"""Tests for exponential backoff with jitter in trajectory_compressor.py summarization retries.

Covers:
- Backoff delay increases exponentially across attempts
- Jitter is added (delay is not exactly 2^n * base)
- Max retries is respected (no extra calls after exhaustion)
- Successful call on a later retry returns the result
"""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from trajectory_compressor import (
    CompressionConfig,
    TrajectoryCompressor,
    TrajectoryMetrics,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_compressor(max_retries=3, retry_delay=2):
    """Return a TrajectoryCompressor with tokenizer and summarizer init mocked out."""
    config = CompressionConfig()
    config.max_retries = max_retries
    config.retry_delay = retry_delay
    with patch.object(TrajectoryCompressor, "_init_tokenizer"), \
         patch.object(TrajectoryCompressor, "_init_summarizer"):
        tc = TrajectoryCompressor(config)
    tc._use_call_llm = False
    return tc


def _fake_response(text="[CONTEXT SUMMARY]: summarized content"):
    """Build a minimal response object matching the shape the code expects."""
    msg = SimpleNamespace(content=text)
    choice = SimpleNamespace(message=msg)
    return SimpleNamespace(choices=[choice])


# ---------------------------------------------------------------------------
# Sync _generate_summary
# ---------------------------------------------------------------------------


class TestGenerateSummaryBackoff:
    """Tests for the synchronous _generate_summary retry loop."""

    def test_success_on_first_attempt_no_sleep(self):
        """No sleep should occur when the first call succeeds."""
        tc = _make_compressor()
        metrics = TrajectoryMetrics()

        tc.client = MagicMock()
        tc.client.chat.completions.create.return_value = _fake_response()

        with patch("time.sleep") as mock_sleep:
            result = tc._generate_summary("some content", metrics)

        assert result.startswith("[CONTEXT SUMMARY]:")
        mock_sleep.assert_not_called()
        assert tc.client.chat.completions.create.call_count == 1

    def test_delays_increase_exponentially(self):
        """sleep delays follow retry_delay * 2^attempt + jitter pattern."""
        tc = _make_compressor(max_retries=3, retry_delay=2)
        metrics = TrajectoryMetrics()

        tc.client = MagicMock()
        # Fail twice, succeed on third attempt
        tc.client.chat.completions.create.side_effect = [
            Exception("err1"),
            Exception("err2"),
            _fake_response(),
        ]

        sleep_calls = []
        with patch("time.sleep", side_effect=lambda t: sleep_calls.append(t)), \
             patch("random.uniform", return_value=0.5):  # fix jitter to 0.5
            result = tc._generate_summary("content", metrics)

        assert result.startswith("[CONTEXT SUMMARY]:")
        # attempt 0 → retry_delay * 2^0 + 0.5 = 2 * 1 + 0.5 = 2.5
        # attempt 1 → retry_delay * 2^1 + 0.5 = 2 * 2 + 0.5 = 4.5
        assert len(sleep_calls) == 2
        assert sleep_calls[0] == pytest.approx(2.5)
        assert sleep_calls[1] == pytest.approx(4.5)
        # Confirm second delay is larger than first (exponential growth)
        assert sleep_calls[1] > sleep_calls[0]

    def test_jitter_makes_delay_non_exact(self):
        """With real random jitter the delay should not be exactly 2^n * base."""
        tc = _make_compressor(max_retries=2, retry_delay=1)
        metrics = TrajectoryMetrics()

        tc.client = MagicMock()
        tc.client.chat.completions.create.side_effect = [
            Exception("err"),
            _fake_response(),
        ]

        sleep_calls = []
        # Use real random.uniform — don't patch it
        with patch("time.sleep", side_effect=lambda t: sleep_calls.append(t)):
            tc._generate_summary("content", metrics)

        assert len(sleep_calls) == 1
        base_delay = 1 * (2 ** 0)  # retry_delay * 2^0 = 1
        # Jitter is uniform(0, 1), so total must be strictly greater than base
        assert sleep_calls[0] > base_delay

    def test_max_retries_respected_returns_fallback(self):
        """After max_retries all fail, fallback summary is returned without extra calls."""
        max_retries = 3
        tc = _make_compressor(max_retries=max_retries)
        metrics = TrajectoryMetrics()

        tc.client = MagicMock()
        tc.client.chat.completions.create.side_effect = Exception("always fails")

        with patch("time.sleep"):
            result = tc._generate_summary("content", metrics)

        assert "Summary generation failed" in result
        assert tc.client.chat.completions.create.call_count == max_retries
        assert metrics.summarization_errors == max_retries

    def test_success_on_last_retry_returns_result(self):
        """A successful call on the final allowed attempt returns the real result."""
        max_retries = 4
        tc = _make_compressor(max_retries=max_retries)
        metrics = TrajectoryMetrics()

        tc.client = MagicMock()
        tc.client.chat.completions.create.side_effect = (
            [Exception("fail")] * (max_retries - 1) + [_fake_response("[CONTEXT SUMMARY]: late win")]
        )

        with patch("time.sleep"):
            result = tc._generate_summary("content", metrics)

        assert result == "[CONTEXT SUMMARY]: late win"
        assert tc.client.chat.completions.create.call_count == max_retries


# ---------------------------------------------------------------------------
# Async _generate_summary_async
# ---------------------------------------------------------------------------


class TestGenerateSummaryAsyncBackoff:
    """Tests for the asynchronous _generate_summary_async retry loop."""

    def test_success_on_first_attempt_no_sleep(self):
        """No asyncio.sleep call when first attempt succeeds."""
        tc = _make_compressor()
        metrics = TrajectoryMetrics()

        tc.async_client = MagicMock()
        tc.async_client.chat.completions.create = AsyncMock(
            return_value=_fake_response()
        )

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = asyncio.get_event_loop().run_until_complete(
                tc._generate_summary_async("content", metrics)
            )

        assert result.startswith("[CONTEXT SUMMARY]:")
        mock_sleep.assert_not_called()

    def test_delays_increase_exponentially_async(self):
        """Async sleep delays follow the same exponential + jitter formula."""
        tc = _make_compressor(max_retries=3, retry_delay=2)
        metrics = TrajectoryMetrics()

        tc.async_client = MagicMock()
        tc.async_client.chat.completions.create = AsyncMock(
            side_effect=[Exception("e1"), Exception("e2"), _fake_response()]
        )

        sleep_calls = []

        async def _capture_sleep(t):
            sleep_calls.append(t)

        with patch("random.uniform", return_value=0.5):
            with patch("asyncio.sleep", side_effect=_capture_sleep):
                asyncio.get_event_loop().run_until_complete(
                    tc._generate_summary_async("content", metrics)
                )

        assert len(sleep_calls) == 2
        assert sleep_calls[0] == pytest.approx(2.5)   # 2 * 2^0 + 0.5
        assert sleep_calls[1] == pytest.approx(4.5)   # 2 * 2^1 + 0.5
        assert sleep_calls[1] > sleep_calls[0]

    def test_max_retries_respected_async(self):
        """All failures within max_retries returns fallback; no extra API calls."""
        max_retries = 3
        tc = _make_compressor(max_retries=max_retries)
        metrics = TrajectoryMetrics()

        tc.async_client = MagicMock()
        tc.async_client.chat.completions.create = AsyncMock(
            side_effect=Exception("always fails")
        )

        async def _run():
            with patch("asyncio.sleep", new_callable=AsyncMock):
                return await tc._generate_summary_async("content", metrics)

        result = asyncio.get_event_loop().run_until_complete(_run())

        assert "Summary generation failed" in result
        assert tc.async_client.chat.completions.create.call_count == max_retries

    def test_success_on_retry_async_returns_result(self):
        """Async path: successful retry returns the real summary."""
        tc = _make_compressor(max_retries=3)
        metrics = TrajectoryMetrics()

        tc.async_client = MagicMock()
        tc.async_client.chat.completions.create = AsyncMock(
            side_effect=[Exception("fail"), _fake_response("[CONTEXT SUMMARY]: async ok")]
        )

        async def _run():
            with patch("asyncio.sleep", new_callable=AsyncMock):
                return await tc._generate_summary_async("content", metrics)

        result = asyncio.get_event_loop().run_until_complete(_run())

        assert result == "[CONTEXT SUMMARY]: async ok"
        assert tc.async_client.chat.completions.create.call_count == 2
