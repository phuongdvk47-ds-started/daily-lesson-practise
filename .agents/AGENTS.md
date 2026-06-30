# Project Rules

## Document & URL Verification
- **No Fabricated URLs**: All generated learning materials, reading passages, and study resources must use authentic, active, and verified source URLs (e.g., from VOA Learning English, BBC, British Council).
- **Check Validity**: The agent must verify the correctness of the article URLs and sources using web search or direct HTTP checks prior to generating them. Do not hallucinate article IDs, publication dates, or link paths.
- **Accurate Citations**: Ensure adapted reading texts match the details of the actual source article.
- **B2+ Current Affairs Priority**: For Level B2, C1, and C2 lessons, prioritize choosing reading sources with high timeliness (current affairs, recent news, contemporary essays) to closely align with real IELTS Academic Reading and Writing tasks.

## Topic Redundancy & History Tracking
- **Consult History**: Before generating any new lesson, the agent must inspect the [lesson_history.txt](../outputs/ielts-daily-reading-writing/lesson_history.txt) file.
- **Update History**: Upon successfully generating a new lesson, the agent must append the new lesson details to the end of [lesson_history.txt](../outputs/ielts-daily-reading-writing/lesson_history.txt) following the new 4-column format: `Level | Day | Theme | Specific Topic`.
- **Context-Efficient Daily Lookup**:
  - Use [lesson_history.txt](../outputs/ielts-daily-reading-writing/lesson_history.txt) as the only source for previous Theme and Specific Topic information.
  - For normal daily lesson generation, do not scan previous lesson folders, PDFs, HTML files, or `lesson_source.json` files to decide a new Theme or Specific Topic.
  - After resolving the target Day and Level, filter the history to the same Level and inspect only the recent rows required by the 3-day Theme and 7-day Specific Topic windows.
- **Theme & Topic Anti-Duplication Rule**:
  - **3-Day Theme Anti-Duplication**: The agent must NOT generate a lesson on the same **Theme** (e.g. `Pets, animals, basic animal care`) for the same Level within 3 consecutive days/lessons.
  - **7-Day Specific Topic Anti-Duplication**: The agent must NOT generate a lesson on the same **Specific Topic** (e.g. `Wildlife rescue & animal hospital care`) or highly similar content for the same Level within 7 consecutive days/lessons.
- **Vocabulary Recycling Lookup**:
  - Use [lesson_history.txt](../outputs/ielts-daily-reading-writing/lesson_history.txt) to select one prior same-Level lesson before the target Day, normally the most recent one.
  - Read only that lesson's single `Quizlet-Vocab.md` file to choose recycled vocabulary.
  - Do not read multiple Quizlet files, previous `lesson_source.json` files, PDFs, or HTML files for routine daily vocabulary recycling.

## Question Quality & Answer Uniqueness
- **Single Unique Answer Rule**: Every question generated (including reading MCQs, True/False/Not Given, short-answer gap-fills, grammar verb-tenses, and conjunction fills) must be strictly designed to have **exactly one unique correct answer**. Avoid vague contexts, overlapping MCQ options, or open-ended grammar prompts that admit multiple grammatically valid responses. For grammar exercises, always constrain the answer choice (e.g., by specifying base verbs in parentheses) to ensure uniqueness of spelling and form.
- **Anti-Skimming/Scanning Question Design**: Reading questions must be designed to test true comprehension rather than simple word-matching. Do not repeat scannable keywords from the passage directly in the questions. Instead, utilize paraphrases (synonyms, antonyms, passive-to-active voice changes) and deliberately place scannable keywords in incorrect distractor choices to bait students who guess answers solely through skimming or scanning.
