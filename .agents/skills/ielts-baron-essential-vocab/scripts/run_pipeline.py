#!/usr/bin/env python3
"""Orchestrator CLI — Entry point for the ielts-baron-essential-vocab pipeline.

Usage:
    python scripts/run_pipeline.py --source "path/to/barron.pdf" --unit "Unit 1" --day 1
    python scripts/run_pipeline.py --lesson-id "LSN-001-B2-A7K9P2QX" --from-stage html-render --force-rerender
    python scripts/run_pipeline.py --resume --lesson-id "LSN-001-B2-A7K9P2QX"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SKILL_NAME = "ielts-baron-essential-vocab"
SKILL_VERSION = "1.0.0"

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = SKILL_ROOT.parent.parent.parent  # .agents/skills/<skill>/ -> project root

DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / SKILL_NAME
DEFAULT_CACHE_ROOT = PROJECT_ROOT / ".cache" / SKILL_NAME

SCHEMAS_DIR = SKILL_ROOT / "schemas"

# Pipeline stage order
STAGE_ORDER = [
    "request-intake",
    "execution-routing",
    "cache-resolve",
    "source-acquire",
    "pdf-structure",
    "text-extract",
    "unit-locate",
    "source-canonicalize",
    "grounding-validate",
    "level-assess",
    "lesson-id",
    "vocabulary-build",
    "grammar-analyze",
    "practice-compose",
    "answer-build",
    "content-qa",
    "document-model",
    "html-render",
    "pdf-render",
    "pdf-visual-qa",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("pipeline")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _compute_file_hash(path: Path) -> str:
    """SHA-256 of file bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Pipeline State
# ---------------------------------------------------------------------------

def _init_pipeline_state(unique_source_id: str) -> dict:
    """Create a fresh pipeline-state.json."""
    stages = {}
    for name in STAGE_ORDER:
        stages[name] = {
            "stage_name": name,
            "status": "PENDING",
            "input_checksum": None,
            "output_checksum": None,
            "stage_version": SKILL_VERSION,
            "started_at": None,
            "completed_at": None,
            "retry_count": 0,
            "error_code": None,
            "error_message": None,
            "artifacts": [],
        }
    return {
        "schema_version": "1.0.0",
        "pipeline_id": f"PL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "unique_source_id": unique_source_id,
        "lession_id": None,
        "current_stage": None,
        "overall_status": "PENDING",
        "stages": stages,
        "human_decisions": [],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }


def _load_or_init_state(state_path: Path, unique_source_id: str) -> dict:
    if state_path.exists():
        return _load_json(state_path)
    state = _init_pipeline_state(unique_source_id)
    _save_json(state_path, state)
    return state


def _update_stage(state: dict, stage_name: str, **kwargs) -> None:
    if stage_name in state["stages"]:
        state["stages"][stage_name].update(kwargs)
    state["updated_at"] = _now_iso()


# ---------------------------------------------------------------------------
# Stage runners (dispatch to individual scripts)
# ---------------------------------------------------------------------------

def _run_stage(stage_name: str, state: dict, ctx: dict) -> bool:
    """Run a single pipeline stage. Returns True if successful."""
    stage_state = state["stages"].get(stage_name)
    if not stage_state:
        logger.error(f"Unknown stage: {stage_name}")
        return False

    # Cache-first check
    if stage_state["status"] == "SKIPPED_FROM_CACHE" and not ctx.get("force"):
        logger.info(f"Stage '{stage_name}' skipped (cached)")
        return True

    if stage_state["status"] == "COMPLETE" and not ctx.get("force"):
        logger.info(f"Stage '{stage_name}' already complete")
        return True

    logger.info(f"Running stage: {stage_name}")
    _update_stage(state, stage_name, status="RUNNING", started_at=_now_iso())

    try:
        # Dispatch to stage-specific handler
        handler = STAGE_HANDLERS.get(stage_name)
        if handler is None:
            logger.warning(f"Stage '{stage_name}' handler not implemented yet — marking PENDING")
            _update_stage(state, stage_name, status="PENDING")
            return True  # Non-blocking for stub stages

        result = handler(state, ctx)
        if result.get("status") == "WAITING_FOR_HUMAN":
            _update_stage(state, stage_name, status="WAITING_FOR_HUMAN")
            logger.info(f"Stage '{stage_name}' waiting for human review")
            return False
        elif result.get("status") == "FAILED":
            _update_stage(
                state, stage_name,
                status="FAILED",
                error_code=result.get("error_code"),
                error_message=result.get("error_message"),
                completed_at=_now_iso(),
            )
            logger.error(f"Stage '{stage_name}' failed: {result.get('error_message')}")
            return False
        else:
            _update_stage(
                state, stage_name,
                status="COMPLETE",
                completed_at=_now_iso(),
                artifacts=result.get("artifacts", []),
                output_checksum=result.get("output_checksum"),
            )
            return True

    except Exception as e:
        _update_stage(
            state, stage_name,
            status="FAILED",
            error_code="STAGE_EXCEPTION",
            error_message=str(e),
            completed_at=_now_iso(),
        )
        logger.exception(f"Stage '{stage_name}' raised exception")
        return False


# ---------------------------------------------------------------------------
# Stage handler: request-intake
# ---------------------------------------------------------------------------

def _handle_request_intake(state: dict, ctx: dict) -> dict:
    """Normalize the incoming request into request.normalized.json."""
    import string
    import secrets

    random_id = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    request_id = f"REQ-{random_id}"

    source_input = ctx["source"]
    if source_input and (source_input.startswith("http://") or source_input.startswith("https://")):
        source_type = "google_drive_url"
    elif source_input:
        source_type = "local_file"
    else:
        return {"status": "FAILED", "error_code": "SRC_UNSUPPORTED_FORMAT", "error_message": "No source provided"}

    normalized = {
        "request_id": request_id,
        "source": {
            "type": source_type,
            "location": source_input,
            "original_input": source_input,
        },
        "target": {
            "unit": ctx.get("unit"),
            "topic": ctx.get("topic"),
            "day": ctx.get("day", 1),
        },
        "options": {
            "force_reextract": ctx.get("force_reextract", False),
            "force_rebuild_content": ctx.get("force_rebuild_content", False),
            "force_rerender": ctx.get("force_rerender", False),
            "human_review": ctx.get("human_review", True),
            "skip_human_review": ctx.get("skip_human_review", False),
            "from_stage": ctx.get("from_stage"),
            "to_stage": ctx.get("to_stage"),
            "resume": ctx.get("resume", False),
            "lesson_id": ctx.get("lesson_id"),
            "output_root": str(ctx.get("output_root", DEFAULT_OUTPUT_ROOT)),
            "cache_root": str(ctx.get("cache_root", DEFAULT_CACHE_ROOT)),
            "page": ctx.get("page"),
            "force_page_reextract": ctx.get("force_page_reextract", False),
        },
        "created_at": _now_iso(),
    }

    # Save to cache
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    out_path = cache_root / source_id / "state" / "request.normalized.json"
    _save_json(out_path, normalized)

    return {
        "status": "COMPLETE",
        "artifacts": [str(out_path)],
    }


# ---------------------------------------------------------------------------
# Stage handler: cache-resolve
# ---------------------------------------------------------------------------

def _handle_cache_resolve(state: dict, ctx: dict) -> dict:
    """Check cache for existing artifacts and mark stages as SKIPPED_FROM_CACHE."""
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    cache_dir = cache_root / source_id

    manifest_path = cache_dir / "cache-manifest.json"
    if manifest_path.exists():
        manifest = _load_json(manifest_path)
        cached_stages = manifest.get("cached_stages", [])
        for stage_name in cached_stages:
            if stage_name in state["stages"] and not ctx.get("force_reextract"):
                _update_stage(state, stage_name, status="SKIPPED_FROM_CACHE")
        logger.info(f"Cache resolved: {len(cached_stages)} stages cached")
    else:
        logger.info("No cache manifest found — fresh run")

    return {"status": "COMPLETE", "artifacts": []}


# ---------------------------------------------------------------------------
# Stage handler: source-acquire
# ---------------------------------------------------------------------------

def _handle_source_acquire(state: dict, ctx: dict) -> dict:
    """Download or copy the source PDF."""
    from acquire_source import acquire_source

    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    source_dir = cache_root / source_id / "source"

    source_input = ctx.get("source")
    if not source_input:
        return {"status": "FAILED", "error_code": "SRC_UNSUPPORTED_FORMAT",
                "error_message": "No source provided"}

    result = acquire_source(source_input, source_dir)
    return result


# ---------------------------------------------------------------------------
# Stage handler: execution-routing
# ---------------------------------------------------------------------------

def _handle_execution_routing(state: dict, ctx: dict) -> dict:
    """Log execution class for all upcoming stages."""
    from route_execution import route_task

    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    routing_dir = cache_root / source_id / "state"
    routing_dir.mkdir(parents=True, exist_ok=True)

    routing_decisions = {}
    # Map pipeline stage names to routing task names
    stage_to_task = {
        "source-acquire": "file_download",
        "pdf-structure": "pdf_metadata",
        "text-extract": "text_extraction",
        "unit-locate": "unit_candidate_detection",
        "source-canonicalize": "json_validation",
        "grounding-validate": "json_validation",
        "level-assess": "cefr_assessment",
        "lesson-id": "lesson_id_generation",
        "vocabulary-build": "vocabulary_grouping",
        "grammar-analyze": "grammar_analysis",
        "practice-compose": "json_validation",
        "answer-build": "answer_explanation",
        "content-qa": "json_validation",
        "document-model": "json_validation",
        "html-render": "html_render",
        "pdf-render": "pdf_render",
        "pdf-visual-qa": "pdf_metadata",
    }

    for stage_name, task_name in stage_to_task.items():
        decision = route_task(task_name)
        routing_decisions[stage_name] = {
            "task": task_name,
            "execution_class": decision["selected_execution_class"],
            "engine": decision["selected_engine"],
        }

    out_path = routing_dir / "routing-decisions.json"
    _save_json(out_path, routing_decisions)
    logger.info(f"Routing decisions saved for {len(routing_decisions)} stages")
    return {"status": "COMPLETE", "artifacts": [str(out_path)]}


# ---------------------------------------------------------------------------
# Stage handler: pdf-structure
# ---------------------------------------------------------------------------

def _handle_pdf_structure(state: dict, ctx: dict) -> dict:
    """Analyze PDF structure — page count, TOC, text layer detection."""
    from inspect_pdf import inspect_pdf, save_inspection

    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    source_pdf = cache_root / source_id / "source" / "original.pdf"
    extraction_dir = cache_root / source_id / "extraction"

    if not source_pdf.exists():
        return {"status": "FAILED", "error_code": "SRC_UNSUPPORTED_FORMAT",
                "error_message": f"Source PDF not found: {source_pdf}"}

    result = inspect_pdf(source_pdf)
    if "error" in result:
        return {"status": "FAILED", "error_code": "PDF_TEXT_LAYER_MISSING",
                "error_message": result["error"]}

    artifacts = save_inspection(result, extraction_dir)

    # Check for encrypted PDF
    if result.get("page_count", 0) == 0:
        return {"status": "FAILED", "error_code": "PDF_ENCRYPTED",
                "error_message": "PDF appears encrypted or has no pages"}

    return {"status": "COMPLETE", "artifacts": artifacts}


# ---------------------------------------------------------------------------
# Stage handler: text-extract
# ---------------------------------------------------------------------------

def _handle_text_extract(state: dict, ctx: dict) -> dict:
    """Extract text blocks from PDF."""
    from extract_pdf import extract_text_blocks, save_extraction
    from extract_assets import extract_images, extract_tables

    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    source_pdf = cache_root / source_id / "source" / "original.pdf"
    extraction_dir = cache_root / source_id / "extraction"

    if not source_pdf.exists():
        return {"status": "FAILED", "error_code": "SRC_UNSUPPORTED_FORMAT",
                "error_message": f"Source PDF not found: {source_pdf}"}

    # Extract text blocks
    target_page = ctx.get("page")
    pages = [target_page] if target_page else None
    blocks = extract_text_blocks(source_pdf, pages)

    if not blocks:
        return {"status": "FAILED", "error_code": "PDF_TEXT_LAYER_MISSING",
                "error_message": "No text blocks extracted"}

    text_artifacts = save_extraction(blocks, extraction_dir)

    # Extract images and tables
    try:
        images = extract_images(source_pdf, extraction_dir, pages)
        tables = extract_tables(source_pdf, extraction_dir, pages)
        asset_manifest = {
            "total_images": len(images),
            "total_tables": len(tables),
            "assets": images + tables,
        }
        asset_path = extraction_dir / "asset-manifest.json"
        _save_json(asset_path, asset_manifest)
        text_artifacts.append(str(asset_path))
    except Exception as e:
        logger.warning(f"Asset extraction partial failure: {e}")

    return {"status": "COMPLETE", "artifacts": text_artifacts}


# ---------------------------------------------------------------------------
# Stage handler: unit-locate
# ---------------------------------------------------------------------------

def _handle_unit_locate(state: dict, ctx: dict) -> dict:
    """Locate the target unit/topic in the extraction data.

    Uses rule-based heading detection first, then falls back to LLM if needed.
    """
    import re

    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    extraction_dir = cache_root / source_id / "extraction"
    units_dir = cache_root / source_id / "units"
    units_dir.mkdir(parents=True, exist_ok=True)

    target_unit = ctx.get("unit", "")
    target_topic = ctx.get("topic", "")

    # Load text blocks
    blocks_path = extraction_dir / "text" / "text-blocks.json"
    if not blocks_path.exists():
        return {"status": "FAILED", "error_code": "UNIT_NOT_FOUND",
                "error_message": "No text blocks to search"}

    blocks = _load_json(blocks_path)

    # Rule-based heading detection
    candidates = []
    unit_patterns = [
        r"(?i)unit\s*(\d+)\s*[:\-–—]?\s*(.*)",
        r"(?i)chapter\s*(\d+)\s*[:\-–—]?\s*(.*)",
        r"(?i)lesson\s*(\d+)\s*[:\-–—]?\s*(.*)",
    ]

    for block in blocks:
        text = block.get("text", "").strip()
        for pattern in unit_patterns:
            match = re.match(pattern, text)
            if match:
                unit_num = match.group(1)
                unit_title = match.group(2).strip() if match.group(2) else ""
                confidence = 0.0

                # Score by match quality
                if target_unit:
                    # Try exact number match
                    target_num = re.search(r"(\d+)", target_unit)
                    if target_num and target_num.group(1) == unit_num:
                        confidence = 0.95
                    elif target_unit.lower() in text.lower():
                        confidence = 0.90
                    else:
                        confidence = 0.50

                if target_topic and target_topic.lower() in unit_title.lower():
                    confidence = max(confidence, 0.90)

                candidates.append({
                    "unit_number": int(unit_num),
                    "unit_title": unit_title,
                    "page": block.get("page", 0),
                    "block_id": block.get("block_id", ""),
                    "confidence": confidence,
                    "raw_text": text[:200],
                })

    if not candidates and not target_unit and not target_topic:
        # No target specified — return all found units
        return {"status": "FAILED", "error_code": "UNIT_NOT_FOUND",
                "error_message": "No --unit or --topic specified and no units detected"}

    # Sort by confidence
    candidates.sort(key=lambda c: c["confidence"], reverse=True)

    if not candidates:
        return {"status": "FAILED", "error_code": "UNIT_NOT_FOUND",
                "error_message": f"Unit '{target_unit}' not found in extraction"}

    best = candidates[0]
    if best["confidence"] < 0.90:
        if len(candidates) > 1:
            logger.warning(f"Multiple ambiguous candidates: {len(candidates)}")
            # Check if human review needed
            if not ctx.get("skip_human_review"):
                location_result = {
                    "candidates": candidates[:5],
                    "selected": None,
                    "confidence": best["confidence"],
                    "needs_human_review": True,
                }
                location_path = units_dir / "unit-location.json"
                _save_json(location_path, location_result)
                return {"status": "WAITING_FOR_HUMAN",
                        "error_code": "UNIT_AMBIGUOUS",
                        "error_message": f"Multiple candidates, best confidence: {best['confidence']:.2f}"}

    # Find the unit's page range by looking for the next unit heading
    start_page = best["page"]
    end_page = start_page  # Default to same page

    for candidate in candidates:
        if candidate["unit_number"] != best["unit_number"] and candidate["page"] > start_page:
            end_page = candidate["page"] - 1
            break

    if end_page <= start_page:
        # No next unit found — estimate 15 pages per unit
        end_page = start_page + 14

    # Detect sub-sections within the page range
    sections = {"reading": None, "questions": None, "vocabulary": None,
                "word_family": None, "answer_key": None}
    section_patterns = {
        "reading": r"(?i)(reading\s*(passage|text)?|passage\s*\d*)",
        "questions": r"(?i)(questions?\s*\d+|questions?\s*$)",
        "vocabulary": r"(?i)(vocabulary|target\s*words?|word\s*list)",
        "word_family": r"(?i)(word\s*famil|word\s*forms?)",
        "answer_key": r"(?i)(answer\s*key|answers?\s*$)",
    }

    for block in blocks:
        page = block.get("page", 0)
        if start_page <= page <= end_page:
            text = block.get("text", "").strip()
            for section_name, pattern in section_patterns.items():
                if sections[section_name] is None and re.search(pattern, text):
                    sections[section_name] = {
                        "page": page,
                        "block_id": block.get("block_id", ""),
                        "text": text[:100],
                    }

    location_result = {
        "unit_id": f"unit-{best['unit_number']:02d}",
        "unit_number": best["unit_number"],
        "unit_name": best.get("unit_title", f"Unit {best['unit_number']}"),
        "topic": best.get("unit_title", ""),
        "page_range": {"start": start_page, "end": end_page},
        "confidence": best["confidence"],
        "heading_block_id": best["block_id"],
        "sections": sections,
        "all_candidates": candidates[:5],
    }

    location_path = units_dir / "unit-location.json"
    _save_json(location_path, location_result)

    logger.info(f"Located {location_result['unit_name']} on pages {start_page}-{end_page} "
                f"(confidence: {best['confidence']:.2f})")

    return {"status": "COMPLETE", "artifacts": [str(location_path)]}


# ---------------------------------------------------------------------------
# Stage handler: source-canonicalize
# ---------------------------------------------------------------------------

def _handle_source_canonicalize(state: dict, ctx: dict) -> dict:
    """Convert extraction into canonical source model."""
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    extraction_dir = cache_root / source_id / "extraction"
    units_dir = cache_root / source_id / "units"

    # Load unit location
    location_path = units_dir / "unit-location.json"
    if not location_path.exists():
        return {"status": "FAILED", "error_code": "UNIT_NOT_FOUND",
                "error_message": "unit-location.json not found — run unit-locate first"}

    location = _load_json(location_path)
    page_range = location.get("page_range", {})
    start_page = page_range.get("start", 1)
    end_page = page_range.get("end", start_page + 14)

    # Load text blocks
    blocks_path = extraction_dir / "text" / "text-blocks.json"
    if not blocks_path.exists():
        return {"status": "FAILED", "error_code": "UNIT_NOT_FOUND",
                "error_message": "text-blocks.json not found"}

    all_blocks = _load_json(blocks_path)

    # Filter blocks to unit page range
    unit_blocks = [b for b in all_blocks if start_page <= b.get("page", 0) <= end_page]

    # Build canonical source model
    paragraphs = []
    questions = []
    vocabulary_items = []
    answer_key_items = []
    unresolved = []

    sections = location.get("sections", {})

    # Classify blocks into sections
    current_section = "reading"
    para_counter = 0
    question_counter = 0

    import re

    for block in unit_blocks:
        text = block.get("text", "").strip()
        page = block.get("page", 0)
        block_id = block.get("block_id", "")

        if not text:
            continue

        # Detect section transitions
        if re.search(r"(?i)(questions?\s*\d+|questions?\s*$)", text):
            current_section = "questions"
            continue
        elif re.search(r"(?i)(vocabulary|target\s*words?)", text):
            current_section = "vocabulary"
            continue
        elif re.search(r"(?i)(word\s*famil|word\s*forms?)", text):
            current_section = "word_family"
            continue
        elif re.search(r"(?i)(answer\s*key|answers?\s*$)", text):
            current_section = "answer_key"
            continue

        source_ref = {
            "source_id": source_id,
            "page": page,
            "block_id": block_id,
            "extraction_method": "native_text",
            "confidence": block.get("confidence", 1.0),
        }

        if current_section == "reading":
            para_counter += 1
            # Check if paragraph starts with a letter label (A, B, C...)
            label_match = re.match(r"^([A-Z])\.\s+", text)
            para_id = label_match.group(1) if label_match else f"P{para_counter}"
            clean_text = text[len(label_match.group(0)):] if label_match else text

            paragraphs.append({
                "paragraph_id": para_id,
                "text": clean_text,
                "source_refs": [source_ref],
                "content_class": "SOURCE_EXTRACTED",
            })

        elif current_section == "questions":
            # Parse numbered questions
            q_match = re.match(r"^(\d+)[.\)]\s*(.*)", text, re.DOTALL)
            if q_match:
                question_counter += 1
                questions.append({
                    "question_id": f"Q{int(q_match.group(1)):02d}",
                    "question_number": int(q_match.group(1)),
                    "text": q_match.group(2).strip(),
                    "type": "unknown",  # Will be classified by content agent
                    "source_refs": [source_ref],
                })

        elif current_section == "vocabulary":
            vocabulary_items.append({
                "word": text.split("\n")[0].strip()[:50],
                "raw_text": text,
                "source_refs": [source_ref],
                "content_class": "SOURCE_EXTRACTED",
            })

        elif current_section == "answer_key":
            # Parse answer entries
            ans_matches = re.findall(r"(\d+)[.\)]\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)", text)
            for num, answer in ans_matches:
                answer_key_items.append({
                    "question_id": f"Q{int(num):02d}",
                    "answer": answer.strip(),
                    "source_refs": [source_ref],
                })

    # Report unresolved items
    if not paragraphs:
        unresolved.append({
            "item_id": "UNRES-001",
            "type": "reading_passage_missing",
            "description": "No reading passage paragraphs detected",
            "severity": "critical",
            "suggested_action": "human_review",
        })

    if not questions:
        unresolved.append({
            "item_id": "UNRES-002",
            "type": "questions_missing",
            "description": "No questions detected",
            "severity": "high",
            "suggested_action": "manual_page_review",
        })

    if not answer_key_items:
        unresolved.append({
            "item_id": "UNRES-003",
            "type": "answer_key_missing",
            "description": "Answer key not found within unit page range",
            "severity": "high",
            "suggested_action": "search_end_of_book",
        })

    canonical = {
        "schema_version": "1.0.0",
        "unique_source_id": source_id,
        "unit": {
            "unit_id": location.get("unit_id", ""),
            "unit_name": location.get("unit_name", ""),
            "topic": location.get("topic", ""),
            "page_range": page_range,
        },
        "reading_passage": {
            "title": location.get("unit_name", ""),
            "paragraphs": paragraphs,
        },
        "questions": questions,
        "core_vocabulary": vocabulary_items,
        "word_family": [],
        "answer_key_source": answer_key_items,
        "assets": [],
        "unresolved_items": unresolved,
    }

    analysis_dir = cache_root / source_id / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    canonical_path = analysis_dir / "canonical-source.json"
    _save_json(canonical_path, canonical)

    logger.info(f"Canonical source: {len(paragraphs)} paragraphs, {len(questions)} questions, "
                f"{len(vocabulary_items)} vocab items, {len(answer_key_items)} answers, "
                f"{len(unresolved)} unresolved")

    return {"status": "COMPLETE", "artifacts": [str(canonical_path)]}


# ---------------------------------------------------------------------------
# Stage handler: grounding-validate
# ---------------------------------------------------------------------------

def _handle_grounding_validate(state: dict, ctx: dict) -> dict:
    """Verify canonical source against raw extraction."""
    from validate_provenance import validate_provenance

    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    analysis_dir = cache_root / source_id / "analysis"
    canonical_path = analysis_dir / "canonical-source.json"

    if not canonical_path.exists():
        return {"status": "FAILED", "error_code": "PROVENANCE_MISSING",
                "error_message": "canonical-source.json not found"}

    result = validate_provenance(canonical_path)

    # Save grounding report
    report_path = analysis_dir / "grounding-report.json"
    _save_json(report_path, result)

    if result["status"] == "FAIL":
        critical_fails = [c for c in result.get("checks", [])
                          if c["status"] == "FAIL" and c.get("severity") == "critical"]
        if critical_fails:
            return {"status": "FAILED", "error_code": "PROVENANCE_MISSING",
                    "error_message": f"{len(critical_fails)} critical provenance failures"}

    return {"status": "COMPLETE", "artifacts": [str(report_path)]}


# ---------------------------------------------------------------------------
# Stage handler: level-assess
# ---------------------------------------------------------------------------

def _handle_level_assess(state: dict, ctx: dict) -> dict:
    """Assess CEFR level and IELTS band.

    This is a PREMIUM_LLM task. For now, uses heuristic assessment.
    Full LLM integration will be added in Phase 3.
    """
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    analysis_dir = cache_root / source_id / "analysis"
    canonical_path = analysis_dir / "canonical-source.json"

    if not canonical_path.exists():
        return {"status": "FAILED", "error_code": "LEVEL_ASSESSMENT_LOW_CONFIDENCE",
                "error_message": "canonical-source.json not found"}

    canonical = _load_json(canonical_path)

    # Extract reading passage text for assessment
    paragraphs = canonical.get("reading_passage", {}).get("paragraphs", [])
    full_text = " ".join(p.get("text", "") for p in paragraphs)

    # Heuristic assessment based on text features
    word_count = len(full_text.split())
    avg_word_length = sum(len(w) for w in full_text.split()) / max(word_count, 1)
    sentence_count = full_text.count(".") + full_text.count("?") + full_text.count("!")
    avg_sentence_length = word_count / max(sentence_count, 1)

    # Simple heuristic CEFR classification
    if avg_word_length > 6 and avg_sentence_length > 20:
        cefr = "C1"
        ielts_range = "7.0-8.0"
        confidence = 0.65
    elif avg_word_length > 5.5 and avg_sentence_length > 16:
        cefr = "B2"
        ielts_range = "5.5-6.5"
        confidence = 0.70
    elif avg_word_length > 5 and avg_sentence_length > 12:
        cefr = "B1"
        ielts_range = "4.0-5.0"
        confidence = 0.70
    else:
        cefr = "A2"
        ielts_range = "3.0-3.5"
        confidence = 0.60

    assessment = {
        "schema_version": "1.0.0",
        "cefr": cefr,
        "ielts_band_range": ielts_range,
        "confidence": confidence,
        "evidence": {
            "lexical": {
                "word_count": word_count,
                "avg_word_length": round(avg_word_length, 2),
                "assessment_method": "heuristic",
            },
            "grammar": {
                "sentence_count": sentence_count,
                "avg_sentence_length": round(avg_sentence_length, 2),
                "assessment_method": "heuristic",
            },
            "discourse": {
                "paragraph_count": len(paragraphs),
                "assessment_method": "heuristic",
            },
        },
        "notes": "Heuristic assessment — LLM-powered assessment available in Phase 3",
        "needs_human_review": confidence < 0.75,
    }

    level_path = analysis_dir / "level-assessment.json"
    _save_json(level_path, assessment)

    if confidence < 0.75 and not ctx.get("skip_human_review"):
        logger.warning(f"Level assessment confidence {confidence:.2f} < 0.75 — requesting human review")
        return {"status": "WAITING_FOR_HUMAN",
                "error_code": "LEVEL_ASSESSMENT_LOW_CONFIDENCE",
                "error_message": f"Confidence {confidence:.2f} below threshold"}

    logger.info(f"Level assessed: CEFR {cefr} / IELTS {ielts_range} (confidence: {confidence:.2f})")
    return {"status": "COMPLETE", "artifacts": [str(level_path)]}


# ---------------------------------------------------------------------------
# Stage handler: lesson-id
# ---------------------------------------------------------------------------

def _handle_lesson_id(state: dict, ctx: dict) -> dict:
    """Generate or preserve lesson ID."""
    from build_lesson_id import build_lesson_id, validate_lesson_id

    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    analysis_dir = cache_root / source_id / "analysis"

    # Get CEFR level
    level_path = analysis_dir / "level-assessment.json"
    if level_path.exists():
        level_data = _load_json(level_path)
        cefr_level = level_data.get("cefr", "B2")
    else:
        cefr_level = "B2"

    day = ctx.get("day", 1)
    existing_id = ctx.get("lesson_id") or state.get("lession_id")

    lid = build_lesson_id(day, cefr_level, existing_id)

    # Store in pipeline state
    state["lession_id"] = lid

    # Save lesson ID file
    lessons_dir = cache_root / source_id / "lessons" / lid
    lessons_dir.mkdir(parents=True, exist_ok=True)
    lid_path = lessons_dir / "lesson-id.json"
    _save_json(lid_path, {"lession_id": lid, "day": day, "cefr": cefr_level,
                          "valid": validate_lesson_id(lid)})

    logger.info(f"Lesson ID: {lid}")
    return {"status": "COMPLETE", "artifacts": [str(lid_path)]}


# ---------------------------------------------------------------------------
# Stage handler: vocabulary-build
# ---------------------------------------------------------------------------

def _handle_vocabulary_build(state: dict, ctx: dict) -> dict:
    """Build vocabulary knowledge model.

    LOW_COST_LLM task — currently uses deterministic extraction from canonical source.
    Full LLM enrichment will be added in Phase 3.
    """
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    analysis_dir = cache_root / source_id / "analysis"
    canonical_path = analysis_dir / "canonical-source.json"

    if not canonical_path.exists():
        return {"status": "FAILED", "error_code": "MODEL_OUTPUT_VALIDATION_FAILED",
                "error_message": "canonical-source.json not found"}

    canonical = _load_json(canonical_path)

    # Extract vocabulary from canonical source
    vocab_items = canonical.get("core_vocabulary", [])
    academic = []
    for item in vocab_items:
        word = item.get("word", "").strip()
        if word:
            academic.append({
                "word": word,
                "ipa": "",  # Will be enriched by LLM
                "pos": "",
                "definition": "",
                "vietnamese": "",
                "example": "",
                "content_class": "SOURCE_EXTRACTED",
                "source_refs": item.get("source_refs", []),
            })

    vocabulary = {
        "schema_version": "1.0.0",
        "academic": academic,
        "compound_words": [],
        "idioms": [],
        "collocations": [],
        "notes": "Base extraction — LLM enrichment available in Phase 3",
    }

    vocab_path = analysis_dir / "vocabulary-knowledge.json"
    _save_json(vocab_path, vocabulary)

    logger.info(f"Vocabulary: {len(academic)} academic items extracted")
    return {"status": "COMPLETE", "artifacts": [str(vocab_path)]}


# ---------------------------------------------------------------------------
# Stage handler: grammar-analyze
# ---------------------------------------------------------------------------

def _handle_grammar_analyze(state: dict, ctx: dict) -> dict:
    """Analyze grammar from reading passage.

    PREMIUM_LLM task — currently uses placeholder. Full LLM analysis in Phase 3.
    """
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    analysis_dir = cache_root / source_id / "analysis"

    grammar = {
        "schema_version": "1.0.0",
        "points": [],
        "tips": [],
        "learning_links": [],
        "notes": "Placeholder — LLM-powered grammar analysis available in Phase 3",
    }

    grammar_path = analysis_dir / "grammar-analysis.json"
    _save_json(grammar_path, grammar)

    logger.info("Grammar analysis: placeholder saved (Phase 3)")
    return {"status": "COMPLETE", "artifacts": [str(grammar_path)]}


# ---------------------------------------------------------------------------
# Stage handler: practice-compose
# ---------------------------------------------------------------------------

def _handle_practice_compose(state: dict, ctx: dict) -> dict:
    """Assemble daily practice document model (NO answers)."""
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    analysis_dir = cache_root / source_id / "analysis"
    lession_id = state.get("lession_id", "LSN-UNKNOWN")

    canonical = _load_json(analysis_dir / "canonical-source.json") if (analysis_dir / "canonical-source.json").exists() else {}
    level = _load_json(analysis_dir / "level-assessment.json") if (analysis_dir / "level-assessment.json").exists() else {}

    practice_model = {
        "type": "daily-practice",
        "lession_id": lession_id,
        "unit": canonical.get("unit", {}),
        "level": {
            "cefr": level.get("cefr", "B2"),
            "ielts_band_range": level.get("ielts_band_range", "5.5-6.5"),
        },
        "reading_passage": canonical.get("reading_passage", {}),
        "questions": canonical.get("questions", []),
        "word_family": canonical.get("word_family", []),
        "time_allowed": "60 minutes",
        # NO answers — this is student-facing
    }

    lessons_dir = cache_root / source_id / "lessons" / lession_id
    lessons_dir.mkdir(parents=True, exist_ok=True)
    practice_path = lessons_dir / "practice-document-model.json"
    _save_json(practice_path, practice_model)

    logger.info(f"Practice model composed for {lession_id}")
    return {"status": "COMPLETE", "artifacts": [str(practice_path)]}


# ---------------------------------------------------------------------------
# Stage handler: answer-build
# ---------------------------------------------------------------------------

def _handle_answer_build(state: dict, ctx: dict) -> dict:
    """Build answer key with explanations.

    PREMIUM_LLM task — currently builds from canonical source answers.
    Full LLM explanations in Phase 3.
    """
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    analysis_dir = cache_root / source_id / "analysis"
    lession_id = state.get("lession_id", "LSN-UNKNOWN")

    canonical = _load_json(analysis_dir / "canonical-source.json") if (analysis_dir / "canonical-source.json").exists() else {}

    answer_key_source = canonical.get("answer_key_source", [])
    answers = []
    for ans in answer_key_source:
        answers.append({
            "question_number": int(ans.get("question_id", "Q0")[1:]),
            "question_id": ans.get("question_id", ""),
            "answer": ans.get("answer", ""),
            "paragraph": "",
            "evidence": "",
            "reasoning": "Source-extracted answer — detailed reasoning available in Phase 3",
            "distractor_analysis": [],
            "paraphrase_matrix": [],
            "confidence": 0.80 if ans.get("source_refs") else 0.50,
            "review_status": "source-confirmed" if ans.get("source_refs") else "human-review-required",
        })

    answer_model = {
        "schema_version": "1.0.0",
        "lession_id": lession_id,
        "answers": answers,
        "word_family_answers": [],
        "notes": "Base answer extraction — LLM explanations available in Phase 3",
    }

    lessons_dir = cache_root / source_id / "lessons" / lession_id
    lessons_dir.mkdir(parents=True, exist_ok=True)
    answer_path = lessons_dir / "answer-key.json"
    _save_json(answer_path, answer_model)

    logger.info(f"Answer key: {len(answers)} answers built")
    return {"status": "COMPLETE", "artifacts": [str(answer_path)]}


# ---------------------------------------------------------------------------
# Stage handler: content-qa
# ---------------------------------------------------------------------------

def _handle_content_qa(state: dict, ctx: dict) -> dict:
    """Validate all content for completeness, consistency, and no leakage."""
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    analysis_dir = cache_root / source_id / "analysis"
    lession_id = state.get("lession_id", "LSN-UNKNOWN")
    lessons_dir = cache_root / source_id / "lessons" / lession_id

    checks = []

    # Check canonical source exists
    canonical_path = analysis_dir / "canonical-source.json"
    if canonical_path.exists():
        canonical = _load_json(canonical_path)
        checks.append({"check_id": "CQA-001", "check_name": "canonical_source_exists",
                       "status": "PASS", "severity": "info", "message": "Canonical source found"})

        # Check reading passage
        paras = canonical.get("reading_passage", {}).get("paragraphs", [])
        if paras:
            checks.append({"check_id": "CQA-002", "check_name": "reading_passage_present",
                           "status": "PASS", "severity": "info",
                           "message": f"{len(paras)} paragraphs"})
        else:
            checks.append({"check_id": "CQA-002", "check_name": "reading_passage_present",
                           "status": "FAIL", "severity": "critical",
                           "message": "No reading passage paragraphs"})

        # Check questions
        questions = canonical.get("questions", [])
        checks.append({"check_id": "CQA-003", "check_name": "questions_present",
                       "status": "PASS" if questions else "WARN", "severity": "high" if not questions else "info",
                       "message": f"{len(questions)} questions"})
    else:
        checks.append({"check_id": "CQA-001", "check_name": "canonical_source_exists",
                       "status": "FAIL", "severity": "critical",
                       "message": "canonical-source.json not found"})

    # Check practice model has no answer leakage
    practice_path = lessons_dir / "practice-document-model.json"
    if practice_path.exists():
        practice = _load_json(practice_path)
        has_answers = "answers" in practice or "answer_key" in practice
        checks.append({"check_id": "CQA-010", "check_name": "no_answer_leakage",
                       "status": "FAIL" if has_answers else "PASS",
                       "severity": "critical" if has_answers else "info",
                       "message": "Answer leakage detected!" if has_answers else "No answer leakage"})

    # Check lesson ID validity
    from build_lesson_id import validate_lesson_id
    lid_valid = validate_lesson_id(lession_id) if lession_id != "LSN-UNKNOWN" else False
    checks.append({"check_id": "CQA-020", "check_name": "lesson_id_valid",
                   "status": "PASS" if lid_valid else "WARN",
                   "severity": "medium" if not lid_valid else "info",
                   "message": f"Lesson ID: {lession_id}"})

    has_fail = any(c["status"] == "FAIL" for c in checks)
    has_warn = any(c["status"] == "WARN" for c in checks)

    report = {
        "schema_version": "1.0.0",
        "report_type": "content_qa",
        "lession_id": lession_id,
        "status": "FAIL" if has_fail else ("WARN" if has_warn else "PASS"),
        "checks": checks,
        "summary": {
            "total_checks": len(checks),
            "passed": sum(1 for c in checks if c["status"] == "PASS"),
            "failed": sum(1 for c in checks if c["status"] == "FAIL"),
            "warnings": sum(1 for c in checks if c["status"] == "WARN"),
        },
    }

    qa_dir = cache_root / source_id / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    report_path = qa_dir / "content-qa-report.json"
    _save_json(report_path, report)

    if has_fail:
        return {"status": "FAILED", "error_code": "CONTENT_QA_FAILED",
                "error_message": f"Content QA failed: {report['summary']['failed']} check(s)"}

    logger.info(f"Content QA: {report['summary']['passed']} passed, "
                f"{report['summary']['warnings']} warnings")
    return {"status": "COMPLETE", "artifacts": [str(report_path)]}


# ---------------------------------------------------------------------------
# Stage handler: document-model
# ---------------------------------------------------------------------------

def _handle_document_model(state: dict, ctx: dict) -> dict:
    """Build render-ready document model from all content artifacts."""
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    analysis_dir = cache_root / source_id / "analysis"
    lession_id = state.get("lession_id", "LSN-UNKNOWN")
    lessons_dir = cache_root / source_id / "lessons" / lession_id
    render_dir = cache_root / source_id / "render"
    render_dir.mkdir(parents=True, exist_ok=True)

    # Load all content artifacts
    canonical = _load_json(analysis_dir / "canonical-source.json") if (analysis_dir / "canonical-source.json").exists() else {}
    level = _load_json(analysis_dir / "level-assessment.json") if (analysis_dir / "level-assessment.json").exists() else {}
    vocabulary = _load_json(analysis_dir / "vocabulary-knowledge.json") if (analysis_dir / "vocabulary-knowledge.json").exists() else {}
    grammar = _load_json(analysis_dir / "grammar-analysis.json") if (analysis_dir / "grammar-analysis.json").exists() else {}
    answers = _load_json(lessons_dir / "answer-key.json") if (lessons_dir / "answer-key.json").exists() else {}

    # Build unified document model
    doc_model = {
        "schema_version": "1.0.0",
        "lession_id": lession_id,
        "center_name": "IELTS Learning Center",
        "unit": canonical.get("unit", {}),
        "level": {
            "cefr": level.get("cefr", "B2"),
            "ielts_band_range": level.get("ielts_band_range", "5.5-6.5"),
        },
        "reading_passage": canonical.get("reading_passage", {}),
        "questions": canonical.get("questions", []),
        "word_family": canonical.get("word_family", []),
        "vocabulary": vocabulary,
        "grammar": grammar,
        "answers": answers.get("answers", []),
        "word_family_answers": answers.get("word_family_answers", []),
        "assets": canonical.get("assets", []),
        "time_allowed": "60 minutes",
        "learning_links": grammar.get("learning_links", []),
    }

    model_path = render_dir / "document-model.json"
    _save_json(model_path, doc_model)

    logger.info(f"Document model built for {lession_id}")
    return {"status": "COMPLETE", "artifacts": [str(model_path)]}


# ---------------------------------------------------------------------------
# Stage handler: html-render
# ---------------------------------------------------------------------------

def _handle_html_render(state: dict, ctx: dict) -> dict:
    """Render HTML from document model using Jinja2."""
    from render_html import render_all_documents

    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    render_dir = cache_root / source_id / "render"
    lession_id = state.get("lession_id", "LSN-UNKNOWN")

    model_path = render_dir / "document-model.json"
    if not model_path.exists():
        return {"status": "FAILED", "error_code": "HTML_VALIDATION_FAILED",
                "error_message": "document-model.json not found"}

    doc_model = _load_json(model_path)
    html_dir = render_dir / "html"

    result = render_all_documents(doc_model, html_dir, lession_id)
    return result


# ---------------------------------------------------------------------------
# Stage handler: pdf-render
# ---------------------------------------------------------------------------

def _handle_pdf_render(state: dict, ctx: dict) -> dict:
    """Render PDFs from HTML using Playwright."""
    from render_pdf import render_all_pdfs

    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")
    render_dir = cache_root / source_id / "render"
    lession_id = state.get("lession_id", "LSN-UNKNOWN")
    output_root = Path(ctx.get("output_root", DEFAULT_OUTPUT_ROOT))

    html_dir = render_dir / "html"
    pdf_dir = output_root / lession_id

    result = render_all_pdfs(html_dir, pdf_dir, lession_id)

    if result["status"] == "COMPLETE":
        # Also create lesson manifest
        manifest = {
            "schema_version": "1.0.0",
            "lession_id": lession_id,
            "skill_version": SKILL_VERSION,
            "generated_at": _now_iso(),
            "outputs": result.get("artifacts", []),
            "output_directory": str(pdf_dir),
        }
        manifest_path = pdf_dir / "lesson-manifest.json"
        _save_json(manifest_path, manifest)
        result["artifacts"].append(str(manifest_path))

    return result


# ---------------------------------------------------------------------------
# Stage handler: pdf-visual-qa
# ---------------------------------------------------------------------------

def _handle_pdf_visual_qa(state: dict, ctx: dict) -> dict:
    """Inspect rendered PDFs for A4, footer, overflow."""
    from inspect_rendered_pdf import inspect_rendered_pdf

    lession_id = state.get("lession_id", "LSN-UNKNOWN")
    output_root = Path(ctx.get("output_root", DEFAULT_OUTPUT_ROOT))
    pdf_dir = output_root / lession_id
    cache_root = Path(ctx.get("cache_root", DEFAULT_CACHE_ROOT))
    source_id = state.get("unique_source_id", "unknown")

    all_checks = []
    pdf_files = ["daily-practice.pdf", "vocabulary-grammar.pdf", "answer-key.pdf"]

    for pdf_name in pdf_files:
        pdf_path = pdf_dir / pdf_name
        if pdf_path.exists():
            result = inspect_rendered_pdf(pdf_path, lession_id)
            all_checks.extend(result.get("checks", []))
        else:
            all_checks.append({
                "check_id": f"VQA-MISS-{pdf_name}",
                "check_name": "pdf_file_exists",
                "status": "FAIL",
                "severity": "critical",
                "message": f"PDF not found: {pdf_name}",
            })

    has_fail = any(c["status"] == "FAIL" for c in all_checks)

    report = {
        "schema_version": "1.0.0",
        "report_type": "visual_pdf_qa",
        "lession_id": lession_id,
        "status": "FAIL" if has_fail else "PASS",
        "checks": all_checks,
        "summary": {
            "total_checks": len(all_checks),
            "passed": sum(1 for c in all_checks if c["status"] == "PASS"),
            "failed": sum(1 for c in all_checks if c["status"] == "FAIL"),
            "warnings": sum(1 for c in all_checks if c["status"] == "WARN"),
        },
    }

    qa_dir = cache_root / source_id / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    report_path = qa_dir / "visual-qa-report.json"
    _save_json(report_path, report)

    if has_fail and not ctx.get("skip_human_review"):
        return {"status": "FAILED", "error_code": "PDF_PAGE_OVERFLOW",
                "error_message": f"Visual QA failed: {report['summary']['failed']} check(s)"}

    logger.info(f"Visual QA: {report['summary']['passed']} passed, "
                f"{report['summary']['failed']} failed, "
                f"{report['summary']['warnings']} warnings")
    return {"status": "COMPLETE", "artifacts": [str(report_path)]}


# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------

STAGE_HANDLERS = {
    "request-intake": _handle_request_intake,
    "execution-routing": _handle_execution_routing,
    "cache-resolve": _handle_cache_resolve,
    "source-acquire": _handle_source_acquire,
    "pdf-structure": _handle_pdf_structure,
    "text-extract": _handle_text_extract,
    "unit-locate": _handle_unit_locate,
    "source-canonicalize": _handle_source_canonicalize,
    "grounding-validate": _handle_grounding_validate,
    "level-assess": _handle_level_assess,
    "lesson-id": _handle_lesson_id,
    "vocabulary-build": _handle_vocabulary_build,
    "grammar-analyze": _handle_grammar_analyze,
    "practice-compose": _handle_practice_compose,
    "answer-build": _handle_answer_build,
    "content-qa": _handle_content_qa,
    "document-model": _handle_document_model,
    "html-render": _handle_html_render,
    "pdf-render": _handle_pdf_render,
    "pdf-visual-qa": _handle_pdf_visual_qa,
}


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_pipeline(args: argparse.Namespace) -> int:
    """Execute the pipeline according to CLI arguments."""

    output_root = Path(args.output_root) if args.output_root else DEFAULT_OUTPUT_ROOT
    cache_root = Path(args.cache_root) if args.cache_root else DEFAULT_CACHE_ROOT

    # Determine unique_source_id
    if args.source and Path(args.source).is_file():
        unique_source_id = _compute_file_hash(Path(args.source))
    elif args.lesson_id:
        # Try to find from existing state
        unique_source_id = f"lesson-{args.lesson_id}"
    else:
        unique_source_id = f"url-{hashlib.sha256(str(args.source or '').encode()).hexdigest()[:16]}"

    # State directory
    state_dir = cache_root / unique_source_id / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "pipeline-state.json"

    # Load or init state
    state = _load_or_init_state(state_path, unique_source_id)

    # Build context from args
    ctx = {
        "source": args.source,
        "unit": args.unit,
        "topic": args.topic,
        "day": args.day,
        "human_review": args.human_review,
        "force_reextract": args.force_reextract,
        "force_rebuild_content": args.force_rebuild_content,
        "force_rerender": args.force_rerender,
        "skip_human_review": args.skip_human_review,
        "resume": args.resume,
        "from_stage": args.from_stage,
        "to_stage": args.to_stage,
        "lesson_id": args.lesson_id,
        "output_root": str(output_root),
        "cache_root": str(cache_root),
        "page": args.page,
        "force_page_reextract": args.force_page_reextract,
    }

    # Determine stage range
    start_idx = 0
    end_idx = len(STAGE_ORDER) - 1

    if args.from_stage:
        if args.from_stage in STAGE_ORDER:
            start_idx = STAGE_ORDER.index(args.from_stage)
        else:
            logger.error(f"Unknown stage: {args.from_stage}")
            return 1

    if args.to_stage:
        if args.to_stage in STAGE_ORDER:
            end_idx = STAGE_ORDER.index(args.to_stage)
        else:
            logger.error(f"Unknown stage: {args.to_stage}")
            return 1

    if args.resume:
        # Find last completed stage and continue from next
        for i, name in enumerate(STAGE_ORDER):
            st = state["stages"].get(name, {})
            if st.get("status") in ("COMPLETE", "SKIPPED_FROM_CACHE"):
                start_idx = i + 1
        logger.info(f"Resuming from stage index {start_idx}")

    # Force flags
    if args.force_rerender:
        # Only rerun render stages
        render_start = STAGE_ORDER.index("html-render")
        start_idx = max(start_idx, render_start)
        ctx["force"] = True

    if args.force_reextract:
        ctx["force"] = True

    # Run stages
    state["overall_status"] = "RUNNING"
    _save_json(state_path, state)

    for i in range(start_idx, end_idx + 1):
        stage_name = STAGE_ORDER[i]
        state["current_stage"] = stage_name
        _save_json(state_path, state)

        success = _run_stage(stage_name, state, ctx)
        _save_json(state_path, state)

        if not success:
            stage_status = state["stages"][stage_name]["status"]
            if stage_status == "WAITING_FOR_HUMAN":
                state["overall_status"] = "WAITING_FOR_HUMAN"
                logger.info(f"Pipeline paused at stage '{stage_name}' — human review required")
            else:
                state["overall_status"] = "FAILED"
                logger.error(f"Pipeline failed at stage '{stage_name}'")
            _save_json(state_path, state)
            return 1 if stage_status != "WAITING_FOR_HUMAN" else 0

    state["overall_status"] = "COMPLETE"
    state["current_stage"] = None
    _save_json(state_path, state)
    logger.info("Pipeline completed successfully")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_pipeline",
        description="IELTS Barron Essential Vocab — Modular Pipeline Orchestrator",
    )
    p.add_argument("--source", type=str, help="PDF path or Google Drive URL")
    p.add_argument("--unit", type=str, help="Target unit name/number")
    p.add_argument("--topic", type=str, help="Target topic name")
    p.add_argument("--day", type=int, default=1, help="Day number (default: 1)")
    p.add_argument("--human-review", action="store_true", default=True, help="Enable HITL checkpoints")
    p.add_argument("--resume", action="store_true", help="Resume from last completed stage")
    p.add_argument("--from-stage", type=str, help="Start from a specific stage")
    p.add_argument("--to-stage", type=str, help="Stop after a specific stage")
    p.add_argument("--force-reextract", action="store_true", help="Force re-extraction")
    p.add_argument("--force-rebuild-content", action="store_true", help="Force content rebuild")
    p.add_argument("--force-rerender", action="store_true", help="Force re-render only")
    p.add_argument("--skip-human-review", action="store_true", help="Skip all HITL checkpoints")
    p.add_argument("--lesson-id", type=str, help="Existing lesson ID for reruns")
    p.add_argument("--output-root", type=str, help="Custom output directory")
    p.add_argument("--cache-root", type=str, help="Custom cache directory")
    p.add_argument("--page", type=int, help="Target specific page (for re-OCR)")
    p.add_argument("--force-page-reextract", action="store_true", help="Force re-extract specific page")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.source and not args.lesson_id and not args.resume:
        parser.error("Either --source, --lesson-id, or --resume is required")

    return run_pipeline(args)


if __name__ == "__main__":
    sys.exit(main())
