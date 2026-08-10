---
title: Delegação opcional de modelos externos via OpenCode no AISDD
slug: delegacao-externa-opencode-no-aisdd
status: promoted
created_at: 2026-08-08
updated_at: 2026-08-08
source: conversa com o usuário e inspeção do repositório AISDD/Agent Bridge MCP
---

# Delegação opcional de modelos externos via OpenCode no AISDD

## Resumo

Permitir que o AISDD delegue uma role para um modelo externo executado pelo
OpenCode através do Agent Bridge MCP, somente quando essa opção estiver
explicitamente configurada no roteamento por role e classificação T0–T4.

A integração é opcional. A ausência do MCP, indisponibilidade do OpenCode,
modelo ausente, permissão, rate limit, franquia esgotada ou qualquer outra falha
encerra somente a tentativa externa. A cadeia continua com dois fallbacks:

1. fallback específico OpenAI da role/classificação;
2. fallback geral já existente no AISDD.

O effort do modelo externo não será enviado como campo separado: ele faz parte
do identificador do modelo externo, como `provedor/modelo#max`. O campo atual
`reasoning_effort` continua associado ao fallback OpenAI.

## Detalhes confirmados

- O Agent Bridge MCP está em `D:/codex/agent-bridge-mcp`.
- O MCP expõe `external_models`, `delegate_start`, `delegate_wait` e
  `delegate_cancel`.
- `external_models` foi chamado com o workspace do AISDD e respondeu com
  sucesso, incluindo modelos ativos dos provedores `opencode` e `openrouter`.
- `delegate_start` recebe `workspace`, `prompt`, `profile`, `model`, identidade
  opcional/idempotência e timeout; não recebe effort separado.
- O modelo externo só pode ser usado se aparecer na resposta de
  `external_models`, com correspondência exata do identificador.
- Se a checagem de disponibilidade falhar ou o modelo não aparecer, não se deve
  chamar `delegate_start`; o fluxo segue para o fallback OpenAI.
- A primeira versão usará exclusivamente `profile = "read"`.
- Delegações externas de escrita ficam fora do escopo atual para evitar risco de
  workspace parcialmente alterado.
- O fallback externo → OpenAI não substitui o fallback geral existente.
- Depois que a cadeia avança para o fallback OpenAI, não se tenta novamente o
  modelo externo na mesma execução.
- Cada tentativa e falha deve ser auditável: modelo externo, motivo, modelo
  OpenAI de fallback, `reasoning_effort` usado e resultado final.
- Modelos externos podem ser adicionados à tabela de custos antes de existir
  telemetria de tokens. Sem preço ou tokens confiáveis, o custo permanece
  `not-available`, nunca zero.
- A telemetria de tokens dos jobs Agent Bridge/OpenCode fica fora do primeiro
  escopo funcional.

## Hipóteses e inferências

- O modelo externo será representado por uma configuração explícita de provedor,
  modelo e fallback dentro do perfil da role ou de seu override por classe.
- O AISDD resolve role/classificação e envia ao MCP somente o modelo externo
  final, o prompt, o workspace e `profile = "read"`.
- `external_models` será a guarda de disponibilidade antes de cada tentativa,
  sem modo de bypass para modelo não descoberto.
- O job externo será acompanhado por `delegate_wait` até estado terminal ou
  timeout controlado; qualquer falha seguirá para o fallback OpenAI.
- A alteração provavelmente é T3 por introduzir executor externo opcional,
  cadeia de fallback, novas regras de roteamento e impacto em evidências,
  custos e documentação.

## Contexto do projeto considerado

- `scripts/model_routing.py` resolve roles, overrides por classe, disponibilidade
  e fallback de roteamento.
- `assets/templates/model-routing.toml` possui perfis por role e overrides
  `by_class`, além de um bloco global `[fallback]`.
- O contrato v2 exige Work Packages, evidência de delegação e separação entre
  execução/fallback e custo indisponível.
- `ADR-0001-delegation-contract-v2.md` determina roteamento sensível à classe e
  não inventa runtime externo.
- `ADR-0002-telemetry-manifest-and-routing-validation.md` separa evidência de
  fallback, subtotal delegado e parcelas `unavailable`.
- O Agent Bridge mantém jobs em memória, exige workspace permitido e oferece
  políticas separadas de leitura e escrita.

## Compatibilidade e conflitos

- Sem configuração externa, o comportamento atual do AISDD deve permanecer
  inalterado.
- O MCP não pode ser dependência obrigatória: falhas nele afetam apenas rotas
  externas explicitamente configuradas.
- A nomenclatura atual do repositório usa `reasoning_effort` em
  `scripts/model_routing.py` e no template. Essa nomenclatura será preservada;
  não haverá renomeação nesta alteração.
- O fallback global atual usa `model = "inherit"` e
  `reasoning_effort = "inherit"`, enquanto o contrato diz que `inherit` não é
  uma capability. A implementação precisa preservar o significado atual do
  fallback geral sem confundi-lo com uma role configurada.
- O Agent Bridge não fornece tokens ou custo de execução no contrato atual; o
  custo externo não pode ser estimado por analogia com rollout OpenAI.

## Perguntas em aberto

1. O bloco externo opcional abaixo deve ser aceito dentro de cada
   `[roles.<role>.by_class.<Tn>]`, ou em uma tabela paralela por role/classe?
2. Os campos atuais `model`, `reasoning_effort` e `tier` devem sempre representar
   o fallback OpenAI quando existir um bloco `[external]`?
3. O fallback geral deve ser tentado tanto quando `delegate_start` falhar antes
   de criar o job quanto quando o job falhar depois de iniciado?
4. O prompt enviado ao OpenCode deve incluir explicitamente role, classe,
   Work Package, critérios de aceitação e restrições AISDD?
5. A evidência v2 deve guardar `job_id`, `session_id`, modelo descoberto,
   eventos terminais e resultado em `delegation-evidence.json`?
6. A tabela de custos deve aceitar uma entrada externa sem preço, com
   `not-available`, ou deve ter uma seção separada por provedor?
7. O teste inicial deve executar uma delegação real `read` contra o OpenCode,
   além de testar descoberta e fallback simulado?

## Evidências de teste já executadas

- `external_models` encontrou `opencode/deepseek-v4-flash-free` como modelo
  ativo no workspace `D:/codex/aisdd`.
- Uma delegação real com esse modelo e `profile = "read"` foi aceita,
  executou leituras no AISDD, retornou um resumo útil para continuar o fluxo e
  terminou com `changed_paths = []`.
- Uma delegação com `opencode/model-that-does-not-exist` foi aceita pelo MCP,
  mas falhou na execução com `RUNTIME_UNAVAILABLE`. A integração do AISDD deve
  evitar esse desperdício fazendo a checagem de `external_models` antes de
  chamar `delegate_start`.
- Uma delegação direta com `profile = "write"` foi aceita pelo MCP e concluiu
  sem alterações porque o prompt não pediu escrita. Portanto, a restrição
  somente leitura precisa ser imposta pelo AISDD antes da chamada; não deve
  depender de o Agent Bridge rejeitar o perfil.

## Testes automatizados obrigatórios

Os testes devem fazer parte da implementação, não ser uma verificação manual
posterior:

1. Sem `[external]`, o fluxo atual OpenAI permanece inalterado.
2. Com `[external]`, `model`, `reasoning_effort` e `tier` continuam sendo o
   fallback OpenAI da role/classificação.
3. `external_models` encontra o identificador externo exato configurado.
4. Modelo ausente em `external_models` não chama `delegate_start` e aciona o
   fallback OpenAI específico.
5. Falha de `external_models` aciona o fallback OpenAI específico.
6. `delegate_start` recebe o modelo completo e `profile = "read"`.
7. Uma rota externa com `profile = "write"` é rejeitada pelo AISDD antes de
   chamar o MCP.
8. Falha de `delegate_start` aciona o fallback OpenAI específico.
9. Falha terminal observada por `delegate_wait` aciona o fallback OpenAI.
10. Se o fallback OpenAI específico falhar, o fallback geral atual continua.
11. Depois de avançar para um fallback, o externo não é tentado novamente.
12. Delegação `read` bem-sucedida retorna texto e metadados para o fluxo
    principal continuar usando o resultado.
13. Delegação `read` bem-sucedida não altera o workspace; `changed_paths` deve
    permanecer vazio.
14. A evidência registra modelo externo, `job_id`, `session_id`, estado,
    fallback usado e motivo de falha quando aplicável.
15. Ausência de tokens/preço externo permanece `not-available`, nunca zero.

O teste real com DeepSeek já demonstrou os itens 3, 6, 12 e 13 no Agent Bridge.
Os testes do roteador e da cadeia de fallback ainda dependem da implementação
da integração no AISDD.

## Formato de roteamento para confirmação

O roteamento OpenAI atual continua definindo o fallback da role/classificação:

```toml
[roles.planner.by_class.T1]
model = "gpt-5.6-luna"
reasoning_effort = "medium"
tier = "economy"

[roles.planner.by_class.T4]
model = "gpt-5.6-terra"
reasoning_effort = "max"
tier = "robust"
```

Quando a classificação usar um modelo externo, a proposta é manter os campos
atuais como fallback OpenAI e adicionar uma tabela opcional `external`:

```toml
[roles.planner.by_class.T1]
model = "gpt-5.6-luna"
reasoning_effort = "medium"
tier = "economy"

[roles.planner.by_class.T1.external]
provider = "agent-bridge"
model = "opencode/gpt-os#medium"
profile = "read"

[roles.planner.by_class.T4]
model = "gpt-5.6-terra"
reasoning_effort = "max"
tier = "robust"

[roles.planner.by_class.T4.external]
provider = "agent-bridge"
model = "opencode/gpt-os#max"
profile = "read"
```

Fluxo dessa configuração:

1. resolver role e classificação;
2. detectar a tabela opcional `[external]` e `provider = "agent-bridge"`;
3. chamar `external_models`;
4. exigir correspondência exata de `model`;
5. chamar `delegate_start` somente com `profile = "read"`;
6. acompanhar o job com `delegate_wait`;
7. em qualquer falha, usar os campos `model` e `reasoning_effort` da própria
   role/classificação no runtime OpenAI;
8. se esse fallback também falhar, preservar o fallback geral atual.

Nesse formato não são criados nomes novos para o fallback: os campos atuais da
role continuam sendo a rota OpenAI, e `[external]` é apenas uma rota opcional
que tem precedência quando estiver disponível.

## Próximo passo

Confirmar o formato de roteamento acima e responder somente as perguntas que
alteram o contrato. O perfil `write` permanece fora do primeiro escopo.

## AISDD promotion

Promoted to [`specs/delegacao-externa-opencode-no-aisdd/`](../../specs/delegacao-externa-opencode-no-aisdd/) when the formal spec was created.
