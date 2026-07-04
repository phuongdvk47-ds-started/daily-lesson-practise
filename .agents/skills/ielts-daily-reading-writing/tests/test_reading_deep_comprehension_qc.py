import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add scripts folder to sys.path to import validate_lesson_json
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.validate_lesson_json import validate_lesson_json

def get_base_payload():
    return {
        "execution": {
            "mode": "auto",
            "pipeline_status": "draft",
            "current_stage": "reading",
            "revision_attempts": {
                "source": 0, "reading": 0, "vocabulary": 0,
                "grammar": 0, "writing": 0, "answers": 0, "pdf_layout": 0
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
            "lesson_id": "LSN-20260706-B1-1234",
            "day": "20260706",
            "level": "B1",
            "theme": "Work",
            "topic": "Daily Routine",
            "specific_topic": "Test",
            "created_at": "2026-07-06T00:00:00Z",
            "reading_question_count": 2,
            "vocabulary_count": 0,
            "grammar_question_count": 0,
            "writing_task_count": 0
        },
        "source": {
            "status": "verified",
            "source_title": "Test",
            "publisher": "Test",
            "verified_url": "https://test.com"
        },
        "reading": {
            "passage": {
                "title": "Test Passage",
                "paragraphs": [
                    {"id": 1, "text": "This is a test passage. The quick brown fox jumps over the lazy dog."}
                ]
            },
            "questions": []
        },
        "vocabulary": {
            "items": [], "recycled_items": [{"term": "a", "ipa": "a", "part_of_speech": "n", "meaning_vi": "a", "source_day": "20260705"}, {"term": "b", "ipa": "b", "part_of_speech": "n", "meaning_vi": "b", "source_day": "20260705"}, {"term": "c", "ipa": "c", "part_of_speech": "n", "meaning_vi": "c", "source_day": "20260705"}],
            "quizlet": {"section_1_simple": [], "section_2_detailed": []},
            "vocab_checker_items": [{"term": "test", "ipa": "test", "part_of_speech": "n", "definition_en": "test", "meaning_vi": "test"}]
        },
        "grammar": {
            "targets": [{"name": "A", "level": "B1", "reason": "A"}],
            "guide": [{"heading": "#### H1", "content": "C1"}],
            "common_mistakes": [{"trap": "T", "wrong_example": "W", "correct_version": "C", "why_it_matters": "W"}],
            "sections": [{"section_title": "S", "internal_question_start": 1, "internal_question_end": 1, "compiler_computed_range": True}],
            "questions": []
        },
        "writing": {"tasks": []},
        "answers": {
            "reading_answers": [],
            "grammar_answers": [],
            "writing_guidance": [],
            "review_bridge": [{"id": 1, "prompt": "a", "correct_answer": "a", "rationale_vi": "a"}, {"id": 2, "prompt": "b", "correct_answer": "b", "rationale_vi": "b"}, {"id": 3, "prompt": "c", "correct_answer": "c", "rationale_vi": "c"}]
        },
        "warm_up": ["Question 1 specifically?", "Question 2 specifically?", "Question 3 specifically?"]
    }

def get_valid_question(id_val, reasoning="paraphrase", is_keyword_trap=False):
    return {
        "id": id_val,
        "type": "Multiple Choice",
        "question": "What did the fox do?",
        "options": ["It jumped", "It slept"],
        "correct_answer": "It jumped",
        "evidence_paragraph": 1,
        "evidence_quote": "The quick brown fox jumps over the lazy dog.",
        "rationale_vi": "Rationale",
        "reasoning_skill": reasoning,
        "source_scope": "printed_passage_only",
        "stretch": False,
        "paraphrase_mapping": "jumps -> jumped",
        "keyword_overlap_check": "Minimal overlap",
        "distractor_analysis": [
            {
                "option": "It slept",
                "is_keyword_trap": is_keyword_trap,
                "analysis": "Trap analysis"
            }
        ]
    }

def get_valid_answer(id_val):
    return {
        "question_id": id_val,
        "correct_answer": "It jumped",
        "evidence_quote": "The quick brown fox jumps over the lazy dog.",
        "evidence_paragraph": 1,
        "explanation_vi": "Exp",
        "why_others_wrong_vi": "Why",
        "tip_vi": "Tip"
    }

def run_validation(payload):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f:
        json.dump(payload, f)
        temp_path = f.name
    
    path = Path(temp_path)
    result = validate_lesson_json(path)
    path.unlink()
    return result

def test_valid_deep_reading():
    payload = get_base_payload()
    # 2 questions, 1 paraphrase, 1 literal. Ratio: 50%
    # B1 requires 60% non-literal, so 1 out of 2 is 50%, which should fail for B1.
    # Let's make it 2 non-literal questions. Ratio: 100%
    q1 = get_valid_question(1, "paraphrase", True)
    q2 = get_valid_question(2, "inference", False)
    payload["reading"]["questions"] = [q1, q2]
    payload["answers"]["reading_answers"] = [get_valid_answer(1), get_valid_answer(2)]
    
    assert run_validation(payload) == True

def test_fail_b1_quota():
    payload = get_base_payload()
    # B1, 2 questions, 1 literal, 1 paraphrase. Non-literal ratio = 50% < 60%
    q1 = get_valid_question(1, "literal", True)
    q2 = get_valid_question(2, "paraphrase", True)
    payload["reading"]["questions"] = [q1, q2]
    payload["answers"]["reading_answers"] = [get_valid_answer(1), get_valid_answer(2)]
    
    assert run_validation(payload) == False

def test_fail_a2_quota():
    payload = get_base_payload()
    payload["lesson_meta"]["level"] = "A2"
    # A2 requires >= 50%. Let's give it 2 literal questions. Ratio = 0%
    q1 = get_valid_question(1, "literal", True)
    q1["paraphrase_mapping"] = ""
    q2 = get_valid_question(2, "literal", True)
    q2["paraphrase_mapping"] = ""
    payload["reading"]["questions"] = [q1, q2]
    payload["answers"]["reading_answers"] = [get_valid_answer(1), get_valid_answer(2)]
    
    assert run_validation(payload) == False

def test_fail_missing_paraphrase_mapping():
    payload = get_base_payload()
    q1 = get_valid_question(1, "paraphrase", True)
    del q1["paraphrase_mapping"] # Remove the required mapping for non-literal
    q2 = get_valid_question(2, "inference", True)
    payload["reading"]["questions"] = [q1, q2]
    payload["answers"]["reading_answers"] = [get_valid_answer(1), get_valid_answer(2)]
    
    assert run_validation(payload) == False

def test_fail_missing_keyword_overlap_check():
    payload = get_base_payload()
    q1 = get_valid_question(1, "paraphrase", True)
    del q1["keyword_overlap_check"]
    q2 = get_valid_question(2, "inference", True)
    payload["reading"]["questions"] = [q1, q2]
    payload["answers"]["reading_answers"] = [get_valid_answer(1), get_valid_answer(2)]
    
    assert run_validation(payload) == False

def test_fail_keyword_trap_ratio():
    payload = get_base_payload()
    # 2 distractors, 0 keyword traps. Ratio: 0% < 30%
    q1 = get_valid_question(1, "paraphrase", False)
    q2 = get_valid_question(2, "inference", False)
    payload["reading"]["questions"] = [q1, q2]
    payload["answers"]["reading_answers"] = [get_valid_answer(1), get_valid_answer(2)]
    
    assert run_validation(payload) == False

if __name__ == " __main__\:
