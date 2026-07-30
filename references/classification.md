# Classificação T0–T4

| Classe | Sinal | Processo mínimo |
|---|---|---|
| T0 | Mecânico, sem comportamento externo novo | Alteração direta + check local |
| T1 | Bug localizado ou pequena mudança conhecida | Spec leve + plano curto + teste |
| T2 | Feature, refactor relevante ou contrato alterado | Spec + design local + plano + testes + review + evidence |
| T3 | Migração, persistência, integração ou arquitetura | T2 + ADR + rollout/rollback + observabilidade |
| T4 | Irreversível, crítico, regulatório ou alto blast radius | T3 + aprovação explícita + plano de contingência e execução controlada |

Use a classe mais alta quando houver dúvida. A classe pode subir durante a descoberta; nunca a reduza para evitar controles.

