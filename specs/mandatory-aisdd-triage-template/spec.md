# Mandatory AISDD triage template

## Objetivo

Garantir que todo projeto inicializado com AISDD receba uma regra obrigatória de triagem antes de alterações de software.

## Contexto

## Comportamento esperado

- O modelo de `AGENTS.md` exige classificação T0–T4 antes de alterações de software.
- T1+ direciona ao AISDD; T2+ exige o roteamento de subagentes, com limitação registrada quando o runtime não os suportar.

## Fluxos principais

## Regras e invariantes

## Casos de borda e falhas

## Interfaces e persistência afetadas

## Requisitos não funcionais

## Fora de escopo

- Aplicar retroativamente o modelo a projetos já inicializados.

## Critérios de aceitação

- [x] AC-001: O modelo instalado exige triagem T0–T4 e uso de AISDD para mudanças T1+.
- [x] AC-002: O modelo exige o roteamento de subagentes para T2+ ou o registro de indisponibilidade.

Cada critério deve ser observável e indicar o comportamento que um teste anotado
com `@spec:AC-xxx` comprovará.

## Suposições

| ID | Suposição | Status | Dono/validação |
|---|---|---|---|
| ASM-001 | Projetos novos são inicializados por `scripts/init_project.py`. | Validada | Script existente copia o modelo de `AGENTS.md`. |

## Perguntas abertas

| ID | Pergunta | Status | Decisão/resposta |
|---|---|---|---|
| Q-001 |  | Resolvida | A regra será aplicada somente aos novos projetos inicializados. |

## Decisões resolvidas
