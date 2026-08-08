# Evidências: Contrato obrigatório de delegação AISDD

## Escopo normativo atual — M8

- Esta feature permanece explicitamente em contrato v1 por decisão registrada;
  a mudança não a migra para v2.
- Novas specs são criadas em v2 por padrão pelo `scripts/create_feature.py`,
  com marcador e esqueletos JSON. Specs existentes/legadas sem marcador e
  specs criadas explicitamente com `--contract v1` permanecem em compatibilidade
  v1, sem exigir `work-packages.json` ou `delegation-evidence.json`.
- A regra do detector/validador permanece estrita: somente um marcador v2
  válido exige os artefatos v2; não há migração automática.
- Rodada independente final do Test Engineer: agente `019fdcbf-adca-75c0-bf7e-fe47a271bbf8`, `agent_type=tester`, com 122 testes aprovados, 1 skip e probes M8 PASS. O resultado é evidência do Test Engineer v1 e não é Verifier.
- A tentativa de spawn da role canônica `verifier` retornou `unknown agent_type 'verifier'`.
- O fallback local foi autorizado e auditado no escopo do projeto. Ele executou os comandos oficiais abaixo, todos com resultado OK:
  `python scripts/verify_feature.py . specs/mandatory-delegation-contract -- python -B -m unittest discover -s tests -q`,
  `python scripts/validate_feature.py . specs/mandatory-delegation-contract` e
  `python scripts/check_drift.py .`.
- `verification.json` foi regenerado pelo fluxo oficial, não editado manualmente.
  Essa execução não é sign-off canônico de Verifier; a indisponibilidade da role
  e o fallback auditado permanecem limitações explícitas.

## Execução final pós-M8

- Estado: `Completion`/feature fechada para M8; evidência oficial, validação da
  feature e drift passaram.
- Ownership: Test Engineer independente (`agent_type=tester`) separado do
  fallback local de Verifier; nenhum resultado foi inferido por nickname, modelo
  ou capability.
- Próxima transição: nenhuma para M8. Uma execução canônica de `verifier`, se
  disponibilizada posteriormente, seria uma validação independente adicional,
  não uma reescrita dos registros abaixo.

## Registro histórico — Completion pós-WP-731/731A

- Cadeia normativa única atual: `WP-727A/B Implementers (concluídos) → WP-728 Test Engineer v1 (concluído: 41 focados/122 amplos/1 skip) → WP-729 Implementer documental (concluído) → WP-730F fallback local auditável (concluído) → (WP-731 Reviewer || WP-731A Documentation Reviewer, concluídos)`.
- `WP-714/T-714`: correção funcional concluída e registrada; os checks focados do Implementer não são validação final.
- `WP-715/T-715`: rodada independente do Test Engineer v1 concluída com 114 testes e 1 skip. O resultado não é prova do Verifier, não marca ACs como concluídos e não fecha a feature. O motivo do skip não é inferido nesta reconciliação.
- `WP-718/T-718`: reconciliação final de documentação/coordenação aplicada pelo Implementer owner; não renumera nem substitui os WPs atuais.
- `WP-727A/B`: correções fail-closed de fallback read-only e estado aberto do `plan.md`, aplicadas em escopos de arquivo separados.
- `WP-728/T-728`: rodada independente do Test Engineer v1 com 41 testes focados e 122 amplos, 1 skip e nenhuma falha/erro.
- `WP-729/T-729`: referências e template alinhados ao escopo `write/read/execute/forbidden` e aos comandos relativos da skill.
- `WP-730F`: `verify_feature.py` regenerou `verification.json` atual com 11 critérios; a suíte executou 122 testes, com 1 skip e nenhuma falha/erro. A mesma evidência foi regenerada pela feature legada `validation-performance-refactor` com 4 critérios, 122 testes, 1 skip e nenhuma falha/erro.
- `validate_feature.py` e `check_drift.py` foram reexecutados após o fechamento dos WPs de revisão e passaram; o `plan.md` vigente não possui estado aberto.
- `WP-731/T-731` e `WP-731A/T-731A` concluíram em paralelo após a evidência atual: Reviewer sem blockers técnicos e Documentation Reviewer sem drift novo.
- Check documental direto do WP-718: sucesso; marcador literal em uma linha, ausência de `--skill-dir`, regra de fence/linha/token no SKILL/ADR, cadeia atual, rótulos históricos e drift cross-feature foram conferidos.
- `git diff --check` do WP-718: sucesso; nenhum erro de whitespace, apenas avisos normais de conversão LF/CRLF do Git.
- Descoberta: a primeira tentativa do probe documental via wrapper recodificou Unicode e foi descartada; a repetição direta com comparações literais passou.

## Registros históricos de checks

As entradas abaixo são registros históricos de milestones e checks anteriores. Elas não substituem o resultado atual do WP-715 nem a validação independente do WP-716. Registros de cadeias antigas e a alegação 29/30 estão rotulados como históricos/superseded.

| Comando | Resultado | Quando |
|---|---|---|
| `python scripts/model_routing.py --role planner --class T3 --json` | Executado; configuração global não expôs disponibilidade e retornou fallback de herança | 2026-08-07 |
| `python scripts/model_routing.py --role architect --class T3 --json` | Falhou no estado inicial porque a configuração global não tinha a role; gap será tratado localmente | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_contract.DelegationContractTests.test_capability_matrix_and_distinct_test_roles_are_present -v` (checagem focada M1) | Sucesso: matriz, alias histórico e roles canônicas locais foram verificados; instalação global não foi tocada | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_contract -v` | Sucesso: 3 testes focados de grafo, v1/v2 opt-in, role coverage, independência e fallback | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_contract tests.test_check_drift -v` | Sucesso: 8 testes; integração não alterou o contrato v1 | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_routing tests.test_interface_validation -v` | Sucesso: 15 testes de roteamento, alias, fallback somente leitura e compatibilidade existente | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_contract tests.test_delegation_routing tests.test_interface_validation -v` | Sucesso: 23 testes focados relevantes ao WP-702 | 2026-08-07 |
| `python -B -m py_compile scripts/delegation_contract.py scripts/model_routing.py scripts/validate_feature.py tests/test_delegation_contract.py tests/test_delegation_routing.py` | Sucesso: módulos e testes compilam | 2026-08-07 |
| `python -B -m py_compile scripts/delegation_contract.py scripts/model_routing.py scripts/create_feature.py scripts/validate_feature.py tests/test_delegation_contract.py tests/test_delegation_routing.py` | Sucesso final: scripts e testes afetados compilam | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_contract tests.test_delegation_routing tests.test_interface_validation -v` | Falhou inicialmente em uma asserção documental; após ajuste da asserção, uma segunda execução ainda encontrou uma asserção de idioma; nenhum blocker funcional foi indicado | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_contract tests.test_delegation_routing tests.test_interface_validation -v` | Sucesso final: 26 testes focados, incluindo os negativos de WP-706 | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_contract tests.test_delegation_routing tests.test_interface_validation -v` | Sucesso na rodada final após o ajuste documental: 26 testes focados | 2026-08-07 |
| `python -B -m py_compile scripts/delegation_contract.py scripts/model_routing.py scripts/validate_feature.py` | Sucesso no WP-707 | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_routing tests.test_interface_validation -v` | Sucesso: 16 testes focados de roteamento, compatibilidade, baseline e guidance | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_contract.DelegationContractTests.test_skill_and_contract_protect_delegable_orchestrator_capabilities tests.test_delegation_contract.DelegationContractTests.test_capability_matrix_and_distinct_test_roles_are_present tests.test_delegation_contract.DelegationContractTests.test_planner_contract_declares_technical_and_execution_plans tests.test_delegation_contract.DelegationContractTests.test_contract_documents_correction_loop_and_fail_closed_completion tests.test_delegation_contract.DelegationContractTests.test_adr_readme_and_templates_record_v1_v2_migration tests.test_delegation_contract.DelegationContractTests.test_create_feature_defaults_to_v2_and_explicit_v1_is_legacy_compatible -v` | Sucesso: 6 testes focados de documentação, matriz, scaffold e compatibilidade v1 | 2026-08-07 |
| `git diff --check` | Sucesso; somente avisos de conversão LF/CRLF do Git | 2026-08-07 |
| `git diff --check` (WP-710) | Sucesso; nenhum erro de whitespace; somente avisos normais de conversão LF/CRLF do Git | 2026-08-07 |
| `git diff --check` (WP-710 final) | Sucesso; nenhum erro de whitespace; somente avisos normais de conversão LF/CRLF | 2026-08-07 |
| probe PowerShell de documentação do WP-710 | Sucesso: 21 invariantes documentais conferidos e `specs/mandatory-delegation-contract/verification.json` ausente | 2026-08-07 |
| `python scripts/validate_feature.py . specs/validation-performance-refactor` | Resultado histórico anterior ao refresh; o fluxo próprio foi executado novamente e o estado atual passou | 2026-08-07 |
| `python scripts/model_routing.py --config assets/templates/model-routing.toml --role tester --json` | Sucesso; `tester` resolve para `test-engineer` e não é remapeado por configuração | 2026-08-07 |
| `python -B -m py_compile scripts/delegation_contract.py scripts/validate_feature.py` | Sucesso no WP-708; scripts afetados compilam | 2026-08-07 |
| `git diff --check` | Sucesso; apenas avisos de conversão LF/CRLF do Git | 2026-08-07 |
| probe Python não autoritativo de fallback/T0/`has_open_status` | Sucesso: declaração limpa aceita, conteúdo incompatível rejeitado, T0 coordinate-only rejeitado, declaração mecânica aprovada aceita, histórico ignorado e estado atual aberto preservado; nenhuma suíte executada | 2026-08-07 |
| `python -B -m unittest` com 5 testes focados de contrato/documentação/v1 | Sucesso: compatibilidade v1, Planner, fallback e ordem documental verificadas; check não substitui Verifier e suíte ampla não executada | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_contract tests.test_check_drift -v` | Sucesso: 24 testes focados passaram; check não substitui Test Engineer/Verifier e a suíte ampla não foi executada | 2026-08-07 |
| `python -B -m py_compile scripts/delegation_contract.py scripts/validate_feature.py` | Sucesso: scripts afetados compilam | 2026-08-07 |
| probe Python inline do WP-709 | Sucesso: fallback ausente/incompatível rejeitado, fallback limpo aceito, role explícita, dependências mínimas, Planner/Architect paralelo, WP corretivo, glob conservador e estados estruturados verificados | 2026-08-07 |
| smoke probe final do WP-709 | Sucesso: marcador/título documental, estado estruturado, frase normal fora de campo, role explícita e conflito glob conservador verificados | 2026-08-07 |
| `git diff --check` | Sucesso; apenas avisos normais de conversão LF/CRLF do Git | 2026-08-07 |
| `git diff --check` (WP-713 coordenação/documentação; registro histórico/superseded) | HISTÓRICO/SUPERSEDED: sucesso; nenhum erro de whitespace; somente avisos normais de conversão LF/CRLF do Git | 2026-08-07 |
| probe PowerShell read-only de coordenação/documentação do WP-713 (registro histórico/superseded) | HISTÓRICO/SUPERSEDED: registrava a cadeia antiga WP-713 → WP-714 → (WP-715 || WP-715A); não é a cadeia normativa atual | 2026-08-07 |
| `python -B -m py_compile scripts/delegation_contract.py scripts/validate_feature.py` (WP-714) | Sucesso: scripts afetados compilam; `verify_feature.py` não foi executado | 2026-08-07 |
| probe Python inline do WP-714 | Sucesso: globos `src/a?.py`/`src/ab*.py` e classes `[ab]`/`[bc]` conflitam; fence não ativa v2; capability mínima e dependência escalar são validadas; T0 trivial/silencioso/ausente é rejeitado; headings, seções, histórico e tabelas de status foram verificados | 2026-08-07 |
| `python -B -m unittest tests.test_delegation_contract tests.test_check_drift -v` (registro histórico/superseded) | HISTÓRICO/SUPERSEDED: alegação 29/30 da rodada anterior; uma asserção documental apontava o marcador canônico quebrado em duas linhas. Não é resultado atual nem substitui WP-715 (114 testes/1 skip) ou WP-716 | 2026-08-07 |
| testes focados de contrato/status (6 casos existentes) | Sucesso: grafo/glob, opt-in v1/v2, aliases, T0, razões triviais e histórico/status passaram; não substitui Test Engineer ou Verifier | 2026-08-07 |
| `git diff --check` (WP-714) | Sucesso; somente avisos normais de conversão LF/CRLF do Git | 2026-08-07 |

Os 26 testes registrados antes desta correção são evidência histórica do
WP-706, não prova atual do contrato v2 endurecido. Os fixtures/testes do WP-703
agora estão rastreados nesta feature; o registro de falha esperada dos fixtures
foi removido da evidência corrente. Esse rastreamento não é aprovação do Verifier;
os testes do Test Engineer estão presentes no workspace/change set e nenhum
arquivo de teste foi alterado no WP-708 ou WP-709.

## Rastreabilidade

| Critério | Implementação | Teste/evidência | Status |
|---|---|---|---|
| AC-701 | `SKILL.md`, `references/agent-routing.md`, `references/lifecycle.md` | `tests/test_delegation_contract.py` (`@spec:AC-701`) | Prova atual em `verification.json`; revisão final concluída |
| AC-702 | `agents/planner.toml`, `references/exec-plan-standard.md` | `tests/test_delegation_contract.py` (`@spec:AC-702`) | Prova atual em `verification.json`; revisão final concluída |
| AC-703 | `references/role-capabilities.md`, agents | `tests/test_delegation_contract.py` (`@spec:AC-703`) | Prova atual em `verification.json`; revisão final concluída |
| AC-704 | `scripts/delegation_contract.py` | `tests/test_delegation_contract.py` (`@spec:AC-704`); probe WP-714 não autoritativo | Prova atual em `verification.json`; revisão final concluída |
| AC-705 | `scripts/create_feature.py`, `scripts/validate_feature.py`, `scripts/delegation_contract.py` | `tests/test_delegation_contract.py` (`@spec:AC-705`); probe WP-714 não autoritativo | Prova atual em `verification.json`; revisão final concluída |
| AC-706 | `scripts/delegation_contract.py` | `tests/test_delegation_contract.py` (`@spec:AC-706`); probe WP-714 não autoritativo | Prova atual em `verification.json`; revisão final concluída |
| AC-707 | `scripts/model_routing.py`, `scripts/delegation_contract.py` | `tests/test_delegation_routing.py`, `tests/test_delegation_contract.py` (`@spec:AC-707`) | Prova atual em `verification.json`; revisão final concluída |
| AC-708 | `scripts/model_routing.py`, agents | `tests/test_delegation_routing.py` (`@spec:AC-708`) | Prova atual em `verification.json`; revisão final concluída |
| AC-709 | `references/delegation-contract.md`, `SKILL.md` | `tests/test_delegation_contract.py` (`@spec:AC-709`) | Prova atual em `verification.json`; revisão final concluída |
| AC-710 | scripts somente leitura/global fallback | `tests/test_delegation_routing.py` (`@spec:AC-710`) | Prova atual em `verification.json`; revisão final concluída |
| AC-711 | ADR, README, templates e plan v1 | `tests/test_delegation_contract.py` (`@spec:AC-711`) | Prova atual em `verification.json`; revisão final concluída |

## Verificação mecânica

Na rodada atual WP-730F, os comandos oficiais foram executados pelo fallback local auditado:

```text
python scripts/verify_feature.py . specs/mandatory-delegation-contract -- python -B -m unittest discover -s tests -q
python scripts/validate_feature.py . specs/mandatory-delegation-contract
python scripts/check_drift.py .
```

- Resultado atual: `verify_feature.py` OK (11 critérios, 122 testes, 1 skip); `validate_feature.py` OK; `check_drift.py` OK, sem drift estrutural ou de rastreabilidade.

## Checks não executados

- Integração com executor externo de agentes: fora do escopo e inexistente no repositório.
- Instalação global: deliberadamente não alterada.
- Validação em projeto consumidor: será feita quando a versão local for aprovada.
- Não há `AGENTS.md` na raiz deste workspace; apenas o template `assets/templates/AGENTS.md` existe.
- A role canônica `verifier` não foi exposta nesta sessão; as demais etapas foram delegadas aos owners registrados e o único trabalho direto foi o fallback WP-730F, auditado abaixo.
- Na rodada histórica WP-725F, `verify_feature.py` gerou `verification.json` com 11 critérios atuais, `validate_feature.py` passou após o fechamento do status de handoff e `check_drift.py` passou depois do refresh próprio de `validation-performance-refactor`.
- Na rodada vigente WP-730F, `verify_feature.py` regenerou novamente a evidência após WP-727A/B e WP-728; a validação de plan/status e o drift foram repetidos após os gates WP-731/731A e passaram. `verification.json` nunca é editado manualmente.

## Histórico de registros de WPs anteriores

## Fallback auditado da execução anterior (WP-706)

- Aprovação: pedido explícito do usuário para executar WP-706/T-706 e cobrir os blockers com testes.
- Role/agente indisponível: não há API de subagentes executável exposta nesta sessão; `ALL_TOOLS` não contém ferramenta de spawn/agent.
- Tentativas: consulta das ferramentas disponíveis e uso do escopo local; nenhuma instalação global, sessão ou projeto consumidor foi usado como alternativa.
- Escopo direto: `SKILL.md`, `README.md`, `agents/`, `assets/templates/`, `docs/architecture/decisions/`, `references/`, `scripts/`, `specs/mandatory-delegation-contract/` e `tests/test_delegation_contract.py`/`tests/test_delegation_routing.py`.
- Resultado observado: enforcement, scaffold, CLI, roteamento, documentação e testes focados corrigidos; 26 testes focados e `py_compile` passaram na última execução registrada.

## Registro do WP-707

- Owner: Implementer, conforme pedido explícito do usuário; execução limitada aos arquivos aprovados e sem editar `tests/`.
- API de subagentes/executor externo: não exposta nesta sessão; não foi inventada integração nem capability.
- Instalação global, sessões do runtime e projetos consumidores: não alterados.
- Resultado parcial: implementação e documentação corrigidas; checks rápidos registrados acima; Test Engineer, Verifier, Reviewer e Documentation Reviewer ainda precisam executar seus WPs independentes.

## Registro do WP-708

- Owner: Implementer, conforme correção exigida pelo Reviewer; escopo limitado aos scripts, referências, templates, ADR e status/evidence aprovados.
- Resultado parcial: enforcement de `fallback.used:false`, semântica T0 v2, filtro de histórico em `has_open_status`, fronteira v1/v2 e ordem `Verifier → (Reviewer || Documentation Reviewer)` atualizados.
- Restrições observadas: `tests/` não foi editado, `verification.json` não foi criado/editado, e nenhum gate foi marcado como concluído antes do Verifier.

## Registro do WP-709

- Owner: Implementer, conforme pedido explícito do usuário; milestone único e escopo limitado a scripts, documentação/configuração e artefatos de coordenação.
- Resultado parcial: fallback v2 obrigatório e explícito, role de WP sem inferência de `owner.role`, dependências mínimas após normalização, glob fail-closed, `has_open_status` estruturado, Planner/grafo T1+ v1 e gatilhos de Documentation Reviewer alinhados.
- Testes do Test Engineer: presentes no workspace/change set e rastreados como pré-requisito; não foram tratados como execução de Verifier.
- Restrições observadas: `tests/` não foi editado, `verification.json` não foi criado/editado, instalação global/runtime externo não foram alterados e nenhum gate foi marcado como concluído.

## Registro do WP-710

- Owner: Implementer, conforme pedido explícito do usuário; milestone único e escopo limitado à correção documental aprovada.
- Revisão que originou o WP: Documentation Reviewer exigiu alinhamento do gate T2/T3/T4, do loop de correção do Test Engineer, da fonte normativa do grafo v1 e da documentação dos aliases do detector v2.
- Resultado parcial: README, SKILL, classification, role-capabilities, completion-standard, ADR, agent-routing, lifecycle, delegation-contract, exec-plan-standard, templates, Planner, Implementer e os artefatos desta feature foram alinhados.
- Restrições observadas: `tests/` não foi editado, `verification.json` não foi criado/editado, scripts não foram alterados e nenhum gate independente foi marcado como concluído.
- Próximo gate: Test Engineer/Verifier; por esta feature ser T3 e ter impacto documental, Reviewer e Documentation Reviewer são obrigatórios após o Verifier e podem executar em paralelo quando independentes.

## Registro do WP-711

- Owner: Implementer, conforme pedido explícito do usuário; a correção de implementação ficou limitada a `scripts/validate_feature.py`.
- Test Engineer: o teste regressivo existente em `tests/test_check_drift.py` foi revisado e não foi editado.
- `python -B -m py_compile scripts/validate_feature.py`: sucesso.
- `python -B -m unittest tests.test_check_drift.CheckDriftTests.test_v1_status_ignores_historical_open_entries_but_rejects_current_pending -v`: sucesso; check focado não substitui o Verifier.
- Probe Python não autoritativo: sucesso em 7 casos, cobrindo `Status`/`STATE`/`Estado atual`, `pending`/`failed`/`open`, capitalização, acentos, histórico, tabela concluída e frase livre.
- Descoberta: o primeiro probe com literais Unicode sofreu conversão do shell para `?`; ele foi repetido com escapes Unicode antes de registrar o resultado.
- `verify_feature.py`: não executado conforme solicitado. `tests/` e `verification.json` não foram alterados nesta rodada.
- Estado de coordenação: WP-711/T-711 concluído como implementação; os gates independentes permanecem pendentes.

## Registro do WP-712

- Owner: Implementer, conforme pedido explícito do usuário; milestone único e escopo limitado a `scripts/delegation_contract.py` e aos artefatos de coordenação desta feature.
- Alteração observada: `CONTRACT_MARKERS` ficou ancorado a uma linha própria, aceita o prefixo de lista Markdown documentado, preserva aliases case-insensitive com `2`/`v2` e rejeita conteúdo após a versão.
- `python -B -m py_compile scripts/delegation_contract.py`: sucesso.
- Probe Python não autoritativo: sucesso em 4 marcadores válidos e 5 casos de fallback v1, cobrindo casefold, lista Markdown, alias numérico, `v2 extra`, `v2.0`, pontuação final e texto adicional.
- `python -B -m unittest tests.test_delegation_contract.DelegationContractTests.test_v1_does_not_require_v2_artifacts_and_v2_is_opt_in tests.test_delegation_contract.DelegationContractTests.test_v2_marker_aliases_are_line_scoped_and_opt_in -v`: sucesso em 2 testes existentes; os testes não foram editados e o resultado não substitui os gates independentes.
- `verify_feature.py`: não executado conforme solicitado. `tests/` não foi editado, `verification.json` não foi criado/editado, a instalação global não foi alterada e os gates independentes continuam pendentes.
- Estado de coordenação: WP-712/T-712 concluído como implementação; o antigo WP-713/T-713 foi superseded por WP-715/T-715 e não é etapa vigente.

## Registro histórico/superseded do WP-713 — coordenação/documentação

- A correção de coordenação/documentação antiga foi aplicada pelo Implementer owner, mas a cadeia WP-713 → WP-714 → (WP-715 || WP-715A) foi superseded e não é normativa.
- No registro histórico, WP-713/T-713 era a rodada final do tester/Test Engineer v1 e WP-714/T-714 aparecia como Verifier; ambos são apenas históricos. WP-715A/T-715A também não é o reviewer atual.
- Esta rodada histórica não editou `tests/`, não criou/editou `verification.json`, não executou `verify_feature.py`, não alterou instalação global e não marcou ACs ou gates como concluídos.

## Registro do WP-714 — correção funcional exigida pelo Reviewer

- Owner: Implementer, conforme pedido explícito do usuário; milestone único e escopo limitado aos dois scripts afetados e aos artefatos de coordenação desta feature.
- Resultado concluído: `_paths_overlap` conflita conservadoramente em prefixes parciais e globos no mesmo diretório; fences Markdown são ignorados pelo detector v2; cada role operacional exige capability mínima; T0 rejeita aprovação falsa, justificativa ausente ou trivial/silenciosa com normalização sem acentos; `has_open_status` reconhece headings de fase/bloqueios, conteúdo aberto de seções e tabelas case-insensitive; `depends_on`, `depends-on` e `dependencies` escalares são rejeitados.
- `python -B -m py_compile scripts/delegation_contract.py scripts/validate_feature.py`: sucesso.
- Probe Python não autoritativo: sucesso nos exemplos de glob, fence dentro/fora, capabilities adicionais versus `inspect` isolado, dependência escalar, razões T0 triviais/silenciosas/ausentes e headings/seções/histórico/tabelas de status.
- Restrições observadas: `tests/` não foi editado, `verification.json` não foi criado/editado, `verify_feature.py` não foi executado, instalação global/runtime externo não foram alterados e nenhum AC ou gate foi marcado como concluído.
- Naquela etapa histórica, a cadeia projetada após WP-715 era WP-716/T-716 Verifier → (WP-717/T-717 Reviewer || WP-717A/T-717A Documentation Reviewer); ela foi superseded por WP-727A/B → WP-730F → (WP-731 || WP-731A).

## Registro do WP-715 — Test Engineer v1

- Owner: tester / Test Engineer v1; rodada independente concluída após WP-714.
- Resultado atual reportado: 114 testes executados e 1 skip. O resultado permanece limitado ao Test Engineer; não é validação final, não conclui ACs e não fecha a feature. O motivo do skip não é inferido nesta reconciliação.
- Estado histórico: WP-715/T-715 concluído; a projeção WP-716/T-716 e WP-717/T-717A foi substituída pela cadeia vigente.

## Registro do WP-718 — reconciliação final de documentação/coordenação

- Owner: Implementer; milestone único executado no escopo aprovado.
- `plan.md`, `status.md` e este `evidence.md` foram sincronizados para a cadeia vigente; WP-713 e o WP-714 histórico de Verifier foram rotulados como históricos/superseded sem duplicar WP-714 Implementer, WP-715, WP-716, WP-717 ou WP-717A.
- `SKILL.md` mantém o marcador literal `Contrato AISDD da feature: v2` em uma única linha, remove a instrução inválida `--skill-dir` e documenta execução a partir do diretório da skill. SKILL/ADR registram linha própria, token terminal `v2`/`2`, fences ignoradas e fallback v1.
- `tests/` não foi editado, `verification.json` não foi criado/editado, `verify_feature.py`, `validate_feature.py` e `check_drift.py` não foram executados e a instalação global não foi alterada.

`plan.md` é a fonte normativa do grafo declarativo v1. Esta evidência apenas
resume owners/dependências e registra provas; não redefine o grafo.

## Histórico: WPs-719 a 724 — endurecimento e Test Engineer

- WP-719A foi aplicado pelo Implementer owner somente em `scripts/delegation_contract.py`: razões genéricas de T0/fallback, fences Markdown `~~~`/blocos indentados, classe em histórico/fence e aliases escalares/ambíguos de dependência passaram a falhar fechados.
- WP-719B foi aplicado pelo Implementer owner somente em `scripts/validate_feature.py`: seções atuais `Fase atual` e `Bloqueios` passaram a ser reconhecidas, preservando histórico, fences, tabelas casefold e estados fechados.
- WP-720R/T-720R foi executado pelo Test Engineer v1; adicionou regressivos em `tests/test_delegation_contract.py` e `tests/test_check_drift.py`. A primeira rodada focal registrou 37 testes, 36 passagens e 1 falha textual da SKILL; o achado retornou ao Orchestrator e abriu WP-721.
- WP-721 e WP-723 foram aplicados por Implementer owner somente em `SKILL.md` para alinhar a frase canônica do marcador. WP-722 foi uma rerodada focal que repetiu a divergência de pontuação antes de WP-723.
- WP-724/T-724 foi executado pelo Test Engineer v1 em modo read-only: 37 testes focados passaram, 118 testes amplos passaram e 1 teste foi pulado; não houve falhas ou erros. O nickname `Verifier` desse agente não altera seu `agent_type`, que foi `tester`, e nenhum sign-off de Verifier foi atribuído.
- Nenhuma etapa acima criou/editou `verification.json`, executou `verify_feature.py`, `validate_feature.py` ou `check_drift.py` como gate final; nenhuma alterou a instalação global.

## Registro dos WPs-727 a 729 — correções dos reviewers

- WP-727A foi aplicado pelo Implementer owner somente em `scripts/delegation_contract.py`: `scope.read`/`scope.execute` passaram a ser escopos v2 opcionais e explícitos; fallback de role read-only exige `direct_work.operation` `read` ou `execute`, não permite escrita e confere `forbidden`. Fallback de Implementer com `scope.write` permanece compatível.
- WP-727B foi aplicado pelo Implementer owner somente em `scripts/validate_feature.py`: `validate_feature` agora também rejeita estado aberto estruturado em `plan.md`, preservando histórico, fences e estados fechados.
- WP-728/T-728 foi executado pelo Test Engineer v1: 41 testes focados e 122 testes amplos passaram, com 1 skip; os testes cobrem fallback read-only, fallback de Implementer e plan aberto/fechado.
- WP-729 foi aplicado pelo Implementer owner em `references/delegation-contract.md` e `assets/templates/evidence.md`: schema `write/read/execute/forbidden`, operação read-only, distinção tester/verifier e comandos relativos ao diretório da skill foram documentados.
- Os WPs acima não criaram/editaram `verification.json`, não executaram os gates finais e não alteraram a instalação global.

## Tentativa e fallback do WP-730F (WP-725F histórico)

- Tentativa de delegação: `multi_agent_v1__spawn_agent(agent_type="verifier")` retornou `unknown agent_type 'verifier'`. O runtime expõe `tester`, mas não expõe a role canônica Verifier; nickname, modelo ou resultado do Test Engineer não foram usados como inferência de capability.
- Aprovação do fallback: o usuário autorizou a alteração somente dentro de `D:\codex\aisdd` e pediu a conclusão da mudança; essa autorização é registrada como aprovação do fallback local restrito, sem alterar a instalação global.
- Motivo: indisponibilidade objetiva da role canônica necessária para executar os comandos oficiais de completion.
- Agente indisponível: `verifier` não aceito pelo runtime (`unknown agent_type 'verifier'`).
- Tentativas: delegação direta à role `verifier`; o Test Engineer v1 foi executado separadamente para a suíte, mas não foi contado como Verifier.
- Trabalho direto autorizado: executar somente `scripts/verify_feature.py`, `scripts/validate_feature.py` e `scripts/check_drift.py`, gerar/atualizar evidência dentro das features afetadas e registrar o resultado; o refresh de `specs/validation-performance-refactor/verification.json` é evidência legada gerada pelo próprio fluxo porque o check de drift o exigiu; não editar código/testes/specs, não corrigir drift fora do fluxo próprio e não tocar `C:\Users\Usuario\.agents\skills\aisdd`.

## Registro de conclusão dos gates WP-731/731A

- WP-731/T-731 Reviewer (`019fdc5a-63b6-7ff0-93fc-e44dc7aa8472`) inspecionou read-only o código/contrato após WP-727A/B e não encontrou blockers técnicos.
- WP-731A/T-731A Documentation Reviewer (`019fdc5a-6494-7cd3-b26d-1cc09f306a31`) identificou deriva histórica; a coordenação a reconciliou em `plan.md`, `status.md`, `evidence.md` e nos artefatos legados. A confirmação posterior (`019fdc70-662e-7481-a90c-bed6c026859d`) não encontrou novos problemas semânticos; a única condição restante era fechar os estados, agora concluídos.
- Após o fechamento, `validate_feature.py` e `check_drift.py` passaram. A feature está em Completion sob contrato v1, com o fallback local explicitamente qualificado e sem sign-off canônico de Verifier.

## Blocker e drift fora desta feature

- `baseline-conformance-ui-traceability`: a alegação de blocker não foi confirmada nesta rodada. Se preexistente, permanece separada e será verificada pelo fluxo próprio; nenhum check foi ocultado, removido ou convertido em aprovação.
- `validation-performance-refactor`: o `verification.json` foi regenerado pelo fluxo próprio após o primeiro `check_drift.py` apontar mapa de testes obsoleto; `validate_feature.py` passou e o check final retornou `OK: nenhum drift estrutural ou de rastreabilidade encontrado`. Continua sendo evidência da feature legada, não baseline nem evidência desta feature; não houve alteração de código/spec nem migração para v2.

## Rastreabilidade de agentes

| Papel | Agente | Tarefa | Modelo solicitado | Effort solicitado | Modelo efetivo | Effort efetivo | Fonte efetiva | Tokens/categorias observados | Custo API estimado | Fallback | Resultado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| planner | `019fdac2-52d9-7fc2-b546-d337daba702b` | análise read-only, plano e migração v1/v2 | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | concluído |
| architect | `019fdac2-5399-76a1-b42d-5548315fe5e3` | invariantes, schema, ownership e ADRs | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | concluído |
| implementer | `019fdc06-ad15-7f90-bd44-6d5055f999fb` | WP-718, reconciliação documental | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | concluído |
| implementer | `019fdc17-0a97-7102-980d-5b9b6d5e2426` | WP-719A, detector/classe/dependências | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | concluído |
| implementer | `019fdc17-0b68-7911-a6c1-560a2b487c03` | WP-719B, parser de status | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | concluído |
| tester | `019fdc4a-96b7-7a82-bf13-a31f8e1b97d0` | WP-728, regressivos e suíte independente | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | concluído |
| tester | `019fdcbf-adca-75c0-bf7e-fe47a271bbf8` | M8, rodada independente final (agent_type=tester), 122 pass/1 skip e probes M8 | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | 122 pass, 1 skip; probes M8 PASS | não disponível | não aplicado | concluído; não é Verifier |
| implementer | `019fdc50-6671-7ae0-b330-3d2dc2faa879` | WP-729, referências e templates | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | concluído |
| reviewer | `019fdc5a-63b6-7ff0-93fc-e44dc7aa8472` | WP-731, revisão de código/contrato | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | concluído; zero blockers técnicos |
| documentation-reviewer | `019fdc5a-6494-7cd3-b26d-1cc09f306a31` | WP-731A, revisão documental | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | concluído após reconciliação |
| documentation-reviewer | `019fdc70-662e-7481-a90c-bed6c026859d` | confirmação documental final | inherit | inherit | desconhecido | desconhecido | `agent_evidence.py: not-found` | não expostos | não disponível | não aplicado | confirmação read-only; condição de estado fechada |

Resumo: agentes usados: múltiplos WPs delegados; fallbacks locais auditados: 2 (WP-730F histórico e M8; em ambos, a role `verifier` não estava disponível e o trabalho direto foi autorizado). A rodada M8 inclui 122 testes pass, 1 skip, probes M8 PASS e os três comandos oficiais OK; não é sign-off canônico de Verifier. A telemetria efetiva não foi localizada para os agentes listados; nenhum modelo, effort, token ou custo foi inferido.

## Custo total da tarefa

- Escopo do total: rollouts de subagentes desta tarefa
- Agentes com estimativa: 0
- Custo total equivalente à API: não disponível
- Base/moeda: API-equivalent-token-only / USD
- Exclusões: chat principal, ferramentas, modalidades e cobrança da assinatura

## Riscos residuais

- O runtime de execução de agentes não está presente no repositório; o grafo será validado, não executado.
- A configuração global pode ficar defasada até uma sincronização posterior autorizada pelo usuário.
