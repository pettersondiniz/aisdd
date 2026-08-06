#!/usr/bin/env python3
"""Validate AISDD artifacts and the current, machine-readable AC test evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from verify_feature import test_map

REQUIRED = ("spec.md", "plan.md", "status.md", "evidence.md", "verification.json")
AC_PATTERN = re.compile(r"\bAC-\d{3,}\b")
TASK_PATTERN = re.compile(r"\bT-\d{3,}\b")
OPEN_STATUS = re.compile(r"\b(aberta|aberto|pending|open)\b", re.I)


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
    if not errors:
        spec = (feature / "spec.md").read_text(encoding="utf-8")
        plan = (feature / "plan.md").read_text(encoding="utf-8")
        evidence = (feature / "evidence.md").read_text(encoding="utf-8")
        if "{{" in spec + plan + evidence:
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
        if OPEN_STATUS.search(spec.split("## Suposições", 1)[-1]):
            errors.append("há suposição ou pergunta aberta na spec")
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
