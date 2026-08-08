# ADR-0002: Manifesto de telemetria delegada e guarda de roteamento

## Status

Aceito para implementação local

## Contexto

O AISDD já possui resolução de evidência por rollout e um relatório separado
para o chat principal, mas não havia uma ligação machine-readable entre um
Work Package, o agente solicitado, o rollout observado e o subtotal delegado.
Também era possível recomendar uma configuração de modelo indisponível sem uma
guarda explícita no ponto de spawn.

## Decisão

1. O contrato v2 usa `delegation-evidence.json` como manifesto opt-in por
   feature. `delegation_telemetry.py` registra cada WP antes da execução e
   coleta a evidência depois do rollout.
2. O collector aceita somente seletores declarados (`rollout_id` ou `agent_id`),
   lê sessões e preços, e grava a saída fora da raiz de sessões. Ele não altera
   rollouts nem inclui eventos brutos no manifesto.
3. A saída mantém três estados distintos: evidência da execução/fallback,
   `delegated_subtotal` para custos observados e `unavailable` para parcelas
   necessárias que não podem ser calculadas. Indisponível nunca é zero.
4. A guarda aditiva de `model_routing.py` separa recomendação, pedido,
   disponibilidade e override. Um mismatch retorna `request-mismatch`; um
   override exige justificativa explícita. Disponibilidade desconhecida não é
   tratada como disponível.
5. O custo do chat principal continua no lifecycle explícito de
   `task_window.py`. O orquestrador deve executar `start`, `close` e
   `report --final`; nenhum marker de task é sintetizado pelo AISDD.
6. `verification.json` continua sendo propriedade exclusiva de
   `verify_feature.py`. Formatter do projeto consumidor não é dependência do
   collector nem do validador semântico.

## Alternativas rejeitadas

- Agregar todos os rollouts encontrados na sessão: poderia atribuir custo de
  outra task e esconder a ausência de correlação.
- Usar `telemetry-manifest.json` como um segundo contrato paralelo: duplicaria
  a fonte de verdade v2 já validada por `delegation_contract.py`.
- Transformar custo ausente em zero: produziria um total aparentemente preciso
  quando a telemetria está incompleta.
- Emitir `task_started`/`task_complete` artificialmente: confundiria eventos
  de runtime com marcadores de observabilidade.

## Compatibilidade e rollback

Specs v1 continuam sem exigir os arquivos v2. Remover o uso de
`delegation_telemetry.py` e da guarda mantém `agent_evidence.py`,
`task_window.py` e a CLI anterior disponíveis; os arquivos do manifesto podem
ser preservados como evidência histórica. O rollback não toca em
`agent-bridge-mcp`.

## Consequências

O orquestrador precisa registrar o WP imediatamente após o spawn e chamar o
collector ao fechar a execução. Em compensação, a ausência de modelo efetivo,
tokens ou preço fica explícita e auditável, e o custo delegado não é confundido
com o custo do chat principal.
