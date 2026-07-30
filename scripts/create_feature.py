#!/usr/bin/env python3
"""Create a feature artifact set from AISDD templates."""
from __future__ import annotations
import argparse
from datetime import date
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]

def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    return re.sub(r"[-\s]+", "-", value).strip("-") or "feature"

def render(text: str, title: str, cls: str) -> str:
    return text.replace("{{FEATURE_TITLE}}", title).replace("{{CLASS}}", cls).replace("{{DATE}}", date.today().isoformat()).replace("{{MILESTONE}}", "Preparação")

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repo", type=Path)
    p.add_argument("title")
    p.add_argument("--class", dest="cls", choices=["T0", "T1", "T2", "T3", "T4"], default="T2")
    p.add_argument("--slug")
    args = p.parse_args()
    repo = args.repo.resolve()
    slug = args.slug or slugify(args.title)
    feature = repo / "specs" / slug
    if feature.exists():
        p.error(f"feature já existe: {feature}")
    feature.mkdir(parents=True)
    for name in ("spec.md", "plan.md", "status.md", "evidence.md"):
        source = ROOT / "assets/templates" / name
        (feature / name).write_text(render(source.read_text(encoding="utf-8"), args.title, args.cls), encoding="utf-8")
    print(feature)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
