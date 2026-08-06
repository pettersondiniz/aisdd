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

## Retorno após falha

- Um blocker, critério falho ou correção exigida pelo `tester` ou `reviewer` impede a conclusão e devolve o fluxo à fase de Implementation.
- Mantenha `tester` e `reviewer` read-only. Reutilize um `implementer` disponível para a correção focada; se não houver um disponível, crie outro com escopo explícito de escrita.
- O agente principal coordena e integra a correção. Só edite diretamente como fallback documentado quando não houver subagente disponível ou quando a mudança for genuinamente trivial.
- Depois de cada correção, execute novamente `tester` e `reviewer` de forma independente antes de retomar Completion.
- Se o achado mudar a spec, a arquitetura ou o plano, retorne primeiro à fase correspondente e atualize os artefatos antes de implementar.
