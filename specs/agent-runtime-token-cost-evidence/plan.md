# ExecPlan: Agent runtime token and cost evidence

## State

Class: T2
Phase: Implementation

## Milestones

### M1 — Read and validate observed telemetry

- [x] Add cumulative usage extraction to `scripts/agent_evidence.py`.
- [x] Refuse incomplete or internally inconsistent category totals.
- [x] Cover observed and unavailable telemetry with synthetic-rollout tests.

### M2 — Price without inventing billing data

- [x] Add a versioned default price-table template and use the user-global table when available.
- [x] Calculate separate input, cache, cache-write, output, and reasoning-output components.
- [x] Refuse an estimate when the observed model is unpriced.

### M3 — Integrate evidence guidance

- [x] Update the AISDD instruction and evidence template.
- [x] Run verification, validation, drift checks, independent review, and install the final global skill copy.

## Tasks

| ID | Milestone | Acceptance criteria | Files | Status |
|---|---|---|---|---|
| T-501 | M1 | AC-501 | `scripts/agent_evidence.py`, tests | Complete |
| T-502 | M1 | AC-502 | `scripts/agent_evidence.py`, tests | Complete |
| T-503 | M2 | AC-503 | price template, script, tests | Complete |
| T-505 | M2 | AC-504 | `scripts/agent_evidence.py`, tests | Complete |
| T-506 | M2 | AC-505 | `scripts/agent_evidence.py`, tests | Complete |
| T-504 | M3 | AC-501–AC-504 | `SKILL.md`, evidence template | Complete |
