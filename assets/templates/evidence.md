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

Preencha para T2+ quando houver delegação. Depois de o agente terminar, execute `python <skill-dir>/scripts/agent_evidence.py --agent-id <id> --json`. Use o último `turn_context` legível como a melhor evidência local observável e anote a fonte; ele não prova toda inferência de um agente multi-turn. Quando houver `total_token_usage` completo, registre obrigatoriamente a fonte, as categorias observadas e a estimativa equivalente à API apenas para tokens retornada pelo script. Ela exclui ferramentas, modalidades e cobrança da assinatura. O contexto longo é desconsiderado por padrão e deve ser marcado como potencialmente impreciso quando o script retornar esse aviso. Ele usa `~/.codex/aisdd/cost-pricing.toml`, ou o template da skill caso a tabela global não exista. Não invente modelo, effort, uso de tokens ou custo quando o runtime não os expuser.

| Papel | Agente | Tarefa | Modelo solicitado | Effort solicitado | Modelo efetivo | Effort efetivo | Fonte efetiva | Tokens/categorias observados | Custo API estimado | Fallback | Resultado |
|---|---|---|---|---|---|---|---|---|---|---|---|

Resumo: agentes usados: 0; fallbacks: 0.

## Riscos residuais
