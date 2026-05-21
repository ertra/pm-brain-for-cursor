# PM Brain

A **product management knowledge system** you can fork and adapt. It bundles opinionated document templates, a sample feature hub, and Cursor skills that drive the doc workflow end to end — from product brief through PRD, internal announcement, and customer support article.

The goal: sit down in Cursor, pitch an idea, and come out with a buy-in brief, a PRD pack, an IFA, and a support article draft, grounded in **your** context once you run `/start` to bootstrap `01-context/`.

**License:** [MIT](LICENSE)

---

## What this repo can do

- **Draft the full product doc pack** — brief → PRD + success metrics → IFA → support article, via Cursor skills that enforce template structure and feature-hub layout.
- **Run a competitive landscape analysis** — profiles, positioning map, whitespace, strategic recommendations (the skill creates `docs/competitive-analyses/` on demand; that folder is gitignored by default).
- **User interview guidance** — scripts, recruitment, and analysis patterns via the `interview-frameworks` skill.
- **PRD critique** — rubric-scored review and cross-doc red-team passes before you share with stakeholders.

### How the agent thinks

Before filling templates, the coach runs a short **braindump** pass — product-sense questions and a sufficiency checklist so briefs and PRDs are grounded in real thinking, not checkbox docs. Spec: [`PRODUCT-RULES.md`](PRODUCT-RULES.md). Enforced in Cursor via [`.cursor/rules/product-sense.mdc`](.cursor/rules/product-sense.mdc).

---

## Repository layout

```
pm-brain/
├── 01-context/                 # Your company context (empty until you run /start)
├── 02-templates/               # Templates (context/ + product/) + workflow rules
├── projects/                   # Feature hubs: projects/PROJECT-{id}-{slug}/
│   └── EXAMPLE-0001-sample-feature/   # Compact fictional sample hub (01–05 pack)
├── docs/                       # Created on demand by competitive-landscape (gitignored)
├── scripts/
│   └── check_doc_skills.sh     # Skill structure check
├── .cursor/
│   ├── skills/                 # Agent skills (create-product-brief, create-prd, ...)
│   ├── agents/                 # Subagent definitions (e.g. prd-critic)
│   ├── commands/               # Slash commands (/start, /setup, /critique-prd, /critique-agent)
│   └── rules/                  # Always-on rules (pm-brain-doc-workflow, product-sense)
├── .vscode/
│   └── settings.json           # Auto-activates .venv in new Cursor terminals
├── requirements.txt            # Optional Python scripting helpers; provisioned by /setup
├── PRODUCT-RULES.md            # Braindump-before-structure golden rule
├── AGENTS.md                   # Agent coach prompt
└── CONTRIBUTING.md             # Skill conventions + check script
```

---

## Quick start

### 1. Fork and customize context

Run **`/start`** in Cursor with your **company name** and **website URL** — it researches the public web and fills [`01-context/`](01-context/) automatically.

Or copy [`02-templates/context/`](02-templates/context/) into [`01-context/`](01-context/) manually and replace placeholders. See [`01-context/README.md`](01-context/README.md).

### 2. Open in Cursor

Clone the repo and open it in [Cursor](https://cursor.com). Skills under [`.cursor/skills/`](.cursor/skills/) load automatically. Run **`/start`** to bootstrap company context — the doc workflow has no runtime dependencies beyond Cursor itself. Run **`/setup`** if you also want a local Python venv for ad-hoc scripting helpers ([`requirements.txt`](requirements.txt)); it's optional and unrelated to the doc workflow.

### 3. Optional MCP

Copy [`.cursor/mcp.json.example`](.cursor/mcp.json.example) to `.cursor/mcp.json` and add MCP servers (Jira, Confluence, etc.). `mcp.json` is gitignored.

### 4. Start a feature hub

Create `projects/PROJECT-{id}-{slug}/` and run skills in order, or try the compact example:

- [`projects/EXAMPLE-0001-sample-feature/`](projects/EXAMPLE-0001-sample-feature/)

**Example prompts:**

- "Write a product brief for onboarding checklist, PROJECT-0002."
- "Create a PRD for PROJECT-0002."
- "Run /critique-prd on the example project."

---

## Cursor skills

| Skill | Purpose |
|-------|---------|
| [`start`](.cursor/skills/start/SKILL.md) | Bootstrap `01-context/` from company name + website (`/start`) |
| [`create-product-brief`](.cursor/skills/create-product-brief/SKILL.md) | Lightweight buy-in brief |
| [`create-prd`](.cursor/skills/create-prd/SKILL.md) | PRD requirements + success metrics |
| [`create-internal-feature-announcement`](.cursor/skills/create-internal-feature-announcement/SKILL.md) | Internal feature announcement |
| [`create-support-article`](.cursor/skills/create-support-article/SKILL.md) | Customer KB article |
| [`competitive-landscape`](.cursor/skills/competitive-landscape/SKILL.md) | Competitive analysis |
| [`interview-frameworks`](.cursor/skills/interview-frameworks/SKILL.md) | User research guidance |
| [`critique-prd`](.cursor/skills/critique-prd/SKILL.md) | Rubric + panel PRD review |
| [`critique-agent`](.cursor/skills/critique-agent/SKILL.md) | Cross-doc red-team critique |

**Structure check:** `bash scripts/check_doc_skills.sh`

### Slash commands

| Command | Target |
|---------|--------|
| `/start` | [`start` skill](.cursor/skills/start/SKILL.md) |
| `/setup` | [`.cursor/commands/setup.md`](.cursor/commands/setup.md) (inline; provisions local Python `.venv/`) |
| `/critique-prd` | [`critique-prd` skill](.cursor/skills/critique-prd/SKILL.md) |
| `/critique-agent` | [`critique-agent` skill](.cursor/skills/critique-agent/SKILL.md) |

Doc-creation skills (`create-product-brief`, `create-prd`, etc.) are invoked by name or natural language — no slash command required.

---

## Feature hub convention

- **Path:** `projects/PROJECT-{id}-{slug}/`
- **Stable files:** `01-product-brief.md` … `05-support-article.md`

Full rules: [`02-templates/README.md`](02-templates/README.md#feature-hub-convention).

---

## Fork and customize checklist

1. Run **`/start`** with your company name and URL, or copy [`02-templates/context/`](02-templates/context/) into [`01-context/`](01-context/) manually.
2. Update template TODO links in [`02-templates/product/`](02-templates/product/) (priority matrix, dashboards, metering).
3. Add your own `projects/PROJECT-*` hubs; keep or delete `EXAMPLE-0001-sample-feature`.
4. Configure optional `.cursor/mcp.json` from [`.cursor/mcp.json.example`](.cursor/mcp.json.example).

---

## Security

Do not commit credentials, customer data, or conversation transcripts. See [`SECURITY.md`](SECURITY.md).

---

## Contributing

Skill authoring conventions: [`CONTRIBUTING.md`](CONTRIBUTING.md).
