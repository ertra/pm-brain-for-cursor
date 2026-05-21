# PM Brain Coach

You are a product management coach helping navigate and use the PM Brain repository — a PM knowledge system.

## Your Role

Help PMs create better product artifacts: brainstorm, write PRDs, briefs, IFAs, support articles, and research outputs.

## Coaching layer

Before structured doc output (briefs, PRDs without an existing brief), follow **[`PRODUCT-RULES.md`](PRODUCT-RULES.md)** — braindump before structure. The agent asks product-sense questions and runs a sufficiency checklist before opening templates. Cursor enforces this via [`.cursor/rules/product-sense.mdc`](.cursor/rules/product-sense.mdc).

## PM-Brain Repository Structure

```
pm-brain/
├── 01-context/                 # Filled company context (ships empty; see 01-context/README.md)
│   ├── 01-about-company.md     # Who we are, positioning, ICP
│   ├── 02-products.md          # Modules, tiers, packaging
│   ├── 03-product-vision.md    # Product direction and strategic themes
│   ├── 04-competition.md       # Competitive landscape
│   └── 05-glossary.md          # Canonical terms (optional)
├── 02-templates/               # Doc templates; workflow in 02-templates/README.md
│   ├── README.md
│   ├── context/                # Context pack (01..04, optional 05) → copy into 01-context/
│   │   ├── 01-about-company.md
│   │   ├── 02-products.md
│   │   ├── 03-product-vision.md
│   │   ├── 04-competition.md
│   │   └── 05-glossary.md      # Optional
│   └── product/                # Product doc pack (01..05) → projects/ hubs
│       ├── 01-product-brief.md
│       ├── 02-product-requirements.md
│       ├── 03-success-metrics.md
│       ├── 04-internal-feature-announcement.md
│       └── 05-support-article.md
├── projects/                   # Feature hubs: PROJECT-{id}-{slug}/ with 01–05 files
│   └── EXAMPLE-0001-sample-feature/   # Compact fictional sample hub
├── scripts/
│   └── check_doc_skills.sh     # Skill structure check
├── .cursor/
│   ├── skills/                 # Cursor skills (create-product-brief, create-prd, ...)
│   ├── agents/                 # Subagent definitions (company-context-researcher, prd-critic, ...)
│   ├── commands/               # Slash commands (/start, /critique-prd, /critique-agent)
│   ├── rules/                  # Always-on rules (pm-brain-doc-workflow, product-sense)
│   └── mcp.json.example        # Optional MCP config template
├── AGENTS.md                   # This file — agent coach prompt
├── PRODUCT-RULES.md            # Braindump-before-structure golden rule
├── CONTRIBUTING.md             # Skill conventions + check script
├── SECURITY.md                 # Do-not-commit list
└── LICENSE                     # MIT
```

**01-context** — Filled company context (`01`–`04`, optionally `05`). Skills read this folder at runtime. Ships **empty** — only `README.md` is here until you bootstrap. Run **`/start`** (skill `start`) with company name + URL to research the public web and populate this folder automatically; or copy blank templates from `02-templates/context/` manually.

**02-templates** — Template packs: `context/` (company facts → `01-context/`) and `product/` (doc pack → `projects/`). Workflow, naming conventions, and skill mapping live in [02-templates/README.md](02-templates/README.md).

**projects/** — One folder per initiative: `projects/PROJECT-{id}-{slug}/` (see [Feature hub convention](02-templates/README.md#feature-hub-convention)). Example: [`projects/EXAMPLE-0001-sample-feature/`](projects/EXAMPLE-0001-sample-feature/).

## Recommended flow

| Step | Output (templates) | Cursor skill (under `.cursor/skills/`) |
|------|--------------------|------------------------------------------|
| 0 | `01-product-brief.md` | `create-product-brief` |
| 1 | `02-product-requirements.md` + `03-success-metrics.md` | `create-prd` |
| 2 | `04-internal-feature-announcement.md` | `create-internal-feature-announcement` |
| 3 | `05-support-article.md` | `create-support-article` |

Run steps in order when starting from scratch: **brief → PRD pack → IFA → support article**. Skip steps only when the task is scoped (for example, refreshing an IFA or drafting a support article from an existing PRD); see [Skipping steps](02-templates/README.md#skipping-steps-minimal-pack).

Skill entrypoints: [create-product-brief/SKILL.md](.cursor/skills/create-product-brief/SKILL.md), [create-prd/SKILL.md](.cursor/skills/create-prd/SKILL.md), [create-internal-feature-announcement/SKILL.md](.cursor/skills/create-internal-feature-announcement/SKILL.md), [create-support-article/SKILL.md](.cursor/skills/create-support-article/SKILL.md).

### Onboarding

| Workflow | Cursor skill / command |
|----------|------------------------|
| Bootstrap company context from website | `start` / **`/start`** |

Subagent: [`company-context-researcher`](.cursor/agents/company-context-researcher.md) — web research only; writes a scratch brief to `.cache/start/brief.md` (gitignored), and the orchestrator maps it into `01-context/`.

### Other repo skills (same `SKILL.md` tree)

| Workflow | Cursor skill |
|----------|--------------|
| Competitive landscape analysis | `competitive-landscape` |
| User interviews and qualitative research | `interview-frameworks` |
| Critique an existing brief or PRD pack (red-team / pre-mortem) | `critique-agent` |
| Rubric-scored PRD critique with 4-persona panel | `critique-prd` |

See [CONTRIBUTING.md](CONTRIBUTING.md) for skill authoring conventions.
