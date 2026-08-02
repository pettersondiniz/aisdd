# Evidências: Playwright validation guidance

## Comandos executados

| Comando | Resultado | Quando |
|---|---|---|
| `python C:\\Users\\Usuario\\.codex\\skills\\.system\\skill-creator\\scripts\\quick_validate.py <skill-dir>` | Sucesso nas cópias do repositório e instalada | 2026-08-01 |
| Comparação SHA-256 dos arquivos instalados e rastreados | Sucesso: arquivos alterados idênticos | 2026-08-01 |
| `python scripts/verify_feature.py . specs/playwright-validation-guidance -- python tests/test_interface_validation.py` | Sucesso: 2 critérios com prova atual | 2026-08-01 |
| `python scripts/validate_feature.py . specs/playwright-validation-guidance` | Sucesso | 2026-08-01 |
| `python scripts/check_drift.py .` | Sucesso: nenhum drift estrutural ou de rastreabilidade | 2026-08-01 |

## Rastreabilidade

| Critério | Implementação | Teste/evidência | Status |
|---|---|---|---|
| AC-001 | `SKILL.md` e `references/interface-validation.md` | `tests/test_interface_validation.py` (`@spec:AC-001`) | Aprovado |
| AC-002 | `references/interface-validation.md` | `tests/test_interface_validation.py` (`@spec:AC-002`) | Aprovado |

## Verificação mecânica

Execute `python <skill-dir>/scripts/verify_feature.py <repo> specs/<feature> -- <comando-de-teste>`.
O comando grava `verification.json`; não edite esse arquivo manualmente. Uma prova só é válida
quando o comando terminou com êxito, o teste anotado não está pulado e o mapa de testes não mudou.

## Checks não executados

## Riscos residuais
