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
from validate_feature import validate_feature  # noqa: E402
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
