# Agent runtime token and cost evidence

## Objective

When a Codex rollout exposes cumulative and per-request token telemetry, preserve its observable token categories and calculate an API-equivalent USD estimate using a versioned local pricing table. For the main conversation, attribute that estimate to an explicit task window rather than charging the entire session.

## Expected behavior

`agent_evidence.py` reads only the selected rollout. It preserves the last readable cumulative `total_token_usage` snapshot and all readable `last_token_usage` snapshots, including input, cached input, cache-write input, output, and reasoning output. When complete per-request telemetry is available, it prices each request independently and reconciles the sum against the final cumulative snapshot. If the observed effective model has complete prices in the selected TOML table, it reports a componentized API-equivalent estimate.

`task_window.py` persists a task boundary in `specs/<slug>/task-window.json` using the main session identifier, rollout filename and runtime turn identifiers. The sidecar does not persist an absolute local path; `close` and `report` resolve the filename below an explicit/default sessions root and verify the session identity. It reads the main session without selecting subagent rollouts, collects only `event_msg` records whose payload type is `token_count` inside the window, subtracts the cumulative baseline immediately before the window, and reconciles the selected `last_token_usage` snapshots against that delta. The runtime's explicit `compacted` → `token_count` → `context_compacted` accounting sequence is preserved as diagnostic evidence but excluded from request pricing.

## Rules and invariants

- The recognized runtime compaction sequence is `compacted` -> `world_state` -> `turn_context` -> `token_count` -> `context_compacted`; only that exact structural sequence is excluded from request pricing, while ambiguous variants fail closed.
- The utility remains read-only with respect to sessions and configuration.
- The default table is `~/.codex/aisdd/cost-pricing.toml`; when absent, the skill template is used. `--pricing-config` permits an explicit table.
- Cached input is treated as a subset of input and replaces the standard input rate for that portion. Cache-write input is a separate priced category when the runtime exposes it. Output is charged once at the configured output rate; reasoning output is reported separately only for traceability.
- Long-context pricing is evaluated per request from `last_token_usage.input_tokens`, never from the cumulative rollout input. A rollout with complete per-request telemetry can apply the configured long-context multipliers to only the requests above the threshold.
- Each model must declare an explicit `long_context_pricing` policy: `standard` means no long-context modifier; `tiered` requires a positive threshold and input/output multipliers. Missing or incomplete policy data is not priced.
- When a model uses tiered long-context pricing and per-request telemetry is unavailable, the default compatibility fallback may produce a standard-price estimate with a warning; `--respect-long-context` refuses that estimate. When per-request telemetry is available, the tiered policy is applied without the fallback warning.
- The sum of complete `last_token_usage` snapshots must match the final cumulative `total_token_usage` fields before a per-request estimate is accepted.
- A main-chat window must have explicit start/end turn references; an open window may produce only a provisional report and must not be recorded as final evidence.
- `start` fails when automatic selection finds multiple open main sessions; `close` requires an explicit `--end-turn-id` matching the start turn, and a boundary cannot silently include a later task.
- A main session requires recognized positive `session_meta`; the sidecar's session ID and rollout filename must match the resolved local rollout below `--sessions-root`.
- Unreadable JSONL records that affect the pre-window baseline or selected window make a closed report unavailable; malformed usage outside the explicit compaction sequence is never silently ignored.
- Model and pricing policy are resolved for each main-chat request from the nearest readable `turn_context`; a model change creates separate priced segments.
- A persisted boundary is resolved by its event index, line, kind and turn identifier; duplicate or changed boundaries fail closed instead of moving the window.
- A closed window with model activity after its last readable `token_count`, or with only excluded compaction snapshots, has no cost estimate.
- `start --force` must not overwrite the selected runtime rollout, and rollout discovery/resolution must reject paths that resolve outside `--sessions-root`.
- Malformed `turn_context` model metadata produces `not-available` rather than a traceback.
- An API-equivalent estimate is never a statement of ChatGPT subscription billing.
- Missing, malformed, inconsistent, or unpriced data produces `not-available`; no totals or prices are inferred.

## Out of scope

- Actual account charges, invoices, rate-limit accounting, or backend billing proof.
- Price discovery or automatic updates from the internet.
- Guessing token counts absent from the local rollout.
- Automatic semantic inference of task boundaries from message text.

## Acceptance criteria

- [ ] AC-501: A uniquely resolved rollout with complete cumulative and per-request token telemetry returns every observed category and a componentized API-equivalent cost based on the per-request snapshots.
- [ ] AC-502: A rollout missing a required classification returns `not-available` for cost rather than assuming zero tokens.
- [ ] AC-503: A rollout whose observed model is absent from the price table returns `not-available` for cost and identifies that observed model.
- [ ] AC-504: When a tiered model has no complete per-request telemetry, `--respect-long-context` returns `not-available` rather than pricing long context from cumulative usage.
- [ ] AC-505: With explicit `--ignore-long-context`, the tool returns the standard-price token estimate and a warning that it may be inaccurate.
- [ ] AC-506: With multiple complete `last_token_usage` snapshots, the tool classifies long context per request, applies the configured tiered multipliers only to qualifying requests, and reports the request counts.
- [ ] AC-507: A model with an explicit `standard` long-context policy can be priced without threshold or multiplier fields, including when a request exceeds the tiered thresholds of other models.
- [ ] AC-508: A model with a missing or incomplete long-context policy returns `not-available` rather than treating the missing policy as standard pricing.
- [ ] AC-509: If the sum of per-request snapshots does not reconcile with the final cumulative usage, the per-request cost estimate returns `not-available`.
- [ ] AC-510: Repeated identical usage events for the same cumulative snapshot are counted once and reported as ignored duplicates.
- [ ] AC-511: A malformed or partially classified `last_token_usage` snapshot returns `not-available` and cannot fall through to a cumulative fallback estimate.
- [ ] AC-512: When cumulative telemetry is absent but per-request snapshots are readable, the snapshots are preserved in the result and cost remains `not-available` because reconciliation is impossible.
- [ ] AC-513: `task_window.py start` persists an open `task-window.json` with the selected main session and a runtime `start_turn_id`, without writing to the runtime session log.
- [ ] AC-514: A closed main-chat task window collects only its in-window `token_count` events, calculates the cumulative delta from the pre-window baseline, and reconciles complete per-request snapshots against that delta.
- [ ] AC-515: Main-chat requests are priced by their associated effective model and explicit `standard`/`tiered` policy, including model changes and per-request long-context classification.
- [ ] AC-516: Missing boundaries, incomplete telemetry, unknown models, or reconciliation mismatch return `not-available` while preserving safe boundary and usage evidence.
- [ ] AC-517: Malformed `turn_context` model metadata returns structured `not-available` output without a traceback.
- [ ] AC-518: `start --force` refuses an output path that would overwrite the selected runtime rollout and leaves that rollout unchanged.
- [ ] AC-519: Automatic rollout discovery rejects a symlink or reparse path that resolves outside `--sessions-root`.
- [ ] AC-520: Persisted boundary identity is enforced and duplicate end boundaries cannot extend a closed window into a later task.
- [ ] AC-521: `start --force` refuses an existing output hardlink to any rollout under `--sessions-root`, even when that hardlink is outside the root.
- [ ] AC-522: Model activity represented by `event_msg.agent_reasoning` after the last `token_count` makes a closed report unavailable until a later `token_count` is observed.

## Decisions

- D-501: Use the final readable cumulative usage event instead of summing event snapshots, because each snapshot is a running rollout total.
- D-502: Keep the pricing table user-editable and require official-source maintenance rather than silently fetching mutable prices.
- D-503: Use `last_token_usage` snapshots for pricing and retain `total_token_usage` as the reconciliation checksum; never sum cumulative snapshots.
- D-504: Apply the long-context input multiplier to uncached, cached, and cache-write input components, and apply the output multiplier to output; reasoning output remains trace-only because output is priced once.
- D-505: Require an explicit per-model long-context policy so an absent configuration cannot silently mean either standard or tiered pricing.
- D-506: Deduplicate identical `(total_token_usage, last_token_usage)` pairs before reconciliation because the runtime can repeat the terminal usage event.
- D-507: Treat a present but malformed usage field as observed invalid telemetry, not as an absent field; preserve it in the safe token summary and refuse pricing.
- D-508: Keep task boundaries in a sidecar `task-window.json`; do not inject marker messages into the model conversation or mutate runtime-owned session logs.
- D-509: Reconcile a main-chat window against the cumulative delta across its boundaries, not against the lifetime session total.
- D-510: Treat only `token_count` event messages as usage calls; identify the explicit compaction accounting sequence structurally and preserve it outside request sums.
- D-511: Require same-turn explicit closure and portable sidecar identity to prevent accidental cross-task/session attribution.
- D-512: Permit only the observed `world_state` record inside the explicit compaction sequence; do not generalize from an arbitrary zero-input snapshot.
- D-513: Persist and validate boundary identity so later events with a reused turn identifier cannot shift the attribution window.
- D-514: Treat model reasoning events as activity requiring a later usage snapshot, while lifecycle and patch bookkeeping remain non-usage events.

## Suposições

- O runtime local preserva `task_started`, `task_complete` ou `turn_aborted`, `turn_context` e eventos `token_count` no rollout da sessão principal.
- O operador fecha a janela depois que a task termina e registra um relatório fechado como evidência final.
