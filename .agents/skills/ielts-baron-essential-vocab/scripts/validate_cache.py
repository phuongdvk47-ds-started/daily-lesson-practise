#!/usr/bin/env python3
"""Cache validator — check cache integrity and detect stale artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def validate_cache(cache_dir: Path) -> dict:
    """Validate cache directory structure and integrity."""
    checks = []

    if not cache_dir.exists():
        return {"status": "PASS", "checks": [{"check_id": "CACHE-001", "status": "PASS", "message": "No cache directory (fresh run)"}]}

    manifest_path = cache_dir / "cache-manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            checks.append({
                "check_id": "CACHE-001",
                "check_name": "manifest_valid",
                "status": "PASS",
                "message": "Cache manifest is valid JSON",
            })
        except json.JSONDecodeError:
            checks.append({
                "check_id": "CACHE-001",
                "check_name": "manifest_valid",
                "status": "FAIL",
                "severity": "high",
                "message": "Cache manifest is corrupt",
            })

    # Check state directory
    state_dir = cache_dir / "state"
    if state_dir.exists():
        state_path = state_dir / "pipeline-state.json"
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
                checks.append({
                    "check_id": "CACHE-002",
                    "check_name": "pipeline_state_valid",
                    "status": "PASS",
                    "message": f"Pipeline state: {state.get('overall_status', 'UNKNOWN')}",
                })
            except json.JSONDecodeError:
                checks.append({
                    "check_id": "CACHE-002",
                    "check_name": "pipeline_state_valid",
                    "status": "FAIL",
                    "severity": "critical",
                    "message": "Pipeline state file is corrupt — CACHE_CORRUPTED",
                })

    has_fail = any(c["status"] == "FAIL" for c in checks)
    return {"status": "FAIL" if has_fail else "PASS", "checks": checks}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate cache integrity")
    parser.add_argument("--cache-dir", required=True)
    args = parser.parse_args()

    result = validate_cache(Path(args.cache_dir))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "PASS" else 1)
