# Evidências: Agent runtime model evidence

## Comandos executados

| Comando | Resultado | Quando |
|---|---|---|
| `python -m unittest discover -s tests -v` | 20 testes passaram | 2026-08-02 |
| `python scripts/agent_evidence.py --agent-id /root/agent_evidence_planning --json` | `resolved`: Terra / medium por `local-rollout-turn_context:last-readable` | 2026-08-02 |
| `python scripts/agent_evidence.py --agent-id /root/agent_evidence_review --json` | `resolved`: Terra / medium por `local-rollout-turn_context:last-readable` | 2026-08-02 |
| `python scripts/verify_feature.py . specs/agent-runtime-model-evidence -- python -m unittest discover -s tests -v` | 3 critérios com prova atual | 2026-08-02 |
| `python scripts/validate_feature.py . specs/agent-runtime-model-evidence` | passou | 2026-08-02 |
| `python scripts/check_drift.py .` | nenhum drift estrutural ou de rastreabilidade | 2026-08-02 |
| `python scripts/agent_evidence.py --rollout-id 019fc476-042b-7b23-8c1f-8c38e2bed985 --json` | `resolved`: gpt-5.5 / high | 2026-08-02 |
| cinco consultas por `--rollout-id` fornecido | todos os modelos/efforts do relato confirmados | 2026-08-02 |

## Rastreabilidade

| Critério | Implementação | Teste/evidência | Status |
|---|---|---|---|
| AC-401 | Consulta de rollout único por identificador do agente | `tests/test_agent_evidence.py` (`@spec:AC-401`) | Passou |
| AC-402 | Leitura de `collaboration_mode.settings` | `tests/test_agent_evidence.py` (`@spec:AC-402`) | Passou |
| AC-403 | Estados `not-available` e `ambiguous` sem inferência | `tests/test_agent_evidence.py` (`@spec:AC-403`) | Passou |
| AC-404 | Seleção direta por UUID terminal de rollout legado; prefixos parciais recusados | `tests/test_agent_evidence.py` (`@spec:AC-404`) | Passou |

## Verificação mecânica

`verification.json` é gerado por `scripts/verify_feature.py`; não é editado manualmente.

## Checks não executados

- Nenhum.

## Rastreabilidade de agentes

| Papel | Agente | Tarefa | Modelo solicitado | Effort solicitado | Modelo efetivo | Effort efetivo | Fonte efetiva | Fallback | Resultado |
|---|---|---|---|---|---|---|---|---|---|
| planner | `/root/agent_evidence_planning` | Planejar consulta local de evidência | inherit | inherit | gpt-5.6-terra | medium | `local-rollout-turn_context:last-readable` | configurado indisponível; herdado | plano entregue |
| reviewer | `/root/agent_evidence_review` | Revisar correlação, privacidade e testes | inherit | inherit | gpt-5.6-terra | medium | `local-rollout-turn_context:last-readable` | configurado indisponível; herdado | 4 achados corrigidos; confirmação sem novos achados |

Resumo: agentes usados: 2; fallbacks: 2.

## Riscos residuais

- O rollout local é a melhor evidência disponível, não uma prova criptográfica da inferência do backend.
- Se o runtime não persistir uma correlação única, o fluxo registra `unknown`.
