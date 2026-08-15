# Padrão de ExecPlan

O `plan.md` deve permitir que outro agente retome o trabalho sem depender do histórico da conversa.

Cada milestone deve conter objetivo, arquivos prováveis, dependências, passos, testes, risco e condição de conclusão. Atualize checkboxes e registre descobertas. Não esconda trabalho futuro em uma lista vaga.

Planeje em fatias verticais quando possível. Separe migrações destrutivas, flags, rollout e rollback. Reavalie o plano antes de cada milestone se o código divergir da hipótese inicial.

## Plano declarativo v1

Em T1+ v1, o Planner declara em `plan.md` as tarefas, owners, dependências,
critérios e condições de paralelização. `plan.md` é a fonte normativa do grafo
declarativo v1. `evidence.md` apenas resume owners/dependências e registra
provas; não é uma segunda fonte do grafo. Isso não cria nem exige
`work-packages.json` ou `delegation-evidence.json`.

## Plano de execução v2

Quando a feature tiver o marcador `Contrato AISDD da feature: v2`, o Planner
também deve projetar `work-packages.json`. Cada WP declara owner, role canônica,
dependências, capabilities, critérios de aceitação, estado, escopo permitido e
escopo proibido. Declare uma ordem topológica determinística e condições de
paralelização. WPs com escrita sobreposta devem ser separados ou ligados por
dependência serial explícita quando representarem uma correção; sem essa
relação, o validador de contrato deve rejeitá-los.

O plano técnico explica o que e por quê; o plano de execução explica quem pode
alterar quais arquivos, em que ordem e com qual evidência. Planner pode escrever
somente `specs/<slug>/spec.md`, `plan.md`, `status.md`, `work-packages.json` e
`delegation-evidence.json`; não escreve `evidence.md`, `verification.json`,
`task-window.json`, código ou testes. Architect pode escrever somente
`docs/architecture/decisions/ADR-*.md`. Achados do Verifier,
Reviewer ou Documentation Reviewer retornam como novo WP de correção para a
role adequada; o mesmo vale para blocker ou critério falho do Test Engineer.
Depois da correção, o fluxo retorna ao Implementer e repete Test Engineer,
Verifier e os revisores aplicáveis. Não
adicione uma nova role de planejamento e não atribua execução de código,
testes, build ou validação final ao Orchestrator.
