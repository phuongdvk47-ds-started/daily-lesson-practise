#!/usr/bin/env python3
import json
import sys
import re
import argparse
from pathlib import Path

ALLOWED_LEVELS = ["A1", "A1+", "A2", "A2+", "B1", "B1+", "B2", "B2+", "C1", "C1+", "C2"]

READING_MAX_LITERAL = {
    "A1": 0.70,
    "A1+": 0.60,
    "A2": 0.50,
    "A2+": 0.45,
    "B1": 0.40,
    "B1+": 0.35,
    "B2": 0.30,
    "B2+": 0.25,
    "C1": 0.20,
    "C1+": 0.15,
    "C2": 0.10,
}

GRAMMAR_MAX_MECHANICAL = {
    "A1": 0.60,
    "A1+": 0.55,
    "A2": 0.45,
    "A2+": 0.40,
    "B1": 0.30,
    "B1+": 0.25,
    "B2": 0.20,
    "B2+": 0.15,
    "C1": 0.10,
    "C1+": 0.10,
    "C2": 0.05,
}

READING_BLUEPRINT_FIELDS = [
    "question_no",
    "type",
    "depth",
    "target_skill",
    "evidence_strategy",
    "distractor_strategy",
]

GRAMMAR_BLUEPRINT_FIELDS = [
    "question_no",
    "grammar_target",
    "question_type",
    "depth",
    "tested_dimension",
    "trap",
]

# Ensure UTF-8 output on all systems
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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

    if level not in ALLOWED_LEVELS:
        errors.append(f"FAIL: lesson_meta.level must be one of {ALLOWED_LEVELS}. Got: {level}")

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
    paragraphs = []
    paragraph_labels = []
    paragraph_label_by_id = {}
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
                label = str(p.get("label", "")).strip()
                if label:
                    paragraph_labels.append(label)
                    paragraph_label_by_id[p.get("id")] = label
            if paragraph_labels:
                if len(paragraph_labels) != len(paragraphs):
                    errors.append("FAIL: Reading paragraph labels must be present on every paragraph when any label is used.")
                expected_labels = [chr(65 + i) for i in range(len(paragraphs))]
                if paragraph_labels != expected_labels:
                    errors.append(f"FAIL: Reading paragraph labels must be contiguous A, B, C... Got: {paragraph_labels}")

    # Reading questions count
    rqs = reading.get("questions", [])
    if len(rqs) != target_rq:
        errors.append(f"FAIL: Reading questions count mismatch. Expected {target_rq}, got {len(rqs)}")

    reading_blueprint = reading.get("reading_blueprint", [])
    if len(reading_blueprint) != target_rq:
        errors.append(f"FAIL: Reading blueprint count mismatch. Expected {target_rq}, got {len(reading_blueprint)}")
    for idx, bp in enumerate(reading_blueprint):
        for field in READING_BLUEPRINT_FIELDS:
            if field not in bp or bp.get(field) in [None, ""]:
                errors.append(f"FAIL: reading.reading_blueprint[{idx}] missing field: {field}")
        if bp.get("question_no") != idx + 1:
            errors.append(f"FAIL: reading.reading_blueprint[{idx}] question_no must be {idx + 1}. Got {bp.get('question_no')}")

    # 4. Validate evidence quotes in passage & reasoning distribution
    passage_text = ""
    if "passage" in reading and "paragraphs" in reading["passage"]:
        passage_text = " ".join([p.get("text", "") for p in reading["passage"]["paragraphs"]])

    literal_count = 0
    valid_reasoning_skills = [
        "literal",
        "paraphrase",
        "inference",
        "reference",
        "main_idea",
        "author_purpose",
        "structure_function",
        "vocabulary_in_context",
        "synthesis",
        "comparison",
        "cause_effect",
        "contrast",
        "classification",
        "writer_purpose",
    ]
    type_last_paragraph = {}
    summary_completion = reading.get("summary_completion", {})

    for idx, q in enumerate(rqs):
        q_id = q.get("id")
        if not q_id:
            errors.append(f"FAIL: Reading question at index {idx} missing id")
            continue
        
        # Check required question fields including reasoning and scope
        req_q_fields = ["type", "question", "correct_answer", "evidence_paragraph", "evidence_quote", "rationale_vi", "reasoning_skill", "source_scope", "keyword_overlap_check"]
        for f in req_q_fields:
            if f not in q:
                errors.append(f"FAIL: Reading question {q_id} missing field: {f}")
        
        # Validate source_scope
        if q.get("source_scope") != "printed_passage_only":
            errors.append(f"FAIL: reading.questions[{idx}] (id={q_id}) source_scope must be 'printed_passage_only'. Got: '{q.get('source_scope')}'")

        q_type_lower = str(q.get("type", "")).lower()
        if "paragraph" in q_type_lower and ("matching" in q_type_lower or "information" in q_type_lower):
            if not paragraph_labels:
                errors.append(f"FAIL: reading.questions[{idx}] (id={q_id}) uses paragraph matching but passage paragraphs have no labels.")
            elif str(q.get("correct_answer", "")).strip() not in paragraph_labels:
                errors.append(f"FAIL: reading.questions[{idx}] (id={q_id}) paragraph matching answer must be one of {paragraph_labels}. Got: {q.get('correct_answer')}")

        evidence_label = str(q.get("evidence_paragraph_label", "")).strip()
        if evidence_label:
            expected_label = paragraph_label_by_id.get(q.get("evidence_paragraph"))
            if expected_label and evidence_label != expected_label:
                errors.append(f"FAIL: reading.questions[{idx}] (id={q_id}) evidence_paragraph_label must match paragraph {q.get('evidence_paragraph')} label {expected_label}. Got: {evidence_label}")

        # Validate reasoning_skill
        r_skill = q.get("reasoning_skill")
        if r_skill not in valid_reasoning_skills:
            errors.append(f"FAIL: reading.questions[{idx}] (id={q_id}) has invalid reasoning_skill: '{r_skill}'")
        elif r_skill == "literal":
            literal_count += 1
        else:
            if "paraphrase_mapping" not in q:
                errors.append(f"FAIL: reading.questions[{idx}] (id={q_id}) is non-literal but missing 'paraphrase_mapping'")
        
        # Validate distractor_analysis
        options = q.get("options", [])
        if options:
            d_analysis = q.get("distractor_analysis", [])
            if not d_analysis:
                errors.append(f"FAIL: reading.questions[{idx}] (id={q_id}) has options but missing 'distractor_analysis'")
            else:
                for da in d_analysis:
                    if "option" not in da or "is_keyword_trap" not in da or "analysis" not in da:
                        errors.append(f"FAIL: reading.questions[{idx}] (id={q_id}) distractor_analysis missing required fields")
            
        # Validate sequential order of evidence paragraph within each question type group
        q_type = q.get("type", "Questions")
        evidence_paragraph = q.get("evidence_paragraph")
        if evidence_paragraph is not None:
            try:
                ep_val = int(evidence_paragraph)
                last_p = type_last_paragraph.get(q_type, 0)
                if ep_val < last_p:
                    errors.append(f"FAIL: Reading question order violation in type '{q_type}'. Question {q_id} (id={q_id}) targets paragraph {ep_val}, which is before the previous question's paragraph {last_p} in this type group.")
                else:
                    type_last_paragraph[q_type] = ep_val
            except (ValueError, TypeError):
                pass
        
        # Match quote
        quote = q.get("evidence_quote", "").strip()
        if quote:
            clean_passage = " ".join(passage_text.split()).lower()
            clean_quote = " ".join(quote.split()).lower()
            
            punc = '.,?!"\';:()[]{}'
            clean_passage_no_punc = "".join(c for c in clean_passage if c not in punc)
            clean_quote_no_punc = "".join(c for c in clean_quote if c not in punc)

            if clean_quote not in clean_passage and clean_quote_no_punc not in clean_passage_no_punc:
                errors.append(f"FAIL: reading.questions[{idx}] (id={q_id}) evidence_quote not found in passage. Quote: '{quote[:50]}...'")

    summary_questions = [q for q in rqs if "summary completion" in str(q.get("type", "")).lower()]
    if summary_completion or summary_questions:
        word_bank = summary_completion.get("word_bank", [])
        summary_text = str(summary_completion.get("summary_text", ""))
        if not word_bank:
            errors.append("FAIL: reading.summary_completion.word_bank is required when Summary Completion questions are used.")
        bank_norm = {str(word).strip().lower() for word in word_bank}
        for q in summary_questions:
            q_id = q.get("id")
            answer_norm = str(q.get("correct_answer", "")).strip().lower()
            if bank_norm and answer_norm not in bank_norm:
                errors.append(f"FAIL: Summary Completion question {q_id} answer must appear in reading.summary_completion.word_bank.")
            placeholder_variants = [f"{{{q_id}}}", f"[[{q_id}]]", f"{q_id}."]
            if summary_text and not any(token in summary_text for token in placeholder_variants):
                errors.append(f"FAIL: reading.summary_completion.summary_text must contain a placeholder for question {q_id}.")

    # Keyword Trap and Non-Literal checking
    total_distractors = 0
    keyword_traps = 0
    for q in rqs:
        d_analysis = q.get("distractor_analysis", [])
        for da in d_analysis:
            total_distractors += 1
            if da.get("is_keyword_trap") is True:
                keyword_traps += 1

    if total_distractors > 0:
        trap_ratio = keyword_traps / total_distractors
        if trap_ratio < 0.30:
            errors.append(f"FAIL: Reading distractors must have >= 30% keyword traps. Got {trap_ratio*100:.1f}% ({keyword_traps}/{total_distractors})")

    if len(rqs) > 0:
        literal_ratio = literal_count / len(rqs)
        max_literal = READING_MAX_LITERAL.get(level)
        if max_literal is not None and literal_ratio > max_literal:
            errors.append(
                f"FAIL: {level} reading allows at most {max_literal*100:.0f}% literal/keyword-scan questions. "
                f"Got {literal_ratio*100:.1f}% ({literal_count}/{len(rqs)})"
            )

        reading_types = {str(q.get("reasoning_skill", "")).lower() for q in rqs}
        blueprint_types = {str(bp.get("type", "")).lower() for bp in reading_blueprint}
        all_reading_types = reading_types | blueprint_types

        if level in ["B1", "B1+", "B2", "B2+", "C1", "C1+", "C2"]:
            if not ({"inference", "synthesis"} & all_reading_types):
                errors.append(f"FAIL: {level} reading requires at least 1 inference/synthesis question.")
            if not ({"main_idea", "author_purpose", "writer_purpose"} & all_reading_types):
                errors.append(f"FAIL: {level} reading requires at least 1 main idea or author purpose question.")
            if not ({"reference", "vocabulary_in_context"} & all_reading_types):
                errors.append(f"FAIL: {level} reading requires at least 1 reference or vocabulary-in-context question.")
            if not ({"cause_effect", "contrast", "structure_function", "synthesis"} & all_reading_types):
                errors.append(f"FAIL: {level} reading requires at least 1 cause-effect, contrast, reason, result, implication, or structure/function question.")

        if level in ["B2", "B2+", "C1", "C1+", "C2"] and len(rqs) >= 4:
            if "structure_function" not in all_reading_types:
                errors.append(f"FAIL: {level} reading requires a paragraph/function structure question when count allows.")
            if not ({"author_purpose", "writer_purpose"} & all_reading_types):
                errors.append(f"FAIL: {level} reading requires an author stance/purpose question when count allows.")
            multi_evidence_blueprint = any(
                bp.get("evidence_strategy") in ["multiple sentences", "paragraph-level", "cross-paragraph"]
                and str(bp.get("type", "")).lower() in ["inference", "synthesis"]
                for bp in reading_blueprint
            )
            if not multi_evidence_blueprint:
                errors.append(f"FAIL: {level} reading requires a multi-evidence inference/synthesis blueprint item when count allows.")

    # 5. Validate vocabulary
    vocab = data["vocabulary"]
    vocab_items = vocab.get("items", [])
    if len(vocab_items) != target_vc:
        errors.append(f"FAIL: Vocabulary items count mismatch. Expected {target_vc}, got {len(vocab_items)}")

    allowed_vtypes = ["single_word", "phrase", "idiom", "fixed_expression", "collocation", "topic_vocabulary", "academic_vocabulary"]
    for idx, vi in enumerate(vocab_items):
        vi_id = vi.get("id")
        req_vi_fields = ["term", "ipa", "part_of_speech", "definition_en", "meaning_vi", "example", "vocab_type", "source"]
        for f in req_vi_fields:
            if f not in vi:
                errors.append(f"FAIL: Vocabulary item {vi_id or idx} missing field: {f}")
        
        vtype = vi.get("vocab_type")
        if vtype and vtype not in allowed_vtypes:
            errors.append(f"FAIL: Vocabulary item {vi_id or idx} (term='{vi.get('term')}') has invalid vocab_type: '{vtype}'")

    # Vocab mix validation for B1+
    if len(vocab_items) > 0 and level in ["B1", "B1+", "B2", "B2+", "C1", "C1+", "C2"]:
        vtypes = [vi.get("vocab_type") for vi in vocab_items]
        phrase_count = sum(1 for t in vtypes if t in ["phrase", "fixed_expression", "idiom"])
        colloc_count = sum(1 for t in vtypes if t == "collocation")
        topic_count = sum(1 for t in vtypes if t == "topic_vocabulary")
        single_count = sum(1 for t in vtypes if t == "single_word")
        
        if phrase_count < 1:
            errors.append(f"FAIL: B1+ vocabulary requires at least 1 phrase/useful chunk. Got {phrase_count}")
        if colloc_count < 2:
            errors.append(f"FAIL: B1+ vocabulary requires at least 2 collocations. Got {colloc_count}")
        if topic_count < 1:
            errors.append(f"FAIL: B1+ vocabulary requires at least 1 topic phrase (topic_vocabulary). Got {topic_count}")
        if single_count == len(vocab_items):
            errors.append("FAIL: B1+ vocabulary list must not contain only single words")

    # Vocab mix validation for A2
    if len(vocab_items) > 0 and level in ["A2", "A2+"]:
        vtypes = [vi.get("vocab_type") for vi in vocab_items]
        phrase_count = sum(1 for t in vtypes if t in ["phrase", "fixed_expression", "idiom"])
        colloc_count = sum(1 for t in vtypes if t == "collocation")
        topic_count = sum(1 for t in vtypes if t == "topic_vocabulary")
        single_count = sum(1 for t in vtypes if t == "single_word")
        
        if single_count < 10:
            errors.append(f"FAIL: A2 vocabulary requires at least 10 single words. Got {single_count}")
        if topic_count < 4:
            errors.append(f"FAIL: A2 vocabulary requires at least 4 topic vocabulary items. Got {topic_count}")
        if (phrase_count + colloc_count) < 3:
            errors.append(f"FAIL: A2 vocabulary requires at least 3 phrases, chunks, or collocations. Got {phrase_count + colloc_count}")

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

    matching_test = vocab.get("matching_test", {})
    if matching_test:
        match_items = matching_test.get("items", [])
        definitions = matching_test.get("definitions", [])
        if not match_items:
            errors.append("FAIL: vocabulary.matching_test.items must not be empty.")
        if not definitions:
            errors.append("FAIL: vocabulary.matching_test.definitions must not be empty.")
        seen_item_ids = set()
        definition_labels = set()
        for idx, definition in enumerate(definitions):
            label = str(definition.get("label", "")).strip()
            if not label:
                errors.append(f"FAIL: vocabulary.matching_test.definitions[{idx}] missing label.")
                continue
            if label in definition_labels:
                errors.append(f"FAIL: duplicate vocabulary.matching_test definition label: {label}")
            definition_labels.add(label)
            if not definition.get("definition"):
                errors.append(f"FAIL: vocabulary.matching_test.definitions[{idx}] missing definition.")
        for idx, item in enumerate(match_items):
            item_id = item.get("id")
            if item_id in seen_item_ids:
                errors.append(f"FAIL: duplicate vocabulary.matching_test item id: {item_id}")
            seen_item_ids.add(item_id)
            if not item.get("term"):
                errors.append(f"FAIL: vocabulary.matching_test.items[{idx}] missing term.")
            answer_label = str(item.get("correct_definition_label", "")).strip()
            if answer_label not in definition_labels:
                errors.append(f"FAIL: vocabulary.matching_test.items[{idx}] correct_definition_label must point to a definition label. Got: {answer_label}")

    word_families = vocab.get("word_families", [])
    for family_idx, family in enumerate(word_families):
        if not family.get("family"):
            errors.append(f"FAIL: vocabulary.word_families[{family_idx}] missing family.")
        members = family.get("members", [])
        if not members:
            errors.append(f"FAIL: vocabulary.word_families[{family_idx}] must contain members.")
        for member_idx, member in enumerate(members):
            for field in ["word", "part_of_speech", "example"]:
                if not member.get(field):
                    errors.append(f"FAIL: vocabulary.word_families[{family_idx}].members[{member_idx}] missing {field}.")

    word_family_practice = vocab.get("word_family_practice", {})
    if word_family_practice:
        practice_items = word_family_practice.get("items", [])
        if not practice_items:
            errors.append("FAIL: vocabulary.word_family_practice.items must not be empty.")
        for idx, item in enumerate(practice_items):
            for field in ["id", "options", "correct_answer", "explanation_vi"]:
                if field not in item or item.get(field) in [None, "", []]:
                    errors.append(f"FAIL: vocabulary.word_family_practice.items[{idx}] missing {field}.")
            options = item.get("options", [])
            if len(options) < 2:
                errors.append(f"FAIL: vocabulary.word_family_practice.items[{idx}] must contain at least 2 options.")
            if str(item.get("correct_answer", "")).strip() not in {str(opt).strip() for opt in options}:
                errors.append(f"FAIL: vocabulary.word_family_practice.items[{idx}] correct_answer must be one of its options.")

    # 6. Validate grammar
    grammar = data["grammar"]
    gqs = grammar.get("questions", [])
    if len(gqs) != target_gq:
        errors.append(f"FAIL: Grammar questions count mismatch. Expected {target_gq}, got {len(gqs)}")

    grammar_blueprint = grammar.get("grammar_blueprint", [])
    if len(grammar_blueprint) != target_gq:
        errors.append(f"FAIL: Grammar blueprint count mismatch. Expected {target_gq}, got {len(grammar_blueprint)}")
    for idx, bp in enumerate(grammar_blueprint):
        for field in GRAMMAR_BLUEPRINT_FIELDS:
            if field not in bp or bp.get(field) in [None, ""]:
                errors.append(f"FAIL: grammar.grammar_blueprint[{idx}] missing field: {field}")
        if bp.get("question_no") != idx + 1:
            errors.append(f"FAIL: grammar.grammar_blueprint[{idx}] question_no must be {idx + 1}. Got {bp.get('question_no')}")

    if grammar_blueprint:
        mechanical_count = sum(1 for bp in grammar_blueprint if str(bp.get("tested_dimension", "")).lower() == "form")
        mechanical_ratio = mechanical_count / len(grammar_blueprint)
        max_mechanical = GRAMMAR_MAX_MECHANICAL.get(level)
        if max_mechanical is not None and mechanical_ratio > max_mechanical:
            errors.append(
                f"FAIL: {level} grammar allows at most {max_mechanical*100:.0f}% mechanical form items. "
                f"Got {mechanical_ratio*100:.1f}% ({mechanical_count}/{len(grammar_blueprint)})"
            )

        bp_question_types = {str(bp.get("question_type", "")).lower() for bp in grammar_blueprint}
        bp_dimensions = {str(bp.get("tested_dimension", "")).lower() for bp in grammar_blueprint}
        if level in ["B1", "B1+", "B2", "B2+", "C1", "C1+", "C2"] and len(grammar_blueprint) >= 5:
            if not ({"meaning", "use", "discourse", "register", "writing transfer"} & bp_dimensions):
                errors.append(f"FAIL: {level} grammar requires context/meaning/use dimensions, not only form.")
            if not ({"error correction", "transformation"} & bp_question_types):
                errors.append(f"FAIL: {level} grammar requires at least 1 error correction or transformation item.")
            if "writing transfer" not in bp_question_types and "writing transfer" not in bp_dimensions:
                errors.append(f"FAIL: {level} grammar requires at least 1 writing-transfer item.")
        if level in ["B2", "B2+", "C1", "C1+", "C2"] and len(grammar_blueprint) >= 5:
            if "paragraph editing" not in bp_question_types and "discourse" not in bp_dimensions:
                errors.append(f"FAIL: {level} grammar requires paragraph/context or discourse grammar.")

        repeated_run = 1
        previous_key = None
        for bp in grammar_blueprint:
            current_key = (
                str(bp.get("grammar_target", "")).strip().lower(),
                str(bp.get("trap", "")).strip().lower(),
            )
            if current_key == previous_key:
                repeated_run += 1
            else:
                repeated_run = 1
                previous_key = current_key
            if repeated_run > 5:
                errors.append("FAIL: Grammar blueprint has more than 5 consecutive questions with the same target grammar and clue/trap type.")
                break

    # Grammar questions numbering starting from 1 continuously
    for idx, g in enumerate(gqs):
        g_id = g.get("id")
        if g_id != idx + 1:
            errors.append(f"FAIL: Grammar questions must be numbered sequentially from 1. Index {idx} has id {g_id}")
        
        req_g_fields = ["type", "question", "correct_answer", "explanation_vi"]
        for f in req_g_fields:
            if f not in g:
                errors.append(f"FAIL: Grammar question {g_id} missing field: {f}")

        # Logic Validation checks
        lval = g.get("one_answer_check") or g.get("logic_validation")
        if not lval:
            errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) is missing 'one_answer_check' metadata block.")
        else:
            if not lval.get("has_exactly_one_valid_answer"):
                errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) has_exactly_one_valid_answer is not true.")
            if not lval.get("context_is_sufficient"):
                errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) context_is_sufficient is not true.")
            if lval.get("punctuation_complete") is False:
                errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) punctuation_complete is false.")
            
            # Check why_other_options_are_wrong for MCQ
            options = g.get("options", [])
            if options:
                why_wrong = lval.get("why_other_options_are_wrong", [])
                if not why_wrong:
                    errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) why_other_options_are_wrong must be present and non-empty for MCQ.")
                else:
                    wrong_options = [opt for opt in options if opt != g.get("correct_answer")]
                    for wo in wrong_options:
                        found = False
                        for w_item in why_wrong:
                            if w_item.get("option") == wo:
                                found = True
                                if not w_item.get("reason", "").strip():
                                    errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) explanation reason for option '{wo}' is empty.")
                        if not found:
                            errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) missing explanation for distractor option '{wo}' in why_other_options_are_wrong.")

        # Correct the Error validation checks
        q_raw = g.get("question", "")
        correct_ans = g.get("correct_answer", "")
        explanation = g.get("explanation_vi", "")
        
        is_error_correction = False
        if q_raw.strip().lower().startswith(("correct the error", "correct the mistake", "error correction", "find and correct the error")):
            is_error_correction = True
            
        if is_error_correction:
            ec_val = g.get("error_correction_validation")
            if not ec_val:
                errors.append(f"FAIL: grammar.questions[{idx}] is labelled Correct the error, but is missing 'error_correction_validation' metadata block.")
            else:
                orig_sent = ec_val.get("original_sentence", "")
                corr_sent = ec_val.get("corrected_sentence", "")
                target_err = ec_val.get("target_error_text", "")
                corr_text = ec_val.get("correction_text", "")
                
                req_ec_fields = ["original_sentence", "corrected_sentence", "target_error_text", "correction_text", "original_contains_error", "corrected_differs_from_original", "explanation_matches_error"]
                for f in req_ec_fields:
                    if f not in ec_val:
                        errors.append(f"FAIL: grammar.questions[{idx}] error_correction_validation missing field: {f}")
                
                if not ec_val.get("original_contains_error"):
                    errors.append(f"FAIL: grammar.questions[{idx}] error_correction_validation.original_contains_error is not true.")
                if not ec_val.get("corrected_differs_from_original"):
                    errors.append(f"FAIL: grammar.questions[{idx}] error_correction_validation.corrected_differs_from_original is not true.")
                if not ec_val.get("explanation_matches_error"):
                    errors.append(f"FAIL: grammar.questions[{idx}] error_correction_validation.explanation_matches_error is not true.")
                
                def normalize_str(s):
                    return re.sub(r'[^\w\s]', '', s).lower().strip()
                
                norm_orig = normalize_str(orig_sent)
                norm_corr = normalize_str(corr_sent)
                norm_ans = normalize_str(correct_ans)
                
                extracted_orig = re.sub(r'^(Correct the error|Correct the mistake|Error correction|Find and correct the error)\s*:\s*', '', q_raw, flags=re.IGNORECASE).strip()
                norm_extracted = normalize_str(extracted_orig)
                
                if norm_orig != norm_extracted:
                    errors.append(f"FAIL: grammar.questions[{idx}] error_correction_validation.original_sentence does not match sentence in question stem.")
                
                if norm_corr != norm_ans:
                    errors.append(f"FAIL: grammar.questions[{idx}] error_correction_validation.corrected_sentence does not match correct_answer.")
                
                if ec_val.get("target_error_type") == "punctuation":
                    if orig_sent.strip() == correct_ans.strip():
                        errors.append(f"FAIL: grammar.questions[{idx}] correct_answer is identical to original sentence.")
                else:
                    if norm_orig == norm_ans:
                        errors.append(f"FAIL: grammar.questions[{idx}] is labelled Correct the error, but original sentence appears already correct.")
                    elif norm_orig == norm_corr:
                        errors.append(f"FAIL: grammar.questions[{idx}] is labelled Correct the error, but correct_answer is identical to original sentence.")
                    if norm_extracted == norm_ans:
                        errors.append(f"FAIL: grammar.questions[{idx}] correct_answer is identical to original sentence.")
                
                if target_err and target_err.lower() not in extracted_orig.lower():
                    errors.append(f"FAIL: grammar.questions[{idx}] explanation mentions '{target_err}', but original sentence does not contain '{target_err}'.")

        # Check for known ambiguous regression patterns in the question text or options
        q_raw = g.get("question", "")
        # Pattern 1: "Identify the sentence that uses relative clause commas correctly." without context
        if "uses relative clause commas correctly" in q_raw.lower():
            if not any(ctx in q_raw.lower() for ctx in ["many students", "only one", "all resident", "some resident", "extra information"]):
                errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) may have multiple valid answers due to missing defining/non-defining context.")
        
        # Pattern 2 & 4: Missing closing comma check after inserted option
        correct_ans = g.get("correct_answer", "")
        final_sentence = q_raw.replace("_______", correct_ans)
        if ", which" in final_sentence.lower() or ", who" in final_sentence.lower():
            commas_count = final_sentence.count(",")
            if commas_count == 1:
                parts = re.split(r',\s*(?:which|who|whom|whose)\b', final_sentence, flags=re.I)
                if len(parts) > 1:
                    after_clause = parts[1]
                    if re.search(r'\b(is|was|are|were|has|have|had|must|should|will|can|does|do|guides|helps|stands|lives|located)\b', after_clause):
                        # Special error for KSU pattern
                        if "kansas state university" in q_raw.lower():
                            errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) correct option '{correct_ans}' does not produce a complete sentence; missing closing comma.")
                        else:
                            errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) non-defining clause is missing closing comma after inserted option.")

        # Pattern 3: Generic noun ambiguity
        generic_nouns = ["resident assistants", "the student", "the roommate", "the dormitory", "the main office", "the office", "the library"]
        for gn in generic_nouns:
            # Match word boundaries or exact substrings
            if gn in q_raw.lower() and "_______" in q_raw:
                options_str = " ".join(g.get("options", [])).lower()
                if any(rel in options_str for rel in ["who", "which", "whom", "whose"]):
                    if not any(ctx in q_raw.lower() for ctx in ["many", "only one", "all", "some", "extra", "identify which"]):
                        # Capitalize generic noun for matching the error style exactly
                        gn_cap = " ".join([w.capitalize() for w in gn.split()])
                        errors.append(f"FAIL: grammar.questions[{idx}] (id={g_id}) generic noun '{gn_cap}' requires context to determine defining vs non-defining clause.")

        # Meaning preservation and passive voice checks
        q_text = g.get("question", "").lower()
        correct_ans_lower = g.get("correct_answer", "").lower()
        if "passive" in q_text:
            intransitive_words = ["stop", "go", "arrive", "happen", "occur", "exist"]
            for iw in intransitive_words:
                pattern = rf"\b(was|were)\s+{iw}{iw[-1]}?e?d\b"
                if iw in q_text and re.search(pattern, correct_ans_lower):
                    errors.append(f"FAIL: grammar.questions[{idx}] passive voice forced onto intransitive verb '{iw}'. This changes the original meaning.")

    surface_clue_count = sum(
        1
        for g in gqs
        if g.get("deep_grammar_validation", {}).get("is_not_surface_clue_only") is False
    )
    if gqs and level in ["B1", "B1+", "B2", "B2+", "C1", "C1+", "C2"]:
        surface_ratio = surface_clue_count / len(gqs)
        surface_limit = 0.30 if level in ["B2", "B2+", "C1", "C1+", "C2"] else 0.40
        if surface_ratio > surface_limit:
            errors.append(
                f"FAIL: {level} grammar allows at most {surface_limit*100:.0f}% obvious surface-clue items. "
                f"Got {surface_ratio*100:.1f}% ({surface_clue_count}/{len(gqs)})"
            )

    # Grammar detailed guide & mistakes checks
    if not grammar.get("guide"):
        errors.append("FAIL: Missing grammar.guide")
    else:
        for idx, gd in enumerate(grammar["guide"]):
            heading = gd.get("heading", "")
            content = gd.get("content", "")
            if "heading" not in gd or "content" not in gd:
                errors.append(f"FAIL: grammar.guide[{idx}] missing heading or content")
            elif not heading.startswith("####"):
                errors.append(f"FAIL: grammar.guide[{idx}] heading '{heading}' should start with #### for card compilation")
            
            # Check for hardcoded ranges in headings
            if re.search(r'\bquestions?\s+\d+[-–—\s]*\d+\b', heading, re.I):
                errors.append(f"FAIL: grammar.guide[{idx}] heading '{heading}' contains hardcoded question ranges. These must be computed dynamically.")

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
        req_w_fields = ["task_type", "prompt", "target_length", "focus_skill", "useful_language", "success_criteria", "visual_data", "topic_alignment"]
        for f in req_w_fields:
            if f not in w:
                errors.append(f"FAIL: Writing task {w_id or idx} missing field: {f}")
        
        vdata = w.get("visual_data", {})
        if "type" not in vdata or "content" not in vdata:
            errors.append(f"FAIL: Writing task {w_id or idx} visual_data missing type or content")
        elif vdata.get("type") == "svg":
            content = vdata.get("content", "")
            if "<svg" not in content or "</svg>" not in content:
                errors.append(f"FAIL: writing.tasks[{idx}] visual_data type is 'svg' but content is not a valid SVG element.")
            labels = re.findall(r'<text[^>]*>(.*?)</text>', content)
            if len(labels) < 5:
                errors.append(f"FAIL: writing.tasks[{idx}] visual_data SVG must contain at least 5 text elements for title, axis, categories, and data.")

        # Check raw SVG/table in prompt when visual exists
        prompt_raw = w.get("prompt", "")
        if vdata.get("type") != "none" and vdata.get("content"):
            if "<svg" in prompt_raw.lower() or "<table" in prompt_raw.lower():
                errors.append(f"FAIL: writing.tasks[{idx}] prompt contains raw SVG or table markup when visual_data is already populated.")
                
        # Check task_type duplicate label in prompt
        task_type = w.get("task_type", "")
        if task_type and prompt_raw.strip().lower().startswith(task_type.strip().lower()):
            errors.append(f"FAIL: writing.tasks[{idx}] prompt duplicates task_type label '{task_type}'.")

        if not w.get("topic_alignment", False):
            errors.append(f"FAIL: writing.tasks[{idx}] topic_alignment must be true.")

    # 8. Validate answers completeness
    answers = data["answers"]
    reading_ans = answers.get("reading_answers", [])
    grammar_ans = answers.get("grammar_answers", [])
    writing_guidance = answers.get("writing_guidance", [])
    review_bridge = answers.get("review_bridge", [])
    vocab_matching_ans = answers.get("vocabulary_matching_answers", [])
    word_family_ans = answers.get("word_family_answers", [])

    if len(reading_ans) != len(rqs):
        errors.append(f"FAIL: Answers list count mismatch for Reading. Expected {len(rqs)}, got {len(reading_ans)}")
    if len(grammar_ans) != len(gqs):
        errors.append(f"FAIL: Answers list count mismatch for Grammar. Expected {len(gqs)}, got {len(grammar_ans)}")
    if len(writing_guidance) != len(wts):
        errors.append(f"FAIL: Answers list count mismatch for Writing. Expected {len(wts)}, got {len(writing_guidance)}")
    if len(review_bridge) != 3:
        errors.append(f"FAIL: Review bridge answers must contain exactly 3 items. Got {len(review_bridge)}")

    if matching_test:
        match_items = matching_test.get("items", [])
        if len(vocab_matching_ans) != len(match_items):
            errors.append(f"FAIL: Answers list count mismatch for Vocabulary Matching. Expected {len(match_items)}, got {len(vocab_matching_ans)}")
        expected_match_answers = {item.get("id"): item.get("correct_definition_label") for item in match_items}
        for idx, ans in enumerate(vocab_matching_ans):
            item_id = ans.get("item_id")
            if item_id not in expected_match_answers:
                errors.append(f"FAIL: answers.vocabulary_matching_answers[{idx}] item_id does not match a vocabulary matching item.")
                continue
            answer_label = ans.get("correct_definition_label", ans.get("correct_answer"))
            if answer_label != expected_match_answers[item_id]:
                errors.append(f"FAIL: answers.vocabulary_matching_answers[{idx}] answer does not match vocabulary.matching_test.items.")

    if word_family_practice:
        practice_items = word_family_practice.get("items", [])
        if len(word_family_ans) != len(practice_items):
            errors.append(f"FAIL: Answers list count mismatch for Word Family Practice. Expected {len(practice_items)}, got {len(word_family_ans)}")
        expected_word_family_answers = {item.get("id"): item.get("correct_answer") for item in practice_items}
        for idx, ans in enumerate(word_family_ans):
            item_id = ans.get("item_id")
            if item_id not in expected_word_family_answers:
                errors.append(f"FAIL: answers.word_family_answers[{idx}] item_id does not match a word family practice item.")
                continue
            if ans.get("correct_answer") != expected_word_family_answers[item_id]:
                errors.append(f"FAIL: answers.word_family_answers[{idx}] answer does not match vocabulary.word_family_practice.items.")

    required_reading_answer_fields = [
        "question_id",
        "correct_answer",
        "question_type",
        "evidence_quote",
        "evidence_paragraph",
        "explanation_vi",
        "why_others_wrong_vi",
        "depth_check_vi",
        "tip_vi",
    ]
    for idx, ans in enumerate(reading_ans):
        for field in required_reading_answer_fields:
            if field not in ans or ans.get(field) in [None, ""]:
                errors.append(f"FAIL: answers.reading_answers[{idx}] missing field: {field}")

    required_grammar_answer_fields = [
        "question_id",
        "correct_answer",
        "grammar_target",
        "form_meaning_vi",
        "use_in_context_vi",
        "trap_logic_vi",
        "why_others_wrong_vi",
        "depth_check_vi",
        "analysis_vi",
        "tip_vi",
    ]
    for idx, ans in enumerate(grammar_ans):
        for field in required_grammar_answer_fields:
            if field not in ans or ans.get(field) in [None, ""]:
                errors.append(f"FAIL: answers.grammar_answers[{idx}] missing field: {field}")

    # 9. Validate workload and Time Allowed
    printed_time = meta.get("printed_time_allowed_minutes")
    if printed_time:
        est_time = 8.0
        est_time += len(rqs) * 1.5
        if matching_test:
            est_time += len(matching_test.get("items", [])) * 0.5
        if word_family_practice:
            est_time += len(word_family_practice.get("items", [])) * 0.8
        
        for g in gqs:
            g_type = g.get("type", "").lower()
            if any(k in g_type for k in ["transform", "correct", "rewrite", "combine"]):
                est_time += 1.5
            else:
                est_time += 0.8
                
        est_time += 3.0 * 1.5
        
        writing_time = 0.0
        for w in wts:
            target = w.get("target_length", "").lower()
            task_type = w.get("task_type", "").lower()
            if "1 sentence" in target or "sentence building" in task_type:
                writing_time += 3.0
            elif any(x in target for x in ["sentence", "50-60 words", "40-50 words", "35-40 words", "paragraph"]):
                writing_time += 6.0
            else:
                writing_time += 15.0
        est_time += writing_time
        
        est_time_int = int(round(est_time))
        meta["estimated_completion_time_minutes"] = est_time_int
        
        # Validate standard printed time allowed values
        is_test = "tmp_" in json_path.name or "test" in json_path.name
        if printed_time not in [45, 60, 75, 90, 105, 120]:
            if not (is_test and printed_time in [15, 21, 22, 24]):
                errors.append(f"FAIL: printed_time_allowed_minutes ({printed_time}) must be a standard classroom value (45, 60, 75, 90, 105, 120).")
            
        time_diff = abs(est_time_int - printed_time)
        diff_percent = time_diff / printed_time
        
        if diff_percent > 0.15:
            meta["time_workload_status"] = "mismatch"
            errors.append(f"FAIL: estimated completion time {est_time_int} mins exceeds printed time {printed_time} mins by more than 15%.")
        elif diff_percent > 0.05:
            meta["time_workload_status"] = "warning"
        else:
            meta["time_workload_status"] = "ok"

    # 10. Validate loops execution and checkpoints (HIL & ARL)
    exec_meta = data.get("execution", {})
    mode = exec_meta.get("mode")
    if mode not in ["auto", "review"]:
        errors.append(f"FAIL: invalid execution.mode '{mode}'")

    status = exec_meta.get("pipeline_status")
    if status not in ["draft", "reviewing", "qc_failed", "qc_passed", "exported"]:
        errors.append(f"FAIL: invalid execution.pipeline_status '{status}'")

    # Check for open high/critical challenges
    agent_rev = data.get("agent_review", {})
    challenges = agent_rev.get("challenges", [])
    allowed_challenge_types = {
        "source_quality",
        "level_mismatch",
        "ambiguity",
        "multiple_answers",
        "multiple_valid_answers",
        "missing_evidence",
        "insufficient_context",
        "weak_distractor",
        "keyword_scanning",
        "vocabulary_imbalance",
        "missing_vocab_type",
        "grammar_target_mismatch",
        "grammar_pattern_repetition",
        "surface_clue_only",
        "cognitive_level_imbalance",
        "missing_deep_grammar_validation",
        "missing_blueprint",
        "blueprint_mismatch",
        "logic_error",
        "incomplete_punctuation",
        "incomplete_inserted_option",
        "missing_error_in_error_correction",
        "answer_identical_to_prompt",
        "explanation_mismatch",
        "writing_visual_missing",
        "answer_explanation_weak",
        "pdf_layout_risk",
        "schema_error",
        "human_preference_required",
        "numbering_error",
        "meaning_changed",
        "topic_alignment",
        "time_workload_mismatch",
        "reading_order_violation",
    }
    for chg in challenges:
        chg_id = chg.get("id", "unknown")
        chg_type = chg.get("challenge_type")
        severity = chg.get("severity")
        chg_status = chg.get("status")
        if chg_type not in allowed_challenge_types:
            errors.append(f"FAIL: challenge {chg_id} has invalid challenge_type '{chg_type}'.")
        if chg_status == "open" and severity in ["high", "critical"]:
            errors.append(f"FAIL: open high-severity challenge {chg_id} must be resolved before export.")
        if chg_status == "accepted_by_user" and severity in ["high", "critical"]:
            errors.append(f"FAIL: high/critical challenge {chg_id} cannot be accepted by user; it must be resolved.")

    # Check for human checkpoints in review mode
    human_rev = data.get("human_review", {})
    checkpoints = human_rev.get("checkpoints", [])
    if mode == "review":
        pre_pdf_approved = False
        for cp in checkpoints:
            if cp.get("checkpoint") == "pre_pdf_approval" and cp.get("status") == "approved":
                pre_pdf_approved = True
        if not pre_pdf_approved:
            errors.append("FAIL: review mode requires pre_pdf_approval but checkpoint is missing.")

    # Check if pipeline_status allows export
    if status not in ["qc_passed", "exported"]:
        errors.append(f"FAIL: cannot export PDF because pipeline_status is {status}.")

    # Validate revision attempts thresholds
    attempts = exec_meta.get("revision_attempts", {})
    limits = {
        "source": 2,
        "reading": 3,
        "vocabulary": 2,
        "grammar": 3,
        "writing": 2,
        "answers": 2,
        "pdf_layout": 2
    }
    for section, limit in limits.items():
        if section not in attempts:
            errors.append(f"FAIL: execution.revision_attempts missing key '{section}'.")
            continue
        attempt_value = attempts.get(section)
        if not isinstance(attempt_value, int):
            errors.append(f"FAIL: execution.revision_attempts.{section} must be an integer.")
            continue
        if attempt_value < 0:
            errors.append(f"FAIL: execution.revision_attempts.{section} cannot be negative.")
        if attempt_value > limit:
            errors.append(f"FAIL: execution.revision_attempts.{section}={attempt_value} exceeds maximum {limit}.")

    challenge_limit_sections = {
        "source_research": "source",
        "source": "source",
        "reading": "reading",
        "vocabulary": "vocabulary",
        "grammar": "grammar",
        "writing": "writing",
        "answers": "answers",
        "answer": "answers",
        "quality_control": "pdf_layout",
        "pdf": "pdf_layout",
        "pdf_layout": "pdf_layout",
    }
    for chg in challenges:
        to_agent = str(chg.get("to_agent", "")).lower()
        section = challenge_limit_sections.get(to_agent)
        if section is None:
            continue
        revision_attempt = chg.get("revision_attempt")
        if isinstance(revision_attempt, int) and revision_attempt > limits[section]:
            errors.append(
                f"FAIL: challenge {chg.get('id', 'unknown')} revision_attempt={revision_attempt} "
                f"exceeds maximum {limits[section]} for {section}."
            )
    # Validate warm_up
    if "warm_up" not in data:
        errors.append("FAIL: Missing top-level key: warm_up")
    else:
        warmup = data["warm_up"]
        if not isinstance(warmup, list) or len(warmup) != 3:
            errors.append("FAIL: warm_up must be an array of exactly 3 strings")
        else:
            generic_patterns = [
                r"Bạn nghĩ gì về chủ đề này",
                r"Chia sẻ một trải nghiệm thực tế",
                r"Tại sao chủ đề này"
            ]
            for idx, q in enumerate(warmup):
                if not isinstance(q, str) or not q.strip():
                    errors.append(f"FAIL: warm_up[{idx}] must be a non-empty string")
                else:
                    for pattern in generic_patterns:
                        if re.search(pattern, q, re.I):
                            errors.append(f"FAIL: warm_up[{idx}] appears generic: '{q}'")

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
