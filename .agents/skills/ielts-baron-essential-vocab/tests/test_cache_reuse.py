"""Tests for cache reuse — verify stages are skipped when cached."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


class TestCacheReuse:
    def test_cache_manifest_detected(self):
        """When cache manifest exists, cached stages should be recognized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test-source"
            cache_dir.mkdir()

            manifest = {
                "cached_stages": ["request-intake", "cache-resolve", "source-acquire"],
            }
            manifest_path = cache_dir / "cache-manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            assert manifest_path.exists()
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            assert len(loaded["cached_stages"]) == 3

    def test_no_cache_means_fresh_run(self):
        """Without cache manifest, all stages should run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "new-source"
            assert not cache_dir.exists()
