# Status: Agent runtime token and cost evidence

- Class: T2
- Current phase: Completion
- Last update: 2026-08-07
- Next action: none; M5 completed with independent Verifier, Reviewer and Documentation Reviewer gates recorded in evidence.md.
- Blockers: none.

## Decisions

- The calculation is API-equivalent only and is not subscription billing.
- Missing token-classification fields are not treated as zero.
- Tiered long-context pricing is not inferred from cumulative usage; the compatibility fallback is explicitly warned or refused when request-level telemetry is unavailable.
- Main-chat attribution uses a sidecar `task-window.json`, not marker messages or writes to runtime-owned session logs.
- The task window was closed at the persisted `task_complete` boundary and is now final evidence.
- Historical M4 recorded the main-chat cost and delegated-agent subtotal separately and produced a combined total after both became available; the current M5 combined total remains not-available while any delegated estimate is unavailable.
- M5 declares documentary impact because it changes the rollout-correlation alert, the final task-window report contract and the validation gate.
- M5 will use an exact rollout UUID fallback only when direct `--agent-id` matching fails; partial or ambiguous selectors remain unavailable.
- A feature declaring mandatory main-chat attribution must retain a closed `task-window.json` plus a final `task-window-report.json`; delegated-agent evidence alone cannot close that gate.

## M5 current execution

- Implementation/documentation state: complete for M5; final evidence is recorded in `evidence.md`.
- Focused result: 96 tests passed; 2 symlink cases were skipped by the host policy.
- Full result: 134 tests passed; `verify_feature.py` recorded 29 criteria with passed=true.
- Final gate: complete; Verifier, Reviewer and Documentation Reviewer passed.
- Global check_drift remains red only for three pre-existing feature artifacts outside this feature.
