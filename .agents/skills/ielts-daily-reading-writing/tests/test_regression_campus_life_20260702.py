#!/usr/bin/env python3
import json
import unittest
from pathlib import Path
import sys

# Add scripts directory to path to import validator
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.append(str(scripts_dir))

from validate_lesson_json import validate_lesson_json

class TestRegressionCampusLife20260702(unittest.TestCase):
    
    def setUp(self):
        self.tmp_json_path = Path("tmp_regression_campus_life.json")
        self.base_data = {
            "execution": {
                "mode": "auto",
                "pipeline_status": "qc_passed",
                "current_stage": "validation",
                "revision_attempts": {
                    "source": 0, "reading": 0, "vocabulary": 0, "grammar": 0, "writing": 0, "answers": 0, "pdf_layout": 0
                }
            },
            "human_review": {
                "mode": "auto",
                "checkpoints": []
            },
            "agent_review": {
                "reviews": [],
                "challenges": []
            },
            "lesson_meta": {
                "lesson_id": "LSN-20260702-B1-CAMPUS-LIFE-A1B2C3D4",
                "day": "20260702",
                "level": "B1",
                "theme": "Education",
                "topic": "Campus Life",
                "specific_topic": "Residence Life",
                "reading_question_count": 1,
                "vocabulary_count": 5,
                "grammar_question_count": 1,
                "writing_task_count": 1,
                "printed_time_allowed_minutes": 21,
                "estimated_completion_time_minutes": 21,
                "time_workload_status": "ok"
            },
            "source": {
                "status": "verified",
                "source_title": "Source",
                "publisher": "VOA",
                "verified_url": "https://example.com/residence"
            },
            "reading": {
                "passage": {
                    "title": "Passage Title",
                    "paragraphs": [
                        { "id": 1, "text": "This has target word innovation." }
                    ]
                },
                "questions": [
                    {
                        "id": 1,
                        "type": "Multiple Choice",
                        "question": "What?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A",
                        "evidence_paragraph": 1,
                        "evidence_quote": "target word innovation",
                        "rationale_vi": "Giải thích",
                        "reasoning_skill": "paraphrase",
                        "source_scope": "printed_passage_only",
                        "stretch": False
                    }
                ]
            },
            "vocabulary": {
                "items": [
                    { "id": 1, "term": "innovation", "ipa": "/ˌɪnəˈveɪʃn/", "part_of_speech": "n", "definition_en": "new", "meaning_vi": "mới", "example": "innovation", "vocab_type": "topic_vocabulary", "source": "reading" },
                    { "id": 2, "term": "traditional distribution models", "ipa": "/tr/", "part_of_speech": "phrase", "definition_en": "old", "meaning_vi": "cũ", "example": "models", "vocab_type": "collocation", "source": "reading" },
                    { "id": 3, "term": "cinema attendance", "ipa": "/cin/", "part_of_speech": "n", "definition_en": "attendance", "meaning_vi": "tham dự", "example": "attendance", "vocab_type": "collocation", "source": "reading" },
                    { "id": 4, "term": "digital streaming platforms", "ipa": "/plat/", "part_of_speech": "phrase", "definition_en": "platforms", "meaning_vi": "nền tảng", "example": "platforms", "vocab_type": "phrase", "source": "reading" },
                    { "id": 5, "term": "reach global audiences", "ipa": "/reach/", "part_of_speech": "phrase", "definition_en": "reach", "meaning_vi": "tiếp cận", "example": "reach", "vocab_type": "academic_vocabulary", "source": "reading" }
                ],
                "recycled_items": [],
                "quizlet": {
                    "section_1_simple": ["innovation : mới"],
                    "section_2_detailed": ["innovation : new"]
                },
                "vocab_checker_items": [
                    { "term": "innovation", "ipa": "/ˌɪn/", "part_of_speech": "n", "definition_en": "new", "meaning_vi": "mới" }
                ]
            },
            "grammar": {
                "guide": [
                    { "heading": "#### Chủ điểm 1: Relative clauses", "content": "Explanation" }
                ],
                "common_mistakes": [
                    { "trap": "Trap", "wrong_example": "who...", "correct_version": "which...", "why_it_matters": "IELTS" }
                ],
                "sections": [
                    { "section_title": "Relative Pronouns", "internal_question_start": 1, "internal_question_end": 1, "compiler_computed_range": True }
                ],
                "questions": []
            },
            "writing": {
                "tasks": [
                    {
                        "id": 1,
                        "task_type": "Data Description",
                        "prompt": "Compare.",
                        "target_length": "3 sentences",
                        "focus_skill": "Comparison",
                        "useful_language": ["more"],
                        "success_criteria": ["Compare"],
                        "visual_data": {
                            "type": "svg",
                            "content": "<svg><text>Media Chart</text><text>y</text><text>x</text><text>unit</text><text>cat</text></svg>"
                        },
                        "topic_alignment": True
                    }
                ]
            },
            "answers": {
                "reading_answers": [
                    { "question_id": 1, "correct_answer": "A", "evidence_quote": "target word innovation", "evidence_paragraph": 1, "explanation_vi": "Giải thích", "why_others_wrong_vi": "Sai", "tip_vi": "Mẹo" }
                ],
                "grammar_answers": [
                    { "question_id": 1, "correct_answer": "which", "analysis_vi": "Giải thích", "tip_vi": "Mẹo" }
                ],
                "writing_guidance": [
                    { "task_id": 1, "model_answer": "Model", "guidance_vi": "Hướng dẫn", "self_checklist": ["Check"] }
                ],
                "review_bridge": [
                    { "id": 1, "prompt": "B1", "correct_answer": "A", "rationale_vi": "G" },
                    { "id": 2, "prompt": "B2", "correct_answer": "A", "rationale_vi": "G" },
                    { "id": 3, "prompt": "B3", "correct_answer": "A", "rationale_vi": "G" }
                ]
            },
            "warm_up": ["Q1", "Q2", "Q3"]
        }

    def tearDown(self):
        if self.tmp_json_path.exists():
            self.tmp_json_path.unlink()

    def write_json(self, data):
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_rejects_ambiguous_commas_question_without_context(self):
        # 1. "The student, who lives next door..." vs "The student who lives next door..."
        data = dict(self.base_data)
        data["grammar"]["questions"] = [
            {
                "id": 1,
                "type": "Multiple Choice",
                "question": "Identify the sentence that uses relative clause commas correctly.",
                "options": [
                    "The student, who lives next door, is very loud.",
                    "The student who lives next door is very loud.",
                    "The student who lives, next door, is very loud."
                ],
                "correct_answer": "The student who lives next door is very loud.",
                "explanation_vi": "giải thích",
                "stretch": False,
                "logic_validation": {
                    "has_exactly_one_valid_answer": True,
                    "context_is_sufficient": True,
                    "punctuation_complete": True,
                    "meaning_preserved": True
                }
            }
        ]
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_rejects_missing_closing_comma_for_ksu_stands(self):
        # 2. "Kansas State University ______ stands..."
        data = dict(self.base_data)
        data["grammar"]["questions"] = [
            {
                "id": 1,
                "type": "Multiple Choice",
                "question": "Kansas State University _______ stands in the state of Kansas has a great campus.",
                "options": ["which", ", which", ", who"],
                "correct_answer": ", which",
                "explanation_vi": "giải thích",
                "stretch": False,
                "logic_validation": {
                    "has_exactly_one_valid_answer": True,
                    "context_is_sufficient": True,
                    "punctuation_complete": True,
                    "meaning_preserved": True
                }
            }
        ]
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_rejects_resident_assistants_missing_context(self):
        # 3. "Resident Assistants ______ must follow..."
        data = dict(self.base_data)
        data["grammar"]["questions"] = [
            {
                "id": 1,
                "type": "Multiple Choice",
                "question": "Resident Assistants _______ must follow university rules.",
                "options": [", who guide new students,", "who guide new students", ", which guide new students,"],
                "correct_answer": ", who guide new students,",
                "explanation_vi": "giải thích",
                "stretch": False,
                "logic_validation": {
                    "has_exactly_one_valid_answer": True,
                    "context_is_sufficient": True,
                    "punctuation_complete": True,
                    "meaning_preserved": True
                }
            }
        ]
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_rejects_main_office_missing_closing_comma(self):
        # 4. "The main office ______ is located..."
        data = dict(self.base_data)
        data["grammar"]["questions"] = [
            {
                "id": 1,
                "type": "Multiple Choice",
                "question": "The main office _______ is located on the first floor is always busy.",
                "options": ["which", ", which", ", who"],
                "correct_answer": ", which",
                "explanation_vi": "giải thích",
                "stretch": False,
                "logic_validation": {
                    "has_exactly_one_valid_answer": True,
                    "context_is_sufficient": True,
                    "punctuation_complete": True,
                    "meaning_preserved": True
                }
            }
        ]
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

if __name__ == "__main__":
    unittest.main()
