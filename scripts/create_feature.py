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

def render(text: str, title: str, cls: str, contract: str) -> str:
    return (
        text.replace("{{FEATURE_TITLE}}", title)
        .replace("{{CLASS}}", cls)
        .replace("{{CONTRACT_VERSION}}", contract)
        .replace("{{DATE}}", date.today().isoformat())
        .replace("{{MILESTONE}}", "Preparação")
    )


def write_v2_skeletons(feature: Path) -> None:
    (feature / "work-packages.json").write_text(
        """{
  "contract": "v2",
  "contract_version": "v2",
  "status": "incomplete",
  "planner_todo": "Preencha Work Packages, owners, roles, dependências, capabilities, escopos, critérios e estados.",
  "work_packages": []
}
""",
        encoding="utf-8",
    )
    (feature / "delegation-evidence.json").write_text(
        """{
  "contract": "v2",
  "contract_version": "v2",
  "status": "incomplete",
  "planner_todo": "Preencha digest, required_roles e evidências de delegação após a execução dos Work Packages.",
  "work_packages_sha256": "",
  "required_roles": [],
  "delegations": []
}
""",
        encoding="utf-8",
    )

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repo", type=Path)
    p.add_argument("title")
    p.add_argument("--class", dest="cls", choices=["T0", "T1", "T2", "T3", "T4"], default="T2")
    p.add_argument(
        "--contract",
        choices=["v1", "v2"],
        default="v2",
        help="contrato da feature; v2 é o padrão, v1 é compatibilidade explícita",
    )
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
        (feature / name).write_text(render(source.read_text(encoding="utf-8"), args.title, args.cls, args.contract), encoding="utf-8")
    if args.contract == "v2":
        write_v2_skeletons(feature)
    print(feature)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
