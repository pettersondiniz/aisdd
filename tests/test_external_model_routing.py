from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_bridge import delegate_read_only  # noqa: E402
from model_routing import delegate_external, resolve, route_with_external_fallback  # noqa: E402


class FakeBridge:
    def __init__(self, *, catalog=None, start=None, waits=None, errors=None, responses=None):
        self.catalog = catalog if catalog is not None else [{"id": "provider/model"}]
        self.start = start if start is not None else {"job_id": "job-1", "session_id": "session-1"}
        self.waits = list(waits or [{"status": "completed", "text": "ok", "changed_paths": []}])
        self.errors = errors or {}
        self.responses = responses or {}
        self.calls: list[tuple[str, dict[str, object]]] = []

    def _record(self, operation: str, arguments: dict[str, object]):
        self.calls.append((operation, arguments))
        if operation in self.errors:
            error = self.errors[operation]
            raise error if isinstance(error, Exception) else RuntimeError(str(error))

    def external_models(self, **arguments):
        self._record("external_models", arguments)
        return self.responses.get("external_models", {"models": self.catalog})

    def delegate_start(self, **arguments):
        self._record("delegate_start", arguments)
        return self.responses.get("delegate_start", self.start)

    def delegate_wait(self, **arguments):
        self._record("delegate_wait", arguments)
        return self.waits.pop(0) if self.waits else {"status": "timeout"}


def external(model: str = "provider/model", profile: str = "read") -> dict[str, str]:
    return {"provider": "agent-bridge", "model": model, "profile": profile}


def routing_config() -> dict[str, object]:
    return {
        "fallback": {"model": "gpt-general", "reasoning_effort": "low"},
        "tiers": {"standard": {"model_patterns": [".*"], "effort_order": ["high", "low"]}},
        "roles": {
            "tester": {
                "model": "gpt-specific",
                "reasoning_effort": "high",
                "tier": "standard",
                "by_class": {
                    "T3": {
                        "model": "gpt-specific-t3",
                        "reasoning_effort": "high",
                        "tier": "standard",
                        "external": external("provider/model#max"),
                    }
                },
            }
        },
    }


class ExternalModelRoutingTests(unittest.TestCase):
    # @spec:AC-001
    def test_without_external_preserves_openai_route_and_does_not_use_mcp(self):
        client = FakeBridge(errors={"external_models": "MCP must not be called"})
        recommendation = resolve(routing_config(), "tester", [{"id": "gpt-specific", "reasoning_efforts": ["high"]}])
        result = route_with_external_fallback(
            recommendation, client, workspace="repo", prompt="inspect", openai_specific=lambda: "specific", openai_general=lambda: "general"
        )
        self.assertEqual(result["route"], "openai-specific")
        self.assertEqual(result["result"], "specific")
        self.assertEqual(client.calls, [])

    # @spec:AC-002
    def test_class_fields_remain_the_specific_openai_fallback(self):
        recommendation = resolve(routing_config(), "tester", [{"id": "gpt-specific-t3", "reasoning_efforts": ["high"]}], "T3")
        self.assertEqual(recommendation["model"], "gpt-specific-t3")
        self.assertEqual(recommendation["reasoning_effort"], "high")
        self.assertEqual(recommendation["tier"], "standard")
        self.assertEqual(recommendation["external"]["model"], "provider/model#max")

    # @spec:AC-003
    def test_external_route_is_resolved_by_role_and_class(self):
        recommendation = resolve(routing_config(), "tester", [{"id": "gpt-specific-t3", "reasoning_efforts": ["high"]}], "T3")
        self.assertTrue(recommendation["class_applied"])
        self.assertEqual(recommendation["configured_role"], "tester")
        self.assertEqual(recommendation["external"]["provider"], "agent-bridge")

    # @spec:AC-004
    def test_catalog_discovery_precedes_start(self):
        client = FakeBridge()
        delegate_read_only(client, external(), workspace="repo", prompt="inspect")
        self.assertEqual([call[0] for call in client.calls], ["external_models", "delegate_start", "delegate_wait"])

    # @spec:AC-005
    def test_external_model_matching_is_literal_and_complete(self):
        client = FakeBridge(catalog=[{"id": "provider/model#max"}])
        result = delegate_read_only(client, external("provider/model"), workspace="repo", prompt="inspect")
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "discovery")
        self.assertEqual([call[0] for call in client.calls], ["external_models"])

    # @spec:AC-006
    def test_missing_model_does_not_start_and_falls_back(self):
        client = FakeBridge(catalog=[{"id": "other/model"}])
        result = route_with_external_fallback(
            {"external": external()}, client, workspace="repo", prompt="inspect", openai_specific=lambda: "specific", openai_general=lambda: "general"
        )
        self.assertEqual(result["route"], "openai-specific")
        self.assertEqual([call[0] for call in client.calls], ["external_models"])

    # @spec:AC-007
    def test_discovery_failure_uses_openai_fallback(self):
        client = FakeBridge(errors={"external_models": "bridge unavailable"})
        result = route_with_external_fallback(
            {"external": external()}, client, workspace="repo", prompt="inspect", openai_specific=lambda: "specific", openai_general=lambda: "general"
        )
        self.assertEqual(result["route"], "openai-specific")
        self.assertEqual(result["external"]["stage"], "discovery")

    # @spec:AC-007
    def test_is_error_external_models_ignores_valid_structured_content_and_falls_back(self):
        client = FakeBridge(
            responses={
                "external_models": {
                    "isError": True,
                    "structuredContent": {"models": [{"id": "provider/model"}]},
                }
            }
        )
        result = route_with_external_fallback(
            {"external": external()}, client, workspace="repo", prompt="inspect", openai_specific=lambda: "specific", openai_general=lambda: "general"
        )
        operations = [call[0] for call in client.calls]
        self.assertEqual(result["route"], "openai-specific")
        self.assertEqual(result["result"], "specific")
        self.assertEqual(result["external"]["stage"], "discovery")
        self.assertNotIn("delegate_start", operations)
        self.assertNotIn("delegate_wait", operations)

    # @spec:AC-008
    def test_start_receives_read_workspace_prompt_model_and_session(self):
        client = FakeBridge(catalog=[{"id": "provider/model#max"}])
        delegate_read_only(client, external("provider/model#max"), workspace="repo", prompt="inspect", session_id="session-0", timeout_ms=250)
        arguments = client.calls[1][1]
        self.assertEqual(arguments, {"workspace": "repo", "prompt": "inspect", "model": "provider/model#max", "profile": "read", "session_id": "session-0", "timeout_ms": 250})

    # @spec:AC-009
    def test_write_profile_is_rejected_before_any_mcp_call(self):
        client = FakeBridge()
        result = delegate_read_only(client, external(profile="write"), workspace="repo", prompt="mutate")
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "config")
        self.assertEqual(client.calls, [])

    # @spec:AC-010
    def test_start_failure_uses_openai_fallback(self):
        client = FakeBridge(errors={"delegate_start": "start failed"})
        result = route_with_external_fallback(
            {"external": external()}, client, workspace="repo", prompt="inspect", openai_specific=lambda: "specific", openai_general=lambda: "general"
        )
        self.assertEqual(result["route"], "openai-specific")
        self.assertEqual(result["external"]["stage"], "start")

    # @spec:AC-010
    def test_is_error_delegate_start_does_not_wait_and_falls_back(self):
        client = FakeBridge(
            responses={
                "delegate_start": {
                    "isError": True,
                    "structuredContent": {"job_id": "job-1", "session_id": "session-1"},
                }
            }
        )
        result = route_with_external_fallback(
            {"external": external()}, client, workspace="repo", prompt="inspect", openai_specific=lambda: "specific", openai_general=lambda: "general"
        )
        operations = [call[0] for call in client.calls]
        self.assertEqual(result["route"], "openai-specific")
        self.assertEqual(result["result"], "specific")
        self.assertEqual(result["external"]["stage"], "start")
        self.assertEqual(operations, ["external_models", "delegate_start"])
        self.assertNotIn("delegate_wait", operations)

    # @spec:AC-011
    def test_wait_failure_timeout_and_cancellation_use_fallback(self):
        cases = [
            (FakeBridge(errors={"delegate_wait": "wait failed"}), "wait"),
            (FakeBridge(waits=[{"status": "running"}]), "result"),
            (FakeBridge(waits=[{"status": "cancelled"}]), "result"),
        ]
        for client, stage in cases:
            with self.subTest(stage=stage):
                result = route_with_external_fallback(
                    {"external": external()}, client, workspace="repo", prompt="inspect", openai_specific=lambda: "specific", openai_general=lambda: "general"
                )
                self.assertEqual(result["route"], "openai-specific")
                self.assertEqual(result["external"]["stage"], stage)

    # @spec:AC-011
    def test_is_error_delegate_wait_falls_back(self):
        client = FakeBridge(
            waits=[
                {
                    "isError": True,
                    "structuredContent": {"status": "completed", "text": "ignored", "changed_paths": []},
                }
            ]
        )
        result = route_with_external_fallback(
            {"external": external()}, client, workspace="repo", prompt="inspect", openai_specific=lambda: "specific", openai_general=lambda: "general"
        )
        operations = [call[0] for call in client.calls]
        self.assertEqual(result["route"], "openai-specific")
        self.assertEqual(result["result"], "specific")
        self.assertEqual(result["external"]["stage"], "wait")
        self.assertEqual(operations, ["external_models", "delegate_start", "delegate_wait"])

    # @spec:AC-012
    def test_specific_failure_preserves_general_fallback(self):
        result = route_with_external_fallback(
            {"external": external()}, FakeBridge(catalog=[]), workspace="repo", prompt="inspect",
            openai_specific=lambda: (_ for _ in ()).throw(RuntimeError("specific failed")), openai_general=lambda: "general",
        )
        self.assertEqual(result["route"], "openai-general")
        self.assertEqual(result["result"], "general")
        self.assertEqual(result["fallback"], "general")

    # @spec:AC-013
    def test_external_is_not_retried_after_fallback(self):
        client = FakeBridge(catalog=[])
        route_with_external_fallback(
            {"external": external()}, client, workspace="repo", prompt="inspect",
            openai_specific=lambda: (_ for _ in ()).throw(RuntimeError("specific failed")), openai_general=lambda: "general",
        )
        self.assertEqual([call[0] for call in client.calls], ["external_models"])

    # @spec:AC-014
    def test_success_returns_text_and_metadata(self):
        client = FakeBridge(waits=[{"status": "completed", "text": "answer", "changed_paths": [], "cursor": 2}])
        result = delegate_read_only(client, external(), workspace="repo", prompt="inspect")
        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "answer")
        self.assertEqual(result["metadata"]["job_id"], "job-1")
        self.assertEqual(result["metadata"]["session_id"], "session-1")

    # @spec:AC-014
    def test_success_requires_non_empty_text(self):
        invalid_text_payloads = {
            "empty": {"text": ""},
            "missing": {},
        }
        for case, payload in invalid_text_payloads.items():
            with self.subTest(case=case):
                client = FakeBridge(waits=[{"status": "completed", "changed_paths": [], **payload}])
                result = delegate_read_only(client, external(), workspace="repo", prompt="inspect")
                self.assertFalse(result["ok"])
                self.assertIn("non-empty final text", result["error"])

    # @spec:AC-015
    def test_success_requires_empty_changed_paths(self):
        client = FakeBridge(waits=[{"status": "completed", "text": "answer", "changed_paths": ["README.md"]}])
        result = delegate_read_only(client, external(), workspace="repo", prompt="inspect")
        self.assertFalse(result["ok"])
        self.assertEqual(result["changed_paths"], ["README.md"])
        self.assertIn("changed_paths", result["error"])

    # @spec:AC-015
    def test_success_requires_changed_paths_to_be_present_as_an_empty_list(self):
        invalid_changed_paths = {
            "missing": {},
            "null": {"changed_paths": None},
            "string": {"changed_paths": "README.md"},
            "object": {"changed_paths": {"path": "README.md"}},
        }
        for case, payload in invalid_changed_paths.items():
            with self.subTest(case=case):
                wait = {"status": "completed", "text": "answer", **payload}
                result = delegate_read_only(FakeBridge(waits=[wait]), external(), workspace="repo", prompt="inspect")
                self.assertFalse(result["ok"])
                self.assertEqual(result["changed_paths"], [])
                self.assertIn("changed_paths", result["error"])

    # @spec:AC-016
    def test_evidence_contains_model_job_session_status_error_fallback_and_result(self):
        client = FakeBridge(waits=[{"status": "failed", "text": "boom", "changed_paths": []}])
        result = route_with_external_fallback(
            {"external": external()}, client, workspace="repo", prompt="inspect", openai_specific=lambda: "specific", openai_general=lambda: "general"
        )
        evidence = result["external"]["metadata"]
        for key in ("provider", "model", "job_id", "session_id", "status", "error", "changed_paths", "result", "cost"):
            self.assertIn(key, evidence)
        self.assertEqual(result["fallback"], "specific")

    # @spec:AC-017
    def test_external_cost_without_telemetry_is_not_available(self):
        result = delegate_read_only(FakeBridge(), external(), workspace="repo", prompt="inspect")
        self.assertEqual(result["cost"], "not-available")
        self.assertNotEqual(result["cost"], 0)

    # @spec:AC-018
    def test_unconfigured_route_works_when_mcp_is_unavailable(self):
        client = FakeBridge(errors={"external_models": "MCP unavailable"})
        result = delegate_external({"model": "gpt-specific"}, client, workspace="repo", prompt="inspect")
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "not-configured")
        self.assertEqual(client.calls, [])

    # @spec:AC-019
    def test_all_feature_acceptance_criteria_have_annotated_tests(self):
        source = inspect.getsource(ExternalModelRoutingTests)
        for number in range(1, 20):
            self.assertIn(f"@spec:AC-{number:03d}", source)


if __name__ == "__main__":
    unittest.main()
