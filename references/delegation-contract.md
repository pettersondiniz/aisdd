# Contrato de delegação AISDD

## Escopo e versões

Este documento define o contrato operacional para tarefas delegáveis. Novas
specs usam v2 por padrão: o scaffolding grava o marcador v2 e cria os
esqueletos `work-packages.json` e `delegation-evidence.json`. O contrato v1 é
modo de compatibilidade para specs existentes/legadas e para features criadas
explicitamente com `--contract v1`; ausência de marcador ou marcador v1 é
aceito com os artefatos históricos (`spec.md`, `plan.md`, `status.md`,
`evidence.md` e `verification.json`) e não exige os JSON v2. Não há migração
automática.

O validador aplica o contrato v2 quando o marcador abaixo, emitido por padrão
para novas specs, ou um alias documentado ocupa uma linha própria em `spec.md`,
`plan.md` ou `status.md`:

```text
Contrato AISDD da feature: v2
```

O marcador canônico é o preferido. O validador também aceita, para preservar
interoperabilidade com rascunhos já existentes, os aliases técnicos
`Contrato AISDD: v2`, `AISDD contract: v2`, `AISDD-contract: v2`,
`AISDD_contract: v2`, `delegation contract: v2`, `delegation-contract: v2`,
`delegation_contract: v2`, `contract: v2`, `contract-version: v2` e
`contract_version: v2`. O detector é case-insensitive, aceita `:` ou `=` e
`2` ou `v2`; o marcador canônico ou alias deve ocupar uma linha própria, com
`v2`/`2` como token terminal. Somente espaços finais e o prefixo de lista
Markdown documentado são aceitos; sufixos ou texto adicional, como `v2 extra`,
`v2.0`, pontuação ou prosa, são rejeitados. O marcador é a única forma de
tornar os artefatos v2 obrigatórios; a ausência ou rejeição do marcador mantém
o modo de compatibilidade v1 e nunca migra uma spec automaticamente.

Em T1+ v1 legado ou explicitamente v1, o Planner mantém o plano técnico, o plano de execução e o grafo declarativo nos
artefatos v1 existentes, com `plan.md` como fonte normativa do grafo. `evidence.md`
apenas resume owners/dependências e registra provas; não redefine o grafo. Esses
níveis não exigem `work-packages.json` nem `delegation-evidence.json`; os dois
arquivos só são obrigatórios quando o marcador v2 estiver presente.

## Responsabilidades e proibições

O Orchestrator coordena o fluxo. Ele pode inspecionar contexto, selecionar e
acompanhar owners, delegar Work Packages, acompanhar dependências, consolidar
resultados e registrar evidências. T0 fica fora do contrato somente quando é
comprovadamente mecânico e não delegável; mesmo em T0, trabalho delegável não pode ser executado diretamente pelo Orchestrator.

O Orchestrator não pode executar as capabilities de implementação, escrita ou
alteração de testes, build, correção de código ou validação final. Ele também
não substitui Test Engineer, Verifier, Reviewer ou Documentation Reviewer. Um
blocker, critério falho ou correção exigida pelo Test Engineer, Verifier,
Reviewer ou Documentation Reviewer volta ao Orchestrator como informação e
gera um novo Work Package de correção para a role adequada. O fluxo retorna ao
Implementer e repete Test Engineer, Verifier e os revisores aplicáveis antes de
retomar Completion.

Se a role ou o agente exigido não estiver disponível, o Work Package fica
`BLOCKED` e aguarda decisão humana. O Orchestrator só pode executar diretamente
após uma aprovação explícita de fallback; a evidência deve registrar motivo,
agente indisponível, tentativas, escopo permitido e resultado. “Trivial” ou
silêncio não são motivos válidos.

A partir de T1, trabalho delegável deve ter owner explícito e role
especializada. O Planner existente é o owner do plano técnico e do plano de
execução; não existe uma segunda role de planejamento.

## Work Packages v2

`work-packages.json` é uma declaração, não um executor. Cada WP precisa
declarar, no mínimo:

Os dois artefatos v2 devem declarar `contract: "v2"` e
`contract_version: "v2"`; ausência ou divergência invalida o artefato.

- `id` único;
- `owner` não vazio;
- `role` canônica, declarada explicitamente na chave do WP;
- `depends_on` (lista, que pode ser vazia);
- `capabilities` requeridas;
- `scope` explícito como objeto de caminhos relativos que pode declarar as
  listas `write`, `read`, `execute` e `forbidden`. `scope.write` e
  `scope.forbidden` devem ser declarados mesmo quando vazios; `read` e
  `execute` são opcionais e, quando presentes, também são listas de caminhos;
  roles read-only devem usar `scope.write: []`, enquanto `implementer` e
  `test-engineer` devem declarar uma lista `scope.write` não vazia;
- `acceptance_criteria`;
- `state`.

No v2, as roles read-only são `orchestrator`, `planner`, `architect`,
`verifier`, `reviewer` e `documentation-reviewer`: elas não escrevem e mantêm
`scope.write` vazio. `implementer` e `test-engineer` são as roles que podem
declarar escrita no escopo autorizado do WP.

`owner.role`, quando fornecido, é apenas informação auxiliar validável; nunca
substitui a chave `role` explícita do WP, que deve existir e ser conhecida.

O validador aceita `dependencies` como alias de `depends_on`, mas exige o
schema canônico de `scope` para v2 e normaliza o grafo para uma representação
única. IDs duplicados, dependências ausentes, auto-dependência e ciclos são
rejeitados antes de qualquer execução. Escopos de escrita sobrepostos também
são rejeitados, exceto quando um WP depende explicitamente do outro (direta ou
transitivamente), como em um WP corretivo serial. A ordem topológica é
determinística: entre WPs disponíveis, o menor ID lexical é escolhido.

Depois da normalização, a execução mínima exige que cada `test-engineer` dependa
transitivamente de algum `implementer` quando houver implementer, que cada
`verifier` dependa de algum `test-engineer` quando houver test-engineer e que
cada `reviewer` e `documentation-reviewer` dependa de algum `verifier` quando
houver verifier. Planner e Architect podem permanecer em paralelo; WPs
corretivos de Implementer continuam permitidos quando sua dependência serial
estiver declarada. Em escopos com glob, prefixos potencialmente sobrepostos são
tratados como conflito de forma conservadora (inclusive classes como
`src/[ab].py` e `src/[bc].py`); padrões ambíguos podem ser rejeitados fail-closed
para evitar falso negativo.

Estados canônicos permitidos são somente `pending`, `ready`, `in_progress`,
`blocked`, `completed`, `failed` e `cancelled`; aliases como `done` e
`in-progress` são inválidos. Um WP `blocked` ou `failed` aberto impede
conclusão; o replanejamento deve criar um WP de correção auditável.

## Evidência v2

`delegation-evidence.json` registra a execução observada. O formato recomendado
é:

```json
{
  "contract": "v2",
  "contract_version": "v2",
  "work_packages_sha256": "...",
  "required_roles": ["planner", "implementer", "test-engineer", "verifier", "reviewer"],
  "delegations": [
    {
      "work_package": "WP-1",
      "role": "implementer",
      "agent_id": "...",
      "state": "completed",
      "fallback": {"used": false}
    }
  ]
}
```

O validador compara o digest dos WPs, confirma que os WPs possuem evidência e
que as roles obrigatórias foram observadas. `tester` é alias v1 de
`test-engineer`; no v2 ele não cobre `verifier` e não pode satisfazer as duas
roles ao mesmo tempo. A ausência de uma role não vira capability disponível por
inferência de nickname, modelo ou texto da resposta do agente.

Cada entrada de `delegations` deve declarar explicitamente `fallback` como um
objeto com `used` booleano. A ausência do objeto invalida a evidência. Quando
`used` é falso, a declaração deve permanecer limpa (`{"used": false}`), e
campos incompatíveis com a ausência de trabalho direto continuam sendo
rejeitados.

Quando `fallback.used` é verdadeiro, a entrada deve registrar todos os campos
auditáveis: `approved: true`, `reason`, `agent_unavailable`, `attempts` e `direct_work`. Os
`attempts` devem ser uma lista não vazia; `direct_work` deve descrever o
trabalho direto, seu escopo relativo e permitido pelo WP, e o resultado.
Quando `fallback.used` é falso, a declaração deve ser limpa (`{"used": false}`);
qualquer campo adicional com conteúdo incompatível com ausência de trabalho
direto invalida a evidência.

O fallback de uma role read-only não pode escrever. Em especial, para WPs de
`verifier`, `reviewer` ou `documentation-reviewer`, `fallback.used: true` exige
`direct_work.operation` explícita com valor `read` ou `execute`. O caminho de
cada item de `direct_work.scope` deve estar contido, respectivamente, em
`scope.read` ou `scope.execute` do WP e não pode atingir `scope.forbidden`;
`direct_work.write`/`writes` não são permitidos. No fallback canônico de
`implementer`, use `direct_work.operation: "write"` e valide
`direct_work.scope` contra `scope.write`. A mesma regra de operação e escopo
aplica-se a qualquer trabalho direto registrado: o fallback não amplia o
escopo do WP.

O fallback local canônico é uma execução direta, restrita e auditada do WP
quando a role canônica não está disponível; ele não cria uma capability nem
troca a identidade da role. Registre a tentativa de delegação, a
indisponibilidade observada, a aprovação explícita, as tentativas, a operação,
o escopo permitido e o resultado. Se o WP for de `verifier`, um fallback local
read/execute continua sendo evidência de fallback desse WP, não uma execução
delegada do runtime. `tester` permanece apenas o alias v1 de `test-engineer`:
seus testes e resultados nunca satisfazem `verifier`, não importando nickname,
modelo ou resultado; o trabalho do Test Engineer e o fallback local do
Verifier devem permanecer registros distintos.

Fallback sem aprovação, indisponibilidade observada, motivo, tentativas, escopo
seguro ou resultado é inválido; motivos que só alegam trivialidade ou silêncio
também são inválidos. `blockers` deve estar ausente ou ser uma lista vazia para
concluir. Em T4, a evidência deve conter `human_approval` com `approved: true`,
`approver`, `timestamp` e `reference` auditável.

Em uma feature T2 v2, o Planner/Orchestrator declara o impacto documental no
`plan.md` e requer manualmente `documentation-reviewer` quando aplicável;
`required_roles` deve refletir essa decisão. O validador v2 não infere a role
condicional. Sem impacto documental declarado, essa role não é parte do mínimo
adicional de T2. Em T3/T4, `documentation-reviewer` é obrigatório por classe.
Em uma feature T0 v2, a evidência só pode concluir com uma declaração
`mechanical_non_delegable` contendo `approved: true` e justificativa auditável,
ou com uma role especializada observada. `orchestrator` com capability
`coordinate` não satisfaz essa cobertura e não pode ser owner de trabalho
delegável.

## Loop de execução

```text
Planner -> Implementer -> Test Engineer -> Verifier -> Reviewer
                                             \-> Documentation Reviewer
                ^             |              |            |
                |             +--------------+------------+
                |                    achado / blocker
                +--------- novo WP de correção para a role adequada
```

Test Engineer cria ou altera testes. Um blocker ou critério falho do Test
Engineer também abre novo WP de correção; após o Implementer, o fluxo repete
Test Engineer, Verifier e os revisores aplicáveis. Verifier executa a validação
final e não altera código nem testes. Reviewer e Documentation Reviewer inspecionam o
resultado de forma independente e podem rodar em paralelo somente depois do
Verifier, quando seus escopos não conflitarem. O ciclo termina somente com evidência atual, cobertura de roles,
nenhum blocker aberto e o gate de conclusão satisfeito. Repetição sem progresso
deve terminar em `BLOCKED` ou pedir decisão humana; nunca em loop infinito.

## Compatibilidade e limites

O alias `tester` permanece disponível para CLIs e specs v1. Roles canônicas
novas são `test-engineer` e `verifier`. O repositório valida declarações e
evidências, mas não inventa uma API de spawn nem executa o grafo. Consultas de
roteamento e fallbacks são somente leitura e não alteram configuração global,
sessões do runtime ou projetos consumidores.
