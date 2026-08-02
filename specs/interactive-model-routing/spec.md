# Interactive model routing

## Objetivo

Permitir que a AISDD recomende modelos e efforts globais de forma consultável e conduza atualizações de mapeamento por conversa confirmada.

## Contexto

## Comportamento esperado

- O roteador lê a configuração global quando ela existe e usa o modelo padrão sem criá-la quando não existe.
- Dada a disponibilidade do runtime, ele lista sugestões por faixa, incluindo identificadores com prefixos de provedores.
- Quando não houver modelo configurado disponível, o fluxo exige herdar modelo e effort do chat e perguntar ao usuário antes de qualquer atualização.

## Fluxos principais

## Regras e invariantes

## Casos de borda e falhas

## Interfaces e persistência afetadas

## Requisitos não funcionais

## Fora de escopo

- Criar ou editar automaticamente `~/.codex/aisdd/model-routing.toml`.
- Declarar disponibilidade de modelo sem evidência do runtime atual.

## Critérios de aceitação

- [x] AC-101: O roteador sugere um modelo dedicado equivalente disponível quando o configurado não está disponível.
- [x] AC-102: O roteador retorna fallback de herança do chat, sem modelo Terra fixo.
- [x] AC-103: Consultar o roteador não cria configuração global do usuário.

Cada critério deve ser observável e indicar o comportamento que um teste anotado
com `@spec:AC-xxx` comprovará.

## Suposições

| ID | Suposição | Status | Dono/validação |
|---|---|---|---|
| ASM-001 | O agente principal consegue consultar a disponibilidade exposta pelo runtime antes de delegar. | Validada | A referência define o formato de entrada. |

## Perguntas abertas

| ID | Pergunta | Status | Decisão/resposta |
|---|---|---|---|
| Q-001 |  | Resolvida | O usuário atualiza mapeamentos somente por conversa confirmada. |

## Decisões resolvidas
