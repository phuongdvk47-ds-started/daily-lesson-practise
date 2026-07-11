#!/usr/bin/env python3
"""Execution & Model Router — Classifies tasks and selects the optimal engine.

Implements the deterministic-first, local-first, cost-aware routing policy.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("router")

# ---------------------------------------------------------------------------
# Routing Policy (from references/execution-routing.md)
# ---------------------------------------------------------------------------

ROUTING_POLICY: dict[str, dict[str, Any]] = {
    # --- DETERMINISTIC tasks ---
    "pdf_metadata": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "pymupdf",
        "fallback_engines": ["pdfplumber", "pypdf"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "file_download": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "urllib",
        "fallback_engines": ["requests"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "fingerprint": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "hashlib_sha256",
        "fallback_engines": [],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "text_extraction": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "pymupdf",
        "fallback_engines": ["pdfplumber", "pdfminer"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "table_extraction": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "pdfplumber",
        "fallback_engines": ["camelot", "tabula"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "image_extraction": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "pymupdf",
        "fallback_engines": ["pdfplumber"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "json_validation": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "jsonschema",
        "fallback_engines": ["pydantic"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "lesson_id_generation": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "python_stdlib",
        "fallback_engines": [],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "html_render": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "jinja2",
        "fallback_engines": [],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "pdf_render": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "playwright_chromium",
        "fallback_engines": ["weasyprint"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "footer_generation": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "jinja2",
        "fallback_engines": [],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "cache_management": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "python_stdlib",
        "fallback_engines": [],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "checksum_compare": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "hashlib_sha256",
        "fallback_engines": [],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "manifest_creation": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "python_stdlib",
        "fallback_engines": [],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "provenance_report": {
        "execution_class": "DETERMINISTIC",
        "preferred_engine": "python_stdlib",
        "fallback_engines": [],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },

    # --- LOCAL_MODEL tasks ---
    "ocr": {
        "execution_class": "LOCAL_MODEL",
        "preferred_engine": "paddleocr",
        "fallback_engines": ["tesseract"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "heading_detection": {
        "execution_class": "LOCAL_MODEL",
        "preferred_engine": "rule_based_plus_regex",
        "fallback_engines": ["sentence_transformer", "low_cost_llm"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "unit_candidate_detection": {
        "execution_class": "LOCAL_MODEL",
        "preferred_engine": "rule_based_plus_regex",
        "fallback_engines": ["sentence_transformer"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "keyword_extraction": {
        "execution_class": "LOCAL_MODEL",
        "preferred_engine": "spacy",
        "fallback_engines": ["nltk", "keybert"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "pos_tagging": {
        "execution_class": "LOCAL_MODEL",
        "preferred_engine": "spacy",
        "fallback_engines": ["stanza", "nltk"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "sentence_segmentation": {
        "execution_class": "LOCAL_MODEL",
        "preferred_engine": "spacy",
        "fallback_engines": ["nltk"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },
    "answer_leakage_detection": {
        "execution_class": "LOCAL_MODEL",
        "preferred_engine": "rule_based_string_match",
        "fallback_engines": ["sentence_transformer"],
        "premium_llm_allowed": False,
        "estimated_cost_class": "free",
    },

    # --- LOW_COST_LLM tasks ---
    "ocr_normalization": {
        "execution_class": "LOW_COST_LLM",
        "preferred_engine": "configured_low_cost_model",
        "fallback_engines": ["configured_reasoning_model"],
        "premium_llm_allowed": True,
        "estimated_cost_class": "low",
    },
    "vocabulary_grouping": {
        "execution_class": "LOW_COST_LLM",
        "preferred_engine": "configured_low_cost_model",
        "fallback_engines": ["configured_reasoning_model"],
        "premium_llm_allowed": True,
        "estimated_cost_class": "low",
    },
    "draft_explanation": {
        "execution_class": "LOW_COST_LLM",
        "preferred_engine": "configured_low_cost_model",
        "fallback_engines": ["configured_reasoning_model"],
        "premium_llm_allowed": True,
        "estimated_cost_class": "low",
    },

    # --- PREMIUM_LLM tasks ---
    "cefr_assessment": {
        "execution_class": "PREMIUM_LLM",
        "preferred_engine": "configured_reasoning_model",
        "fallback_engines": ["human_review"],
        "premium_llm_allowed": True,
        "estimated_cost_class": "medium",
    },
    "grammar_analysis": {
        "execution_class": "PREMIUM_LLM",
        "preferred_engine": "configured_reasoning_model",
        "fallback_engines": ["human_review"],
        "premium_llm_allowed": True,
        "estimated_cost_class": "medium",
    },
    "answer_explanation": {
        "execution_class": "PREMIUM_LLM",
        "preferred_engine": "configured_reasoning_model",
        "fallback_engines": ["human_review"],
        "premium_llm_allowed": True,
        "estimated_cost_class": "medium",
    },
    "ambiguity_resolution": {
        "execution_class": "PREMIUM_LLM",
        "preferred_engine": "configured_reasoning_model",
        "fallback_engines": ["human_review"],
        "premium_llm_allowed": True,
        "estimated_cost_class": "medium",
    },
    "final_academic_review": {
        "execution_class": "PREMIUM_LLM",
        "preferred_engine": "configured_reasoning_model",
        "fallback_engines": ["human_review"],
        "premium_llm_allowed": True,
        "estimated_cost_class": "high",
    },
}

# ---------------------------------------------------------------------------
# Core routing function
# ---------------------------------------------------------------------------

def route_task(
    task_name: str,
    task_complexity: str = "low",
    required_quality: float = 0.90,
    requires_reasoning: bool = False,
    requires_provenance: bool = True,
    privacy_level: str = "normal",
    allowed_execution_classes: list[str] | None = None,
) -> dict[str, Any]:
    """Route a task to the optimal execution engine.

    Returns a routing-decision dict per schemas/routing-decision.schema.json.
    """
    policy = ROUTING_POLICY.get(task_name)

    if policy is None:
        # Unknown task — default to PREMIUM_LLM with human fallback
        logger.warning(f"No routing policy for task '{task_name}' — defaulting to PREMIUM_LLM")
        policy = {
            "execution_class": "PREMIUM_LLM",
            "preferred_engine": "configured_reasoning_model",
            "fallback_engines": ["human_review"],
            "premium_llm_allowed": True,
            "estimated_cost_class": "high",
        }

    selected_class = policy["execution_class"]
    selected_engine = policy["preferred_engine"]

    # Check if execution class is allowed
    if allowed_execution_classes and selected_class not in allowed_execution_classes:
        # Try fallback engines
        for fb in policy.get("fallback_engines", []):
            # Map engine name back to class
            fb_class = _engine_to_class(fb)
            if fb_class in allowed_execution_classes:
                selected_class = fb_class
                selected_engine = fb
                break
        else:
            return {
                "task_name": task_name,
                "selected_execution_class": "BLOCKED",
                "selected_engine": "none",
                "decision_reason": f"No allowed engine for task '{task_name}'",
                "error_code": "EXECUTION_POLICY_VIOLATION",
            }

    # Enforce premium blocking
    if selected_class == "PREMIUM_LLM" and not policy.get("premium_llm_allowed", False):
        return {
            "task_name": task_name,
            "selected_execution_class": "BLOCKED",
            "selected_engine": "none",
            "decision_reason": f"Premium LLM not allowed for task '{task_name}'",
            "error_code": "EXECUTION_POLICY_VIOLATION",
        }

    # Privacy enforcement
    if privacy_level == "local-only" and selected_class in ("LOW_COST_LLM", "PREMIUM_LLM"):
        # Try to find local alternative
        if policy.get("fallback_engines"):
            for fb in policy["fallback_engines"]:
                fb_class = _engine_to_class(fb)
                if fb_class in ("DETERMINISTIC", "LOCAL_MODEL"):
                    selected_class = fb_class
                    selected_engine = fb
                    break
            else:
                return {
                    "task_name": task_name,
                    "selected_execution_class": "BLOCKED",
                    "selected_engine": "none",
                    "decision_reason": f"Privacy requires local-only but no local engine available for '{task_name}'",
                    "error_code": "PRIVACY_POLICY_VIOLATION",
                }

    # Build budget
    budget = _get_budget(task_name, selected_class)

    return {
        "task_name": task_name,
        "task_complexity": task_complexity,
        "required_quality": required_quality,
        "requires_reasoning": requires_reasoning,
        "requires_provenance": requires_provenance,
        "privacy_level": privacy_level,
        "selected_execution_class": selected_class,
        "selected_engine": selected_engine,
        "fallback_chain": policy.get("fallback_engines", []),
        "budget": budget,
        "cache_key": "",
        "escalation_policy": {
            "escalate_on": ["schema_validation_fail", "confidence_below_threshold", "retry_limit_exceeded"],
            "escalate_to": _next_class(selected_class),
        },
        "decision_reason": f"Policy match for '{task_name}': {selected_class}/{selected_engine}",
    }


def validate_routing_decision(task_name: str, decision: dict) -> bool:
    """Validate that a routing decision complies with execution policy."""
    policy = ROUTING_POLICY.get(task_name, {})

    if decision.get("selected_execution_class") == "PREMIUM_LLM":
        if not policy.get("premium_llm_allowed", False):
            logger.error(f"EXECUTION_POLICY_VIOLATION: Premium LLM not allowed for '{task_name}'")
            return False

    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ENGINE_CLASS_MAP = {
    "pymupdf": "DETERMINISTIC",
    "pdfplumber": "DETERMINISTIC",
    "pypdf": "DETERMINISTIC",
    "pdfminer": "DETERMINISTIC",
    "hashlib_sha256": "DETERMINISTIC",
    "python_stdlib": "DETERMINISTIC",
    "jinja2": "DETERMINISTIC",
    "playwright_chromium": "DETERMINISTIC",
    "weasyprint": "DETERMINISTIC",
    "jsonschema": "DETERMINISTIC",
    "pydantic": "DETERMINISTIC",
    "urllib": "DETERMINISTIC",
    "requests": "DETERMINISTIC",
    "rule_based_plus_regex": "LOCAL_MODEL",
    "rule_based_string_match": "LOCAL_MODEL",
    "rule_based_plus_sentence_transformer": "LOCAL_MODEL",
    "sentence_transformer": "LOCAL_MODEL",
    "spacy": "LOCAL_MODEL",
    "stanza": "LOCAL_MODEL",
    "nltk": "LOCAL_MODEL",
    "keybert": "LOCAL_MODEL",
    "paddleocr": "LOCAL_MODEL",
    "tesseract": "LOCAL_MODEL",
    "configured_low_cost_model": "LOW_COST_LLM",
    "configured_reasoning_model": "PREMIUM_LLM",
    "human_review": "HUMAN_REQUIRED",
}

_CLASS_ORDER = ["DETERMINISTIC", "LOCAL_MODEL", "LOW_COST_LLM", "PREMIUM_LLM", "HUMAN_REQUIRED"]

_BUDGET_DEFAULTS = {
    "DETERMINISTIC": {"max_input_tokens": 0, "max_output_tokens": 0, "max_attempts": 3, "max_cost_class": "free", "premium_escalation_allowed": False},
    "LOCAL_MODEL": {"max_input_tokens": 4000, "max_output_tokens": 2000, "max_attempts": 3, "max_cost_class": "free", "premium_escalation_allowed": False},
    "LOW_COST_LLM": {"max_input_tokens": 6000, "max_output_tokens": 2000, "max_attempts": 2, "max_cost_class": "low", "premium_escalation_allowed": True},
    "PREMIUM_LLM": {"max_input_tokens": 8000, "max_output_tokens": 4000, "max_attempts": 2, "max_cost_class": "medium", "premium_escalation_allowed": False},
    "HUMAN_REQUIRED": {"max_input_tokens": 0, "max_output_tokens": 0, "max_attempts": 1, "max_cost_class": "free", "premium_escalation_allowed": False},
}


def _engine_to_class(engine: str) -> str:
    return _ENGINE_CLASS_MAP.get(engine, "PREMIUM_LLM")


def _next_class(current_class: str) -> str:
    idx = _CLASS_ORDER.index(current_class) if current_class in _CLASS_ORDER else 0
    if idx < len(_CLASS_ORDER) - 1:
        return _CLASS_ORDER[idx + 1]
    return "HUMAN_REQUIRED"


def _get_budget(task_name: str, execution_class: str) -> dict:
    return dict(_BUDGET_DEFAULTS.get(execution_class, _BUDGET_DEFAULTS["DETERMINISTIC"]))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Route a task to the optimal engine")
    parser.add_argument("--task", required=True, help="Task name from routing policy")
    parser.add_argument("--complexity", default="low", choices=["low", "medium", "high"])
    parser.add_argument("--quality", type=float, default=0.90)
    parser.add_argument("--privacy", default="normal", choices=["local-only", "restricted", "normal"])
    args = parser.parse_args()

    decision = route_task(
        task_name=args.task,
        task_complexity=args.complexity,
        required_quality=args.quality,
        privacy_level=args.privacy,
    )
    print(json.dumps(decision, indent=2))
