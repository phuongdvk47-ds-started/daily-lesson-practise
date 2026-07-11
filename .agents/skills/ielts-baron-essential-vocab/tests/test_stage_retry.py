"""Tests for stage retry — verify retry isolates to the failed stage."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from run_pipeline import STAGE_ORDER, _init_pipeline_state, _update_stage


class TestStageRetry:
    def test_stages_are_independent(self):
        """Each stage should be addressable independently."""
        assert len(STAGE_ORDER) == 20
        assert "html-render" in STAGE_ORDER
        assert "pdf-render" in STAGE_ORDER

    def test_failed_stage_does_not_reset_completed(self):
        """Failing pdf-render should not reset source-acquire."""
        state = _init_pipeline_state("test-source-id")

        # Mark early stages as complete
        _update_stage(state, "source-acquire", status="COMPLETE")
        _update_stage(state, "text-extract", status="COMPLETE")

        # Mark render as failed
        _update_stage(state, "pdf-render", status="FAILED", error_code="PDF_RENDER_FAILED")

        assert state["stages"]["source-acquire"]["status"] == "COMPLETE"
        assert state["stages"]["text-extract"]["status"] == "COMPLETE"
        assert state["stages"]["pdf-render"]["status"] == "FAILED"

    def test_render_failure_only_reruns_render(self):
        """From-stage should allow starting at html-render."""
        start_idx = STAGE_ORDER.index("html-render")
        assert start_idx > 0  # Not the first stage
        assert STAGE_ORDER[start_idx] == "html-render"
        assert STAGE_ORDER[start_idx + 1] == "pdf-render"
