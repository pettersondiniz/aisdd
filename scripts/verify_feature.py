#!/usr/bin/env python3
"""Run a feature's real test command and record traceable AC evidence."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

AC_PATTERN = re.compile(r"\bAC-\d{3,}\b")
TAG_PATTERN = re.compile(r"@spec:\s*(AC-\d{3,})", re.I)
SKIP_PATTERN = re.compile(r"\b(skip|todo|xit|xdescribe)\b", re.I)
IGNORED_PARTS = {".git", ".spec", "specs", "node_modules", "vendor", "dist", "build", ".next", "coverage", "__pycache__"}
TEXT_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".go", ".rb", ".php", ".cs", ".rs", ".swift", ".kt", ".kts"}


def criteria(spec: Path) -> list[str]:
    return sorted(set(AC_PATTERN.findall(spec.read_text(encoding="utf-8"))))


def test_map(repo: Path) -> dict[str, list[dict[str, object]]]:
    mapped: dict[str, list[dict[str, object]]] = {}
    for path in repo.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or any(part in IGNORED_PARTS for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lines = content.splitlines()
        file_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        for line_no, line in enumerate(lines, 1):
            for ac in TAG_PATTERN.findall(line):
                context = "\n".join(lines[max(0, line_no - 2): min(len(lines), line_no + 1)])
                mapped.setdefault(ac, []).append({
                    "path": path.relative_to(repo).as_posix(),
                    "line": line_no,
                    "file_sha256": file_sha256,
                    "skipped": bool(SKIP_PATTERN.search(context)),
                })
    return mapped


def mapping_digest(mapping: dict[str, list[dict[str, object]]]) -> str:
    payload = json.dumps(mapping, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("feature", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Use -- followed by the real test command.")
    args = parser.parse_args()
    repo = args.repo.resolve()
    feature = (repo / args.feature).resolve()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("informe o comando de teste após --")
    spec = feature / "spec.md"
    if not spec.exists():
        parser.error(f"spec ausente: {spec}")
    ids = criteria(spec)
    mapping = test_map(repo)
    missing = [ac for ac in ids if not mapping.get(ac)]
    skipped = [ac for ac in ids if any(item["skipped"] for item in mapping.get(ac, []))]
    result = subprocess.run(command, cwd=repo, text=True, check=False)
    record = {
        "feature": feature.name,
        "generated_at": datetime.now(UTC).isoformat(),
        "command": command,
        "exit_code": result.returncode,
        "criteria": ids,
        "test_map": {ac: mapping.get(ac, []) for ac in ids},
        "mapping_sha256": mapping_digest({ac: mapping.get(ac, []) for ac in ids}),
        "passed": result.returncode == 0 and not missing and not skipped,
    }
    (feature / "verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if missing:
        print("FALHA: critérios sem teste anotado: " + ", ".join(missing))
    if skipped:
        print("FALHA: critérios com teste pulado/todo: " + ", ".join(skipped))
    if result.returncode:
        print(f"FALHA: comando de teste terminou com código {result.returncode}")
    if record["passed"]:
        print(f"OK: {feature} — {len(ids)} critérios com prova atual")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
