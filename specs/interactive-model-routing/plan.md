# ExecPlan: Interactive model routing

## Estado

Classe: T2
Fase: Implementation

## Contexto e restrições

Capacidade T2 que precisa funcionar em ambientes com nomes de modelos dedicados e sem gravar configuração global por conta própria.

## Milestones

### M1 — Consulta e orientação interativa

- [x] Objetivo: adicionar configuração padrão, roteador somente-leitura e fluxo conversacional.
- Arquivos: `SKILL.md`, `references/model-routing.md`, `assets/templates/model-routing.toml`, `scripts/model_routing.py`, testes.
- Dependências: Python 3.11+ para `tomllib`.
- Passos: consultar modelo global, correlacionar padrões de capacidade e instruir confirmação antes de editar.
- Validação: testes de roteamento, verificação de feature e check de drift.
- Risco/rollback: sugestão indevida de modelo; usar fallback de herança e não persistir mudanças.
- Concluído quando: todos os critérios tiverem testes anotados e o roteador não escrever no diretório do usuário.

## Tarefas rastreáveis

| ID | Milestone | Critérios atendidos | Arquivos previstos | Dependências | Status |
|---|---|---|---|---|---|
| T-001 | M1 | AC-101, AC-102, AC-103 | arquivos da M1 | Python 3.11+ | Concluída |

Tarefas com arquivos em comum ou dependência explícita não podem ser executadas em paralelo.

## Descobertas e replanejamento
