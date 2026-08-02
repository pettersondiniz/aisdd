# Evidências: Mandatory AISDD triage template

## Comandos executados

| Comando | Resultado | Quando |
|---|---|---|
| `python scripts/verify_feature.py . specs/mandatory-aisdd-triage-template -- python tests/test_interface_validation.py` | Sucesso: 2 critérios com prova atual | 2026-08-01 |
| `python scripts/validate_feature.py . specs/mandatory-aisdd-triage-template` | Sucesso | 2026-08-01 |
| `python scripts/check_drift.py .` | Sucesso: nenhum drift estrutural ou de rastreabilidade | 2026-08-01 |
| `quick_validate.py` nas cópias do repositório e instalada | Sucesso | 2026-08-01 |
| Comparação SHA-256 do modelo instalado e do repositório | Sucesso: arquivos idênticos | 2026-08-01 |

## Rastreabilidade

| Critério | Implementação | Teste/evidência | Status |
|---|---|---|---|
| AC-001 | `assets/templates/AGENTS.md` | `tests/test_interface_validation.py` (`@spec:AC-001`) | Aprovado |
| AC-002 | `assets/templates/AGENTS.md` | `tests/test_interface_validation.py` (`@spec:AC-002`) | Aprovado |

## Verificação mecânica

Execute `python <skill-dir>/scripts/verify_feature.py <repo> specs/<feature> -- <comando-de-teste>`.
O comando grava `verification.json`; não edite esse arquivo manualmente. Uma prova só é válida
quando o comando terminou com êxito, o teste anotado não está pulado e o mapa de testes não mudou.

## Checks não executados

## Riscos residuais
