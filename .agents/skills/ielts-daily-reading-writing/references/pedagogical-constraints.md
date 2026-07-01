# Pedagogical Constraints

These pedagogical constraints must be strictly followed by all generation and reviewing agents.

## 1. Reading Passage & Question Constraints
- **CEFR-Aligned Passage Length**:
  - A1: 120-180 words
  - A2: 180-260 words
  - B1: 300-450 words
  - B2: 550-750 words
  - C1: 750-950 words
  - C2: 900-1100 words
- **Vocabulary Bolding**:
  - All occurrences of target vocabulary words (from Part 2) inside the passage must be **bolded** (`**word**`).
  - Recycled vocabulary words must be bolded and marked with `[R]` (e.g. `**word** [R]`).
- **Printed Passage Boundary Rule (Anti-Hallucination)**:
  - **Reading questions must be answerable only from the final printed reading passage.**
  - Omitted facts from original source web pages or outside general knowledge must never be tested.
- **Verbatim Evidence Quotes**:
  - Every reading question answer must have an `evidence_quote` taken *verbatim* from the final printed passage text.
  - The paragraph number must be marked with a paragraph symbol (`§`).
- **Anti-Skimming & Scanning (At least 50% non-literal)**:
  - Do not reuse exact scannable keywords from the passage inside the questions. Paraphrase using synonyms or altered sentence structures.
  - Intentionally insert scannable passage keywords inside incorrect choices (distractors) to catch skimming-only students.
  - **For B1+ levels, at least 50% of the questions must be non-literal** (requiring paraphrase, inference, logical relation, comparison, cause-effect, contrast, classification, or writer-purpose reasoning).

## 2. Grammar Question Constraints (Single Unique Answer)
- **Grammar Questions**:
  - Every grammar question must have **exactly one correct answer**.
  - Gap-fill items must be constrained (e.g., by providing the base word in parentheses) to prevent multiple correct tenses/forms.
  - Number grammar exercises starting from **1** continuously in the raw JSON payload. Do not offset.
- **Meaning Preservation**:
  - Grammar transformation, rewrite, combine, and correction questions **must strictly preserve the original meaning**.
- **Passive Voice Constraint**:
  - Do not force passive voice onto intransitive verbs (like "stop", "go", "arrive", "happen", "occur", "exist") unless the prompt supplies a transitive source sentence (e.g., "The police stopped the cars", not "The cars stopped").
- **Common Mistakes / IELTS Traps Table**:
  - Must use exactly 4 columns: `| Common mistake / Trap | Wrong example | Correct version | Why it matters for IELTS |`.
  - **CRITICAL**: Do NOT include vocabulary words, IPAs, or vocabulary definitions in this table. It is strictly for grammar and test strategies.

## 3. Writing Task Constraints (Topic Relevance)
- **Daily Topic Alignment**:
  - **Every Writing task must be clearly connected to the daily lesson topic.**
  - Even if the Writing Level is lower than the Reading Level (e.g., A1/A2 Writing vs. B1 Reading), the tasks must remain themed.
  - Do not generate generic, unrelated tasks.
- **Visual Writing Space**:
  - Tasks must clearly state the requested writing length (e.g., "write 3 sentences" or "write a short paragraph").
  - Do not hardcode dots or underscores. The compiler automatically renders spacious, dotted `.writing-line` divs.
- **Data Representation & Graphics**:
  - Presenting raw numbers in plain text is forbidden.
  - Tables must be formatted as clean Markdown tables.
  - Charts, maps, and diagrams must be drawn using valid, responsive SVG vectors wrapped in `<div class="svg-chart-container"><svg ...>...</svg></div>`. All text labels, grids, and values must be aligned.

## 4. Explanations, Rationale & Time Constraints
- **Persona**: Highly supportive senior English teacher.
- **Language**: All explanations, reasoning steps, pocket formulas, and exam tips must be written in **Vietnamese (tiếng Việt)**.
- **Warm-up Specificity Rule**:
  - Warm-up questions must be specific to the lesson topic and activate relevant background knowledge.
  - Do not use generic placeholders (e.g., "What do you think about this topic?", "Share a real experience related to this topic.").
  - Generate exactly 3 questions:
    1. Personal connection question (e.g., "Bạn thường xem phim ở rạp hay xem online? Vì sao?")
    2. Topic prediction question (e.g., "Vì sao nhiều người thích streaming hơn cinema?")
    3. Key concept activation question (e.g., "Rạp chiếu phim cần thay đổi gì để thu hút người xem?")
- **Workload Time Allowed Constraint**:
  - The printed `Time Allowed` must match the estimated workload completion time within a **15% threshold**.
  - Estimated formula:
    * Reading Passage Reading time: 8 minutes.
    * Reading Question: 1.5 minutes each.
    * Grammar MCQ/gap-fill: 0.8 minutes each.
    * Grammar correction/rewrite/combine: 1.5 minutes each.
    * Warm-up question: 1.5 minutes each.
    * Writing task: 3 minutes for 1-sentence/rearrangements, 6 minutes for short tasks (under 60 words/paragraphs/emails), 15 minutes for standard long tasks.

- **Standard Time Allowed Values**:
  - The printed Time Allowed must be rounded to a standard classroom value: `45, 60, 75, 90, 105, or 120 minutes`.
  - Do not print odd values (like 111 mins). For daily practice A1/A2 packs, prefer `45-60 mins` or `60-90 mins` depending on workload.

## 5. Correct-the-Error Constraints
- For any Correct-the-error task:
  - The original sentence must have exactly one target error.
  - The correct answer must be different from the original.
  - The explanation must match the actual error in the prompt.
  - An identical answer is invalid.

## 6. Writing Prompt & Visual Rules
- **No Duplicate Task Type**: `task_type` heading is rendered by template, so `prompt` must not repeat it.
- **No Raw Visual in Prompt**: SVG/HTML charts must go only in `visual_data.content`.
- **A2 Vocabulary Mix**: For A2, mix topic words, collocations, phrases/useful chunks, and core single words. Do not put only single words. Use section titles: Core Words, Topic Vocabulary, Phrases, Chunks & Collocations, Recycled Vocabulary.

