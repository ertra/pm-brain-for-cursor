---
name: create-internal-feature-announcement
description: >-
  Drafts an internal feature announcement (IFA) from the PRD pack and user
  sources using the repo template, then writes 04-internal-feature-announcement.md.
  Use when: IFA, internal feature announcement, internal FAQ, Slack IFA prep,
  launch comms pack, or internal product documentation from the template.
disable-model-invocation: true
version: 1.0
---

# Internal feature announcement (IFA) writer (pm-brain)

Produce **`04-internal-feature-announcement.md`** by filling the IFA template from the **PRD pack** (`01-`–`03-`) and any extra sources the user names. Content is **internal only**; do not copy confidential customer identifiers into examples unless the user explicitly allows it.

**Repo convention:** Feature hub paths, skipping steps, and the skills table — see [`02-templates/README.md`](../../../02-templates/README.md) (*Feature hub convention*, *Skipping steps*, *Cursor skills*).

This skill assumes a PRD pack exists; if `02-product-requirements.md` and `03-success-metrics.md` are missing, tell the user to run **`create-prd`** first or provide equivalent source paths.

## Step 0: Locate the feature hub

1. Ask for the **PROJECT Jira key** (`PROJECT-abcde`) **or** the path to an existing feature hub folder.
2. Resolve the feature-hub folder: `projects/{PROJECT-KEY}-{slug}/`.
   - If only the key is given, list `projects/` and match the `PROJECT-{KEY}-*` directory.
   - If multiple match, show them and ask which one.
3. Confirm the PRD pack exists in that folder: `01-product-brief.md`, `02-product-requirements.md`, and `03-success-metrics.md`. If any are missing, tell the user to run **`create-prd`** first or provide explicit paths to equivalent docs.

## Output

Save the deliverable to:

`projects/{PROJECT-KEY}-{slug}/04-internal-feature-announcement.md`

If the file already exists, ask whether to overwrite, create a dated backup, or choose a different name.

## When to use this skill

- Aligning internal comms before or after launch
- Preparing Slack `#internal-feature-announcement` copy and internal FAQ stems
- Handing off facts to support via the IFA before a customer-facing article

## What you'll need

**Critical inputs (collect in Step 1 if missing):**

- Feature hub with `01-product-brief.md`, `02-product-requirements.md`, `03-success-metrics.md`
- **Roadmap / release** — Alpha, private beta, GA (or explicit TBD)
- **Key contacts** — PM, EM, PMM (names or `[PLACEHOLDER]`)

**Nice-to-have inputs:**

- Design link (Figma, screenshots)
- Phased rollout table, limitations, regional or integration caveats
- Prior IFA drafts, meeting notes, Coda / Confluence / Jira references

## Process

### Step 1: Read + gather

Do **not** split this into a separate "read files, then wait" round and a second "ask questions" round. Combine into **one interaction**.

1. Read the feature-hub PRD pack: `01-product-brief.md`, `02-product-requirements.md`, `03-success-metrics.md`.
2. Read any additional sources the user listed:
   - **Local files** (paths, folders) — read directly.
   - **Coda URLs** — use Coda MCP `url_convert` (decode) if needed, then `document_read` on the doc URI to list pages, and `page_read` on each relevant page. Use `table_rows_read` for tables holding requirements, rollout, or FAQs. Do not assume a single page is complete.
   - **Jira / Confluence (Atlassian MCP)** — pull only what the user asked for; cite issue keys / page titles in the body where helpful.
3. In **one message** to the user, deliver:
   - **What the PRD pack already covers** — short summary: problem, scope, key use cases, surfaces, open questions.
   - **What's still missing for the IFA** — roadmap dates, contacts, phased rollout, differentiation vs workarounds, external release-notes tone, customer FAQ stems, screenshots.
   - If evidence is thin, say so explicitly; **do not invent** rollout dates, named owners, or product behavior.
4. **Gate:** Do not present the outline until you have enough to fill the template meaningfully (or the user has confirmed TBD / placeholders for gaps).

### CHECKPOINT 1: IFA outline for approval

Present a structured outline (not the full doc):

- **Roadmap row** — link, Alpha / Private beta / GA (or TBD)
- **Contacts** — PM, EM, PMM
- **Slack post** — 4–6 scannable lines (what + who it's for)
- **Top use cases** — 2–3 bullets mapped to the PRD
- **Rollout phases** — if applicable; else "single ship" or N/A
- **External release notes** — one-line summary + bullet themes
- **Customer FAQs** — 3–5 question stems with draft answers grounded in sources

End with: **"Does this IFA framing look right? Any changes before I write the full draft?"**

Wait for approval or revisions before Step 2.

### Step 2: Write draft

1. Read [`02-templates/product/04-internal-feature-announcement.md`](../../../02-templates/product/04-internal-feature-announcement.md) and [`02-templates/README.md`](../../../02-templates/README.md) if pack context is unclear.
2. Write `projects/{PROJECT-KEY}-{slug}/04-internal-feature-announcement.md` following the template **section structure exactly**. Set frontmatter:
   - `title` — feature name + "Internal Feature Announcement" (match template shape)
   - `jira` — PROJECT key
   - `date` — today
   - `audience: Internal only` and `source` per template
3. Replace `{{placeholders}}` with copy grounded in the PRD pack and user answers. Use `[PLACEHOLDER]` or "TBD — need [X]" where unknown — never fabricate GA dates or named owners.
4. Preserve **INTERNAL USE ONLY**, headings, tables, horizontal rules, and the **Related docs** line (relative links to `01-` / `02-` / `03-` in the same folder).

### CHECKPOINT 2: Draft review

1. Point the user to `projects/{PROJECT-KEY}-{slug}/04-internal-feature-announcement.md`.
2. Ask: **"Review the IFA draft — what should I change before finalizing?"**

Wait for feedback (or explicit "looks good").

### Step 3: Finalize + handoff

1. Incorporate edits into the same file path.
2. Confirm the file is saved.
3. **Handoff:** Per [`02-templates/README.md`](../../../02-templates/README.md), the next step for customer-facing help is **`create-support-article`**.
4. **Optional Coda:** If they want to share the IFA in Coda, offer to create a doc and upload via the Coda MCP (`document_create`, then `content_modify` with markdown blocks). Only offer — do not run unless asked.

---

## Writing guidance (internal — do not present as numbered steps to the user)

**Roadmap table**

- Prefer **TBD** or `[PLACEHOLDER]` over guessed dates.

**Slack announcement**

- 4–6 scannable lines; lead with **what** and **who it's for**; align with Feature overview below.

**Product differentiation**

- Ground in PRD Sections B/C and brief; no invented competitive claims.

**Release notes (external)**

- Neutral customer tone; no internal codenames unless the user asked to keep them.

**Customer FAQs (PM deliverable)**

- Each answer must be supportable from **public** documentation paths you expect (aligns with **`create-support-article`**).

**Evidence discipline**

- Only facts from the PRD pack, context files, or user-provided sources; use `[PLACEHOLDER]` instead of guessing.

---

## Output template

Use the template at [`02-templates/product/04-internal-feature-announcement.md`](../../../02-templates/product/04-internal-feature-announcement.md). Read it before drafting. Follow the section structure exactly.

---

## Principles

- **Start from the PRD pack** — reuse problem, scope, use cases, and metrics context; don't re-derive from scratch.
- **Evidence over assertions** — cite brief / PRD sections and user-provided sources.
- **Internal vs external** — IFA is internal; release-notes and FAQ prep should still read as publishable where marked.
- **No invented launch facts** — dates and named owners need sources or explicit TBD.

## Pre-ship checklist

- **INTERNAL USE ONLY** banner and **Related docs** (`01`–`03`) are present and paths match the feature hub.
- Slack post, roadmap table, and contacts are sourced or explicitly TBD / `[PLACEHOLDER]`.
- **Release notes (external)** and **Customer FAQs** read publishable; FAQ answers align with what **`create-support-article`** can defend publicly.
- No confidential customer identifiers in examples unless the user allowed them.
