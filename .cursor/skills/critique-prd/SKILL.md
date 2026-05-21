---
name: critique-prd
description: 'Rubric-score a PRD pack (02 + 03) against the 7-dimension PM Brain rubric and run a 4-persona panel review. Returns scores, panel critiques, the single weakest section, a concrete rewrite, and P0/P1 fix lists. Use when: PRD review, score my PRD, rubric review, panel review, rewrite weakest section, critique-prd.'
disable-model-invocation: true
version: 1.0
---

# PRD Critic (pm-brain)

Rubric-driven, panel-reviewed critique of the **PRD pack** — `02-product-requirements.md` + `03-success-metrics.md` — in a feature hub. Runs in an **isolated subagent context** so scoring is not hedged by the current conversation.

**Complements [`critique-agent`](../critique-agent/SKILL.md):** use `critique-prd` for rubric scores + 4-persona panel + weakest-section rewrite; use `critique-agent` for broad cross-doc red-team (brief + pack + pre-mortem). The braindump gate in [`PRODUCT-RULES.md`](../../../PRODUCT-RULES.md) does **not** apply — the doc already exists.

**Repo convention:** Feature hub paths — see [`02-templates/README.md`](../../../02-templates/README.md) (*Feature hub convention*).

## When to Use This Skill

- Before engineering or design review on a PRD pack
- You want a **numeric rubric verdict** (weighted 1–5) and hard-block callouts
- You want **four stakeholder voices** (eng, design, exec, end user) on the same doc
- You want **one concrete rewrite** of the weakest section, not a shopping list

## When NOT to Use

- No `02-product-requirements.md` yet — run [`create-prd`](../create-prd/SKILL.md) first
- You want cross-doc red-team across brief + PRD + metrics without rubric scoring — use [`critique-agent`](../critique-agent/SKILL.md)
- You want competitive landscape analysis — use [`competitive-landscape`](../competitive-landscape/SKILL.md)

## What You'll Need

**Critical inputs (collect in Step 0 if missing):**

- **PROJECT key** (`PROJECT-abcde`) **or** explicit path to `02-product-requirements.md`
- `02-product-requirements.md` must exist in the feature hub
- `03-success-metrics.md` strongly expected (Outcome metric dimension hard-blocks at 1 if missing)

**Optional:**

- `+include <filename>` — load an extra hub file into the critic (e.g. prior `critique-*.md`, `04-`, `05-`)
- Specific concerns to pass to the subagent ("challenge metering in §D")

## Step 0: Locate the PRD pack

1. Parse user input for **PROJECT key**, **file path**, and any **`+include <file>`** tokens.
2. Resolve feature hub: `projects/{PROJECT-KEY}-{slug}/`. List matches if ambiguous.
3. Confirm **`02-product-requirements.md`** exists. If only `01-product-brief.md` exists, tell the user to run `create-prd` first.
4. Note whether **`03-success-metrics.md`** and **`01-product-brief.md`** exist.
5. **Glob** the hub for all `*.md` files. Split into:
   - **Loaded pack:** `01-product-brief.md` (if present), `02-product-requirements.md`, `03-success-metrics.md`
   - **Listed not loaded:** every other `.md` in the hub (e.g. `04-`, `05-`, `critique-*.md`, notes) unless user passed `+include`
6. **Detect Persona D** from brief §B / PRD §A (primary user: AE, SDR, Sales Manager, RevOps, CSM). Default **AE** if unclear. One line to user: *"Panel end-user voice: [persona] — say if you want a different one."*
7. If hub has extra files not in the load set, ask once: *"I also see [list] in the hub — include any with `+include filename` or say 'proceed' to score the PRD pack only."* If user says proceed, continue without extras.

## Step 1: Spawn the prd-critic subagent

**Do not score or critique the PRD in the main context.** The critic exists so critique runs in an isolated window — inline critique defeats the pattern.

Spawn the **`prd-critic`** agent (defined in [`.cursor/agents/prd-critic.md`](../../agents/prd-critic.md)). Use the Cursor Task tool to spawn the subagent:

- **Cursor Task tool:** prefer `subagent_type: prd-critic`. If the environment does not register custom subagent types by name, fall back to a generic subagent type (e.g. `generalPurpose`) and start the prompt with: *"You are the prd-critic agent. Open `.cursor/agents/prd-critic.md` and follow it exactly."*
- Either way, the prompt must include the items below and the agent file owns the rest of the procedure.

Pass the spawned agent:

- Absolute paths to hub files in the **loaded pack** (`01-product-brief.md` if present, `02-product-requirements.md`, `03-success-metrics.md`)
- **Persona D** label detected in Step 0.6
- **extra_files:** paths from `+include` (if any) — empty list otherwise
- Instruction to return the full 6-section output **plus** the "What I read" preamble, verbatim

Example prompt shape:

> You are the prd-critic agent for pm-brain. Open `.cursor/agents/prd-critic.md` and follow it exactly.  
> Critique the PRD pack at `projects/PROJECT-1693-skills-for-ai-platform/`.  
> Load: `01-product-brief.md`, `02-product-requirements.md`, `03-success-metrics.md`.  
> Persona D: AE.  
> Extra files: [none | list paths].  
> Read `01-context/` and `02-templates/product/02,03` as specified by the agent file. Do not edit any file. Return the "What I read" preamble + the full 6-section output.

## Step 2: Save output, then render verbatim

1. Save the subagent's output to the feature hub **by default** — do not ask first.
2. Filename:
   - Default: `projects/{PROJECT-KEY}-{slug}/critique-prd-{YYYY-MM-DD}.md`
   - If that file already exists, do **not** overwrite it. Use `critique-prd-{YYYY-MM-DD}-{HHMM}.md` instead.
3. Write YAML frontmatter followed by the subagent output body:

   ```yaml
   ---
   title: PRD Critique
   jira: "PROJECT-#####"
   date: YYYY-MM-DD
   mode: prd
   rubric_total: "X.X / 5"
   hard_blocks: "[list or none]"
   reviewer: prd-critic (pm-brain)
   ---
   ```

   Parse `rubric_total` and `hard_blocks` from the subagent output when possible. If parsing is ambiguous, use `"unknown"` rather than inventing.
4. Display the saved file path.
5. Display the subagent's output **verbatim** — no summary, no "looks good," no softening.
6. Do **not** add your own rubric scores or panel commentary on top.

Do **not** use `01-`–`05-` prefixes for critique filenames.

## Step 3: Offer next steps

After the verbatim output, append:

> **Saved to:** `projects/{PROJECT-KEY}-{slug}/critique-prd-{YYYY-MM-DD}[{-HHMM}].md`
>
> **Next steps:** Address P0 items, paste the proposed rewrite into the weakest section (or ask the PM to revise), then re-run `/critique-prd` or `/critique-agent` before stakeholder review.

## Principles

- **Isolated critique** — spawning the subagent is mandatory; inline critique defeats the pattern.
- **Saved by default** — every run creates a `critique-prd-*.md` review artifact in the feature hub before responding.
- **PRD pack only by default** — extras require explicit `+include` so prior critiques do not anchor scoring.
- **Evidence discipline** — the critic scores low when the pack has `Evidence: TBD` or `[PLACEHOLDER]` without owners; you do not paper over that in Step 2.
- **Complement, don't duplicate** — point to `critique-agent` when the user needs pre-mortem or cross-doc passes, not another rubric run.

## Pre-ship checklist (for this skill's run)

- Subagent was spawned (not inlined critique in parent context)
- Critique was saved to `critique-prd-{YYYY-MM-DD}.md` or a non-overwriting timestamped variant
- Output includes rubric table, 4 panel voices, one weakest section, one rewrite, P0 and P1 lists
- Persona D was stated in "What I read"
- Hub extras were listed if present; only `+include` files were loaded beyond the pack
