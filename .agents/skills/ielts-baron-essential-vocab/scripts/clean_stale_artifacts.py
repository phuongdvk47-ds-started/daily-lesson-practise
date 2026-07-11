#!/usr/bin/env python3
"""Clean stale artifacts — purge outdated cache entries."""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

logger = logging.getLogger("clean_stale")


def clean_stale_artifacts(cache_root: Path, dry_run: bool = True) -> dict:
    """Find and optionally remove stale cache entries.

    A cache entry is stale if:
    - pipeline-state.json shows FAILED status
    - No successful output exists
    """
    removed = []
    kept = []

    if not cache_root.exists():
        return {"removed": [], "kept": [], "dry_run": dry_run}

    for source_dir in cache_root.iterdir():
        if not source_dir.is_dir():
            continue

        state_path = source_dir / "state" / "pipeline-state.json"
        if not state_path.exists():
            continue

        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            if not dry_run:
                shutil.rmtree(source_dir, ignore_errors=True)
            removed.append(str(source_dir))
            continue

        if state.get("overall_status") == "FAILED":
            if not dry_run:
                shutil.rmtree(source_dir, ignore_errors=True)
            removed.append(str(source_dir))
        else:
            kept.append(str(source_dir))

    return {"removed": removed, "kept": kept, "dry_run": dry_run}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean stale cache artifacts")
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--execute", action="store_true", help="Actually remove (default: dry run)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    result = clean_stale_artifacts(Path(args.cache_root), dry_run=not args.execute)
    print(json.dumps(result, indent=2))
