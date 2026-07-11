"""Tests for source fingerprinting — SHA-256 consistency and format."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from fingerprint_source import compute_sha256, generate_source_id


class TestFingerprint:
    def test_deterministic_hash(self):
        """Same file must produce same hash."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="wb") as f:
            f.write(b"test content for hashing")
            f.flush()
            path = Path(f.name)

        try:
            hash1 = compute_sha256(path)
            hash2 = compute_sha256(path)
            assert hash1 == hash2
        finally:
            path.unlink(missing_ok=True)

    def test_different_content_different_hash(self):
        """Different files must produce different hashes."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="wb") as f1:
            f1.write(b"content A")
            f1.flush()
            path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="wb") as f2:
            f2.write(b"content B")
            f2.flush()
            path2 = Path(f2.name)

        try:
            assert compute_sha256(path1) != compute_sha256(path2)
        finally:
            path1.unlink(missing_ok=True)
            path2.unlink(missing_ok=True)

    def test_hash_format(self):
        """Hash must be 64-char hex string."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="wb") as f:
            f.write(b"test")
            f.flush()
            path = Path(f.name)

        try:
            h = compute_sha256(path)
            assert len(h) == 64
            assert all(c in "0123456789abcdef" for c in h)
        finally:
            path.unlink(missing_ok=True)

    def test_generate_source_id_returns_dict(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="wb") as f:
            f.write(b"test source content")
            f.flush()
            path = Path(f.name)

        try:
            result = generate_source_id(path)
            assert "unique_source_id" in result
            assert "filename" in result
            assert "file_size_bytes" in result
            assert "sha256" in result
            assert result["unique_source_id"] == result["sha256"]
        finally:
            path.unlink(missing_ok=True)
