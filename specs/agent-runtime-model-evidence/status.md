# Status: Agent runtime model evidence

- Classe: T2
- Fase atual: Complete
- Última atualização: 2026-08-02
- Próxima ação: nenhuma.
- Bloqueios: nenhum.

## Histórico

- 2026-08-02: implementada consulta local de evidência efetiva e atualizadas instruções/template.
- 2026-08-02: revisão independente corrigiu a semântica do último contexto, o seletor legado e formatos JSONL inesperados.
- 2026-08-02: validação mecânica e checagem de drift concluídas.
- 2026-08-02: adicionado seletor direto de ID de rollout para sessões legadas.

## Decisões recentes

- `turn_context` é melhor evidência local, não garantia do backend; resultados não recuperáveis continuam `unknown`.

