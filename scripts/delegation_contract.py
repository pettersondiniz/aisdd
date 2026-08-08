#!/usr/bin/env python3
"""Validate the AISDD delegation contract v2 without executing agents."""
from __future__ import annotations

import argparse
from collections import defaultdict
import fnmatch
import hashlib
import heapq
import json
from pathlib import Path
import re
from typing import Any
import unicodedata


CONTRACT_V2 = "v2"
CONTRACT_VERSION_KEYS = ("contract", "contract_version")
DEPENDENCY_ALIASES = ("depends_on", "depends-on", "dependencies")
VALID_STATES = {
    "pending",
    "ready",
    "in_progress",
    "blocked",
    "completed",
    "failed",
    "cancelled",
}
ROLE_ALIASES = {
    "tester": "test-engineer",
    "test_engineer": "test-engineer",
    "testengineer": "test-engineer",
    "documentation_reviewer": "documentation-reviewer",
    "documentationreviewer": "documentation-reviewer",
}
KNOWN_ROLES = {
    "orchestrator",
    "planner",
    "architect",
    "implementer",
    "test-engineer",
    "verifier",
    "reviewer",
    "documentation-reviewer",
}
ROLE_CAPABILITIES = {
    "orchestrator": {"inspect", "coordinate", "delegate", "track-dependencies", "consolidate-evidence"},
    "planner": {"inspect", "plan", "plan-technical", "plan-execution"},
    "architect": {"inspect", "design", "adr"},
    "implementer": {"inspect", "implement"},
    "test-engineer": {"inspect", "design-tests", "write-tests"},
    "verifier": {"inspect", "build", "run-tests", "verify-final"},
    "reviewer": {"inspect", "review"},
    "documentation-reviewer": {"inspect", "review-docs"},
}
MINIMUM_OPERATIONAL_CAPABILITY_BY_ROLE = {
    "implementer": "implement",
    "test-engineer": "write-tests",
    "verifier": "verify-final",
    "reviewer": "review",
    "documentation-reviewer": "review-docs",
    "planner": "plan-execution",
    "architect": "design",
}
CAPABILITY_ALIASES = {
    "implementation": "implement",
    "write-code": "implement",
    "write_code": "implement",
    "code": "implement",
    "testing": "write-tests",
    "test": "write-tests",
    "write_test": "write-tests",
    "write-tests": "write-tests",
    "validation": "verify-final",
    "final-validation": "verify-final",
    "final_validation": "verify-final",
    "verify": "verify-final",
    "run-build": "build",
    "documentation": "review-docs",
}
READ_ONLY_ROLES = {
    "orchestrator",
    "planner",
    "architect",
    "verifier",
    "reviewer",
    "documentation-reviewer",
}
READ_ONLY_OPERATIONS = frozenset({"read", "execute"})
INDEPENDENT_ROLES = {
    "implementer",
    "test-engineer",
    "verifier",
    "reviewer",
    "documentation-reviewer",
}
MINIMUM_ROLES_BY_CLASS = {
    "T0": (),
    "T1": ("planner", "implementer", "test-engineer", "verifier"),
    "T2": ("planner", "implementer", "test-engineer", "verifier", "reviewer"),
    "T3": (
        "planner",
        "architect",
        "implementer",
        "test-engineer",
        "verifier",
        "reviewer",
        "documentation-reviewer",
    ),
    "T4": (
        "planner",
        "architect",
        "implementer",
        "test-engineer",
        "verifier",
        "reviewer",
        "documentation-reviewer",
    ),
}
VALID_CLASSES = frozenset(MINIMUM_ROLES_BY_CLASS)
T0_SPECIALIZED_ROLES = frozenset(KNOWN_ROLES - {"orchestrator"})
# The status template documents a single Markdown list prefix. Keep the
# marker line-scoped and reject prose or punctuation after the version token.
_MARKDOWN_LIST_PREFIX = r"(?:[-*+][ \t]+)?"
_MARKER_LINE_END = r"[ \t]*(?:\r?$)"
CONTRACT_MARKERS = (
    re.compile(rf"(?im)^[ \t]*{_MARKDOWN_LIST_PREFIX}contrato[ \t]+aisdd(?:[ \t]+da[ \t]+feature)?[ \t]*[:=][ \t]*v?2{_MARKER_LINE_END}"),
    re.compile(rf"(?im)^[ \t]*{_MARKDOWN_LIST_PREFIX}aisdd[-_ ]contract[ \t]*[:=][ \t]*v?2{_MARKER_LINE_END}"),
    re.compile(rf"(?im)^[ \t]*{_MARKDOWN_LIST_PREFIX}delegation[-_ ]contract[ \t]*[:=][ \t]*v?2{_MARKER_LINE_END}"),
    re.compile(rf"(?im)^[ \t]*{_MARKDOWN_LIST_PREFIX}contract(?:[-_ ]version)?[ \t]*[:=][ \t]*v?2{_MARKER_LINE_END}"),
)


def normalize_role(role: object) -> str:
    """Return a stable canonical role name, preserving unknown names for errors."""
    if not isinstance(role, str):
        return ""
    value = role.strip().lower().replace(" ", "-")
    return ROLE_ALIASES.get(value, value)


def _canonical_capability(capability: object) -> str:
    if not isinstance(capability, str):
        return ""
    value = capability.strip().lower().replace(" ", "-")
    return CAPABILITY_ALIASES.get(value, value)


def _as_list(value: object, *, allow_string: bool = False) -> list[object] | None:
    if isinstance(value, list):
        return value
    if allow_string and isinstance(value, str):
        return [value]
    return None


def _contract_errors(payload: object, filename: str) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{filename}: deve ser um objeto com contrato v2"]
    errors: list[str] = []
    for key in CONTRACT_VERSION_KEYS:
        if payload.get(key) != CONTRACT_V2:
            errors.append(f"{filename}: {key} deve ser v2")
    return errors


def _extract_collection(
    payload: object,
    keys: tuple[str, ...],
    filename: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    if isinstance(payload, list):
        raw = payload
    elif isinstance(payload, dict):
        raw = None
        for key in keys:
            if key in payload:
                raw = payload[key]
                break
        if isinstance(raw, dict):
            converted: list[object] = []
            for package_id, item in raw.items():
                if isinstance(item, dict):
                    converted.append({**item, "id": package_id})
                else:
                    errors.append(f"{filename}: item {package_id} deve ser um objeto")
            raw = converted
    else:
        raw = None
    if not isinstance(raw, list):
        return [], errors
    items: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f"{filename}: item {index} deve ser um objeto")
            continue
        items.append(item)
    return items, errors


def _extract_work_packages(payload: object) -> list[dict[str, Any]]:
    items, _ = _extract_collection(
        payload,
        ("work_packages", "work-packages", "workPackages", "packages"),
        "work-packages.json",
    )
    return items


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _extract_scope(package: dict[str, Any]) -> tuple[object, object, object, object]:
    raw_scope = package.get("scope")
    if not isinstance(raw_scope, dict):
        return None, None, None, None
    return (
        raw_scope.get("write"),
        raw_scope.get("read"),
        raw_scope.get("execute"),
        raw_scope.get("forbidden"),
    )


def _safe_relative_path(value: object) -> tuple[str | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, "caminho deve ser texto não vazio"
    raw = value.strip().replace("\\", "/")
    if "\x00" in raw:
        return None, "caminho contém NUL"
    if raw.startswith(("/", "//", "~")) or re.match(r"^[A-Za-z]:", raw):
        return None, "caminho absoluto"
    if ":" in raw:
        return None, "caminho contém prefixo inválido"
    trailing_separator = raw.endswith("/")
    if trailing_separator:
        raw = raw.rstrip("/")
    parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None, "caminho contém segmento inválido/traversal"
    normalized = "/".join(parts)
    if not normalized:
        return None, "caminho vazio"
    if trailing_separator:
        normalized += "/"
    return normalized, None


def _validated_paths(
    value: object,
    label: str,
    *,
    required: bool,
    allow_string: bool = False,
    required_error: str | None = None,
) -> tuple[list[str], list[str]]:
    if value is None:
        values: list[object] = []
    else:
        raw_values = _as_list(value, allow_string=allow_string)
        if raw_values is None:
            return [], [f"{label}: deve ser uma lista de caminhos"]
        values = raw_values
    errors: list[str] = []
    paths: list[str] = []
    for index, item in enumerate(values):
        normalized, error = _safe_relative_path(item)
        if error:
            errors.append(f"{label}[{index}]: {error}")
        elif normalized is not None:
            paths.append(normalized)
    if required and not paths:
        errors.append(required_error or f"{label}: escopo de escrita ausente")
    return paths, errors


def _normalize_state(value: object) -> str:
    return _text(value)


def _normalize_package(package: dict[str, Any], index: int) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    package_id = _text(package.get("id"))
    label = package_id or f"index {index}"
    if not package_id:
        errors.append(f"WP {label}: owner/id ausente: id ausente")

    owner_value = package.get("owner")
    owner = _text(owner_value)
    owner_role = ""
    if isinstance(owner_value, dict):
        owner = _text(owner_value.get("id", owner_value.get("name", owner_value.get("agent"))))
        owner_role = normalize_role(owner_value.get("role"))
    if not owner:
        errors.append(f"WP {label}: owner ausente")

    role_value = package.get("role")
    role = normalize_role(role_value)
    if "role" not in package or not role:
        errors.append(f"WP {label}: role ausente")
    elif role not in KNOWN_ROLES:
        errors.append(f"WP {label}: role desconhecida: {role}")
    if isinstance(owner_value, dict) and "role" in owner_value:
        if not owner_role:
            errors.append(f"WP {label}: owner.role inválida ou ausente")
        elif owner_role not in KNOWN_ROLES:
            errors.append(f"WP {label}: owner.role desconhecida: {owner_role}")
        elif role and owner_role != role:
            errors.append(f"WP {label}: owner.role não corresponde à role explícita")

    dependency_aliases = [key for key in DEPENDENCY_ALIASES if key in package]
    if len(dependency_aliases) > 1:
        errors.append(
            f"WP {label}: aliases de dependência são mutuamente exclusivos: "
            + ", ".join(dependency_aliases)
        )
    dependencies_value = package[dependency_aliases[0]] if dependency_aliases else []
    dependencies = _as_list(dependencies_value)
    if dependencies is None or any(not isinstance(item, str) or not item.strip() for item in dependencies):
        errors.append(f"WP {label}: depends_on deve ser uma lista de IDs")
        dependencies = []
    dependencies = [item.strip() for item in dependencies]
    if len(set(dependencies)) != len(dependencies):
        errors.append(f"WP {label}: dependência duplicada")
    if package_id and package_id in dependencies:
        errors.append(f"WP {label}: auto-dependência inválida")

    capabilities_value = package.get("capabilities")
    capabilities = _as_list(capabilities_value, allow_string=True)
    if not capabilities:
        errors.append(f"WP {label}: capabilities ausentes")
        capabilities = []
    normalized_capabilities = [_canonical_capability(item) for item in capabilities]
    if any(not item for item in normalized_capabilities):
        errors.append(f"WP {label}: capability inválida")
    if role in ROLE_CAPABILITIES:
        for capability in normalized_capabilities:
            if capability and capability not in ROLE_CAPABILITIES[role]:
                errors.append(f"WP {label}: role {role} não possui capability {capability}")
        required_capability = MINIMUM_OPERATIONAL_CAPABILITY_BY_ROLE.get(role)
        if required_capability and required_capability not in normalized_capabilities:
            errors.append(
                f"WP {label}: role {role} exige capability operacional mínima {required_capability}"
            )

    raw_write_scope, raw_read_scope, raw_execute_scope, raw_forbidden_scope = _extract_scope(package)
    scope_value = package.get("scope")
    if "scope" not in package:
        errors.append(f"WP {label}: scope ausente")
    elif not isinstance(scope_value, dict):
        errors.append(f"WP {label}: scope deve ser um objeto com listas de escopo")
    else:
        if "write" not in scope_value:
            errors.append(f"WP {label}: scope.write ausente")
        elif not isinstance(raw_write_scope, list):
            errors.append(f"WP {label}: scope.write deve ser uma lista de caminhos")
        if "read" in scope_value and not isinstance(raw_read_scope, list):
            errors.append(f"WP {label}: scope.read deve ser uma lista de caminhos")
        if "execute" in scope_value and not isinstance(raw_execute_scope, list):
            errors.append(f"WP {label}: scope.execute deve ser uma lista de caminhos")
        if "forbidden" not in scope_value:
            errors.append(f"WP {label}: scope.forbidden ausente")
        elif not isinstance(raw_forbidden_scope, list):
            errors.append(f"WP {label}: scope.forbidden deve ser uma lista de caminhos")
    write_scope, scope_errors = _validated_paths(
        raw_write_scope,
        f"WP {label}: escopo de escrita",
        required=role not in READ_ONLY_ROLES,
    )
    read_scope, read_errors = _validated_paths(
        raw_read_scope,
        f"WP {label}: escopo de leitura",
        required=False,
    )
    execute_scope, execute_errors = _validated_paths(
        raw_execute_scope,
        f"WP {label}: escopo de execucao",
        required=False,
    )
    forbidden_scope, forbidden_errors = _validated_paths(
        raw_forbidden_scope,
        f"WP {label}: escopo proibido",
        required=False,
    )
    errors.extend(scope_errors)
    errors.extend(read_errors)
    errors.extend(execute_errors)
    errors.extend(forbidden_errors)
    if role in READ_ONLY_ROLES and isinstance(raw_write_scope, list) and raw_write_scope:
        errors.append(f"WP {label}: role read-only exige scope.write vazio")
    for scope_name, scope_paths, scope_label in (
        ("write", write_scope, "escrita"),
        ("read", read_scope, "leitura"),
        ("execute", execute_scope, "execucao"),
    ):
        for scope_path in scope_paths:
            if any(_paths_overlap(scope_path, forbidden_path) for forbidden_path in forbidden_scope):
                errors.append(f"WP {label}: escopo de {scope_label} proibido: {scope_path}")

    normalized_scope: dict[str, Any] = {"write": write_scope, "forbidden": forbidden_scope}
    if isinstance(scope_value, dict):
        if "read" in scope_value:
            normalized_scope["read"] = read_scope
        if "execute" in scope_value:
            normalized_scope["execute"] = execute_scope

    criteria = package.get("acceptance_criteria", package.get("criteria", []))
    criteria_list = _as_list(criteria, allow_string=True)
    if not criteria_list or any(not isinstance(item, str) or not item.strip() for item in criteria_list):
        errors.append(f"WP {label}: acceptance_criteria ausentes ou inválidos")
        criteria_list = []
    if "state" not in package:
        errors.append(f"WP {label}: state ausente")
    state = _normalize_state(package.get("state"))
    if "state" in package and state not in VALID_STATES:
        errors.append(f"WP {label}: estado inválido: {state or '<ausente>'}")

    normalized = {
        "id": package_id,
        "owner": owner,
        "role": role,
        "depends_on": dependencies,
        "capabilities": normalized_capabilities,
        "scope": normalized_scope,
        "acceptance_criteria": [item.strip() for item in criteria_list],
        "state": state,
    }
    return normalized, errors


def _path_prefix(value: str) -> str:
    wildcard = re.search(r"[*?\[]", value)
    return value[: wildcard.start()] if wildcard else value


def _paths_overlap(left: str, right: str) -> bool:
    """Conservatively detect exact, ancestor and glob-overlapping paths."""
    left = left.replace("\\", "/").strip("/").casefold()
    right = right.replace("\\", "/").strip("/").casefold()
    if not left or not right:
        return False
    if left == right or left.startswith(right + "/") or right.startswith(left + "/"):
        return True
    if fnmatch.fnmatchcase(left, right) or fnmatch.fnmatchcase(right, left):
        return True
    left_has_glob = any(char in left for char in "*?[")
    right_has_glob = any(char in right for char in "*?[")
    left_prefix = _path_prefix(left).rstrip("/")
    right_prefix = _path_prefix(right).rstrip("/")
    if not left_prefix or not right_prefix:
        return True
    if left_has_glob and right_has_glob:
        left_directory = left.rsplit("/", 1)[0] if "/" in left else ""
        right_directory = right.rsplit("/", 1)[0] if "/" in right else ""
        if left_directory and left_directory == right_directory:
            return True
        if left_prefix.startswith(right_prefix) or right_prefix.startswith(left_prefix):
            return True
    return bool(
        left_prefix == right_prefix
        or left_prefix.startswith(right_prefix + "/")
        or right_prefix.startswith(left_prefix + "/")
    )


def _topological_order(packages: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    by_id = {package["id"]: package for package in packages if package.get("id")}
    errors: list[str] = []
    indegree = {package_id: 0 for package_id in by_id}
    dependents: dict[str, set[str]] = defaultdict(set)
    for package in packages:
        package_id = package.get("id")
        if not package_id:
            continue
        for dependency in package.get("depends_on", []):
            if dependency not in by_id:
                errors.append(f"WP {package_id}: dependência inexistente: {dependency}")
                continue
            indegree[package_id] += 1
            dependents[dependency].add(package_id)
    ready = [package_id for package_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        package_id = heapq.heappop(ready)
        order.append(package_id)
        for dependent in sorted(dependents[package_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(order) != len(by_id):
        cyclic = sorted(package_id for package_id, degree in indegree.items() if degree > 0)
        errors.append("grafo contém ciclo: " + ", ".join(cyclic))
    return order, errors


def _has_dependency_path(
    packages_by_id: dict[str, dict[str, Any]],
    start: str,
    target: str,
) -> bool:
    """Return whether start explicitly depends on target, directly or transitively."""
    pending = list(packages_by_id.get(start, {}).get("depends_on", []))
    visited: set[str] = set()
    while pending:
        dependency = pending.pop()
        if dependency == target:
            return True
        if dependency in visited:
            continue
        visited.add(dependency)
        pending.extend(packages_by_id.get(dependency, {}).get("depends_on", []))
    return False


def _has_dependency_role(
    packages_by_id: dict[str, dict[str, Any]],
    start: str,
    target_role: str,
) -> bool:
    """Return whether a WP transitively depends on a WP with ``target_role``."""
    return any(
        package.get("role") == target_role
        and _has_dependency_path(packages_by_id, start, package_id)
        for package_id, package in packages_by_id.items()
    )


def _execution_dependency_errors(packages: list[dict[str, Any]]) -> list[str]:
    """Enforce the minimum execution ordering after package normalization."""
    packages_by_id = {package["id"]: package for package in packages if package.get("id")}
    by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for package in packages_by_id.values():
        by_role[package.get("role", "")].append(package)

    errors: list[str] = []
    if by_role.get("implementer"):
        for package in by_role.get("test-engineer", []):
            if not _has_dependency_role(packages_by_id, package["id"], "implementer"):
                errors.append(
                    f"WP {package['id']}: test-engineer deve depender transitivamente de algum implementer"
                )
    if by_role.get("test-engineer"):
        for package in by_role.get("verifier", []):
            if not _has_dependency_role(packages_by_id, package["id"], "test-engineer"):
                errors.append(
                    f"WP {package['id']}: verifier deve depender transitivamente de algum test-engineer"
                )
    if by_role.get("verifier"):
        for role in ("reviewer", "documentation-reviewer"):
            for package in by_role.get(role, []):
                if not _has_dependency_role(packages_by_id, package["id"], "verifier"):
                    errors.append(
                        f"WP {package['id']}: {role} deve depender transitivamente de algum verifier"
                    )
    return errors


def validate_work_packages(payload: object) -> dict[str, Any]:
    """Validate WPs and return deterministic order plus structured errors."""
    errors: list[str] = []
    errors.extend(_contract_errors(payload, "work-packages.json"))
    raw_packages, collection_errors = _extract_collection(
        payload,
        ("work_packages", "work-packages", "workPackages", "packages"),
        "work-packages.json",
    )
    errors.extend(collection_errors)
    if not raw_packages:
        errors.append("work-packages.json: work_packages ausente ou vazio")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, package in enumerate(raw_packages):
        item, item_errors = _normalize_package(package, index)
        normalized.append(item)
        errors.extend(item_errors)
        package_id = item["id"]
        if package_id and package_id in seen:
            errors.append(f"ID duplicado de WP: {package_id}")
        if package_id:
            seen.add(package_id)

    unique_packages = []
    unique_ids: set[str] = set()
    for package in normalized:
        if package["id"] and package["id"] not in unique_ids:
            unique_packages.append(package)
            unique_ids.add(package["id"])
    order, graph_errors = _topological_order(unique_packages)
    errors.extend(graph_errors)

    packages_by_id = {package["id"]: package for package in unique_packages}
    errors.extend(_execution_dependency_errors(unique_packages))
    for index, left in enumerate(unique_packages):
        for right in unique_packages[index + 1 :]:
            for left_path in left["scope"]["write"]:
                for right_path in right["scope"]["write"]:
                    serial_dependency = _has_dependency_path(packages_by_id, left["id"], right["id"]) or _has_dependency_path(
                        packages_by_id, right["id"], left["id"]
                    )
                    if _paths_overlap(left_path, right_path) and not serial_dependency:
                        errors.append(
                            f"conflito de escopo entre {left['id']} e {right['id']}: {left_path} / {right_path}"
                        )

    return {
        "valid": not errors,
        "errors": errors,
        "order": order if not any("grafo contém ciclo" in error for error in errors) else [],
        "work_packages": normalized,
    }


def _canonical_packages_for_digest(payload: object) -> list[dict[str, Any]]:
    result = validate_work_packages(payload)
    packages = [item for item in result["work_packages"] if item.get("id")]
    return sorted(packages, key=lambda item: item["id"])


def _json_digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def work_packages_sha256(payload: object) -> str:
    """Return the canonical digest used by v2 evidence."""
    return _json_digest(_canonical_packages_for_digest(payload))


def _accepted_package_digests(payload: object) -> set[str]:
    raw_packages = _extract_work_packages(payload)
    return {
        work_packages_sha256(payload),
        _json_digest(payload),
        _json_digest(raw_packages),
    }


def _evidence_entries(payload: object) -> list[dict[str, Any]]:
    entries, _ = _extract_evidence_entries(payload)
    return entries


def _extract_evidence_entries(payload: object) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(payload, dict):
        return [], ["delegation-evidence.json: deve ser um objeto"]
    keys = (
        "delegations",
        "entries",
        "evidence",
        "executions",
        "work_packages",
        "workPackages",
        "work_package_evidence",
    )
    raw = None
    for key in keys:
        if key in payload:
            raw = payload[key]
            break
    return _extract_collection(payload if raw is None else {"items": raw}, ("items",), "delegation-evidence.json")


def _entry_package_id(entry: dict[str, Any]) -> str:
    return _text(entry.get("work_package", entry.get("work_package_id", entry.get("wp_id", entry.get("wp", entry.get("id"))))))


def _path_is_within_scope(path: str, allowed: str) -> bool:
    normalized_path = path.rstrip("/").casefold()
    normalized_allowed = allowed.rstrip("/").casefold()
    if not normalized_path or not normalized_allowed:
        return False
    if any(char in normalized_allowed for char in "*?["):
        return fnmatch.fnmatchcase(normalized_path, normalized_allowed)
    return normalized_path == normalized_allowed or normalized_path.startswith(normalized_allowed + "/")


def _normalize_operation(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("_", "-")


def _has_content(value: object) -> bool:
    """Return whether a fallback field contains non-empty direct-work data."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, bool):
        return value
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _normalize_audit_text(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").casefold()


TRIVIAL_RATIONALE = re.compile(
    r"\b(?:trivial|trivialidade|triviality|silencio|silencios[oa]s?|silence|silent|"
    r"sem\s+motivo|no\s+reason|without\s+reason|none|ausente|absent|missing|"
    r"not\s+provided|not\s+specified|unspecified|sem\s+justificativa|"
    r"no\s+justification|without\s+justification|nao\s+informad[oa]s?|"
    r"nao\s+especificad[oa]s?|nao\s+se\s+aplica|not\s+applicable)\b|n\s*/\s*a"
)
GENERIC_RATIONALE_MARKERS = frozenset({
    "ok",
    "okay",
    "no work",
    "nowork",
})


def _is_trivial_rationale(value: str) -> bool:
    normalized = _normalize_audit_text(value)
    compact = re.sub(r"[\W_]+", " ", normalized).strip()
    if len(compact) <= 1 or compact in GENERIC_RATIONALE_MARKERS:
        return True
    return bool(TRIVIAL_RATIONALE.search(normalized))


def _fallback_errors(entry: dict[str, Any], package: dict[str, Any]) -> list[str]:
    package_id = package.get("id", "<desconhecido>")
    if "fallback" not in entry:
        return [f"evidência {package_id}: fallback ausente; declare um objeto com used booleano"]
    fallback = entry.get("fallback")
    if fallback is None:
        return [f"evidência {package_id}: fallback inválido"]
    if not isinstance(fallback, dict):
        return [f"evidência {package_id}: fallback inválido"]
    if not isinstance(fallback.get("used"), bool):
        return [f"evidência {package_id}: fallback.used deve ser booleano"]
    if not fallback["used"]:
        incompatible = sorted(
            key for key, value in fallback.items() if key != "used" and _has_content(value)
        )
        if incompatible:
            return [
                f"evidência {package_id}: fallback.used=false exige declaração limpa; "
                "conteúdo incompatível em: "
                + ", ".join(incompatible)
            ]
        return []
    errors: list[str] = []
    if fallback.get("approved") is not True:
        errors.append(f"evidência {package_id}: fallback sem aprovação explícita")
    reason = _text(fallback.get("reason"))
    if not reason:
        errors.append(f"evidência {package_id}: fallback sem motivo")
    elif _is_trivial_rationale(reason):
        errors.append(f"evidência {package_id}: motivo de fallback trivial ou silêncio não é válido")
    if fallback.get("agent_unavailable") is not True:
        errors.append(f"evidência {package_id}: fallback sem agente indisponível observado")
    attempts = fallback.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        errors.append(f"evidência {package_id}: fallback sem tentativas")
    elif any(not isinstance(attempt, dict) for attempt in attempts):
        errors.append(f"evidência {package_id}: fallback com tentativa inválida")
    direct_work = fallback.get("direct_work")
    if not isinstance(direct_work, dict):
        errors.append(f"evidência {package_id}: fallback sem trabalho direto auditável")
    else:
        if not _text(direct_work.get("result", direct_work.get("summary"))):
            errors.append(f"evidência {package_id}: fallback sem resultado do trabalho direto")
        direct_scope = direct_work.get("scope", direct_work.get("paths"))
        direct_paths, path_errors = _validated_paths(
            direct_scope,
            f"evidência {package_id}: escopo do trabalho direto",
            required=True,
            required_error=f"evidência {package_id}: escopo do trabalho direto ausente",
        )
        errors.extend(path_errors)
        package_scope = package.get("scope", {})
        if not isinstance(package_scope, dict):
            package_scope = {}
        forbidden_paths = package_scope.get("forbidden", [])
        if not isinstance(forbidden_paths, list):
            forbidden_paths = []
        role = package.get("role")
        operation_present = "operation" in direct_work
        operation = _normalize_operation(direct_work.get("operation"))
        if role in READ_ONLY_ROLES:
            if not operation_present or not operation:
                errors.append(
                    f"evidência {package_id}: role read-only exige direct_work.operation explicita: read ou execute"
                )
            elif operation not in READ_ONLY_OPERATIONS:
                if operation == "write":
                    errors.append(f"evidência {package_id}: escrita direta proibida para role read-only")
                else:
                    errors.append(
                        f"evidência {package_id}: direct_work.operation deve ser read ou execute para role read-only"
                    )
            for write_field in ("write", "writes"):
                if _has_content(direct_work.get(write_field)):
                    errors.append(f"evidência {package_id}: escrita direta proibida para role read-only")
            allowed_paths = package_scope.get(operation, []) if operation in READ_ONLY_OPERATIONS else []
            if operation in READ_ONLY_OPERATIONS and not isinstance(allowed_paths, list):
                allowed_paths = []
            if operation in READ_ONLY_OPERATIONS and not allowed_paths:
                errors.append(
                    f"evidência {package_id}: scope.{operation} ausente ou vazio para fallback read-only"
                )
        else:
            if operation_present and operation != "write":
                errors.append(
                    f"evidência {package_id}: direct_work.operation deve ser write quando informado"
                )
            allowed_paths = package_scope.get("write", [])
            if not isinstance(allowed_paths, list):
                allowed_paths = []
        if direct_paths and not allowed_paths:
            errors.append(f"evidência {package_id}: trabalho direto fora do escopo permitido")
        for direct_path in direct_paths:
            if allowed_paths and not any(_path_is_within_scope(direct_path, allowed) for allowed in allowed_paths):
                errors.append(f"evidência {package_id}: trabalho direto fora do escopo: {direct_path}")
            if any(_paths_overlap(direct_path, forbidden) for forbidden in forbidden_paths):
                errors.append(f"evidência {package_id}: trabalho direto em escopo proibido: {direct_path}")
        if not direct_paths and direct_scope is not None:
            errors.append(f"evidência {package_id}: fallback sem escopo do trabalho direto")
    return errors


def _t0_coverage_errors(
    evidence: dict[str, Any],
    packages: dict[str, dict[str, Any]],
    observed_roles: set[str],
    required_roles: list[str],
) -> list[str]:
    """Require auditable non-delegability or a specialized T0 owner."""
    declaration = evidence.get("mechanical_non_delegable")
    declaration_valid = False
    errors: list[str] = []
    if declaration is not None:
        declaration_valid = isinstance(declaration, dict)
        if not declaration_valid:
            errors.append("T0: mechanical_non_delegable deve ser um objeto auditável")
        else:
            if declaration.get("approved") is not True:
                errors.append("T0: mechanical_non_delegable.approved deve ser true")
            rationale = _text(
                declaration.get(
                    "reason",
                    declaration.get(
                        "rationale",
                        declaration.get("basis", declaration.get("justification", declaration.get("evidence"))),
                    ),
                )
            )
            if not rationale:
                errors.append("T0: mechanical_non_delegable sem justificativa auditável")
            elif _is_trivial_rationale(rationale):
                errors.append("T0: mechanical_non_delegable exige justificativa não trivial e auditável")
            declaration_valid = not errors

    if declaration_valid:
        return errors

    specialized_roles = observed_roles & T0_SPECIALIZED_ROLES
    if not specialized_roles:
        errors.append(
            "T0: evidência exige mechanical_non_delegable.approved=true com "
            "justificativa auditável ou uma role especializada; "
            "orchestrator/coordinate não satisfaz a cobertura"
        )
    if required_roles and not (set(required_roles) & T0_SPECIALIZED_ROLES):
        errors.append("T0: required_roles deve incluir uma role especializada")
    for package in packages.values():
        if package.get("role") == "orchestrator" and "coordinate" in package.get("capabilities", []):
            errors.append(
                "T0: capability coordinate do orchestrator não pode ser owner de trabalho delegável"
            )
    return errors


def minimum_required_roles(change_class: str | None) -> tuple[str, ...]:
    """Return the non-reducible role set for a change class."""
    normalized = change_class.strip().upper() if isinstance(change_class, str) else ""
    if normalized not in VALID_CLASSES:
        reason = "ausente" if not normalized else f"inválida: {change_class}"
        raise ValueError(f"classe {reason}")
    return MINIMUM_ROLES_BY_CLASS[normalized]


def _human_approval_errors(evidence: dict[str, Any], change_class: str | None) -> list[str]:
    normalized = change_class.strip().upper() if isinstance(change_class, str) else ""
    if normalized != "T4":
        return []
    approval = evidence.get("human_approval")
    if not isinstance(approval, dict):
        return ["delegation-evidence.json: T4 exige human_approval auditável"]
    errors: list[str] = []
    if approval.get("approved") is not True:
        errors.append("delegation-evidence.json: aprovação humana T4 não foi aprovada")
    if not _text(approval.get("approver", approval.get("approved_by", approval.get("by")))):
        errors.append("delegation-evidence.json: aprovação humana T4 sem aprovador")
    if not _text(approval.get("timestamp", approval.get("approved_at", approval.get("at")))):
        errors.append("delegation-evidence.json: aprovação humana T4 sem timestamp")
    if not _text(approval.get("reference", approval.get("record", approval.get("decision_id", approval.get("audit_ref"))))):
        errors.append("delegation-evidence.json: aprovação humana T4 sem referência auditável")
    return errors


def validate_delegation_evidence(
    work_packages: object,
    evidence: object,
    change_class: str | None = None,
) -> dict[str, Any]:
    """Validate role coverage, freshness, independence and audited fallbacks."""
    errors: list[str] = []
    graph = validate_work_packages(work_packages)
    errors.extend(f"work-packages: {error}" for error in graph["errors"])
    packages = {item["id"]: item for item in graph["work_packages"] if item.get("id")}
    if not isinstance(evidence, dict):
        errors.append("delegation-evidence.json deve ser um objeto")
        return {"valid": False, "errors": errors, "roles": [], "entries": []}
    errors.extend(_contract_errors(evidence, "delegation-evidence.json"))

    supplied_digest = evidence.get("work_packages_sha256", evidence.get("work_packages_digest"))
    if not isinstance(supplied_digest, str) or not supplied_digest:
        errors.append("delegation-evidence.json: digest dos Work Packages ausente")
    elif supplied_digest != work_packages_sha256(work_packages):
        errors.append("delegation-evidence.json: evidência obsoleta (digest dos Work Packages não corresponde)")

    entries, entry_errors = _extract_evidence_entries(evidence)
    errors.extend(entry_errors)
    if not entries:
        errors.append("delegation-evidence.json: delegations ausente ou vazio")
    entries_by_package: dict[str, dict[str, Any]] = {}
    observed_roles: set[str] = set()
    roles_by_agent: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        package_id = _entry_package_id(entry)
        if not package_id:
            errors.append("evidência sem work_package")
            continue
        if package_id in entries_by_package:
            errors.append(f"evidência duplicada para {package_id}")
            continue
        entries_by_package[package_id] = entry
        if package_id not in packages:
            errors.append(f"evidência para WP inexistente: {package_id}")
            continue
        role_value = entry.get("role")
        role = normalize_role(role_value)
        if not role:
            errors.append(f"evidência {package_id}: role ausente")
        elif role not in KNOWN_ROLES:
            errors.append(f"evidência {package_id}: role ausente ou desconhecida")
        else:
            if role != packages[package_id].get("role"):
                errors.append(f"evidência {package_id}: role não corresponde ao WP")
        agent_id = _text(entry.get("agent_id"))
        if not agent_id:
            errors.append(f"evidência {package_id}: agent_id ausente")
        state_value = entry.get("state")
        state = _normalize_state(state_value)
        if state not in VALID_STATES:
            errors.append(f"evidência {package_id}: estado inválido ou ausente")
        if not isinstance(state_value, str) or state_value.strip().lower() != "completed":
            errors.append(f"evidência {package_id}: estado deve ser completed")
        package_state = packages[package_id].get("state")
        if package_state != state:
            errors.append(
                f"evidência {package_id}: estado não corresponde ao WP ({state or '<ausente>'} != {package_state or '<ausente>'})"
            )
        if role in KNOWN_ROLES and agent_id:
            observed_roles.add(role)
            if role in INDEPENDENT_ROLES:
                roles_by_agent[agent_id].add(role)
        errors.extend(_fallback_errors(entry, packages[package_id]))

    for package_id, package in packages.items():
        if package.get("state") != "completed":
            errors.append(f"WP {package_id}: estado deve ser completed para evidência final")

    for package_id in packages:
        if package_id not in entries_by_package:
            errors.append(f"WP sem evidência: {package_id}")
    if any(package_id not in packages for package_id in entries_by_package):
        pass

    try:
        minimum_roles = list(minimum_required_roles(change_class))
    except ValueError as error:
        errors.append(str(error))
        minimum_roles = []
    required_value = evidence.get("required_roles")
    if required_value is None:
        required_roles = minimum_roles
    else:
        required_items = _as_list(required_value, allow_string=True)
        if required_items is None or (not required_items and minimum_roles) or any(not isinstance(item, str) or not item.strip() for item in required_items or []):
            errors.append("delegation-evidence.json: required_roles inválido")
            required_roles = []
        else:
            required_roles = [normalize_role(item) for item in required_items]
            if len(set(required_roles)) != len(required_roles):
                errors.append("delegation-evidence.json: required_roles contém duplicatas")
            missing_minimum = sorted(set(minimum_roles) - set(required_roles))
            if missing_minimum:
                errors.append(
                    "delegation-evidence.json: required_roles reduz o mínimo da classe "
                    + (change_class or "T1")
                    + ": "
                    + ", ".join(missing_minimum)
                )
    for role in required_roles:
        if role not in KNOWN_ROLES:
            errors.append(f"role obrigatória desconhecida: {role or '<vazia>'}")
        elif role not in observed_roles:
            errors.append(f"role obrigatória ausente: {role}")

    for agent_id, roles in sorted(roles_by_agent.items()):
        if len(roles) > 1:
            errors.append(
                "roles independentes compartilham agent_id "
                + agent_id
                + ": "
                + ", ".join(sorted(roles))
            )
    blockers = evidence.get("blockers", [])
    if "blocker_open" in evidence and not isinstance(evidence["blocker_open"], bool):
        errors.append("delegation-evidence.json: blocker_open deve ser booleano")
    elif evidence.get("blocker_open") is True:
        errors.append("delegation-evidence.json: há blocker aberto")
    if "blockers" in evidence and not isinstance(blockers, list):
        errors.append("delegation-evidence.json: blockers deve ser uma lista vazia")
    elif isinstance(blockers, list) and blockers:
        errors.append("delegation-evidence.json: blockers deve estar vazio para concluir")
    errors.extend(_human_approval_errors(evidence, change_class))
    if isinstance(change_class, str) and change_class.strip().upper() == "T0":
        errors.extend(_t0_coverage_errors(evidence, packages, observed_roles, required_roles))

    return {
        "valid": not errors,
        "errors": errors,
        "roles": sorted(observed_roles),
        "required_roles": required_roles,
        "entries": sorted(entries_by_package),
    }


def _without_markdown_fences(content: str) -> str:
    """Remove fenced and indented Markdown code before checking metadata."""
    visible: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in content.splitlines(keepends=True):
        leading = re.match(r"^[ \t]*", line)
        indentation = leading.group(0) if leading else ""
        if fence_char is not None:
            if re.match(
                rf"^[ \t]{{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*(?:\r?\n)?$",
                line,
            ):
                fence_char = None
                fence_length = 0
            continue
        if "\t" in indentation or len(indentation) >= 4:
            continue
        opening = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})[^\r\n]*(?:\r?\n)?$", line)
        if opening:
            fence = opening.group(1)
            fence_char = fence[0]
            fence_length = len(fence)
            continue
        visible.append(line)
    return "".join(visible)


HISTORICAL_HEADING = re.compile(
    r"\b(?:historico(?:s)?|historica(?:s)?|history|histories|historical(?:ly)?|"
    r"evidencia(?:s)?\s+historica(?:s)?|evidence\s+historical)\b"
)


def _without_historical_sections(content: str) -> str:
    """Remove content nested below explicitly historical Markdown headings."""
    visible: list[str] = []
    ignored_level: int | None = None
    for raw_line in content.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        heading = re.match(r"^[ \t]{0,3}(#{1,6})[ \t]+(.+?)[ \t]*$", line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            title = re.sub(r"[ \t]+#+[ \t]*$", "", title)
            if ignored_level is not None:
                if level <= ignored_level:
                    ignored_level = None
                else:
                    continue
            if HISTORICAL_HEADING.search(_normalize_audit_text(title)):
                ignored_level = level
                continue
            visible.append(raw_line)
        elif ignored_level is None:
            visible.append(raw_line)
    return "".join(visible)


def contract_version(feature: Path) -> str:
    """Read only feature metadata and return v2 when an explicit marker exists."""
    feature = Path(feature)
    for name in ("spec.md", "plan.md", "status.md"):
        path = feature / name
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if any(marker.search(_without_markdown_fences(content)) for marker in CONTRACT_MARKERS):
            return CONTRACT_V2
    return "v1"


def is_v2_feature(feature: Path) -> bool:
    return contract_version(feature) == CONTRACT_V2


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def extract_feature_class(feature: Path) -> str | None:
    """Read the declared Class from a feature folder for CLI validation."""
    feature = Path(feature)
    declared: set[str] = set()
    invalid: set[str] = set()
    for name in ("spec.md", "plan.md", "status.md"):
        path = feature / name
        if not path.exists():
            continue
        content = _without_historical_sections(_without_markdown_fences(path.read_text(encoding="utf-8")))
        for match in re.finditer(
            r"(?im)^[ \t]*(?:[-*+][ \t]+)?(?:classe|class)[ \t]*:[ \t]*([^\s#]+)",
            content,
        ):
            value = match.group(1).strip().rstrip(".,;)")
            normalized = value.upper()
            if normalized in VALID_CLASSES:
                declared.add(normalized)
            else:
                invalid.add(value)
    if invalid:
        raise ValueError("classe inválida: " + ", ".join(sorted(invalid)))
    if len(declared) > 1:
        raise ValueError("feature possui classes conflitantes: " + ", ".join(sorted(declared)))
    return next(iter(declared), None)


def validate_v2_feature(feature: Path) -> list[str]:
    """Validate v2 artifacts for a feature; return user-facing errors."""
    feature = Path(feature)
    if not is_v2_feature(feature):
        return []
    errors: list[str] = []
    work_packages_path = feature / "work-packages.json"
    evidence_path = feature / "delegation-evidence.json"
    if not work_packages_path.exists():
        errors.append("contrato v2: arquivo ausente: work-packages.json")
    if not evidence_path.exists():
        errors.append("contrato v2: arquivo ausente: delegation-evidence.json")
    if errors:
        return errors
    try:
        work_packages = _load_json(work_packages_path)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"contrato v2: work-packages.json inválido: {error}")
        return errors
    try:
        evidence = _load_json(evidence_path)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"contrato v2: delegation-evidence.json inválido: {error}")
        return errors
    try:
        change_class = extract_feature_class(feature)
    except (OSError, ValueError) as error:
        errors.append(f"contrato v2: classe da feature inválida: {error}")
        change_class = None
    if change_class is None and not any("classe da feature inválida" in error for error in errors):
        errors.append("contrato v2: classe da feature ausente")
    if errors:
        return errors
    evidence_result = validate_delegation_evidence(work_packages, evidence, change_class)
    errors.extend(f"delegation-evidence: {error}" for error in evidence_result["errors"])
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", help="work-packages.json ou pasta da feature")
    parser.add_argument("--work-packages", dest="work_packages_option", type=Path, help="work-packages.json")
    parser.add_argument("--evidence", type=Path, help="delegation-evidence.json correspondente")
    parser.add_argument("--delegation-evidence", dest="evidence_option", type=Path, help="delegation-evidence.json correspondente")
    parser.add_argument("--graph-only", action="store_true", help="validar somente o grafo; não é o modo padrão")
    parser.add_argument("--json", action="store_true", help="emitir resultado estruturado")
    args = parser.parse_args()
    path = args.work_packages_option or args.path
    if path is None:
        parser.error("informe uma pasta/arquivo de Work Packages")
    if args.graph_only and path.is_dir():
        parser.error("--graph-only aceita somente um arquivo de Work Packages, não uma pasta de feature")
    if args.graph_only and (args.evidence or args.evidence_option):
        parser.error("--graph-only não pode ser combinado com evidência")
    work_packages_path = path / "work-packages.json" if path.is_dir() else path
    evidence_path = args.evidence or args.evidence_option or (path / "delegation-evidence.json" if path.is_dir() else None)
    result: dict[str, Any]
    class_error: str | None = None
    try:
        work_packages = _load_json(work_packages_path)
        graph = validate_work_packages(work_packages)
        result = {"graph": graph}
        change_class = None
        if path.is_dir():
            try:
                change_class = extract_feature_class(path)
            except (OSError, ValueError) as error:
                class_error = str(error)
            result["class"] = change_class
            if change_class is None and class_error is None:
                class_error = "classe da feature ausente"
            if class_error:
                result["class_error"] = class_error
        if evidence_path and evidence_path.exists():
            evidence = _load_json(evidence_path)
            result["evidence"] = validate_delegation_evidence(work_packages, evidence, change_class)
        elif not args.graph_only:
            evidence_label = str(evidence_path) if evidence_path else "delegation-evidence.json"
            result["evidence"] = {
                "valid": False,
                "errors": [
                    f"delegation-evidence.json ausente ou não encontrado: {evidence_label}; use --graph-only explicitamente para validar somente o grafo"
                ],
            }
        result["valid"] = not class_error and all(
            section.get("valid", False) for section in result.values() if isinstance(section, dict) and "valid" in section
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        result = {"valid": False, "errors": [str(error)]}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("valid"):
            print("OK: contrato v2 válido")
            if "graph" in result:
                print("Ordem: " + " -> ".join(result["graph"].get("order", [])))
        else:
            print("FALHA")
            sections = [result] if "errors" in result else list(result.values())
            for section in sections:
                for error in section.get("errors", []) if isinstance(section, dict) else []:
                    print(f"- {error}")
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
