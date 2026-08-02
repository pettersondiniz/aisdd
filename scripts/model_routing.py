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


def resolve(config: dict[str, Any], role: str, availability: list[dict[str, Any]]) -> dict[str, Any]:
    roles = config.get("roles", {})
    tiers = config.get("tiers", {})
    fallback = config.get("fallback", {})
    selected = roles.get(role)
    if not isinstance(selected, dict):
        raise ValueError(f"unknown role: {role}")
    model = selected.get("model")
    effort = selected.get("reasoning_effort")
    tier = tiers.get(selected.get("tier"), {})
    if not isinstance(model, str) or not isinstance(effort, str) or not isinstance(tier, dict):
        raise ValueError(f"invalid configuration for role: {role}")
    patterns = tier.get("model_patterns", [])
    order = tier.get("effort_order", [])
    if not all(isinstance(value, str) for value in patterns + order):
        raise ValueError(f"invalid tier for role: {role}")
    exact = next((item for item in availability if item["id"] == model), None)
    if exact:
        available_effort = choose_effort(exact["reasoning_efforts"], effort, order)
        if available_effort:
            return {"status": "configured-available", "model": model, "reasoning_effort": available_effort}
    candidates: list[dict[str, str]] = []
    for pattern in patterns:
        regex = re.compile(pattern)
        for item in availability:
            if regex.search(item["id"]) and not any(candidate["model"] == item["id"] for candidate in candidates):
                candidate_effort = choose_effort(item["reasoning_efforts"], effort, order)
                if candidate_effort:
                    candidates.append({"model": item["id"], "reasoning_effort": candidate_effort})
    return {
        "status": "configured-unavailable" if availability else "availability-not-provided",
        "model": None,
        "reasoning_effort": None,
        "candidates": candidates,
        "fallback": {
            "model": fallback.get("model", "inherit"),
            "reasoning_effort": fallback.get("reasoning_effort", "inherit"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", help="AISDD role to query.")
    parser.add_argument("--class", dest="change_class", choices=["T0", "T1", "T2", "T3", "T4"], help="Change class for display.")
    parser.add_argument("--availability-json", type=Path, help="JSON of models and efforts exposed by the runtime.")
    parser.add_argument("--config", type=Path, help="Path to the user-global configuration.")
    parser.add_argument("--list", action="store_true", help="List effective configuration without querying a role.")
    parser.add_argument("--json", action="store_true", help="Emit JSON for agent consumption.")
    args = parser.parse_args()
    config_path = args.config or (USER_CONFIG if USER_CONFIG.exists() else DEFAULT_CONFIG)
    try:
        config = load_toml(config_path)
        availability = read_availability(args.availability_json)
        if args.list:
            output: dict[str, Any] = {"config_path": str(config_path), "roles": config.get("roles", {}), "fallback": config.get("fallback", {})}
        elif args.role:
            output = {
                "config_path": str(config_path), "role": args.role, "class": args.change_class,
                "configured": config.get("roles", {}).get(args.role), "available_models": availability,
                "recommendation": resolve(config, args.role, availability),
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
        else:
            print("Fallback: inherit current chat configuration")
            for candidate in recommendation.get("candidates", []):
                print(f"Suggestion: {candidate['model']} / {candidate['reasoning_effort']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
