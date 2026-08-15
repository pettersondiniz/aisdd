#!/usr/bin/env python3
"""Report an AISDD role's model recommendation without changing user configuration."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "assets" / "templates" / "model-routing.toml"
USER_CONFIG = Path.home() / ".codex" / "aisdd" / "model-routing.toml"
ROLE_ALIASES = {"tester": "test-engineer", "test_engineer": "test-engineer"}
RESERVED_ALIASES = frozenset(ROLE_ALIASES)


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"invalid configuration: {path}")
    return data


def read_availability(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, list):
        raise ValueError("availability JSON must contain a 'models' list")
    normalized: list[dict[str, Any]] = []
    for item in models:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("each model needs a textual 'id'")
        efforts = item.get("reasoning_efforts", [])
        if not isinstance(efforts, list) or not all(isinstance(value, str) for value in efforts):
            raise ValueError("reasoning_efforts must be a list of strings")
        normalized.append({"id": item["id"], "reasoning_efforts": efforts})
    return normalized


def choose_effort(efforts: list[str], preferred: str, order: list[str]) -> str | None:
    if preferred in efforts:
        return preferred
    for effort in order:
        if effort in efforts:
            return effort
    return efforts[0] if efforts else None


def _normalize_role(role: str) -> str:
    value = role.strip().lower().replace(" ", "-")
    return ROLE_ALIASES.get(value, value)


def _config_aliases(config: dict[str, Any]) -> dict[str, str]:
    aliases = dict(ROLE_ALIASES)
    configured = config.get("aliases", {})
    if isinstance(configured, dict):
        for alias, target in configured.items():
            if isinstance(alias, str) and isinstance(target, str):
                normalized_alias = alias.strip().lower().replace(" ", "-")
                if normalized_alias in RESERVED_ALIASES:
                    continue
                normalized_target = target.strip().lower().replace(" ", "-")
                aliases[normalized_alias] = ROLE_ALIASES.get(normalized_target, normalized_target)
    aliases.update(ROLE_ALIASES)
    return aliases


def _role_candidates(config: dict[str, Any], role: str) -> tuple[str, list[str]]:
    aliases = _config_aliases(config)
    requested = role.strip().lower().replace(" ", "-")
    canonical = aliases.get(requested, requested)
    candidates = [canonical]
    if requested not in candidates:
        candidates.append(requested)
    for alias, target in sorted(aliases.items()):
        if target == canonical and alias not in candidates:
            candidates.append(alias)
    return canonical, candidates


def _class_override(config: dict[str, Any], selected: dict[str, Any], canonical_role: str, change_class: str | None) -> tuple[dict[str, Any], str]:
    profile = dict(selected)
    source = "base"
    if not change_class:
        return profile, source
    class_name = change_class.upper()
    override: object = None
    selected_by_class = selected.get("by_class")
    if isinstance(selected_by_class, dict):
        override = selected_by_class.get(class_name, selected_by_class.get(change_class))
    if not isinstance(override, dict):
        global_by_class = config.get("by_class")
        if isinstance(global_by_class, dict):
            class_profile = global_by_class.get(class_name, global_by_class.get(change_class))
            if isinstance(class_profile, dict):
                override = class_profile.get(canonical_role)
                if not isinstance(override, dict):
                    override = class_profile.get("roles", {}).get(canonical_role) if isinstance(class_profile.get("roles"), dict) else None
    if isinstance(override, dict):
        profile.update(override)
        source = "by_class"
    return profile, source


def _fallback(config: dict[str, Any]) -> dict[str, str]:
    fallback = config.get("fallback", {})
    if not isinstance(fallback, dict):
        fallback = {}
    return {
        "model": fallback.get("model", "inherit"),
        "reasoning_effort": fallback.get("reasoning_effort", "inherit"),
    }


def _unconfigured_result(
    requested_role: str,
    canonical_role: str,
    change_class: str | None,
    fallback: dict[str, str],
) -> dict[str, Any]:
    return {
        "status": "role-not-configured",
        "model": None,
        "reasoning_effort": None,
        "requested_role": requested_role,
        "resolved_role": canonical_role,
        "configured_role": None,
        "class": change_class,
        "class_applied": False,
        "fallback": fallback,
        "capability_available": False,
        "candidates": [],
    }


def _inherit_result(
    requested_role: str,
    canonical_role: str,
    configured_role: str,
    change_class: str | None,
    fallback: dict[str, str],
) -> dict[str, Any]:
    return {
        "status": "inherit-not-capability",
        "model": None,
        "reasoning_effort": None,
        "requested_role": requested_role,
        "resolved_role": canonical_role,
        "configured_role": configured_role,
        "class": change_class,
        "class_applied": False,
        "fallback": fallback,
        "capability_available": False,
        "candidates": [],
    }


def resolve(
    config: dict[str, Any],
    role: str,
    availability: list[dict[str, Any]],
    change_class: str | None = None,
) -> dict[str, Any]:
    """Resolve a role while keeping the v1 three-argument call compatible."""
    roles = config.get("roles", {})
    tiers = config.get("tiers", {})
    if not isinstance(roles, dict) or not isinstance(tiers, dict):
        raise ValueError("configuration must contain roles and tiers tables")
    requested_role = role
    canonical_role, candidates = _role_candidates(config, role)
    selected: dict[str, Any] | None = None
    configured_role: str | None = None
    for candidate in candidates:
        value = roles.get(candidate)
        if isinstance(value, dict):
            selected = value
            configured_role = candidate
            break
    fallback = _fallback(config)
    if selected is None:
        return _unconfigured_result(requested_role, canonical_role, change_class, fallback)

    profile, profile_source = _class_override(config, selected, canonical_role, change_class)
    model = profile.get("model")
    effort = profile.get("reasoning_effort")
    tier_name = profile.get("tier")
    tier = tiers.get(tier_name, {})
    if not isinstance(model, str) or not isinstance(effort, str) or not isinstance(tier, dict):
        raise ValueError(f"invalid configuration for role: {configured_role}")
    if model.strip().lower() == "inherit" or effort.strip().lower() == "inherit":
        return _inherit_result(requested_role, canonical_role, configured_role or canonical_role, change_class, fallback)
    patterns = tier.get("model_patterns", [])
    order = tier.get("effort_order", [])
    if not isinstance(patterns, list) or not isinstance(order, list) or not all(isinstance(value, str) for value in patterns + order):
        raise ValueError(f"invalid tier for role: {configured_role}")
    try:
        compiled_patterns = [re.compile(pattern) for pattern in patterns]
    except re.error as error:
        raise ValueError(f"invalid model pattern for role: {configured_role}: {error}") from error

    base = {
        "requested_role": requested_role,
        "resolved_role": canonical_role,
        "configured_role": configured_role,
        "class": change_class,
        "class_applied": profile_source == "by_class",
        "profile": profile_source,
        "tier": tier_name,
        "capability_available": True,
    }
    exact = next((item for item in availability if item["id"] == model), None)
    if exact:
        available_effort = choose_effort(exact["reasoning_efforts"], effort, order)
        if available_effort:
            return {
                **base,
                "status": "configured-available",
                "model": model,
                "reasoning_effort": available_effort,
            }
    candidates_found: list[dict[str, str]] = []
    for pattern in compiled_patterns:
        for item in availability:
            if pattern.search(item["id"]) and not any(candidate["model"] == item["id"] for candidate in candidates_found):
                candidate_effort = choose_effort(item["reasoning_efforts"], effort, order)
                if candidate_effort:
                    candidates_found.append({"model": item["id"], "reasoning_effort": candidate_effort})
    return {
        **base,
        "status": "configured-unavailable" if availability else "availability-not-provided",
        "model": None,
        "reasoning_effort": None,
        "candidates": candidates_found,
        "fallback": fallback,
    }


def validate_request(
    config: dict[str, Any],
    role: str,
    availability: list[dict[str, Any]],
    requested_model: str | None = None,
    requested_effort: str | None = None,
    change_class: str | None = None,
    *,
    allow_override: bool = False,
    override_reason: str | None = None,
) -> dict[str, Any]:
    """Validate a spawn request against the resolved routing decision.

    This is deliberately separate from ``resolve`` so existing callers keep
    the v1 recommendation behavior.  The guard is used by the orchestrator
    immediately before spawning a child and makes model/effort substitutions
    explicit instead of silently treating them as runtime fallbacks.
    """
    recommendation = resolve(config, role, availability, change_class)
    requested = {
        "model": requested_model,
        "reasoning_effort": requested_effort,
    }
    result: dict[str, Any] = {
        "requested": requested,
        "recommendation": recommendation,
        "fallback_required": False,
        "routing_fallback": {"used": False},
    }

    status = recommendation.get("status")
    if status == "configured-available":
        recommended = {
            "model": recommendation.get("model"),
            "reasoning_effort": recommendation.get("reasoning_effort"),
        }
        has_override = requested_model is not None or requested_effort is not None
        if not has_override:
            return {**result, "status": "ready", "spawn": recommended}
        if requested == recommended:
            return {**result, "status": "ready", "spawn": requested}
        if allow_override and isinstance(override_reason, str) and override_reason.strip():
            return {
                **result,
                "status": "explicit-override",
                "spawn": requested,
                "routing_fallback": {
                    "used": True,
                    "kind": "model-and-effort"
                    if requested_model != recommended["model"]
                    and requested_effort != recommended["reasoning_effort"]
                    else "model"
                    if requested_model != recommended["model"]
                    else "effort",
                    "reason": override_reason.strip(),
                },
            }
        return {
            **result,
            "status": "request-mismatch",
            "reason": "requested model/effort differs from the available configured route",
        }

    if status in {"configured-unavailable", "availability-not-provided"}:
        has_override = requested_model is not None or requested_effort is not None
        fallback = {
            "used": True,
            "kind": "model-unavailable" if status == "configured-unavailable" else "availability-not-provided",
            "reason": (
                "configured model is unavailable; inherit the current chat configuration"
                if status == "configured-unavailable"
                else "runtime availability was not provided; inherit the current chat configuration"
            ),
        }
        if has_override:
            return {
                **result,
                "status": "request-unavailable-override",
                "fallback_required": True,
                "routing_fallback": fallback,
                "reason": "do not override model/effort when the configured route is unavailable or unobserved",
            }
        return {
            **result,
            "status": "fallback-required",
            "fallback_required": True,
            "routing_fallback": fallback,
            "spawn": {"model": None, "reasoning_effort": None},
        }

    return {
        **result,
        "status": "blocked",
        "reason": recommendation.get("status", "routing is not executable"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", help="AISDD role to query.")
    parser.add_argument("--class", dest="change_class", choices=["T0", "T1", "T2", "T3", "T4"], help="Change class for display.")
    parser.add_argument("--availability-json", type=Path, help="JSON of models and efforts exposed by the runtime.")
    parser.add_argument("--config", type=Path, help="Path to the user-global configuration.")
    parser.add_argument("--list", action="store_true", help="List effective configuration without querying a role.")
    parser.add_argument("--requested-model", help="Model requested for the spawn guard.")
    parser.add_argument("--requested-effort", help="Reasoning effort requested for the spawn guard.")
    parser.add_argument("--allow-override", action="store_true", help="Allow an explicit routing override with a reason.")
    parser.add_argument("--override-reason", help="Audit reason for an explicit routing override.")
    parser.add_argument("--require-available", action="store_true", help="Fail when the configured route cannot be proven available.")
    parser.add_argument("--json", action="store_true", help="Emit JSON for agent consumption.")
    args = parser.parse_args()
    config_path = args.config or (USER_CONFIG if USER_CONFIG.exists() else DEFAULT_CONFIG)
    try:
        config = load_toml(config_path)
        availability = read_availability(args.availability_json)
        if args.list:
            output: dict[str, Any] = {"config_path": str(config_path), "roles": config.get("roles", {}), "fallback": config.get("fallback", {})}
        elif args.role:
            canonical_role, candidates = _role_candidates(config, args.role)
            role_table = config.get("roles", {})
            if not isinstance(role_table, dict):
                raise ValueError("configuration roles table is invalid")
            configured = next((role_table.get(candidate) for candidate in candidates if isinstance(role_table.get(candidate), dict)), None)
            request_mode = any(
                value is not None
                for value in (args.requested_model, args.requested_effort, args.override_reason)
            ) or args.allow_override or args.require_available
            if request_mode:
                output = {
                    "config_path": str(config_path),
                    "role": args.role,
                    "class": args.change_class,
                    "configured": configured,
                    "available_models": availability,
                    **validate_request(
                        config,
                        args.role,
                        availability,
                        args.requested_model,
                        args.requested_effort,
                        args.change_class,
                        allow_override=args.allow_override,
                        override_reason=args.override_reason,
                    ),
                }
            else:
                output = {
                    "config_path": str(config_path),
                    "role": args.role,
                    "class": args.change_class,
                    "configured": configured,
                    "available_models": availability,
                    "recommendation": resolve(config, args.role, availability, args.change_class),
                }
        else:
            parser.error("provide --role or --list")
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif args.list:
        print(f"Configuration: {config_path}")
        for name, values in output["roles"].items():
            print(f"- {name}: {values.get('model')} / {values.get('reasoning_effort')}")
    else:
        recommendation = output["recommendation"]
        print(f"Role: {args.role}")
        print(f"Status: {recommendation['status']}")
        if recommendation.get("model"):
            print(f"Recommended: {recommendation['model']} / {recommendation['reasoning_effort']}")
        elif recommendation["status"] == "role-not-configured":
            print(f"BLOCKED: role not configured: {recommendation['resolved_role']}")
            print("Human decision required; inherit is not a capability")
        elif recommendation["status"] == "inherit-not-capability":
            print(f"BLOCKED: configured role {recommendation['resolved_role']} only inherits chat settings")
            print("Human decision required; inherit is not a capability")
        else:
            print("Fallback: inherit current chat configuration")
            for candidate in recommendation.get("candidates", []):
                print(f"Suggestion: {candidate['model']} / {candidate['reasoning_effort']}")
    if args.role and "recommendation" in output and not output["recommendation"].get("capability_available", False):
        return 1
    if args.role and "status" in output:
        if output["status"] in {"request-mismatch", "request-unavailable-override", "blocked"}:
            return 1
        if args.require_available and output.get("fallback_required"):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
