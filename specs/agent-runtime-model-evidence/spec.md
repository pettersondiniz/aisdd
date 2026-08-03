# Agent runtime model evidence

## Objetivo

Registrar em evidências AISDD o modelo e o effort realmente resolvidos para cada subagente, quando o rollout local do Codex os expuser.

## Contexto

O pedido de spawn prova intenção, mas pode divergir do runtime. O `turn_context` do rollout filho é a melhor evidência local recuperável.

## Comportamento esperado

AISDD consulta um utilitário local após a conclusão do subagente. Com um rollout filho identificado de forma única, o utilitário retorna modelo e effort do último `turn_context`. Com metadados ausentes, inacessíveis ou ambíguos, não retorna uma suposição.

## Fluxos principais

## Regras e invariantes

- O utilitário é somente leitura e não altera sessões nem configurações.
- A correlação por papel em runtimes legados exige identificador do pai ou outro seletor que torne o resultado único.
- `unknown` é preferível a inferir o modelo a partir da resposta do agente ou da UI.

## Casos de borda e falhas

## Interfaces e persistência afetadas

## Requisitos não funcionais

## Fora de escopo

- Provar criptograficamente o modelo usado pelo backend.
- Alterar o roteamento, o fallback ou a disponibilidade dos modelos.

## Critérios de aceitação

- [ ] AC-401: Dado um rollout filho identificado de forma única com `turn_context`, a consulta retorna o modelo e effort efetivos registrados.
- [ ] AC-402: A consulta lê o modelo e effort de `collaboration_mode.settings` quando a estrutura do runtime os armazenar ali.
- [ ] AC-403: Com rollouts ausentes ou ambíguos, a consulta retorna estado honesto, sem escolher ou inferir um modelo.
- [ ] AC-404: Dado o ID de um rollout filho legado, a consulta seleciona esse rollout sem depender de `agent_path`.

Cada critério deve ser observável e indicar o comportamento que um teste anotado
com `@spec:AC-xxx` comprovará.

## Suposições

| ID | Suposição | Status | Dono/validação |
|---|---|---|---|
| ASM-001 | Rollouts locais ficam disponíveis em `~/.codex/sessions` quando o runtime persiste sessões. | Validada localmente | Teste do utilitário |

## Perguntas abertas

| ID | Pergunta | Status | Decisão/resposta |
|---|---|---|---|
| Q-001 |  | N/A | O fluxo usa `unknown` quando o runtime não persistir metadados. |

## Decisões resolvidas

- D-001: Usar `turn_context` do rollout filho como melhor evidência local; manter pedido do spawn como evidência de intenção.
