#!/usr/bin/env python3
"""Source fingerprinting — SHA-256 hash and unique_source_id generation."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_source_id(file_path: Path) -> dict:
    """Generate unique source ID and metadata."""
    sha = compute_sha256(file_path)
    stat = file_path.stat()

    return {
        "unique_source_id": sha,
        "filename": file_path.name,
        "file_size_bytes": stat.st_size,
        "sha256": sha,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute source fingerprint")
    parser.add_argument("file", type=str, help="Path to source file")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(json.dumps({"error": f"File not found: {args.file}"}), file=sys.stderr)
        sys.exit(1)

    result = generate_source_id(path)
    print(json.dumps(result, indent=2))
