---
name: create-support-article
description: >-
  Drafts a customer-facing support / KB article from the PRD pack and/or IFA
  using the repo template, then writes 05-support-article.md. Use when: support
  article, KB article, help doc, how-to from a PRD or internal feature
  announcement, or the support-article workflow.
disable-model-invocation: true
version: 1.0
---

# Support article writer (pm-brain)

Produce **`05-support-article.md`** by filling the support template from the **PRD pack** (`01-`–`03-`), **`04-internal-feature-announcement.md`**, and any extra sources the user names. Copy must be **customer-safe**: no internal codenames, roadmap-only details, or confidential identifiers unless the user explicitly allows them.

**Repo convention:** Feature hub paths, skipping steps, and the skills table — see [`02-templates/README.md`](../../../02-templates/README.md) (*Feature hub convention*, *Skipping steps*, *Cursor skills*).

## Step 0: Locate output folder and sources

**A. Feature hub (default)**

1. Ask for the **PROJECT Jira key** (`PROJECT-abcde`) **or** the path to an existing feature hub folder.
2. Resolve: `projects/{PROJECT-KEY}-{slug}/`.
   - If only the key is given, list `projects/` and match `PROJECT-{KEY}-*`.
   - If multiple match, show them and ask which one.
3. Confirm sources exist or get explicit paths:
   - Prefer **`02-product-requirements.md`** and **`03-success-metrics.md`** in that folder.
   - If the user wants IFA-grounded copy, include **`04-internal-feature-announcement.md`**.
   - If **`01-product-brief.md`** is the only spec, say the article should lean on **`02`/`03`** when possible and offer to run **`create-prd`** or accept equivalent paths / Coda.

**B. No feature hub**

If the user has no `projects/...` folder: ask for **output directory** (absolute or repo-relative) and **explicit paths or URLs** to every source (PRD files, IFA, Coda, etc.). Write **`05-support-article.md`** in the directory they name.

## Output

**Default path:** `projects/{PROJECT-KEY}-{slug}/05-support-article.md`

If the file already exists, ask whether to overwrite, create a dated backup, or choose a different name.

## When to use this skill

- Publishing or drafting customer help aligned with an approved PRD or IFA
- Turning release facts into **Applies To**, setup steps, and FAQs
- Refreshing KB copy after the internal pack changes

## What you'll need

**Critical:**

- Source docs: **PRD** (`02`/`03`), **IFA** (`04`), or **both** — or Coda / files the user lists
- **`article_type`** in frontmatter (`how_to`, `troubleshooting`, `faq`, `release_notes`, `reference`, `compliance`)

**Nice-to-have:**

- Product / package names for **`product_areas`**
- Known limits, regional caveats, permission names
- Links to design or existing public articles

## Process

### Step 1: Read + gather

Do **not** split into a "read only" round and a separate "questions" round. Combine into **one interaction**.

1. Read local sources in the feature hub (or paths the user gave): `01-product-brief.md` when present, `02-product-requirements.md`, `03-success-metrics.md`, `04-internal-feature-announcement.md`.
2. Read any additional sources:
   - **Coda** — `url_convert` (decode) if needed, then `document_read` on the doc URI to list **all** pages (including subpages). Call `page_read` on each relevant page and `table_rows_read` for requirement / flow / release tables. Merge only **customer-relevant** facts.
   - **Jira / Confluence (Atlassian MCP)** — only what the user asked for; cite keys or titles in **Additional Information** when helpful.
3. In **one message**:
   - **What the sources already cover** for a public article (summary, setup, limits, FAQs).
   - **What's missing** (packages, roles, prerequisites, screenshots, legal/compliance).
   - **Do not invent** behavior, limits, or SKUs not stated in sources.

4. **Gate:** Do not present the outline until you can map sections meaningfully (or the user accepts TBD / placeholders).

### CHECKPOINT 1: Article outline for approval

Present a structured outline (not the full article):

- **`article_type`** and working **title** / H1
- **Applies To** — products, roles, prerequisites (from sources)
- **Section plan** — whether to include or skip **Objective**; main setup subheads
- **FAQ** — 3–5 customer questions with draft answers grounded in sources
- **Tone** — neutral support voice; flag any internal-only facts to strip

End with: **"Does this outline look right? Any changes before I write the full draft?"**

Wait for approval or revisions before Step 2.

### Step 2: Write draft

1. Read [`02-templates/product/05-support-article.md`](../../../02-templates/product/05-support-article.md) and [`02-templates/README.md`](../../../02-templates/README.md) if workflow context is unclear.
2. Write `05-support-article.md` in the chosen directory following the template **section structure exactly**.
3. Set frontmatter:
   - `title` and H1 aligned with the feature
   - `article_type`, `audience: customers`, `product_areas`, `status: draft` (unless user says otherwise)
   - `jira` — PROJECT key when working from a feature hub; else `[PLACEHOLDER]` or omit per user
   - `date` — today
4. Replace `{{placeholders}}` with sourced copy. Use "Contact your admin" or omit unknown limits rather than guessing.
5. Keep **Related docs** in the file body (relative links to `01`–`04`) — for repo workflow; strip or replace if the user exports only the article body to a CMS.

### CHECKPOINT 2: Draft review

1. Point the user to the saved `05-support-article.md`.
2. Ask: **"Review the support article draft — what should I change before finalizing?"**

Wait for feedback (or explicit "looks good").

### Step 3: Finalize

1. Incorporate edits into the same path.
2. Confirm the file is saved.
3. **Handoff:** Remind them to publish through their KB/CMS process and to keep the repo copy aligned with what ships.
4. **Optional Coda:** If they want the article in Coda, offer `document_create` + `content_modify` — only if asked.

---

## Writing guidance (internal — do not present as numbered steps to the user)

**Customer safety**

- No capabilities, limits, or SKUs not in the sources.
- Avoid internal codenames unless the user asked to keep them for launch.

**Structure**

- Use `article_type` and template comments: skip **Objective** for pure FAQ/reference when appropriate.
- **Applies To** and **Before You Begin** must match source facts.

**FAQ**

- Answers must be defensible from **public** documentation expectations (align with IFA FAQ prep when both exist).

**Evidence**

- Prefer PRD + IFA; use `[PLACEHOLDER]` for unknowns.

---

## Output template

[`02-templates/product/05-support-article.md`](../../../02-templates/product/05-support-article.md) — read before drafting; follow section structure exactly.

---

## Principles

- **Customer truth only** — if it is not in the sources, do not ship it in the article.
- **Align with the pack** — when IFA exists, release-notes and FAQ themes should match.
- **Scannable** — steps, bullets, clear headings; minimal internal narrative.

## Pre-ship checklist

- **`article_type`** matches which sections you kept or skipped (see template comments in `05-support-article.md`).
- **Applies To**, steps, limits, and SKUs match sources only — no invented behavior.
- **Customer-safe:** no internal codenames or roadmap-only details unless the user explicitly allowed them.
- **Related docs** (`01`–`04`) present for the repo copy; strip or replace when exporting body-only to a CMS.
