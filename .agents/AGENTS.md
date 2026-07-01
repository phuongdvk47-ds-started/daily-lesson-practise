# Global Project Rules

These guidelines apply universally to all agents, disciplines, and skill modules within this workspace (including IELTS, SAT, Mathematics, Chemistry, Physics, etc.).

## 1. Modular Pipeline & Role Boundaries
- **Pipeline Architecture**: Complex learning packs must be generated using a modular pipeline rather than in a single monolithic response.
- **Ranh giới Phân quyền (Role Boundaries)**: Only dedicated Research Agents or research-specialized prompts are authorized to perform web searches and access external URLs. Content-generating agents (e.g., question writers, vocabulary extractors, grammar authors) must work solely within the verified data payload.
- **No Fabrications**: Do not invent source metadata, URLs, publication dates, or factual claims. If no verified source is available, stop and report a source gap.

## 2. Question Quality & Answer Uniqueness
- **Single Unique Answer Rule**: Every question generated (across all subjects, including multiple choice, gap-fill, short answer, numerical, or true/false formats) must be designed to have **exactly one unique correct answer**.
- **Context Constraints**: Eliminate vague or overlapping options. For open-ended formats (like gap-fills or numerical entries), always specify constraints or hints (e.g., base verbs in grammar, rounding guidelines in math) to guarantee a single valid spelling and representation.

## 3. Data Integrity & Content Consistency
- **Single Source of Truth**: All lessons must compile from an intermediate structured JSON payload (e.g., `lesson_source.json`).
- **No Regeneration for Compilation**: PDF compilation scripts must read solely from the JSON payload. Never call the AI (LLM) to regenerate content when updating stylesheets, formats, or layouts. Rerun the Python compiler directly using the existing JSON source.
- **Output Directory Structure**: Preserve the output folder contract and file naming conventions of each skill module to ensure consistent integration with CLI tools and databases.

## 4. History Tracking & Spaced Repetition
- **Consult History**: Every daily generator must read the history file corresponding to its level/module to prevent topic duplication.
- **Duplication Limits**: Enforce the anti-duplication windows defined by each skill (e.g., theme and specific topic limits) to ensure a diverse curriculum.
- **Vocabulary/Topic Recycling**: Select prior target concepts from recent history to build spaced repetition exercises, ensuring students review past material naturally.
