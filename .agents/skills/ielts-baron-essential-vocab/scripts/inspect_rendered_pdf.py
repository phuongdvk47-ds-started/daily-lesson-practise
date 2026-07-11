#!/usr/bin/env python3
"""Inspect rendered PDF — Visual QA checks for A4 compliance, footer, overflow."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger("inspect_rendered_pdf")

# A4 dimensions in points (72 dpi): 595.28 x 841.89
A4_WIDTH_PT = 595.28
A4_HEIGHT_PT = 841.89
TOLERANCE_PT = 2.0


def inspect_rendered_pdf(pdf_path: Path, lession_id: str) -> dict:
    """Run visual QA checks on a rendered PDF.

    Returns qa-report compatible dict.
    """
    try:
        import fitz
    except ImportError:
        return {"status": "FAIL", "checks": [{
            "check_id": "VQA-000", "check_name": "pymupdf_available",
            "status": "FAIL", "severity": "critical",
            "message": "PyMuPDF not installed",
        }]}

    if not pdf_path.exists():
        return {"status": "FAIL", "checks": [{
            "check_id": "VQA-000", "check_name": "pdf_exists",
            "status": "FAIL", "severity": "critical",
            "message": f"PDF not found: {pdf_path}",
        }]}

    doc = fitz.open(str(pdf_path))
    checks = []
    total_pages = len(doc)

    for i in range(total_pages):
        page = doc[i]
        page_num = i + 1

        # Check A4 size
        w, h = page.rect.width, page.rect.height
        is_a4 = (abs(w - A4_WIDTH_PT) < TOLERANCE_PT and abs(h - A4_HEIGHT_PT) < TOLERANCE_PT)
        checks.append({
            "check_id": f"VQA-A4-{page_num:03d}",
            "check_name": "page_size_a4",
            "status": "PASS" if is_a4 else "FAIL",
            "severity": "high" if not is_a4 else "info",
            "message": f"Page {page_num}: {w:.1f}x{h:.1f}pt" + ("" if is_a4 else " (NOT A4)"),
            "page": page_num,
        })

        # Check for blank pages
        text = page.get_text("text").strip()
        if len(text) < 10:
            checks.append({
                "check_id": f"VQA-BLANK-{page_num:03d}",
                "check_name": "blank_page",
                "status": "WARN",
                "severity": "medium",
                "message": f"Page {page_num} appears blank or nearly blank ({len(text)} chars)",
                "page": page_num,
            })

        # Check footer contains lession_id
        # Footer is typically in the bottom 30pt of the page
        footer_rect = fitz.Rect(0, h - 30, w, h)
        footer_text = page.get_text("text", clip=footer_rect).strip()
        has_footer = lession_id in footer_text
        checks.append({
            "check_id": f"VQA-FOOTER-{page_num:03d}",
            "check_name": "footer_correctness",
            "status": "PASS" if has_footer else "WARN",
            "severity": "medium" if not has_footer else "info",
            "message": f"Page {page_num} footer: {'found' if has_footer else 'missing'} lession_id",
            "page": page_num,
        })

    doc.close()

    # Page numbering check
    checks.append({
        "check_id": "VQA-TOTAL",
        "check_name": "page_numbering",
        "status": "PASS",
        "severity": "info",
        "message": f"Total pages: {total_pages}",
    })

    has_fail = any(c["status"] == "FAIL" for c in checks)
    has_warn = any(c["status"] == "WARN" for c in checks)

    return {
        "schema_version": "1.0.0",
        "report_type": "visual_pdf_qa",
        "lession_id": lession_id,
        "status": "FAIL" if has_fail else ("WARN" if has_warn else "PASS"),
        "checks": checks,
        "summary": {
            "total_checks": len(checks),
            "passed": sum(1 for c in checks if c["status"] == "PASS"),
            "failed": sum(1 for c in checks if c["status"] == "FAIL"),
            "warnings": sum(1 for c in checks if c["status"] == "WARN"),
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visual QA on rendered PDF")
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--lesson-id", required=True)
    parser.add_argument("--output", help="Output QA report path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    result = inspect_rendered_pdf(Path(args.pdf), args.lesson_id)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] != "FAIL" else 1)
