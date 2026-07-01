#!/usr/bin/env python3
import json
import unittest
from pathlib import Path
import sys

# Add scripts directory to path to import validator
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.append(str(scripts_dir))

from validate_lesson_json import validate_lesson_json

class TestCorrectTheErrorLogic(unittest.TestCase):
    
    def setUp(self):
        self.tmp_json_path = Path("tmp_test_correct_error_lesson_source.json")
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
                "lesson_id": "LSN-20260702-A2-SCHOOL-LIFE-R9T2W1",
                "day": "20260702",
                "level": "A2",
                "theme": "School Life",
                "topic": "School Life",
                "specific_topic": "Year-Round Schooling",
                "reading_question_count": 1,
                "vocabulary_count": 19,
                "grammar_question_count": 1,
                "writing_task_count": 1,
                "printed_time_allowed_minutes": 22,
                "estimated_completion_time_minutes": 22,
                "time_workload_status": "ok"
            },
            "source": {
                "status": "verified",
                "source_title": "School life article",
                "publisher": "VOA",
                "verified_url": "https://example.com/school"
            },
            "reading": {
                "passage": {
                    "title": "Passage Title",
                    "paragraphs": [
                        { "id": 1, "text": "This is school life target words." }
                    ]
                },
                "questions": [
                    {
                        "id": 1,
                        "type": "Multiple Choice",
                        "question": "What is school life?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A",
                        "evidence_paragraph": 1,
                        "evidence_quote": "school life target words",
                        "rationale_vi": "Giải thích",
                        "reasoning_skill": "literal",
                        "source_scope": "printed_passage_only",
                        "stretch": False
                    }
                ]
            },
            "vocabulary": {
                "items": [
                    { "id": 1, "term": "calendar", "ipa": "/cal/", "part_of_speech": "n", "definition_en": "cal", "meaning_vi": "lịch", "example": "school calendar", "vocab_type": "single_word", "source": "reading" },
                    { "id": 2, "term": "vacation", "ipa": "/vac/", "part_of_speech": "n", "definition_en": "vac", "meaning_vi": "kỳ nghỉ", "example": "summer vacation", "vocab_type": "single_word", "source": "reading" },
                    { "id": 3, "term": "forget", "ipa": "/for/", "part_of_speech": "v", "definition_en": "forget", "meaning_vi": "quên", "example": "forget things", "vocab_type": "single_word", "source": "reading" },
                    { "id": 4, "term": "subject", "ipa": "/sub/", "part_of_speech": "n", "definition_en": "subj", "meaning_vi": "môn học", "example": "school subjects", "vocab_type": "single_word", "source": "reading" },
                    { "id": 5, "term": "employee", "ipa": "/emp/", "part_of_speech": "n", "definition_en": "emp", "meaning_vi": "nhân viên", "example": "local employees", "vocab_type": "single_word", "source": "reading" },
                    { "id": 6, "term": "costly", "ipa": "/cost/", "part_of_speech": "adj", "definition_en": "expensive", "meaning_vi": "tốn kém", "example": "it is costly", "vocab_type": "single_word", "source": "reading" },
                    { "id": 7, "term": "school calendar", "ipa": "/sc/", "part_of_speech": "n", "definition_en": "calendar", "meaning_vi": "lịch học", "example": "school calendar", "vocab_type": "phrase", "source": "reading" },
                    { "id": 8, "term": "summer vacation", "ipa": "/sv/", "part_of_speech": "n", "definition_en": "vacation", "meaning_vi": "nghỉ hè", "example": "summer vacation", "vocab_type": "phrase", "source": "reading" },
                    { "id": 9, "term": "year-round schedule", "ipa": "/ys/", "part_of_speech": "n", "definition_en": "schedule", "meaning_vi": "lịch học cả năm", "example": "year-round schedule", "vocab_type": "collocation", "source": "reading" },
                    { "id": 10, "term": "raise test scores", "ipa": "/rt/", "part_of_speech": "v", "definition_en": "raise", "meaning_vi": "tăng điểm số", "example": "raise test scores", "vocab_type": "collocation", "source": "reading" },
                    { "id": 11, "term": "under pressure", "ipa": "/up/", "part_of_speech": "prep", "definition_en": "pressure", "meaning_vi": "chịu áp lực", "example": "under pressure", "vocab_type": "collocation", "source": "reading" },
                    { "id": 12, "term": "public school students", "ipa": "/ps/", "part_of_speech": "n", "definition_en": "students", "meaning_vi": "học sinh trường công", "example": "public school students", "vocab_type": "topic_vocabulary", "source": "reading" },
                    { "id": 13, "term": "extra time", "ipa": "/et/", "part_of_speech": "n", "definition_en": "time", "meaning_vi": "thời gian thêm", "example": "extra time", "vocab_type": "topic_vocabulary", "source": "reading" },
                    { "id": 14, "term": "short breaks", "ipa": "/sb/", "part_of_speech": "n", "definition_en": "breaks", "meaning_vi": "kỳ nghỉ ngắn", "example": "short breaks", "vocab_type": "topic_vocabulary", "source": "reading" },
                    { "id": 15, "term": "traditional one", "ipa": "/to/", "part_of_speech": "n", "definition_en": "traditional", "meaning_vi": "truyền thống", "example": "traditional one", "vocab_type": "topic_vocabulary", "source": "reading" },
                    { "id": 16, "term": "modern society", "ipa": "/ms/", "part_of_speech": "n", "definition_en": "society", "meaning_vi": "xã hội hiện đại", "example": "modern society", "vocab_type": "single_word", "source": "reading" },
                    { "id": 17, "term": "local businesses", "ipa": "/lb/", "part_of_speech": "n", "definition_en": "businesses", "meaning_vi": "doanh nghiệp địa phương", "example": "local businesses", "vocab_type": "single_word", "source": "reading" },
                    { "id": 18, "term": "classroom", "ipa": "/class/", "part_of_speech": "n", "definition_en": "classroom", "meaning_vi": "lớp học", "example": "in classroom", "vocab_type": "single_word", "source": "reading" },
                    { "id": 19, "term": "teacher", "ipa": "/teach/", "part_of_speech": "n", "definition_en": "teacher", "meaning_vi": "giáo viên", "example": "our teacher", "vocab_type": "single_word", "source": "reading" }
                ],
                "recycled_items": [],
                "quizlet": {
                    "section_1_simple": ["calendar : lịch"],
                    "section_2_detailed": ["calendar (/cal/) [n] : lịch"]
                },
                "vocab_checker_items": [
                    { "term": "calendar", "ipa": "/cal/", "part_of_speech": "n", "definition_en": "cal", "meaning_vi": "lịch" }
                ]
            },
            "grammar": {
                "guide": [
                    { "heading": "#### Chủ điểm 1: Comparatives", "content": "Explanation" }
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
                        "task_type": "Word Ordering",
                        "prompt": "Sắp xếp từ.",
                        "target_length": "3 sentences",
                        "focus_skill": "Ordering",
                        "useful_language": ["more"],
                        "success_criteria": ["Compare"],
                        "visual_data": {
                            "type": "none",
                            "content": ""
                        },
                        "topic_alignment": True
                    }
                ]
            },
            "answers": {
                "reading_answers": [
                    { "question_id": 1, "correct_answer": "A", "evidence_quote": "school life target words", "evidence_paragraph": 1, "explanation_vi": "Giải thích", "why_others_wrong_vi": "Sai", "tip_vi": "Mẹo" }
                ],
                "grammar_answers": [
                    { "question_id": 1, "correct_answer": "Local businesses do not like the new calendar.", "analysis_vi": "Giải thích", "tip_vi": "Mẹo" }
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

    def test_rejects_correct_the_error_with_no_error(self):
        data = dict(self.base_data)
        data["grammar"]["questions"] = [
            {
                "id": 1,
                "type": "Error Correction",
                "question": "Correct the error: Local businesses do not like the new calendar.",
                "options": [],
                "correct_answer": "Local businesses do not like the new calendar.",
                "explanation_vi": "Explanation mentions 'does not'",
                "stretch": False,
                "logic_validation": {
                    "has_exactly_one_valid_answer": True,
                    "context_is_sufficient": True,
                    "punctuation_complete": True,
                    "meaning_preserved": True
                },
                "error_correction_validation": {
                    "original_sentence": "Local businesses do not like the new calendar.",
                    "corrected_sentence": "Local businesses do not like the new calendar.",
                    "target_error_text": "does not",
                    "target_error_type": "subject_verb_agreement",
                    "correction_text": "do not",
                    "original_contains_error": True,
                    "corrected_differs_from_original": True,
                    "exactly_one_target_error": True,
                    "explanation_matches_error": True
                }
            }
        ]
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_rejects_correct_the_error_when_answer_same_as_original(self):
        data = dict(self.base_data)
        data["grammar"]["questions"] = [
            {
                "id": 1,
                "type": "Error Correction",
                "question": "Correct the error: This school is more expensive than that school.",
                "options": [],
                "correct_answer": "This school is more expensive than that school.",
                "explanation_vi": "Explanation",
                "stretch": False,
                "logic_validation": {
                    "has_exactly_one_valid_answer": True,
                    "context_is_sufficient": True,
                    "punctuation_complete": True,
                    "meaning_preserved": True
                },
                "error_correction_validation": {
                    "original_sentence": "This school is more expensive than that school.",
                    "corrected_sentence": "This school is more expensive than that school.",
                    "target_error_text": "most",
                    "target_error_type": "comparative",
                    "correction_text": "more",
                    "original_contains_error": True,
                    "corrected_differs_from_original": True,
                    "exactly_one_target_error": True,
                    "explanation_matches_error": True
                }
            }
        ]
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_rejects_explanation_that_mentions_missing_error_text(self):
        data = dict(self.base_data)
        data["grammar"]["questions"] = [
            {
                "id": 1,
                "type": "Error Correction",
                "question": "Correct the error: Local businesses do not like the new calendar.",
                "options": [],
                "correct_answer": "Local businesses do not like the new calendar.",
                "explanation_vi": "Change 'does not' to 'do not'.",
                "stretch": False,
                "logic_validation": {
                    "has_exactly_one_valid_answer": True,
                    "context_is_sufficient": True,
                    "punctuation_complete": True,
                    "meaning_preserved": True
                },
                "error_correction_validation": {
                    "original_sentence": "Local businesses do not like the new calendar.",
                    "corrected_sentence": "Local businesses do not like the new calendar.",
                    "target_error_text": "does not",
                    "target_error_type": "subject_verb_agreement",
                    "correction_text": "do not",
                    "original_contains_error": True,
                    "corrected_differs_from_original": True,
                    "exactly_one_target_error": True,
                    "explanation_matches_error": True
                }
            }
        ]
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_accepts_subject_verb_error_local_businesses_does_not(self):
        data = dict(self.base_data)
        data["grammar"]["questions"] = [
            {
                "id": 1,
                "type": "Error Correction",
                "question": "Correct the error: Local businesses does not like the new calendar.",
                "options": [],
                "correct_answer": "Local businesses do not like the new calendar.",
                "explanation_vi": "Change 'does not' to 'do not'.",
                "stretch": False,
                "logic_validation": {
                    "has_exactly_one_valid_answer": True,
                    "context_is_sufficient": True,
                    "punctuation_complete": True,
                    "meaning_preserved": True
                },
                "error_correction_validation": {
                    "original_sentence": "Local businesses does not like the new calendar.",
                    "corrected_sentence": "Local businesses do not like the new calendar.",
                    "target_error_text": "does not",
                    "target_error_type": "subject_verb_agreement",
                    "correction_text": "do not",
                    "original_contains_error": True,
                    "corrected_differs_from_original": True,
                    "exactly_one_target_error": True,
                    "explanation_matches_error": True
                }
            }
        ]
        self.write_json(data)
        self.assertTrue(validate_lesson_json(self.tmp_json_path))

    def test_accepts_comparative_error_the_most_expensive_than(self):
        data = dict(self.base_data)
        data["grammar"]["questions"] = [
            {
                "id": 1,
                "type": "Error Correction",
                "question": "Correct the error: This school is the most expensive than that school.",
                "options": [],
                "correct_answer": "This school is more expensive than that school.",
                "explanation_vi": "Change 'most' to 'more'.",
                "stretch": False,
                "logic_validation": {
                    "has_exactly_one_valid_answer": True,
                    "context_is_sufficient": True,
                    "punctuation_complete": True,
                    "meaning_preserved": True
                },
                "error_correction_validation": {
                    "original_sentence": "This school is the most expensive than that school.",
                    "corrected_sentence": "This school is more expensive than that school.",
                    "target_error_text": "most",
                    "target_error_type": "comparative",
                    "correction_text": "more",
                    "original_contains_error": True,
                    "corrected_differs_from_original": True,
                    "exactly_one_target_error": True,
                    "explanation_matches_error": True
                }
            }
        ]
        self.write_json(data)
        self.assertTrue(validate_lesson_json(self.tmp_json_path))

if __name__ == "__main__":
    unittest.main()
