#!/usr/bin/env bash
# Warn when a .cursor/skills/* folder is missing a SKILL.md file.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

status=0

if [[ ! -d .cursor/skills ]]; then
  echo "check_doc_skills: missing .cursor/skills" >&2
  exit 1
fi

while IFS= read -r -d '' skill_dir; do
  name="$(basename "$skill_dir")"
  if [[ ! -f "$skill_dir/SKILL.md" ]]; then
    echo "WARN: skill folder '${name}' has no SKILL.md" >&2
    status=1
  fi
done < <(find .cursor/skills -mindepth 1 -maxdepth 1 -type d -print0)

if [[ "$status" -eq 0 ]]; then
  echo "check_doc_skills: OK (every .cursor/skills/*/ has a SKILL.md)"
fi
exit "$status"
