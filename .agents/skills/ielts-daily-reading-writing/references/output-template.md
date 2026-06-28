# Daily Pack Output Template

Use this structure exactly unless the user requests a different format. The daily output has four separated deliverable parts. Parts 1-3 must be exported as clean PDFs. Part 4 must be exported as a Markdown file for Quizlet import.

## Global Header Metadata
Resolve these fields before writing any content:
- Day: `Day YYYYMMDD`
- Level: CEFR level
- Topic: topic name
- Topic cluster: cluster name
- IELTS pathway focus: reading micro-skill + writing micro-skill; for B2 Task 1, state chart/process/map/mixed visual focus
- Verified reading source: source title + publisher/organization + date if available + final verified URL + access date + URL status + reliability note
- Band-bridge focus: what next-level skill is being introduced
- Grammar focus: 1-3 grammar targets
- Counts: reading questions, vocabulary words, grammar questions, writing practice tasks

Use these values in each PDF header.

## Required Output Files
Create exactly these files, using sanitized file names with spaces replaced by hyphens and unsafe punctuation removed:
1. `[Level]-[Topic]-[Day]-Practise.pdf`
2. `[Level]-[Topic]-[Day]-Vocabulary-Grammar.pdf`
3. `[Level]-[Topic]-[Day]-Answers.pdf`
4. `[Level]-[Topic]-[Day]-Quizlet-Vocab.md`

Keep the spelling `Practise.pdf` because the user requested this naming convention.

## Part 1 - Practice PDF
File name: `[Level]-[Topic]-[Day]-Practise.pdf`

Purpose: printable student worksheet without answers.

Required sections:

### 1. Cover Header
Include:
- Day
- Level
- Topic
- Topic cluster
- IELTS pathway focus
- Grammar focus
- Student name/date fields if useful

### 2. Reading Source Verification
Include a compact source box before the passage. This is mandatory.

Required fields:
| Source title | Publisher/Organization | Date/Access date | Final verified URL | URL status | Source type | Reliability check | How the passage uses the source |

Rules:
- The reading must be based on a reputable verified source, not self-generated from memory.
- The final URL must be checked and clickable before finalizing the PDF. Do not use URLs that return 404, 403, timeout, login wall, irrelevant redirect, or title/content mismatch.
- Do not invent a source, URL, author, publication date, or factual claim.
- Preserve the original wording for the selected excerpt when reproduction is allowed. Do not silently shorten, rewrite, summarize, or fabricate the passage.
- If the full original article cannot be reproduced because of copyright/access limits, include only a compliant exact excerpt and state the limitation; ask for a user-provided/licensed text if the full original article is required.
- Keep the source box short so it does not crowd the worksheet.

### 3. Warm-up
Give 3-5 short questions in Vietnamese or bilingual English/Vietnamese to activate prior knowledge. Do not answer them here.

### 4. Reading Passage
Provide the verified reading text with title.
- Use exact source wording for the selected excerpt when allowed.
- Do not present AI-written, shortened, or paraphrased text as the original article.
- If an adapted learner version is explicitly requested, label it as adapted and keep a separate source note; otherwise preserve the source text/excerpt.
- **Vocabulary bolding**: Bold all occurrences of target vocabulary words from Part 2 inside the reading passage using `**word**` (or its inflected forms).

### 5. Questions for Reading
Generate exactly the requested number of IELTS-style reading questions. Group by question type. Number continuously. Include a controlled band-bridge challenge: 10-20% of the questions should approach the next level and be marked `(*)`.

Question-type guidance:
- A1-A2: form/table completion, matching information, short answer, basic multiple choice.
- B1: multiple choice, matching headings, sentence completion, summary completion, True/False/Not Given.
- B2: True/False/Not Given, Yes/No/Not Given, matching features, matching headings, summary completion, classification.
- C1-C2: inference, writer's claims, complex matching, classification, summary completion with distractors.

### 6. Questions for Grammar
Generate exactly the requested number of grammar questions. Group by exercise type when useful:
- gap-fill
- sentence transformation
- error correction
- sentence combining
- controlled production

Do not include answers in Part 1. Include a small number of scaffolded `(*)` grammar questions that approach the next level without overwhelming the learner.

### 7. Questions for Writing
Generate exactly the requested number of writing practice tasks. Keep the Writing section direct and compact. Use this table only:
| # | Task | Target length | Focus skill | Useful language | Success criteria |

For B2 map/diagram-change tasks, include spatial vocabulary and change verbs in Useful language. Where appropriate, mark one writing task or sub-task as `(*)` to help the learner move toward the next level.
Do not add long explanations under Writing questions; put explanation/model support in Part 3 only.

**Data Visualization Formats for Writing Tasks**:
For data description tasks, you must embed the data visually in the "Task" column using one of the following formats:
- **Table Data Format**:
  ```markdown
  Look at this basic budget table and write 3 sentences describing it:
  | Item | Amount |
  | :--- | :--- |
  | Weekly allowance | $15 |
  | Spend on snacks | $7 |
  | Save in bank | $8 |
  ```
- **SVG Chart Format**:
  ```html
  Describe the following bar chart:
  <div class="svg-chart-container">
    <svg width="400" height="200" viewBox="0 0 400 200" style="font-family:sans-serif;">
      <!-- Grid lines -->
      <line x1="50" y1="150" x2="350" y2="150" stroke="#ccc" />
      <line x1="50" y1="100" x2="350" y2="100" stroke="#eee" stroke-dasharray="4" />
      <line x1="50" y1="50" x2="350" y2="50" stroke="#eee" stroke-dasharray="4" />
      <!-- Bars -->
      <rect x="75" y="60" width="40" height="90" fill="#3498db" />
      <rect x="175" y="80" width="40" height="70" fill="#2ecc71" />
      <rect x="275" y="100" width="40" height="50" fill="#e74c3c" />
      <!-- Labels -->
      <text x="95" y="170" font-size="11" text-anchor="middle">Food</text>
      <text x="195" y="170" font-size="11" text-anchor="middle">Toys</text>
      <text x="295" y="170" font-size="11" text-anchor="middle">Savings</text>
      <!-- Values -->
      <text x="95" y="50" font-size="11" text-anchor="middle" font-weight="bold">$9</text>
      <text x="195" y="70" font-size="11" text-anchor="middle" font-weight="bold">$7</text>
      <text x="295" y="90" font-size="11" text-anchor="middle" font-weight="bold">$5</text>
    </svg>
  </div>
  ```

- **Writing Space & Line Allocation Guidelines**:
  - Always write clear, specific instructions detailing length requirements (e.g., "write 3 sentences" or "write a short paragraph").
  - Do not hardcode dots or underscores for student answers in the markdown. The compiler automatically detects sentence counts and renders custom, spacious `.writing-line` elements.

## Part 2 - Vocabulary & Grammar PDF
File name: `[Level]-[Topic]-[Day]-Vocabulary-Grammar.pdf`

Purpose: vocabulary study sheet and grammar mini-lesson.

Required sections:

### 1. Cover Header
Repeat Day, Level, Topic, topic cluster, IELTS pathway focus, and grammar focus.

### 2. Vocabulary Table
Generate exactly the requested number of vocabulary items unless the user asks for more.

The table must have exactly 5 columns:
| Từ/Cụm từ | Phiên âm | Loại từ | Định nghĩa và Tiếng Việt | Ví dụ minh họa |

Vocabulary composition rules:
- Include Academic Vocabulary from the Reading, Grammar, and Writing sections.
- Include Compound Words found in or related to the lesson, such as `public transport`, `carbon footprint`, `job market`.
- Include Idioms & Phrases or useful chunks, such as `play a role in`, `on the one hand`, `in the long run`, but keep idioms level-appropriate.
- Prefer words/chunks that appeared in the Reading passage, grammar examples, or writing prompts.
- If the generated lesson does not contain enough vocabulary items, add level-appropriate related vocabulary from the same topic cluster.
- Mark multi-word phrases naturally in the first column; do not force every item to be a single word.
- Provide IPA-style pronunciation when practical. For multi-word phrases, provide a readable phrase-level pronunciation or main stressed words.
- Keep Vietnamese meanings concise but clear.
- Example sentences must connect to the day's topic and level.

### 3. Vocabulary Grouping Notes
After the table, briefly group the vocabulary into:
- Academic Vocab
- Compound Words
- Idioms & Phrases / Useful Chunks

Do not duplicate the full table; just list item names under each category.

### 3b. Recycled Vocabulary (Từ vựng ôn tập)
This section is mandatory for Day $N$ (where $N > 1$). Provide a 5-column table listing the 3 recycled vocabulary items from the previous lessons:
| Từ/Cụm từ | Phiên âm | Loại từ | Định nghĩa và Tiếng Việt | Bài học gốc (Day) |
| :--- | :--- | :--- | :--- | :--- |
| [Word] [R] | [IPA] | [Type] | [Definition & Vietnamese meaning] | Day YYYYMMDD |

### 4. Detailed Grammar Guide
Explain the selected grammar targets in Vietnamese or bilingual style.
- **IMPORTANT**: You must always split individual grammar topics and tips using `#### Chủ điểm X: ...` or `#### Tips & Tricks: ...` subheadings. Do not combine all grammar content into a single block, as it creates a giant visual box that causes massive empty print pages (due to page-break-inside avoid rule).
- Include:
  - What the grammar point is
  - Why it matters for IELTS Reading/Writing
  - Form/structure
  - 3-6 level-appropriate examples linked to the topic
  - Common mistakes made by Vietnamese learners
  - Quick correction rules

### 5. Common Mistakes / IELTS Traps for This Topic
This subsection is mandatory.
- **CRITICAL WARNING**: Do NOT populate this table with vocabulary words, IPA, or word meanings. It is strictly for grammar mistakes, incorrect structures, and IELTS exam pitfalls.
- Include 5-8 traps linked to the day's topic, reading source, grammar focus, and writing tasks. Use exactly this 4-column layout:

| Common mistake / Trap | Wrong example | Correct version | Why it matters for IELTS |

Include topic-specific traps where relevant, for example:
- map/task 1 traps: wrong prepositions of place, confusing `to the north of` vs `in the north of`, missing overview, describing every small change
- data traps: using `while/whereas` without true contrast, singular/plural errors with percentages, wrong articles before abstract nouns
- reading traps: assuming Not Given from outside knowledge, missing paraphrases, confusing cause and effect
- writing traps: unsupported claims, memorized phrases, overgeneralization, unclear comparison

When level-appropriate, explicitly include the high-impact targets:
- A2: basic data comparison modifiers such as `slightly`, `significantly`, `twice as`, `half as`.
- B1: defining vs non-defining relative clauses and chart contrast linkers such as `while`, `whereas`, `by contrast`.
- B2: complex subject-verb agreement and articles with geographical names or abstract concepts.
- C1-C2: subjunctive mood for formal recommendations, e.g. `It is essential that governments implement...`.

## Part 3 - Answers PDF
File name: `[Level]-[Topic]-[Day]-Answers.pdf`

Purpose: teacher/student answer key with explanations.

Required sections:

### 1. Cover Header
Repeat Day, Level, Topic, topic cluster, IELTS pathway focus, and grammar focus.

### 2. Reading Answer Key and Detailed Explanations
For every reading question, adopt the persona of a highly supportive teacher. Follow this exact Markdown structure:

📖 **Tóm tắt bài đọc:** [Provide a 3-4 sentence Vietnamese summary of the passage]

1. **[Answer Letter]** — [Answer text]
- Bằng chứng: "[Verbatim quote from passage]" (§[Paragraph number])
- Cách tìm đáp án: [Explain step-by-step how to scan and analyze keywords in Vietnamese, and why other options are wrong]
> **💡 Mẹo:** [Practical exam tip for this question type]

2. **[Answer Letter]** *[Stretch Point]* — [Answer text]
- Bằng chứng: "[Verbatim quote from passage]" (§[Paragraph number])
- Kỹ năng [Next Level] — [Skill name (e.g. Kỹ năng B1 — Suy luận (Inference))]: [Detailed reasoning in Vietnamese]
> **💡 Mẹo:** [Practical exam tip]

### 3. Grammar Answer Key and Detailed Explanations
For every grammar question, follow this exact Markdown structure:

> **Bảng phân biệt nhanh / Công thức bỏ túi:**
> - [Brief grammar summary or formulas in Vietnamese]

14. **[Answer word/phrase]**
- Dấu hiệu / Phân tích: [Identify target cues and explain why it is correct in Vietnamese]
> **💡 Mẹo:** [Helpful tip or trap warning]

23. **[Answer word/phrase]** *[Stretch Point]*
- Kỹ năng [Next Level] — [Grammar structure]: [Explain the next-level grammar concept in Vietnamese]
> **💡 Mẹo:** [Grammar tip]

### 4. Writing Guidance / Suggested Answers
For every writing task, follow this exact Markdown structure:

#### Task [X]: [Task name (e.g. Word Ordering / Short Description)]

> **Suggested Model Answer:**
> "[Level-appropriate model text]"

- **Hướng dẫn viết từng câu / từng bước:**
  - Câu 1 / Bước 1: [Detailed structural construction explanation in Vietnamese]
- *Tự kiểm tra:*
  - [Capitalization, subject-verb concord, tense checks, word limits, etc.]

### 5. Review Bridge
Add 3-5 review prompts that recycle the previous or related topic. Follow this structure:

#### IV. Review Bridge / Ôn tập liên chủ đề

1. [Review Question / Translation Prompt]
- **Đáp án:** [Correct answer]
- **Giải thích:** [Vietnamese grammatical or vocabulary rationale]

## Part 4 - Quizlet Vocabulary Markdown
File name: `[Level]-[Topic]-[Day]-Quizlet-Vocab.md`

Purpose: importable vocabulary list for Quizlet or flashcard systems.

Split the file into two separate sections:

### Section 1: Simple Vocabulary List (Học từ vựng đơn giản)
Create a 2-column Markdown table:
| Từ vựng tiếng Anh | Nghĩa tiếng Việt |
| --- | --- |
- The English column must contain the word/phrase/idiom only (no IPA or word type).
- The Vietnamese column must contain the Vietnamese meaning only.

### Section 2: Detailed Vocabulary List (Học từ vựng đầy đủ)
Create a 2-column Markdown table:
| Từ vựng + IPA + Loại từ | Nghĩa tiếng Việt |
| --- | --- |
- The English column must contain the word, the IPA pronunciation, and the word type combined (e.g. `preserve /prɪˈzɜːv, v/`).
- The Vietnamese column must contain the Vietnamese meaning only.

Rules:
- Keep cell content concise so it imports cleanly.
- Escape pipe characters inside cells by replacing them with `/`.
- Do not include grammar explanations in this file.
- Do not include answer keys in this file.

## PDF Layout Requirements
When exporting Parts 1-3 to PDF:
- Use compact margins and consistent headers/footers.
- Avoid excessive blank lines.
- Avoid orphan headings at the bottom of a page.
- Avoid large page breaks inside vocabulary tables, grammar explanations, answer explanations, or writing-task tables.
- Use repeated table headers for long tables.
- Use a Unicode-capable font for Vietnamese and IPA.
- Keep headings clear and tables readable.
- Render and inspect at least the first page and any table-heavy pages when tools are available.

If using the bundled `scripts/export_daily_pack.py`, create a JSON file with these keys:
- `level`
- `topic`
- `day`
- `practice_markdown`
- `vocabulary_grammar_markdown`
- `answers_markdown`
- `quizlet_markdown`

## Cumulative Review Pack Template

When compiling review packs, save the payload as a JSON file with these keys and pass it to `scripts/export_review_pack.py`:
- `level`: target level (e.g. `B2`)
- `days`: list of target days (e.g. `["20260625", "20260626", "20260627"]`)
- `topics`: list of target topics (e.g. `["Urbanization", "Public Facilities"]`)
- `practice_markdown`: markdown structure containing:
  - `# Reading Source Verification` (with verified URL table)
  - `# Warm-up` (warm-up questions)
  - `# Reading Passage` (reading text)
  - `# Questions for Reading` (exercise details)
  - `# Questions for Grammar` (grammar items, covering all target rules, 30% marked with `(*)`)
  - `# Questions for Writing` (writing prompts)
- `answers_markdown`: markdown containing:
  - `# Reading Answer Key and Detailed Explanations` (with step-by-step cognitive guidance in Vietnamese)
  - `# Grammar Answer Key and Detailed Explanations` (explanations in Vietnamese)
  - `# Writing Guidance / Suggested Answers` (sample essays/answers in Vietnamese)
- `vocab_items`: list of dicts, where each dict has keys `word`, `ipa`, `type`, `definition`, `vietnamese`, `example`.
