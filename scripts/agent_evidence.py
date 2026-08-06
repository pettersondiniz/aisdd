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
    try:
        with path.open(encoding="utf-8") as source_file:
            for line in source_file:
                if not re.search(r'"type"\s*:\s*"session_meta"', line):
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict) or event.get("type") != "session_meta":
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
    except OSError:
        return None
    return None


def compact(candidate: dict[str, Any]) -> dict[str, Any]:
    spawn = candidate["spawn"]
    def scalar(value: Any) -> str | None:
        return value if isinstance(value, str) else None

    return {
        "rollout": candidate["rollout"],
        "agent_id": scalar(spawn.get("agent_path")),
        "role": scalar(spawn.get("agent_role")),
        "nickname": scalar(spawn.get("agent_nickname")),
        "parent_session_id": scalar(spawn.get("parent_thread_id")),
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


def usage_evidence(event: dict[str, Any], usage_field: str) -> dict[str, Any] | None:
    """Read one token snapshot without exposing session contents."""
    if event.get("type") != "event_msg":
        return None
    payload = event.get("payload") or {}
    if not isinstance(payload, dict):
        return None
    info = payload.get("info") or {}
    if not isinstance(info, dict):
        return None
    if usage_field not in info:
        return None
    usage = info.get(usage_field)

    result: dict[str, Any] = {"timestamp": event.get("timestamp")}
    if not isinstance(usage, dict):
        return {
            **result,
            **{field: None for field in TOKEN_FIELDS},
            "unavailable_categories": list(TOKEN_FIELDS),
            "malformed": True,
        }
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
    result["unavailable_categories"] = unavailable
    if not available:
        result["malformed"] = True
    elif unavailable:
        result["partial"] = True
    return result


def token_usage_evidence(event: dict[str, Any]) -> dict[str, Any] | None:
    """Read a cumulative per-rollout token snapshot."""
    return usage_evidence(event, "total_token_usage")


def request_token_usage_evidence(event: dict[str, Any]) -> dict[str, Any] | None:
    """Read the token snapshot for the model request represented by an event."""
    return usage_evidence(event, "last_token_usage")


def usage_validation(usage: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in TOKEN_FIELDS if usage.get(field) is None]
    if missing:
        return {
            "status": "not-available",
            "reason": "token usage lacks the classifications required for an honest estimate",
            "missing_fields": missing,
        }
    input_tokens = usage["input_tokens"]
    cached = usage["cached_input_tokens"]
    reasoning = usage["reasoning_output_tokens"]
    output = usage["output_tokens"]
    total = usage["total_tokens"]
    if cached > input_tokens or reasoning > output or total != input_tokens + output:
        return {
            "status": "not-available",
            "reason": "token usage classifications are internally inconsistent",
        }
    return {"status": "valid"}


def sum_usage(snapshots: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(snapshot[field] for snapshot in snapshots)
        for field in TOKEN_FIELDS
    }


def usage_mismatches(observed: dict[str, Any], calculated: dict[str, int]) -> dict[str, dict[str, int]]:
    return {
        field: {"observed": observed[field], "per_request_sum": calculated[field]}
        for field in TOKEN_FIELDS
        if observed.get(field) != calculated.get(field)
    }


def usage_signature(usage: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(usage.get(field) for field in TOKEN_FIELDS)


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


def model_pricing(observed_models: set[str], pricing_path: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if len(observed_models) != 1 or "unknown" in observed_models:
        return None, {
            "status": "not-available",
            "reason": "multiple-or-unknown-models-in-cumulative-rollout",
            "observed_models": sorted(observed_models),
        }
    model = next(iter(observed_models))
    try:
        pricing = load_pricing(pricing_path)
    except ValueError as error:
        return None, {"status": "not-available", "reason": str(error)}

    aliases = pricing.get("aliases") if isinstance(pricing.get("aliases"), dict) else {}
    resolved_model = aliases.get(model, model)
    models = pricing["models"]
    rates = models.get(resolved_model) if isinstance(resolved_model, str) else None
    if not isinstance(rates, dict):
        return None, {
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
        return None, {"status": "not-available", "reason": "configured model has incomplete API-equivalent prices"}

    policy = rates.get("long_context_pricing")
    if policy not in ("standard", "tiered"):
        return None, {
            "status": "not-available",
            "reason": "configured model has no explicit long-context pricing policy",
            "observed_model": model,
        }
    if policy == "tiered":
        threshold = rates.get("long_context_threshold_tokens")
        if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold <= 0:
            return None, {"status": "not-available", "reason": "configured long-context threshold is invalid"}
        for field in ("long_context_input_multiplier", "long_context_output_multiplier"):
            if not valid_number(rates.get(field), positive=True):
                return None, {"status": "not-available", "reason": "configured tiered long-context pricing is incomplete"}

    return {
        "pricing": pricing,
        "model": model,
        "resolved_model": resolved_model,
        "rates": rates,
        "policy": policy,
    }, None


def priced_components(
    usage: dict[str, Any],
    rates: dict[str, Any],
    *,
    input_multiplier: float = 1.0,
    output_multiplier: float = 1.0,
) -> dict[str, dict[str, float | int]]:
    input_tokens = usage["input_tokens"]
    cached = usage["cached_input_tokens"]
    cache_write = usage["cache_write_input_tokens"]
    output = usage["output_tokens"]
    components = {
        "input": (input_tokens - cached, rates["input_per_million"] * input_multiplier),
        "cached_input": (cached, rates["cached_input_per_million"] * input_multiplier),
        "cache_write_input": (cache_write, rates["cache_write_input_per_million"] * input_multiplier),
        "output": (output, rates["output_per_million"] * output_multiplier),
    }
    return {
        name: {"tokens": tokens, "usd": round(tokens * rate / 1_000_000, 12)}
        for name, (tokens, rate) in components.items()
    }


def empty_components() -> dict[str, dict[str, float | int]]:
    return {name: {"tokens": 0, "usd": 0.0} for name in ("input", "cached_input", "cache_write_input", "output")}


def add_components(target: dict[str, dict[str, float | int]], source: dict[str, dict[str, float | int]]) -> None:
    for name in target:
        target[name]["tokens"] += source[name]["tokens"]
        target[name]["usd"] += source[name]["usd"]


def finalize_components(components: dict[str, dict[str, float | int]]) -> dict[str, dict[str, float | int]]:
    return {
        name: {"tokens": values["tokens"], "usd": round(values["usd"], 12)}
        for name, values in components.items()
    }


def estimate_result(
    pricing: dict[str, Any],
    resolved_model: str,
    rates: dict[str, Any],
    components: dict[str, dict[str, float | int]],
    *,
    scope: str,
    long_context_pricing: str,
) -> dict[str, Any]:
    components = finalize_components(components)
    return {
        "status": "estimated",
        "basis": f"{pricing.get('pricing_basis', 'api-equivalent')}-token-only",
        "currency": pricing.get("currency", "USD"),
        "pricing_updated_at": pricing.get("updated_at"),
        "pricing_model": resolved_model,
        "long_context_pricing": long_context_pricing,
        "scope": scope,
        "components": components,
        "total_usd": round(sum(item["usd"] for item in components.values()), 12),
        "exclusions": ["tool fees", "modality fees", "subscription billing"],
    }


def cumulative_cost_estimate(
    usage: dict[str, Any],
    observed_models: set[str],
    pricing_path: Path,
    *,
    ignore_long_context: bool,
) -> dict[str, Any]:
    validation = usage_validation(usage)
    if validation["status"] != "valid":
        return validation
    pricing_context, error = model_pricing(observed_models, pricing_path)
    if error:
        return error
    assert pricing_context is not None
    pricing = pricing_context["pricing"]
    rates = pricing_context["rates"]
    policy = pricing_context["policy"]
    warning = None
    if policy == "tiered":
        if not ignore_long_context:
            return {
                "status": "not-available",
                "reason": "request-level-token-usage-unavailable-for-tiered-long-context-pricing",
            }
        warning = "long-context pricing was explicitly ignored; estimate may be inaccurate"
    applied_policy = "standard" if policy == "tiered" and ignore_long_context else policy
    result = estimate_result(
        pricing,
        pricing_context["resolved_model"],
        rates,
        priced_components(usage, rates),
        scope="last-readable-rollout-total",
        long_context_pricing=applied_policy,
    )
    if warning:
        result["warnings"] = [warning]
    return result


def request_cost_estimate(
    usage: dict[str, Any],
    request_usage: list[dict[str, Any]],
    observed_models: set[str],
    pricing_path: Path,
    *,
    ignore_long_context: bool,
) -> dict[str, Any]:
    total_validation = usage_validation(usage)
    if total_validation["status"] != "valid":
        return total_validation
    pricing_context, error = model_pricing(observed_models, pricing_path)
    if error:
        return error
    assert pricing_context is not None
    pricing = pricing_context["pricing"]
    rates = pricing_context["rates"]
    policy = pricing_context["policy"]

    for index, snapshot in enumerate(request_usage, 1):
        validation = usage_validation(snapshot)
        if validation["status"] != "valid":
            validation["request_index"] = index
            return validation
    calculated = sum_usage(request_usage)
    mismatches = usage_mismatches(usage, calculated)
    if mismatches:
        return {
            "status": "not-available",
            "reason": "per-request-token-usage-does-not-reconcile-with-cumulative-rollout-total",
            "mismatches": mismatches,
        }

    aggregate = empty_components()
    segments = {
        "standard": {"requests": 0, "components": empty_components()},
        "long_context": {"requests": 0, "components": empty_components()},
    }
    threshold = rates.get("long_context_threshold_tokens")
    input_multiplier = 1.0
    output_multiplier = 1.0
    apply_tiered_pricing = policy == "tiered" and not ignore_long_context
    for snapshot in request_usage:
        is_long_context = apply_tiered_pricing and snapshot["input_tokens"] > threshold
        segment = "long_context" if is_long_context else "standard"
        if is_long_context:
            input_multiplier = rates["long_context_input_multiplier"]
            output_multiplier = rates["long_context_output_multiplier"]
        else:
            input_multiplier = 1.0
            output_multiplier = 1.0
        components = priced_components(
            snapshot,
            rates,
            input_multiplier=input_multiplier,
            output_multiplier=output_multiplier,
        )
        add_components(aggregate, components)
        segments[segment]["requests"] += 1
        add_components(segments[segment]["components"], components)

    result = estimate_result(
        pricing,
        pricing_context["resolved_model"],
        rates,
        aggregate,
        scope="last-token-usage-per-request",
        long_context_pricing="standard" if policy == "tiered" and ignore_long_context else policy,
    )
    result["request_count"] = len(request_usage)
    result["standard_request_count"] = segments["standard"]["requests"]
    result["long_context_request_count"] = segments["long_context"]["requests"]
    result["request_segments"] = {
        name: {
            "requests": segment["requests"],
            "components": finalize_components(segment["components"]),
        }
        for name, segment in segments.items()
    }
    if policy == "tiered":
        result["long_context_threshold_tokens"] = threshold
        if ignore_long_context:
            result["warnings"] = ["long-context pricing was explicitly ignored; estimate may be inaccurate"]
    return result


def cost_estimate(
    usage: dict[str, Any],
    observed_models: set[str],
    pricing_path: Path,
    *,
    ignore_long_context: bool,
    force_standard_long_context: bool = False,
    request_usage: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if request_usage:
        return request_cost_estimate(
            usage,
            request_usage,
            observed_models,
            pricing_path,
            ignore_long_context=force_standard_long_context,
        )
    return cumulative_cost_estimate(
        usage,
        observed_models,
        pricing_path,
        ignore_long_context=ignore_long_context,
    )


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
    events = read_events(candidate["path"])
    contexts = [evidence for event in events if (evidence := context_evidence(event))]
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
    usage = [evidence for event in events if (evidence := token_usage_evidence(event))]
    all_request_usage: list[dict[str, Any]] = []
    request_usage: list[dict[str, Any]] = []
    request_signatures: set[tuple[tuple[Any, ...], tuple[Any, ...]]] = set()
    duplicate_request_snapshots = 0
    for event in events:
        request_snapshot = request_token_usage_evidence(event)
        if not request_snapshot:
            continue
        all_request_usage.append(request_snapshot)
        cumulative_snapshot = token_usage_evidence(event)
        if cumulative_snapshot is None:
            request_usage.append(request_snapshot)
            continue
        signature = (
            usage_signature(cumulative_snapshot),
            usage_signature(request_snapshot),
        )
        if signature in request_signatures:
            duplicate_request_snapshots += 1
            continue
        request_signatures.add(signature)
        request_usage.append(request_snapshot)
    if all_request_usage:
        request_status = "observed" if all(not item["unavailable_categories"] for item in all_request_usage) else "partial"
        request_evidence: dict[str, Any] = {
            "status": request_status,
            "source": "local-rollout-event_msg.info.last_token_usage:deduplicated",
            "scope": "deduplicated-request-usage-events",
            "request_count": len(request_usage),
            "readable_snapshot_count": len(all_request_usage),
            "snapshots": all_request_usage,
        }
        if duplicate_request_snapshots:
            request_evidence["duplicate_snapshots_ignored"] = duplicate_request_snapshots
        if request_status == "observed":
            request_evidence["sum"] = sum_usage(request_usage)
        else:
            request_evidence["reason"] = "one or more request snapshots lack required token classifications"
        result["request_token_usage"] = request_evidence
    else:
        result["request_token_usage"] = {
            "status": "not-available",
            "reason": "matching rollout has no readable per-request last_token_usage metadata",
        }
    if usage:
        result["token_usage"] = {
            "status": "observed" if not usage[-1]["unavailable_categories"] else "partial",
            "source": "local-rollout-event_msg.info.total_token_usage:last-readable",
            "scope": "last-readable-rollout-total",
            **usage[-1],
        }
    else:
        result["token_usage"] = {
            "status": "not-available",
            "reason": "matching rollout has no readable cumulative token usage metadata",
        }
    observed_models = {
        context["model"] if isinstance(context.get("model"), str) and context["model"] else "unknown"
        for context in contexts
    }
    if usage:
        result["cost_estimate"] = cost_estimate(
            result["token_usage"], observed_models, args.pricing_config,
            ignore_long_context=not args.respect_long_context,
            force_standard_long_context=args.ignore_long_context,
            request_usage=request_usage,
        )
    elif request_usage:
        result["cost_estimate"] = {
            "status": "not-available",
            "reason": "cumulative-token-usage-metadata-unavailable-for-reconciliation",
        }
    else:
        result["cost_estimate"] = {
            "status": "not-available",
            "reason": "matching rollout has no readable token usage metadata",
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions-root", type=Path, default=default_sessions_root())
    parser.add_argument("--pricing-config", type=Path, default=default_pricing_config())
    long_context_flags = parser.add_mutually_exclusive_group()
    long_context_flags.add_argument("--respect-long-context", dest="respect_long_context", action="store_true", help="Refuse a cumulative fallback when tiered long-context pricing lacks request-level telemetry.")
    long_context_flags.add_argument("--ignore-long-context", dest="ignore_long_context", action="store_true", help="Force standard pricing and warn when long-context pricing is ignored.")
    parser.set_defaults(respect_long_context=False, ignore_long_context=False)
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
                cost = payload["cost_estimate"]
                print(f"Token-only API-equivalent cost: ${cost['total_usd']:.8f} USD")
                if cost.get("scope") == "last-token-usage-per-request":
                    print(f"Priced requests: {cost['request_count']} (long context: {cost['long_context_request_count']})")
                for warning in cost.get("warnings", []):
                    print(f"Warning: {warning}")
        elif "reason" in payload:
            print(f"Reason: {payload['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
