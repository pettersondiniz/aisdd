# Status: Contrato obrigatório de delegação AISDD

- Classe: T3
- Contrato AISDD da feature: v1
- Fase atual: Completion — M8 fechado; a feature permanece explicitamente v1, enquanto novas specs são criadas em v2
- Última atualização: 2026-08-07
- Próxima ação: nenhuma no escopo do M8; a feature está fechada com evidência oficial regenerada pelo fluxo próprio.
- Bloqueios: nenhum. A role canônica `verifier` permaneceu indisponível (`unknown agent_type 'verifier'`); o fallback local autorizado e auditado executou os gates oficiais, sem sign-off canônico de Verifier.

## Histórico

- 2026-08-07: diagnóstico read-only confirmou que a permissão de edição direta do agente principal é o principal bypass atual.
- 2026-08-07: Planner e Architect concluíram análises independentes; ambos recomendaram migração aditiva v1/v2.
- 2026-08-07: usuário autorizou a implementação local, sem alterar a instalação global.
- 2026-08-07: Implementer concluiu o primeiro patch; 23 testes focados passaram.
- 2026-08-07: Test Engineer, Reviewer e Documentation Reviewer reprovaram o patch com blockers; WP-706 foi aberto para correção focada.
- 2026-08-07: WP-702 foi superseded/corrigido por WP-706; a primeira correção ajustou enforcement de fallback, validação v2, CLI de classe, roteamento `inherit`, scaffold v1/v2 e ownership documental, sem editar `verification.json`.
- 2026-08-07: WP-707 foi registrado para corrigir os blockers remanescentes de classe/evidência, escopo, estados, fallback, blockers, independência, T4, aliases, dependências seriais e documentação.
- 2026-08-07: WP-707 concluiu a implementação e os checks rápidos; naquele ponto, a suíte histórica de contrato ainda precisava de fixtures atualizados pelo Test Engineer para refletir escopo read-only explícito.
- 2026-08-07: checks focados locais passaram: 26 testes direcionados e `py_compile` dos scripts/testes afetados; a suíte ampla e os gates do Verifier não foram executados.
- 2026-08-07: WP-703 foi superseded pela rodada histórica WP-713; os fixtures/testes existentes continuam sem converter rastreamento em aprovação do Verifier, e a rodada vigente passou a ser WP-715.
- 2026-08-07: WP-708 foi aplicado pelo Implementer owner para corrigir os blockers do Reviewer em fallback limpo, T0 v2, histórico de status, fronteira v1/v2 e ordem dos revisores; gates independentes continuam pendentes.
- 2026-08-07: WP-708 passou por `py_compile`, `git diff --check`, probes não autoritários e cinco testes focados de compatibilidade; isso não substitui o Verifier.
- 2026-08-07: WP-709 foi aplicado pelo Implementer owner para corrigir fallback obrigatório, role explícita, dependências mínimas, glob conservador, estados atuais estruturados e gatilhos de Documentation Reviewer; os testes do Test Engineer estão presentes no workspace/change set, sem aprovação de Verifier ou completion.

- 2026-08-07: WP-710 foi aplicado pelo Implementer owner para corrigir a regra de gate T2/T3/T4, explicitar o loop corretivo iniciado também pelo Test Engineer, tornar `plan.md` a fonte normativa do grafo v1, documentar aliases do detector v2 e registrar a revisão documental exigida; gates independentes continuam pendentes.
- 2026-08-07: WP-711 foi aplicado pelo Implementer owner em `scripts/validate_feature.py`; `has_open_status` agora normaliza cabeçalhos/células de tabela com casefold e acentos. O teste regressivo existente foi revisado sem edição; `py_compile`, o teste focado e um probe não autoritativo passaram. `verify_feature.py` não foi executado, e gates independentes continuam pendentes.
- 2026-08-07: WP-712 foi concluído pelo Implementer owner em `scripts/delegation_contract.py`; `CONTRACT_MARKERS` agora exige linha própria terminada no token de versão, aceita o prefixo de lista Markdown documentado e mantém o fallback v1 para texto adicional. `py_compile` e probes rápidos passaram; `verify_feature.py` não foi executado, `tests/` não foi alterado, `verification.json` não foi criado e os gates independentes continuam pendentes.
- 2026-08-07: o registro de coordenação/documentação do antigo WP-713 foi superseded; a rodada vigente do Test Engineer passou a ser WP-715/T-715, sem duplicar o antigo WP-714 Verifier ou o antigo WP-715A de revisão.
- 2026-08-07: WP-714 foi concluído pelo Implementer owner como correção funcional histórica; a cadeia WP-716 → (WP-717 || WP-717A) que aparecia naquele handoff foi superseded por WP-727A/B, WP-730F e WP-731/731A.
- 2026-08-07: WP-715/T-715 foi concluído pelo Test Engineer v1 com 114 testes e 1 skip; o resultado é evidência de teste independente, não é Verifier e não conclui ACs ou a feature.
- 2026-08-07: WP-718/T-718 foi aplicado pelo Implementer owner para reconciliação documental/coordenação histórica; a cadeia vigente passou depois a WP-730F → (WP-731 || WP-731A).
- 2026-08-07: WP-719A/B foram aplicados por Implementers em escopos de arquivo separados para endurecer razões, fences, classe, aliases de dependência e seções atuais do parser de status; nenhum teste ou `verification.json` foi alterado nessa etapa.
- 2026-08-07: WP-720R/T-720R, Test Engineer v1, adicionou testes regressivos; a primeira rodada focal teve 37 testes, 36 passagens e 1 falha textual da SKILL, que abriu WP-721.
- 2026-08-07: WP-721 e WP-723 foram aplicados por Implementer para alinhar a frase do marcador v2; WP-722 foi uma rerodada do Test Engineer que repetiu a falha de pontuação antes de WP-723.
- 2026-08-07: WP-724/T-724, Test Engineer v1, passou 37 testes focados e 118 testes amplos, com 1 skip e nenhuma falha/erro. O resultado não é sign-off de Verifier.
- 2026-08-07: a tentativa de delegar WP-725 à role canônica `verifier` falhou porque o runtime retornou `unknown agent_type 'verifier'`; o fallback local foi autorizado pelo escopo explícito do usuário para concluir a alteração somente em `D:\codex\aisdd` e será auditado antes da execução.
- 2026-08-07: WP-727A/B foram aplicados por Implementers para corrigir o escopo read/execute de fallbacks read-only e fazer o gate v1 inspecionar `plan.md`; WP-728/T-728 passou 41 testes focados e 122 amplos, com 1 skip.
- 2026-08-07: WP-729 foi aplicado pelo Implementer owner para alinhar referências/templates aos campos `write/read/execute/forbidden` e remover o placeholder ambíguo de caminho nos comandos de telemetria.
- 2026-08-07: a primeira revisão independente encontrou blockers de reconciliação, fallback read-only, plan aberto e justificativa do refresh de evidência legada; esses achados abriram WP-727A/B e a nova cadeia WP-730F → (WP-731 || WP-731A).
- 2026-08-07: WP-731/T-731 Reviewer concluiu inspeção read-only sem blockers técnicos; WP-731A/T-731A Documentation Reviewer concluiu a reconciliação após os WPs documentais, sem drift novo. A feature fecha com o fallback explicitamente qualificado, sem alegar Verifier canônico executado.
- 2026-08-07: M8 foi aberto para corrigir o default de criação: novas specs passam a v2, `--contract v1` permanece compatibilidade explícita, e esta feature continua v1; registros históricos anteriores permanecem históricos.
- 2026-08-07: M8 foi concluído pelo Implementer owner com 33 testes focados do contrato, `py_compile` dos arquivos Python afetados e `git diff --check`; `verification.json` e a evidência final do Verifier não foram atualizados.
- 2026-08-07: execução final pós-M8 registrada: Test Engineer independente `agent_type=tester` (`019fdcbf-adca-75c0-bf7e-fe47a271bbf8`) com 122 pass, 1 skip e probes M8 PASS; tentativa canônica de `verifier` retornou `unknown agent_type`; fallback local autorizado/auditado executou `verify_feature.py`, `validate_feature.py` e `check_drift.py`, todos OK, e regenerou `verification.json` pelo fluxo oficial. Não é sign-off canônico de Verifier.

## Decisões recentes

- A própria feature usa o contrato v1 existente.
- Novas specs usam v2 por padrão no scaffolding; ausência de marcador ou v1 explícito é compatibilidade v1, e o marcador v2 continua ativando a validação estrita.
- O Planner atual será ampliado; não haverá uma nova role de planejamento.
- `tester` será preservado como alias de compatibilidade; Test Engineer e Verifier serão roles distintas no v2.
- 2026-08-07: M1 formalizou o contrato, a matriz de capabilities, o loop de correção e as roles canônicas; a API de subagentes não está exposta nesta sessão.
- 2026-08-07: M2 adicionou o validador v2 opt-in, grafo topológico determinístico, auditoria de escopo/roles/fallback e integração compatível em `validate_feature.py`; checks focados passaram.
- 2026-08-07: M3 adicionou overrides `by_class`, faixa `robust`, roles canônicas/alias e status explícito para role ausente; chamadas sem `--class` permanecem compatíveis.
- 2026-08-07: M4 atualizou Planner, Implementer, Test Engineer, Verifier, templates, README, ADR e completion guidance; 23 testes focados e `py_compile` passaram.
- 2026-08-07: WP-706 foi executado localmente sob aprovação explícita do pedido; a ausência de API de subagentes e o escopo direto auditável estão registrados em `evidence.md`.
- 2026-08-07: WP-707 é executado pelo Implementer owner, no escopo aprovado, sem editar `tests/`, sem criar executor externo e sem alterar instalação global; os gates independentes ainda não foram executados.
- 2026-08-07: WP-708 mantém T1+ inalterado, não edita `tests/`, não cria `verification.json` e não registra timestamp operacional ausente da evidência declarativa.
- 2026-08-07: WP-709 mantém a feature em contrato v1, não edita `tests/`, não cria `verification.json` e mantém a ordem Verifier → (Reviewer || Documentation Reviewer).
- 2026-08-07: o `verification.json` de `validation-performance-refactor` foi regenerado pelo fluxo próprio após o check apontar mapa obsoleto; `validate_feature.py` passou e o drift final ficou OK, separado do baseline preexistente de `baseline-conformance-ui-traceability`.
- 2026-08-07: WP-710 mantém a feature em contrato v1, não edita `tests/`, não cria `verification.json` e mantém a ordem Test Engineer → Verifier → (Reviewer || Documentation Reviewer), com Documentation Reviewer obrigatório nesta T3.
- 2026-08-07: WP-712 está concluído como implementação e mantém a feature em contrato v1; somente um marcador v2 estrito ativa o opt-in. Linhas com `v2 extra`, `v2.0` ou texto adicional permanecem v1; o WP-714 posterior corrige o comportamento funcional sem migrar esta feature para v2.
- 2026-08-07: o replanejamento marcou WP-714 Verifier e a cadeia WP-715 → WP-716 → (WP-717 || WP-717A) como histórico/superseded; a cadeia vigente passou a ser WP-730F → (WP-731 || WP-731A), sem completion naquele momento.
- 2026-08-07: em T2, o Planner/Orchestrator deve declarar o impacto documental no plano e requerer manualmente o Documentation Reviewer quando aplicável; o validador v2 não infere a role condicional. Esta feature é T3 e requer a role por classe.
- `plan.md` é a fonte normativa do grafo declarativo v1; `evidence.md` apenas resume owners/dependências e registra provas.
