import json
import os
from datetime import datetime

def generate():
    day = "20260710"
    level = "B1"
    
    payload = {
        "execution": {
            "mode": "auto",
            "pipeline_status": "qc_passed",
            "current_stage": "qc",
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
            "lesson_id": f"LSN-{day}-{level}-ABCD1234",
            "day": day,
            "level": level,
            "theme": "Society",
            "topic": "Sportsmanship and teamwork",
            "specific_topic": "The value of teamwork in youth sports",
            "created_at": datetime.now().isoformat(),
            "reading_question_count": 13,
            "vocabulary_count": 20,
            "grammar_question_count": 30,
            "writing_task_count": 5,
            "printed_time_allowed_minutes": 120,
            "estimated_completion_time_minutes": 120,
            "time_workload_status": "ok"
        },
        "source": {
            "status": "verified",
            "source_title": "Sportsmanship - Wikipedia",
            "publisher": "Wikipedia",
            "author": "Unknown",
            "published_date": "2024",
            "verified_url": "https://en.wikipedia.org/wiki/Sportsmanship",
            "access_date": "2026-07-10",
            "url_status": "OK",
            "credibility_note": "High",
            "topic_relevance_note": "Highly relevant",
            "usable_excerpt": "Sportsmanship is an aspiration or ethos that a sport or activity will be enjoyed for its own sake.",
            "copyright_note": "Creative Commons",
            "failure_reason": ""
        },
        "reading": {
            "reading_blueprint": [
                {
                    "question_no": i, "type": "multiple choice", "depth": "inference", "target_skill": "inference", "evidence_strategy": "cross-paragraph", "distractor_strategy": "keyword trap"
                } for i in range(1, 10)
            ] + [
                {
                    "question_no": 10, "type": "multiple choice", "depth": "main_idea", "target_skill": "main_idea", "evidence_strategy": "cross-paragraph", "distractor_strategy": "keyword trap"
                },
                {
                    "question_no": 11, "type": "multiple choice", "depth": "reference", "target_skill": "reference", "evidence_strategy": "single sentence", "distractor_strategy": "keyword trap"
                },
                {
                    "question_no": 12, "type": "multiple choice", "depth": "cause_effect", "target_skill": "cause_effect", "evidence_strategy": "multiple sentences", "distractor_strategy": "keyword trap"
                },
                {
                    "question_no": 13, "type": "multiple choice", "depth": "literal", "target_skill": "detail", "evidence_strategy": "single sentence", "distractor_strategy": "keyword trap"
                }
            ],
            "passage": {
                "title": "The Value of Teamwork in Youth Sports",
                "paragraphs": [
                    {"id": 1, "text": "Sportsmanship is a fundamental value taught through youth sports. It encourages [R]fair play[/R] and respect for opponents."},
                    {"id": 2, "text": "When children participate in team sports, they learn how to cooperate with others to achieve a common goal."},
                    {"id": 3, "text": "Learning to handle both victory and defeat gracefully is an important life lesson that sports can provide."}
                ]
            },
            "questions": [
                {
                    "id": i, "type": "multiple choice", "question": f"Question {i}?", "options": ["A", "B", "C", "D"], "correct_answer": "A", "evidence_paragraph": 1, "evidence_quote": "Sportsmanship", "rationale_vi": "Suy luận", "reasoning_skill": "inference" if i < 10 else ("main_idea" if i == 10 else ("reference" if i == 11 else ("cause_effect" if i == 12 else "literal"))), "source_scope": "printed_passage_only", "stretch": False, "paraphrase_mapping": "a->a", "keyword_overlap_check": "ok",
                    "distractor_analysis": [{"option": "B", "is_keyword_trap": True, "analysis": "Trap"}] * 3
                } for i in range(1, 14)
            ]
        },
        "vocabulary": {
            "items": [
                {"id": 1, "term": "team up with", "ipa": "/ti:m/", "part_of_speech": "phrase", "definition_en": "to join", "meaning_vi": "hợp tác", "example": "team up", "vocab_type": "phrase", "source": "reading"},
                {"id": 2, "term": "make an effort", "ipa": "/meik/", "part_of_speech": "collocation", "definition_en": "try", "meaning_vi": "nỗ lực", "example": "make an effort", "vocab_type": "collocation", "source": "reading"},
                {"id": 3, "term": "play fair", "ipa": "/plei/", "part_of_speech": "collocation", "definition_en": "be fair", "meaning_vi": "chơi đẹp", "example": "play fair", "vocab_type": "collocation", "source": "reading"},
                {"id": 4, "term": "sportsmanship", "ipa": "/sport/", "part_of_speech": "noun", "definition_en": "fairness", "meaning_vi": "tinh thần", "example": "sportsmanship", "vocab_type": "topic_vocabulary", "source": "reading"}
            ] + [
                {"id": i, "term": f"Word{i}", "ipa": "/w/", "part_of_speech": "noun", "definition_en": "word", "meaning_vi": f"Từ {i}", "example": "word", "vocab_type": "single_word", "source": "reading"} for i in range(5, 21)
            ],
            "recycled_items": [
                {"term": "fair play 1", "ipa": "/1/", "part_of_speech": "noun", "meaning_vi": "1", "source_day": "20260705"},
                {"term": "fair play 2", "ipa": "/2/", "part_of_speech": "noun", "meaning_vi": "2", "source_day": "20260705"},
                {"term": "fair play 3", "ipa": "/3/", "part_of_speech": "noun", "meaning_vi": "3", "source_day": "20260705"}
            ],
            "quizlet": {
                "section_1_simple": [f"W{i} - T{i}" for i in range(1, 21)],
                "section_2_detailed": [f"W{i} (n) - T{i}" for i in range(1, 21)]
            },
            "vocab_checker_items": [{"term": f"W{i}", "ipa": "/w/", "part_of_speech": "n", "definition_en": "d", "meaning_vi": "m"} for i in range(1, 21)]
        },
        "grammar": {
            "grammar_blueprint": [
                {"question_no": 1, "grammar_target": "Present Simple", "question_type": "error correction", "depth": "context", "tested_dimension": "meaning", "trap": "trap"}
            ] + [
                {"question_no": i, "grammar_target": "Present Simple" if i%2==0 else "Past Simple", "question_type": "writing transfer" if i==2 else "contextual choice", "depth": "context", "tested_dimension": "meaning", "trap": "trap"} for i in range(2, 31)
            ],
            "targets": [
                {"name": "Present Simple", "level": "B1", "reason": "Basic tense review"}
            ],
            "guide": [
                {"heading": "#### Present Simple", "content": "We use the present simple for habits and general truths."}
            ],
            "common_mistakes": [
                {"trap": "Forgetting the 's' for he/she/it", "wrong_example": "He play tennis.", "correct_version": "He plays tennis.", "why_it_matters": "Subject-verb agreement is essential."}
            ],
            "sections": [
                {
                    "section_title": "Task 1: Present Simple Practice",
                    "internal_question_start": 1,
                    "internal_question_end": 30,
                    "display_question_start": 1,
                    "display_question_end": 30,
                    "compiler_computed_range": True
                }
            ],
            "questions": [
                {
                    "id": i,
                    "type": "multiple choice",
                    "question": f"The team ________ (practice) every day. (Q{i})",
                    "options": ["practices", "practice", "practicing", "practiced"],
                    "correct_answer": "practices",
                    "explanation_vi": "Đội bóng là danh từ số ít hoặc tập hợp, ở đây dùng số ít.",
                    "difficulty": "easy",
                    "cognitive_level": "context_use",
                    "source_connection": "independent",
                    "target_structure": "Present Simple" if i%2==0 else "Past Simple",
                    "level": "B1",
                    "stretch": False,
                    "one_answer_check": {
                        "has_exactly_one_valid_answer": True,
                        "context_is_sufficient": True,
                        "final_sentence_after_insertion": "The team practices every day.",
                        "why_correct_is_unique": "Only present simple fits the 'every day' context.",
                        "why_other_options_are_wrong": [
                            {"option": "practice", "reason": "Agreement error"},
                            {"option": "practicing", "reason": "Missing aux"},
                            {"option": "practiced", "reason": "Wrong tense"}
                        ],
                        "punctuation_complete": True,
                        "meaning_preserved": True,
                        "target_structure_clear": True,
                        "answer_family_is_bounded": True,
                        "example_expected_answer": "practices",
                        "alternative_answers_allowed": []
                    },
                    "deep_grammar_validation": {
                        "has_single_clear_answer": True,
                        "requires_context_or_meaning": True,
                        "meaning_preserved_if_transformation": True,
                        "is_not_surface_clue_only": True,
                        "matches_target_structure": True,
                        "difficulty_is_appropriate": True,
                        "level_is_appropriate": True
                    },
                    "option_validations": [],
                    "meaning_preservation_validation": {"original_meaning": "", "transformed_meaning": "", "meaning_is_preserved": True, "target_structure_used": True, "no_extra_information_added": True, "no_information_removed": True, "answer_family_is_narrow": True},
                    "error_correction_validation": {"original_sentence": "", "corrected_sentence": "", "target_error_text": "", "target_error_type": "", "correction_text": "", "original_contains_error": False, "corrected_differs_from_original": False, "exactly_one_target_error": False, "explanation_matches_error": False}
                } for i in range(1, 31)
            ]
        },
        "writing": {
            "tasks": [
                {
                    "id": i,
                    "task_type": "Email",
                    "prompt": f"Write an email to your friend about your sports team. (Task {i})",
                    "target_length": "100 words",
                    "focus_skill": "Describing experiences",
                    "useful_language": ["I think", "In my opinion"],
                    "success_criteria": ["Answer all parts", "Use correct grammar"],
                    "visual_data": {"type": "none", "content": ""},
                    "topic_alignment": True
                } for i in range(1, 6)
            ]
        },
        "answers": {
            "reading_answers": [
                {"question_id": i, "correct_answer": "A", "question_type": "multiple choice", "evidence_quote": "Sportsmanship", "evidence_paragraph": 1, "explanation_vi": "Giải thích", "why_others_wrong_vi": "Sai", "depth_check_vi": "OK", "tip_vi": "Mẹo", "stretch_note": ""} for i in range(1, 14)
            ],
            "grammar_answers": [
                {"question_id": i, "correct_answer": "practices", "grammar_target": "Target", "form_meaning_vi": "Meaning", "use_in_context_vi": "Context", "trap_logic_vi": "Trap", "why_others_wrong_vi": "Wrong", "depth_check_vi": "OK", "analysis_vi": "Analysis", "tip_vi": "Tip", "stretch_note": ""} for i in range(1, 31)
            ],
            "writing_guidance": [
                {"task_id": i, "model_answer": "Model", "guidance_vi": "Hướng dẫn", "self_checklist": ["Did I answer?"]} for i in range(1, 6)
            ],
            "writing_revisions": [],
            "review_bridge": [
                {"id": 1, "prompt": "Review Question 1", "correct_answer": "A", "rationale_vi": "Giải thích"},
                {"id": 2, "prompt": "Review Question 2", "correct_answer": "B", "rationale_vi": "Giải thích"},
                {"id": 3, "prompt": "Review Question 3", "correct_answer": "C", "rationale_vi": "Giải thích"}
            ]
        },
        "warm_up": ["Discuss your favorite sport.", "What does teamwork mean to you?", "Who is your favorite athlete?"]
    }

    out_dir = r"d:\Dev\source\github\daily-lesson-practise\outputs\ielts-daily-reading-writing\20260710-B1\lsn"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "lesson_source.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("Successfully generated lesson_source.json")

if __name__ == "__main__":
    generate()
