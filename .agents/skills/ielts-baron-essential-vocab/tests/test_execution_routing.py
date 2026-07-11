"""Tests for execution routing — policy enforcement, premium blocking, privacy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from route_execution import route_task, validate_routing_decision, ROUTING_POLICY


class TestDeterministicRouting:
    def test_checksum_is_deterministic(self):
        decision = route_task("fingerprint")
        assert decision["selected_execution_class"] == "DETERMINISTIC"
        assert decision["selected_engine"] == "hashlib_sha256"

    def test_html_render_is_deterministic(self):
        decision = route_task("html_render")
        assert decision["selected_execution_class"] == "DETERMINISTIC"
        assert decision["selected_engine"] == "jinja2"

    def test_pdf_render_is_deterministic(self):
        decision = route_task("pdf_render")
        assert decision["selected_execution_class"] == "DETERMINISTIC"

    def test_footer_is_deterministic(self):
        decision = route_task("footer_generation")
        assert decision["selected_execution_class"] == "DETERMINISTIC"

    def test_lesson_id_is_deterministic(self):
        decision = route_task("lesson_id_generation")
        assert decision["selected_execution_class"] == "DETERMINISTIC"


class TestPremiumBlocking:
    def test_deterministic_blocks_premium(self):
        """Premium LLM must be blocked for deterministic tasks."""
        for task_name, policy in ROUTING_POLICY.items():
            if policy["execution_class"] == "DETERMINISTIC":
                assert not policy.get("premium_llm_allowed", False), \
                    f"EXECUTION_POLICY_VIOLATION: {task_name} allows premium LLM"

    def test_local_model_blocks_premium(self):
        """Premium LLM must be blocked for LOCAL_MODEL tasks."""
        for task_name, policy in ROUTING_POLICY.items():
            if policy["execution_class"] == "LOCAL_MODEL":
                assert not policy.get("premium_llm_allowed", False), \
                    f"EXECUTION_POLICY_VIOLATION: {task_name} allows premium LLM"

    def test_premium_allowed_only_for_premium_tasks(self):
        """Only PREMIUM_LLM and LOW_COST_LLM tasks may allow premium."""
        for task_name, policy in ROUTING_POLICY.items():
            if policy.get("premium_llm_allowed", False):
                assert policy["execution_class"] in ("PREMIUM_LLM", "LOW_COST_LLM"), \
                    f"EXECUTION_POLICY_VIOLATION: {task_name} class={policy['execution_class']} allows premium"


class TestPrivacyEnforcement:
    def test_local_only_blocks_external_llm(self):
        decision = route_task("cefr_assessment", privacy_level="local-only")
        # Should be blocked since CEFR requires premium but privacy is local-only
        assert decision["selected_execution_class"] in ("BLOCKED", "HUMAN_REQUIRED") or \
               decision.get("error_code") == "PRIVACY_POLICY_VIOLATION"

    def test_normal_privacy_allows_llm(self):
        decision = route_task("cefr_assessment", privacy_level="normal")
        assert decision["selected_execution_class"] == "PREMIUM_LLM"


class TestCostAwareness:
    def test_deterministic_is_free(self):
        for task_name, policy in ROUTING_POLICY.items():
            if policy["execution_class"] == "DETERMINISTIC":
                assert policy.get("estimated_cost_class", "free") == "free", \
                    f"{task_name} should be free"

    def test_local_model_is_free(self):
        for task_name, policy in ROUTING_POLICY.items():
            if policy["execution_class"] == "LOCAL_MODEL":
                assert policy.get("estimated_cost_class", "free") == "free", \
                    f"{task_name} should be free"


class TestUnknownTask:
    def test_unknown_task_defaults_to_premium(self):
        decision = route_task("completely_unknown_task_xyz")
        assert decision["selected_execution_class"] == "PREMIUM_LLM"
