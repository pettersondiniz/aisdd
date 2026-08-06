# ExecPlan: Agent runtime token and cost evidence

## State

Class: T2
Phase: Completion

## Milestones

### M1 — Read and validate observed telemetry

- [x] Add cumulative usage extraction to `scripts/agent_evidence.py`.
- [x] Refuse incomplete or internally inconsistent category totals.
- [x] Cover observed and unavailable telemetry with synthetic-rollout tests.
- [x] Add extraction and reconciliation for every complete `last_token_usage` snapshot.
- [x] Price each request independently and retain a cumulative fallback only when the selected policy permits it.

### M2 — Price without inventing billing data

- [x] Add a versioned default price-table template and use the user-global table when available.
- [x] Calculate separate input, cache, cache-write, output, and reasoning-output components.
- [x] Refuse an estimate when the observed model is unpriced.
- [x] Add an explicit `standard`/`tiered` long-context policy to every model entry.
- [x] Apply tiered multipliers per request and report standard/long-context request counts.

### M3 — Integrate evidence guidance

- [x] Update the AISDD instruction and evidence template.
- [x] Run verification, validation, drift checks, independent review, and install the final global skill copy.
- [x] Update the feature evidence and guidance for per-request telemetry and the explicit policy.

### M4 — Attribute main-chat cost to a task window

- [x] Define the sidecar boundary contract and keep runtime session logs read-only.
- [x] Implement start/close/report lifecycle for `specs/<slug>/task-window.json`.
- [x] Reconcile in-window `last_token_usage` snapshots against the cumulative delta between boundaries.
- [x] Price main-chat requests by associated model and policy without mixing subagent rollouts.
- [x] Validate open, closed, missing, malformed and mismatched windows with synthetic session tests.
- [x] Reject runtime-rollout overwrite, unsafe resolved paths, duplicate boundaries and malformed context metadata.

## Tasks

| ID | Milestone | Acceptance criteria | Files | Status |
|---|---|---|---|---|
| T-501 | M1 | AC-501 | `scripts/agent_evidence.py`, tests | Complete |
| T-502 | M1 | AC-502 | `scripts/agent_evidence.py`, tests | Complete |
| T-503 | M2 | AC-503 | price template, script, tests | Complete |
| T-505 | M2 | AC-504 | `scripts/agent_evidence.py`, tests | Complete |
| T-506 | M2 | AC-505 | `scripts/agent_evidence.py`, tests | Complete |
| T-504 | M3 | AC-501, AC-502, AC-503, AC-504 | `SKILL.md`, evidence template | Complete |
| T-507 | M1 | AC-501, AC-502, AC-509, AC-510, AC-511, AC-512 | `scripts/agent_evidence.py`, tests | Complete |
| T-508 | M2 | AC-504, AC-505, AC-506, AC-507, AC-508 | `assets/templates/cost-pricing.toml`, `scripts/agent_evidence.py`, tests | Complete |
| T-509 | M3 | AC-501, AC-502, AC-503, AC-504, AC-505, AC-506, AC-507, AC-508, AC-509, AC-510, AC-511, AC-512 | `SKILL.md`, `spec.md`, `status.md`, `evidence.md` | Complete |
| T-510 | M4 | AC-513 | `scripts/task_window.py`, `task-window.json`, tests | Complete |
| T-511 | M4 | AC-514, AC-516 | `scripts/task_window.py`, tests | Complete |
| T-512 | M4 | AC-515 | `scripts/task_window.py`, tests | Complete |
| T-513 | M4 | AC-513, AC-514, AC-515, AC-516 | `spec.md`, `status.md`, `evidence.md`, verification | Complete |
| T-514 | M4 | AC-517, AC-518, AC-519, AC-520, AC-521, AC-522 | `scripts/task_window.py`, tests, `spec.md` | Complete |
