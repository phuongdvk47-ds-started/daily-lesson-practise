#!/usr/bin/env python3
"""Build a unique lesson ID: LSN-[Day]-[Level]-[Random8]."""
from __future__ import annotations

import argparse
import json
import secrets
import string
import sys


# Characters that avoid ambiguity (no 0/O, 1/I/L)
SAFE_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def build_lesson_id(day: int, cefr_level: str, existing_id: str | None = None) -> str:
    """Generate a lesson ID. If existing_id is provided and valid, return it unchanged."""
    if existing_id and existing_id.startswith("LSN-"):
        return existing_id

    day_str = f"{day:03d}"
    level_str = cefr_level.upper().replace("+", "")  # B2+ -> B2
    random_part = "".join(secrets.choice(SAFE_CHARS) for _ in range(8))

    return f"LSN-{day_str}-{level_str}-{random_part}"


def validate_lesson_id(lesson_id: str) -> bool:
    """Check if a lesson ID matches the expected format."""
    import re
    pattern = r"^LSN-\d{3}-[A-C]\d-[A-HJ-NP-Z2-9]{8}$"
    return bool(re.match(pattern, lesson_id))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a lesson ID")
    parser.add_argument("--day", type=int, required=True, help="Day number")
    parser.add_argument("--level", type=str, required=True, help="CEFR level (e.g. B2)")
    parser.add_argument("--existing-id", type=str, help="Existing ID to preserve")
    args = parser.parse_args()

    lid = build_lesson_id(args.day, args.level, args.existing_id)
    print(json.dumps({"lession_id": lid, "valid": validate_lesson_id(lid)}))
