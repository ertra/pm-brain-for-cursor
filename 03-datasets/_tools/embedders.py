"""Embedder protocol + local Ollama implementation.

The rest of the pipeline is provider-agnostic. Future providers (Voyage,
OpenAI, ...) can be added here without touching build_index.py or query.py.
Each .db records meta.provider / meta.model / meta.dim so query.py verifies
the local environment matches the index.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Protocol

import numpy as np
import requests

log = logging.getLogger(__name__)


class Embedder(Protocol):
    provider: str
    model: str
    dim: int

    def embed_one(self, text: str) -> np.ndarray: ...
    def embed_batch(self, texts: list[str]) -> np.ndarray: ...


@dataclass
class OllamaEmbedder:
    """Embeds via the local Ollama HTTP API.

    Uses the batched `/api/embed` endpoint, which Ollama 0.1.26+ supports.
    On older Ollama versions falls back to the single-doc `/api/embeddings`
    endpoint. Retries transient errors with exponential backoff. Dim is
    asserted against the first real embedding; mismatches abort fast.
    """

    model: str = "nomic-embed-text"
    host: str = "http://localhost:11434"
    timeout: float = 300.0
    max_attempts: int = 3
    backoff_seconds: tuple[float, ...] = (1.0, 4.0, 16.0)
    expected_dim: int | None = None
    batch_size: int = 16

    provider: str = "ollama"
    dim: int = 0

    _session: requests.Session | None = None
    _use_batched: bool | None = None

    def _session_get(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def _check_dim(self, vec: np.ndarray) -> None:
        if self.dim == 0:
            self.dim = int(vec.shape[0])
            if self.expected_dim is not None and self.dim != self.expected_dim:
                raise RuntimeError(
                    f"embedding dim mismatch: model={self.model} returned "
                    f"{self.dim}, expected {self.expected_dim}"
                )
        elif vec.shape[0] != self.dim:
            raise RuntimeError(
                f"embedding dim drifted: first={self.dim}, now={vec.shape[0]}"
            )

    def _normalize(self, vec: np.ndarray) -> np.ndarray:
        norm = float(np.linalg.norm(vec))
        if norm == 0.0 or not np.isfinite(norm):
            raise RuntimeError("degenerate embedding (zero or non-finite norm)")
        return (vec / norm).astype(np.float32, copy=False)

    def embed_one(self, text: str) -> np.ndarray:
        """Embed a single text. Returns L2-normalized float32 vector."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts. Returns (N, dim) L2-normalized float32 matrix."""
        if not texts:
            return np.zeros((0, self.dim or 0), dtype=np.float32)

        # Try batched endpoint first; fall back to per-request on failure.
        url_batch = f"{self.host.rstrip('/')}/api/embed"
        url_single = f"{self.host.rstrip('/')}/api/embeddings"

        last_err: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                if self._use_batched is not False:
                    r = self._session_get().post(
                        url_batch,
                        json={"model": self.model, "input": texts},
                        timeout=self.timeout,
                    )
                    if r.status_code == 404 and self._use_batched is None:
                        # Old Ollama without /api/embed; fall back permanently.
                        log.info("ollama /api/embed returned 404; falling back to /api/embeddings")
                        self._use_batched = False
                    else:
                        r.raise_for_status()
                        data = r.json()
                        raw = data.get("embeddings")
                        if not raw or not isinstance(raw, list):
                            raise RuntimeError(f"ollama /api/embed returned no embeddings: {r.text[:200]}")
                        if len(raw) != len(texts):
                            raise RuntimeError(
                                f"ollama /api/embed returned {len(raw)} embeddings for {len(texts)} inputs"
                            )
                        self._use_batched = True
                        mat = np.asarray(raw, dtype=np.float32)
                        if mat.ndim != 2:
                            raise RuntimeError(f"unexpected shape from /api/embed: {mat.shape}")
                        self._check_dim(mat[0])
                        norms = np.linalg.norm(mat, axis=1, keepdims=True)
                        if not np.all(np.isfinite(norms)) or np.any(norms == 0.0):
                            raise RuntimeError("degenerate embedding (zero or non-finite norm)")
                        return (mat / norms).astype(np.float32, copy=False)

                # Fallback: one-at-a-time /api/embeddings
                out = np.empty((len(texts), self.dim or 0), dtype=np.float32)
                for i, text in enumerate(texts):
                    r = self._session_get().post(
                        url_single,
                        json={"model": self.model, "prompt": text},
                        timeout=self.timeout,
                    )
                    r.raise_for_status()
                    emb_list = r.json().get("embedding")
                    if not emb_list:
                        raise RuntimeError(f"ollama returned empty embedding: {r.text[:200]}")
                    vec = np.asarray(emb_list, dtype=np.float32)
                    self._check_dim(vec)
                    if out.shape[1] == 0:
                        out = np.empty((len(texts), self.dim), dtype=np.float32)
                    out[i] = self._normalize(vec)
                return out

            except (requests.RequestException, RuntimeError, ValueError) as err:
                last_err = err
                if attempt + 1 < self.max_attempts:
                    wait = self.backoff_seconds[min(attempt, len(self.backoff_seconds) - 1)]
                    log.warning(
                        "ollama embed_batch failed (attempt %d/%d, n=%d): %s; sleeping %.1fs",
                        attempt + 1, self.max_attempts, len(texts), err, wait,
                    )
                    time.sleep(wait)
                else:
                    log.error(
                        "ollama embed_batch permanently failed after %d attempts (n=%d): %s",
                        self.max_attempts, len(texts), err,
                    )
        assert last_err is not None
        raise last_err


@dataclass
class SentenceTransformersEmbedder:
    """Embeds via a local sentence-transformers model (PyTorch, no server).

    Default model is `nomic-ai/nomic-embed-text-v1.5` (768d, 8192-token
    context). That model ships custom modeling code, so we load with
    `trust_remote_code=True`. Nomic's training expects task-specific
    prefixes on the input text: `search_document: ` for corpus text
    (indexing) and `search_query: ` for user questions (retrieval). We
    apply the document prefix here; `query.py` applies the query prefix
    on its side via `embed_query()`.

    On CUDA we switch the model to fp16 (`half()`) which ~halves latency
    on T4/A10 for this architecture with no measurable retrieval impact
    (vectors are L2-normalized after encode, so the small precision loss
    washes out for cosine similarity).
    """

    model: str = "nomic-ai/nomic-embed-text-v1.5"
    expected_dim: int | None = None
    batch_size: int = 64
    # Cap the model's input sequence length to bound activation memory at fp16 on
    # mid-range GPUs (T4/A10). nomic-embed-text-v1.5 ships with an 8192-token
    # default, but a single 8192-token input on a T4 OOMs even at batch=1 because
    # attention activations scale O(L^2). 2048 still covers ~1500 English words —
    # plenty for ticket bodies / CR descriptions / kaia utterance windows — and
    # cuts per-item activation memory ~16x vs. the default. Override per
    # corpus/host if needed.
    max_seq_length: int = 2048
    doc_prefix: str = "search_document: "
    query_prefix: str = "search_query: "
    device: str | None = None  # None = auto-detect (cuda if available)
    fp16: bool | None = None   # None = auto (True on CUDA, False on CPU)

    provider: str = "sentence-transformers"
    dim: int = 0

    _model: object | None = None
    _resolved_device: str = ""

    def _load(self) -> object:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            try:
                import torch  # noqa: WPS433
                cuda_available = bool(torch.cuda.is_available())
            except Exception:  # pragma: no cover - torch always present in this project
                cuda_available = False

            device = self.device or ("cuda" if cuda_available else "cpu")
            use_fp16 = (self.fp16 if self.fp16 is not None else device.startswith("cuda"))

            log.info(
                "loading sentence-transformers model %s on device=%s fp16=%s "
                "(first run may download ~500 MB)",
                self.model, device, use_fp16,
            )
            m = SentenceTransformer(self.model, trust_remote_code=True, device=device)
            try:
                m.max_seq_length = int(self.max_seq_length)
            except Exception as err:  # pragma: no cover - defensive only
                log.warning("failed to set max_seq_length=%s: %s", self.max_seq_length, err)
            if use_fp16 and device.startswith("cuda"):
                m = m.half()
            log.info(
                "model ready: max_seq_length=%s",
                getattr(m, "max_seq_length", "unknown"),
            )
            self._model = m
            self._resolved_device = device
        return self._model

    def _check_dim(self, vec_dim: int) -> None:
        if self.dim == 0:
            self.dim = int(vec_dim)
            if self.expected_dim is not None and self.dim != self.expected_dim:
                raise RuntimeError(
                    f"embedding dim mismatch: model={self.model} returned "
                    f"{self.dim}, expected {self.expected_dim}"
                )
        elif vec_dim != self.dim:
            raise RuntimeError(
                f"embedding dim drifted: first={self.dim}, now={vec_dim}"
            )

    def _encode(self, texts: list[str], *, prefix: str) -> np.ndarray:
        m = self._load()
        prefixed = [prefix + (t or "") for t in texts]
        mat = m.encode(
            prefixed,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        mat = np.asarray(mat, dtype=np.float32)
        if mat.ndim != 2:
            raise RuntimeError(f"unexpected shape from sentence-transformers: {mat.shape}")
        self._check_dim(mat.shape[1])
        return mat

    def embed_one(self, text: str) -> np.ndarray:
        return self._encode([text], prefix=self.doc_prefix)[0]

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim or 0), dtype=np.float32)
        return self._encode(texts, prefix=self.doc_prefix)

    def embed_query(self, text: str) -> np.ndarray:
        """Embed a user query with the `search_query: ` prefix."""
        return self._encode([text], prefix=self.query_prefix)[0]


def make_embedder(provider: str, model: str, *, expected_dim: int | None = None) -> Embedder:
    """Factory. Add new providers here as new branches."""
    if provider == "ollama":
        return OllamaEmbedder(model=model, expected_dim=expected_dim)
    if provider == "sentence-transformers":
        return SentenceTransformersEmbedder(model=model, expected_dim=expected_dim)
    raise ValueError(f"unknown embedder provider: {provider!r}")
