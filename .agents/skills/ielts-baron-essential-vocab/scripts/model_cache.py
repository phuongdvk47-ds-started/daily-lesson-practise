#!/usr/bin/env python3
"""Model output cache — read/write cached model outputs keyed by input+model+prompt hash."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("model_cache")


def compute_cache_key(
    input_data: Any,
    task_name: str,
    engine_name: str,
    model_version: str = "",
    prompt_version: str = "",
    schema_version: str = "1.0.0",
) -> str:
    """Compute a deterministic cache key from input + model + prompt + schema."""
    key_parts = json.dumps(
        {
            "input": input_data,
            "task": task_name,
            "engine": engine_name,
            "model_version": model_version,
            "prompt_version": prompt_version,
            "schema_version": schema_version,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(key_parts.encode("utf-8")).hexdigest()[:24]


def get_cache_path(cache_root: Path, task_name: str, cache_key: str) -> Path:
    """Return the cache directory for a given task and key."""
    return cache_root / "model-cache" / task_name / cache_key


def read_cache(cache_root: Path, task_name: str, cache_key: str) -> dict | None:
    """Read cached output if it exists and is valid.

    Returns:
        The cached output dict, or None if cache miss.
    """
    cache_dir = get_cache_path(cache_root, task_name, cache_key)
    output_path = cache_dir / "output.json"
    validation_path = cache_dir / "validation.json"

    if not output_path.exists():
        logger.debug(f"Cache miss: {task_name}/{cache_key}")
        return None

    # Check validation status
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        if validation.get("status") == "FAIL":
            logger.debug(f"Cache invalid (validation FAIL): {task_name}/{cache_key}")
            return None

    output = json.loads(output_path.read_text(encoding="utf-8"))
    logger.info(f"Cache hit: {task_name}/{cache_key}")
    return output


def write_cache(
    cache_root: Path,
    task_name: str,
    cache_key: str,
    input_data: Any,
    output_data: Any,
    validation_status: str = "PASS",
    execution_metadata: dict | None = None,
) -> Path:
    """Write model output to cache.

    Returns:
        Path to the cache directory.
    """
    cache_dir = get_cache_path(cache_root, task_name, cache_key)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Write input
    input_path = cache_dir / "input.json"
    input_path.write_text(
        json.dumps(input_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Write output
    output_path = cache_dir / "output.json"
    output_path.write_text(
        json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Write validation
    validation_path = cache_dir / "validation.json"
    validation_path.write_text(
        json.dumps(
            {"status": validation_status, "created_at": datetime.now(timezone.utc).isoformat()},
            indent=2,
        ),
        encoding="utf-8",
    )

    # Write execution metadata
    if execution_metadata:
        meta_path = cache_dir / "execution-metadata.json"
        meta_path.write_text(
            json.dumps(execution_metadata, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    logger.info(f"Cache written: {task_name}/{cache_key}")
    return cache_dir


def invalidate_cache(cache_root: Path, task_name: str, cache_key: str) -> bool:
    """Mark a cache entry as invalid without deleting it."""
    cache_dir = get_cache_path(cache_root, task_name, cache_key)
    validation_path = cache_dir / "validation.json"

    if cache_dir.exists():
        validation_path.write_text(
            json.dumps(
                {"status": "FAIL", "invalidated_at": datetime.now(timezone.utc).isoformat()},
                indent=2,
            ),
            encoding="utf-8",
        )
        logger.info(f"Cache invalidated: {task_name}/{cache_key}")
        return True
    return False
