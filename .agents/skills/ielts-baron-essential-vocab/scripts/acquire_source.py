#!/usr/bin/env python3
"""Source acquisition — download or copy the source PDF to cache."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import shutil
import sys
import urllib.request
from pathlib import Path

logger = logging.getLogger("acquire_source")


def _normalize_gdrive_url(url: str) -> str | None:
    """Extract Google Drive file ID and return a direct download URL.

    Supports:
    - https://drive.google.com/file/d/FILE_ID/view
    - https://drive.google.com/open?id=FILE_ID
    - https://docs.google.com/document/d/FILE_ID/...
    """
    patterns = [
        r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
        r"docs\.google\.com/\w+/d/([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return None


def acquire_source(source: str, dest_dir: Path) -> dict:
    """Acquire source file to dest_dir/original.pdf.

    Args:
        source: Local path or URL.
        dest_dir: Destination directory for source files.

    Returns:
        Result dict with status, artifacts, checksum.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "original.pdf"

    try:
        source_path = Path(source)
        if source_path.is_file():
            # Local file — copy
            shutil.copy2(source_path, dest_file)
            logger.info(f"Copied local file: {source} -> {dest_file}")
        elif source.startswith("http://") or source.startswith("https://"):
            # URL — download
            download_url = source
            if "drive.google.com" in source or "docs.google.com" in source:
                normalized = _normalize_gdrive_url(source)
                if normalized:
                    download_url = normalized
                else:
                    return {
                        "status": "FAILED",
                        "error_code": "SRC_ACCESS_DENIED",
                        "error_message": f"Cannot parse Google Drive URL: {source}",
                    }

            logger.info(f"Downloading: {download_url}")
            urllib.request.urlretrieve(download_url, str(dest_file))
            logger.info(f"Downloaded to: {dest_file}")
        else:
            return {
                "status": "FAILED",
                "error_code": "SRC_UNSUPPORTED_FORMAT",
                "error_message": f"Unsupported source: {source}",
            }

        # Compute checksum
        h = hashlib.sha256()
        with open(dest_file, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        checksum = h.hexdigest()

        # Write metadata
        metadata = {
            "original_source": source,
            "filename": "original.pdf",
            "checksum_sha256": checksum,
            "file_size_bytes": dest_file.stat().st_size,
        }
        meta_path = dest_dir / "source-metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Write checksum file
        checksum_path = dest_dir / "checksum.sha256"
        checksum_path.write_text(f"{checksum}  original.pdf\n", encoding="utf-8")

        return {
            "status": "COMPLETE",
            "artifacts": [str(dest_file), str(meta_path), str(checksum_path)],
            "output_checksum": checksum,
        }

    except urllib.error.HTTPError as e:
        return {
            "status": "FAILED",
            "error_code": "SRC_DOWNLOAD_FAILED",
            "error_message": f"HTTP {e.code}: {e.reason}",
        }
    except Exception as e:
        return {
            "status": "FAILED",
            "error_code": "SRC_DOWNLOAD_FAILED",
            "error_message": str(e),
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Acquire source PDF")
    parser.add_argument("--source", required=True, help="Local path or URL")
    parser.add_argument("--dest", required=True, help="Destination directory")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    result = acquire_source(args.source, Path(args.dest))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "COMPLETE" else 1)
