# Evidências: Interactive model routing

## Comandos executados

| Comando | Resultado | Quando |
|---|---|---|
| `python scripts/verify_feature.py . specs/interactive-model-routing -- python tests/test_interface_validation.py` | Sucesso: 3 critérios com prova atual | 2026-08-02 |
| `python scripts/validate_feature.py . specs/interactive-model-routing` | Sucesso | 2026-08-02 |
| `python scripts/check_drift.py .` | Sucesso: nenhum drift estrutural ou de rastreabilidade | 2026-08-02 |
| Execução na cópia instalada com modelos dedicados simulados | Sucesso: sugestões e fallback de herança retornados | 2026-08-02 |

## Rastreabilidade

| Critério | Implementação | Teste/evidência | Status |
|---|---|---|---|
| AC-101 | roteador e mapeamento de faixas | `tests/test_interface_validation.py` (`@spec:AC-101`) | Aprovado |
| AC-102 | fallback | `tests/test_interface_validation.py` (`@spec:AC-102`) | Aprovado |
| AC-103 | consulta somente-leitura | `tests/test_interface_validation.py` (`@spec:AC-103`) | Aprovado |

## Verificação mecânica

Execute `python <skill-dir>/scripts/verify_feature.py <repo> specs/<feature> -- <comando-de-teste>`.
O comando grava `verification.json`; não edite esse arquivo manualmente. Uma prova só é válida
quando o comando terminou com êxito, o teste anotado não está pulado e o mapa de testes não mudou.

## Checks não executados

## Riscos residuais
