# ExecPlan: Playwright validation guidance

## Estado

Classe: T1
Fase: Validation

## Contexto e restrições

Mudança T1 na documentação operacional da skill. Manter Playwright recomendado, porém opcional, e não instalar ferramentas automaticamente.

## Milestones

### M1 — Orientação de validação de interface

- [x] Objetivo: registrar seleção de ferramenta e níveis de evidência.
- Arquivos: `SKILL.md`, `references/interface-validation.md`.
- Dependências: nenhuma.
- Passos: adicionar regra principal e referência detalhada; sincronizar a cópia instalada.
- Validação: validar a estrutura da skill e comparar os arquivos instalados com os do repositório.
- Risco/rollback: orientação excessivamente rígida; reverter os dois arquivos alterados.
- Concluído quando: ambas as cópias forem idênticas e a validação passar.

## Tarefas rastreáveis

| ID | Milestone | Critérios atendidos | Arquivos previstos | Dependências | Status |
|---|---|---|---|---|---|
| T-001 | M1 | AC-001, AC-002 | `SKILL.md`, `references/interface-validation.md` | Nenhuma | Concluída |

Tarefas com arquivos em comum ou dependência explícita não podem ser executadas em paralelo.

## Descobertas e replanejamento
