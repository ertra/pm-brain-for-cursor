# PM Brain — document templates

This directory holds **template packs** for company context and product documentation:

- **Context pack** (`01`–`04`, optional `05`) — [`context/`](context/) — copy into [`01-context/`](../01-context/) and fill with your company facts.
- **Product doc pack** (`01`–`05`) — [`product/`](product/) — skills materialize into [`projects/`](../projects/) feature hubs.

Copy or draft from these files; keep the **section structure and frontmatter shape** from the templates unless the team agrees on a deliberate change.

## Context templates

| File | Purpose |
|------|---------|
| **`context/01-about-company.md`** | Company, ICP, buyer vs user, GTM, compliance, brand voice, pains table. Frontmatter includes `confidence`, `last_verified`. |
| **`context/02-products.md`** | Surfaces, platform capabilities, integrations, modules, tiers, add-ons. Tables include **Source** column. |
| **`context/03-product-vision.md`** | North star, strategic themes table, product principles, non-goals. |
| **`context/04-competition.md`** | Category map (with named exemplars), win/loss, status quo, recent moves, pricing bands. |
| **`context/05-glossary.md`** (optional) | Canonical product terms — use for consistent naming in docs. |

## Context instance convention

Materialize filled company context under **`01-context/`** with the **same basenames** as the context templates:

| Basename | Role |
|----------|------|
| `01-about-company.md` | Who you are, ICP, pains |
| `02-products.md` | Modules, tiers, add-ons |
| `03-product-vision.md` | Vision and strategic themes |
| `04-competition.md` | Competitive framing |
| `05-glossary.md` | Canonical terms (optional) |

Skills read from **`01-context/`** at runtime — not from `02-templates/context/`. `01-context/` ships **empty** (only its `README.md`). To populate it, run **`/start`** with your company name and URL (automated), or copy `context/01-*.md` through `context/04-*.md` into `01-context/` and add `context/05-glossary.md` only if you need a glossary.

## Product templates

| File | Purpose |
|------|---------|
| **`product/01-product-brief.md`** | Lightweight product brief for buy-in before full specs (problem, rationale, approach, risks, next steps). Frontmatter: `title`, `jira` (project key; templates use quoted placeholder `"PROJECT-#####"` so YAML parses correctly), `date`. |
| **`product/02-product-requirements.md`** | PRD product requirements — use cases, priorities, constraints. Frontmatter: `title`, `jira`, `date`. |
| **`product/03-success-metrics.md`** | PRD success metrics — business impact, adoption, retention dashboards. Frontmatter: `title`, `jira`, `date`. |
| **`product/04-internal-feature-announcement.md`** | Internal feature announcement (IFA) and FAQ-style product documentation. Frontmatter: `title`, `jira`, `date`, `audience`, `source`. |
| **`product/05-support-article.md`** | Customer-facing knowledge base article outline. Frontmatter: `title`, `jira`, `date`, `article_type`, `audience`, `product_areas`, `status`. |

## Feature hub convention

Materialize each initiative under **`projects/PROJECT-{id}-{slug}/`**:

- **`{id}`** — Your tracker epic or initiative id (e.g. `0001` for `PROJECT-0001`).
- **`{slug}`** — Short kebab-case name derived from the feature title (lowercase, hyphens, no punctuation).

**Stable basenames** inside that folder (so `Related docs` links and skills stay predictable):

| Basename | Role |
|----------|------|
| `01-product-brief.md` | Buy-in brief |
| `02-product-requirements.md` | PRD requirements |
| `03-success-metrics.md` | PRD metrics |
| `04-internal-feature-announcement.md` | IFA |
| `05-support-article.md` | Customer KB draft |

**Example:** `PROJECT-0001` + “onboarding checklist for new reps” → `projects/PROJECT-0001-onboarding-checklist-for-new-reps/01-product-brief.md` (and sibling files as you add them).

See also the sample hub: [`projects/EXAMPLE-0001-sample-feature/`](../projects/EXAMPLE-0001-sample-feature/).

## Skipping steps (minimal pack)

- **Full pack:** `01` → `02`+`03` → `04` → `05` when you are standing up a new feature end-to-end.
- **PRD only:** You may write `02`+`03` without `01` if leadership already approved the initiative elsewhere; still keep one feature hub and stable names.
- **IFA:** The **`create-internal-feature-announcement`** skill expects **`01`**, **`02`**, and **`03`** in the feature hub. If the brief is missing, add `01` first or point the skill at equivalent docs the user provides.
- **Support article:** **`create-support-article`** can run from **`02`+`03`** alone, or include **`04`** for IFA-grounded copy, or use explicit file paths / URLs if there is no `projects/...` folder.

## Suggested workflow

0. **Product Brief** — Pitch the idea and get buy-in (`01-product-brief.md`). Optional — skip if you already have approval.
1. **PRD** — Shape the problem, solution, and metrics (`02-product-requirements.md`, `03-success-metrics.md`).
2. **IFA** — Align internal comms and support-facing prep (`04-internal-feature-announcement.md`), driven by the PRD where possible.
3. **Support article** — Publish customer help content (`05-support-article.md`), aligned with IFA and release facts.

**Optional review step:** between Step 0 and Step 1, or before sharing the `02`+`03` pack with leadership / eng leads:

- **`/critique-prd`** — rubric-scored PRD pack review with a 4-persona panel and a concrete rewrite of the weakest section. See [`.cursor/skills/critique-prd/SKILL.md`](../.cursor/skills/critique-prd/SKILL.md).
- **`/critique-agent`** — broader cross-doc red-team (brief + PRD + metrics): assumptions, pre-mortem, stakeholder hard questions. See [`.cursor/skills/critique-agent/SKILL.md`](../.cursor/skills/critique-agent/SKILL.md).

## Cursor skills

| Skill folder | Primary template(s) | Default output |
|--------------|---------------------|----------------|
| **`create-product-brief`** | `product/01-product-brief.md` | `projects/PROJECT-{id}-{slug}/01-product-brief.md` |
| **`create-prd`** | `product/02-product-requirements.md`, `product/03-success-metrics.md` | Same hub: `02-` and `03-` |
| **`create-internal-feature-announcement`** | `product/04-internal-feature-announcement.md` | Same hub: `04-` |
| **`create-support-article`** | `product/05-support-article.md` | Same hub: `05-` (or user-chosen directory) |

Entrypoints: [`.cursor/skills/create-product-brief/SKILL.md`](../.cursor/skills/create-product-brief/SKILL.md), [`.cursor/skills/create-prd/SKILL.md`](../.cursor/skills/create-prd/SKILL.md), [`.cursor/skills/create-internal-feature-announcement/SKILL.md`](../.cursor/skills/create-internal-feature-announcement/SKILL.md), [`.cursor/skills/create-support-article/SKILL.md`](../.cursor/skills/create-support-article/SKILL.md).

Repo coach overview: [`AGENTS.md`](../AGENTS.md).

## External references in templates

[`product/02-product-requirements.md`](product/02-product-requirements.md) and [`product/03-success-metrics.md`](product/03-success-metrics.md) include **placeholder comments** where your company may link internal wikis (priority definitions, metering, dashboards, analytics naming). Replace those with your canonical URLs when forking this repo.

## Output filenames (convention)

When materializing a pack into a feature hub or repo folder, keep **stable basenames** so cross-links and skills stay predictable:

- `01-product-brief.md`
- `02-product-requirements.md`
- `03-success-metrics.md`
- `04-internal-feature-announcement.md`
- **`05-support-article.md`** — customer support / KB draft in the same feature hub as `01`–`04` (default output of **`create-support-article`**); the user may set another folder for ad-hoc drafts.
