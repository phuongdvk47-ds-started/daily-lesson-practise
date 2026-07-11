# Rendering Rules

## Document Types
Three separate PDFs are generated per lesson:
1. **daily-practice.pdf** — Student worksheet (NO answers)
2. **vocabulary-grammar.pdf** — Knowledge reference
3. **answer-key.pdf** — Teacher/self-check document

## Template Engine
- Jinja2 with FileSystemLoader
- Templates in `assets/templates/`
- Print CSS injected inline via `{{ print_css }}`

## HTML Rendering Pipeline
```
document-model.json → Jinja2 → HTML → Playwright → PDF
```

## PDF Generation Rules
- Format: A4
- Margins: top 14mm, right 13mm, bottom 16mm, left 13mm
- Footer: `[lession_id] | Page [current]/[total]`
- Print background: true
- Wait until: networkidle

## Anti-Leakage Rules
The `daily-practice.html` template must NOT contain:
- Answer text
- Evidence quotes
- Reasoning explanations
- Distractor analysis
- Confidence scores
- Review status

## Image Handling
- Source images are embedded via relative path
- Playwright resolves local `file://` URLs
- Images maintain original quality and aspect ratio

## Font Requirements
- Times New Roman for body text
- Noto Sans / DejaVu Sans for IPA transcriptions
- Full Unicode support for Vietnamese text

## Page Break Strategy
- Avoid breaking inside: questions, tips, grammar formulas, word family items
- Allow breaking between: table rows, question blocks
- Enforce orphan/widow minimums: 3 lines each
