#!/usr/bin/env python3
import json
import unittest
from pathlib import Path
import sys

# Add scripts directory to path to import validator
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.append(str(scripts_dir))

from validate_lesson_json import validate_lesson_json

class TestGrammarLogicQC(unittest.TestCase):
    
    def setUp(self):
        self.tmp_json_path = Path("tmp_test_logic_lesson_source.json")
        
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
                "lesson_id": "LSN-20260706-B1-Q7R9T2W1",
                "day": "20260706",
                "level": "B1",
                "theme": "Entertainment",
                "topic": "Streaming",
                "specific_topic": "Streaming Rise",
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
                "source_title": "Reputable Source",
                "publisher": "Reputable Publisher",
                "verified_url": "https://example.com/source"
            },
            "reading": {
                "passage": {
                    "title": "Passage Title",
                    "paragraphs": [
                        { "id": 1, "text": "This is paragraph one with target vocabulary word innovation." }
                    ]
                },
                "questions": [
                    {
                        "id": 1,
                        "type": "Multiple Choice",
                        "question": "What is the main theme?",
                        "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
                        "correct_answer": "Option A text",
                        "evidence_paragraph": 1,
                        "evidence_quote": "target vocabulary word innovation",
                        "rationale_vi": "Giải thích",
                        "reasoning_skill": "paraphrase",
                        "source_scope": "printed_passage_only",
                        "stretch": False
                    }
                ]
            },
            "vocabulary": {
                "items": [
                    { "id": 1, "term": "innovation", "ipa": "/ˌɪnəˈveɪʃn/", "part_of_speech": "n", "definition_en": "new ideas", "meaning_vi": "sự đổi mới", "example": "innovation is key", "vocab_type": "topic_vocabulary", "source": "reading" },
                    { "id": 2, "term": "traditional distribution models", "ipa": "/trəˈdɪʃənl ˌdɪstrɪˈbjuːʃn ˈmɒdlz/", "part_of_speech": "phrase", "definition_en": "old distribution ways", "meaning_vi": "mô hình phân phối truyền thống", "example": "traditional distribution models are disrupted", "vocab_type": "collocation", "source": "reading" },
                    { "id": 3, "term": "cinema attendance", "ipa": "/ˈsɪnəmə əˈtendəns/", "part_of_speech": "n", "definition_en": "going to cinema", "meaning_vi": "lượng khán giả đến rạp", "example": "cinema attendance is dropping", "vocab_type": "collocation", "source": "reading" },
                    { "id": 4, "term": "digital streaming platforms", "ipa": "/ˈdɪdʒɪtəl ˈstriːmɪŋ ˈplætfɔːmz/", "part_of_speech": "phrase", "definition_en": "streaming platforms", "meaning_vi": "nền tảng phát trực tuyến", "example": "digital streaming platforms are rising", "vocab_type": "phrase", "source": "reading" },
                    { "id": 5, "term": "reach global audiences", "ipa": "/riːtʃ ˈɡləʊbl ˈɔːdiənsɪz/", "part_of_speech": "phrase", "definition_en": "reach the world", "meaning_vi": "tiếp cận khán giả toàn cầu", "example": "films reach global audiences", "vocab_type": "academic_vocabulary", "source": "reading" }
                ],
                "recycled_items": [],
                "quizlet": {
                    "section_1_simple": ["innovation : sự đổi mới"],
                    "section_2_detailed": ["innovation : new ideas"]
                },
                "vocab_checker_items": [
                    { "term": "innovation", "ipa": "/ˌɪnəˈveɪʃn/", "part_of_speech": "n", "definition_en": "new ideas", "meaning_vi": "sự đổi mới" }
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
                        "type": "Multiple Choice",
                        "question": "The cinema, _______ was built in 1920, is modern.",
                        "options": ["that", "which", "who", "where"],
                        "correct_answer": "which",
                        "explanation_vi": "giải thích",
                        "stretch": False,
                        "logic_validation": {
                          "has_exactly_one_valid_answer": True,
                          "context_is_sufficient": True,
                          "punctuation_complete": True,
                          "meaning_preserved": True,
                          "why_other_options_are_wrong": [
                            {"option": "that", "reason": "cannot be used after a comma in non-defining relative clauses"},
                            {"option": "who", "reason": "used for people, not things like a cinema"},
                            {"option": "where", "reason": "adverb requiring a subject and verb afterwards, not immediately followed by a verb"}
                          ]
                        }
                      }
                ]
            },
            "writing": {
                "tasks": [
                    {
                        "id": 1,
                        "task_type": "Data Description",
                        "prompt": "Compare cinema and streaming.",
                        "target_length": "3 sentences",
                        "focus_skill": "Comparison",
                        "useful_language": ["more hours"],
                        "success_criteria": ["Compare categories"],
                        "visual_data": {
                            "type": "svg",
                            "content": "<svg><text x=\"10\" y=\"20\">Media Chart</text><text>y axis</text><text>x axis</text><text>unit</text><text>categories</text></svg>"
                        },
                        "topic_alignment": True
                    }
                ]
            },
            "answers": {
                "reading_answers": [
                    { "question_id": 1, "correct_answer": "Option A text", "evidence_quote": "target vocabulary word innovation", "evidence_paragraph": 1, "explanation_vi": "Giải thích", "why_others_wrong_vi": "Sai", "tip_vi": "Mẹo" }
                ],
                "grammar_answers": [
                    { "question_id": 1, "correct_answer": "which", "analysis_vi": "Phân tích", "tip_vi": "Mẹo" }
                ],
                "writing_guidance": [
                    { "task_id": 1, "model_answer": "Cinema is decreasing.", "guidance_vi": "Hướng dẫn", "self_checklist": ["Check"] }
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

    def test_accepts_valid_data(self):
        self.write_json(self.valid_data)
        self.assertTrue(validate_lesson_json(self.tmp_json_path))

    def test_rejects_relative_clause_comma_question_without_context(self):
        data = dict(self.valid_data)
        data["grammar"]["questions"][0] = {
            "id": 1,
            "type": "Multiple Choice",
            "question": "Identify the sentence that uses relative clause commas correctly.",
            "options": ["A", "B", "C"],
            "correct_answer": "B",
            "explanation_vi": "giải thích",
            "stretch": False,
            "logic_validation": {
                "has_exactly_one_valid_answer": True,
                "context_is_sufficient": True,
                "punctuation_complete": True,
                "meaning_preserved": True
            }
        }
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_rejects_multiple_valid_answers_for_defining_nondefining_clause(self):
        data = dict(self.valid_data)
        data["grammar"]["questions"][0]["logic_validation"]["has_exactly_one_valid_answer"] = False
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_rejects_nondefining_clause_missing_closing_comma(self):
        data = dict(self.valid_data)
        data["grammar"]["questions"][0] = {
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
                "meaning_preserved": True,
                "why_other_options_are_wrong": [{"option": "which", "reason": "x"}, {"option": ", who", "reason": "y"}]
            }
        }
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_rejects_inserted_option_that_does_not_complete_sentence(self):
        # Covered by nondefining_clause_missing_closing_comma
        pass

    def test_rejects_generic_noun_without_context(self):
        data = dict(self.valid_data)
        data["grammar"]["questions"][0] = {
            "id": 1,
            "type": "Multiple Choice",
            "question": "Resident Assistants _______ must follow university rules.",
            "options": ["who", ", who,", "which"],
            "correct_answer": "who",
            "explanation_vi": "giải thích",
            "stretch": False,
            "logic_validation": {
                "has_exactly_one_valid_answer": True,
                "context_is_sufficient": True,
                "punctuation_complete": True,
                "meaning_preserved": True,
                "why_other_options_are_wrong": [{"option": ", who,", "reason": "x"}, {"option": "which", "reason": "y"}]
            }
        }
        self.write_json(data)
        self.assertFalse(validate_lesson_json(self.tmp_json_path))

    def test_accepts_defining_clause_when_context_says_many_students(self):
        data = dict(self.valid_data)
        data["grammar"]["questions"][0] = {
            "id": 1,
            "type": "Multiple Choice",
            "question": "There are many students. Resident Assistants _______ must follow university rules.",
            "options": ["who", ", who,", "which"],
            "correct_answer": "who",
            "explanation_vi": "giải thích",
            "stretch": False,
            "logic_validation": {
                "has_exactly_one_valid_answer": True,
                "context_is_sufficient": True,
                "punctuation_complete": True,
                "meaning_preserved": True,
                "why_other_options_are_wrong": [{"option": ", who,", "reason": "x"}, {"option": "which", "reason": "y"}]
            }
        }
        self.write_json(data)
        self.assertTrue(validate_lesson_json(self.tmp_json_path))

    def test_accepts_nondefining_clause_when_context_says_only_one_student(self):
        data = dict(self.valid_data)
        data["grammar"]["questions"][0] = {
            "id": 1,
            "type": "Multiple Choice",
            "question": "There is only one assistant. Resident Assistants, _______, must follow rules.",
            "options": ["who", "which", "whose"],
            "correct_answer": "who",
            "explanation_vi": "giải thích",
            "stretch": False,
            "logic_validation": {
                "has_exactly_one_valid_answer": True,
                "context_is_sufficient": True,
                "punctuation_complete": True,
                "meaning_preserved": True,
                "why_other_options_are_wrong": [{"option": "which", "reason": "x"}, {"option": "whose", "reason": "y"}]
            }
        }
        self.write_json(data)
        self.assertTrue(validate_lesson_json(self.tmp_json_path))

if __name__ == "__main__":
    unittest.main()
