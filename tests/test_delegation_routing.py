from __future__ import annotations

import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "model_routing.py"


def _run_router(*arguments: str, env: dict[str, str] | None = None) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *arguments, "--json"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(result.stdout)


def _run_router_raw(*arguments: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments, "--json"],
        capture_output=True,
        text=True,
        env=env,
    )


class DelegationRoutingTests(unittest.TestCase):
    # @spec:AC-804
    def test_spawn_guard_accepts_the_configured_available_route(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            availability = Path(temporary) / "availability.json"
            availability.write_text(
                json.dumps({"models": [{"id": "gpt-5.6-terra", "reasoning_efforts": ["high", "max"]}]}),
                encoding="utf-8",
            )
            result = _run_router(
                "--config",
                str(ROOT / "assets" / "templates" / "model-routing.toml"),
                "--role",
                "planner",
                "--class",
                "T3",
                "--availability-json",
                str(availability),
                "--requested-model",
                "gpt-5.6-terra",
                "--requested-effort",
                "high",
                "--require-available",
            )
            self.assertEqual(result["status"], "ready")
            self.assertFalse(result["fallback_required"])

    # @spec:AC-804
    def test_spawn_guard_rejects_an_unapproved_model_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            availability = Path(temporary) / "availability.json"
            availability.write_text(
                json.dumps({"models": [{"id": "gpt-5.6-terra", "reasoning_efforts": ["high", "max"]}, {"id": "gpt-5.4-mini", "reasoning_efforts": ["low"]}]}),
                encoding="utf-8",
            )
            result = _run_router_raw(
                "--config",
                str(ROOT / "assets" / "templates" / "model-routing.toml"),
                "--role",
                "planner",
                "--class",
                "T3",
                "--availability-json",
                str(availability),
                "--requested-model",
                "gpt-5.4-mini",
                "--requested-effort",
                "low",
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "request-mismatch")
            self.assertFalse(payload["routing_fallback"]["used"])

    # @spec:AC-804
    def test_spawn_guard_requires_inheritance_when_availability_is_unknown(self) -> None:
        result = _run_router_raw(
            "--config",
            str(ROOT / "assets" / "templates" / "model-routing.toml"),
            "--role",
            "planner",
            "--class",
            "T3",
            "--requested-model",
            "gpt-5.4-mini",
            "--requested-effort",
            "low",
        )
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "request-unavailable-override")
        self.assertTrue(payload["fallback_required"])

    # @spec:AC-804
    def test_spawn_guard_requires_a_reason_for_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            availability = Path(temporary) / "availability.json"
            availability.write_text(
                json.dumps({"models": [{"id": "gpt-5.6-terra", "reasoning_efforts": ["high", "max"]}, {"id": "gpt-5.4-mini", "reasoning_efforts": ["low"]}]}),
                encoding="utf-8",
            )
            result = _run_router(
                "--config",
                str(ROOT / "assets" / "templates" / "model-routing.toml"),
                "--role",
                "planner",
                "--class",
                "T3",
                "--availability-json",
                str(availability),
                "--requested-model",
                "gpt-5.4-mini",
                "--requested-effort",
                "low",
                "--allow-override",
                "--override-reason",
                "economy-approved-for-correction",
            )
            self.assertEqual(result["status"], "explicit-override")
            self.assertTrue(result["routing_fallback"]["used"])

    # @spec:AC-707
    def test_class_override_is_opt_in_and_changes_only_classified_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            availability = Path(temporary) / "availability.json"
            availability.write_text(json.dumps({"models": [{"id": "gpt-5.6-terra", "reasoning_efforts": ["medium", "high", "max"]}]}), encoding="utf-8")
            base = _run_router("--config", str(ROOT / "assets" / "templates" / "model-routing.toml"), "--role", "planner", "--availability-json", str(availability))
            classified = _run_router("--config", str(ROOT / "assets" / "templates" / "model-routing.toml"), "--role", "planner", "--class", "T3", "--availability-json", str(availability))

            base_recommendation = base["recommendation"]
            classified_recommendation = classified["recommendation"]
            assert isinstance(base_recommendation, dict)
            assert isinstance(classified_recommendation, dict)
            self.assertEqual(base_recommendation["reasoning_effort"], "medium")
            self.assertFalse(base_recommendation["class_applied"])
            self.assertEqual(classified_recommendation["reasoning_effort"], "high")
            self.assertTrue(classified_recommendation["class_applied"])
            self.assertEqual(classified_recommendation["profile"], "by_class")

    # @spec:AC-708
    def test_alias_is_canonicalized_and_missing_role_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "routing.toml"
            config.write_text(
                """[fallback]\nmodel = \"inherit\"\nreasoning_effort = \"inherit\"\n\n[aliases]\ntester = \"test-engineer\"\n\n[tiers.standard]\nmodel_patterns = [\".*\"]\neffort_order = [\"low\"]\n\n[roles.tester]\nmodel = \"legacy-tester\"\nreasoning_effort = \"low\"\ntier = \"standard\"\n""",
                encoding="utf-8",
            )
            availability = Path(temporary) / "availability.json"
            availability.write_text(json.dumps({"models": [{"id": "legacy-tester", "reasoning_efforts": ["low"]}]}), encoding="utf-8")
            alias = _run_router("--config", str(config), "--role", "tester", "--availability-json", str(availability))
            missing_result = _run_router_raw("--config", str(config), "--role", "verifier", "--availability-json", str(availability))
            self.assertNotEqual(missing_result.returncode, 0)
            missing = json.loads(missing_result.stdout)

            alias_recommendation = alias["recommendation"]
            missing_recommendation = missing["recommendation"]
            assert isinstance(alias_recommendation, dict)
            assert isinstance(missing_recommendation, dict)
            self.assertEqual(alias_recommendation["resolved_role"], "test-engineer")
            self.assertEqual(alias_recommendation["configured_role"], "tester")
            self.assertEqual(missing_recommendation["status"], "role-not-configured")
            self.assertFalse(missing_recommendation["capability_available"])

    # @spec:AC-708
    def test_v1_tester_alias_cannot_be_remapped_to_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "routing.toml"
            config.write_text(
                """[fallback]\nmodel = \"inherit\"\nreasoning_effort = \"inherit\"\n\n[aliases]\ntester = \"verifier\"\n\n[tiers.standard]\nmodel_patterns = [\".*\"]\neffort_order = [\"low\"]\n\n[roles.verifier]\nmodel = \"legacy-verifier\"\nreasoning_effort = \"low\"\ntier = \"standard\"\n""",
                encoding="utf-8",
            )
            availability = Path(temporary) / "availability.json"
            availability.write_text(
                json.dumps({"models": [{"id": "legacy-verifier", "reasoning_efforts": ["low"]}]}),
                encoding="utf-8",
            )
            result = _run_router_raw(
                "--config",
                str(config),
                "--role",
                "tester",
                "--availability-json",
                str(availability),
            )
            self.assertNotEqual(result.returncode, 0)
            recommendation = json.loads(result.stdout)["recommendation"]
            self.assertEqual(recommendation["resolved_role"], "test-engineer")
            self.assertIsNone(recommendation["configured_role"])
            self.assertEqual(recommendation["status"], "role-not-configured")
            self.assertFalse(recommendation["capability_available"])

    # @spec:AC-708
    def test_inherit_is_not_a_capability_or_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "routing.toml"
            config.write_text(
                """[fallback]\nmodel = \"inherit\"\nreasoning_effort = \"inherit\"\n\n[tiers.standard]\nmodel_patterns = [\".*\"]\neffort_order = [\"low\"]\n\n[roles.verifier]\nmodel = \"inherit\"\nreasoning_effort = \"inherit\"\ntier = \"standard\"\n""",
                encoding="utf-8",
            )
            result = _run_router_raw("--config", str(config), "--role", "verifier")
            self.assertNotEqual(result.returncode, 0)
            recommendation = json.loads(result.stdout)["recommendation"]
            self.assertEqual(recommendation["status"], "inherit-not-capability")
            self.assertFalse(recommendation["capability_available"])

    # @spec:AC-710
    def test_class_query_does_not_write_global_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = os.environ | {"HOME": temporary, "USERPROFILE": temporary}
            template = ROOT / "assets" / "templates" / "model-routing.toml"
            before = template.read_bytes()
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--config", str(template), "--role", "verifier", "--class", "T3"],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertIn("Role: verifier", result.stdout)
            self.assertFalse(Path(temporary, ".codex", "aisdd", "model-routing.toml").exists())
            self.assertEqual(template.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
