# Completion e Evidence

Só conclua quando:

- todos os critérios de aceitação têm implementação, teste anotado e prova atual em `verification.json`;
- testes, lint, tipos, build e migrações aplicáveis foram executados;
- revisão independente não deixou bloqueadores;
- `status.md` e `plan.md` refletem a realidade;
- docs e ADRs afetados estão atualizados;
- riscos e checks não executados estão explicitados;
- não há suposições ou perguntas abertas que dependam de decisão do produto.

`evidence.md` deve registrar comando, resultado, data/contexto, critério coberto e limitações. Não invente resultados.

Rode `verify_feature.py` com o comando de teste real antes de `validate_feature.py`; ambos devem
terminar com código 0. Para mudanças de interface, inclua a validação visual, responsiva e de
acessibilidade aplicável.
