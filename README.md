# AISDD

AISDD (*AI Software Delivery & Design*) é uma skill reutilizável do Codex para desenvolvimento orientado por especificações, planos executáveis, evidências, revisão independente e documentação viva.

## Instalação global

No Windows, copie a pasta `aisdd` para:

```text
C:\Users\<seu-usuário>\.agents\skills\aisdd
```

No macOS/Linux:

```text
~/.agents/skills/aisdd
```

Para disponibilizar os agentes especializados globalmente, copie também `agents/*.toml` para `~/.codex/agents/`. Para um projeto específico, use `.codex/agents/` dentro do repositório.

## Uso

```text
$aisdd Inicialize este repositório para o fluxo AISDD.
$aisdd Crie a especificação da autenticação com Entra ID.
$aisdd Implemente specs/autenticacao-entra-id.
$aisdd Audite o repositório e verifique drift.
```

O inicializador cria `AGENTS.md`, `docs/` e `specs/` sem sobrescrever arquivos existentes. O criador de features cria uma pasta com spec, plano, status e evidências.

## Fluxo recomendado

1. Classifique a mudança em T0–T4.
2. Especifique comportamento e critérios de aceitação.
3. Faça design/ADR quando houver impacto arquitetural.
4. Planeje milestones pequenos e retomáveis.
5. Delegue exploração e revisão a agentes independentes.
6. Implemente em etapas, adicionando testes.
7. Execute os testes pelo verificador de feature, revise, cheque drift e registre evidências.

## Rastreabilidade mecânica

Para features T2+, cada critério de aceitação usa um ID global (`AC-001`), aparece em uma
tarefa (`T-001`) e é coberto por pelo menos um teste anotado com `@spec:AC-001`. A evidência
de execução não é preenchida manualmente: execute o comando de teste real pelo verificador,
que gera `verification.json` e rejeita testes ausentes, pulados ou prova obsoleta.

```text
python scripts/verify_feature.py . specs/exemplo -- <comando-de-teste-real>
python scripts/validate_feature.py . specs/exemplo
python scripts/check_drift.py .
```

## Mudanças de interface

Na descoberta, AISDD identifica páginas, componentes, formulários, estilos, design system e
comportamento responsivo. Quando houver interface e a skill `impeccable` não estiver instalada,
AISDD propõe sua instalação — nunca instala sem autorização. Quando ela estiver disponível, os
agentes usam comandos adequados ao papel: planejamento (`shape`), implementação (`craft` e
comandos especializados), teste (`audit`), revisão (`critique`/`polish`) e documentação (`document`/`extract`).

## Compatibilidade Codex

O pacote segue o formato documentado atualmente: skill com `SKILL.md` e frontmatter `name`/`description`; agentes personalizados como TOML independentes com `name`, `description` e `developer_instructions`. Consulte `references/codex-official-format.md` para a base oficial usada na montagem.

## Validação local

```text
python scripts/validate_feature.py . specs/exemplo
python scripts/check_drift.py .
```

O pacote não inclui dependências externas.
