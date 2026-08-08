# Lifecycle AISDD

## Fases

1. **Discovery** — entender pedido, repositório, riscos, comandos e perguntas abertas.
2. **Specification** — registrar comportamento observável e critérios testáveis.
3. **Design** — definir interfaces, dados, invariantes, compatibilidade e ADRs.
4. **Planning** — dividir em milestones ordenados, pequenos e executáveis.
5. **Implementation** — alterar código e testes somente contra a spec aprovada.
6. **Validation** — executar testes, lint, tipos, build e checks operacionais aplicáveis.
7. **Review** — revisar independentemente diff, segurança, regressões e lacunas.
8. **Documentation** — atualizar docs, status, ADRs e comandos reais.
9. **Completion** — preencher evidências e declarar limitações.

## Regras

- Retome da primeira fase incompleta encontrada nos artefatos.
- Uma descoberta que muda comportamento exige atualizar spec e plano antes de continuar.
- Um plano é vivo: registre decisões e replaneje milestones obsoletos.
- Não marque concluído apenas porque o código compila.
- A delegação é obrigatória para trabalho delegável a partir de T1 e também para
  trabalho delegável identificado em T0. T0 só fica fora do contrato quando for
  comprovadamente mecânico e não delegável; sem role/agente disponível, marque
  o trabalho como `BLOCKED` e peça decisão humana.

## Retorno após falha

- Um blocker, critério falho ou correção exigida pelo `test-engineer`, `verifier`, `reviewer` ou `documentation-reviewer` impede a conclusão, abre um novo WP de correção e devolve o fluxo à fase de Implementation.
- Test Engineer é owner de criação/alteração de testes; Verifier é owner da
  validação final; Reviewer e Documentation Reviewer são independentes e
  read-only. O alias `tester` cobre apenas o Test Engineer em features v1.
- Reutilize um `implementer` disponível para a correção focada; se nenhuma
  role/agente estiver disponível, marque `BLOCKED` e peça decisão humana.
- O agente principal coordena e integra a correção. Edição direta só é permitida
  após fallback explicitamente aprovado e auditado com motivo, agente
  indisponível, tentativas, escopo permitido e resultado. Trivialidade ou
  silêncio nunca autorizam bypass.
- Depois de cada correção, execute novamente Test Engineer quando testes ou o
  critério afetado exigirem nova cobertura, depois Verifier e, após ele, Reviewer
  e Documentation Reviewer de forma independente antes de retomar Completion.
  Isso inclui a correção de um achado do Test Engineer. A ordem é Implementer →
  Test Engineer (quando aplicável) → Verifier → (Reviewer || Documentation
  Reviewer), e os dois revisores só começam depois do Verifier.
  Reviewer e Documentation Reviewer podem rodar em paralelo entre si quando
  seus escopos forem independentes; uma dependência serial explícita prevalece.
- Se o achado mudar a spec, a arquitetura ou o plano, retorne primeiro à fase correspondente e atualize os artefatos antes de implementar. Achados do Test Engineer, Verifier, Reviewer e Documentation Reviewer geram novo WP de correção para a role adequada.
