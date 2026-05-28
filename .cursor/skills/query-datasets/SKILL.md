---
name: query-datasets
description: "Answer grounded yes/no questions about what exists in the 03-datasets/ example corpora (support_tickets, call_transcripts) using the local SQLite + FTS5 + vector hybrid index. Use when the user asks 'do/does [corpus] contain/mention/include/have requests for X?', 'any [corpus] about Y?', or similar factual queries over the datasets. Strictly one corpus per question."
---

# query-datasets

Answer questions about what's in `03-datasets/` using the local indexes at `03-datasets/_indexes/*.db`.

The repo ships a small, fictional sample dataset under `03-datasets/` plus
the self-contained tooling under `03-datasets/_tools/`. Use this skill for
demos, walkthroughs, and questions of the form *"do any support tickets /
calls in the sample mention X?"*. The skill is read-only.

## When this skill applies

- "Do support tickets mention conflicts with the Gmail extension?"
- "Did any prospect on a call ask for an audit log UI?"
- "Is there a ticket about timezone / DST handling?"
- Any factual lookup against `03-datasets/`.

## When it does NOT apply

- General PM workflow questions not tied to the datasets.
- Requests to modify / add / delete tickets. This skill is read-only.
- Questions spanning multiple corpora at once — **ask the user which one** instead.

## Preconditions

1. `03-datasets/_indexes/<corpus>.db` must exist and be complete. The file exists AND `SELECT value FROM meta WHERE key='build_complete_at'` returns non-empty.
2. Local Python env must be ready to load the same sentence-transformers model recorded in `meta.model` when using hybrid or vector mode.
3. Python venv at `.venv/` with dependencies installed (`pip install -r requirements.txt`).
4. If the indexes do not exist yet, build them first:
   ```bash
   source .venv/bin/activate
   python 03-datasets/_tools/build_index.py --corpus support_tickets \
     --provider sentence-transformers --model nomic-ai/nomic-embed-text-v1.5
   python 03-datasets/_tools/build_index.py --corpus call_transcripts \
     --provider sentence-transformers --model nomic-ai/nomic-embed-text-v1.5
   ```
   First run downloads `nomic-ai/nomic-embed-text-v1.5` from Hugging Face (~500 MB).

If any of these fail, tell the user what's missing and how to fix it — don't invent results.

## Checklist

Do these steps in order. Create TodoWrite items for them when the question is non-trivial.

1. **Identify the single target corpus** from the user's phrasing. Signals:
   - "support tickets" / "Zendesk" / "help desk" / "customer support" / "ticket #NNN" → `support_tickets`
   - "calls" / "recordings" / "transcripts" / "what did the prospect say" → `call_transcripts`

   If the user says "all of them", "across the data", "tickets" (bare), or anything ambiguous, **STOP and ask**:
   > "Which corpus should I check? support_tickets (10 customer support tickets) or call_transcripts (10 call recordings)?"

   Do not guess, do not query multiple corpora at once, do not silently pick a default.

2. **Verify the index exists and is complete.** Run:
   ```bash
   sqlite3 03-datasets/_indexes/<corpus>.db \
     "SELECT value FROM meta WHERE key IN ('build_complete_at','record_count','parent_count','model','provider');"
   ```
   If the file is missing or `build_complete_at` is empty, point at `03-datasets/README.md` (quick start) or the build commands above. Don't try to build for them without asking.

3. **Run the query**:
   ```bash
   source .venv/bin/activate
   python 03-datasets/_tools/query.py --corpus <corpus> --k 20 "<question>"
   ```
   - **Call date bounds (optional):** `--call-date-from YYYY-MM-DD` and `--call-date-to YYYY-MM-DD` filter hits by recording `call_date` after retrieval. Response includes `"filters"` when set.
   - **Call customer-voice incidence:** `python 03-datasets/_tools/call_incidence.py` — same args as `query.py` for search, default `--mode keyword`, then annotates each parent with `customer_voice_any_excerpt` (PROSPECT/EXTERNAL spoke in a top excerpt) plus an `incidence` summary. Pass `--no-prospect-enrich` to skip the customer-voice reload.
   - **Support tickets incidence:** `python 03-datasets/_tools/support_incidence.py` — same retrieval as `query.py`, default `--mode keyword`, then derives tag-based flags (`is_internal_triage`, `business_impact` P1..P4, `is_followup`, `is_feature_request`, `support_topics`, `support_resolution`, etc.) plus an `incidence_summary`. Optional `--created-from / --created-to` filters by `metadata.created_at`; `--exclude-internal-triage` drops CSR-only rows; `--no-incidence-enrich` returns raw `query.py` output.
   - Default mode is `hybrid` (vector + FTS5 BM25 + RRF). The example dataset is tiny (~10 records total), so RAM is never a concern — keep hybrid on.
   - For call_transcripts the CLI auto-enables `--group-by-parent`; results are recordings, each with up to 3 `excerpts[]`. `support_tickets` has one chunk per ticket (no chunking), so grouping is a no-op.
   - If the index has topics, every result carries `metadata.topic_id` + `metadata.topic_label`.

4. **Parse the JSON output**. Fields depend on whether results are grouped:
   - **Chunk-level** (support_tickets, or call_transcripts with `--no-group`):
     `id`, `parent_id`, `score` (RRF), `vector_score`, `bm25_score`,
     `in_vector_topK`, `in_fts_topK`, `strong`, `title`, `text`, `metadata`, `source_path`.
   - **Grouped** (default for call_transcripts): `id` equals `parent_id` (e.g. `call:5392477`),
     plus `title`, `metadata`, `source_path`, and `excerpts[]` (up to 3 chunks, each
     with its own `id`, `text`, `score`, `vector_score`, `bm25_score`). The
     top-level `score` / `vector_score` / `bm25_score` / `strong` reflect the
     **best chunk** within the recording; there is no top-level `text` — quote
     from `excerpts[].text`.
   - `parent_id` shape: `call:<recording_id>` for calls, `support:<ticket_id>` for tickets.
     Strip the `call:` / `support:` prefix when rendering human-facing citations
     (e.g. "recording 5392477", "ticket #928173").

5. **Read the raw source files** for the top hits to quote verbatim.
   - support_tickets: `source_path` is `meta.json`; sibling `body.md` has the ticket text.
   - call_transcripts: `source_path` is `transcript.json`; the `excerpts[]` already contain rendered chunks with `[Speaker, ROLE @ mm:ss]` headers — usually sufficient for quoting.

6. **Decide for each candidate**: "Does this record literally contain what the user asked about?" Drop records that are only loosely related.

7. **Compose the answer** in this shape:

   **One-line verdict**:
   - `**Yes** — N tickets directly request an audit log UI.`
   - call_transcripts: `**Yes** — N calls discuss audit log UI; in M of them the request comes from a PROSPECT.`
   - `**No strong matches.**` if all scores are below the threshold or no hit actually contains the subject.

   **Bullet list** (up to all 5 if relevant) in corpus-appropriate citation format:
   - support_tickets: `` `#TICKET_ID` — Subject (status, partition YYYYMM) — "short direct quote"``
   - call_transcripts: `` `recording 5392477` — "Discovery call" (account_name, 2026-02-05, ~30 min) — at **14:22** PROSPECT said: "…"``

   **Related-but-weaker** section if useful: bullet list of near-misses, clearly labeled.

   **Coverage footer**: one italic line with actual numbers from the JSON response, e.g.:
   *Searched 10 support_tickets via nomic-ai/nomic-embed-text-v1.5 (hybrid: vector + FTS5 BM25); top-20 retrieved, 2 strong, 8 weak.*

   For call_transcripts: *Searched 10 recordings (10 utterance-chunks total); top-20 chunks grouped into 1–10 recordings.*

8. **Never invent quotes.** If the top-K record text doesn't actually contain the asked-about phrase, exclude it from the "direct matches" list. Transparency beats confident-sounding hallucination.

## Output style

- Markdown with bullet lists.
- Back-tick ticket IDs, recording IDs, and file paths.
- Use bold for speaker roles (e.g. **PROSPECT**, **USER**) when citing call_transcripts.
- Keep excerpts to one short sentence or phrase.
- Always name the corpus you searched in the verdict line.

## Example interaction

> User: Do any support tickets mention an audit log UI?

Steps the agent follows:
1. Corpus = `support_tickets` (explicit).
2. Check `03-datasets/_indexes/support_tickets.db` exists with `build_complete_at`.
3. Run `python 03-datasets/_tools/query.py --corpus support_tickets --k 20 "audit log UI"`.
4. Read top hits (`body.md` for each) for verbatim quoting.
5. Synthesize:

   **Yes** — 1 support ticket directly requests an audit log UI:
   - `#933215` — Feature request: audit log UI for admins (closed, partition 202602) — "We need a UI for admins to browse the audit log"

   *Searched 10 support_tickets via nomic-ai/nomic-embed-text-v1.5 (hybrid); top-20 retrieved, 1 strong, 9 weak.*

## Cross-corpus hints (for the bundled sample)

The sample dataset is designed so that several topics appear in **both**
corpora. If the user asks about one of these, the answer is more interesting
when you check both — but still ask the user to pick one corpus per query:

| Topic | Support ticket | Call recording |
|-------|----------------|----------------|
| Audit log UI | `#933215` | `5428901` (Umbrella renewal), `5424700` (Nimbus discovery) |
| DST sequence scheduling | `#935112` | `5421188` (Acme expansion) |
| Okta / SAML SSO | `#931004` | `5410033` (Initech onboarding), `5428901` (Umbrella) |
| Salesforce custom field sync | `#928420` | `5392477`, `5409122` (Globex deep dive) |
| API rate limit / bulk pull | `#938401` | `5409122` (Globex deep dive) |
| iOS mobile app crash | `#939287` | `5443210` (Initech QBR) |
| Email deliverability / DKIM | `#941023` | `5433100` (Helios competitive) |
| UTF-8 / CSV import | `#941877` | `5414550` (Quantum demo) |
| Manager role / permissions | `#943298` | `5424700` (Nimbus discovery) |

## Troubleshooting hints (for the user)

- "Index not found": run the build commands in the Preconditions section.
- "provider/model mismatch" from `query.py`: the local environment doesn't match the model/provider recorded in the index. Keep the sentence-transformers model aligned with `meta.model`; if needed, rebuild the index.
- "No topics in this index" from `--topic` / `--topic-search`: the example indexes are not built with a BERTopic layer by default (the dataset is too small to be useful). Skip topic queries here, or run `python 03-datasets/_tools/build_topics.py --corpus <corpus>` if you want to experiment.
- `BrokenPipeError` when piping `query.py | head`: the current `query.py` swallows this cleanly; if you still see the traceback you're running an older copy. Pipe into a file (`> out.json`) and read a slice with `python -m json.tool out.json | head -c 800`.
