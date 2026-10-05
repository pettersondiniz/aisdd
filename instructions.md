# AISDD instructions

AISDD is a lightweight, delegated delivery workflow. It keeps specification-driven delivery useful without mandatory machine manifests, generated proof artifacts, telemetry, strict model gates, or recursive artifact reconciliation.

## Mandatory triage

Before changing code, tests, configuration, infrastructure, data, or technical
documentation:

1. Inspect the repository, its `AGENTS.md`, relevant docs, code, tests, and
   available commands.
2. Classify the request as low, medium, or high risk.
3. Unless the user requests solo execution, select at least one specialized
   agent for delegable work using the runtime selection below.
4. Decide the minimum artifacts and validation needed.
5. Identify irreversible or external effects that require explicit
   authorization before execution.

Use the template at `assets/templates/AGENTS.md` when initializing project
guidance. Preserve an existing project `AGENTS.md` unless the user asks for an
update.

### Risk levels

- **Low** — localized bug, mechanical change, or known behavior with limited
  blast radius. Delegate one focused role, run focused checks, and avoid
  persistent planning artifacts unless the task needs them.
- **Medium** — feature, meaningful refactor, interface change, or changed
  contract. Use `spec.md`, `plan.md`, and `status.md`; delegate planning,
  implementation, and testing.
- **High** — migration, persistence, security-sensitive change, architecture,
  irreversible operation, or broad integration. Use the medium workflow plus
  explicit risks, rollback/contingency notes, and relevant validation. Stop
  before an irreversible or external effect unless the user authorized it.

When uncertain, choose the higher level, but do not create controls that are
not relevant to the actual change.

## Delegation

Delegation is the default for changes when the user has not requested solo
execution. Use the smallest useful set of roles; do not create a rigid chain
merely to satisfy a template. An explicit request to work without delegation
takes precedence over this default.

### Subagent runtime selection

The main agent owns delegation. Check the active model's `multi_agent_version`
and the collaboration tools actually exposed by the current runtime. A missing
tool from an initial or abbreviated listing is not proof that it is unavailable;
discover the collaboration tools before claiming unavailability.

1. Prefer `multi_agent_version: "v2"` and its `spawn_agent` collaboration tool
   when supported by the active model and runtime.
2. If V2 is unavailable or its spawn call is rejected as unsupported, try
   `multi_agent_version: "v1"` and its `spawn_agent` tool when available.
3. If neither protocol can create a subagent, perform the work in the main
   agent without delegation. Record the actual missing capability or error in
   `status.md` or the final summary.

This order selects among capabilities provided by the runtime; a skill cannot
change the model's protocol version. Do not modify global Codex configuration
to force a version. Do not use `create_thread`, `fork_thread`, or another
user-visible task as a substitute for a subagent. Create a separate task only
when the user explicitly requests one.

When a specialized agent receives a role and file scope, it is already the
delegate: execute that assignment directly. Do not apply the main agent's
delegation rule recursively or create another agent unless the parent
explicitly authorizes a further split. State this boundary in each delegated
prompt.

- **planner** — inspect context, clarify behavior, write or update the
  specification and execution plan, and identify risks and checks.
- **implementer** — modify product code, configuration, migrations, or other
  implementation files within the agreed scope.
- **tester** — create or update tests and run focused validation. The tester
  may fix test setup, but does not silently change product behavior to make a
  test pass.
- **reviewer** — perform a read-only independent review when the user asks for
  one. Review is not a default completion gate.

Typical routing is:

- low: one focused implementer or tester;
- medium: planner → implementer → tester;
- high: planner → implementer → tester, with reviewer when requested.

The main agent coordinates, integrates results, and resolves conflicts. If a
specialized agent is genuinely unavailable after the runtime checks above,
use the main-agent fallback when the user did not require that exact agent or
model. Record the attempted protocol and actual reason in `status.md` or the
final summary; do not turn ordinary unavailability into a blocked task.

Only one agent should write a given file scope at a time. Independent read-only
work may run in parallel. Run testing after the implementation it covers.

## Lightweight artifacts

Use artifacts only when they improve continuity:

- `spec.md` — behavior, constraints, acceptance criteria, compatibility, and
  out of scope. Use for medium and high-risk work.
- `plan.md` — milestones, files or areas, dependencies, delegated roles,
  validation commands, risks, and rollback notes.
- `status.md` — current phase, delegated work and results, checks run,
  limitations, corrections, and next action.

Keep delegation records as a small table in `plan.md` or `status.md` with role,
objective, scope, result, and fallback if applicable. Do not create
`work-packages.json`, `delegation-evidence.json`, `verification.json`, task
windows, generation markers, or reconciliation journals.

For low-risk work, a concise plan and final summary can replace persistent
artifacts. Never create artifacts only to satisfy this skill.

## Model routing

Model routing is a preference layer, not a completion gate.

- If a project or user-supplied routing file exists, prefer its role and risk
  mappings. Otherwise use `assets/templates/model-routing.toml`, which prefers
  `gpt-6-luna` for specialized roles.
- If the preferred model is unavailable, inherit the current runtime model
  and a compatible effort.
- Do not query availability through a separate manifest, modify global
  configuration automatically, or require an exact model/effort match.
- If a preferred model is unavailable, use the compatible runtime fallback and
  record the requested and effective choice when it matters.
- If the user explicitly requires one exact model, do not silently substitute;
  report the limitation before that delegated step.

Do not collect token, cost, rollout, or model telemetry as a mandatory part of
the workflow.

## Lifecycle

Follow this short lifecycle and resume from the first incomplete phase:

1. **Discover** — inspect context, commands, risks, and existing guidance.
2. **Triage** — classify risk, choose artifacts, agents, model preferences,
   and validation.
3. **Specify and plan** — for medium/high work, create or update the three
   lightweight artifacts before implementation.
4. **Implement** — delegate the scoped change when available and authorized,
   or execute it in the main agent under the fallback above; integrate results.
5. **Test and validate** — run the real relevant checks; report skipped checks
   and residual risk honestly.
6. **Review** — only when requested or explicitly included in the plan.
7. **Close** — update status, summarize evidence and limitations, and state the
   remaining next action if the work is incomplete.

If discovery changes the behavior, scope, or risk, update the spec/plan before
continuing. Do not rewrite artifacts merely to make a validator pass.

## Bounded correction policy

When a test or requested review finds a problem:

1. identify the concrete failing behavior or finding;
2. delegate one focused correction to the appropriate role when available and
   authorized, or correct it in the main agent under the fallback above;
3. rerun only the affected checks plus the relevant regression checks;
4. count that as one correction cycle.

Allow at most two correction cycles per task execution. Batch closely related
findings within one cycle, but do not open an unbounded chain of corrective
work. If the issue persists, progress stops, or the artifacts and code begin
to disagree, end the execution with a partial/blocked status, diagnosis,
checks already run, and a concrete next action. Do not automatically start
another agent chain.

## Validation and completion

- Run the project's real focused tests and add broader tests, lint, types,
  build, migration, or browser checks when relevant.
- For interface changes, use the strongest available browser or project-native
  validation and state when real-browser validation was not possible.
- Do not install tools, change global configuration, or perform external
  operations without explicit authorization.
- Do not claim completion when an acceptance criterion, required check, or
  authorized side effect remains unresolved.
- Record limitations as limitations; never turn missing evidence into success.

## Explicit exclusions

This skill intentionally does not require:

- T0–T4 compatibility contracts;
- mandatory verifier or documentation-reviewer roles;
- machine-readable delegation graphs;
- generated evidence JSON or hash-based artifact generations;
- task-window or token-cost accounting;
- external model bridges;
- global drift audits or baseline-conformance workflows;
- automatic retries without a bounded correction budget.
