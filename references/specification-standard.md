# Padrão de Specification

Uma spec descreve o que deve ser verdade, não uma solução presumida. Inclua apenas seções aplicáveis.

- objetivo e contexto;
- comportamento esperado e fluxos;
- regras de negócio e invariantes;
- casos de borda e falhas;
- interfaces, contratos e persistência afetados;
- requisitos não funcionais;
- fora de escopo e compatibilidade;
- critérios de aceitação numerados (`AC-001`, `AC-002`...);
- suposições identificadas (`ASM-001`...) e perguntas abertas identificadas (`Q-001`...);
- perguntas abertas e decisões resolvidas.

Cada critério deve ser observável, ligado a uma tarefa (`T-001`...) no plano e a um teste
anotado com `@spec:AC-xxx`. A validação mecânica gera `verification.json`; menção textual
em `evidence.md` não é prova suficiente.
