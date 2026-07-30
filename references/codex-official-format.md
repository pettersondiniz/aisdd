# Formato oficial consultado

Baseado no manual atual do Codex/OpenAI consultado em 2026-07-20:

- skills são pastas com `SKILL.md`; o frontmatter requer `name` e `description`;
- agentes personalizados são arquivos TOML em `~/.codex/agents/` ou `.codex/agents/`;
- cada agente requer `name`, `description` e `developer_instructions`;
- `agents.max_threads` limita concorrência e `agents.max_depth` limita profundidade; mantenha a profundidade padrão salvo necessidade clara;
- a documentação recomenda agentes estreitos, resultados resumidos e paralelismo principalmente para tarefas read-heavy.

Fonte local: manual oficial baixado pelo helper `fetch-codex-manual.mjs`, seção “Multi-agent operations” e “Customization, Skills, Rules, MCP, and Integrations”.

