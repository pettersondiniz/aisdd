---
name: aisdd
description: Use for non-trivial software features, bug fixes, refactors, migrations, and architectural changes. AISDD classifies T0-T4 risk, maintains specs and ExecPlans, routes Codex subagents, validates evidence, reviews changes, checks documentation drift, and updates repository guidance.
---

# AISDD

## Mandatory delegation contract

From T1 onward, delegable work has an explicit owner and specialized role. The
Orchestrator may inspect, coordinate, delegate, track dependencies, consolidate
results, and record evidence, but it must not implement code, write or alter
tests, run builds, fix findings, or perform final validation. Read
`references/delegation-contract.md` and `references/role-capabilities.md` for
the v1/v2 boundary and the capability matrix.

Delegation is mandatory for every delegable task from T1 onward, and for any
delegable work identified inside T0. A T0 task is outside this contract only
when it is demonstrably mechanical and non-delegable; when T0 is delegable, the
Orchestrator must not execute it directly. If the required role or agent is
unavailable, stop that work as `BLOCKED` and request a human decision; do not
silently substitute the Orchestrator. Direct execution is allowed only as an
explicitly approved fallback and must be audited with the reason, observed
agent unavailability, attempts, allowed scope and result. It must never be
justified by triviality or silence.

New specs use the v2 contract by default: `scripts/create_feature.py` writes
the canonical v2 marker and the two v2 JSON skeletons. The v1 contract is a
compatibility mode for existing/legacy specs and for features explicitly
created with `--contract v1`; absence of a marker or an explicit v1 declaration
remains valid v1 and does not require the JSON artifacts. There is no automatic
migration. The validator applies v2 only when the canonical marker
`Contrato AISDD da feature: v2`, or one of the documented technical aliases
below, occupies its own line.
The version must be a terminal token `v2` or `2`; only trailing whitespace and
the documented optional Markdown list prefix are allowed. Suffixes or trailing
text such as `v2 extra`, `v2.0`, punctuation, or prose are rejected and leave
the feature in v1 compatibility mode. Matching is case-insensitive and accepts `:` or
`=`. The detector also accepts the technical aliases `Contrato AISDD: v2`,
`AISDD contract: v2`, `AISDD-contract: v2`, `AISDD_contract: v2`,
`delegation contract: v2`, `delegation-contract: v2`, `delegation_contract: v2`,
`contract: v2`, `contract-version: v2`, and `contract_version: v2`.
Only visible lines are considered: markers inside Markdown fenced blocks are
ignored. Only for a v2 marker are `work-packages.json` and
`delegation-evidence.json` required.
Prefer the canonical marker. `tester` remains a v1 CLI/spec alias for
`test-engineer`, but never substitutes for `verifier` in v2. No external spawn
executor is assumed or invented.

For T1+ legacy or explicitly v1 features, the Planner records the technical plan, the
execution plan, and a declarative task/dependency graph in `plan.md`, which is
the normative graph source. `evidence.md` only summarizes owners/dependencies
and records proof; it does not redefine the graph. The Planner does not create
or require the v2 JSON files. A v2 marker is the only trigger for enforcing
`work-packages.json` and `delegation-evidence.json`, including for manually
created or migrated specs.

AISDD is a repository-centered workflow for specification-driven, agent-assisted delivery. The repository is the source of truth; this skill is the reusable process.

## Route the request

1. Inspect the repository, existing `AGENTS.md`, `docs/`, `specs/`, code, tests, and available commands before editing.
2. Detect whether the request changes a user-facing interface. If it does, check whether `impeccable` is installed; when absent, propose its installation before design work, but never install it without explicit user authorization. When present, route its use according to `references/agent-routing.md`. Assess browser-validation capabilities using `references/interface-validation.md`; Playwright is preferred when available, never required.
3. Classify the change using `references/classification.md`. Use the highest applicable class.
4. For T0, confirm whether the work is truly mechanical and non-delegable. Only
   that narrow case may remain outside the contract; otherwise assign it to the
   appropriate role and run the smallest relevant check. In v2 evidence, a T0
   completion requires approved `mechanical_non_delegable` evidence or a
   specialized role; `orchestrator/coordinate` is never coverage for delegable
   work.
5. For T1, create or update a lightweight feature folder and plan.
6. For T2, require `spec.md`, `plan.md`, `status.md`, tests, review, and evidence.
7. For T3, also require architectural design and an ADR when a decision is introduced.
8. For T4, require rollout, rollback, observability, and explicit user approval before irreversible actions.

The Documentation Reviewer gate is conditional in T2: the Planner/Orchestrator
declares documentary impact in `plan.md` and manually requires the gate when
that impact exists; it is not inferred or added by the v2 validator. Do not add
the role to a T2 with no declared impact. T3 and T4 require Documentation
Reviewer by class. Documentary impact includes changes to normative or
operational documentation, feature artifacts, ADRs, templates, AGENTS.md, or
agent instructions.

Read the relevant reference before creating or judging an artifact. Use the templates under `assets/templates/`; adapt them to the repository instead of copying empty sections that do not apply.

## Lifecycle

Follow `references/lifecycle.md`: discovery → specification → design → planning → implementation → validation → review → documentation → completion. Resume from the first incomplete phase; do not recreate existing artifacts without reading them.

## Multi-agent routing

Use the custom agents in `agents/` when the Codex runtime supports subagents. Agent files are project-scoped when copied to `.codex/agents/` or globally available when copied to `~/.codex/agents/`.

- `planner`: clarify scope, dependencies, sequencing, and risks; read-only.
- `architect`: define interfaces, data flow, invariants, and ADR candidates; read-only.
- `implementer`: execute one approved plan milestone at a time; do not create or
  alter tests.
- `test-engineer`: create or alter tests; do not claim final validation.
- `verifier`: run independent final validation; do not alter code or tests.
- `tester`: v1 compatibility alias for `test-engineer` only.
- `reviewer`: independently inspect the diff against the spec, security, regressions, and test gaps; read-only.
- `documentation-reviewer`: inspect docs/spec/ADR consistency and drift; read-only.

Select agents according to `references/agent-routing.md`. Prefer parallel
read-only work only after its dependencies are satisfied. For T3/T4, run
Reviewer and Documentation Reviewer in parallel after Verifier; a serial
dependency or overlapping scope still takes precedence. State what each agent
must return, wait for all required agents, and combine concise findings.

Keep validation ownership explicit. The `implementer` may run only quick,
focused non-authoritative checks while editing (for example, lint or type-check)
to catch local mistakes; it does not create or alter tests. The `test-engineer`
owns test creation, alteration and coverage; the `verifier` owns independent final validation,
regressions, edge cases, broader or slow suites, and final test evidence. Do
not treat implementer or test-engineer reports as final proof. In v1, `tester`
keeps its historical alias; in v2, wait for the distinct `verifier` role before
declaring validation complete.

When the `test-engineer`, `verifier`, `reviewer`, or `documentation-reviewer`
reports a blocker, failed criterion, or required correction, do not complete
the work and do not ask the read-only agent to fix it. Open a new corrective WP,
return to Implementation, and assign the focused correction to an available
`implementer`; if none is available, mark the WP `BLOCKED` and request a human
decision. The principal agent may edit directly only after an explicit
human-approved fallback decision; record the reason, unavailable agent,
attempts, scope and result in the evidence. Never use triviality or silence as
a fallback reason. After each correction, rerun Test Engineer when the test
scope or criterion is affected (including a Test Engineer finding), then
Verifier; after Verifier, rerun Reviewer and Documentation Reviewer when their
scopes apply. If the finding changes the specification, architecture, or plan,
return to the corresponding earlier lifecycle phase first.

Always set the subagent creation timeout to the maximum value accepted by the runtime. If the spawn API does not expose a creation-time timeout, use the maximum wait timeout on every wait (`multi_agent_v1__wait_agent` currently allows `timeout_ms: 3600000`). A wait timeout is not a completion signal: do not close or interrupt an agent that is still `pending_init` or `running`; continue waiting with the maximum timeout until it reaches a terminal status, unless the user explicitly requests cancellation.

## Model routing

Before spawning, validate the actual model/effort request with the strict guard:

```text
python scripts/model_routing.py --role <role> --class <class> --availability-json available-models.json --requested-model <model> --requested-effort <effort> --require-available --json
```

When the configured route is available, a different pair is rejected unless an
explicit override and a non-trivial audit reason are supplied. When availability
is missing or the configured route is unavailable, omit model and effort from
the spawn so the child inherits the current chat configuration. `inherit` is a
fallback decision, not proof of a capability.

For multi-agent work, read `references/model-routing.md` before spawning agents. Query the current runtime for available model and reasoning-effort pairs, then call `scripts/model_routing.py` with that availability and the selected role. The user-global mapping lives at `~/.codex/aisdd/model-routing.toml`; use `assets/templates/model-routing.toml` as the default when it does not exist. The script only reports recommendations and never creates or changes the global mapping.

If a configured model is unavailable, spawn without a model or effort override so the subagent inherits the current chat configuration. If the role itself is not configured, mark the work `BLOCKED` and request a human decision; `inherit` does not provide a capability. State any model fallback, list the available choices and the tier-based suggestions, then ask whether the user wants to update any roles or efforts. Change the global mapping only after explicit confirmation. Never claim that static configuration proves a model is available.

For T2+, record every delegated agent in `evidence.md`: role, agent identifier, task, requested model and effort, effective model and effort when the runtime exposes them, fallback, and result. After the child completes, run `scripts/agent_evidence.py` against its local rollout, using its agent identifier or a uniquely scoped legacy selector, and record all returned token categories and cost estimate in the agent table whenever telemetry is complete. Treat its last readable `turn_context` as the best local evidence for the observed effective settings and record its source; it is not proof of every backend inference in a multi-turn agent. The script reports input, cache, cache-write, output, reasoning-output, and a token-only API-equivalent estimate. When `last_token_usage` snapshots are complete, it prices each model request independently and reconciles their sum against the final `total_token_usage`; it deduplicates identical terminal pairs, preserves safe per-request snapshots, and never sums cumulative snapshots. It reads `~/.codex/aisdd/cost-pricing.toml`, or `assets/templates/cost-pricing.toml` when the user table is absent. Each model must declare `long_context_pricing = "standard"` or `"tiered"`; tiered pricing is evaluated per request. It excludes tool/modality fees and subscription billing. When request-level telemetry is unavailable for a tiered model, the compatibility fallback is flagged as potentially imprecise; use `--respect-long-context` to refuse it or `--ignore-long-context` to opt into it. Present but malformed telemetry is never treated as absent. If any other telemetry or the model price/policy is unavailable, record that limitation rather than estimating. Count the agents and token-only estimates in a summary.

When `--agent-id` does not match `agent_path`, its only correlation fallback is an exact, complete UUID that appears uniquely in one rollout filename. The fallback is allowed only after direct matching fails, the resolved path remains inside `--sessions-root`, and all other readable metadata agrees with the selectors. Partial UUIDs, ambiguous filenames, inconsistent metadata and unsafe paths fail closed without invented evidence. A successful fallback must expose `resolution.fallback_used: true` in JSON and the stable text alert `AGENT_ID_FALLBACK`, including the original selector and the resolved rollout ID.

For v2, use `scripts/delegation_telemetry.py` as the machine-readable collection
boundary. Record each Work Package when it is spawned, preferring the exact
`rollout_id`, then run `collect` after the child terminates. The collector calls
the existing `agent_evidence.py` resolver only for explicitly recorded
delegations, preserves effective settings, token categories, cost estimates and
correlation fallbacks, and writes a delegated subtotal plus an unavailable
parcel list. It never discovers spawn relationships, mutates rollouts or turns
an unavailable cost into zero. Keep this delegated subtotal separate from the
main-chat `task_window.py` report.

For T2+ delegated work, add a `Custo total da tarefa` section to `evidence.md`: sum only the estimated `total_usd` values from agent rollouts belonging to the current task, record the number of costed agents, currency/basis, and exclusions; do not include the main conversation or unrelated validation rollouts, and record `not available` when no complete estimates exist.

When the task includes main-chat attribution, require this lifecycle: `start` → `close` → `report --final --output task-window-report.json`. Create `specs/<slug>/task-window.json` with `python scripts/task_window.py start --task-id <task-id> --output specs/<slug>/task-window.json --sessions-root <sessions-root> [--session-file <rollout.jsonl>|--session-id <session-id>]`, close it after the task's `task_complete` or `turn_aborted` event with `python scripts/task_window.py close --window specs/<slug>/task-window.json --sessions-root <sessions-root> --end-turn-id <start-turn-id>`, and generate the final report with `python scripts/task_window.py report --window specs/<slug>/task-window.json --sessions-root <sessions-root> --pricing-config <pricing-config.toml> --final --output specs/<slug>/task-window-report.json --json`. The final report must use `scope: main-chat-orchestrator` and explicitly exclude delegated-agent rollouts, tool fees, modality fees and subscription billing. The sidecar stores the main session ID, rollout filename and runtime turn boundaries, without an absolute local path; it must not write marker messages or mutate the runtime-owned rollout. An open/provisional window is never final evidence. A `not-available` cost remains unavailable, never zero; keep the main-chat estimate separate from the delegated-agent subtotal, and record the combined task total as unavailable whenever a required parcel is unavailable.

The Orchestrator must actually execute this lifecycle when attribution is
required. `task_window.py` consumes real runtime-owned `task_started`,
`task_complete` and `turn_aborted` events; it does not emit synthetic markers.
If a boundary is absent, preserve `not-available` and do not inject a marker into
the rollout.

## Required artifacts

For a feature folder `specs/<slug>/`, keep:

- `spec.md`: behavior, constraints, acceptance criteria, and out of scope.
- `plan.md`: executable milestones with files, commands, dependencies, and rollback notes.
- `status.md`: current phase, completed work, blockers, and next action.
- `evidence.md`: commands, results, and acceptance-criteria traceability.
- `verification.json`: generated proof that the current annotated tests passed for each acceptance criterion.
- v2 `delegation-evidence.json`: machine-readable delegation declarations and collected rollout evidence; use `scripts/delegation_telemetry.py` rather than prose-only aggregation.

Use `docs/architecture/decisions/ADR-*.md` for durable architectural decisions. Keep `AGENTS.md` short and repository-specific.

## Completion gate

Do not claim completion until `references/completion-standard.md` is satisfied. For a feature, run its real test command through `scripts/verify_feature.py`, collect delegated evidence when delegation exists, then run `scripts/validate_feature.py`; run `scripts/check_drift.py` for the repository when applicable. Report skipped checks honestly. A passing test command without an `@spec:AC-xxx` mapping is not proof for an acceptance criterion.

## Interface validation

For a user-facing change, prefer validation in a real browser. First detect available capabilities. Prefer `playwright-cli` for repeatable browser flows and evidence; use Playwright MCP for interactive inspection, browser-session state, or live debugging when it is available to the runtime. Do not require both tools for the same scenario. If neither is available, use the strongest available project-native or approved browser validation, record the limitation, and never claim real-browser proof that was not obtained. Recommend enabling Playwright tooling for interface work, but never install it without explicit user authorization. Read `references/interface-validation.md` before planning or judging interface evidence.

For UI-affecting features, record in `evidence.md` whether Impeccable was used. When used, record role, action and purpose; when not used, record the reason. Its use and installation remain optional and never block completion.

## Baseline conformance

Offer `baseline-conformance` only for projects that began without AISDD. Run it only on explicit user request and follow `references/baseline-conformance.md`. It may create documentation and follow-up specs but must never alter product code, tests, dependencies, runtime configuration, infrastructure, database, or CI.

## Scripts

Run these commands from the directory that contains this `SKILL.md` so the
relative `scripts/` paths resolve:

```text
python scripts/init_project.py <repo>
python scripts/create_feature.py <repo> "Feature name" --class T2
# new features default to v2; use --contract v1 only for compatibility/fixtures
python scripts/verify_feature.py <repo> specs/<slug> -- <real-test-command>
python scripts/validate_feature.py <repo> specs/<slug>
python scripts/check_drift.py <repo>
python scripts/model_routing.py --role reviewer --class T2 --availability-json available-models.json
python scripts/model_routing.py --role reviewer --class T2 --availability-json available-models.json --requested-model <model> --requested-effort <effort> --require-available --json
python scripts/agent_evidence.py --agent-id /root/reviewer --json
python scripts/agent_evidence.py --rollout-id <id-do-rollout> --json
python scripts/delegation_telemetry.py init --output specs/<slug>/delegation-evidence.json --work-packages specs/<slug>/work-packages.json
python scripts/delegation_telemetry.py record --output specs/<slug>/delegation-evidence.json --work-package WP-001 --role implementer --agent-id <id> --requested-model <model> --requested-effort <effort>
python scripts/delegation_telemetry.py collect --output specs/<slug>/delegation-evidence.json --sessions-root <sessions-root> --pricing-config <pricing-config.toml> --json
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
