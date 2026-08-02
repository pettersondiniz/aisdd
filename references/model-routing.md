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
