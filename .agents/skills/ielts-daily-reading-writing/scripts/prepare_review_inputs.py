#!/usr/bin/env python3
"""Aggregate vocabulary and grammar targets from previous daily packs to prepare cumulative review inputs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Reconfigure stdout to use utf-8 for unicode printing on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def parse_vocab_from_html(html_content: str) -> list[dict]:
    # Regex to find table rows representing vocabulary
    row_pattern = re.compile(
        r'<tr>\s*'
        r'<td class="col-word">(.*?)</td>\s*'
        r'<td class="col-phon">(.*?)</td>\s*'
        r'<td class="col-pos">(.*?)</td>\s*'
        r'<td class="col-def">(.*?)</td>\s*'
        r'<td class="col-ex">(.*?)</td>\s*'
        r'</tr>',
        re.DOTALL
    )
    
    items = []
    for match in row_pattern.finditer(html_content):
        word = match.group(1).strip()
        ipa = match.group(2).strip()
        vocab_type = match.group(3).strip()
        col_def = match.group(4).strip()
        example = match.group(5).strip()
        
        # Split definition and Vietnamese meaning (en_def<br><b>vi_mean</b>)
        def_match = re.search(r'^(.*?)<br>\s*<b>(.*?)</b>', col_def, re.DOTALL)
        if def_match:
            definition = def_match.group(1).strip()
            vietnamese = def_match.group(2).strip()
        else:
            definition = col_def
            vietnamese = col_def
            
        items.append({
            "word": word,
            "ipa": ipa,
            "type": vocab_type,
            "definition": definition,
            "vietnamese": vietnamese,
            "example": example
        })
    return items

def parse_grammar_targets_from_html(html_content: str) -> list[str]:
    # Regex to find grammar box titles
    return re.findall(r'Chủ điểm \d+:\s*(.*?)</div', html_content)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", required=True, help="CEFR Level (e.g., A2, B2)")
    parser.add_argument("--days", help="Comma-separated list of YYYYMMDD days")
    parser.add_argument("--history-file", default="outputs/ielts-daily-reading-writing/lesson_history.txt")
    parser.add_argument("--outputs-dir", default="outputs/ielts-daily-reading-writing")
    args = parser.parse_args()

    level = args.level.upper().strip()
    outputs_dir = Path(args.outputs_dir)
    history_path = Path(args.history_file)

    target_days = []
    if args.days:
        target_days = [d.strip() for d in args.days.split(",") if d.strip()]
    else:
        # Load last 5 days from lesson history file for this level
        if history_path.exists():
            history_lines = history_path.read_text(encoding="utf-8").splitlines()
            entries = []
            for line in history_lines:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3 and parts[0].upper() == level:
                    entries.append({
                        "day": parts[1],
                        "topic": parts[2]
                    })
            # Take last 5 unique days
            unique_days = []
            for entry in reversed(entries):
                if entry["day"] not in unique_days:
                    unique_days.append(entry["day"])
                if len(unique_days) >= 5:
                    break
            target_days = list(reversed(unique_days))
        else:
            print(json.dumps({"error": f"History file {args.history_file} not found and no days provided."}, indent=2))
            return

    if not target_days:
        print(json.dumps({"error": f"No history found for level {level} and no days provided."}, indent=2))
        return

    aggregated_vocab = {}
    aggregated_grammar = []
    day_topic_map = {}

    for day in target_days:
        # Search output folders starting with {day}-{level}-
        day_folder = None
        for p in outputs_dir.glob(f"{day}-{level}-*"):
            if p.is_dir():
                day_folder = p
                break
        
        # Try legacy format in case of fallback: {level}_{day}_
        if not day_folder:
            for p in outputs_dir.glob(f"{level}_{day}_*"):
                if p.is_dir():
                    day_folder = p
                    break
                    
        if not day_folder:
            continue

        materials_html = day_folder / "part2_materials.html"
        if materials_html.exists():
            html_content = materials_html.read_text(encoding="utf-8")
            
            # Parse topic name from folder name
            folder_parts = day_folder.name.split("-", 2)
            topic_name = folder_parts[2].replace("-", " ") if len(folder_parts) >= 3 else "Unknown Topic"
            day_topic_map[day] = topic_name
            
            # Vocab
            day_vocab = parse_vocab_from_html(html_content)
            for item in day_vocab:
                word_key = item["word"].lower().strip()
                if word_key not in aggregated_vocab:
                    aggregated_vocab[word_key] = item
            
            # Grammar
            day_grammar = parse_grammar_targets_from_html(html_content)
            for g in day_grammar:
                if g not in aggregated_grammar:
                    aggregated_grammar.append(g)

    result = {
        "level": level,
        "days": target_days,
        "topics": list(day_topic_map.values()),
        "grammar_targets": aggregated_grammar,
        "vocab_count": len(aggregated_vocab),
        "vocab_items": list(aggregated_vocab.values())
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
