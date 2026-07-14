#!/usr/bin/env python3
"""Resolve defaults and suggest a level-appropriate IELTS daily topic.

Usage examples:
  python scripts/select_daily_inputs.py --level B1
  python scripts/select_daily_inputs.py --history '[{"day":"20260624","topic":"Weather"}]'
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
from dataclasses import dataclass

TOPICS = {
    "A1": ["Daily routines", "Family relations", "Food and local restaurants", "Weather and clothing", "Public facilities"],
    "A2": ["Daily routines", "Family celebrations", "School life", "Shopping and customer service", "Health appointments", "Money and simple budgeting", "Pets and animal care", "Work and study background"],
    "B1": ["Wildlife conservation", "Natural disasters", "Fitness trends", "Campus life", "Online safety", "City vs countryside", "Sportsmanship and teamwork", "Advertising aimed at young consumers", "Job advertisements and interview advice", "Museum layouts and monument tours"],
    "B2": ["Climate change", "Urbanization and public transport", "Remote work", "Museums and society", "Crime and rehabilitation", "Consumerism", "Mental health and academic pressure", "Housing affordability", "Geographical maps and facility changes", "History of artistic mediums and craftsmanship"],
    "C1": ["Data privacy and surveillance", "AI ethics", "Ageing populations", "Brain drain", "Media credibility and misinformation", "Environmental justice", "Consumer psychology and neuromarketing ethics", "Automation and future job markets"],
    "C2": ["Human and machine intelligence", "Bioethics and animal testing", "Macroeconomics and global trade", "Freedom of speech and censorship", "Neuromarketing ethics", "Automation and future job markets"],
}

RELATED = {
    "weather": ["Natural disasters", "Climate change", "Environmental justice"],
    "shopping": ["Advertising aimed at young consumers", "Consumerism", "Consumer psychology and neuromarketing ethics", "Neuromarketing ethics"],
    "money": ["Advertising aimed at young consumers", "Consumerism", "Consumer psychology and neuromarketing ethics", "Neuromarketing ethics"],
    "budgeting": ["Advertising aimed at young consumers", "Consumerism", "Consumer psychology and neuromarketing ethics", "Neuromarketing ethics"],
    "advertising": ["Consumerism", "Consumer psychology and neuromarketing ethics", "Neuromarketing ethics"],
    "consumerism": ["Consumer psychology and neuromarketing ethics", "Neuromarketing ethics"],
    "school": ["Campus life", "School uniforms", "Global education inequality"],
    "health": ["Fitness trends", "Mental health and academic pressure", "Ageing populations"],
    "animals": ["Wildlife conservation", "Animal testing and bioethics"],
    "technology": ["Online safety", "Data privacy and surveillance", "AI ethics"],
    "transport": ["Road safety", "Urbanization and public transport", "Smart cities"],
    "map": ["Museum layouts and monument tours", "Geographical maps and facility changes", "Urbanization and public transport"],
    "neighborhood": ["Museum layouts and monument tours", "Geographical maps and facility changes", "Housing affordability"],
    "museum": ["Geographical maps and facility changes", "History of artistic mediums and craftsmanship"],
    "art": ["History of artistic mediums and craftsmanship", "Government funding: arts, science, healthcare, education"],
    "craft": ["History of artistic mediums and craftsmanship", "Commercialization of indigenous traditions and identity loss"],
    "work": ["Job advertisements and interview advice", "Remote work", "Automation and future job markets"],
    "job": ["Remote work", "Automation and future job markets"],
    "remote": ["Automation and future job markets"],
    "automation": ["Remote work", "Automation and future job markets"],
}

@dataclass
class Inputs:
    day: str
    level: str
    topic: str
    reading_questions: int
    vocabulary_words: int
    grammar_questions: int
    writing_practice: int


def normalize_level(level: str | None) -> str:
    value = (level or "A2").upper().strip()
    return value if value in TOPICS else "A2"


def today_label() -> str:
    return "Day " + dt.date.today().strftime("%Y%m%d")


def choose_topic(level: str, history: list[dict] | None = None) -> str:
    pool = TOPICS[level]
    if history:
        recent_topics = [str(item.get("topic", "")) for item in history[-5:]]
        recent_lower = " ".join(recent_topics).lower()
        candidates = []
        for key, related in RELATED.items():
            if key in recent_lower:
                candidates.extend([t for t in related if t in pool])
        candidates = [t for t in candidates if t not in recent_topics]
        if candidates:
            return random.choice(candidates)
        unused = [t for t in pool if t not in recent_topics]
        if unused:
            return random.choice(unused)
    return random.choice(pool)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day")
    parser.add_argument("--topic")
    parser.add_argument("--level")
    parser.add_argument("--reading-questions", type=int, default=13)
    parser.add_argument("--vocabulary-words", type=int, default=20)
    parser.add_argument("--grammar-questions", type=int, default=30)
    parser.add_argument("--writing-practice", type=int, default=5)
    parser.add_argument("--history", help="JSON list of previous day/topic objects")
    args = parser.parse_args()

    level = normalize_level(args.level)
    history = json.loads(args.history) if args.history else None
    resolved = Inputs(
        day=args.day or today_label(),
        level=level,
        topic=args.topic or choose_topic(level, history),
        reading_questions=args.reading_questions,
        vocabulary_words=args.vocabulary_words,
        grammar_questions=args.grammar_questions,
        writing_practice=args.writing_practice,
    )
    print(json.dumps(resolved.__dict__, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
