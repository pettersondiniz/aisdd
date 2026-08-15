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

## Roteamento por classe e roles canônicas

`--class T0` a `--class T4` é opcional. Sem `--class`, `model_routing.py`
seleciona exatamente o perfil base e preserva o comportamento v1. Com a classe,
o roteador aplica `roles.<role>.by_class.<Tn>` quando configurado; se não houver
override, usa o perfil base. `robust` é uma faixa de esforço, não uma
capability.

As roles canônicas incluem `test-engineer` e `verifier`. `tester` é um alias v1
reservado de `test-engineer`: a configuração não pode remapeá-lo para
`verifier` ou outra role. Uma role sem entrada retorna o status
explícito `role-not-configured`, `capability_available: false` e o fallback; o
roteador não inventa configuração nem capability e a CLI retorna código não-zero
para essa consulta. `inherit` é apenas fallback de conversa: nunca é modelo
configurado nem capability disponível.

Exemplo somente leitura:

```text
python scripts/model_routing.py --role implementer --class T3 --availability-json available-models.json --json
```

O resultado inclui `requested_role`, `resolved_role`, `configured_role`,
`class_applied` e `profile` para tornar a decisão auditável.

## EvidÃªncia efetiva apÃ³s a delegaÃ§Ã£o

Depois de o subagente terminar, tente obter a configuraÃ§Ã£o efetiva do rollout local:

```text
python scripts/agent_evidence.py --agent-id <identificador-do-agente> --json
```

`--agent-id` primeiro exige uma correspondência exata com `agent_path`. Se essa
correlação direta falhar, o único fallback permitido é o UUID completo,
exatamente formatado e único no nome de um rollout. O caminho resolvido deve
continuar dentro de `--sessions-root`, o metadado legível deve ser consistente
com os demais seletores e o resultado normal de modelo/tokens/custo deve ser
preservado. UUID parcial, mais de um filename correspondente, metadado
inconsistente ou path inseguro é rejeitado com fail-closed; não invente
evidência nem selecione um rollout por aproximação.

Um fallback bem-sucedido é auditável: o JSON inclui
`resolution.fallback_used: true`, junto do seletor original e do UUID de
rollout resolvido (`requested_agent_id` e `matched_rollout_id`), e o modo texto
emite o alerta estável `AGENT_ID_FALLBACK`. Isso não transforma prefixos
parciais em seletores válidos.

Quando o runtime informar o UUID terminal do rollout filho, prefira a correlação direta. Não use prefixos parciais:

```text
python scripts/agent_evidence.py --rollout-id <id-do-rollout> --json
```

Em runtimes legados, quando o identificador nÃ£o estiver no metadado do filho, use uma combinaÃ§Ã£o que seja Ãºnica:

```text
python scripts/agent_evidence.py --role reviewer --parent-session-id <id-do-pai> --json
```

O script lÃª `turn_context` em `~/.codex/sessions/**/rollout-*.jsonl`. `effective.model` e `effective.reasoning_effort` refletem o Ãºltimo contexto legÃ­vel do rollout e sÃ£o a melhor evidÃªncia local observÃ¡vel; compare-os ao pedido do spawn. NÃ£o os trate como prova de cada inferÃªncia de um agente multi-turn. Se o resultado for `not-available`, `not-found` ou `ambiguous`, registre o modelo/effort efetivo como `unknown` e a limitaÃ§Ã£o, sem inferir pela resposta do agente ou pela interface.

Quando a tarefa declarar `Main-chat attribution: required` no `plan.md`, o
registro de custo do chat principal usa o lifecycle `start` → `close` →
`report --final --output task-window-report.json`. O relatório final deve estar
fechado, não provisório, ter `scope: main-chat-orchestrator` e declarar as
exclusões de rollouts delegados, ferramentas, modalidades e cobrança da
assinatura. Janela aberta/provisória não é evidência final; custo
`not-available` permanece indisponível e nunca vira zero. O subtotal delegado,
o custo do chat principal e qualquer total combinado devem continuar separados;
se uma parcela necessária não estiver disponível, o total combinado é
`not-available`.

## Spawn guard

Validate a requested model/effort pair before spawning:

```text
python scripts/model_routing.py --role implementer --class T3 --availability-json available-models.json --requested-model <model> --requested-effort <effort> --require-available --json
```

With `configured-available`, `ready` requires an exact match. A mismatch is
`request-mismatch` and requires `--allow-override` plus `--override-reason`.
With `configured-unavailable` or `availability-not-provided`, the valid
decision is `fallback-required` and the spawn must omit model and effort.
`routing_fallback`, execution `fallback`, and
`resolution.fallback_used` are separate namespaces and must not be conflated.

For v2, record each delegation at spawn time and collect it after completion:

```text
python scripts/delegation_telemetry.py record --output specs/<slug>/delegation-evidence.json --work-package WP-001 --role implementer --agent-id <id> --requested-model <model> --requested-effort <effort>
python scripts/delegation_telemetry.py collect --output specs/<slug>/delegation-evidence.json --sessions-root <sessions-root> --pricing-config <pricing-config.toml> --json
```

The collector uses only explicit IDs, preserves effective settings, tokens,
cost and correlation warnings, and emits a separate delegated subtotal. Missing,
ambiguous or unpriced rollouts remain `not-available`; unavailable cost is never
converted to zero.
