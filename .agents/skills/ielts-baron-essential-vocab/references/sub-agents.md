# Sub-Agents

Detailed responsibilities for each agent. See pipeline-contracts.md for JSON specifications.

## Agent 00 — Request Intake & Input Normalizer
- Receive CLI args or chat parameters
- Normalize source path/URL
- Normalize unit/topic/day
- Validate required inputs
- Generate request_id
- Create `request.normalized.json`
- Does NOT download, parse, or analyze

## Agent 00B — Execution & Model Router
- Classify every task by execution class
- Select cheapest qualifying engine
- Enforce premium blocking
- Enforce privacy policy
- Enforce budget limits
- Log routing decisions
- Does NOT execute tasks

## Agent 01 — Source Identity & Cache Resolver
- Compute SHA-256 of source file
- Generate unique_source_id
- Check if cache exists for this source
- Identify which stages have valid cached outputs
- Mark cached stages as SKIPPED_FROM_CACHE
- Does NOT download or modify source

## Agent 02 — Source Acquisition
- Download from URL or copy local file
- Save as `source/original.pdf`
- Generate `source-metadata.json` and `checksum.sha256`
- Never modify the source file
- Does NOT parse or analyze content

## Agent 03 — PDF Structure Analyzer
- Count pages
- Read PDF outline / bookmarks
- Detect text layer presence
- Inventory images per page
- Detect tables per page
- Identify pages needing OCR
- Does NOT extract content

## Agent 04 — Text & Asset Extractor
- Extract text blocks with page, bbox, reading order
- Extract images with metadata
- Extract tables as structured data
- Run selective OCR on pages without text layer
- Does NOT interpret or analyze content

## Agent 05 — Unit/Topic Locator
- Search extraction for target unit heading
- Match against unit patterns (regex first, then embedding)
- Determine page range for unit
- Locate reading passage, questions, vocabulary, answer key sections
- Human review if ambiguous
- Does NOT extract full content from located sections

## Agent 06 — Source Canonicalizer
- Convert located extraction into canonical-source.json
- Map text blocks to paragraphs, questions, vocabulary, answers
- Attach source_refs to every element
- Does NOT add content, enrich, or explain

## Agent 07 — Grounding & Fidelity Validator
- Compare canonical source against raw extraction
- Detect missing paragraphs, reordered content
- Verify question count
- Verify answer key mapping
- Check source_refs completeness
- Does NOT fix errors, only reports

## Agent 08 — Reading Level Assessor
- Receives ONLY reading passage text (lazy loading)
- Assess CEFR level with evidence
- Assess IELTS Band range
- Analyze lexical, grammar, discourse complexity
- Assess inference burden
- Human review if confidence < 0.75

## Agent 09 — Lesson Identity Manager
- Generate LSN-[Day]-[Level]-[Random8]
- Preserve existing ID on rerun
- Validate format
- Pure deterministic

## Agent 10 — Vocabulary Knowledge Builder
- Academic vocabulary with IPA, POS, definition, Vietnamese, examples
- Compound words, idioms, phrasal verbs, collocations
- Label every item: SOURCE_EXTRACTED / ENRICHED_CONTENT / etc.
- Source examples must have source_refs
- Generated examples must be labeled

## Agent 11 — Grammar & Strategy Analyst
- Identify dominant grammar points from reading
- Explain formula, nature, translation thinking
- Apply to IELTS Writing Task 2
- Create ≥3 Tips & Tricks
- Provide 3 learning link groups (Cambridge, British Council, PEG)

## Agent 12 — Daily Practice Composer
- Assemble practice document without answers
- Include header, student info, reading, questions, word family, assets
- NO answer key, NO explanations

## Agent 13 — Answer Key & Explanation Builder
- Detailed answers with evidence, reasoning, distractor analysis
- Paraphrase matrix
- Word family explanations
- Confidence and review status per answer

## Agent 14 — Content QA Agent
- Check completeness, consistency, no leakage
- Generate qa/content-qa-report.json
- MUST pass before rendering

## Agent 15 — Document Model Builder
- Create render-ready document model
- Define sections, blocks, page breaks, typography
- Reference assets by path

## Agent 16 — HTML Renderer
- Render 3 HTML files from Jinja2 templates
- Include print CSS
- Print-safe, A4

## Agent 17 — PDF Renderer
- Convert HTML to PDF via Playwright
- Add footer with lession_id and page numbers
- A4 format

## Agent 18 — PDF Visual QA
- Inspect rendered PDFs
- Check A4 size, blank pages, footer, overflow
- Generate qa/visual-qa-report.json
