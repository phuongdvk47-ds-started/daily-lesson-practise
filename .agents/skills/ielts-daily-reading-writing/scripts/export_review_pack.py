#!/usr/bin/env python3
"""Export IELTS review pack sections to HTMLs and compile to four PDFs via Playwright.
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

# Reconfigure stdout to use utf-8 for unicode printing on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def safe_filename_part(value: str) -> str:
    value = re.sub(r"^Day\s+", "", str(value).strip(), flags=re.I)
    value = re.sub(r"[^\w\s.-]+", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"-+", "-", value)
    return value or "Review-Pack"

def build_names(level: str, days: list[str]) -> dict[str, str]:
    day_str = f"{days[0]}-{days[-1]}" if len(days) > 1 else f"{days[0]}"
    base = f"{safe_filename_part(level)}-Review-{day_str}"
    return {
        "practice_pdf": f"{base}-Practise.pdf",
        "answers_pdf": f"{base}-Answers.pdf",
        "vocab_checker_pdf": f"{base}-Vocab-Checker.pdf",
        "vocab_checker_answer_pdf": f"{base}-Vocab-Checker-Answer.pdf",
    }

def format_markdown_inline(text: str) -> str:
    # Protect underscores by converting them to blanks
    text = re.sub(r'_{3,}', '<span class="fill-blank"></span>', text)
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
    "suggested answers"
]

def is_major_section_heading(line: str) -> bool:
    line_str = line.strip()
    if not (line_str.startswith("## ") or line_str.startswith("### ")):
        return False
    if line_str.startswith("## Level:") or line_str.startswith("## Topic:") or line_str.startswith("### Level:") or line_str.startswith("### Topic:"):
        return False
    
    title_clean = re.sub(r'^[#\s\d\.]+', '', line_str).strip().lower()
    for kw in MAJOR_SECTION_KEYWORDS:
        if kw in title_clean:
            return True
    return False

def split_sections_by_heading(md_text: str) -> dict[str, str]:
    sections = {}
    current_heading = "Intro"
    current_lines = []
    md_text = md_text.replace("\r\n", "\n")
    for line in md_text.splitlines():
        if is_major_section_heading(line):
            sections[current_heading] = "\n".join(current_lines).strip()
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
    instruction = "Answer the following questions in Vietnamese or English:"
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        if line_str.startswith("*") and line_str.endswith("*"):
            instruction = line_str.replace("*", "").strip()
        elif re.match(r'^\d+\.', line_str):
            questions.append(format_markdown_inline(line_str))
            
    questions_html = "<br>\n        ".join(questions)
    
    return f"""    <div class="section-title">Warm-up / Khởi động</div>
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
    
    return f"""    <div class="section-title">I. Reading Passage</div>
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
    
    html_parts = [f'    <div class="section-title">II. IELTS Reading Questions ({total_questions} questions)</div>']
    
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
            q_text = re.sub(r'_{3,}', '<span class="fill-blank"></span>', q_text)
            stretch_marker = " (*)" if q.get("is_stretch") else ""
            
            q_item_html = f'        <div class="question-item">\n            <span class="question-number">{num}.</span> {q_text}{stretch_marker}'
            if q["options"]:
                q_item_html += '\n            <div class="question-options">'
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
    
    html_parts = [f'    <div class="section-title">III. Questions for Grammar ({total_questions} questions)</div>']
    
    for g in groups:
        title = g["title"]
        instruction = g["instruction"]
        qs = g["questions"]
        
        group_html = []
        group_html.append('    <div class="question-group">')
        if qs:
            start_num = int(qs[0]["num"]) + offset
            end_num = int(qs[-1]["num"]) + offset
            prefix = f"Questions {start_num}–{end_num}: "
            if not instruction.strip().startswith("Questions"):
                instruction = prefix + instruction
                
        adjusted_instruction = adjust_instruction_numbers(instruction, offset)
        group_html.append(f'        <div class="question-instruction">{adjusted_instruction}</div>')
        
        for q in qs:
            num = int(q["num"]) + offset
            q_text = format_markdown_inline(q["text"])
            q_text = re.sub(r'_{3,}', '<span class="fill-blank"></span>', q_text)
            stretch_marker = " (*)" if q.get("is_stretch") else ""
            
            q_item_html = f'        <div class="question-item">\n            <span class="question-number">{num}.</span> {q_text}{stretch_marker}'
            if q["options"]:
                q_item_html += '\n            <div class="question-options">'
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
        return f"Task {num}: {prefix} Word Ordering (Sắp xếp từ thành câu)".replace(": (*)", ": (*)").strip()
    elif "conjunction" in skill_lower or "completion" in skill_lower:
        return f"Task {num}: {prefix} Sentence Completion (Hoàn thành câu)".replace(": (*)", ": (*)").strip()
    elif "translation" in skill_lower or "translate" in skill_lower:
        return f"Task {num}: {prefix} Translation (Dịch câu)".replace(": (*)", ": (*)").strip()
    
    return f"Task {num}: {prefix} {skill_clean}".replace(": (*)", ": (*)").strip()

def get_required_lines_count(text: str) -> int:
    text_lower = text.lower()
    
    # Check for specific "write X sentences" pattern
    match = re.search(r'write\s+(\d+)\s+sentence', text_lower)
    if match:
        num_sentences = int(match.group(1))
        return max(num_sentences + 1, 3)
        
    # Check for range "X-Y sentences"
    match_range = re.search(r'write\s+(\d+)-(\d+)\s+sentence', text_lower)
    if match_range:
        max_sentences = int(match_range.group(2))
        return max(max_sentences + 1, 3)
        
    if "email" in text_lower or "message" in text_lower or "letter" in text_lower:
        return 5
    if "paragraph" in text_lower or "essay" in text_lower or "describe" in text_lower or "comparison" in text_lower:
        return 4
        
    return 1

def format_writing_task_content(task_text: str) -> str:
    # Clean up redundant arrows (→), dots (...), and trailing dots/dots-with-spaces
    text = task_text.replace("<br>", "\n")
    text = re.sub(r'[\s\.]*→\s*\.{5,}', '', text)
    text = re.sub(r'[\s\.]*→\s*$', '', text)
    text = re.sub(r'\s*\.{5,}\s*$', '', text)
    text = re.sub(r'\s+\.\s*$', '', text)
    text = text.strip()
    
    lines = text.splitlines()
    formatted_lines = []
    
    # Detect if there are sub-questions (e.g. a) or 1.) outside tables
    has_sub = False
    for line in lines:
        line_str = line.strip()
        if not (line_str.startswith("|") and line_str.endswith("|")):
            if re.match(r'^\s*([a-z]\)|\d+\.)', line_str):
                has_sub = True
                break
                
    table_lines = []
    non_table_text_lines = []
    
    for line in lines:
        line_str = line.strip()
        if line_str.startswith("|") and line_str.endswith("|"):
            if non_table_text_lines:
                txt = "\n".join(non_table_text_lines)
                if has_sub:
                    sub_lines = txt.splitlines()
                    for sl in sub_lines:
                        sl_str = sl.strip()
                        if re.match(r'^\s*([a-z]\)|\d+\.)', sl_str):
                            formatted_lines.append(format_markdown_inline(sl_str))
                            sub_lines_count = get_required_lines_count(sl_str)
                            formatted_lines.append('<div class="writing-line"></div>' * sub_lines_count)
                        else:
                            formatted_lines.append(format_markdown_inline(sl_str))
                else:
                    formatted_lines.append(format_markdown_inline(txt.replace("\n", "<br>")))
                non_table_text_lines = []
            
            table_lines.append(line_str)
        else:
            if table_lines:
                formatted_lines.append(parse_markdown_table_to_html("\n".join(table_lines)))
                table_lines = []
            non_table_text_lines.append(line)
            
    if non_table_text_lines:
        txt = "\n".join(non_table_text_lines)
        if has_sub:
            sub_lines = txt.splitlines()
            for sl in sub_lines:
                sl_str = sl.strip()
                if re.match(r'^\s*([a-z]\)|\d+\.)', sl_str):
                    formatted_lines.append(format_markdown_inline(sl_str))
                    sub_lines_count = get_required_lines_count(sl_str)
                    formatted_lines.append('<div class="writing-line"></div>' * sub_lines_count)
                else:
                    formatted_lines.append(format_markdown_inline(sl_str))
        else:
            formatted_lines.append(format_markdown_inline(txt.replace("\n", "<br>")))
    if table_lines:
        formatted_lines.append(parse_markdown_table_to_html("\n".join(table_lines)))
        
    if not has_sub:
        lines_count = get_required_lines_count(task_text)
        if "email" in task_text.lower() or "message" in task_text.lower():
            formatted_lines.append("<br>To: ...................................................... Subject: ......................................................<br>")
        
        if lines_count == 1:
            formatted_lines.append("<br>Answer: <div class='writing-line' style='display:inline-block; width:90%; margin-top:0; vertical-align:middle;'></div>")
        else:
            formatted_lines.append("<br>" + '<div class="writing-line"></div>' * lines_count)
            
    return "<br>".join(formatted_lines)

def generate_writing_questions_html(sections: dict[str, str]) -> str:
    writing_qs_md = sections.get("Questions for Writing", "")
    if not writing_qs_md:
        for k in sections.keys():
            if "questions for writing" in k.lower() or "writing questions" in k.lower():
                writing_qs_md = sections[k]
                break
    if not writing_qs_md:
        return ""
        
    tasks = parse_writing_table(writing_qs_md)
    html_parts = [f'    <div class="section-title">IV. Questions for Writing ({len(tasks)} tasks)</div>']
    
    for t in tasks:
        num = t["num"]
        task_text = t["task"]
        skill = t["skill"]
        skill_lower = skill.lower()
        
        # Append words to order for Sentence Building / Word Ordering / Completion tasks
        language_text = t.get("language", "").strip()
        if language_text and any(keyword in skill_lower for keyword in ["order", "building", "completion", "complete"]):
            task_text = task_text + "\n\n" + language_text
            
        title = get_writing_task_title(num, skill)
        content_html = format_writing_task_content(task_text)
        
        task_html = f"""    <div class="writing-box">
        <div class="question-instruction">{title}</div>
        <div class="writing-item">
            {content_html}
        </div>
    </div>"""
        html_parts.append(task_html)
        
    return "\n\n".join(html_parts)

def build_practice_html(practice_md: str, level: str, days: list[str], topics: list[str], vocab_words: list[str] = None) -> str:
    sections = split_sections_by_heading(practice_md)
    day_str = f"{days[0]}–{days[-1]}" if len(days) > 1 else f"{days[0]}"
    topics_list_str = ", ".join(topics)
    
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
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CUMULATIVE REVIEW: LEVEL {level} - DAYS {day_str}</title>
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
            font-size: 10.5pt; 
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
            border-left: 3px solid #2980b9; 
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
            margin: 15px 0;
            page-break-inside: avoid;
        }}
        .writing-line {{
            border-bottom: 1px dotted #bdc3c7;
            height: 26px;
            margin-top: 6px;
            margin-bottom: 2px;
            width: 98%;
            page-break-inside: avoid;
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
            color: #2980b9;
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
        }}
        .question-options div {{
            margin-bottom: 2px;
        }}
        .fill-blank {{
            display: inline-block;
            width: 100px;
            border-bottom: 1px solid #000;
            text-align: center;
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
        <h1>CUMULATIVE REVIEW: DAYS {day_str}</h1>
        <h2>Level: {level} | Topics: {topics_list_str}</h2>
        <div class="student-info">
            <span>Student Name: ..............................................................</span>
            <span>Time Allowed: 120 mins</span>
        </div>
    </div>

{warmup_html}
{reading_html}
{reading_qs_html}
{grammar_html}
{writing_html}

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
                sub_line = re.sub(r'^[\-\*]\s+', '', sub_line).strip()
                is_bullet_stretch = "(*)" in sub_line or "stretch" in sub_line.lower()
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
    if rest_lower.startswith("giải thích") or rest_lower.startswith("dữ kiện") or rest_lower.startswith("*giải thích*") or rest_lower.startswith("<b>giải thích"):
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
    for line in task["lines"]:
        line_str = line.strip()
        if not line_str:
            continue
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
    if in_list:
        html_parts.append("</ul>")
    return f'<div class="sample-essay-box">\n    {"".join(html_parts)}\n</div>'

def build_answers_html(answers_md: str, days: list[str], topics: list[str], practice_md: str) -> str:
    sections = split_sections_by_heading(answers_md)
    practice_sections = split_sections_by_heading(practice_md)
    
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
    
    day_str = f"{days[0]}–{days[-1]}" if len(days) > 1 else f"{days[0]}"
    topics_list_str = ", ".join(topics)
    
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>ANSWER KEY & EXPLANATIONS - DAYS {day_str}</title>
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
            border-bottom: 2px solid #e74c3c; 
            padding-bottom: 8px; 
            margin-bottom: 15px; 
            text-align: center;
        }}
        .header h1 {{ 
            font-size: 15pt; 
            margin: 0; 
            color: #c0392b;
            text-transform: uppercase;
            font-weight: bold;
        }}
        .header h2 {{
            font-size: 10.5pt;
            margin: 3px 0;
            font-style: italic;
            color: #7f8c8d;
        }}
        .section-title {{ 
            font-size: 12pt; 
            color: #2c3e50; 
            border-left: 4px solid #e74c3c; 
            padding-left: 8px; 
            margin-top: 20px; 
            margin-bottom: 8px; 
            text-transform: uppercase;
            font-weight: bold;
        }}
        .explanation-item {{
            margin-bottom: 12px;
            padding-bottom: 8px;
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
            padding-left: 10px;
            margin: 4px 0;
        }}
        .sample-essay-box {{
            background-color: #fafbfc;
            border: 1px solid #dcdde1;
            padding: 12px;
            margin-top: 10px;
            text-align: justify;
            page-break-inside: avoid;
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
            margin: 15px 0;
            page-break-inside: avoid;
        }}
        .writing-line {{
            border-bottom: 1px dotted #bdc3c7;
            height: 26px;
            margin-top: 6px;
            margin-bottom: 2px;
            width: 98%;
            page-break-inside: avoid;
        }}
        ul {{
            margin: 5px 0;
            padding-left: 20px;
        }}
    </style>
</head>
<body>

    <div class="header">
        <h1>ANSWER KEY & EXPLANATIONS - DAYS {day_str}</h1>
        <h2>Topics: {topics_list_str}</h2>
    </div>

    <div class="section-title">I. Reading Passage Answers & Explanations</div>
{reading_explanations_html}

    <div class="section-title">II. Grammar Practice Answers & Explanations</div>
{grammar_explanations_html}

    <div class="section-title">III. Writing Guidance / Suggested Answers</div>
{writing_answers_html}

</body>
</html>
"""
    return html_content

def build_vocab_checker_html(items_c1: list[dict], items_c2: list[dict], level: str, days: list[str], topics: list[str], is_answer: bool = False) -> str:
    day_str = f"{days[0]}–{days[-1]}" if len(days) > 1 else f"{days[0]}"
    topics_list_str = ", ".join(topics)
    
    checker_1_rows = []
    for idx, item in enumerate(items_c1):
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
    <title>VOCABULARY CHECKER{title_suffix} - DAYS {day_str}</title>
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
            Days: {day_str} | Level: {level} | Topics: {topics_list_str}
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
            Days: {day_str} | Level: {level} | Topics: {topics_list_str}
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

def compile_html_to_pdf(html_path: Path, pdf_path: Path, lesson_id: str = "", doc_type: str = "") -> None:
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
        )
        browser.close()

def convert_review_json_to_flat(data: dict) -> dict:
    if "practice_markdown" in data:
        return data
        
    converted = data.copy()
    
    pm = []
    pm.append("## Reading Passage")
    reading = data.get("reading", {})
    passage = reading.get("passage", {})
    if passage:
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
                    options_str = "\n" + "\n".join([f"    - {opt}" for opt in q["options"]])
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
                    options_str = "\n" + "\n".join([f"    - {opt}" for opt in q["options"]])
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
            task_cell = f"{t.get('task_type', '')}: {prompt_clean}{visual_prefix}"
            task_cell = task_cell.replace("|", "\\|")
            
            lang_cell = "<br>".join(t.get("useful_language", []))
            crit_cell = "<br>".join(t.get("success_criteria", []))
            pm.append(f"| {t.get('id', 1)} | {task_cell} | {t.get('target_length', '')} | {t.get('focus_skill', '')} | {lang_cell} | {crit_cell} |")
        pm.append("")
        
    converted["practice_markdown"] = "\n".join(pm)
    
    am = []
    answers = data.get("answers", {})
    r_ans = answers.get("reading_answers", [])
    if r_ans:
        am.append("## Reading Answer Key and Detailed Explanations")
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
            am.append("> **Suggested Model Answer:**")
            am.append(f"> \"{wg.get('model_answer', '')}\"")
            am.append("")
            am.append(f"- **Hướng dẫn viết từng câu / từng bước:** {wg.get('guidance_vi', '')}")
            checklist = wg.get("self_checklist", [])
            if checklist:
                checklist_str = " ".join([f"* {item}" for item in checklist])
                am.append(f"- *Tự kiểm tra:* {checklist_str}")
            am.append("")
            
    converted["answers_markdown"] = "\n".join(am)
    
    vocab = data.get("vocabulary", {})
    if vocab and "items" in vocab:
        raw_items = vocab.get("items", [])
        vocab_items = []
        for ri in raw_items:
            vocab_items.append({
                "word": ri.get("term", ""),
                "ipa": ri.get("ipa", ""),
                "type": ri.get("part_of_speech", ""),
                "meaning": ri.get("meaning_vi", ""),
                "example": ri.get("example", "")
            })
        converted["vocab_items"] = vocab_items
        
    return converted

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Review pack JSON file")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    
    # Run JSON schema and pedagogical validations
    from validate_lesson_json import validate_lesson_json
    if not validate_lesson_json(Path(args.json_file)):
        print("FAIL: JSON validation failed. Exiting.", file=sys.stderr)
        sys.exit(1)
        
    # Adapter for structured JSON compilation
    if "practice_markdown" not in data:
        data = convert_review_json_to_flat(data)

    level = str(data.get("level", "A2"))
    days = list(data.get("days", ["00000000"]))
    topics = list(data.get("topics", ["General Review"]))
    
    day_str = f"{days[0]}-{days[-1]}" if len(days) > 1 else f"{days[0]}"
    
    lesson_id = data.get("lesson_id")
    if not lesson_id:
        level_part = safe_filename_part(level)
        rand_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        lesson_id = f"LSN-{day_str}-{level_part}-REV-{rand_str}"
        
    names = build_names(level, days)
    
    if args.out_dir is None:
        out_dir = Path("outputs") / "ielts-daily-reading-writing" / f"{level}-Review-{day_str}"
    else:
        out_dir = Path(args.out_dir)
        
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the original input JSON payload as the source of truth
    source_json_path = out_dir / "lesson_source.json"
    if Path(args.json_file).resolve() != source_json_path.resolve():
        source_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    part1_html_path = out_dir / "part1_practice_sheet.html"
    part3_html_path = out_dir / "part3_answer_key.html"
    vocab_checker_html_path = out_dir / "vocab_checker.html"
    vocab_checker_answer_html_path = out_dir / "vocab_checker_answer.html"
    
    practice_pdf_path = out_dir / names["practice_pdf"]
    answers_pdf_path = out_dir / names["answers_pdf"]
    vocab_checker_pdf_path = out_dir / names["vocab_checker_pdf"]
    vocab_checker_answer_pdf_path = out_dir / names["vocab_checker_answer_pdf"]

    vocab_items = list(data.get("vocab_items", []))
    vocab_words = [item["word"] for item in vocab_items] if vocab_items else []

    practice_html_content = build_practice_html(data.get("practice_markdown", ""), level, days, topics, vocab_words)
    answers_html_content = build_answers_html(data.get("answers_markdown", ""), days, topics, data.get("practice_markdown", ""))
    
    # Shuffle vocab items
    items_c1 = list(vocab_items)
    while True:
        random.shuffle(items_c1)
        if len(vocab_items) <= 1 or [x["word"] for x in items_c1] != [x["word"] for x in vocab_items]:
            break
            
    items_c2 = list(vocab_items)
    while True:
        random.shuffle(items_c2)
        if len(vocab_items) <= 1 or ([x["word"] for x in items_c2] != [x["word"] for x in vocab_items] and [x["word"] for x in items_c2] != [x["word"] for x in items_c1]):
            break

    vocab_checker_html_content = build_vocab_checker_html(items_c1, items_c2, level, days, topics, is_answer=False)
    vocab_checker_answer_html_content = build_vocab_checker_html(items_c1, items_c2, level, days, topics, is_answer=True)

    part1_html_path.write_text(practice_html_content, encoding="utf-8")
    part3_html_path.write_text(answers_html_content, encoding="utf-8")
    vocab_checker_html_path.write_text(vocab_checker_html_content, encoding="utf-8")
    vocab_checker_answer_html_path.write_text(vocab_checker_answer_html_content, encoding="utf-8")

    compile_html_to_pdf(part1_html_path, practice_pdf_path, lesson_id, "Cumulative Review Practice")
    compile_html_to_pdf(part3_html_path, answers_pdf_path, lesson_id, "Review Answer Key & Explanations")
    compile_html_to_pdf(vocab_checker_html_path, vocab_checker_pdf_path, lesson_id, "Vocabulary Checker")
    compile_html_to_pdf(vocab_checker_answer_html_path, vocab_checker_answer_pdf_path, lesson_id, "Vocabulary Checker Answer Key")

    result = {
        "part1_html": str(part1_html_path),
        "part3_html": str(part3_html_path),
        "vocab_checker_html": str(vocab_checker_html_path),
        "vocab_checker_answer_html": str(vocab_checker_answer_html_path),
        "practice_pdf": str(practice_pdf_path),
        "answers_pdf": str(answers_pdf_path),
        "vocab_checker_pdf": str(vocab_checker_pdf_path),
        "vocab_checker_answer_pdf": str(vocab_checker_answer_pdf_path),
        "lesson_id": lesson_id
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
