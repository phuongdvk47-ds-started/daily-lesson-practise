# Project Rules

## Document & URL Verification
- **No Fabricated URLs**: All generated learning materials, reading passages, and study resources must use authentic, active, and verified source URLs (e.g., from VOA Learning English, BBC, British Council).
- **Check Validity**: The agent must verify the correctness of the article URLs and sources using web search or direct HTTP checks prior to generating them. Do not hallucinate article IDs, publication dates, or link paths.
- **Accurate Citations**: Ensure adapted reading texts match the details of the actual source article.
- **B2+ Current Affairs Priority**: For Level B2, C1, and C2 lessons, prioritize choosing reading sources with high timeliness (current affairs, recent news, contemporary essays) to closely align with real IELTS Academic Reading and Writing tasks.

## Topic Redundancy & History Tracking
- **Consult History**: Before generating any new lesson, the agent must inspect the [lesson_history.txt](../outputs/ielts-daily-reading-writing/lesson_history.txt) file.
- **3-Day Anti-Duplication Rule**: The agent must NOT generate a lesson on the same Topic for the same Level within 3 consecutive days/lessons. For example, if Topic A is generated for Level A2 on Day 1, it cannot be generated for Level A2 on Day 2 or Day 3. It can only be repeated on Day 4 or later.
- **Update History**: Upon successfully generating a new lesson, the agent must append the new lesson details (Level | Day | Topic) to the end of [lesson_history.txt](../outputs/ielts-daily-reading-writing/lesson_history.txt) following the established format.
