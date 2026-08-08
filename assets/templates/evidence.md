# Evidências: {{FEATURE_TITLE}}

## Comandos executados

| Comando | Resultado | Quando |
|---|---|---|
|  |  |  |

## Rastreabilidade

| Critério | Implementação | Teste/evidência | Status |
|---|---|---|---|
| AC-001 |  | `caminho/do/teste` (`@spec:AC-001`) | Pendente |
| AC-002 |  | `caminho/do/teste` (`@spec:AC-002`) | Pendente |

## Verificação mecânica

O scaffolding de novas specs usa v2 por padrão e cria o marcador e os dois
esqueletos JSON. Specs existentes/legadas sem marcador e specs explicitamente
criadas com `--contract v1` permanecem em v1 como compatibilidade, sem exigir
esses artefatos e sem migração automática. A validação v2 continua estrita e
só é ativada por um marcador v2 válido.

Execute os comandos abaixo a partir do diretório que contém este `SKILL.md`,
isto é, a raiz da skill. Assim, `scripts/...` é sempre relativo ao diretório da
skill e não depende de um placeholder de caminho absoluto.

Execute `python scripts/verify_feature.py <repo> specs/<feature> -- <comando-de-teste>`.
O comando grava `verification.json`; não edite esse arquivo manualmente. Uma prova só é válida
quando o comando terminou com êxito, o teste anotado não está pulado e o mapa de testes não mudou.

Em contrato v1, `plan.md` é a fonte normativa do grafo declarativo. Esta
`evidence.md` apenas resume owners/dependências e registra comandos, resultados,
provas e limitações; não redefine tarefas ou dependências. Blockers, critérios
falhos ou correções exigidas pelo Test Engineer também devem ser registrados
como novo WP no `plan.md`, com retorno ao Implementer e repetição de Test
Engineer, Verifier e revisores aplicáveis.

## Contrato v2

T0 só fica fora do contrato quando for comprovadamente mecânico e não
delegável; se houver trabalho delegável, registre sua role e evidência como nos
demais níveis. O Orchestrator não executa esse trabalho diretamente. Em T0 v2,
exija `mechanical_non_delegable.approved: true` com justificativa auditável ou
uma role especializada; `orchestrator/coordinate` não cobre trabalho
delegável.

Em T1+ legado ou explicitamente v1, mantenha a evidência nos artefatos v1 e não crie nem exija
`work-packages.json` ou `delegation-evidence.json`. A seção v2 abaixo só se
aplica quando a feature contiver o marcador v2 explícito.

Se a feature contiver `Contrato AISDD da feature: v2`, registre os arquivos
`work-packages.json` e `delegation-evidence.json`, a ordem topológica retornada,
o digest validado, a cobertura de `planner`, `implementer`, `test-engineer`,
`verifier`, `reviewer` e `documentation-reviewer` conforme a classe e o impacto documental, escopos canônicos explícitos, estados canônicos,
a independência entre os papéis que exigem separação, blockers e qualquer
fallback. Cada entrada de `delegations` deve conter `fallback` como objeto com
`used` booleano; a ausência falha, e `{"used": false}` deve permanecer limpo.
O `scope` de cada Work Package é um objeto de caminhos relativos que pode
declarar `write`, `read`, `execute` e `forbidden`; `write` e `forbidden` devem
ser declarados mesmo vazios. Roles read-only usam `scope.write: []` e não
escrevem. Para fallback usado de `verifier`, `reviewer` ou
`documentation-reviewer`, registre `direct_work.operation` como `read` ou
`execute` e use, respectivamente, `scope.read` ou `scope.execute` como escopo
permitido; para `implementer`, use `operation: "write"` e `scope.write`.
No fallback local canônico, preserve a role declarada no WP e registre o
trabalho direto como fallback auditado; a execução ou o resultado de `tester`
continua sendo apenas Test Engineer e nunca cobre `verifier`.
`tester` cobre somente o alias v1 de `test-engineer`; nunca registre-o
como Verifier. Fallback exige aprovação explícita, motivo não trivial,
indisponibilidade observada, tentativas e trabalho direto com escopo permitido
e resultado. Sem role/agente disponível, registre `BLOCKED`/decisão humana;
nunca use trivialidade ou silêncio como bypass. Em T4, registre
`human_approval.approved`, `approver`, `timestamp` e `reference`. Não edite
`verification.json` manualmente.

## Checks não executados

## Rastreabilidade de agentes

Preencha para T2+ quando houver delegação. Depois de o agente terminar, execute `python scripts/agent_evidence.py --agent-id <id> --json` a partir do diretório da skill. Use o último `turn_context` legível como a melhor evidência local observável e anote a fonte; ele não prova toda inferência de um agente multi-turn. Quando houver `total_token_usage` e `last_token_usage` completos, registre obrigatoriamente a fonte, as categorias observadas, a quantidade de requisições e a estimativa equivalente à API apenas para tokens retornada pelo script. O cálculo usa cada `last_token_usage`, preserva snapshots seguros, ignora apenas pares cumulativo/per-request idênticos e confere a soma contra o total acumulado; não some snapshots cumulativos. Ela exclui ferramentas, modalidades e cobrança da assinatura. O long context é classificado por requisição quando a política do modelo é `tiered`; um fallback cumulativo deve ser marcado como potencialmente impreciso. Telemetria presente porém malformada não pode cair em fallback. Ele usa `~/.codex/aisdd/cost-pricing.toml`, ou o template da skill caso a tabela global não exista. Não invente modelo, effort, uso de tokens, política ou custo quando o runtime/tabela não os expuserem.

Ao usar `--agent-id`, a correlação direta com `agent_path` vem primeiro. Se ela
falhar, o único fallback é um UUID completo, exatamente formatado e único no
nome de um rollout. O path resolvido deve permanecer dentro de
`--sessions-root` e os demais metadados devem ser consistentes. UUID parcial,
match ambíguo, metadado inconsistente ou path inseguro deve falhar fechado sem
inventar evidência. Registre o fallback somente quando o JSON trouxer
`resolution.fallback_used: true` e o texto trouxer o alerta estável
`AGENT_ID_FALLBACK`, com o seletor original e o rollout resolvido.

| Papel | Agente | Tarefa | Modelo solicitado | Effort solicitado | Modelo efetivo | Effort efetivo | Fonte efetiva | Tokens/categorias observados | Custo API estimado | Fallback | Resultado |
|---|---|---|---|---|---|---|---|---|---|---|---|

Resumo: agentes usados: 0; fallbacks: 0.

## Custo total da tarefa

Para T2+ com delegação, some somente os valores `total_usd` com status `estimated` dos rollouts de subagentes pertencentes a esta tarefa. Registre o escopo, a quantidade de agentes com custo, a moeda/base do cálculo, o total e as exclusões. Não inclua o chat principal nem rollouts de validação não pertencentes à tarefa; quando não houver estimativas completas, registre `não disponível`.

- Escopo do total: rollouts de subagentes desta tarefa
- Agentes com estimativa: 0
- Custo total equivalente à API: não disponível
- Base/moeda: API-equivalent-token-only / USD
- Exclusões: chat principal, ferramentas, modalidades e cobrança da assinatura

## Custo do chat principal

Quando a tarefa incluir o chat principal, exija o lifecycle `start` → `close` →
`report --final --output task-window-report.json`. Mantenha
`specs/<slug>/task-window.json` como sidecar da janela e use:

```text
python scripts/task_window.py start --task-id <task-id> --output specs/<slug>/task-window.json --sessions-root <sessions-root> [--session-file <rollout.jsonl>|--session-id <session-id>]
python scripts/task_window.py close --window specs/<slug>/task-window.json --sessions-root <sessions-root> --end-turn-id <start-turn-id>
python scripts/task_window.py report --window specs/<slug>/task-window.json --sessions-root <sessions-root> --pricing-config <pricing-config.toml> --final --output specs/<slug>/task-window-report.json --json
```

Registre os limites, o status e o custo retornado. O relatório final deve usar
`scope: main-chat-orchestrator` e declarar as exclusões `delegated-agent
rollouts`, `tool fees`, `modality fees` e `subscription billing`.
Uma janela aberta é provisória, não é evidência final; use
`report --final --output` para fechar o relatório.
O cálculo usa somente eventos da sessão principal dentro dos limites, o delta
cumulativo entre eles e os `last_token_usage` por requisição; não soma
subagentes, mensagens de marcador, ferramentas ou cobrança da assinatura.
Se o custo for `not-available`, preserve esse estado e sua razão; nunca o trate
como zero. O subtotal delegado, o custo do chat principal e o total combinado
ficam separados, e o total combinado é `not-available` quando uma parcela
necessária estiver indisponível.

- Arquivo da janela: `specs/<slug>/task-window.json`
- Limites: `start.turn_id` → `end.turn_id` (ou `end: null` enquanto aberta)
- Status da janela: `open`/`closed`
- Custo do chat principal equivalente à API: registrar o valor retornado; enquanto `open`, marcar como provisório e não como evidência final
- Base/moeda: `api-equivalent-token-only` / USD
- Exclusões: subagentes, ferramentas, modalidades e cobrança da assinatura

Ao registrar o total combinado, some o custo fechado do chat principal ao custo dos rollouts de subagentes desta tarefa. Não inclua rollouts de validação ou outras tarefas; se qualquer parcela necessária estiver indisponível, registre o total como `não disponível`.

## Riscos residuais

## Coleta machine-readable de delegações

Em contrato v2, registre a delegação assim que o spawn retornar e colete o
rollout depois que ele terminar:

```text
python scripts/delegation_telemetry.py record --output specs/<slug>/delegation-evidence.json --work-package WP-001 --role implementer --agent-id <id> --requested-model <model> --requested-effort <effort>
python scripts/delegation_telemetry.py collect --output specs/<slug>/delegation-evidence.json --sessions-root <sessions-root> --pricing-config <pricing-config.toml> --json
```

O coletor usa apenas delegações explicitamente registradas, preserva modelo,
effort, tokens, custo e correlação, e mantém o subtotal delegado separado do
chat principal. Rollout ausente/ambíguo, telemetria incompleta ou preço ausente
permanece `not-available`; nunca use zero para representar uma parcela ausente.
