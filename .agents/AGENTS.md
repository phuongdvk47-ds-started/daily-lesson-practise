# Project Rules

## Document & URL Verification
- **No Fabricated URLs**: All generated learning materials, reading passages, and study resources must use authentic, active, and verified source URLs (e.g., from VOA Learning English, BBC, British Council).
- **Check Validity**: The agent must verify the correctness of the article URLs and sources using web search or direct HTTP checks prior to generating them. Do not hallucinate article IDs, publication dates, or link paths.
- **Accurate Citations**: Ensure adapted reading texts match the details of the actual source article.
- **B2+ Current Affairs Priority**: For Level B2, C1, and C2 lessons, prioritize choosing reading sources with high timeliness (current affairs, recent news, contemporary essays) to closely align with real IELTS Academic Reading and Writing tasks.

## Topic Redundancy & History Tracking
- **Consult History**: Before generating any new lesson, the agent must inspect the [lesson_history.txt](../outputs/ielts-daily-reading-writing/lesson_history.txt) file.
- **Update History**: Upon successfully generating a new lesson, the agent must append the new lesson details to the end of [lesson_history.txt](../outputs/ielts-daily-reading-writing/lesson_history.txt) following the new 4-column format: `Level | Day | Theme | Specific Topic`.
- **Theme & Topic Anti-Duplication Rule**:
  - **3-Day Theme Anti-Duplication**: The agent must NOT generate a lesson on the same **Theme** (e.g. `Pets, animals, basic animal care`) for the same Level within 3 consecutive days/lessons.
  - **7-Day Specific Topic Anti-Duplication**: The agent must NOT generate a lesson on the same **Specific Topic** (e.g. `Wildlife rescue & animal hospital care`) or highly similar content for the same Level within 7 consecutive days/lessons.
