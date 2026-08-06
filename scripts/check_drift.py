#!/usr/bin/env python3
"""Check every AISDD feature for structural and test-traceability drift."""
from __future__ import annotations

import argparse
from pathlib import Path

from validate_feature import validate_feature
from verify_feature import test_map


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repo", type=Path)
    args = p.parse_args()
    repo = args.repo.resolve()
    specs = repo / "specs"
    if not specs.exists():
        print("OK: nenhuma pasta specs encontrada")
        return 0
    full_map = test_map(repo)
    failures: list[str] = []
    pending_baseline_gaps: list[str] = []
    for feature in sorted(x for x in specs.iterdir() if x.is_dir()):
        status = feature / "status.md"
        if feature.name.startswith("baseline-") and status.exists() and "Origem: baseline-conformance" in status.read_text(encoding="utf-8", errors="ignore"):
            pending_baseline_gaps.append(feature.name)
            continue
        errors = validate_feature(repo, feature.relative_to(repo), full_map=full_map)
        if errors:
            details = "FALHA | " + " | ".join(f"- {error}" for error in errors)
            failures.append(f"{feature.name}: {details}")
    if failures:
        print("DRIFT ENCONTRADO")
        print("\n".join(f"- {item}" for item in failures))
        return 1
    if pending_baseline_gaps:
        print("OK: nenhum drift estrutural ou de rastreabilidade encontrado")
        print("FOLLOW-UPS DE BASELINE PENDENTES: " + ", ".join(pending_baseline_gaps))
        return 0
    print("OK: nenhum drift estrutural ou de rastreabilidade encontrado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
