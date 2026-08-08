# ExecPlan: Contrato obrigatório de delegação AISDD

## Estado

Classe: T3
Contrato AISDD da feature: v1
Fase: Completion — M8 fechado com evidência oficial e gates OK; a feature permanece explicitamente v1, enquanto o scaffolding de novas specs passa a v2

## Contexto e restrições

Esta é uma mudança arquitetural da própria skill. A implementação deve ocorrer somente em `D:\codex\aisdd`; a instalação global permanece inalterada. O repositório não contém executor externo de agentes, portanto a entrega deve implementar contrato, validação, documentação e dry-run, sem inventar integração de runtime. Em v1, `plan.md` é a fonte normativa do grafo declarativo; `evidence.md` apenas resume owners/dependências e registra provas.

## Histórico de milestones anteriores

### M1 — Contrato, capabilities e compatibilidade

- [x] Objetivo: formalizar invariantes, roles, capabilities, fallback e modos v1/v2.
- Arquivos: `SKILL.md`, `references/delegation-contract.md`, `references/role-capabilities.md`, `references/agent-routing.md`, `agents/*.toml`, ADR.
- Dependências: spec e pareceres read-only de Planner/Architect.
- Passos: tornar delegação obrigatória a partir de T1; definir exceções T0; separar Test Engineer/Verifier; documentar loop de correção e gate fail-closed; preservar alias `tester`.
- Validação: testes de documentação e revisão independente.
- Risco/rollback: instruções incompatíveis com agentes instalados; manter alias e modo v1.
- Concluído quando: capabilities, owners, loops e compatibilidade estiverem explícitos.

### M2 — Work Packages e evidência v2

- [x] Objetivo: validar grafo, dependências, escopo, estados, role coverage e fallback sem alterar o contrato v1.
- Arquivos: `scripts/delegation_contract.py`, `scripts/validate_feature.py`, `tests/test_delegation_contract.py`.
- Dependências: M1.
- Passos: adicionar marcador explícito v2; validar `work-packages.json` e `delegation-evidence.json` somente em v2; ordenar WPs deterministicamente; rejeitar ciclo, dependência inexistente, conflito e fallback incompleto.
- Validação: testes unitários com fixtures v1/v2; specs legadas continuam passando.
- Risco/rollback: falso drift em specs antigas; ausência de marcador deve continuar significando v1.
- Concluído quando: v1 não exige arquivos novos e v2 falha fechada em estruturas inválidas.

### M3 — Roteamento sensível à classe

- [x] Objetivo: fazer `--class` selecionar perfis de modelo/effort por role, mantendo defaults legados.
- Arquivos: `scripts/model_routing.py`, `assets/templates/model-routing.toml`, `references/model-routing.md`, testes.
- Dependências: M1.
- Passos: adicionar tier robusto, overrides `by_class`, roles canônicas e alias; preservar fallback `inherit`; retornar estado explícito para role não configurada.
- Validação: testes com T1/T2/T3, disponibilidade conhecida e ausência de disponibilidade.
- Risco/rollback: configuração global antiga; usar template local nos testes e fallback sem escrever global.
- Concluído quando: a classe altera a recomendação apenas quando informada.

### M4 — Planner, agentes e documentação operacional

- [x] Objetivo: atualizar o contrato escrito e instruções dos agentes, sem transferir implementação para o Orchestrator.
- Arquivos: `SKILL.md`, `README.md`, `assets/templates/plan.md`, `assets/templates/status.md`, `assets/templates/evidence.md`, `assets/templates/AGENTS.md`, agentes e referências.
- Dependências: M1–M3.
- Passos: inserir plano de execução no Planner; declarar capability matrix; instruir ownership de arquivos; registrar fallback; documentar loop e completion gate.
- Validação: testes de presença e revisão de drift documental.
- Risco/rollback: docs prescritivos demais; manter o executor externo fora do escopo.
- Concluído quando: a skill orienta o fluxo completo e não permite o bypass silencioso.

### Histórico/superseded M6 — WP-716: Verifier e evidências finais

- Estado: superseded pela rodada WP-730F após os WPs corretivos WP-727A/B e WP-729; preservado apenas para rastreabilidade histórica.
- Arquivos: `specs/mandatory-delegation-contract/verification.json`, `evidence.md`, `status.md`.
- Dependências: WP-715.
- Passos: executar suíte real via `verify_feature.py`; validar feature; rodar drift; revisar diff e checar instalação global sem alterações.
- Validação: `python -B -m unittest discover -s tests -q`, `verify_feature.py`, `validate_feature.py`, `check_drift.py`.
- Risco/rollback: drift cross-feature de outra spec deve ser reportado separadamente, sem ser tratado como baseline desta feature.
- Resultado histórico: a validação independente canônica não foi exposta pelo runtime; a execução local auditada foi registrada em WP-730F e não recebe sign-off canônico de Verifier.

### M5 — WP-707: enforcement fail-closed e correção documental

- [x] Objetivo: corrigir os blockers independentes remanescentes sem editar `tests/`.
- Arquivos: `scripts/delegation_contract.py`, `scripts/validate_feature.py`, `scripts/model_routing.py`, referências, templates, ADR e artefatos de status/evidence da feature.
- Dependências: WP-706 concluído como primeira correção; Test Engineer será owner dos testes.
- Passos: exigir classe v2 válida e evidência no CLI; endurecer escopo, estados, blockers, fallback, independência, dependência serial e aprovação T4; reservar alias `tester`; alinhar docs, comandos e histórico.
- Validação: `py_compile`, checks focados existentes e comandos read-only; não gerar `verification.json` nem executar instalação global.
- Risco/rollback: preservar v1; se necessário reverter somente os arquivos deste WP, mantendo as alterações anteriores de WP-706.
- Concluído quando: os blockers deste ciclo estiverem cobertos pela implementação/documentação e o pacote estiver pronto para Test Engineer/Verifier independentes.

### M5.1 — WP-708: correção exigida pelo Reviewer

- [x] Objetivo: fechar fallback limpo, semântica T0 v2, histórico de status, fronteira v1/v2 e ordem dos gates documentais sem editar `tests/`.
- Arquivos: `scripts/delegation_contract.py`, `scripts/validate_feature.py`, referências, templates, Planner, ADR e artefatos de status/evidence da feature.
- Dependências: WP-707; os fixtures/testes do antigo WP-703 permanecem históricos e os gates independentes continuam pendentes.
- Passos: rejeitar conteúdo incompatível em `fallback.used:false`; exigir declaração T0 auditável ou role especializada; ignorar histórico em `has_open_status`; alinhar Planner, routing/lifecycle/agent-routing e registrar o blocker preexistente.
- Validação: `py_compile`, `git diff --check` e probes rápidos não autoritativos; não gerar `verification.json`, editar `tests/` ou marcar gates como concluídos.
- Risco/rollback: preservar T1+ e o contrato v1; reverter somente os arquivos deste WP se a validação focal falhar.
- Concluído quando: os blockers do Reviewer estiverem cobertos e o pacote estiver pronto para Test Engineer/Verifier/Reviewer/Documentation Reviewer independentes.

### M5.2 — WP-709: correções exigidas pelas revisões finais

- [x] Objetivo: corrigir o contrato de fallback obrigatório, role explícita, dependências mínimas, conflito conservador de glob, estados estruturados e gatilhos documentais, sem editar `tests/`.
- Arquivos: `scripts/delegation_contract.py`, `scripts/validate_feature.py`, `README.md`, `SKILL.md`, referências, templates, `agents/implementer.toml` e artefatos desta feature.
- Dependências: WP-708; a rodada independente do Test Engineer será WP-715, e os testes/fixtures históricos do WP-703 não constituem validação independente.
- Passos: exigir `fallback` objeto com `used`; remover inferência de `owner.role`; validar dependências após normalização; tratar globs fail-closed; reconhecer apenas estados estruturados atuais; incluir Documentation Reviewer no loop de correção; alinhar Planner/grafo T1+ v1.
- Validação: `py_compile`, probes e checks rápidos não autoritativos; não gerar `verification.json`, editar `tests/` ou marcar Verifier/Reviewer/Documentation Reviewer como concluídos.
- Risco/rollback: preservar o contrato v1 e WPs corretivos de Implementer; reverter somente os arquivos deste WP se os checks focados falharem.
- Concluído quando: a implementação do WP-709 estiver aplicada e o change set estiver pronto para Test Engineer/Verifier/Reviewer/Documentation Reviewer independentes, mantendo gates pendentes.

### M5.3 — WP-710: correção documental exigida pelo Documentation Reviewer

- [x] Objetivo: alinhar o gate condicional de T2, o gate obrigatório de T3/T4, o loop de correção do Test Engineer, a fonte normativa do grafo v1 e os aliases do marcador v2.
- Arquivos: `README.md`, `SKILL.md`, `references/`, `docs/architecture/decisions/ADR-0001-delegation-contract-v2.md`, `assets/templates/`, `agents/planner.toml`, `agents/implementer.toml` e os artefatos desta feature.
- Dependências: WP-709; revisão documental que exigiu a correção.
- Passos: documentar impacto documental e cobertura por classe; declarar que blocker/critério falho do Test Engineer abre novo WP e retorna ao Implementer; tornar `plan.md` a fonte do grafo v1; registrar aliases aceitos pelo detector; atualizar status/evidence sem alegar completion.
- Validação: checks rápidos de documentação e `git diff --check`; não editar `tests/`, não criar/editar `verification.json`, não executar `py_compile` porque nenhum script foi alterado e não alterar instalação global.
- Risco/rollback: preservar contrato v1, aliases existentes e histórico; reverter somente os arquivos deste WP se a revisão documental encontrar inconsistência.
- Concluído quando: a correção documental estiver aplicada e o pacote estiver pronto para Test Engineer, Verifier, Reviewer e Documentation Reviewer independentes, mantendo os gates pendentes.

### M5.4 — WP-711: parser casefold, tabelas e histórico

- [x] Objetivo: tornar a leitura de status determinística para cabeçalhos/células de tabela, sem confundir histórico com estado atual.
- Arquivos: `scripts/validate_feature.py` e artefatos de coordenação desta feature (`plan.md`, `status.md`, `evidence.md`).
- Dependências: WP-710.
- Passos: normalizar casefold e acentos no parser; reconhecer estados atuais em cabeçalhos e tabelas; ignorar entradas históricas claramente delimitadas e preservar o default v1.
- Critérios: parser casefold, tabelas e histórico cobertos por checks focados, sem converter o resultado em aprovação independente.
- Escopo permitido: `scripts/validate_feature.py` e os artefatos de coordenação desta feature.
- Escopo proibido: `tests/`, `verification.json`, `spec.md` salvo necessidade aprovada, scripts fora do escopo, instalação global e runtime externo.
- Paralelização: serial após WP-710; não paralelizar com WP-712 por dependência de coordenação; gates independentes somente depois da implementação.
- Validação: `py_compile` e probe focado não autoritativo; não executar `verify_feature.py` neste ciclo.
- Risco/rollback: preservar a detecção v1 e o histórico; reverter somente os arquivos deste WP se o parser divergir dos estados documentados.
- Concluído quando: os critérios de parser estiverem registrados e o pacote estiver pronto para os gates independentes, sem alegar verification.

### M5.5 — WP-712: marcador v2 estrito

- [x] Objetivo: restringir `CONTRACT_MARKERS` a uma linha própria terminada no token `v2`/`2`, mantendo aliases documentados e o default v1.
- Arquivos: `scripts/delegation_contract.py` e artefatos de coordenação desta feature (`plan.md`, `status.md`, `evidence.md`).
- Dependências: WP-711.
- Passos: ancorar início/fim de linha; aceitar apenas espaços finais e o prefixo de lista Markdown já documentado; rejeitar texto adicional, `v2 extra` e `v2.0`.
- Critérios: aliases case-insensitive preservados, linhas válidas detectadas e linhas ambíguas retornam v1.
- Escopo permitido: `scripts/delegation_contract.py` e os artefatos de coordenação desta feature.
- Escopo proibido: `tests/`, `verification.json`, `spec.md` salvo necessidade aprovada, instalação global e runtime externo.
- Paralelização: serial após WP-711; Test Engineer, Verifier e os revisores aplicáveis permanecem gates posteriores, não paralelos à implementação.
- Validação: `python -B -m py_compile scripts/delegation_contract.py` e probes rápidos não autoritários; não executar `verify_feature.py`.
- Risco/rollback: preservar o contrato v1 e os aliases `2`/`v2`; reverter somente os arquivos deste WP se houver regressão no opt-in.
- Concluído quando: o detector estiver estrito e o pacote estiver pronto para Test Engineer, Verifier, Reviewer e Documentation Reviewer, mantendo os gates pendentes.

### Histórico — WP-713 (superseded por WP-715; não vigente)

- Estado: registro histórico da rodada do Test Engineer v1; não é milestone nem etapa da cadeia normativa atual.
- Dependência histórica: WP-712.
- A rodada vigente do Test Engineer é WP-715/T-715, concluída com 114 testes e 1 skip. O antigo WP-714 que aparecia como Verifier e o antigo WP-715A de revisão também são apenas numeração histórica; não duplicam os WPs atuais.

### M5.7 — WP-714: correção funcional exigida pelo Reviewer

- [x] Objetivo: aplicar a correção funcional solicitada pelo Reviewer no contrato, no detector de marcador v2, na declaração T0, nas dependências e no parser de status, sem editar `tests/`.
- Arquivos: `scripts/delegation_contract.py`, `scripts/validate_feature.py` e os artefatos de coordenação desta feature.
- Dependências: WP-712; o WP-714 substitui a rodada de gates anteriormente projetada como WP-714 Verifier.
- Passos: tornar a sobreposição de glob fail-closed para prefixes parciais; ignorar fences Markdown no marcador v2; exigir capability operacional mínima por role; rejeitar justificativa T0 trivial, silenciosa ou ausente; reconhecer headings/seções estruturados em `has_open_status`; exigir listas em `depends_on` e aliases.
- Escopo permitido: scripts afetados e `plan.md`, `status.md`, `evidence.md` desta feature.
- Escopo proibido: `tests/`, `verification.json`, instalação global e runtime externo.
- Validação: `python -B -m py_compile` dos scripts afetados e probes rápidos não autoritários; Test Engineer, Verifier e revisores permanecem gates posteriores.
- Risco/rollback: preservar o contrato v1 e reverter somente o patch do WP-714 se os gates independentes identificarem regressão.
- Concluído quando: a implementação estiver aplicada e registrada, sem declarar AC, validação final ou completion.

### M5.7A — WP-715: rodada vigente do Test Engineer v1

- [x] Objetivo: concluir a rodada independente do Test Engineer após WP-714 e registrar cobertura sem assumir validação final.
- Arquivos: `tests/` e fixtures de teste; `specs/mandatory-delegation-contract/evidence.md` e `status.md` para o resultado da rodada.
- Dependências: WP-714.
- Resultado: 114 testes executados e 1 skip; o resultado não substitui o Verifier e não conclui ACs ou a feature.
- Validação: Test Engineer v1 (`tester`) concluído; WP-716/T-716 permanece como gate independente.
- Risco/rollback: preservar o contrato v1 e não transformar a rodada de testes em aprovação de completion; achados corretivos retornam a novo WP de Implementer.
- Concluído quando: o resultado atual estiver registrado e o pacote estiver pronto para WP-716, com WP-717/WP-717A ainda bloqueados por sua dependência do Verifier.

### M5.8 — WP-718: reconciliação final de documentação e coordenação

- [x] Objetivo: sincronizar a cadeia normativa e o handoff após WP-715, separar checks históricos dos resultados atuais e alinhar SKILL/ADR ao detector v2.
- Arquivos: `plan.md`, `status.md`, `evidence.md`, `SKILL.md` e `docs/architecture/decisions/ADR-0001-delegation-contract-v2.md`.
- Dependências: WP-715; WP-714 concluído.
- Passos: registrar WP-715 como concluído com 114 testes/1 skip; manter WP-716 pendente e WP-717/WP-717A pendentes, paralelos e dependentes de WP-716; rotular WP-713 e o WP-714 histórico como superseded; registrar o drift cross-feature separado.
- Validação: checks documentais e `git diff --check`; não executar `verify_feature.py`, `validate_feature.py` ou `check_drift.py`, não editar `tests/` e não criar/editar `verification.json`.
- Risco/rollback: preservar todas as alterações pré-existentes e o contrato v1; reverter somente as linhas documentais deste WP-718 se a revisão encontrar inconsistência.
- Concluído quando: a documentação refletir a cadeia única sem declarar ACs ou completion; os gates de WP-716 em diante permanecerem abertos.

### Histórico/superseded M7 — WP-717/WP-717A: revisões independentes

- Estado: superseded pela revisão vigente WP-731/WP-731A após WP-730F.
- Arquivos: diff, `spec.md`, `plan.md`, `status.md`, `evidence.md`, SKILL, referências e ADR, somente para inspeção read-only.
- Dependências: WP-716.
- Passos: executar WP-717 (Reviewer) e WP-717A (Documentation Reviewer) após o Verifier; podem rodar em paralelo porque seus escopos são independentes; qualquer blocker abre novo WP de Implementer.
- Validação: dois pareceres independentes, sem correção direta pelos revisores.
- Risco/rollback histórico: não transformar pareceres em aprovação parcial; a regra foi preservada na cadeia vigente.
- Resultado histórico: não é a cadeia normativa atual.

### M8 — Default v2 no scaffolding e compatibilidade v1

- [x] Objetivo: criar novas specs em v2 por padrão, mantendo specs existentes/legadas sem marcador e specs explicitamente v1 válidas sem JSON v2; esta feature continua v1 por decisão explícita.
- Arquivos: `scripts/create_feature.py`, `scripts/delegation_contract.py` (somente docstring), `tests/test_delegation_contract.py`, `SKILL.md`, `README.md`, `references/delegation-contract.md`, `docs/architecture/decisions/ADR-0001-delegation-contract-v2.md`, `agents/planner.toml`, `assets/templates/plan.md`, `assets/templates/status.md`, `assets/templates/evidence.md` e artefatos normativos desta feature.
- Dependências: M1–M7 históricos concluídos; comportamento do detector/validador v2 permanece sem alteração.
- Passos: mudar o default do scaffolding para v2 e gerar marcador/esqueletos; preservar `--contract v1`; ajustar testes de default, v1 legado/explícito e v2 estrito; alinhar documentação sem migração automática; registrar a decisão atual sem reescrever o histórico.
- Validação final: Test Engineer independente `agent_type=tester` (`019fdcbf-adca-75c0-bf7e-fe47a271bbf8`) com 122 pass, 1 skip e probes M8 PASS; tentativa canônica de `verifier` retornou `unknown agent_type 'verifier'`; fallback local autorizado/auditado executou `python scripts/verify_feature.py . specs/mandatory-delegation-contract -- python -B -m unittest discover -s tests -q`, `python scripts/validate_feature.py . specs/mandatory-delegation-contract` e `python scripts/check_drift.py .`, todos OK. `verification.json` foi regenerado pelo fluxo oficial, sem edição manual; o resultado não é sign-off canônico de Verifier.
- Risco/rollback: manter o detector fail-closed — somente marcador v2 exige `work-packages.json`/`delegation-evidence.json`; reverter apenas o patch M8 se o scaffolding ou os testes focados falharem.
- Concluído quando: o default novo for v2, `--contract v1` e specs sem marcador forem aceitos sem JSON v2, os testes focados passarem e a documentação distinguir claramente compatibilidade v1 de criação nova v2.

## Histórico de Work Packages de execução anteriores

| ID | Owner | Depende de | Critérios de conclusão | Escopo permitido | Escopo proibido | Paralelização | Status |
|---|---|---|---|---|---|---|---|
| WP-701 | Planner | — | contrato, schema e riscos do plano aprovados | análise e documentação de planejamento | código/testes de produto | paralelo com WP-701A | Concluído |
| WP-701A | Architect | — | invariantes, ADR e compatibilidade aprovados | análise e documentação arquitetural | código/testes de produto | paralelo com WP-701 | Concluído |
| WP-702 | Implementer | WP-701, WP-701A | scripts, agentes e templates implementados | arquivos listados nos milestones | instalação global e runtime externo | serializado por arquivo | Superseded/corrigido por WP-706 |
| WP-703 | Test Engineer | WP-707 | testes focados e casos de borda adicionados | `tests/` e fixtures | código de produto | após implementação | Superseded por WP-715; evidência histórica apenas |
| WP-704 | Verifier | WP-703 | suíte, validação e evidências independentes passam | execução de comandos e evidências geradas | editar código/testes | após Test Engineer | Superseded por WP-716 |
| WP-705 | Reviewer | WP-704, WP-707 | sem blockers de código/contrato | inspeção read-only | correção direta | após Verifier; paralelo com WP-705A | Superseded por WP-717 |
| WP-705A | Documentation Reviewer | WP-704, WP-707 | sem drift documental novo | inspeção read-only | correção direta | após Verifier; paralelo com WP-705 | Superseded por WP-717A |
| WP-706 | Implementer | WP-702 | primeira rodada de blockers corrigida | scripts, referências, templates, agentes e artefatos da feature | `tests/` (owner: Test Engineer), instalação global e runtime externo | serializado | Concluído; WP-707 corrige blockers remanescentes |
| WP-707 | Implementer | WP-706 | enforcement v2 fail-closed, docs alinhadas e pacote pronto para gates independentes | scripts, referências, templates, ADR e status/evidence da feature | `tests/`, instalação global e runtime externo | serializado; sobreposição somente com dependência explícita | Correção aplicada; gates pendentes |
| WP-708 | Implementer | WP-707 | blockers do Reviewer corrigidos e pacote pronto para gates independentes | scripts e documentação/configuração aprovados neste milestone | `tests/`, `verification.json`, instalação global e runtime externo | serializado; Reviewer e Documentation Reviewer só após Verifier | Implementação concluída; gates pendentes |
| WP-709 | Implementer | WP-708 | blockers finais corrigidos e contrato/documentação alinhados | scripts, documentação/configuração e artefatos de coordenação aprovados neste milestone | `tests/`, `verification.json`, instalação global e runtime externo | serializado; Test Engineer → Verifier → (Reviewer || Documentation Reviewer) | Implementação aplicada; gates pendentes |
| WP-710 | Implementer | WP-709 | regra de gate, loop corretivo, grafo v1, aliases e documentação alinhados | README, SKILL, references, ADR, templates, agentes e artefatos desta feature | `tests/`, `verification.json`, scripts, instalação global e runtime externo | serializado; após a correção: Test Engineer → Verifier → (Reviewer || Documentation Reviewer) | Implementação aplicada; gates pendentes |
| WP-711 | Implementer | WP-710 | parser com casefold, tabelas e histórico delimitado | `scripts/validate_feature.py` e artefatos de coordenação desta feature | `tests/`, `verification.json`, `spec.md` salvo necessidade aprovada, scripts fora do escopo, instalação global e runtime externo | serializado após WP-710; sem paralelização com WP-712; gates posteriores | Concluído; gates posteriores pendentes |
| WP-712 | Implementer | WP-711 | marcador v2 estrito, aliases preservados e fallback v1 | `scripts/delegation_contract.py` e artefatos de coordenação desta feature | `tests/`, `verification.json`, `spec.md` salvo necessidade aprovada, instalação global e runtime externo | serializado após WP-711; WP-714 → WP-715 → WP-716 → (WP-717 || WP-717A) depois da implementação | Concluído; WP-714 concluído |
| WP-713 | tester / Test Engineer v1 | WP-712 | rodada final de testes focados e casos de borda registrada | `tests/`, fixtures e evidência da rodada | código de produto, instalação global e runtime externo | serial após WP-712; não é Verifier | Histórico/superseded por WP-715; não vigente |
| WP-714 | Implementer | WP-712 | correção funcional aplicada e registrada | `scripts/delegation_contract.py`, `scripts/validate_feature.py` e artefatos desta feature | `tests/`, `verification.json`, instalação global e runtime externo | serial após WP-712; WP-715 → WP-716 → (WP-717 || WP-717A) depois da implementação | Concluído; WP-715 concluído; gates posteriores pendentes |
| WP-715 | tester / Test Engineer v1 | WP-714 | rodada independente de testes focados e casos de borda registrada | `tests/`, fixtures e evidência da rodada | código de produto, instalação global e runtime externo | após WP-714; não é Verifier | Concluído: 114 testes, 1 skip; não é Verifier |
| WP-718 | Implementer | WP-715 | reconciliação final de documentação e coordenação registrada | `plan.md`, `status.md`, `evidence.md`, `SKILL.md`, ADR | `tests/`, `verification.json`, scripts, instalação global e runtime externo | após WP-715; não altera a cadeia de gates | Concluído; WP-716 em diante pendentes |
| WP-719A | Implementer | WP-718 | correções fail-closed no detector v2, classe e dependências | `scripts/delegation_contract.py` | `tests/`, docs, specs, `verification.json`, instalação global e runtime externo | paralelo com WP-719B; serial antes do Test Engineer | Concluído |
| WP-719B | Implementer | WP-718 | seções atuais de status detectadas sem abrir estados fechados | `scripts/validate_feature.py` | `tests/`, docs, specs, `verification.json`, instalação global e runtime externo | paralelo com WP-719A; serial antes do Test Engineer | Concluído |
| WP-720R | tester / Test Engineer v1 | WP-719A, WP-719B | testes regressivos dos novos casos e rodada focal registrada | `tests/test_delegation_contract.py`, `tests/test_check_drift.py` | código de produto, docs, specs, `verification.json`, instalação global e runtime externo | serial após Implementers | Concluído; 37 testes, inicialmente 1 falha documental |
| WP-721 | Implementer | WP-720R | formulação canônica do marcador alinhada ao teste existente | `SKILL.md` | `tests/`, scripts, specs, `verification.json`, instalação global e runtime externo | serial após achado do Test Engineer | Concluído |
| WP-722 | tester / Test Engineer v1 | WP-721 | rerodada focal independente | somente execução de testes | edição de código/testes, docs, specs, `verification.json`, instalação global e runtime externo | serial | Superseded pela correção WP-723; 1 falha textual observada |
| WP-723 | Implementer | WP-722 | vírgula canônica após `below` restaurada | `SKILL.md` | `tests/`, scripts, specs, `verification.json`, instalação global e runtime externo | serial após WP-722 | Concluído |
| WP-724 | tester / Test Engineer v1 | WP-723 | suíte focal e ampla passam, com skips reportados | somente execução de testes | edição de código/testes, docs, specs, `verification.json`, instalação global e runtime externo | serial após Implementer | Concluído; 37 focados, 118 amplos, 1 skip |
| WP-725F | Fallback local auditável | WP-724 | primeira geração de evidência oficial antes do endurecimento final | comandos oficiais e artefatos de evidência dentro da feature | código/testes, instalação global, runtime externo e correção de drift fora do fluxo próprio | serial; aprovação registrada em `evidence.md` | Superseded por WP-730F após WP-727A/B |
| WP-726 | Reviewer | WP-725F | primeira revisão independente | inspeção read-only do change set | correção direta | após fallback; paralelo com WP-726A | Superseded por WP-731 após blockers |
| WP-726A | Documentation Reviewer | WP-725F | primeira revisão documental independente | inspeção read-only de docs/spec/ADR/status/evidence | correção direta | após fallback; paralelo com WP-726 | Superseded por WP-731A após blockers |
| WP-727A | Implementer | WP-726 | fallback read-only com escopo read/execute e operação explícita | `scripts/delegation_contract.py` | `tests/`, docs, specs, `verification.json`, instalação global e runtime externo | paralelo com WP-727B; serial antes do Test Engineer | Concluído |
| WP-727B | Implementer | WP-726A | `plan.md` incluído no gate de estado atual | `scripts/validate_feature.py` | `tests/`, docs, specs, `verification.json`, instalação global e runtime externo | paralelo com WP-727A; serial antes do Test Engineer | Concluído |
| WP-728 | tester / Test Engineer v1 | WP-727A, WP-727B | regressivos de fallback read-only e plan aberto passam | `tests/test_delegation_contract.py`, `tests/test_check_drift.py` | código de produto, docs, specs, `verification.json`, instalação global e runtime externo | serial após Implementers | Concluído; 41 focados, 122 amplos, 1 skip |
| WP-729 | Implementer | WP-728 | documentação de scope read/execute e comando relativo alinhada | `references/delegation-contract.md`, `assets/templates/evidence.md` | `tests/`, scripts, specs, `verification.json`, instalação global e runtime externo | serial após Test Engineer | Concluído |
| WP-730F | Fallback local auditável | WP-729 | regenerar evidência oficial atual; fechar plan/status após as revisões e repetir validação/drift | comandos oficiais e artefatos de evidência dentro das features | código/testes, instalação global, runtime externo e correção de drift fora do fluxo próprio | serial; aprovação registrada em `evidence.md` | Evidência regenerada; gate final após WP-731/731A |
| WP-731 | Reviewer | WP-730F | sem blockers de código/contrato | inspeção read-only do change set | correção direta | após fallback; paralelo com WP-731A | Histórico/superseded; resultado consolidado no grafo atual |
| WP-731A | Documentation Reviewer | WP-730F | sem drift documental novo | inspeção read-only de docs/spec/ADR/status/evidence | correção direta | após fallback; paralelo com WP-731 | Histórico/superseded; resultado consolidado no grafo atual |

## Grafo atual de execução v1

| ID | Owner | Depende de | Critérios de conclusão | Escopo permitido | Escopo proibido | Paralelização | Status |
|---|---|---|---|---|---|---|---|
| WP-727A | Implementer | WP-726 histórico | fallback read/execute read-only fail-closed | `scripts/delegation_contract.py` | `tests/`, specs, `verification.json`, instalação global | paralelo com WP-727B | Concluído |
| WP-727B | Implementer | WP-726A histórico | `plan.md` incluído no gate de estado | `scripts/validate_feature.py` | `tests/`, specs, `verification.json`, instalação global | paralelo com WP-727A | Concluído |
| WP-728 | Test Engineer | WP-727A, WP-727B | regressivos e suíte independente passam | `tests/` | código de produto, specs, `verification.json`, instalação global | serial após Implementers | Concluído |
| WP-729 | Implementer | WP-728 | referências/templates alinhados | `references/delegation-contract.md`, `assets/templates/evidence.md` | `tests/`, scripts, specs, `verification.json`, instalação global | serial após Test Engineer | Concluído |
| WP-730F | Fallback local auditável | WP-729 | evidência oficial, validação e drift atuais | comandos oficiais e evidências locais | código/testes, instalação global, correção externa | serial; aprovação registrada em `evidence.md` | Concluído |
| WP-731 | Reviewer | WP-730F | sem blockers de código/contrato | inspeção read-only | correção direta | paralelo com WP-731A | Concluído; zero blockers técnicos |
| WP-731A | Documentation Reviewer | WP-730F | sem drift documental novo | inspeção read-only | correção direta | paralelo com WP-731 | Concluído; reconciliação documental confirmada |

## Histórico de tarefas rastreáveis anteriores

| ID | Milestone | Critérios atendidos | Arquivos previstos | Dependências | Owner | Paralelização/condição | Status |
|---|---|---|---|---|---|---|---|
| T-701 | M1 | AC-701, AC-702, AC-703 | skill, referências, agentes, ADR | WP-701, WP-701A | Implementer | serial após Planner/Architect | Concluído |
| T-702 | M2 | AC-704, AC-705, AC-706 | scripts, testes, fixtures | WP-701, WP-701A | Implementer | serial após M1 | Concluído |
| T-703 | M3 | AC-707, AC-708 | roteador, template, testes | T-701 | Implementer | serial após T-701 | Concluído |
| T-704 | M4 | AC-709, AC-711 | docs e templates | T-701, T-702, T-703 | Implementer | serial após dependências | Concluído |
| T-705 | M6 | AC-710 | evidências e validações | T-702, T-703, T-704, T-707, T-710, T-711, T-712 | Verifier | substituída por T-716 após T-715 | Superseded por T-716 |
| T-706 | M2, M4 | AC-701, AC-702, AC-704, AC-705, AC-706, AC-707, AC-708, AC-709, AC-711 | primeira correção negativa de contrato, fallback, ownership, scaffold, CLI e documentação | T-701, T-702, T-703, T-704 | Implementer | serial; superseded por T-707 | Concluído; superseded/corrigido por T-707 |
| T-707 | M5 | AC-701, AC-704, AC-705, AC-706, AC-707, AC-708, AC-709, AC-711 | correção fail-closed de classe, evidência, escopo, estados, blockers, independência, T4, aliases e documentação | T-706 | Implementer | serial; gates após Test Engineer | Implementação concluída; gates pendentes |
| T-708 | M5.1 | AC-701, AC-704, AC-705, AC-706, AC-709, AC-711 | correção de fallback limpo, T0 v2, histórico, fronteira v1/v2 e ordem de revisão | T-707 | Implementer | serial; revisores somente após Verifier | Implementação concluída; gates pendentes |
| T-709 | M5.2 | AC-702, AC-704, AC-705, AC-706, AC-709, AC-711 | scripts, docs, agentes e artefatos da feature | T-708 | Implementer | serial; Test Engineer → Verifier → (Reviewer || Documentation Reviewer) | Implementação aplicada; gates pendentes |
| T-710 | M5.3 | AC-701, AC-702, AC-709, AC-711 | correção documental de gate, loop Test Engineer, grafo v1, aliases e status/evidence | T-709 | Implementer | serial; após correção: Test Engineer → Verifier → (Reviewer || Documentation Reviewer) | Implementação aplicada; gates pendentes |
| T-711 | M5.4 | AC-705 | parser casefold, tabelas e histórico delimitado | `scripts/validate_feature.py`, plan/status/evidence da feature | WP-710 | Implementer | serial após WP-710; WP-712 e gates posteriores não são paralelos | Concluído; gates posteriores pendentes |
| T-712 | M5.5 | AC-705 | marcador v2 estrito e fallback v1 preservado | `scripts/delegation_contract.py`, plan/status/evidence da feature | WP-711 | Implementer | serial após WP-711; WP-714 → WP-715 → WP-716 → (WP-717 || WP-717A) depois | Concluído; WP-714 concluído |
| T-713 | Histórico | AC-705 | rodada histórica do Test Engineer v1 | `tests/`, fixtures e evidence/status da feature | WP-712 | tester / Test Engineer v1 | não é etapa vigente; superseded por T-715 | Histórico/superseded |
| T-714 | M5.7 | AC-701–AC-711 | correção funcional e enforcement registrados | `scripts/delegation_contract.py`, `scripts/validate_feature.py`, plan/status/evidence | WP-712 | Implementer | serial; gates posteriores não são paralelos à implementação | Implementação aplicada; gates pendentes |
| T-715 | M5.7A | AC-701–AC-711 | rodada independente do Test Engineer registrada | `tests/`, fixtures e evidence/status da feature | T-714 | tester / Test Engineer v1 | após Implementer; não substitui Verifier | Concluído: 114 testes, 1 skip |
| T-718 | M5.8 | AC-701–AC-711 | reconciliação final de documentação e coordenação | `plan.md`, `status.md`, `evidence.md`, `SKILL.md`, ADR | T-715 | Implementer | após T-715; handoff documental antes de T-716; não é gate de validação | Concluído; gates pendentes |
| T-719A | M5.9 | AC-704–AC-706 | detector v2 e extração de classe/dependências endurecidos | `scripts/delegation_contract.py` | `tests/`, docs, specs, `verification.json`, instalação global | paralelo com T-719B | Implementer | Concluído |
| T-719B | M5.9 | AC-705 | seções atuais do status cobertas | `scripts/validate_feature.py` | `tests/`, docs, specs, `verification.json`, instalação global | paralelo com T-719A | Implementer | Concluído |
| T-720R | M5.9 | AC-704–AC-706 | testes regressivos e rodada focal | `tests/` e fixtures | código de produto, `verification.json`, instalação global | após T-719A/B | Test Engineer v1 | Concluído; 37 testes, achado documental aberto para correção |
| T-721 | M5.9 | AC-701, AC-705 | texto canônico da SKILL alinhado | `SKILL.md` | `tests/`, scripts, specs, `verification.json`, instalação global | após T-720R | Implementer | Concluído |
| T-722 | M5.9 | AC-701 | rerodada focal | somente execução | edição de arquivos, `verification.json`, instalação global | após T-721 | Test Engineer v1 | Superseded; falha textual levou a T-723 |
| T-723 | M5.9 | AC-701 | pontuação canônica restaurada | `SKILL.md` | `tests/`, scripts, specs, `verification.json`, instalação global | após T-722 | Implementer | Concluído |
| T-724 | M5.9 | AC-701–AC-711 | suíte focal e ampla atuais passam | somente execução | edição de arquivos, `verification.json`, instalação global | após T-723 | Test Engineer v1 | Concluído; 37 focados, 118 amplos, 1 skip |
| T-725F | M6 | AC-701–AC-711 | primeira evidência oficial antes do endurecimento final | comandos oficiais e `verification.json` | produto/testes, instalação global, correção automática de drift | após T-724 | Fallback local aprovado | Superseded por T-730F |
| T-726 | M7 | AC-701–AC-711 | primeira revisão independente | change set e artefatos | correção direta | após T-725F; paralelo com T-726A | Reviewer | Superseded por T-731 |
| T-726A | M7 | AC-701–AC-711 | primeira revisão independente documental | docs, spec, plan/status/evidence e ADR | correção direta | após T-725F; paralelo com T-726 | Documentation Reviewer | Superseded por T-731A |
| T-727A | M5.10 | AC-706 | fallback read-only auditável | `scripts/delegation_contract.py` | `tests/`, docs, specs, `verification.json`, instalação global | paralelo com T-727B | Implementer | Concluído |
| T-727B | M5.10 | AC-705 | plan incluído no gate de estado | `scripts/validate_feature.py` | `tests/`, docs, specs, `verification.json`, instalação global | paralelo com T-727A | Implementer | Concluído |
| T-728 | M5.10 | AC-705, AC-706 | testes regressivos atuais | `tests/` e fixtures | código de produto, `verification.json`, instalação global | após T-727A/B | Test Engineer v1 | Concluído; 41 focados, 122 amplos, 1 skip |
| T-729 | M5.10 | AC-703, AC-706 | docs de escopo e fallback alinhadas | referências/templates | `tests/`, scripts, specs, `verification.json`, instalação global | após T-728 | Implementer | Concluído |
| T-730F | M6 | AC-701–AC-711 | evidência oficial atual e fechamento dos checks | suíte, `verification.json`, plan/status/evidence | código/testes, instalação global, drift fora do fluxo próprio | após T-729; validação final após revisão | Fallback local aprovado | Evidência regenerada; validação final após T-731/T-731A |
| T-731 | M7 | AC-701–AC-711 | revisão independente de código/contrato | change set e artefatos | correção direta | após T-730F; paralelo com T-731A | Reviewer | Histórico/superseded; resultado consolidado no grafo atual |
| T-731A | M7 | AC-701–AC-711 | revisão independente documental | docs, spec, plan/status/evidence e ADR | correção direta | após T-730F; paralelo com T-731 | Documentation Reviewer | Histórico/superseded; resultado consolidado no grafo atual |

## Tarefas atuais

| ID | Milestone | Critérios atendidos | Arquivos previstos | Dependências | Owner | Paralelização/condição | Status |
|---|---|---|---|---|---|---|---|
| T-727A | M5.10 | AC-706 | `scripts/delegation_contract.py` | WP-726 histórico | Implementer | paralelo com T-727B | Concluído |
| T-727B | M5.10 | AC-705 | `scripts/validate_feature.py` | WP-726A histórico | Implementer | paralelo com T-727A | Concluído |
| T-728 | M5.10 | AC-705, AC-706 | `tests/` | T-727A, T-727B | Test Engineer | serial após Implementers | Concluído |
| T-729 | M5.10 | AC-703, AC-706 | referências/templates | T-728 | Implementer | serial após Test Engineer | Concluído |
| T-730F | M6 | AC-701–AC-711 | suíte, `verification.json`, plan/status/evidence | T-729 | Fallback local aprovado | checks oficiais após revisão | Concluído |
| T-731 | M7 | AC-701–AC-711 | change set e artefatos | T-730F | Reviewer | paralelo com T-731A | Concluído; zero blockers técnicos |
| T-731A | M7 | AC-701–AC-711 | docs, spec, plan/status/evidence e ADR | T-730F | Documentation Reviewer | paralelo com T-731 | Concluído; sem drift novo |
| T-732 | M8 | AC-702, AC-705, AC-711 | default v2 no scaffolding, compatibilidade v1 e documentação corrigida | `scripts/create_feature.py`, `scripts/delegation_contract.py` (docstring), `tests/test_delegation_contract.py`, docs, templates e artefatos normativos desta feature | editar manualmente `verification.json`, instalação global e runtime externo | serial; execução oficial posterior pelo fallback auditado | Concluído/fechado; 122 pass, 1 skip, probes M8 PASS, `verify_feature.py`, `validate_feature.py` e `check_drift.py` OK; sem sign-off canônico de Verifier |

Tarefas com arquivos em comum ou dependência explícita não podem ser executadas em paralelo. Em T2, o Planner/Orchestrator declara o impacto documental no `plan.md` e inclui manualmente o Documentation Reviewer quando aplicável; o validador v2 não infere essa role condicional. Em T3/T4, Documentation Reviewer é obrigatório por classe.
Cada Work Package tem exatamente um owner; Test Engineer é o único owner de
criação e alteração de testes. O Implementer pode alterar somente os arquivos
de implementação e documentação aprovados no WP.

## Histórico de descobertas e replanejamentos anteriores

- O runtime não expõe neste repositório uma API de execução de grafo; a entrega ficará em modo declarativo/validável.
- O roteador global selecionado pode não conter roles novas; o template versionado será a fonte dos testes locais e a ausência global será reportada como fallback, nunca corrigida automaticamente.
- As specs existentes não recebem arquivos v2 nem são regravadas nesta tarefa.
- O ciclo de revisão 1 encontrou blockers de enforcement, scaffold, ownership e referências; eles devem ser corrigidos antes da validação final.
- WP-706 mantém o contrato v1 da feature; WP-702 foi superseded/corrigido por WP-706 e WP-707 corrige os blockers remanescentes sem migrar esta pasta para v2.
- `specs/validation-performance-refactor` permanece fora deste WP; seu `verification.json` já foi regenerado pelo fluxo próprio e o `check_drift.py` final retornou OK, sem ser confundido com o baseline preexistente.
- O runtime desta sessão não expõe subagentes executáveis; qualquer fallback direto usado para concluir a correção será registrado com aprovação, indisponibilidade, tentativas, escopo e resultado.
- WP-703 foi superseded pelo WP-713 histórico, e essa rodada histórica foi superseded por WP-715; fixtures/testes existentes permanecem evidência histórica e não substituem a rodada independente do Test Engineer nem os gates posteriores.
- A alegação de blocker de `baseline-conformance-ui-traceability` não foi confirmada nesta rodada; se preexistente, permanece separada e será verificada pelo fluxo próprio. Nenhum check foi ocultado, removido ou convertido em aprovação.
- Reviewer e Documentation Reviewer iniciam somente após o Verifier e podem rodar em paralelo entre si quando os escopos forem independentes.
- WP-709 foi aprovado para execução pelo Implementer owner; os testes do Test Engineer estão presentes no workspace/change set e aguardam os gates independentes, sem alegação de Verifier ou completion.
- WP-710 foi aplicado pelo Implementer owner para a correção documental exigida pelo Documentation Reviewer; a feature T3 mantém esse gate obrigatório por classe, além do Reviewer, após o Verifier. A mudança não editou `tests/` nem `verification.json`.
- WP-711/T-711 foram concluídos pelo Implementer para registrar a correção do parser de casefold, tabelas e histórico dependente de WP-710; os gates posteriores permanecem pendentes.
- WP-712/T-712 foram concluídos pelo Implementer para endurecer o detector de marcadores v2; os checks foram focais e não autoritativos, sem editar `tests/`, criar `verification.json` ou alegar completion.
- WP-714/T-714 e a cadeia WP-715 → WP-716 → (WP-717 || WP-717A) são registros históricos/superseded; a sequência vigente é WP-730F → (WP-731 || WP-731A).
- WP-715/T-715 foi concluído pelo Test Engineer v1 com 114 testes e 1 skip; o resultado não é validação final nem marca ACs como concluídos.
- WP-718/T-718 foi aplicado pelo Implementer owner para a reconciliação documental histórica; a cadeia vigente foi posteriormente replanejada para WP-730F → (WP-731 || WP-731A).
- O refresh cross-feature de `validation-performance-refactor` foi executado pelo fluxo próprio e seu drift final está OK; não constitui baseline nem evidência de completion desta feature.
- M8 foi concluído pelo Implementer owner: o scaffolding novo usa v2 por padrão, `--contract v1` e ausência de marcador permanecem compatibilidade sem JSON v2, e a feature não foi migrada. Foram executados 33 testes focados do contrato, `py_compile` dos arquivos Python afetados e `git diff --check`; `verification.json` e a evidência final de Verifier não foram atualizados.
- Execução final pós-M8: a evidência foi regenerada pelo fluxo oficial após a rodada independente `agent_type=tester` (`019fdcbf-adca-75c0-bf7e-fe47a271bbf8`, 122 pass/1 skip, probes M8 PASS). A tentativa canônica de `verifier` falhou com `unknown agent_type`; o fallback local autorizado/auditado executou os três gates oficiais, todos OK. Próxima transição: nenhuma; a limitação do Verifier e a ausência de sign-off canônico permanecem registradas.
