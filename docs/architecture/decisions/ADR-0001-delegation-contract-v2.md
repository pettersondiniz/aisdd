# ADR-0001: Contrato versionado de delegação e Work Packages

## Status

Aceito para implementação local

## Contexto

A AISDD possui roles especializadas, mas o contrato atual é predominantemente textual. O agente principal pode editar diretamente em um fallback amplo, o Planner não precisa declarar um grafo de execução e a validação não confirma que as roles obrigatórias executaram suas responsabilidades.

Também existem specs legadas e evidências v1 em uso. Tornar os novos artefatos obrigatórios de forma retroativa causaria drift artificial e quebraria tarefas em andamento.

## Decisão

1. Novas specs usam o contrato v2 por padrão: `create_feature.py` grava o
   marcador v2 e cria `work-packages.json` e `delegation-evidence.json` como
   esqueletos incompletos.
2. O contrato v1 é modo de compatibilidade para specs existentes/legadas sem
   marcador e para features criadas explicitamente com `--contract v1`. Esses
   modos continuam válidos sem os JSON v2; o validador só aplica v2 quando há
   um marcador v2 válido.
3. O Planner atual produz o plano técnico e o plano de execução; não será criada uma nova role de planejamento.
4. A execução v2 usa Work Packages com owner, dependências, capabilities, escopo, critérios, estado e evidências.
5. Test Engineer e Verifier são roles distintas. `tester` permanece alias v1, mas não substitui as duas roles no modo v2 enforce.
6. O Orchestrator coordena e consolida, mas não executa capabilities de implementação, teste, build ou validação final.
7. Fallbacks são permitidos somente após aprovação explícita, com registro de motivo, indisponibilidade, tentativas, escopo permitido e resultado do trabalho direto; trivialidade ou silêncio nunca autorizam bypass.
8. O roteamento de modelo é sensível à classe quando solicitado; capabilities não dependem do modelo ou effort.
9. A cobertura mínima v2 é derivada da classe: T1 exige Planner, Implementer,
   Test Engineer e Verifier; T2 adiciona Reviewer e, quando o impacto
   documental for declarado pelo Planner/Orchestrator no `plan.md`, requer
   manualmente Documentation Reviewer; o validador v2 não infere essa role
   condicional. T3/T4 exigem Planner, Architect, Implementer, Test Engineer,
   Verifier, Reviewer e Documentation Reviewer por classe. T4 também exige
   aprovação humana auditável antes de qualquer etapa irreversível.
10. Em T0 v2, a conclusão exige uma declaração auditável
    `mechanical_non_delegable.approved: true` com justificativa ou uma role
    especializada observada; `orchestrator/coordinate` não é cobertura de
    trabalho delegável.
11. O fluxo de revisão é `Verifier → (Reviewer || Documentation Reviewer)`;
    os dois revisores só iniciam após o Verifier e podem rodar em paralelo
    quando os escopos forem independentes. Um blocker, critério falho ou
    correção exigida pelo Test Engineer também abre um novo WP e retorna ao
    Implementer; depois repetem-se Test Engineer, Verifier e os revisores
    aplicáveis. A aprovação T4 deve ocorrer antes de qualquer etapa
    irreversível; documentação declarativa não inventa timestamp operacional
    quando a evidência não o fornece.
12. Em T1+ v1, `plan.md` é a fonte normativa do grafo declarativo; `evidence.md`
    apenas resume owners/dependências e registra provas.

## Consequências

Specs v1 não precisam ser migradas. Em T1/T2 v1, o Planner usa
`plan.md` como fonte normativa para registrar um grafo declarativo, sem
exigir os JSON v2. Features v2 recebem validação mais estrita, grafo
determinístico e auditoria de roles. O repositório poderá validar o contrato,
mas não executará um runtime de agentes que não está presente nele.

O custo é manter leitores compatíveis com v1 e um caminho explícito de migração. A estratégia evita que uma atualização da skill invalide evidências históricas ou uma tarefa em andamento.

## Estratégia de migração v1/v2

| Situação | Contrato aplicado | Artefatos/roles | Migração automática |
|---|---|---|---|
| Specs v1 legadas ou explicitamente v1 | v1, grandfathered/compatibilidade | artefatos históricos atuais e alias `tester` | não; permanecem válidas sem WPs v2 |
| Novas features | v2 por default | marcador v2 e esqueletos `work-packages.json`, `delegation-evidence.json` | não migra specs existentes |
| Feature com marcador v2 | v2 | `work-packages.json`, `delegation-evidence.json` e roles canônicas, com validação fail-closed | não; ausência de marcador não é migrada |

1. Specs existentes continuam v1 quando não têm marcador ou declaram v1
   explicitamente. O marcador `Contrato AISDD da feature: v2` ativa o v2; o detector também aceita os aliases
   `Contrato AISDD: v2`, `AISDD contract: v2`, `AISDD-contract: v2`,
   `AISDD_contract: v2`, `delegation contract: v2`, `delegation-contract: v2`,
   `delegation_contract: v2`, `contract: v2`, `contract-version: v2` e
   `contract_version: v2`, com `:`/`=`, `2`/`v2` e comparação sem distinção de
   maiúsculas. O marcador canônico ou alias deve ocupar uma linha própria,
   com `v2`/`2` como token terminal; somente espaços finais e o prefixo de
   lista Markdown documentado são aceitos. Sufixos ou texto adicional, como
   `v2 extra`, `v2.0`, pontuação ou prosa, são rejeitados e preservam o default
   v1. Marcadores dentro de blocos fenced Markdown são ignorados antes da
   detecção; portanto, somente uma linha própria visível com token terminal
    `v2`/`2` pode ativar o v2. Sem marcador válido, a feature permanece em v1 de
   compatibilidade. Sufixos, prosa e marcadores em fences não ativam o v2.
2. Uma nova feature criada pelo scaffolding adiciona o marcador e cria os dois
   esqueletos v2 no mesmo change set; `--contract v1` é uma escolha explícita
   de compatibilidade e não cria esses arquivos. `validate_feature.py` passa a
   exigir grafo, digest, cobertura de roles e fallback auditável somente quando
   o marcador v2 estiver presente.
3. A migração é declarativa e local: o validador não regrava specs, não cria
   configuração global e não executa agentes. Um rollback remove o marcador do
   change set e retorna ao leitor v1, mantendo os arquivos v2 como dados não
   aplicados.

O plano humano permanece em `plan.md`; a ordem efetiva vem das dependências
declaradas nos WPs. A ausência de migração automática evita drift artificial em
evidências históricas.

## Histórico da decisão

A redação inicial deste ADR descrevia v1 como default e v2 como opt-in. Em
2026-08-07, essa regra foi corrigida para novas criações: o scaffolding novo
passa a v2, enquanto specs existentes/legadas e a feature
`specs/mandatory-delegation-contract`, explicitamente mantida em v1, não são
migradas nem passam a exigir artefatos v2.

## Rollback

Desativar o modo v2 e retornar ao leitor/validador v1. Preservar `spec.md`, `plan.md`, `status.md`, `evidence.md`, `verification.json` e os artefatos v2 já gerados como dados não aplicados.
