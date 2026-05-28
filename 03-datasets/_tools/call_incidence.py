#!/usr/bin/env python3
"""Call-transcripts retrieval helper: prospect/customer voice flags + optional date filters.

Runs the same retrieval as query.py, then (for call_transcripts) reloads full
chunk text from the index so speaker-role detection is not truncated at 500
chars. Emits JSON with per-excerpt and per-recording incidence fields.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from _tools.query import INDEXES_DIR, run_query  # noqa: E402

# Utterance lines from UtteranceWindowChunker: `[Name, ROLE @ mm:ss]`,
# `[Name | Org, ROLE @ mm:ss]`, or `[Name, ROLE @ hh:mm:ss]` for very long calls.
_ROLE_IN_BRACKET_RE = re.compile(
    r"\[[^\]]*?,\s*(USER|PROSPECT|EXTERNAL|GUEST|UNKNOWN|PARTICIPANT)\s+@\s*\d+:\d+(?::\d+)?\]"
)

_CUSTOMER_ROLES = frozenset({"PROSPECT", "EXTERNAL"})


def roles_in_chunk_text(text: str) -> set[str]:
    """Return utterance roles present in chunk text (from bracket headers)."""
    return set(_ROLE_IN_BRACKET_RE.findall(text or ""))


def chunk_has_customer_voice(text: str) -> bool:
    return bool(roles_in_chunk_text(text) & _CUSTOMER_ROLES)


def _fetch_texts_by_id(
    conn: sqlite3.Connection,
    chunk_ids: list[str],
) -> dict[str, str]:
    if not chunk_ids:
        return {}
    placeholders = ",".join(["?"] * len(chunk_ids))
    rows = conn.execute(
        f"SELECT id, text FROM records WHERE id IN ({placeholders})",
        chunk_ids,
    ).fetchall()
    return {str(r[0]): (r[1] or "") for r in rows}


def enrich_prospect_voice(
    payload: dict[str, Any],
    *,
    corpus: str,
) -> dict[str, Any]:
    """Add customer_voice fields using full chunk text from the index."""
    if corpus != "call_transcripts":
        payload["incidence_note"] = "prospect_voice only applies to call_transcripts"
        return payload

    results = payload.get("results") or []
    all_chunk_ids: list[str] = []
    for rec in results:
        for ex in rec.get("excerpts") or []:
            cid = ex.get("id")
            if cid:
                all_chunk_ids.append(str(cid))

    db_path = INDEXES_DIR / f"{corpus}.db"
    if not db_path.is_file():
        payload["incidence_error"] = f"index not found: {db_path}"
        return payload

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        texts = _fetch_texts_by_id(conn, all_chunk_ids)
    finally:
        conn.close()

    with_customer = 0
    for rec in results:
        excerpt_flags: list[dict[str, Any]] = []
        voice_ids: list[str] = []
        for ex in rec.get("excerpts") or []:
            cid = str(ex.get("id") or "")
            full = texts.get(cid, ex.get("text") or "")
            roles = sorted(roles_in_chunk_text(full))
            cv = chunk_has_customer_voice(full)
            excerpt_flags.append({
                "chunk_id": cid,
                "roles_in_chunk": roles,
                "customer_voice": cv,
            })
            if cv:
                voice_ids.append(cid)
        rec["excerpt_customer_voice"] = excerpt_flags
        rec["customer_voice_any_excerpt"] = len(voice_ids) > 0
        rec["customer_voice_excerpt_ids"] = voice_ids
        if rec["customer_voice_any_excerpt"]:
            with_customer += 1

    n = len(results)
    payload["incidence"] = {
        "recordings_returned": n,
        "recordings_with_customer_voice_in_top_excerpts": with_customer,
    }
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Call-transcripts keyword/hybrid search with customer-voice incidence flags.",
    )
    ap.add_argument("--corpus", default="call_transcripts",
                    help="Corpus name (default: call_transcripts).")
    ap.add_argument("--k", type=int, default=20, help="Top-K parents or chunks.")
    ap.add_argument("--mode", choices=["hybrid", "vector", "keyword"], default="keyword",
                    help="Retrieval mode (default keyword for large kaia index).")
    ap.add_argument("--min-score", type=float, default=None,
                    help="Override default_min_score for hybrid/vector.")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--group-by-parent", dest="group", action="store_const", const=True)
    group.add_argument("--no-group", dest="group", action="store_const", const=False)
    ap.set_defaults(group=None)
    ap.add_argument("--provider", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--topic", type=int, default=None)
    ap.add_argument(
        "--call-date-from",
        default=None,
        metavar="YYYY-MM-DD",
        help="Forwarded to query.run_query: filter by recording call_date.",
    )
    ap.add_argument(
        "--call-date-to",
        default=None,
        metavar="YYYY-MM-DD",
        help="Forwarded to query.run_query: filter by recording call_date.",
    )
    ap.add_argument(
        "--no-prospect-enrich",
        action="store_true",
        help="Skip customer-voice reload (raw query.py output only).",
    )
    ap.add_argument("question", nargs="+", help="Search question / keywords.")
    args = ap.parse_args()

    question = " ".join(args.question)
    try:
        out = run_query(
            corpus=args.corpus,
            question=question,
            k=args.k,
            mode=args.mode,
            min_score=args.min_score,
            group_by_parent=args.group,
            provider=args.provider,
            model=args.model,
            topic=args.topic,
            call_date_from=args.call_date_from,
            call_date_to=args.call_date_to,
        )
    except (FileNotFoundError, RuntimeError) as err:
        print(json.dumps({"error": str(err)}, ensure_ascii=False))
        return 2

    if not args.no_prospect_enrich:
        out = enrich_prospect_voice(out, corpus=args.corpus)

    try:
        json.dump(out, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    except BrokenPipeError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
