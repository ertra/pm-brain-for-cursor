---
name: critique-agent
description: 'Pressure-test an existing product brief or PRD pack — find gaps, hidden assumptions, inconsistencies, and failure modes before stakeholder review. Use when: critique brief, critique PRD, devils advocate, red team, pressure test, find holes, what could go wrong, stress test the doc, pre-mortem.'
disable-model-invocation: true
version: 1.0
---

# Critique Agent (pm-brain)

Challenge an existing **product brief**, **PRD**, or **PRD + metrics pack** by surfacing assumptions, gaps, inconsistencies, and likely failure scenarios. You are not killing the idea — you are making it survive the next stakeholder review.

**Repo convention:** Feature hub paths and stable basenames — see [`02-templates/README.md`](../../../02-templates/README.md) (*Feature hub convention*). The braindump gate from [`PRODUCT-RULES.md`](../../../PRODUCT-RULES.md) does **not** apply here — the doc already exists.

## When to Use This Skill

- Pressure-testing a brief or PRD before sharing with SLT / GM / eng leads
- A draft "feels too easy" and you want a reality check
- Preparing for tough questions from skeptical stakeholders (Eng, Finance, Sales, Legal, Design)
- Sanity-checking brief → PRD → metrics consistency before handoff
- Pre-mortem: imagine this shipped and failed — why?

## What You'll Need

**Critical inputs (collect in Step 0 if missing):**

- The doc(s) to critique — PROJECT key + which file(s), **or** an explicit path
- Critique mode — `brief` / `prd` / `pack` (PRD + metrics together) / `cross-doc` (brief vs. PRD vs. metrics consistency)

**Nice-to-have inputs:**

- Specific concerns the PM already has ("I'm worried about engineering feasibility on use case 3")
- Target audience for the upcoming review (SLT vs. eng vs. cross-functional)
- Calibration: light (top 3 risks) / standard / hard (maximally skeptical)

## Step 0: Locate the target doc

1. Ask for the **PROJECT key** (`PROJECT-abcde`) **or** an explicit file path.
2. Resolve feature hub: `projects/{PROJECT-KEY}-{slug}/`. List matching dirs if ambiguous.
3. Confirm which doc(s) exist and which to critique. Default targets in order of preference:
   - `pack` (both `02-product-requirements.md` + `03-success-metrics.md`) if both exist
   - Single doc otherwise
   - `cross-doc` if `01`, `02`, and `03` all exist and the user wants consistency checking
4. Ask the **calibration**: light / standard / hard. Default = standard.
5. Ask for any **specific concerns** the PM already has — they get extra scrutiny.

## Process

### Step 1: Read everything that matters

In **one pass** (no extra "ready?" round-trip):

1. Read the target doc(s) in the feature hub.
2. Read the sibling docs in the hub if they exist — even when not the critique target — to enable cross-doc checks.
3. Read `01-context/` files relevant to the topic:
   - `01-context/01-about-company.md` — ICP, buyer/user, pains table, compliance, GTM
   - `01-context/02-products.md` — Surfaces, Platform capabilities, Integrations, modules, tiers
   - `01-context/03-product-vision.md` — Strategic themes table, Product principles
   - `01-context/04-competition.md` — archetypes, named exemplars, win/loss, status quo alternatives
4. **Tell the user what you found.** Format:
   > "Critiquing `02-product-requirements.md` (and `03-success-metrics.md` since it exists). Grounding in `04-competition.md` — I'll challenge any unstated parity assumptions against named competitors or archetypes."

   If context is thin, say so explicitly: "I scanned `01-context/` and didn't find direct support for your AI-coach claim — generic challenges only on that point."

### Step 2: Run the critique passes

Apply these passes in order. Skip passes that are clearly N/A for the doc type.

**Pass A — Assumptions presented as facts.** Find sentences that assert user behavior, demand, or competitor weakness without evidence. Quote each one. Mark `Evidence: cited / thin / absent` per claim.

**Pass B — Section completeness vs. template.** For each template section, mark Filled / Thin / Empty / Hand-wavy. Reference the live template:
- Brief → [`02-templates/product/01-product-brief.md`](../../../02-templates/product/01-product-brief.md), Sections A–F (esp. C "Expected impact on metrics", D "What this is NOT", E risks table).
- PRD → [`02-templates/product/02-product-requirements.md`](../../../02-templates/product/02-product-requirements.md): Use case priorities (P0–P3), Section B surface table (per template rows: Mobile, Email, Slack, CRM, governance, localization, accessibility, etc.), Section C reporting/PII/AI data, Section D metering, Section E monetization intent.
- Metrics → [`02-templates/product/03-success-metrics.md`](../../../02-templates/product/03-success-metrics.md): Business impact / Activation / Adoption / Retention coverage, guardrail counter-metrics, proposed new events with source + owner.

**Pass C — Cross-doc consistency (only when ≥2 docs exist).**
- Brief Section C metrics → carried into `03-success-metrics.md` Section 1?
- Brief Section D in-scope → matches PRD Section A use cases?
- Brief Section D out-of-scope → still excluded in PRD?
- Every metric in `03-` traces back to a use case # in PRD Section A?
- `jira` and `date` align across files; `Related docs:` cross-links present?

**Pass D — company reality checks.** Use `01-context/` to challenge:
- Vision alignment — does this fit the FY27 platform / agent direction?
- Platform reuse — could existing auth, API, context graph, RAG do this? Why isn't it?
- Competitive — what would key competitors or archetypes ship instead? Are we matching parity or differentiating?
- Surface scope — is Mobile / Slack / OE / SF silently dropped without justification?

**Pass E — Pre-mortem.** Imagine the feature shipped and failed 6 months later. Walk three failure paths:
- Adoption < 10% of expectation — why?
- Engineering took 2× the estimate — what was hidden?
- A competitor shipped first — what's our differentiation?

**Pass F — Money & ops.**
- Metering filled with a real action (or honestly "Unsure")? AI credit burn flagged?
- Monetization intent ticked (Yes / No / Unsure) with 1–2 line rationale?
- Support / docs / training burden mentioned anywhere?
- Governance / PII / Lakehouse / Audit considered (PRD Section C)?

**Pass G — Hard questions by stakeholder.** Generate 2–3 questions per:
- **Engineering** — feasibility, dependencies, hidden complexity
- **SLT / GM** — strategic fit, opportunity cost, ROI thesis
- **Sales** — what changes in the deal? competitive talk track?
- **Design** — primary user flow concerns, accessibility, mobile parity
- **Legal / Compliance** — PII, data residency, AI explainability, customer contracts
- **Support / CS** — net new tickets? known-issue articles needed?

### Step 3: Generate the critique output

Default = **chat output** using the Output Template below. Do **not** create files unless the user says so — PMs iterate fast and a critique markdown clutters the hub.

At the end of the output, offer:
> "Want me to save this as `projects/{PROJECT-KEY}-{slug}/critique-{YYYY-MM-DD}-{target}.md` for the next review, or just keep it in chat?"

If saved: filename pattern `critique-{YYYY-MM-DD}-{target}.md` where `{target}` is `brief` / `prd` / `metrics` / `pack` / `cross-doc`. Do **not** reuse the numbered `01-`–`05-` prefix — that range is reserved for the doc pack.

## Output Template

Render in chat, scannable, with section anchors back into the target doc.

````markdown
# Critique: {target doc} — {PROJECT-KEY}-{slug}

**Reviewed:** [path(s)]
**Mode:** brief / PRD / pack / cross-doc
**Calibration:** light / standard / hard
**Date:** YYYY-MM-DD

## Overall assessment

🟢 Solid · 🟡 Needs work · 🔴 High risk

**Top 3 risks** (ranked):
1. [Highest]
2. [Next]
3. [Next]

**The one question that must be answered before stakeholder review:**
> "[…]"

---

## Assumptions presented as facts

| # | Quote / paraphrase | Where (section) | Evidence | What if wrong? |
|---|---|---|---|---|
| 1 | "…" | Brief §B | thin / absent / cited | … |

---

## Section gaps (vs. template)

| Section | Status | What's missing or vague |
|---|---|---|
| Brief §C (expected impact) | Thin | Baselines marked `[PLACEHOLDER]` — no source cited |
| PRD §B Slack | Empty | No Y/N decision; silent scope creep risk |
| Metrics §1 guardrails | Empty | No counter-metric defined |

---

## Cross-doc consistency *(when applicable)*

- [ ] Brief §C metrics carried to Metrics §1
- [ ] Brief §D out-of-scope still excluded in PRD §A
- [ ] Every metric in §03 traces to a PRD §A use case #
- [ ] `Related docs:` cross-links present in `02-` and `03-`

Flag mismatches inline.

---

## Pre-mortem (3 failure paths)

### Scenario 1: Adoption is 10× lower than expected
- **How:** …
- **Early warning signs:** …
- **Mitigation:** …

### Scenario 2: Engineering takes 2× longer
- **How:** …
- **Hidden complexity:** …
- **Mitigation:** …

### Scenario 3: Competitor ships first
- **Likely competitor / move:** …
- **Differentiation that holds:** …
- **Differentiation that does not:** …

---

## company-context challenges

- **Vision fit** (`03-product-vision.md`): …
- **Platform reuse** (`02-products.md`): could `[X]` do this already?
- **Competitive** (`04-competition.md`): named competitors or archetypes — parity or differentiation?
- **Surface discipline**: Mobile / Slack / extension / CRM — explicit Y/N?

---

## Blind spots

- **User segments not considered:** …
- **Operational impact:** support tickets, docs, training, sales enablement
- **External dependencies not named:** …
- **Metering / AI credit burn:** …

---

## Hard questions by stakeholder

**Engineering** — …
**SLT / GM** — …
**Sales** — …
**Design** — …
**Legal / Compliance** — …
**Support / CS** — …

---

## Stress tests

- If adoption is 10× lower → still worth doing?
- If timeline doubles → what gets cut?
- If competitor ships first → ship anyway?
- If key person leaves → can we deliver?

---

## Recommendations before stakeholder review

1. [Action — addresses highest risk]
2. [Action — validates critical assumption]
3. [Action — pre-empts most likely hard question]

**Defer but track:**
- …

---

## The uncomfortable question

> "[The one you probably don't want to ask out loud.]"
````

---

## Calibration knobs

- **Light** — top 3 risks only, skip Passes D and G, no pre-mortem.
- **Standard** — all passes, default output.
- **Hard** — maximally skeptical; assume worst case on every assumption; double the hard questions; explicitly call out any sentence that is unverifiable.
- **Focused** — if the user names a section ("just §B and §E"), restrict passes to those plus cross-doc.

## Principles

- **Constructive challenge, not dismissal.** Frame as "here is what would go wrong; let's prepare."
- **Quote the doc.** Every assumption challenged should be tied to a specific line / section. Anchor or the PM can't act on it.
- **Evidence discipline.** Mark every claim as `cited / thin / absent / stale` (use `stale` when context `last_verified` is > 12 months old for competitive or market-timing claims). Don't invent counter-evidence; if `01-context/` is silent, say so.
- **No new templates.** Critique runs *against* the existing templates — it does not propose a new doc structure.
- **Output stays in chat by default.** Save only on request, to a `critique-*.md` filename outside the numbered `01-`–`05-` range.

## When NOT to use this skill

- The doc is still in the braindump stage — run [`create-product-brief`](../create-product-brief/SKILL.md) first.
- The doc is already in execution / handed off — too late to change course meaningfully.
- The user wants a competitive analysis, not a doc review — use [`competitive-landscape`](../competitive-landscape/SKILL.md).
- The user wants to validate with users, not pressure-test the doc — use [`interview-frameworks`](../interview-frameworks/SKILL.md).

## Pre-ship checklist (for this skill's output)

- Every assumption challenged is anchored to a quote + section in the target doc.
- Section gap table only flags real gaps (cross-checked against the live template, not assumed structure).
- Cross-doc pass run when ≥2 docs exist in the hub.
- All `01-context/` references actually exist in those files.
- Critique respects the calibration mode the user picked.
