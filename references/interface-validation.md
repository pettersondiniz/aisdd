# Interface validation

For changes that affect a user-facing interface, first discover the available validation capabilities. The absence of Playwright does not block AISDD, but limits the evidence that can be claimed.

## Preference order

1. Use `playwright-cli` for repeatable browser flows, observable assertions, screenshots, and traces.
2. Use Playwright MCP when interactive inspection, existing-session state, or live debugging is materially more useful. Use it only when MCP tools are exposed to the runtime.
3. Use the project’s existing Playwright suite or another approved browser tool when the CLI and MCP are unavailable.
4. When no browser validation can run, execute the strongest available validation and record the limitation in `evidence.md`.

Do not use CLI and MCP to duplicate the same scenario. Choose the tool that produces the most reliable evidence at the lowest cost, and record the choice.

## Evidence

Classify interface validation in `evidence.md` as one of:

- `real-browser`: a flow ran using `playwright-cli`, Playwright MCP, or the project's browser suite, with its result and covered criteria recorded;
- `alternative`: another approved browser tool was used;
- `not-run`: no browser tool was available or the environment could not start. Record the reason and residual risk.

Screenshots and traces support evidence, but do not replace assertions about expected behavior or state. Continue mapping automated tests to criteria with `@spec:AC-xxx` when applicable. Never claim `real-browser` without an actual execution.

## Installation

Recommend enabling `playwright-cli` or Playwright MCP for interface work because they increase validation confidence. Never install, enable, or change project configuration automatically; request explicit user authorization.
