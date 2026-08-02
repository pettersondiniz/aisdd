# ExecPlan: Mandatory AISDD triage template

## Estado

Classe: T1
Fase: Implementation

## Contexto e restrições

Mudança T1 no modelo de orientação de projetos. A regra deve ser curta e direcionar a classificação proporcional.

## Milestones

### M1 — Atualizar o modelo de projeto

- [x] Objetivo: incluir a triagem AISDD obrigatória no modelo.
- Arquivos: `assets/templates/AGENTS.md`, `tests/test_interface_validation.py`.
- Dependências: nenhuma.
- Passos: atualizar a cópia do repositório e a instalada; testar o conteúdo do modelo.
- Validação: executar os testes rastreáveis, validação de feature e check de drift.
- Risco/rollback: regra excessivamente rígida; reverter somente o bloco de triagem.
- Concluído quando: o modelo e a cópia instalada coincidirem e as validações passarem.

## Tarefas rastreáveis

| ID | Milestone | Critérios atendidos | Arquivos previstos | Dependências | Status |
|---|---|---|---|---|---|
| T-001 | M1 | AC-001, AC-002 | `assets/templates/AGENTS.md`, `tests/test_interface_validation.py` | Nenhuma | Concluída |

Tarefas com arquivos em comum ou dependência explícita não podem ser executadas em paralelo.

## Descobertas e replanejamento
