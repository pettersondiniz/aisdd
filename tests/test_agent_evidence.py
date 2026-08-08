from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "agent_evidence.py"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import agent_evidence  # noqa: E402


def write_rollout(
    root: Path,
    name: str,
    spawn: dict,
    contexts: list[dict],
    usages: list[dict] | None = None,
    last_usages: list[dict] | None = None,
    directory: tuple[str, ...] = ("2026", "08", "02"),
) -> None:
    rollout = root.joinpath(*directory, name)
    rollout.parent.mkdir(parents=True, exist_ok=True)
    usage_events = []
    for index in range(max(len(usages or []), len(last_usages or []))):
        info = {}
        if usages and index < len(usages):
            info["total_token_usage"] = usages[index]
        if last_usages and index < len(last_usages):
            info["last_token_usage"] = last_usages[index]
        usage_events.append({
            "timestamp": f"2026-08-02T21:01:0{index}Z",
            "type": "event_msg",
            "payload": {"info": info},
        })
    events = [
        {"type": "session_meta", "payload": {"session_id": name, "source": {"subagent": {"thread_spawn": spawn}}}},
        *[
            {"timestamp": f"2026-08-02T21:00:0{index}Z", "type": "turn_context", "payload": payload}
            for index, payload in enumerate(contexts)
        ],
        *usage_events,
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

    # @spec:AC-523
    # @spec:AC-524
    def test_agent_id_falls_back_to_an_exact_rollout_uuid_and_emits_an_alert(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            agent_id = "019fc476-042b-7b23-8c1f-8c38e2bed985"
            pricing = sessions / "pricing.toml"
            pricing.write_text("""
[models.test]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            token_usage = {
                "input_tokens": 100,
                "cached_input_tokens": 10,
                "cache_write_input_tokens": 5,
                "output_tokens": 50,
                "reasoning_output_tokens": 10,
                "total_tokens": 150,
            }
            write_rollout(
                sessions,
                f"rollout-2026-08-02T18-51-36-{agent_id}.jsonl",
                {"agent_path": None, "parent_thread_id": "parent", "agent_role": "reviewer"},
                [{"model": "test", "effort": "high"}],
                [token_usage],
                last_usages=[token_usage],
            )

            json_run = subprocess.run(
                [sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--agent-id", agent_id, "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(json_run.stdout)
            self.assertEqual(payload["status"], "resolved")
            self.assertTrue(payload["resolution"]["fallback_used"])
            self.assertEqual(payload["resolution"]["requested_agent_id"], agent_id)
            self.assertEqual(payload["resolution"]["matched_rollout_id"], agent_id)
            self.assertEqual(payload["effective"]["model"], "test")
            self.assertEqual(payload["cost_estimate"]["status"], "estimated")

            text_run = subprocess.run(
                [sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--agent-id", agent_id],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("AGENT_ID_FALLBACK", text_run.stdout)

    # @spec:AC-524
    def test_partial_agent_uuid_is_not_found_while_direct_agent_path_still_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            agent_id = "019fc476-042b-7b23-8c1f-8c38e2bed985"
            write_rollout(
                sessions,
                f"rollout-2026-08-02T18-51-36-{agent_id}.jsonl",
                {"agent_path": None, "parent_thread_id": "parent", "agent_role": "reviewer"},
                [{"model": "gpt-5.6-terra", "effort": "high"}],
            )
            write_rollout(
                sessions,
                "rollout-direct-agent-path.jsonl",
                {"agent_path": "/root/reviewer", "parent_thread_id": "parent", "agent_role": "reviewer"},
                [{"model": "gpt-5.6-luna", "effort": "medium"}],
            )

            partial_run = subprocess.run(
                [sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", agent_id[:8], "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(partial_run.stdout)["status"], "not-found")

            direct_run = subprocess.run(
                [sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/reviewer", "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            direct_payload = json.loads(direct_run.stdout)
            self.assertEqual(direct_payload["status"], "resolved")
            self.assertNotIn("resolution", direct_payload)
            self.assertEqual(direct_payload["effective"]["model"], "gpt-5.6-luna")

    # @spec:AC-525
    def test_agent_id_uuid_fallback_refuses_ambiguous_filenames_across_date_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            agent_id = "019fc476-042b-7b23-8c1f-8c38e2bed985"
            filename = f"rollout-2026-08-02T18-51-36-{agent_id}.jsonl"
            for directory in (("2026", "08", "02"), ("2026", "08", "03")):
                write_rollout(
                    sessions,
                    filename,
                    {"agent_path": None, "parent_thread_id": "parent", "agent_role": "reviewer"},
                    [{"model": "test", "effort": "high"}],
                    directory=directory,
                )

            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", agent_id, "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "ambiguous")
            self.assertIn("more than one rollout filename", payload["reason"])
            self.assertNotIn("cost_estimate", payload)

    # @spec:AC-525
    def test_agent_id_uuid_fallback_refuses_conflicting_non_null_agent_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            agent_id = "019fc476-042b-7b23-8c1f-8c38e2bed985"
            write_rollout(
                sessions,
                f"rollout-2026-08-02T18-51-36-{agent_id}.jsonl",
                {"agent_path": "/root/another-agent", "parent_thread_id": "parent", "agent_role": "reviewer"},
                [{"model": "test", "effort": "high"}],
            )

            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", agent_id, "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "not-available")
            self.assertIn("metadata conflicts", payload["reason"])
            self.assertNotIn("cost_estimate", payload)

    # @spec:AC-525
    def test_agent_id_uuid_fallback_refuses_conflicting_session_meta_events(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            agent_id = "019fc476-042b-7b23-8c1f-8c38e2bed985"
            filename = f"rollout-2026-08-02T18-51-36-{agent_id}.jsonl"
            write_rollout(
                sessions,
                filename,
                {"agent_path": None, "parent_thread_id": "parent", "agent_role": "reviewer"},
                [{"model": "test", "effort": "high"}],
            )
            rollout = sessions / "2026" / "08" / "02" / filename
            with rollout.open("a", encoding="utf-8") as source:
                source.write(json.dumps({
                    "type": "session_meta",
                    "payload": {
                        "session_id": filename,
                        "source": {"subagent": {"thread_spawn": {
                            "agent_path": "/root/another-agent",
                            "parent_thread_id": "parent",
                            "agent_role": "reviewer",
                        }}},
                    },
                }) + "\n")

            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", agent_id, "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "not-available")
            self.assertIn("no readable subagent metadata", payload["reason"])
            self.assertNotIn("cost_estimate", payload)

    # @spec:AC-525
    def test_is_within_sessions_root_fails_closed_when_resolution_raises_runtime_error(self) -> None:
        with patch.object(Path, "resolve", side_effect=RuntimeError("resolution failed")):
            self.assertFalse(
                agent_evidence.is_within_sessions_root(Path("candidate.jsonl"), Path("sessions"))
            )

    # @spec:AC-525
    def test_agent_id_uuid_fallback_refuses_a_symlinked_rollout_outside_sessions_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sessions = root / "sessions"
            outside = root / "outside"
            agent_id = "019fc476-042b-7b23-8c1f-8c38e2bed985"
            filename = f"rollout-2026-08-02T18-51-36-{agent_id}.jsonl"
            write_rollout(
                outside,
                filename,
                {"agent_path": None, "parent_thread_id": "parent", "agent_role": "reviewer"},
                [{"model": "test", "effort": "high"}],
            )
            target = outside / "2026" / "08" / "02" / filename
            candidate = sessions / "2026" / "08" / "02" / filename
            candidate.parent.mkdir(parents=True)
            try:
                candidate.symlink_to(target)
            except OSError as error:
                self.skipTest(f"Windows policy denied creation of the required file symlink: {error}")

            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", agent_id, "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "not-available")
            self.assertIn("outside sessions root", payload["reason"])
            self.assertNotIn("cost_estimate", payload)

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
    def test_finds_later_subagent_metadata_after_an_initial_non_subagent_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            rollout = sessions / "2026" / "08" / "02" / "rollout-multiple-metadata.jsonl"
            rollout.parent.mkdir(parents=True)
            rollout.write_text("\n".join((
                json.dumps({"type": "session_meta", "payload": {"source": {"thread_source": "user"}}}),
                "not-json-response-content",
                json.dumps({"type": "session_meta", "payload": {"source": {"subagent": {"thread_spawn": {"agent_path": "/root/reviewer", "parent_thread_id": "parent", "agent_role": "reviewer"}}}}}),
                json.dumps({"type": "turn_context", "payload": {"model": "gpt-5.6-terra", "effort": "high"}}),
            )) + "\n", encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/reviewer", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "resolved")
            self.assertEqual(payload["effective"]["model"], "gpt-5.6-terra")

    # @spec:AC-403
    def test_sanitizes_non_scalar_spawn_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(
                sessions,
                "rollout-sanitized-metadata.jsonl",
                {"agent_path": "/root/reviewer", "agent_role": {"unexpected": True}, "agent_nickname": ["private"], "parent_thread_id": {"id": "parent"}},
                [{"model": "gpt-5.6-terra", "effort": "high"}],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/reviewer", "--json"], check=True, capture_output=True, text=True)
            candidate = json.loads(run.stdout)["candidate"]
            self.assertIsNone(candidate["role"])
            self.assertIsNone(candidate["nickname"])
            self.assertIsNone(candidate["parent_session_id"])

    # @spec:AC-403
    def test_reports_missing_local_sessions_honestly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary) / "missing"
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/reviewer", "--json"], check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(run.stdout)["status"], "not-available")

    # @spec:AC-502
    def test_reports_missing_usage_and_cost_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            write_rollout(
                sessions,
                "rollout-without-usage.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "gpt-5.6-luna", "effort": "medium"}],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["cost_estimate"]["status"], "not-available")
            self.assertEqual(payload["cost_estimate"]["reason"], "matching rollout has no readable token usage metadata")

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
                last_usages=[{
                    "input_tokens": 1000,
                    "cached_input_tokens": 200,
                    "cache_write_input_tokens": 100,
                    "output_tokens": 500,
                    "reasoning_output_tokens": 300,
                    "total_tokens": 1500,
                }],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(ROOT / "assets" / "templates" / "cost-pricing.toml"), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["token_usage"]["status"], "observed")
            self.assertEqual(payload["token_usage"]["scope"], "last-readable-rollout-total")
            self.assertEqual(payload["token_usage"]["reasoning_output_tokens"], 300)
            self.assertEqual(payload["request_token_usage"]["status"], "observed")
            self.assertEqual(payload["request_token_usage"]["request_count"], 1)
            self.assertEqual(payload["cost_estimate"]["status"], "estimated")
            self.assertEqual(payload["cost_estimate"]["pricing_model"], "gpt-5.6-luna")
            self.assertEqual(payload["cost_estimate"]["scope"], "last-token-usage-per-request")
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
long_context_pricing = "tiered"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
long_context_threshold_tokens = 1000
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
            self.assertEqual(payload["cost_estimate"]["reason"], "request-level-token-usage-unavailable-for-tiered-long-context-pricing")

    # @spec:AC-505
    def test_ignores_long_context_by_default_with_a_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            pricing = sessions / "pricing.toml"
            pricing.write_text("""
[models.test]
long_context_pricing = "tiered"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
long_context_threshold_tokens = 1000
long_context_input_multiplier = 2.0
long_context_output_multiplier = 1.5
""", encoding="utf-8")
            write_rollout(
                sessions,
                "rollout-long-context-override.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "test", "effort": "medium"}],
                [{"input_tokens": 200, "cached_input_tokens": 50, "cache_write_input_tokens": 0, "output_tokens": 100, "reasoning_output_tokens": 20, "total_tokens": 300}],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--ignore-long-context", "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["cost_estimate"]["status"], "estimated")
            self.assertIn("long-context pricing was explicitly ignored", payload["cost_estimate"]["warnings"][0])
            text_run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--ignore-long-context", "--agent-id", "/root/tester"], check=True, capture_output=True, text=True)
            self.assertIn("Warning: long-context pricing was explicitly ignored", text_run.stdout)

    # @spec:AC-505
    def test_ignores_long_context_with_request_usage_and_warns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            pricing = sessions / "pricing.toml"
            pricing.write_text("""
[models.test]
long_context_pricing = "tiered"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
long_context_threshold_tokens = 1000
long_context_input_multiplier = 2.0
long_context_output_multiplier = 1.5
""", encoding="utf-8")
            usage = {"input_tokens": 200, "cached_input_tokens": 50, "cache_write_input_tokens": 0, "output_tokens": 100, "reasoning_output_tokens": 20, "total_tokens": 300}
            write_rollout(
                sessions,
                "rollout-request-long-context-override.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "test", "effort": "medium"}],
                [usage],
                last_usages=[usage],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--ignore-long-context", "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            estimate = json.loads(run.stdout)["cost_estimate"]
            self.assertEqual(estimate["status"], "estimated")
            self.assertEqual(estimate["long_context_pricing"], "standard")
            self.assertEqual(estimate["standard_request_count"], 1)
            self.assertEqual(estimate["long_context_request_count"], 0)
            self.assertIn("long-context pricing was explicitly ignored", estimate["warnings"][0])

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
    def test_refuses_cost_when_a_later_context_has_no_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            usage = {"input_tokens": 10, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 5, "reasoning_output_tokens": 0, "total_tokens": 15}
            write_rollout(
                sessions,
                "rollout-unknown-later-model.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "gpt-5.6-luna", "effort": "medium"}, {"effort": "medium"}],
                [usage],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(ROOT / "assets" / "templates" / "cost-pricing.toml"), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            estimate = json.loads(run.stdout)["cost_estimate"]
            self.assertEqual(estimate["status"], "not-available")
            self.assertEqual(estimate["reason"], "multiple-or-unknown-models-in-cumulative-rollout")

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

    # @spec:AC-506
    # @spec:AC-510
    def test_prices_long_context_per_request_and_reports_segments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            pricing = sessions / "pricing.toml"
            pricing.write_text("""
[models.test]
long_context_pricing = "tiered"
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
                "rollout-per-request-long-context.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "test", "effort": "medium"}],
                [
                    {"input_tokens": 80, "cached_input_tokens": 20, "cache_write_input_tokens": 0, "output_tokens": 10, "reasoning_output_tokens": 4, "total_tokens": 90},
                    {"input_tokens": 200, "cached_input_tokens": 50, "cache_write_input_tokens": 5, "output_tokens": 30, "reasoning_output_tokens": 14, "total_tokens": 230},
                    {"input_tokens": 200, "cached_input_tokens": 50, "cache_write_input_tokens": 5, "output_tokens": 30, "reasoning_output_tokens": 14, "total_tokens": 230},
                ],
                last_usages=[
                    {"input_tokens": 80, "cached_input_tokens": 20, "cache_write_input_tokens": 0, "output_tokens": 10, "reasoning_output_tokens": 4, "total_tokens": 90},
                    {"input_tokens": 120, "cached_input_tokens": 30, "cache_write_input_tokens": 5, "output_tokens": 20, "reasoning_output_tokens": 10, "total_tokens": 140},
                    {"input_tokens": 120, "cached_input_tokens": 30, "cache_write_input_tokens": 5, "output_tokens": 20, "reasoning_output_tokens": 10, "total_tokens": 140},
                ],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            estimate = payload["cost_estimate"]
            self.assertEqual(estimate["status"], "estimated")
            self.assertEqual(estimate["scope"], "last-token-usage-per-request")
            self.assertEqual(estimate["request_count"], 2)
            self.assertEqual(estimate["standard_request_count"], 1)
            self.assertEqual(estimate["long_context_request_count"], 1)
            self.assertEqual(estimate["total_usd"], 0.0003405)
            self.assertEqual(estimate["request_segments"]["long_context"]["requests"], 1)
            self.assertEqual(payload["request_token_usage"]["duplicate_snapshots_ignored"], 1)
            self.assertEqual(payload["request_token_usage"]["readable_snapshot_count"], 3)
            self.assertEqual(len(payload["request_token_usage"]["snapshots"]), 3)

    # @spec:AC-507
    def test_explicit_standard_policy_has_no_long_context_modifier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            pricing = sessions / "pricing.toml"
            pricing.write_text("""
[models.test]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            usage = {"input_tokens": 200, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 100, "reasoning_output_tokens": 20, "total_tokens": 300}
            write_rollout(
                sessions,
                "rollout-standard-long-context.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "test", "effort": "medium"}],
                [usage],
                last_usages=[usage],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            estimate = json.loads(run.stdout)["cost_estimate"]
            self.assertEqual(estimate["status"], "estimated")
            self.assertEqual(estimate["long_context_pricing"], "standard")
            self.assertEqual(estimate["long_context_request_count"], 0)
            self.assertEqual(estimate["total_usd"], 0.0004)

    # @spec:AC-508
    def test_refuses_a_model_without_an_explicit_long_context_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            pricing = sessions / "pricing.toml"
            pricing.write_text("""
[models.test]
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            usage = {"input_tokens": 10, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 5, "reasoning_output_tokens": 0, "total_tokens": 15}
            write_rollout(
                sessions,
                "rollout-missing-long-context-policy.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "test", "effort": "medium"}],
                [usage],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            estimate = json.loads(run.stdout)["cost_estimate"]
            self.assertEqual(estimate["status"], "not-available")
            self.assertEqual(estimate["reason"], "configured model has no explicit long-context pricing policy")

    # @spec:AC-509
    def test_refuses_per_request_cost_when_snapshots_do_not_reconcile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            pricing = sessions / "pricing.toml"
            pricing.write_text("""
[models.test]
long_context_pricing = "tiered"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
long_context_threshold_tokens = 100
long_context_input_multiplier = 2.0
long_context_output_multiplier = 1.5
""", encoding="utf-8")
            total = {"input_tokens": 200, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 20, "reasoning_output_tokens": 0, "total_tokens": 220}
            last = {"input_tokens": 80, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 10, "reasoning_output_tokens": 0, "total_tokens": 90}
            write_rollout(
                sessions,
                "rollout-inconsistent-per-request-usage.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "test", "effort": "medium"}],
                [total],
                last_usages=[last],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(pricing), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            estimate = json.loads(run.stdout)["cost_estimate"]
            self.assertEqual(estimate["status"], "not-available")
            self.assertEqual(estimate["reason"], "per-request-token-usage-does-not-reconcile-with-cumulative-rollout-total")

    # @spec:AC-511
    def test_refuses_malformed_last_token_usage_without_cumulative_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            usage = {"input_tokens": 10, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 5, "reasoning_output_tokens": 0, "total_tokens": 15}
            write_rollout(
                sessions,
                "rollout-malformed-last-usage.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "gpt-5.6-luna", "effort": "medium"}],
                [usage],
                last_usages=[{}],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(ROOT / "assets" / "templates" / "cost-pricing.toml"), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["request_token_usage"]["status"], "partial")
            self.assertEqual(payload["cost_estimate"]["status"], "not-available")
            self.assertEqual(payload["cost_estimate"]["reason"], "token usage lacks the classifications required for an honest estimate")

    # @spec:AC-512
    def test_preserves_request_usage_when_cumulative_usage_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sessions = Path(temporary)
            usage = {"input_tokens": 10, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 5, "reasoning_output_tokens": 0, "total_tokens": 15}
            write_rollout(
                sessions,
                "rollout-request-usage-without-total.jsonl",
                {"agent_path": "/root/tester", "parent_thread_id": "parent", "agent_role": "tester"},
                [{"model": "gpt-5.6-luna", "effort": "medium"}],
                last_usages=[usage, usage],
            )
            run = subprocess.run([sys.executable, str(SCRIPT), "--sessions-root", str(sessions), "--pricing-config", str(ROOT / "assets" / "templates" / "cost-pricing.toml"), "--agent-id", "/root/tester", "--json"], check=True, capture_output=True, text=True)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["token_usage"]["status"], "not-available")
            self.assertEqual(payload["request_token_usage"]["status"], "observed")
            self.assertEqual(payload["request_token_usage"]["request_count"], 2)
            self.assertEqual(len(payload["request_token_usage"]["snapshots"]), 2)
            self.assertEqual(payload["cost_estimate"]["status"], "not-available")
            self.assertEqual(payload["cost_estimate"]["reason"], "cumulative-token-usage-metadata-unavailable-for-reconciliation")


if __name__ == "__main__":
    unittest.main()
