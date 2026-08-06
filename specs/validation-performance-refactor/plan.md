# ExecPlan: Otimização do fluxo de validação AISDD

## Estado

Classe: T2
Fase: Completion

## Contexto e restrições

A mudança é uma refatoração localizada nos scripts de validação. Deve preservar a CLI, as regras de validação e o tratamento especial das features baseline. Não há interface visual, portanto a validação de browser e a skill de design não se aplicam.

## Milestones

### M1 — Especificar o contrato e a linha de base

- [x] Objetivo: registrar comportamento, invariantes, compatibilidade e critérios rastreáveis.
- Arquivos: `specs/validation-performance-refactor/{spec,plan,status,evidence}.md`.
- Dependências: leitura dos scripts e testes atuais.
- Passos: classificar como T2; registrar o drift preexistente; identificar o caminho real `scripts/`/`tests/`.
- Validação: testes atuais passam; estado inicial documentado.
- Risco/rollback: somente artefatos de documentação; remover a pasta da feature se necessário.
- Concluído quando: spec e plano tiverem critérios sem perguntas abertas.

### M2 — Refatorar o fluxo e adicionar cobertura

- [x] Objetivo: extrair a função reutilizável, eliminar subprocessos por feature e cobrir o cache compartilhado.
- Arquivos: `scripts/validate_feature.py`, `scripts/check_drift.py`, `tests/test_check_drift.py`.
- Dependências: M1.
- Passos: mover a lógica de validação para `validate_feature`; manter `main()` como wrapper; importar a função no drift checker; calcular `test_map` uma vez; adicionar testes para mapa compartilhado, baseline e CLI.
- Validação: `python -m unittest discover -s tests -v`.
- Risco/rollback: regressão de import ou de saída CLI; reverter somente os três arquivos de código/teste caso os testes revelem incompatibilidade.
- Concluído quando: AC-601 a AC-604 tiverem testes anotados.

### M3 — Verificar, revisar e registrar evidências

- [x] Objetivo: obter prova mecânica atual e revisão do diff.
- Arquivos: `specs/validation-performance-refactor/verification.json`, `evidence.md` e `status.md`.
- Dependências: M2.
- Passos: executar o comando real pelo `verify_feature.py`; executar `validate_feature.py`; executar `check_drift.py`; revisar diff e atualizar evidências sem mascarar drift externo.
- Validação: comandos AISDD executados; a feature passou. O check global continua apontando apenas drift preexistente fora do escopo.
- Risco/rollback: `verification.json` é gerado pelo verificador; não editar manualmente.
- Concluído quando: critérios têm mapa de testes atual, limitações documentadas e o plano/status refletem a realidade.

## Tarefas rastreáveis

| ID | Milestone | Critérios atendidos | Arquivos previstos | Dependências | Status |
|---|---|---|---|---|---|
| T-601 | M1 | AC-601–AC-604 | `spec.md`, `plan.md`, `status.md`, `evidence.md` | Nenhuma | Completa |
| T-602 | M2 | AC-601 | `scripts/validate_feature.py` | T-601 | Completa |
| T-603 | M2 | AC-602 | `scripts/validate_feature.py`, `tests/test_check_drift.py` | T-602 | Completa |
| T-604 | M2 | AC-603–AC-604 | `scripts/check_drift.py`, `tests/test_check_drift.py` | T-602 | Completa |
| T-605 | M3 | AC-601–AC-604 | `verification.json`, `evidence.md`, `status.md` | T-603, T-604 | Completa |

Tarefas com arquivos em comum ou dependência explícita não serão executadas em paralelo.

## Descobertas e replanejamento

- O código atual está em `scripts/` e `tests/`, embora as imagens mencionem `skills/aisdd/`.
- A linha de base tem 28 testes passando.
- `scripts/check_drift.py` já possui uma exceção para features baseline; ela será preservada.
- O drift atual de `specs/agent-runtime-model-evidence/verification.json` antecede esta mudança e será reportado separadamente.
