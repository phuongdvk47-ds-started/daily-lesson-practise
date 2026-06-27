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
from pathlib import Path
from playwright.sync_api import sync_playwright

def safe_filename_part(value: str) -> str:
    value = re.sub(r"^Day\s+", "", str(value).strip(), flags=re.I)
    value = re.sub(r"[^\w\s.-]+", "", value, flags=re.UNICODE)
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
    text = re.sub(r'_{3,}', '<span class="fill-blank"></span>', text)
    # Bold: **text** -> <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Italic: *text* or _text_ -> <i>text</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_([^_]+?)_', r'<i>\1</i>', text)
    # Inline code: `code` -> <code>code</code>
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    return text

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
        
        if qs:
            start_num = int(qs[0]["num"]) + offset
            end_num = int(qs[-1]["num"]) + offset
            prefix = f"Questions {start_num}–{end_num}: "
            if not instruction.strip().startswith("Questions"):
                instruction = prefix + instruction
                
        group_html.append(f'        <div class="question-instruction">{instruction}</div>')
        
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
    return [cell.strip() for cell in line.split("|")]

def parse_writing_table(table_md: str) -> list[dict]:
    lines = table_md.splitlines()
    tasks = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|") or "Target length" in line or "---" in line:
            continue
        parts = split_table_row(line)
        if len(parts) >= 6:
            tasks.append({
                "num": parts[0],
                "task": parts[1],
                "length": parts[2],
                "skill": parts[3],
                "language": parts[4],
                "criteria": parts[5]
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
    
    has_sub = False
    for line in lines:
        if re.match(r'^\s*([a-z]\)|\d+\.)', line.strip()):
            has_sub = True
            break
            
    if has_sub:
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if re.match(r'^\s*([a-z]\)|\d+\.)', line_str):
                formatted_line = format_markdown_inline(line_str)
                formatted_lines.append(formatted_line)
                formatted_lines.append('Answer: .................................................................................................................................................')
            else:
                formatted_lines.append(format_markdown_inline(line_str))
    else:
        formatted_lines.append(format_markdown_inline(text.replace("\n", "<br>")))
        if "paragraph" in task_text.lower() or "email" in task_text.lower() or "message" in task_text.lower():
            if "email" in task_text.lower() or "message" in task_text.lower():
                formatted_lines.append("<br>To: ...................................................... Subject: ......................................................<br>")
            formatted_lines.append(".............................................................................................................................................................<br>" * 4)
        else:
            formatted_lines.append("<br>Answer: .................................................................................................................................................")
            
    return "<br>".join(formatted_lines)

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
        skill = t["skill"]
        
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

def build_practice_html(practice_md: str, level: str, topic: str, day: str, vocab_words: list[str] = None) -> str:
    sections = split_sections_by_heading(practice_md)
    
    reading_level = level
    writing_level = "A1"
    intro_sec = sections.get("Intro", "")
    r_match = re.search(r'Reading:\s*([A-C][1-2])', intro_sec, re.I)
    if r_match:
        reading_level = r_match.group(1).upper()
    w_match = re.search(r'Writing:\s*([A-C][1-2])', intro_sec, re.I)
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
        <h2>(Level: Reading {reading_level} - Writing {writing_level})</h2>
        <div class="student-info">
            <span>Student Name: ..............................................................</span>
            <span>Time Allowed: 50 mins</span>
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

def parse_vocab_from_markdown(md_table: str) -> list[dict]:
    items = []
    lines = md_table.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line.startswith("|") or "Từ/Cụm từ" in line or "---" in line:
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
        return re.sub(r'^[#\s\d\.]+', '', line_str).strip()
    bold_match = re.match(r'^\*\*(Chủ điểm|Grammar Point|Target|Topic)\s+\d+:?\s*(.*?)\*\*$', line_str, re.I)
    if bold_match:
        return bold_match.group(2).strip()
    return line_str

def build_materials_html(vocab_grammar_md: str, quizlet_md: str, day: str, topic: str) -> str:
    vocab_items = parse_vocab_from_markdown(quizlet_md)
    sections = split_sections_by_heading(vocab_grammar_md)
    
    grouping_md = sections.get("Vocabulary Grouping Notes", "")
    if not grouping_md:
        for k in sections.keys():
            if "grouping" in k.lower():
                grouping_md = sections[k]
                break
                
    groups = parse_grouping_notes(grouping_md)
    
    academic_list = []
    compound_list = []
    idiom_list = []
    
    for item in vocab_items:
        cat = categorize_word(item["word"], groups)
        if cat == "academic":
            academic_list.append(item)
        elif cat == "compound":
            compound_list.append(item)
        else:
            idiom_list.append(item)
            
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

    t1 = build_table(academic_list, "Academic Vocabulary (Từ vựng học thuật)", 1)
    t2 = build_table(compound_list, "Compound Words Table (Từ ghép)", 2)
    t3 = build_table(idiom_list, "Idioms & Phrases Table (Thành ngữ / Cụm từ cố định)", 3)
    
    vocab_tables_html = "\n\n".join(filter(None, [t1, t2, t3]))
    
    academic_words = ", ".join(item["word"] for item in academic_list)
    compound_words = ", ".join(item["word"] for item in compound_list)
    idiom_words = ", ".join(item["word"] for item in idiom_list)
    
    grouping_summary_html = f"""    <div class="subsection-title">Vocabulary Grouping Notes (Phân loại từ vựng)</div>
    <ul>
        <li><b>Academic Vocab:</b> {academic_words}.</li>
        <li><b>Compound Words:</b> {compound_words}.</li>
        <li><b>Idioms & Phrases / Useful Chunks:</b> {idiom_words}.</li>
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

def render_review_bridge(md_text: str) -> str:
    html_parts = []
    lines = md_text.splitlines()
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        if re.match(r'^\d+\.', line_str):
            html_parts.append(f"{format_markdown_inline(line_str)}<br>")
        else:
            html_parts.append(f"<p>{format_markdown_inline(line_str)}</p>")
    return "\n".join(html_parts)

def build_answers_html(answers_md: str, day: str, topic: str, practice_md: str) -> str:
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
    
    review_sec = sections.get("Review Bridge", "")
    if not review_sec:
        for k in sections.keys():
            if "review" in k.lower() or "bridge" in k.lower():
                review_sec = sections[k]
                break
    review_html = ""
    if review_sec:
        review_content = render_review_bridge(review_sec)
        review_html = f"""    <!-- REVIEW BRIDGE -->
    <div class="section-title">IV. Review Bridge / Ôn tập</div>
    <div class="warmup-box">
        {review_content}
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
        .bold-vocab {{
            font-weight: bold;
            text-decoration: underline;
            color: #2980b9;
        }}
        ul {{
            margin: 5px 0;
            padding-left: 20px;
        }}
    </style>
</head>
<body>

    <div class="header">
        <h1>ANSWER KEY & EXPLANATIONS - DAY {day_only}: {topic_upper}</h1>
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

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Daily pack JSON file")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
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
        topic_part = safe_filename_part(topic)
        out_dir = Path("outputs") / "ielts-daily-reading-writing" / f"{day_part}-{level_part}-{topic_part}"
    else:
        out_dir = Path(args.out_dir)
        
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the original input JSON payload as the source of truth
    source_json_path = out_dir / "lesson_source.json"
    if Path(args.json_file).resolve() != source_json_path.resolve():
        source_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    part1_html_path = out_dir / "part1_practice_sheet.html"
    part2_html_path = out_dir / "part2_materials.html"
    part3_html_path = out_dir / "part3_answer_key.html"
    vocab_checker_html_path = out_dir / "vocab_checker.html"
    vocab_checker_answer_html_path = out_dir / "vocab_checker_answer.html"
    
    practice_pdf_path = out_dir / names["practice_pdf"]
    vocab_grammar_pdf_path = out_dir / names["vocab_grammar_pdf"]
    answers_pdf_path = out_dir / names["answers_pdf"]
    vocab_checker_pdf_path = out_dir / names["vocab_checker_pdf"]
    vocab_checker_answer_pdf_path = out_dir / names["vocab_checker_answer_pdf"]
    quizlet_md_path = out_dir / names["quizlet_md"]
    quizlet_txt_path = out_dir / names["quizlet_txt"]

    vocab_items = parse_vocab_from_markdown(data.get("quizlet_markdown", ""))
    vocab_words = [item["word"] for item in vocab_items] if vocab_items else []

    practice_html_content = build_practice_html(data.get("practice_markdown", ""), level, topic, day, vocab_words)
    materials_html_content = build_materials_html(data.get("vocabulary_grammar_markdown", ""), data.get("quizlet_markdown", ""), day, topic)
    answers_html_content = build_answers_html(data.get("answers_markdown", ""), day, topic, data.get("practice_markdown", ""))
    
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
