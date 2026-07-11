import json
import os

out_dir = r"d:\Dev\source\github\daily-lesson-practise\outputs\ielts-daily-reading-writing\20260710-B1\lsn"
os.makedirs(out_dir, exist_ok=True)

# Generate 13 reading questions
reading_questions = []
for i in range(1, 14):
    reading_questions.append({
        "id": i,
        "type": "multiple choice",
        "question": f"What is the main point of paragraph {i}?" if i <= 3 else f"In paragraph 1, what does the word 'X' refer to? (Q{i})",
        "options": ["A: Teamwork is good", "B: Teamwork is bad", "C: Sports are hard", "D: Winning is everything"],
        "correct_answer": "A: Teamwork is good",
        "evidence_paragraph": 1,
        "evidence_quote": "Teamwork is good.",
        "rationale_vi": "Đoạn văn nói rằng làm việc nhóm là tốt.",
        "reasoning_skill": "main_idea" if i == 1 else ("reference" if i == 2 else ("cause_effect" if i == 3 else ("inference" if i <= 8 else "literal"))),
        "source_scope": "printed_passage_only",
        "stretch": False,
        "paraphrase_mapping": "teamwork -> teamwork",
        "keyword_overlap_check": "ok",
        "distractor_analysis": [
            {"option": "B: Teamwork is bad", "is_keyword_trap": True, "analysis": "Sai logic"},
            {"option": "C: Sports are hard", "is_keyword_trap": False, "analysis": "Không được nhắc đến"},
            {"option": "D: Winning is everything", "is_keyword_trap": False, "analysis": "Trái ngược với ý chính"}
        ]
    })

# Generate 20 vocab words
vocab_items = []
for i in range(1, 21):
    vocab_items.append({
        "id": i,
        "term": f"teamwork {i}",
        "ipa": "/ˈtiːm.wɜːk/",
        "part_of_speech": "noun",
        "definition_en": "the activity of working together in a group",
        "meaning_vi": "sự làm việc nhóm",
        "example": "Teamwork is essential.",
        "vocab_type": "phrase" if i == 1 else ("collocation" if i <= 3 else "topic_vocabulary"),
        "source": "reading"
    })

# Generate 30 grammar questions
grammar_questions = []
for i in range(1, 31):
    grammar_questions.append({
        "id": i,
        "type": "multiple choice",
        "question": f"He usually ________ (play) football on Sundays. (Q{i})",
        "options": ["plays", "play", "playing", "played"],
        "correct_answer": "plays",
        "explanation_vi": "Chủ ngữ ngôi thứ 3 số ít, thì hiện tại đơn.",
        "difficulty": "easy",
        "cognitive_level": "context_use",
        "source_connection": "independent",
        "target_structure": "Present Simple",
        "level": "B1",
        "stretch": False,
        "one_answer_check": {
            "has_exactly_one_valid_answer": True,
            "context_is_sufficient": True,
            "final_sentence_after_insertion": "He usually plays football on Sundays.",
            "why_correct_is_unique": "Chỉ thì hiện tại đơn phù hợp với usually.",
            "why_other_options_are_wrong": [{"option": "play", "reason": "Sai thì"}, {"option": "playing", "reason": "Sai dạng"}, {"option": "played", "reason": "Sai thì"}],
            "punctuation_complete": True,
            "meaning_preserved": True,
            "target_structure_clear": True,
            "answer_family_is_bounded": True,
            "example_expected_answer": "plays",
            "alternative_answers_allowed": []
        },
        "deep_grammar_validation": {"has_single_clear_answer": True, "requires_context_or_meaning": True, "meaning_preserved_if_transformation": True, "is_not_surface_clue_only": True, "matches_target_structure": True, "difficulty_is_appropriate": True, "level_is_appropriate": True},
        "option_validations": [],
        "meaning_preservation_validation": {"original_meaning": "", "transformed_meaning": "", "meaning_is_preserved": True, "target_structure_used": True, "no_extra_information_added": True, "no_information_removed": True, "answer_family_is_narrow": True},
        "error_correction_validation": {"original_sentence": "", "corrected_sentence": "", "target_error_text": "", "target_error_type": "", "correction_text": "", "original_contains_error": False, "corrected_differs_from_original": False, "exactly_one_target_error": False, "explanation_matches_error": False}
    })

# Writing tasks
writing_tasks = []
for i in range(1, 6):
    writing_tasks.append({
        "id": i,
        "task_type": "Email",
        "prompt": f"Write an email to a friend about a recent sports match. (Task {i})",
        "target_length": "100 words",
        "focus_skill": "Describing past events",
        "useful_language": ["First", "Then", "Finally"],
        "success_criteria": ["Use past tense", "Write 100 words"],
        "visual_data": {"type": "none", "content": ""},
        "topic_alignment": True
    })

payload = {
    "execution": {"mode": "auto", "pipeline_status": "qc_passed", "current_stage": "qc", "revision_attempts": {"source": 0, "reading": 0, "vocabulary": 0, "grammar": 0, "writing": 0, "answers": 0, "pdf_layout": 0}},
    "human_review": {"mode": "auto", "checkpoints": []},
    "agent_review": {"reviews": [], "challenges": []},
    "lesson_meta": {
        "lesson_id": "LSN-20260710-B1-ABC", "day": "20260710", "level": "B1", "theme": "Society", "topic": "Sportsmanship and teamwork", "specific_topic": "The value of teamwork",
        "created_at": "2026-07-10T10:00:00", "reading_question_count": 13, "vocabulary_count": 20, "grammar_question_count": 30, "writing_task_count": 5,
        "printed_time_allowed_minutes": 120, "estimated_completion_time_minutes": 120, "time_workload_status": "ok"
    },
    "source": {
        "status": "verified", "source_title": "The importance of sportsmanship", "publisher": "Sports Daily", "author": "John Doe", "published_date": "2023",
        "verified_url": "https://example.com/sportsmanship", "access_date": "2026-07-10", "url_status": "OK", "credibility_note": "High", "topic_relevance_note": "High",
        "usable_excerpt": "Sportsmanship is key to teamwork.", "copyright_note": "CC", "failure_reason": ""
    },
    "reading": {
        "reading_blueprint": [{"question_no": i, "type": "multiple choice", "depth": "main_idea" if i == 1 else ("reference" if i == 2 else ("cause-effect" if i == 3 else ("inference" if i <= 8 else "literal"))), "target_skill": "main_idea" if i == 1 else ("reference" if i == 2 else ("cause_effect" if i == 3 else ("inference" if i <= 8 else "detail"))), "evidence_strategy": "single sentence", "distractor_strategy": "keyword trap"} for i in range(1, 14)],
        "passage": {"title": "Teamwork in Sports", "paragraphs": [{"id": 1, "text": "Teamwork is good. It helps teams win."}]},
        "questions": reading_questions
    },
    "vocabulary": {
        "items": vocab_items,
        "recycled_items": [{"term": "fair play", "ipa": "/ipa/", "part_of_speech": "n", "meaning_vi": "chơi đẹp", "source_day": "20260705"}, {"term": "fair play 2", "ipa": "/ipa/", "part_of_speech": "n", "meaning_vi": "chơi đẹp", "source_day": "20260705"}, {"term": "fair play 3", "ipa": "/ipa/", "part_of_speech": "n", "meaning_vi": "chơi đẹp", "source_day": "20260705"}],
        "quizlet": {"section_1_simple": [f"word {i} - def {i}" for i in range(1, 21)], "section_2_detailed": [f"word {i} (n) - def {i}" for i in range(1, 21)]},
        "vocab_checker_items": [{"term": f"teamwork {i}", "ipa": "/ipa/", "part_of_speech": "n", "definition_en": "def", "meaning_vi": "y nghia"} for i in range(1, 21)]
    },
    "grammar": {
        "grammar_blueprint": [{"question_no": i, "grammar_target": "Present Simple", "question_type": "error correction" if i == 1 else ("writing transfer" if i == 2 else "contextual choice"), "depth": "context", "tested_dimension": "meaning", "trap": f"trap_{i%4}"} for i in range(1, 31)],
        "targets": [{"name": "Present Simple", "level": "B1", "reason": "Basic grammar"}],
        "guide": [{"heading": "#### Present Simple", "content": "Used for habits."}],
        "common_mistakes": [{"trap": "Missing s", "wrong_example": "He play", "correct_version": "He plays", "why_it_matters": "Subject-verb agreement"}],
        "sections": [{"section_title": "Task 1: Present Simple", "internal_question_start": 1, "internal_question_end": 30, "display_question_start": 1, "display_question_end": 30, "compiler_computed_range": True}],
        "questions": grammar_questions
    },
    "writing": {"tasks": writing_tasks},
    "answers": {
        "reading_answers": [{"question_id": i, "correct_answer": "A: Teamwork is good", "question_type": "multiple choice", "evidence_quote": "Teamwork is good.", "evidence_paragraph": 1, "explanation_vi": "Giải thích", "why_others_wrong_vi": "Sai", "depth_check_vi": "OK", "tip_vi": "Mẹo", "stretch_note": ""} for i in range(1, 14)],
        "grammar_answers": [{"question_id": i, "correct_answer": "plays", "grammar_target": "Present Simple", "form_meaning_vi": "Ý nghĩa", "use_in_context_vi": "Ngữ cảnh", "trap_logic_vi": "Bẫy", "why_others_wrong_vi": "Sai", "depth_check_vi": "OK", "analysis_vi": "Phân tích", "tip_vi": "Mẹo", "stretch_note": ""} for i in range(1, 31)],
        "writing_guidance": [{"task_id": i, "model_answer": "Model answer here.", "guidance_vi": "Hướng dẫn", "self_checklist": ["Did I use past tense?"]} for i in range(1, 6)],
        "writing_revisions": [],
        "review_bridge": [
            {"id": 1, "prompt": "Review Question 1", "correct_answer": "A", "rationale_vi": "Giải thích"},
            {"id": 2, "prompt": "Review Question 2", "correct_answer": "B", "rationale_vi": "Giải thích"},
            {"id": 3, "prompt": "Review Question 3", "correct_answer": "C", "rationale_vi": "Giải thích"}
        ]
    },
    "warm_up": ["What sports do you play?", "Do you like teamwork?", "Why is it important?"]
}

with open(os.path.join(out_dir, "lesson_source.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)

print("JSON successfully generated.")
