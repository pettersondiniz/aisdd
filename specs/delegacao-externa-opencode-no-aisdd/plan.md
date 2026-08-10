# ExecPlan: Delegação externa OpenCode somente leitura

Classe: T3  
Contrato AISDD da feature: v2  
Impacto documental: sim

## Milestones

- T-001 — Design e contrato: WP-001/WP-002 definiram a rota externa read-only, matching literal, fallback e ADR para AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018 e AC-019. Concluído.
- T-002 — Implementação: WP-003, WP-008 e WP-009 implementaram a integração no AISDD sem alterar Agent Bridge. Concluído.
- T-003 — Testes e primeira validação: WP-004/WP-005 e WP-010/WP-011 produziram a prova inicial. Concluído.
- T-004 — Revisão e reconciliação: WP-006/WP-007 e os fechamentos posteriores produziram a reconciliação documental final. Concluído.
- T-005 — Correções pós-validação: WP-015 e WP-019 concluíram as correções históricas; WP-024 fechou a compatibilidade por fallback nativo auditado. Concluído.
- T-006 — Reruns independentes: WP-025 e WP-026 registraram a matriz funcional atual; os WPs de revisão aplicáveis foram fechados com a evidência local reconciliada. A reconciliação posterior à correção final de `isError` confirmou a suíte completa, o focused external/delegation e as três regressões. Concluído.

## Grafo normativo

`WP-001 → WP-002 → WP-003 → WP-004 → WP-005 → (WP-006 || WP-007) → WP-008 → WP-009 → WP-010 → WP-011 → (WP-012 || WP-013) → WP-014 → WP-015 → WP-016`

Correções posteriores preservadas no mesmo manifesto:

`WP-016 → WP-019 → WP-020 → WP-024 → WP-025 → WP-026 → (WP-027 || WP-028)`

`WP-016 → (WP-017 || WP-018)` e `WP-020 → WP-021 → (WP-022 || WP-023)`.

## Histórico preservado

Os estados históricos failed, stalled, blocked, in_progress e pending permanecem nos campos `history`/`result` dos WPs e nas entradas correspondentes de `delegation-evidence.json`. O estado efetivo de todos os WPs é completed porque a evidência final nativa encerrou essas tentativas sem reivindicar sucesso externo.

## Condição de conclusão

Todos os WPs estão completed, cada WP possui evidência correspondente, o digest do manifesto está atualizado (`c614d1409efd0a058d1b67b993a34c3e24b03fc376f5e73eb59498236f9945e6`) e `blockers` está vazio. A prova funcional registrada é `python -m pytest tests -q = 163 passed, 2 skipped`, focused external/delegation `= 69 passed`, regressões `isError` `= 3 passed` e `verify_feature.py` com o separador obrigatório `= 19 ACs passed`. O rollback continua sendo remover ou desativar `[external]`; Agent Bridge permanece fora do escopo.
