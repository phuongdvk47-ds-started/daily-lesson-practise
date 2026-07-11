"""Tests for lesson ID generation — format, idempotency, and safe characters."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_lesson_id import build_lesson_id, validate_lesson_id


class TestLessonIdFormat:
    def test_format_matches_pattern(self):
        lid = build_lesson_id(1, "B2")
        assert validate_lesson_id(lid), f"Invalid format: {lid}"

    def test_day_zero_padded(self):
        lid = build_lesson_id(1, "B2")
        assert lid.startswith("LSN-001-"), f"Day not zero-padded: {lid}"

    def test_day_three_digits(self):
        lid = build_lesson_id(123, "C1")
        assert "LSN-123-C1-" in lid

    def test_level_normalized(self):
        lid = build_lesson_id(1, "B2+")
        # B2+ should become B2
        assert "-B2-" in lid, f"Level not normalized: {lid}"

    def test_random_part_length(self):
        lid = build_lesson_id(1, "B2")
        parts = lid.split("-")
        assert len(parts) == 4
        assert len(parts[3]) == 8

    def test_no_ambiguous_chars(self):
        """Random part should not contain 0, O, 1, I, L."""
        for _ in range(50):  # Run multiple times due to randomness
            lid = build_lesson_id(1, "B2")
            random_part = lid.split("-")[3]
            for ch in "0OIL1":
                assert ch not in random_part, f"Ambiguous char '{ch}' in {random_part}"

    def test_idempotency_preserves_existing(self):
        existing = "LSN-001-B2-A7K9P2QX"
        result = build_lesson_id(1, "B2", existing_id=existing)
        assert result == existing


class TestLessonIdValidation:
    def test_valid_id(self):
        assert validate_lesson_id("LSN-001-B2-A7K9P2QX")

    def test_invalid_format(self):
        assert not validate_lesson_id("invalid")
        assert not validate_lesson_id("LSN-01-B2-A7K9P2QX")  # Day too short
        assert not validate_lesson_id("LSN-001-B2-A7K9P2Q")  # Random too short

    def test_all_cefr_levels(self):
        for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            lid = build_lesson_id(1, level)
            assert validate_lesson_id(lid), f"Failed for level {level}: {lid}"
