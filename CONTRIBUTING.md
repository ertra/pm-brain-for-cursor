# Contributing to PM Brain

## Cursor skills

- **Single procedure:** Each workflow lives in **`.cursor/skills/<name>/SKILL.md`**. Cursor loads those as skills.

- **Adding a new skill:** Create `.cursor/skills/<name>/SKILL.md` with frontmatter (`name`, `description`) and the procedure body. [`scripts/check_doc_skills.sh`](scripts/check_doc_skills.sh) validates that every skill folder has a `SKILL.md`.

- **Canonical prose:** Keep long-form workflow rules in **[`AGENTS.md`](AGENTS.md)** and **[`02-templates/README.md`](02-templates/README.md)** so the Cursor rules and skills stay aligned.

## Check script

From the repo root:

```bash
bash scripts/check_doc_skills.sh
```

Exit code `0` means every folder under `.cursor/skills/` has a `SKILL.md`. Non-zero prints warnings for drift you should fix before merging skill changes.
