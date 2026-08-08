from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_drift  # noqa: E402
import validate_feature as validate_feature_module  # noqa: E402
from validate_feature import has_open_status, validate_feature  # noqa: E402
from verify_feature import test_map  # noqa: E402


def _mapping_digest(mapping: object) -> str:
    payload = json.dumps(mapping, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_feature(
    repo: Path,
    name: str,
    mapping: dict[str, list[dict[str, object]]],
    criteria: list[str] | None = None,
) -> Path:
    feature = repo / "specs" / name
    feature.mkdir(parents=True, exist_ok=True)
    criteria = criteria or ["AC-601"]
    criteria_text = "\n".join(f"- {criterion}: comportamento" for criterion in criteria)
    task_text = "\n".join(f"- T-{criterion[3:]} ({criterion}): tarefa" for criterion in criteria)
    evidence_text = "\n".join(f"@spec:{criterion}" for criterion in criteria)
    (feature / "spec.md").write_text(f"# Feature\n\n## Critérios\n{criteria_text}\n", encoding="utf-8")
    (feature / "plan.md").write_text(f"# Plano\n\n{task_text}\n", encoding="utf-8")
    (feature / "status.md").write_text("# Status\n", encoding="utf-8")
    (feature / "evidence.md").write_text(evidence_text + "\n", encoding="utf-8")
    (feature / "verification.json").write_text(
        json.dumps(
            {
                "criteria": criteria,
                "test_map": mapping,
                "mapping_sha256": _mapping_digest(mapping),
                "passed": True,
                "exit_code": 0,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return feature


def _write_mapped_feature(repo: Path, name: str = "feature") -> tuple[Path, dict[str, list[dict[str, object]]]]:
    source = repo / "tests" / "support.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# @spec:AC-601\n", encoding="utf-8")
    mapping = test_map(repo)
    return _write_feature(repo, name, mapping), mapping


def _run_check_drift(repo: Path) -> tuple[int, str]:
    output = io.StringIO()
    with patch.object(sys, "argv", ["check_drift.py", str(repo)]), redirect_stdout(output):
        result = check_drift.main()
    return result, output.getvalue()


class CheckDriftTests(unittest.TestCase):
    # @spec:AC-601
    def test_validate_feature_returns_validation_errors_as_a_list(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            feature, mapping = _write_mapped_feature(repo)

            result = validate_feature(repo, feature, full_map=mapping)

            self.assertEqual(result, [])
            self.assertIsInstance(result, list)

    # @spec:AC-526
    def test_validate_feature_requires_closed_matching_main_chat_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            feature, mapping = _write_mapped_feature(repo)
            (feature / "plan.md").write_text(
                "# Plano\n\n"
                "Main-chat attribution: required\n\n"
                "- T-601 (AC-601): tarefa\n",
                encoding="utf-8",
            )

            self.assertEqual(
                validate_feature(repo, feature, full_map=mapping),
                [
                    "arquivo ausente: task-window.json",
                    "arquivo ausente: task-window-report.json",
                ],
            )

            window = {
                "schema_version": 1,
                "task_id": "WP-527",
                "status": "closed",
                "session": {"session_id": "session-527", "rollout_file": "rollout.jsonl"},
                "start": {
                    "event_index": 11,
                    "line": 12,
                    "kind": "task_started",
                    "turn_id": "turn-527",
                },
                "end": {
                    "event_index": 19,
                    "line": 20,
                    "kind": "task_complete",
                    "turn_id": "turn-527",
                },
            }
            report = {
                "schema_version": 1,
                "status": "closed",
                "provisional": False,
                "final": True,
                "task_id": "WP-527",
                "scope": "main-chat-orchestrator",
                "exclusions": [
                    "delegated-agent rollouts",
                    "tool fees",
                    "modality fees",
                    "subscription billing",
                ],
                "session": {"session_id": "session-527", "rollout_file": "rollout.jsonl"},
                "boundaries": {"start": window["start"], "end": window["end"]},
                "cost_estimate": {"status": "estimated", "total_usd": 0.125},
            }

            def write_artifacts(current_window: dict[str, object], current_report: dict[str, object]) -> None:
                (feature / "task-window.json").write_text(
                    json.dumps(current_window) + "\n", encoding="utf-8"
                )
                (feature / "task-window-report.json").write_text(
                    json.dumps(current_report) + "\n", encoding="utf-8"
                )

            rejected_cases = (
                ("open window", {**window, "status": "open"}, report, "task-window.json deve estar fechado"),
                ("provisional report", window, {**report, "provisional": True}, "task-window-report.json deve ser não-provisório"),
                (
                    "report without final marker",
                    window,
                    {key: value for key, value in report.items() if key != "final"},
                    "task-window-report.json deve ser final",
                ),
                (
                    "window without schema version",
                    {key: value for key, value in window.items() if key != "schema_version"},
                    report,
                    "task-window.json tem schema incompatível",
                ),
                (
                    "report with incompatible schema version",
                    window,
                    {**report, "schema_version": 2},
                    "task-window-report.json tem schema incompatível",
                ),
                ("wrong report scope", window, {**report, "scope": "delegated-agent"}, "task-window-report.json deve usar scope main-chat-orchestrator"),
                ("mismatched task", window, {**report, "task_id": "WP-528"}, "task-window-report.json task_id does not match task-window.json"),
                (
                    "mismatched session",
                    window,
                    {**report, "session": {"session_id": "session-528", "rollout_file": "rollout.jsonl"}},
                    "task-window-report.json session identity does not match task-window.json",
                ),
                (
                    "mismatched boundary",
                    window,
                    {**report, "boundaries": {"start": {**window["start"], "line": 13}, "end": window["end"]}},
                    "task-window-report.json boundaries do not match task-window.json",
                ),
                (
                    "unsafe rollout",
                    {**window, "session": {"session_id": "session-527", "rollout_file": "../rollout.jsonl"}},
                    report,
                    "task-window.json has an unsafe rollout_file",
                ),
            )
            for label, current_window, current_report, expected_error in rejected_cases:
                with self.subTest(case=label):
                    write_artifacts(current_window, current_report)
                    self.assertIn(expected_error, validate_feature(repo, feature, full_map=mapping))

    # @spec:AC-529
    def test_validate_feature_requires_valid_main_chat_cost_and_accepts_final_cost_states(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            feature, mapping = _write_mapped_feature(repo)
            (feature / "plan.md").write_text(
                "# Plano\n\n"
                "Main-chat attribution: required\n\n"
                "- T-601 (AC-601): tarefa\n",
                encoding="utf-8",
            )
            window = {
                "schema_version": 1,
                "task_id": "WP-527",
                "status": "closed",
                "session": {"session_id": "session-527", "rollout_file": "rollout.jsonl"},
                "start": {
                    "event_index": 11,
                    "line": 12,
                    "kind": "task_started",
                    "turn_id": "turn-527",
                },
                "end": {
                    "event_index": 19,
                    "line": 20,
                    "kind": "task_complete",
                    "turn_id": "turn-527",
                },
            }
            report = {
                "schema_version": 1,
                "status": "closed",
                "provisional": False,
                "final": True,
                "task_id": "WP-527",
                "scope": "main-chat-orchestrator",
                "exclusions": [
                    "delegated-agent rollouts",
                    "tool fees",
                    "modality fees",
                    "subscription billing",
                ],
                "session": {"session_id": "session-527", "rollout_file": "rollout.jsonl"},
                "boundaries": {"start": window["start"], "end": window["end"]},
            }
            (feature / "task-window.json").write_text(
                json.dumps(window) + "\n", encoding="utf-8"
            )

            rejected_costs = (
                ("zero estimated cost", {"status": "estimated", "total_usd": 0}, "task-window-report.json estimated cost lacks a valid total_usd"),
                ("non-numeric estimated cost", {"status": "estimated", "total_usd": "0.125"}, "task-window-report.json estimated cost lacks a valid total_usd"),
                ("unavailable cost without reason", {"status": "not-available"}, "task-window-report.json unavailable cost lacks a reason"),
                (
                    "unavailable cost with null total",
                    {"status": "not-available", "reason": "telemetry is incomplete", "total_usd": None},
                    "task-window-report.json unavailable cost must not include total_usd",
                ),
            )
            for label, cost_estimate, expected_error in rejected_costs:
                with self.subTest(cost=label):
                    (feature / "task-window-report.json").write_text(
                        json.dumps({**report, "cost_estimate": cost_estimate}) + "\n",
                        encoding="utf-8",
                    )
                    self.assertIn(expected_error, validate_feature(repo, feature, full_map=mapping))

            accepted_costs = (
                {"status": "estimated", "total_usd": 0.125},
                {"status": "not-available", "reason": "telemetry is incomplete"},
            )
            for cost_estimate in accepted_costs:
                with self.subTest(cost=cost_estimate["status"]):
                    (feature / "task-window-report.json").write_text(
                        json.dumps({**report, "cost_estimate": cost_estimate}) + "\n",
                        encoding="utf-8",
                    )
                    self.assertEqual(validate_feature(repo, feature, full_map=mapping), [])

    # @spec:AC-705
    def test_v1_status_ignores_historical_open_entries_but_rejects_current_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            feature, mapping = _write_mapped_feature(repo)
            historical_status = (
                "# Status\n\n"
                "## Histórico\n"
                "- execução falhou\n"
                "- pending\n\n"
                "## Estado atual\n"
                "- concluído\n"
            )
            (feature / "status.md").write_text(historical_status, encoding="utf-8")

            self.assertFalse(has_open_status(historical_status))
            self.assertTrue(has_open_status("## Estado atual: pending\n"))
            self.assertTrue(has_open_status("Estado atual: pending\n"))
            self.assertTrue(has_open_status("- Fase atual: pending\n"))
            self.assertTrue(has_open_status("- Bloqueios: blocker aberto\n"))
            self.assertTrue(has_open_status("## Fase atual\nEm andamento\n"))
            self.assertTrue(has_open_status("## Bloqueios\nHá um blocker aberto\n"))
            self.assertFalse(has_open_status("- Fase atual: concluída\n- Bloqueios: nenhum\n"))
            self.assertFalse(
                has_open_status("## Fase atual\nConcluída\n## Bloqueios\nNenhum\n")
            )
            self.assertTrue(has_open_status("## Perguntas abertas\n- Q-705: qual é a decisão?\n"))
            self.assertTrue(has_open_status("## Suposições\n- ASM-705: o runtime está disponível.\n"))
            self.assertFalse(has_open_status("## Perguntas abertas\n- Q-705: Resolvida\n"))
            self.assertFalse(has_open_status("## Suposições\n- ASM-705: Validada\n"))
            self.assertFalse(has_open_status("A frase specs pendentes não representa um estado estruturado.\n"))
            table_status = (
                "## History\n"
                "| ID | Status |\n"
                "| --- | --- |\n"
                "| WP-1 | pending |\n\n"
                "## Work packages\n"
                "| ID | Status |\n"
                "| --- | --- |\n"
                "| WP-1 | completed |\n"
            )
            self.assertFalse(has_open_status(table_status))
            self.assertTrue(has_open_status(table_status.replace("completed", "PENDING")))
            self.assertFalse(has_open_status("```text\nstatus: pending\n```\n"))
            self.assertEqual(validate_feature(repo, feature, full_map=mapping), [])

            closed_sections = "# Status\n\n## Fase atual\nConcluída\n\n## Bloqueios\nNenhum\n"
            (feature / "status.md").write_text(closed_sections, encoding="utf-8")
            self.assertEqual(validate_feature(repo, feature, full_map=mapping), [])

            open_sections = "# Status\n\n## Fase atual\nPendente\n\n## Bloqueios\nNenhum\n"
            (feature / "status.md").write_text(open_sections, encoding="utf-8")
            self.assertIn(
                "status.md indica estado aberto",
                validate_feature(repo, feature, full_map=mapping),
            )

            current_pending = historical_status.replace("- concluído", "- pending")
            (feature / "status.md").write_text(current_pending, encoding="utf-8")
            self.assertTrue(has_open_status(current_pending))
            errors = validate_feature(repo, feature, full_map=mapping)
            self.assertIn("status.md indica estado aberto", errors)

    # @spec:AC-705
    def test_historical_phase_and_blocker_sections_do_not_open_current_status(self) -> None:
        historical = (
            "# Status\n\n"
            "## Historico\n"
            "### Fase atual\nPendente\n"
            "### Bloqueios\nHa um blocker aberto\n\n"
            "## Fase atual\nConcluida\n"
            "## Bloqueios\nNenhum\n"
        )

        self.assertFalse(has_open_status(historical))
        self.assertTrue(has_open_status(historical.replace("Concluida", "Pendente")))
        self.assertTrue(has_open_status(historical.replace("Nenhum", "blocker aberto")))

    # @spec:AC-705
    def test_validate_feature_rejects_open_structured_plan_and_accepts_historical_or_closed_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            feature, mapping = _write_mapped_feature(repo)

            open_plan = (
                "# Plano\n\n"
                "## Estado atual\n"
                "Pendente\n\n"
                "- T-601 (AC-601): tarefa\n"
            )
            (feature / "plan.md").write_text(open_plan, encoding="utf-8")
            self.assertTrue(has_open_status(open_plan))
            errors = validate_feature(repo, feature, full_map=mapping)
            self.assertIn("plan.md indica estado aberto", errors)

            accepted_plans = (
                (
                    "historical",
                    "# Plano\n\n"
                    "## Historico\n"
                    "- estado: pending\n"
                    "- execucao falhou\n\n"
                    "## Estado atual\n"
                    "Concluido\n\n"
                    "- T-601 (AC-601): tarefa\n",
                ),
                (
                    "closed",
                    "# Plano\n\n"
                    "## Fase atual\n"
                    "Concluida\n\n"
                    "## Bloqueios\n"
                    "Nenhum\n\n"
                    "- T-601 (AC-601): tarefa\n",
                ),
            )
            for label, plan in accepted_plans:
                with self.subTest(plan=label):
                    (feature / "plan.md").write_text(plan, encoding="utf-8")
                    self.assertFalse(has_open_status(plan))
                    self.assertEqual(validate_feature(repo, feature, full_map=mapping), [])

    # @spec:AC-601
    def test_validate_feature_respects_an_explicit_empty_full_map(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            feature, mapping = _write_mapped_feature(repo)
            verification = json.loads((feature / "verification.json").read_text(encoding="utf-8"))
            verification["test_map"] = {}
            verification["mapping_sha256"] = _mapping_digest({})
            (feature / "verification.json").write_text(json.dumps(verification) + "\n", encoding="utf-8")

            with patch.object(validate_feature_module, "test_map", side_effect=AssertionError("test_map não deveria ser chamado")):
                result = validate_feature(repo, feature, full_map={})

            self.assertIn("AC-601 sem teste anotado em código", result)
            self.assertTrue(result)
            self.assertNotIn("verification.json está obsoleto", result)

    # @spec:AC-602
    def test_validate_feature_cli_preserves_success_and_failure_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            feature, _ = _write_mapped_feature(repo)
            command = [sys.executable, str(ROOT / "scripts" / "validate_feature.py"), str(repo), str(feature.relative_to(repo))]

            success = subprocess.run(command, check=False, capture_output=True, text=True)

            self.assertEqual(success.returncode, 0)
            self.assertEqual(success.stdout.strip(), f"OK: {feature.resolve()}")
            self.assertEqual(success.stderr, "")

            failure = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_feature.py"), str(repo), "specs\nmissing"],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(failure.returncode, 1)
            self.assertTrue(failure.stdout.startswith("FALHA\n"))
            self.assertEqual(failure.stderr, "")

    # @spec:AC-603
    def test_check_drift_calculates_one_map_and_reuses_the_same_object(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            (repo / "specs" / "alpha").mkdir(parents=True)
            (repo / "specs" / "beta").mkdir()
            shared_map: dict[str, list[dict[str, object]]] = {}

            with patch.object(check_drift, "test_map", return_value=shared_map) as map_mock, patch.object(
                check_drift, "validate_feature", return_value=[]
            ) as validate_mock:
                result, output = _run_check_drift(repo)

            self.assertEqual(result, 0)
            self.assertIn("OK: nenhum drift", output)
            map_mock.assert_called_once_with(repo.resolve())
            self.assertEqual(validate_mock.call_count, 2)
            self.assertIs(validate_mock.call_args_list[0].kwargs["full_map"], shared_map)
            self.assertIs(validate_mock.call_args_list[1].kwargs["full_map"], shared_map)

    # @spec:AC-604
    def test_check_drift_preserves_baseline_followups_and_does_not_spawn_subprocesses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            baseline = repo / "specs" / "baseline-existing"
            baseline.mkdir(parents=True)
            (baseline / "status.md").write_text("Origem: baseline-conformance\n", encoding="utf-8")
            regular = repo / "specs" / "regular"
            regular.mkdir()
            shared_map: dict[str, list[dict[str, object]]] = {}

            with patch.object(check_drift, "test_map", return_value=shared_map) as map_mock, patch.object(
                check_drift, "validate_feature", return_value=[]
            ) as validate_mock, patch("subprocess.run", side_effect=AssertionError("subprocess não deveria ser chamado")):
                result, output = _run_check_drift(repo)

            self.assertEqual(result, 0)
            self.assertIn("FOLLOW-UPS DE BASELINE PENDENTES: baseline-existing", output)
            map_mock.assert_called_once_with(repo.resolve())
            self.assertEqual(validate_mock.call_count, 1)
            self.assertEqual(validate_mock.call_args.args[1], Path("specs/regular"))


if __name__ == "__main__":
    unittest.main()
