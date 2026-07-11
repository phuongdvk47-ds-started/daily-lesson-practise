#!/usr/bin/env python3
"""PDF Renderer — convert HTML to print-ready A4 PDF using Playwright/Chromium."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger("render_pdf")


def render_pdf(
    html_path: Path,
    pdf_path: Path,
    footer_template: str = "",
) -> dict:
    """Render an HTML file to A4 PDF using Playwright.

    Args:
        html_path: Path to HTML file.
        pdf_path: Path for output PDF.
        footer_template: HTML template for footer.

    Returns:
        Result dict.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "status": "FAILED",
            "error_code": "PDF_RENDER_FAILED",
            "error_message": "Playwright not installed",
        }

    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            # Load HTML
            file_url = html_path.as_uri()
            page.goto(file_url, wait_until="networkidle")

            # Render to PDF
            pdf_options = {
                "path": str(pdf_path),
                "format": "A4",
                "margin": {
                    "top": "14mm",
                    "right": "13mm",
                    "bottom": "16mm",
                    "left": "13mm",
                },
                "print_background": True,
            }

            if footer_template:
                pdf_options["display_header_footer"] = True
                pdf_options["footer_template"] = footer_template
                pdf_options["header_template"] = "<span></span>"

            page.pdf(**pdf_options)
            browser.close()

        # Verify PDF was created
        if not pdf_path.exists() or pdf_path.stat().st_size == 0:
            return {
                "status": "FAILED",
                "error_code": "PDF_RENDER_FAILED",
                "error_message": "PDF file is empty or not created",
            }

        return {
            "status": "COMPLETE",
            "artifacts": [str(pdf_path)],
            "pdf_size_bytes": pdf_path.stat().st_size,
        }

    except Exception as e:
        return {
            "status": "FAILED",
            "error_code": "PDF_RENDER_FAILED",
            "error_message": str(e),
        }


def build_footer_template(lession_id: str) -> str:
    """Build the footer HTML template with lesson ID and page numbers."""
    return (
        '<div style="font-size:8px; width:100%; text-align:center; '
        'font-family:\'Times New Roman\', serif; color:#666;">'
        f'{lession_id} | Page <span class="pageNumber"></span>'
        '/<span class="totalPages"></span>'
        '</div>'
    )


def render_all_pdfs(
    html_dir: Path,
    pdf_dir: Path,
    lession_id: str,
) -> dict:
    """Render all HTML files in a directory to PDFs.

    Returns combined result.
    """
    pdf_dir.mkdir(parents=True, exist_ok=True)
    footer = build_footer_template(lession_id)
    artifacts = []
    failures = []

    html_files = [
        ("daily-practice.html", "daily-practice.pdf"),
        ("vocabulary-grammar.html", "vocabulary-grammar.pdf"),
        ("answer-key.html", "answer-key.pdf"),
    ]

    for html_name, pdf_name in html_files:
        html_path = html_dir / html_name
        if not html_path.exists():
            failures.append({"file": html_name, "error": "HTML file not found"})
            continue

        pdf_path = pdf_dir / pdf_name
        result = render_pdf(html_path, pdf_path, footer)

        if result["status"] == "COMPLETE":
            artifacts.extend(result.get("artifacts", []))
        else:
            failures.append({"file": html_name, "error": result.get("error_message")})

    if failures:
        return {
            "status": "FAILED",
            "error_code": "PDF_RENDER_FAILED",
            "error_message": f"{len(failures)} PDF(s) failed to render",
            "artifacts": artifacts,
            "failures": failures,
        }

    return {"status": "COMPLETE", "artifacts": artifacts}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render HTML to A4 PDF")
    parser.add_argument("--html-dir", required=True, help="Directory with HTML files")
    parser.add_argument("--pdf-dir", required=True, help="Output directory for PDFs")
    parser.add_argument("--lesson-id", required=True, help="Lesson ID for footer")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    result = render_all_pdfs(Path(args.html_dir), Path(args.pdf_dir), args.lesson_id)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "COMPLETE" else 1)
