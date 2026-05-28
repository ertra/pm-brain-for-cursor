#!/usr/bin/env python3
"""Hybrid retrieval CLI over one corpus `.db` (vector + FTS5 BM25 + RRF)."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from _tools.embedders import make_embedder  # noqa: E402

log = logging.getLogger("query")

# Paths resolve relative to this file, so the kit works wherever it is dropped.
INDEXES_DIR = _HERE.parent / "_indexes"

RRF_K = 60  # standard RRF constant

# Heuristic candidate-pool widening when a call_transcripts call_date filter is active.
# Most candidates are typically outside any narrow date window, so we pull a
# much larger pre-filter slice to keep effective recall ~k. Tune if recall
# becomes poor on rare phrases.
_DATE_FILTER_K_MULTIPLIER = 40
_DATE_FILTER_K_FLOOR = 800

# FTS5 reserved characters. We strip the ones that would change query semantics.
_FTS5_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*")


def build_match_string(question: str) -> str:
    """Turn a natural-language question into a safe FTS5 MATCH string.

    Tokenizes on word boundaries, quotes each token (so reserved chars/operators
    are inert), joins with OR. Empty-safe (returns "" which caller treats as
    "no FTS match").
    """
    tokens = [t.lower() for t in _FTS5_TOKEN_RE.findall(question) if len(t) > 1]
    if not tokens:
        return ""
    return " OR ".join(f'"{t.replace(chr(34), "")}"' for t in tokens)


@dataclass
class Hit:
    rowid: int
    vector_score: float | None = None
    bm25_score: float | None = None
    vector_rank: int | None = None
    fts_rank: int | None = None
    rrf_score: float = 0.0

    @property
    def in_vector_topK(self) -> bool:
        return self.vector_rank is not None

    @property
    def in_fts_topK(self) -> bool:
        return self.fts_rank is not None


def _load_meta(conn: sqlite3.Connection) -> dict[str, str]:
    return {k: v for k, v in conn.execute("SELECT key, value FROM meta")}


def _has_topics(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='topics'"
    ).fetchone()
    return row is not None


def _topic_rowids(conn: sqlite3.Connection, topic_id: int) -> set[int]:
    rows = conn.execute(
        "SELECT r.rowid FROM records r "
        "JOIN record_topics rt ON rt.record_id = r.id "
        "WHERE rt.topic_id = ?",
        (topic_id,),
    ).fetchall()
    return {int(r[0]) for r in rows}


def _topic_label_for_rowids(
    conn: sqlite3.Connection, rowids: list[int]
) -> dict[int, tuple[int | None, str | None]]:
    if not rowids or not _has_topics(conn):
        return {}
    placeholders = ",".join(["?"] * len(rowids))
    rows = conn.execute(
        f"SELECT r.rowid, rt.topic_id, t.label "
        f"FROM records r "
        f"LEFT JOIN record_topics rt ON rt.record_id = r.id "
        f"LEFT JOIN topics t ON t.topic_id = rt.topic_id "
        f"WHERE r.rowid IN ({placeholders})",
        rowids,
    ).fetchall()
    return {
        int(r[0]): (int(r[1]) if r[1] is not None else None,
                    r[2] if r[2] is not None else None)
        for r in rows
    }


def _load_all_vectors(conn: sqlite3.Connection, dim: int) -> tuple[np.ndarray, list[int]]:
    rows = conn.execute("SELECT rowid, embedding FROM records ORDER BY rowid").fetchall()
    if not rows:
        return np.zeros((0, dim), dtype=np.float32), []
    ids = [r[0] for r in rows]
    mat = np.empty((len(rows), dim), dtype=np.float32)
    for i, (_rowid, blob) in enumerate(rows):
        arr = np.frombuffer(blob, dtype=np.float32, count=dim)
        mat[i] = arr
    return mat, ids


def _vector_top(
    vectors: np.ndarray,
    rowids: list[int],
    q: np.ndarray,
    k: int,
    *,
    allowed_rowids: set[int] | None = None,
) -> list[tuple[int, float]]:
    if vectors.shape[0] == 0:
        return []
    scores = vectors @ q
    if allowed_rowids is not None:
        mask = np.fromiter(
            (rid in allowed_rowids for rid in rowids),
            count=len(rowids),
            dtype=bool,
        )
        if not mask.any():
            return []
        idx_allowed = np.nonzero(mask)[0]
        scores_allowed = scores[idx_allowed]
        k_eff = min(k, scores_allowed.shape[0])
        top = idx_allowed[np.argpartition(-scores_allowed, k_eff - 1)[:k_eff]]
        top = top[np.argsort(-scores[top])]
        return [(rowids[i], float(scores[i])) for i in top]
    k = min(k, scores.shape[0])
    top_idx = np.argpartition(-scores, k - 1)[:k]
    top_idx = top_idx[np.argsort(-scores[top_idx])]
    return [(rowids[i], float(scores[i])) for i in top_idx]


def _fts_top(
    conn: sqlite3.Connection,
    match_str: str,
    k: int,
    *,
    allowed_rowids: set[int] | None = None,
) -> list[tuple[int, float]]:
    if not match_str:
        return []
    try:
        rows = conn.execute(
            "SELECT rowid, bm25(records_fts) AS b FROM records_fts "
            "WHERE records_fts MATCH ? ORDER BY b LIMIT ?",
            (match_str, k if allowed_rowids is None else k * 5),
        ).fetchall()
    except sqlite3.OperationalError as err:
        log.warning("FTS5 query failed (%s); match_str=%r", err, match_str)
        return []
    out = [(int(r[0]), float(r[1])) for r in rows]
    if allowed_rowids is not None:
        out = [(rid, b) for (rid, b) in out if rid in allowed_rowids]
        out = out[:k]
    return out


def _rrf_merge(
    vector: list[tuple[int, float]],
    fts: list[tuple[int, float]],
) -> dict[int, Hit]:
    hits: dict[int, Hit] = {}
    for rank, (rid, score) in enumerate(vector):
        hits.setdefault(rid, Hit(rowid=rid)).vector_score = score
        hits[rid].vector_rank = rank
        hits[rid].rrf_score += 1.0 / (RRF_K + rank + 1)
    for rank, (rid, bm25) in enumerate(fts):
        hits.setdefault(rid, Hit(rowid=rid)).bm25_score = bm25
        hits[rid].fts_rank = rank
        hits[rid].rrf_score += 1.0 / (RRF_K + rank + 1)
    return hits


def _parse_iso_date_arg(s: str | None) -> date | None:
    """Parse YYYY-MM-DD from CLI / kwargs; None if s is empty."""
    if not s or not str(s).strip():
        return None
    raw = str(s).strip()
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as err:
        raise RuntimeError(f"invalid date {raw!r}; expected YYYY-MM-DD") from err


def _metadata_date_in_range(
    md: dict[str, Any],
    *,
    field: str,
    d_from: date | None,
    d_to: date | None,
) -> bool:
    """True if md[field] (parsed as YYYY-MM-DD) is within [d_from, d_to] inclusive.

    Unknown / unparseable dates fail closed when at least one bound is set so the
    filter never silently keeps rows whose date we can't verify.
    """
    if d_from is None and d_to is None:
        return True
    raw = md.get(field)
    if not raw:
        return False
    try:
        cd = datetime.strptime(str(raw)[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return False
    if d_from is not None and cd < d_from:
        return False
    if d_to is not None and cd > d_to:
        return False
    return True


def _metadata_call_date_in_range(
    md: dict[str, Any],
    d_from: date | None,
    d_to: date | None,
) -> bool:
    """Back-compat wrapper used by the call_transcripts call_date filter path."""
    return _metadata_date_in_range(md, field="call_date", d_from=d_from, d_to=d_to)


def _materialize(conn: sqlite3.Connection, rowids: list[int]) -> dict[int, dict[str, Any]]:
    if not rowids:
        return {}
    placeholders = ",".join(["?"] * len(rowids))
    cur = conn.execute(
        f"SELECT rowid, id, parent_id, title, text, metadata, source_path "
        f"FROM records WHERE rowid IN ({placeholders})",
        rowids,
    )
    out = {}
    for r in cur:
        out[int(r[0])] = {
            "id": r[1],
            "parent_id": r[2],
            "title": r[3],
            "text": r[4],
            "metadata": json.loads(r[5]) if r[5] else {},
            "source_path": r[6],
        }
    topic_labels = _topic_label_for_rowids(conn, rowids)
    for rowid, doc in out.items():
        tid, tlabel = topic_labels.get(rowid, (None, None))
        if tid is not None:
            doc["metadata"]["topic_id"] = tid
        if tlabel is not None:
            doc["metadata"]["topic_label"] = tlabel
    return out


def _group_by_parent(
    results: list[dict[str, Any]],
    *,
    excerpts_per_parent: int = 3,
) -> list[dict[str, Any]]:
    """Collapse chunk-level results to parent-level; keep top N chunks as excerpts."""
    by_parent: dict[str, dict[str, Any]] = {}
    for r in results:
        pid = r["parent_id"]
        if pid not in by_parent:
            by_parent[pid] = {
                "id": pid,
                "parent_id": pid,
                "score": r["score"],
                "vector_score": r["vector_score"],
                "bm25_score": r["bm25_score"],
                "in_vector_topK": r["in_vector_topK"],
                "in_fts_topK": r["in_fts_topK"],
                "title": r["title"],
                "metadata": r["metadata"],
                "source_path": r["source_path"],
                "excerpts": [],
            }
        parent = by_parent[pid]
        parent["score"] = max(parent["score"], r["score"])
        parent["in_vector_topK"] = parent["in_vector_topK"] or r["in_vector_topK"]
        parent["in_fts_topK"] = parent["in_fts_topK"] or r["in_fts_topK"]
        if len(parent["excerpts"]) < excerpts_per_parent:
            parent["excerpts"].append({
                "id": r["id"],
                "score": r["score"],
                "text": r["text"][:500],
                "chunk_metadata": {
                    k: v for k, v in r["metadata"].items()
                    if k.startswith("chunk_")
                },
            })
    return sorted(by_parent.values(), key=lambda x: -x["score"])


def run_query(
    *,
    corpus: str,
    question: str,
    k: int,
    mode: str,
    min_score: float | None,
    group_by_parent: bool | None,
    provider: str | None,
    model: str | None,
    topic: int | None = None,
    call_date_from: str | None = None,
    call_date_to: str | None = None,
) -> dict[str, Any]:
    if (call_date_from or call_date_to) and corpus != "call_transcripts":
        raise RuntimeError(
            "--call-date-from / --call-date-to are only supported for corpus 'call_transcripts' "
            f"(received corpus={corpus!r}); other corpora do not store metadata.call_date."
        )

    db_path = INDEXES_DIR / f"{corpus}.db"
    if not db_path.is_file():
        raise FileNotFoundError(f"Index not found: {db_path}. Run build_index.py --corpus {corpus}.")

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta = _load_meta(conn)

        if not meta.get("build_complete_at"):
            raise RuntimeError(
                f"Index at {db_path} is marked incomplete (no build_complete_at). "
                "Re-run build_index.py to finish it."
            )

        stored_provider = meta.get("provider", "")
        stored_model = meta.get("model", "")
        stored_dim = int(meta.get("dim", "0"))
        stored_chunker = meta.get("chunker", "noop")

        effective_provider = provider or stored_provider
        effective_model = model or stored_model

        if stored_provider != effective_provider or stored_model != effective_model:
            raise RuntimeError(
                f"Index built with provider={stored_provider} model={stored_model}, "
                f"but you passed provider={effective_provider} model={effective_model}. "
                "Either match them or rebuild the index."
            )

        default_min = float(meta.get("default_min_score", "0.35"))
        effective_min = min_score if min_score is not None else default_min

        allowed_rowids: set[int] | None = None
        if topic is not None:
            if not _has_topics(conn):
                raise RuntimeError(
                    "--topic passed but this index has no topics. "
                    "Run build_topics.py --corpus <corpus> first."
                )
            allowed_rowids = _topic_rowids(conn, topic)
            if not allowed_rowids:
                raise RuntimeError(f"no records found for topic_id={topic}")

        # Pure keyword mode: no question embedding and no full vector matrix load.
        # Hybrid/vector load all embeddings into RAM (fine for the sample dataset; large at production scale).
        if mode == "keyword":
            if not stored_dim:
                raise RuntimeError("keyword mode requires meta.dim in the index")
            t_embed = 0.0
            vectors = np.zeros((0, stored_dim), dtype=np.float32)
            rowids: list[int] = []
        else:
            embedder = make_embedder(effective_provider, effective_model, expected_dim=stored_dim or None)
            t0 = time.time()
            if hasattr(embedder, "embed_query"):
                q = embedder.embed_query(question)
            else:
                q = embedder.embed_one(question)
            if stored_dim and q.shape[0] != stored_dim:
                raise RuntimeError(
                    f"question embedding dim ({q.shape[0]}) != index dim ({stored_dim})"
                )
            t_embed = time.time() - t0

            vectors, rowids = _load_all_vectors(conn, stored_dim or q.shape[0])

        top_k_candidates = max(k * 5, 50)
        vec_hits = (
            _vector_top(vectors, rowids, q, top_k_candidates, allowed_rowids=allowed_rowids)
            if mode in ("hybrid", "vector") else []
        )
        fts_hits = (
            _fts_top(conn, build_match_string(question), top_k_candidates, allowed_rowids=allowed_rowids)
            if mode in ("hybrid", "keyword") else []
        )

        hits_map = _rrf_merge(vec_hits, fts_hits)
        hits = sorted(hits_map.values(), key=lambda h: -h.rrf_score)

        # If pure vector or pure keyword, rrf_score is from one source only — use
        # that score for ordering and preserve it as `score` transparently.
        if mode == "vector":
            hits = sorted(
                [Hit(rowid=rid, vector_score=s, vector_rank=r, rrf_score=s)
                 for r, (rid, s) in enumerate(vec_hits)],
                key=lambda h: -h.rrf_score,
            )
        elif mode == "keyword":
            # BM25: lower is better -> negate for display
            hits = sorted(
                [Hit(rowid=rid, bm25_score=s, fts_rank=r, rrf_score=-s)
                 for r, (rid, s) in enumerate(fts_hits)],
                key=lambda h: -h.rrf_score,
            )

        # Classify strong vs weak
        def is_strong(h: Hit) -> bool:
            if h.in_vector_topK and h.in_fts_topK:
                return True
            if h.vector_score is not None and h.vector_score >= effective_min:
                return True
            return False

        d_from = _parse_iso_date_arg(call_date_from)
        d_to = _parse_iso_date_arg(call_date_to)
        date_filter_active = d_from is not None or d_to is not None
        # Default candidate slice is small (k*3) since grouping/ranking happens
        # just below. When a date filter is active, widen via the constants
        # at the top of the module — without this, narrow ranges trivially
        # produce empty result sets even though matching records exist deeper.
        top_slice = max(k * 3, k)
        if date_filter_active:
            top_slice = min(
                len(hits),
                max(top_slice * _DATE_FILTER_K_MULTIPLIER, _DATE_FILTER_K_FLOOR),
            )
        top = hits[:top_slice]
        info = _materialize(conn, [h.rowid for h in top])

        results = []
        for h in top:
            doc = info.get(h.rowid)
            if not doc:
                continue
            results.append({
                "id": doc["id"],
                "parent_id": doc["parent_id"],
                "score": round(h.rrf_score, 6),
                "vector_score": None if h.vector_score is None else round(h.vector_score, 6),
                "bm25_score": None if h.bm25_score is None else round(h.bm25_score, 6),
                "in_vector_topK": h.in_vector_topK,
                "in_fts_topK": h.in_fts_topK,
                "title": doc["title"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "source_path": doc["source_path"],
                "strong": is_strong(h),
            })

        # Chunk-level date filter: applied before grouping, so a recording survives
        # only if at least one of its top chunks falls inside the requested window.
        candidates_pre_date = len(results)
        if date_filter_active:
            results = [
                r for r in results
                if _metadata_call_date_in_range(r["metadata"], d_from, d_to)
            ]
        candidates_post_date = len(results)

        grouped_flag = group_by_parent
        if grouped_flag is None:
            grouped_flag = stored_chunker != "noop"

        if grouped_flag:
            grouped = _group_by_parent(results)
            final = grouped[:k]
        else:
            final = results[:k]

        strong_count = sum(1 for r in final if r.get("strong") or r.get("in_vector_topK") and r.get("in_fts_topK"))
        weak_count = len(final) - strong_count

        out: dict[str, Any] = {
            "question": question,
            "corpus": corpus,
            "mode": mode,
            "provider": stored_provider,
            "model": stored_model,
            "dim": stored_dim,
            "chunker": stored_chunker,
            "total_indexed": int(meta.get("record_count", "0") or len(rowids)),
            "total_parents": int(meta.get("parent_count", "0") or 0),
            "min_score": effective_min,
            "grouped": bool(grouped_flag),
            "results": final,
            "strong_count": strong_count,
            "weak_count": weak_count,
            "timings": {
                "embed_seconds": round(t_embed, 3),
            },
        }
        if date_filter_active:
            out["filters"] = {
                "call_date_from": call_date_from,
                "call_date_to": call_date_to,
                "candidates_before_date_filter": candidates_pre_date,
                "candidates_after_date_filter": candidates_post_date,
            }
        return out
    finally:
        conn.close()


def run_topic_search(
    *,
    corpus: str,
    phrase: str,
    k: int,
    top_recordings_per_topic: int = 10,
) -> dict[str, Any]:
    """Search topics_fts for a phrase and return matched topics with reps + top recordings."""
    db_path = INDEXES_DIR / f"{corpus}.db"
    if not db_path.is_file():
        raise FileNotFoundError(f"Index not found: {db_path}")

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta = _load_meta(conn)
        if not _has_topics(conn):
            raise RuntimeError(
                "No topics in this index. Run build_topics.py first."
            )
        match_str = build_match_string(phrase)
        if not match_str:
            raise RuntimeError(f"could not parse --topic-search phrase: {phrase!r}")

        try:
            fts_rows = conn.execute(
                "SELECT rowid, bm25(topics_fts) AS b FROM topics_fts "
                "WHERE topics_fts MATCH ? ORDER BY b LIMIT ?",
                (match_str, k),
            ).fetchall()
        except sqlite3.OperationalError as err:
            raise RuntimeError(f"topics_fts query failed: {err}") from err

        topics_out: list[dict[str, Any]] = []
        for (tid, b) in fts_rows:
            tid_int = int(tid)
            trow = conn.execute(
                "SELECT label, keywords_json, description, size, representative_ids_json "
                "FROM topics WHERE topic_id = ?",
                (tid_int,),
            ).fetchone()
            if not trow:
                continue
            label, kw_json, desc, size, reps_json = trow
            keywords = json.loads(kw_json) if kw_json else []
            rep_ids: list[str] = json.loads(reps_json) if reps_json else []
            rep_excerpts: list[dict[str, Any]] = []
            if rep_ids:
                placeholders = ",".join(["?"] * len(rep_ids))
                rep_rows = conn.execute(
                    f"SELECT id, text, metadata FROM records WHERE id IN ({placeholders})",
                    rep_ids,
                ).fetchall()
                by_id = {r[0]: (r[1], r[2]) for r in rep_rows}
                for rid in rep_ids:
                    pair = by_id.get(rid)
                    if not pair:
                        continue
                    text, md_json = pair
                    rep_excerpts.append({
                        "id": rid,
                        "text": text,
                        "metadata": json.loads(md_json) if md_json else {},
                    })

            rec_rows = conn.execute(
                """
                SELECT rt.parent_id, rt.primary_share, rt.chunk_count,
                       (SELECT title FROM records WHERE parent_id = rt.parent_id LIMIT 1) AS title,
                       (SELECT metadata FROM records WHERE parent_id = rt.parent_id LIMIT 1) AS md_json
                FROM recording_topics rt
                WHERE rt.primary_topic_id = ?
                ORDER BY rt.chunk_count DESC
                LIMIT ?
                """,
                (tid_int, top_recordings_per_topic),
            ).fetchall()
            top_recordings: list[dict[str, Any]] = []
            for (parent_id, share, chunk_count, title, md_json) in rec_rows:
                md = {}
                try:
                    md = json.loads(md_json) if md_json else {}
                except (TypeError, ValueError):
                    md = {}
                top_recordings.append({
                    "parent_id": parent_id,
                    "title": title,
                    "primary_share": round(float(share), 4),
                    "chunk_count": int(chunk_count),
                    "account_name": md.get("account_name"),
                    "account_id": md.get("account_id"),
                    "call_date": md.get("call_date"),
                    "recording_id": md.get("recording_id"),
                })

            topics_out.append({
                "topic_id": tid_int,
                "label": label,
                "keywords": keywords,
                "description": desc,
                "size": int(size),
                "bm25_score": round(float(b), 4),
                "representative_excerpts": rep_excerpts,
                "top_recordings": top_recordings,
            })

        return {
            "corpus": corpus,
            "phrase": phrase,
            "topics": topics_out,
            "total_topics_indexed": int(
                conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
            ),
            "catalog_path": str(
                INDEXES_DIR / f"{corpus}_topics.md"
            ),
        }
    finally:
        conn.close()


def _emit_result_json(obj: Any) -> int:
    """Write JSON to stdout; return 0 even if the reader closed early (e.g. `head -c`)."""
    try:
        json.dump(obj, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    except BrokenPipeError:
        pass
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Hybrid retrieval over a corpus .db.")
    ap.add_argument("--corpus", required=True,
                    help="Corpus name (matches _indexes/<corpus>.db).")
    ap.add_argument("--k", type=int, default=20, help="Top-K results to return.")
    ap.add_argument("--mode", choices=["hybrid", "vector", "keyword"], default="hybrid",
                    help="Retrieval mode (default: hybrid).")
    ap.add_argument("--min-score", type=float, default=None,
                    help="Override the index's default_min_score (vector cosine threshold for 'strong').")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--group-by-parent", dest="group", action="store_const", const=True,
                       help="Force grouping by parent_id.")
    group.add_argument("--no-group", dest="group", action="store_const", const=False,
                       help="Force no grouping (chunk-level results).")
    ap.set_defaults(group=None)
    ap.add_argument("--provider", default=None,
                    help="Embedder provider (default: whatever the index was built with).")
    ap.add_argument("--model", default=None,
                    help="Embedding model (default: whatever the index was built with).")
    ap.add_argument("--topic", type=int, default=None,
                    help="Restrict hybrid retrieval to records in this topic_id.")
    ap.add_argument(
        "--call-date-from",
        default=None,
        metavar="YYYY-MM-DD",
        help="call_transcripts: after retrieval, keep only chunks whose recording call_date is on or after this day.",
    )
    ap.add_argument(
        "--call-date-to",
        default=None,
        metavar="YYYY-MM-DD",
        help="call_transcripts: after retrieval, keep only chunks whose recording call_date is on or before this day.",
    )
    ap.add_argument("--topic-search", default=None,
                    help="Search topics_fts for this phrase and return matched topics "
                         "with representative excerpts + top recordings.")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("question", nargs="*", help="Natural-language question.")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    if args.topic_search:
        try:
            out = run_topic_search(
                corpus=args.corpus,
                phrase=args.topic_search,
                k=args.k,
            )
        except (FileNotFoundError, RuntimeError) as err:
            print(json.dumps({"error": str(err)}, ensure_ascii=False))
            return 2
        return _emit_result_json(out)

    if not args.question:
        print(json.dumps({"error": "question is required unless --topic-search is used"}))
        return 2

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

    return _emit_result_json(out)


if __name__ == "__main__":
    sys.exit(main())
