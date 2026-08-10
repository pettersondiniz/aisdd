# Ideias

## Estrutura

- `active/`: ideias em descoberta; somente estas entram na entrevista e podem ser promovidas.
- `promoted/`: ideias que viraram uma spec AISDD; não significa que a implementação terminou.
- `discarded/`: ideias abandonadas, preservadas para evitar rediscussão acidental.

## Transições

- Use `$shape-idea` para criar, extrair ou refinar arquivos em `active/`.
- Quando uma implementação criar `specs/<slug>/`, mova a ideia correspondente para `promoted/` e mantenha links entre a ideia e a spec.
- Mova uma ideia descartada para `discarded/`; não apague sem pedido explícito.

## Formato

Cada ideia usa o template da skill e distingue fatos confirmados de inferências. Ideias ativas podem estar em `draft` ou `ready`.
