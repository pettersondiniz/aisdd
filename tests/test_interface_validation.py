from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InterfaceValidationGuidanceTests(unittest.TestCase):
    # @spec:AC-001
    def test_declares_capability_preference_order(self) -> None:
        reference = (ROOT / "references" / "interface-validation.md").read_text(encoding="utf-8")
        self.assertIn("`playwright-cli`", reference)
        self.assertIn("Playwright MCP", reference)
        self.assertIn("another approved browser tool", reference)

    # @spec:AC-002
    def test_requires_honest_evidence_when_browser_validation_is_unavailable(self) -> None:
        reference = (ROOT / "references" / "interface-validation.md").read_text(encoding="utf-8")
        self.assertIn("`not-run`", reference)
        self.assertIn("Never claim `real-browser` without an actual execution.", reference)

    # @spec:AC-001
    def test_template_requires_triage_before_software_changes(self) -> None:
        template = (ROOT / "assets" / "templates" / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## Mandatory AISDD triage", template)
        self.assertIn("classify the request as T0–T4", template)
        self.assertIn("T1+: use `$aisdd`", template)

    # @spec:AC-002
    def test_template_requires_t2_routing_or_honest_limitation(self) -> None:
        template = (ROOT / "assets" / "templates" / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("T2+: use the subagents required", template)
        self.assertIn("record that limitation in `evidence.md`", template)

    # @spec:AC-101
    def test_model_router_recommends_dedicated_equivalent_when_configured_model_is_missing(self) -> None:
        availability = ROOT / "tests" / "fixtures" / "dedicated-models.json"
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "model_routing.py"), "--role", "explorer", "--availability-json", str(availability), "--json"],
            check=True, capture_output=True, text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["recommendation"]["status"], "configured-unavailable")
        self.assertEqual(payload["recommendation"]["candidates"][0], {"model": "dinizpe-5.6-luna", "reasoning_effort": "low"})

    # @spec:AC-102
    def test_model_router_returns_inherit_fallback_without_availability(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "model_routing.py"), "--role", "reviewer", "--json"],
            check=True, capture_output=True, text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["recommendation"]["fallback"], {"model": "inherit", "reasoning_effort": "inherit"})

    # @spec:AC-103
    def test_model_router_does_not_create_user_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_home:
            environment = os.environ | {"HOME": temporary_home, "USERPROFILE": temporary_home}
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "model_routing.py"), "--list"],
                check=True, capture_output=True, text=True, env=environment,
            )
            self.assertIn("model-routing.toml", result.stdout)
            self.assertFalse(Path(temporary_home, ".codex", "aisdd", "model-routing.toml").exists())

    # @spec:AC-201
    def test_baseline_dry_run_does_not_write_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp); (repo / "README.md").write_text("x", encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "scripts" / "baseline_conformance.py"), str(repo), "--baseline-id", "first"], check=True, capture_output=True, text=True)
            self.assertIn("would_write", result.stdout)
            self.assertFalse((repo / "docs").exists())

    # @spec:AC-202
    def test_baseline_apply_requires_documentation_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run([sys.executable, str(ROOT / "scripts" / "baseline_conformance.py"), temp, "--baseline-id", "first", "--apply"], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("confirm-documentation-only", result.stderr)

    # @spec:AC-203
    def test_baseline_reports_an_outdated_agents_file_as_a_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "AGENTS.md").write_text("For non-trivial changes, use AISDD.", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "baseline_conformance.py"), str(repo), "--baseline-id", "audit"],
                check=True, capture_output=True, text=True,
            )
            payload = json.loads(result.stdout)
            gaps = {item["slug"]: item for item in payload["audit"]["gaps"]}
            self.assertIn("agents-guidance", gaps)
            self.assertIn("## Mandatory AISDD triage", gaps["agents-guidance"]["evidence"]["missing_markers"])

    # @spec:AC-204
    def test_baseline_apply_preserves_code_and_creates_documentation_followups(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            code = repo / "app.py"
            code.write_text("print('unchanged')\n", encoding="utf-8")
            subprocess.run(
                [
                    sys.executable, str(ROOT / "scripts" / "baseline_conformance.py"), str(repo),
                    "--baseline-id", "audit", "--apply", "--confirm-documentation-only",
                ],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(code.read_text(encoding="utf-8"), "print('unchanged')\n")
            self.assertTrue((repo / "docs" / "architecture" / "baselines" / "audit" / "manifest.json").exists())
            self.assertTrue((repo / "specs" / "baseline-audit-agents-guidance" / "plan.md").exists())
            self.assertTrue((repo / "docs" / "architecture" / "decisions" / "ADR-BASELINE-audit.md").exists())

    # @spec:AC-301
    def test_evidence_template_records_agent_execution_without_guessing(self) -> None:
        template = (ROOT / "assets" / "templates" / "evidence.md").read_text(encoding="utf-8")
        self.assertIn("## Rastreabilidade de agentes", template)
        self.assertIn("Modelo solicitado", template)
        self.assertIn("Modelo efetivo", template)
        self.assertIn("Não invente", template)


if __name__ == "__main__":
    unittest.main()
