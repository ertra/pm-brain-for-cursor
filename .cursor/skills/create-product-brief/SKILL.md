---
name: create-product-brief
description: 'Write concise (~2-page) product briefs to get buy-in before investing in full specs. Use when: product brief, one pager, feature brief, quick spec, feature proposal, pitch idea.'
disable-model-invocation: true
version: 1.0
---

# Product Brief Writer

Write concise product briefs (~2 printed pages) to get buy-in before investing in full specs.

**Repo convention:** Feature hub paths, skipping steps, and the skills table — see [`02-templates/README.md`](../../../02-templates/README.md) (*Feature hub convention*, *Skipping steps*, *Cursor skills*).

## Step 0: Collect identifiers

1. Ask for the **product brief name** (working title).
2. Ask for the **project tracker id** (e.g. `PROJECT-0001` or your team's key format).

**Folder path:** Build the output path as `projects/{PROJECT-KEY}-{slug}/01-product-brief.md` where `slug` is the brief name in **lowercase with hyphens** (kebab-case). Strip punctuation; collapse spaces to hyphens.

**Example:** `PROJECT-2211` + "MS Teams integration for notifications" → `projects/PROJECT-2211-ms-teams-integration-for-notifications/01-product-brief.md`

## Step 0.5: Braindump gate

**Before Step 1:** Follow [`PRODUCT-RULES.md`](../../../PRODUCT-RULES.md). Do **not** read `01-context/` files, present an outline, or open the brief template until this gate passes or the user overrides.

1. Ask **3–5 product-sense questions** from `PRODUCT-RULES.md` (pick what fits the topic — who is this really for, what are you assuming, what could go wrong, why now, who loses, etc.).
2. After the user responds, confirm the **braindump sufficient?** checklist (all four must be true):
   - Key assumptions named
   - Known vs. guessed separated
   - At least one risk / edge case / second-order effect touched
   - Something uncomfortable or challenging surfaced
3. If any item is missing, ask **one** more targeted question and wait — do not proceed to Step 1.
4. **Override:** If the user says **"skip braindump"**, proceed to Step 1 immediately. When writing the draft, set frontmatter `braindump: skipped by user` or a one-line note at the top of the body.

Only after the checklist passes (or skip) continue to Step 1.

## Output

Save the finalized brief to:

`projects/{PROJECT-KEY}-{slug}/01-product-brief.md`

Use the same `slug` rule as Step 0.

## When to Use This Skill

- PMs pitching new ideas to leadership
- Getting exec approval on early-stage ideas
- Aligning stakeholders before writing a full PRD
- Requesting resources for a new initiative
- Communicating decisions or recommendations quickly

## The Problem

A full PRD is overkill for getting initial buy-in. You don't need 10 pages of specs to get a "yes, let's explore this." You need a short, scannable pitch that answers: **What's the problem? Why now? What's the proposed direction?**

## What You'll Need

**Critical inputs (collect in Step 1 if missing):**

- What problem are you trying to solve?
- Who has this problem?
- What evidence do you have that it's worth solving?
- Who is the audience? (execs, eng leads, cross-functional team)

**Nice-to-have inputs:**

- Rough solution direction
- Similar initiatives or competitors
- Decision deadline

## Process

### Step 1: Research & Gather

Do **not** split this into a separate "read files, then wait for continue" round and a second "ask questions" round. Combine into **one interaction**.

1. Read the context files in `01-context/` (filled instances; blank templates live in [`02-templates/context/`](../../../02-templates/context/) for new repo setup):
   - `01-context/01-about-company.md` — ICP, **Buyer vs end user**, pains table, GTM, compliance
   - `01-context/02-products.md` — Modules, tiers, **Surfaces**, **Platform capabilities**, **Integrations**
   - `01-context/03-product-vision.md` — **Strategic themes** table, **Product principles**, north star
   - `01-context/04-competition.md` — Category map, **Win/loss**, **Status quo alternatives** (for brief §B "how customers solve today")
   - `01-context/05-glossary.md` if present — canonical terms
   - If other markdown files exist under `01-context/`, scan them for relevant evidence.
2. In **one message** to the user, deliver:
   - **What you found** — bullet list with file references (e.g. "Vision lists Slack as an external surface — `03-product-vision.md`").
   - If **no file directly supports the topic**, say so explicitly: list every file you scanned and note that evidence is thin or absent. Do not skip this — it prevents silent hallucination of context.
   - **What's still missing** — all open questions in one place (problem, audience, evidence gaps, links to extra data). Use the "Critical inputs" list above. Ask for **external sources** when context is thin: customer interviews, CFRs, support tickets, analytics, internal docs, links.
3. **Gate:** Do not present the outline or write the draft until you understand the problem and audience. If the user hasn't answered your questions, wait for their reply.

**Example shape (adapt to the topic):**

> "Here's what I found in context:
> - …
> - …
>
> To finish the outline I still need:
> 1. …
> 2. …"

### CHECKPOINT 1: Outline for approval

After you have enough input, present a **structured outline** (not the full brief yet):

- **One-line summary** — what we're building and for whom
- **Problem** — who, what, how big (or "unknown" if evidence is thin)
- **Evidence** — cite context files or mark gaps as `Evidence: TBD — need [X]` (do not infer or fabricate)
- **Why now** — 1–2 bullets (strategy, market, urgency, opportunity cost)
- **Proposed direction** — general approach + what's in / out of scope (high level)
- **Key risks** — top 2–3

End with: **"Does this framing look right? Any adjustments before I write the full brief?"**

Wait for the user to approve or revise before Step 2.

### Step 2: Write draft

1. Read [`02-templates/product/01-product-brief.md`](../../../02-templates/product/01-product-brief.md).
2. Write the full brief following the template **section structure exactly** — fill placeholders with evidence from context files and the user's answers. Set template frontmatter `jira` to the PROJECT key and `date` to the brief date.
3. Apply **Writing guidance** below while drafting (do not walk the user through those bullets; they are for you).

### CHECKPOINT 2: Draft review

1. Write the draft to `projects/{PROJECT-KEY}-{slug}/01-product-brief.md` (same slug rule as Step 0) so the user can open it in the editor.
2. Point them to the file and ask: **"Review the draft — what should I change before finalizing?"**

Wait for feedback (or explicit "looks good").

### Step 3: Finalize

1. Incorporate edits from the review into the same file path (`projects/{PROJECT-KEY}-{slug}/01-product-brief.md`).
2. **Length:** Aim for **≤ ~120 lines of body content** (excluding YAML frontmatter) — roughly **two printed pages**, scannable. Trim tables, duplicate bullets, and long paragraphs if the draft runs long.
3. Confirm the file is saved.
4. **Handoff:** Tell the user the recommended next step per [`02-templates/README.md`](../../../02-templates/README.md): shape the PRD with [`02-product-requirements.md`](../../../02-templates/product/02-product-requirements.md) (and [`03-success-metrics.md`](../../../02-templates/product/03-success-metrics.md) as needed).
5. **Optional export:** If they use Confluence, Notion, or another wiki, offer to format for paste — only if they ask.

---

## Writing guidance (internal — do not present as numbered steps to the user)

Use this checklist while building the outline and drafting. The user sees **Checkpoints 1–2** only.

**Adapt tone to the audience (from Step 1)**

- **SLT / execs** — Lead with strategic thesis. Keep Section B tight; weight Section C (why now, competitive, business benefit).
- **GM / eng leads** — Emphasize dependencies, assumptions, and technical risk. Sections D and E carry more detail.
- **Cross-functional** — Make trade-offs and **What this is NOT** prominent in Section D.

**Define the problem**

- Who has this problem? (personas / ICP from context)
- What is the problem in their words?
- How big is it? (quantify when possible; use `[PLACEHOLDER]` instead of inventing numbers)
- What's the evidence? (context files or user-provided sources)

**Explain why now**

- Strategic alignment (vision / company context)
- Market or competitive pressure
- Customer urgency (feedback, renewals, deals)
- Opportunity cost of waiting

**Propose solution direction**

- General direction only — not a full spec
- Explicit **out of scope** to prevent creep
- MVP shape if helpful

**Risks and open questions**

- Show you've thought it through; use the template's risk table and open questions
- Section D points to **Section E** for detailed risk analysis — keep that consistency

**Constrain length and clarity**

- Target **≤ ~120 lines** of body (excluding frontmatter), ~2 printed pages
- Prefer bullets over long paragraphs
- Lead with the punchline in the one-line summary and opening of Section B
- Cut anything that doesn't support the narrative (problem → why now → direction → risks / next steps)

---

## Output template

Use the template at [`01-product-brief.md`](../../../02-templates/product/01-product-brief.md). Read it before generating the brief. Follow the section structure exactly.

---

## Principles

- **Evidence over assertions** — Cite context filenames; use `[PLACEHOLDER]` instead of inventing numbers.
- **Problem before solution** — Earn the right to propose.
- **Scope ruthlessly** — Narrow initiatives are easier to align on.
- **Risks acknowledged** — Builds trust; use Section E.
- **Audience-aware** — Match depth and emphasis to who reads the brief (see Writing guidance).

## Pre-ship checklist

- Frontmatter `jira` is the real PROJECT key (replace template placeholder `"PROJECT-#####"`).
- Body length within target; Section C metrics use `[PLACEHOLDER]` or cited evidence — not invented numbers.
- Sections D/E match the approved outline; Section E risk table reflects known risks and mitigations.
