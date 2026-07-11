#!/usr/bin/env python3
"""Text & Asset Extractor — extract text blocks, images, tables from PDF pages."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("extract_pdf")


def extract_text_blocks(pdf_path: Path, pages: list[int] | None = None) -> list[dict]:
    """Extract text blocks with page, bbox, and reading order.

    Args:
        pdf_path: Path to PDF.
        pages: Optional list of 1-indexed page numbers. None = all pages.

    Returns:
        List of text block dicts per canonical schema.
    """
    try:
        import fitz
    except ImportError:
        logger.error("PyMuPDF not installed")
        return []

    doc = fitz.open(str(pdf_path))
    blocks = []
    block_counter = 0

    page_range = range(len(doc)) if pages is None else [p - 1 for p in pages if 0 < p <= len(doc)]

    for page_idx in page_range:
        page = doc[page_idx]
        page_blocks = page.get_text("dict", sort=True)["blocks"]

        for b in page_blocks:
            if b["type"] == 0:  # text block
                text_lines = []
                for line in b.get("lines", []):
                    spans_text = "".join(span["text"] for span in line.get("spans", []))
                    text_lines.append(spans_text)

                full_text = "\n".join(text_lines).strip()
                if not full_text:
                    continue

                block_counter += 1
                blocks.append({
                    "block_id": f"BLK-{block_counter:04d}",
                    "page": page_idx + 1,
                    "bbox": [round(b["bbox"][0], 2), round(b["bbox"][1], 2),
                             round(b["bbox"][2], 2), round(b["bbox"][3], 2)],
                    "method": "native_text",
                    "confidence": 1.0,
                    "text": full_text,
                })

    doc.close()
    return blocks


def extract_page_text(pdf_path: Path, page_number: int) -> str:
    """Extract full text from a single page."""
    try:
        import fitz
    except ImportError:
        return ""

    doc = fitz.open(str(pdf_path))
    if page_number < 1 or page_number > len(doc):
        doc.close()
        return ""

    text = doc[page_number - 1].get_text("text")
    doc.close()
    return text


def save_extraction(
    blocks: list[dict],
    output_dir: Path,
    manifest_extras: dict | None = None,
) -> list[str]:
    """Save extraction results to the extraction/ directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    text_dir = output_dir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)

    # Save all blocks
    blocks_path = text_dir / "text-blocks.json"
    with open(blocks_path, "w", encoding="utf-8") as f:
        json.dump(blocks, f, indent=2, ensure_ascii=False)

    # Save per-page text
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    pages_seen = set()
    for block in blocks:
        page = block["page"]
        if page not in pages_seen:
            pages_seen.add(page)

    for page in sorted(pages_seen):
        page_blocks = [b for b in blocks if b["page"] == page]
        page_text = "\n\n".join(b["text"] for b in page_blocks)
        page_path = pages_dir / f"page-{page:04d}.txt"
        page_path.write_text(page_text, encoding="utf-8")

    # Manifest
    manifest = {
        "total_blocks": len(blocks),
        "pages_extracted": sorted(pages_seen),
        "extraction_method": "native_text",
        **(manifest_extras or {}),
    }
    manifest_path = output_dir / "extraction-manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return [str(blocks_path), str(manifest_path)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract text from PDF")
    parser.add_argument("--pdf", required=True, help="Path to PDF")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--pages", type=str, help="Comma-separated page numbers (1-indexed)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    pages = [int(p) for p in args.pages.split(",")] if args.pages else None

    blocks = extract_text_blocks(Path(args.pdf), pages)
    artifacts = save_extraction(blocks, Path(args.output_dir))
    print(json.dumps({"status": "COMPLETE", "total_blocks": len(blocks), "artifacts": artifacts}, indent=2))
