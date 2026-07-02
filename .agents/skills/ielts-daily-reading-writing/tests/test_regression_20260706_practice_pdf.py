#!/usr/bin/env python3
import json
import unittest
import copy
from pathlib import Path
import sys

# Add scripts directory to path to import validator
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.append(str(scripts_dir))

from validate_lesson_json import validate_lesson_json

class TestIELTSRegression20260706(unittest.TestCase):
    
    def setUp(self):
        # Create a basic valid lesson source structure
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
            "lesson_id": "LSN-20260706-B1-AI-TRAFFIC-12345678",
            "day": "20260706",
            "level": "B1",
            "theme": "Travel & Transportation",
            "topic": "Road safety, traffic rules, public transport problems",
            "specific_topic": "Google's AI System Helps Improve City Traffic Flow",
            "created_at": "2026-07-01T22:00:00Z",
            "reading_question_count": 2,
            "vocabulary_count": 6,
            "grammar_question_count": 2,
            "writing_task_count": 1,
            "printed_time_allowed_minutes": 24
          },
          "source": {
            "status": "verified",
            "source_title": "Google Project Green Light",
            "publisher": "Google",
            "verified_url": "https://blog.google/green-light"
          },
          "reading": {
            "passage": {
              "title": "Google's Project Green Light",
              "paragraphs": [
                { "id": 1, "text": "Google first tested Project Green Light to help improve city traffic flow and reduce emissions." },
                { "id": 2, "text": "The system utilizes AI to analyze driving trends and suggest traffic signal adjustments." }
              ]
            },
            "questions": [
              {
                "id": 1,
                "type": "Multiple Choice",
                "question": "What is the primary goal of Project Green Light?",
                "options": ["To improve traffic flow", "To sell maps", "To track people", "To build cars"],
                "correct_answer": "To improve traffic flow",
                "evidence_paragraph": 1,
                "evidence_quote": "improve city traffic flow and reduce emissions",
                "rationale_vi": "Đoạn 1 nêu rõ dự án giúp cải thiện luồng giao thông.",
                "reasoning_skill": "paraphrase",
                "source_scope": "printed_passage_only",
                "stretch": False
              },
              {
                "id": 2,
                "type": "Gap Fill",
                "question": "The system analyzes data to suggest traffic ___ adjustments.",
                "options": [],
                "correct_answer": "signal",
                "evidence_paragraph": 2,
                "evidence_quote": "suggest traffic signal adjustments",
                "rationale_vi": "Đoạn 2 chỉ ra hệ thống đề xuất điều chỉnh tín hiệu.",
                "reasoning_skill": "inference",
                "source_scope": "printed_passage_only",
                "stretch": False
              }
            ]
          },
          "vocabulary": {
            "items": [
              {
                "id": 1, "term": "emissions", "ipa": "/ɪˈmɪʃnz/", "part_of_speech": "noun",
                "definition_en": "gas sent out into the air", "meaning_vi": "khí thải",
                "example": "reduce emissions", "vocab_type": "single_word", "source": "reading"
              },
              {
                "id": 2, "term": "AI", "ipa": "/ˌeɪ ˈaɪ/", "part_of_speech": "noun",
                "definition_en": "artificial intelligence", "meaning_vi": "trí tuệ nhân tạo",
                "example": "utilizes AI", "vocab_type": "single_word", "source": "reading"
              },
              {
                "id": 3, "term": "traffic flow", "ipa": "/ˈtræfɪk fləʊ/", "part_of_speech": "noun phrase",
                "definition_en": "the movement of vehicles", "meaning_vi": "luồng giao thông",
                "example": "improve traffic flow", "vocab_type": "collocation", "source": "reading"
              },
              {
                "id": 4, "term": "traffic signal adjustments", "ipa": "/ˈtræfɪk ˈsɪɡnəl əˈdʒʌstmənts/", "part_of_speech": "noun phrase",
                "definition_en": "changes to traffic lights", "meaning_vi": "điều chỉnh tín hiệu giao thông",
                "example": "suggest traffic signal adjustments", "vocab_type": "topic_vocabulary", "source": "reading"
              },
              {
                "id": 5, "term": "reduce emissions", "ipa": "/rɪˈdjuːs ɪˈmɪʃnz/", "part_of_speech": "verb phrase",
                "definition_en": "decrease gas release", "meaning_vi": "giảm khí thải",
                "example": "help reduce emissions", "vocab_type": "phrase", "source": "reading"
              },
              {
                "id": 6, "term": "public transport", "ipa": "/ˈpʌblɪk ˈtrænspɔːt/", "part_of_speech": "noun",
                "definition_en": "buses and trains", "meaning_vi": "phương tiện công cộng",
                "example": "use public transport", "vocab_type": "collocation", "source": "reading"
              }
            ],
            "recycled_items": [],
            "quizlet": {
              "section_1_simple": ["emissions : khí thải", "AI : trí tuệ nhân tạo"],
              "section_2_detailed": ["emissions : gas sent out", "AI : artificial intelligence"]
            },
            "vocab_checker_items": [
              { "term": "emissions", "ipa": "/ɪˈmɪʃnz/", "part_of_speech": "noun", "definition_en": "gas sent out", "meaning_vi": "khí thải" },
              { "term": "AI", "ipa": "/ˌeɪ ˈaɪ/", "part_of_speech": "noun", "definition_en": "artificial intelligence", "meaning_vi": "trí tuệ nhân tạo" }
            ]
          },
          "grammar": {
            "targets": [
              { "name": "Relative Pronouns", "level": "B1", "reason": "Target structure" }
            ],
            "guide": [
              { "heading": "#### Chủ điểm 1: Relative clauses", "content": "Grammar points explanation" }
            ],
            "common_mistakes": [
              { "trap": "Trap detail", "wrong_example": "who...", "correct_version": "which...", "why_it_matters": "IELTS score" }
            ],
            "sections": [
              { "section_title": "Relative Pronouns", "internal_question_start": 1, "internal_question_end": 2, "compiler_computed_range": True }
            ],
            "questions": [
              {
                "id": 1, "type": "Gap Fill", "question": "This is the car _____ (which/who) was stopped.",
                "options": [], "correct_answer": "which", "explanation_vi": "dùng which cho vật", "stretch": False,
                "logic_validation": {
                  "has_exactly_one_valid_answer": True,
                  "context_is_sufficient": True,
                  "punctuation_complete": True,
                  "meaning_preserved": True
                }
              },
              {
                "id": 2, "type": "Sentence Transformation", "question": "Complete using active structure.",
                "options": [], "correct_answer": "The police stopped the car.", "explanation_vi": "chủ động", "stretch": False,
                "logic_validation": {
                  "has_exactly_one_valid_answer": True,
                  "context_is_sufficient": True,
                  "punctuation_complete": True,
                  "meaning_preserved": True
                }
              }
            ]
          },
          "writing": {
            "tasks": [
              {
                "id": 1, "task_type": "Email", "prompt": "Write about traffic.", "target_length": "3 sentences",
                "focus_skill": "Writing about transport problems", "useful_language": ["traffic congestion"],
                "success_criteria": ["Write 3 sentences"],
                "visual_data": { "type": "none", "content": "" },
                "topic_alignment": True
              }
            ]
          },
          "answers": {
            "reading_answers": [
              { "question_id": 1, "correct_answer": "To improve traffic flow", "evidence_quote": "improve city traffic flow and reduce emissions", "evidence_paragraph": 1, "explanation_vi": "Giải thích", "why_others_wrong_vi": "Khác sai", "tip_vi": "Mẹo" },
              { "question_id": 2, "correct_answer": "signal", "evidence_quote": "suggest traffic signal adjustments", "evidence_paragraph": 2, "explanation_vi": "Giải thích", "why_others_wrong_vi": "Khác sai", "tip_vi": "Mẹo" }
            ],
            "grammar_answers": [
              { "question_id": 1, "correct_answer": "which", "analysis_vi": "Phân tích", "tip_vi": "Mẹo" },
              { "question_id": 2, "correct_answer": "The police stopped the car.", "analysis_vi": "Phân tích", "tip_vi": "Mẹo" }
            ],
            "writing_guidance": [
              { "task_id": 1, "model_answer": "Traffic is busy.", "guidance_vi": "Hướng dẫn", "self_checklist": ["Correct grammar"] }
            ],
            "review_bridge": [
              { "id": 1, "prompt": "Warmup prompt", "correct_answer": "Answer", "rationale_vi": "Giải thích" },
              { "id": 2, "prompt": "Warmup prompt", "correct_answer": "Answer", "rationale_vi": "Giải thích" },
              { "id": 3, "prompt": "Warmup prompt", "correct_answer": "Answer", "rationale_vi": "Giải thích" }
            ]
          },
          "warm_up": [
            "Warmup question 1?",
            "Warmup question 2?",
            "Warmup question 3?"
          ]
        }
        
        self.tmp_json_path = Path("tmp_test_lesson_source.json")

    def tearDown(self):
        if self.tmp_json_path.exists():
            self.tmp_json_path.unlink()

    def test_valid_pack_passes_validation(self):
        self.tmp_json_path.write_text(json.dumps(self.valid_data, ensure_ascii=False), encoding="utf-8")
        self.assertTrue(validate_lesson_json(self.tmp_json_path))

    def test_reading_questions_must_have_evidence_in_printed_passage(self):
        # Corrupt evidence quote to not match passage
        data = copy.deepcopy(self.valid_data)
        data["reading"]["questions"][0]["evidence_quote"] = "this is not in the text at all"
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_no_question_uses_omitted_source_information(self):
        # Corrupt source_scope
        data = copy.deepcopy(self.valid_data)
        data["reading"]["questions"][0]["source_scope"] = "original_source_only"
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_b1_reading_requires_non_literal_reasoning_ratio(self):
        # Make both reading questions "literal" (violating the B1 50% non-literal ratio rule)
        data = copy.deepcopy(self.valid_data)
        data["reading"]["questions"][0]["reasoning_skill"] = "literal"
        data["reading"]["questions"][1]["reasoning_skill"] = "literal"
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_reading_questions_must_be_sequential(self):
        # Mutate reading questions to violate sequence order within the same type group
        data = copy.deepcopy(self.valid_data)
        data["reading"]["questions"][0]["type"] = "Multiple Choice"
        data["reading"]["questions"][1]["type"] = "Multiple Choice"
        data["reading"]["questions"][0]["evidence_paragraph"] = 2
        data["reading"]["questions"][1]["evidence_paragraph"] = 1
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_grammar_section_ranges_are_computed_not_hardcoded(self):
        # Introduce a hardcoded range in heading
        data = copy.deepcopy(self.valid_data)
        data["grammar"]["guide"][0]["heading"] = "#### Chủ điểm 1: Relative clauses (Questions 27-36)"
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_passive_transformation_does_not_change_meaning(self):
        # Force passive on intransitive "stop"
        data = copy.deepcopy(self.valid_data)
        data["grammar"]["questions"][0]["question"] = "Rewrite using passive voice: The cars stopped at the crossing."
        data["grammar"]["questions"][0]["correct_answer"] = "The cars were stopped at the crossing."
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_writing_tasks_are_topic_aligned(self):
        # Corrupt topic alignment to false
        data = copy.deepcopy(self.valid_data)
        data["writing"]["tasks"][0]["topic_alignment"] = False
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_time_allowed_matches_estimated_workload(self):
        # Set printed time too low compared to workload
        data = copy.deepcopy(self.valid_data)
        data["lesson_meta"]["printed_time_allowed_minutes"] = 15  # Too low, estimate is ~34 mins
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

if __name__ == "__main__":
    unittest.main()
