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

Execute `python <skill-dir>/scripts/verify_feature.py <repo> specs/<feature> -- <comando-de-teste>`.
O comando grava `verification.json`; não edite esse arquivo manualmente. Uma prova só é válida
quando o comando terminou com êxito, o teste anotado não está pulado e o mapa de testes não mudou.

## Checks não executados

## Rastreabilidade de agentes

Preencha para T2+ quando houver delegação. Depois de o agente terminar, execute `python <skill-dir>/scripts/agent_evidence.py --agent-id <id> --json`. Use o último `turn_context` legível como a melhor evidência local observável e anote a fonte; ele não prova toda inferência de um agente multi-turn. Quando houver `total_token_usage` e `last_token_usage` completos, registre obrigatoriamente a fonte, as categorias observadas, a quantidade de requisições e a estimativa equivalente à API apenas para tokens retornada pelo script. O cálculo usa cada `last_token_usage`, preserva snapshots seguros, ignora apenas pares cumulativo/per-request idênticos e confere a soma contra o total acumulado; não some snapshots cumulativos. Ela exclui ferramentas, modalidades e cobrança da assinatura. O long context é classificado por requisição quando a política do modelo é `tiered`; um fallback cumulativo deve ser marcado como potencialmente impreciso. Telemetria presente porém malformada não pode cair em fallback. Ele usa `~/.codex/aisdd/cost-pricing.toml`, ou o template da skill caso a tabela global não exista. Não invente modelo, effort, uso de tokens, política ou custo quando o runtime/tabela não os expuserem.

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

Quando a tarefa incluir o chat principal, mantenha `specs/<slug>/task-window.json` como sidecar da janela. Crie-a com `scripts/task_window.py start`, feche-a depois de `task_complete` ou `turn_aborted` com `scripts/task_window.py close` e gere o custo com `scripts/task_window.py report`. Registre os limites, o status e o custo retornado; uma janela aberta é apenas provisória e não deve ser usada como evidência final. O cálculo usa somente eventos da sessão principal dentro dos limites, o delta cumulativo entre eles e os `last_token_usage` por requisição; não soma subagentes, mensagens de marcador, ferramentas ou cobrança da assinatura.

- Arquivo da janela: `specs/<slug>/task-window.json`
- Limites: `start.turn_id` → `end.turn_id` (ou `end: null` enquanto aberta)
- Status da janela: `open`/`closed`
- Custo do chat principal equivalente à API: registrar o valor retornado; enquanto `open`, marcar como provisório e não como evidência final
- Base/moeda: `api-equivalent-token-only` / USD
- Exclusões: subagentes, ferramentas, modalidades e cobrança da assinatura

Ao registrar o total combinado, some o custo fechado do chat principal ao custo dos rollouts de subagentes desta tarefa. Não inclua rollouts de validação ou outras tarefas; se qualquer parcela necessária estiver indisponível, registre o total como `não disponível`.

## Riscos residuais
