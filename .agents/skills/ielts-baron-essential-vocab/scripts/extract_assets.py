#!/usr/bin/env python3
"""Asset extractor — extract images, tables, charts from PDF pages."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger("extract_assets")


def extract_images(pdf_path: Path, output_dir: Path, pages: list[int] | None = None) -> list[dict]:
    """Extract images from PDF pages.

    Returns list of asset metadata dicts.
    """
    try:
        import fitz
    except ImportError:
        logger.error("PyMuPDF not installed")
        return []

    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    assets = []
    img_counter = 0

    page_range = range(len(doc)) if pages is None else [p - 1 for p in pages if 0 < p <= len(doc)]

    for page_idx in page_range:
        page = doc[page_idx]
        image_list = page.get_images(full=True)

        for img_info in image_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                if base_image is None:
                    continue

                img_ext = base_image.get("ext", "png")
                img_bytes = base_image.get("image", b"")
                if not img_bytes:
                    continue

                img_counter += 1
                filename = f"img-p{page_idx + 1:04d}-{img_counter:04d}.{img_ext}"
                img_path = images_dir / filename
                img_path.write_bytes(img_bytes)

                assets.append({
                    "asset_id": f"IMG-{img_counter:04d}",
                    "type": "image",
                    "path": str(img_path),
                    "page": page_idx + 1,
                    "width": base_image.get("width", 0),
                    "height": base_image.get("height", 0),
                    "format": img_ext,
                    "size_bytes": len(img_bytes),
                })

            except Exception as e:
                logger.warning(f"Failed to extract image xref={xref} on page {page_idx + 1}: {e}")

    doc.close()
    return assets


def extract_tables(pdf_path: Path, output_dir: Path, pages: list[int] | None = None) -> list[dict]:
    """Extract tables using pdfplumber (if available).

    Returns list of table metadata dicts.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.info("pdfplumber not installed — skipping table extraction")
        return []

    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    assets = []
    table_counter = 0

    with pdfplumber.open(str(pdf_path)) as pdf:
        page_range = range(len(pdf.pages)) if pages is None else [p - 1 for p in pages if 0 < p <= len(pdf.pages)]

        for page_idx in page_range:
            page = pdf.pages[page_idx]
            tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 2:
                    continue

                table_counter += 1
                table_path = tables_dir / f"table-p{page_idx + 1:04d}-{table_counter:04d}.json"
                with open(table_path, "w", encoding="utf-8") as f:
                    json.dump(table, f, indent=2, ensure_ascii=False)

                assets.append({
                    "asset_id": f"TBL-{table_counter:04d}",
                    "type": "table",
                    "path": str(table_path),
                    "page": page_idx + 1,
                    "rows": len(table),
                    "columns": max(len(row) for row in table) if table else 0,
                })

    return assets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract images and tables from PDF")
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--pages", type=str, help="Comma-separated page numbers")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    pages = [int(p) for p in args.pages.split(",")] if args.pages else None
    output = Path(args.output_dir)

    images = extract_images(Path(args.pdf), output, pages)
    tables = extract_tables(Path(args.pdf), output, pages)

    all_assets = images + tables
    manifest_path = output / "asset-manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"total_images": len(images), "total_tables": len(tables), "assets": all_assets}, f, indent=2, ensure_ascii=False)

    print(json.dumps({"status": "COMPLETE", "images": len(images), "tables": len(tables)}, indent=2))
