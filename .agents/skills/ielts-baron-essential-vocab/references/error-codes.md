# Error Codes

Every error code includes stage, severity, retryable flag, action, and HITL requirement.

| Code | Stage | Severity | Retryable | Action | HITL |
|------|-------|----------|-----------|--------|------|
| `SRC_ACCESS_DENIED` | source-acquire | critical | yes (3x) | Check URL permissions | if persist |
| `SRC_DOWNLOAD_FAILED` | source-acquire | high | yes (3x) | Retry with backoff | if persist |
| `SRC_UNSUPPORTED_FORMAT` | request-intake | critical | no | Ask user for PDF | yes |
| `SRC_HASH_MISMATCH` | cache-resolve | high | no | Source changed, new cache | no |
| `PDF_ENCRYPTED` | pdf-structure | critical | no | Ask user for password | yes |
| `PDF_TEXT_LAYER_MISSING` | pdf-structure | high | no | Trigger full OCR | no |
| `OCR_LOW_CONFIDENCE` | text-extract | medium | yes (per page) | Re-OCR specific page | if < 0.85 |
| `UNIT_NOT_FOUND` | unit-locate | critical | yes (1x) | Escalate to LLM then human | yes |
| `UNIT_AMBIGUOUS` | unit-locate | high | no | Show candidates to human | yes |
| `QUESTION_COUNT_MISMATCH` | grounding-validate | high | no | Flag discrepancy | if critical |
| `ANSWER_KEY_NOT_FOUND` | grounding-validate | high | no | Mark UNRESOLVED, no fabrication | yes |
| `ANSWER_MAPPING_LOW_CONFIDENCE` | answer-build | medium | yes (1x) | Escalate or human review | if < 0.90 |
| `PROVENANCE_MISSING` | grounding-validate | high | no | Add source refs or mark gap | no |
| `LEVEL_ASSESSMENT_LOW_CONFIDENCE` | level-assess | medium | yes (1x) | Human override | yes |
| `CONTENT_QA_FAILED` | content-qa | high | no | Fix upstream, re-QA | no |
| `HTML_VALIDATION_FAILED` | html-render | high | yes (2x) | Fix template, re-render | no |
| `PDF_RENDER_FAILED` | pdf-render | high | yes (2x) | Check Playwright, re-render | no |
| `PDF_PAGE_OVERFLOW` | pdf-visual-qa | medium | yes | Adjust CSS, re-render | no |
| `PDF_ASSET_MISSING` | pdf-visual-qa | high | no | Check asset paths | no |
| `FOOTER_INVALID` | pdf-visual-qa | medium | yes | Fix footer template | no |
| `CACHE_CORRUPTED` | cache-resolve | high | no | Delete cache, fresh run | no |
| `HUMAN_REVIEW_REQUIRED` | any | info | no | Wait for human | yes |
| `EXECUTION_POLICY_VIOLATION` | routing | critical | no | Block, log violation | no |
| `MODEL_OUTPUT_VALIDATION_FAILED` | any LLM stage | high | yes (1x) | Retry or escalate | if persist |
| `MODEL_BUDGET_EXCEEDED` | routing | high | no | Block premium call | no |
| `PRIVACY_POLICY_VIOLATION` | routing | critical | no | Block external call | no |
