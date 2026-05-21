---
name: create-prd
description: 'Write the PRD pack (02-product-requirements.md + 03-success-metrics.md) on top of an approved product brief. Use when: PRD, product requirements, requirements doc, success metrics, spec writeup, shape the PRD.'
disable-model-invocation: true
version: 1.0
---

# PRD Writer (pm-brain)

Write the **PRD pack** — product requirements and success metrics — ideally from an approved product brief (`01-product-brief.md` in the feature hub or an explicit brief path). **Preferred:** brief exists → skip Step 0.5 and use the brief as source of truth. **If no brief:** offer **`create-product-brief`** first; if the user wants a PRD anyway, run **Step 0.5** (braindump gate per [`PRODUCT-RULES.md`](../../../PRODUCT-RULES.md)) before Step 1.

**Repo convention:** Feature hub paths, skipping steps, and the skills table — see [`02-templates/README.md`](../../../02-templates/README.md) (*Feature hub convention*, *Skipping steps*, *Cursor skills*).

The pack is two tightly-coupled files:

- `02-product-requirements.md` — use cases, priorities, cross-surface considerations
- `03-success-metrics.md` — business impact, activation, adoption, retention, proposed new events

## Step 0: Locate the product brief

1. Ask for the **PROJECT Jira key** (`PROJECT-abcde`) **or** the path to an existing product brief.
2. Resolve the feature-hub folder: `projects/{PROJECT-KEY}-{slug}/`.
   - If only the key is given, list `projects/` and match the `PROJECT-{KEY}-*` directory.
   - If multiple match, show them and ask which one.
3. Confirm a brief is available:
   - `01-product-brief.md` in the feature hub, **or**
   - An explicit brief path the user provided in Step 0.
   If neither exists, suggest **`create-product-brief`** or an external brief path. If they still want a PRD without a brief, continue to **Step 0.5** (braindump gate).

## Step 0.5: Braindump gate (only when no brief)

Run this step **only if** neither `01-product-brief.md` in the feature hub nor an explicit external brief path is available. If **either** brief exists, **skip Step 0.5** — the brief is the braindump; go to Step 1.

When no brief is available, follow [`PRODUCT-RULES.md`](../../../PRODUCT-RULES.md) before Step 1:

1. Ask **3–5 product-sense questions** from `PRODUCT-RULES.md`.
2. Confirm the **braindump sufficient?** checklist (all four items — see `PRODUCT-RULES.md`).
3. If any item is missing, ask one more targeted question and wait.
4. **Override:** If the user says **"skip braindump"**, proceed to Step 1 and log `braindump: skipped by user` in both PRD files' frontmatter when you write them.

## Output

Save both files to the feature-hub folder:

- `projects/{PROJECT-KEY}-{slug}/02-product-requirements.md`
- `projects/{PROJECT-KEY}-{slug}/03-success-metrics.md`

If either file already exists, ask whether to overwrite, create a dated backup, or choose a different name — per file.

## When to Use This Skill

- After a product brief is approved and you're ready to spec
- Shaping use cases, priorities, and cross-surface considerations
- Defining business impact, activation, adoption, retention metrics and the events needed to power them
- Preparing a PRD that engineering and design can build from

## What You'll Need

**Critical inputs (collect in Step 1 if missing):**

- Approved `01-product-brief.md` in the feature-hub folder (source of truth for problem, scope, approach, expected metric impact)
- **Use cases / user flows** to spec (draw from the brief's Section D, then expand)
- **Design link** (Figma, prototype) when available — or note that design is pending
- **Candidate metrics** per category (business impact, activation, adoption, retention) with baselines if known — `[PLACEHOLDER]` when not

**Nice-to-have inputs:**

- Priority guidance (P0–P3) from the user or roadmap context
- Known platform constraints (Mobile, Slack, Governance, Localization, Accessibility)
- Reporting / data / metering decisions already made
- Pricing & packaging direction from leadership
- Existing dashboard URL, Amplitude events already in use, Lakehouse tables involved
- Jira issues, Confluence pages, Coda specs referenced by the user

## Process

### Step 1: Read brief + gather

Do **not** split this into a separate "read files, then wait for continue" round and a second "ask questions" round. Combine into **one interaction**.

1. Read the feature-hub brief: `projects/{PROJECT-KEY}-{slug}/01-product-brief.md`. Pay attention to Section C's "Expected impact on metrics" table — those rows seed Section 1 of the metrics doc.
2. Read any additional sources the user listed:
   - **Local files** (paths, folders) — read directly.
   - **Coda URLs** — use Coda MCP `url_convert` (decode), then `document_read` on the doc URI to list pages, and `page_read` on each relevant page. Use `table_rows_read` for tables holding requirements, metrics, or decisions. Merge facts into the appropriate PRD / metrics sections.
   - **Jira / Confluence (Atlassian MCP)** — pull only what the user asked for; cite issue keys / page titles in the body where helpful.
   - Scan `01-context/` files when the brief references them (platform, competition, vision) and evidence is otherwise thin.
3. In **one message** to the user, deliver:
   - **What the brief already covers** — short summary of problem, approach, in-scope / out-of-scope, and expected metric impact pulled from `01-product-brief.md`.
   - **What's still missing to write the PRD** — open questions across use cases, priorities, design, platform / governance, reporting, metering, monetization.
   - **What's still missing to write success metrics** — candidate metrics per category, baselines, dashboard URL, proposed events / event sources (Amplitude, Snowflake, APIs), and any guardrail / counter-metrics.
   - If evidence is thin, say so explicitly; **do not invent requirements or metrics**.
4. **Gate:** Do not present the outline or draft until the user has answered enough of the open questions to write each section meaningfully.

**Example shape (adapt to the feature):**

> "From the brief I have:
> - Problem: …
> - Proposed approach: …
> - In scope / out of scope: …
> - Expected metric impact: …
>
> To write the PRD I still need:
> 1. Use cases + priorities (P0–P3)
> 2. Design link (Figma) or 'pending'
> 3. Platform surfaces in scope (Mobile, Slack, Governance, …)
> 4. Reporting / metering / pricing decisions made so far
>
> For success metrics I still need:
> 5. Candidate metrics per category (business impact, activation, adoption, retention) with baselines
> 6. Dashboard URL (or 'pending')
> 7. Proposed events + source (Amplitude, Snowflake, internal API, other telemetry)
> 8. Guardrail / counter-metrics we should not move negatively"

### CHECKPOINT 1: PRD + metrics outline for approval

Once you have enough input, present a combined outline (not the full drafts):

**PRD outline**

- **Summary** — 1 line (from brief)
- **Design link** — Figma / prototype, or "pending"
- **Use cases table** — `# | Feature / use case | User benefit | Priority | Design link | Notes`
- **Experience surfaces in scope** — quick list (Mobile, Slack, Governance, …)
- **Open questions** — anything still unknown

**Metrics outline**

- **Business impact metrics** — 2–4 rows, each with baseline (or PLACEHOLDER) and target
- **Activation metrics** — 1–2 rows
- **Adoption metrics** — 1–2 rows
- **Retention metrics** — 1–2 rows
- **Guardrail / counter-metrics** — 0–2 rows
- **Proposed new events** — list with source (Amplitude / Snowflake / API)
- **Open questions** — anything still unknown

End with: **"Does this PRD + metrics framing look right? Any changes before I write the full drafts?"**

Wait for approval or revisions before Step 2.

### Step 2: Write drafts

1. Read both templates:
   - [`02-templates/product/02-product-requirements.md`](../../../02-templates/product/02-product-requirements.md)
   - [`02-templates/product/03-success-metrics.md`](../../../02-templates/product/03-success-metrics.md)
2. Write both files following the template **section structure exactly**. Set frontmatter `jira` to the PROJECT key and `date` to today in **both** files. Replace placeholders with content **grounded in the brief, PRD decisions, and the user's answers**. Use `[PLACEHOLDER]` or "TBD — need [X]" only where the user confirmed something is unknown.
3. Cross-link: the PRD `Related docs:` header points to `03-success-metrics.md`, and the metrics `Related docs:` header points to `02-product-requirements.md`.
4. Keep metrics **anchored to use cases**: every metric row should tie back to a use case in PRD Section A (mention the use case name or # in the `Definition` column when it clarifies).
5. Apply **Writing guidance** below while drafting (do not walk the user through those bullets; they are for you).

### CHECKPOINT 2: Draft review

1. Write both drafts to the feature-hub folder:
   - `projects/{PROJECT-KEY}-{slug}/02-product-requirements.md`
   - `projects/{PROJECT-KEY}-{slug}/03-success-metrics.md`
2. Point the user to both files and ask: **"Review the PRD and metrics drafts — what should I change before finalizing?"**

Wait for feedback (or explicit "looks good").

### Step 3: Finalize

1. Incorporate edits into the same file paths.
2. Confirm both files are saved.
3. **Handoff:** Tell the user the recommended next steps per [`02-templates/README.md`](../../../02-templates/README.md):
   - Internal comms — `create-internal-feature-announcement` skill.
   - Customer-facing help — `create-support-article` skill.
4. **Optional Coda:** If they want to share the PRD pack in Coda, offer to create a doc and upload via the Coda MCP (`document_create`, then `content_modify` with markdown blocks). Only offer — do not run unless asked.

---

## Writing guidance (internal — do not present as numbered steps to the user)

### PRD (`02-product-requirements.md`)

**Use cases & priorities (Section A)**

- One row per major user flow — keep the table scannable.
- Use **P0–P3** priorities. Default P0 = cannot ship without, P1 = strong should, P2 = if time, P3 = explicitly deferred.
- Below the table, include a short "Detailed requirements" block per use case with acceptance criteria.
- Every row should trace back to a persona / problem in the brief.

**Experience considerations (Section B)**

- Walk the PRD surface table using rows from **`01-context/02-products.md` → Surfaces and channels** as the source of truth (add company-specific surfaces if listed there; do not assume a fixed vertical like sales-only or CRM-only).
- If a surface is **out of scope**, mark it N and note why (prevents silent scope creep later).
- Flag where **Platform capabilities** from `01-context/02-products.md` can be reused (auth, API, eventing, audit, AI/ML, etc.) before proposing net-new infrastructure.
- Check **`01-context/02-products.md` → Integrations** for dependencies the feature touches.

**Reporting considerations (Section C)**

- State whether the feature **introduces** or **changes** customer data; align with **`01-context/01-about-company.md` → Compliance and data posture**.
- Call out AI-relevant data explicitly when the product offers AI/ML capabilities.
- Note retention / PII / governance hooks needed.

**Metering (Section D)**

- Align with **`01-context/01-about-company.md` → Go-to-market** (revenue model) and **`02-products.md` → Packaging / Add-ons** (entitlements, credits, usage limits).
- If the brief hints at usage-based or credit metering, flag metering as required and name the action.
- If uncertain, mark **Unsure** — do not invent rates.

**Monetization intent (Section E)**

- Tick exactly one of Yes / No / Unsure.
- If Yes, keep the description to 1–2 lines — detailed pricing lives in a Pricing & Packaging doc, not here.

### Success metrics (`03-success-metrics.md`)

**Ordering & coverage**

- Fill all four phases (Business impact → Activation → Adoption → Retention). If a phase has no metric, keep the section and explain why instead of deleting it.
- Every metric anchors to a **use case in PRD Section A** (reference the use case # or name in the Definition column when it sharpens the metric).
- Carry over the "Expected impact on metrics" rows from the brief's Section C into Section 1 (Business impact) and expand — these are the metrics leadership already bought into.

**Baselines and targets**

- If a baseline exists (analytics, Lakehouse, past features), cite the source in Definition or a footnote.
- If unknown, use `[PLACEHOLDER]` — never invent numbers.
- Set confidence H/M/L honestly; low confidence is fine, silent guesses are not.

**Guardrail / counter-metrics**

- Always consider at least one: what should *not* regress? (trust, time-to-value, agent-answer latency, AI credit burn, etc.)
- Put these in Section 1 under the table.

**Proposed new events (Section 5)**

- Every metric that cannot be computed from existing data needs a new event row.
- Name the source explicitly (Amplitude / Snowflake / internal API / other telemetry).
- For Amplitude events, follow the naming best-practices link in the template.
- List the key properties needed to slice the metric (e.g. `org_id`, `pack_version`, `agent_consumer`).
- Put an owner and, if applicable, a tracking Jira ticket for each event.

**Evidence discipline (applies to both files)**

- Do not invent requirements, priorities, or metrics not supported by the brief or the user's answers.
- Use `[PLACEHOLDER]` or "TBD — need [X]" when unknown — never fabricate.

**Length and clarity**

- Prefer tables and bullets over prose.
- Lead each section with the table or checklist; add narrative only where it clarifies a decision.

---

## Output templates

Use the templates at:

- [`02-product-requirements.md`](../../../02-templates/product/02-product-requirements.md)
- [`03-success-metrics.md`](../../../02-templates/product/03-success-metrics.md)

Read both before drafting. Follow the section structures exactly.

---

## Principles

- **Start from the brief** — reuse problem, scope, approach, and expected impact; don't re-derive them.
- **Evidence over assertions** — cite brief sections, context files, and user-provided sources.
- **Prioritize explicitly** — every use case gets a P0–P3.
- **Scope surfaces deliberately** — marking a surface "out" is as important as marking it "in".
- **Anchor metrics to use cases** — every metric ties back to a user flow in PRD Section A.
- **Flag money and metering early** — pricing, packaging, and metered actions block launch if surfaced late.
- **No invented numbers** — baselines and targets use `[PLACEHOLDER]` rather than guesses.

## Pre-ship checklist

- `02-product-requirements.md` and `03-success-metrics.md` share the same `jira` and `date`; **Related docs** lines cross-link each other and `01-product-brief.md`.
- Every **P0** use case has acceptance criteria in **Detailed requirements**.
- Every metric row ties to a use case in PRD Section A; business-impact rows reflect the brief’s expected impact where applicable.
- Surfaces in Section B and metering / monetization ticks match decisions — no silent defaults.
