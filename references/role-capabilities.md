# Matriz de roles e capabilities

Capabilities são responsabilidades do contrato, independentes de modelo e
effort. O roteamento escolhe um modelo; ele nunca cria uma capability nem
substitui uma role ausente.

| Role | Pode executar | Deve produzir | Não pode executar em nome de outra role |
|---|---|---|---|
| `orchestrator` | inspeção, coordenação, delegação, acompanhamento de dependências, consolidação de resultados e registro de evidências | estado do fluxo, decisões e evidências | implementação, alteração de testes, build, correção de código ou validação final |
| `planner` | análise, plano técnico e plano de execução | Work Packages, owners, dependências, critérios, escopos e paralelização | código, testes, build ou validação final |
| `architect` | desenho de interfaces, invariantes e ADRs | decisões arquiteturais e riscos | implementação ou testes de produto |
| `implementer` | implementação e correção no escopo do WP | código alterado e resultado de checks focados | criar/alterar testes, validação final ou revisão independente |
| `test-engineer` | desenho, criação e alteração de testes | testes anotados e cobertura de critérios | declarar validação final sem Verifier |
| `verifier` | execução de testes, build e validação final | resultado independente e blockers | alterar código ou testes |
| `reviewer` | revisão independente de contrato, segurança, regressões e lacunas | achados com severidade e localização | corrigir diretamente o próprio achado |
| `documentation-reviewer` | revisão de docs, templates, spec, plano e ADR | drift documental e correções sugeridas | alterar código ou mascarar drift |

## Capabilities protegidas

As capabilities `implement`, `write-tests`, `build`, `verify-final` e
`review` são protegidas no contrato v2. Um WP precisa apontar para uma role que
as possua na tabela acima. `orchestrator` tem `coordinate`, não essas
capabilities protegidas.

## Cobertura por classe

- T0 fica fora do contrato somente quando é comprovadamente mecânico e não
  delegável. Em v2, a evidência deve declarar
  `mechanical_non_delegable: {approved: true, reason: "..."}` ou observar uma
  role especializada; `orchestrator`/`coordinate` nunca é cobertura de trabalho
  delegável.
- T1 exige Planner, Implementer, Test Engineer e Verifier.
- T2 exige as quatro roles de T1 e Reviewer. Documentation Reviewer é
  obrigatório somente quando houver impacto documental; sem esse impacto, não
  é requisito adicional.
- T3 e T4 exigem Planner, Architect, Implementer, Test Engineer, Verifier,
  Reviewer e Documentation Reviewer. T4 também exige aprovação humana antes de
  qualquer etapa irreversível.
- Planner continua responsável pelo plano e Architect é usado conforme a
  classe e o impacto; nenhuma delas é convertida em uma nova role de execução.

`tester` é somente o alias histórico de `test-engineer`. No v2, uma evidência
com `tester` pode cobrir Test Engineer depois da normalização, mas nunca Verifier
e nunca as duas roles simultaneamente.

Impacto documental inclui alterações em documentação operacional, README,
SKILL, references, ADR, templates, AGENTS, instruções de agentes ou nos
artefatos de feature. Em T2, o Planner/Orchestrator declara o impacto no
`plan.md` e requer manualmente Documentation Reviewer após o Verifier; o
validador v2 não infere essa role condicional. Em T3/T4, a role entra sempre
por classe.

Em v2, `implementer`, `test-engineer`, `verifier`, `reviewer` e
`documentation-reviewer` exigem `agent_id` distintos entre si quando
observados na mesma execução; em particular, Test Engineer e Verifier nunca
podem compartilhar identidade.
