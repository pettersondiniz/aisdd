# Evidence: Agent runtime token and cost evidence

## Commands run

| Command | Result | When |
|---|---|---|
| `python -m unittest tests.test_agent_evidence -v` | 27 focused tests passed | 2026-08-05 |
| `python -m unittest discover -s tests -v` | 44 tests passed | 2026-08-05 |
| `python scripts/verify_feature.py . specs/agent-runtime-token-cost-evidence -- python -m unittest discover -s tests -v` | 12 criteria with current proof; 44 tests passed | 2026-08-05 |
| `python scripts/validate_feature.py . specs/agent-runtime-token-cost-evidence` | passed | 2026-08-05 |
| `python scripts/verify_feature.py . specs/agent-runtime-model-evidence -- python -m unittest discover -s tests -v` | 4 dependent criteria with current proof; 44 tests passed | 2026-08-05 |
| `python scripts/verify_feature.py` for `baseline-conformance-ui-traceability`, `interactive-model-routing`, `mandatory-aisdd-triage-template` and `playwright-validation-guidance` | refreshed 11 dependent criteria after the shared template-test update | 2026-08-05 |
| `python scripts/check_drift.py .` | no structural or traceability drift | 2026-08-05 |
| `git diff --check` | passed; only Git line-ending conversion warnings | 2026-08-05 |
| `python scripts/agent_evidence.py --rollout-id 019fd432-ca5d-7942-949b-36247e293f8f --pricing-config C:\Users\Usuario\.codex\aisdd\cost-pricing.toml --json` | real subagent rollout resolved as `gpt-5.6-sol/high`; 220101 cumulative tokens, 8 unique request snapshots, 1 duplicate terminal snapshot ignored; reconciled estimate `0.381748` USD; no long-context requests | 2026-08-05 |
| `python -m unittest tests.test_task_window -v` | historical pre-hardening snapshot: 17 focused task-window tests passed | 2026-08-06 |
| `python -m unittest discover -s tests -v` | 61 tests passed after the independent-review correction | 2026-08-06 |
| `python scripts/task_window.py report --window specs/agent-runtime-token-cost-evidence/task-window.json --sessions-root C:\Users\Usuario\.codex\sessions --pricing-config C:\Users\Usuario\.codex\aisdd\cost-pricing.toml --json` | historical pre-hardening snapshot: open/provisional; 160 request snapshots, 1 explicit compaction snapshot excluded; not current/final | 2026-08-06 |
| `python scripts/model_routing.py --role implementer --class T2 --availability-json <runtime snapshot> --json` | implementer routed to `gpt-5.6-luna/max`; correction completed without runtime edits | 2026-08-06 |
| `python -m unittest tests.test_task_window -v` | 5 focused task-window tests passed | 2026-08-06 |
| `python -m unittest discover -s tests -v` | 49 tests passed | 2026-08-06 |
| `python scripts/verify_feature.py . specs/agent-runtime-token-cost-evidence -- python -m unittest discover -s tests -v` | 16 criteria with current proof; 49 tests passed | 2026-08-06 |
| `python scripts/model_routing.py --role tester/reviewer --class T2 --availability-json <runtime snapshot> --json` | tester routed to `gpt-5.6-luna/max`; reviewer routed to `gpt-5.6-sol/high` | 2026-08-06 |
| `python scripts/task_window.py start --task-id agent-runtime-token-cost-evidence --output specs/agent-runtime-token-cost-evidence/task-window.json` | open main-session window persisted; runtime rollout unchanged | 2026-08-06 |
| `python -B -m py_compile scripts/task_window.py tests/test_task_window.py` | passed | 2026-08-06 |
| `python -B -m unittest tests.test_task_window -v` | 36 tests passed; 1 symlink test skipped because Windows denied the required privilege | 2026-08-06 |
| `python -B -m unittest discover -s tests -v` | 81 tests passed; 1 direct-symlink test skipped for the same environmental reason; the junction containment test passed | 2026-08-06 |
| `python -B scripts/verify_feature.py . specs/agent-runtime-token-cost-evidence -- python -B -m unittest discover -s tests -v` | 22 criteria with current proof; 81 tests passed and 1 direct-symlink test skipped | 2026-08-06 |
| `python -B scripts/verify_feature.py` for the five dependent specs | refreshed 15 dependent criteria with current proof; 81 tests passed in each suite and 1 direct-symlink test skipped | 2026-08-06 |
| `python -B -m unittest tests.test_task_window -v` | final focused validation: 37 tests passed; the direct-symlink case was skipped by Windows privilege policy and the directory-junction case passed | 2026-08-06 |
| `python -B scripts/validate_feature.py . specs/agent-runtime-token-cost-evidence` | passed after the final independent tester/reviewer gate | 2026-08-06 |
| `python -B scripts/check_drift.py .` | no structural or traceability drift after the final documentation refresh | 2026-08-06 |
| `git diff --check` | passed; only Git line-ending conversion warnings | 2026-08-06 |
| `python scripts/task_window.py report --window specs/agent-runtime-token-cost-evidence/task-window.json --sessions-root C:\Users\Usuario\.codex\sessions --pricing-config C:\Users\Usuario\.codex\aisdd\cost-pricing.toml --json` | open/provisional; latest real probe recognized 2 explicit compaction snapshots and failed closed because the active turn had model activity after its last `token_count`; no final main-chat cost recorded | 2026-08-06 |
| `python -B scripts/task_window.py close --window specs/agent-runtime-token-cost-evidence/task-window.json --sessions-root C:\Users\Usuario\.codex\sessions --end-turn-id 019fd4d3-6dbe-7b22-8895-b87ec3d68858 --json` | closed at the persisted `task_complete` boundary; start line 1901, end line 4287 | 2026-08-06 |
| `python -B scripts/task_window.py report --window specs/agent-runtime-token-cost-evidence/task-window.json --sessions-root C:\Users\Usuario\.codex\sessions --pricing-config C:\Users\Usuario\.codex\aisdd\cost-pricing.toml --respect-long-context --json` | final closed report; `gpt-5.6-luna`; 453 request snapshots, 3 compaction snapshots excluded, 66,354,354 window tokens, no long-context requests; cost `1.71691256` USD | 2026-08-06 |
| `python -B scripts/verify_feature.py . specs/agent-runtime-token-cost-evidence -- python -B -m unittest discover -s tests -q` | final proof refresh: 22 criteria with current proof; 81 tests passed and 1 direct-symlink test skipped | 2026-08-06 |
| `python -B scripts/validate_feature.py . specs/agent-runtime-token-cost-evidence` | passed after final closure and evidence update | 2026-08-06 |
| `python -B scripts/check_drift.py .` | no structural or traceability drift after final closure and evidence update | 2026-08-06 |

## Traceability

| Criterion | Implementation | Test/evidence | Status |
|---|---|---|---|
| AC-501 | cumulative/per-request extraction, reconciliation and componentized estimate | `tests/test_agent_evidence.py` (`@spec:AC-501`) | Passed |
| AC-502 | incomplete token-category refusal | `tests/test_agent_evidence.py` (`@spec:AC-502`) | Passed |
| AC-503 | unpriced or unknown observed-model refusal | `tests/test_agent_evidence.py` (`@spec:AC-503`) | Passed |
| AC-504 | `--respect-long-context` refuses tiered fallback without request telemetry | `tests/test_agent_evidence.py` (`@spec:AC-504`) | Passed |
| AC-505 | explicit `--ignore-long-context` standard-price fallback and warning in JSON/text | `tests/test_agent_evidence.py` (`@spec:AC-505`) | Passed |
| AC-506 | per-request long-context classification, multipliers and counts | `tests/test_agent_evidence.py` (`@spec:AC-506`) | Passed |
| AC-507 | explicit standard policy without threshold/multipliers | `tests/test_agent_evidence.py` (`@spec:AC-507`) | Passed |
| AC-508 | incomplete long-context policy refusal | `tests/test_agent_evidence.py` (`@spec:AC-508`) | Passed |
| AC-509 | per-request/cumulative reconciliation refusal | `tests/test_agent_evidence.py` (`@spec:AC-509`) | Passed |
| AC-510 | duplicate terminal snapshot detection and reporting | `tests/test_agent_evidence.py` (`@spec:AC-510`) | Passed |
| AC-511 | malformed or partial `last_token_usage` refusal without cumulative fallback | `tests/test_agent_evidence.py` (`@spec:AC-511`) | Passed |
| AC-512 | snapshot preservation with missing cumulative telemetry and unavailable cost | `tests/test_agent_evidence.py` (`@spec:AC-512`) | Passed |
| AC-513 | sidecar start lifecycle and read-only runtime session | `tests/test_task_window.py` (`@spec:AC-513`) | Passed |
| AC-514 | closed-window selection, cumulative delta and duplicate reconciliation | `tests/test_task_window.py` (`@spec:AC-514`) | Passed |
| AC-515 | per-request model/policy pricing and long-context classification | `tests/test_task_window.py` (`@spec:AC-515`) | Passed |
| AC-516 | mismatch and missing-boundary fail-closed behavior | `tests/test_task_window.py` (`@spec:AC-516`) | Passed |
| AC-517 | malformed `turn_context` metadata returns structured unavailable output | `tests/test_task_window.py` (`@spec:AC-517`) | Passed |
| AC-518 | `--force` cannot overwrite the selected runtime rollout | `tests/test_task_window.py` (`@spec:AC-518`) | Passed |
| AC-519 | resolved rollout paths remain inside `--sessions-root` | `tests/test_task_window.py` (`@spec:AC-519`) | Passed via executed directory-junction test; direct symlink variant skipped on this Windows host due privilege policy |
| AC-520 | persisted boundary identity and duplicate-end rejection | `tests/test_task_window.py` (`@spec:AC-520`) | Passed |
| AC-521 | hardlink/output protection covers any rollout under the sessions root | `tests/test_task_window.py` (`@spec:AC-521`) | Passed |
| AC-522 | `agent_reasoning` after the last snapshot fails closed until a later snapshot | `tests/test_task_window.py` (`@spec:AC-522`) | Passed |

## Agent traceability

The first 12 historical delegated agents inherited the chat model and effort. Subsequent rollouts used the explicit T2 tester/reviewer/implementer routing shown below. The local rollout evidence records effective settings and token-only estimates observed after each completion.

| Role | Agent | Task/result | Effective model/effort | Tokens | Requests | Duplicate snapshots | API cost estimate | Fallback |
|---|---|---|---|---:|---:|---:|---:|---|
| tester | `019fd47a-8526-7ea2-a463-1720a50e914d` (Signal) | first focused validation; gaps corrected | gpt-5.6-luna / max | 2392342 | 37 | 0 | `0.10712776` USD | inherited chat configuration |
| reviewer | `019fd47a-85ce-7ca0-858f-79a739767b41` (Lens) | first independent review; blockers corrected | gpt-5.6-luna / max | 2945149 | 36 | 0 | `0.13148812` USD | inherited chat configuration |
| tester | `019fd48a-e087-7d62-9ea5-89208338b4ca` (Probe) | regression validation; metadata gap corrected | gpt-5.6-luna / max | 1312606 | 22 | 0 | `0.07812276` USD | inherited chat configuration |
| reviewer | `019fd48a-e13d-70f1-8cfd-7308c0a84c30` (Guard) | second independent review; fail-closed/artifact gaps corrected | gpt-5.6-luna / max | 3071148 | 42 | 0 | `0.13407652` USD | inherited chat configuration |
| tester | `019fd49b-eeb9-72c1-b192-4768bbb1fca8` (Verifier) | found fallback warning gap and stale evidence; corrected | gpt-5.6-luna / max | 1839891 | 26 | 0 | `0.08885420` USD | inherited chat configuration |
| reviewer | `019fd49b-ef6d-7431-957b-17c04df241b5` (Sentinel) | functional PASS; documentation synchronized later | gpt-5.6-luna / max | 3080983 | 39 | 1 | `0.11604760` USD | inherited chat configuration |
| tester | `019fd4a6-8eec-70e0-bb45-f9c4270979ca` (Verifier the 2nd) | found request-telemetry override gap; corrected | gpt-5.6-luna / max | 495633 | 12 | 0 | `0.03346872` USD | inherited chat configuration |
| reviewer | `019fd4a6-8fb6-7380-b636-a2af0fc02986` (Sentinel the 2nd) | functional PASS; documentation synchronized later | gpt-5.6-luna / max | 744231 | 15 | 1 | `0.03952780` USD | inherited chat configuration |
| tester | `019fd4ab-67a4-7971-803b-36b86f105aba` (Probe the 2nd) | functional PASS after request override correction | gpt-5.6-luna / max | 916493 | 17 | 0 | `0.04671208` USD | inherited chat configuration |
| reviewer | `019fd4ab-685a-71c0-9e37-b62f33cab004` (Guard the 2nd) | found text-CLI warning gap; corrected | gpt-5.6-luna / max | 627676 | 12 | 0 | `0.04109352` USD | inherited chat configuration |
| tester | `019fd4b1-b8dd-7561-98d7-f6be383f60bc` (Signal the 2nd) | final functional PASS; verified JSON/text warnings | gpt-5.6-luna / max | 1139819 | 18 | 0 | `0.06859800` USD | inherited chat configuration |
| reviewer | `019fd4b1-b981-7273-85c1-786c57b73ee5` (Lens the 2nd) | final PASS; only stale-documentation note, then synchronized | gpt-5.6-luna / max | 849122 | 15 | 0 | `0.05054448` USD | inherited chat configuration |
| tester | `019fd4e4-65a3-70e2-89b6-fd4775225510` (Signal the 3rd) | focused validation; found remaining lifecycle gaps | gpt-5.6-luna / max | 2070005 | 24 | 1 | `0.09699884` USD | explicit model routing |
| reviewer | `019fd4e4-6676-7b40-8e8c-494af4a5c384` (Sentinel the 3rd) | independent review; identified safety and compaction gaps | gpt-5.6-sol / high | 1011973 | 17 | 0 | `1.48116400` USD | explicit model routing |
| implementer | `019fd4ee-8fe4-7173-9fee-15c45eb24751` (Forge the 3rd) | implemented lifecycle hardening and follow-up corrections | gpt-5.6-luna / max | 24408810 | 235 | 1 | `not-available` — internally inconsistent token classifications | explicit model routing |
| tester | `019fd508-8be0-77e1-a03f-c67a34ad9488` (Verifier the 3rd) | regression validation after the first hardening pass | gpt-5.6-luna / max | 1995229 | 27 | 0 | `0.10000272` USD | explicit model routing |
| reviewer | `019fd508-8cf4-7ce0-ad8d-ba1b2959cbb8` (Lens the 3rd) | independent review; found fail-closed and artifact gaps | gpt-5.6-sol / high | 3299099 | 39 | 0 | `2.98938100` USD | explicit model routing |
| tester | `019fd520-fa40-76c1-9761-42f580fbd1ff` (Verifier the 4th) | targeted validation of corrected boundary behavior | gpt-5.6-luna / max | 3731194 | 45 | 0 | `0.15205000` USD | explicit model routing |
| tester | `019fd520-b1a9-74a3-b84f-b62325a3f582` (Probe the 3rd) | targeted validation of runtime safety and reporting | gpt-5.6-luna / max | 5016411 | 51 | 0 | `0.17979064` USD | explicit model routing |
| tester | `019fd521-4b25-7a83-8a70-71bb6369dcea` (Probe the 4th) | additional focused validation of path protections | gpt-5.6-luna / max | 4533439 | 46 | 0 | `0.17526252` USD | explicit model routing |
| reviewer | `019fd521-61f8-7463-bef5-26ea6cad0b70` (Lens the 4th) | independent security and contract review | gpt-5.6-sol / high | 2440269 | 34 | 0 | `2.64684000` USD | explicit model routing |
| tester | `019fd539-778b-7c01-a2be-9e48332e08c6` (Signal the 4th) | regression validation after safety corrections | gpt-5.6-luna / max | 2687058 | 37 | 0 | `0.11918252` USD | explicit model routing |
| reviewer | `019fd539-7845-7971-bf2b-1677b0e1ccf4` (Guard the 4th) | independent review of final safety and evidence behavior | gpt-5.6-sol / high | 1667458 | 24 | 0 | `1.93577800` USD | explicit model routing |
| tester | `019fd545-f7a3-7641-b2f3-42350586e5b2` (Signal the 5th) | final functional validation before junction coverage | gpt-5.6-luna / max | 1656045 | 22 | 0 | `0.09226656` USD | explicit model routing |
| reviewer | `019fd545-f858-7913-8ce0-cf57c4d47caf` (Lens the 5th) | final review before junction coverage; documentation note corrected | gpt-5.6-sol / high | 4879036 | 46 | 2 | `3.95370100` USD | explicit model routing |
| tester | `019fd54f-eb58-7660-a6ed-8796a027af98` (Verifier the 5th) | final focused and full validation; junction coverage passed | gpt-5.6-luna / max | 3202280 | 39 | 0 | `0.14167364` USD | explicit model routing |
| reviewer | `019fd54f-ec3b-7301-a3fc-a6b922003c30` (Sentinel the 5th) | final independent review; only the intentionally open window remains | gpt-5.6-sol / high | 1630877 | 26 | 0 | `1.70578700` USD | explicit model routing |

Summary: agents used: 27; costed agents: 26; historical inherited configuration: 12; explicitly routed roles: 15. One implementer rollout is token-observed but not costed because its classifications are internally inconsistent.

## Custo total da tarefa (histórico M4)

Este total combinado pertence à execução histórica M4 abaixo. Ele não é o
total da execução M5 atual; como um rollout M5 ficou sem estimativa completa,
o combinado M5 permanece indisponível.

- Escopo do total: 27 rollouts de subagentes delegados e 1 janela fechada do chat principal
- Subagentes: 83,644,276 tokens observados; 26 agentes com estimativa; **US$ 16.70554000**
- Chat principal: 66,354,354 tokens observados em 453 chamadas; **US$ 1.71691256**
- Tokens observados no total: 149,998,630
- Custo total combinado equivalente à API: **US$ 18.42245256**
- Base/moeda: `api-equivalent-token-only` / USD
- Exclusões: ferramentas, modalidades, cobrança da assinatura e o rollout separado usado apenas como validação real (`US$ 0.381748`)

## Custo do chat principal

- Arquivo da janela: `specs/agent-runtime-token-cost-evidence/task-window.json`
- Sessão/rollout: `019fd446-85dc-7501-a03a-b9d674b7e9f8` / `rollout-2026-08-05T20-33-39-019fd446-85dc-7501-a03a-b9d674b7e9f8.jsonl`
- Limites observados: `019fd4d3-6dbe-7b22-8895-b87ec3d68858` → `019fd4d3-6dbe-7b22-8895-b87ec3d68858` (`task_complete`)
- Status: `closed` / final
- Modelo observado: `gpt-5.6-luna`
- Uso atribuído à janela: 66.354.354 tokens; 453 chamadas; 3 snapshots estruturais de compactação excluídos; 0 chamadas long-context.
- Custo final equivalente à API: **US$ 1.71691256**
- Base/moeda: `api-equivalent-token-only` / USD
- Exclusões: subagentes, ferramentas, modalidades e cobrança da assinatura

## Residual risks

- Local rollout usage is observable telemetry, not a backend billing ledger.
- The price table requires explicit maintenance from official pricing sources.
- Tool and modality fees are excluded from the token-only estimate.
- Main-chat attribution is final through the closed `task-window.json` histórica M4; o combinado M5 permanece indisponível enquanto houver parcela sem estimativa.
- The direct-symlink variant of AC-519 is skipped on this Windows host because creating that link requires an unavailable privilege; the directory-junction variant executes successfully. This is an environment-specific coverage limitation, not a functional blocker: the implementation resolves every candidate strictly and rejects destinations outside `--sessions-root`.

> The historical M4 aggregates above are preserved unchanged. The following
> section records only the current M5/WP-528 execution and must not be added to
> those historical totals.

## M5 — Current execution evidence (2026-08-07)

### Focused tests

| Command | Result | Scope |
|---|---|---|
| `python -B -m unittest tests.test_agent_evidence tests.test_task_window -v` | 72 focused tests passed; 2 symlink cases skipped by Windows policy | AC-523–AC-525, AC-527–AC-529 |
| `python -B -m unittest tests.test_check_drift tests.test_interface_validation -v` | 22 validator/interface tests passed after correction | AC-526, AC-529 and validator/interface coverage |
| `python -B -m unittest tests.test_agent_evidence tests.test_task_window tests.test_check_drift tests.test_interface_validation -v` | 96 tests passed; 2 symlink cases skipped by Windows policy | final focused gate |
| `python -B -m unittest discover -s tests -p "test_*.py" -v` | 134 tests passed; 2 symlink cases skipped by Windows policy | final full gate |

The first two rows are intermediate implementation/test-engineer evidence;
the last two rows are the final independent results recorded below.

### M5 acceptance traceability

| Criterion | Current evidence | Status |
|---|---|---|
| AC-523 | `tests/test_agent_evidence.py` — exact UUID filename fallback resolves normal model/token/cost evidence | Focused evidence passed |
| AC-524 | `tests/test_agent_evidence.py` — `resolution.fallback_used: true` and `AGENT_ID_FALLBACK` | Focused evidence passed |
| AC-525 | `tests/test_agent_evidence.py` — partial, ambiguous, conflicting metadata and unsafe fallback rejection; RuntimeError containment | Final focused evidence passed; symlink case skipped by host policy |
| AC-526 | `tests/test_check_drift.py` — required closed/matching task-window artifacts, schema/final flags and invalid unavailable cost rejection | Final focused evidence passed |
| AC-527 | `tests/test_task_window.py` — `--final` rejects open windows and writes a closed final report | Focused evidence passed |
| AC-528 | `tests/test_task_window.py` — `main-chat-orchestrator` scope and explicit exclusions | Focused evidence passed |
| AC-529 | `tests/test_check_drift.py` — delegated/main-chat separation and unavailable-cost handling | Focused evidence passed |

Current proof tags: `@spec:AC-523`, `@spec:AC-524`, `@spec:AC-525`, `@spec:AC-526`, `@spec:AC-527`, `@spec:AC-528`, `@spec:AC-529`.

### Main-chat final report

The required lifecycle is `start` → `close` → `report --final --output
task-window-report.json`. The observed final artifact is
`specs/agent-runtime-token-cost-evidence/task-window-report.json`:

- Model: `gpt-5.6-luna`
- Window usage: 66,354,354 tokens
- Requests: 453
- Cost: **US$1.71691256**, API-equivalent token-only estimate
- Scope: `main-chat-orchestrator`
- Explicit exclusions: delegated-agent rollouts, tool fees, modality fees and subscription billing
- State: closed/final; not provisional

### Delegated rollout costs observed in this execution

| Rollout identifier | Role/result | Effective model/effort | Tokens | Requests | Cost/status |
|---|---|---|---:|---:|---|
| `019fdd91` | planner | `gpt-5.6-luna` / `max` | 4,053,637 | 37 | US$0.17304548 — estimated |
| `019fdda2-b084` | implementer | `gpt-5.6-luna` / `max` | 2,056,730 | 27 | US$0.09089372 — estimated |
| `019fdda2-f78` | implementer; duplicate WP-525 | `gpt-5.6-luna` / `max` | 4,867,750 | 48 | US$0.17931032 — estimated |
| `019fddb1` | interrupted implementer; no change | `gpt-5.6-luna` / `max` | 1,089,684 | 18 | US$0.04983712 — estimated |
| `019fddb8` | fallback implementer | `gpt-5.6-terra` / `high` | 635,951 | 14 | US$0.33646720 — estimated |
| `019fddc2` | test engineer | `gpt-5.6-terra` / `high` | 622,025 | 13 | US$0.32775240 — estimated |
| `019fddc5` | validator test engineer | `gpt-5.6-luna` / `max` | 595,264 | 12 | not-available — multiple/unknown observed models |
| `019fddc7` | corrective implementer | `gpt-5.6-terra` / `high` | 246,241 | 7 | US$0.15009080 — estimated |
| `019fddcb` | documentation implementer | `gpt-5.6-luna` / `max` | 2,389,104 | 28 | US$0.10157524 — estimated |
| `019fddd4` | AC-525 test engineer | `gpt-5.6-terra` / `high` | 631,973 | 13 | US$0.33694920 — estimated |
| `019fddd8` | documentation reviewer | `gpt-5.6-luna` / `low` | 460,082 | 12 | US$0.02397560 — estimated |
| `019fdde2` | template correction implementer | `gpt-5.6-luna` / `max` | 529,464 | 12 | US$0.02731720 — estimated |
| `019fddf0-9e6` | agent-evidence safety correction | `gpt-5.6-terra` / `high` | 258,396 | 8 | US$0.15726360 — estimated |
| `019fddf0-b649` | validator safety correction | `gpt-5.6-terra` / `high` | 293,020 | 8 | US$0.16349560 — estimated |
| `019fddf2` | corrective test engineer | `gpt-5.6-terra` / `high` | 431,163 | 10 | US$0.25795840 — estimated |
| `019fddc9` | final verifier | `gpt-5.6-luna` / `max` | 13,139,646 | 128 | not-available — internally inconsistent token classifications |
| `019fdde7` | first reviewer, corrective review | `gpt-5.6-luna` / `max` | 4,998,863 | 55 | not-available — internally inconsistent token classifications |
| `019fddfb` | final reviewer | `gpt-5.6-terra` / `high` | 519,092 | 11 | US$0.29302040 — estimated |

Known estimated delegated subtotal: **US$2.66895228** across 15 costed
rollouts. Three delegated rollouts are `not-available` because their token
classifications were inconsistent or multiple; therefore no combined task
total is declared for this execution. This subtotal includes the final gates;
the historical M4 combined total above remains separate.

### M5 final gate and limitations

Final gate: **PASS**. Verifier, Reviewer and Documentation Reviewer passed.
Focused tests: 96 passed with 2 Windows symlink skips; full discovery: 134
passed with the same 2 skips; `verify_feature.py` recorded 29 criteria with
`passed: true`; `validate_feature.py` passed. The global `check_drift.py`
still reports only pre-existing stale verification maps in three other
features: `agent-runtime-model-evidence`, `mandatory-delegation-contract` and
`validation-performance-refactor`.

`verification.json` was regenerated by `verify_feature.py`. The final report
remains closed and non-provisional. An unavailable delegated cost remains
explicitly marked as such, and the current M5 combined total remains
not-available rather than being recorded as zero.
