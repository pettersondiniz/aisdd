# ADR-0003: Roteamento externo somente leitura via Agent Bridge

- Status: accepted
- Data: 2026-08-08

## Contexto

O AISDD precisa permitir delegação opcional a modelos expostos pelo Agent
Bridge MCP/OpenCode sem tornar essa dependência obrigatória e sem alterar o
projeto do Agent Bridge. A rota existente de cada role deve continuar sendo o
fallback específico, seguida pelo fallback geral.

## Decisão

A rota externa só é lida de `[roles.<role>.by_class.<Tn>.external]` e exige
`provider = "agent-bridge"` e `profile = "read"`. Antes de iniciar um job, o
adapter chama `external_models` e compara o `id` configurado literalmente,
incluindo qualquer sufixo como `#max`. Em seguida chama `delegate_start` e
acompanha o job com `delegate_wait`.

Somente um estado terminal bem-sucedido com `changed_paths = []` é aceito.
Falha de configuração, descoberta, start, wait, timeout, cancelamento ou
mudança reportada segue para o OpenAI específico e depois para o fallback geral.
Não há retry externo na mesma execução. O adapter é injetável e não importa
nem modifica o Agent Bridge quando a rota externa não está configurada.

## Alternativas consideradas

- Tornar o Agent Bridge obrigatório: rejeitada por quebrar instalações sem MCP.
- Normalizar IDs ou separar esforço do ID: rejeitada porque o catálogo define o
  identificador opaco e `provider/model` e `provider/model#max` são distintos.
- Permitir perfil `write`: rejeitada por estar fora do escopo desta feature.

## Consequências

Rotas sem `[external]` preservam o caminho OpenAI e não fazem chamadas MCP.
Resultados externos carregam job/session, estado, erro, mudanças e resultado.
Tokens e preços externos sem telemetria são registrados como `not-available`,
nunca como zero. A integração requer um cliente MCP fornecido pelo chamador.

## Rollback ou reversão

Remover os blocos `[external]` do roteamento. O código mantém o caminho legado
quando esses blocos não existem; nenhuma alteração no Agent Bridge é necessária.
