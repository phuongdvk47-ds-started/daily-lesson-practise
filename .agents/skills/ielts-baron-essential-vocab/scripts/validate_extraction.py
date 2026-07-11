#!/usr/bin/env python3
"""Validate extraction integrity — check completeness, missing pages, block counts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate_extraction(extraction_dir: Path, expected_pages: list[int] | None = None) -> dict:
    """Validate extraction artifacts for completeness.

    Returns QA-style report.
    """
    checks = []

    # Check manifest exists
    manifest_path = extraction_dir / "extraction-manifest.json"
    if not manifest_path.exists():
        checks.append({
            "check_id": "EXT-001",
            "check_name": "extraction_manifest_exists",
            "status": "FAIL",
            "severity": "critical",
            "message": "extraction-manifest.json not found",
        })
        return {"status": "FAIL", "checks": checks}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks.append({
        "check_id": "EXT-001",
        "check_name": "extraction_manifest_exists",
        "status": "PASS",
        "severity": "info",
        "message": f"Manifest found: {manifest.get('total_blocks', 0)} blocks",
    })

    # Check text blocks exist
    blocks_path = extraction_dir / "text" / "text-blocks.json"
    if blocks_path.exists():
        blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
        if len(blocks) == 0:
            checks.append({
                "check_id": "EXT-002",
                "check_name": "text_blocks_not_empty",
                "status": "FAIL",
                "severity": "high",
                "message": "No text blocks extracted",
            })
        else:
            checks.append({
                "check_id": "EXT-002",
                "check_name": "text_blocks_not_empty",
                "status": "PASS",
                "severity": "info",
                "message": f"{len(blocks)} text blocks extracted",
            })
    else:
        checks.append({
            "check_id": "EXT-002",
            "check_name": "text_blocks_not_empty",
            "status": "FAIL",
            "severity": "critical",
            "message": "text-blocks.json not found",
        })

    # Check expected pages covered
    if expected_pages and blocks_path.exists():
        blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
        extracted_pages = set(b["page"] for b in blocks)
        missing = set(expected_pages) - extracted_pages
        if missing:
            checks.append({
                "check_id": "EXT-003",
                "check_name": "expected_pages_covered",
                "status": "WARN",
                "severity": "medium",
                "message": f"Missing text from pages: {sorted(missing)}",
            })
        else:
            checks.append({
                "check_id": "EXT-003",
                "check_name": "expected_pages_covered",
                "status": "PASS",
                "severity": "info",
                "message": "All expected pages have text blocks",
            })

    # Determine overall status
    has_fail = any(c["status"] == "FAIL" for c in checks)
    has_warn = any(c["status"] == "WARN" for c in checks)
    overall = "FAIL" if has_fail else ("WARN" if has_warn else "PASS")

    return {
        "status": overall,
        "checks": checks,
        "summary": {
            "total_checks": len(checks),
            "passed": sum(1 for c in checks if c["status"] == "PASS"),
            "failed": sum(1 for c in checks if c["status"] == "FAIL"),
            "warnings": sum(1 for c in checks if c["status"] == "WARN"),
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate extraction artifacts")
    parser.add_argument("--extraction-dir", required=True)
    parser.add_argument("--expected-pages", type=str, help="Comma-separated page numbers")
    args = parser.parse_args()

    expected = [int(p) for p in args.expected_pages.split(",")] if args.expected_pages else None
    result = validate_extraction(Path(args.extraction_dir), expected)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] != "FAIL" else 1)
