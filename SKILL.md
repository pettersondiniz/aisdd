---
name: aisdd
description: Use for non-trivial software features, bug fixes, refactors, migrations, and architectural changes. AISDD classifies T0-T4 risk, maintains specs and ExecPlans, routes Codex subagents, validates evidence, reviews changes, checks documentation drift, and updates repository guidance.
---

# AISDD

AISDD is a repository-centered workflow for specification-driven, agent-assisted delivery. The repository is the source of truth; this skill is the reusable process.

## Route the request

1. Inspect the repository, existing `AGENTS.md`, `docs/`, `specs/`, code, tests, and available commands before editing.
2. Detect whether the request changes a user-facing interface. If it does, check whether `impeccable` is installed; when absent, propose its installation before design work, but never install it without explicit user authorization. When present, route its use according to `references/agent-routing.md`.
3. Classify the change using `references/classification.md`. Use the highest applicable class.
4. For T0, make the mechanical change and run the smallest relevant check.
5. For T1, create or update a lightweight feature folder and plan.
6. For T2, require `spec.md`, `plan.md`, `status.md`, tests, review, and evidence.
7. For T3, also require architectural design and an ADR when a decision is introduced.
8. For T4, require rollout, rollback, observability, and explicit user approval before irreversible actions.

Read the relevant reference before creating or judging an artifact. Use the templates under `assets/templates/`; adapt them to the repository instead of copying empty sections that do not apply.

## Lifecycle

Follow `references/lifecycle.md`: discovery → specification → design → planning → implementation → validation → review → documentation → completion. Resume from the first incomplete phase; do not recreate existing artifacts without reading them.

## Multi-agent routing

Use the custom agents in `agents/` when the Codex runtime supports subagents. Agent files are project-scoped when copied to `.codex/agents/` or globally available when copied to `~/.codex/agents/`.

- `planner`: clarify scope, dependencies, sequencing, and risks; read-only.
- `architect`: define interfaces, data flow, invariants, and ADR candidates; read-only.
- `implementer`: execute one approved plan milestone at a time.
- `tester`: design and run focused validation; do not silently weaken tests.
- `reviewer`: independently inspect the diff against the spec, security, regressions, and test gaps; read-only.
- `documentation-reviewer`: inspect docs/spec/ADR consistency and drift; read-only.

Select agents according to `references/agent-routing.md`. Prefer parallel read-only work. Serialize write-heavy implementation and documentation work. State what each agent must return, wait for all required agents, and combine concise findings.

## Required artifacts

For a feature folder `specs/<slug>/`, keep:

- `spec.md`: behavior, constraints, acceptance criteria, and out of scope.
- `plan.md`: executable milestones with files, commands, dependencies, and rollback notes.
- `status.md`: current phase, completed work, blockers, and next action.
- `evidence.md`: commands, results, and acceptance-criteria traceability.
- `verification.json`: generated proof that the current annotated tests passed for each acceptance criterion.

Use `docs/architecture/decisions/ADR-*.md` for durable architectural decisions. Keep `AGENTS.md` short and repository-specific.

## Completion gate

Do not claim completion until `references/completion-standard.md` is satisfied. For a feature, run its real test command through `scripts/verify_feature.py`, then run `scripts/validate_feature.py`; run `scripts/check_drift.py` for the repository when applicable. Report skipped checks honestly. A passing test command without an `@spec:AC-xxx` mapping is not proof for an acceptance criterion.

## Scripts

Run from the skill directory or pass `--skill-dir` when needed:

```text
python scripts/init_project.py <repo>
python scripts/create_feature.py <repo> "Feature name" --class T2
python scripts/verify_feature.py <repo> specs/<slug> -- <real-test-command>
python scripts/validate_feature.py <repo> specs/<slug>
python scripts/check_drift.py <repo>
```

These scripts are deterministic scaffolding and checks, not substitutes for reading the code or exercising the application.

## References

- `references/lifecycle.md` — phase transitions and resume rules.
- `references/classification.md` — T0–T4 decision table.
- `references/specification-standard.md` — requirements and acceptance criteria.
- `references/exec-plan-standard.md` — living executable plans.
- `references/completion-standard.md` — evidence and completion gate.
- `references/review-standard.md` — independent review rubric.
- `references/documentation-policy.md` — what to update and when.
- `references/agent-routing.md` — agent selection and concurrency rules.
