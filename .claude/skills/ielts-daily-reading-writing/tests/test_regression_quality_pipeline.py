#!/usr/bin/env python3
import json
import unittest
from pathlib import Path
import sys
import copy

# Add scripts directory to path to import validator
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.append(str(scripts_dir))

from validate_lesson_json import validate_lesson_json

class TestRegressionQualityPipeline(unittest.TestCase):
    
    def setUp(self):
        self.tmp_json_path = Path("tmp_regression_quality_pipeline_test.json")
        
        # A template for a valid lesson source JSON
        self.valid_data = {
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
                "lesson_id": "LSN-20260715-A2+-K8L2P9W4",
                "day": "20260715",
                "level": "A2+",
                "theme": "Community",
                "topic": "Volunteering",
                "specific_topic": "Volunteering benefits",
                "reading_question_count": 2,
                "vocabulary_count": 5,
                "grammar_question_count": 2,
                "writing_task_count": 1,
                "printed_time_allowed_minutes": 21,
                "estimated_completion_time_minutes": 21,
                "time_workload_status": "ok"
            },
            "source": {
                "status": "verified",
                "source_title": "The Benefits of Volunteering",
                "publisher": "Health Pub",
                "verified_url": "https://example.com/volunteering"
            },
            "reading": {
                "passage": {
                    "title": "The Benefits of Volunteering",
                    "paragraphs": [
                        { "id": 1, "text": "Google and Facebook are volunteering partners. Volunteering offers cognitive benefits." }
                    ]
                },
                "questions": [
                    {
                        "id": 1,
                        "type": "Gap Fill",
                        "question": "Which company is the first partner?",
                        "options": [],
                        "correct_answer": "Google",
                        "evidence_paragraph": 1,
                        "evidence_quote": "Google and Facebook are volunteering partners.",
                        "rationale_vi": "Google là đối tác đầu tiên.",
                        "reasoning_skill": "inference",
                        "source_scope": "printed_passage_only",
                        "keyword_overlap_check": "Checked",
                        "paraphrase_mapping": "Google -> Google",
                        "stretch": False
                    },
                    {
                        "id": 2,
                        "type": "Multiple Choice",
                        "question": "What is the benefit?",
                        "options": ["Cognitive benefits", "Money", "Time", "Fame"],
                        "correct_answer": "Cognitive benefits",
                        "evidence_paragraph": 1,
                        "evidence_quote": "volunteering offers cognitive benefits.",
                        "rationale_vi": "Đoạn 1 nêu rõ.",
                        "reasoning_skill": "paraphrase",
                        "source_scope": "printed_passage_only",
                        "keyword_overlap_check": "Checked",
                        "paraphrase_mapping": "benefit -> benefits",
                        "distractor_analysis": [
                          {"option": "Cognitive benefits", "is_keyword_trap": False, "analysis": "Correct"},
                          {"option": "Money", "is_keyword_trap": True, "analysis": "Wrong"},
                          {"option": "Time", "is_keyword_trap": True, "analysis": "Wrong"},
                          {"option": "Fame", "is_keyword_trap": False, "analysis": "Wrong"}
                        ],
                        "stretch": False
                    }
                ]
            },
            "vocabulary": {
                "items": [
                    { "id": 1, "term": "benefit", "ipa": "/ˈbenɪfɪt/", "part_of_speech": "n", "definition_en": "advantage", "meaning_vi": "lợi ích", "example": "cognitive benefit", "vocab_type": "topic_vocabulary", "source": "reading" },
                    { "id": 2, "term": "volunteer", "ipa": "/ˌvɒlənˈtɪə(r)/", "part_of_speech": "v", "definition_en": "do work without pay", "meaning_vi": "tình nguyện", "example": "volunteering is fun", "vocab_type": "topic_vocabulary", "source": "reading" },
                    { "id": 3, "term": "cognitive decline", "ipa": "/ˈkɒɡnətɪv dɪˈklaɪn/", "part_of_speech": "n", "definition_en": "drop in brain power", "meaning_vi": "suy giảm nhận thức", "example": "protect against cognitive decline", "vocab_type": "collocation", "source": "reading" },
                    { "id": 4, "term": "social connections", "ipa": "/ˈsəʊʃl kəˈnekʃnz/", "part_of_speech": "phrase", "definition_en": "connections with others", "meaning_vi": "kết nối xã hội", "example": "build social connections", "vocab_type": "collocation", "source": "reading" },
                    { "id": 5, "term": "mental health", "ipa": "/ˈmentl helθ/", "part_of_speech": "n", "definition_en": "state of mind", "meaning_vi": "sức khỏe tinh thần", "example": "improve mental health", "vocab_type": "academic_vocabulary", "source": "reading" }
                ],
                "recycled_items": [],
                "quizlet": {
                    "section_1_simple": ["benefit : lợi ích"],
                    "section_2_detailed": ["benefit : advantage"]
                },
                "vocab_checker_items": [
                    { "term": "benefit", "ipa": "/ˈbenɪfɪt/", "part_of_speech": "n", "definition_en": "advantage", "meaning_vi": "lợi ích" }
                ]
            },
            "grammar": {
                "guide": [
                    { "heading": "#### Chủ điểm 1: Relative clauses", "content": "Explanation" }
                ],
                "common_mistakes": [
                    { "trap": "Trap", "wrong_example": "who...", "correct_version": "which...", "why_it_matters": "IELTS score" }
                ],
                "sections": [
                    { "section_title": "Relative Pronouns", "internal_question_start": 1, "internal_question_end": 1, "compiler_computed_range": True }
                ],
                "questions": [
                    {
                        "id": 1,
                        "type": "Transformation",
                        "question": "Combine these sentences using 'although': She was tired. She finished the volunteering work.",
                        "correct_answer": "Although she was tired, she finished the volunteering work.",
                        "explanation_vi": "giải thích",
                        "stretch": False,
                        "logic_validation": {
                          "has_exactly_one_valid_answer": True,
                          "context_is_sufficient": True,
                          "punctuation_complete": True,
                          "meaning_preserved": True,
                          "why_other_options_are_wrong": []
                        }
                      },
                      {
                        "id": 2,
                        "type": "Multiple Choice",
                        "question": "Choose the best option.",
                        "options": ["Option A", "Option B"],
                        "correct_answer": "Option A",
                        "explanation_vi": "giải thích",
                        "stretch": False,
                        "logic_validation": {
                          "has_exactly_one_valid_answer": True,
                          "context_is_sufficient": True,
                          "punctuation_complete": True,
                          "meaning_preserved": True,
                          "why_other_options_are_wrong": [
                            {"option": "Option B", "reason": "wrong"}
                          ]
                        }
                      }
                ]
            },
            "writing": {
                "tasks": [
                    {
                        "id": 1,
                        "task_type": "Sentence combining",
                        "prompt": "Combine using relative clause: Dr. Rachel lives in Davis. She encourages volunteers.",
                        "target_length": "1 sentence",
                        "focus_skill": "Relative clauses",
                        "useful_language": ["who encourages"],
                        "success_criteria": ["Use non-defining clause"],
                        "visual_data": {"type": "none", "content": ""},
                        "topic_alignment": True
                    }
                ]
            },
            "answers": {
                "reading_answers": [
                    { "question_id": 1, "correct_answer": "Google", "evidence_quote": "Google and Facebook are volunteering partners.", "evidence_paragraph": 1, "explanation_vi": "Đối tác Google.", "why_others_wrong_vi": "", "tip_vi": "" },
                    { "question_id": 2, "correct_answer": "Cognitive benefits", "evidence_quote": "volunteering offers cognitive benefits.", "evidence_paragraph": 1, "explanation_vi": "Giải thích", "why_others_wrong_vi": "", "tip_vi": "" }
                ],
                "grammar_answers": [
                    { "question_id": 1, "correct_answer": "Although she was tired, she finished the volunteering work.", "analysis_vi": "Phân tích", "tip_vi": "Mẹo" },
                    { "question_id": 2, "correct_answer": "Option A", "analysis_vi": "Phân tích", "tip_vi": "Mẹo" }
                ],
                "writing_guidance": [
                    { 
                        "task_id": 1, 
                        "model_answer": "Dr. Rachel, who lives in Davis, encourages volunteers.", 
                        "guidance_vi": "Hướng dẫn", 
                        "self_checklist": ["Check if comma is after 'Rachel'", "Check if comma is before 'encourages'"] 
                    }
                ],
                "review_bridge": [
                    { "id": 1, "prompt": "Bridge 1", "correct_answer": "Ans", "rationale_vi": "Giải thích" },
                    { "id": 2, "prompt": "Bridge 2", "correct_answer": "Ans", "rationale_vi": "Giải thích" },
                    { "id": 3, "prompt": "Bridge 3", "correct_answer": "Ans", "rationale_vi": "Giải thích" }
                ]
            },
            "warm_up": ["Q1", "Q2", "Q3"]
        }

    def tearDown(self):
        if self.tmp_json_path.exists():
            self.tmp_json_path.unlink()

    def write_json(self, data):
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_regression_valid_pack_passes(self):
        self.write_json(self.valid_data)
        self.assertTrue(validate_lesson_json(self.tmp_json_path))

    def test_regression_ambiguous_gap_fill_slash_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Add slash admitting ambiguity in rationale
        data["reading"]["questions"][0]["rationale_vi"] = "Có thể điền Google / Facebook."
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_regression_ambiguous_gap_fill_phrase_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Add ambiguous phrase in explanation
        data["answers"]["reading_answers"][0]["explanation_vi"] = "chấp nhận cả hai phương án."
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_regression_gap_fill_proper_noun_no_differentiator_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Correct answer is Google, listed with Facebook in quote, but question has no differentiator (like "first")
        data["reading"]["questions"][0]["question"] = "Which company is a volunteering partner?"
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_regression_gap_fill_proper_noun_with_differentiator_passes(self):
        data = copy.deepcopy(self.valid_data)
        # Has "first" which is a unique differentiator
        data["reading"]["questions"][0]["question"] = "Which company is the first partner?"
        self.write_json(data)
        self.assertTrue(validate_lesson_json(self.tmp_json_path))

    def test_regression_writing_task_mismatch_missing_proper_noun_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Model answer is missing proper noun "Rachel" (it uses "She")
        data["answers"]["writing_guidance"][0]["model_answer"] = "She, who lives in Davis, encourages volunteers."
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_regression_writing_task_mismatch_missing_content_words_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Model answer drops important content words like "lives" and "encourages" and "volunteers"
        data["answers"]["writing_guidance"][0]["model_answer"] = "Dr. Rachel in Davis is good."
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_regression_writing_model_answer_identical_to_grammar_correct_answer_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Set writing model answer to be identical to grammar answer 1
        grammar_ans = data["answers"]["grammar_answers"][0]["correct_answer"]
        data["answers"]["writing_guidance"][0]["model_answer"] = grammar_ans
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_regression_writing_self_checklist_comma_target_nonexistent_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Target a word not in the model answer
        data["answers"]["writing_guidance"][0]["self_checklist"] = ["Check if comma is after 'unknown'"]
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_regression_writing_self_checklist_comma_target_not_adjacent_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Target comma after 'encourages' which is not followed by comma in model answer
        data["answers"]["writing_guidance"][0]["self_checklist"] = ["Check if comma is after 'encourages'"]
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_regression_tfng_vocabulary_synonym_statement_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Make question 2 a True/False/Not Given statement but contain synonym instructions
        data["reading"]["questions"][1]["type"] = "True/False/Not Given"
        data["reading"]["questions"][1]["question"] = "Select the word closest in meaning to volunteering."
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_regression_transformation_meaning_loss_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Grammar transformation has 'although' in prompt, but correct answer drops contrast (no 'although', 'but', etc.)
        data["grammar"]["questions"][0]["correct_answer"] = "She was tired and she finished the volunteering work."
        data["answers"]["grammar_answers"][0]["correct_answer"] = "She was tired and she finished the volunteering work."
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_regression_proper_noun_relative_clause_comma_placement_fails(self):
        data = copy.deepcopy(self.valid_data)
        # Model answer has relative clause modifying proper noun but lacks closing comma before main verb 'encourages'
        data["answers"]["writing_guidance"][0]["model_answer"] = "Dr. Rachel, who lives in Davis encourages volunteers."
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

if __name__ == "__main__":
    unittest.main()
