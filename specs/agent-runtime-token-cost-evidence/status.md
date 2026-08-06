# Status: Agent runtime token and cost evidence

- Class: T2
- Current phase: Completion
- Last update: 2026-08-06
- Next action: none; the final task-window report and combined task total are recorded.
- Blockers: none.

## Decisions

- The calculation is API-equivalent only and is not subscription billing.
- Missing token-classification fields are not treated as zero.
- Tiered long-context pricing is not inferred from cumulative usage; the compatibility fallback is explicitly warned or refused when request-level telemetry is unavailable.
- Main-chat attribution uses a sidecar `task-window.json`, not marker messages or writes to runtime-owned session logs.
- The task window was closed at the persisted `task_complete` boundary and is now final evidence.
- Main-chat cost and delegated-agent subtotal are recorded separately, with the combined total recorded after both became available.
