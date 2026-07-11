"""Tests for model cache — key computation, read/write, invalidation."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from model_cache import compute_cache_key, read_cache, write_cache, invalidate_cache


class TestCacheKeyComputation:
    def test_deterministic_key(self):
        """Same inputs must produce same key."""
        key1 = compute_cache_key({"text": "hello"}, "test_task", "test_engine")
        key2 = compute_cache_key({"text": "hello"}, "test_task", "test_engine")
        assert key1 == key2

    def test_different_input_different_key(self):
        key1 = compute_cache_key({"text": "hello"}, "test_task", "test_engine")
        key2 = compute_cache_key({"text": "world"}, "test_task", "test_engine")
        assert key1 != key2

    def test_different_model_different_key(self):
        key1 = compute_cache_key({"text": "hello"}, "test_task", "engine_v1", model_version="1.0")
        key2 = compute_cache_key({"text": "hello"}, "test_task", "engine_v1", model_version="2.0")
        assert key1 != key2

    def test_different_prompt_different_key(self):
        key1 = compute_cache_key({"text": "hello"}, "test_task", "engine", prompt_version="v1")
        key2 = compute_cache_key({"text": "hello"}, "test_task", "engine", prompt_version="v2")
        assert key1 != key2

    def test_key_length(self):
        key = compute_cache_key({"text": "hello"}, "test_task", "test_engine")
        assert len(key) == 24


class TestCacheReadWrite:
    def test_write_then_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir)
            key = "test_cache_key_12345678"

            write_cache(cache_root, "test_task", key,
                        input_data={"q": "test"},
                        output_data={"a": "result"})

            result = read_cache(cache_root, "test_task", key)
            assert result is not None
            assert result["a"] == "result"

    def test_cache_miss(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir)
            result = read_cache(cache_root, "test_task", "nonexistent_key")
            assert result is None

    def test_invalidated_cache_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir)
            key = "test_invalidate_key_123"

            write_cache(cache_root, "test_task", key,
                        input_data={"q": "test"},
                        output_data={"a": "result"})

            invalidate_cache(cache_root, "test_task", key)

            result = read_cache(cache_root, "test_task", key)
            assert result is None


class TestCacheIdempotency:
    def test_same_write_twice_no_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir)
            key = "test_idempotent_key_123"

            write_cache(cache_root, "test_task", key,
                        input_data={"q": "test"},
                        output_data={"a": "result1"})

            write_cache(cache_root, "test_task", key,
                        input_data={"q": "test"},
                        output_data={"a": "result2"})

            result = read_cache(cache_root, "test_task", key)
            assert result["a"] == "result2"
