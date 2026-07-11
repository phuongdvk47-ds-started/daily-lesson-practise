#!/usr/bin/env python3
"""PDF Structure Analyzer — page count, outline, text layer detection, headings."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("inspect_pdf")


def inspect_pdf(pdf_path: Path) -> dict[str, Any]:
    """Analyze PDF structure using PyMuPDF (fitz).

    Returns document-structure.json content.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed. Install with: pip install pymupdf")
        return {"error": "PyMuPDF not installed"}

    doc = fitz.open(str(pdf_path))

    # Basic metadata
    metadata = doc.metadata or {}

    # Outline / TOC
    toc = doc.get_toc(simple=True)  # [[level, title, page], ...]

    # Page inventory
    pages = []
    has_text_layer = False
    ocr_needed_pages = []

    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text").strip()
        images = page.get_images(full=True)

        page_info = {
            "page_number": i + 1,
            "width": round(page.rect.width, 2),
            "height": round(page.rect.height, 2),
            "has_text": len(text) > 10,
            "text_length": len(text),
            "image_count": len(images),
            "rotation": page.rotation,
        }
        pages.append(page_info)

        if len(text) > 10:
            has_text_layer = True
        elif len(images) > 0:
            ocr_needed_pages.append(i + 1)

    doc.close()

    result = {
        "schema_version": "1.0.0",
        "file_path": str(pdf_path),
        "page_count": len(pages),
        "has_text_layer": has_text_layer,
        "metadata": {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
        },
        "table_of_contents": [
            {"level": entry[0], "title": entry[1], "page": entry[2]}
            for entry in toc
        ],
        "ocr_needed_pages": ocr_needed_pages,
        "pages": pages,
    }

    return result


def save_inspection(result: dict, output_dir: Path) -> list[str]:
    """Save inspection results to JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # document-structure.json
    struct_path = output_dir / "document-structure.json"
    with open(struct_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # page-inventory.json (just the pages array)
    inv_path = output_dir / "page-inventory.json"
    with open(inv_path, "w", encoding="utf-8") as f:
        json.dump({"pages": result["pages"]}, f, indent=2, ensure_ascii=False)

    return [str(struct_path), str(inv_path)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect PDF structure")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    result = inspect_pdf(Path(args.pdf))
    if "error" in result:
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    artifacts = save_inspection(result, Path(args.output_dir))
    print(json.dumps({"status": "COMPLETE", "artifacts": artifacts}, indent=2))
