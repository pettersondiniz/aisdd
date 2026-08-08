# Completion e Evidence

Só conclua quando:

- todos os critérios de aceitação têm implementação, teste anotado e prova atual em `verification.json`;
- testes, lint, tipos, build e migrações aplicáveis foram executados;
- revisão independente não deixou bloqueadores;
- em T2 com impacto documental, o Documentation Reviewer concluiu a revisão
  independente após o Verifier, em paralelo com o Reviewer quando aplicável;
- em T3/T4, o Documentation Reviewer concluiu essa revisão por exigência da
  classe, mesmo que o impacto documental específico seja pequeno;
- `status.md` e `plan.md` refletem a realidade;
- docs e ADRs afetados estão atualizados;
- riscos e checks não executados estão explicitados;
- não há suposições ou perguntas abertas que dependam de decisão do produto.

Quando `plan.md` contiver a declaração exata `Main-chat attribution: required`,
os artefatos `task-window.json` e `task-window-report.json` devem representar o
lifecycle `start` → `close` → `report --final --output task-window-report.json`.
O relatório final deve estar fechado, não provisório, usar
`scope: main-chat-orchestrator` e declarar as exclusões explícitas de rollouts
delegados, ferramentas, modalidades e cobrança da assinatura. Uma janela
aberta ou provisória nunca é evidência final. Custo `not-available` deve ser
preservado com sua razão e nunca convertido em zero; se uma parcela necessária
estiver indisponível, o total combinado também permanece `not-available`.

`evidence.md` deve registrar comando, resultado, data/contexto, critério coberto e limitações. Não invente resultados.

Um blocker, critério falho ou correção exigida pelo Test Engineer também impede
Completion e abre um novo WP para o Implementer. Depois da correção, repita
Test Engineer, Verifier e os revisores aplicáveis antes de reavaliar o gate.

Rode `verify_feature.py` com o comando de teste real antes de `validate_feature.py`; ambos devem
terminar com código 0. Para mudanças de interface, inclua a validação visual, responsiva e de
acessibilidade aplicável.

Para uma feature v2, `validate_feature.py` também deve confirmar a integridade
de `work-packages.json` e `delegation-evidence.json`: grafo determinístico,
digest atual, cobertura de roles, independência entre os papéis canônicos que
exigem separação, fallback explicitamente aprovado e auditado, ausência de
blocker e aprovação humana auditável em T4. Um fallback ou role ausente não
pode ser compensado por inferência do Orchestrator.
Quando houver delegações, a conclusão também exige uma entrada machine-readable
por Work Package e uma coleta posterior com
`python scripts/delegation_telemetry.py collect`. O resultado deve manter
`delegated_subtotal` separado de `unavailable`; uma parcela sem correlação,
tokens ou preço permanece `not-available`. A coleta não substitui o lifecycle
do chat principal: quando `Main-chat attribution: required` estiver declarado,
o orquestrador ainda precisa executar `task_window.py start`, `close` e
`report --final` sobre a sessão real.
`verification.json` é um artefato gerado por `verify_feature.py`. Se o projeto
consumidor aplicar Prettier ou outro formatter a esse arquivo, trate a
diferença como particularidade do projeto consumidor: ajuste a configuração do
formatter nesse projeto ou regenere o artefato pelo verificador. O fluxo AISDD
não deve editar o JSON gerado manualmente nem assumir que whitespace é prova de
validade; a validação é semântica e baseada no mapa/digest atuais.
