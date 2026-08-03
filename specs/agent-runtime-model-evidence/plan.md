# ExecPlan: Agent runtime model evidence

## Estado

Classe: T2
Fase: Implementation

## Contexto e restrições

O utilitário deve aceitar metadados V1 e V2, ser somente leitura e nunca resolver candidatos ambíguos por ordem de arquivo.

## Milestones

### M1 — Consulta confiável de rollout

- [x] Objetivo: implementar consulta de metadados efetivos do subagente.
- Arquivos: `scripts/agent_evidence.py`, `tests/test_agent_evidence.py`.
- Dependências: sessão Codex local, opcional em cada execução.
- Passos: localizar somente rollouts filhos; filtrar por identificador/role/pai; extrair `turn_context`; recusar ambiguidade.
- Validação: testes unitários com rollouts sintéticos e uma leitura local real.
- Risco/rollback: o formato de sessão pode mudar; o resultado passa a `not-available`, sem impedir a feature.
- Concluído quando: AC-401 a AC-403 passarem.

### M2 — Integração de evidência

- [x] Objetivo: tornar a consulta parte da instrução e do template AISDD.
- Arquivos: `SKILL.md`, `references/model-routing.md`, `assets/templates/evidence.md`, testes de template.
- Dependências: M1.
- Passos: documentar o comando, a prioridade do `turn_context` e a regra `unknown`.
- Validação: teste do template e revisão independente.
- Risco/rollback: documentação pode ficar prescritiva demais; manter a consulta como melhor esforço.
- Concluído quando: template declara a fonte e a ausência honesta.

## Tarefas rastreáveis

| ID | Milestone | Critérios atendidos | Arquivos previstos | Dependências | Status |
|---|---|---|---|---|---|
| T-401 | M1 | AC-401 | `scripts/agent_evidence.py`, testes | nenhum | Concluída |
| T-402 | M1 | AC-402 | `scripts/agent_evidence.py`, testes | nenhum | Concluída |
| T-403 | M1 | AC-403 | `scripts/agent_evidence.py`, testes | nenhum | Concluída |
| T-404 | M2 | AC-401, AC-402, AC-403 | skill, referência e template | M1 | Concluída |
| T-405 | M1 | AC-404 | `scripts/agent_evidence.py`, testes | nenhum | Concluída |

Tarefas com arquivos em comum ou dependência explícita não podem ser executadas em paralelo.

## Descobertas e replanejamento

- O formato V1 e V2 local observado usa `session_meta.payload.source.subagent.thread_spawn`; o modelo aparece em `turn_context.payload.model`, e effort também pode estar em `payload.effort` ou `collaboration_mode.settings`.
