"""BERTopic layer over an existing `<corpus>.db` hybrid index.

This module is provider-agnostic: it reads precomputed `records.embedding`
BLOBs from the SQLite index (built by `build_index.py`), fits a BERTopic
model, and writes topic assignments + metadata back into the same `.db`.

Public entrypoints:

* `load_embeddings_from_db(db_path)`
* `fit_bertopic(embeddings, texts, sbert_model, ...)`
* `write_topics(db_path, ids, texts, topics_arr, probs, model, params)`
* `aggregate_recording_topics(db_path)`
* `render_catalog_markdown(db_path, out_path)`
* `sample_topic_chunks(db_path, *, top_n_topics=5, per_topic=5, seed=42)`

LLM-based topic descriptions are intentionally deferred (`describe_topics`
is a no-op stub); `topics.description` is left `NULL` in v1.
"""

from __future__ import annotations

import json
import logging
import random
import re
import sqlite3
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

# Must stay in sync with the CountVectorizer token_pattern in fit_bertopic().
# Used by extract_speaker_stopwords() so that a name like "O'Brien" emits
# both the naive-cleaned form ("obrien") AND the sub-tokens the vectorizer
# will actually produce at fit time ("brien"). Without this, surnames
# containing apostrophes, hyphens, or periods leak through as topic
# keywords even though their "cleaned" form is in the stopword list.
_NAME_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z]+")

log = logging.getLogger(__name__)


# -- Schema (kept in sync with build_index.py SCHEMA_SQL) ---------------------


TOPIC_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS topics (
    topic_id                INTEGER PRIMARY KEY,
    label                   TEXT NOT NULL,
    keywords_json           TEXT NOT NULL,
    description             TEXT,
    size                    INTEGER NOT NULL,
    representative_ids_json TEXT,
    created_at              REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS record_topics (
    record_id   TEXT PRIMARY KEY REFERENCES records(id) ON DELETE CASCADE,
    topic_id    INTEGER NOT NULL REFERENCES topics(topic_id),
    probability REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS record_topics_topic ON record_topics(topic_id);

CREATE TABLE IF NOT EXISTS recording_topics (
    parent_id        TEXT PRIMARY KEY,
    primary_topic_id INTEGER NOT NULL REFERENCES topics(topic_id),
    primary_share    REAL NOT NULL,
    secondary_json   TEXT NOT NULL,
    chunk_count      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS recording_topics_primary ON recording_topics(primary_topic_id);

CREATE VIRTUAL TABLE IF NOT EXISTS topics_fts USING fts5(
    label, keywords_json, description,
    content='topics', content_rowid='topic_id',
    tokenize='porter unicode61 remove_diacritics 2'
);
"""


# -- Loading ------------------------------------------------------------------


def load_embeddings_from_db(
    db_path: Path,
) -> tuple[list[str], list[str], np.ndarray, list[str]]:
    """Return (ids, texts, embeddings, parent_ids) from an existing index.

    `embeddings` is a contiguous `(N, dim)` float32 matrix (L2-normalized
    at index time). Reads in rowid order so downstream code can rely on
    parallel-array semantics.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        dim_row = conn.execute(
            "SELECT value FROM meta WHERE key = 'dim'"
        ).fetchone()
        if not dim_row:
            raise RuntimeError(
                f"{db_path} has no meta.dim; did build_index.py finish?"
            )
        dim = int(dim_row[0])

        rows = conn.execute(
            "SELECT id, parent_id, text, embedding FROM records ORDER BY rowid"
        ).fetchall()
        if not rows:
            raise RuntimeError(f"{db_path} has no records")

        ids = [r[0] for r in rows]
        parent_ids = [r[1] for r in rows]
        texts = [r[2] for r in rows]
        mat = np.empty((len(rows), dim), dtype=np.float32)
        for i, r in enumerate(rows):
            mat[i] = np.frombuffer(r[3], dtype=np.float32, count=dim)
        return ids, texts, mat, parent_ids
    finally:
        conn.close()


def load_embeddings_no_text_from_db(
    db_path: Path,
) -> tuple[list[str], np.ndarray, list[str]]:
    """Return (ids, embeddings, parent_ids) without loading records.text.

    This mode is for memory-constrained BERTopic runs on very large corpora.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        dim_row = conn.execute(
            "SELECT value FROM meta WHERE key = 'dim'"
        ).fetchone()
        if not dim_row:
            raise RuntimeError(
                f"{db_path} has no meta.dim; did build_index.py finish?"
            )
        dim = int(dim_row[0])

        rows = conn.execute(
            "SELECT id, parent_id, embedding FROM records ORDER BY rowid"
        ).fetchall()
        if not rows:
            raise RuntimeError(f"{db_path} has no records")

        ids = [r[0] for r in rows]
        parent_ids = [r[1] for r in rows]
        mat = np.empty((len(rows), dim), dtype=np.float32)
        for i, r in enumerate(rows):
            mat[i] = np.frombuffer(r[2], dtype=np.float32, count=dim)
        return ids, mat, parent_ids
    finally:
        conn.close()


# -- Fitting ------------------------------------------------------------------


# Role tokens that `_render_window` injects as `[Name, ROLE @ mm:ss]` plus
# a few conversational fillers that otherwise dominate kaia topics. Add
# new per-corpus fillers here; users can also pass ad-hoc ones via
# `build_topics.py --stopword WORD` without editing this file.
_KAIA_META_STOPWORDS = frozenset({
    "prospect", "user", "unknown", "external", "internal",
    "yeah", "okay", "ok", "uh", "um", "umm", "hmm", "mm", "ah", "oh", "yep", "nope",
    "like", "know", "just", "really", "actually", "basically", "kind", "sort",
    "going", "got", "gonna", "wanna", "kinda", "stuff", "thing", "things",
    "right", "sure", "maybe", "mean", "guess", "think", "say", "said", "saying",
    "guys", "alright", "perfect", "cool", "exactly", "bit", "good",
    "new", "ve", "ll", "don", "doesn", "didn", "isn", "wasn",
    "want", "click", "clicks", "ahead", "scroll", "test",
    # Added after the first 500-recording smoke run: surfaced as top
    # cTF-IDF keywords but carry no topic signal on sales calls.
    "different", "quite", "suppose", "probably", "little", "looks",
    "today", "way",
})


def extract_speaker_stopwords(db_path: Path) -> list[str]:
    """Pull every alphabetic participant-name token from records.metadata.

    Scans `records.metadata.participants` for kaia-style `{name, role}`
    entries and returns all lowercase alphabetic tokens (length >= 2).
    Used by `fit_bertopic` to stop participant names from dominating the
    c-TF-IDF keyword lists (a kaia-specific artifact of rendering each
    utterance as `[Name, ROLE @ mm:ss] text`).

    For names containing apostrophes, hyphens, periods, or parentheses
    (e.g. `O'Brien`, `Van-Court`, `Hayden Usher (WTax)`), we emit BOTH
    the naive cleaned form (e.g. `obrien`) AND every sub-token the
    CountVectorizer will actually produce at fit time (e.g. `brien`).
    That is important because the vectorizer splits on punctuation, so
    without emitting sub-tokens a surname like `Brien` would bypass the
    stopword list and end up as a c-TF-IDF keyword.
    """
    tokens: set[str] = set()
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        for (md_json,) in conn.execute("SELECT metadata FROM records"):
            try:
                md = json.loads(md_json) if md_json else {}
            except (TypeError, ValueError):
                continue
            for p in (md.get("participants") or []):
                name = (p.get("name") or "") if isinstance(p, dict) else ""
                if not name:
                    continue
                for raw in name.split():
                    lower = raw.lower()
                    cleaned = "".join(c for c in lower if c.isalpha())
                    if len(cleaned) >= 2:
                        tokens.add(cleaned)
                    # Sub-tokens the vectorizer would actually produce.
                    for sub in _NAME_TOKEN_RE.findall(lower):
                        if len(sub) >= 2:
                            tokens.add(sub)
    finally:
        conn.close()
    return sorted(tokens)


def fit_bertopic(
    embeddings: np.ndarray,
    texts: list[str],
    *,
    min_topic_size: int = 10,
    nr_topics: str | int | None = "auto",
    sbert_model: Any = None,
    sample_fit: int | None = None,
    random_state: int = 42,
    extra_stopwords: list[str] | None = None,
) -> tuple[np.ndarray, np.ndarray, Any, dict[str, Any]]:
    """Fit BERTopic on precomputed embeddings and return topic assignments.

    Parameters
    ----------
    embeddings : (N, dim) float32 matrix (already L2-normalized).
    texts : len-N list of chunk texts.
    min_topic_size : HDBSCAN min_cluster_size.
    nr_topics : "auto" / int / None -> passed to BERTopic constructor.
    sbert_model : a SentenceTransformer (or None). Passing the model lets
        the fitted BERTopic embed new queries later via `.transform()` or
        `.find_topics()` without the caller having to pre-embed.
    sample_fit : if set and `< len(embeddings)`, fit on a random sample of
        that size then `.transform()` the rest in batches. No-op at smoke
        scale; future scale-up path.
    random_state : seed for UMAP and the sample_fit RNG.
    extra_stopwords : additional tokens to exclude from the c-TF-IDF
        vocabulary (merged with sklearn's English stopword list and a
        fixed kaia-specific filler set). Typically the output of
        `extract_speaker_stopwords()` on the same `.db`.

    Returns
    -------
    (topics_arr, probs, model, params_dict)
    """
    from bertopic import BERTopic
    from bertopic.vectorizers import ClassTfidfTransformer
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import (
        ENGLISH_STOP_WORDS,
        CountVectorizer,
    )
    from umap import UMAP

    n = embeddings.shape[0]
    text_n = len(texts)
    if text_n != n:
        if not sample_fit:
            raise ValueError(
                f"embeddings/texts length mismatch: {n} vs {text_n}; "
                "pass aligned texts or enable sample_fit."
            )
        if text_n != int(sample_fit):
            raise ValueError(
                f"when using sampled texts, len(texts) must equal sample_fit; "
                f"got len(texts)={text_n} sample_fit={sample_fit}"
            )

    nr_topics_arg: Any = nr_topics
    if isinstance(nr_topics, str) and nr_topics != "auto":
        raise ValueError("nr_topics must be 'auto', an int, or None")

    umap_model = UMAP(
        n_neighbors=15,
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        random_state=random_state,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=max(2, int(min_topic_size)),
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )
    ctfidf_model = ClassTfidfTransformer(reduce_frequent_words=True)

    stopwords: set[str] = set(ENGLISH_STOP_WORDS) | set(_KAIA_META_STOPWORDS)
    if extra_stopwords:
        stopwords.update(w.lower() for w in extra_stopwords)
    # Alphabetic tokens only (drops timestamps like "03" / "2024-06-05"
    # that leaked in from `[@ mm:ss]` brackets) with a length floor.
    vectorizer_model = CountVectorizer(
        stop_words=sorted(stopwords),
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b",
        ngram_range=(1, 2),
        min_df=2,
    )

    topic_model = BERTopic(
        embedding_model=sbert_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        ctfidf_model=ctfidf_model,
        vectorizer_model=vectorizer_model,
        nr_topics=nr_topics_arg,
        calculate_probabilities=False,
        verbose=True,
    )

    if sample_fit and sample_fit < n:
        log.info(
            "sample-fit: fitting on %d random chunks out of %d, then transforming the rest",
            sample_fit, n,
        )
        if len(texts) == n:
            rng = np.random.default_rng(random_state)
            sample_idx = rng.choice(n, size=sample_fit, replace=False)
            sample_idx.sort()
            sample_embs = embeddings[sample_idx]
            sample_texts = [texts[i] for i in sample_idx]
        else:
            # Low-memory mode: caller provided exactly `sample_fit` texts.
            # Fit on the first `sample_fit` embeddings to avoid materializing full text.
            sample_embs = embeddings[:sample_fit]
            sample_texts = texts
        topic_model.fit(sample_texts, sample_embs)

        topics_arr = np.full(n, -1, dtype=np.int64)
        probs = np.zeros(n, dtype=np.float32)
        BATCH = 10_000
        for start in range(0, n, BATCH):
            end = min(n, start + BATCH)
            batch_size = end - start
            transform_texts = texts[start:end] if len(texts) == n else [""] * batch_size
            t_batch, p_batch = topic_model.transform(
                transform_texts, embeddings=embeddings[start:end]
            )
            topics_arr[start:end] = np.asarray(t_batch, dtype=np.int64)
            if p_batch is not None:
                probs[start:end] = np.asarray(p_batch, dtype=np.float32).reshape(-1)
    else:
        topics_list, probs_list = topic_model.fit_transform(texts, embeddings)
        topics_arr = np.asarray(topics_list, dtype=np.int64)
        probs = (
            np.asarray(probs_list, dtype=np.float32).reshape(-1)
            if probs_list is not None
            else np.zeros(n, dtype=np.float32)
        )

    params = {
        "min_topic_size": int(min_topic_size),
        "nr_topics": nr_topics_arg,
        "umap_n_neighbors": 15,
        "umap_n_components": 5,
        "random_state": random_state,
        "sample_fit": sample_fit,
        "extra_stopwords_count": len(extra_stopwords) if extra_stopwords else 0,
        "vectorizer_ngram_range": [1, 2],
        "vectorizer_min_df": 2,
    }
    return topics_arr, probs, topic_model, params


# -- Writing ------------------------------------------------------------------


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def _ensure_topic_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(TOPIC_SCHEMA_SQL)


def _drop_topic_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS topics_fts;
        DROP TABLE IF EXISTS record_topics;
        DROP TABLE IF EXISTS recording_topics;
        DROP TABLE IF EXISTS topics;
        """
    )


def _safe_label(topic_id: int, keywords: list[str]) -> str:
    if topic_id == -1:
        return "(outliers)"
    top = [w for w in keywords[:4] if w]
    return ", ".join(top) if top else f"topic {topic_id}"


def _build_representative_ids(
    model: Any,
    texts: list[str] | None,
    ids: list[str],
    topics_arr: np.ndarray,
) -> dict[int, list[str]]:
    """Map BERTopic's representative doc strings back to the original chunk IDs.

    BERTopic.get_representative_docs() returns strings; we rebuild a
    text->id lookup (first-occurrence wins) to find the chunk IDs.
    """
    text_to_ids: dict[str, list[str]] = defaultdict(list)
    if texts:
        for i, t in enumerate(texts):
            text_to_ids[t].append(ids[i])

    out: dict[int, list[str]] = {}
    try:
        reps_by_topic = model.get_representative_docs()
    except Exception as err:  # noqa: BLE001
        log.warning("get_representative_docs() failed: %s; falling back to first-in-topic", err)
        reps_by_topic = {}

    topic_to_idx: dict[int, list[int]] = defaultdict(list)
    for idx, t in enumerate(topics_arr):
        topic_to_idx[int(t)].append(idx)

    if texts:
        for topic_id, reps in reps_by_topic.items():
            seen: set[str] = set()
            rep_ids: list[str] = []
            for text in reps:
                candidates = text_to_ids.get(text, [])
                for cand in candidates:
                    if cand in seen:
                        continue
                    seen.add(cand)
                    rep_ids.append(cand)
                    break
                if len(rep_ids) >= 3:
                    break
            out[int(topic_id)] = rep_ids

    for topic_id, idxs in topic_to_idx.items():
        if topic_id in out and out[topic_id]:
            continue
        fallback = [ids[i] for i in idxs[:3]]
        out[topic_id] = fallback

    return out


def write_topics(
    db_path: Path,
    ids: list[str],
    texts: list[str] | None,
    topics_arr: np.ndarray,
    probs: np.ndarray,
    model: Any,
    params: dict[str, Any],
    *,
    fresh: bool = False,
) -> dict[str, Any]:
    """Persist BERTopic output back into the `.db`.

    Populates `topics`, `record_topics`, rebuilds `topics_fts`, and stamps
    meta keys (`topics_build_complete_at`, `bertopic_version`, `topics_params`).
    Does NOT populate `recording_topics` — call `aggregate_recording_topics`
    after this.
    """
    import bertopic

    conn = _connect(db_path)
    try:
        if fresh:
            _drop_topic_tables(conn)
        _ensure_topic_schema(conn)

        topic_info = model.get_topic_info()
        size_by_topic: dict[int, int] = dict(
            zip(topic_info["Topic"].astype(int), topic_info["Count"].astype(int))
        )

        representative_ids = _build_representative_ids(model, texts, ids, topics_arr)

        topic_ids_sorted = sorted(size_by_topic.keys())
        log.info(
            "writing %d topics (incl. outliers=%s) covering %d chunks",
            len(topic_ids_sorted),
            -1 in size_by_topic,
            int(topics_arr.size),
        )

        conn.execute("DELETE FROM topics")
        conn.execute("DELETE FROM record_topics")

        now = time.time()
        topic_rows = []
        for t in topic_ids_sorted:
            kw_pairs = model.get_topic(t) or []
            keywords = [w for (w, _score) in kw_pairs if isinstance(w, str)]
            label = _safe_label(int(t), keywords)
            topic_rows.append((
                int(t),
                label,
                json.dumps(keywords[:15], ensure_ascii=False),
                None,
                int(size_by_topic.get(t, 0)),
                json.dumps(representative_ids.get(int(t), []), ensure_ascii=False),
                now,
            ))
        conn.executemany(
            "INSERT INTO topics(topic_id, label, keywords_json, description, size, "
            "representative_ids_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            topic_rows,
        )

        conn.executemany(
            "INSERT INTO record_topics(record_id, topic_id, probability) VALUES (?, ?, ?)",
            [
                (ids[i], int(topics_arr[i]), float(probs[i]))
                for i in range(len(ids))
            ],
        )

        conn.execute("INSERT INTO topics_fts(topics_fts) VALUES('rebuild')")

        _meta_set(conn, "topics_build_complete_at", f"{now:.3f}")
        _meta_set(conn, "bertopic_version", bertopic.__version__)
        _meta_set(conn, "topics_params", json.dumps(params, ensure_ascii=False, default=str))
        conn.commit()

        return {
            "topic_count": len(topic_ids_sorted),
            "outliers": int(size_by_topic.get(-1, 0)),
            "chunks_assigned": int((topics_arr != -1).sum()),
            "chunks_total": int(topics_arr.size),
        }
    finally:
        conn.close()


# -- Recording-level aggregation ---------------------------------------------


def aggregate_recording_topics(db_path: Path) -> int:
    """Fill `recording_topics` from `record_topics` + `records.parent_id`."""
    conn = _connect(db_path)
    try:
        _ensure_topic_schema(conn)
        rows = conn.execute(
            "SELECT r.parent_id, rt.topic_id "
            "FROM records r JOIN record_topics rt ON rt.record_id = r.id"
        ).fetchall()

        by_parent: dict[str, Counter] = defaultdict(Counter)
        for parent_id, topic_id in rows:
            by_parent[parent_id][int(topic_id)] += 1

        conn.execute("DELETE FROM recording_topics")
        out_rows = []
        for parent_id, counter in by_parent.items():
            total = sum(counter.values())
            ranked = counter.most_common()
            primary_topic_id, primary_count = ranked[0]
            primary_share = primary_count / total if total else 0.0
            secondary = [
                {"topic_id": int(t), "count": int(c), "share": round(c / total, 4)}
                for t, c in ranked[1:4]
            ]
            out_rows.append((
                parent_id,
                int(primary_topic_id),
                float(primary_share),
                json.dumps(secondary, ensure_ascii=False),
                int(total),
            ))

        conn.executemany(
            "INSERT INTO recording_topics(parent_id, primary_topic_id, primary_share, "
            "secondary_json, chunk_count) VALUES (?, ?, ?, ?, ?)",
            out_rows,
        )
        conn.commit()
        return len(out_rows)
    finally:
        conn.close()


# -- Markdown catalog --------------------------------------------------------


def render_catalog_markdown(
    db_path: Path,
    out_path: Path,
    *,
    top_recordings_per_topic: int = 10,
) -> Path:
    """Write a single `<corpus>_topics.md` catalog from the `.db`."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta = {k: v for k, v in conn.execute("SELECT key, value FROM meta")}
        corpus = meta.get("corpus", db_path.stem)

        topics_rows = conn.execute(
            "SELECT topic_id, label, keywords_json, description, size, "
            "representative_ids_json FROM topics ORDER BY size DESC, topic_id"
        ).fetchall()

        if not topics_rows:
            raise RuntimeError(f"{db_path}: no topics to render; run build_topics.py first")

        lines: list[str] = []
        lines.append(f"# {corpus} — topic catalog")
        lines.append("")
        lines.append(
            f"Auto-generated from `{db_path.name}`. "
            f"Built with bertopic `{meta.get('bertopic_version', '?')}`, "
            f"sbert model `{meta.get('model', '?')}`, "
            f"min_topic_size={json.loads(meta.get('topics_params', '{}')).get('min_topic_size', '?')}."
        )
        lines.append("")
        lines.append(
            f"Covering **{int(meta.get('record_count', '0') or 0)} chunks** "
            f"across **{int(meta.get('parent_count', '0') or 0)} recordings**; "
            f"**{len(topics_rows)} topics** (including -1 outliers if present)."
        )
        lines.append("")

        lines.append("## Topics (by size)")
        lines.append("")
        lines.append("| Topic | Size | Keywords |")
        lines.append("|---:|---:|---|")
        for (tid, label, kw_json, _desc, size, _reps) in topics_rows:
            kws = ", ".join(json.loads(kw_json)[:6]) if kw_json else ""
            anchor = f"topic-{int(tid)}" if int(tid) >= 0 else "topic-outliers"
            lines.append(f"| [{int(tid):>3}](#{anchor}) | {int(size)} | {kws} |")
        lines.append("")

        for (tid, label, kw_json, desc, size, reps_json) in topics_rows:
            tid_int = int(tid)
            anchor = f"topic-{tid_int}" if tid_int >= 0 else "topic-outliers"
            lines.append(f"### <a name=\"{anchor}\"></a>Topic {tid_int}: {label}")
            lines.append("")
            lines.append(f"- **Size**: {int(size)} chunks")
            kws = json.loads(kw_json) if kw_json else []
            if kws:
                lines.append(f"- **Keywords**: {', '.join(kws[:15])}")
            if desc:
                lines.append(f"- **Description**: {desc}")
            lines.append("")

            rep_ids: list[str] = json.loads(reps_json) if reps_json else []
            if rep_ids:
                placeholders = ",".join(["?"] * len(rep_ids))
                rep_rows = conn.execute(
                    f"SELECT id, text FROM records WHERE id IN ({placeholders})",
                    rep_ids,
                ).fetchall()
                by_id = {r[0]: r[1] for r in rep_rows}
                lines.append("**Representative excerpts**:")
                lines.append("")
                for rid in rep_ids:
                    text = (by_id.get(rid) or "").strip()
                    if not text:
                        continue
                    snippet = text.replace("\r", "").strip()
                    if len(snippet) > 600:
                        snippet = snippet[:600].rstrip() + "…"
                    lines.append(f"- `{rid}` —")
                    for t_line in snippet.split("\n"):
                        lines.append(f"  > {t_line}")
                lines.append("")

            rec_rows = conn.execute(
                """
                SELECT rt.parent_id, rt.primary_share, rt.chunk_count,
                       (SELECT title FROM records WHERE parent_id = rt.parent_id LIMIT 1) AS title,
                       (SELECT metadata FROM records WHERE parent_id = rt.parent_id LIMIT 1) AS meta_json
                FROM recording_topics rt
                WHERE rt.primary_topic_id = ?
                ORDER BY rt.chunk_count DESC
                LIMIT ?
                """,
                (tid_int, top_recordings_per_topic),
            ).fetchall()
            if rec_rows:
                lines.append("**Top recordings (primary topic):**")
                lines.append("")
                for (parent_id, share, chunk_count, title, meta_json) in rec_rows:
                    md = {}
                    try:
                        md = json.loads(meta_json) if meta_json else {}
                    except (TypeError, ValueError):
                        md = {}
                    account = md.get("account_name") or md.get("account_id") or "?"
                    date = md.get("call_date") or "?"
                    recording_id = md.get("recording_id") or parent_id.split(":", 1)[-1]
                    pretty_title = title or f"recording {recording_id}"
                    lines.append(
                        f"- `{recording_id}` — {pretty_title} "
                        f"(account: {account}, {date}, {int(chunk_count)} chunks, "
                        f"{float(share) * 100:.0f}% primary share)"
                    )
                lines.append("")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path
    finally:
        conn.close()


# -- Sanity check / inspection -----------------------------------------------


def sample_topic_chunks(
    db_path: Path,
    *,
    top_n_topics: int = 5,
    per_topic: int = 5,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Return random chunks from each of the N largest non-outlier topics."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        topics = conn.execute(
            "SELECT topic_id, label, size FROM topics "
            "WHERE topic_id >= 0 ORDER BY size DESC LIMIT ?",
            (top_n_topics,),
        ).fetchall()

        rng = random.Random(seed)
        out: list[dict[str, Any]] = []
        for (tid, label, size) in topics:
            tid_int = int(tid)
            ids = [
                r[0] for r in conn.execute(
                    "SELECT record_id FROM record_topics WHERE topic_id = ?",
                    (tid_int,),
                ).fetchall()
            ]
            if not ids:
                continue
            pick_n = min(per_topic, len(ids))
            picked = rng.sample(ids, pick_n)
            placeholders = ",".join(["?"] * len(picked))
            chunks = conn.execute(
                f"SELECT id, parent_id, text FROM records WHERE id IN ({placeholders})",
                picked,
            ).fetchall()
            out.append({
                "topic_id": tid_int,
                "label": label,
                "size": int(size),
                "chunks": [
                    {"id": c[0], "parent_id": c[1], "text": c[2]} for c in chunks
                ],
            })
        return out
    finally:
        conn.close()


# -- LLM description stub (future hook) --------------------------------------


def describe_topics(*_args, **_kwargs):
    """Future hook for LLM-generated topic descriptions; currently a no-op."""
    raise NotImplementedError(
        "LLM topic descriptions are deferred to a later pass; "
        "topics.description stays NULL in v1."
    )
