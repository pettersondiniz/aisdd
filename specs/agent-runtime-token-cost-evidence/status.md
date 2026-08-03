# Status: Agent runtime token and cost evidence

- Class: T2
- Current phase: Complete
- Last update: 2026-08-02
- Next action: none.
- Blockers: none.

## Decisions

- The calculation is API-equivalent only and is not subscription billing.
- Missing token-classification fields are not treated as zero.
- Cumulative usage above a model's long-context threshold is not priced without request-level telemetry.
