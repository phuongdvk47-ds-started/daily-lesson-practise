"""Integration test — verify pipeline runs through early stages without crashing."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from run_pipeline import (
    _init_pipeline_state,
    _run_stage,
    STAGE_ORDER,
    STAGE_HANDLERS,
    _save_json,
    _load_json,
)


class TestStageHandlersRegistered:
    """All 20 stages must have a handler (no None)."""

    def test_all_handlers_registered(self):
        for stage in STAGE_ORDER:
            assert stage in STAGE_HANDLERS, f"Stage '{stage}' not in registry"
            assert STAGE_HANDLERS[stage] is not None, f"Stage '{stage}' has no handler (None)"

    def test_handler_count(self):
        assert len(STAGE_HANDLERS) == 20

    def test_all_handlers_callable(self):
        for stage, handler in STAGE_HANDLERS.items():
            assert callable(handler), f"Stage '{stage}' handler is not callable"


class TestRequestIntakeHandler:
    """Test request-intake handler independently."""

    def test_local_file_intake(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir) / "cache"
            state = _init_pipeline_state("test-source-id")
            ctx = {
                "source": "test.pdf",
                "unit": "Unit 1",
                "topic": "Animals",
                "day": 1,
                "cache_root": str(cache_root),
            }

            handler = STAGE_HANDLERS["request-intake"]
            result = handler(state, ctx)

            assert result["status"] == "COMPLETE"
            assert len(result["artifacts"]) == 1

            # Verify the normalized request was saved
            normalized = _load_json(Path(result["artifacts"][0]))
            assert normalized["source"]["type"] == "local_file"
            assert normalized["target"]["unit"] == "Unit 1"

    def test_url_intake(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir) / "cache"
            state = _init_pipeline_state("test-source-id")
            ctx = {
                "source": "https://drive.google.com/file/d/abc123",
                "cache_root": str(cache_root),
            }

            handler = STAGE_HANDLERS["request-intake"]
            result = handler(state, ctx)

            assert result["status"] == "COMPLETE"
            normalized = _load_json(Path(result["artifacts"][0]))
            assert normalized["source"]["type"] == "google_drive_url"

    def test_no_source_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir) / "cache"
            state = _init_pipeline_state("test-source-id")
            ctx = {"source": None, "cache_root": str(cache_root)}

            handler = STAGE_HANDLERS["request-intake"]
            result = handler(state, ctx)

            assert result["status"] == "FAILED"


class TestCacheResolveHandler:
    """Test cache-resolve handler."""

    def test_fresh_run_no_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir) / "cache"
            state = _init_pipeline_state("test-source-id")
            ctx = {"cache_root": str(cache_root)}

            handler = STAGE_HANDLERS["cache-resolve"]
            result = handler(state, ctx)

            assert result["status"] == "COMPLETE"

    def test_cached_stages_detected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir) / "cache"
            source_dir = cache_root / "test-source-id"
            source_dir.mkdir(parents=True)

            # Create cache manifest
            manifest = {"cached_stages": ["request-intake", "cache-resolve"]}
            _save_json(source_dir / "cache-manifest.json", manifest)

            state = _init_pipeline_state("test-source-id")
            ctx = {"cache_root": str(cache_root)}

            handler = STAGE_HANDLERS["cache-resolve"]
            result = handler(state, ctx)

            assert result["status"] == "COMPLETE"
            assert state["stages"]["request-intake"]["status"] == "SKIPPED_FROM_CACHE"
            assert state["stages"]["cache-resolve"]["status"] == "SKIPPED_FROM_CACHE"


class TestLessonIdHandler:
    """Test lesson-id handler."""

    def test_generates_valid_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir) / "cache"
            analysis_dir = cache_root / "test-id" / "analysis"
            analysis_dir.mkdir(parents=True)

            # Create level assessment
            _save_json(analysis_dir / "level-assessment.json", {"cefr": "B2"})

            state = _init_pipeline_state("test-id")
            ctx = {"cache_root": str(cache_root), "day": 1}

            handler = STAGE_HANDLERS["lesson-id"]
            result = handler(state, ctx)

            assert result["status"] == "COMPLETE"
            assert state["lession_id"] is not None
            assert state["lession_id"].startswith("LSN-001-B2-")

    def test_preserves_existing_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir) / "cache"
            state = _init_pipeline_state("test-id")
            state["lession_id"] = "LSN-001-B2-EXISTING1"
            ctx = {
                "cache_root": str(cache_root),
                "day": 1,
                "lesson_id": "LSN-001-B2-EXISTING1",
            }

            handler = STAGE_HANDLERS["lesson-id"]
            result = handler(state, ctx)

            assert result["status"] == "COMPLETE"
            assert state["lession_id"] == "LSN-001-B2-EXISTING1"
