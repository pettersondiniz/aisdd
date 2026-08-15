# ExecPlan: {{FEATURE_TITLE}}

## Estado

Classe: {{CLASS}}
Contrato AISDD da feature: {{CONTRACT_VERSION}}
Fase: Discovery

Novas specs são criadas em v2 por padrão: o scaffolding grava o marcador
`Contrato AISDD da feature: v2` e cria os dois esqueletos JSON. Specs
existentes/legadas sem marcador e specs explicitamente criadas com
`--contract v1` permanecem em compatibilidade v1; não exigem os JSON v2 e não
há migração automática. O detector também aceita os aliases técnicos
documentados em `references/delegation-contract.md`; prefira o marcador
canônico.

## Contexto e restrições

Quando houver atribuição do chat principal, acrescente em uma linha própria a
declaração exata `Main-chat attribution: required`. O lifecycle obrigatório é
`start` → `close` → `report --final --output task-window-report.json`; o
relatório final deve estar fechado, não provisório, usar
`scope: main-chat-orchestrator` e declarar as exclusões de rollouts delegados,
ferramentas, modalidades e cobrança da assinatura. Custo `not-available` nunca
é zero e mantém o total combinado indisponível quando uma parcela necessária
faltar.

## Milestones

### M1 — {{MILESTONE}}

- [ ] Objetivo:
- Arquivos:
- Dependências:
- Passos:
- Validação:
- Risco/rollback:
- Concluído quando:

## Tarefas rastreáveis

| ID | Milestone | Critérios atendidos | Arquivos previstos | Dependências | Owner | Paralelização/condição | Status |
|---|---|---|---|---|---|---|---|
| T-001 | M1 | AC-001 |  |  |  |  | Pendente |

Em qualquer tarefa/WP delegável, Owner e Paralelização/condição são obrigatórios;
descreva se a execução é serial, paralela ou condicionada a outro WP. Tarefas
com arquivos em comum ou dependência explícita não podem ser executadas em
paralelo. `plan.md` é a fonte normativa desse grafo v1; `evidence.md` apenas
resume owners/dependências e registra provas.

## Work Packages e execução delegada

Em T1+ legado ou explicitamente v1, use as tarefas rastreáveis acima para
declarar o grafo de dependências e a paralelização em `plan.md`; não crie nem
exija arquivos v2. Preencha a seção abaixo quando a feature contiver o
marcador literal `Contrato AISDD da feature: v2` em uma única linha — como já
ocorre no scaffolding padrão para novas specs. O Planner continua owner do
plano técnico e do plano de execução; não crie uma role de planejamento nova.

| ID | Owner | Role | Depende de | Capabilities | Escopo permitido | Escopo proibido | Paralelização | Estado |
|---|---|---|---|---|---|---|---|---|
| WP-001 |  |  |  |  |  |  |  | pending |

Registre o digest de `work-packages.json` na evidência. Use `scope.write: []` e
`scope.forbidden: []` explicitamente para roles sem escrita; Planner, Architect
e roles de implementação devem declarar `scope.write` não vazio e permitido
pela allowlist da role. Achados de Verifier, Reviewer ou
Documentation Reviewer, assim como blockers ou critérios falhos do Test Engineer,
devem gerar um novo WP de correção para a role adequada; o fluxo retorna ao
Implementer e repete Test Engineer, Verifier e os revisores aplicáveis; não
esconda correções em um WP concluído. A ordem de revisão é Verifier →
(Reviewer || Documentation Reviewer), e os dois revisores só começam depois do
Verifier. Um escopo sobreposto só é permitido com dependência serial explícita
do WP corretivo.

## Descobertas e replanejamento
