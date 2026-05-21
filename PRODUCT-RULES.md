# Product Rules — Braindump Before Structure

**Golden rule:** Braindump before structure.

Before you open any template, framework, or structured doc skill: help the PM think first. Your raw, unstructured thinking is more valuable than perfectly formatted templates filled with shallow answers.

**For agents:** This file is the canonical spec for the braindump gate. Cursor enforces it via [`.cursor/rules/product-sense.mdc`](.cursor/rules/product-sense.mdc). Doc skills embed the gate in Step 0.5 where applicable.

---

## Why this matters

Frameworks and templates are seductive — they give you boxes to fill. The trap is filling boxes without thinking deeply. The fix: **think before you structure.**

Templates organize good thinking. They do not create it.

---

## The workflow

### Step 1: Braindump (no structure)

When the PM has a product decision, problem, or opportunity:

1. Do **not** open a template yet.
2. Ask **3–5 product-sense questions** (see below) — pick the ones that make the plan uncomfortable.
3. Let the PM answer in messy, honest form — bullets, fragments, voice-to-text style is fine.
4. Stay in braindump mode until the sufficiency checklist passes (or the user overrides).

**Time box:** 10–30 minutes of back-and-forth is enough for most briefs.

### Step 2: Pattern recognition (light structure)

Before opening a template, briefly reflect back:

- What themes emerged?
- What assumptions are being made?
- What is known vs. guessed?
- What makes this uncomfortable?
- What is being avoided?

**Time box:** 5–10 minutes.

### Step 3: Open the template

Only now invoke the doc skill and fill the template — using insights from the braindump, not generic filler.

---

## Product-sense questions (pick 3–5)

Use these before any brief or PRD when the gate applies. Do not ask all of them — choose what fits the topic.

1. **Who is this really for?** Not "users" — name the persona or role and the job they're trying to do.
2. **What are you assuming about how they'll use this?** What if that assumption is wrong?
3. **What evidence do you have this is worth solving now?** What would change your mind?
4. **What could go catastrophically wrong?** Second-order effects — "and then what?"
5. **Why this, why now?** What is the opportunity cost of waiting?
6. **What are you hoping *not* to hear?** (Often the thing worth investigating.)
7. **Who loses if we ship this?** Internal stakeholders, customer segments, or metrics that might regress.

---

## Is the braindump sufficient?

The agent may **not** move to a template or structured outline until **all four** are true:

1. **Key assumptions are named** — not just the desired outcome.
2. **Known vs. guessed is separated** — the PM (or agent summary) explicitly labels what is evidence vs. hypothesis.
3. **At least one risk, edge case, or second-order effect** has been touched.
4. **Something uncomfortable or challenging** to the current plan has been surfaced.

If any item is missing, stay in braindump mode and ask one more targeted question.

---

## Override

The user may say **"skip braindump"** at any time. The agent must obey immediately and proceed to the doc skill — but log the override:

- In a product brief: add `braindump: skipped by user` to YAML frontmatter, or a one-line note at the top of the draft body.
- In a PRD (when gate applied): same pattern in both `02-product-requirements.md` and `03-success-metrics.md` frontmatter or top of file.

Do not argue after a clear skip request.

---

## Confidence × reversibility (decision aid)

Use after braindump, when choosing how hard to push for more input vs. moving to structure:

| Confidence | Reversibility | Action |
|------------|---------------|--------|
| **>80%** | Reversible | Decide / structure now. Set a review date. |
| **>80%** | Irreversible | Sanity-check with 2–3 others, then structure. |
| **50–80%** | Can learn quickly (<1 day) | Gather the specific fact that would raise confidence, then structure. |
| **50–80%** | Slow to learn | Structure with current info + explicit review point. |
| **<50%** | — | Do not structure yet. Learn more or reframe the decision. |

---

## When the gate applies

| Skill / request | Gate |
|-----------------|------|
| **`create-product-brief`** (or any ad-hoc "write a product brief") | **Required** — run braindump before Step 1 (research & gather). |
| **`create-prd`** (or ad-hoc "write a PRD") | **Required only when no brief is available** — neither `01-product-brief.md` in the feature hub nor an explicit external brief path from the user. If either exists, the brief is the braindump; skip to Step 1. |
| **`create-internal-feature-announcement`**, **`create-support-article`** | **Not required** — downstream of completed thinking. |
| **`competitive-landscape`**, **`interview-frameworks`** | **Not required** — different workflow (research / interviews). |

Ad-hoc prompts in Cursor ("write me a brief for X") follow the same table — see always-on enforcement in `.cursor/rules/product-sense.mdc`.

---

## Links

- Doc workflow: [`AGENTS.md`](AGENTS.md) → Recommended flow
- Product brief skill: [`.cursor/skills/create-product-brief/SKILL.md`](.cursor/skills/create-product-brief/SKILL.md)
- PRD skill: [`.cursor/skills/create-prd/SKILL.md`](.cursor/skills/create-prd/SKILL.md)
- Templates: [`02-templates/README.md`](02-templates/README.md)
