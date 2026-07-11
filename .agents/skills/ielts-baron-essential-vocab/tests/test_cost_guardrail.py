"""Tests for cost guardrail — budget enforcement and premium blocking."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from estimate_task_cost import estimate_cost_class, estimate_tokens
from route_execution import route_task, ROUTING_POLICY


class TestTokenEstimation:
    def test_short_text(self):
        tokens = estimate_tokens("hello world")
        assert tokens >= 1

    def test_longer_text(self):
        text = "This is a longer sentence with more words for testing purposes."
        tokens = estimate_tokens(text)
        assert tokens > 5


class TestCostClassification:
    def test_deterministic_is_free(self):
        result = estimate_cost_class("DETERMINISTIC", 0, 0)
        assert result["cost_class"] == "free"
        assert result["estimated_cost_usd"] == 0

    def test_local_model_is_free(self):
        result = estimate_cost_class("LOCAL_MODEL", 1000, 500)
        assert result["cost_class"] == "free"

    def test_low_cost_llm_is_low(self):
        result = estimate_cost_class("LOW_COST_LLM", 2000, 1000)
        assert result["cost_class"] in ("free", "low")

    def test_premium_llm_costs_more(self):
        result = estimate_cost_class("PREMIUM_LLM", 5000, 3000)
        # Should have nonzero cost
        assert result["estimated_cost_usd"] > 0


class TestCostGuardrails:
    def test_deterministic_tasks_have_no_cost(self):
        """All deterministic tasks should have zero token budgets."""
        for task_name, policy in ROUTING_POLICY.items():
            if policy["execution_class"] == "DETERMINISTIC":
                decision = route_task(task_name)
                budget = decision.get("budget", {})
                assert budget.get("max_cost_class") == "free", \
                    f"{task_name} should be free, got {budget}"

    def test_no_premium_escalation_for_deterministic(self):
        """Deterministic tasks should never allow premium escalation."""
        for task_name, policy in ROUTING_POLICY.items():
            if policy["execution_class"] == "DETERMINISTIC":
                decision = route_task(task_name)
                budget = decision.get("budget", {})
                assert not budget.get("premium_escalation_allowed", False), \
                    f"{task_name} should not allow premium escalation"
