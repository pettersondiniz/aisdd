#!/usr/bin/env python3
"""Validate AISDD artifacts and the current, machine-readable AC test evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

from verify_feature import test_map
from delegation_contract import is_v2_feature, validate_v2_feature

REQUIRED = ("spec.md", "plan.md", "status.md", "evidence.md", "verification.json")
AC_PATTERN = re.compile(r"\bAC-\d{3,}\b")
TASK_PATTERN = re.compile(r"\bT-\d{3,}\b")
OPEN_STATUS = re.compile(
    r"\b(?:abert[oa]s?|bloquead[oa]s?|pendente(?:s)?|pending|open|"
    r"em\s+aberto|em\s+andamento|falha|falhou|failed|blocked|"
    r"in[_ -]?progress|incomplet[oa]s?|cancelad[oa]s?)\b",
    re.I,
)
HISTORICAL_HEADING = re.compile(
    r"\b(?:historico(?:s)?|historica(?:s)?|history|histories|historical(?:ly)?|"
    r"evidencia(?:s)?\s+historica(?:s)?|evidence\s+historical)\b",
    re.I,
)
STATE_HEADING = re.compile(
    r"^(?:estado(?: atual)?|status(?: atual)?|state|current\s+(?:status|state))\s*[:=]\s*(.+)$",
    re.I,
)
STATE_SECTION = re.compile(
    r"^(?:estado(?: atual)?|status(?: atual)?|state|"
    r"fase(?:\s+(?:atual|corrente))?|phase(?:\s+current)?|"
    r"current\s+(?:status|state|phase)|bloqueio(?:s)?|blocker(?:s)?)"
    r"\s*:?\s*$",
    re.I,
)
OPEN_SECTION_HEADING = re.compile(
    r"^(?:perguntas\s+abertas?|questoes\s+abertas?|open\s+questions?|"
    r"suposic(?:ao|oes)|assumption(?:s)?)\s*:?[ \t]*$",
    re.I,
)
OPEN_SECTION_ITEM = re.compile(r"^\s*(?:[-*+]\s*)?\[\s*\]\s*")
CLOSED_SECTION_CONTENT = re.compile(
    r"\b(?:resolvid[oa]s?|valid(?:ad[oa]s?|ada\s+localmente)|confirmad[oa]s?|"
    r"concluid[oa]s?|closed|done|completed|nenhuma|none|n\s*/\s*a)\b",
    re.I,
)
STRUCTURED_FIELD = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:estado(?: atual)?|status(?: atual)?|state|"
    r"fase(?: atual)?|phase(?: current)?|bloqueios?|blockers?)\s*[:=]\s*(.+)$",
    re.I,
)
TRACKED_ITEM = re.compile(r"\b(?:ASM|Q)-\d{3,}\b", re.I)
TABLE_STATUS_HEADERS = {
    "status",
    "status atual",
    "state",
    "estado",
    "estado atual",
    "situacao",
    "situacao atual",
}
MAIN_CHAT_ATTRIBUTION_DECLARATION = "Main-chat attribution: required"
TASK_WINDOW_SCHEMA_VERSION = 1
BOUNDARY_IDENTITY_FIELDS = ("event_index", "line", "kind", "turn_id")
TASK_WINDOW_END_KINDS = {"task_complete", "turn_aborted"}
TASK_WINDOW_EXCLUSION_CATEGORIES = (
    ("subagent", "delegated-agent"),
    ("tool",),
    ("modal",),
    ("subscription",),
)


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    return "".join(character for character in normalized if not unicodedata.combining(character))


def has_open_status(text: str) -> bool:
    """Inspect structured current values while excluding marked history."""
    current_lines: list[tuple[str, str, int | None]] = []
    ignored_level: int | None = None
    in_fence = False
    for line in text.splitlines():
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        heading = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            level = len(heading.group(1))
            title = _fold(heading.group(2)).strip()
            if ignored_level is not None:
                if level <= ignored_level:
                    ignored_level = None
                else:
                    continue
            if HISTORICAL_HEADING.search(title):
                ignored_level = level
                continue
            current_lines.append(("heading", title, level))
            continue
        if ignored_level is None:
            current_lines.append(("line", _fold(line), None))

    state_section_level: int | None = None
    open_section_level: int | None = None
    open_section_kind: str | None = None
    table_status_columns: list[int] | None = None
    for kind, value, level in current_lines:
        if kind == "heading":
            if open_section_level is not None and level is not None and level <= open_section_level:
                open_section_level = None
                open_section_kind = None
            if state_section_level is not None and level is not None and level <= state_section_level:
                state_section_level = None
            inline_structured = STRUCTURED_FIELD.match(value)
            if inline_structured and OPEN_STATUS.search(inline_structured.group(1)):
                return True
            inline_state = STATE_HEADING.match(value)
            if inline_state and OPEN_STATUS.search(inline_state.group(1)):
                return True
            if STATE_SECTION.match(value) and level is not None:
                state_section_level = level
            if OPEN_SECTION_HEADING.match(value) and level is not None:
                open_section_level = level
                normalized_heading = value.strip().rstrip(":").strip()
                open_section_kind = (
                    "questions"
                    if normalized_heading.startswith(("perguntas", "questoes", "open questions"))
                    else "assumptions"
                )
            table_status_columns = None
            continue

        structured = STRUCTURED_FIELD.match(value)
        if structured and OPEN_STATUS.search(structured.group(1)):
            return True
        if state_section_level is not None and OPEN_STATUS.search(value):
            return True
        if open_section_level is not None and open_section_kind is not None:
            stripped = value.strip()
            if OPEN_SECTION_ITEM.match(value):
                return True
            if OPEN_STATUS.search(value):
                return True
            if TRACKED_ITEM.search(value) and not CLOSED_SECTION_CONTENT.search(value):
                return True
            if (
                open_section_kind == "questions"
                and stripped.startswith(("-", "*", "+"))
                and stripped[1:].strip()
                and not CLOSED_SECTION_CONTENT.search(value)
            ):
                return True
        if TRACKED_ITEM.search(value) and OPEN_STATUS.search(value):
            return True

        stripped = value.strip()
        if stripped.startswith("|"):
            cells = [_fold(cell.strip()) for cell in stripped.strip("|").split("|")]
            if table_status_columns is None:
                table_status_columns = [
                    index
                    for index, cell in enumerate(cells)
                    if cell in TABLE_STATUS_HEADERS
                ]
            elif any(
                index < len(cells) and OPEN_STATUS.search(cells[index])
                for index in table_status_columns
            ):
                return True
        else:
            table_status_columns = None
    return False


def _has_exact_visible_declaration(text: str, declaration: str) -> bool:
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and stripped == declaration:
            return True
    return False


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_rollout_file(value: object) -> bool:
    return (
        _nonempty_text(value)
        and isinstance(value, str)
        and not Path(value).is_absolute()
        and "/" not in value
        and "\\" not in value
        and Path(value).name == value
    )


def _valid_boundary(
    boundary: object,
    label: str,
    expected_kinds: set[str],
    errors: list[str],
) -> bool:
    if not isinstance(boundary, dict):
        errors.append(f"{label} boundary is missing or invalid")
        return False
    valid = True
    event_index = boundary.get("event_index")
    if not isinstance(event_index, int) or isinstance(event_index, bool) or event_index < 0:
        errors.append(f"{label} boundary has an invalid event_index")
        valid = False
    line = boundary.get("line")
    if not isinstance(line, int) or isinstance(line, bool) or line <= 0:
        errors.append(f"{label} boundary has an invalid line")
        valid = False
    if not _nonempty_text(boundary.get("turn_id")):
        errors.append(f"{label} boundary has an invalid turn_id")
        valid = False
    if boundary.get("kind") not in expected_kinds:
        errors.append(f"{label} boundary has an invalid kind")
        valid = False
    return valid


def _boundary_matches(left: object, right: object) -> bool:
    return (
        isinstance(left, dict)
        and isinstance(right, dict)
        and all(left.get(field) == right.get(field) for field in BOUNDARY_IDENTITY_FIELDS)
    )


def _read_json_object(path: Path, label: str, errors: list[str]) -> dict[str, object] | None:
    if path.is_symlink():
        errors.append(f"{label} inseguro: link simbólico não permitido")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append(f"{label} inválido")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} inválido")
        return None
    return value


def _validate_main_chat_artifacts(feature: Path, plan: str) -> list[str]:
    if not _has_exact_visible_declaration(plan, MAIN_CHAT_ATTRIBUTION_DECLARATION):
        return []

    errors: list[str] = []
    window_path = feature / "task-window.json"
    report_path = feature / "task-window-report.json"
    if not window_path.is_file():
        errors.append("arquivo ausente: task-window.json")
    if not report_path.is_file():
        errors.append("arquivo ausente: task-window-report.json")
    if errors:
        return errors

    window = _read_json_object(window_path, "task-window.json", errors)
    report = _read_json_object(report_path, "task-window-report.json", errors)
    if window is None or report is None:
        return errors

    window_valid = True
    if window.get("schema_version") != TASK_WINDOW_SCHEMA_VERSION:
        errors.append("task-window.json tem schema incompatível")
        window_valid = False
    if not _nonempty_text(window.get("task_id")):
        errors.append("task-window.json lacks task_id")
        window_valid = False
    if window.get("status") != "closed":
        errors.append("task-window.json deve estar fechado")
        window_valid = False
    if "provisional" in window and window.get("provisional") is not False:
        errors.append("task-window.json não pode ser provisório")
        window_valid = False

    window_session = window.get("session")
    if not isinstance(window_session, dict):
        errors.append("task-window.json lacks session identity")
        window_valid = False
    else:
        if not _nonempty_text(window_session.get("session_id")):
            errors.append("task-window.json lacks a positive session_id")
            window_valid = False
        if not _safe_rollout_file(window_session.get("rollout_file")):
            errors.append("task-window.json has an unsafe rollout_file")
            window_valid = False
        if "path" in window_session:
            errors.append("task-window.json must not persist a session path")
            window_valid = False

    window_start = window.get("start")
    window_end = window.get("end")
    if not _valid_boundary(window_start, "task-window start", {"task_started"}, errors):
        window_valid = False
    if not _valid_boundary(window_end, "task-window end", TASK_WINDOW_END_KINDS, errors):
        window_valid = False
    if (
        isinstance(window_start, dict)
        and isinstance(window_end, dict)
        and window_start.get("turn_id") != window_end.get("turn_id")
    ):
        errors.append("task-window.json end boundary does not match its start turn")
        window_valid = False

    report_valid = True
    if report.get("schema_version") != TASK_WINDOW_SCHEMA_VERSION:
        errors.append("task-window-report.json tem schema incompatível")
        report_valid = False
    if report.get("status") != "closed":
        errors.append("task-window-report.json deve estar fechado")
        report_valid = False
    if report.get("provisional") is not False:
        errors.append("task-window-report.json deve ser não-provisório")
        report_valid = False
    if report.get("final") is not True:
        errors.append("task-window-report.json deve ser final")
        report_valid = False
    if report.get("scope") != "main-chat-orchestrator":
        errors.append("task-window-report.json deve usar scope main-chat-orchestrator")
        report_valid = False
    exclusions = report.get("exclusions")
    if not isinstance(exclusions, list) or any(
        not isinstance(item, str) or not item.strip() for item in exclusions
    ):
        errors.append("task-window-report.json deve declarar exclusões explícitas")
        report_valid = False
    else:
        folded_exclusions = [_fold(item) for item in exclusions]
        if any(
            not any(any(term in item for term in category) for item in folded_exclusions)
            for category in TASK_WINDOW_EXCLUSION_CATEGORIES
        ):
            errors.append("task-window-report.json possui exclusões incompletas")
            report_valid = False
    if not _nonempty_text(report.get("task_id")):
        errors.append("task-window-report.json lacks task_id")
        report_valid = False

    report_session = report.get("session")
    if not isinstance(report_session, dict):
        errors.append("task-window-report.json lacks session identity")
        report_valid = False
    else:
        if not _nonempty_text(report_session.get("session_id")):
            errors.append("task-window-report.json lacks a positive session_id")
            report_valid = False
        if not _safe_rollout_file(report_session.get("rollout_file")):
            errors.append("task-window-report.json has an unsafe rollout_file")
            report_valid = False
        if "path" in report_session:
            errors.append("task-window-report.json must not persist a session path")
            report_valid = False

    report_boundaries = report.get("boundaries")
    if not isinstance(report_boundaries, dict):
        errors.append("task-window-report.json lacks boundaries")
        report_valid = False
    else:
        report_start = report_boundaries.get("start")
        report_end = report_boundaries.get("end")
        if not _valid_boundary(report_start, "task-window-report start", {"task_started"}, errors):
            report_valid = False
        if not _valid_boundary(report_end, "task-window-report end", TASK_WINDOW_END_KINDS, errors):
            report_valid = False
        if (
            isinstance(report_start, dict)
            and isinstance(report_end, dict)
            and report_start.get("turn_id") != report_end.get("turn_id")
        ):
            errors.append("task-window-report.json end boundary does not match its start turn")
            report_valid = False
        if window_valid and (
            not _boundary_matches(report_start, window_start)
            or not _boundary_matches(report_end, window_end)
        ):
            errors.append("task-window-report.json boundaries do not match task-window.json")
            report_valid = False

    if window_valid and report_valid:
        if report.get("task_id") != window.get("task_id"):
            errors.append("task-window-report.json task_id does not match task-window.json")
        if report_session != window_session:
            errors.append("task-window-report.json session identity does not match task-window.json")

    if "cost_estimate" not in report or not isinstance(report.get("cost_estimate"), dict):
        errors.append("task-window-report.json lacks cost_estimate")
    else:
        cost_estimate = report["cost_estimate"]
        cost_status = cost_estimate.get("status")
        if cost_status == "estimated":
            total_usd = cost_estimate.get("total_usd")
            if (
                not isinstance(total_usd, (int, float))
                or isinstance(total_usd, bool)
                or not math.isfinite(total_usd)
                or total_usd <= 0
            ):
                errors.append("task-window-report.json estimated cost lacks a valid total_usd")
        elif cost_status == "not-available":
            if not _nonempty_text(cost_estimate.get("reason")):
                errors.append("task-window-report.json unavailable cost lacks a reason")
            if "total_usd" in cost_estimate:
                errors.append("task-window-report.json unavailable cost must not include total_usd")
        else:
            errors.append("task-window-report.json cost_estimate has an invalid status")
    return errors


def digest(mapping: object) -> str:
    payload = json.dumps(mapping, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_feature(
    repo: Path,
    feature: Path,
    full_map: dict[str, list[dict[str, object]]] | None = None,
) -> list[str]:
    repo = Path(repo).resolve()
    feature = (repo / Path(feature)).resolve()
    errors: list[str] = []
    if not feature.is_dir():
        errors.append(f"feature não encontrada: {feature}")
    for name in REQUIRED:
        if not (feature / name).exists():
            errors.append(f"arquivo ausente: {name}")
    if feature.is_dir() and is_v2_feature(feature):
        errors.extend(validate_v2_feature(feature))
    if not errors:
        spec = (feature / "spec.md").read_text(encoding="utf-8")
        plan = (feature / "plan.md").read_text(encoding="utf-8")
        status = (feature / "status.md").read_text(encoding="utf-8")
        evidence = (feature / "evidence.md").read_text(encoding="utf-8")
        if "{{" in spec + plan + status + evidence:
            errors.append("há placeholders não substituídos")
        criteria = sorted(set(AC_PATTERN.findall(spec)))
        if not criteria:
            errors.append("spec sem critérios de aceitação AC-xxx")
        if not TASK_PATTERN.search(plan):
            errors.append("plan sem tarefas rastreáveis T-xxx")
        for ac in criteria:
            if ac not in plan:
                errors.append(f"{ac} sem tarefa no plan")
            if f"@spec:{ac}" not in evidence:
                errors.append(f"{ac} sem teste anotado declarado em evidence.md")
        if has_open_status(spec):
            errors.append("há suposição ou pergunta aberta na spec")
        if has_open_status(status):
            errors.append("status.md indica estado aberto")
        if has_open_status(plan):
            errors.append("plan.md indica estado aberto")
        try:
            verification = json.loads((feature / "verification.json").read_text(encoding="utf-8"))
            recorded_map = verification.get("test_map", {})
            if verification.get("criteria") != criteria:
                errors.append("verification.json não corresponde aos critérios atuais")
            if verification.get("mapping_sha256") != digest(recorded_map):
                errors.append("verification.json está malformado")
            mapping = test_map(repo) if full_map is None else full_map
            current_map = {ac: mapping.get(ac, []) for ac in criteria}
            if recorded_map != current_map:
                errors.append("verification.json está obsoleto: o mapa de testes mudou")
            if not verification.get("passed") or verification.get("exit_code") != 0:
                errors.append("verificação de testes não passou")
            for ac in criteria:
                if not recorded_map.get(ac):
                    errors.append(f"{ac} sem teste anotado em código")
                if any(item.get("skipped") for item in recorded_map.get(ac, [])):
                    errors.append(f"{ac} possui teste pulado/todo")
        except (json.JSONDecodeError, OSError):
            errors.append("verification.json inválido")
        errors.extend(_validate_main_chat_artifacts(feature, plan))
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repo", type=Path)
    p.add_argument("feature", type=Path)
    args = p.parse_args()
    repo = args.repo.resolve()
    feature = (repo / args.feature).resolve()
    errors = validate_feature(repo, feature)
    if errors:
        print("FALHA")
        print("\n".join(f"- {e}" for e in errors))
        return 1
    print(f"OK: {feature}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
