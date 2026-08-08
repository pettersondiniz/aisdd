#!/usr/bin/env python3
"""Record and collect read-only telemetry for delegated AISDD work packages."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Iterable

import agent_evidence
from delegation_contract import work_packages_sha256


CONTRACT_VERSION = "v2"
TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
UNKNOWN_EFFECTIVE = {"model": "unknown", "reasoning_effort": "unknown"}
UUID_RE = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z", re.I)


class TelemetryError(ValueError):
    """An input or safety condition prevents an honest artifact update."""


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _jsonish(value: str | None) -> Any:
    """Parse JSON-shaped CLI values while retaining ordinary text decisions."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as source:
            value = json.load(source)
    except (OSError, json.JSONDecodeError) as error:
        raise TelemetryError(f"{label} is not readable JSON: {error}") from error
    if not isinstance(value, dict):
        raise TelemetryError(f"{label} must be a JSON object")
    return value


def _resolved(path: Path) -> Path:
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise TelemetryError(f"path is not safely resolvable: {path}") from error


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(_resolved(left))) == os.path.normcase(str(_resolved(right)))


def _inside(path: Path, root: Path) -> bool:
    try:
        _resolved(path).relative_to(_resolved(root))
    except (ValueError, TelemetryError):
        return False
    return True


def _assert_output_safe(output: Path, *, sessions_root: Path | None = None, forbidden: Iterable[Path] = ()) -> None:
    """Reject output aliases that could mutate a rollout or configuration."""
    if output.exists() and output.is_dir():
        raise TelemetryError(f"output is a directory: {output}")
    for path in forbidden:
        if _same_path(output, path):
            raise TelemetryError(f"output must not overwrite a read-only input: {path}")

    if sessions_root is None:
        return
    if _inside(output, sessions_root):
        raise TelemetryError("output must not be inside the Codex sessions root")
    if not output.exists() or not sessions_root.is_dir():
        return

    try:
        rollout_paths = sessions_root.rglob("rollout-*.jsonl")
        for rollout in rollout_paths:
            try:
                if rollout.is_file() and os.path.samefile(output, rollout):
                    raise TelemetryError("output aliases a read-only rollout")
            except FileNotFoundError:
                continue
    except OSError as error:
        raise TelemetryError(f"cannot inspect sessions root safely: {error}") from error


def _write_json(output: Path, value: dict[str, Any]) -> None:
    if not output.parent.is_dir():
        raise TelemetryError(f"output parent directory does not exist: {output.parent}")
    try:
        with output.open("w", encoding="utf-8", newline="\n") as target:
            json.dump(value, target, ensure_ascii=False, indent=2)
            target.write("\n")
    except OSError as error:
        raise TelemetryError(f"output is not writable: {error}") from error


def _manifest(value: dict[str, Any], label: str) -> dict[str, Any]:
    if value.get("contract") != CONTRACT_VERSION or value.get("contract_version") != CONTRACT_VERSION:
        raise TelemetryError(f"{label} must declare delegation-evidence contract v2")
    delegations = value.get("delegations")
    if not isinstance(delegations, list):
        raise TelemetryError(f"{label} delegations must be a list")
    seen: set[str] = set()
    for index, entry in enumerate(delegations):
        if not isinstance(entry, dict):
            raise TelemetryError(f"{label} delegation {index} must be an object")
        work_package = _text(entry.get("work_package"))
        if not work_package:
            raise TelemetryError(f"{label} delegation {index} has no work_package")
        if work_package in seen:
            raise TelemetryError(f"{label} has duplicate delegation for {work_package}")
        seen.add(work_package)
    return value


def _required_roles(values: Iterable[str] | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        for value in raw.split(","):
            role = value.strip()
            if role and role not in seen:
                result.append(role)
                seen.add(role)
    return result


def _default_sessions_root() -> Path:
    return agent_evidence.default_sessions_root()


def init_manifest(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output
    sessions_root = _default_sessions_root()
    forbidden: list[Path] = []
    if args.work_packages:
        forbidden.append(args.work_packages)
    _assert_output_safe(output, sessions_root=sessions_root, forbidden=forbidden)
    if output.exists():
        raise TelemetryError(f"refusing to overwrite existing manifest: {output}")

    if args.work_packages and args.work_packages_sha256:
        raise TelemetryError("use either --work-packages or --work-packages-sha256, not both")
    if args.work_packages:
        packages = _read_json(args.work_packages, "work packages")
        digest = work_packages_sha256(packages)
    else:
        digest = _text(args.work_packages_sha256) or ""
        if digest and not re.fullmatch(r"[0-9a-f]{64}", digest, re.I):
            raise TelemetryError("--work-packages-sha256 must be a 64-character hexadecimal digest")

    manifest = {
        "contract": CONTRACT_VERSION,
        "contract_version": CONTRACT_VERSION,
        "status": "incomplete",
        "work_packages_sha256": digest,
        "required_roles": _required_roles(args.required_role),
        "delegations": [],
    }
    _write_json(output, manifest)
    return manifest


def _source_path(args: argparse.Namespace) -> Path:
    source = args.manifest or args.output
    if not source.exists():
        raise TelemetryError(f"manifest does not exist: {source}")
    return source


def _fallback_from_args(existing: dict[str, Any] | None, args: argparse.Namespace) -> dict[str, Any]:
    detail_supplied = any(
        value is not None
        for value in (
            args.fallback_reason,
            args.fallback_attempt,
            args.fallback_operation,
            args.fallback_scope,
            args.fallback_result,
            args.fallback_direct_work,
        )
    ) or args.fallback_agent_unavailable is not None
    fallback_supplied = args.fallback is not None or args.fallback_used is not None or detail_supplied

    if not fallback_supplied and existing is not None:
        previous = existing.get("fallback")
        if not isinstance(previous, dict) or not isinstance(previous.get("used"), bool):
            raise TelemetryError("existing delegation has an invalid fallback object")
        return deepcopy(previous)

    parsed: Any = _jsonish(args.fallback)
    if parsed is None:
        current: dict[str, Any] = {"used": False}
    elif isinstance(parsed, bool):
        current = {"used": parsed}
    elif isinstance(parsed, dict):
        current = deepcopy(parsed)
        if not isinstance(current.get("used"), bool):
            raise TelemetryError("fallback JSON must contain a boolean used field")
    else:
        raise TelemetryError("fallback must be a boolean or JSON object")

    if args.fallback_used is not None:
        used = _jsonish(args.fallback_used)
        if not isinstance(used, bool):
            raise TelemetryError("--fallback-used must be true or false")
        if "used" in current and current["used"] != used and args.fallback is not None:
            raise TelemetryError("fallback declarations disagree about used")
        current["used"] = used

    if args.fallback_reason is not None:
        current["reason"] = args.fallback_reason
    if args.fallback_agent_unavailable is not None:
        unavailable = _jsonish(args.fallback_agent_unavailable)
        if not isinstance(unavailable, bool):
            raise TelemetryError("--fallback-agent-unavailable must be true or false")
        current["agent_unavailable"] = unavailable
    if args.fallback_attempt:
        attempts: list[dict[str, Any]] = []
        for attempt in args.fallback_attempt:
            value = _jsonish(attempt)
            attempts.append(value if isinstance(value, dict) else {"detail": attempt})
        current["attempts"] = attempts

    direct_work: dict[str, Any] = {}
    if args.fallback_direct_work is not None:
        parsed_direct = _jsonish(args.fallback_direct_work)
        if not isinstance(parsed_direct, dict):
            raise TelemetryError("--fallback-direct-work must be a JSON object")
        direct_work.update(parsed_direct)
    if args.fallback_operation is not None:
        direct_work["operation"] = args.fallback_operation
    if args.fallback_scope:
        direct_work["scope"] = list(args.fallback_scope)
    if args.fallback_result is not None:
        direct_work["result"] = args.fallback_result
    if direct_work:
        current["direct_work"] = direct_work

    if current.get("used") is False:
        # v2 requires a clean declaration when no direct fallback occurred.
        return {"used": False}
    return current


def _add_requested_fields(entry: dict[str, Any], model: str | None, effort: str | None) -> None:
    entry["requested_model"] = model
    entry["requested_effort"] = effort
    entry["requested"] = {"model": model, "effort": effort}


def _declaration_signature(entry: dict[str, Any]) -> str:
    declaration = {
        key: entry.get(key)
        for key in (
            "work_package",
            "role",
            "agent_id",
            "rollout_id",
            "requested_model",
            "requested_effort",
            "requested",
            "routing_decision",
            "routing",
            "fallback",
            "state",
        )
    }
    return json.dumps(declaration, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _clear_collection(manifest: dict[str, Any]) -> None:
    for key in ("totals", "summary", "delegated_subtotal", "unavailable", "collection_status"):
        manifest.pop(key, None)


def _clear_entry_telemetry(entry: dict[str, Any]) -> None:
    for key in (
        "collection",
        "agent_evidence",
        "effective",
        "token_usage",
        "request_token_usage",
        "cost_estimate",
        "resolution",
    ):
        entry.pop(key, None)


def record_delegation(args: argparse.Namespace) -> dict[str, Any]:
    agent_id = _text(args.agent_id)
    rollout_id = _text(args.rollout_id)
    if not agent_id and not rollout_id:
        raise TelemetryError("record requires --agent-id or --rollout-id")
    work_package = _text(args.work_package)
    role = _text(args.role)
    if not work_package or not role:
        raise TelemetryError("record requires non-empty --work-package and --role")

    output = args.output
    source = _source_path(args)
    _assert_output_safe(output, sessions_root=_default_sessions_root())
    manifest = _manifest(_read_json(source, "manifest"), "manifest")
    delegations = manifest["delegations"]
    matches = [index for index, item in enumerate(delegations) if item.get("work_package") == work_package]
    if len(matches) > 1:
        raise TelemetryError(f"manifest has ambiguous delegation for {work_package}")

    previous = deepcopy(delegations[matches[0]]) if matches else None
    entry = deepcopy(previous) if previous is not None else {}
    entry["work_package"] = work_package
    entry["role"] = role
    if agent_id:
        entry["agent_id"] = agent_id
        if not rollout_id:
            # An explicit agent selector supersedes a previous rollout selector;
            # keeping both would silently correlate the old rollout instead.
            entry.pop("rollout_id", None)
    elif "agent_id" not in entry:
        # v2 requires agent_id; a rollout id is the only declared identity here.
        entry["agent_id"] = rollout_id
    if rollout_id:
        entry["rollout_id"] = rollout_id
    if not _text(entry.get("agent_id")):
        raise TelemetryError("record could not establish an agent_id")

    requested_model = _text(args.requested_model) if args.requested_model is not None else entry.get("requested_model")
    requested_effort = _text(args.requested_effort) if args.requested_effort is not None else entry.get("requested_effort")
    _add_requested_fields(entry, requested_model, requested_effort)

    if args.routing_decision is not None:
        routing = _jsonish(args.routing_decision)
        entry["routing_decision"] = routing
        entry["routing"] = deepcopy(routing)
    elif previous is None:
        entry["routing_decision"] = None
        entry["routing"] = None

    if args.state is not None:
        entry["state"] = args.state
    elif "state" not in entry:
        entry["state"] = "completed"
    entry["fallback"] = _fallback_from_args(previous, args)

    changed = previous is None or _declaration_signature(previous) != _declaration_signature(entry)
    if changed:
        _clear_entry_telemetry(entry)
        _clear_collection(manifest)
    if matches:
        delegations[matches[0]] = entry
    else:
        delegations.append(entry)
    _write_json(output, manifest)
    return manifest


def _unavailable(reason: str, **extra: Any) -> dict[str, Any]:
    value: dict[str, Any] = {"status": "not-available", "reason": reason}
    value.update(extra)
    return value


def _resolve_one(entry: dict[str, Any], args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, str]]:
    rollout_id = _text(entry.get("rollout_id"))
    agent_id = _text(entry.get("agent_id"))
    if rollout_id:
        selector = {"kind": "rollout_id", "value": rollout_id}
        resolve_args = argparse.Namespace(
            sessions_root=args.sessions_root,
            pricing_config=args.pricing_config,
            respect_long_context=args.respect_long_context,
            ignore_long_context=args.ignore_long_context,
            rollout_id=rollout_id,
            agent_id=None,
            role=None,
            nickname=None,
            parent_session_id=None,
        )
    elif agent_id:
        selector = {"kind": "agent_id", "value": agent_id}
        resolve_args = argparse.Namespace(
            sessions_root=args.sessions_root,
            pricing_config=args.pricing_config,
            respect_long_context=args.respect_long_context,
            ignore_long_context=args.ignore_long_context,
            rollout_id=None,
            agent_id=agent_id,
            role=None,
            nickname=None,
            parent_session_id=None,
        )
    else:
        selector = {"kind": "none", "value": ""}
        return _unavailable("delegation has neither rollout_id nor agent_id"), selector

    try:
        payload = agent_evidence.resolve(resolve_args)
    except (OSError, ValueError, RuntimeError) as error:
        payload = _unavailable(f"agent evidence resolution failed: {error}")
    if not isinstance(payload, dict):
        payload = _unavailable("agent evidence returned an invalid result")
    return payload, selector


def _safe_effective(payload: dict[str, Any]) -> dict[str, Any]:
    effective = payload.get("effective")
    if not isinstance(effective, dict):
        return deepcopy(UNKNOWN_EFFECTIVE)
    result = deepcopy(effective)
    if not _text(result.get("model")):
        result["model"] = "unknown"
    if not _text(result.get("reasoning_effort")):
        result["reasoning_effort"] = "unknown"
    return result


def _apply_evidence(entry: dict[str, Any], payload: dict[str, Any], selector: dict[str, str]) -> None:
    entry["collection"] = {
        "selector": deepcopy(selector),
        "status": payload.get("status", "not-available"),
    }
    if _text(payload.get("reason")):
        entry["collection"]["reason"] = payload["reason"]
    entry["agent_evidence"] = deepcopy(payload)
    entry["effective"] = _safe_effective(payload)

    token_usage = payload.get("token_usage")
    if isinstance(token_usage, dict):
        entry["token_usage"] = deepcopy(token_usage)
    else:
        entry["token_usage"] = _unavailable("cumulative token usage is unavailable")
    request_usage = payload.get("request_token_usage")
    if isinstance(request_usage, dict):
        entry["request_token_usage"] = deepcopy(request_usage)
    else:
        entry["request_token_usage"] = _unavailable("per-request token usage is unavailable")

    cost_estimate = payload.get("cost_estimate")
    if isinstance(cost_estimate, dict):
        entry["cost_estimate"] = deepcopy(cost_estimate)
    else:
        entry["cost_estimate"] = _unavailable("cost estimate is unavailable")

    resolution = payload.get("resolution")
    if isinstance(resolution, dict):
        entry["resolution"] = deepcopy(resolution)
    else:
        entry.pop("resolution", None)


def _valid_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _cost_item(entry: dict[str, Any]) -> tuple[float, str] | tuple[None, str]:
    cost = entry.get("cost_estimate")
    if not isinstance(cost, dict):
        return None, "cost estimate is missing"
    if cost.get("status") != "estimated":
        return None, _text(cost.get("reason")) or "cost estimate is not available"
    total = cost.get("total_usd")
    if not _valid_number(total) or total < 0:
        return None, "estimated cost has no finite non-negative total_usd"
    currency = _text(cost.get("currency"))
    if not currency:
        return None, "estimated cost has no currency"
    return float(total), currency


def _totals(manifest: dict[str, Any]) -> dict[str, Any]:
    entries = manifest.get("delegations", [])
    costed: list[tuple[str, float, str]] = []
    unavailable: list[dict[str, Any]] = []
    for entry in entries:
        work_package = _text(entry.get("work_package")) or "<missing>"
        total, reason = _cost_item(entry)
        if total is None:
            unavailable.append(
                {
                    "work_package": work_package,
                    "status": entry.get("collection", {}).get("status", "not-available")
                    if isinstance(entry.get("collection"), dict)
                    else "not-available",
                    "reason": reason,
                }
            )
        else:
            costed.append((work_package, total, reason))

    currencies = {currency for _, _, currency in costed}
    if len(currencies) > 1:
        for work_package, _, currency in costed:
            unavailable.append(
                {
                    "work_package": work_package,
                    "status": "not-available",
                    "reason": f"delegated cost estimates use multiple currencies; cannot subtotal {currency}",
                }
            )
        costed = []

    if costed:
        currency = next(iter({currency for _, _, currency in costed}))
        subtotal: dict[str, Any] = {
            "status": "estimated",
            "currency": currency,
            "total_usd": round(sum(total for _, total, _ in costed), 12),
            "costed_agents": len(costed),
            "delegated_agents": len(entries),
            "unavailable_agents": len(unavailable),
        }
    else:
        subtotal = {
            "status": "not-available",
            "reason": "no complete delegated cost estimates are available",
            "costed_agents": 0,
            "delegated_agents": len(entries),
            "unavailable_agents": len(unavailable),
        }

    unavailable_summary = {
        "status": "not-available" if unavailable else "none",
        "count": len(unavailable),
        "delegations": unavailable,
    }
    return {
        "delegated_subtotal": subtotal,
        "unavailable": unavailable_summary,
    }


def collect_manifest(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    source = _source_path(args)
    _assert_output_safe(
        args.output,
        sessions_root=args.sessions_root,
        forbidden=[args.pricing_config],
    )
    manifest = _manifest(_read_json(source, "manifest"), "manifest")
    for entry in manifest["delegations"]:
        payload, selector = _resolve_one(entry, args)
        _apply_evidence(entry, payload, selector)

    totals = _totals(manifest)
    manifest["totals"] = totals
    manifest["summary"] = deepcopy(totals)
    # These aliases keep the two requested parcels easy to consume without
    # collapsing an unavailable parcel into the delegated subtotal.
    manifest["delegated_subtotal"] = deepcopy(totals["delegated_subtotal"])
    manifest["unavailable"] = deepcopy(totals["unavailable"])
    manifest["collection_status"] = "complete" if not totals["unavailable"]["count"] else "partial"
    _write_json(args.output, manifest)
    return manifest, not totals["unavailable"]["count"]


def _add_source(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--manifest",
        "--input",
        dest="manifest",
        type=Path,
        help="manifest to read; defaults to --output",
    )


def _add_fallback_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--fallback", nargs="?", const="true", help="fallback boolean or JSON object")
    parser.add_argument("--fallback-used", nargs="?", const="true")
    parser.add_argument("--fallback-reason")
    parser.add_argument("--fallback-agent-unavailable", nargs="?", const="true")
    parser.add_argument("--fallback-attempt", action="append", default=[])
    parser.add_argument("--fallback-operation")
    parser.add_argument("--fallback-scope", action="append", default=[])
    parser.add_argument("--fallback-result")
    parser.add_argument("--fallback-direct-work")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create an empty delegation-evidence v2 manifest")
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--work-packages", type=Path)
    init.add_argument("--work-packages-sha256")
    init.add_argument("--required-role", action="append", default=[])
    init.add_argument("--json", action="store_true")

    record = commands.add_parser("record", help="add or update one delegation idempotently")
    record.add_argument("--output", type=Path, required=True)
    _add_source(record)
    record.add_argument("--work-package", "--work-package-id", dest="work_package", required=True)
    record.add_argument("--role", required=True)
    record.add_argument("--agent-id")
    record.add_argument("--rollout-id")
    record.add_argument("--requested-model", "--model", dest="requested_model")
    record.add_argument("--requested-effort", "--effort", "--reasoning-effort", dest="requested_effort")
    record.add_argument("--routing-decision", "--routing", dest="routing_decision")
    record.add_argument("--state")
    _add_fallback_options(record)
    record.add_argument("--json", action="store_true")

    collect = commands.add_parser("collect", help="collect local rollout evidence into the manifest")
    collect.add_argument("--output", type=Path, required=True)
    _add_source(collect)
    collect.add_argument("--sessions-root", type=Path, default=_default_sessions_root())
    collect.add_argument("--pricing-config", type=Path, default=agent_evidence.default_pricing_config())
    long_context = collect.add_mutually_exclusive_group()
    long_context.add_argument("--respect-long-context", action="store_true")
    long_context.add_argument("--ignore-long-context", action="store_true")
    collect.add_argument("--json", action="store_true")

    return parser


def _print_result(args: argparse.Namespace, value: dict[str, Any]) -> None:
    if getattr(args, "json", False):
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return
    if args.command == "collect":
        print(f"Status: {value.get('collection_status', 'partial')}")
        subtotal = value.get("totals", {}).get("delegated_subtotal", {})
        if subtotal.get("status") == "estimated":
            print(f"Delegated subtotal: {subtotal['total_usd']:.12f} {subtotal['currency']}")
        else:
            print(f"Delegated subtotal: not-available ({subtotal.get('reason', 'unknown reason')})")
        unavailable = value.get("totals", {}).get("unavailable", {})
        print(f"Unavailable: {unavailable.get('count', 0)}")
    else:
        print(f"Status: {value.get('status', 'updated')}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            value = init_manifest(args)
            successful = True
        elif args.command == "record":
            value = record_delegation(args)
            successful = True
        else:
            value, successful = collect_manifest(args)
    except (OSError, TelemetryError, ValueError) as error:
        if getattr(args, "json", False):
            print(json.dumps({"status": "not-available", "reason": str(error)}, ensure_ascii=False, indent=2))
        else:
            print(f"Status: not-available\nReason: {error}")
        return 1
    _print_result(args, value)
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
