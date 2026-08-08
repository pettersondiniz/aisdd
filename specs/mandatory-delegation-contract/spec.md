# Contrato obrigatório de delegação AISDD

## Objetivo

Endurecer a arquitetura de delegação da AISDD para que o Orchestrator coordene a execução, mas não implemente código, escreva testes, corrija bugs, execute builds ou faça a validação final de tarefas delegáveis.

## Contexto

O contrato atual recomenda o uso de agentes especializados, mas permite edição direta pelo agente principal como fallback amplo. O Planner também produz principalmente um plano técnico, enquanto a execução, o ownership, as capabilities e a cobertura de roles não são validados mecanicamente.

Esta mudança adiciona o contrato v2 para Work Packages, evidências de delegação,
capabilities, fallbacks e roteamento sensível à classe. Novas specs usam v2 por
padrão no scaffolding; o contrato v1 é compatibilidade para specs
existentes/legadas e para esta própria feature, que permanece v1 por decisão
explícita. Não há migração automática.

## Comportamento esperado

- A partir de T1, toda tarefa delegável tem owner explícito e role especializada.
- O Orchestrator pode inspecionar, coordenar, delegar, acompanhar dependências, consolidar resultados e registrar evidências.
- O Orchestrator não implementa código, altera testes, executa build/testes ou corrige achados, inclusive em tarefas T0 que contenham trabalho delegável.
- Em T1+ v1, o Planner produz plano técnico, plano de execução e grafo declarativo nos artefatos v1; somente features marcadas v2 exigem Work Packages e evidência JSON, com owners, dependências, critérios, escopos e condições de paralelização.
- Em v2, cada WP exige a chave `role` explícita e conhecida; `owner.role`, quando presente, é apenas informação auxiliar e nunca é inferida para preencher `role`.
- Test Engineer produz ou altera testes; Verifier executa a validação final e não altera código nem testes.
- Um blocker, critério falho ou correção exigida pelo Test Engineer, Verifier, Reviewer ou Documentation Reviewer retorna ao Orchestrator e gera um novo WP de correção para a role adequada; o fluxo volta ao Implementer e repete Test Engineer, Verifier e os revisores aplicáveis.
- Após o Verifier, Reviewer e Documentation Reviewer podem revisar em paralelo quando seus escopos forem independentes; nenhum começa antes do Verifier.
- Em T2, Documentation Reviewer é obrigatório quando houver impacto documental e não é exigido para T2 sem esse impacto; em T3/T4, é obrigatório por classe.
- Cada entrada de delegação v2 exige `fallback` como objeto explícito com `used` booleano; ausência falha, `used: false` permanece limpo e campos incompatíveis são rejeitados.
- Fallback pode ser usado somente com motivo, agente indisponível, tentativas e trabalho direto registrados.
- Após a normalização, cada test-engineer depende transitivamente de implementer quando houver implementer, cada verifier depende de test-engineer quando houver test-engineer e cada reviewer/documentation-reviewer depende de verifier quando houver verifier; Planner e Architect podem permanecer em paralelo e WPs corretivos de Implementer continuam válidos com dependência serial.
- Conflitos de escopo com glob são avaliados de forma conservadora: prefixos potencialmente sobrepostos podem conflitar para evitar falso negativo.
- Em T0 v2, a evidência de conclusão exige `mechanical_non_delegable.approved: true` com justificativa auditável ou uma role especializada; `orchestrator/coordinate` não satisfaz cobertura de trabalho delegável.
- O contrato v1 continua válido sem `work-packages.json` ou `delegation-evidence.json`.
- O scaffolding novo grava o marcador v2 e cria esses artefatos; ausência de
  marcador ou v1 explícito mantém a compatibilidade v1.
- O contrato v2 exige esses artefatos somente quando o marcador v2 está presente
  na feature; a regra v2 permanece estrita.

## Regras e invariantes

- A matriz de capabilities é independente do modelo e do effort.
- `tester` permanece alias de compatibilidade v1 para `test-engineer`; não satisfaz simultaneamente Test Engineer e Verifier no contrato v2.
- A conclusão falha fechada quando há owner ausente, WP inválido, role obrigatória ausente, evidência obsoleta, fallback não auditado ou blocker aberto.
- `plan.md` é a fonte normativa do grafo declarativo v1 e a projeção humana do plano; `evidence.md` apenas resume owners/dependências e registra provas. No v2, o grafo usa dependências declaradas e determinísticas.
- A resolução de modelo sem classe preserva o comportamento v1; `--class` aplica o perfil por role e classe apenas quando fornecido.
- Nenhuma consulta ou fallback altera a configuração global, sessões do runtime ou o projeto fora do escopo local.

## Casos de borda e falhas

- Grafo com ciclo, dependência inexistente, ID duplicado ou escopo de escrita conflitante é rejeitado antes da execução.
- Padrões wildcard ambíguos ou com prefixo potencialmente sobreposto são rejeitados de forma fail-closed.
- Runtime ou capability não observados não são inferidos por nickname, resposta do agente ou modelo.
- Falha repetida sem progresso termina em `BLOCKED` ou exige decisão humana; não há loop infinito.
- Spec legada sem marcador, ou explicitamente v1, é tratada como compatibilidade
  v1 e não é regravada/migrada automaticamente.
- `has_open_status` ignora somente seções históricas claramente marcadas, reconhece estados estruturados atuais e não trata frases comuns como “specs pendentes” como estado aberto; assumptions/questions abertas continuam sendo detectadas.

## Fora de escopo

- Integração com uma API externa de spawn/execução que não existe neste repositório.
- Alteração da instalação global em `C:\Users\Usuario\.agents\skills\aisdd`.
- Migração automática das specs existentes.
- Escrita automática em `~/.codex/aisdd/model-routing.toml` ou nos rollouts do runtime.

## Critérios de aceitação

- [x] AC-701: A skill e o roteamento definem delegação obrigatória para trabalho delegável a partir de T1 e proíbem execução direta do Orchestrator nas capabilities de implementação, testes, build e validação.
- [x] AC-702: O Planner é instruído a produzir plano técnico e plano de execução com grafo declarativo de tarefas/WPs, owners, dependências, critérios e paralelização; novas specs usam v2 por padrão, enquanto T1+ legado/explicitamente v1 não cria nem exige JSON v2; no v2, cada WP declara escopo permitido/proibido.
- [x] AC-703: A matriz de capabilities e a separação entre Implementer, Test Engineer, Verifier, Reviewer e Orchestrator estão documentadas e refletidas nos agentes.
- [x] AC-704: O validador v2 rejeita Work Packages com ciclo, dependência inexistente, ID duplicado, role ausente/desconhecida, dependências mínimas de execução ausentes ou conflito de escopo (inclusive glob conservador) e produz ordem topológica determinística.
- [x] AC-705: O scaffolding de novas specs usa v2 por padrão; a validação aceita specs legadas sem marcador e specs explicitamente v1 sem exigir artefatos v2, e aplica regras v2 estritas somente com marcador v2 válido, sem migração automática.
- [x] AC-706: A evidência v2 valida cobertura de roles, independência entre Test Engineer e Verifier, fallback obrigatório como objeto com `used` booleano e os campos de fallback usado.
- [x] AC-707: O roteador aplica perfil sensível à classe quando `--class` é informado e preserva o roteamento legado quando ele é omitido.
- [x] AC-708: Roles canônicas novas e alias legado são resolvidos sem transformar uma role ausente em capability disponível silenciosamente.
- [x] AC-709: O contrato documenta o loop Implementer/Test Engineer/Verifier/(Reviewer || Documentation Reviewer), correções auditáveis e encerramento fail-closed sem execução direta do Orchestrator.
- [x] AC-710: A implementação local não altera configuração global, sessões do runtime ou arquivos fora de `D:\codex\aisdd`.
- [x] AC-711: A decisão arquitetural e a estratégia de migração v1/v2 estão registradas em ADR e nos templates/documentação da skill.

Cada critério deve ser observável e indicar o comportamento que um teste anotado com `@spec:AC-xxx` comprovará.

## Suposições

| ID | Suposição | Status | Dono/validação |
|---|---|---|---|
| ASM-701 | O runtime externo pode não expor uma API de spawn neste repositório. | Validada | Architect/Planner |
| ASM-702 | A ausência ou declaração v1 de marcador identifica compatibilidade v1; novas specs recebem marcador v2 pelo scaffolding. | Validada | ADR, scaffolding e validador |

## Perguntas abertas

| ID | Pergunta | Status | Decisão/resposta |
|---|---|---|---|
| Q-701 | Qual API externa executará o grafo? | Resolvida | Fora do escopo; esta entrega valida e documenta o grafo, sem inventar executor. |

## Decisões resolvidas

- O Planner atual permanece como owner do plano técnico e do plano de execução.
- Não serão criadas versões `planner-light`, `planner-standard` ou `planner-robust`; modelo/effort variam por classe, capabilities não.
- A própria feature permanece v1 por decisão explícita; novas specs são criadas
  em v2 por padrão, e ausência/v1 explícito permanece compatibilidade sem
  migração automática.
