#!/usr/bin/env python3
"""Export IELTS daily pack sections to three HTMLs, compile to three PDFs via Playwright,
and write Quizlet markdown + tab-separated text files.
"""
from __future__ import annotations

import argparse
import json
import re
import random
import string
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def safe_filename_part(value: str) -> str:
    value = re.sub(r"^Day\s+", "", str(value).strip(), flags=re.I)
    value = re.sub(r"[^\w\s.+\-]+", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"-+", "-", value)
    return value or "Daily-Pack"

def build_names(level: str, topic: str, day: str) -> dict[str, str]:
    base = f"{safe_filename_part(level)}-{safe_filename_part(topic)}-{safe_filename_part(day)}"
    return {
        "practice_pdf": f"{base}-Practise.pdf",
        "vocab_grammar_pdf": f"{base}-Vocabulary-Grammar.pdf",
        "answers_pdf": f"{base}-Answers.pdf",
        "vocab_checker_pdf": f"{base}-Vocab-Checker.pdf",
        "vocab_checker_answer_pdf": f"{base}-Vocab-Checker-Answer.pdf",
        "quizlet_md": f"{base}-Quizlet-Vocab.md",
        "quizlet_txt": f"{base}-Quizlet.txt",
    }

def format_markdown_inline(text: str) -> str:
    # First, protect underscores by converting them to blanks
    text = re.sub(r'_{3,}', '<span class="fill-blank">&nbsp;</span>', text)
    # Bold: **text** -> <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Italic: *text* or _text_ -> <i>text</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_([^_]+?)_', r'<i>\1</i>', text)
    # Inline code: `code` -> <code>code</code>
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    return text

def parse_markdown_table_to_html(md_table_text: str) -> str:
    lines = md_table_text.splitlines()
    if len(lines) < 2:
        return md_table_text
        
    html_rows = []
    in_tbody = False
    
    for idx, line in enumerate(lines):
        line_str = line.strip()
        if not line_str.startswith("|") or not line_str.endswith("|"):
            continue
        
        # Skip alignment row (e.g., | :--- | :--- |)
        if re.match(r'^\|\s*[:\-]+\s*\|', line_str) or "| ---" in line_str:
            continue
            
        cells = [c.strip() for c in line_str.split("|")[1:-1]]
        
        if idx == 0 or (idx == 1 and not html_rows):  # Header
            cell_html = "".join(f"<th>{format_markdown_inline(c)}</th>" for c in cells)
            html_rows.append(f"<thead><tr>{cell_html}</tr></thead>")
        else:
            if not in_tbody:
                html_rows.append("<tbody>")
                in_tbody = True
            cell_html = "".join(f"<td>{format_markdown_inline(c)}</td>" for c in cells)
            html_rows.append(f"<tr>{cell_html}</tr>")
            
    if in_tbody:
        html_rows.append("</tbody>")
        
    if not html_rows:
        return md_table_text
        
    return f'<table class="data-table">{"".join(html_rows)}</table>'

def build_word_regex(word: str) -> str:
    w = word.strip().lower()
    # Strip parenthetical annotations e.g. 'fed (content)' -> 'fed'
    w = re.sub(r'\s*\([^)]*\)\s*', ' ', w).strip()
    # Escape special regex characters, then re-allow [- ]+ for word separators
    # We only use the first token(s) without special chars
    if not w:
        return r'\bx\b'  # safe no-match placeholder
    # Replace dashes/spaces to allow both
    w = re.sub(r'[- ]+', r'[- ]+', w)
    
    parts = w.split(r'[- ]+')
    if len(parts) > 1:
        first = parts[0]
        if first in ("make", "run", "take", "go", "set", "keep", "bring", "come", "find", "get", "give", "hold", "show"):
            v_forms = {
                "make": "(?:make|makes|making|made)",
                "run": "(?:run|runs|running|ran)",
                "take": "(?:take|takes|taking|took|taken)",
                "go": "(?:go|goes|going|went|gone)",
                "set": "(?:set|sets|setting)",
                "keep": "(?:keep|keeps|keeping|kept)",
                "bring": "(?:bring|brings|bringing|brought)",
                "come": "(?:come|comes|coming|came)",
                "find": "(?:find|finds|finding|found)",
                "get": "(?:get|gets|getting|got|gotten)",
                "give": "(?:give|gives|giving|gave|given)",
                "hold": "(?:hold|holds|holding|held)",
                "show": "(?:show|shows|showing|showed|shown)"
            }
            parts[0] = v_forms[first]
        else:
            if first.endswith("e"):
                parts[0] = f"{first[:-1]}(?:e|es|ed|ing)"
            else:
                parts[0] = f"{first}(?:s|ed|ing)?"
        return r'\b' + r'[- ]+'.join(parts) + r'\b'
    
    # Single words
    if w.endswith("y") and len(w) > 3:
        return r'\b' + w[:-1] + r'(?:y|ies)\b'
    elif w.endswith("e") and len(w) > 3:
        return r'\b' + w[:-1] + r'(?:e|es|ed|ing)\b'
    elif w.endswith("s") or w.endswith("x") or w.endswith("ch") or w.endswith("sh"):
        return r'\b' + w + r'(?:es)?\b'
    else:
        return r'\b' + w + r'(?:s|es|ed|ing)?\b'

def bold_vocab_in_html(html_text: str, vocab_words: list[str]) -> str:
    if not vocab_words:
        return html_text
        
    # Sort by length descending to prevent substring replacements breaking larger words
    sorted_words = sorted(list(set(vocab_words)), key=len, reverse=True)
    
    patterns = []
    for w in sorted_words:
        w_clean = w.strip()
        if len(w_clean) < 3:
            continue
        patterns.append((w_clean, re.compile(build_word_regex(w_clean), re.IGNORECASE)))
        
    placeholders = {}
    temp_text = html_text
    
    for idx, (word, pattern) in enumerate(patterns):
        # We split text by HTML tags to only replace text outside tags
        parts = re.split(r'(<[^>]+>)', temp_text)
        for i in range(len(parts)):
            if i % 2 == 0:  # Text content
                matches = pattern.findall(parts[i])
                if matches:
                    def repl(match):
                        m_text = match.group(0)
                        p_id = f"__VOCAB_PH_{len(placeholders)}__"
                        placeholders[p_id] = f"<b>{m_text}</b>"
                        return p_id
                    parts[i] = pattern.sub(repl, parts[i])
        temp_text = "".join(parts)
        
    # Restore placeholders
    for p_id, bold_text in placeholders.items():
        temp_text = temp_text.replace(p_id, bold_text)
        
    return temp_text

MAJOR_SECTION_KEYWORDS = [
    "vocabulary table",
    "vocabulary grouping notes",
    "detailed grammar guide",
    "common mistakes",
    "ielts traps",
    "reading source verification",
    "warm-up",
    "reading passage",
    "questions for reading",
    "questions for grammar",
    "questions for writing",
    "reading answer key",
    "grammar answer key",
    "writing guidance",
    "suggested answers",
    "recycled vocabulary",
    "từ vựng ôn tập",
    "review bridge"
]

def is_major_section_heading(line: str) -> bool:
    line_str = line.strip()
    if not (line_str.startswith("## ") or line_str.startswith("### ")):
        return False
    if line_str.startswith("## Level:") or line_str.startswith("## Topic:") or line_str.startswith("### Level:") or line_str.startswith("### Topic:"):
        return False
    
    title_clean = re.sub(r'^[#\s\d\.]+', '', line_str).strip().lower()
    for kw in MAJOR_SECTION_KEYWORDS:
        if kw in title_clean and len(title_clean) < 50:
            return True
    return False

def split_sections_by_heading(md_text: str) -> dict[str, str]:
    sections = {}
    current_heading = "Intro"
    current_lines = []
    # Normalize newlines
    md_text = md_text.replace("\r\n", "\n")
    for line in md_text.splitlines():
        if is_major_section_heading(line):
            sections[current_heading] = "\n".join(current_lines).strip()
            # Clean heading
            current_heading = re.sub(r'^[#\s\d\.]+', '', line.strip()).strip()
            current_lines = []
        else:
            current_lines.append(line)
    sections[current_heading] = "\n".join(current_lines).strip()
    return sections

def parse_source_table(table_md: str) -> dict[str, str]:
    lines = table_md.splitlines()
    headers = []
    data_row = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [c.strip() for c in line.split("|")[1:-1]]
        if not headers:
            headers = parts
        elif all(re.match(r'^:?-+:?$', p) for p in parts):
            continue
        else:
            data_row = parts
            break
            
    info = {}
    for h, d in zip(headers, data_row):
        info[h.strip()] = d.strip()
    return info

def generate_source_box(sections: dict[str, str]) -> str:
    source_table_md = sections.get("Reading Source Verification", "")
    if not source_table_md:
        return ""
    try:
        info = parse_source_table(source_table_md)
        pub_date = info.get("Date/Access date", "")
        if "/" in pub_date:
            pub_date = pub_date.split("/")[0].strip()
        
        pub_org = info.get("Publisher/Organization", "").strip()
        src_title = info.get("Source title", "").strip()
        url = info.get("Final verified URL", "").strip()
        
        if not pub_org and not src_title and not url:
            for k, v in info.items():
                k_lower = k.lower()
                if "publisher" in k_lower or "org" in k_lower:
                    pub_org = v
                elif "title" in k_lower:
                    src_title = v
                elif "url" in k_lower:
                    url = v
                elif "date" in k_lower and not pub_date:
                    pub_date = v.split("/")[0].strip()
                    
        if pub_org or src_title or url:
            return f"""    <div class="source-box">
        Source: Adapted from <i>{pub_org}</i> - "{src_title}" ({pub_date})<br>
        URL: <a href="{url}" target="_blank">{url}</a>
    </div>"""
    except Exception as e:
        print(f"Warning: failed to parse source table: {e}")
    return ""

def generate_warmup_html(sections: dict[str, str]) -> str:
    warmup_md = sections.get("Warm-up", "")
    if not warmup_md:
        for k in sections.keys():
            if "warm-up" in k.lower() or "warmup" in k.lower():
                warmup_md = sections[k]
                break
    if not warmup_md:
        return ""
        
    lines = warmup_md.splitlines()
    questions = []
    instruction = "Answer the following questions in English:"
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        if line_str.startswith("*") and line_str.endswith("*"):
            instruction = line_str.replace("*", "").strip()
        elif re.match(r'^\d+\.', line_str):
            questions.append(format_markdown_inline(line_str))
            
    questions_html = "<br>\n        ".join(questions)
    
    return f"""    <!-- WARM-UP SECTION -->
    <div class="section-title">Warm-up / Khởi động</div>
    <div class="warmup-box">
        <div class="warmup-title">{instruction}</div>
        {questions_html}
    </div>"""

def generate_reading_passage_html(sections: dict[str, str], source_box_html: str, vocab_words: list[str] = None) -> str:
    passage_md = sections.get("Reading Passage", "")
    if not passage_md:
        for k in sections.keys():
            if "passage" in k.lower():
                passage_md = sections[k]
                break
    if not passage_md:
        return ""
        
    lines = passage_md.splitlines()
    title = "Reading Passage"
    passage_paras = []
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        if line_str.startswith("#### ") or line_str.startswith("### "):
            title = re.sub(r'^[#\s\d\.]+', '', line_str).strip()
        elif line_str.startswith("---"):
            continue
        else:
            cleaned_line = format_markdown_inline(line_str)
            passage_paras.append(f"        <p>{cleaned_line}</p>")
            
    paras_html = "\n".join(passage_paras)
    if vocab_words:
        paras_html = bold_vocab_in_html(paras_html, vocab_words)
    
    return f"""    <!-- READING PASSAGE -->
    <div class="section-title">I. Reading Passage</div>
    <div class="passage-title">{title}</div>
    
    <div class="reading-text">
{paras_html}
    </div>

{source_box_html}"""

def parse_questions_section(md_text: str) -> list[dict]:
    groups = []
    current_group = None
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        if line.startswith("#### ") or line.startswith("### ") or line.startswith("## Exercise"):
            if current_group:
                groups.append(current_group)
            current_group = {
                "title": re.sub(r'^[#\s\d\.]+', '', line).strip(),
                "instruction": "",
                "questions": []
            }
            i += 1
            continue
            
        if not current_group:
            current_group = {"title": "Questions", "instruction": "", "questions": []}
            
        if line.startswith("*") and line.endswith("*"):
            current_group["instruction"] = line.replace("*", "").strip()
            i += 1
            continue
            
        q_match = re.match(r'^(\d+)\.\s*(.*)', line)
        if q_match:
            q_num = q_match.group(1)
            q_text = q_match.group(2)
            
            is_stretch = "(*)" in line
            q_text = q_text.replace("(*)", "").strip()
            
            options = []
            while i + 1 < len(lines) and re.match(r'^\s*[A-D]\.\s*(.*)', lines[i+1]):
                opt_match = re.match(r'^\s*([A-D])\.\s*(.*)', lines[i+1])
                options.append(f"{opt_match.group(1)}. {opt_match.group(2).strip()}")
                i += 1
                
            current_group["questions"].append({
                "num": q_num,
                "text": q_text,
                "options": options,
                "is_stretch": is_stretch
            })
            i += 1
            continue
            
        i += 1
        
    if current_group:
        groups.append(current_group)
    return groups

def get_options_layout_class(options: list[str]) -> str:
    if not options:
        return ""
    cleaned_options = []
    for opt in options:
        opt_clean = re.sub(r'^\s*(?:\*\*)?[A-F](?:\.\s*|\*\*\s*)', '', opt).strip()
        cleaned_options.append(opt_clean)
        
    max_len = max(len(opt) for opt in cleaned_options)
    total_len = sum(len(opt) for opt in cleaned_options)
    
    if max_len <= 15 and total_len <= 55:
        return "options-4col"
    elif max_len <= 35 and total_len <= 125:
        return "options-2col"
    return "options-1col"

def generate_reading_questions_html(sections: dict[str, str]) -> str:
    reading_qs_md = sections.get("Questions for Reading", "")
    if not reading_qs_md:
        for k in sections.keys():
            if "questions for reading" in k.lower() or "reading questions" in k.lower():
                reading_qs_md = sections[k]
                break
    if not reading_qs_md:
        return ""
        
    groups = parse_questions_section(reading_qs_md)
    total_questions = sum(len(g["questions"]) for g in groups)
    
    html_parts = [f'    <!-- READING QUESTIONS -->\n    <div class="section-title">II. IELTS Reading Questions ({total_questions} questions)</div>']
    
    for g in groups:
        title = g["title"]
        instruction = g["instruction"]
        qs = g["questions"]
        
        is_tfng = "true" in title.lower() or "true" in instruction.lower() or "false" in title.lower() or "false" in instruction.lower()
        
        group_html = []
        group_html.append('    <div class="question-group">')
        
        if qs:
            start_num = qs[0]["num"]
            end_num = qs[-1]["num"]
            prefix = f"Questions {start_num}–{end_num}: "
            if not instruction.strip().startswith("Questions"):
                instruction = prefix + instruction
                
        group_html.append(f'        <div class="question-instruction">{instruction}</div>')
        
        if is_tfng:
            group_html.append("""        <div style="margin-left: 20px; font-weight: bold; margin-bottom: 8px; font-size: 10pt;">
            TRUE &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; if the statement agrees with the information<br>
            FALSE &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; if the statement contradicts the information<br>
            NOT GIVEN &nbsp;&nbsp;&nbsp;&nbsp; if there is no information on this
        </div>""")
            
        for q in qs:
            num = q["num"]
            q_text = format_markdown_inline(q["text"])
            q_text = re.sub(r'_{3,}', '<span class="fill-blank">&nbsp;</span>', q_text)
            
            stretch_marker = " (*)" if q.get("is_stretch") else ""
            
            q_item_html = f'        <div class="question-item">\n            <span class="question-number">{num}.</span> {q_text}{stretch_marker}'
            
            if q["options"]:
                layout_class = get_options_layout_class(q["options"])
                q_item_html += f'\n            <div class="question-options {layout_class}">'
                for opt in q["options"]:
                    q_item_html += f'\n                <div>{opt}</div>'
                q_item_html += '\n            </div>'
                
            q_item_html += '\n        </div>'
            group_html.append(q_item_html)
            
        group_html.append('    </div>')
        html_parts.append("\n".join(group_html))
        
    return "\n\n".join(html_parts)

def adjust_instruction_numbers(instruction: str, offset: int) -> str:
    if not offset:
        return instruction
        
    def replace_match(match):
        val = match.group(1).strip()
        range_match = re.match(r'^(\d+)[\s]*([-–—to]+)[\s]*(\d+)$', val, re.I)
        if range_match:
            num1 = int(range_match.group(1)) + offset
            sep = range_match.group(2).strip()
            num2 = int(range_match.group(3)) + offset
            return f"questions {num1}{sep}{num2}"
            
        if val.isdigit():
            return f"question {int(val) + offset}"
            
        return match.group(0)
        
    adjusted = re.sub(r'\bquestions?\s+(\d+[\s]*[-–—to]*[\s]*\d*)\b', replace_match, instruction, flags=re.I)
    return adjusted

def generate_grammar_questions_html(sections: dict[str, str], offset: int = 13) -> str:
    grammar_qs_md = sections.get("Questions for Grammar", "")
    if not grammar_qs_md:
        for k in sections.keys():
            if "questions for grammar" in k.lower() or "grammar questions" in k.lower():
                grammar_qs_md = sections[k]
                break
    if not grammar_qs_md:
        return ""
        
    groups = parse_questions_section(grammar_qs_md)
    total_questions = sum(len(g["questions"]) for g in groups)
    
    html_parts = [f'    <!-- GRAMMAR QUESTIONS -->\n    <div class="section-title">III. Questions for Grammar ({total_questions} questions)</div>']
    
    for g in groups:
        title = g["title"]
        instruction = g["instruction"]
        qs = g["questions"]
        
        group_html = []
        group_html.append('    <div class="question-group">')
        
        adjusted_instruction = adjust_instruction_numbers(instruction, offset)
        if qs:
            start_num = int(qs[0]["num"]) + offset
            end_num = int(qs[-1]["num"]) + offset
            prefix = f"Questions {start_num}–{end_num}: "
            
            display_title = title.strip() if title else ""
            if display_title:
                if "multiple choice" in display_title.lower() and "questions" not in display_title.lower():
                    display_title = "Multiple Choice Questions"
                elif "error correction" in display_title.lower():
                    display_title = "Error Correction"
                    if not adjusted_instruction.strip():
                        adjusted_instruction = "Correct the single grammatical error in each of the following sentences."
                elif "sentence transformation" in display_title.lower():
                    display_title = "Sentence Transformation and Combining"
                    if not adjusted_instruction.strip():
                        adjusted_instruction = "Combine or rewrite the sentences as instructed."
                
                if adjusted_instruction.strip():
                    adjusted_instruction = f"{prefix}{display_title} - {adjusted_instruction.strip()}"
                else:
                    adjusted_instruction = f"{prefix}{display_title}"
            else:
                if not adjusted_instruction.strip().startswith("Questions"):
                    adjusted_instruction = prefix + adjusted_instruction
                    
        group_html.append(f'        <div class="question-instruction">{adjusted_instruction}</div>')
        
        for q in qs:
            num = int(q["num"]) + offset
            q_text = format_markdown_inline(q["text"])
            q_text = re.sub(r'_{3,}', '<span class="fill-blank">&nbsp;</span>', q_text)
            
            stretch_marker = " (*)" if q.get("is_stretch") else ""
            
            q_item_html = f'        <div class="question-item">\n            <span class="question-number">{num}.</span> {q_text}{stretch_marker}'
            
            if q.get("options"):
                layout_class = get_options_layout_class(q["options"])
                q_item_html += f'\n            <div class="question-options {layout_class}">'
                for opt in q["options"]:
                    q_item_html += f'\n                <div>{opt}</div>'
                q_item_html += '\n            </div>'
            else:
                raw_text = q.get("text", "")
                has_blank = "_" in raw_text or "fill-blank" in q_text
                is_rewrite_or_correct = any(kw in q_text.lower() for kw in ["correct the error", "rewrite", "combine", "translate"])
                if is_rewrite_or_correct or not has_blank:
                    q_item_html += '\n            <div class="writing-line" style="margin-top: 8px; margin-bottom: 4px;"></div>'
                
            q_item_html += '\n        </div>'
            group_html.append(q_item_html)
            
        group_html.append('    </div>')
        html_parts.append("\n".join(group_html))
        
    return "\n\n".join(html_parts)

def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in re.split(r'(?<!\\)\|', line)]

def parse_writing_table(table_md: str) -> list[dict]:
    lines = table_md.splitlines()
    tasks = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|") or "Target length" in line or re.match(r'^\|[\s\-|\:]+$', line):
            continue
        parts = split_table_row(line)
        if len(parts) >= 6:
            tasks.append({
                "num": parts[0].replace("\\|", "|"),
                "task": parts[1].replace("\\|", "|"),
                "length": parts[2].replace("\\|", "|"),
                "skill": parts[3].replace("\\|", "|"),
                "language": parts[4].replace("\\|", "|"),
                "criteria": parts[5].replace("\\|", "|")
            })
    return tasks

def get_writing_task_title(num: str, skill: str) -> str:
    num = str(num).strip()
    skill_lower = skill.lower()
    is_stretch = "(*)" in skill or "(*)" in num
    prefix = "(*)" if is_stretch else ""
    
    skill_clean = skill.replace("(*)", "").strip()
    
    if "word order" in skill_lower or "ordering" in skill_lower:
        return f"Task {num}: {prefix} Word Ordering (Sắp xếp từ thành câu hoàn chỉnh)".replace(": (*)", ": (*)").strip()
    elif "conjunction" in skill_lower or "completion" in skill_lower:
        return f"Task {num}: {prefix} Sentence Completion (Hoàn thành câu)".replace(": (*)", ": (*)").strip()
    elif "translation" in skill_lower or "translate" in skill_lower:
        return f"Task {num}: {prefix} Translation (Dịch câu)".replace(": (*)", ": (*)").strip()
    elif "descriptive" in skill_lower or "describe" in skill_lower or "place" in skill_lower or "park" in skill_lower:
        return f"Task {num}: {prefix} Short Description (Mô tả ngắn)".replace(": (*)", ": (*)").strip()
    elif "email" in skill_lower or "invite" in skill_lower or "informal" in skill_lower or "message" in skill_lower:
        return f"Task {num}: {prefix} Guided Email Invite (Viết email ngắn)".replace(": (*)", ": (*)").strip()
    
    return f"Task {num}: {prefix} {skill_clean}".replace(": (*)", ": (*)").strip()

def get_required_lines_count(text: str) -> int:
    text_lower = text.lower()
    
    # Check for specific "X sentences" or "write X sentences" pattern
    match = re.search(r'(?:write\s+)?(\d+)\s+sentence', text_lower)
    if match:
        num_sentences = int(match.group(1))
        return max(num_sentences + 1, 3)
        
    # Check for range "X-Y sentences" or "write X-Y sentences"
    match_range = re.search(r'(?:write\s+)?(\d+)-(\d+)\s+sentence', text_lower)
    if match_range:
        max_sentences = int(match_range.group(2))
        return max(max_sentences + 1, 3)
        
    if "email" in text_lower or "message" in text_lower or "letter" in text_lower:
        return 5
    if "paragraph" in text_lower or "essay" in text_lower or "describe" in text_lower or "comparison" in text_lower:
        return 4
        
    return 1

def format_writing_task_content(task_text: str, target_length: str = "") -> str:
    # Clean up redundant arrows (→), dots (...), and trailing dots/dots-with-spaces
    text = task_text.replace("<br>", "\n")
    text = re.sub(r'[\s\.]*→\s*\.{5,}', '', text)
    text = re.sub(r'[\s\.]*→\s*$', '', text)
    text = re.sub(r'\s*\.{5,}\s*$', '', text)
    text = re.sub(r'\s+\.\s*$', '', text)
    text = text.strip()
    return generate_writing_task_block(text, target_length)
def generate_writing_task_block(task_text: str, target_length: str) -> str:
    lines = task_text.splitlines()
    formatted_lines = []
    
    # Detect if there are sub-questions (e.g. a) or 1.) or - or * outside tables
    has_sub = False
    for line in lines:
        line_str = line.strip()
        if not (line_str.startswith("|") and line_str.endswith("|")):
            if re.match(r'^\s*([a-z]\)|\d+\.|\-|\*)', line_str):
                has_sub = True
                break
                
    table_lines = []
    non_table_text_lines = []
    
    def format_prompt_line(line: str) -> str:
        line_str = line.strip()
        if line_str.startswith("<") or "<svg" in line_str or "<div" in line_str:
            return line_str
        return format_markdown_inline(line_str)
    
    def flush_text():
        if non_table_text_lines:
            txt = "\n".join(non_table_text_lines)
            if has_sub:
                sub_lines = txt.splitlines()
                for sl in sub_lines:
                    sl_str = sl.strip()
                    if not sl_str:
                        continue
                    if re.match(r'^\s*([a-z]\)|\d+\.|\-|\*)', sl_str):
                        formatted_lines.append(f'<div class="writing-prompt-sub-item">{format_prompt_line(sl_str)}</div>')
                        sub_lines_count = get_required_lines_count(sl_str)
                        for _ in range(sub_lines_count):
                            formatted_lines.append('<div class="writing-line"></div>')
                    else:
                        formatted_lines.append(f'<div class="writing-prompt-text">{format_prompt_line(sl_str)}</div>')
            else:
                for sl in txt.splitlines():
                    sl_str = sl.strip()
                    if not sl_str:
                        continue
                    if sl_str.startswith("<") or "<svg" in sl_str or "<div" in sl_str:
                        formatted_lines.append(sl_str)
                    else:
                        formatted_lines.append(f'<div class="writing-prompt-text">{format_prompt_line(sl_str)}</div>')
            non_table_text_lines.clear()

    for line in lines:
        line_str = line.strip()
        if line_str.startswith("|") and line_str.endswith("|"):
            flush_text()
            table_lines.append(line_str)
        else:
            if table_lines:
                formatted_lines.append(parse_markdown_table_to_html("\n".join(table_lines)))
                table_lines.clear()
            non_table_text_lines.append(line)
            
    flush_text()
    if table_lines:
        formatted_lines.append(parse_markdown_table_to_html("\n".join(table_lines)))
        
    if not has_sub:
        # Check if the task contains a table with fill-in placeholders
        has_table_placeholders = False
        if "|" in task_text:
            for line in lines:
                if "|" in line:
                    if "...." in line or "___" in line or "[Fill" in line:
                        has_table_placeholders = True
                        break
        
        if "|" not in task_text or not has_table_placeholders:
            lines_count = get_required_lines_count(task_text)
            if lines_count == 1 and target_length:
                lines_count = get_required_lines_count(target_length)
                
            if "email" in task_text.lower() or "message" in task_text.lower():
                formatted_lines.append("<div style='margin-top: 4px; margin-bottom: 2px;'>To: ...................................................... Subject: ......................................................</div>")
            
            if lines_count == 1:
                formatted_lines.append("<div style='margin-top: 4px;'>Answer: <div class='writing-line' style='display:inline-block; width:90%; margin-top:0; vertical-align:middle;'></div></div>")
            else:
                for _ in range(lines_count):
                    formatted_lines.append('<div class="writing-line"></div>')
            
    return "\n".join(formatted_lines)

def generate_writing_questions_html(sections: dict[str, str]) -> str:
    writing_qs_md = sections.get("Questions for Writing", "")
    if not writing_qs_md:
        for k in sections.keys():
            if "questions for writing" in k.lower() or "writing questions" in k.lower() or "writing practice" in k.lower():
                writing_qs_md = sections[k]
                break
    if not writing_qs_md:
        return ""
        
    tasks = parse_writing_table(writing_qs_md)
    
    html_parts = [f'    <!-- WRITING QUESTIONS -->\n    <div class="section-title">IV. Questions for Writing ({len(tasks)} tasks)</div>']
    
    for t in tasks:
        num = t["num"]
        task_text = t["task"]
        # Clean any redundant task type labels/headers (case-insensitive) to prevent double headings
        # Use [a-zA-Z\s\-]+ instead of [\w\s\-]+ to avoid matching Vietnamese characters
        task_types_pattern = r'^(Word\s+Ordering|Sentence\s+Completion|Translation|Short\s+Description|Visual\s+Data\s+Description|Data\s+Description|Guided\s+Email\s+Invite|Email|Word\s+order|Sentence\s+completion|Visual\s+data\s+description|Guided\s+email\s+invite|[a-zA-Z\s\-]+)\s*:\s*'
        while True:
            new_task = re.sub(task_types_pattern, '', task_text, flags=re.IGNORECASE).strip()
            if new_task == task_text:
                break
            task_text = new_task
            
        skill = t["skill"]
        skill_lower = skill.lower()
        
        # Append words to order for Sentence Building / Word Ordering / Completion tasks
        language_text = t.get("language", "").strip()
        if language_text and any(keyword in skill_lower for keyword in ["order", "building", "completion", "complete"]):
            task_text = task_text + "\n\n" + language_text
            
        title = get_writing_task_title(num, skill)
        target_len = t.get("length", "")
        content_html = format_writing_task_content(task_text, target_len)
        
        task_html = f"""    <div class="writing-box">
        <div class="question-instruction">{title}</div>
        <div class="writing-item">
            {content_html}
        </div>
    </div>"""
        html_parts.append(task_html)
        
    return "\n\n".join(html_parts)

def build_practice_html(practice_md: str, level: str, topic: str, day: str, vocab_words: list[str] = None, time_allowed: int = None, skill_level: dict = None) -> str:
    sections = split_sections_by_heading(practice_md)

    # Prefer explicit skill_level dict from lesson_meta; fall back to intro-section regex
    if skill_level:
        reading_level   = skill_level.get("reading_level",   level)
        grammar_level   = skill_level.get("grammar_level",   "")
        writing_level   = skill_level.get("writing_level",   "A1")
        vocabulary_level = skill_level.get("vocabulary_level", "")
    else:
        reading_level    = level
        writing_level    = "A1"
        grammar_level    = ""
        vocabulary_level = ""
        intro_sec = sections.get("Intro", "")
        r_match = re.search(r'Reading:\s*([A-C][1-2]\+?)', intro_sec, re.I)
        if r_match:
            reading_level = r_match.group(1).upper()
        w_match = re.search(r'Writing:\s*([A-C][1-2]\+?)', intro_sec, re.I)
        if w_match:
            writing_level = w_match.group(1).upper()

    day_only = re.sub(r'^Day\s+', '', day.strip(), flags=re.I)
    topic_upper = topic.upper()
    
    source_box_html = generate_source_box(sections)
    warmup_html = generate_warmup_html(sections)
    reading_html = generate_reading_passage_html(sections, source_box_html, vocab_words)
    reading_qs_html = generate_reading_questions_html(sections)
    
    reading_offset = 13
    groups = parse_questions_section(sections.get("Questions for Reading", ""))
    if groups:
        reading_offset = sum(len(g["questions"]) for g in groups)
        
    grammar_html = generate_grammar_questions_html(sections, reading_offset)
    writing_html = generate_writing_questions_html(sections)
    
    review_sec = sections.get("Review Bridge", "")
    if not review_sec:
        for k in sections.keys():
            if "review" in k.lower() or "bridge" in k.lower():
                review_sec = sections[k]
                break
    review_html = ""
    if review_sec:
        review_content = render_review_bridge(review_sec, is_answer=False)
        review_html = f"""    <!-- REVIEW BRIDGE -->
    <div class="review-bridge-container" style="page-break-before: always; page-break-inside: avoid;">
        <div class="section-title">V. Review Bridge / Ôn tập liên chủ đề</div>
        <div class="warmup-box" style="background-color: #fafbfc; border: 1px solid #bdc3c7; border-radius: 4px; padding: 10px;">
            {review_content}
        </div>
    </div>"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DAILY PRACTICE: DAY {day_only} - {topic_upper}</title>
    <style>
        @page {{ 
            size: A4; 
            margin: 15mm 15mm 20mm 15mm; 
        }}
        body {{ 
            font-family: "Times New Roman", Times, serif; 
            font-size: 11.5pt; 
            line-height: 1.45; 
            color: #1a1a1a; 
            margin: 0; 
            padding: 0;
        }}
        .header {{ 
            border-bottom: 2px double #2c3e50; 
            padding-bottom: 8px; 
            margin-bottom: 15px; 
            text-align: center;
        }}
        .header .center-name {{ 
            font-size: 9.5pt; 
            text-transform: uppercase; 
            letter-spacing: 1.5px; 
            color: #7f8c8d; 
            font-weight: bold;
            margin-bottom: 3px;
        }}
        .header h1 {{ 
            font-size: 15pt; 
            margin: 3px 0; 
            color: #2c3e50;
            text-transform: uppercase;
            font-weight: bold;
        }}
        .header h2 {{ 
            font-size: 11pt; 
            margin: 3px 0; 
            font-style: italic; 
            color: #34495e;
        }}
        .student-info {{ 
            margin-top: 10px; 
            display: flex; 
            justify-content: space-between; 
            font-size: 10pt;
            font-weight: bold;
        }}
        .section-title {{ 
            font-size: 12pt; 
            color: #2c3e50; 
            border-left: 3px solid #27ae60; 
            padding-left: 8px; 
            margin-top: 18px; 
            margin-bottom: 8px; 
            text-transform: uppercase;
            font-weight: bold;
        }}
        .passage-title {{
            font-size: 12pt;
            font-weight: bold;
            text-align: center;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        .reading-text {{ 
            text-align: justify; 
            margin-bottom: 12px; 
            text-indent: 25px;
        }}
        .reading-text p {{
            margin: 0 0 6px 0;
        }}
        .data-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 10px 0; 
            font-size: 10pt; 
            page-break-inside: avoid;
        }}
        .data-table th {{ 
            background-color: #f2f4f8; 
            border: 1px solid #dcdde1; 
            padding: 6px 10px; 
            text-align: left; 
            font-weight: bold; 
            color: #2c3e50; 
        }}
        .data-table td {{ 
            border: 1px solid #dcdde1; 
            padding: 6px 10px; 
            color: #333; 
        }}
        .data-table tr:nth-child(even) {{ 
            background-color: #fafbfc; 
        }}
        .svg-chart-container {{
            text-align: center;
            margin: 10px 0;
            page-break-inside: avoid;
        }}
        .writing-line {{
            border-bottom: 1px dotted #bdc3c7;
            height: 22px;
            margin-top: 4px;
            margin-bottom: 1px;
            width: 98%;
            page-break-inside: avoid;
        }}
        .writing-prompt-text {{
            margin-top: 2px;
            margin-bottom: 2px;
            text-align: justify;
        }}
        .writing-prompt-sub-item {{
            margin-top: 4px;
            margin-bottom: 2px;
            text-align: justify;
        }}
        .source-box {{ 
            font-style: italic; 
            font-size: 9pt; 
            color: #7f8c8d; 
            margin-bottom: 15px; 
            padding: 6px 10px;
            background-color: #f8f9fa;
            border-left: 3px solid #bdc3c7;
        }}
        .source-box a {{
            color: #27ae60;
            text-decoration: none;
        }}
        .question-instruction {{
            font-style: italic;
            margin-bottom: 8px;
            color: #2c3e50;
            font-weight: bold;
            font-size: 10.5pt;
        }}
        .question-group {{
            margin-bottom: 12px;
        }}
        .question-item {{
            margin-bottom: 8px;
            padding-left: 20px;
            text-indent: -20px;
            text-align: justify;
            page-break-inside: avoid;
        }}
        .question-options {{
            margin: 4px 0 4px 20px;
            text-indent: 0;
            display: flex;
            flex-wrap: wrap;
        }}
        .question-options div {{
            margin-bottom: 2px;
            box-sizing: border-box;
            padding-right: 8px;
        }}
        .options-4col div {{
            width: 25%;
        }}
        .options-2col div {{
            width: 50%;
        }}
        .options-1col div {{
            width: 100%;
        }}
        .fill-blank {{
            display: inline-block;
            width: 100px;
            border-bottom: 1px solid #000;
            text-align: center;
        }}
        .grammar-item {{
            margin-bottom: 8px;
            text-align: justify;
            page-break-inside: avoid;
        }}
        .writing-box {{
            border: 1px solid #bdc3c7;
            padding: 10px;
            background-color: #fafbfc;
            border-radius: 4px;
            margin-bottom: 12px;
            text-align: left;
            page-break-inside: avoid;
        }}
        .writing-item {{
            margin-bottom: 10px;
        }}
        .warmup-box {{
            background-color: #fcfcfc;
            border: 1px dashed #bdc3c7;
            padding: 8px 12px;
            margin-bottom: 15px;
            font-size: 10pt;
        }}
        .warmup-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 4px;
        }}
    </style>
</head>
<body>

    <div class="header">
        <div class="center-name">IELTS PREMIUM PREPARATION ACADEMY</div>
        <h1>DAILY PRACTICE: DAY {day_only} - {topic_upper}</h1>
        <h2>(Level: Reading {reading_level} | Grammar {grammar_level} | Writing {writing_level} | Vocab {vocabulary_level})</h2>
        <div class="student-info">
            <span>Student Name: ..............................................................</span>
            <span>Time Allowed: {time_allowed or 50} mins</span>
        </div>
    </div>

{warmup_html}

{reading_html}

{reading_qs_html}

{grammar_html}

{writing_html}

{review_html}

</body>
</html>
"""
    return html_content

def split_definition(cell_text: str) -> tuple[str, str]:
    match = re.search(r'^(.*?)\s*\(([^)]+)\)\s*$', cell_text.strip(), re.DOTALL)
    if match:
        definition = match.group(2).strip()
        vietnamese = match.group(1).strip()
        if definition:
            definition = definition[0].upper() + definition[1:]
        return definition, vietnamese
    if " - " in cell_text:
        parts = cell_text.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return cell_text.strip(), cell_text.strip()

# Header keywords that indicate we've left the vocabulary table
_NON_VOCAB_TABLE_HEADERS = (
    "common mistake", "wrong example", "correct version", "why it matters",
    "grammar point", "trap", "ielts trap", "recycled vocabulary", "từ vựng ôn tập",
)

def parse_vocab_from_markdown(md_table: str, is_recycled: bool = False) -> list[dict]:
    items = []
    in_vocab_table = False
    lines = md_table.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Detect non-vocab keywords on ALL lines to stop vocab parsing
        if not is_recycled:
            line_lower = line.lower()
            if any(kw in line_lower for kw in _NON_VOCAB_TABLE_HEADERS):
                in_vocab_table = False
                continue
        if not line.startswith("|"):
            continue
        # Detect the vocabulary table header row
        if "Từ/Cụm từ" in line or "Phiên âm" in line:
            has_recycled_marker = "Bài học gốc" in line or "Day" in line
            if is_recycled == has_recycled_marker:
                in_vocab_table = True
            else:
                in_vocab_table = False
            continue
        # Skip separator rows
        if re.match(r'^\|[\s:|-]+\|', line):
            continue
        if not in_vocab_table:
            continue
        parts = split_table_row(line)
        if len(parts) >= 4:
            word = parts[0]
            ipa = parts[1]
            vocab_type = parts[2]
            def_vi = parts[3]
            example = parts[4] if len(parts) > 4 else ""
            
            definition, vietnamese = split_definition(def_vi)
            items.append({
                "word": word,
                "ipa": ipa,
                "type": vocab_type,
                "definition": definition,
                "vietnamese": vietnamese,
                "example": example
            })
    return items

def parse_grouping_notes(notes_md: str) -> dict[str, list[str]]:
    groups = {
        "academic": [],
        "compound": [],
        "idiom": []
    }
    for line in notes_md.splitlines():
        line = line.strip()
        if not line:
            continue
        line_lower = line.lower()
        match = re.search(r'\*\*.*?\*\*:\s*(.*)', line)
        if not match:
            continue
        words_str = match.group(1).strip()
        words = [w.strip().lower() for w in words_str.split(",")]
        
        if "academic" in line_lower:
            groups["academic"] = words
        elif "compound" in line_lower:
            groups["compound"] = words
        elif "idiom" in line_lower or "phrase" in line_lower or "chunk" in line_lower:
            groups["idiom"] = words
            
    return groups

def categorize_word(word: str, groups: dict[str, list[str]]) -> str:
    word_norm = word.lower().strip()
    if word_norm in groups["academic"]:
        return "academic"
    if word_norm in groups["compound"]:
        return "compound"
    if word_norm in groups["idiom"]:
        return "idiom"
        
    for w in groups["academic"]:
        if w in word_norm or word_norm in w:
            return "academic"
    for w in groups["compound"]:
        if w in word_norm or word_norm in w:
            return "compound"
    for w in groups["idiom"]:
        if w in word_norm or word_norm in w:
            return "idiom"
            
    if " " in word_norm:
        return "idiom"
    return "academic"

def markdown_to_html_body(md_text: str) -> str:
    lines = md_text.splitlines()
    html_parts = []
    in_list = False
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue
            
        if line_str.startswith("- ") or line_str.startswith("* "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            content = line_str[2:].strip()
            formatted = format_markdown_inline(content)
            html_parts.append(f"<li>{formatted}</li>")
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            formatted = format_markdown_inline(line_str)
            if formatted.startswith("##### "):
                html_parts.append(f"<h5>{formatted[6:].strip()}</h5>")
            elif formatted.startswith("###### "):
                html_parts.append(f"<h6>{formatted[7:].strip()}</h6>")
            else:
                html_parts.append(f"<p>{formatted}</p>")
                
    if in_list:
        html_parts.append("</ul>")
        
    return "\n".join(html_parts)

GRAMMAR_LINKS = [
    {
        "keywords": ["present perfect", "past simple"],
        "links": [
            ("British Council - Present Perfect vs Past Simple", "https://learnenglish.britishcouncil.org/grammar/b1-b2-grammar/present-perfect-simple-and-past-simple"),
            ("Perfect English Grammar - Present Perfect or Past Simple", "https://www.perfect-english-grammar.com/present-perfect-or-past-simple.html")
        ]
    },
    {
        "keywords": ["relative clause", "defining", "non-defining"],
        "links": [
            ("British Council - Defining and Non-defining Relative Clauses", "https://learnenglish.britishcouncil.org/grammar/b1-b2-grammar/relative-clauses-defining-and-non-defining"),
            ("Cambridge Dictionary - Relative Clauses Rules & Punctuation", "https://dictionary.cambridge.org/grammar/british-grammar/relative-clauses")
        ]
    },
    {
        "keywords": ["contrast", "linker", "linkers"],
        "links": [
            ("British Council - Linking words of contrast", "https://learnenglish.britishcouncil.org/grammar/b1-b2-grammar/linking-words-contrast"),
            ("Cambridge Dictionary - Linking Words & Clauses", "https://dictionary.cambridge.org/grammar/british-grammar/linking-words-and-expressions")
        ]
    }
]

def get_study_links(topic_title: str) -> list[tuple[str, str]]:
    topic_lower = topic_title.lower()
    for item in GRAMMAR_LINKS:
        if any(k in topic_lower for k in item["keywords"]):
            return item["links"]
    return []

def is_grammar_subheading(line: str) -> bool:
    line_str = line.strip()
    if line_str.startswith("## ") or line_str.startswith("### ") or line_str.startswith("#### ") or line_str.startswith("##### "):
        title_clean = re.sub(r'^[#\s\d\.]+', '', line_str).strip().lower()
        for kw in MAJOR_SECTION_KEYWORDS:
            if kw in title_clean and len(title_clean) < 35:
                return False
        return True
    bold_match = re.match(r'^\*\*(Chủ điểm|Grammar Point|Target|Topic)\s+\d+:?\s*(.*?)\*\*$', line_str, re.I)
    if bold_match:
        return True
    return False

def clean_grammar_subheading(line: str) -> str:
    line_str = line.strip()
    if line_str.startswith("#"):
        cleaned = re.sub(r'^[#\s\d\.]+', '', line_str).strip()
        cleaned = re.sub(r'^(Chủ điểm|Grammar Point|Target|Topic)\s+\d+[:\-\s]*', '', cleaned, flags=re.IGNORECASE).strip()
        return cleaned
    bold_match = re.match(r'^\*\*(Chủ điểm|Grammar Point|Target|Topic)\s+\d+:?\s*(.*?)\*\*$', line_str, re.I)
    if bold_match:
        return bold_match.group(2).strip()
    return line_str

def build_materials_html(vocab_grammar_md: str, quizlet_md: str, day: str, topic: str) -> str:
    # Parse from the full 5-column table in vocab_grammar_md; quizlet_md is 2-column only
    vocab_items = parse_vocab_from_markdown(vocab_grammar_md)
    if not vocab_items:
        vocab_items = parse_vocab_from_markdown(quizlet_md)
    sections = split_sections_by_heading(vocab_grammar_md)
    
    grouping_md = sections.get("Vocabulary Grouping Notes", "")
    if not grouping_md:
        for k in sections.keys():
            if "grouping" in k.lower():
                grouping_md = sections[k]
                break
                
    groups = parse_grouping_notes(grouping_md)
    
    core_list = []
    topic_list = []
    phrase_list = []
    
    for item in vocab_items:
        t_lower = item.get("type", "").lower()
        if "single" in t_lower or "core" in t_lower or t_lower in ["n", "v", "adj", "adv", "noun", "verb", "adjective", "adverb"]:
            core_list.append(item)
        elif "topic" in t_lower or "academic" in t_lower:
            topic_list.append(item)
        elif any(x in t_lower for x in ["phrase", "collocation", "idiom", "expression", "chunk"]):
            phrase_list.append(item)
        else:
            if " " in item["word"]:
                phrase_list.append(item)
            else:
                core_list.append(item)
            
    tables_html = []
    
    def build_table(items, title, idx):
        if not items:
            return ""
        
        rows = []
        for item in items:
            en_def = item["definition"].strip()
            vi_mean = item["vietnamese"].strip()
            
            row = f"""            <tr>
                <td class="col-word">{item['word']}</td>
                <td class="col-phon">{item['ipa']}</td>
                <td class="col-pos">{item['type']}</td>
                <td class="col-def">{en_def}<br><b>{vi_mean}</b></td>
                <td class="col-ex">{item['example']}</td>
            </tr>"""
            rows.append(row)
            
        rows_html = "\n".join(rows)
        
        return f"""    <div class="subsection-title">Table 2.{idx}: {title}</div>
    <table>
        <thead>
            <tr>
                <th style="width: 18%;">Từ / Cụm từ</th>
                <th style="width: 14%;">Phiên âm</th>
                <th style="width: 10%;">Loại từ</th>
                <th style="width: 28%;">Định nghĩa & Nghĩa tiếng Việt</th>
                <th style="width: 30%;">Ví dụ minh họa</th>
            </tr>
        </thead>
        <tbody>
{rows_html}
        </tbody>
    </table>"""

    idx = 1
    t1 = ""
    if core_list:
        t1 = build_table(core_list, "Core Words (Từ vựng cốt lõi)", idx)
        idx += 1
        
    t2 = ""
    if topic_list:
        t2 = build_table(topic_list, "Topic Vocabulary (Từ vựng theo chủ đề)", idx)
        idx += 1
        
    t3 = ""
    if phrase_list:
        t3 = build_table(phrase_list, "Phrases, Chunks & Collocations (Cụm từ & Kết hợp từ)", idx)
        idx += 1
    
    recycled_sec = ""
    for k in sections.keys():
        if "recycled" in k.lower() or "ôn tập" in k.lower():
            recycled_sec = sections[k]
            break
            
    recycled_html = ""
    if recycled_sec:
        recycled_items = parse_vocab_from_markdown(recycled_sec, is_recycled=True)
        if recycled_items:
            recycled_rows = []
            for item in recycled_items:
                recycled_rows.append(f"""            <tr>
                <td class="col-word">{item['word']}</td>
                <td class="col-phon">{item['ipa']}</td>
                <td class="col-pos">{item['type']}</td>
                <td class="col-def"><b>{item['vietnamese']}</b></td>
                <td class="col-ex">{item['example']}</td>
            </tr>""")
            recycled_rows_html = "\n".join(recycled_rows)
            recycled_html = f"""    <div class="subsection-title">Table 2.{idx}: Recycled Vocabulary (Từ vựng ôn tập)</div>
    <table>
        <thead>
            <tr>
                <th style="width: 18%;">Từ / Cụm từ</th>
                <th style="width: 14%;">Phiên âm</th>
                <th style="width: 10%;">Loại từ</th>
                <th style="width: 28%;">Nghĩa tiếng Việt</th>
                <th style="width: 30%;">Bài học gốc (Day)</th>
            </tr>
        </thead>
        <tbody>
{recycled_rows_html}
        </tbody>
    </table>"""
            
    vocab_tables_html = "\n\n".join(filter(None, [t1, t2, t3, recycled_html]))
    
    core_words = ", ".join(item["word"] for item in core_list)
    topic_words = ", ".join(item["word"] for item in topic_list)
    phrase_words = ", ".join(item["word"] for item in phrase_list)
    
    group_items = []
    if core_list:
        group_items.append(f"        <li><b>Core Words:</b> {core_words}.</li>")
    if topic_list:
        group_items.append(f"        <li><b>Topic Vocabulary:</b> {topic_words}.</li>")
    if phrase_list:
        group_items.append(f"        <li><b>Phrases, Chunks & Collocations:</b> {phrase_words}.</li>")
        
    group_items_html = "\n".join(group_items)
    grouping_summary_html = f"""    <div class="subsection-title">Vocabulary Grouping Notes (Phân loại từ vựng)</div>
    <ul>
{group_items_html}
    </ul>"""
    
    grammar_guide_md = sections.get("Detailed Grammar Guide", "")
    if not grammar_guide_md:
        for k in sections.keys():
            if "grammar guide" in k.lower() or "detailed grammar" in k.lower():
                grammar_guide_md = sections[k]
                break
                
    grammar_parts = []
    border_colors = ["#27ae60", "#2980b9", "#8e44ad"]
    title_colors = ["#1b5e20", "#1b4f72", "#4a235a"]
    
    g_idx = 0
    current_g_title = None
    current_g_lines = []
    
    for line in grammar_guide_md.splitlines():
        line_str = line.strip()
        if is_grammar_subheading(line_str):
            if current_g_title:
                g_body = "\n".join(current_g_lines).strip()
                g_body_html = markdown_to_html_body(g_body)
                
                links = get_study_links(current_g_title)
                links_html = ""
                if links:
                    links_li = "".join(f'            <li><a href="{url}" target="_blank">{title}</a></li>\n' for title, url in links)
                    links_html = f"""        <p><b>Tài liệu tự học trực tuyến uy tín:</b></p>
        <ul class="link-list">
{links_li}        </ul>"""
                
                b_color = border_colors[g_idx % len(border_colors)]
                t_color = title_colors[g_idx % len(title_colors)]
                
                grammar_parts.append(f"""    <div class="grammar-box" style="border-left-color: {b_color};">
        <div class="subsection-title" style="margin-top:0; color:{t_color};">Chủ điểm {g_idx + 1}: {current_g_title}</div>
        {g_body_html}
        {links_html}
    </div>""")
                g_idx += 1
                
            current_g_title = clean_grammar_subheading(line_str)
            current_g_lines = []
        else:
            current_g_lines.append(line)
            
    if current_g_title:
        g_body = "\n".join(current_g_lines).strip()
        g_body_html = markdown_to_html_body(g_body)
        links = get_study_links(current_g_title)
        links_html = ""
        if links:
            links_li = "".join(f'            <li><a href="{url}" target="_blank">{title}</a></li>\n' for title, url in links)
            links_html = f"""        <p><b>Tài liệu tự học trực tuyến uy tín:</b></p>
        <ul class="link-list">
{links_li}        </ul>"""
        b_color = border_colors[g_idx % len(border_colors)]
        t_color = title_colors[g_idx % len(title_colors)]
        grammar_parts.append(f"""    <div class="grammar-box" style="border-left-color: {b_color};">
        <div class="subsection-title" style="margin-top:0; color:{t_color};">Chủ điểm {g_idx + 1}: {current_g_title}</div>
        {g_body_html}
        {links_html}
    </div>""")
        
    if not grammar_parts and grammar_guide_md.strip():
        g_body_html = markdown_to_html_body(grammar_guide_md.strip())
        b_color = border_colors[0]
        grammar_parts.append(f"""    <div class="grammar-box" style="border-left-color: {b_color};">
        <div class="subsection-title" style="margin-top:0; color:#1b5e20;">Grammar Study (Hướng dẫn ngữ pháp)</div>
        {g_body_html}
    </div>""")
        
    grammar_boxes_html = "\n\n".join(grammar_parts)
    
    mistakes_md = sections.get("Common Mistakes / IELTS Traps for This Topic", "")
    if not mistakes_md:
        for k in sections.keys():
            if "mistakes" in k.lower() or "traps" in k.lower():
                mistakes_md = sections[k]
                break
                
    mistakes_rows = []
    for line in mistakes_md.splitlines():
        line_str = line.strip()
        if not line_str.startswith("|") or "Wrong example" in line_str or "---" in line_str:
            continue
        row_cells = split_table_row(line_str)
        if len(row_cells) >= 4:
            col1 = format_markdown_inline(row_cells[0])
            col2 = format_markdown_inline(row_cells[1])
            col3 = format_markdown_inline(row_cells[2])
            col4 = format_markdown_inline(row_cells[3])
            
            mistakes_rows.append(f"""            <tr>
                <td>{col1}</td>
                <td>{col2}</td>
                <td>{col3}</td>
                <td>{col4}</td>
            </tr>""")
            
    mistakes_rows_html = "\n".join(mistakes_rows)
    
    day_only = re.sub(r'^Day\s+', '', day.strip(), flags=re.I)
    topic_upper = topic.upper()
    
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>VOCABULARY & GRAMMAR KNOWLEDGE - DAY {day_only}</title>
    <style>
        @page {{ 
            size: A4; 
            margin: 15mm 15mm 20mm 15mm; 
        }}
        body {{ 
            font-family: "Times New Roman", Times, serif; 
            font-size: 11pt; 
            line-height: 1.45; 
            color: #2c3e50; 
            margin: 0; 
            padding: 0;
        }}
        .header {{ 
            border-bottom: 2px solid #27ae60; 
            padding-bottom: 8px; 
            margin-bottom: 15px; 
            text-align: center;
        }}
        .header h1 {{ 
            font-size: 15pt; 
            margin: 0; 
            color: #2c3e50;
            text-transform: uppercase;
            font-weight: bold;
        }}
        .section-title {{ 
            font-size: 12pt; 
            color: #2c3e50; 
            border-left: 4px solid #27ae60; 
            padding-left: 8px; 
            margin-top: 20px; 
            margin-bottom: 8px; 
            text-transform: uppercase;
            font-weight: bold;
        }}
        .subsection-title {{
            font-size: 10.5pt;
            font-weight: bold;
            color: #27ae60;
            margin: 12px 0 6px 0;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-bottom: 15px; 
            font-size: 9.5pt;
            page-break-inside: auto;
        }}
        tr {{
            page-break-inside: avoid;
        }}
        th, td {{ 
            border: 1px solid #bdc3c7; 
            padding: 6px 8px; 
            text-align: left; 
            vertical-align: top;
        }}
        th {{ 
            background-color: #f2f4f4; 
            color: #2c3e50;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #fafdff;
        }}
        .col-word {{ width: 18%; font-weight: bold; color: #27ae60; }}
        .col-phon {{ width: 14%; font-style: italic; color: #7f8c8d; }}
        .col-pos {{ width: 10%; font-weight: 500; }}
        .col-def {{ width: 28%; }}
        .col-ex {{ width: 30%; font-style: italic; }}
        
        .grammar-box {{
            background-color: #f8f9fa;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #27ae60;
            padding: 12px;
            margin-bottom: 15px;
            text-align: justify;
            page-break-inside: avoid;
        }}
        .tips-box {{
            background-color: #fff9f0;
            border: 1px solid #ffe8cc;
            border-left: 4px solid #e67e22;
            padding: 12px;
            margin-bottom: 15px;
            text-align: justify;
            page-break-inside: avoid;
        }}
        .link-list {{
            margin-top: 8px;
            padding-left: 20px;
        }}
        .link-list li {{
            margin-bottom: 4px;
        }}
        .link-list a {{
            color: #27ae60;
            text-decoration: none;
        }}
        .link-list a:hover {{
            text-decoration: underline;
        }}
        ul {{
            margin: 5px 0;
            padding-left: 20px;
        }}
    </style>
</head>
<body>

    <div class="header">
        <h1>VOCABULARY & GRAMMAR KNOWLEDGE - DAY {day_only}: {topic_upper}</h1>
    </div>

    <!-- VOCABULARY SECTION -->
    <div class="section-title">I. Vocabulary & Idioms Tables</div>
    
{vocab_tables_html}

{grouping_summary_html}

    <!-- GRAMMAR DETAIL & STRATEGY -->
    <div class="section-title">II. Grammar Detail & Strategy (Lý thuyết & Mẹo)</div>
    
{grammar_boxes_html}

    <!-- COMMON MISTAKES / IELTS TRAPS -->
    <div class="section-title">III. Common Mistakes / IELTS Traps for This Topic</div>
    <table>
        <thead>
            <tr>
                <th style="width: 25%;">Common mistake / Trap</th>
                <th style="width: 25%;">Wrong example</th>
                <th style="width: 25%;">Correct version</th>
                <th style="width: 25%;">Why it matters for IELTS</th>
            </tr>
        </thead>
        <tbody>
{mistakes_rows_html}
        </tbody>
    </table>

</body>
</html>
"""
    return html_content

def parse_explanation_items(md_text: str, is_grammar: bool = False, offset: int = 0) -> list[dict]:
    items = []
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        match = re.match(r'^(\d+)\.\s*(.*)', line)
        if match:
            q_num = int(match.group(1))
            rest = match.group(2).strip()
            
            display_num = q_num + offset
            
            ans_match = re.match(r'^\*\*(.*?)\*\*(.*)', rest)
            if ans_match:
                answer = ans_match.group(1).strip()
                rest_text = ans_match.group(2).strip()
                rest_text = re.sub(r'^[\s\-–—,\.\(\)\*]+', '', rest_text).strip()
                rest_text = rest_text.replace("*", "").strip()
            else:
                answer = ""
                rest_text = rest.replace("*", "").strip()
                
            sub_parts = []
            while i + 1 < len(lines) and (lines[i+1].strip().startswith("-") or lines[i+1].strip().startswith("*")):
                sub_line = lines[i+1].strip()
                # Strip leading bullet char and space only
                sub_line = re.sub(r'^[\-\*]\s+', '', sub_line).strip()
                
                # Check stretch
                is_bullet_stretch = "(*)" in sub_line or "stretch" in sub_line.lower()
                
                # Clean prefix like *Giải thích (*) (Stretch)*: or *Dữ kiện trong bài*:
                prefix_match = re.match(r'^\*?(Giải thích|Dữ kiện trong bài).*?\*?:\s*(.*)', sub_line, re.I)
                if prefix_match:
                    label = prefix_match.group(1).strip()
                    rest_content = prefix_match.group(2).strip()
                    stretch_lbl = " (Stretch)" if is_bullet_stretch else ""
                    formatted_sub = f"<b>{label}{stretch_lbl}:</b> {format_markdown_inline(rest_content)}"
                else:
                    formatted_sub = format_markdown_inline(sub_line)
                    
                sub_parts.append(formatted_sub)
                i += 1
                
            items.append({
                "num": display_num,
                "answer": answer,
                "rest": rest_text,
                "bullets": sub_parts
            })
        i += 1
    return items

def render_explanation_item(item: dict) -> str:
    num = item["num"]
    answer = item["answer"]
    rest = item["rest"]
    bullets = item["bullets"]
    
    html_parts = []
    header = f'<span class="answer-key">{num}. {answer}</span>'
    
    rest_clean = rest.strip()
    rest_is_explanation = False
    
    rest_lower = rest_clean.lower()
    if rest_lower.startswith("giải thích") or rest_lower.startswith("dữ kiện") or rest_lower.startswith("*giải thích*") or rest_lower.startswith("_giải thích_") or rest_lower.startswith("<i>giải thích") or rest_lower.startswith("<b>giải thích"):
        rest_is_explanation = True
        
    if rest_clean and not rest_is_explanation:
        header += f' - <i>{format_markdown_inline(rest_clean)}</i>'
        
    html_parts.append(header + "<br>")
    
    if rest_is_explanation:
        is_stretch = "(*)" in rest_clean or "stretch" in rest_clean.lower()
        prefix_match = re.match(r'^\*?(Giải thích|Dữ kiện trong bài).*?\*?:\s*(.*)', rest_clean, re.I)
        if prefix_match:
            label = prefix_match.group(1).strip()
            rest_content = prefix_match.group(2).strip()
            stretch_lbl = " (Stretch)" if is_stretch else ""
            formatted_rest = f"<b>{label}{stretch_lbl}:</b> {format_markdown_inline(rest_content)}"
        else:
            formatted_rest = format_markdown_inline(rest_clean)
        html_parts.append(formatted_rest + "<br>")
        
    for bullet in bullets:
        # Bullets are already formatted in parse_explanation_items
        html_parts.append(bullet + "<br>")
        
    inner_html = "".join(html_parts).strip()
    if inner_html.endswith("<br>"):
        inner_html = inner_html[:-4]
        
    return f'<div class="explanation-item">\n    {inner_html}\n</div>'

def parse_writing_answers(md_text: str) -> list[dict]:
    tasks = []
    current_task = None
    lines = md_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#### "):
            if current_task:
                tasks.append(current_task)
            current_task = {
                "title": re.sub(r'^[#\s\d\.]+', '', line).strip(),
                "lines": []
            }
        else:
            if current_task:
                current_task["lines"].append(line)
    if current_task:
        tasks.append(current_task)
    return tasks

def render_writing_answer_task(task: dict) -> str:
    html_parts = [f'<b>{task["title"]}</b><br>']
    in_list = False
    
    table_lines = []
    def flush_table():
        if table_lines:
            html_parts.append(parse_markdown_table_to_html("\n".join(table_lines)))
            table_lines.clear()

    for line in task["lines"]:
        line_str = line.strip()
        if not line_str:
            continue
        if line_str.startswith("|") and line_str.endswith("|"):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            table_lines.append(line_str)
        else:
            flush_table()
            if line_str.startswith("- ") or line_str.startswith("* "):
                if not in_list:
                    html_parts.append("<ul>")
                    in_list = True
                content = line_str[2:].strip()
                content = format_markdown_inline(content)
                html_parts.append(f"<li>{content}</li>")
            else:
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                if line_str.startswith(">"):
                    content = line_str[1:].strip()
                    content = format_markdown_inline(content)
                    html_parts.append(f'<div class="quote-text">{content}</div>')
                else:
                    html_parts.append(f"<p>{format_markdown_inline(line_str)}</p>")
    flush_table()
    if in_list:
        html_parts.append("</ul>")
    return f'<div class="sample-essay-box">\n    {"".join(html_parts)}\n</div>'

def render_review_bridge(md_text: str, is_answer: bool = False) -> str:
    html_parts = []
    lines = md_text.splitlines()
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        
        # Check if this line is an answer key or explanation detail
        is_ans_line = line_str.startswith("- ") or line_str.startswith("* ") or "đáp án:" in line_str.lower() or "giải thích:" in line_str.lower()
        if is_ans_line and not is_answer:
            continue
            
        if re.match(r'^\d+\.', line_str):
            html_parts.append(f"{format_markdown_inline(line_str)}<br>")
            if not is_answer:
                html_parts.append('<div class="writing-line"></div><br>')
        elif line_str.startswith("##") or line_str.startswith("####"):
            # Don't wrap headings in <p> tags
            # Strip markdown hashes
            clean_heading = re.sub(r'^#+\s*', '', line_str).strip()
            # Skip the duplicate Review Bridge header
            if "review bridge" in clean_heading.lower():
                continue
            # If it's V. in practice sheet but we want IV. in answer key, let's keep what's in the markdown
            html_parts.append(f'<div class="question-instruction" style="margin-top: 15px; font-size: 11.5pt;">{clean_heading}</div>')
        else:
            html_parts.append(f"<p>{format_markdown_inline(line_str)}</p>")
    return "\n".join(html_parts)

def build_answers_html(answers_md: str, day: str, topic: str, practice_md: str, skill_level: dict = None) -> str:
    sections = split_sections_by_heading(answers_md)
    practice_sections = split_sections_by_heading(practice_md)

    # Prefer explicit skill_level dict from lesson_meta; fall back to intro-section regex
    if skill_level:
        reading_level    = skill_level.get("reading_level",    "")
        grammar_level    = skill_level.get("grammar_level",    "")
        writing_level    = skill_level.get("writing_level",    "")
        vocabulary_level = skill_level.get("vocabulary_level", "")
    else:
        reading_level = writing_level = grammar_level = vocabulary_level = ""
        intro_sec = practice_sections.get("Intro", "")
        top_of_md = practice_md[:200]
        r_match = re.search(r'Reading:\s*([A-C][1-2]\+?)', intro_sec or top_of_md, re.I)
        if r_match:
            reading_level = r_match.group(1).upper()
        w_match = re.search(r'Writing:\s*([A-C][1-2]\+?)', intro_sec or top_of_md, re.I)
        if w_match:
            writing_level = w_match.group(1).upper()

    level_header_html = ""
    parts = []
    if reading_level:    parts.append(f"Reading {reading_level}")
    if grammar_level:    parts.append(f"Grammar {grammar_level}")
    if writing_level:    parts.append(f"Writing {writing_level}")
    if vocabulary_level: parts.append(f"Vocab {vocabulary_level}")
    if parts:
        level_header_html = f'\n        <h2>(Level: {" | ".join(parts)})</h2>'

    reading_offset = 13
    groups = parse_questions_section(practice_sections.get("Questions for Reading", ""))
    if groups:
        reading_offset = sum(len(g["questions"]) for g in groups)
        
    reading_sec = sections.get("Reading Answer Key and Detailed Explanations", "")
    if not reading_sec:
        for k in sections.keys():
            if "reading" in k.lower() and "answer" in k.lower():
                reading_sec = sections[k]
                break
    reading_items = parse_explanation_items(reading_sec, is_grammar=False, offset=0)
    reading_explanations_html = "\n\n".join(render_explanation_item(item) for item in reading_items)
    
    grammar_sec = sections.get("Grammar Answer Key and Detailed Explanations", "")
    if not grammar_sec:
        for k in sections.keys():
            if "grammar" in k.lower() and "answer" in k.lower():
                grammar_sec = sections[k]
                break
    grammar_items = parse_explanation_items(grammar_sec, is_grammar=True, offset=reading_offset)
    grammar_explanations_html = "\n\n".join(render_explanation_item(item) for item in grammar_items)
    
    writing_sec = sections.get("Writing Guidance / Suggested Answers", "")
    if not writing_sec:
        for k in sections.keys():
            if "writing" in k.lower() and ("guidance" in k.lower() or "suggested" in k.lower()):
                writing_sec = sections[k]
                break
    writing_tasks = parse_writing_answers(writing_sec)
    writing_answers_html = "\n\n".join(render_writing_answer_task(task) for task in writing_tasks)
    
    review_sec = sections.get("Review Bridge", "")
    if not review_sec:
        for k in sections.keys():
            if "review" in k.lower() or "bridge" in k.lower():
                review_sec = sections[k]
                break
    review_html = ""
    if review_sec:
        review_content = render_review_bridge(review_sec, is_answer=True)
        review_html = f"""    <!-- REVIEW BRIDGE -->
    <div class="review-bridge-container" style="page-break-before: always; page-break-inside: avoid;">
        <div class="section-title">IV. Review Bridge / Ôn tập</div>
        <div class="warmup-box">
            {review_content}
        </div>
    </div>"""
        
    day_only = re.sub(r'^Day\s+', '', day.strip(), flags=re.I)
    topic_upper = topic.upper()
    
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>ANSWER KEY & EXPLANATIONS - DAY {day_only}</title>
    <style>
        @page {{ 
            size: A4; 
            margin: 15mm 15mm 20mm 15mm; 
        }}
        body {{ 
            font-family: "Times New Roman", Times, serif; 
            font-size: 11pt; 
            line-height: 1.25; 
            color: #2c3e50; 
            margin: 0; 
            padding: 0;
        }}
        .header {{ 
            border-bottom: 2px solid #e74c3c; 
            padding-bottom: 6px; 
            margin-bottom: 10px; 
            text-align: center;
        }}
        .header h1 {{ 
            font-size: 14pt; 
            margin: 0; 
            color: #c0392b;
            text-transform: uppercase;
            font-weight: bold;
        }}
        .section-title {{ 
            font-size: 11pt; 
            color: #2c3e50; 
            border-left: 4px solid #e74c3c; 
            padding-left: 6px; 
            margin-top: 10px; 
            margin-bottom: 4px; 
            text-transform: uppercase;
            font-weight: bold;
        }}
        .explanation-item {{
            margin-bottom: 6px;
            padding-bottom: 4px;
            border-bottom: 1px dotted #e0e0e0;
            text-align: justify;
            page-break-inside: avoid;
        }}
        .answer-key {{
            font-weight: bold;
            color: #e74c3c;
        }}
        .quote-text {{
            font-style: italic;
            color: #555;
            background-color: #fcfcfc;
            border-left: 2px solid #bdc3c7;
            padding-left: 8px;
            margin: 2px 0;
        }}
        .sample-essay-box {{
            background-color: #fafbfc;
            border: 1px solid #dcdde1;
            padding: 6px 10px;
            margin-top: 5px;
            text-align: justify;
            page-break-inside: avoid;
        }}
        .data-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 6px 0; 
            font-size: 9.5pt; 
            page-break-inside: avoid;
        }}
        .data-table th {{ 
            background-color: #f2f4f8; 
            border: 1px solid #dcdde1; 
            padding: 4px 8px; 
            text-align: left; 
            font-weight: bold; 
            color: #2c3e50; 
        }}
        .data-table td {{ 
            border: 1px solid #dcdde1; 
            padding: 4px 8px; 
            color: #333; 
        }}
        .data-table tr:nth-child(even) {{ 
            background-color: #fafbfc; 
        }}
        .svg-chart-container {{
            text-align: center;
            margin: 10px 0;
            page-break-inside: avoid;
        }}
        .writing-line {{
            border-bottom: 1px dotted #bdc3c7;
            height: 22px;
            margin-top: 4px;
            margin-bottom: 2px;
            width: 98%;
            page-break-inside: avoid;
        }}
        .bold-vocab {{
            font-weight: bold;
            text-decoration: underline;
            color: #2980b9;
        }}
        ul {{
            margin: 2px 0;
            padding-left: 15px;
        }}
    </style>
</head>
<body>

    <div class="header">
        <h1>ANSWER KEY & EXPLANATIONS - DAY {day_only}: {topic_upper}</h1>{level_header_html}
    </div>

    <!-- READING ANSWERS -->
    <div class="section-title">I. Reading Passage Answers & Explanations</div>
    
{reading_explanations_html}

    <!-- GRAMMAR ANSWERS -->
    <div class="section-title">II. Grammar Practice Answers & Explanations</div>
    
{grammar_explanations_html}

    <!-- WRITING ANSWERS -->
    <div class="section-title">III. Writing Guidance / Suggested Answers</div>
    
{writing_answers_html}

{review_html}

</body>
</html>
"""
    return html_content

def build_vocab_checker_html(items_c1: list[dict], items_c2: list[dict], level: str, topic: str, day: str, is_answer: bool = False) -> str:
    day_only = re.sub(r'^Day\s+', '', day.strip(), flags=re.I)
    topic_upper = topic.upper()
    
    checker_1_rows = []
    for idx, item in enumerate(items_c1):
        # In the original parser, item["definition"] holds the Vietnamese meaning
        vi_mean = item["definition"].strip()
        if vi_mean:
            vi_mean = vi_mean[0].upper() + vi_mean[1:]
            
        ans_content = f'{item["word"]}' if is_answer else ""
        
        row_html = f"""        <div class="checker-row">
            <div class="checker-prompt"><b>{idx+1}.</b> {vi_mean}</div>
            <div class="checker-blank">{ans_content}</div>
        </div>"""
        checker_1_rows.append(row_html)
    checker_1_rows_html = "\n".join(checker_1_rows)

    checker_2_rows = []
    for idx, item in enumerate(items_c2):
        # In the original parser, item["vietnamese"] holds the English definition
        en_def = item["vietnamese"].strip()
        if en_def:
            en_def = en_def[0].upper() + en_def[1:]
            
        ans_content = f'{item["word"]}' if is_answer else ""
        
        row_html = f"""        <div class="checker-row">
            <div class="checker-prompt"><b>{idx+1}.</b> {en_def}</div>
            <div class="checker-blank">{ans_content}</div>
        </div>"""
        checker_2_rows.append(row_html)
    checker_2_rows_html = "\n".join(checker_2_rows)

    title_suffix = " (ANSWER KEY)" if is_answer else ""
    header_color = "#c0392b" if is_answer else "#2980b9"
    blank_color = "#c0392b" if is_answer else "#2c3e50"
    blank_weight = "bold" if is_answer else "normal"

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>VOCABULARY CHECKER{title_suffix} - DAY {day_only}</title>
    <style>
        @page {{ 
            size: A4; 
            margin: 15mm 15mm 20mm 15mm; 
        }}
        body {{ 
            font-family: "Times New Roman", Times, serif; 
            font-size: 11pt; 
            line-height: 1.45; 
            color: #2c3e50; 
            margin: 0; 
            padding: 0;
        }}
        .header {{ 
            border-bottom: 2px solid {header_color}; 
            padding-bottom: 8px; 
            margin-bottom: 15px; 
            text-align: center;
        }}
        .header h1 {{ 
            font-size: 15pt; 
            margin: 0; 
            color: {header_color};
            text-transform: uppercase;
            font-weight: bold;
        }}
        .instruction {{
            font-style: italic;
            margin-bottom: 15px;
            color: #555;
            font-size: 10pt;
        }}
        .checker-container {{
            column-count: 2;
            column-gap: 30px;
            column-rule: 1px solid #dcdde1;
        }}
        .checker-row {{
            break-inside: avoid;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 22px;
            padding-bottom: 4px;
            border-bottom: 1px dashed #b2bec3;
        }}
        .checker-prompt {{
            font-size: 10pt;
            width: 55%;
            text-align: justify;
            line-height: 1.3;
        }}
        .checker-blank {{
            width: 42%;
            border-bottom: 1px solid #2c3e50;
            height: 22px;
            color: {blank_color};
            font-weight: {blank_weight};
            text-align: center;
            line-height: 22px;
        }}
        .page-break {{
            page-break-before: always;
        }}
    </style>
</head>
<body>

    <div class="header">
        <h1>VOCABULARY CHECKER 1: VIETNAMESE TO ENGLISH RECALL{title_suffix}</h1>
        <div style="font-size: 10pt; font-weight: bold; margin-top: 5px;">
            Day: {day_only} | Level: {level} | Topic: {topic_upper}
        </div>
    </div>
    <div class="instruction">
        Hướng dẫn: Viết từ/cụm từ tiếng Anh chính xác tương ứng với nghĩa tiếng Việt dưới đây.
    </div>

    <div class="checker-container">
{checker_1_rows_html}
    </div>

    <div class="page-break"></div>

    <div class="header">
        <h1>VOCABULARY CHECKER 2: DEFINITION TO ENGLISH RECALL{title_suffix}</h1>
        <div style="font-size: 10pt; font-weight: bold; margin-top: 5px;">
            Day: {day_only} | Level: {level} | Topic: {topic_upper}
        </div>
    </div>
    <div class="instruction">
        Instructions: Write the correct English word/phrase that matches the definition below.
    </div>

    <div class="checker-container">
{checker_2_rows_html}
    </div>

</body>
</html>
"""
    return html_content

def generate_quizlet_markdown(vocab_items: list[dict]) -> str:
    # Section 1: Simple Vocabulary List (2 columns: English Word vs Vietnamese Meaning)
    lines_part1 = [
        "### Phần 1: Học từ vựng đơn giản (Simple Vocabulary)",
        "| Từ vựng tiếng Anh | Nghĩa tiếng Việt |",
        "| --- | --- |"
    ]
    for item in vocab_items:
        # In the original parser, item["definition"] holds the Vietnamese meaning
        vi_mean = item["definition"].strip()
        lines_part1.append(f"| {item['word']} | {vi_mean} |")
        
    # Section 2: Detailed Vocabulary List (2 columns: Word + IPA + Type vs Vietnamese Meaning)
    lines_part2 = [
        "### Phần 2: Học từ vựng đầy đủ (Detailed Vocabulary)",
        "| Từ vựng + IPA + Loại từ | Nghĩa tiếng Việt |",
        "| --- | --- |"
    ]
    for item in vocab_items:
        ipa = item["ipa"].strip()
        vocab_type = item["type"].strip()
        vi_mean = item["definition"].strip()
        
        # Format: word /ipa, type/
        if ipa.startswith("/") and ipa.endswith("/"):
            detailed_word = f"{item['word']} {ipa[:-1]}, {vocab_type}/"
        else:
            detailed_word = f"{item['word']} {ipa}, {vocab_type}"
            
        lines_part2.append(f"| {detailed_word} | {vi_mean} |")
        
    return "\n".join(lines_part1) + "\n\n" + "\n".join(lines_part2) + "\n"

def generate_quizlet_text(vocab_items: list[dict]) -> str:
    lines = []
    for item in vocab_items:
        en_def = item["definition"].strip()
        vi_mean = item["vietnamese"].strip()
        line = f"{item['word']} ({item['ipa']}) [{item['type']}]\t{en_def} - {vi_mean}. Ví dụ: {item['example']}"
        lines.append(line)
    return "\n".join(lines) + "\n"

def compile_html_to_pdf(html_path: Path, pdf_path: Path, lesson_id: str = "", doc_type: str = "") -> None:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(html_path.absolute().as_uri())
            
            margin = {"top": "15mm", "bottom": "20mm", "left": "15mm", "right": "15mm"}
            
            footer_template = f"""
                <div style="font-size: 8pt; font-family: 'Times New Roman', Times, serif; color: #7f8c8d; width: 100%; display: flex; justify-content: space-between; border-top: 1px solid #e0e0e0; padding-top: 5px; margin: 0 15mm 5mm 15mm; box-sizing: border-box;">
                    <span>Lesson ID: {lesson_id}</span>
                    <span>{doc_type}</span>
                    <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
                </div>
            """
            
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin=margin,
                display_header_footer=True,
                header_template="<span></span>",
                footer_template=footer_template
            )
            browser.close()
    except Exception as e:
        print(f"\nWARNING: Could not compile PDF {pdf_path.name} because of error: {e}", file=sys.stderr)
        print("Please close any applications holding a lock on this file (e.g. PDF readers) and try again.\n", file=sys.stderr)

def convert_json_to_markdown_fields(data: dict) -> dict:
    if "reading" in data and "practice_markdown" in data:
        data = data.copy()
        data.pop("practice_markdown", None)

    if "practice_markdown" in data:
        return data
        
    converted = data.copy()
    
    # Sort and re-index reading questions by type to ensure consecutive numbering
    reading = converted.get("reading", {})
    rqs = reading.get("questions", [])
    if rqs:
        by_type = {}
        for q in rqs:
            q_type = q.get("type", "Questions")
            by_type.setdefault(q_type, []).append(q)
            
        for q_type in by_type:
            by_type[q_type].sort(key=lambda x: (x.get("evidence_paragraph", 0), x.get("id", 0)))
            
        type_order = ["Heading Matching", "True/False/Not Given", "Gap Fill", "Multiple Choice"]
        all_types = list(by_type.keys())
        sorted_types = sorted(all_types, key=lambda t: type_order.index(t) if t in type_order else len(type_order))
        
        sorted_qs = []
        for q_type in sorted_types:
            sorted_qs.extend(by_type[q_type])
            
        old_to_new = {}
        for new_idx, q in enumerate(sorted_qs):
            old_id = q["id"]
            new_id = new_idx + 1
            old_to_new[old_id] = new_id
            q["id"] = new_id
            
        converted["reading"] = reading.copy()
        converted["reading"]["questions"] = sorted_qs
        
        # Update answer keys
        answers = converted.get("answers", {})
        r_answers = answers.get("reading_answers", [])
        if r_answers:
            new_ans = []
            for ans in r_answers:
                old_qid = ans["question_id"]
                if old_qid in old_to_new:
                    ans_copy = ans.copy()
                    ans_copy["question_id"] = old_to_new[old_qid]
                    new_ans.append(ans_copy)
            new_ans.sort(key=lambda a: a["question_id"])
            converted["answers"] = answers.copy()
            converted["answers"]["reading_answers"] = new_ans
    
    data = converted
    meta = data.get("lesson_meta", {})
    level = meta.get("level", data.get("level", "A2"))
    topic = meta.get("topic", data.get("topic", ""))
    day = meta.get("day", data.get("day", ""))
    
    pm = []
    writing_level_map = {
        "A1": "A1",
        "A2": "A2",
        "B1": "A2",
        "B2": "B1",
        "C1": "B2",
        "C2": "C1"
    }
    w_level = writing_level_map.get(level, "A1")
    pm.append(f"Reading: {level}")
    pm.append(f"Writing: {w_level}")
    pm.append("")

    source = data.get("source", {})
    if source:
        pm.append("## Reading Source Verification")
        pm.append("| Source title | Publisher/Organization | Date/Access date | Final verified URL | URL status | Source type | Reliability check | How the passage uses the source |")
        pm.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        pm.append(f"| {source.get('source_title', '')} | {source.get('publisher', '')} | {source.get('published_date', '')} / {source.get('access_date', '')} | {source.get('verified_url', '')} | {source.get('url_status', 'Active')} | {source.get('source_type', 'Educational News Article')} | {source.get('credibility_note', '')} | {source.get('topic_relevance_note', '')} |")
        pm.append("")
        
    pm.append("## Warm-up")
    pm.append("Answer the following questions in English:")
    warmups = data.get("warm_up")
    if warmups and isinstance(warmups, list) and len(warmups) == 3:
        for idx, wq in enumerate(warmups):
            pm.append(f"{idx+1}. {wq}")
    else:
        pm.append("1. Bạn nghĩ gì về chủ đề này? (What do you think about this topic?)")
        pm.append("2. Chia sẻ một trải nghiệm thực tế của bạn liên quan đến chủ đề này. (Share a real experience related to this topic.)")
        pm.append("3. Tại sao chủ đề này lại quan trọng đối với cuộc sống hàng ngày? (Why is this topic important in daily life?)")
    pm.append("")
    
    reading = data.get("reading", {})
    passage = reading.get("passage", {})
    if passage:
        pm.append("## Reading Passage")
        pm.append(f"### {passage.get('title', '')}")
        pm.append("")
        for p in passage.get("paragraphs", []):
            pm.append(p.get("text", ""))
            pm.append("")
            
    rqs = reading.get("questions", [])
    if rqs:
        pm.append("## Questions for Reading")
        by_type = {}
        for q in rqs:
            q_type = q.get("type", "Questions")
            by_type.setdefault(q_type, []).append(q)
            
        for q_type, q_list in by_type.items():
            start_num = q_list[0]["id"]
            end_num = q_list[-1]["id"]
            range_str = f"Questions {start_num}–{end_num}: " if start_num != end_num else f"Question {start_num}: "
            pm.append(f"### {range_str}{q_type}")
            pm.append("")
            for q in q_list:
                stretch_mark = " (*)" if q.get("stretch") else ""
                options_str = ""
                if q.get("options"):
                    letters = ["A", "B", "C", "D", "E", "F"]
                    options_str = "\n" + "\n".join([f"    {letters[opt_idx]}. {opt}" for opt_idx, opt in enumerate(q["options"])])
                pm.append(f"{q['id']}. {q['question']}{stretch_mark}{options_str}")
            pm.append("")
            
    grammar = data.get("grammar", {})
    gqs = grammar.get("questions", [])
    if gqs:
        pm.append("## Questions for Grammar")
        by_type = {}
        for q in gqs:
            q_type = q.get("type", "Grammar Exercise")
            by_type.setdefault(q_type, []).append(q)
            
        for q_type, q_list in by_type.items():
            pm.append(f"### {q_type}")
            pm.append("")
            for q in q_list:
                stretch_mark = " (*)" if q.get("stretch") else ""
                options_str = ""
                if q.get("options"):
                    letters = ["A", "B", "C", "D", "E", "F"]
                    options_str = "\n" + "\n".join([f"    {letters[opt_idx]}. {opt}" for opt_idx, opt in enumerate(q["options"])])
                pm.append(f"{q['id']}. {q['question']}{stretch_mark}{options_str}")
            pm.append("")
            
    writing = data.get("writing", {})
    tasks = writing.get("tasks", [])
    if tasks:
        pm.append("## Questions for Writing")
        pm.append("| # | Task | Target length | Focus skill | Useful language | Success criteria |")
        pm.append("| --- | --- | --- | --- | --- | --- |")
        for t in tasks:
            visual_prefix = ""
            vis = t.get("visual_data", {})
            if vis.get("type") in ["markdown_table", "svg"] and vis.get("content"):
                visual_prefix = "<br><br>" + vis["content"].replace("\n", "<br>")
            
            prompt_clean = t.get('prompt', '').replace('\n', '<br>')
            if vis.get("content"):
                prompt_clean = re.sub(r'<svg[^>]*>.*?</svg>', '', prompt_clean, flags=re.DOTALL|re.I)
                prompt_clean = re.sub(r'<table[^>]*>.*?</table>', '', prompt_clean, flags=re.DOTALL|re.I)
                
            task_type = t.get('task_type', '')
            if task_type:
                prompt_clean = re.sub(r'^' + re.escape(task_type) + r'\s*:\s*', '', prompt_clean, flags=re.IGNORECASE).strip()
                task_types_pattern = r'^(Word\s+Ordering|Sentence\s+Completion|Translation|Short\s+Description|Visual\s+Data\s+Description|Data\s+Description|Guided\s+Email\s+Invite|Email|Word\s+order|Sentence\s+completion|Visual\s+data\s+description|Guided\s+email\s+invite)\s*:\s*'
                prompt_clean = re.sub(task_types_pattern, '', prompt_clean, flags=re.IGNORECASE).strip()
                
            task_cell = f"{task_type}: {prompt_clean}{visual_prefix}"
            task_cell = task_cell.replace("|", "\\|")
            
            lang_cell = "<br>".join(t.get("useful_language", []))
            crit_cell = "<br>".join(t.get("success_criteria", []))
            pm.append(f"| {t.get('id', 1)} | {task_cell} | {t.get('target_length', '')} | {t.get('focus_skill', '')} | {lang_cell} | {crit_cell} |")
        pm.append("")
        
    answers = data.get("answers", {})
    review_bridge = answers.get("review_bridge", [])
    if review_bridge:
        pm.append("## Review Bridge")
        pm.append("#### V. Review Bridge / Ôn tập liên chủ đề")
        for idx, rb in enumerate(review_bridge):
            pm.append(f"{idx+1}. {rb.get('prompt', '')}")
            pm.append("")
            
    converted["practice_markdown"] = "\n".join(pm)
    
    vgm = []
    vocab = data.get("vocabulary", {})
    v_items = vocab.get("items", [])
    if v_items:
        vgm.append("## Vocabulary Table")
        vgm.append("| Từ/Cụm từ | Phiên âm | Loại từ | Định nghĩa và Tiếng Việt | Ví dụ minh họa |")
        vgm.append("| --- | --- | --- | --- | --- |")
        for item in v_items:
            vgm.append(f"| {item.get('term', '')} | {item.get('ipa', '')} | {item.get('part_of_speech', '')} | {item.get('meaning_vi', '')} ({item.get('definition_en', '')}) | {item.get('example', '')} |")
        vgm.append("")
        
    v_recycled = vocab.get("recycled_items", [])
    if v_recycled:
        vgm.append("## Recycled Vocabulary (Từ vựng ôn tập)")
        vgm.append("| Từ/Cụm từ | Phiên âm | Loại từ | Định nghĩa và Tiếng Việt | Bài học gốc (Day) |")
        vgm.append("| --- | --- | --- | --- | --- |")
        for item in v_recycled:
            vgm.append(f"| {item.get('term', '')} | {item.get('ipa', '')} | {item.get('part_of_speech', '')} | {item.get('meaning_vi', '')} | Day {item.get('source_day', '')} |")
        vgm.append("")
        
    guide = grammar.get("guide", [])
    if guide:
        vgm.append("## Detailed Grammar Guide")
        for g in guide:
            vgm.append(g.get("heading", "#### Chủ điểm:"))
            vgm.append(g.get("content", ""))
            vgm.append("")
            
    mistakes = grammar.get("common_mistakes", [])
    if mistakes:
        vgm.append("## Common Mistakes / IELTS Traps for This Topic")
        vgm.append("| Common mistake / Trap | Wrong example | Correct version | Why it matters for IELTS |")
        vgm.append("| --- | --- | --- | --- |")
        for m in mistakes:
            vgm.append(f"| {m.get('trap', '')} | {m.get('wrong_example', '')} | {m.get('correct_version', '')} | {m.get('why_it_matters', '')} |")
        vgm.append("")
        
    converted["vocabulary_grammar_markdown"] = "\n".join(vgm)
    
    am = []
    answers = data.get("answers", {})
    r_ans = answers.get("reading_answers", [])
    if r_ans:
        am.append("## Reading Answer Key and Detailed Explanations")
        am.append("")
        am.append("📖 **Tóm tắt bài đọc:** Bài đọc mô tả chi tiết thông tin từ nguồn đã xác thực.")
        am.append("")
        for idx, ra in enumerate(r_ans):
            q_id = ra.get("question_id", idx + 1)
            stretch_mark = " *[Stretch Point]*" if ra.get("stretch_note") else ""
            am.append(f"{q_id}. **{ra.get('correct_answer', '')}**{stretch_mark}")
            am.append(f"- Bằng chứng: \"{ra.get('evidence_quote', '')}\" (§{ra.get('evidence_paragraph', 1)})")
            am.append(f"- Cách tìm đáp án: {ra.get('explanation_vi', '')} {ra.get('why_others_wrong_vi', '')}")
            if ra.get("tip_vi"):
                am.append(f"> **💡 Mẹo:** {ra['tip_vi']}")
            am.append("")
            
    g_ans = answers.get("grammar_answers", [])
    if g_ans:
        am.append("## Grammar Answer Key and Detailed Explanations")
        am.append("")
        am.append("> **Bảng phân biệt nhanh / Công thức bỏ túi:**")
        am.append("> - Ôn tập lý thuyết đã học trong bài.")
        am.append("")
        for idx, ga in enumerate(g_ans):
            q_id = ga.get("question_id", idx + 1)
            am.append(f"{q_id}. **{ga.get('correct_answer', '')}**")
            am.append(f"- Dấu hiệu / Phân tích: {ga.get('analysis_vi', '')}")
            if ga.get("tip_vi"):
                am.append(f"> **💡 Mẹo:** {ga['tip_vi']}")
            am.append("")
            
    w_guidance = answers.get("writing_guidance", [])
    if w_guidance:
        am.append("## Writing Guidance / Suggested Answers")
        am.append("")
        for idx, wg in enumerate(w_guidance):
            t_id = wg.get("task_id", idx + 1)
            am.append(f"#### Task {t_id}")
            m_ans = wg.get('model_answer', '').strip()
            if m_ans.startswith("|"):
                am.append("**Suggested Model Answer:**")
                am.append(m_ans)
            else:
                am.append("> **Suggested Model Answer:**")
                am.append(f"> \"{m_ans}\"")
            am.append("")
            am.append(f"- **Hướng dẫn viết từng câu / từng bước:** {wg.get('guidance_vi', '')}")
            checklist = wg.get("self_checklist", [])
            if checklist:
                checklist_str = " ".join([f"* {item}" for item in checklist])
                am.append(f"- *Tự kiểm tra:* {checklist_str}")
            am.append("")
            
    rev_bridge = answers.get("review_bridge", [])
    if rev_bridge:
        am.append("## Review Bridge")
        am.append("#### IV. Review Bridge / Ôn tập liên chủ đề")
        for idx, rb in enumerate(rev_bridge):
            am.append(f"{idx+1}. {rb.get('prompt', '')}")
            am.append(f"- **Đáp án:** {rb.get('correct_answer', '')}")
            am.append(f"- **Giải thích:** {rb.get('rationale_vi', '')}")
            am.append("")
            
    converted["answers_markdown"] = "\n".join(am)
    
    qm = []
    quizlet = vocab.get("quizlet", {})
    if quizlet:
        qm.append("## Section 1: Simple Vocabulary List (Học từ vựng đơn giản)")
        qm.append("| Từ vựng tiếng Anh | Nghĩa tiếng Việt |")
        qm.append("| --- | --- |")
        for s1 in quizlet.get("section_1_simple", []):
            parts = s1.split(" : ")
            if len(parts) == 2:
                qm.append(f"| {parts[0].strip()} | {parts[1].strip()} |")
        qm.append("")
        
        qm.append("## Section 2: Detailed Vocabulary List (Học từ vựng đầy đủ)")
        qm.append("| Từ vựng + IPA + Loại từ | Nghĩa tiếng Việt |")
        qm.append("| --- | --- |")
        for s2 in quizlet.get("section_2_detailed", []):
            parts = s2.split(" : ")
            if len(parts) == 2:
                qm.append(f"| {parts[0].strip()} | {parts[1].strip()} |")
        qm.append("")
        
    converted["quizlet_markdown"] = "\n".join(qm)
    
    return converted

def append_to_history(data: dict) -> None:
    try:
        level = str(data.get("level", "A2"))
        day = str(data.get("day", ""))
        day_part = re.sub(r"^Day\s+", "", day.strip(), flags=re.I)
        meta = data.get("lesson_meta", {})
        topic = meta.get("topic", data.get("topic", ""))
        specific_topic = meta.get("specific_topic", "")
        if specific_topic:
            # Format to Title Case if it seems fully lowercase
            words = specific_topic.split()
            lower_words = {"in", "on", "at", "for", "to", "and", "but", "or", "the", "a", "an", "with", "against", "of"}
            title_words = [
                w.capitalize() if idx == 0 or w.lower() not in lower_words else w.lower()
                for idx, w in enumerate(words)
            ]
            source_title = " ".join(title_words)
        else:
            source_title = data.get("source", {}).get("source_title") or meta.get("theme", "") or topic
        
        if not day_part or not level:
            return
            
        history_path = Path("outputs/ielts-daily-reading-writing/lesson_history.txt")
        history_path.parent.mkdir(parents=True, exist_ok=True)
        
        new_entry = f"{level} | {day_part} | {topic} | {source_title}"
        
        existing_content = ""
        if history_path.exists():
            existing_content = history_path.read_text(encoding="utf-8")
            
        # Check if this exact day and level already exists in the history to avoid duplicate entries
        duplicate = False
        for line in existing_content.splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2 and parts[0] == level and parts[1] == day_part:
                duplicate = True
                break
                
        if not duplicate:
            # Ensure trailing newline in existing content
            if existing_content and not existing_content.endswith("\n"):
                existing_content += "\n"
            existing_content += new_entry + "\n"
            history_path.write_text(existing_content, encoding="utf-8")
            print(f"Logged lesson history entry: {new_entry}")
    except Exception as e:
        print(f"WARNING: Could not update lesson history: {e}", file=sys.stderr)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Daily pack JSON file")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    
    # Fill in printed_time_allowed_minutes if missing before validation
    meta = data.setdefault("lesson_meta", {})
    if not meta.get("printed_time_allowed_minutes"):
        rqs = data.get("reading", {}).get("questions", [])
        gqs = data.get("grammar", {}).get("questions", [])
        wts = data.get("writing", {}).get("tasks", [])
        
        est_time = 8.0 + len(rqs) * 1.5
        for g in gqs:
            g_type = g.get("type", "").lower()
            if any(k in g_type for k in ["transform", "correct", "rewrite", "combine"]):
                est_time += 1.5
            else:
                est_time += 0.8
        est_time += 4.5
        for w in wts:
            target = w.get("target_length", "").lower()
            task_type = w.get("task_type", "").lower()
            if "1 sentence" in target or "sentence building" in task_type:
                est_time += 3.0
            elif any(x in target for x in ["sentence", "50-60 words", "40-50 words", "35-40 words", "paragraph"]):
                est_time += 6.0
            else:
                est_time += 15.0
        
        printed_time = int(round(est_time))
        meta["printed_time_allowed_minutes"] = printed_time
        meta["estimated_completion_time_minutes"] = printed_time
        meta["time_workload_status"] = "ok"
        Path(args.json_file).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Run JSON schema and pedagogical validations
    from validate_lesson_json import validate_lesson_json
    if not validate_lesson_json(Path(args.json_file)):
        print("FAIL: JSON validation failed. Exiting.", file=sys.stderr)
        sys.exit(1)
        
    # Safety checks for compilation loops
    if "execution" in data:
        exec_meta = data.get("execution", {})
        pipeline_status = exec_meta.get("pipeline_status")
        
        # 1. Refuse export if pipeline status is not qc_passed or exported
        if pipeline_status not in ["qc_passed", "exported"]:
            print(f"FAIL: cannot export PDF because pipeline_status is {pipeline_status}.", file=sys.stderr)
            sys.exit(1)
            
        # 2. Refuse export if unresolved high/critical challenges exist
        agent_rev = data.get("agent_review", {})
        challenges = agent_rev.get("challenges", [])
        for chg in challenges:
            if chg.get("status") == "open" and chg.get("severity") in ["high", "critical"]:
                print(f"FAIL: open high-severity challenge {chg.get('id')} must be resolved before export.", file=sys.stderr)
                sys.exit(1)
                
        # 3. Refuse export in Review Mode if required checkpoint approval is missing
        mode = exec_meta.get("mode")
        if mode == "review":
            human_rev = data.get("human_review", {})
            checkpoints = human_rev.get("checkpoints", [])
            pre_pdf_approved = False
            for cp in checkpoints:
                if cp.get("checkpoint") == "pre_pdf_approval" and cp.get("status") == "approved":
                    pre_pdf_approved = True
            if not pre_pdf_approved:
                print("FAIL: review mode requires pre_pdf_approval but checkpoint is missing.", file=sys.stderr)
                sys.exit(1)
    
    # Adapter for structured JSON compilation
    if "practice_markdown" not in data or "reading" in data:
        if "reading" in data:
            data.pop("practice_markdown", None)
            data.pop("vocabulary_grammar_markdown", None)
            data.pop("answers_markdown", None)
            data.pop("quizlet_markdown", None)
        meta = data.get("lesson_meta", {})
        if meta:
            data["level"] = meta.get("level", "A2")
            data["topic"] = meta.get("topic", "")
            data["day"] = meta.get("day", "")
            data["lesson_id"] = meta.get("lesson_id", "")
        data = convert_json_to_markdown_fields(data)

    level = str(data.get("level", "A2"))
    topic = str(data.get("topic", "Daily Topic"))
    day = str(data.get("day", "Day 00000000"))
    
    lesson_id = data.get("lesson_id")
    if not lesson_id:
        day_part = re.sub(r"^Day\s+", "", day.strip(), flags=re.I)
        level_part = safe_filename_part(level)
        rand_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        lesson_id = f"LSN-{day_part}-{level_part}-{rand_str}"
        
    names = build_names(level, topic, day)
    
    if args.out_dir is None:
        day_part = re.sub(r"^Day\s+", "", day.strip(), flags=re.I)
        level_part = safe_filename_part(level)
        out_dir = Path("outputs") / "ielts-daily-reading-writing" / f"{day_part}-{level_part}"
    else:
        out_dir = Path(args.out_dir)
        
    out_dir.mkdir(parents=True, exist_ok=True)
    
    lsn_dir = out_dir / "lsn"
    aws_dir = out_dir / "aws"
    lsn_dir.mkdir(parents=True, exist_ok=True)
    aws_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the original input JSON payload as the source of truth
    source_json_path = out_dir / "lesson_source.json"
    source_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if Path(args.json_file).resolve() != source_json_path.resolve():
        try:
            Path(args.json_file).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    part1_html_path = out_dir / "part1_practice_sheet.html"
    part2_html_path = out_dir / "part2_materials.html"
    part3_html_path = out_dir / "part3_answer_key.html"
    vocab_checker_html_path = out_dir / "vocab_checker.html"
    vocab_checker_answer_html_path = out_dir / "vocab_checker_answer.html"
    
    practice_pdf_path = lsn_dir / names["practice_pdf"]
    vocab_grammar_pdf_path = lsn_dir / names["vocab_grammar_pdf"]
    answers_pdf_path = aws_dir / names["answers_pdf"]
    vocab_checker_pdf_path = lsn_dir / names["vocab_checker_pdf"]
    vocab_checker_answer_pdf_path = aws_dir / names["vocab_checker_answer_pdf"]
    quizlet_md_path = out_dir / names["quizlet_md"]
    quizlet_txt_path = out_dir / names["quizlet_txt"]

    # Parse vocab from the full 5-column vocabulary_grammar_markdown table.
    # quizlet_markdown is 2-column and will always fail the len(parts)>=4 check.
    vocab_items = parse_vocab_from_markdown(data.get("vocabulary_grammar_markdown", ""))
    if not vocab_items:
        vocab_items = parse_vocab_from_markdown(data.get("quizlet_markdown", ""))
    vocab_words = [item["word"] for item in vocab_items] if vocab_items else []

    printed_time = data.get("lesson_meta", {}).get("printed_time_allowed_minutes")
    skill_level = data.get("lesson_meta", {}).get("skill_level") or {}
    # If skill_level dict is absent, build it from flat lesson_meta keys
    if not skill_level:
        meta_sl = data.get("lesson_meta", {})
        skill_level = {
            "reading_level":    meta_sl.get("reading_level", ""),
            "grammar_level":    meta_sl.get("grammar_level", ""),
            "writing_level":    meta_sl.get("writing_level", ""),
            "vocabulary_level": meta_sl.get("vocabulary_level", ""),
        }
    practice_html_content = build_practice_html(data.get("practice_markdown", ""), level, topic, day, vocab_words, time_allowed=printed_time, skill_level=skill_level)
    materials_html_content = build_materials_html(data.get("vocabulary_grammar_markdown", ""), data.get("quizlet_markdown", ""), day, topic)
    answers_html_content = build_answers_html(data.get("answers_markdown", ""), day, topic, data.get("practice_markdown", ""), skill_level=skill_level)
    
    # Shuffle vocab items once for the checker sheets
    # 1. Shuffle vocab_items for Checker 1 (Vietnamese to English)
    items_c1 = list(vocab_items)
    while True:
        random.shuffle(items_c1)
        if len(vocab_items) <= 1 or [x["word"] for x in items_c1] != [x["word"] for x in vocab_items]:
            break
            
    # 2. Shuffle vocab_items for Checker 2 (English Definition to English)
    items_c2 = list(vocab_items)
    while True:
        random.shuffle(items_c2)
        if len(vocab_items) <= 1 or ([x["word"] for x in items_c2] != [x["word"] for x in vocab_items] and [x["word"] for x in items_c2] != [x["word"] for x in items_c1]):
            break

    vocab_checker_html_content = build_vocab_checker_html(items_c1, items_c2, level, topic, day, is_answer=False)
    vocab_checker_answer_html_content = build_vocab_checker_html(items_c1, items_c2, level, topic, day, is_answer=True)

    part1_html_path.write_text(practice_html_content, encoding="utf-8")
    part2_html_path.write_text(materials_html_content, encoding="utf-8")
    part3_html_path.write_text(answers_html_content, encoding="utf-8")
    vocab_checker_html_path.write_text(vocab_checker_html_content, encoding="utf-8")
    vocab_checker_answer_html_path.write_text(vocab_checker_answer_html_content, encoding="utf-8")

    compile_html_to_pdf(part1_html_path, practice_pdf_path, lesson_id, "Daily Practice Sheet")
    compile_html_to_pdf(part2_html_path, vocab_grammar_pdf_path, lesson_id, "Vocabulary & Grammar Guide")
    compile_html_to_pdf(part3_html_path, answers_pdf_path, lesson_id, "Answer Key & Explanations")
    compile_html_to_pdf(vocab_checker_html_path, vocab_checker_pdf_path, lesson_id, "Vocabulary Checker")
    compile_html_to_pdf(vocab_checker_answer_html_path, vocab_checker_answer_pdf_path, lesson_id, "Vocabulary Checker Answer Key")
    
    # Run post-render validation
    print("Running Post-Render PDF Quality Control...")
    try:
        sys.path.append(str(Path(__file__).parent))
        from validate_rendered_pdf import validate_rendered_pdf
        pdf_errors = validate_rendered_pdf(source_json_path, practice_pdf_path)
        if pdf_errors:
            print("\nFAIL: Rendered PDF QC failed with the following errors:", file=sys.stderr)
            for err in pdf_errors:
                print(f" - {err}", file=sys.stderr)
            sys.exit(1)
        else:
            print("Post-Render PDF Quality Control PASSED successfully!")
    except Exception as e:
        # Fallback to subprocess if import fails or other error
        import subprocess
        script_path = Path(__file__).parent / "validate_rendered_pdf.py"
        res = subprocess.run([sys.executable, str(script_path), "--lesson-json", str(source_json_path), "--pdf", str(practice_pdf_path)], capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            print("\nFAIL: Rendered PDF QC failed:", file=sys.stderr)
            print(res.stdout, file=sys.stderr)
            print(res.stderr, file=sys.stderr)
            sys.exit(1)
        else:
            print("Post-Render PDF Quality Control PASSED successfully!")

    append_to_history(data)

    quizlet_md_content = generate_quizlet_markdown(vocab_items)
    quizlet_txt_content = generate_quizlet_text(vocab_items)
    
    quizlet_md_path.write_text(quizlet_md_content, encoding="utf-8")
    quizlet_txt_path.write_text(quizlet_txt_content, encoding="utf-8")

    result = {
        "part1_html": str(part1_html_path),
        "part2_html": str(part2_html_path),
        "part3_html": str(part3_html_path),
        "vocab_checker_html": str(vocab_checker_html_path),
        "vocab_checker_answer_html": str(vocab_checker_answer_html_path),
        "practice_pdf": str(practice_pdf_path),
        "vocab_grammar_pdf": str(vocab_grammar_pdf_path),
        "answers_pdf": str(answers_pdf_path),
        "vocab_checker_pdf": str(vocab_checker_pdf_path),
        "vocab_checker_answer_pdf": str(vocab_checker_answer_pdf_path),
        "quizlet_md": str(quizlet_md_path),
        "quizlet_txt": str(quizlet_txt_path),
        "lesson_id": lesson_id
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
