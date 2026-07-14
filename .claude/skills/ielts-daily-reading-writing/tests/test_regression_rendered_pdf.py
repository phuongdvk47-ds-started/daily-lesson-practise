#!/usr/bin/env python3
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add scripts directory to path to import validator
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.append(str(scripts_dir))

from validate_rendered_pdf import validate_rendered_pdf
from validate_lesson_json import validate_lesson_json

class TestRenderedPDFValidation(unittest.TestCase):
    
    def setUp(self):
        self.tmp_json_path = Path("tmp_test_lesson_source.json")
        self.tmp_pdf_path = Path("tmp_test_practice.pdf")
        
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
                "topic": "The Shift to Digital Streaming Services and the Impact on Cinema Attendance",
                "specific_topic": "The Rise of Streaming",
                "created_at": "2026-07-01T22:00:00Z",
                "reading_question_count": 1,
                "vocabulary_count": 5,
                "grammar_question_count": 1,
                "writing_task_count": 1,
                "printed_time_allowed_minutes": 45
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
                    { "section_title": "Relative Pronouns", "internal_question_start": 1, "internal_question_end": 2, "compiler_computed_range": True }
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
                                {"option": "that", "reason": "cannot be used in non-defining"},
                                {"option": "who", "reason": "for people"},
                                {"option": "where", "reason": "adverb"}
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
                            "content": "<svg><text x=\"10\" y=\"20\">Media Chart</text></svg>"
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
            "warm_up": [
                "Warmup question 1?",
                "Warmup question 2?",
                "Warmup question 3?"
            ]
        }
        
    def tearDown(self):
        for path in [self.tmp_json_path, self.tmp_pdf_path]:
            if path.exists():
                path.unlink()

    def write_json(self, data):
        self.tmp_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @patch("validate_rendered_pdf.PdfReader")
    def test_pdf_validation_success(self, mock_pdf_reader):
        self.write_json(self.valid_data)
        self.tmp_pdf_path.touch()
        
        # Set up mock text extraction returning a correct rendering of Part 1 practice sheet
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "IELTS PREMIUM PREPARATION ACADEMY\n"
            "DAILY PRACTICE: DAY 20260706 - THE RISE OF STREAMING\n"
            "(Level: Reading B1 - Writing A1)\n"
            "Time Allowed: 45 mins\n"
            "Student Name: ..............................................................\n"
            "Questions 1: Multiple Choice\n"
            "What is the main theme?\n"
            "Option A text Option B text Option C text Option D text\n"
            "Questions 2-3: Relative Pronouns\n"
            "The cinema,   was built in 1920, is modern.\n"
            "that which who where\n"
            "Media Chart\n"
        )
        mock_pdf_reader.return_value.pages = [mock_page]
        
        errors = validate_rendered_pdf(self.tmp_json_path, self.tmp_pdf_path)
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {errors}")

    @patch("validate_rendered_pdf.PdfReader")
    def test_pdf_validation_missing_mcq_options(self, mock_pdf_reader):
        self.write_json(self.valid_data)
        self.tmp_pdf_path.touch()
        
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Time Allowed: 45 mins\n"
            "What is the main theme?\n"
            "Questions 2-3: Relative Pronouns\n"
            "The cinema,   was built in 1920, is modern.\n"
            "that which who where\n"
        )
        mock_pdf_reader.return_value.pages = [mock_page]
        
        errors = validate_rendered_pdf(self.tmp_json_path, self.tmp_pdf_path)
        self.assertTrue(any("option missing" in err for err in errors), f"Errors were: {errors}")

    @patch("validate_rendered_pdf.PdfReader")
    def test_pdf_validation_collapsed_blank(self, mock_pdf_reader):
        self.write_json(self.valid_data)
        self.tmp_pdf_path.touch()
        
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Time Allowed: 45 mins\n"
            "What is the main theme?\n"
            "Option A text Option B text Option C text Option D text\n"
            "Questions 2-3: Relative Pronouns\n"
            "The cinema, was built in 1920, is modern.\n" # collapsed blank (only 1 space)
            "that which who where\n"
        )
        mock_pdf_reader.return_value.pages = [mock_page]
        
        errors = validate_rendered_pdf(self.tmp_json_path, self.tmp_pdf_path)
        self.assertTrue(any("blank '_______' missing" in err for err in errors), f"Errors were: {errors}")

    @patch("validate_rendered_pdf.PdfReader")
    def test_pdf_validation_stale_grammar_ranges(self, mock_pdf_reader):
        self.write_json(self.valid_data)
        self.tmp_pdf_path.touch()
        
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Time Allowed: 45 mins\n"
            "What is the main theme?\n"
            "Option A text Option B text Option C text Option D text\n"
            "questions 27-36: Multiple Choice Questions\n" # Stale range!
            "The cinema,   was built in 1920, is modern.\n"
            "that which who where\n"
        )
        mock_pdf_reader.return_value.pages = [mock_page]
        
        errors = validate_rendered_pdf(self.tmp_json_path, self.tmp_pdf_path)
        self.assertTrue(any("stale hardcoded grammar range" in err for err in errors), f"Errors were: {errors}")

    @patch("validate_rendered_pdf.PdfReader")
    def test_pdf_validation_time_allowed_mismatch(self, mock_pdf_reader):
        self.write_json(self.valid_data)
        self.tmp_pdf_path.touch()
        
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Time Allowed: 50 mins\n" # Mismatch (expected 45)
            "What is the main theme?\n"
            "Option A text Option B text Option C text Option D text\n"
            "Questions 2-3: Relative Pronouns\n"
            "The cinema,   was built in 1920, is modern.\n"
            "that which who where\n"
        )
        mock_pdf_reader.return_value.pages = [mock_page]
        
        errors = validate_rendered_pdf(self.tmp_json_path, self.tmp_pdf_path)
        self.assertTrue(any("Time Allowed" in err and "mismatch" in err or "says" in err for err in errors), f"Errors were: {errors}")

    @patch("validate_rendered_pdf.PdfReader")
    def test_pdf_validation_generic_warmup(self, mock_pdf_reader):
        self.write_json(self.valid_data)
        self.tmp_pdf_path.touch()
        
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Time Allowed: 45 mins\n"
            "Bạn nghĩ gì về chủ đề này?\n" # Generic warm-up!
            "What is the main theme?\n"
            "Option A text Option B text Option C text Option D text\n"
            "Questions 2-3: Relative Pronouns\n"
            "The cinema,   was built in 1920, is modern.\n"
            "that which who where\n"
        )
        mock_pdf_reader.return_value.pages = [mock_page]
        
        errors = validate_rendered_pdf(self.tmp_json_path, self.tmp_pdf_path)
        self.assertTrue(any("Warm-up question appears generic" in err for err in errors), f"Errors were: {errors}")

    @patch("validate_rendered_pdf.PdfReader")
    def test_pdf_validation_missing_chart_label(self, mock_pdf_reader):
        self.write_json(self.valid_data)
        self.tmp_pdf_path.touch()
        
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Time Allowed: 45 mins\n"
            "What is the main theme?\n"
            "Option A text Option B text Option C text Option D text\n"
            "Questions 2-3: Relative Pronouns\n"
            "The cinema,   was built in 1920, is modern.\n"
            "that which who where\n"
            # Missing "Media Chart" text label!
        )
        mock_pdf_reader.return_value.pages = [mock_page]
        
        errors = validate_rendered_pdf(self.tmp_json_path, self.tmp_pdf_path)
        self.assertTrue(any("Visual SVG text label" in err for err in errors), f"Errors were: {errors}")

if __name__ == "__main__":
    unittest.main()
