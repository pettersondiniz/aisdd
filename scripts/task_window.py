#!/usr/bin/env python3
"""Track and price a bounded main-chat task window without mutating runtime logs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any

from agent_evidence import (
    TOKEN_FIELDS,
    add_components,
    context_evidence,
    cumulative_cost_estimate,
    default_pricing_config,
    default_sessions_root,
    empty_components,
    finalize_components,
    model_pricing,
    priced_components,
    request_token_usage_evidence,
    sum_usage,
    usage_evidence,
    usage_mismatches,
    usage_signature,
    usage_validation,
)


SCHEMA_VERSION = 1
MAIN_SESSION_SOURCES = frozenset({"vscode", "cli", "desktop", "codex", "user"})
MAIN_THREAD_SOURCES = frozenset({"user", "main"})
END_BOUNDARY_KINDS = frozenset({"task_complete", "turn_aborted"})
BOUNDARY_IDENTITY_FIELDS = ("event_index", "line", "kind", "turn_id")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_session(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, 1):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as error:
                    events.append({
                        "_line": line_number,
                        "_jsonl_error": {
                            "line": line_number,
                            "column": error.colno,
                            "message": error.msg,
                        },
                    })
                    continue
                if not isinstance(event, dict):
                    events.append({
                        "_line": line_number,
                        "_jsonl_error": {
                            "line": line_number,
                            "column": 1,
                            "message": "JSONL record is not an object",
                        },
                    })
                    continue
                event["_line"] = line_number
                events.append(event)
    except OSError:
        return []
    return events


def jsonl_errors(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        error = event.get("_jsonl_error")
        if not isinstance(error, dict):
            continue
        errors.append({**error, "event_index": index})
    return errors


def _positive_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _session_meta_payloads(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for event in events:
        if event.get("type") != "session_meta":
            continue
        payload = event.get("payload")
        if isinstance(payload, dict):
            payloads.append(payload)
        else:
            payloads.append({})
    return payloads


def _is_subagent_metadata(payload: dict[str, Any]) -> bool:
    if payload.get("thread_source") == "subagent" or "subagent" in payload:
        return True
    source = payload.get("source")
    return isinstance(source, dict) and "subagent" in source


def _is_recognized_main_metadata(payload: dict[str, Any]) -> bool:
    if not _positive_text(payload.get("session_id")):
        return False
    thread_source = payload.get("thread_source")
    if thread_source is not None and thread_source not in MAIN_THREAD_SOURCES:
        return False
    if "source" not in payload:
        return thread_source in MAIN_THREAD_SOURCES
    source = payload["source"]
    if isinstance(source, str):
        return source in MAIN_SESSION_SOURCES
    if isinstance(source, dict):
        return set(source) == {"user"} and _positive_text(source.get("user"))
    return False


def main_session_id(events: list[dict[str, Any]]) -> str:
    payloads = _session_meta_payloads(events)
    if not payloads:
        raise ValueError("the selected session lacks recognized positive session_meta metadata")
    if any(_is_subagent_metadata(payload) for payload in payloads):
        raise ValueError("the selected session contains subagent metadata")
    if any(not _is_recognized_main_metadata(payload) for payload in payloads):
        raise ValueError("the selected session contains unrecognized or contradictory session_meta metadata")
    identifiers = {payload["session_id"].strip() for payload in payloads}
    if not identifiers:
        raise ValueError("the selected session lacks recognized positive session_meta metadata")
    if len(identifiers) != 1:
        raise ValueError("the selected session has conflicting session_meta session_id values")
    return identifiers.pop()


def session_id(events: list[dict[str, Any]], path: Path) -> str:
    del path
    return main_session_id(events)


def is_main_session(events: list[dict[str, Any]]) -> bool:
    try:
        main_session_id(events)
    except ValueError:
        return False
    return True


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_boundary_record(
    boundary: Any,
    label: str,
    expected_kinds: set[str] | frozenset[str],
) -> None:
    if not isinstance(boundary, dict):
        raise ValueError(f"task-window.json lacks a {label} boundary")
    if not _is_nonnegative_int(boundary.get("event_index")):
        raise ValueError(f"task-window.json {label} boundary has an invalid event_index")
    if not _is_positive_int(boundary.get("line")):
        raise ValueError(f"task-window.json {label} boundary has an invalid line")
    if not _positive_text(boundary.get("turn_id")):
        raise ValueError(f"task-window.json {label} boundary has an invalid turn_id")
    if boundary.get("kind") not in expected_kinds:
        raise ValueError(f"task-window.json {label} boundary has an invalid kind")


def boundary_events(events: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    starts: dict[str, dict[str, Any]] = {}
    ends: dict[str, dict[str, Any]] = {}
    for index, event in enumerate(events):
        if event.get("type") != "event_msg":
            continue
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        kind = payload.get("type")
        turn_id = payload.get("turn_id")
        if not isinstance(turn_id, str):
            continue
        record = {
            "turn_id": turn_id,
            "timestamp": event.get("timestamp"),
            "line": event.get("_line"),
            "event_index": index,
            "kind": kind,
        }
        if kind == "task_started":
            if turn_id in starts:
                raise ValueError(f"ambiguous duplicate task_started boundary for turn_id {turn_id}")
            starts[turn_id] = record
        elif kind in END_BOUNDARY_KINDS:
            if turn_id in ends:
                raise ValueError(f"ambiguous duplicate end boundary for turn_id {turn_id}")
            ends[turn_id] = record
    return starts, ends


def open_starts(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    starts, ends = boundary_events(events)
    return [record for turn_id, record in starts.items() if turn_id not in ends]


def _find_unique_boundary(
    events: list[dict[str, Any]],
    turn_id: str,
    expected_kinds: set[str] | frozenset[str],
) -> dict[str, Any] | None:
    starts, ends = boundary_events(events)
    candidates: list[dict[str, Any]] = []
    if "task_started" in expected_kinds and turn_id in starts:
        candidates.append(starts[turn_id])
    if expected_kinds & END_BOUNDARY_KINDS and turn_id in ends:
        candidates.append(ends[turn_id])
    if len(candidates) > 1:
        raise ValueError(f"ambiguous duplicate boundary for turn_id {turn_id}")
    return candidates[0] if candidates else None


def _resolve_persisted_boundary(
    events: list[dict[str, Any]],
    persisted: dict[str, Any],
    label: str,
    expected_kinds: set[str] | frozenset[str],
) -> dict[str, Any]:
    _validate_boundary_record(persisted, label, expected_kinds)
    actual = _find_unique_boundary(events, persisted["turn_id"], {persisted["kind"]})
    if actual is None:
        raise ValueError(f"{label} boundary no longer exists in the session")
    for field in BOUNDARY_IDENTITY_FIELDS:
        if actual.get(field) != persisted.get(field):
            raise ValueError(f"{label} boundary identity does not match the session")
    return actual


def load_main_session(path: Path) -> tuple[Path, list[dict[str, Any]]]:
    events = read_session(path)
    if not events:
        raise ValueError(f"main session is empty or unreadable: {path}")
    main_session_id(events)
    return path, events


def select_main_session(sessions_root: Path, session_file: Path | None, session_selector: str | None) -> tuple[Path, list[dict[str, Any]], dict[str, Any]]:
    sessions_root = _resolved_sessions_root(sessions_root)
    if session_file is not None:
        path = _resolve_existing_path(session_file, "--session-file")
        if not _path_is_within(sessions_root, path):
            raise ValueError("--session-file must resolve within --sessions-root")
        path, events = load_main_session(path)
        return path, events, {"method": "explicit-session-file"}

    candidates: list[tuple[Path, list[dict[str, Any]], dict[str, Any]]] = []
    for discovered_path in sessions_root.rglob("rollout-*.jsonl"):
        path = _resolve_existing_path(discovered_path, "rollout candidate")
        if not _path_is_within(sessions_root, path):
            raise ValueError("rollout candidate resolves outside --sessions-root")
        if not path.is_file():
            continue
        events = read_session(path)
        if not events or not is_main_session(events):
            continue
        if session_selector and session_id(events, path) != session_selector and path.name != session_selector:
            continue
        starts = open_starts(events)
        if starts:
            latest = max(starts, key=lambda item: item.get("event_index", -1))
            candidates.append((path, events, {"method": "latest-open-main-session", "start_turn_id": latest["turn_id"]}))
    if not candidates:
        raise ValueError("no open main-chat task was found; pass --session-file or --session-id")
    if len(candidates) > 1:
        if session_selector:
            raise ValueError("session selector resolves to multiple open main sessions")
        raise ValueError("multiple open main sessions found; pass --session-file or --session-id")
    return candidates[0]


def write_window(path: Path, window: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(window, ensure_ascii=False, indent=2) + "\n"
    existing_mode: int | None = None
    try:
        existing_mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        pass
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as target:
            temporary_path = Path(target.name)
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
        if existing_mode is not None:
            os.chmod(temporary_path, existing_mode)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def read_window(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid task-window.json: {path}") from error
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported task-window schema")
    if not isinstance(data.get("task_id"), str) or not data["task_id"].strip():
        raise ValueError("task-window.json lacks task_id")
    session = data.get("session")
    if not isinstance(session, dict):
        raise ValueError("task-window.json lacks session identity")
    if not _positive_text(session.get("session_id")):
        raise ValueError("task-window.json lacks a positive session_id")
    rollout_file = session.get("rollout_file")
    if not _positive_text(rollout_file) or Path(rollout_file).name != rollout_file:
        raise ValueError("task-window.json lacks a safe rollout_file")
    if "path" in session and (not isinstance(session.get("path"), str) or not session["path"].strip()):
        raise ValueError("task-window.json has an invalid session path")
    if data.get("status") not in ("open", "closed"):
        raise ValueError("task-window.json has an invalid status")
    start = data.get("start")
    _validate_boundary_record(start, "start", {"task_started"})
    if data.get("status") == "closed":
        end = data.get("end")
        _validate_boundary_record(end, "end", END_BOUNDARY_KINDS)
        if end["turn_id"] != start["turn_id"]:
            raise ValueError("closed task-window.json end boundary does not match its start turn")
    return data


def _resolve_existing_path(path: Path, label: str) -> Path:
    try:
        return path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(f"{label} is not resolvable: {path}") from error


def _resolved_sessions_root(sessions_root: Path) -> Path:
    root = _resolve_existing_path(sessions_root, "sessions directory")
    if not root.is_dir():
        raise ValueError(f"sessions directory does not exist: {sessions_root}")
    return root


def _path_is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _resolved_path_is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def resolve_window_session(window: dict[str, Any], sessions_root: Path) -> tuple[Path, list[dict[str, Any]]]:
    sessions_root = _resolved_sessions_root(sessions_root)
    session = window["session"]
    expected_id = session["session_id"].strip()
    rollout_file = session["rollout_file"]
    stored_path = session.get("path")
    candidates: list[Path] = []
    if stored_path:
        raw_path = Path(stored_path)
        raw_candidate = raw_path if raw_path.is_absolute() else sessions_root / raw_path
        if raw_candidate.name != rollout_file:
            raise ValueError("window session path does not match rollout_file")
        candidate = _resolve_existing_path(raw_candidate, "window session path")
        if not _path_is_within(sessions_root, candidate):
            raise ValueError("window session path is outside --sessions-root")
        if candidate.name != rollout_file:
            raise ValueError("window session path does not match rollout_file")
        candidates = [candidate]
    else:
        for discovered_path in sessions_root.rglob(rollout_file):
            candidate = _resolve_existing_path(discovered_path, "rollout_file candidate")
            if not _path_is_within(sessions_root, candidate):
                raise ValueError("rollout_file candidate resolves outside --sessions-root")
            if candidate.is_file():
                candidates.append(candidate)
        candidates.sort(key=lambda candidate: str(candidate))
    if not candidates:
        raise ValueError(f"rollout_file is not present under --sessions-root: {rollout_file}")
    if len(candidates) > 1:
        raise ValueError("rollout_file resolves to multiple files under --sessions-root")
    path = candidates[0]
    _, events = load_main_session(path)
    actual_id = session_id(events, path)
    if actual_id != expected_id:
        raise ValueError("task-window session_id does not match the resolved session")
    if path.name != rollout_file:
        raise ValueError("resolved session rollout_file does not match the sidecar")
    return path, events


def _reject_session_output_collision(output: Path, sessions_root: Path, session_path: Path) -> None:
    resolved_root = _resolved_sessions_root(sessions_root)
    resolved_session = _resolve_existing_path(session_path, "selected rollout")
    try:
        resolved_output = output.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise ValueError(f"task-window output is not resolvable: {output}") from error
    if _resolved_path_is_within(resolved_root, resolved_output):
        raise ValueError(
            "task-window output must be outside --sessions-root and must not overwrite a runtime rollout"
        )

    protected_rollouts = [resolved_session]
    for discovered_path in resolved_root.rglob("rollout-*.jsonl"):
        candidate = _resolve_existing_path(discovered_path, "rollout candidate")
        if not _path_is_within(resolved_root, candidate):
            raise ValueError("rollout candidate resolves outside --sessions-root")
        if candidate.is_file():
            protected_rollouts.append(candidate)
    if not output.exists():
        return
    for candidate in protected_rollouts:
        try:
            if os.path.samefile(output, candidate):
                raise ValueError("task-window output must not overwrite a runtime rollout")
        except OSError:
            continue


def start_window(args: argparse.Namespace) -> dict[str, Any]:
    path, events, selection = select_main_session(args.sessions_root, args.session_file, args.session_id)
    _reject_session_output_collision(args.output, args.sessions_root, path)
    starts = open_starts(events)
    if not starts:
        raise ValueError("no open task_started event exists in the selected main session")
    start = max(starts, key=lambda item: item.get("event_index", -1))
    window = {
        "schema_version": SCHEMA_VERSION,
        "task_id": args.task_id,
        "status": "open",
        "session": {
            "session_id": session_id(events, path),
            "rollout_file": path.name,
        },
        "start": start,
        "end": None,
        "selection": selection,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    if args.output.exists() and not args.force:
        raise ValueError(f"task-window already exists: {args.output}; use --force to replace it")
    write_window(args.output, window)
    return {"status": "created", "window": window, "output": str(args.output)}


def close_window(args: argparse.Namespace) -> dict[str, Any]:
    window = read_window(args.window)
    end_turn_id = getattr(args, "end_turn_id", None)
    if not end_turn_id:
        raise ValueError("--end-turn-id is required")
    sessions_root = getattr(args, "sessions_root", default_sessions_root())
    _, events = resolve_window_session(window, sessions_root)
    start = _resolve_persisted_boundary(events, window["start"], "start", {"task_started"})
    if window.get("status") == "closed":
        end = _resolve_persisted_boundary(events, window["end"], "end", END_BOUNDARY_KINDS)
        saved_end_turn_id = end["turn_id"]
        if end_turn_id != saved_end_turn_id:
            raise ValueError("--end-turn-id must match the saved window end turn_id")
        return {"status": "already-closed", "window": window}
    if end_turn_id != start["turn_id"]:
        raise ValueError("--end-turn-id must match the window start turn_id")
    end = _find_unique_boundary(events, end_turn_id, END_BOUNDARY_KINDS)
    if end is None:
        raise ValueError("--end-turn-id must identify a completed or aborted task turn")
    if end["event_index"] < start["event_index"]:
        raise ValueError("window end precedes window start")
    window["status"] = "closed"
    window["end"] = end
    window["updated_at"] = now_iso()
    write_window(args.window, window)
    return {"status": "closed", "window": window}


def zero_usage() -> dict[str, int]:
    return {field: 0 for field in TOKEN_FIELDS}


def subtract_usage(end: dict[str, Any], start: dict[str, Any]) -> dict[str, int] | None:
    delta = {field: end.get(field, 0) - start.get(field, 0) for field in TOKEN_FIELDS}
    if any(value < 0 for value in delta.values()):
        return None
    return delta


def usage_record(usage: dict[str, Any]) -> dict[str, Any]:
    return {field: usage.get(field) for field in TOKEN_FIELDS} | {
        "timestamp": usage.get("timestamp"),
        "unavailable_categories": usage.get("unavailable_categories", []),
    }


def window_events(window: dict[str, Any], events: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    start = _resolve_persisted_boundary(events, window["start"], "start", {"task_started"})
    end = None
    if window.get("status") == "closed":
        end = _resolve_persisted_boundary(events, window["end"], "end", END_BOUNDARY_KINDS)
        if end["turn_id"] != start["turn_id"]:
            raise ValueError("window end boundary does not match the start turn_id")
    end_index = end["event_index"] if end else len(events) - 1
    if end_index < start["event_index"]:
        raise ValueError("window end precedes window start")
    return start, end, events[start["event_index"]: end_index + 1]


def _is_context_compacted(event: dict[str, Any]) -> bool:
    if event.get("type") == "context_compacted":
        return True
    if event.get("type") != "event_msg":
        return False
    payload = event.get("payload")
    return isinstance(payload, dict) and payload.get("type") == "context_compacted"


def _is_neutral_world_state(event: dict[str, Any]) -> bool:
    if event.get("type") != "world_state":
        return False
    payload = event.get("payload")
    return (
        isinstance(payload, dict)
        and set(payload) == {"full", "state"}
        and payload.get("full") is True
        and isinstance(payload.get("state"), dict)
    )


def _is_compaction_usage(usage: dict[str, Any] | None) -> bool:
    if usage is None:
        return False
    return (
        usage.get("input_tokens") == 0
        and usage.get("cached_input_tokens") == 0
        and usage.get("cache_write_input_tokens") == 0
        and usage.get("output_tokens") == 0
        and usage.get("reasoning_output_tokens") == 0
        and isinstance(usage.get("total_tokens"), int)
        and usage["total_tokens"] > 0
    )


def compaction_snapshots(events: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Identify only the runtime's explicit context-compaction accounting sequence."""
    snapshots: dict[int, dict[str, Any]] = {}
    compacted_indices = [index for index, event in enumerate(events) if event.get("type") == "compacted"]
    for marker_index in compacted_indices:
        next_marker = next(
            (index for index in compacted_indices if index > marker_index),
            len(events),
        )
        context_indices = [
            index
            for index in range(marker_index + 1, next_marker)
            if _is_context_compacted(events[index])
        ]
        if len(context_indices) != 1:
            continue
        context_index = context_indices[0]
        between = events[marker_index + 1:context_index]
        if (
            len(between) != 3
            or not _is_neutral_world_state(between[0])
            or between[1].get("type") != "turn_context"
            or not _is_token_count_event(between[2])
        ):
            continue
        token_index = marker_index + 3
        candidate = events[token_index]
        request = request_token_usage_evidence(candidate)
        cumulative = usage_evidence(candidate, "total_token_usage")
        if (
            not _is_compaction_usage(request)
            or cumulative is None
            or usage_validation(cumulative)["status"] != "valid"
        ):
            continue
        snapshots[token_index] = {
            "reason": "context-compaction-accounting",
            "compacted_event_index": marker_index,
            "compacted_line": events[marker_index].get("_line"),
            "world_state_event_index": marker_index + 1,
            "world_state_line": events[marker_index + 1].get("_line"),
            "token_count_event_index": token_index,
            "token_count_line": candidate.get("_line"),
            "context_compacted_event_index": context_index,
            "context_compacted_line": events[context_index].get("_line"),
            "last_token_usage": usage_record(request),
            "total_token_usage": usage_record(cumulative),
        }
    return snapshots


def baseline_usage(events: list[dict[str, Any]], start_index: int) -> tuple[dict[str, int] | None, str]:
    last: dict[str, Any] | None = None
    activity_since_snapshot = False
    for event in events[:start_index]:
        if event.get("_jsonl_error") is not None:
            return None, "pre-window-jsonl-errors"
        if _is_token_count_event(event) and not _has_usage_field(event, "last_token_usage"):
            return None, "pre-window-token-count-missing-last-usage"
        total = usage_evidence(event, "total_token_usage") if _is_token_count_event(event) else None
        if total is not None:
            if usage_validation(total)["status"] != "valid":
                return None, "pre-window-cumulative-usage-invalid"
            last = total
            activity_since_snapshot = False
            continue
        if (_is_token_count_event(event) and _has_usage_field(event, "last_token_usage")) or _is_activity_event(event):
            if event.get("type") == "turn_context" and last is not None:
                continue
            activity_since_snapshot = True
    if last is not None:
        if activity_since_snapshot:
            return None, "pre-window-activity-after-last-cumulative-snapshot"
        return {field: last[field] for field in TOKEN_FIELDS}, "last-readable-total-before-window"
    if activity_since_snapshot:
        return None, "pre-window-activity-without-readable-baseline"
    return zero_usage(), "zero-session-baseline"


def _has_usage_field(event: dict[str, Any], field: str) -> bool:
    if not _is_token_count_event(event):
        return False
    payload = event.get("payload")
    info = payload.get("info") if isinstance(payload, dict) else None
    return isinstance(info, dict) and field in info


def _is_token_count_event(event: dict[str, Any]) -> bool:
    if event.get("type") != "event_msg":
        return False
    payload = event.get("payload")
    return isinstance(payload, dict) and payload.get("type") == "token_count"


def _is_activity_event(event: dict[str, Any]) -> bool:
    event_type = event.get("type")
    if event_type == "response_item":
        return True
    if event_type == "turn_context":
        return True
    if event_type != "event_msg":
        return False
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return True
    activity_type = payload.get("type")
    if activity_type in {
        "task_started",
        "task_complete",
        "turn_aborted",
        "thread_settings_applied",
        "user_message",
        "patch_apply_begin",
        "patch_apply_end",
        "patch_apply_failure",
        "patch_apply_start",
        "patch_apply_finish",
        "compacted",
        "context_compacted",
    }:
        return False
    if isinstance(activity_type, str) and (
        activity_type.startswith("patch_") or activity_type.startswith("apply_patch_")
    ):
        return False
    return True


def model_for_event(context: dict[str, Any] | None) -> dict[str, Any]:
    if not context:
        return {"model": "unknown", "reasoning_effort": "unknown"}
    model = context.get("model")
    reasoning_effort = context.get("reasoning_effort")
    if model is not None and not isinstance(model, str):
        raise ValueError("turn_context model metadata is malformed")
    if reasoning_effort is not None and not isinstance(reasoning_effort, str):
        raise ValueError("turn_context reasoning metadata is malformed")
    return {
        "model": model.strip() if isinstance(model, str) and model.strip() else "unknown",
        "reasoning_effort": (
            reasoning_effort.strip()
            if isinstance(reasoning_effort, str) and reasoning_effort.strip()
            else "unknown"
        ),
    }


def _validate_context_string_fields(payload: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if field in payload and payload[field] is not None and not isinstance(payload[field], str):
            raise ValueError(f"turn_context {label}.{field} metadata is malformed")


def validated_context_evidence(event: dict[str, Any]) -> dict[str, Any] | None:
    if event.get("type") != "turn_context":
        return None
    payload = event.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("turn_context metadata is malformed")
    _validate_context_string_fields(payload, ("model", "reasoning_effort", "effort"), "payload")
    collaboration = payload.get("collaboration_mode")
    if collaboration is not None and not isinstance(collaboration, dict):
        raise ValueError("turn_context collaboration metadata is malformed")
    if isinstance(collaboration, dict):
        _validate_context_string_fields(collaboration, ("mode",), "collaboration_mode")
        settings = collaboration.get("settings")
        if settings is not None and not isinstance(settings, dict):
            raise ValueError("turn_context settings metadata is malformed")
        if isinstance(settings, dict):
            _validate_context_string_fields(
                settings,
                ("model", "reasoning_effort", "effort"),
                "collaboration_mode.settings",
            )
    context = context_evidence(event)
    if context is None:
        raise ValueError("turn_context metadata is malformed")
    return model_for_event(context) | {
        "turn_id": context.get("turn_id"),
        "timestamp": context.get("timestamp"),
    }


def price_request_records(records: list[dict[str, Any]], pricing_path: Path, *, ignore_long_context: bool) -> dict[str, Any]:
    aggregate = empty_components()
    models: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    standard_count = 0
    long_count = 0
    for index, record in enumerate(records, 1):
        usage = record["usage"]
        validation = usage_validation(usage)
        if validation["status"] != "valid":
            return {**validation, "request_index": index}
        model = record["model"]
        pricing_context, error = model_pricing({model}, pricing_path)
        if error:
            return error
        assert pricing_context is not None
        rates = pricing_context["rates"]
        policy = pricing_context["policy"]
        apply_tiered = policy == "tiered" and not ignore_long_context
        is_long = bool(apply_tiered and usage["input_tokens"] > rates["long_context_threshold_tokens"])
        if is_long:
            input_multiplier = rates["long_context_input_multiplier"]
            output_multiplier = rates["long_context_output_multiplier"]
            long_count += 1
        else:
            input_multiplier = 1.0
            output_multiplier = 1.0
            standard_count += 1
        components = priced_components(
            usage,
            rates,
            input_multiplier=input_multiplier,
            output_multiplier=output_multiplier,
        )
        add_components(aggregate, components)
        model_entry = models.setdefault(model, {
            "model": model,
            "resolved_model": pricing_context["resolved_model"],
            "policy": "standard" if policy == "tiered" and ignore_long_context else policy,
            "request_count": 0,
            "standard_request_count": 0,
            "long_context_request_count": 0,
            "components": empty_components(),
        })
        model_entry["request_count"] += 1
        model_entry["long_context_request_count"] += int(is_long)
        model_entry["standard_request_count"] += int(not is_long)
        add_components(model_entry["components"], components)
        if policy == "tiered" and ignore_long_context and "long-context pricing was explicitly ignored; estimate may be inaccurate" not in warnings:
            warnings.append("long-context pricing was explicitly ignored; estimate may be inaccurate")
    result: dict[str, Any] = {
        "status": "estimated",
        "basis": "api-equivalent-token-only",
        "currency": "USD",
        "scope": "main-chat-task-window-last-token-usage-per-request",
        "pricing_models": sorted(models),
        "components": finalize_components(aggregate),
        "total_usd": round(sum(item["usd"] for item in aggregate.values()), 12),
        "request_count": len(records),
        "standard_request_count": standard_count,
        "long_context_request_count": long_count,
        "models": {
            model: {
                **entry,
                "components": finalize_components(entry["components"]),
            }
            for model, entry in models.items()
        },
        "exclusions": ["tool fees", "modality fees", "subscription billing"],
    }
    if warnings:
        result["warnings"] = warnings
    return result


def report_window(args: argparse.Namespace) -> dict[str, Any]:
    window = read_window(args.window)
    sessions_root = getattr(args, "sessions_root", default_sessions_root())
    _, events = resolve_window_session(window, sessions_root)
    start, end, selected = window_events(window, events)
    base, base_source = baseline_usage(events, start["event_index"])
    selected_end_index = end["event_index"] if end else len(events) - 1
    all_errors = jsonl_errors(events)
    baseline_errors = [error for error in all_errors if error["event_index"] < start["event_index"]]
    window_errors = [
        error for error in all_errors
        if start["event_index"] <= error["event_index"] <= selected_end_index
    ]
    cumulative_records: list[dict[str, Any]] = []
    cumulative_error: str | None = None
    token_count_event_count = 0
    activity_after_last_token_count = False
    for event in selected:
        if _is_token_count_event(event):
            token_count_event_count += 1
            activity_after_last_token_count = False
        else:
            if token_count_event_count and _is_activity_event(event):
                activity_after_last_token_count = True
            continue
        if not _has_usage_field(event, "total_token_usage"):
            cumulative_error = cumulative_error or "in-window cumulative telemetry is incomplete"
            continue
        if not _has_usage_field(event, "last_token_usage"):
            cumulative_error = cumulative_error or "in-window cumulative telemetry is incomplete"
            continue
        cumulative = usage_evidence(event, "total_token_usage")
        if cumulative is None or usage_validation(cumulative)["status"] != "valid":
            cumulative_error = cumulative_error or "in-window cumulative telemetry is invalid"
        if cumulative is not None:
            cumulative_records.append(cumulative)
    if activity_after_last_token_count:
        cumulative_error = cumulative_error or (
            "in-window model activity after last token_count without a new token_count"
        )
    end_total = cumulative_records[-1] if cumulative_records else None
    delta = None
    if (
        not baseline_errors
        and not window_errors
        and cumulative_error is None
        and end_total is not None
        and base is not None
        and usage_validation(end_total)["status"] == "valid"
    ):
        delta = subtract_usage(end_total, base)

    all_requests: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    request_signatures: set[tuple[tuple[Any, ...], tuple[Any, ...]]] = set()
    duplicates = 0
    current_context: dict[str, Any] | None = None
    for event in events[:start["event_index"]]:
        context = validated_context_evidence(event)
        if context:
            current_context = model_for_event(context)
    contexts: list[dict[str, Any]] = [current_context] if current_context else []
    compaction_by_index = compaction_snapshots(events)
    selected_compaction: list[dict[str, Any]] = []
    for local_index, event in enumerate(selected):
        event_index = start["event_index"] + local_index
        context = validated_context_evidence(event)
        if context:
            current_context = model_for_event(context)
            contexts.append(current_context)
        if not _is_token_count_event(event):
            continue
        request = request_token_usage_evidence(event)
        if not request:
            continue
        if event_index in compaction_by_index:
            selected_compaction.append(compaction_by_index[event_index])
            continue
        all_requests.append(request)
        cumulative = usage_evidence(event, "total_token_usage")
        if cumulative is not None:
            signature = (usage_signature(cumulative), usage_signature(request))
            if signature in request_signatures:
                duplicates += 1
                continue
            request_signatures.add(signature)
        requests.append({
            "usage": request,
            "model": (current_context or {"model": "unknown"})["model"],
            "reasoning_effort": (current_context or {"reasoning_effort": "unknown"})["reasoning_effort"],
            "timestamp": request.get("timestamp"),
        })

    invalid_requests = [item for item in all_requests if usage_validation(item)["status"] != "valid"]
    request_status = (
        "invalid"
        if invalid_requests
        else "observed"
        if all_requests and all(not item.get("unavailable_categories") for item in all_requests)
        else "partial"
        if all_requests
        else "not-available"
    )
    request_evidence: dict[str, Any] = {
        "status": request_status,
        "source": "main-session-event_msg.info.last_token_usage:task-window",
        "scope": "selected-task-window",
        "readable_snapshot_count": len(all_requests),
        "request_count": len(requests),
        "snapshots": [usage_record(item) for item in all_requests],
    }
    if duplicates:
        request_evidence["duplicate_snapshots_ignored"] = duplicates
    if selected_compaction:
        request_evidence["compaction_snapshots_excluded"] = len(selected_compaction)
        request_evidence["compaction_snapshots"] = selected_compaction
    if invalid_requests:
        request_evidence["invalid_snapshot_count"] = len(invalid_requests)
    if request_status == "observed":
        request_evidence["sum"] = sum_usage([record["usage"] for record in requests])
    else:
        request_evidence["reason"] = (
            "one or more in-window request snapshots are internally inconsistent"
            if request_status == "invalid"
            else "one or more in-window request snapshots lack required token classifications"
            if all_requests
            else "window contains only excluded compaction token_count snapshots; no priceable request"
            if selected_compaction and token_count_event_count == len(selected_compaction)
            else "window has no readable call last_token_usage metadata"
        )

    result: dict[str, Any] = {
        "status": "closed" if window.get("status") == "closed" else "open",
        "provisional": window.get("status") != "closed",
        "task_id": window["task_id"],
        "session": window["session"],
        "boundaries": {
            "start": start,
            "end": end,
            "baseline_source": base_source,
            "selected_event_count": len(selected),
        },
        "baseline_total_token_usage": base,
        "ending_total_token_usage": usage_record(end_total) if end_total else None,
        "window_token_usage": delta,
        "request_token_usage": request_evidence,
        "observed_models": sorted({record["model"] for record in requests} | {context["model"] for context in contexts}),
    }
    if selected_compaction:
        result["compaction"] = {
            "status": "observed",
            "excluded_from_request_sum": len(selected_compaction),
            "excluded_from_price": len(selected_compaction),
            "snapshots": selected_compaction,
        }
    if all_errors:
        result["jsonl_errors"] = {
            "count": len(all_errors),
            "records": all_errors,
            "affecting_baseline": baseline_errors,
            "affecting_window": window_errors,
        }
    if delta is None:
        if baseline_errors:
            reason = "baseline contains unreadable JSONL records"
        elif window_errors:
            reason = "window contains unreadable JSONL records"
        elif cumulative_error:
            reason = cumulative_error
        else:
            reason = "window lacks a valid cumulative baseline or ending total"
        result["cost_estimate"] = {"status": "not-available", "reason": reason}
    elif selected_compaction and not all_requests and token_count_event_count == len(selected_compaction):
        result["cost_estimate"] = {
            "status": "not-available",
            "reason": "window contains only excluded compaction token_count snapshots; no priceable request",
        }
    elif requests:
        calculated = sum_usage([record["usage"] for record in requests]) if request_status == "observed" else None
        mismatches = usage_mismatches(delta, calculated) if calculated is not None else {}
        if mismatches:
            result["cost_estimate"] = {
                "status": "not-available",
                "reason": "in-window request usage does not reconcile with cumulative window delta",
                "mismatches": mismatches,
            }
        elif request_status != "observed":
            result["cost_estimate"] = {
                "status": "not-available",
                "reason": (
                    "in-window request telemetry is internally inconsistent"
                    if request_status == "invalid"
                    else "in-window request telemetry is incomplete"
                ),
            }
        else:
            result["cost_estimate"] = price_request_records(
                requests,
                args.pricing_config,
                ignore_long_context=args.ignore_long_context,
            )
    else:
        models = {context["model"] for context in contexts}
        if len(models) != 1 or "unknown" in models:
            result["cost_estimate"] = {
                "status": "not-available",
                "reason": "main-chat cumulative fallback lacks one known effective model",
                "observed_models": sorted(models),
            }
        else:
            result["cost_estimate"] = cumulative_cost_estimate(
                delta,
                models,
                args.pricing_config,
                ignore_long_context=not args.respect_long_context,
            )
            result["cost_estimate"]["scope"] = "main-chat-task-window-cumulative-delta"
    if result["provisional"]:
        result.setdefault("warnings", []).append("task window is open; report is provisional until an end boundary is recorded")
    return result


def print_text(payload: dict[str, Any]) -> None:
    print(f"Status: {payload['status']}")
    print(f"Task: {payload.get('task_id', '')}")
    if payload.get("boundaries"):
        start = payload["boundaries"].get("start", {}).get("turn_id")
        end = (payload["boundaries"].get("end") or {}).get("turn_id")
        print(f"Window: {start} -> {end or '(open)'}")
    cost = payload.get("cost_estimate", {})
    if cost.get("status") == "estimated":
        print(f"Main-chat token-only cost: ${cost['total_usd']:.8f} USD")
    elif cost:
        print(f"Cost: {cost.get('status')} ({cost.get('reason', '')})")
    for warning in payload.get("warnings", []) + cost.get("warnings", []):
        print(f"Warning: {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    start = commands.add_parser("start", help="create an open main-chat task window")
    start.add_argument("--task-id", required=True)
    start.add_argument("--output", type=Path, required=True)
    start.add_argument("--sessions-root", type=Path, default=default_sessions_root())
    start.add_argument("--session-file", type=Path)
    start.add_argument("--session-id")
    start.add_argument("--force", action="store_true")
    start.add_argument("--json", action="store_true")

    close = commands.add_parser("close", help="close a task window at a completed main-chat turn")
    close.add_argument("--window", type=Path, required=True)
    close.add_argument("--sessions-root", type=Path, default=default_sessions_root())
    close.add_argument("--end-turn-id", required=True)
    close.add_argument("--json", action="store_true")

    report = commands.add_parser("report", help="report token usage and cost for a task window")
    report.add_argument("--window", type=Path, required=True)
    report.add_argument("--sessions-root", type=Path, default=default_sessions_root())
    report.add_argument("--pricing-config", type=Path, default=default_pricing_config())
    long_context_flags = report.add_mutually_exclusive_group()
    long_context_flags.add_argument("--respect-long-context", action="store_true")
    long_context_flags.add_argument("--ignore-long-context", action="store_true")
    report.add_argument("--json", action="store_true")

    args = parser.parse_args()
    try:
        if args.command == "start":
            payload = start_window(args)
        elif args.command == "close":
            payload = close_window(args)
        else:
            payload = report_window(args)
    except (OSError, ValueError) as error:
        if getattr(args, "json", False):
            print(json.dumps({"status": "not-available", "reason": str(error)}, ensure_ascii=False, indent=2))
        else:
            print(f"Status: not-available\nReason: {error}")
        return 1
    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
