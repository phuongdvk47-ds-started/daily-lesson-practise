#!/usr/bin/env python3
import copy
import json
import tempfile
import unittest
from pathlib import Path
import sys

scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.append(str(scripts_dir))

from export_daily_pack import build_answers_html, build_practice_html, convert_json_to_markdown_fields
from validate_lesson_json import validate_lesson_json


def _reading_question(q_id, q_type, question, answer, paragraph_id, quote, skill):
    item = {
        "id": q_id,
        "type": q_type,
        "question": question,
        "correct_answer": answer,
        "evidence_paragraph": paragraph_id,
        "evidence_quote": quote,
        "rationale_vi": "Reasoning is based on the printed passage.",
        "reasoning_skill": skill,
        "source_scope": "printed_passage_only",
        "stretch": False,
        "keyword_overlap_check": "The item uses paraphrase instead of direct copying.",
        "distractor_analysis": [],
    }
    if skill != "literal":
        item["paraphrase_mapping"] = "passage wording -> question wording"
    if q_type == "Paragraph Information Matching":
        item["evidence_paragraph_label"] = answer
    return item


def _reading_answer(q):
    return {
        "question_id": q["id"],
        "correct_answer": q["correct_answer"],
        "question_type": q["type"],
        "evidence_quote": q["evidence_quote"],
        "evidence_paragraph": q["evidence_paragraph"],
        "explanation_vi": "Giai thich dua tren bang chung trong doan van.",
        "why_others_wrong_vi": "Cac lua chon khac khong khop y cua doan van.",
        "depth_check_vi": "Cau hoi yeu cau hieu y, khong chi tim tu khoa.",
        "tip_vi": "Doc y chinh truoc khi chon dap an.",
        "stretch_note": "",
    }


def _vocab_item(idx, term, vocab_type):
    return {
        "id": idx,
        "term": term,
        "ipa": f"/{term.replace(' ', '-')}/",
        "part_of_speech": "noun",
        "definition_en": f"a lesson definition for {term}",
        "meaning_vi": f"nghia cua {term}",
        "example": f"The passage mentions {term}.",
        "vocab_type": vocab_type,
        "source": "reading",
    }


def get_barron_payload():
    paragraphs = [
        {"id": 1, "label": "A", "text": "Logging removes tall trees from forest slopes and opens gaps in the canopy."},
        {"id": 2, "label": "B", "text": "Heavy machines press the soil down, so rainwater cannot move through it easily."},
        {"id": 3, "label": "C", "text": "When habitats disappear, birds and insects lose food, shelter, and nesting places."},
        {"id": 4, "label": "D", "text": "Some communities plant young trees and protect stream edges after timber work."},
        {"id": 5, "label": "E", "text": "Careful rules can limit erosion, but weak enforcement often leaves rivers muddy."},
        {"id": 6, "label": "F", "text": "Scientists track biodiversity to understand how quickly a forest can recover."},
    ]

    questions = [
        _reading_question(1, "Paragraph Information Matching", "A paragraph about compacted ground", "B", 2, "Heavy machines press the soil down", "structure_function"),
        _reading_question(2, "Paragraph Information Matching", "A paragraph about animal homes", "C", 3, "birds and insects lose food, shelter, and nesting places", "main_idea"),
        _reading_question(3, "Paragraph Information Matching", "A paragraph about repairs after timber work", "D", 4, "plant young trees and protect stream edges", "cause_effect"),
        _reading_question(4, "Paragraph Information Matching", "A paragraph about measuring recovery", "F", 6, "Scientists track biodiversity", "inference"),
        _reading_question(5, "Summary Completion", "Blank 5", "canopy", 1, "opens gaps in the canopy", "vocabulary_in_context"),
        _reading_question(6, "Summary Completion", "Blank 6", "soil", 2, "press the soil down", "paraphrase"),
        _reading_question(7, "Summary Completion", "Blank 7", "habitats", 3, "When habitats disappear", "reference"),
        _reading_question(8, "Summary Completion", "Blank 8", "biodiversity", 6, "Scientists track biodiversity", "synthesis"),
    ]

    vocab_types = (
        ["single_word"] * 10
        + ["topic_vocabulary"] * 4
        + ["phrase", "collocation", "collocation", "single_word", "topic_vocabulary", "single_word"]
    )
    terms = [
        "logging", "forest", "slope", "canopy", "machine", "soil", "rainwater", "habitat", "bird", "insect",
        "stream edge", "timber work", "young tree", "muddy river", "protect stream edges", "heavy machines",
        "plant young trees", "erosion", "biodiversity", "recover",
    ]
    vocab_items = [_vocab_item(idx + 1, term, vocab_types[idx]) for idx, term in enumerate(terms)]

    return {
        "execution": {
            "mode": "auto",
            "pipeline_status": "qc_passed",
            "current_stage": "validation",
            "revision_attempts": {
                "source": 0,
                "reading": 0,
                "vocabulary": 0,
                "grammar": 0,
                "writing": 0,
                "answers": 0,
                "pdf_layout": 0,
            },
        },
        "human_review": {"mode": "auto", "checkpoints": []},
        "agent_review": {"reviews": [], "challenges": []},
        "lesson_meta": {
            "lesson_id": "LSN-20260706-A2-BARRON-STYLE",
            "day": "20260706",
            "level": "A2",
            "theme": "The Natural World",
            "topic": "Environmental Impacts of Logging",
            "specific_topic": "Environmental Impacts of Logging",
            "created_at": "2026-07-06T00:00:00Z",
            "reading_question_count": 8,
            "vocabulary_count": 20,
            "grammar_question_count": 0,
            "writing_task_count": 0,
            "practice_profile": "barron_style",
        },
        "source": {
            "status": "verified",
            "source_title": "Environmental Impacts of Logging",
            "publisher": "Lesson Source",
            "verified_url": "https://example.com/logging",
        },
        "reading": {
            "reading_blueprint": [
                {
                    "question_no": idx,
                    "type": "main_idea" if idx <= 4 else "summary_completion",
                    "depth": "medium",
                    "target_skill": "understand paragraph information",
                    "evidence_strategy": "paragraph-level" if idx <= 4 else "single sentence",
                    "distractor_strategy": "near-topic but unsupported",
                }
                for idx in range(1, 9)
            ],
            "passage": {"title": "Environmental Impacts of Logging", "paragraphs": paragraphs},
            "summary_completion": {
                "instruction": "Complete the summary using words from the list below.",
                "summary_text": "Logging opens gaps in the {5}. Machines damage the {6}. Animals suffer when {7} disappear, so scientists measure {8}.",
                "word_bank": ["canopy", "soil", "habitats", "biodiversity", "profit", "roads", "fuel"],
            },
            "questions": questions,
        },
        "vocabulary": {
            "items": vocab_items,
            "recycled_items": [
                {"term": "river", "ipa": "/river/", "part_of_speech": "noun", "meaning_vi": "song", "source_day": "20260705"},
                {"term": "animal", "ipa": "/animal/", "part_of_speech": "noun", "meaning_vi": "dong vat", "source_day": "20260705"},
                {"term": "plant", "ipa": "/plant/", "part_of_speech": "verb", "meaning_vi": "trong cay", "source_day": "20260705"},
            ],
            "quizlet": {
                "section_1_simple": [f"{item['term']} : {item['meaning_vi']}" for item in vocab_items],
                "section_2_detailed": [f"{item['term']} ({item['ipa']}) [{item['part_of_speech']}] : {item['meaning_vi']} *e.g., {item['example']}*" for item in vocab_items],
            },
            "vocab_checker_items": [
                {
                    "term": item["term"],
                    "ipa": item["ipa"],
                    "part_of_speech": item["part_of_speech"],
                    "definition_en": item["definition_en"],
                    "meaning_vi": item["meaning_vi"],
                }
                for item in vocab_items
            ],
            "matching_test": {
                "instruction": "Look for the following words as you read the passage. Match each word with its correct definition.",
                "items": [
                    {"id": 1, "term": "logging", "correct_definition_label": "C"},
                    {"id": 2, "term": "canopy", "correct_definition_label": "A"},
                    {"id": 3, "term": "soil", "correct_definition_label": "D"},
                    {"id": 4, "term": "habitats", "correct_definition_label": "B"},
                    {"id": 5, "term": "erosion", "correct_definition_label": "F"},
                    {"id": 6, "term": "biodiversity", "correct_definition_label": "E"},
                ],
                "definitions": [
                    {"label": "A", "part_of_speech": "noun", "definition": "the leaves and branches at the top of trees"},
                    {"label": "B", "part_of_speech": "noun", "definition": "places where plants or animals live"},
                    {"label": "C", "part_of_speech": "noun", "definition": "cutting down trees for wood"},
                    {"label": "D", "part_of_speech": "noun", "definition": "the top layer of earth where plants grow"},
                    {"label": "E", "part_of_speech": "noun", "definition": "the variety of living things in an area"},
                    {"label": "F", "part_of_speech": "noun", "definition": "the process of soil being carried away"},
                ],
            },
            "word_families": [
                {
                    "family": "destroy",
                    "members": [
                        {"word": "destroy", "part_of_speech": "verb", "example": "Machines can destroy small habitats."},
                        {"word": "destructive", "part_of_speech": "adjective", "example": "Destructive logging harms streams."},
                        {"word": "destruction", "part_of_speech": "noun", "example": "Habitat destruction reduces biodiversity."},
                    ],
                },
                {
                    "family": "recover",
                    "members": [
                        {"word": "recover", "part_of_speech": "verb", "example": "A forest can recover slowly."},
                        {"word": "recovery", "part_of_speech": "noun", "example": "Recovery takes many years."},
                    ],
                },
            ],
            "word_family_practice": {
                "instruction": "Choose the correct word family member to complete each blank.",
                "practice_text": "Careless logging can cause habitat {1}. Some methods are very {2}. With protection, a forest can begin its {3}.",
                "items": [
                    {"id": 1, "family": "destroy", "options": ["destroy", "destructive", "destruction"], "correct_answer": "destruction", "explanation_vi": "Can danh tu sau habitat."},
                    {"id": 2, "family": "destroy", "options": ["destroy", "destructive", "destruction"], "correct_answer": "destructive", "explanation_vi": "Can tinh tu sau very."},
                    {"id": 3, "family": "recover", "options": ["recover", "recovery", "recoverable"], "correct_answer": "recovery", "explanation_vi": "Can danh tu sau its."},
                ],
            },
        },
        "grammar": {
            "grammar_blueprint": [],
            "targets": [],
            "guide": [],
            "common_mistakes": [],
            "sections": [],
            "questions": [],
        },
        "writing": {"tasks": []},
        "answers": {
            "vocabulary_matching_answers": [
                {"item_id": 1, "term": "logging", "correct_definition_label": "C", "explanation_vi": "Logging means cutting down trees for wood."},
                {"item_id": 2, "term": "canopy", "correct_definition_label": "A", "explanation_vi": "Canopy is the top layer of branches."},
                {"item_id": 3, "term": "soil", "correct_definition_label": "D", "explanation_vi": "Soil is the top layer of earth."},
                {"item_id": 4, "term": "habitats", "correct_definition_label": "B", "explanation_vi": "Habitats are living places."},
                {"item_id": 5, "term": "erosion", "correct_definition_label": "F", "explanation_vi": "Erosion carries soil away."},
                {"item_id": 6, "term": "biodiversity", "correct_definition_label": "E", "explanation_vi": "Biodiversity means variety of life."},
            ],
            "reading_answers": [_reading_answer(q) for q in questions],
            "grammar_answers": [],
            "word_family_answers": [
                {"item_id": 1, "family": "destroy", "correct_answer": "destruction", "explanation_vi": "A noun fits after habitat."},
                {"item_id": 2, "family": "destroy", "correct_answer": "destructive", "explanation_vi": "An adjective fits after very."},
                {"item_id": 3, "family": "recover", "correct_answer": "recovery", "explanation_vi": "A noun fits after its."},
            ],
            "writing_guidance": [],
            "review_bridge": [
                {"id": 1, "prompt": "Translate: plant young trees.", "correct_answer": "trong cay non", "rationale_vi": "Review vocabulary."},
                {"id": 2, "prompt": "Complete: muddy ____.", "correct_answer": "river", "rationale_vi": "Review vocabulary."},
                {"id": 3, "prompt": "Translate: animal habitat.", "correct_answer": "moi truong song cua dong vat", "rationale_vi": "Review vocabulary."},
            ],
        },
        "warm_up": [
            "What can happen when many trees are cut down?",
            "Which animals near your home need trees or plants?",
            "How can people use wood without damaging forests too much?",
        ],
    }


def run_validation(payload):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as handle:
        json.dump(payload, handle)
        temp_path = Path(handle.name)
    try:
        return validate_lesson_json(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


class TestBarronStyleSections(unittest.TestCase):
    def test_barron_style_payload_validates(self):
        self.assertTrue(run_validation(get_barron_payload()))

    def test_barron_style_markdown_and_practice_html_render_sections(self):
        converted = convert_json_to_markdown_fields(copy.deepcopy(get_barron_payload()))

        practice_md = converted["practice_markdown"]
        self.assertIn("## Vocabulary Matching Test", practice_md)
        self.assertIn("**A** Logging removes tall trees", practice_md)
        self.assertIn("## Word Family Practice", practice_md)
        self.assertIn("Word bank: canopy | soil | habitats | biodiversity", practice_md)

        html = build_practice_html(practice_md, "A2", "Environmental Impacts of Logging", "20260706")
        self.assertIn("Vocabulary Matching Test", html)
        self.assertIn('<span class="paragraph-label">A</span>', html)
        self.assertIn("Word bank:", html)
        self.assertIn("Word Family Practice", html)
        self.assertIn("destruction", html)

    def test_barron_style_answers_render_sections(self):
        converted = convert_json_to_markdown_fields(copy.deepcopy(get_barron_payload()))
        html = build_answers_html(
            converted["answers_markdown"],
            "20260706",
            "Environmental Impacts of Logging",
            converted["practice_markdown"],
        )
        self.assertIn("Vocabulary Matching Answers", html)
        self.assertIn("Word Family Practice Answers", html)
        self.assertIn("destruction", html)

    def test_invalid_vocabulary_matching_answer_fails(self):
        payload = get_barron_payload()
        payload["answers"]["vocabulary_matching_answers"][0]["correct_definition_label"] = "A"
        self.assertFalse(run_validation(payload))


if __name__ == "__main__":
    unittest.main()
