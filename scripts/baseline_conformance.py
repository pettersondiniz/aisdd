#!/usr/bin/env python3
"""Create a documentation-only AISDD baseline and actionable follow-up specs."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_NAMES = ("docs", "specs", "AGENTS.md")
DENY = {".env", "node_modules", "__pycache__", ".git", "dist", "build"}
CURRENT_AGENT_MARKERS = (
    "## Mandatory AISDD triage",
    "Before changing code",
    "classify the request as T0",
    "T1+: use `$aisdd`",
    "T2+: use the subagents",
    "AISDD: not applicable",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def allowed(path: Path) -> bool:
    return not any(part in DENY for part in path.parts)


def documentation_files(repo: Path):
    for name in DOC_NAMES:
        target = repo / name
        if target.is_file():
            yield target
        elif target.is_dir():
            yield from (path for path in target.rglob("*") if path.is_file() and allowed(path))


def code_files(repo: Path):
    suffixes = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".cs", ".rb", ".php"}
    return [path for path in repo.rglob("*") if path.is_file() and path.suffix in suffixes and allowed(path)]


def relative(repo: Path, paths: list[Path]) -> list[str]:
    return [str(path.relative_to(repo)).replace("\\", "/") for path in paths]


def audit(repo: Path):
    gaps = []
    agents = repo / "AGENTS.md"
    agent_text = agents.read_text(encoding="utf-8", errors="ignore") if agents.exists() else ""
    missing_markers = [marker for marker in CURRENT_AGENT_MARKERS if marker not in agent_text]
    if missing_markers:
        gaps.append((
            "agents-guidance",
            "AGENTS.md ausente ou desatualizado: faltam marcadores da triagem AISDD obrigatoria.",
            {"missing_markers": missing_markers},
        ))
    if not (repo / "specs").is_dir():
        gaps.append(("feature-specifications", "Nao ha pasta specs/ para documentar funcionalidades e correcoes.", {}))
    if not (repo / "docs" / "architecture" / "decisions").is_dir():
        gaps.append(("architecture-decisions", "Nao ha pasta de ADRs para decisoes arquiteturais reconstruidas.", {}))

    tests = [path for path in code_files(repo) if "test" in path.name.lower()]
    mapped = sum("@spec:AC-" in path.read_text(encoding="utf-8", errors="ignore") for path in tests)
    if tests and not mapped:
        gaps.append(("test-traceability", "Testes existentes nao possuem mapeamento @spec:AC-xxx observavel.", {}))
    if not tests:
        gaps.append(("test-inventory", "Nenhuma suite de testes foi identificada; validar manualmente ou criar spec de cobertura.", {}))
    return gaps, tests


def write_gap_spec(repo: Path, baseline: str, slug: str, detail: str) -> None:
    """Create a complete but intentionally pending T1 artifact set for a follow-up."""
    folder = repo / "specs" / f"baseline-{baseline}-{slug}"
    if folder.exists():
        raise FileExistsError(f"spec de lacuna ja existe: {folder}")
    folder.mkdir(parents=True)
    title = f"Baseline gap: {slug}"
    (folder / "spec.md").write_text(
        f"# {title}\n\n## Objetivo\n\n{detail}\n\n"
        "## Fora de escopo\n\nNenhuma mudanca de produto e feita pela baseline.\n\n"
        "## Criterios de aceitacao\n\n"
        "- [ ] AC-001: A lacuna e resolvida em trabalho posterior e possui evidencia atual.\n",
        encoding="utf-8",
    )
    (folder / "plan.md").write_text(
        f"# ExecPlan: {title}\n\nClasse: T1\nFase: Discovery\n\n"
        "## Tarefas rastreaveis\n\n"
        "| ID | Criterios atendidos | Status |\n|---|---|---|\n"
        "| T-001 | AC-001 | Pendente: executar somente mediante solicitacao do usuario |\n",
        encoding="utf-8",
    )
    (folder / "status.md").write_text(
        "# Status\n\n- Classe: T1\n- Fase atual: Discovery\n"
        "- Origem: baseline-conformance\n- Proxima acao: aguardar solicitacao explicita para tratar a lacuna.\n",
        encoding="utf-8",
    )
    (folder / "evidence.md").write_text(
        f"# Evidencias: {title}\n\n"
        "Esta spec e um follow-up pendente criado pela baseline. Nao ha verificacao ainda, "
        "pois a baseline nao altera codigo ou testes.\n\n"
        "| Criterio | Evidencia | Status |\n|---|---|---|\n"
        "| AC-001 | A definir na execucao posterior | Pendente |\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("--baseline-id", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-documentation-only", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not repo.exists() or any(char in args.baseline_id for char in "/\\"):
        parser.error("repositorio ou baseline-id invalido")

    selected = list(documentation_files(repo))
    gaps, tests = audit(repo)
    root = repo / "docs" / "architecture" / "baselines" / args.baseline_id
    adr = repo / "docs" / "architecture" / "decisions" / f"ADR-BASELINE-{args.baseline_id}.md"
    manifest = {
        "schema_version": 1,
        "baseline_id": args.baseline_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "source_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True).stdout.strip() or "unavailable",
        "entries": [{"path": item, "sha256": sha(repo / item)} for item in relative(repo, selected)],
    }
    audit_plan = {
        "gaps": [{"slug": slug, "detail": detail, "evidence": evidence} for slug, detail, evidence in gaps],
        "code_files_observed": relative(repo, code_files(repo)),
        "tests_observed": relative(repo, tests),
    }
    if not args.apply:
        print(json.dumps({"would_write": [str(root), str(adr.relative_to(repo)), "specs/baseline-<id>-*"], "audit": audit_plan, "manifest": manifest}, ensure_ascii=False, indent=2))
        return 0
    if not args.confirm_documentation_only:
        parser.error("--apply exige --confirm-documentation-only")
    if root.exists() or adr.exists():
        parser.error("baseline ou ADR com esse id ja existe")

    root.mkdir(parents=True)
    legacy = root / "legacy"
    legacy.mkdir()
    for source in selected:
        destination = legacy / source.relative_to(repo)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "as-built.md").write_text(
        "# Estado observado\n\nInventario inferido de codigo, testes e documentacao; nao e intencao historica confirmada.\n\n"
        "## Arquivos de codigo\n" + "\n".join(f"- {item}" for item in audit_plan["code_files_observed"]) + "\n\n"
        "## Testes observados\n" + "\n".join(f"- {item}" for item in audit_plan["tests_observed"]) + "\n",
        encoding="utf-8",
    )
    (root / "report.md").write_text(
        "# Relatorio de baseline\n\n## Lacunas\n" + "\n".join(f"- {item['slug']}: {item['detail']}" for item in audit_plan["gaps"]) + "\n\n"
        "## Alteracoes realizadas\n- Backup documental em legacy/.\n- Manifesto com hashes.\n- Estado observado e ADR reconstruido.\n- Specs pendentes para cada lacuna.\n\n"
        "Nenhum codigo, teste, dependencia, configuracao, infraestrutura, banco ou CI foi alterado.\n",
        encoding="utf-8",
    )
    adr.parent.mkdir(parents=True, exist_ok=True)
    adr.write_text(
        f"# ADR-BASELINE-{args.baseline_id}: Baseline conformance\n\nStatus: Reconstructed\n\n"
        "## Decisao\n\nPreservar a documentacao existente, registrar o estado observado e transformar lacunas em specs pendentes.\n\n"
        "## Evidencia e confianca\n\nBaseado em inventario estatico de arquivos; confianca limitada, sem inferir intencao historica.\n",
        encoding="utf-8",
    )
    if not (repo / "AGENTS.md").exists():
        shutil.copy2(ROOT / "assets" / "templates" / "AGENTS.md", repo / "AGENTS.md")
    for slug, detail, _ in gaps:
        write_gap_spec(repo, args.baseline_id, slug, detail)
    print(f"OK: baseline criada com {len(gaps)} lacunas em {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
