from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "delegation_telemetry.py"


def _usage(total: int = 150) -> dict[str, int]:
    return {
        "input_tokens": 100,
        "cached_input_tokens": 10,
        "cache_write_input_tokens": 0,
        "output_tokens": 50,
        "reasoning_output_tokens": 10,
        "total_tokens": total,
    }


def _write_rollout(root: Path, agent_path: str, *, model: str = "test-model") -> None:
    path = root / "2026" / "08" / "08" / "rollout-child.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    usage = _usage()
    events = [
        {
            "type": "session_meta",
            "payload": {
                "session_id": "child-session",
                "source": {
                    "subagent": {
                        "thread_spawn": {
                            "agent_path": agent_path,
                            "parent_thread_id": "parent-session",
                            "agent_role": "implementer",
                        }
                    }
                },
            },
        },
        {"type": "turn_context", "payload": {"model": model, "effort": "low"}},
        {
            "type": "event_msg",
            "payload": {"type": "token_count", "info": {"total_token_usage": usage, "last_token_usage": usage}},
        },
    ]
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")


def _write_pricing(path: Path) -> None:
    path.write_text(
        """
[models.test-model]
long_context_pricing = "standard"
input_per_million = 1.0
cached_input_per_million = 0.1
cache_write_input_per_million = 1.0
output_per_million = 2.0
""",
        encoding="utf-8",
    )


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


class DelegationTelemetryTests(unittest.TestCase):
    # @spec:AC-801
    def test_init_and_record_are_idempotent_by_work_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "delegation-evidence.json"
            self.assertEqual(_run("init", "--output", str(manifest)).returncode, 0)
            first = _run(
                "record",
                "--output",
                str(manifest),
                "--manifest",
                str(manifest),
                "--work-package",
                "WP-001",
                "--role",
                "implementer",
                "--agent-id",
                "/root/one",
                "--requested-model",
                "gpt-5.6-luna",
                "--requested-effort",
                "max",
            )
            second = _run(
                "record",
                "--output",
                str(manifest),
                "--manifest",
                str(manifest),
                "--work-package",
                "WP-001",
                "--role",
                "implementer",
                "--agent-id",
                "/root/two",
                "--state",
                "completed",
            )
            self.assertEqual(first.returncode, 0)
            self.assertEqual(second.returncode, 0)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["delegations"]), 1)
            self.assertEqual(payload["delegations"][0]["agent_id"], "/root/two")

    # @spec:AC-802
    def test_collect_preserves_effective_usage_and_estimates_delegated_cost(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sessions = root / "sessions"
            pricing = root / "pricing.toml"
            manifest = root / "delegation-evidence.json"
            _write_rollout(sessions, "/root/one")
            _write_pricing(pricing)
            self.assertEqual(_run("init", "--output", str(manifest)).returncode, 0)
            self.assertEqual(
                _run(
                    "record",
                    "--output",
                    str(manifest),
                    "--manifest",
                    str(manifest),
                    "--work-package",
                    "WP-001",
                    "--role",
                    "implementer",
                    "--agent-id",
                    "/root/one",
                    "--state",
                    "completed",
                    "--requested-model",
                    "test-model",
                    "--requested-effort",
                    "low",
                ).returncode,
                0,
            )
            result = _run(
                "collect",
                "--output",
                str(manifest),
                "--manifest",
                str(manifest),
                "--sessions-root",
                str(sessions),
                "--pricing-config",
                str(pricing),
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            entry = payload["delegations"][0]
            self.assertEqual(entry["effective"]["model"], "test-model")
            self.assertEqual(entry["request_token_usage"]["status"], "observed")
            self.assertEqual(payload["delegated_subtotal"]["status"], "estimated")
            self.assertGreater(payload["delegated_subtotal"]["total_usd"], 0)

    # @spec:AC-803
    def test_incomplete_telemetry_is_not_zero_and_strict_mode_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "delegation-evidence.json"
            self.assertEqual(_run("init", "--output", str(manifest)).returncode, 0)
            self.assertEqual(
                _run(
                    "record",
                    "--output",
                    str(manifest),
                    "--manifest",
                    str(manifest),
                    "--work-package",
                    "WP-001",
                    "--role",
                    "implementer",
                    "--agent-id",
                    "/root/missing",
                    "--state",
                    "completed",
                ).returncode,
                0,
            )
            result = _run(
                "collect",
                "--output",
                str(manifest),
                "--manifest",
                str(manifest),
                "--sessions-root",
                str(root / "sessions"),
                "--json",
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            delegated = payload["delegated_subtotal"]
            self.assertEqual(delegated["status"], "not-available")
            self.assertNotIn("total_usd", delegated)

if __name__ == "__main__":
    unittest.main()
