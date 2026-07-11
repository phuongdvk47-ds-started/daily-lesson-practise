#!/usr/bin/env python3
"""HTML Renderer — render document model to HTML using Jinja2 templates."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("render_html")

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "assets" / "templates"


def _load_template(template_name: str) -> str:
    """Load a Jinja2 template from the templates directory."""
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def render_html(
    document_model: dict,
    template_name: str,
    output_path: Path,
    extra_context: dict | None = None,
) -> dict:
    """Render a document model to HTML using Jinja2.

    Args:
        document_model: The document-model.json content.
        template_name: Name of template file in assets/templates/.
        output_path: Where to write the HTML.
        extra_context: Additional template context variables.

    Returns:
        Result dict with status and artifacts.
    """
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        return {
            "status": "FAILED",
            "error_code": "HTML_VALIDATION_FAILED",
            "error_message": "Jinja2 not installed. Install with: pip install jinja2",
        }

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )

    template = env.get_template(template_name)

    # Load print CSS
    css_path = TEMPLATES_DIR / "print.css"
    print_css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    context = {
        "model": document_model,
        "print_css": print_css,
        **(extra_context or {}),
    }

    html_content = template.render(**context)

    # Validate basic HTML structure
    if not html_content.strip():
        return {
            "status": "FAILED",
            "error_code": "HTML_VALIDATION_FAILED",
            "error_message": "Rendered HTML is empty",
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")

    return {
        "status": "COMPLETE",
        "artifacts": [str(output_path)],
        "html_size_bytes": len(html_content.encode("utf-8")),
    }


def render_all_documents(
    document_model: dict,
    output_dir: Path,
    lession_id: str,
) -> dict:
    """Render all three HTML documents from a document model.

    Returns combined result.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    all_artifacts = []

    templates = [
        ("daily-practice.html", "daily-practice.html"),
        ("vocabulary-grammar.html", "vocabulary-grammar.html"),
        ("answer-key.html", "answer-key.html"),
    ]

    for template_name, output_name in templates:
        output_path = output_dir / output_name
        result = render_html(
            document_model,
            template_name,
            output_path,
            extra_context={"lession_id": lession_id},
        )
        results.append(result)
        if result["status"] == "COMPLETE":
            all_artifacts.extend(result.get("artifacts", []))

    failed = [r for r in results if r["status"] != "COMPLETE"]
    if failed:
        return {
            "status": "FAILED",
            "error_code": "HTML_VALIDATION_FAILED",
            "error_message": f"{len(failed)} template(s) failed to render",
            "details": failed,
        }

    return {
        "status": "COMPLETE",
        "artifacts": all_artifacts,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render HTML from document model")
    parser.add_argument("--model", required=True, help="Path to document-model.json")
    parser.add_argument("--output-dir", required=True, help="Output directory for HTML files")
    parser.add_argument("--lesson-id", required=True, help="Lesson ID for footer")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    result = render_all_documents(model, Path(args.output_dir), args.lesson_id)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "COMPLETE" else 1)
