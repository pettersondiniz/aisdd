# Otimização do fluxo de validação AISDD

## Objetivo

Reduzir o custo de execução da validação de features sem alterar as regras de validação nem a interface de linha de comando.

## Contexto

`check_drift.py` executava `validate_feature.py` em um subprocesso para cada feature e cada validação podia recalcular o mapa de testes do repositório. Isso repetia inicialização do Python, imports, parsing de argumentos e a varredura dos arquivos.

## Comportamento esperado

- `validate_feature.py` deve expor uma função reutilizável `validate_feature(repo, feature, full_map=None)` que execute a lógica atual e retorne `list[str]` com os erros encontrados.
- A função deve usar o `full_map` fornecido, inclusive quando ele for um dicionário vazio, e só chamar `test_map(repo)` quando o mapa não for fornecido.
- `main()` deve permanecer como wrapper da CLI: interpretar argumentos, chamar a função, imprimir o resultado e retornar o exit code existente.
- `check_drift.py` deve importar e chamar `validate_feature` diretamente, sem criar um subprocesso para cada feature.
- Em cada execução com `specs/`, `check_drift.py` deve calcular `test_map(repo)` uma única vez e passar o mesmo mapa para todas as validações aplicáveis.
- O tratamento das features `baseline-*` com origem `baseline-conformance` deve permanecer inalterado.

## Fluxos principais

1. A CLI chama `validate_feature` sem `full_map`; a função preserva o comportamento autônomo anterior.
2. `check_drift.py` calcula o mapa uma vez, percorre as features e chama a função diretamente com o mapa compartilhado.
3. Erros retornados pela função são agregados por `check_drift.py` e apresentados no mesmo formato geral de falha.

## Regras e invariantes

- As regras existentes de artefatos obrigatórios, critérios, tarefas, evidências e `verification.json` não mudam.
- A ordem de validação e o conteúdo dos erros permanecem compatíveis.
- `full_map=None` significa que a função deve calcular o mapa internamente.
- Um `full_map` fornecido é tratado como cache explícito e não pode ser substituído por uma nova varredura.
- Uma execução de `check_drift.py` não pode recalcular o mapa por feature.

## Casos de borda e falhas

- Feature inexistente continua retornando erro pela função e falha pela CLI.
- `verification.json` inválido continua sendo reportado como erro.
- Mapa pré-calculado vazio deve ser respeitado, sem fallback silencioso para uma nova varredura.
- Repositório sem `specs/` continua encerrando com sucesso sem realizar trabalho adicional.

## Interfaces e persistência afetadas

- Interface interna: nova função reutilizável em `scripts/validate_feature.py`.
- Interface CLI preservada: `python scripts/validate_feature.py <repo> <feature>`.
- Não há alteração de banco, arquivos persistentes de produto ou formato de artefatos AISDD.

## Requisitos não funcionais

- Remover o overhead de subprocesso por feature.
- Reutilizar o resultado da varredura do repositório durante toda a execução de `check_drift.py`.
- Manter o código importável pelos scripts executados diretamente.

## Fora de escopo

- Alterar as regras de validação de features.
- Alterar a saída pública ou os argumentos da CLI.
- Corrigir o drift preexistente em `specs/agent-runtime-model-evidence/verification.json`.
- Alterar a cópia instalada/global da skill.

## Critérios de aceitação

- [x] AC-601: `validate_feature` executa a validação atual, retorna erros como lista e usa um `full_map` fornecido sem recalcular `test_map`.
- [x] AC-602: A invocação CLI existente continua válida e preserva sucesso/falha e saída compatíveis.
- [x] AC-603: `check_drift.py` calcula `test_map(repo)` uma vez, chama `validate_feature` diretamente uma vez por feature não ignorada e reutiliza o mesmo mapa.
- [x] AC-604: O teste de regressão confirma o fluxo otimizado sem subprocesso por feature e mantém o tratamento das features baseline ignoradas.

## Suposições

| ID | Suposição | Status | Dono/validação |
|---|---|---|---|
| ASM-601 | Os scripts continuam sendo executados a partir do diretório `scripts/`, permitindo os imports diretos já usados pelo pacote. | Resolvida | Verificada na implementação e nos testes |

## Perguntas abertas

| ID | Pergunta | Status | Decisão/resposta |
|---|---|---|---|
| Q-601 | É necessário manter a CLI existente? | Resolvida | Sim; a compatibilidade da CLI é critério de aceitação. |

## Decisões resolvidas

- O mapa compartilhado será injetado como argumento opcional, preservando o uso direto da função sem cache.
- O caminho real deste repositório é `scripts/` e `tests/`; os caminhos `skills/aisdd/...` das imagens foram interpretados como a instalação empacotada da mesma skill.
