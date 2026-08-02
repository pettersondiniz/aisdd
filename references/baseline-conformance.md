# Baseline de conformidade

Use somente quando o usuario solicitar explicitamente `baseline-conformance`. Sugira a operacao quando um projeto em andamento nao tiver marcadores AISDD, mas nunca a execute automaticamente.

A operacao e documental: faca inventario, backup versionado e documentacao `as-built`; nunca altere codigo, testes, dependencias, infraestrutura, banco ou CI. Execute primeiro em `--dry-run`; antes de `--apply`, mostre os arquivos que serao criados e obtenha confirmacao explicita. O script exige `--confirm-documentation-only`.

Crie manifesto com hashes, copia da documentacao preexistente, estado observado, relatorio e `AGENTS.md` se ausente. Valide tambem o conteudo de `AGENTS.md`: a versao atual deve conter `Mandatory AISDD triage` e marcadores de classificacao T0, T1+, T2+ e `AISDD: not applicable`. Um arquivo legado que apenas diz "for non-trivial" e uma lacuna `agents-guidance`, nao conformidade.

Documente ADRs retroativos como reconstruidos/inferidos, com evidencias e confianca; nao invente intencao historica. Toda lacuna entre comportamento, docs e testes vira uma spec de follow-up, nunca alteracao de codigo. Essas specs ficam pendentes e nao recebem `verification.json` ate que o usuario solicite o trabalho corretivo.
