# Evidence: Agent runtime token and cost evidence

## Commands run

| Command | Result | When |
|---|---|---|
| `python -m unittest tests.test_agent_evidence -v` | 11 tests passed | 2026-08-02 |
| `python -m unittest discover -s tests -v` | 27 tests passed | 2026-08-02 |
| `python scripts/verify_feature.py . specs/agent-runtime-token-cost-evidence -- python -m unittest discover -s tests -v` | 4 criteria with current proof | 2026-08-02 |
| `python scripts/validate_feature.py . specs/agent-runtime-token-cost-evidence` | passed | 2026-08-02 |
| `python scripts/check_drift.py .` | no structural or traceability drift | 2026-08-02 |
| installed `agent_evidence.py` against `/root/token_cost_planner` | resolved model/effort and token telemetry; cost honestly unavailable for cumulative long-context usage | 2026-08-03 |

## Traceability

| Criterion | Implementation | Test/evidence | Status |
|---|---|---|---|
| AC-501 | usage extraction and component cost estimate | `tests/test_agent_evidence.py` (`@spec:AC-501`) | Passed |
| AC-502 | incomplete classification refusal | `tests/test_agent_evidence.py` (`@spec:AC-502`) | Passed |
| AC-503 | unpriced observed-model refusal | `tests/test_agent_evidence.py` (`@spec:AC-503`) | Passed |
| AC-504 | refusal of long-context estimate without request-level telemetry | `tests/test_agent_evidence.py` (`@spec:AC-504`) | Passed |
| AC-505 | standard-price default with warning | `tests/test_agent_evidence.py` (`@spec:AC-505`) | Passed |

## Agent traceability

| Role | Agent | Task | Requested model | Requested effort | Effective model | Effective effort | Effective source | Tokens/categories observed | API cost estimate | Fallback | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| planner | `/root/token_cost_planner` | Read-only design review for telemetry and pricing semantics | inherit | inherit | gpt-5.6-terra | medium | `local-rollout-turn_context:last-readable` | observed: input, cached input, cache-write input, output, reasoning output | unavailable: cumulative long-context data lacks per-request granularity | inherit | completed |
| reviewer | `/root/token_cost_reviewer` | Independent review of pricing semantics and robustness | inherit | inherit | gpt-5.6-terra | medium | `local-rollout-turn_context:last-readable` | observed: input, cached input, cache-write input, output, reasoning output | unavailable: cumulative long-context data lacks per-request granularity | inherit | completed; blockers corrected |

Summary: agents used: 2; fallbacks: 2 (inherited chat configuration).

## Residual risks

- Local rollout usage is observable telemetry, not a backend billing ledger.
- The price table requires explicit maintenance from official pricing sources.
- Tool and modality fees are excluded from the token-only estimate.
