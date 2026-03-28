"""Tests for session lineage exclusion in _list_recent_sessions.

After context compression, the current conversation has a parent→child
chain. All sessions in that chain must be excluded from "recent sessions"
results, otherwise the agent sees its own conversation as a separate
recent session.
"""

from unittest.mock import MagicMock
from tools.session_search_tool import _list_recent_sessions


def _mock_db(sessions, parent_map=None):
    """Build a mock SessionDB with get_session and list_sessions_rich."""
    parent_map = parent_map or {}
    db = MagicMock()
    db.list_sessions_rich.return_value = sessions

    def get_session(sid):
        parent = parent_map.get(sid)
        return {"id": sid, "parent_session_id": parent} if sid in parent_map or any(s.get("id") == sid for s in sessions) else None

    db.get_session.side_effect = get_session
    return db


class TestLineageExclusion:

    def test_parent_excluded_from_recent(self):
        """Parent session of current conversation must not appear in results."""
        sessions = [
            {"id": "parent-aaa", "title": "Old convo"},
            {"id": "child-bbb", "title": None, "parent_session_id": "parent-aaa"},
            {"id": "unrelated-ccc", "title": "Other work"},
        ]
        parent_map = {"child-bbb": "parent-aaa", "parent-aaa": None}
        db = _mock_db(sessions, parent_map)

        result = _list_recent_sessions(db, limit=10, current_session_id="child-bbb")

        assert "unrelated-ccc" in result
        assert "parent-aaa" not in result
        assert "child-bbb" not in result

    def test_deep_lineage_all_excluded(self):
        """A→B→C chain: all three excluded when current is C."""
        sessions = [
            {"id": "root-a", "title": "Session A"},
            {"id": "mid-b", "title": None, "parent_session_id": "root-a"},
            {"id": "leaf-c", "title": None, "parent_session_id": "mid-b"},
            {"id": "other-d", "title": "Unrelated"},
        ]
        parent_map = {"leaf-c": "mid-b", "mid-b": "root-a", "root-a": None}
        db = _mock_db(sessions, parent_map)

        result = _list_recent_sessions(db, limit=10, current_session_id="leaf-c")

        assert "other-d" in result
        assert "root-a" not in result
        assert "mid-b" not in result
        assert "leaf-c" not in result

    def test_no_compression_still_works(self):
        """Session with no parent chain should just exclude itself."""
        sessions = [
            {"id": "current-x", "title": "My session"},
            {"id": "other-y", "title": "Other"},
        ]
        parent_map = {"current-x": None}
        db = _mock_db(sessions, parent_map)

        result = _list_recent_sessions(db, limit=10, current_session_id="current-x")

        assert "other-y" in result
        assert "current-x" not in result

    def test_no_current_session_returns_all(self):
        """When current_session_id is None, nothing is excluded."""
        sessions = [
            {"id": "aaa", "title": "First"},
            {"id": "bbb", "title": "Second"},
        ]
        db = _mock_db(sessions)

        result = _list_recent_sessions(db, limit=10, current_session_id=None)

        assert "aaa" in result
        assert "bbb" in result
