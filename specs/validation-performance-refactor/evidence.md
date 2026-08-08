# Evidências: Otimização do fluxo de validação AISDD

## Comandos executados

| Comando | Resultado | Quando |
|---|---|---|
| `python -m unittest discover -s tests -v` | Linha de base: 28 testes passaram | 2026-08-05 |
| `python -m unittest discover -s tests -p "test_check_drift.py" -v` | 5 testes passaram | 2026-08-05 |
| `python -m unittest discover -s tests -v` | 33 testes passaram | 2026-08-05 |
| `python -m compileall -q scripts tests` | Passou | 2026-08-05 |
| `git diff --check` | Passou; apenas avisos de conversão LF/CRLF do Git | 2026-08-05 |
| `python scripts/verify_feature.py . specs/validation-performance-refactor -- python -m unittest discover -s tests -v` | 4 critérios com prova atual | 2026-08-05 |
| `python scripts/validate_feature.py . specs/validation-performance-refactor` | Passou | 2026-08-05 |
| `python scripts/validate_feature.py . specs/agent-runtime-token-cost-evidence` | Passou | 2026-08-05 |
| `python scripts/check_drift.py .` | Resultado histórico anterior ao refresh; o check atual passou após a evidência ser regenerada | 2026-08-05 |
| `python scripts/verify_feature.py . specs/validation-performance-refactor -- python -B -m unittest discover -s tests -q` | 4 critérios com prova atual; 122 testes passaram e 1 foi pulado | 2026-08-07 |
| `python scripts/validate_feature.py . specs/validation-performance-refactor` | Passou após o refresh do mapa de testes | 2026-08-07 |
| `python scripts/check_drift.py .` | Passou: nenhum drift estrutural ou de rastreabilidade | 2026-08-07 |

## Rastreabilidade

| Critério | Implementação | Teste/evidência | Status |
|---|---|---|---|
| AC-601 | `scripts/validate_feature.py` | `tests/test_check_drift.py` (`@spec:AC-601`) | Passou |
| AC-602 | Wrapper CLI de `scripts/validate_feature.py` | `tests/test_check_drift.py` (`@spec:AC-602`) | Passou |
| AC-603 | Cache compartilhado em `scripts/check_drift.py` | `tests/test_check_drift.py` (`@spec:AC-603`) | Passou |
| AC-604 | Regressão do fluxo direto e baseline | `tests/test_check_drift.py` (`@spec:AC-604`) | Passou |

## Verificação mecânica

`verification.json` foi gerado por `scripts/verify_feature.py` e contém o mapa atual dos quatro critérios. Não foi editado manualmente.

## Checks não executados

- Validação da cópia instalada/global: fora do escopo desta tarefa.
- Parecer delegado do reviewer: não retornou antes do encerramento do agente; foi feita revisão local read-only do diff e dos testes.

## Rastreabilidade de agentes

O planner AISDD foi delegado para análise read-only. A configuração efetiva e a telemetria serão consultadas após a conclusão do agente e registradas sem inferências.

| Papel | Agente | Tarefa | Modelo solicitado | Effort solicitado | Modelo efetivo | Effort efetivo | Fonte efetiva | Tokens/categorias observados | Custo API estimado | Fallback | Resultado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| planner | `019fd427-86a8-7091-9aaa-4e6a736ad84b` | Plano read-only e riscos da refatoração | `gpt-5.6-sol` | `high` | unknown | unknown | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | concluído; resultado recebido pelo runtime |
| implementer | `019fd42c-ff8f-7fb1-b321-ec86d9e60ca8` | M2: scripts e teste de regressão | `gpt-5.6-luna` | `max` | unknown | unknown | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | encerrado sem parecer final; alterações observadas e revisadas localmente |
| reviewer | `019fd432-ca5d-7942-949b-36247e293f8f` | Revisão read-only de regressões e contratos | `gpt-5.6-sol` | `high` | unknown | unknown | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | encerrado sem parecer; revisão local realizada |

Resumo: agentes usados: 3; fallbacks: 0. A telemetria local não foi localizada para nenhum agente; nenhum modelo, effort, token ou custo efetivo foi inferido além do solicitado no spawn.

## Riscos residuais

- A falha histórica de `agent-runtime-model-evidence/verification.json` foi registrada antes do refresh; o check atual passou e não há drift estrutural aberto nesta rodada.
- O ganho de desempenho não será medido por benchmark; a prova será comportamental, verificando chamadas únicas e reutilização do objeto.
