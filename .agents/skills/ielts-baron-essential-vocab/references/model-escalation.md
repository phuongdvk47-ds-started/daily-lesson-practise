# Model Escalation Policy

## Escalation Chain
```
Rule-based/local library → Local model → Low-cost LLM → Premium LLM → Human review
```

## Escalation Conditions
Only escalate when:
- Schema validation fails at current tier
- Confidence below quality threshold
- Provenance requirements not met
- Semantic consistency fails
- Multiple ambiguous candidates found
- Retry limit exceeded at current tier
- Risk level is high and current tier inadequate

Do NOT escalate just because:
- Output formatting isn't perfect
- Minor cosmetic issues
- Task could theoretically benefit from better model

## Escalation Example
```json
{
  "task": "unit_location",
  "attempts": [
    {
      "engine": "rule_based_heading_matcher",
      "execution_class": "LOCAL_MODEL",
      "confidence": 0.71,
      "result": "AMBIGUOUS",
      "reason": "Multiple heading candidates"
    },
    {
      "engine": "sentence_transformer_similarity",
      "execution_class": "LOCAL_MODEL",
      "confidence": 0.88,
      "result": "BELOW_THRESHOLD",
      "reason": "Confidence 0.88 < threshold 0.90"
    },
    {
      "engine": "configured_low_cost_model",
      "execution_class": "LOW_COST_LLM",
      "confidence": 0.94,
      "result": "APPROVED",
      "reason": "Confidence 0.94 >= threshold 0.90"
    }
  ],
  "premium_llm_used": false,
  "total_cost": 0.002
}
```
