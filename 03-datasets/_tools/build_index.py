#!/usr/bin/env python3
"""Build (or incrementally update) the SQLite + FTS5 semantic index for a corpus.

Single-file artifact: `<dataset_root>/_indexes/<corpus>.db` holds the text,
metadata, vectors (as BLOBs), and FTS5 inverted index. Resumable, atomic,
and safe to Ctrl-C. Paths resolve relative to this script's location,
so the kit works wherever the `_tools/` folder is dropped (e.g. when
shipped alongside the `03-datasets/` example dataset).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import signal
import sqlite3
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
# Allow `python 03-datasets/_tools/build_index.py` to work from any cwd.
# Add the `03-datasets/` dir to sys.path so `_tools` resolves as a package.
sys.path.insert(0, str(_HERE.parent))

from _tools.chunker import NoopChunker, Record, UtteranceWindowChunker  # noqa: E402
from _tools.embedders import make_embedder  # noqa: E402
from _tools.flatten import FLATTENER_REGISTRY  # noqa: E402

log = logging.getLogger("build_index")

# Layout ----------------------------------------------------------------------

# Paths resolve relative to this file, so the kit works wherever it is dropped.
# `_HERE` is `<dataset_root>/_tools/`, so `_HERE.parent` is the dataset root
# that contains `support_tickets/`, `call_transcripts/`, and `_indexes/`.
DATASETS_DIR = _HERE.parent
INDEXES_DIR = DATASETS_DIR / "_indexes"


_CUDA_OOM_PATTERNS = (
    re.compile(r"cuda out of memory", re.IGNORECASE),
    re.compile(r"cublas_status_alloc_failed", re.IGNORECASE),
)


def _is_cuda_oom_error(err: Exception) -> bool:
    msg = str(err or "")
    return any(p.search(msg) for p in _CUDA_OOM_PATTERNS)


def _corpus_db_path(corpus: str) -> Path:
    return INDEXES_DIR / f"{corpus}.db"


def _corpus_building_path(corpus: str) -> Path:
    return INDEXES_DIR / f"{corpus}.db.building"


def _corpus_source_dir(corpus: str, reg: dict) -> Path:
    return DATASETS_DIR / reg["corpus_dir_name"]


# Schema ----------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS records (
    rowid        INTEGER PRIMARY KEY,
    id           TEXT UNIQUE NOT NULL,
    parent_id    TEXT NOT NULL,
    title        TEXT,
    text         TEXT NOT NULL,
    metadata     TEXT NOT NULL,
    embedding    BLOB NOT NULL,
    source_path  TEXT NOT NULL,
    source_mtime REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS records_parent_id  ON records(parent_id);
CREATE INDEX IF NOT EXISTS records_source_path ON records(source_path);

CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(
    title,
    text,
    parent_id UNINDEXED,
    content='records',
    content_rowid='rowid',
    tokenize='porter unicode61 remove_diacritics 2'
);

CREATE TABLE IF NOT EXISTS progress (
    rowid         INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at     REAL NOT NULL,
    done_count    INTEGER NOT NULL,
    total_count   INTEGER NOT NULL,
    rate_per_sec  REAL NOT NULL,
    eta_seconds   REAL
);

-- Topic modeling layer (populated by build_topics.py). Created here so
-- fresh builds are forward-compatible; build_topics.py re-runs these
-- CREATE TABLE IF NOT EXISTS statements to work against older .db files.
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

# Triggers keep FTS synced for incremental runs. Disabled during bulk fresh
# builds via `DROP TRIGGER IF EXISTS ...` and re-created afterwards.
TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS records_ai AFTER INSERT ON records BEGIN
  INSERT INTO records_fts(rowid, title, text, parent_id)
    VALUES (new.rowid, new.title, new.text, new.parent_id);
END;
CREATE TRIGGER IF NOT EXISTS records_ad AFTER DELETE ON records BEGIN
  INSERT INTO records_fts(records_fts, rowid, title, text, parent_id)
    VALUES ('delete', old.rowid, old.title, old.text, old.parent_id);
END;
CREATE TRIGGER IF NOT EXISTS records_au AFTER UPDATE ON records BEGIN
  INSERT INTO records_fts(records_fts, rowid, title, text, parent_id)
    VALUES ('delete', old.rowid, old.title, old.text, old.parent_id);
  INSERT INTO records_fts(rowid, title, text, parent_id)
    VALUES (new.rowid, new.title, new.text, new.parent_id);
END;
"""

DROP_TRIGGERS_SQL = """
DROP TRIGGER IF EXISTS records_ai;
DROP TRIGGER IF EXISTS records_ad;
DROP TRIGGER IF EXISTS records_au;
"""


# Meta helpers ----------------------------------------------------------------


def _meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def _meta_get(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


# Main logic ------------------------------------------------------------------


@dataclass
class BuildPlan:
    new_sources: list[Path]
    changed_sources: list[Path]
    unchanged_count: int
    to_delete_paths: list[str]

    @property
    def todo(self) -> list[Path]:
        return self.new_sources + self.changed_sources


def _load_existing_state(conn: sqlite3.Connection) -> tuple[dict[str, float], dict[str, list[str]]]:
    """Return (mtime_by_source_path, parent_ids_by_source_path)."""
    mtimes: dict[str, float] = {}
    parents: dict[str, list[str]] = {}
    for sp, mt, pid in conn.execute(
        "SELECT source_path, source_mtime, parent_id FROM records"
    ):
        mtimes[sp] = mt  # may be overwritten; same mtime for chunks of same parent
        parents.setdefault(sp, []).append(pid)
    return mtimes, parents


def _plan_build(
    sources: list[Path],
    existing_mtimes: dict[str, float],
    pipeline_version_matches: bool,
) -> BuildPlan:
    new: list[Path] = []
    changed: list[Path] = []
    on_disk: set[str] = set()
    for p in sources:
        sp = str(p)
        on_disk.add(sp)
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        prev = existing_mtimes.get(sp)
        if prev is None:
            new.append(p)
        elif not pipeline_version_matches or abs(prev - mtime) > 1e-6:
            changed.append(p)
    deleted = [sp for sp in existing_mtimes if sp not in on_disk]
    unchanged = len(existing_mtimes) - len(changed) - len(deleted)
    return BuildPlan(
        new_sources=new,
        changed_sources=changed,
        unchanged_count=max(unchanged, 0),
        to_delete_paths=deleted,
    )


def _vector_to_blob(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32, copy=False).tobytes(order="C")


def _blob_to_vector(blob: bytes, dim: int) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32, count=dim).copy()


# Signal handling -------------------------------------------------------------

_STOP = threading.Event()


def _install_signal_handlers() -> None:
    def handler(signum, _frame):
        name = signal.Signals(signum).name
        log.warning("\nreceived %s; finishing current batch and exiting cleanly...", name)
        _STOP.set()
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


# Build pass ------------------------------------------------------------------


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.executescript(TRIGGER_SQL)


def _run_build(
    *,
    corpus: str,
    provider: str,
    model: str,
    parallel: int,
    limit: int | None,
    check_only: bool,
    dry_run: bool,
    fresh: bool,
    retry_skipped: bool,
) -> int:
    reg = FLATTENER_REGISTRY.get(corpus)
    if reg is None:
        log.error("unknown corpus %r (available: %s)", corpus, ", ".join(sorted(FLATTENER_REGISTRY)))
        return 2

    corpus_dir = _corpus_source_dir(corpus, reg)
    if not corpus_dir.is_dir():
        log.error("corpus source directory missing: %s", corpus_dir)
        return 2

    INDEXES_DIR.mkdir(parents=True, exist_ok=True)
    final_path = _corpus_db_path(corpus)
    building_path = _corpus_building_path(corpus)

    existing_final = final_path.exists()
    if fresh and existing_final:
        log.info("--fresh: leaving existing %s in place until new build is ready", final_path.name)

    # Decide write target
    if existing_final and not fresh:
        work_path = final_path
        mode_label = "incremental"
    else:
        if fresh and building_path.exists():
            building_path.unlink()
        work_path = building_path
        mode_label = "fresh"

    log.info("corpus=%s mode=%s db=%s", corpus, mode_label, work_path.name)

    conn = _connect(work_path)
    try:
        _init_schema(conn)

        # Check provider/model/dim consistency with any previous content.
        stored_provider = _meta_get(conn, "provider")
        stored_model = _meta_get(conn, "model")
        stored_dim_str = _meta_get(conn, "dim")
        stored_pipeline = _meta_get(conn, "pipeline_version")
        pipeline_version = reg["pipeline_version"]

        if stored_provider and (stored_provider != provider or stored_model != model):
            log.error(
                "provider/model mismatch: stored=%s/%s, requested=%s/%s. "
                "Use --fresh to rebuild or match the stored model.",
                stored_provider, stored_model, provider, model,
            )
            return 2

        pipeline_matches = (stored_pipeline == pipeline_version) or (stored_pipeline is None)

        # Enumerate source files
        sources = list(reg["iter_sources"](corpus_dir))
        if limit is not None:
            sources = sources[:limit]
        log.info("enumerated %d source files under %s", len(sources), corpus_dir)

        existing_mtimes, _parents_by_src = _load_existing_state(conn)
        plan = _plan_build(sources, existing_mtimes, pipeline_matches)

        log.info(
            "plan: new=%d changed=%d unchanged=%d deleted=%d (pipeline_version match=%s)",
            len(plan.new_sources), len(plan.changed_sources), plan.unchanged_count,
            len(plan.to_delete_paths), pipeline_matches,
        )

        if check_only:
            log.info("--check: exiting without writing")
            return 0

        if dry_run:
            log.info("--dry-run: would embed %d records; skipping embedding", len(plan.todo))
            return 0

        # Establish embedder (dim will be set on first embed). Verify against stored_dim if present.
        expected_dim = int(stored_dim_str) if stored_dim_str else None
        embedder = make_embedder(provider, model, expected_dim=expected_dim)

        # --retry-skipped: re-queue previously-skipped ids.
        if retry_skipped:
            skipped_json = _meta_get(conn, "skipped_ids")
            skipped = json.loads(skipped_json) if skipped_json else []
            if skipped:
                log.info("--retry-skipped: re-queuing %d previously-skipped records", len(skipped))
                # Can't easily map id->source_path here; simplest = force all changed.
                # Conservative: re-embed every source whose parent_id is in skipped.
                if skipped:
                    new_source_paths = {str(p) for p in plan.new_sources}
                    changed_source_paths = {str(p) for p in plan.changed_sources}
                    for src in sources:
                        src_str = str(src)
                        if src_str in new_source_paths or src_str in changed_source_paths:
                            continue
                        plan.changed_sources.append(src)
                        changed_source_paths.add(src_str)
                _meta_set(conn, "skipped_ids", "[]")
                conn.commit()

        if not plan.todo and not plan.to_delete_paths:
            log.info("nothing to do; index is up to date.")
            _finalize(conn, corpus=corpus, pipeline_version=pipeline_version,
                      provider=provider, model=model, mode_label=mode_label,
                      work_path=work_path, final_path=final_path)
            return 0

        _install_signal_handlers()

        # Fresh full build optimization: drop FTS triggers for speed, rebuild at end.
        bulk_mode = mode_label == "fresh" and plan.unchanged_count == 0 and not plan.to_delete_paths
        if bulk_mode:
            log.info("fresh bulk mode: FTS triggers disabled during insert; will rebuild at end")
            conn.executescript(DROP_TRIGGERS_SQL)

        # Record build start
        now = time.time()
        _meta_set(conn, "corpus", corpus)
        _meta_set(conn, "provider", provider)
        _meta_set(conn, "model", model)
        _meta_set(conn, "chunker", reg["chunker_name"])
        _meta_set(conn, "fts_tokenizer", "porter unicode61 remove_diacritics 2")
        _meta_set(conn, "build_started_at", f"{now:.3f}")
        if not stored_pipeline:
            _meta_set(conn, "pipeline_version", pipeline_version)
        conn.commit()

        # Delete rows whose source files no longer exist
        if plan.to_delete_paths:
            conn.executemany(
                "DELETE FROM records WHERE source_path = ?",
                [(sp,) for sp in plan.to_delete_paths],
            )
            conn.commit()
            log.info("deleted %d stale rows", len(plan.to_delete_paths))

        # For chunked corpora, changed sources need their existing chunks purged first.
        if reg["chunker_name"] != "noop" and plan.changed_sources:
            changed_paths = [str(p) for p in plan.changed_sources]
            conn.executemany(
                "DELETE FROM records WHERE source_path = ?",
                [(sp,) for sp in changed_paths],
            )
            conn.commit()

        # Embed + insert loop (batched via /api/embed).
        skipped_ids: list[str] = (
            json.loads(_meta_get(conn, "skipped_ids") or "[]") if not retry_skipped else []
        )
        chunker = _make_chunker(reg["chunker_name"])
        flatten = reg["flatten"]

        # Tunables. For Ollama the outer batch is capped tight because the
        # server serializes embedding calls anyway. For local GPU inference
        # via sentence-transformers the outer batch *is* the GPU batch, so
        # a much larger size (128 on T4-class cards with nomic v1.5) is a
        # ~3-4x throughput win over 32. Honors an explicit EMBED_BATCH env
        # override for easy tuning without code changes.
        env_batch = os.environ.get("EMBED_BATCH")
        if env_batch:
            try:
                batch_size = max(1, int(env_batch))
            except ValueError:
                log.warning("ignoring non-integer EMBED_BATCH=%r", env_batch)
                batch_size = 32
        elif provider == "sentence-transformers":
            batch_size = 96
        else:
            batch_size = max(4, min(32, parallel * 4))
        embedder.batch_size = batch_size
        log.info("embed batch size = %d (provider=%s)", batch_size, provider)

        total = 0
        total_records_estimate = len(plan.todo)  # ~= for NoopChunker
        build_start = time.time()
        last_commit = build_start
        last_progress_log = build_start
        COMMIT_EVERY_N = 500
        COMMIT_EVERY_S = 30.0
        PROGRESS_EVERY_S = 5.0

        def log_progress(
            done_embeds: int, source_files_queued: int, label: str = "progress"
        ) -> None:
            nonlocal last_progress_log
            elapsed = time.time() - build_start
            rate = done_embeds / elapsed if elapsed > 0 else 0.0
            # For chunked corpora, `done_embeds` is chunk rows written; comparing it
            # to `source_files_queued` produced bogus ">100%" and negative ETAs.
            eta: float | None = None
            if rate > 0 and done_embeds <= source_files_queued:
                eta = (source_files_queued - done_embeds) / rate
            log.info(
                "%s: %d embeddings | %d source files in this run | rate=%.2f emb/s eta=%s",
                label,
                done_embeds,
                source_files_queued,
                rate,
                f"{eta / 60:.1f} min" if eta is not None else "?",
            )
            if done_embeds % 500 == 0 or label == "final":
                conn.execute(
                    "INSERT INTO progress(logged_at, done_count, total_count, rate_per_sec, eta_seconds) "
                    "VALUES(?, ?, ?, ?, ?)",
                    (time.time(), done_embeds, source_files_queued, rate, eta),
                )
                conn.commit()
            last_progress_log = time.time()

        def flush_batch(batch: list[Record], vectors: np.ndarray) -> None:
            nonlocal last_commit
            if not batch:
                return
            conn.executemany(
                "INSERT OR REPLACE INTO records "
                "(id, parent_id, title, text, metadata, embedding, source_path, source_mtime) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        r.id, r.parent_id, r.title, r.text,
                        json.dumps(r.metadata, ensure_ascii=False),
                        _vector_to_blob(vectors[i]),
                        r.source_path, r.source_mtime,
                    )
                    for i, r in enumerate(batch)
                ],
            )
            conn.commit()
            _meta_set(conn, "build_last_commit_at", f"{time.time():.3f}")
            conn.commit()
            last_commit = time.time()

        current_batch: list[Record] = []

        def embed_and_flush_current() -> int:
            """Embed current_batch as a single /api/embed call and persist. Returns count."""
            nonlocal current_batch
            if not current_batch:
                return 0
            texts = [r.text for r in current_batch]
            try:
                vectors = embedder.embed_batch(texts)
            except Exception as err:  # noqa: BLE001
                # On CUDA OOM, recursively split the batch to avoid repeated full-batch failures.
                if _is_cuda_oom_error(err) and len(current_batch) > 1:
                    log.warning(
                        "batch embed OOM (%d items): %s; splitting batch and retrying",
                        len(current_batch),
                        err,
                    )
                    try:
                        import torch  # noqa: WPS433
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                    except Exception:
                        pass

                    mid = max(1, len(current_batch) // 2)
                    left = current_batch[:mid]
                    right = current_batch[mid:]
                    current_batch = []

                    def _embed_sub_batch(batch_part: list[Record]) -> int:
                        nonlocal current_batch
                        if not batch_part:
                            return 0
                        current_batch = batch_part
                        return embed_and_flush_current()

                    return _embed_sub_batch(left) + _embed_sub_batch(right)

                # Permanent failure on the whole batch; split and individual-retry.
                log.error(
                    "batch embed failed (%d items): %s; falling back to individual",
                    len(current_batch),
                    err,
                )
                valid = []
                valid_vectors = []
                for r in current_batch:
                    try:
                        v = embedder.embed_one(r.text)
                        valid.append(r)
                        valid_vectors.append(v)
                    except Exception as e2:  # noqa: BLE001
                        log.error("  permanently skipped id=%s: %s", r.id, e2)
                        skipped_ids.append(r.id)
                if not valid:
                    current_batch = []
                    return 0
                flush_batch(valid, np.asarray(valid_vectors, dtype=np.float32))
                n = len(valid)
                current_batch = []
                return n
            flush_batch(current_batch, vectors)
            n = len(current_batch)
            current_batch = []
            return n

        for src in plan.todo:
            if _STOP.is_set():
                break
            doc = flatten(src)
            if doc is None:
                continue
            try:
                records = chunker.chunk(doc)
            except Exception as err:  # noqa: BLE001
                log.error("chunker failed for %s: %s", src, err)
                continue
            for r in records:
                current_batch.append(r)
                if len(current_batch) >= batch_size:
                    n = embed_and_flush_current()
                    total += n
                    if time.time() - last_progress_log >= PROGRESS_EVERY_S:
                        log_progress(total, total_records_estimate)

        # Flush tail
        n = embed_and_flush_current()
        total += n
        if total > 0:
            log_progress(total, total_records_estimate, label="final")

        if skipped_ids:
            _meta_set(conn, "skipped_ids", json.dumps(skipped_ids))
            conn.commit()
            log.warning("skipped %d records after retries; see meta.skipped_ids", len(skipped_ids))
        else:
            _meta_set(conn, "skipped_ids", "[]")
            conn.commit()

        # Rebuild FTS if we disabled triggers during bulk
        if bulk_mode:
            log.info("rebuilding FTS5 index...")
            t0 = time.time()
            conn.execute("INSERT INTO records_fts(records_fts) VALUES('rebuild')")
            conn.commit()
            conn.executescript(TRIGGER_SQL)
            log.info("FTS5 rebuild done in %.1fs", time.time() - t0)

        # If we got Ctrl-C'd mid-build, don't finalize/rename — leave state for resume
        if _STOP.is_set():
            log.warning(
                "interrupted; build state saved. Re-run to resume:\n    "
                "python _tools/build_index.py --corpus %s --provider %s --model %s",
                corpus, provider, model,
            )
            return 130  # conventional "terminated by SIGINT" exit

        # Finalize embedder dim into meta (now that we have a real one)
        if embedder.dim and not stored_dim_str:
            _meta_set(conn, "dim", str(embedder.dim))
            conn.commit()

        _finalize(conn, corpus=corpus, pipeline_version=pipeline_version,
                  provider=provider, model=model, mode_label=mode_label,
                  work_path=work_path, final_path=final_path)
        return 0

    finally:
        conn.close()


def _make_chunker(name: str):
    if name == "noop":
        return NoopChunker()
    if name == "utterance_window":
        return UtteranceWindowChunker()
    raise ValueError(f"unknown chunker: {name!r}")


def _finalize(
    conn: sqlite3.Connection,
    *,
    corpus: str,
    pipeline_version: str,
    provider: str,
    model: str,
    mode_label: str,
    work_path: Path,
    final_path: Path,
) -> None:
    # record counts
    (record_count,) = conn.execute("SELECT COUNT(*) FROM records").fetchone()
    (parent_count,) = conn.execute("SELECT COUNT(DISTINCT parent_id) FROM records").fetchone()
    (source_file_count,) = conn.execute("SELECT COUNT(DISTINCT source_path) FROM records").fetchone()

    _meta_set(conn, "pipeline_version", pipeline_version)
    _meta_set(conn, "record_count", str(record_count))
    _meta_set(conn, "parent_count", str(parent_count))
    _meta_set(conn, "source_file_count", str(source_file_count))
    _meta_set(conn, "build_complete_at", f"{time.time():.3f}")

    conn.execute("ANALYZE")
    conn.commit()
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    # Switch back to a rollback journal so the published .db is a single
    # self-contained file. WAL mode is great during the write-heavy build,
    # but read-only consumers (query.py opens with ?mode=ro) can't create
    # the required -shm sidecar and would fail with "unable to open
    # database file". DELETE mode has no such requirement.
    try:
        conn.execute("PRAGMA journal_mode=DELETE")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

    if mode_label == "fresh":
        os.replace(work_path, final_path)
        log.info("atomic rename: %s -> %s", work_path.name, final_path.name)

        # Clean up any leftover WAL/SHM sidecars on the building path (rare)
        for sidecar in (f"{work_path}-wal", f"{work_path}-shm"):
            p = Path(sidecar)
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

    log.info(
        "done. records=%d parents=%d source_files=%d -> %s",
        record_count, parent_count, source_file_count, final_path,
    )


# CLI -------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="Build SQLite + FTS5 semantic index for a corpus.")
    ap.add_argument("--corpus", required=True, choices=sorted(FLATTENER_REGISTRY.keys()),
                    help="Which corpus to index.")
    ap.add_argument("--provider", default="ollama", help="Embedder provider (default: ollama).")
    ap.add_argument("--model", default="nomic-embed-text",
                    help="Embedding model name (default: nomic-embed-text).")
    ap.add_argument("--parallel", type=int, default=8,
                    help="Batch-size scaling hint (default: 8); not worker concurrency.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Process at most N source files (smoke tests).")
    ap.add_argument("--check", action="store_true",
                    help="Print added/changed/deleted counts and exit.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Flatten + chunk but don't embed; useful for chunk counts.")
    ap.add_argument("--fresh", action="store_true",
                    help="Ignore existing .db; build a new one from scratch.")
    ap.add_argument("--resume", action="store_true",
                    help="Explicit resume (default behavior; flag exists for documentation).")
    ap.add_argument("--retry-skipped", action="store_true",
                    help="Re-attempt records that were permanently skipped in a prior run.")
    ap.add_argument("-v", "--verbose", action="store_true", help="Verbose logging.")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    return _run_build(
        corpus=args.corpus,
        provider=args.provider,
        model=args.model,
        parallel=args.parallel,
        limit=args.limit,
        check_only=args.check,
        dry_run=args.dry_run,
        fresh=args.fresh,
        retry_skipped=args.retry_skipped,
    )


if __name__ == "__main__":
    sys.exit(main())
