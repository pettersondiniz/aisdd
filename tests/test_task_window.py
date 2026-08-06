from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "task_window.py"


def sidecar(root: Path, *parts: str) -> Path:
    return root.parent / f"{root.name}-sidecars" / Path(*parts)


def usage(
    input_tokens: int,
    output_tokens: int,
    *,
    cached: int = 0,
    cache_write: int = 0,
    reasoning: int | None = None,
) -> dict[str, int]:
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "cache_write_input_tokens": cache_write,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": min(output_tokens, 5) if reasoning is None else reasoning,
        "total_tokens": input_tokens + output_tokens,
    }


def event(timestamp: str, kind: str, payload: dict) -> dict:
    return {"timestamp": timestamp, "type": kind, "payload": payload}


def write_main_session(
    root: Path,
    *,
    requests: list[tuple[str, dict[str, int], dict[str, int]]],
    mismatch: bool = False,
    complete: bool = False,
    filename: str = "rollout-main.jsonl",
    session_name: str = "main-session",
    compaction: bool = False,
    previous_task: bool = False,
    request_context: bool = True,
    non_token_usage_event: bool = False,
    non_token_total_before: bool = False,
    missing_last: bool = False,
    compaction_extra_event: bool = False,
    trailing_model_activity: bool = False,
    trailing_agent_reasoning: bool = False,
    agent_reasoning_before_followup_token: bool = False,
    malformed_context: bool = False,
    session_metadata: dict | None = None,
) -> Path:
    path = root / "2026" / "08" / "06" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    session_payload = {"session_id": session_name, "source": {"user": "main"}}
    if session_metadata is not None:
        session_payload = {"session_id": session_name, **session_metadata}
    events = [
        event("2026-08-06T00:00:00Z", "session_meta", session_payload),
        event("2026-08-06T00:00:01Z", "turn_context", {"model": "standard", "effort": "high", "turn_id": "before"}),
        event("2026-08-06T00:00:02Z", "event_msg", {"type": "token_count", "info": {"total_token_usage": usage(60, 40, cached=10), "last_token_usage": usage(60, 40, cached=10)}}),
    ]
    if non_token_total_before:
        events.append(event(
            "2026-08-06T00:00:03Z",
            "event_msg",
            {"type": "agent_message", "info": {"total_token_usage": usage(999, 1), "last_token_usage": usage(999, 1)}},
        ))
    if previous_task:
        events.extend([
            event("2026-08-06T00:00:10Z", "event_msg", {"type": "task_started", "turn_id": "previous-task", "started_at": "2026-08-06T00:00:10Z"}),
            event("2026-08-06T00:00:20Z", "event_msg", {"type": "task_complete", "turn_id": "previous-task", "completed_at": "2026-08-06T00:00:20Z"}),
            event("2026-08-06T00:00:21Z", "event_msg", {"type": "thread_settings_applied", "thread_settings": {}}),
            event("2026-08-06T00:00:22Z", "event_msg", {"type": "user_message", "message": "previous task"}),
            event("2026-08-06T00:00:23Z", "event_msg", {"type": "agent_reasoning", "text": "previous reasoning"}),
            event("2026-08-06T00:00:24Z", "event_msg", {"type": "patch_apply_end", "success": True}),
            event("2026-08-06T00:00:25Z", "event_msg", {"type": "token_count", "info": {
                "total_token_usage": usage(60, 40, cached=10),
                "last_token_usage": usage(60, 40, cached=10),
            }}),
        ])
    events.append(event("2026-08-06T00:01:00Z", "event_msg", {"type": "task_started", "turn_id": "task-start", "started_at": "2026-08-06T00:01:00Z"}))
    if compaction:
        events.extend([
            event("2026-08-06T00:01:00.500Z", "compacted", {"message": "", "replacement_history": []}),
            event("2026-08-06T00:01:00.550Z", "world_state", {"full": True, "state": {}}),
            event("2026-08-06T00:01:00.600Z", "turn_context", {"model": "standard", "effort": "high", "turn_id": "compaction-turn"}),
        ])
        if compaction_extra_event:
            events.append(event("2026-08-06T00:01:00.650Z", "event_msg", {"type": "agent_message", "message": "unexpected event"}))
        events.extend([
            event("2026-08-06T00:01:00.700Z", "event_msg", {"type": "token_count", "info": {
                "total_token_usage": usage(60, 40, cached=10),
                "last_token_usage": {
                    "input_tokens": 0,
                    "cached_input_tokens": 0,
                    "cache_write_input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_output_tokens": 0,
                    "total_tokens": 13368,
                },
            }}),
            event("2026-08-06T00:01:00.800Z", "event_msg", {"type": "context_compacted"}),
        ])
    running_total = 100
    for index, (model, request_usage, cumulative_usage) in enumerate(requests, 1):
        if request_context:
            context_payload = {"model": model, "effort": "high", "turn_id": f"turn-{index}"}
            if malformed_context and index == 1:
                context_payload["model"] = {"name": model}
            events.append(event(f"2026-08-06T00:01:0{index}Z", "turn_context", context_payload))
        running_total += request_usage["total_tokens"]
        cumulative = dict(cumulative_usage)
        if non_token_usage_event and index == 1:
            events.append(event(f"2026-08-06T00:01:0{index}.5Z", "event_msg", {"type": "agent_message", "info": {"total_token_usage": usage(999, 1), "last_token_usage": usage(999, 1)}}))
        if mismatch and index == len(requests):
            cumulative["input_tokens"] += 10
            cumulative["total_tokens"] += 10
        token_info = {"total_token_usage": cumulative}
        if not missing_last:
            token_info["last_token_usage"] = request_usage
        events.append(event(f"2026-08-06T00:01:1{index}Z", "event_msg", {"type": "token_count", "info": token_info}))
        if index == 1:
            duplicate_info = {"total_token_usage": cumulative}
            if not missing_last:
                duplicate_info["last_token_usage"] = request_usage
            events.append(event(f"2026-08-06T00:01:2{index}Z", "event_msg", {"type": "token_count", "info": duplicate_info}))
            if agent_reasoning_before_followup_token and index == 1:
                events.append(event(
                    "2026-08-06T00:01:25Z",
                    "event_msg",
                    {"type": "agent_reasoning", "text": "reasoning between token snapshots"},
                ))
    if trailing_model_activity:
        events.append(event(
            "2026-08-06T00:01:59Z",
            "response_item",
            {"type": "message", "role": "assistant", "content": []},
        ))
    if trailing_agent_reasoning:
        events.append(event(
            "2026-08-06T00:01:59Z",
            "event_msg",
            {"type": "agent_reasoning", "text": "reasoning after the final token snapshot"},
        ))
    if complete:
        events.append(event("2026-08-06T00:02:00Z", "event_msg", {"type": "task_complete", "turn_id": "task-start", "completed_at": "2026-08-06T00:02:00Z"}))
        events.append(event("2026-08-06T00:03:00Z", "event_msg", {"type": "task_started", "turn_id": "outside-start", "started_at": "2026-08-06T00:03:00Z"}))
        events.append(event("2026-08-06T00:03:01Z", "turn_context", {"model": "standard", "effort": "high", "turn_id": "outside"}))
        events.append(event("2026-08-06T00:03:02Z", "event_msg", {"type": "token_count", "info": {"total_token_usage": usage(400, 200), "last_token_usage": usage(200, 100)}}))
        events.append(event("2026-08-06T00:04:00Z", "event_msg", {"type": "task_complete", "turn_id": "outside-start", "completed_at": "2026-08-06T00:04:00Z"}))
    path.write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")
    return path


def append_task_complete(path: Path, turn_id: str = "task-start") -> None:
    with path.open("a", encoding="utf-8") as target:
        target.write(json.dumps(event("2026-08-06T00:02:00Z", "event_msg", {"type": "task_complete", "turn_id": turn_id, "completed_at": "2026-08-06T00:02:00Z"})) + "\n")


def run_json(*args: str) -> dict:
    run = subprocess.run([sys.executable, str(SCRIPT), *args, "--json"], capture_output=True, text=True)
    if run.returncode:
        raise AssertionError(f"task_window failed: {run.stderr}{run.stdout}")
    return json.loads(run.stdout)


def run_failure(*args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    run = subprocess.run([sys.executable, str(SCRIPT), *args, "--json"], capture_output=True, text=True)
    if run.returncode == 0:
        raise AssertionError(f"task_window unexpectedly succeeded: {run.stdout}")
    payload = json.loads(run.stdout) if run.stdout.strip() else {}
    return run, payload


class TaskWindowTests(unittest.TestCase):
    # @spec:AC-513
    def test_start_persists_an_open_main_session_window(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            original_session = session.read_bytes()
            output = sidecar(root, "specs", "task-window.json")
            payload = run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            self.assertEqual(payload["status"], "created")
            window = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(window["status"], "open")
            self.assertEqual(window["session"]["session_id"], "main-session")
            self.assertEqual(window["session"]["rollout_file"], session.name)
            self.assertNotIn("path", window["session"])
            self.assertEqual(window["start"]["turn_id"], "task-start")
            self.assertIsNone(window["end"])
            self.assertEqual(session.read_bytes(), original_session)

    # @spec:AC-518
    def test_start_rejects_output_that_would_overwrite_the_runtime_rollout_even_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            original_session = session.read_bytes()
            _, payload = run_failure(
                "start",
                "--task-id",
                "demo-task",
                "--sessions-root",
                str(root),
                "--output",
                str(session),
                "--force",
            )
            self.assertIn("must not overwrite", payload["reason"])
            self.assertEqual(session.read_bytes(), original_session)

    # @spec:AC-521
    def test_start_rejects_output_rollout_of_another_session_and_preserves_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            selected = write_main_session(
                root,
                requests=[],
                filename="rollout-selected.jsonl",
                session_name="selected-session",
            )
            victim = write_main_session(
                root,
                requests=[],
                filename="rollout-victim.jsonl",
                session_name="victim-session",
            )
            original_victim = victim.read_bytes()
            _, payload = run_failure(
                "start",
                "--task-id",
                "demo-task",
                "--sessions-root",
                str(root),
                "--session-file",
                str(selected),
                "--output",
                str(victim),
                "--force",
            )
            self.assertIn("outside --sessions-root", payload["reason"])
            self.assertEqual(victim.read_bytes(), original_victim)

    # @spec:AC-521
    def test_start_rejects_output_hardlink_to_any_rollout_outside_sessions_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            selected = write_main_session(
                root,
                requests=[],
                filename="rollout-selected.jsonl",
                session_name="selected-session",
            )
            victim = write_main_session(
                root,
                requests=[],
                filename="rollout-victim.jsonl",
                session_name="victim-session",
            )
            original_victim = victim.read_bytes()
            output = sidecar(root, "hardlink-output.jsonl")
            output.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(victim, output)
            except OSError as error:
                self.skipTest(f"hardlinks are unavailable: {error}")
            _, payload = run_failure(
                "start",
                "--task-id",
                "demo-task",
                "--sessions-root",
                str(root),
                "--session-file",
                str(selected),
                "--output",
                str(output),
                "--force",
            )
            self.assertIn("must not overwrite", payload["reason"])
            self.assertEqual(victim.read_bytes(), original_victim)

    # @spec:AC-514
    def test_closed_window_reconciles_only_in_window_requests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = usage(100, 50, cached=20)
            session = write_main_session(root, requests=[("standard", request, usage(160, 90, cached=30, reasoning=10))])
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            close = run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            self.assertEqual(close["status"], "closed")
            pricing = root / "pricing.toml"
            pricing.write_text("""
[models.standard]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root), "--pricing-config", str(pricing))
            self.assertEqual(report["status"], "closed")
            self.assertEqual(report["window_token_usage"]["total_tokens"], 150)
            self.assertEqual(report["request_token_usage"]["request_count"], 1)
            self.assertEqual(report["request_token_usage"]["duplicate_snapshots_ignored"], 1)
            self.assertEqual(report["cost_estimate"]["status"], "estimated")

    # @spec:AC-514
    def test_ignores_last_usage_on_non_token_count_event_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = usage(100, 50)
            session = write_main_session(
                root,
                requests=[("standard", request, usage(160, 90, cached=10, reasoning=10))],
                non_token_usage_event=True,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            pricing = root / "pricing.toml"
            pricing.write_text("""
[models.standard]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root), "--pricing-config", str(pricing))
            self.assertEqual(report["request_token_usage"]["readable_snapshot_count"], 2)
            self.assertEqual(report["request_token_usage"]["request_count"], 1)
            self.assertEqual(report["cost_estimate"]["status"], "estimated")

    # @spec:AC-514
    def test_ignores_non_token_total_before_the_window_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(
                root,
                requests=[("standard", usage(100, 50), usage(160, 90, cached=10, reasoning=10))],
                non_token_total_before=True,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root))
            self.assertIsNone(report["baseline_total_token_usage"])
            self.assertEqual(report["boundaries"]["baseline_source"], "pre-window-activity-after-last-cumulative-snapshot")
            self.assertEqual(report["cost_estimate"]["status"], "not-available")

    # @spec:AC-514
    def test_token_count_without_last_usage_never_uses_cumulative_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(
                root,
                requests=[("standard", usage(100, 50), usage(160, 90, cached=10, reasoning=10))],
                missing_last=True,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root))
            self.assertIsNone(report["window_token_usage"])
            self.assertEqual(report["request_token_usage"]["status"], "not-available")
            self.assertEqual(report["cost_estimate"]["status"], "not-available")
            self.assertEqual(report["cost_estimate"]["reason"], "in-window cumulative telemetry is incomplete")

    # @spec:AC-514
    def test_keeps_baseline_after_a_completed_prior_task_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = usage(100, 50)
            session = write_main_session(
                root,
                requests=[("standard", request, usage(160, 90, cached=10, reasoning=10))],
                previous_task=True,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            pricing = root / "pricing.toml"
            pricing.write_text("""
[models.standard]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root), "--pricing-config", str(pricing))
            self.assertEqual(report["boundaries"]["baseline_source"], "last-readable-total-before-window")
            self.assertEqual(report["baseline_total_token_usage"]["total_tokens"], 100)
            self.assertEqual(report["cost_estimate"]["status"], "estimated")

    # @spec:AC-515
    def test_uses_the_last_readable_context_before_the_start_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = usage(100, 50)
            session = write_main_session(
                root,
                requests=[("standard", request, usage(160, 90, cached=10, reasoning=10))],
                request_context=False,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            pricing = root / "pricing.toml"
            pricing.write_text("""
[models.standard]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root), "--pricing-config", str(pricing))
            self.assertEqual(report["request_token_usage"]["request_count"], 1)
            self.assertEqual(report["cost_estimate"]["status"], "estimated")

    # @spec:AC-514
    def test_excludes_explicit_context_compaction_accounting_from_calls_and_price(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = usage(100, 50)
            session = write_main_session(
                root,
                requests=[("standard", request, usage(160, 90, cached=10, reasoning=10))],
                compaction=True,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            pricing = root / "pricing.toml"
            pricing.write_text("""
[models.standard]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root), "--pricing-config", str(pricing))
            self.assertEqual(report["request_token_usage"]["request_count"], 1)
            self.assertEqual(report["request_token_usage"]["compaction_snapshots_excluded"], 1)
            self.assertEqual(report["compaction"]["excluded_from_request_sum"], 1)
            self.assertEqual(report["compaction"]["snapshots"][0]["reason"], "context-compaction-accounting")
            self.assertEqual(report["cost_estimate"]["status"], "estimated")

    # @spec:AC-514
    def test_compaction_only_window_has_no_priceable_request_or_cumulative_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[], compaction=True)
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root))
            self.assertEqual(report["request_token_usage"]["request_count"], 0)
            self.assertEqual(report["request_token_usage"]["compaction_snapshots_excluded"], 1)
            self.assertEqual(report["cost_estimate"]["status"], "not-available")
            self.assertIn("only excluded compaction", report["cost_estimate"]["reason"])

    # @spec:AC-514
    def test_model_activity_after_last_token_count_makes_closed_cost_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(
                root,
                requests=[("standard", usage(100, 50), usage(160, 90, cached=10, reasoning=10))],
                trailing_model_activity=True,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root))
            self.assertIsNone(report["window_token_usage"])
            self.assertEqual(report["cost_estimate"]["status"], "not-available")
            self.assertEqual(
                report["cost_estimate"]["reason"],
                "in-window model activity after last token_count without a new token_count",
            )

    # @spec:AC-522
    def test_agent_reasoning_after_last_token_count_makes_closed_cost_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(
                root,
                requests=[("standard", usage(100, 50), usage(160, 90, cached=10, reasoning=10))],
                trailing_agent_reasoning=True,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root))
            self.assertEqual(report["cost_estimate"]["status"], "not-available")
            self.assertEqual(
                report["cost_estimate"]["reason"],
                "in-window model activity after last token_count without a new token_count",
            )

    # @spec:AC-522
    def test_agent_reasoning_is_reset_by_a_later_token_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(
                root,
                requests=[
                    ("standard", usage(100, 50), usage(160, 90, cached=10, reasoning=10)),
                    ("standard", usage(40, 20), usage(200, 110, cached=10, reasoning=15)),
                ],
                agent_reasoning_before_followup_token=True,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            pricing = root / "pricing.toml"
            pricing.write_text("""
[models.standard]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            report = run_json(
                "report",
                "--window",
                str(output),
                "--sessions-root",
                str(root),
                "--pricing-config",
                str(pricing),
            )
            self.assertEqual(report["request_token_usage"]["request_count"], 2)
            self.assertEqual(report["cost_estimate"]["status"], "estimated")

    # @spec:AC-517
    def test_malformed_turn_context_returns_json_not_available_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(
                root,
                requests=[("standard", usage(100, 50), usage(160, 90, cached=10, reasoning=10))],
                malformed_context=True,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            run, payload = run_failure("report", "--window", str(output), "--sessions-root", str(root))
            self.assertEqual(payload["status"], "not-available")
            self.assertIn("turn_context", payload["reason"])
            self.assertNotIn("Traceback", run.stderr)

    # @spec:AC-514
    def test_does_not_exclude_an_ambiguous_compaction_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(
                root,
                requests=[("standard", usage(100, 50), usage(160, 90, cached=10, reasoning=10))],
                compaction=True,
                compaction_extra_event=True,
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root))
            self.assertNotIn("compaction", report)
            self.assertNotIn("compaction_snapshots_excluded", report["request_token_usage"])
            self.assertEqual(report["request_token_usage"]["status"], "invalid")
            self.assertEqual(report["request_token_usage"]["invalid_snapshot_count"], 1)
            self.assertEqual(report["cost_estimate"]["status"], "not-available")

    # @spec:AC-516
    def test_does_not_treat_unmarked_zero_input_telemetry_as_compaction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            malformed = usage(0, 0)
            malformed["total_tokens"] = 13368
            session = write_main_session(
                root,
                requests=[("standard", malformed, usage(160, 90, cached=10, reasoning=10))],
            )
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root))
            self.assertEqual(report["request_token_usage"]["status"], "invalid")
            self.assertNotIn("compaction", report)
            self.assertEqual(report["cost_estimate"]["status"], "not-available")

    # @spec:AC-515
    def test_prices_main_requests_by_model_policy_and_long_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = usage(120, 30, cached=20)
            second = usage(40, 20)
            session = write_main_session(root, requests=[
                ("tiered", first, usage(180, 70, cached=30, reasoning=10)),
                ("standard", second, usage(220, 90, cached=30, reasoning=15)),
            ])
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            pricing = root / "pricing.toml"
            pricing.write_text("""
[models.tiered]
long_context_pricing = "tiered"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
long_context_threshold_tokens = 100
long_context_input_multiplier = 2.0
long_context_output_multiplier = 1.5

[models.standard]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root), "--pricing-config", str(pricing))
            estimate = report["cost_estimate"]
            self.assertEqual(estimate["status"], "estimated")
            self.assertEqual(estimate["request_count"], 2)
            self.assertEqual(estimate["long_context_request_count"], 1)
            self.assertEqual(sorted(estimate["pricing_models"]), ["standard", "tiered"])

    # @spec:AC-513
    def test_rejects_ambiguous_open_main_session_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_main_session(root, requests=[], filename="rollout-one.jsonl", session_name="session-one")
            write_main_session(root, requests=[], filename="rollout-two.jsonl", session_name="session-two")
            _, payload = run_failure(
                "start",
                "--task-id",
                "demo-task",
                "--sessions-root",
                str(root),
                "--output",
                str(sidecar(root, "task-window.json")),
            )
            self.assertEqual(payload["status"], "not-available")
            self.assertIn("multiple open main sessions", payload["reason"])

    # @spec:AC-519
    def test_rejects_automatic_rollout_symlink_that_resolves_outside_sessions_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "sessions"
            outside = Path(temporary) / "outside"
            source = write_main_session(outside, requests=[], filename="rollout-outside.jsonl")
            link = root / "2026" / "08" / "06" / "rollout-link.jsonl"
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(source, target_is_directory=False)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlinks are unavailable: {error}")
            _, payload = run_failure(
                "start",
                "--task-id",
                "demo-task",
                "--sessions-root",
                str(root),
                "--output",
                str(sidecar(root, "task-window.json")),
            )
            self.assertIn("outside --sessions-root", payload["reason"])

    # @spec:AC-519
    def test_rejects_automatic_rollout_directory_junction_that_resolves_outside_sessions_root(self) -> None:
        if os.name != "nt":
            self.skipTest("directory junctions require Windows")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "sessions"
            outside = Path(temporary) / "outside"
            write_main_session(outside, requests=[], filename="rollout-outside.jsonl")
            junction = root / "external-rollouts"
            junction.parent.mkdir(parents=True, exist_ok=True)
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                capture_output=True,
                text=True,
            )
            if created.returncode:
                details = (created.stdout + created.stderr).strip()
                self.skipTest(f"directory junctions are unavailable: {details}")
            output = sidecar(root, "junction-window.json")
            try:
                _, payload = run_failure(
                    "start",
                    "--task-id",
                    "demo-task",
                    "--sessions-root",
                    str(root),
                    "--output",
                    str(output),
                )
                self.assertEqual(payload["status"], "not-available")
                self.assertIn("outside --sessions-root", payload["reason"])
                self.assertFalse(output.exists())
            finally:
                subprocess.run(
                    ["cmd", "/c", "rmdir", str(junction)],
                    capture_output=True,
                    text=True,
                )

    # @spec:AC-513
    def test_rejects_missing_session_meta_and_subagent_rollout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing = write_main_session(root, requests=[], filename="rollout-missing.jsonl")
            lines = missing.read_text(encoding="utf-8").splitlines()
            missing.write_text("\n".join(lines[1:]) + "\n", encoding="utf-8")
            _, missing_payload = run_failure(
                "start",
                "--task-id",
                "demo-task",
                "--sessions-root",
                str(root),
                "--session-file",
                str(missing),
                "--output",
                str(sidecar(root, "missing-window.json")),
            )
            self.assertIn("recognized positive session_meta", missing_payload["reason"])

            child = write_main_session(root, requests=[], filename="rollout-child.jsonl", session_name="child-session")
            child_text = child.read_text(encoding="utf-8").replace(
                '"source": {"user": "main"}',
                '"source": {"subagent": {"thread_spawn": {"agent_path": "/root/child"}}}',
                1,
            )
            child.write_text(child_text, encoding="utf-8")
            _, child_payload = run_failure(
                "start",
                "--task-id",
                "demo-task",
                "--sessions-root",
                str(root),
                "--session-file",
                str(child),
                "--output",
                str(sidecar(root, "child-window.json")),
            )
            self.assertIn("subagent metadata", child_payload["reason"])

    # @spec:AC-513
    def test_accepts_only_documented_main_session_metadata_forms(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            supported = [
                {"source": "cli"},
                {"source": "vscode", "thread_source": "main"},
                {"thread_source": "user"},
            ]
            for index, metadata in enumerate(supported):
                output = sidecar(root, f"supported-{index}.json")
                write_main_session(
                    root,
                    requests=[],
                    filename=f"rollout-supported-{index}.jsonl",
                    session_name=f"supported-{index}",
                    session_metadata=metadata,
                )
                payload = run_json(
                    "start",
                    "--task-id",
                    "demo-task",
                    "--sessions-root",
                    str(root),
                    "--session-file",
                    str(root / "2026" / "08" / "06" / f"rollout-supported-{index}.jsonl"),
                    "--output",
                    str(output),
                )
                self.assertEqual(payload["status"], "created")

    # @spec:AC-513
    def test_rejects_unknown_and_contradictory_main_session_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            invalid = [
                {},
                {"source": {"unknown": "main"}},
                {"source": {"user": "main", "extra": "value"}},
                {"source": None},
                {"source": "cli", "thread_source": "subagent"},
                {"source": "cli", "thread_source": "worker"},
            ]
            for index, metadata in enumerate(invalid):
                session = write_main_session(
                    root,
                    requests=[],
                    filename=f"rollout-invalid-metadata-{index}.jsonl",
                    session_name=f"invalid-metadata-{index}",
                    session_metadata=metadata,
                )
                _, payload = run_failure(
                    "start",
                    "--task-id",
                    "demo-task",
                    "--sessions-root",
                    str(root),
                    "--session-file",
                    str(session),
                    "--output",
                str(sidecar(root, f"invalid-{index}.json")),
                )
                self.assertEqual(payload["status"], "not-available")
                self.assertTrue(
                    "session_meta" in payload["reason"] or "subagent metadata" in payload["reason"]
                )

    # @spec:AC-513
    def test_explicit_session_file_must_be_inside_sessions_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "sessions"
            outside = root.parent / "outside-rollout.jsonl"
            inside = write_main_session(root, requests=[])
            outside.write_bytes(inside.read_bytes())
            _, payload = run_failure(
                "start",
                "--task-id",
                "demo-task",
                "--sessions-root",
                str(root),
                "--session-file",
                str(outside),
                "--output",
                str(sidecar(root, "outside-window.json")),
            )
            self.assertIn("within --sessions-root", payload["reason"])

    # @spec:AC-516
    def test_rejects_sidecar_session_path_and_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            window = json.loads(output.read_text(encoding="utf-8"))
            window["session"]["path"] = str(root / "2026" / "08" / "06" / "rollout-child.jsonl")
            output.write_text(json.dumps(window), encoding="utf-8")
            _, path_payload = run_failure("report", "--window", str(output), "--sessions-root", str(root))
            self.assertIn("does not match rollout_file", path_payload["reason"])

            window["session"].pop("path")
            window["session"]["session_id"] = "other-session"
            output.write_text(json.dumps(window), encoding="utf-8")
            _, identity_payload = run_failure("report", "--window", str(output), "--sessions-root", str(root))
            self.assertIn("session_id does not match", identity_payload["reason"])
            self.assertEqual(session.name, window["session"]["rollout_file"])

    # @spec:AC-516
    def test_closed_report_fails_closed_for_unreadable_jsonl_in_window(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            with session.open("a", encoding="utf-8") as target:
                target.write("{not valid jsonl}\n")
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root))
            self.assertIsNone(report["window_token_usage"])
            self.assertEqual(report["cost_estimate"]["status"], "not-available")
            self.assertEqual(report["cost_estimate"]["reason"], "window contains unreadable JSONL records")
            self.assertEqual(len(report["jsonl_errors"]["affecting_window"]), 1)

    # @spec:AC-516
    def test_does_not_infer_zero_baseline_after_prior_activity_without_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            lines = session.read_text(encoding="utf-8").splitlines()
            session.write_text("\n".join([lines[0], lines[1], lines[3]]) + "\n", encoding="utf-8")
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root))
            self.assertIsNone(report["baseline_total_token_usage"])
            self.assertEqual(report["boundaries"]["baseline_source"], "pre-window-activity-without-readable-baseline")
            self.assertEqual(report["cost_estimate"]["status"], "not-available")

    # @spec:AC-516
    def test_close_requires_end_turn_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run = subprocess.run(
                [sys.executable, str(SCRIPT), "close", "--window", str(output), "--sessions-root", str(root), "--json"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("--end-turn-id", run.stderr)

    # @spec:AC-516
    def test_close_rejects_an_end_turn_id_from_another_turn(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session, "other-turn")
            _, payload = run_failure(
                "close",
                "--window",
                str(output),
                "--sessions-root",
                str(root),
                "--end-turn-id",
                "other-turn",
            )
            self.assertIn("match the window start turn_id", payload["reason"])

    # @spec:AC-516
    def test_close_idempotency_validates_the_saved_end_turn_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            already_closed = run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            self.assertEqual(already_closed["status"], "already-closed")
            _, payload = run_failure(
                "close",
                "--window",
                str(output),
                "--sessions-root",
                str(root),
                "--end-turn-id",
                "other-turn",
            )
            self.assertIn("saved window end turn_id", payload["reason"])

    # @spec:AC-520
    def test_report_and_close_require_the_persisted_boundary_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")

            window = json.loads(output.read_text(encoding="utf-8"))
            window["end"]["line"] += 1
            output.write_text(json.dumps(window), encoding="utf-8")
            _, report_payload = run_failure("report", "--window", str(output), "--sessions-root", str(root))
            self.assertIn("end boundary identity", report_payload["reason"])

            window["status"] = "open"
            window["end"] = None
            window["start"]["event_index"] += 1
            output.write_text(json.dumps(window), encoding="utf-8")
            _, close_payload = run_failure(
                "close",
                "--window",
                str(output),
                "--sessions-root",
                str(root),
                "--end-turn-id",
                "task-start",
            )
            self.assertIn("start boundary identity", close_payload["reason"])

    # @spec:AC-520
    def test_duplicate_end_boundary_is_ambiguous_and_cannot_extend_a_closed_window(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            append_task_complete(session)
            _, payload = run_failure("report", "--window", str(output), "--sessions-root", str(root))
            self.assertIn("ambiguous duplicate end boundary", payload["reason"])

    # @spec:AC-516
    def test_window_writes_leave_no_temporary_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = write_main_session(root, requests=[])
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            self.assertEqual(list(output.parent.glob(f".{output.name}.*.tmp")), [])
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            self.assertEqual(list(output.parent.glob(f".{output.name}.*.tmp")), [])

    # @spec:AC-516
    def test_refuses_a_window_when_delta_does_not_reconcile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = usage(100, 50)
            session = write_main_session(root, requests=[("standard", request, usage(160, 90, cached=10, reasoning=10))], mismatch=True)
            output = sidecar(root, "task-window.json")
            run_json("start", "--task-id", "demo-task", "--sessions-root", str(root), "--output", str(output))
            append_task_complete(session)
            run_json("close", "--window", str(output), "--sessions-root", str(root), "--end-turn-id", "task-start")
            pricing = root / "pricing.toml"
            pricing.write_text("""
[models.standard]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.25
output_per_million = 2.0
""", encoding="utf-8")
            report = run_json("report", "--window", str(output), "--sessions-root", str(root), "--pricing-config", str(pricing))
            self.assertEqual(report["cost_estimate"]["status"], "not-available")
            self.assertEqual(report["cost_estimate"]["reason"], "in-window request usage does not reconcile with cumulative window delta")

    # @spec:AC-516
    def test_rejects_a_window_without_explicit_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = sidecar(root, "task-window.json")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps({
                "schema_version": 1,
                "task_id": "demo-task",
                "status": "closed",
                "session": {
                    "session_id": "main-session",
                    "rollout_file": "rollout-main.jsonl",
                },
                "start": None,
                "end": None,
            }), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(SCRIPT), "report", "--window", str(output), "--json"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(run.returncode, 0)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "not-available")
            self.assertIn("start boundary", payload["reason"])


if __name__ == "__main__":
    unittest.main()
