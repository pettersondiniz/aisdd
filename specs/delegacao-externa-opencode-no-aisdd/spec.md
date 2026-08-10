# Delegação externa OpenCode somente leitura

Contrato AISDD da feature: v2

## Objetivo

Adicionar ao AISDD uma rota opcional para delegar tarefas read-only a modelos
expostos pelo Agent Bridge MCP/OpenCode, mantendo a rota OpenAI existente e os
dois níveis de fallback.

## Comportamento esperado

Uma rota externa só existe em `[roles.<role>.by_class.<Tn>.external]`. Os campos
`model`, `reasoning_effort` e `tier` continuam sendo o fallback OpenAI específico.
O bloco externo contém `provider = "agent-bridge"`, um `model` opaco e
`profile = "read"`.

O identificador externo é comparado literalmente ao `id` retornado por
`external_models`. Não há parsing, alias, regex, remoção ou normalização de
`#effort`; `provider/model` e `provider/model#max` são IDs distintos.

Fluxo: resolver role/classe → descobrir modelos → exigir ID exato → iniciar
`delegate_start` read → acompanhar `delegate_wait` → aceitar somente resultado
terminal sem `changed_paths` → retornar texto/metadados. Qualquer falha segue
para o fallback OpenAI específico; se ele falhar, segue para o fallback geral.
O modelo externo não é tentado novamente na mesma execução.

## Regras e invariantes

- Sem `[external]`, o comportamento atual não muda.
- `external_models` sempre ocorre antes de `delegate_start`.
- Falha de descoberta ou modelo ausente não chama `delegate_start`.
- `provider` deve ser `agent-bridge`; `profile` deve ser `read`.
- Uma configuração `write` é rejeitada antes de qualquer chamada MCP.
- `changed_paths` não vazio invalida o resultado read-only.
- Resultado externo não deve ser tratado como rollout OpenAI.
- Tokens/preço ausentes permanecem `not-available`, nunca zero.
- O Agent Bridge não é alterado nesta feature.

## Interfaces afetadas

- `scripts/model_routing.py`: resolver rota externa opcional sem quebrar a saída OpenAI existente.
- Novo adapter cliente do Agent Bridge: descoberta, start, wait e resultado.
- Template de roteamento e documentação do contrato.
- Evidência v2: tentativa externa, job/session, estado, mudanças, fallback e custo indisponível.

## Fora de escopo

Delegação externa `write`, alteração do Agent Bridge, telemetria de tokens
OpenCode, retry externo, UI, cobrança real e migração automática de specs v1.

## Critérios de aceitação

- [x] AC-001: Sem `[external]`, o roteamento OpenAI atual permanece inalterado.
- [x] AC-002: `model`, `reasoning_effort` e `tier` continuam sendo o fallback OpenAI.
- [x] AC-003: A rota externa é resolvida por role e classificação.
- [x] AC-004: `external_models` é chamado antes de `delegate_start`.
- [x] AC-005: O matching do ID externo é literal e completo.
- [x] AC-006: Modelo ausente não chama `delegate_start` e usa fallback OpenAI.
- [x] AC-007: Falha de descoberta usa fallback OpenAI.
- [x] AC-008: `delegate_start` recebe workspace, prompt, model e `profile=read`.
- [x] AC-009: `profile=write` é rejeitado antes do MCP.
- [x] AC-010: Falha de start usa fallback OpenAI.
- [x] AC-011: Falha, timeout ou cancelamento no wait usa fallback OpenAI.
- [x] AC-012: Falha do fallback específico preserva o fallback geral.
- [x] AC-013: Não há nova tentativa externa após fallback.
- [x] AC-014: Sucesso read retorna texto e metadados ao fluxo principal.
- [x] AC-015: Sucesso read exige `changed_paths=[]`.
- [x] AC-016: Evidência registra modelo, job/session, estado, erro, fallback e resultado.
- [x] AC-017: Custo externo sem telemetria é `not-available`, nunca zero.
- [x] AC-018: Rotas sem `[external]` não são afetadas por MCP indisponível.
- [x] AC-019: Todos os critérios têm testes `@spec:AC-xxx` e prova em `verification.json`.

## Decisões resolvidas

- A nomenclatura existente `reasoning_effort` é preservada.
- O esforço externo fica embutido no ID quando o catálogo o expuser.
- A checagem `external_models` é obrigatória.
- A primeira versão é somente leitura.
