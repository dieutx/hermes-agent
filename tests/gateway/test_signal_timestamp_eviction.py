"""Tests for Signal adapter FIFO timestamp eviction."""
import pytest
from unittest.mock import patch
from collections import OrderedDict


@pytest.fixture
def signal_adapter():
    """Create a minimal SignalAdapter with mocked config."""
    with patch.dict("os.environ", {
        "SIGNAL_CLI_REST_URL": "http://localhost:8080",
        "SIGNAL_ACCOUNT": "+15551234567",
    }):
        with patch("gateway.platforms.signal.SignalAdapter.__init__", lambda self: None):
            from gateway.platforms.signal import SignalAdapter
            adapter = SignalAdapter.__new__(SignalAdapter)
            adapter._recent_sent_timestamps = OrderedDict()
            adapter._max_recent_timestamps = 50
            return adapter


class TestTimestampEviction:
    """Verify _recent_sent_timestamps uses FIFO eviction."""

    def test_tracks_timestamp(self, signal_adapter):
        signal_adapter._track_sent_timestamp({"timestamp": "ts_1"})
        assert "ts_1" in signal_adapter._recent_sent_timestamps

    def test_ignores_missing_timestamp(self, signal_adapter):
        signal_adapter._track_sent_timestamp({})
        assert len(signal_adapter._recent_sent_timestamps) == 0

    def test_ignores_non_dict(self, signal_adapter):
        signal_adapter._track_sent_timestamp("not a dict")
        assert len(signal_adapter._recent_sent_timestamps) == 0

    def test_evicts_oldest_first(self, signal_adapter):
        """When exceeding max, the OLDEST timestamp must be evicted."""
        signal_adapter._max_recent_timestamps = 5
        for i in range(7):
            signal_adapter._track_sent_timestamp({"timestamp": f"ts_{i}"})

        assert len(signal_adapter._recent_sent_timestamps) == 5
        # Oldest two (ts_0, ts_1) should be gone
        assert "ts_0" not in signal_adapter._recent_sent_timestamps
        assert "ts_1" not in signal_adapter._recent_sent_timestamps
        # Newest five should remain
        for i in range(2, 7):
            assert f"ts_{i}" in signal_adapter._recent_sent_timestamps

    def test_fifo_order_under_sustained_load(self, signal_adapter):
        """Under sustained load, only the most recent N timestamps survive."""
        signal_adapter._max_recent_timestamps = 50
        for i in range(10000):
            signal_adapter._track_sent_timestamp({"timestamp": f"ts_{i}"})

        assert len(signal_adapter._recent_sent_timestamps) == 50
        # Only the last 50 should survive
        for i in range(9950, 10000):
            assert f"ts_{i}" in signal_adapter._recent_sent_timestamps
        # None of the old ones should remain
        for i in range(100):
            assert f"ts_{i}" not in signal_adapter._recent_sent_timestamps

    def test_uses_ordered_dict_not_set(self, signal_adapter):
        """The backing store must be OrderedDict for deterministic eviction."""
        assert isinstance(signal_adapter._recent_sent_timestamps, OrderedDict)
