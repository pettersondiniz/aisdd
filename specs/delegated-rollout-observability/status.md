# Status: Delegated rollout observability

- Classe: T3
- Contrato AISDD da feature: v2
- Fase atual: Concluída
- Última atualização: 2026-08-08
- Próxima ação: sincronizar e conferir a instalação global
- Bloqueios: nenhum

## Histórico

- Discovery: identificado que o orquestrador precisa chamar o collector e a
  guarda de roteamento, sem alterar a UI/API do Agent Bridge.
- Implementação: adicionados collector de evidência v2 e validação explícita
  de pedido de modelo/effort.
- Verificação: testes focados, suíte completa, contrato v2 e drift executados.

## Decisões recentes

- `delegated_subtotal` e `unavailable` permanecem parcelas distintas.
- `task_window.py` não cria markers; o orquestrador deve executar o lifecycle
  start → close → report --final sobre a sessão real.
- O formatter/prettier do projeto consumidor fica fora do escopo AISDD.

## Deleção v2

O WP atual, owner, role, fallback auditado e próxima transição estão registrados
no `plan.md` e em `delegation-evidence.json`. O fallback direto foi usado apenas
após tentativas de delegação sem aplicação das mudanças e está delimitado pelos
escopos dos WPs.
