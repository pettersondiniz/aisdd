# ExecPlan: Baseline conformance and UI traceability

Classe: T3
Fase: Validation

## Milestones

### M1 - Auditoria documental

- Arquivos: `scripts/baseline_conformance.py`, `references/baseline-conformance.md`.
- Passos: validar marcadores obrigatorios de AGENTS; criar backup, manifesto, estado observado, ADR reconstruido e follow-ups documentais.
- Risco/rollback: o comando so escreve com `--apply --confirm-documentation-only`; os resultados sao novos arquivos documentais.

### M2 - Evidencia

- Arquivos: `tests/test_interface_validation.py`, `specs/baseline-conformance-ui-traceability/`.
- Passos: cobrir AGENTS legado e preservacao de codigo; atualizar rastreabilidade de UI/agentes.

## Tarefas rastreaveis

| ID | Milestone | Criterios atendidos | Status |
|---|---|---|---|
| T-201 | M1 | AC-201, AC-202, AC-203, AC-204 | Concluida |
| T-202 | M2 | AC-201, AC-202, AC-203, AC-204 | Concluida |
