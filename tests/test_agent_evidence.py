from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "agent_evidence.py"


def write_rollout(root: Path, name: str, spawn: dict, contexts: list[dict], usages: list[dict] | None = None) -> None:
    rollout = root / "2026" / "08" / "02" / name
    rollout.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {"type": "session_meta", "payload": {"session_id": name, "source": {"subagent": {"thread_spawn": spawn}}}},
        *[
            {"timestamp": f"2026-08-02T21:00:0{index}Z", "type": "turn_context", "payload": payload}
            for index, payload in enumerate(contexts)
        ],
        *[
            {
                "timestamp": f"2026-08-02T21:01:0{index}Z",
                "type": "event_msg",
                "payload": {"info": {"total_token_usage": payload}},
            }
            for index, payload in enumerate(usages or [])
        ],
    ]
    rollout.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")


class AgentEvidenceTests(unittest.TestCase):
    # @spec:AC-401
    def test_resolves_effective_settings_from_a_unique_agent_rollout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(sessions, "rollout-child.jsonl", {"agent_path": "/root/reviewer", "parent_thread_id": "parent", "agent_role": None}, [{"model": "gpt-5.6-sol", "effort": "high"}])
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/reviewer", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "resolved")
            self.assertEqual(payload["effective"]["model"], "gpt-5.6-sol")
            self.assertEqual(payload["effective"]["reasoning_effort"], "high")
            self.assertNotIn(str(sessions), run.stdout)

    # @spec:AC-402
    def test_reads_settings_shape_when_top_level_effort_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(sessions, "rollout-child.jsonl", {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": None}, [{"collaboration_mode": {"settings": {"model": "gpt-5.6-luna", "reasoning_effort": "medium"}}}])
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["effective"]["model"], "gpt-5.6-luna")
            self.assertEqual(payload["effective"]["reasoning_effort"], "medium")

    # @spec:AC-403
    def test_refuses_to_guess_when_a_legacy_role_matches_multiple_rollouts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            for suffix in ("one", "two"):
                write_rollout(sessions, f"rollout-{suffix}.jsonl", {"agent_path": None, "parent_thread_id": "parent", "agent_role": "reviewer"}, [{"model": "gpt-5.6-terra", "effort": "high"}])
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--role", "reviewer", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "ambiguous")
            self.assertEqual(len(payload["candidates"]), 2)

    # @spec:AC-401
    def test_legacy_role_and_parent_selector_resolve_the_right_child(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(sessions, "rollout-one.jsonl", {"agent_path": None, "parent_thread_id": "parent-one", "agent_role": "reviewer"}, [{"model": "gpt-5.6-terra", "effort": "high"}])
            write_rollout(sessions, "rollout-two.jsonl", {"agent_path": None, "parent_thread_id": "parent-two", "agent_role": "reviewer"}, [{"model": "gpt-5.6-luna", "effort": "low"}])
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--role", "reviewer", "--parent-session-id", "parent-two", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "resolved")
            self.assertEqual(payload["effective"]["model"], "gpt-5.6-luna")

    # @spec:AC-404
    def test_rollout_id_selects_a_legacy_child_without_agent_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(sessions, "rollout-2026-08-02T18-51-36-019fc476-042b-7b23-8c1f-8c38e2bed985.jsonl", {"agent_path": None, "parent_thread_id": "parent", "agent_role": "reviewer"}, [{"model": "gpt-5.5", "effort": "high"}])
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--rollout-id", "019fc476-042b-7b23-8c1f-8c38e2bed985", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "resolved")
            self.assertEqual(payload["effective"]["model"], "gpt-5.5")

    # @spec:AC-404
    def test_rollout_id_requires_an_exact_terminal_uuid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(sessions, "rollout-2026-08-02T18-51-36-019fc476-042b-7b23-8c1f-8c38e2bed985.jsonl", {"agent_path": None, "parent_thread_id": "parent", "agent_role": "reviewer"}, [{"model": "gpt-5.5", "effort": "high"}])
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--rollout-id", "019fc476", "--json"], check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(run.stdout)["status"], "not-found")

    # @spec:AC-403
    def test_tolerates_malformed_optional_session_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            rollout = sessions / "2026" / "08" / "02" / "rollout-malformed.jsonl"
            rollout.parent.mkdir(parents=True)
            rollout.write_text("\n".join((
                json.dumps({"type": "session_meta", "payload": {"source": {"subagent": {"thread_spawn": {"agent_path": "/root/reviewer"}}}}}),
                json.dumps({"type": "turn_context", "payload": []}),
                json.dumps({"type": "turn_context", "payload": {"model": "gpt-5.6-terra", "collaboration_mode": "invalid"}}),
            )) + "\n", encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/reviewer", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "resolved")
            self.assertEqual(payload["effective"]["reasoning_effort"], "unknown")

    # @spec:AC-403
    def test_reports_missing_local_sessions_honestly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary) / "missing"
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/reviewer", "--json"], check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(run.stdout)["status"], "not-available")

    # @spec:AC-501
    def test_records_all_observed_token_categories_and_estimates_api_cost(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(
                sessions,
                "rollout-usage.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "gpt-5.6-luna", "effort": "medium"}],
                [{
                    "input_tokens": 1000,
                    "cached_input_tokens": 200,
                    "cache_write_input_tokens": 100,
                    "output_tokens": 500,
                    "reasoning_output_tokens": 300,
                    "total_tokens": 1500,
                }],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["token_usage"]["status"], "observed")
            self.assertEqual(payload["token_usage"]["scope"], "last-readable-rollout-total")
            self.assertEqual(payload["token_usage"]["reasoning_output_tokens"], 300)
            self.assertEqual(payload["cost_estimate"]["status"], "estimated")
            self.assertEqual(payload["cost_estimate"]["pricing_model"], "gpt-5.6-luna")
            self.assertEqual(payload["cost_estimate"]["total_usd"], 0.000789)
            self.assertEqual(payload["cost_estimate"]["components"]["output"]["tokens"], 500)

    # @spec:AC-502
    def test_refuses_a_cost_estimate_when_token_classifications_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(
                sessions,
                "rollout-incomplete-usage.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "gpt-5.6-luna", "effort": "medium"}],
                [{"input_tokens": 1000, "output_tokens": 500}],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["cost_estimate"]["status"], "not-available")
            self.assertIn("cached_input_tokens", payload["cost_estimate"]["missing_fields"])
            self.assertEqual(payload["token_usage"]["status"], "partial")
            self.assertIsNone(payload["token_usage"]["cache_write_input_tokens"])

    # @spec:AC-503
    def test_refuses_to_price_an_observed_model_missing_from_the_table(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(
                sessions,
                "rollout-unpriced.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "unpriced-model", "effort": "medium"}],
                [{
                    "input_tokens": 1000,
                    "cached_input_tokens": 0,
                    "cache_write_input_tokens": 0,
                    "output_tokens": 500,
                    "reasoning_output_tokens": 0,
                    "total_tokens": 1500,
                }],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["cost_estimate"]["status"], "not-available")
            self.assertEqual(payload["cost_estimate"]["observed_model"], "unpriced-model")

    # @spec:AC-504
    def test_refuses_to_price_long_context_from_cumulative_usage_alone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            pricing = sessions / "pricing.toml"
            pricing.write_text("""
currency = "USD"
pricing_basis = "api-equivalent-standard"
updated_at = "2026-08-02"
[models.test]
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
long_context_threshold_tokens = 100
long_context_input_multiplier = 2.0
long_context_output_multiplier = 1.5
""", encoding="utf-8")
            write_rollout(
                sessions,
                "rollout-long-context.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "test", "effort": "medium"}],
                [{
                    "input_tokens": 200,
                    "cached_input_tokens": 50,
                    "cache_write_input_tokens": 10,
                    "output_tokens": 100,
                    "reasoning_output_tokens": 20,
                    "total_tokens": 300,
                }],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--respect-long-context", "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["cost_estimate"]["status"], "not-available")
            self.assertEqual(payload["cost_estimate"]["reason"], "cumulative-token-usage-cannot-price-long-context-per-request")

    # @spec:AC-505
    def test_ignores_long_context_by_default_with_a_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            pricing = sessions / "pricing.toml"
            pricing.write_text("""
[models.test]
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
long_context_threshold_tokens = 100
""", encoding="utf-8")
            write_rollout(
                sessions,
                "rollout-long-context-override.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "test", "effort": "medium"}],
                [{"input_tokens": 200, "cached_input_tokens": 50, "cache_write_input_tokens": 0, "output_tokens": 100, "reasoning_output_tokens": 20, "total_tokens": 300}],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["cost_estimate"]["status"], "estimated")
            self.assertIn("long-context pricing was explicitly ignored", payload["cost_estimate"]["warnings"][0])

    # @spec:AC-502
    def test_refuses_inconsistent_cumulative_totals(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(
                sessions,
                "rollout-inconsistent-usage.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "gpt-5.6-luna", "effort": "medium"}],
                [{
                    "input_tokens": 1000,
                    "cached_input_tokens": 0,
                    "cache_write_input_tokens": 0,
                    "output_tokens": 500,
                    "reasoning_output_tokens": 0,
                    "total_tokens": 1,
                }],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["cost_estimate"]["status"], "not-available")
            self.assertEqual(payload["cost_estimate"]["reason"], "token usage classifications are internally inconsistent")

    # @spec:AC-503
    def test_refuses_to_price_cumulative_usage_with_multiple_observed_models(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(
                sessions,
                "rollout-multiple-models.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "gpt-5.6-luna", "effort": "medium"}, {"model": "gpt-5.6-terra", "effort": "medium"}],
                [{
                    "input_tokens": 1000,
                    "cached_input_tokens": 0,
                    "cache_write_input_tokens": 0,
                    "output_tokens": 500,
                    "reasoning_output_tokens": 0,
                    "total_tokens": 1500,
                }],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["cost_estimate"]["status"], "not-available")
            self.assertEqual(payload["cost_estimate"]["reason"], "multiple-or-unknown-models-in-cumulative-rollout")

    # @spec:AC-503
    def test_refuses_invalid_numeric_rates_in_the_pricing_table(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            pricing = sessions / "pricing.toml"
            pricing.write_text("""
[models.bad]
input_per_million = nan
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            write_rollout(
                sessions,
                "rollout-bad-pricing.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "bad", "effort": "medium"}],
                [{
                    "input_tokens": 1000,
                    "cached_input_tokens": 0,
                    "cache_write_input_tokens": 0,
                    "output_tokens": 500,
                    "reasoning_output_tokens": 0,
                    "total_tokens": 1500,
                }],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["cost_estimate"]["status"], "not-available")
            self.assertEqual(payload["cost_estimate"]["reason"], "configured model has incomplete API-equivalent prices")


if __name__ == "__main__":
    unittest.main()
