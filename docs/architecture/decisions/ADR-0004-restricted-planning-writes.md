# ADR-0004: Escrita restrita para planejamento e ADRs

## Status

Aceito — 2026-08-15

## Contexto

O Planner precisava produzir `spec.md`, `plan.md`, status e manifests v2, mas
era classificado como read-only e nenhum executor autorizado podia materializar
esses artefatos. O Architect tinha a mesma limitação para ADRs.

## Decisão

No contrato v2, Planner e Architect podem declarar escrita restrita por role:

- Planner: `specs/<slug>/{spec,plan,status}.md`,
  `work-packages.json` e `delegation-evidence.json`.
- Architect: `docs/architecture/decisions/ADR-*.md`.

As capabilities `write-planning` e `write-adr` são exigidas somente quando o
WP usa `scope.write`; WPs históricos sem escrita permanecem compatíveis. As
duas roles continuam sem capabilities de implementação, testes, build ou
validação final. `orchestrator`, `verifier`, `reviewer` e
`documentation-reviewer` permanecem sem escrita.

## Consequências

O schema de `scope.write` valida caminhos relativos e a allowlist da role.
Isso permite materializar o planejamento sem abrir acesso a código, testes,
dependências, infraestrutura ou validação final. Fallbacks diretos continuam
exigindo aprovação, indisponibilidade observada, escopo e resultado auditáveis.
