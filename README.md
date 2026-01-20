# LogTech Analysis Tool 

This folder contains a small RCA assistant that uses a local Ollama-compatible LLM and Jira MCP server

Required environment variables
- `OLLAMA_API_BASE` — base URL for Ollama API (default: `http://localhost:11434`).
- `OLLAMA_MODEL` — model name to request (default: `llama3`).
- `JIRA_USER` — Jira username or email for Basic auth.
- `JIRA_TOKEN` — Jira API token for Basic auth.
- `JIRA_BASE` — (optional) custom Jira base URL (default: `https://mitel.atlassian.net`).

Quick tests
- Run RCA from CLI: `python run_query.py -d "short description"`.
