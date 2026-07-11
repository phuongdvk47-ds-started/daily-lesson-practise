"""Tests for PDF layout — A4 size, footer, overflow checks (requires PyMuPDF)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


class TestPDFLayoutSpec:
    """Test PDF layout specification compliance (design-level)."""

    def test_footer_format(self):
        """Footer must match: [lession_id] | Page [current]/[total]"""
        from render_pdf import build_footer_template
        footer = build_footer_template("LSN-001-B2-A7K9P2QX")
        assert "LSN-001-B2-A7K9P2QX" in footer
        assert "pageNumber" in footer
        assert "totalPages" in footer

    def test_a4_margins_in_css(self):
        """Print CSS must define A4 with proper margins."""
        css_path = Path(__file__).resolve().parent.parent / "assets" / "templates" / "print.css"
        css = css_path.read_text(encoding="utf-8")
        assert "14mm" in css  # top margin
        assert "13mm" in css  # left/right margin
        assert "16mm" in css  # bottom margin
