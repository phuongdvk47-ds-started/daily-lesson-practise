# Model Selection Policy

## Priority Order
```
Deterministic local tool → Open-source model local → LLM low-cost → Premium LLM → Human review
```

## Core Rule
> Use the cheapest engine that reliably passes the required quality gate.

NOT: "Always use the cheapest engine regardless of quality."

## Execution Classes

| Class | Cost | Privacy | Examples |
|-------|------|---------|----------|
| DETERMINISTIC | Free | Local | hashlib, regex, Jinja2, PyMuPDF |
| LOCAL_MODEL | Free | Local | PaddleOCR, Tesseract, spaCy, sentence-transformers |
| LOW_COST_LLM | Low | External | Gemini Flash, GPT-4o-mini equivalents |
| PREMIUM_LLM | Medium-High | External | Gemini Pro, GPT-4o, Claude equivalents |
| HUMAN_REQUIRED | N/A | Local | Checkpoint decisions |

## Budget Defaults per Class

| Class | Max Input Tokens | Max Output Tokens | Max Attempts |
|-------|-----------------|-------------------|--------------|
| DETERMINISTIC | 0 | 0 | 3 |
| LOCAL_MODEL | 4000 | 2000 | 3 |
| LOW_COST_LLM | 6000 | 2000 | 2 |
| PREMIUM_LLM | 8000 | 4000 | 2 |

## Premium LLM Justification

Premium LLM is only justified for tasks requiring:
- Multi-step reasoning
- Cross-reference analysis
- Nuanced linguistic judgment
- Ambiguity resolution with competing evidence

Tasks that MUST NOT use Premium LLM:
- File I/O, checksums, hashing
- JSON serialization, schema validation
- HTML/PDF rendering
- Page numbering, footer generation
- Regex matching, string operations
- Directory operations, cache management
