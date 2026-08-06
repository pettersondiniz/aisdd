# Roteamento de agentes

| Classe | Agentes recomendados |
|---|---|
| T0 | nenhum, salvo revisão solicitada |
| T1 | planner ou tester |
| T2 | planner → implementer; tester e reviewer em paralelo após implementação; documentation-reviewer se docs mudarem |
| T3 | planner + architect em paralelo; implementer; tester + reviewer + documentation-reviewer em paralelo |
| T4 | planner + architect; aprovação humana; implementer em etapas; tester/reviewer/documentation-reviewer antes de cada rollout |

Agentes read-only podem trabalhar em paralelo. Apenas um agente deve editar o mesmo conjunto de arquivos por vez. O agente principal consolida resultados e resolve conflitos.

## Correções após validação ou revisão

- Um blocker, critério falho ou correção exigida pelo `tester` ou `reviewer` impede a conclusão e devolve o fluxo ao `implementer`.
- `tester` e `reviewer` permanecem read-only e não corrigem os próprios achados. Reutilize um `implementer` disponível para a correção focada; se não houver um disponível, crie outro com escopo explícito de escrita.
- O agente principal coordena e integra a correção, editando diretamente somente como fallback documentado quando não houver subagente disponível ou quando a mudança for genuinamente trivial.
- Após cada correção, execute novamente `tester` e `reviewer` de forma independente. Se o achado mudar a spec, a arquitetura ou o plano, retorne primeiro ao agente/fase correspondente.

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
| tester | `audit` para acessibilidade, desempenho e responsividade; valida estados de erro, vazios e `prefers-reduced-motion`. |
| reviewer | `critique` para revisão de UX/hierarquia e `polish` para a passada final; compara o resultado com a spec e não apenas com estética. |
| documentation-reviewer | `document` para registrar o sistema visual existente e `extract` quando houver tokens/componentes reutilizáveis a documentar. |
