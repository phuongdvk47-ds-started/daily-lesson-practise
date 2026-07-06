#!/usr/bin/env python3
import json
import sys
import re
import argparse
from pathlib import Path
from pypdf import PdfReader

# Ensure UTF-8 output on all systems
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def validate_rendered_pdf(json_path: Path, pdf_path: Path) -> list[str]:
    errors = []
    
    if not json_path.exists():
        errors.append(f"FAIL: JSON file does not exist: {json_path}")
        return errors
        
    if not pdf_path.exists():
        errors.append(f"FAIL: PDF file does not exist: {pdf_path}")
        return errors

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"FAIL: Failed to parse JSON: {e}")
        return errors

    try:
        reader = PdfReader(pdf_path)
        pdf_text = ""
        for page in reader.pages:
            pdf_text += page.extract_text() + "\n"
    except Exception as e:
        errors.append(f"FAIL: Failed to read PDF: {e}")
        return errors

    # Normalize whitespace for comparison
    pdf_norm = " ".join(pdf_text.split())

    vocabulary = data.get("vocabulary", {})
    matching_test = vocabulary.get("matching_test", {})
    if matching_test:
        if "Vocabulary Matching Test" not in pdf_norm:
            errors.append("Vocabulary Matching Test section missing in rendered PDF.")
        for item in matching_test.get("items", []):
            term = " ".join(str(item.get("term", "")).split())
            if term and term not in pdf_norm:
                errors.append(f"Vocabulary matching term missing in rendered PDF: '{term}'")
        for definition in matching_test.get("definitions", []):
            label = str(definition.get("label", "")).strip()
            definition_text = " ".join(str(definition.get("definition", "")).split())
            if label and f"{label}." not in pdf_norm:
                errors.append(f"Vocabulary matching definition label missing in rendered PDF: '{label}'")
            if definition_text and definition_text[:30] not in pdf_norm:
                errors.append(f"Vocabulary matching definition missing in rendered PDF: '{definition_text[:30]}...'")

    paragraphs = data.get("reading", {}).get("passage", {}).get("paragraphs", [])
    paragraph_labels = [str(p.get("label", "")).strip() for p in paragraphs if str(p.get("label", "")).strip()]
    if paragraph_labels:
        for label in paragraph_labels:
            if not re.search(rf'\b{re.escape(label)}\b', pdf_text):
                errors.append(f"Reading paragraph label '{label}' missing in rendered PDF.")

    summary_completion = data.get("reading", {}).get("summary_completion", {})
    if summary_completion:
        if "Word bank:" not in pdf_norm and "Word bank" not in pdf_norm:
            errors.append("Summary Completion word bank missing in rendered PDF.")
        for word in summary_completion.get("word_bank", []):
            word_clean = " ".join(str(word).split())
            if word_clean and word_clean not in pdf_norm:
                errors.append(f"Summary Completion word bank item missing in rendered PDF: '{word_clean}'")

    word_family_practice = vocabulary.get("word_family_practice", {})
    if word_family_practice:
        if "Word Family Practice" not in pdf_norm:
            errors.append("Word Family Practice section missing in rendered PDF.")
        for item in word_family_practice.get("items", []):
            for option in item.get("options", []):
                option_clean = " ".join(str(option).split())
                if option_clean and option_clean not in pdf_norm:
                    errors.append(f"Word Family Practice option missing in rendered PDF: '{option_clean}'")

    # 1. Multiple Choice Options Rendering
    # Check Reading MCQs
    reading_qs = data.get("reading", {}).get("questions", [])
    for idx, q in enumerate(reading_qs):
        if q.get("type") == "Multiple Choice":
            q_id = q.get("id")
            q_stem = q.get("question", "")
            q_stem_clean = " ".join(q_stem.split())
            
            # Stem must be in PDF
            # (Remove leading number and space just in case)
            stem_match = re.sub(r'^\d+\.\s*', '', q_stem_clean)
            stem_match = stem_match.replace("(*)", "").strip()
            if stem_match not in pdf_norm:
                errors.append(f"Reading question {q_id} stem missing in rendered PDF. Expected: '{stem_match[:40]}...'")
                
            # Options must be in PDF
            options = q.get("options", [])
            for opt_idx, opt in enumerate(options):
                opt_clean = " ".join(opt.split())
                if opt_clean not in pdf_norm:
                    errors.append(f"Reading question {q_id} option missing in rendered PDF. Expected: '{opt_clean}'")

    # Check Grammar MCQs
    grammar_qs = data.get("grammar", {}).get("questions", [])
    for idx, q in enumerate(grammar_qs):
        if q.get("type") == "Multiple Choice":
            q_id = q.get("id")
            q_stem = q.get("question", "")
            
            # Stem must be in PDF (with blanks replaced)
            stem_clean = q_stem.replace("_______", "").replace("(*)", "")
            stem_clean = " ".join(stem_clean.split()).strip()
            if stem_clean[:30] not in pdf_norm:
                errors.append(f"Grammar question {q_id} stem missing in rendered PDF. Expected part: '{stem_clean[:30]}...'")
                
            # Options must be in PDF
            options = q.get("options", [])
            for opt_idx, opt in enumerate(options):
                opt_clean = " ".join(opt.split())
                if opt_clean not in pdf_norm:
                    errors.append(f"Grammar question {q_id} option missing in rendered PDF. Expected: '{opt_clean}'")

    # 2. Blank Preservation Check
    # Verify that blanks in grammar questions don't collapse into a single space
    for idx, q in enumerate(grammar_qs):
        q_id = q.get("id")
        q_stem = q.get("question", "")
        if "_______" in q_stem:
            parts = q_stem.split("_______")
            left = parts[0].strip().split()[-1] if parts[0].strip() else ""
            right = parts[1].strip().split()[0] if parts[1].strip() else ""
            
            if left and right:
                # Search directly in the raw pdf_text to preserve whitespace characters
                # Remove common punctuation only from search words to match pypdf extraction
                left_pat = re.escape(re.sub(r'[^\w,]', '', left))
                right_pat = re.escape(re.sub(r'[^\w,]', '', right))
                pattern = r"\b" + left_pat + r"(\s+)" + right_pat + r"\b"
                
                # Strip special characters from pdf_text for matching but keep spaces
                clean_pdf_text = re.sub(r'[^\w\s,]', '', pdf_text)
                match = re.search(pattern, clean_pdf_text)
                if match:
                    whitespace = match.group(1)
                    # If it has only 1 normal space, then the blank was collapsed!
                    if whitespace == " " or len(whitespace) <= 1:
                        errors.append(f"Grammar question {q_id} blank '_______' missing or collapsed in rendered PDF.")

    # 3. Computed Grammar Ranges Check
    # Forbidden stale hardcoded ranges
    stale_ranges = ["questions 27–36", "questions 37–46", "questions 47–56", "questions 27-36", "questions 37-46", "questions 47-56"]
    for sr in stale_ranges:
        if sr in pdf_text.lower():
            errors.append(f"PDF contains stale hardcoded grammar range '{sr}'.")

    # Expected computed ranges from grammar.sections
    reading_count = len(reading_qs)
    grammar_sections = data.get("grammar", {}).get("sections", [])
    for sec in grammar_sections:
        start_idx = sec.get("internal_question_start")
        end_idx = sec.get("internal_question_end")
        if start_idx is not None and end_idx is not None:
            start_num = start_idx + reading_count
            end_num = end_idx + reading_count
            expected_range = f"Questions {start_num}–{end_num}"
            norm_range = expected_range.replace("–", "-")
            
            # Check if expected range is in the PDF
            if expected_range not in pdf_text and norm_range not in pdf_text:
                if expected_range.lower() not in pdf_text.lower() and norm_range.lower() not in pdf_text.lower():
                    errors.append(f"Expected computed grammar range '{expected_range}' not found in rendered PDF.")

    # 4. Time Allowed Consistency Check
    printed_time = data.get("lesson_meta", {}).get("printed_time_allowed_minutes")
    if printed_time:
        expected_time_str = f"Time Allowed: {printed_time} mins"
        if expected_time_str not in pdf_text:
            # Try case-insensitive or space-tolerant match
            time_match = re.search(r'time\s+allowed:\s*\d+\s*mins', pdf_text, re.I)
            if time_match:
                actual_time_str = time_match.group(0)
                errors.append(f"PDF Time Allowed is '{actual_time_str}' but lesson_source.json says '{printed_time} mins'.")
            else:
                errors.append(f"PDF Time Allowed header not found. Expected: '{expected_time_str}'")

    # 5. Warm-up Specificity Check
    # Verify that warm-up is not generic placeholders
    generic_patterns = [
        r"Bạn nghĩ gì về chủ đề này\?",
        r"Chia sẻ một trải nghiệm thực tế",
        r"Tại sao chủ đề này lại quan trọng"
    ]
    for pattern in generic_patterns:
        if re.search(pattern, pdf_text, re.I):
            errors.append(f"Warm-up question appears generic: '{pattern.replace('\\', '')}'")

    # 6. Visual Data SVG check
    # Check if writing tasks with svg type have their chart text rendered
    writing_tasks = data.get("writing", {}).get("tasks", [])
    for idx, task in enumerate(writing_tasks):
        vdata = task.get("visual_data", {})
        if vdata.get("type") == "svg":
            # Extract text from SVG content to see what labels to expect in PDF
            svg_content = vdata.get("content", "")
            # Find all <text> labels
            text_labels = re.findall(r'<text[^>]*>(.*?)</text>', svg_content)
            for label in text_labels:
                # Clean label
                label_clean = " ".join(label.strip().split())
                if label_clean and label_clean not in pdf_norm:
                    errors.append(f"Visual SVG text label '{label_clean}' missing in rendered PDF.")

    # 7. Grammar Logic and Punctuation Regression Checks in PDF
    pdf_lower = pdf_text.lower()
    if "uses relative clause commas correctly" in pdf_lower:
        if not any(ctx in pdf_lower for ctx in ["many students", "only one", "all resident", "some resident", "extra information"]):
            errors.append("FAIL: rendered PDF contains ambiguous item: \"Identify the sentence that uses relative clause commas correctly\" without context.")
            
    if "kansas state university" in pdf_lower and "stands in the state of kansas" in pdf_lower:
        if re.search(r'kansas state university,\s*which stands in the state of kansas\s+has', pdf_lower):
            errors.append("FAIL: rendered PDF contains incomplete sentence frame: \"Kansas State University ____ stands in the state of Kansas has a great campus.\"")

    if "main office" in pdf_lower and "located on the first floor" in pdf_lower:
        if re.search(r'main office,\s*which is located on the first floor\s+is', pdf_lower):
            errors.append("FAIL: rendered PDF contains non-defining clause option without closing comma.")

    if "resident assistants" in pdf_lower and "must follow university rules" in pdf_lower:
        if not any(ctx in pdf_lower for ctx in ["many", "only one", "all", "some", "extra", "identify which"]):
            errors.append("FAIL: rendered PDF contains ambiguous generic noun 'Resident Assistants' without context.")

    # 8. Correct-the-Error PDF rendering checks
    for idx, q in enumerate(grammar_qs):
        q_raw = q.get("question", "")
        q_id = q.get("id")
        # Shift q_id to display ID (adding reading_count)
        display_id = q_id + len(reading_qs)
        if q_raw.strip().lower().startswith(("correct the error", "correct the mistake", "error correction", "find and correct the error")):
            expected_orig = re.sub(r'^(Correct the error|Correct the mistake|Error correction|Find and correct the error)\s*:\s*', '', q_raw, flags=re.IGNORECASE).strip()
            correct_ans = q.get("correct_answer", "")
            
            def norm(s):
                return re.sub(r'[^\w\s]', '', s).lower().strip()
                
            norm_orig = norm(expected_orig)
            norm_ans = norm(correct_ans)
            
            corr_clean = " ".join(correct_ans.split()).replace("(*)", "").strip()
            
            # General check: If original sentence is already correct (no error present)
            ec_val = q.get("error_correction_validation", {})
            if ec_val.get("target_error_type") == "punctuation":
                if expected_orig.strip() == correct_ans.strip():
                    errors.append(f"FAIL: rendered PDF item {display_id} correct_answer is identical to original sentence.")
            else:
                if norm_orig == norm_ans:
                    errors.append(f"FAIL: rendered PDF item {display_id} asks to correct a sentence that is already correct.")
                else:
                    # If the PDF renders the corrected version in the prompt
                    pattern = r'(correct the error|correct the mistake|error correction|find and correct the error)\s*:\s*' + re.escape(corr_clean)
                    if re.search(pattern, pdf_norm, flags=re.IGNORECASE):
                        errors.append(f"FAIL: rendered PDF shows corrected sentence in error-correction item {display_id}.")

    # 9. Duplicate writing task label check
    for label in ["Word Ordering", "Sentence Completion", "Translation", "Visual Data Description", "Guided Email Invite"]:
        # Match case-insensitive duplicate label
        pattern = re.escape(label) + r'\s*:\s*' + re.escape(label)
        if re.search(pattern, pdf_norm, flags=re.IGNORECASE):
            errors.append(f"FAIL: rendered PDF contains duplicate writing task label: {label}")

    return errors

def main():
    parser = argparse.ArgumentParser(description="Validate rendered IELTS daily practice PDF.")
    parser.add_argument("--lesson-json", type=str, required=True, help="Path to the lesson_source.json file.")
    parser.add_argument("--pdf", type=str, required=True, help="Path to the Practice PDF file.")
    args = parser.parse_args()

    json_path = Path(args.lesson_json)
    pdf_path = Path(args.pdf)

    errors = validate_rendered_pdf(json_path, pdf_path)
    if errors:
        print("\nRendered PDF QC FAILED:")
        for err in errors:
            print(f" - {err}")
        sys.exit(1)
    else:
        print("\nRendered PDF QC PASSED successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
