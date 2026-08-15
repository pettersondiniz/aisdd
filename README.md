# AISDD

AISDD (*AI Software Delivery & Design*) é uma skill reutilizável do Codex para desenvolvimento orientado por especificações, planos executáveis, evidências, revisão independente e documentação viva.

## Instalação global

No Windows, copie a pasta `aisdd` para:

```text
C:\Users\<seu-usuário>\.agents\skills\aisdd
```

No macOS/Linux:

```text
~/.agents/skills/aisdd
```

Para disponibilizar os agentes especializados globalmente, copie também `agents/*.toml` para `~/.codex/agents/`. Para um projeto específico, use `.codex/agents/` dentro do repositório.

## Uso

```text
$aisdd Inicialize este repositório para o fluxo AISDD.
$aisdd Crie a especificação da autenticação com Entra ID.
$aisdd Implemente specs/autenticacao-entra-id.
$aisdd Audite o repositório e verifique drift.
```

O inicializador cria `AGENTS.md`, `docs/` e `specs/` sem sobrescrever arquivos existentes. O criador de features cria uma pasta com spec, plano, status e evidências.

## Fluxo recomendado

1. Classifique a mudança em T0–T4.
2. Especifique comportamento e critérios de aceitação.
3. Faça design/ADR quando houver impacto arquitetural.
4. Planeje milestones pequenos e retomáveis.
5. Delegue exploração e revisão a agentes independentes.
6. Implemente em etapas, adicionando testes.
7. Execute os testes pelo verificador de feature, revise, cheque drift e registre evidências.

## Contrato de delegação

A partir de T1, trabalho delegável tem owner e role especializada. Um T0 só
fica fora do contrato quando for comprovadamente mecânico e não delegável; em
evidência v2, a conclusão exige `mechanical_non_delegable.approved` com
justificativa auditável ou uma role especializada. `orchestrator/coordinate`
nunca cobre trabalho delegável. Se for delegável, o Orchestrator não o executa. O Orchestrator coordena,
acompanha dependências e consolida evidências; não implementa código, altera
testes, executa build, corrige achados nem faz a validação final. Em T1+ v1, o
Planner produz o plano técnico, o plano de execução e o grafo declarativo nos
artefatos v1; T1/T2 incluem Planner, Implementer, Test Engineer e Verifier, T2 também inclui Reviewer, e T3/T4
incluem ainda Architect e Documentation Reviewer. Em T2, Documentation Reviewer
é obrigatório somente quando houver impacto documental; sem esse impacto, a role
não é um requisito adicional. Em T3/T4, Documentation Reviewer é obrigatório
por classe. `test-engineer` cria ou altera testes, `verifier` executa a validação
final e `reviewer` revisa de forma independente. `tester` permanece alias v1 de
`test-engineer`. No contrato v2, Planner pode materializar somente
`specs/<slug>/spec.md`, `plan.md`, `status.md`, `work-packages.json` e
`delegation-evidence.json`; isso exclui `evidence.md`, `verification.json`,
`task-window.json`, código e testes. Architect pode registrar somente ADRs em
`docs/architecture/decisions/ADR-*.md`.

Um blocker, critério falho ou correção exigida pelo Test Engineer, Verifier,
Reviewer ou Documentation Reviewer impede a conclusão e abre um novo WP de
correção para a role adequada. O fluxo retorna ao Implementer e repete Test
Engineer, Verifier e os revisores aplicáveis antes de retomar Completion.

Em T1+ v1, `plan.md` é a fonte normativa do grafo declarativo de tarefas/WPs,
owners, dependências e paralelização. `evidence.md` apenas resume owners e
dependências e registra provas; não redefine o grafo.

Se uma role ou agente não estiver disponível, o trabalho fica `BLOCKED` até
decisão humana. Edição direta só é permitida como fallback explicitamente
aprovado e auditado com motivo, tentativas, escopo e resultado; trivialidade ou
silêncio não autorizam bypass.

Novas specs usam contrato v2 por padrão: `scripts/create_feature.py` grava o
marcador canônico e cria os esqueletos `work-packages.json` e
`delegation-evidence.json`. Specs existentes/legadas sem marcador, ou criadas
explicitamente com `--contract v1`, permanecem em v1 como modo de
compatibilidade; usam os artefatos históricos e não exigem os JSON v2. Não há
migração automática.

O validador aplica v2 somente quando o marcador literal
`Contrato AISDD da feature: v2` (ou um alias documentado) ocupa uma única linha em `spec.md`,
`plan.md` ou `status.md`; ausência ou marcador v1 permanece compatibilidade v1.
Valide os artefatos v2 com:

O marcador canônico é `Contrato AISDD da feature: v2`. Para interoperabilidade,
o detector também aceita, em uma linha própria e sem distinção de maiúsculas,
os aliases `Contrato AISDD: v2`, `AISDD contract: v2`, `AISDD-contract: v2`,
`AISDD_contract: v2`, `delegation contract: v2`, `delegation-contract: v2`,
`delegation_contract: v2`, `contract: v2`, `contract-version: v2` e
`contract_version: v2`. Os aliases aceitam `:` ou `=` e `2` ou `v2`; prefira o
marcador canônico para evitar ambiguidade.

```text
python scripts/delegation_contract.py specs/<feature> --json
```

Em uma feature v2, o validador exige a evidência v2; `--graph-only` é um modo
explícito somente para validar o grafo. Ele não inventa nem executa um runtime
externo de agentes.

## Rastreabilidade mecânica

Para features T2+, cada critério de aceitação usa um ID global (`AC-001`), aparece em uma
tarefa (`T-001`) e é coberto por pelo menos um teste anotado com `@spec:AC-001`. A evidência
de execução não é preenchida manualmente: execute o comando de teste real pelo verificador,
que gera `verification.json` e rejeita testes ausentes, pulados ou prova obsoleta.

```text
python scripts/verify_feature.py . specs/exemplo -- <comando-de-teste-real>
python scripts/validate_feature.py . specs/exemplo
python scripts/check_drift.py .
```

## Mudanças de interface

Na descoberta, AISDD identifica páginas, componentes, formulários, estilos, design system e
comportamento responsivo. Quando houver interface e a skill `impeccable` não estiver instalada,
AISDD propõe sua instalação — nunca instala sem autorização. Quando ela estiver disponível, os
agentes usam comandos adequados ao papel: planejamento (`shape`), implementação (`craft` e
comandos especializados), teste (`audit`), revisão (`critique`/`polish`) e documentação (`document`/`extract`).

## Compatibilidade Codex

O pacote segue o formato documentado atualmente: skill com `SKILL.md` e frontmatter `name`/`description`; agentes personalizados como TOML independentes com `name`, `description` e `developer_instructions`. Consulte `references/codex-official-format.md` para a base oficial usada na montagem.

## Validação local

```text
python scripts/validate_feature.py . specs/exemplo
python scripts/check_drift.py .
```

O pacote não inclui dependências externas.
## Telemetria de delegações

Em uma feature v2, registre a declaração de cada Work Package e depois colete
a evidência observável do rollout:

```text
python scripts/delegation_telemetry.py init --output specs/<feature>/delegation-evidence.json --work-packages specs/<feature>/work-packages.json
python scripts/delegation_telemetry.py record --output specs/<feature>/delegation-evidence.json --work-package WP-001 --role implementer --agent-id <id> --requested-model <model> --requested-effort <effort>
python scripts/delegation_telemetry.py collect --output specs/<feature>/delegation-evidence.json --sessions-root <sessions-root> --pricing-config <pricing-config.toml> --json
```

O collector só usa rollouts explicitamente associados, preserva o modelo e o
effort efetivos, e separa `delegated_subtotal` de `unavailable`. A guarda de
roteamento pode ser usada antes do spawn com `model_routing.py --require-available`;
um mismatch exige override e motivo explícito. O chat principal continua sendo
medido por `task_window.py` quando a feature declarar essa atribuição.
## Roteamento externo read-only

Uma feature pode declarar uma rota externa somente em
`roles.<role>.by_class.<Tn>.external`. O adapter deve consultar
`external_models` antes de `delegate_start`, exigir o `id` literal completo e
iniciar o trabalho com `profile=read`. `write` é rejeitado antes de qualquer
chamada MCP; resultado com `changed_paths` não vazio também é rejeitado.

Falha de descoberta, modelo ausente, start, wait, timeout, cancelamento ou
mudança reportada usa primeiro o fallback OpenAI específico da role/classe e
depois o fallback geral. Não há retry externo na mesma execução. A rota externa
é opcional: sem `[external]`, o caminho OpenAI não consulta o MCP e permanece
compatível com instalações sem Agent Bridge.

O roteamento é somente leitura e não altera configuração global, sessões do
runtime nem projetos consumidores. Custos, tokens ou modelo efetivo externos
sem telemetria são registrados como `not-available`, nunca como zero. Registre
modelo, job/session, estado, erro, mudanças, fallback e resultado em evidência
v2; não trate o resultado externo como rollout OpenAI.
