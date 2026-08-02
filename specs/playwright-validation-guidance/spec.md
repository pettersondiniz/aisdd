# Playwright validation guidance

## Objetivo

Definir validação de interface que priorize Playwright sem exigir `playwright-cli` ou MCP.

## Contexto

## Comportamento esperado

- A skill verifica as capacidades de navegador antes de planejar evidências de interface.
- `playwright-cli` é a opção preferida para fluxos repetíveis; o MCP atende inspeção e depuração interativas.
- Quando as ferramentas não estiverem disponíveis, a skill orienta a melhor validação disponível e registra a limitação.

## Fluxos principais

## Regras e invariantes

## Casos de borda e falhas

## Interfaces e persistência afetadas

## Requisitos não funcionais

## Fora de escopo

- Instalar ou configurar Playwright automaticamente.
- Exigir CLI e MCP para o mesmo cenário.

## Critérios de aceitação

- [x] AC-001: A skill define a ordem de escolha entre `playwright-cli`, MCP, ferramentas do projeto e ausência de navegador.
- [x] AC-002: A skill exige que limitações de validação sejam registradas e proíbe alegar prova em navegador sem execução real.

Cada critério deve ser observável e indicar o comportamento que um teste anotado
com `@spec:AC-xxx` comprovará.

## Suposições

| ID | Suposição | Status | Dono/validação |
|---|---|---|---|
| ASM-001 | A instalação existente continua a carregar `SKILL.md` e referências relativas. | Validada | Estrutura atual da skill |

## Perguntas abertas

| ID | Pergunta | Status | Decisão/resposta |
|---|---|---|---|
| Q-001 |  | Resolvida | Nenhuma decisão adicional necessária. |

## Decisões resolvidas
