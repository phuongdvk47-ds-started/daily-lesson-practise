#!/usr/bin/env python3
import json
import sys
import argparse
from pathlib import Path

def validate_lesson_json(json_path: Path) -> bool:
    print(f"Validating JSON: {json_path}")
    if not json_path.exists():
        print(f"FAIL: File does not exist: {json_path}")
        return False

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL: Failed to parse JSON: {e}")
        return False

    errors = []

    # 1. Check basic structure
    required_sections = ["lesson_meta", "source", "reading", "vocabulary", "grammar", "writing", "answers"]
    for sec in required_sections:
        if sec not in data:
            errors.append(f"FAIL: Missing top-level section: {sec}")
    
    if errors:
        for err in errors:
            print(err)
        return False

    # Meta variables
    meta = data["lesson_meta"]
    req_meta = ["lesson_id", "day", "level", "theme", "topic", "specific_topic", "reading_question_count", "vocabulary_count", "grammar_question_count", "writing_task_count"]
    for m in req_meta:
        if m not in meta:
            errors.append(f"FAIL: Missing metadata field: lesson_meta.{m}")
    
    if errors:
        for err in errors:
            print(err)
        return False

    day = meta["day"]
    level = meta["level"]
    target_rq = meta["reading_question_count"]
    target_vc = meta["vocabulary_count"]
    target_gq = meta["grammar_question_count"]
    target_wt = meta["writing_task_count"]

    # 2. Validate source
    source = data["source"]
    if source.get("status") != "verified":
        errors.append(f"FAIL: Source status is not verified. Current: {source.get('status')}")
    if not source.get("source_title"):
        errors.append("FAIL: Source missing source_title")
    if not source.get("verified_url"):
        errors.append("FAIL: Source missing verified_url")

    # 3. Validate reading
    reading = data["reading"]
    if "passage" not in reading:
        errors.append("FAIL: Missing reading.passage")
    else:
        passage = reading["passage"]
        if not passage.get("title"):
            errors.append("FAIL: Missing reading.passage.title")
        if not passage.get("paragraphs"):
            errors.append("FAIL: Missing reading.passage.paragraphs")
        else:
            paragraphs = passage["paragraphs"]
            for idx, p in enumerate(paragraphs):
                if "id" not in p or "text" not in p:
                    errors.append(f"FAIL: Paragraph at index {idx} missing id or text")

    # Reading questions count
    rqs = reading.get("questions", [])
    if len(rqs) != target_rq:
        errors.append(f"FAIL: Reading questions count mismatch. Expected {target_rq}, got {len(rqs)}")

    # 4. Validate evidence quotes in passage
    passage_text = ""
    if "passage" in reading and "paragraphs" in reading["passage"]:
        passage_text = " ".join([p.get("text", "") for p in reading["passage"]["paragraphs"]])

    for idx, q in enumerate(rqs):
        q_id = q.get("id")
        if not q_id:
            errors.append(f"FAIL: Reading question at index {idx} missing id")
            continue
        
        # Check required question fields
        req_q_fields = ["type", "question", "correct_answer", "evidence_paragraph", "evidence_quote", "rationale_vi"]
        for f in req_q_fields:
            if f not in q:
                errors.append(f"FAIL: Reading question {q_id} missing field: {f}")
        
        # Match quote
        quote = q.get("evidence_quote", "").strip()
        if quote:
            # Simple substring match (case insensitive, ignoring extra whitespace)
            clean_passage = " ".join(passage_text.split()).lower()
            clean_quote = " ".join(quote.split()).lower()
            
            # Remove punctuation for fuzzy comparison if exact fails
            punc = '.,?!"\';:()[]{}'
            clean_passage_no_punc = "".join(c for c in clean_passage if c not in punc)
            clean_quote_no_punc = "".join(c for c in clean_quote if c not in punc)

            if clean_quote not in clean_passage and clean_quote_no_punc not in clean_passage_no_punc:
                errors.append(f"FAIL: reading.questions[{idx}] (id={q_id}) evidence_quote not found in passage. Quote: '{quote[:50]}...'")

    # 5. Validate vocabulary
    vocab = data["vocabulary"]
    vocab_items = vocab.get("items", [])
    if len(vocab_items) != target_vc:
        errors.append(f"FAIL: Vocabulary items count mismatch. Expected {target_vc}, got {len(vocab_items)}")

    for idx, vi in enumerate(vocab_items):
        vi_id = vi.get("id")
        req_vi_fields = ["term", "ipa", "part_of_speech", "definition_en", "meaning_vi", "example", "source"]
        for f in req_vi_fields:
            if f not in vi:
                errors.append(f"FAIL: Vocabulary item {vi_id or idx} missing field: {f}")

    # Vocab recycled items presence
    recycled_items = vocab.get("recycled_items", [])
    if len(recycled_items) != 3:
        print(f"WARNING: Recycled vocabulary count should ideally be 3. Got {len(recycled_items)}")

    # Vocab Quizlet check
    quizlet = vocab.get("quizlet", {})
    if "section_1_simple" not in quizlet or "section_2_detailed" not in quizlet:
        errors.append("FAIL: Missing vocabulary.quizlet simple or detailed sections")
    
    # Vocab checker items check
    checker_items = vocab.get("vocab_checker_items", [])
    if not checker_items:
        errors.append("FAIL: Missing vocabulary.vocab_checker_items")

    # 6. Validate grammar
    grammar = data["grammar"]
    gqs = grammar.get("questions", [])
    if len(gqs) != target_gq:
        errors.append(f"FAIL: Grammar questions count mismatch. Expected {target_gq}, got {len(gqs)}")

    # Grammar questions numbering starting from 1 continuously
    for idx, g in enumerate(gqs):
        g_id = g.get("id")
        if g_id != idx + 1:
            errors.append(f"FAIL: Grammar questions must be numbered sequentially from 1. Index {idx} has id {g_id}")
        
        req_g_fields = ["type", "question", "correct_answer", "explanation_vi"]
        for f in req_g_fields:
            if f not in g:
                errors.append(f"FAIL: Grammar question {g_id} missing field: {f}")

    # Grammar detailed guide & mistakes checks
    if not grammar.get("guide"):
        errors.append("FAIL: Missing grammar.guide")
    else:
        for idx, gd in enumerate(grammar["guide"]):
            if "heading" not in gd or "content" not in gd:
                errors.append(f"FAIL: grammar.guide[{idx}] missing heading or content")
            elif not gd["heading"].startswith("####"):
                errors.append(f"FAIL: grammar.guide[{idx}] heading '{gd['heading']}' should start with #### for card compilation")

    if "common_mistakes" not in grammar:
        errors.append("FAIL: Missing grammar.common_mistakes")
    else:
        for idx, cm in enumerate(grammar["common_mistakes"]):
            req_cm = ["trap", "wrong_example", "correct_version", "why_it_matters"]
            for f in req_cm:
                if f not in cm:
                    errors.append(f"FAIL: grammar.common_mistakes[{idx}] missing field: {f}")

    # 7. Validate writing tasks
    writing = data["writing"]
    wts = writing.get("tasks", [])
    if len(wts) != target_wt:
        errors.append(f"FAIL: Writing tasks count mismatch. Expected {target_wt}, got {len(wts)}")

    for idx, w in enumerate(wts):
        w_id = w.get("id")
        req_w_fields = ["task_type", "prompt", "target_length", "focus_skill", "useful_language", "success_criteria", "visual_data"]
        for f in req_w_fields:
            if f not in w:
                errors.append(f"FAIL: Writing task {w_id or idx} missing field: {f}")
        
        vdata = w.get("visual_data", {})
        if "type" not in vdata or "content" not in vdata:
            errors.append(f"FAIL: Writing task {w_id or idx} visual_data missing type or content")

    # 8. Validate answers completeness
    answers = data["answers"]
    reading_ans = answers.get("reading_answers", [])
    grammar_ans = answers.get("grammar_answers", [])
    writing_guidance = answers.get("writing_guidance", [])
    review_bridge = answers.get("review_bridge", [])

    if len(reading_ans) != len(rqs):
        errors.append(f"FAIL: Answers list count mismatch for Reading. Expected {len(rqs)}, got {len(reading_ans)}")
    if len(grammar_ans) != len(gqs):
        errors.append(f"FAIL: Answers list count mismatch for Grammar. Expected {len(gqs)}, got {len(grammar_ans)}")
    if len(writing_guidance) != len(wts):
        errors.append(f"FAIL: Answers list count mismatch for Writing. Expected {len(wts)}, got {len(writing_guidance)}")
    if len(review_bridge) != 3:
        errors.append(f"FAIL: Review bridge answers must contain exactly 3 items. Got {len(review_bridge)}")

    # Print results
    if errors:
        print(f"\nValidation failed with {len(errors)} error(s):")
        for err in errors:
            print(f" - {err}")
        return False
    else:
        print("\nValidation PASSED successfully! Payload is 100% compliant.")
        return True

def main():
    parser = argparse.ArgumentParser(description="Validate IELTS daily lesson JSON payload.")
    parser.add_argument("json_file", type=str, help="Path to the lesson_source.json file.")
    args = parser.parse_args()

    json_path = Path(args.json_file)
    success = validate_lesson_json(json_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
