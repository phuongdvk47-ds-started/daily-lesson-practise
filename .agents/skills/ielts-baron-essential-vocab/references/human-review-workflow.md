# Human Review Workflow

## Checkpoints

### Checkpoint A — Source Selection
**Trigger**: Google Drive folder, multiple files, multiple versions, non-PDF.
**Display**: File list with names, sizes, dates.
**Decision**: Select correct file.
**Logged as**: `{"checkpoint": "A", "decision": "selected file X", "actor": "human"}`

### Checkpoint B — Unit Confirmation
**Trigger**: Multiple unit candidates, confidence < 0.90, ambiguous headings.
**Display**: Candidate list with page ranges, heading text, confidence scores.
**Decision**: Confirm correct unit or provide manual page range.
**Logged as**: `{"checkpoint": "B", "decision": "confirmed Unit 3 pages 45-58", "actor": "human"}`

### Checkpoint C — Extraction Review
**Trigger**: OCR confidence < 0.85, missing text, table parsing errors, image misplacement, question count mismatch.
**Display**: Extraction report with warnings, low-confidence blocks.
**Decision**: Accept, request re-OCR for specific pages, or provide manual corrections.

### Checkpoint D — Level Approval
**Trigger**: Level assessment complete.
**Display**: CEFR level, IELTS Band range, evidence (lexical, grammar, discourse), confidence.
**Decision**: Accept or override with reason.
**Override format**:
```json
{
  "checkpoint": "D",
  "decision": "override",
  "reason": "Passage complexity matches B2+ not C1",
  "original_cefr": "C1",
  "override_cefr": "B2",
  "timestamp": "...",
  "actor": "human"
}
```

### Checkpoint E — Content Preview
**Trigger**: All content stages complete, before rendering.
**Display**: Outlines of Daily Practice, Vocabulary, Grammar, Answer Key sections. Enriched content highlighted.
**Decision**: Approve or request revisions.

### Checkpoint F — Final PDF Approval
**Trigger**: PDFs rendered, Visual QA complete.
**Display**: File paths, page counts, QA results, warnings, provenance summary, cost summary.
**Decision**: Accept, reject (request re-render), or accept with known warnings.

## Decision Logging

All human decisions are stored in `human-decisions.json`:
```json
[
  {
    "checkpoint": "B",
    "decision": "confirmed",
    "reason": "Unit 1 clearly identified on page 10",
    "timestamp": "2024-01-15T10:30:00Z",
    "actor": "human"
  }
]
```

## Skip Mode

When `--skip-human-review` is set, all checkpoints are auto-approved with `"actor": "agent"`.
Warnings are still logged.
