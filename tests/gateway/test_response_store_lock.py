"""
Tests for ResponseStore thread safety (PR #2780).

Verifies that the threading.Lock added to ResponseStore prevents data
corruption under concurrent access and that the lock is acquired during
store, get, and delete operations.
"""

import threading
import time
import unittest
from unittest.mock import patch

from gateway.platforms.api_server import ResponseStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_store(max_size=100):
    """Return an in-memory ResponseStore."""
    return ResponseStore(max_size=max_size, db_path=":memory:")


# ---------------------------------------------------------------------------
# Lock presence
# ---------------------------------------------------------------------------


class TestResponseStoreLockExists:
    def test_has_lock_attribute(self):
        store = _make_store()
        assert hasattr(store, "_lock"), "ResponseStore should have a _lock attribute"

    def test_lock_is_threading_lock(self):
        store = _make_store()
        # threading.Lock() returns a _thread.lock / threading._RLock-compatible object
        assert hasattr(store._lock, "acquire") and hasattr(store._lock, "release")


# ---------------------------------------------------------------------------
# Lock is acquired during each operation
# ---------------------------------------------------------------------------


class _TrackingLock:
    """threading.Lock wrapper that counts context-manager entries."""

    def __init__(self):
        self._lock = threading.Lock()
        self.enter_count = 0

    def __enter__(self):
        self._lock.acquire()
        self.enter_count += 1
        return self

    def __exit__(self, *args):
        self._lock.release()

    def acquire(self, *a, **kw):
        return self._lock.acquire(*a, **kw)

    def release(self):
        return self._lock.release()


class TestResponseStoreLockAcquired:
    """Replace the store's lock with a _TrackingLock to verify it is entered."""

    def _tracked_store(self):
        store = _make_store()
        tracking = _TrackingLock()
        store._lock = tracking
        return store, tracking

    def test_put_acquires_lock(self):
        store, lock = self._tracked_store()
        store.put("r1", {"x": 1})
        assert lock.enter_count >= 1

    def test_get_acquires_lock(self):
        store, lock = self._tracked_store()
        store.put("r1", {"x": 1})
        before = lock.enter_count
        store.get("r1")
        assert lock.enter_count > before

    def test_get_missing_acquires_lock(self):
        store, lock = self._tracked_store()
        store.get("no_such_id")
        assert lock.enter_count >= 1

    def test_delete_acquires_lock(self):
        store, lock = self._tracked_store()
        store.put("r1", {"x": 1})
        before = lock.enter_count
        store.delete("r1")
        assert lock.enter_count > before

    def test_get_conversation_acquires_lock(self):
        store, lock = self._tracked_store()
        store.get_conversation("conv1")
        assert lock.enter_count >= 1

    def test_set_conversation_acquires_lock(self):
        store, lock = self._tracked_store()
        store.set_conversation("conv1", "r1")
        assert lock.enter_count >= 1


# ---------------------------------------------------------------------------
# Concurrent access does not crash or corrupt data
# ---------------------------------------------------------------------------


class TestResponseStoreConcurrency:
    """Hammer the store from multiple threads and verify correctness."""

    def test_concurrent_puts_do_not_crash(self):
        store = _make_store(max_size=200)
        errors = []

        def worker(tid):
            try:
                for i in range(20):
                    store.put(f"t{tid}_r{i}", {"tid": tid, "i": i})
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent puts raised: {errors}"

    def test_concurrent_gets_do_not_crash(self):
        store = _make_store()
        for i in range(50):
            store.put(f"r{i}", {"val": i})

        errors = []

        def reader(tid):
            try:
                for i in range(50):
                    store.get(f"r{i % 50}")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=reader, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent gets raised: {errors}"

    def test_concurrent_mixed_operations_do_not_crash(self):
        store = _make_store(max_size=50)
        errors = []

        def writer(tid):
            try:
                for i in range(10):
                    rid = f"t{tid}_r{i}"
                    store.put(rid, {"tid": tid, "i": i})
                    store.get(rid)
                    store.delete(rid)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Mixed concurrent operations raised: {errors}"

    def test_concurrent_puts_data_integrity(self):
        """Each thread writes its own keyed entry; all entries must be readable."""
        store = _make_store(max_size=1000)
        n_threads = 10
        items_per_thread = 10

        def writer(tid):
            for i in range(items_per_thread):
                store.put(f"t{tid}_r{i}", {"tid": tid, "idx": i})

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify a sampling of written entries survived
        for tid in range(n_threads):
            for i in range(items_per_thread):
                result = store.get(f"t{tid}_r{i}")
                assert result is not None, f"Entry t{tid}_r{i} missing after concurrent write"
                assert result["tid"] == tid
                assert result["idx"] == i

    def test_concurrent_conversation_set_get(self):
        store = _make_store()
        errors = []

        def worker(tid):
            try:
                for i in range(20):
                    store.set_conversation(f"conv{tid}", f"r{tid}_{i}")
                    store.get_conversation(f"conv{tid}")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent conversation ops raised: {errors}"

    def test_lock_prevents_interleaved_writes(self):
        """
        Simulate interleaving by holding the lock externally and confirm
        a second thread blocks until the lock is released.
        """
        store = _make_store()
        results = []

        def slow_writer():
            with store._lock:
                # Hold the lock for a moment
                time.sleep(0.05)
                results.append("slow_start")
                time.sleep(0.05)
                results.append("slow_end")

        def fast_writer():
            # Give slow_writer a moment to grab the lock first
            time.sleep(0.01)
            # This should block until slow_writer releases
            store.put("fast_key", {"v": 1})
            results.append("fast_done")

        t1 = threading.Thread(target=slow_writer)
        t2 = threading.Thread(target=fast_writer)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # slow_writer must complete entirely before fast_writer's put proceeds
        assert results.index("slow_end") < results.index("fast_done"), (
            "fast_writer should not complete before slow_writer releases the lock"
        )
