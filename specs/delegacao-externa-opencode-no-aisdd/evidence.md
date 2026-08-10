# Evidências: Delegação externa OpenCode somente leitura

## Rastreabilidade

`verification.json` preserva a prova anotada para AC-001–AC-019. Os marcadores de teste declarados são: `@spec:AC-001`, `@spec:AC-002`, `@spec:AC-003`, `@spec:AC-004`, `@spec:AC-005`, `@spec:AC-006`, `@spec:AC-007`, `@spec:AC-008`, `@spec:AC-009`, `@spec:AC-010`, `@spec:AC-011`, `@spec:AC-012`, `@spec:AC-013`, `@spec:AC-014`, `@spec:AC-015`, `@spec:AC-016`, `@spec:AC-017`, `@spec:AC-018` e `@spec:AC-019`.

## Work Packages e agentes

| WP | Estado final | Agente ou fechamento | Resultado |
|---|---|---|---|
| WP-001–WP-011 | completed | IDs históricos `external-routing-*` | Execução histórica preservada; sem telemetria completa de tokens/custo. |
| WP-012–WP-013 | completed | `not-available:WP-012/013` | Falhas históricas preservadas e fechadas por reconciliação nativa; nenhum sucesso externo alegado. |
| WP-014 | completed | `019fe3d6-7cb3-75e0-bcc7-66424c167027` | Reconciliação parcial histórica fechada pela consolidação documental autorizada. |
| WP-015 | completed | `019fe3de-e037-79a0-9e55-7d08e22cf0af` | Fallback direto auditado no escopo de `scripts/verify_feature.py`; `py_compile` focado passou. |
| WP-016 | completed | `019fe3e2-ca0d-72b1-84e4-7654e08bfd67` | Blocker histórico preservado; fechamento por rerun nativo com prova funcional atual. |
| WP-017–WP-018 | completed | `not-available:WP-017/018` | WPs históricos pendentes fechados pela evidência local reconciliada. |
| WP-019 | completed | `019fe3e7-7e8f-79e0-bc13-07c9c2a9c426` | Referências dos validadores corrigidas; `--help` passou. |
| WP-020 | completed | `019fe3f1-40b0-7173-8814-63e765b44cec` | Falha histórica preservada; fechamento com a matriz funcional atual, sem alteração de testes. |
| WP-021–WP-023 | completed | `not-available:WP-021/022/023` | WPs históricos pendentes fechados por rerun/reconciliação nativa; nenhum sucesso externo alegado. |
| WP-024 | completed | `019fec0c-b0af-7871-9719-0eaf0b6cb6d3` | Compatibilidade dos helpers confirmada por fallback nativo; nenhuma edição nesta reconciliação. |
| WP-025 | completed | `019fec1d-f4df-7611-83e6-3c3291df8d0e` | Test Engineer final histórico: suíte 160 passed, 2 skipped; focused 21 passed. A reconciliação posterior confirmou 163 passed, 2 skipped; focused external/delegation 69 passed; regressões `isError` 3 passed. |
| WP-026 | completed | `019fec20-365a-77f1-afb3-1a8100f64207` | Verifier final histórico: 19 ACs aprovados por `verify_feature.py`; o refresh oficial posterior manteve os 19 ACs aprovados com o mapa atual. |
| WP-027–WP-028 | completed | `not-available:WP-027/028` | Revisões finais fechadas por reconciliação nativa; nenhum sucesso externo alegado. |

Os estados históricos failed, stalled, blocked, in_progress e pending também estão preservados nos campos `history`/`result` de `work-packages.json` e nas entradas correspondentes de `delegation-evidence.json`. O estado efetivo é completed para todos os 28 WPs, com digest atual e `blockers` vazio.

## Prova funcional

| Comando | Resultado registrado |
|---|---|
| `python -m pytest tests -q` | 163 passed, 2 skipped |
| `python -m pytest tests/test_external_model_routing.py tests/test_delegation_routing.py tests/test_delegation_contract.py tests/test_delegation_telemetry.py -q` | 69 passed |
| `python -m pytest tests/test_external_model_routing.py -k is_error -q` | 3 passed, 21 deselected |
| `python scripts/verify_feature.py . specs/delegacao-externa-opencode-no-aisdd -- python -m pytest tests -q` | Exit code 0 — 19 critérios de aceitação aprovados; suíte subjacente 163 passed, 2 skipped |

Esses resultados são a base nativa usada para encerrar os WPs históricos. Não foram inventados resultados de agentes externos, nem executado Agent Bridge/MCP nesta reconciliação.

O histórico anterior de WP-025/WP-026 permanece explícito acima; os resultados atuais são a reconciliação após a correção final de `isError`. O digest do manifesto permanece `c614d1409efd0a058d1b67b993a34c3e24b03fc376f5e73eb59498236f9945e6`, pois nenhum Work Package foi alterado.

## Checks de artefatos

| Comando | Resultado |
|---|---|
| `python scripts/validate_feature.py . specs/delegacao-externa-opencode-no-aisdd` | Exit code 0 — `OK: D:\\codex\\aisdd\\specs\\delegacao-externa-opencode-no-aisdd` |
| `python scripts/check_drift.py .` | Exit code 0 — `OK: nenhum drift estrutural ou de rastreabilidade encontrado` |

Esses checks validam os artefatos reconciliados, o estado completed de todos os WPs, a correspondência de evidências e o digest atual; não substituem a prova funcional registrada acima.

## Limitações e custo

Não há telemetria correlacionável completa de modelo, tokens ou preço para os agentes históricos ou para os fechamentos nativos. Custos permanecem `not-available`, nunca zero.

### Custo total da tarefa

`not available` — nenhum rollout possui estimativa completa correlacionável; excluídos o chat principal, ferramentas, modalidades e cobrança de assinatura.
