#!/usr/bin/env python3
"""Read the best available local Codex model evidence for one subagent rollout."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import tomllib
from typing import Any


def default_sessions_root() -> Path:
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    return home / ".codex" / "sessions"


def default_pricing_config() -> Path:
    """Prefer the user-global table, then the skill's conservative default."""
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    configured = home / ".codex" / "aisdd" / "cost-pricing.toml"
    if configured.is_file():
        return configured
    return Path(__file__).resolve().parents[1] / "assets" / "templates" / "cost-pricing.toml"


def read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as source:
            for line in source:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    events.append(item)
    except OSError:
        return []
    return events


def find_metadata(path: Path) -> dict[str, Any] | None:
    for event in read_events(path):
        if event.get("type") != "session_meta":
            continue
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        source = payload.get("source")
        if not isinstance(source, dict):
            continue
        subagent = source.get("subagent")
        spawn = (subagent or {}).get("thread_spawn") if isinstance(subagent, dict) else None
        if isinstance(spawn, dict):
            return {"path": path, "rollout": path.name, "spawn": spawn}
    return None


def compact(candidate: dict[str, Any]) -> dict[str, Any]:
    spawn = candidate["spawn"]
    return {
        "rollout": candidate["rollout"],
        "agent_id": spawn.get("agent_path"),
        "role": spawn.get("agent_role"),
        "nickname": spawn.get("agent_nickname"),
        "parent_session_id": spawn.get("parent_thread_id"),
    }


def rollout_matches(name: str, selector: str) -> bool:
    """Match either the complete filename or its terminal UUID exactly."""
    if name.lower() == selector.lower():
        return True
    match = re.search(r"([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\.jsonl$", name, re.I)
    return bool(match and match.group(1).lower() == selector.lower())


def matches(candidate: dict[str, Any], args: argparse.Namespace) -> bool:
    spawn = candidate["spawn"]
    return (
        (not args.rollout_id or rollout_matches(candidate["rollout"], args.rollout_id))
        and
        (not args.agent_id or spawn.get("agent_path") == args.agent_id)
        and (not args.role or spawn.get("agent_role") == args.role)
        and (not args.nickname or spawn.get("agent_nickname") == args.nickname)
        and (not args.parent_session_id or spawn.get("parent_thread_id") == args.parent_session_id)
    )


def context_evidence(event: dict[str, Any]) -> dict[str, Any] | None:
    if event.get("type") != "turn_context":
        return None
    payload = event.get("payload") or {}
    if not isinstance(payload, dict):
        return None
    collaboration = payload.get("collaboration_mode") or {}
    if not isinstance(collaboration, dict):
        collaboration = {}
    settings = collaboration.get("settings") or {}
    if not isinstance(settings, dict):
        settings = {}
    model = payload.get("model") or settings.get("model")
    effort = payload.get("reasoning_effort") or payload.get("effort") or settings.get("reasoning_effort")
    if not model and not effort:
        return None
    return {
        "model": model or "unknown",
        "reasoning_effort": effort or "unknown",
        "turn_id": payload.get("turn_id"),
        "timestamp": event.get("timestamp"),
    }


TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


def token_usage_evidence(event: dict[str, Any]) -> dict[str, Any] | None:
    """Read a cumulative per-rollout token snapshot without exposing session contents."""
    if event.get("type") != "event_msg":
        return None
    payload = event.get("payload") or {}
    if not isinstance(payload, dict):
        return None
    info = payload.get("info") or {}
    if not isinstance(info, dict):
        return None
    usage = info.get("total_token_usage")
    if not isinstance(usage, dict):
        return None

    result: dict[str, Any] = {"timestamp": event.get("timestamp")}
    available = 0
    unavailable: list[str] = []
    for field in TOKEN_FIELDS:
        value = usage.get(field)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            result[field] = value
            available += 1
        else:
            result[field] = None
            unavailable.append(field)
    if not available:
        return None
    result["unavailable_categories"] = unavailable
    return result


def load_pricing(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as source:
            data = tomllib.load(source)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"pricing configuration is not readable: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("models"), dict):
        raise ValueError("pricing configuration has no [models] table")
    return data


def valid_number(value: Any, *, positive: bool = False) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and (value > 0 if positive else value >= 0)
    )


def cost_estimate(usage: dict[str, Any], observed_models: set[str], pricing_path: Path, *, ignore_long_context: bool) -> dict[str, Any]:
    required = TOKEN_FIELDS
    missing = [field for field in required if usage.get(field) is None]
    if missing:
        return {
            "status": "not-available",
            "reason": "token usage lacks the classifications required for an honest estimate",
            "missing_fields": missing,
        }
    if len(observed_models) != 1:
        return {
            "status": "not-available",
            "reason": "multiple-or-unknown-models-in-cumulative-rollout",
            "observed_models": sorted(observed_models),
        }
    model = next(iter(observed_models))
    try:
        pricing = load_pricing(pricing_path)
    except ValueError as error:
        return {"status": "not-available", "reason": str(error)}

    aliases = pricing.get("aliases") if isinstance(pricing.get("aliases"), dict) else {}
    resolved_model = aliases.get(model, model)
    models = pricing["models"]
    rates = models.get(resolved_model) if isinstance(resolved_model, str) else None
    if not isinstance(rates, dict):
        return {
            "status": "not-available",
            "reason": "no API-equivalent price is configured for the observed model",
            "observed_model": model,
        }
    rate_fields = (
        "input_per_million",
        "cached_input_per_million",
        "cache_write_input_per_million",
        "output_per_million",
    )
    if any(not valid_number(rates.get(field)) for field in rate_fields):
        return {"status": "not-available", "reason": "configured model has incomplete API-equivalent prices"}

    input_tokens = usage["input_tokens"]
    cached = usage["cached_input_tokens"]
    cache_write = usage["cache_write_input_tokens"]
    output = usage["output_tokens"]
    reasoning = usage["reasoning_output_tokens"]
    total = usage["total_tokens"]
    if cached > input_tokens or reasoning > output or total != input_tokens + output:
        return {
            "status": "not-available",
            "reason": "token usage classifications are internally inconsistent",
        }

    threshold = rates.get("long_context_threshold_tokens")
    if threshold is not None and (not isinstance(threshold, int) or isinstance(threshold, bool) or threshold <= 0):
        return {"status": "not-available", "reason": "configured long-context threshold is invalid"}
    if isinstance(threshold, int) and input_tokens > threshold:
        if ignore_long_context:
            long_context_warning = "long-context pricing was explicitly ignored; estimate may be inaccurate"
        else:
            return {
                "status": "not-available",
                "reason": "cumulative-token-usage-cannot-price-long-context-per-request",
            }
    else:
        long_context_warning = None

    components = {
        "input": (input_tokens - cached, rates["input_per_million"]),
        "cached_input": (cached, rates["cached_input_per_million"]),
        "cache_write_input": (cache_write, rates["cache_write_input_per_million"]),
        "output": (output, rates["output_per_million"]),
    }
    priced_components = {
        name: {"tokens": tokens, "usd": round(tokens * rate / 1_000_000, 12)}
        for name, (tokens, rate) in components.items()
    }
    result = {
        "status": "estimated",
        "basis": f"{pricing.get('pricing_basis', 'api-equivalent')}-token-only",
        "currency": pricing.get("currency", "USD"),
        "pricing_updated_at": pricing.get("updated_at"),
        "pricing_model": resolved_model,
        "components": priced_components,
        "total_usd": round(sum(item["usd"] for item in priced_components.values()), 12),
        "exclusions": ["tool fees", "modality fees", "subscription billing"],
    }
    if long_context_warning:
        result["warnings"] = [long_context_warning]
    return result


def resolve(args: argparse.Namespace) -> dict[str, Any]:
    if not any((args.rollout_id, args.agent_id, args.role, args.nickname, args.parent_session_id)):
        raise ValueError("provide at least one selector")
    if not args.sessions_root.is_dir():
        return {"status": "not-available", "reason": "local Codex sessions directory was not found"}

    files = args.sessions_root.rglob("rollout-*.jsonl")
    candidates = [candidate for path in files if (candidate := find_metadata(path)) and matches(candidate, args)]
    if not candidates:
        return {"status": "not-found", "reason": "no matching subagent rollout was found"}
    if len(candidates) != 1:
        return {
            "status": "ambiguous",
            "reason": "more than one subagent rollout matched; refine the selectors",
            "candidates": [compact(candidate) for candidate in candidates],
        }

    candidate = candidates[0]
    contexts = [evidence for event in read_events(candidate["path"]) if (evidence := context_evidence(event))]
    if not contexts:
        return {
            "status": "not-available",
            "reason": "matching rollout has no readable turn_context model metadata",
            "candidate": compact(candidate),
        }
    result: dict[str, Any] = {
        "status": "resolved",
        "source": "local-rollout-turn_context:last-readable",
        "effective": contexts[-1],
        "effective_scope": "last-readable-turn-context",
        "turn_context_count": len(contexts),
        "candidate": compact(candidate),
    }
    usage = [evidence for event in read_events(candidate["path"]) if (evidence := token_usage_evidence(event))]
    if not usage:
        result["token_usage"] = {
            "status": "not-available",
            "reason": "matching rollout has no readable cumulative token usage metadata",
        }
        return result
    result["token_usage"] = {
        "status": "observed" if not usage[-1]["unavailable_categories"] else "partial",
        "source": "local-rollout-event_msg.info.total_token_usage:last-readable",
        "scope": "last-readable-rollout-total",
        **usage[-1],
    }
    observed_models = {
        context["model"]
        for context in contexts
        if isinstance(context.get("model"), str) and context["model"] != "unknown"
    }
    result["cost_estimate"] = cost_estimate(
        result["token_usage"], observed_models, args.pricing_config,
        ignore_long_context=not args.respect_long_context,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions-root", type=Path, default=default_sessions_root())
    parser.add_argument("--pricing-config", type=Path, default=default_pricing_config())
    parser.add_argument("--respect-long-context", action="store_true", help="Refuse an estimate when cumulative input crosses the long-context threshold and request-level telemetry is unavailable.")
    parser.add_argument("--rollout-id", help="Exact terminal UUID or complete rollout filename.")
    parser.add_argument("--agent-id")
    parser.add_argument("--role")
    parser.add_argument("--nickname")
    parser.add_argument("--parent-session-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        payload = resolve(args)
    except ValueError as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Status: {payload['status']}")
        if payload["status"] == "resolved":
            effective = payload["effective"]
            print(f"Effective: {effective['model']} / {effective['reasoning_effort']}")
            print(f"Source: {payload['source']} ({payload['candidate']['rollout']})")
            if payload.get("cost_estimate", {}).get("status") == "estimated":
                print(f"Token-only API-equivalent cost: ${payload['cost_estimate']['total_usd']:.8f} USD")
        elif "reason" in payload:
            print(f"Reason: {payload['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
