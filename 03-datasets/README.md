# 03-datasets — Self-contained example dataset + tooling

A small, **fictional** sample dataset that mirrors the exact folder layout
the PM Brain pipeline expects, plus a copy of the Python tooling
(`_tools/`) so the whole thing works as a stand-alone kit.

Use it to:

- Eyeball the format before plugging in your own export.
- Run a smoke build / query end-to-end on a tiny corpus.
- Hand it to a teammate as a “what does the input look like?” reference.

> Nothing in this folder is real customer data. Names, accounts, ticket
> IDs, emails, and quotes are all invented for documentation purposes.

## Layout

```text
03-datasets/
  README.md
  _tools/                  # build + query pipeline (copy of pm-brain tooling)
    build_index.py         # CLI: flatten → chunk → embed → SQLite index
    query.py               # CLI: hybrid (vector + BM25 + RRF) search
    flatten.py             # per-corpus flatteners
    chunker.py             # noop + utterance-window chunker
    embedders.py           # sentence-transformers + (optional) Ollama
    call_incidence.py      # PROSPECT/EXTERNAL customer-voice flags
    support_incidence.py   # tag-based severity / triage flags
    build_topics.py        # optional BERTopic layer
    topics.py              # BERTopic helpers
    adf.py                 # Atlassian Document Format helper (unused here)
  support_tickets/
    <YYYYMM>/<ticket_id>/
      meta.json            # ticket metadata (Zendesk-shaped, UPPER_CASE keys)
      body.md              # human-readable ticket conversation
  call_transcripts/
    <account_id>/
      name.txt             # display name of the account
      <YYYYMM>/<recording_id>/
        recording.json     # call metadata (title, participants, duration, ...)
        transcript.json    # list of utterances (speaker + offset + text)
  _indexes/                # created on first build; one .db per corpus
```

The tooling in `_tools/` resolves paths relative to its own location, so
dropping the whole `03-datasets/` folder anywhere on your machine works
without code changes. Builds write into `03-datasets/_indexes/`.

## What's included

**10 support tickets** (`support_tickets/`):

| Partition | Ticket ID | Org | Topic |
|-----------|-----------|-----|-------|
| 202601 | 928173 | Acme | Gmail extension stops loading after Chrome update |
| 202601 | 928420 | Globex | Salesforce sync failing on custom fields |
| 202602 | 931004 | Umbrella | SSO / SAML login broken for new IdP |
| 202602 | 933215 | Initech | Feature request — audit log UI for admins |
| 202603 | 935112 | Acme | Sequences not sending on scheduled time |
| 202604 | 938401 | Globex | Partner integration hitting REST API rate limit |
| 202604 | 939287 | Initech | iOS app crashes on save when editing a sequence |
| 202605 | 941023 | Helios | Outbound emails going to spam after DMARC / DKIM change |
| 202605 | 941877 | Quantum | Bulk CSV import failing on European characters |
| 202606 | 943298 | Nimbus Health | Manager role cannot see reports for their direct team |

**10 call recordings** (`call_transcripts/`):

| Account | Month | Recording | Call type |
|---------|-------|-----------|-----------|
| 4400123 — Acme Corporation | 202602 | 5392477 | Discovery — prospect asks for CRM custom-field sync |
| 4400456 — Globex Industries | 202602 | 5398012 | Pricing / packaging discussion |
| 4400456 — Globex Industries | 202603 | 5409122 | Technical deep dive with Salesforce admin |
| 4400789 — Initech | 202603 | 5410033 | Onboarding kick-off |
| 4401501 — Quantum Logistics | 202603 | 5414550 | First demo (new prospect, logistics) |
| 4400123 — Acme Corporation | 202604 | 5421188 | Expansion — more seats + AI add-on |
| 4401822 — Nimbus Health | 202604 | 5424700 | Discovery — regulated industry, HIPAA |
| 4400999 — Umbrella SaaS | 202604 | 5428901 | Renewal at risk, churn signals |
| 4401204 — Helios Energy | 202605 | 5433100 | Competitive eval vs Salesloft |
| 4400789 — Initech | 202606 | 5443210 | Q2 business review |

Several topics appear in **both corpora** on purpose, so you can test that
the agent really finds cross-source evidence:

| Topic | Support ticket | Call recording |
|-------|----------------|----------------|
| Audit log UI | `#933215` | `5428901` (Umbrella), `5424700` (Nimbus) |
| DST scheduling bug | `#935112` | `5421188` (Acme expansion) |
| Okta / SAML SSO | `#931004` | `5410033` (Initech), `5428901` (Umbrella) |
| Salesforce custom field sync | `#928420` | `5392477`, `5409122` (Globex) |
| API rate limit / bulk pull | `#938401` | `5409122` (Globex deep dive) |
| iOS mobile app crash | `#939287` | `5443210` (Initech QBR) |
| Email deliverability / DKIM | `#941023` | `5433100` (Helios competitive) |
| UTF-8 / CSV import | `#941877` | `5414550` (Quantum demo) |
| Manager role / permissions | `#943298` | `5424700` (Nimbus discovery) |

## Quick start

From the **`pm-brain` repo root**, with a Python virtual env activated:

```bash
# 1. Install pipeline deps (sentence-transformers, torch, numpy, requests).
pip install -r requirements.txt

# 2. Build the two indexes (first run downloads the embedding model ~500 MB).
python 03-datasets/_tools/build_index.py \
  --corpus support_tickets \
  --provider sentence-transformers \
  --model nomic-ai/nomic-embed-text-v1.5

python 03-datasets/_tools/build_index.py \
  --corpus call_transcripts \
  --provider sentence-transformers \
  --model nomic-ai/nomic-embed-text-v1.5

# 3. Ask grounded questions.
python 03-datasets/_tools/query.py --corpus support_tickets \
  "gmail extension conflict after chrome update"

python 03-datasets/_tools/query.py --corpus call_transcripts \
  "prospect asks for crm custom field sync"
```

Indexes are written to `03-datasets/_indexes/<corpus>.db` — a single
SQLite file per corpus, self-contained and rsync-friendly.

## Using your own data instead

The flatteners in `_tools/flatten.py` are the only corpus-specific piece.
If your support export or call transcripts have a different shape, edit
the matching flattener (or add a new one to `FLATTENER_REGISTRY`) and run
the same `build_index.py` / `query.py` against your folders.

## What's not included

- `tests/` from the main repo (they reference paths inside `03-datasets/`).
- `ec2/` (GPU deployment kit; only needed at production scale — see
  `03-datasets/_tools/ec2/README.md` in the main repo).
- `cr_tickets/` (Jira feature-request corpus is out of scope for this
  example).
