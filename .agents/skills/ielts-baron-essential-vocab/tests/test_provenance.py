"""Tests for provenance — verify source references are enforced."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from validate_provenance import validate_provenance


class TestProvenance:
    def _write_canonical(self, tmpdir: str, data: dict) -> Path:
        p = Path(tmpdir) / "canonical-source.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_pass_with_full_provenance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "reading_passage": {
                    "paragraphs": [
                        {"paragraph_id": "A", "text": "Test", "source_refs": [{"source_id": "x", "page": 1}]}
                    ]
                },
                "questions": [
                    {"question_id": "Q1", "text": "?", "source_refs": [{"source_id": "x", "page": 1}]}
                ],
                "answer_key_source": [
                    {"question_id": "Q1", "answer": "A"}
                ],
                "unresolved_items": [],
            }
            path = self._write_canonical(tmpdir, data)
            result = validate_provenance(path)
            assert result["status"] == "PASS"

    def test_fail_missing_paragraph_refs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "reading_passage": {
                    "paragraphs": [
                        {"paragraph_id": "A", "text": "Test", "source_refs": []}
                    ]
                },
                "questions": [],
                "answer_key_source": [],
                "unresolved_items": [],
            }
            path = self._write_canonical(tmpdir, data)
            result = validate_provenance(path)
            assert result["status"] == "FAIL"

    def test_fail_orphan_answer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "reading_passage": {"paragraphs": []},
                "questions": [
                    {"question_id": "Q1", "text": "?", "source_refs": [{"source_id": "x", "page": 1}]}
                ],
                "answer_key_source": [
                    {"question_id": "Q99", "answer": "X"}  # references non-existent question
                ],
                "unresolved_items": [],
            }
            path = self._write_canonical(tmpdir, data)
            result = validate_provenance(path)
            assert result["status"] == "FAIL"

    def test_fail_critical_unresolved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "reading_passage": {"paragraphs": []},
                "questions": [],
                "answer_key_source": [],
                "unresolved_items": [
                    {"item_id": "U1", "type": "answer_key_missing", "description": "Missing", "severity": "critical"}
                ],
            }
            path = self._write_canonical(tmpdir, data)
            result = validate_provenance(path)
            assert result["status"] == "FAIL"
