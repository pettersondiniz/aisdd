# Roteamento de agentes

| Classe | Agentes recomendados |
|---|---|
| T0 | declaração v2 aprovada de `mechanical_non_delegable` ou role especializada; `orchestrator/coordinate` não cobre trabalho delegável |
| T1 | planner → implementer → test-engineer (`tester` como alias v1) → verifier |
| T2 | planner → implementer → test-engineer → verifier → reviewer; o Planner/Orchestrator declara impacto documental no plano e requer manualmente Documentation Reviewer em paralelo quando aplicável |
| T3 | planner + architect em paralelo → implementer → test-engineer → verifier → (reviewer || documentation-reviewer) |
| T4 | planner + architect → aprovação humana → implementer em etapas → test-engineer → verifier → (reviewer || documentation-reviewer) antes de cada rollout |

Agentes read-only podem trabalhar em paralelo somente depois de suas
dependências estarem satisfeitas. Reviewer e Documentation Reviewer começam
após o Verifier e podem executar em paralelo entre si; uma dependência serial
ou escopo sobreposto mantém o WP serializado. Apenas um agente deve editar o
mesmo conjunto de arquivos por vez. O agente principal consolida resultados e
resolve conflitos.

## Correções após validação ou revisão

- Um blocker, critério falho ou correção exigida pelo `test-engineer`, `verifier`, `reviewer` ou `documentation-reviewer` impede a conclusão, abre um novo WP de correção e devolve o fluxo ao `implementer`.
- `test-engineer`, `verifier`, `reviewer` e `documentation-reviewer` têm ownerships distintos: Test Engineer cria/altera testes; Verifier valida independentemente; Reviewer e Documentation Reviewer inspecionam. Nenhum corrige o próprio achado.
- Reutilize um `implementer` disponível para a correção focada; se nenhuma role/agente estiver disponível, marque `BLOCKED` e peça decisão humana. Não substitua a role ausente silenciosamente.
- O agente principal coordena e integra a correção. Edição direta só ocorre após fallback explicitamente aprovado e auditado com motivo, agente indisponível, tentativas, escopo e resultado; nunca por trivialidade ou silêncio.
- Após cada correção, execute novamente Test Engineer quando testes ou o
  critério afetado exigirem nova cobertura, depois Verifier e, após ele, Reviewer
  e Documentation Reviewer em paralelo quando aplicáveis. Isso também vale para
  um achado do próprio Test Engineer. Se o achado mudar a spec, a arquitetura
  ou o plano, retorne primeiro ao agente/fase correspondente.

## Roles canônicas e contrato v2

As roles canônicas de execução e revisão são `implementer`, `test-engineer`,
`verifier`, `reviewer` e `documentation-reviewer`. `planner` continua sendo a role que produz o plano técnico e o
plano de execução; `architect` apoia design e ADR. `tester` é alias de
compatibilidade v1 para `test-engineer` e não cobre `verifier` no v2.

Em features marcadas `Contrato AISDD da feature: v2`, cada Work Package deve
ter owner, role, dependências, capabilities, escopo permitido/proibido,
critérios e estado. O Orchestrator coordena e delega; não implementa, escreve
testes, executa build, corrige código ou faz validação final. Achados do Test
Engineer, Verifier, Reviewer ou Documentation Reviewer retornam como novo WP de
correção. Em T2, o Planner/Orchestrator declara impacto documental no plano e
requer manualmente Documentation Reviewer quando aplicável; o validador v2 não
infere a role condicional. Em T3/T4, é obrigatório por classe.

O fallback só é aceito com aprovação explícita, motivo, indisponibilidade
observada, tentativas e trabalho direto registrados com escopo e resultado. A
ausência de subagente deve resultar em `BLOCKED`/decisão humana até essa
aprovação; nunca se presume capability pela resposta, nickname ou modelo.

## Interface e Impeccable

Durante Discovery, identifique se a alteração cria ou modifica uma interface visível (página,
componente, formulário, estado vazio, fluxo de onboarding, estilos, design system ou comportamento
responsivo). Se sim, verifique se a skill `impeccable` está disponível. Se não estiver, proponha sua
instalação ao usuário; não a instale sem pedido explícito. Se estiver disponível, aplique os comandos
abaixo conforme o papel, sem transformar uma mudança backend em trabalho de design.

| Agente | Uso de Impeccable |
|---|---|
| planner | `shape` para planejar UX/UI e `clarify` para critérios de texto e estados; registra o comando recomendado no plano. |
| architect | `extract` quando a mudança afeta tokens/componentes compartilhados; avalia impacto de design system, responsividade e acessibilidade. |
| implementer | `craft` para uma interface nova; `layout`, `typeset`, `colorize`, `adapt`, `clarify`, `animate`, `onboard` ou `harden` conforme a necessidade concreta. |
| test-engineer (`tester` como alias v1) | `audit` para acessibilidade, desempenho e responsividade; valida estados de erro, vazios e `prefers-reduced-motion`. |
| reviewer | `critique` para revisão de UX/hierarquia e `polish` para a passada final; compara o resultado com a spec e não apenas com estética. |
| documentation-reviewer | `document` para registrar o sistema visual existente e `extract` quando houver tokens/componentes reutilizáveis a documentar. |
