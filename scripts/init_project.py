#!/usr/bin/env python3
"""Scaffold AISDD repository artifacts without overwriting user files."""
from __future__ import annotations
import argparse
from datetime import date
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

def copy_if_missing(src: Path, dst: Path) -> bool:
    if dst.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repo", type=Path)
    args = p.parse_args()
    repo = args.repo.resolve()
    if not repo.exists():
        p.error(f"repositório não encontrado: {repo}")
    created = []
    targets = {
        ROOT / "assets/templates/AGENTS.md": repo / "AGENTS.md",
    }
    for src, dst in targets.items():
        if copy_if_missing(src, dst): created.append(str(dst.relative_to(repo)))
    for directory in (repo / "docs/product", repo / "docs/architecture/decisions", repo / "docs/development", repo / "specs"):
        directory.mkdir(parents=True, exist_ok=True)
    index = repo / "specs/index.md"
    if not index.exists():
        index.write_text("# Feature specifications\n\n| Feature | Classe | Fase | Status |\n|---|---|---|---|\n", encoding="utf-8")
        created.append("specs/index.md")
    stamp = repo / "docs/development/aisdd.md"
    if not stamp.exists():
        stamp.write_text(f"# AISDD\n\nInicializado em {date.today().isoformat()}. Substitua os comandos em `AGENTS.md` pelos comandos reais do projeto.\n", encoding="utf-8")
        created.append("docs/development/aisdd.md")
    print("Criados:")
    print("\n".join(f"- {x}" for x in created) if created else "- nada (arquivos já existentes)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
