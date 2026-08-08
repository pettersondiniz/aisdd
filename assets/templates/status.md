# Status: {{FEATURE_TITLE}}

- Classe: {{CLASS}}
- Contrato AISDD da feature: {{CONTRACT_VERSION}}
- Fase atual: Discovery
- Última atualização: {{DATE}}
- Próxima ação:
- Bloqueios:

Novas specs usam v2 por padrão e recebem o marcador e os esqueletos JSON pelo
scaffolding. Ausência de marcador ou `--contract v1` explícito identifica
compatibilidade v1 para specs existentes/legadas; esse modo não exige
`work-packages.json` nem `delegation-evidence.json` e não é migrado
automaticamente.

## Histórico

## Decisões recentes

Quando `plan.md` declarar `Main-chat attribution: required`, o estado só pode
ser considerado documentado com o lifecycle `start` → `close` →
`report --final --output task-window-report.json`. A janela/relatório final
devem estar fechados, não provisórios, usar `scope: main-chat-orchestrator` e
declarar as exclusões explícitas. Custo `not-available` permanece indisponível;
nunca o registre como zero nem o some ao total combinado.

## Delegação v2

Quando aplicável, registre o WP atual, owner, role, dependências, blockers,
fallback auditado e próxima transição. A ausência de executor externo é uma
limitação explícita, não uma capability implícita do Orchestrator. Um blocker,
critério falho ou correção exigida pelo Test Engineer abre novo WP para o
Implementer; após a correção, repita Test Engineer, Verifier e os revisores
aplicáveis. O grafo normativo está em `plan.md`; `evidence.md` apenas resume
owners/dependências e registra provas.
