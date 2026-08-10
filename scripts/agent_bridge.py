#!/usr/bin/env python3
"""Optional, read-only Agent Bridge adapter used by model routing.

The adapter deliberately depends on a small injected client protocol.  This
keeps Agent Bridge optional for the AISDD process and makes the MCP boundary
easy to replace without importing or changing the Agent Bridge project.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any


NOT_AVAILABLE = "not-available"
TERMINAL_STATES = {
    "completed", "complete", "succeeded", "success", "failed", "error",
    "cancelled", "canceled", "timeout", "timed-out", "timed_out",
}


def _call(client: Any, operation: str, arguments: dict[str, Any]) -> Any:
    method = getattr(client, operation, None)
    if callable(method):
        return method(**arguments)
    for name in ("call_tool", "call"):
        method = getattr(client, name, None)
        if callable(method):
            return method(operation, arguments)
    if isinstance(client, Mapping):
        method = client.get(operation)
        if callable(method):
            return method(arguments)
    raise TypeError("Agent Bridge client must expose MCP operation methods")


def _is_error(value: Any) -> bool:
    """Return whether an MCP result explicitly reports an error."""
    return isinstance(value, Mapping) and value.get("isError") is True


def _payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        structured = value.get("structuredContent")
        if structured is not None:
            return structured
        content = value.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, Mapping) and item.get("type") == "text":
                    try:
                        return json.loads(str(item.get("text", "")))
                    except (TypeError, ValueError):
                        return {"text": item.get("text", "")}
        return value
    return value


def _models(value: Any) -> list[dict[str, Any]]:
    payload = _payload(value)
    candidates = payload.get("models", []) if isinstance(payload, Mapping) else []
    if not isinstance(candidates, list):
        return []
    return [item for item in candidates if isinstance(item, Mapping) and isinstance(item.get("id"), str)]


def _job_id(value: Any) -> str | None:
    payload = _payload(value)
    if isinstance(payload, Mapping) and isinstance(payload.get("job_id"), str):
        return payload["job_id"]
    return None


def _session_id(value: Any) -> str | None:
    payload = _payload(value)
    if isinstance(payload, Mapping) and isinstance(payload.get("session_id"), str):
        return payload["session_id"]
    return None


def _status(value: Any) -> str:
    payload = _payload(value)
    if not isinstance(payload, Mapping):
        return "unknown"
    raw = payload.get("status", payload.get("state", "unknown"))
    return str(raw).strip().lower()


def _changed_paths(value: Any) -> list[Any]:
    payload = _payload(value)
    if not isinstance(payload, Mapping):
        return []
    changed = payload.get("changed_paths")
    return changed if isinstance(changed, list) else []


def _result_text(value: Any) -> str | None:
    payload = _payload(value)
    if not isinstance(payload, Mapping):
        return str(payload) if payload is not None else None
    for key in ("text", "result", "output", "message"):
        item = payload.get(key)
        if isinstance(item, str):
            return item
    return None


def _evidence(*, model: str, job_id: str | None, status: str, error: str | None,
              changed_paths: list[Any], result: str | None, session_id: str | None) -> dict[str, Any]:
    return {
        "provider": "agent-bridge",
        "model": model,
        "job_id": job_id,
        "session_id": session_id,
        "status": status,
        "error": error,
        "changed_paths": changed_paths,
        "result": result,
        "cost": NOT_AVAILABLE,
    }


def delegate_read_only(
    client: Any,
    external: Mapping[str, Any],
    *,
    workspace: str,
    prompt: str,
    session_id: str | None = None,
    timeout_ms: int | None = None,
    max_polls: int = 100,
) -> dict[str, Any]:
    """Discover, exact-match, start and wait for one external read job.

    The external model is attempted at most once.  Configuration is validated
    before the first MCP operation, including the write-profile guard.
    """
    provider = external.get("provider")
    profile = external.get("profile")
    model = external.get("model")
    def failure(stage: str, error: str, *, job_id: str | None = None, status: str = "failed", changed_paths: list[Any] | None = None, result: str | None = None, observed_session_id: str | None = session_id) -> dict[str, Any]:
        evidence = _evidence(model=model if isinstance(model, str) else "", job_id=job_id, status=status, error=error, changed_paths=changed_paths or [], result=result, session_id=observed_session_id)
        return {"ok": False, "stage": stage, **evidence, "metadata": evidence}

    if provider != "agent-bridge":
        return failure("config", "external provider must be agent-bridge")
    if profile != "read":
        return failure("config", "external profile must be read")
    if not isinstance(model, str):
        return failure("config", "external model must be a string")

    try:
        catalog_result = _call(client, "external_models", {"workspace": workspace})
        if _is_error(catalog_result):
            return failure("discovery", "external_models returned isError=true")
        catalog = _models(catalog_result)
    except Exception as error:  # MCP is optional; route failure is evidence, not a crash.
        return failure("discovery", str(error))
    if not any(item["id"] == model for item in catalog):
        return failure("discovery", "external model id is not available")

    arguments: dict[str, Any] = {"workspace": workspace, "prompt": prompt, "model": model, "profile": "read"}
    if session_id is not None:
        arguments["session_id"] = session_id
    if timeout_ms is not None:
        arguments["timeout_ms"] = timeout_ms
    try:
        started = _call(client, "delegate_start", arguments)
        if _is_error(started):
            return failure("start", "delegate_start returned isError=true")
        job_id = _job_id(started)
        observed_session_id = _session_id(started) or session_id
        if not job_id:
            return failure("start", "delegate_start returned no job_id", observed_session_id=observed_session_id)
    except Exception as error:
        return failure("start", str(error), observed_session_id=session_id)

    cursor: int | None = None
    try:
        final: Any = None
        for _ in range(max_polls):
            wait_args: dict[str, Any] = {"job_id": job_id, "max_events": 100, "wait_ms": timeout_ms or 1000}
            if cursor is not None:
                wait_args["cursor"] = cursor
            final = _call(client, "delegate_wait", wait_args)
            if _is_error(final):
                return failure("wait", "delegate_wait returned isError=true", job_id=job_id, observed_session_id=observed_session_id)
            payload = _payload(final)
            if isinstance(payload, Mapping) and isinstance(payload.get("cursor"), int):
                cursor = payload["cursor"]
            status = _status(final)
            if status in TERMINAL_STATES:
                break
        else:
            status = "timeout"
            final = {"status": status}
    except Exception as error:
        return failure("wait", str(error), job_id=job_id, observed_session_id=observed_session_id)

    status = _status(final)
    changed = _changed_paths(final)
    text = _result_text(final)
    success_status = status in {"completed", "complete", "succeeded", "success"}
    error = None if success_status else (text or status)
    payload = _payload(final)
    changed_paths_valid = isinstance(payload, Mapping) and isinstance(payload.get("changed_paths"), list) and not payload["changed_paths"]
    ok = success_status and changed_paths_valid and bool(text)
    if success_status and changed:
        error = "read-only result reported changed_paths"
    elif success_status and not changed_paths_valid:
        error = "read-only result must report changed_paths as an empty list"
    elif success_status and not text:
        error = "read-only result must report non-empty final text"
    evidence = _evidence(model=model, job_id=job_id, status=status, error=error, changed_paths=changed, result=text, session_id=observed_session_id)
    return {"ok": ok, "stage": "result", "text": text if ok else None, "metadata": evidence, **evidence}


def route_with_fallback(
    external_call: Callable[[], dict[str, Any]],
    openai_specific: Callable[[], Any],
    openai_general: Callable[[], Any],
) -> dict[str, Any]:
    """Apply external -> specific OpenAI -> general fallback exactly once each."""
    external_result = external_call()
    if external_result.get("ok"):
        return {"route": "external", "result": external_result, "fallback": None}
    try:
        specific = openai_specific()
        return {"route": "openai-specific", "result": specific, "external": external_result, "fallback": "specific"}
    except Exception as specific_error:
        try:
            general = openai_general()
            return {"route": "openai-general", "result": general, "external": external_result, "specific_error": str(specific_error), "fallback": "general"}
        except Exception as general_error:
            return {"route": "failed", "external": external_result, "specific_error": str(specific_error), "general_error": str(general_error), "fallback": "general"}
