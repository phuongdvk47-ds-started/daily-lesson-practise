"""Tests for HTML quality — template rendering, no empty lines, structure."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"


class TestTemplateExists:
    def test_daily_practice_template(self):
        assert (TEMPLATES_DIR / "daily-practice.html").exists()

    def test_vocabulary_grammar_template(self):
        assert (TEMPLATES_DIR / "vocabulary-grammar.html").exists()

    def test_answer_key_template(self):
        assert (TEMPLATES_DIR / "answer-key.html").exists()

    def test_print_css(self):
        assert (TEMPLATES_DIR / "print.css").exists()


class TestPrintCSS:
    def test_a4_page_size(self):
        css = (TEMPLATES_DIR / "print.css").read_text(encoding="utf-8")
        assert "size: A4" in css

    def test_margins(self):
        css = (TEMPLATES_DIR / "print.css").read_text(encoding="utf-8")
        assert "margin:" in css

    def test_times_new_roman(self):
        css = (TEMPLATES_DIR / "print.css").read_text(encoding="utf-8")
        assert "Times New Roman" in css

    def test_orphan_widow_rules(self):
        css = (TEMPLATES_DIR / "print.css").read_text(encoding="utf-8")
        assert "orphans:" in css
        assert "widows:" in css

    def test_page_break_avoid(self):
        css = (TEMPLATES_DIR / "print.css").read_text(encoding="utf-8")
        assert "page-break-inside: avoid" in css or "break-inside: avoid" in css


class TestTemplateStructure:
    def test_daily_practice_no_br_br(self):
        """Templates should not use <br><br> for spacing."""
        for template_name in ["daily-practice.html", "vocabulary-grammar.html", "answer-key.html"]:
            content = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
            assert "<br><br>" not in content, f"{template_name} contains <br><br>"

    def test_templates_have_doctype(self):
        for template_name in ["daily-practice.html", "vocabulary-grammar.html", "answer-key.html"]:
            content = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
            assert "<!DOCTYPE html>" in content, f"{template_name} missing DOCTYPE"

    def test_templates_have_charset(self):
        for template_name in ["daily-practice.html", "vocabulary-grammar.html", "answer-key.html"]:
            content = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
            assert 'charset="UTF-8"' in content, f"{template_name} missing charset"
