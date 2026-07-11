#!/usr/bin/env python3
"""Estimate task cost — token counting and cost classification."""
from __future__ import annotations

import json
import sys


# Rough token estimation: 1 token ≈ 4 characters for English
def estimate_tokens(text: str) -> int:
    """Estimate token count from text length."""
    return max(1, len(text) // 4)


def estimate_cost_class(execution_class: str, input_tokens: int, output_tokens: int) -> dict:
    """Estimate cost class for a task.

    Returns dict with estimated_cost, cost_class, within_budget.
    """
    # Cost per 1M tokens (rough estimates)
    COST_RATES = {
        "DETERMINISTIC": {"input": 0, "output": 0},
        "LOCAL_MODEL": {"input": 0, "output": 0},
        "LOW_COST_LLM": {"input": 0.15, "output": 0.60},
        "PREMIUM_LLM": {"input": 2.50, "output": 10.00},
        "HUMAN_REQUIRED": {"input": 0, "output": 0},
    }

    rates = COST_RATES.get(execution_class, COST_RATES["PREMIUM_LLM"])
    cost = (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000

    if cost == 0:
        cost_class = "free"
    elif cost < 0.01:
        cost_class = "low"
    elif cost < 0.10:
        cost_class = "medium"
    else:
        cost_class = "high"

    return {
        "estimated_cost_usd": round(cost, 6),
        "cost_class": cost_class,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "execution_class": execution_class,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Estimate task cost")
    parser.add_argument("--class", dest="exec_class", required=True)
    parser.add_argument("--input-tokens", type=int, required=True)
    parser.add_argument("--output-tokens", type=int, required=True)
    args = parser.parse_args()

    result = estimate_cost_class(args.exec_class, args.input_tokens, args.output_tokens)
    print(json.dumps(result, indent=2))
