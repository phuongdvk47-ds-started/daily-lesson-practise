#!/usr/bin/env python3
"""Validate execution policy — enforce routing rules, premium blocking, privacy."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from route_execution import ROUTING_POLICY, validate_routing_decision


def validate_execution_policy(task_name: str, decision: dict) -> dict:
    """Validate that a routing decision complies with all policies.

    Returns validation report.
    """
    checks = []

    # Check 1: Task has a defined policy
    policy = ROUTING_POLICY.get(task_name)
    if policy is None:
        checks.append({
            "check": "policy_exists",
            "status": "WARN",
            "message": f"No policy defined for task '{task_name}' — using defaults",
        })
    else:
        checks.append({
            "check": "policy_exists",
            "status": "PASS",
            "message": f"Policy found for '{task_name}'",
        })

    # Check 2: Premium LLM not used for blocked tasks
    if decision.get("selected_execution_class") == "PREMIUM_LLM":
        if policy and not policy.get("premium_llm_allowed", False):
            checks.append({
                "check": "premium_not_blocked",
                "status": "FAIL",
                "message": f"EXECUTION_POLICY_VIOLATION: Premium LLM blocked for '{task_name}'",
            })
        else:
            checks.append({
                "check": "premium_not_blocked",
                "status": "PASS",
                "message": "Premium LLM allowed for this task",
            })

    # Check 3: Budget within limits
    budget = decision.get("budget", {})
    if budget.get("max_cost_class") == "free" and decision.get("selected_execution_class") in ("LOW_COST_LLM", "PREMIUM_LLM"):
        checks.append({
            "check": "budget_respected",
            "status": "FAIL",
            "message": "MODEL_BUDGET_EXCEEDED: Task budget is 'free' but LLM selected",
        })
    else:
        checks.append({
            "check": "budget_respected",
            "status": "PASS",
            "message": "Budget within limits",
        })

    # Check 4: Privacy
    if decision.get("privacy_level") == "local-only":
        if decision.get("selected_execution_class") in ("LOW_COST_LLM", "PREMIUM_LLM"):
            checks.append({
                "check": "privacy_respected",
                "status": "FAIL",
                "message": "PRIVACY_POLICY_VIOLATION: local-only but external LLM selected",
            })
        else:
            checks.append({
                "check": "privacy_respected",
                "status": "PASS",
                "message": "Privacy policy satisfied",
            })

    has_fail = any(c["status"] == "FAIL" for c in checks)
    return {
        "status": "FAIL" if has_fail else "PASS",
        "checks": checks,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate execution policy")
    parser.add_argument("--task", required=True)
    parser.add_argument("--decision", required=True, help="Path to routing decision JSON")
    args = parser.parse_args()

    decision = json.loads(Path(args.decision).read_text(encoding="utf-8"))
    result = validate_execution_policy(args.task, decision)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "PASS" else 1)
