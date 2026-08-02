# AISDD repository guidance

## Mandatory AISDD triage

Before changing code, configuration, infrastructure, database schema, tests, or technical documentation, classify the request as T0–T4 using `$aisdd`.

- T0: make the mechanical change and run the smallest relevant check.
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

## Commands

Replace this section with the repository's real install, lint, test, typecheck, build, migration, and deploy commands.
