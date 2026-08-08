from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from delegation_contract import (  # noqa: E402
    extract_feature_class,
    is_v2_feature,
    validate_delegation_evidence,
    validate_v2_feature,
    validate_work_packages,
    work_packages_sha256,
)
from validate_feature import validate_feature  # noqa: E402


def _package(
    package_id: str,
    role: str,
    path: str | None,
    dependencies: list[str] | None = None,
    state: str = "completed",
) -> dict[str, object]:
    capability = {
        "implementer": "implement",
        "test-engineer": "write-tests",
        "verifier": "verify-final",
        "reviewer": "review",
        "planner": "plan-execution",
        "architect": "design",
        "documentation-reviewer": "review-docs",
    }[role]
    scope: object = {"write": [], "forbidden": []} if path is None else {"write": [path], "forbidden": ["runtime/"]}
    return {
        "id": package_id,
        "owner": f"owner-{package_id.lower()}",
        "role": role,
        "depends_on": dependencies or [],
        "capabilities": [capability],
        "scope": scope,
        "acceptance_criteria": ["AC-704"],
        "state": state,
    }


def _valid_work_packages() -> dict[str, object]:
    return {
        "contract": "v2",
        "contract_version": "v2",
        "work_packages": [
            _package("WP-5", "verifier", None, ["WP-4"]),
            _package("WP-1", "planner", None),
            _package("WP-7", "documentation-reviewer", None, ["WP-6"]),
            _package("WP-3", "implementer", "scripts/change.py", ["WP-2"]),
            _package("WP-6", "reviewer", None, ["WP-5"]),
            _package("WP-2", "architect", None, ["WP-1"]),
            _package("WP-4", "test-engineer", "tests/change.py", ["WP-3"]),
        ],
    }


def _valid_evidence(work_packages: dict[str, object]) -> dict[str, object]:
    return {
        "contract": "v2",
        "contract_version": "v2",
        "work_packages_sha256": work_packages_sha256(work_packages),
        "required_roles": ["planner", "architect", "implementer", "test-engineer", "verifier", "reviewer", "documentation-reviewer"],
        "delegations": [
            {"work_package": "WP-1", "role": "planner", "agent_id": "compass", "state": "completed", "fallback": {"used": False}},
            {"work_package": "WP-2", "role": "architect", "agent_id": "keystone", "state": "completed", "fallback": {"used": False}},
            {"work_package": "WP-3", "role": "implementer", "agent_id": "forge", "state": "completed", "fallback": {"used": False}},
            {"work_package": "WP-4", "role": "test-engineer", "agent_id": "probe", "state": "completed", "fallback": {"used": False}},
            {"work_package": "WP-5", "role": "verifier", "agent_id": "gate", "state": "completed", "fallback": {"used": False}},
            {"work_package": "WP-6", "role": "reviewer", "agent_id": "sentinel", "state": "completed", "fallback": {"used": False}},
            {"work_package": "WP-7", "role": "documentation-reviewer", "agent_id": "archivist", "state": "completed", "fallback": {"used": False}},
        ],
    }


def _t0_work_packages(role: str, capability: str, write_path: str | None = None) -> dict[str, object]:
    return {
        "contract": "v2",
        "contract_version": "v2",
        "work_packages": [
            {
                "id": "WP-T0",
                "owner": "owner-wp-t0",
                "role": role,
                "depends_on": [],
                "capabilities": [capability],
                "scope": {
                    "write": [] if write_path is None else [write_path],
                    "forbidden": [],
                },
                "acceptance_criteria": ["AC-706"],
                "state": "completed",
            }
        ],
    }


def _t0_evidence(work_packages: dict[str, object], role: str) -> dict[str, object]:
    return {
        "contract": "v2",
        "contract_version": "v2",
        "work_packages_sha256": work_packages_sha256(work_packages),
        "required_roles": [role],
        "delegations": [
            {
                "work_package": "WP-T0",
                "role": role,
                "agent_id": "agent-t0",
                "state": "completed",
                "fallback": {"used": False},
            }
        ],
    }


class DelegationContractTests(unittest.TestCase):
    # @spec:AC-701
    def test_skill_and_contract_protect_delegable_orchestrator_capabilities(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "references" / "delegation-contract.md").read_text(encoding="utf-8")
        routing = (ROOT / "references" / "agent-routing.md").read_text(encoding="utf-8")
        lifecycle = (ROOT / "references" / "lifecycle.md").read_text(encoding="utf-8")
        self.assertIn("From T1 onward", skill)
        self.assertIn("must not implement code", skill)
        skill_flat = " ".join(skill.split())
        self.assertIn(
            "canonical marker `Contrato AISDD da feature: v2`, or one of the documented technical aliases below, occupies its own line.",
            skill_flat,
        )
        self.assertIn("não pode ser executado diretamente pelo Orchestrator", contract)
        for content in (skill, routing, lifecycle):
            self.assertIn("BLOCKED", content)
            self.assertTrue("aprov" in content.lower() or "approved" in content.lower())
            self.assertTrue("tentativas" in content or "attempts" in content)
            self.assertNotIn("genuinamente trivial", content)
            self.assertNotIn("genuinely trivial", content)

    # @spec:AC-702
    def test_planner_contract_declares_technical_and_execution_plans(self) -> None:
        planner = (ROOT / "agents" / "planner.toml").read_text(encoding="utf-8")
        plan_standard = (ROOT / "references" / "exec-plan-standard.md").read_text(encoding="utf-8")
        template = (ROOT / "assets" / "templates" / "plan.md").read_text(encoding="utf-8")
        for content in (planner, plan_standard, template):
            normalized = " ".join(content.lower().split())
            self.assertTrue(
                "grafo declarativo" in normalized
                or ("grafo de" in normalized and "depend" in normalized),
                content,
            )
            self.assertIn("owner", normalized)
            self.assertIn("depend", normalized)
            self.assertIn("escopo", normalized)
            self.assertIn("paralel", normalized)
        planner_flat = " ".join(planner.lower().split())
        self.assertIn("t1+ v1", planner_flat)
        self.assertIn("novas specs", planner_flat)
        self.assertIn("v2 por padrão", planner_flat)
        self.assertIn("sem migração automática", planner_flat)
        self.assertIn("plan.md", template)
        self.assertIn("fonte normativa", template.lower())
        self.assertIn("evidence.md", template)
        self.assertNotIn("planner-light", planner)

    # @spec:AC-703
    def test_capability_matrix_and_distinct_test_roles_are_present(self) -> None:
        matrix = (ROOT / "references" / "role-capabilities.md").read_text(encoding="utf-8")
        tester = (ROOT / "agents" / "tester.toml").read_text(encoding="utf-8")
        test_engineer = (ROOT / "agents" / "test-engineer.toml").read_text(encoding="utf-8")
        verifier = (ROOT / "agents" / "verifier.toml").read_text(encoding="utf-8")
        self.assertIn("`test-engineer`", matrix)
        self.assertIn("`verifier`", matrix)
        self.assertIn("tester", tester)
        self.assertIn("Não altere código", test_engineer)
        self.assertIn("Não altere código", verifier)
        self.assertIn("validação final", verifier)
        implementer = (ROOT / "agents" / "implementer.toml").read_text(encoding="utf-8")
        self.assertIn("não crie nem altere testes", implementer)
        self.assertNotIn('"Verifier"', tester)

    # @spec:AC-704
    def test_orders_graph_deterministically_and_rejects_invalid_graphs(self) -> None:
        stable_payload = _valid_work_packages()
        graph = validate_work_packages(stable_payload)
        self.assertTrue(graph["valid"], graph["errors"])
        self.assertEqual(graph["order"], ["WP-1", "WP-2", "WP-3", "WP-4", "WP-5", "WP-6", "WP-7"])

        repeated = validate_work_packages(stable_payload)
        self.assertEqual(repeated, graph)
        self.assertEqual(repeated["valid"], graph["valid"])
        self.assertEqual(repeated["order"], graph["order"])

        reordered = _valid_work_packages()
        reordered_packages = reordered["work_packages"]
        assert isinstance(reordered_packages, list)
        reordered["work_packages"] = list(reversed(reordered_packages))
        self.assertEqual(validate_work_packages(reordered)["order"], graph["order"])

        cycle = _valid_work_packages()
        packages = cycle["work_packages"]
        assert isinstance(packages, list)
        packages[1]["depends_on"] = ["WP-4"]
        self.assertTrue(any("ciclo" in error for error in validate_work_packages(cycle)["errors"]))

        missing = _valid_work_packages()
        missing_packages = missing["work_packages"]
        assert isinstance(missing_packages, list)
        missing_packages[0]["depends_on"] = ["WP-missing"]
        self.assertTrue(any("inexistente" in error for error in validate_work_packages(missing)["errors"]))

        duplicate = _valid_work_packages()
        duplicate_packages = duplicate["work_packages"]
        assert isinstance(duplicate_packages, list)
        duplicate_packages.append(dict(duplicate_packages[0]))
        self.assertTrue(any("duplicado" in error for error in validate_work_packages(duplicate)["errors"]))

        conflict = _valid_work_packages()
        conflict_packages = conflict["work_packages"]
        assert isinstance(conflict_packages, list)
        conflict_packages[6]["depends_on"] = []
        conflict_packages[6]["scope"] = {"write": ["scripts/change.py"], "forbidden": []}
        self.assertTrue(any("conflito de escopo" in error for error in validate_work_packages(conflict)["errors"]))

        glob_conflict = _valid_work_packages()
        glob_packages = glob_conflict["work_packages"]
        assert isinstance(glob_packages, list)
        glob_implementer = next(package for package in glob_packages if package["id"] == "WP-3")
        glob_implementer["scope"] = {"write": ["src/[ab].py"], "forbidden": []}
        glob_packages.append(_package("WP-8", "implementer", "src/[bc].py", ["WP-1"]))
        glob_result = validate_work_packages(glob_conflict)
        self.assertFalse(glob_result["valid"])
        self.assertTrue(
            any(
                "conflito de escopo" in error
                and "src/[ab].py" in error
                and "src/[bc].py" in error
                for error in glob_result["errors"]
            ),
            glob_result["errors"],
        )

    # @spec:AC-704
    def test_partial_prefix_and_bracket_glob_overlap_fail_closed(self) -> None:
        cases = (
            ("src/a?.py", "src/ab*.py"),
            ("src/[ab].py", "src/[bc].py"),
        )
        for left_path, right_path in cases:
            with self.subTest(left_path=left_path, right_path=right_path):
                payload = _valid_work_packages()
                packages = payload["work_packages"]
                assert isinstance(packages, list)
                left_package = next(package for package in packages if package["id"] == "WP-3")
                left_package["scope"] = {"write": [left_path], "forbidden": []}
                packages.append(_package("WP-8", "implementer", right_path, ["WP-1"]))

                result = validate_work_packages(payload)

                self.assertFalse(result["valid"])
                self.assertTrue(
                    any(
                        "conflito de escopo" in error
                        and left_path in error
                        and right_path in error
                        for error in result["errors"]
                    ),
                    result["errors"],
                )

    # @spec:AC-704
    def test_operational_roles_require_their_minimum_capability(self) -> None:
        cases = (
            ("planner", "WP-1", "plan-execution"),
            ("architect", "WP-2", "design"),
            ("implementer", "WP-3", "implement"),
            ("test-engineer", "WP-4", "write-tests"),
            ("verifier", "WP-5", "verify-final"),
            ("reviewer", "WP-6", "review"),
            ("documentation-reviewer", "WP-7", "review-docs"),
        )
        for role, package_id, minimum_capability in cases:
            with self.subTest(role=role):
                payload = _valid_work_packages()
                packages = payload["work_packages"]
                assert isinstance(packages, list)
                package = next(item for item in packages if item["id"] == package_id)
                package["capabilities"] = ["inspect"]

                result = validate_work_packages(payload)

                self.assertFalse(result["valid"])
                self.assertTrue(
                    any(
                        f"role {role} exige capability operacional mínima {minimum_capability}" in error
                        for error in result["errors"]
                    ),
                    result["errors"],
                )

        serial_overlap = _valid_work_packages()
        serial_packages = serial_overlap["work_packages"]
        assert isinstance(serial_packages, list)
        serial_packages[6]["scope"] = {"write": ["scripts/change.py"], "forbidden": []}
        serial_result = validate_work_packages(serial_overlap)
        self.assertTrue(serial_result["valid"], serial_result["errors"])

        non_object = _valid_work_packages()
        non_object["work_packages"] = [None]  # type: ignore[list-item]
        self.assertTrue(any("deve ser um objeto" in error for error in validate_work_packages(non_object)["errors"]))

        wrong_contract = _valid_work_packages()
        wrong_contract["contract_version"] = "v1"
        self.assertTrue(any("contract_version deve ser v2" in error for error in validate_work_packages(wrong_contract)["errors"]))

        unknown_role = _valid_work_packages()
        unknown_role_packages = unknown_role["work_packages"]
        assert isinstance(unknown_role_packages, list)
        unknown_role_packages[1]["role"] = "not-a-role"
        unknown_role_result = validate_work_packages(unknown_role)
        self.assertFalse(unknown_role_result["valid"])
        self.assertTrue(any("role desconhecida" in error for error in unknown_role_result["errors"]))

        absolute_path = _valid_work_packages()
        absolute_packages = absolute_path["work_packages"]
        assert isinstance(absolute_packages, list)
        absolute_packages[3]["scope"] = {"write": ["C:/outside.py"], "forbidden": []}
        self.assertTrue(any("caminho absoluto" in error for error in validate_work_packages(absolute_path)["errors"]))

        traversal_path = _valid_work_packages()
        traversal_packages = traversal_path["work_packages"]
        assert isinstance(traversal_packages, list)
        traversal_packages[3]["scope"] = {"write": ["scripts/../outside.py"], "forbidden": []}
        self.assertTrue(any("traversal" in error for error in validate_work_packages(traversal_path)["errors"]))

        read_only_missing_write = _valid_work_packages()
        read_only_packages = read_only_missing_write["work_packages"]
        assert isinstance(read_only_packages, list)
        read_only_packages[0]["scope"] = {"forbidden": []}
        read_only_result = validate_work_packages(read_only_missing_write)
        self.assertFalse(read_only_result["valid"])
        self.assertTrue(any("scope.write ausente" in error for error in read_only_result["errors"]))

        malformed_scope = _valid_work_packages()
        malformed_packages = malformed_scope["work_packages"]
        assert isinstance(malformed_packages, list)
        malformed_packages[0]["scope"] = None
        malformed_result = validate_work_packages(malformed_scope)
        self.assertFalse(malformed_result["valid"])
        self.assertTrue(any("scope deve ser um objeto" in error for error in malformed_result["errors"]))

        write_empty = _valid_work_packages()
        write_packages = write_empty["work_packages"]
        assert isinstance(write_packages, list)
        write_packages[3]["scope"] = {"write": [], "forbidden": []}
        write_result = validate_work_packages(write_empty)
        self.assertFalse(write_result["valid"])
        self.assertTrue(any("escopo de escrita ausente" in error for error in write_result["errors"]))

        read_only_write = _valid_work_packages()
        read_only_write_packages = read_only_write["work_packages"]
        assert isinstance(read_only_write_packages, list)
        read_only_write_packages[0]["scope"] = {"write": ["tests/read-only.py"], "forbidden": []}
        read_only_write_result = validate_work_packages(read_only_write)
        self.assertFalse(read_only_write_result["valid"])
        self.assertTrue(any("role read-only exige scope.write vazio" in error for error in read_only_write_result["errors"]))

        non_canonical_state = _valid_work_packages()
        non_canonical_packages = non_canonical_state["work_packages"]
        assert isinstance(non_canonical_packages, list)
        non_canonical_packages[3]["state"] = "done"
        non_canonical_result = validate_work_packages(non_canonical_state)
        self.assertFalse(non_canonical_result["valid"])
        self.assertTrue(any("estado inválido" in error for error in non_canonical_result["errors"]))

    # @spec:AC-704
    def test_work_package_role_is_explicit_even_when_owner_role_is_present(self) -> None:
        payload = _valid_work_packages()
        packages = payload["work_packages"]
        assert isinstance(packages, list)
        planner = next(package for package in packages if package["id"] == "WP-1")
        planner.pop("role")
        planner["owner"] = {"id": "owner-wp-1", "role": "planner"}

        result = validate_work_packages(payload)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any("WP WP-1" in error and "role ausente" in error for error in result["errors"]),
            result["errors"],
        )

        mismatched_owner_role = _valid_work_packages()
        mismatched_packages = mismatched_owner_role["work_packages"]
        assert isinstance(mismatched_packages, list)
        mismatched_planner = next(package for package in mismatched_packages if package["id"] == "WP-1")
        mismatched_planner["owner"] = {"id": "owner-wp-1", "role": "implementer"}
        mismatch_result = validate_work_packages(mismatched_owner_role)
        self.assertFalse(mismatch_result["valid"])
        self.assertTrue(
            any("owner.role não corresponde" in error for error in mismatch_result["errors"]),
            mismatch_result["errors"],
        )

    # @spec:AC-704
    def test_minimum_execution_dependencies_fail_closed(self) -> None:
        cases = (
            ("verifier", "WP-5"),
            ("reviewer", "WP-6"),
            ("documentation-reviewer", "WP-7"),
            ("test-engineer", "WP-4"),
        )
        for role, package_id in cases:
            with self.subTest(role=role):
                payload = _valid_work_packages()
                packages = payload["work_packages"]
                assert isinstance(packages, list)
                package = next(item for item in packages if item["id"] == package_id)
                package["depends_on"] = []

                result = validate_work_packages(payload)

                self.assertFalse(result["valid"])
                self.assertTrue(
                    any(
                        role in error and "deve depender transitivamente" in error
                        for error in result["errors"]
                    ),
                    result["errors"],
                )

    # @spec:AC-704
    def test_scalar_dependency_fields_are_rejected(self) -> None:
        for field in ("depends_on", "depends-on", "dependencies"):
            with self.subTest(field=field):
                payload = _valid_work_packages()
                packages = payload["work_packages"]
                assert isinstance(packages, list)
                package = next(item for item in packages if item["id"] == "WP-5")
                package.pop("depends_on", None)
                package[field] = "WP-4"

                result = validate_work_packages(payload)

                self.assertFalse(result["valid"])
                self.assertTrue(
                    any("depends_on deve ser uma lista de IDs" in error for error in result["errors"]),
                    result["errors"],
                )

    # @spec:AC-704
    def test_combined_dependency_aliases_are_rejected(self) -> None:
        for aliases in (
            ("depends_on", "depends-on"),
            ("depends_on", "dependencies"),
            ("depends-on", "dependencies"),
        ):
            with self.subTest(aliases=aliases):
                payload = _valid_work_packages()
                packages = payload["work_packages"]
                assert isinstance(packages, list)
                package = next(item for item in packages if item["id"] == "WP-5")
                package.pop("depends_on")
                package[aliases[0]] = ["WP-4"]
                package[aliases[1]] = ["WP-4"]

                result = validate_work_packages(payload)

                self.assertFalse(result["valid"])
                self.assertTrue(
                    any("aliases de dependência são mutuamente exclusivos" in error for error in result["errors"]),
                    result["errors"],
                )

    # @spec:AC-704
    def test_ambiguous_dependency_alias_with_scalar_fails_closed(self) -> None:
        payload = _valid_work_packages()
        packages = payload["work_packages"]
        assert isinstance(packages, list)
        package = next(item for item in packages if item["id"] == "WP-5")
        package.pop("depends_on")
        package["depends_on"] = "WP-4"
        package["dependencies"] = ["WP-4"]

        result = validate_work_packages(payload)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any("aliases de depend" in error and "mutuamente exclusivos" in error for error in result["errors"]),
            result["errors"],
        )
        self.assertTrue(
            any("depends_on deve ser uma lista de IDs" in error for error in result["errors"]),
            result["errors"],
        )

    # @spec:AC-704
    def test_transitive_dependencies_pass_and_reviewers_can_run_in_parallel(self) -> None:
        transitive = _valid_work_packages()
        packages = transitive["work_packages"]
        assert isinstance(packages, list)
        by_id = {package["id"]: package for package in packages}
        by_id["WP-4"]["depends_on"] = ["WP-8"]
        by_id["WP-5"]["depends_on"] = ["WP-9"]
        by_id["WP-6"]["depends_on"] = ["WP-10"]
        by_id["WP-7"]["depends_on"] = ["WP-11"]
        packages.extend(
            [
                _package("WP-8", "planner", None, ["WP-3"]),
                _package("WP-9", "planner", None, ["WP-4"]),
                _package("WP-10", "planner", None, ["WP-5"]),
                _package("WP-11", "planner", None, ["WP-5"]),
            ]
        )

        transitive_result = validate_work_packages(transitive)
        self.assertTrue(transitive_result["valid"], transitive_result["errors"])

        parallel = _valid_work_packages()
        parallel_packages = parallel["work_packages"]
        assert isinstance(parallel_packages, list)
        parallel_by_id = {package["id"]: package for package in parallel_packages}
        parallel_by_id["WP-7"]["depends_on"] = ["WP-5"]
        parallel_result = validate_work_packages(parallel)

        self.assertTrue(parallel_result["valid"], parallel_result["errors"])
        self.assertEqual(parallel_by_id["WP-6"]["depends_on"], ["WP-5"])
        self.assertEqual(parallel_by_id["WP-7"]["depends_on"], ["WP-5"])
        self.assertNotIn("WP-6", parallel_by_id["WP-7"]["depends_on"])
        self.assertNotIn("WP-7", parallel_by_id["WP-6"]["depends_on"])
        order = parallel_result["order"]
        self.assertLess(order.index("WP-5"), order.index("WP-6"))
        self.assertLess(order.index("WP-5"), order.index("WP-7"))

    # @spec:AC-705
    def test_legacy_and_explicit_v1_do_not_require_v2_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            feature = repo / "specs" / "legacy"
            feature.mkdir(parents=True)
            (feature / "spec.md").write_text("# Legacy\n\n- AC-705\n", encoding="utf-8")
            (feature / "plan.md").write_text("# Plan\n\n- T-705 (AC-705)\n", encoding="utf-8")
            (feature / "status.md").write_text("# Status\n", encoding="utf-8")
            (feature / "evidence.md").write_text("@spec:AC-705\n", encoding="utf-8")
            legacy_mapping = {
                "AC-705": [
                    {
                        "path": "tests/test_legacy.py",
                        "line": 1,
                        "file_sha256": "legacy-fixture",
                        "skipped": False,
                    }
                ]
            }
            (feature / "verification.json").write_text(
                json.dumps(
                    {
                        "criteria": ["AC-705"],
                        "test_map": legacy_mapping,
                        "mapping_sha256": hashlib.sha256(
                            json.dumps(
                                legacy_mapping,
                                ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":"),
                            ).encode("utf-8")
                        ).hexdigest(),
                        "passed": True,
                        "exit_code": 0,
                    }
                ),
                encoding="utf-8",
            )
            legacy_artifacts = tuple(
                feature / name
                for name in ("spec.md", "plan.md", "status.md", "evidence.md", "verification.json")
            )
            legacy_bytes_before_validation = {
                path: path.read_bytes() for path in legacy_artifacts
            }
            self.assertFalse(is_v2_feature(feature))
            self.assertEqual(validate_v2_feature(feature), [])
            self.assertEqual(validate_feature(repo, feature.relative_to(repo), full_map=legacy_mapping), [])
            self.assertEqual(
                {path: path.read_bytes() for path in legacy_artifacts},
                legacy_bytes_before_validation,
            )

            (feature / "status.md").write_text("Contrato AISDD da feature: v1\n", encoding="utf-8")
            self.assertFalse(is_v2_feature(feature))
            self.assertEqual(validate_v2_feature(feature), [])
            self.assertEqual(validate_feature(repo, feature.relative_to(repo), full_map=legacy_mapping), [])

            (feature / "status.md").write_text("Contrato AISDD da feature: v2\n", encoding="utf-8")
            self.assertTrue(is_v2_feature(feature))
            self.assertTrue(any("work-packages.json" in error for error in validate_v2_feature(feature)))
            self.assertTrue(validate_feature(repo, feature.relative_to(repo)))

    # @spec:AC-705
    def test_v2_marker_aliases_are_line_scoped_and_opt_in(self) -> None:
        markers = (
            "Contrato AISDD da feature: v2",
            "Contrato AISDD: 2",
            "AISDD contract=2",
            "AISDD-contract: v2",
            "AISDD_contract: v2",
            "delegation contract: v2",
            "delegation-contract=2",
            "delegation_contract: v2",
            "contract: v2",
            "contract-version=2",
            "contract_version: v2",
        )
        invalid_markers = (
            "Contrato AISDD da feature: v2 extra",
            "Contrato AISDD da feature: v2.0",
            "Contrato AISDD da feature: v2 em texto",
            "A documentação menciona Contrato AISDD da feature: v2",
            "contract: v2 extra",
            "contract: v2.0",
            "contract: v2, texto adicional",
        )
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "feature"
            feature.mkdir()
            status = feature / "status.md"
            for marker in markers:
                status.write_text(marker + "\n", encoding="utf-8")
                self.assertTrue(is_v2_feature(feature), marker)

            for marker in invalid_markers:
                status.write_text(marker + "\n", encoding="utf-8")
                self.assertFalse(is_v2_feature(feature), marker)

            status.write_text(
                "```text\nContrato AISDD da feature: v2\n```\n",
                encoding="utf-8",
            )
            self.assertFalse(is_v2_feature(feature))

            status.write_text(
                "```text\nContrato AISDD da feature: v2\n```\n"
                "Contrato AISDD da feature: v2\n",
                encoding="utf-8",
            )
            self.assertTrue(is_v2_feature(feature))

            for hidden_marker in (
                "~~~text\nContrato AISDD da feature: v2\n~~~\n",
                "    Contrato AISDD da feature: v2\n",
            ):
                with self.subTest(hidden_marker=hidden_marker):
                    status.write_text(hidden_marker, encoding="utf-8")
                    self.assertFalse(is_v2_feature(feature))

    # @spec:AC-707
    def test_feature_class_ignores_fenced_and_historical_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "feature"
            feature.mkdir()
            (feature / "spec.md").write_text(
                "~~~text\n"
                "Classe: T9\n"
                "~~~\n"
                "## Histórico\n"
                "Classe: T8\n"
                "    Classe: T8\n"
                "## Estado atual\n"
                "Classe: T3\n",
                encoding="utf-8",
            )

            self.assertEqual(extract_feature_class(feature), "T3")

    # @spec:AC-707
    def test_v2_requires_present_valid_feature_class(self) -> None:
        for class_declaration, expected_error in (("", "classe da feature ausente"), ("Classe: T9\n", "classe da feature inválida")):
            with self.subTest(class_declaration=class_declaration or "ausente"):
                with tempfile.TemporaryDirectory() as temporary:
                    feature = Path(temporary) / "feature"
                    feature.mkdir()
                    (feature / "spec.md").write_text(
                        "Contrato AISDD da feature: v2\n" + class_declaration,
                        encoding="utf-8",
                    )
                    work_packages = _valid_work_packages()
                    (feature / "work-packages.json").write_text(json.dumps(work_packages), encoding="utf-8")
                    (feature / "delegation-evidence.json").write_text(
                        json.dumps(_valid_evidence(work_packages)),
                        encoding="utf-8",
                    )
                    errors = validate_v2_feature(feature)
                    self.assertTrue(any(expected_error in error for error in errors), errors)

    # @spec:AC-707
    def test_v2_cli_fails_closed_when_delegation_evidence_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "feature"
            feature.mkdir()
            (feature / "spec.md").write_text(
                "Contrato AISDD da feature: v2\nClasse: T3\n",
                encoding="utf-8",
            )
            (feature / "work-packages.json").write_text(
                json.dumps(_valid_work_packages()),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "delegation_contract.py"), str(feature), "--json"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["valid"])
            self.assertFalse(payload["evidence"]["valid"])
            self.assertTrue(
                any("delegation-evidence.json ausente ou não encontrado" in error for error in payload["evidence"]["errors"]),
                payload,
            )

    # @spec:AC-706
    def test_fallback_false_is_clean_and_rejects_incompatible_fields(self) -> None:
        work_packages = _valid_work_packages()
        clean = _valid_evidence(work_packages)
        clean["delegations"][2]["fallback"] = {"used": False}
        accepted = validate_delegation_evidence(work_packages, clean, "T3")
        self.assertTrue(accepted["valid"], accepted["errors"])

        incompatible_fields = {
            "direct_work": {"scope": ["scripts/change.py"], "result": "registro"},
            "reason": "agente indisponível",
            "attempts": [{"result": "not available"}],
            "approved": True,
        }
        for field, value in incompatible_fields.items():
            with self.subTest(field=field):
                evidence = _valid_evidence(work_packages)
                evidence["delegations"][2]["fallback"] = {"used": False, field: value}
                result = validate_delegation_evidence(work_packages, evidence, "T3")
                self.assertFalse(result["valid"])
                self.assertTrue(
                    any("fallback.used=false" in error and field in error for error in result["errors"]),
                    result["errors"],
                )

    # @spec:AC-706
    def test_read_only_fallback_accepts_read_and_execute_for_verifier_and_reviewer(self) -> None:
        for package_id, role in (("WP-5", "verifier"), ("WP-6", "reviewer")):
            for operation, path in (("execute", "scripts/check.py"), ("read", "tests/contract.py")):
                with self.subTest(package_id=package_id, role=role, operation=operation):
                    work_packages = _valid_work_packages()
                    packages = work_packages["work_packages"]
                    assert isinstance(packages, list)
                    package = next(item for item in packages if item["id"] == package_id)
                    package["scope"] = {
                        "write": [],
                        "read": ["tests/"],
                        "execute": ["scripts/"],
                        "forbidden": ["runtime/"],
                    }

                    evidence = _valid_evidence(work_packages)
                    entries = evidence["delegations"]
                    assert isinstance(entries, list)
                    entry = next(item for item in entries if item["work_package"] == package_id)
                    entry["fallback"] = {
                        "used": True,
                        "approved": True,
                        "reason": "role especializada indisponivel",
                        "agent_unavailable": True,
                        "attempts": [{"result": "role unavailable"}],
                        "direct_work": {
                            "operation": operation,
                            "scope": [path],
                            "result": "fallback read-only registrado",
                        },
                    }

                    result = validate_delegation_evidence(work_packages, evidence, "T3")
                    self.assertTrue(result["valid"], result["errors"])

    # @spec:AC-706
    def test_read_only_fallback_rejects_missing_or_write_operation_scope_and_path_violations(self) -> None:
        cases = (
            (
                "operation ausente",
                "read",
                {"write": [], "read": ["tests/"], "execute": ["scripts/"], "forbidden": ["runtime/"]},
                "tests/contract.py",
                {},
                "direct_work.operation explicita",
            ),
            (
                "operation write",
                "write",
                {"write": [], "read": ["tests/"], "execute": ["scripts/"], "forbidden": ["runtime/"]},
                "tests/contract.py",
                {},
                "escrita direta proibida",
            ),
            (
                "escrita direta",
                "read",
                {"write": [], "read": ["tests/"], "execute": ["scripts/"], "forbidden": ["runtime/"]},
                "tests/contract.py",
                {"write": ["tests/contract.py"]},
                "escrita direta proibida",
            ),
            (
                "scope.read ausente",
                "read",
                {"write": [], "execute": ["scripts/"], "forbidden": ["runtime/"]},
                "tests/contract.py",
                {},
                "scope.read ausente",
            ),
            (
                "scope.execute ausente",
                "execute",
                {"write": [], "read": ["tests/"], "forbidden": ["runtime/"]},
                "scripts/check.py",
                {},
                "scope.execute ausente",
            ),
            (
                "caminho fora do escopo",
                "read",
                {"write": [], "read": ["tests/"], "execute": ["scripts/"], "forbidden": ["runtime/"]},
                "docs/outside.md",
                {},
                "trabalho direto fora do escopo:",
            ),
            (
                "caminho forbidden",
                "read",
                {"write": [], "read": ["tests/allowed/"], "execute": ["scripts/"], "forbidden": ["runtime/"]},
                "runtime/config.json",
                {},
                "trabalho direto em escopo proibido",
            ),
        )

        for package_id in ("WP-5", "WP-6"):
            for label, operation, scope, path, direct_fields, expected_error in cases:
                with self.subTest(package_id=package_id, case=label):
                    work_packages = _valid_work_packages()
                    packages = work_packages["work_packages"]
                    assert isinstance(packages, list)
                    package = next(item for item in packages if item["id"] == package_id)
                    package["scope"] = scope

                    evidence = _valid_evidence(work_packages)
                    entries = evidence["delegations"]
                    assert isinstance(entries, list)
                    entry = next(item for item in entries if item["work_package"] == package_id)
                    direct_work = {
                        "scope": [path],
                        "result": "fallback read-only registrado",
                    }
                    if label != "operation ausente":
                        direct_work["operation"] = operation
                    direct_work.update(direct_fields)
                    entry["fallback"] = {
                        "used": True,
                        "approved": True,
                        "reason": "role especializada indisponivel",
                        "agent_unavailable": True,
                        "attempts": [{"result": "role unavailable"}],
                        "direct_work": direct_work,
                    }

                    result = validate_delegation_evidence(work_packages, evidence, "T3")
                    self.assertFalse(result["valid"], result["errors"])
                    self.assertTrue(
                        any(expected_error in error for error in result["errors"]),
                        result["errors"],
                    )

    # @spec:AC-706
    def test_implementer_fallback_keeps_legacy_scope_write_contract(self) -> None:
        work_packages = _valid_work_packages()
        evidence = _valid_evidence(work_packages)
        entries = evidence["delegations"]
        assert isinstance(entries, list)
        entry = next(item for item in entries if item["work_package"] == "WP-3")
        entry["fallback"] = {
            "used": True,
            "approved": True,
            "reason": "implementer indisponivel",
            "agent_unavailable": True,
            "attempts": [{"result": "role unavailable"}],
            "direct_work": {
                "scope": ["scripts/change.py"],
                "result": "implementacao direta registrada",
            },
        }

        result = validate_delegation_evidence(work_packages, evidence, "T3")
        self.assertTrue(result["valid"], result["errors"])

    # @spec:AC-706
    def test_fallback_must_be_an_object_with_boolean_used(self) -> None:
        for malformed in (None, [], {"used": "false"}):
            with self.subTest(fallback=malformed):
                work_packages = _valid_work_packages()
                evidence = _valid_evidence(work_packages)
                evidence["delegations"][2]["fallback"] = malformed

                result = validate_delegation_evidence(work_packages, evidence, "T3")

                self.assertFalse(result["valid"])
                self.assertTrue(
                    any("fallback" in error and ("inválido" in error or "booleano" in error) for error in result["errors"]),
                    result["errors"],
                )

    # @spec:AC-706
    def test_evidence_requires_fallback_object_on_every_delegation_entry(self) -> None:
        work_packages = _valid_work_packages()
        baseline = _valid_evidence(work_packages)
        baseline_entries = baseline["delegations"]
        assert isinstance(baseline_entries, list)

        for index in range(len(baseline_entries)):
            with self.subTest(entry=index):
                evidence = _valid_evidence(work_packages)
                entries = evidence["delegations"]
                assert isinstance(entries, list)
                entry = entries[index]
                assert isinstance(entry, dict)
                entry.pop("fallback")

                result = validate_delegation_evidence(work_packages, evidence, "T3")

                self.assertFalse(result["valid"])
                self.assertTrue(
                    any("fallback ausente" in error for error in result["errors"]),
                    result["errors"],
                )

    # @spec:AC-706
    def test_t0_requires_non_delegable_declaration_or_specialized_role(self) -> None:
        orchestrator_packages = _t0_work_packages("orchestrator", "coordinate")
        orchestrator_evidence = _t0_evidence(orchestrator_packages, "orchestrator")
        rejected = validate_delegation_evidence(orchestrator_packages, orchestrator_evidence, "T0")
        self.assertFalse(rejected["valid"])
        self.assertTrue(any("orchestrator/coordinate" in error for error in rejected["errors"]), rejected["errors"])

        for reason in ("trivial", "silêncio", "x", "ok", "no work", ""):
            with self.subTest(reason=reason or "ausente"):
                rejected_reason = json.loads(json.dumps(orchestrator_evidence))
                rejected_reason["mechanical_non_delegable"] = {
                    "approved": True,
                    "reason": reason,
                }
                result = validate_delegation_evidence(
                    orchestrator_packages,
                    rejected_reason,
                    "T0",
                )
                self.assertFalse(result["valid"])
                self.assertTrue(
                    any("mechanical_non_delegable" in error for error in result["errors"]),
                    result["errors"],
                )

        declared = json.loads(json.dumps(orchestrator_evidence))
        declared["mechanical_non_delegable"] = {
            "approved": True,
            "reason": "alteração mecânica limitada a metadados; nenhuma capacidade delegável foi executada",
        }
        accepted_declaration = validate_delegation_evidence(orchestrator_packages, declared, "T0")
        self.assertTrue(accepted_declaration["valid"], accepted_declaration["errors"])

        specialized_packages = _t0_work_packages("test-engineer", "write-tests", "tests/t0.py")
        specialized_evidence = _t0_evidence(specialized_packages, "test-engineer")
        accepted_role = validate_delegation_evidence(specialized_packages, specialized_evidence, "T0")
        self.assertTrue(accepted_role["valid"], accepted_role["errors"])

    # @spec:AC-706
    def test_evidence_requires_role_coverage_independence_and_audited_fallback(self) -> None:
        work_packages = _valid_work_packages()
        evidence = _valid_evidence(work_packages)
        result = validate_delegation_evidence(work_packages, evidence, "T3")
        self.assertTrue(result["valid"], result["errors"])

        t2_without_documentary_impact = _valid_evidence(work_packages)
        t2_without_documentary_impact["required_roles"] = [
            "planner",
            "architect",
            "implementer",
            "test-engineer",
            "verifier",
            "reviewer",
        ]
        t2_result = validate_delegation_evidence(work_packages, t2_without_documentary_impact, "T2")
        self.assertTrue(t2_result["valid"], t2_result["errors"])

        t2_documentary_required = _valid_evidence(work_packages)
        t2_documentary_required["required_roles"] = [
            "planner",
            "architect",
            "implementer",
            "test-engineer",
            "verifier",
            "reviewer",
            "documentation-reviewer",
        ]
        t2_documentary_required["delegations"] = [
            entry
            for entry in t2_documentary_required["delegations"]
            if entry["role"] != "documentation-reviewer"
        ]
        t2_documentary_result = validate_delegation_evidence(work_packages, t2_documentary_required, "T2")
        self.assertTrue(any("role obrigatória ausente: documentation-reviewer" in error for error in t2_documentary_result["errors"]))

        t3_missing_documentation_reviewer = _valid_evidence(work_packages)
        t3_missing_documentation_reviewer["delegations"] = [
            entry
            for entry in t3_missing_documentation_reviewer["delegations"]
            if entry["role"] != "documentation-reviewer"
        ]
        t3_result = validate_delegation_evidence(work_packages, t3_missing_documentation_reviewer, "T3")
        self.assertTrue(any("role obrigatória ausente: documentation-reviewer" in error for error in t3_result["errors"]))

        missing_verifier = json.loads(json.dumps(evidence))
        missing_verifier["delegations"] = [entry for entry in missing_verifier["delegations"] if entry["role"] != "verifier"]
        missing_verifier["required_roles"] = ["implementer", "test-engineer", "verifier", "reviewer"]
        result = validate_delegation_evidence(work_packages, missing_verifier, "T3")
        self.assertTrue(any("verifier" in error for error in result["errors"]))

        same_agent = json.loads(json.dumps(evidence))
        same_agent["delegations"][3]["agent_id"] = "gate"
        result = validate_delegation_evidence(work_packages, same_agent, "T3")
        self.assertTrue(any("independentes" in error for error in result["errors"]))

        fallback = json.loads(json.dumps(evidence))
        fallback["delegations"][2]["fallback"] = {"used": True, "approved": True, "reason": "runtime indisponível", "agent_unavailable": True, "attempts": [{"result": "not available"}], "direct_work": {"scope": ["scripts/change.py"], "result": "implementação direta registrada"}}
        self.assertTrue(validate_delegation_evidence(work_packages, fallback, "T3")["valid"])
        fallback["delegations"][2]["fallback"].pop("attempts")
        result = validate_delegation_evidence(work_packages, fallback, "T3")
        self.assertTrue(any("tentativas" in error for error in result["errors"]))

        reduced_roles = _valid_evidence(work_packages)
        reduced_roles["required_roles"] = ["implementer"]
        result = validate_delegation_evidence(work_packages, reduced_roles, "T3")
        self.assertTrue(any("reduz o mínimo" in error for error in result["errors"]))

        missing_role = _valid_evidence(work_packages)
        missing_role["delegations"][2].pop("role")
        result = validate_delegation_evidence(work_packages, missing_role, "T3")
        self.assertTrue(any("role ausente" in error for error in result["errors"]))

        missing_agent = _valid_evidence(work_packages)
        missing_agent["delegations"][2].pop("agent_id")
        result = validate_delegation_evidence(work_packages, missing_agent, "T3")
        self.assertTrue(any("agent_id ausente" in error for error in result["errors"]))

        open_state = _valid_evidence(work_packages)
        open_state["delegations"][2]["state"] = "pending"
        result = validate_delegation_evidence(work_packages, open_state, "T3")
        self.assertTrue(any("estado deve ser completed" in error for error in result["errors"]))

        mismatched_packages = _valid_work_packages()
        mismatched_package_list = mismatched_packages["work_packages"]
        assert isinstance(mismatched_package_list, list)
        mismatched_package_list[3]["state"] = "pending"
        result = validate_delegation_evidence(mismatched_packages, _valid_evidence(work_packages), "T3")
        self.assertTrue(any("estado não corresponde" in error for error in result["errors"]))

        outside_direct = _valid_evidence(work_packages)
        outside_direct["delegations"][2]["fallback"] = {
            "used": True,
            "approved": True,
            "reason": "role indisponível",
            "agent_unavailable": True,
            "attempts": [{"result": "indisponível"}],
            "direct_work": {"scope": ["docs/change.md"], "result": "registrado"},
        }
        result = validate_delegation_evidence(work_packages, outside_direct, "T3")
        self.assertTrue(any("fora do escopo" in error for error in result["errors"]))

        graph_broken = _valid_work_packages()
        graph_packages = graph_broken["work_packages"]
        assert isinstance(graph_packages, list)
        graph_packages[3]["depends_on"] = ["WP-missing"]
        result = validate_delegation_evidence(graph_broken, _valid_evidence(work_packages), "T3")
        self.assertTrue(any("work-packages" in error and "inexistente" in error for error in result["errors"]))

    # @spec:AC-706
    def test_evidence_rejects_trivial_or_silent_fallback_reasons(self) -> None:
        for reason in ("trivial", "silêncio", "x", "ok", "no work"):
            with self.subTest(reason=reason):
                work_packages = _valid_work_packages()
                evidence = _valid_evidence(work_packages)
                evidence["delegations"][2]["fallback"] = {
                    "used": True,
                    "approved": True,
                    "reason": reason,
                    "agent_unavailable": True,
                    "attempts": [{"result": "not available"}],
                    "direct_work": {
                        "scope": ["scripts/change.py"],
                        "result": "implementacao direta registrada",
                    },
                }
                result = validate_delegation_evidence(work_packages, evidence, "T3")
                self.assertFalse(result["valid"])
                self.assertTrue(
                    any("motivo de fallback trivial" in error for error in result["errors"]),
                    result["errors"],
                )

    # @spec:AC-706
    def test_evidence_rejects_malformed_or_non_empty_blockers(self) -> None:
        malformed = _valid_work_packages()
        malformed_evidence = _valid_evidence(malformed)
        malformed_evidence["blockers"] = {"id": "B-706"}
        malformed_result = validate_delegation_evidence(malformed, malformed_evidence, "T3")
        self.assertFalse(malformed_result["valid"])
        self.assertTrue(any("blockers deve ser uma lista vazia" in error for error in malformed_result["errors"]))

        non_empty = _valid_work_packages()
        non_empty_evidence = _valid_evidence(non_empty)
        non_empty_evidence["blockers"] = [{"id": "B-706", "state": "open"}]
        non_empty_result = validate_delegation_evidence(non_empty, non_empty_evidence, "T3")
        self.assertFalse(non_empty_result["valid"])
        self.assertTrue(any("blockers deve estar vazio" in error for error in non_empty_result["errors"]))

    # @spec:AC-706
    def test_evidence_rejects_agent_id_reuse_between_implementer_and_reviewer(self) -> None:
        work_packages = _valid_work_packages()
        evidence = _valid_evidence(work_packages)
        evidence["delegations"][5]["agent_id"] = evidence["delegations"][2]["agent_id"]
        result = validate_delegation_evidence(work_packages, evidence, "T3")
        self.assertFalse(result["valid"])
        shared_errors = [error for error in result["errors"] if "compartilham agent_id" in error]
        self.assertTrue(shared_errors, result["errors"])
        self.assertIn("implementer", shared_errors[0])
        self.assertIn("reviewer", shared_errors[0])

    # @spec:AC-706
    def test_t4_evidence_requires_human_approval(self) -> None:
        work_packages = _valid_work_packages()
        evidence = _valid_evidence(work_packages)
        missing_approval = validate_delegation_evidence(work_packages, evidence, "T4")
        self.assertFalse(missing_approval["valid"])
        self.assertTrue(any("T4 exige human_approval auditável" in error for error in missing_approval["errors"]))

        evidence["human_approval"] = {
            "approved": True,
            "approver": "human-reviewer",
            "timestamp": "2026-08-07T12:00:00Z",
            "reference": "approval-706",
        }
        approved = validate_delegation_evidence(work_packages, evidence, "T4")
        self.assertTrue(approved["valid"], approved["errors"])

    # @spec:AC-709
    def test_contract_documents_correction_loop_and_fail_closed_completion(self) -> None:
        contract = (ROOT / "references" / "delegation-contract.md").read_text(encoding="utf-8")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Planner -> Implementer -> Test Engineer -> Verifier -> Reviewer", contract)
        self.assertIn("novo Work Package de correção", contract)
        self.assertIn("nunca em loop infinito", contract)
        self.assertIn("aprovação explícita", contract)
        self.assertIn("Test Engineer", contract)
        self.assertIn("novo Work Package de correção", contract)
        self.assertIn("BLOCKED", skill)
        self.assertNotIn("genuinely trivial", skill)
        self.assertIn("final validation", skill)

    # @spec:AC-711
    def test_adr_readme_and_templates_record_v1_v2_migration(self) -> None:
        adr = (ROOT / "docs" / "architecture" / "decisions" / "ADR-0001-delegation-contract-v2.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        contract = (ROOT / "references" / "delegation-contract.md").read_text(encoding="utf-8")
        planner = (ROOT / "agents" / "planner.toml").read_text(encoding="utf-8")
        routing = (ROOT / "references" / "agent-routing.md").read_text(encoding="utf-8")
        classification = (ROOT / "references" / "classification.md").read_text(encoding="utf-8")
        lifecycle = (ROOT / "references" / "lifecycle.md").read_text(encoding="utf-8")
        lifecycle_flat = " ".join(lifecycle.split())
        plan_template = (ROOT / "assets" / "templates" / "plan.md").read_text(encoding="utf-8")
        evidence_template = (ROOT / "assets" / "templates" / "evidence.md").read_text(encoding="utf-8")
        feature_plan = (ROOT / "specs" / "mandatory-delegation-contract" / "plan.md").read_text(encoding="utf-8")
        self.assertIn("Estratégia de migração v1/v2", adr)
        readme_flat = " ".join(readme.lower().split())
        self.assertIn("novas specs", readme_flat)
        self.assertIn("v2 por padrão", readme_flat)
        self.assertIn("não há migração automática", readme_flat)
        self.assertIn("Contrato AISDD da feature: v2", contract)
        self.assertIn("T1+ v1", planner)
        self.assertIn("Reviewer e Documentation Reviewer", routing)
        self.assertIn("Verifier e podem executar em paralelo", routing)
        self.assertIn("documentation-reviewer", routing)
        self.assertIn("Documentation Reviewer somente se houver impacto documental", classification)
        self.assertIn("T3/T4", classification)
        self.assertIn("Test Engineer", lifecycle)
        self.assertIn("Reviewer || Documentation Reviewer", lifecycle_flat)
        self.assertIn("novo WP de corre", lifecycle)
        self.assertIn("Work Packages e execução delegada", plan_template)
        self.assertIn("Owner", plan_template)
        self.assertIn("Paralelização/condição", plan_template)
        self.assertIn("`plan.md` é a fonte normativa", plan_template)
        self.assertIn("`evidence.md` apenas", plan_template)
        self.assertIn("Contrato v2", evidence_template)
        self.assertIn("Cada Work Package tem exatamente um owner", feature_plan)
        self.assertIn("`plan.md` é a fonte normativa do grafo declarativo", feature_plan)
        feature_evidence = (ROOT / "specs" / "mandatory-delegation-contract" / "evidence.md").read_text(encoding="utf-8")
        self.assertIn("não redefine o grafo", feature_evidence)
        self.assertNotIn("AC-707–AC-708", feature_plan)

    # @spec:AC-705
    def test_create_feature_defaults_to_v2_and_explicit_v1_is_legacy_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            v2 = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "create_feature.py"), str(repo), "New Feature", "--class", "T1"],
                check=True,
                capture_output=True,
                text=True,
            )
            v2_feature = Path(v2.stdout.strip())
            self.assertTrue(is_v2_feature(v2_feature))
            self.assertIn("Contrato AISDD da feature: v2", (v2_feature / "plan.md").read_text(encoding="utf-8"))
            self.assertIn("Contrato AISDD da feature: v2", (v2_feature / "status.md").read_text(encoding="utf-8"))
            work_packages = json.loads((v2_feature / "work-packages.json").read_text(encoding="utf-8"))
            evidence = json.loads((v2_feature / "delegation-evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(work_packages["status"], "incomplete")
            self.assertEqual(evidence["status"], "incomplete")
            self.assertTrue(validate_work_packages(work_packages)["errors"])

            v1 = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "create_feature.py"), str(repo), "Legacy", "--class", "T1", "--contract", "v1"],
                check=True,
                capture_output=True,
                text=True,
            )
            v1_feature = Path(v1.stdout.strip())
            self.assertFalse(is_v2_feature(v1_feature))
            self.assertIn("Contrato AISDD da feature: v1", (v1_feature / "plan.md").read_text(encoding="utf-8"))
            self.assertFalse((v1_feature / "work-packages.json").exists())
            self.assertFalse((v1_feature / "delegation-evidence.json").exists())

    # @spec:AC-707
    def test_contract_cli_reads_class_from_feature_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "feature"
            feature.mkdir()
            work_packages = _valid_work_packages()
            (feature / "spec.md").write_text("# Feature\n\nClasse: T3\n", encoding="utf-8")
            (feature / "plan.md").write_text("Classe: T3\n", encoding="utf-8")
            (feature / "status.md").write_text("Classe: T3\n", encoding="utf-8")
            (feature / "work-packages.json").write_text(json.dumps(work_packages), encoding="utf-8")
            (feature / "delegation-evidence.json").write_text(json.dumps(_valid_evidence(work_packages)), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "delegation_contract.py"), str(feature), "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["class"], "T3")
            self.assertTrue(payload["valid"])


if __name__ == "__main__":
    unittest.main()
