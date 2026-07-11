# Cost-Quality Policy

## Core Principle
> Use the cheapest engine that reliably passes the required quality gate.

Cost optimization must NEVER reduce content fidelity or provenance integrity.

## Cost Classes
| Class | Estimated Cost per Task | Examples |
|-------|------------------------|----------|
| free | $0 | Deterministic, local model |
| low | < $0.01 | Low-cost LLM short tasks |
| medium | $0.01 - $0.10 | Premium LLM with bounded context |
| high | > $0.10 | Premium LLM with large context |

## Budget Enforcement
- Each task declares `max_cost_class`
- Router blocks tasks exceeding budget
- Token limits enforced per task
- Context minimization required (lazy loading)

## Escalation Justification
Every premium escalation must log:
```json
{
  "task": "...",
  "escalated_from": "low_cost_llm",
  "escalated_to": "premium_llm",
  "reason": "Schema validation failed: missing evidence field",
  "attempt_count": 2,
  "quality_score_before": 0.72,
  "quality_threshold": 0.90
}
```
