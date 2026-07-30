#!/usr/bin/env python3
"""Check every AISDD feature for structural and test-traceability drift."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repo", type=Path)
    args = p.parse_args()
    repo = args.repo.resolve()
    specs = repo / "specs"
    if not specs.exists():
        print("OK: nenhuma pasta specs encontrada")
        return 0
    validator = Path(__file__).with_name("validate_feature.py")
    failures: list[str] = []
    for feature in sorted(x for x in specs.iterdir() if x.is_dir()):
        result = subprocess.run(
            [sys.executable, str(validator), str(repo), str(feature.relative_to(repo))],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            details = (result.stdout + result.stderr).strip().replace("\n", " | ")
            failures.append(f"{feature.name}: {details}")
    if failures:
        print("DRIFT ENCONTRADO")
        print("\n".join(f"- {item}" for item in failures))
        return 1
    print("OK: nenhum drift estrutural ou de rastreabilidade encontrado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
