---
name: start
description: "Bootstrap company context from a website: collect company name and URL, run web research, fill 02-templates/context templates, and write 01-context/. Trigger on: /start, set up my company, bootstrap context, onboard company."
argument-hint: "[optional company name or URL if user already provided]"
---

# Start — Company context bootstrap

Collect company name and website URL, research the public web, then populate [`01-context/`](../../../01-context/) from [`02-templates/context/`](../../../02-templates/context/). **Braindump gate does not apply.**

---

## First turn — opening message (strict)

When `/start` is invoked and **both** company name and website URL are **not** already confirmed in the user's message:

- Use a **one-sentence preamble** only, then the two input prompts. No greeting, skill overview, step list, links, or extra explanation.
- Do **not** mention research, subagents, templates, or next steps until inputs are confirmed.

**Allowed opening (keep this shape; wording may vary slightly):**

> I'll fill [`01-context/`](../../../01-context/) for you — I just need two pieces of info:
>
> **Company name** — display name for your company  
> **Website URL** — homepage (e.g. `https://example.com`)

Use `AskQuestion` when available with the same preamble plus exactly those two fields; otherwise post the preamble and two prompts in chat.

If the user already provided name or URL in the invoke message, use the same one-sentence preamble and ask **only** for the missing field.

---

## Step 0 — Collect inputs (strict)

Before any web fetch or file write, obtain and confirm:

1. **Company name** (display name)
2. **Website URL** (homepage)

If the user invoked `/start` with name or URL in the message, confirm both values before proceeding — still without extra explanatory text until both are set.

**Normalize URL:**

- Ensure scheme: `https://` (upgrade `http://` if needed)
- Strip trailing slash from path (keep path if not homepage)
- Reject obviously invalid URLs (no domain)

Do **not** fetch the web, spawn research, or write files until both values are confirmed.

---

## Step 1 — Spawn company-context-researcher

**Do not research inline in the main context** when a subagent is available — isolated research reduces hallucination and keeps the orchestrator focused on template mapping.

Spawn the **`company-context-researcher`** agent ([`.cursor/agents/company-context-researcher.md`](../../agents/company-context-researcher.md)):

- **Task tool:** prefer `subagent_type: company-context-researcher`. If unregistered, use `generalPurpose` and start with: *"You are the company-context-researcher agent. Open `.cursor/agents/company-context-researcher.md` and follow it exactly."*
- **Write scope:** subagent may write **only** to `.cache/start/brief.md` (gitignored). It must not modify `01-context/`, `02-templates/`, or anything else.

**Prompt must include:**

- `company_name: [name]`
- `website_url: [normalized URL]`
- Instruction to **write the complete Company Context Research Brief to `.cache/start/brief.md`** per the agent file's "Hand-off" section (all sections including `section_confidence`, `about_company`, `products`, `product_vision`, `competition`, `glossary`, `sources`, `gaps`) and return only `brief_path`, `bytes_written`, and a 3–5 line summary.

If web tools are unavailable and the agent returns the degradation message, stop and ask the user to paste key page content or enable web tools — do not fill `01-context/` from model memory alone.

---

## Step 1.5 — Read the brief from disk

After the subagent returns, **read the full brief from `.cache/start/brief.md`** using the file-read tool. Treat the file — not the subagent's spoken response — as the source of truth for the mapping in Step 2.

**Sanity checks (do all four):**

1. **File exists** at `.cache/start/brief.md`. If missing, stop and ask the user whether the subagent failed silently — do not proceed to write `01-context/`.
2. **First line is `# Company Context Research Brief`**. If not, stop and re-run the subagent (the file is malformed).
3. **All expected top-level headings are present:** `## section_confidence`, `## about_company`, `## products`, `## product_vision`, `## competition`, `## glossary`, `## sources`, `## gaps`. If any are missing, ask the subagent to re-write the brief before mapping.
4. **Brief is dense enough.** Inspect the loaded content. Confirm the freeform research tables — `pains_table`, `core_modules`, `category_map`, and `recent_moves` — each have at least one populated row (these are the tables the subagent has to invent from research, unlike `surfaces` or `platform_capabilities` which have pre-listed rows that can be `To be verified`). As a secondary signal, the subagent should have reported `bytes_written ≥ ~4000`; a fully-populated brief is typically 8–25 KB. If all four research tables are empty placeholders, or if `bytes_written` is missing or far below 4 KB, re-run the subagent before mapping.

Do **not** rely on the subagent's spoken response to populate `01-context/`. Its 3–5 line summary is for orientation only; the full structured content lives in the file.

---

## Step 2 — Fill context templates

1. Read templates from [`02-templates/context/`](../../../02-templates/context/):
   - `01-about-company.md`, `02-products.md`, `03-product-vision.md`, `04-competition.md`
   - `05-glossary.md` if the brief includes glossary rows with content
2. Map the research brief into each file — **preserve section structure and headings** from the templates.
3. **Frontmatter** on every file written:
   - `title`, `document`, `last_updated` (today), `confidence` (from brief `section_confidence` for that file's section), `last_verified` (today)
   - `company` / `website` — on `01-about-company.md` only
   - `source_notes` — `Generated by /start from public web research on [date]. Sources: [URLs]. Review and correct before sharing externally.`
4. **Evidence rules:**
   - Populate **Source** columns from the brief (`Primary` / `Secondary` / `Inference` / `To be verified`).
   - Use **`To be verified`** for missing cells — never invent metrics, win/loss, or pricing.
   - Remove `[placeholder]` brackets when filled; keep all section headings even if thin.
5. Keep every **Implications for PRDs** block at the end of each template file.

---

## Step 3 — Write `01-context/` (auto-overwrite)

Overwrite in place (no backup step):

- `01-context/01-about-company.md`
- `01-context/02-products.md`
- `01-context/03-product-vision.md`
- `01-context/04-competition.md`
- `01-context/05-glossary.md` — only if brief has glossary content; otherwise skip this file

Do not modify `01-context/README.md`.

---

## Step 4 — Handoff

Tell the user:

1. **What was written** — list the four (or five) files in `01-context/`.
2. **Sources used** — URLs from the brief `sources` section.
3. **Gaps / To be verified** — bullets from `gaps` and any snapshot fields marked To be verified.
4. **Audit trail** — the raw research brief is preserved at `.cache/start/brief.md` (gitignored). If any `01-context/` field looks wrong, read the brief to see exactly what the subagent produced. The file is overwritten on the next `/start` run.
5. **Next steps** — e.g. run **`create-product-brief`** for a feature, or read [`02-templates/README.md`](../../../02-templates/README.md) for feature-hub orientation.
6. **Security** — per [`SECURITY.md`](../../../SECURITY.md): context is from public web only; do not add credentials, customer PII, or confidential internals without redaction.

---

## Mapping reference (brief → files)

| Brief section | Target file | Template sections |
|---------------|-------------|---------------------|
| `about_company` | `01-about-company.md` | Who we serve, Buyer vs end user, Go-to-market, Company snapshot, ICP, Compliance, Brand voice, Common user pains table |
| `products` | `02-products.md` | Surfaces and channels, Platform capabilities, Integrations, Core platform, Packaging tiers, Add-ons |
| `product_vision` | `03-product-vision.md` | Time horizon, North star, Strategic themes table, Product principles, Not optimizing for |
| `competition` | `04-competition.md` | Category map, Positioning, Win/loss, Status quo alternatives, Recent moves, Switching costs, Pricing benchmarks |
| `glossary` | `05-glossary.md` (optional) | Glossary table |

---

## Failure modes

| Situation | Action |
|-----------|--------|
| User provides only name or only URL | Ask for the missing field; do not proceed |
| Research returns empty / blocked | Do not write `01-context/`; explain and offer manual paste |
| Partial research | Write best-effort files with explicit `To be verified` markers |
| Subagent returns success but `.cache/start/brief.md` is missing | Treat as silent failure. Show the user the subagent's spoken response and offer to (a) re-run the subagent or (b) fall back to inline research. Do not invent content from the spoken summary. |
| `.cache/start/brief.md` is missing required top-level sections | Re-run the subagent with an explicit reminder to write the full brief; do not patch the gaps from memory. |

---

## Why a file-based hand-off

The skill writes the research brief to disk (`.cache/start/brief.md`) instead of having the subagent return it as text because Cursor's `Task` tool summarizes subagent responses before returning them to the orchestrator. A long, structured markdown brief gets compressed into a short "user-visible high-level summary," which silently degrades the hand-off: the orchestrator either invents the missing structure from the summary or has to redo the research inline.

Writing to disk makes the hand-off lossless: the subagent runs in isolation, drops the full brief at `.cache/start/brief.md`, and returns a short response. The orchestrator reads the file. No content is lost, and the brief stays on disk (gitignored) so you can audit exactly what the subagent produced if a `01-context/` field looks wrong.

`.cache/` is gitignored at the repo root. The brief is overwritten on each `/start` run.
