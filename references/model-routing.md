# Roteamento interativo de modelos

Use um mapeamento global do usuÃ¡rio em `~/.codex/aisdd/model-routing.toml`. Se ele ainda nÃ£o existir, consulte `assets/templates/model-routing.toml` como padrÃ£o, sem criar arquivo algum. Esse mapeamento Ã© uma preferÃªncia, nÃ£o uma prova de disponibilidade.

## Consulta

Antes de delegar, obtenha os pares de modelo e effort expostos pelo runtime atual. Grave-os em JSON no formato abaixo e consulte o roteador:

```json
{"models":[{"id":"dinizpe-5.4-mini","reasoning_efforts":["low","medium","high"]}]}
```

```text
python scripts/model_routing.py --role explorer --class T2 --availability-json available-models.json
```

O resultado informa a preferÃªncia configurada, a recomendaÃ§Ã£o compatÃ­vel, os efforts disponÃ­veis e o fallback. A faixa `economy` prioriza Luna e 5.4 mini; a `standard` prioriza Terra e 5.4. Os padrÃµes aceitam prefixos de provedores, como `dinizpe-5.4-mini`.

## Fallback e conversa

Quando o modelo configurado nÃ£o estiver disponÃ­vel, delegue sem sobrescrever `model` nem `reasoning_effort`; isso preserva a configuraÃ§Ã£o do chat atual. Registre o fallback em `evidence.md` quando ele afetar uma feature.

Apresente ao usuÃ¡rio:

1. o papel, modelo e effort configurados que falharam;
2. os modelos e efforts disponÃ­veis no runtime;
3. as sugestÃµes compatÃ­veis por faixa; e
4. a opÃ§Ã£o de manter o fallback somente nesta execuÃ§Ã£o.

Pergunte se deseja aplicar uma sugestÃ£o, escolher outro modelo/effort, editar outros papÃ©is ou manter o fallback sem salvar. Atualize `~/.codex/aisdd/model-routing.toml` somente com confirmaÃ§Ã£o explÃ­cita. Ao alterar, mostre o diff e preserve as entradas nÃ£o relacionadas.

## EvidÃªncia efetiva apÃ³s a delegaÃ§Ã£o

Depois de o subagente terminar, tente obter a configuraÃ§Ã£o efetiva do rollout local:

```text
python scripts/agent_evidence.py --agent-id <identificador-do-agente> --json
```

Quando o runtime informar o UUID terminal do rollout filho, prefira a correlação direta. Não use prefixos parciais:

```text
python scripts/agent_evidence.py --rollout-id <id-do-rollout> --json
```

Em runtimes legados, quando o identificador nÃ£o estiver no metadado do filho, use uma combinaÃ§Ã£o que seja Ãºnica:

```text
python scripts/agent_evidence.py --role reviewer --parent-session-id <id-do-pai> --json
```

O script lÃª `turn_context` em `~/.codex/sessions/**/rollout-*.jsonl`. `effective.model` e `effective.reasoning_effort` refletem o Ãºltimo contexto legÃ­vel do rollout e sÃ£o a melhor evidÃªncia local observÃ¡vel; compare-os ao pedido do spawn. NÃ£o os trate como prova de cada inferÃªncia de um agente multi-turn. Se o resultado for `not-available`, `not-found` ou `ambiguous`, registre o modelo/effort efetivo como `unknown` e a limitaÃ§Ã£o, sem inferir pela resposta do agente ou pela interface.
