# Cache and Retry Strategy

## Cache Root
```
.cache/ielts-baron-essential-vocab/[unique_source_id]/
├── source/
├── extraction/
├── units/
├── analysis/
├── lessons/[lession_id]/
├── model-cache/
├── logs/
├── state/
│   ├── pipeline-state.json
│   ├── stage-checksums.json
│   └── human-decisions.json
└── cache-manifest.json
```

## Cache-First Rule

Before running any stage, check:
1. Output artifact exists?
2. Input checksum matches?
3. Stage version unchanged?
4. Schema validation passes?
5. Output status = COMPLETE?
6. Prompt/model version unchanged?
7. Upstream dependencies still valid?

If ALL pass → skip (status: `SKIPPED_FROM_CACHE`).
Otherwise → rerun.

## Rerun Triggers
- Artifact missing
- Input checksum changed
- Schema validation fails
- Stage version changed
- Prompt version changed
- Model version changed
- User `--force-*` flag
- Artifact marked stale
- Artifact marked failed

## Stage States
```
PENDING → RUNNING → COMPLETE
                  → FAILED → (retry) → RUNNING
                  → BLOCKED
                  → WAITING_FOR_HUMAN → (decision) → RUNNING
SKIPPED_FROM_CACHE
STALE
```

## Retry Policy
- Each stage declares its own `max_retries` and `backoff_strategy`
- Retry is per-stage, NOT restart-from-beginning
- If OCR fails on page 18 → retry page 18, not all pages
- If render fails → retry render, not extraction
- If grammar analysis fails → retry grammar, not level assessment

## Idempotency Rules
Same input MUST:
- Not generate new lession_id
- Not re-download source
- Not create duplicate cache entries
- Not modify unrelated artifacts

## Model Cache
Key = SHA-256 of (input_data + task_name + engine_name + model_version + prompt_version + schema_version)

```
model-cache/[task-name]/[cache-key]/
├── input.json
├── output.json
├── validation.json
└── execution-metadata.json
```

If cache valid → no model call. Never overwrite valid cache when model/prompt version changes — create new entry.
