#!/usr/bin/env python3
"""Validate provenance — ensure all source-grounded content has proper references."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def validate_provenance(canonical_source_path: Path) -> dict:
    """Validate provenance chain in a canonical source model.

    Checks:
    - All paragraphs have source_refs
    - All questions have source_refs
    - Answer key entries reference valid question_ids
    - No orphan references
    """
    checks = []

    data = json.loads(canonical_source_path.read_text(encoding="utf-8"))

    # Check reading passage paragraphs
    paragraphs = data.get("reading_passage", {}).get("paragraphs", [])
    for para in paragraphs:
        pid = para.get("paragraph_id", "?")
        refs = para.get("source_refs", [])
        if not refs:
            checks.append({
                "check_id": f"PROV-PARA-{pid}",
                "check_name": "paragraph_source_ref",
                "status": "FAIL",
                "severity": "high",
                "message": f"Paragraph {pid} has no source_refs",
            })
        else:
            checks.append({
                "check_id": f"PROV-PARA-{pid}",
                "check_name": "paragraph_source_ref",
                "status": "PASS",
                "severity": "info",
                "message": f"Paragraph {pid}: {len(refs)} source ref(s)",
            })

    # Check questions
    questions = data.get("questions", [])
    question_ids = set()
    for q in questions:
        qid = q.get("question_id", "?")
        question_ids.add(qid)
        refs = q.get("source_refs", [])
        if not refs:
            checks.append({
                "check_id": f"PROV-Q-{qid}",
                "check_name": "question_source_ref",
                "status": "WARN",
                "severity": "medium",
                "message": f"Question {qid} has no source_refs",
            })

    # Check answer key references valid questions
    answers = data.get("answer_key_source", [])
    for ans in answers:
        ref_qid = ans.get("question_id", "?")
        if ref_qid not in question_ids:
            checks.append({
                "check_id": f"PROV-ANS-{ref_qid}",
                "check_name": "answer_key_orphan",
                "status": "FAIL",
                "severity": "high",
                "message": f"Answer key references unknown question: {ref_qid}",
            })

    # Check unresolved items
    unresolved = data.get("unresolved_items", [])
    critical_unresolved = [u for u in unresolved if u.get("severity") == "critical"]
    if critical_unresolved:
        checks.append({
            "check_id": "PROV-UNRESOLVED",
            "check_name": "critical_unresolved",
            "status": "FAIL",
            "severity": "critical",
            "message": f"{len(critical_unresolved)} critical unresolved item(s)",
        })

    has_fail = any(c["status"] == "FAIL" for c in checks)
    return {
        "status": "FAIL" if has_fail else "PASS",
        "checks": checks,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate provenance chain")
    parser.add_argument("--source", required=True, help="Path to canonical-source.json")
    args = parser.parse_args()

    result = validate_provenance(Path(args.source))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "PASS" else 1)
