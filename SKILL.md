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

Keep validation ownership explicit. The `implementer` may run only quick, focused checks while editing (for example, the directly affected unit test, lint, or type-check) to catch local mistakes. The `tester` owns independent final validation: acceptance criteria, regressions, edge cases, broader or slow suites, and test evidence. Do not treat the implementer's checks or report as a substitute for the tester; when a tester is required, wait for its independent result before declaring validation complete.

When the tester or reviewer reports a blocker, failed criterion, or required correction, do not complete the work and do not ask the read-only agent to fix it. Return to Implementation and assign a focused correction to an available `implementer`; if none is available, spawn a new one with explicit write scope. The principal agent orchestrates and integrates the correction, editing directly only as a documented fallback when no subagent is available or the change is genuinely trivial. After every correction, rerun the tester and reviewer independently before resuming Completion. If the finding changes the specification, architecture, or plan, return to the corresponding earlier lifecycle phase first.

Always set the subagent creation timeout to the maximum value accepted by the runtime. If the spawn API does not expose a creation-time timeout, use the maximum wait timeout on every wait (`multi_agent_v1__wait_agent` currently allows `timeout_ms: 3600000`). A wait timeout is not a completion signal: do not close or interrupt an agent that is still `pending_init` or `running`; continue waiting with the maximum timeout until it reaches a terminal status, unless the user explicitly requests cancellation.

## Model routing

For multi-agent work, read `references/model-routing.md` before spawning agents. Query the current runtime for available model and reasoning-effort pairs, then call `scripts/model_routing.py` with that availability and the selected role. The user-global mapping lives at `~/.codex/aisdd/model-routing.toml`; use `assets/templates/model-routing.toml` as the default when it does not exist. The script only reports recommendations and never creates or changes the global mapping.

If a configured model is unavailable, spawn without a model or effort override so the subagent inherits the current chat configuration. State that fallback, list the available choices and the tier-based suggestions, then ask whether the user wants to update any roles or efforts. Change the global mapping only after explicit confirmation. Never claim that static configuration proves a model is available.

For T2+, record every delegated agent in `evidence.md`: role, agent identifier, task, requested model and effort, effective model and effort when the runtime exposes them, fallback, and result. After the child completes, run `scripts/agent_evidence.py` against its local rollout, using its agent identifier or a uniquely scoped legacy selector, and record all returned token categories and cost estimate in the agent table whenever telemetry is complete. Treat its last readable `turn_context` as the best local evidence for the observed effective settings and record its source; it is not proof of every backend inference in a multi-turn agent. The script reports input, cache, cache-write, output, reasoning-output, and a token-only API-equivalent estimate. When `last_token_usage` snapshots are complete, it prices each model request independently and reconciles their sum against the final `total_token_usage`; it deduplicates identical terminal pairs, preserves safe per-request snapshots, and never sums cumulative snapshots. It reads `~/.codex/aisdd/cost-pricing.toml`, or `assets/templates/cost-pricing.toml` when the user table is absent. Each model must declare `long_context_pricing = "standard"` or `"tiered"`; tiered pricing is evaluated per request. It excludes tool/modality fees and subscription billing. When request-level telemetry is unavailable for a tiered model, the compatibility fallback is flagged as potentially imprecise; use `--respect-long-context` to refuse it or `--ignore-long-context` to opt into it. Present but malformed telemetry is never treated as absent. If any other telemetry or the model price/policy is unavailable, record that limitation rather than estimating. Count the agents and token-only estimates in a summary.

For T2+ delegated work, add a `Custo total da tarefa` section to `evidence.md`: sum only the estimated `total_usd` values from agent rollouts belonging to the current task, record the number of costed agents, currency/basis, and exclusions; do not include the main conversation or unrelated validation rollouts, and record `not available` when no complete estimates exist.

When the task includes main-chat attribution, create `specs/<slug>/task-window.json` with `scripts/task_window.py start`, close it after the task's `task_complete` or `turn_aborted` event with `scripts/task_window.py close --end-turn-id <start-turn-id>`, and generate the report with `scripts/task_window.py report`. Pass `--sessions-root` when the rollout root is not the default. The sidecar stores the main session ID, rollout filename and runtime turn boundaries, without an absolute local path; it must not write marker messages or mutate the runtime-owned rollout. Only a closed window is final evidence; an open window is provisional. Keep the main-chat estimate separate from the delegated-agent total until both are available, then record the combined task total in `evidence.md`.

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
