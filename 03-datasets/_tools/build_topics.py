#!/usr/bin/env python3
"""Fit BERTopic on an existing corpus `.db` and persist topic metadata.

Reads precomputed `records.embedding` vectors from
`03-datasets/_indexes/<corpus>.db` (built by `build_index.py`), fits a
BERTopic model, writes topics + per-chunk assignments + per-recording
aggregates back into the same `.db`, and renders a human-browsable
`03-datasets/_indexes/<corpus>_topics.md` catalog.

No network, no Ollama, no API keys. Embeddings are NEVER recomputed.
The BERTopic constructor is given a SentenceTransformer only so future
`.transform()` / `.find_topics()` calls can embed new queries.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from _tools.topics import (  # noqa: E402
    aggregate_recording_topics,
    extract_speaker_stopwords,
    fit_bertopic,
    load_embeddings_from_db,
    load_embeddings_no_text_from_db,
    render_catalog_markdown,
    sample_topic_chunks,
    write_topics,
)

log = logging.getLogger("build_topics")

# Paths resolve relative to this file, so the kit works wherever it is dropped.
INDEXES_DIR = _HERE.parent / "_indexes"


def _load_sbert_from_index(db_path: Path):
    """Instantiate the sentence-transformers model recorded in meta.

    BERTopic needs the SentenceTransformer object (not our Embedder
    wrapper) so it can call `.encode(...)` on new queries later.
    """
    import sqlite3

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta = {k: v for k, v in conn.execute("SELECT key, value FROM meta")}
    finally:
        conn.close()

    provider = meta.get("provider", "")
    model_name = meta.get("model", "")
    if provider != "sentence-transformers":
        log.warning(
            "index provider=%r (model=%r) is not sentence-transformers; "
            "BERTopic will be fitted without an embedding model, so later "
            ".transform() calls would need pre-embedded vectors.",
            provider, model_name,
        )
        return None

    from sentence_transformers import SentenceTransformer
    log.info("loading %s for BERTopic (so .transform() works later)", model_name)
    return SentenceTransformer(model_name, trust_remote_code=True)


def _inspect(db_path: Path, *, top_n_topics: int, per_topic: int) -> int:
    out = sample_topic_chunks(
        db_path, top_n_topics=top_n_topics, per_topic=per_topic
    )
    if not out:
        print("no topics found; run without --inspect first")
        return 2
    for topic in out:
        print("=" * 78)
        print(
            f"Topic {topic['topic_id']} ({topic['size']} chunks): {topic['label']}"
        )
        print("=" * 78)
        for c in topic["chunks"]:
            print(f"\n-- {c['id']} (recording {c['parent_id']}):")
            text = c["text"]
            if len(text) > 800:
                text = text[:800].rstrip() + "…"
            print(text)
        print()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fit BERTopic on an existing corpus .db and persist topic metadata."
    )
    ap.add_argument("--corpus", required=True,
                    help="Corpus name (matches _indexes/<corpus>.db).")
    ap.add_argument("--min-topic-size", type=int, default=10,
                    help="HDBSCAN min_cluster_size (default: 10).")
    ap.add_argument("--nr-topics", default="auto",
                    help="'auto' (default), an integer, or 'none' to disable topic reduction.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Use only the first N records (after load). Smoke-test knob.")
    ap.add_argument("--sample-fit", type=int, default=None,
                    help="Fit on a random sample of this many records then transform the rest. "
                         "No-op at smoke scale.")
    ap.add_argument("--low-memory", action="store_true",
                    help="Avoid loading full text for all chunks; uses sample text for fit "
                         "and lightweight placeholders for transform. Recommended for very "
                         "large corpora on 16 GB RAM hosts.")
    ap.add_argument("--fresh", action="store_true",
                    help="Drop and recreate topic tables before writing.")
    ap.add_argument("--stopword", action="append", default=[],
                    metavar="WORD",
                    help="Extra stopword to exclude from topic keywords. "
                         "Repeatable: --stopword guys --stopword click.")
    ap.add_argument("--stopwords-file", default=None, type=Path,
                    help="Path to a text file with one stopword per line. "
                         "Lines starting with '#' are ignored. Merged with "
                         "--stopword and the built-in kaia filler set.")
    ap.add_argument("--inspect", action="store_true",
                    help="Print random chunks from the 5 largest topics and exit. "
                         "Requires a previous successful build.")
    ap.add_argument("--inspect-top-n", type=int, default=5,
                    help="--inspect: number of largest topics to sample (default: 5).")
    ap.add_argument("--inspect-per-topic", type=int, default=5,
                    help="--inspect: chunks sampled per topic (default: 5).")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    db_path = INDEXES_DIR / f"{args.corpus}.db"
    if not db_path.is_file():
        log.error("index not found: %s (run build_index.py first)", db_path)
        return 2

    if args.inspect:
        return _inspect(
            db_path,
            top_n_topics=args.inspect_top_n,
            per_topic=args.inspect_per_topic,
        )

    nr_topics: str | int | None
    if args.nr_topics.lower() == "auto":
        nr_topics = "auto"
    elif args.nr_topics.lower() == "none":
        nr_topics = None
    else:
        try:
            nr_topics = int(args.nr_topics)
        except ValueError:
            log.error("--nr-topics must be 'auto', 'none', or an int; got %r", args.nr_topics)
            return 2

    log.info("loading embeddings from %s", db_path)
    if args.low_memory:
        ids, embeddings, _parent_ids = load_embeddings_no_text_from_db(db_path)
        texts: list[str] | None = None
    else:
        ids, texts, embeddings, _parent_ids = load_embeddings_from_db(db_path)
    log.info("loaded %d records, dim=%d", embeddings.shape[0], embeddings.shape[1])

    if args.limit is not None:
        ids = ids[: args.limit]
        if texts is not None:
            texts = texts[: args.limit]
        embeddings = embeddings[: args.limit]
        log.info("--limit: truncated to %d records", len(ids))

    sbert_model = _load_sbert_from_index(db_path)

    extra_stopwords_set: set[str] = set(extract_speaker_stopwords(db_path))
    if extra_stopwords_set:
        log.info("collected %d speaker-name stopwords from metadata", len(extra_stopwords_set))

    for w in args.stopword:
        cleaned = w.strip().lower()
        if cleaned:
            extra_stopwords_set.add(cleaned)

    if args.stopwords_file:
        if not args.stopwords_file.is_file():
            log.error("stopwords file not found: %s", args.stopwords_file)
            return 2
        with args.stopwords_file.open(encoding="utf-8") as f:
            added = 0
            for line in f:
                tok = line.strip().lower()
                if not tok or tok.startswith("#"):
                    continue
                extra_stopwords_set.add(tok)
                added += 1
        log.info("added %d stopwords from %s", added, args.stopwords_file)

    extra_stopwords = sorted(extra_stopwords_set)

    if args.low_memory:
        if not args.sample_fit:
            log.error("--low-memory requires --sample-fit to bound text loading and fit memory")
            return 2
        fit_n = min(int(args.sample_fit), len(ids))
        log.info(
            "low-memory mode: loading %d texts for fit sample (transform uses placeholders)",
            fit_n,
        )
        # Read only the first fit_n texts in rowid order to avoid materializing all text.
        import sqlite3

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            rows = conn.execute(
                "SELECT text FROM records ORDER BY rowid LIMIT ?",
                (fit_n,),
            ).fetchall()
        finally:
            conn.close()
        texts = [r[0] for r in rows]

    log.info(
        "fitting BERTopic: min_topic_size=%d nr_topics=%r sample_fit=%r",
        args.min_topic_size, nr_topics, args.sample_fit,
    )
    fit_texts = texts if texts is not None else [""] * embeddings.shape[0]
    topics_arr, probs, model, params = fit_bertopic(
        embeddings=embeddings,
        texts=fit_texts,
        min_topic_size=args.min_topic_size,
        nr_topics=nr_topics,
        sbert_model=sbert_model,
        sample_fit=args.sample_fit,
        extra_stopwords=extra_stopwords,
    )

    log.info("writing topics to %s", db_path)
    texts_for_write = texts if texts is not None and len(texts) == len(ids) else None
    summary = write_topics(
        db_path, ids, texts_for_write, topics_arr, probs, model, params, fresh=args.fresh
    )
    log.info(
        "wrote topics: %d total, %d outliers, %d/%d chunks assigned",
        summary["topic_count"], summary["outliers"],
        summary["chunks_assigned"], summary["chunks_total"],
    )

    n_recordings = aggregate_recording_topics(db_path)
    log.info("aggregated %d recordings into recording_topics", n_recordings)

    catalog_path = INDEXES_DIR / f"{args.corpus}_topics.md"
    render_catalog_markdown(db_path, catalog_path)
    log.info("wrote catalog: %s", catalog_path)

    print(json.dumps({
        "corpus": args.corpus,
        "db": str(db_path),
        "catalog": str(catalog_path),
        "topics": summary["topic_count"],
        "outliers": summary["outliers"],
        "chunks_assigned": summary["chunks_assigned"],
        "chunks_total": summary["chunks_total"],
        "recordings": n_recordings,
        "params": params,
    }, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
