# ExecPlan: Delegated rollout observability

## Estado

Classe: T3
Contrato AISDD da feature: v2
Fase: Concluída

## Contexto e restrições

Esta mudança é limitada à skill AISDD. O manifesto de delegação é um artefato
local, separado do relatório do chat principal. Nenhum evento sintético é
gerado: `task_window.py` continua consumindo somente markers presentes no
runtime.

## Milestones

### M1 — Contrato e roteamento

- Arquivos: `scripts/model_routing.py`, `references/model-routing.md`.
- Passos: adicionar a guarda de modelo/effort, preservar o resolver existente e
  documentar mismatch, override e indisponibilidade.
- Validação: testes AC-804 e compilação do script.

### M2 — Manifesto e coleta

- Arquivos: `scripts/delegation_telemetry.py`, template de evidência e
  documentação da skill.
- Passos: registrar WPs de forma idempotente, correlacionar rollouts, calcular
  tokens/custo observáveis e manter indisponíveis fora do subtotal.
- Validação: testes AC-801, AC-802 e AC-803.

### M3 — Verificação e instalação

- Arquivos: `specs/delegated-rollout-observability/*`, testes e ADR.
- Passos: validar contrato v2, executar suíte completa, gerar
  `verification.json` e sincronizar a skill para a instalação global.
- Validação: `validate_feature.py`, `verify_feature.py`, suíte unittest e
  `check_drift.py`.

## Tarefas rastreáveis

| ID | Milestone | Critérios atendidos | Arquivos previstos | Dependências | Owner | Paralelização/condição | Status |
|---|---|---|---|---|---|---|---|
| T-001 | M1 | AC-804 | scripts/model_routing.py, references/model-routing.md | — | architect → implementer | serial | Concluída |
| T-002 | M2 | AC-801, AC-802, AC-803 | scripts/delegation_telemetry.py, testes, docs | T-001 | implementer → test-engineer | serial | Concluída |
| T-003 | M3 | AC-801..AC-804 | specs/delegated-rollout-observability, ADR | T-002 | verifier → reviewers | serial após testes | Concluída |

## Work Packages e execução delegada

O grafo normativo completo está em `work-packages.json`. A execução foi
concluída com Planner e Architect observados em rollouts dedicados. Após
tentativas de implementação/teste sem aplicação de patch, o chat principal
usou fallback direto autorizado e o registrou em `delegation-evidence.json`;
Verifier e revisores também têm evidência de auditoria direta, sem atribuir
essas ações a um falso agente.

| ID | Owner | Role | Depende de | Capabilities | Escopo permitido | Escopo proibido | Paralelização | Estado |
|---|---|---|---|---|---|---|---|---|
| WP-001 | planner-rollout | planner | — | plan-execution | leitura da skill/spec | agent-bridge-mcp | serial | completed |
| WP-002 | architect-rollout | architect | WP-001 | design, adr | leitura da skill/spec | agent-bridge-mcp | serial | completed |
| WP-003 | main-chat-fallback-implementer | implementer | WP-002 | implement | scripts, testes, docs e spec | agent-bridge-mcp | serial | completed |
| WP-004 | main-chat-fallback-test-engineer | test-engineer | WP-003 | write-tests | testes | agent-bridge-mcp | serial | completed |
| WP-005 | main-chat-fallback-verifier | verifier | WP-004 | verify-final | scripts e testes | agent-bridge-mcp | serial | completed |
| WP-006 | main-chat-fallback-reviewer | reviewer | WP-005 | review | arquivos alterados | agent-bridge-mcp | serial | completed |
| WP-007 | main-chat-fallback-documentation-reviewer | documentation-reviewer | WP-005 | review-docs | documentação | agent-bridge-mcp | serial | completed |

Todas as roles independentes têm agent_id distinto. A ordem é Planner →
Architect → Implementer → Test Engineer → Verifier → (Reviewer ||
Documentation Reviewer), com a execução dos dois revisores mantida serial no
registro por dependerem da mesma verificação final.

## Descobertas e replanejamento

- A telemetria não deve inferir o modelo efetivo a partir do modelo solicitado;
  a evidência do rollout é a fonte observável.
- O cálculo delegado não inclui o chat principal; esse cálculo continua no
  lifecycle explícito de `task_window.py`.
