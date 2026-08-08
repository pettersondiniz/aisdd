# Delegated rollout observability

## Objetivo

Disponibilizar no AISDD uma trilha machine-readable para cada Work Package
delegado. O orquestrador declara a delegação, preserva modelo/effort
solicitados e decisão de roteamento, e depois coleta evidência observável do
rollout sem transformar ausência de dados em custo zero.

## Contexto

O runtime pode iniciar rollouts fora do processo que gera a especificação.
Por isso, a telemetria precisa correlacionar explicitamente `work_package` com
`agent_id` ou `rollout_id`, distinguir modelo solicitado de modelo efetivo e
manter separado o subtotal delegado do custo do chat principal. A validação de
roteamento também precisa impedir que um pedido de modelo não aprovado seja
tratado como escolha implícita.

## Comportamento esperado

- `delegation_telemetry.py init` cria um manifesto v2 com digest opcional dos
  Work Packages e roles obrigatórias.
- `record` é idempotente por Work Package e registra a declaração antes da
  execução; uma mudança de agente ou roteamento remove a evidência coletada
  anteriormente para evitar mistura de rollouts.
- `collect` resolve somente os agentes declarados, registra modelo/effort
  efetivos, uso de tokens e estimativa de custo quando observáveis, e mantém
  `delegated_subtotal` separado de `unavailable`.
- `model_routing.py` expõe uma guarda explícita: mismatch de modelo/effort é
  bloqueado, e override só é aceito com justificativa não vazia.
- O lifecycle do chat principal continua sendo responsabilidade do
  orquestrador: ele deve executar `task_window.py start`, `close` e
  `report --final`; os marcadores precisam vir dos eventos reais do runtime.

## Fluxos principais

1. Validar a recomendação e a disponibilidade antes de chamar spawn.
2. Inicializar o manifesto e registrar cada WP com o seletor do rollout.
3. Executar o trabalho delegado e coletar evidência ao final.
4. Validar contrato v2, rodar a suíte anotada e gerar `verification.json` pelo
   verificador.

## Regras e invariantes

- O manifesto usa contrato v2 e possui uma entrada no máximo por WP.
- `fallback` é sempre um objeto com `used: true|false`; fallback usado exige
  aprovação, motivo, tentativas, indisponibilidade observada e trabalho direto
  dentro do escopo do WP.
- Dados de sessão são somente leitura; a saída nunca pode sobrescrever um
  rollout ou arquivo de preços.
- Custo indisponível permanece `not-available`; não há conversão para zero.
- O subtotal delegado não incorpora o chat principal nem taxas de ferramenta,
  modalidade ou assinatura.
- Specs v1 existentes permanecem v1 e não recebem migração automática.

## Casos de borda e falhas

- Se o agente não puder ser resolvido, `collect` retorna status parcial e lista
  a delegação em `unavailable`.
- Se houver moedas incompatíveis, o subtotal delegado fica indisponível.
- Se a declaração solicitar um modelo diferente da recomendação, a guarda
  retorna `request-mismatch`; override sem motivo continua bloqueado.
- Saídas dentro da raiz de sessões ou iguais a um rollout são rejeitadas.

## Interfaces e persistência afetadas

- `scripts/delegation_telemetry.py` — CLI `init`, `record` e `collect`.
- `scripts/model_routing.py` — função `validate_request` e opções de guarda.
- `specs/<slug>/delegation-evidence.json` — manifesto v2 persistido.
- `specs/<slug>/verification.json` — artefato gerado por `verify_feature.py`.

## Requisitos não funcionais

- Operação determinística, idempotente e segura contra sobrescrita de entrada.
- Nenhuma inferência de modelo, tokens, política de preço ou custo ausente.
- Compatibilidade com as specs v1 e com a resolução existente de evidência.

## Fora de escopo

- Exibir telemetria na UI ou API do Agent Bridge.
- Alterar o projeto `agent-bridge-mcp` ou seu formatter.
- Inventar eventos de `task_started`/`task_completed` no AISDD.

## Critérios de aceitação

- [ ] AC-801: `init` e `record` criam e atualizam uma entrada por Work Package
  de forma idempotente, preservando a última declaração de agente e roteamento.
- [ ] AC-802: `collect` correlaciona um rollout declarado e preserva modelo
  efetivo, uso de tokens e estimativa de custo no subtotal delegado.
- [ ] AC-803: uma correlação ausente mantém custo `not-available`, lista a
  delegação em `unavailable` e faz `collect` terminar com status parcial.
- [ ] AC-804: a guarda aceita a recomendação, rejeita mismatch não aprovado e
  aceita override somente com justificativa explícita.

Cada critério é observável por teste anotado com `@spec:AC-xxx`.

## Suposições

| ID | Suposição | Status | Dono/validação |
|---|---|---|---|
| ASM-001 | O runtime local expõe rollouts JSONL compatíveis com `agent_evidence.py`. | Validada | Testes de telemetria |
| ASM-002 | A disponibilidade do modelo pode ser desconhecida sem ser tratada como disponível. | Validada | Guarda de roteamento |

## Perguntas abertas

| ID | Pergunta | Status | Decisão/resposta |
|---|---|---|---|
| Q-001 | A telemetria precisa aparecer na UI/API do Agent Bridge? | Resolvida | Não; o artefato local é suficiente para esta mudança. |

## Decisões resolvidas

- O AISDD mantém o subtotal delegado em `delegated_subtotal` e a parcela
  indisponível em `unavailable`; o custo do chat principal permanece no
  `task-window-report.json`.
- O formatter do projeto consumidor não é tratado como requisito do fluxo
  AISDD; `verification.json` continua sendo um artefato gerado pelo script.
