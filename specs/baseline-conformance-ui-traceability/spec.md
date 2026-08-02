# Baseline conformance and UI traceability

## Objetivo

Tornar a baseline-conformance uma auditoria documental confiavel e manter rastreabilidade de uso ou nao uso de Impeccable em mudancas de UI.

## Comportamento esperado

A baseline em dry-run identifica um `AGENTS.md` legado como lacuna, sem escrever no projeto. Com confirmacao documental, ela preserva documentacao existente, inventaria codigo e testes, cria um ADR reconstruido e specs pendentes para as lacunas, sem alterar codigo ou testes.

## Regras e invariantes

- `AGENTS.md` atual deve conter os marcadores da triagem obrigatoria; uma frase generica sobre mudancas nao triviais nao basta.
- Follow-ups gerados ficam pendentes ate solicitacao explicita do usuario.
- Impeccable permanece opcional: evidencia de UI deve registrar `used` ou `not-used` com motivo.

## Fora de escopo

- Corrigir o codigo, os testes ou o AGENTS.md legado durante a baseline.
- Tornar Impeccable, Playwright CLI ou Playwright MCP obrigatorios.

## Criterios de aceitacao

- [x] AC-201: O dry-run nao escreve arquivos no projeto.
- [x] AC-202: O apply exige confirmacao explicita de escopo documental.
- [x] AC-203: Um `AGENTS.md` legado sem a triagem obrigatoria aparece como lacuna `agents-guidance`.
- [x] AC-204: O apply preserva codigo e cria manifesto, ADR reconstruido e specs pendentes.

## Decisoes resolvidas

- Baseline detecta conformidade por marcadores obrigatorios, nao apenas pela existencia de `AGENTS.md`.
