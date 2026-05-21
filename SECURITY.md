# Security

## Do not commit

- **Credentials** — API keys, OAuth tokens, `.env` files, `*_tokens.json`
- **Customer data** — support tickets, call transcripts, CRM exports, survey PII
- **Internal strategy** — unreleased roadmap, financials, or confidential competitive intelligence

## If you fork this repo

1. Populate [`01-context/`](01-context/) with your own company context — run **`/start`** (public web research only) or copy from [`02-templates/context/`](02-templates/context/) manually. Review generated files before sharing externally; do not publish internal docs verbatim.
2. Keep real feature work in `projects/PROJECT-*` folders locally, or adjust [`.gitignore`](.gitignore) to match your team's policy.
3. Copy [`.cursor/mcp.json.example`](.cursor/mcp.json.example) to `.cursor/mcp.json` locally only — never commit live MCP credentials.

## Reporting issues

If you discover a security issue in this public template, open a GitHub issue or contact the repository maintainer privately.
