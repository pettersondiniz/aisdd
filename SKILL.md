---
name: aisdd
description: Use for non-trivial software features, bug fixes, refactors, migrations, and architectural changes. AISDD classifies T0-T4 risk, maintains specs and ExecPlans, routes Codex subagents, validates evidence, reviews changes, checks documentation drift, and updates repository guidance.
---

# AISDD

AISDD is a repository-centered workflow for specification-driven, agent-assisted delivery. The repository is the source of truth; this skill is the reusable process.

## Route the request

1. Inspect the repository, existing `AGENTS.md`, `docs/`, `specs/`, code, tests, and available commands before editing.
2. Detect whether the request changes a user-facing interface. If it does, check whether `impeccable` is installed; when absent, propose its installation before design work, but never install it without explicit user authorization. When present, route its use according to `references/agent-routing.md`. Assess browser-validation capabilities using `references/interface-validation.md`; Playwright is preferred when available, never required.
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

## Model routing

For multi-agent work, read `references/model-routing.md` before spawning agents. Query the current runtime for available model and reasoning-effort pairs, then call `scripts/model_routing.py` with that availability and the selected role. The user-global mapping lives at `~/.codex/aisdd/model-routing.toml`; use `assets/templates/model-routing.toml` as the default when it does not exist. The script only reports recommendations and never creates or changes the global mapping.

If a configured model is unavailable, spawn without a model or effort override so the subagent inherits the current chat configuration. State that fallback, list the available choices and the tier-based suggestions, then ask whether the user wants to update any roles or efforts. Change the global mapping only after explicit confirmation. Never claim that static configuration proves a model is available.

For T2+, record every delegated agent in `evidence.md`: role, agent identifier, task, requested model and effort, effective model and effort when the runtime exposes them, fallback, and result. After the child completes, run `scripts/agent_evidence.py` against its local rollout, using its agent identifier or a uniquely scoped legacy selector, and record all returned token categories and cost estimate in the agent table whenever telemetry is complete. Treat its last readable `turn_context` as the best local evidence for the observed effective settings and record its source; it is not proof of every backend inference in a multi-turn agent. The script reports input, cache, cache-write, output, reasoning-output, and a token-only API-equivalent estimate. It reads `~/.codex/aisdd/cost-pricing.toml`, or `assets/templates/cost-pricing.toml` when the user table is absent. It excludes tool/modality fees and subscription billing. Context-long pricing is ignored by default and the returned estimate is flagged as potentially imprecise; use `--respect-long-context` to refuse such estimates when request-level telemetry is unavailable. If any other telemetry or the model price is unavailable, record that limitation rather than estimating. Count the agents and token-only estimates in a summary.

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

## Interface validation

For a user-facing change, prefer validation in a real browser. First detect available capabilities. Prefer `playwright-cli` for repeatable browser flows and evidence; use Playwright MCP for interactive inspection, browser-session state, or live debugging when it is available to the runtime. Do not require both tools for the same scenario. If neither is available, use the strongest available project-native or approved browser validation, record the limitation, and never claim real-browser proof that was not obtained. Recommend enabling Playwright tooling for interface work, but never install it without explicit user authorization. Read `references/interface-validation.md` before planning or judging interface evidence.

For UI-affecting features, record in `evidence.md` whether Impeccable was used. When used, record role, action and purpose; when not used, record the reason. Its use and installation remain optional and never block completion.

## Baseline conformance

Offer `baseline-conformance` only for projects that began without AISDD. Run it only on explicit user request and follow `references/baseline-conformance.md`. It may create documentation and follow-up specs but must never alter product code, tests, dependencies, runtime configuration, infrastructure, database, or CI.

## Scripts

Run from the skill directory or pass `--skill-dir` when needed:

```text
python scripts/init_project.py <repo>
python scripts/create_feature.py <repo> "Feature name" --class T2
python scripts/verify_feature.py <repo> specs/<slug> -- <real-test-command>
python scripts/validate_feature.py <repo> specs/<slug>
python scripts/check_drift.py <repo>
python scripts/model_routing.py --role reviewer --class T2 --availability-json available-models.json
python scripts/agent_evidence.py --agent-id /root/reviewer --json
python scripts/agent_evidence.py --rollout-id <id-do-rollout> --json
python scripts/agent_evidence.py --agent-id /root/reviewer --pricing-config <tabela-de-precos.toml> --json
python scripts/agent_evidence.py --agent-id /root/reviewer --respect-long-context --json
python scripts/baseline_conformance.py <repo> --baseline-id <id>
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
- `references/interface-validation.md` — browser-validation capability selection and evidence.
