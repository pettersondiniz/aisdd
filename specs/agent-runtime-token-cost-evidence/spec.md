# Agent runtime token and cost evidence

## Objective

When a Codex subagent rollout exposes cumulative token telemetry, preserve its observable token categories and calculate an API-equivalent USD estimate using a versioned local pricing table.

## Expected behavior

`agent_evidence.py` reads only the selected rollout. It preserves the last readable cumulative `total_token_usage` snapshot, including input, cached input, cache-write input, output, and reasoning output. If the observed effective model has complete prices in the selected TOML table, it reports a componentized API-equivalent estimate.

## Rules and invariants

- The utility remains read-only with respect to sessions and configuration.
- The default table is `~/.codex/aisdd/cost-pricing.toml`; when absent, the skill template is used. `--pricing-config` permits an explicit table.
- Cached input is treated as a subset of input and replaces the standard input rate for that portion. Cache-write input is a separate priced category when the runtime exposes it. Output is charged once at the configured output rate; reasoning output is reported separately only for traceability.
- Context-long pricing is per request. A cumulative rollout total above the configured threshold cannot be priced honestly without per-request telemetry.
- An API-equivalent estimate is never a statement of ChatGPT subscription billing.
- Missing, malformed, inconsistent, or unpriced data produces `not-available`; no totals or prices are inferred.

## Out of scope

- Actual account charges, invoices, rate-limit accounting, or backend billing proof.
- Price discovery or automatic updates from the internet.
- Guessing token counts absent from the local rollout.

## Acceptance criteria

- [ ] AC-501: A uniquely resolved rollout with complete cumulative token telemetry returns every observed category and a componentized API-equivalent cost for a priced model.
- [ ] AC-502: A rollout missing a required classification returns `not-available` for cost rather than assuming zero tokens.
- [ ] AC-503: A rollout whose observed model is absent from the price table returns `not-available` for cost and identifies that observed model.
- [ ] AC-504: When cumulative usage alone cannot establish per-request long-context pricing, the estimate returns `not-available`.
- [ ] AC-505: With explicit `--ignore-long-context`, the tool returns the standard-price token estimate and a warning that it may be inaccurate.

## Decisions

- D-501: Use the final readable cumulative usage event instead of summing event snapshots, because each snapshot is a running rollout total.
- D-502: Keep the pricing table user-editable and require official-source maintenance rather than silently fetching mutable prices.
