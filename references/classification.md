# Classificação T0–T4

| Classe | Sinal | Processo mínimo |
|---|---|---|
| T0 | Mecânico, sem comportamento externo novo | Fora do contrato somente se realmente não delegável; caso contrário role adequada + menor check local |
| T1 | Bug localizado ou pequena mudança conhecida | Spec leve + plano curto + Planner + Implementer + Test Engineer + Verifier |
| T2 | Feature, refactor relevante ou contrato alterado | Spec + design local + plano + Planner + Implementer + Test Engineer + Verifier + Reviewer + evidence; Documentation Reviewer somente se houver impacto documental |
| T3 | Migração, persistência, integração ou arquitetura | T2 + Planner + Architect + Documentation Reviewer + ADR + rollout/rollback + observabilidade |
| T4 | Irreversível, crítico, regulatório ou alto blast radius | T3 + aprovação humana explícita + plano de contingência e execução controlada |

Use a classe mais alta quando houver dúvida. A classe pode subir durante a descoberta; nunca a reduza para evitar controles. Em T0 v2, a evidência de conclusão exige `mechanical_non_delegable.approved: true` com justificativa auditável ou uma role especializada; `orchestrator/coordinate` não cobre trabalho delegável.

Em T1+ v1, o Planner deve registrar no `plan.md` o grafo declarativo de tarefas,
dependências, owners e paralelização; `plan.md` é a fonte normativa e
`evidence.md` apenas resume o grafo e registra provas. Isso não exige os
artefatos JSON v2 sem marcador explícito.

Para este gate, há impacto documental quando o trabalho altera ou cria
documentação ou artefatos normativos, como README, SKILL, references, ADR,
templates, AGENTS, instruções de agentes ou os artefatos `spec.md`, `plan.md`,
`status.md` e `evidence.md`. Em T2, o Planner/Orchestrator declara esse impacto
no `plan.md` e requer manualmente Documentation Reviewer quando ele existe; o
validador v2 não infere nem acrescenta essa role condicional. Sem impacto
declarado, essa role não é exigida. Em T3/T4, Documentation Reviewer é
obrigatória pela classe, com ou sem impacto documental.

## Delegação e fallback

Trabalho delegável nunca é executado diretamente pelo Orchestrator. Se uma role
ou agente exigido não estiver disponível, o trabalho fica `BLOCKED` até decisão
humana. Um fallback direto só pode ser usado com aprovação explícita e registro
auditável de motivo, agente indisponível, tentativas, escopo e resultado; não há
exceção por trabalho trivial ou ausência de registro.
