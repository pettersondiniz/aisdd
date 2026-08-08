# AISDD repository guidance

## Mandatory AISDD triage

Before changing code, configuration, infrastructure, database schema, tests, or technical documentation, classify the request as T0–T4 using `$aisdd`.

- T0: keep the work outside the contract only when it is demonstrably
  mechanical and non-delegable; otherwise assign the appropriate role and run
  the smallest relevant check.
- T1+: use `$aisdd` and follow the proportional artifacts and validation.
- T2+: use the subagents required by `references/agent-routing.md`. If the runtime cannot provide them, record that limitation in `evidence.md`.
- When AISDD does not apply, state `AISDD: not applicable — <reason>` before proceeding.
- When in doubt, use the higher class; never lower the class to avoid planning, testing, review, or subagents.

- Locate or create the feature artifacts under `specs/`.
- Do not implement behavior that contradicts the approved specification.
- Keep `plan.md` and `status.md` current.
- Add tests and record real validation in `evidence.md`.
- Update affected documentation and ADRs.
- Use specialized subagents for independent planning, testing, review, and documentation checks when available.

## Delegação obrigatória

A partir de T1, trabalho delegável precisa de owner e role especializada. O
T0 só fica fora do contrato quando for comprovadamente mecânico e não
delegável; em v2, registre `mechanical_non_delegable.approved: true` com
justificativa auditável ou uma role especializada. `orchestrator/coordinate`
não cobre trabalho delegável e o Orchestrator também não o executa diretamente.
O
Orchestrator coordena e consolida, mas não implementa código, escreve ou altera
testes, executa build, corrige achados ou faz validação final. Use
`implementer`, `test-engineer`, `verifier`, `reviewer` e `documentation-reviewer`
conforme o contrato; o
`implementer` não cria nem altera testes; Test Engineer é o owner dos testes.
`tester` é apenas alias v1 de `test-engineer`. Em v2, registre WPs, escopo e
fallback auditável e gere um novo WP para blockers, critérios falhos ou
correções de Test Engineer, Verifier, Reviewer ou Documentation Reviewer. O
fluxo retorna ao Implementer e repete Test Engineer, Verifier e os revisores
aplicáveis. Se uma role/agente estiver
indisponível, marque `BLOCKED` e peça decisão humana; edição direta só após
aprovação explícita com motivo, tentativas, escopo e resultado. Não invente
executor externo nem capability para uma role ausente.

## Commands

Replace this section with the repository's real install, lint, test, typecheck, build, migration, and deploy commands.
