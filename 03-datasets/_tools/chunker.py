"""Chunkers split a LogicalDoc into one or more indexable Records.

`NoopChunker` is the identity chunker for cr_tickets and support_tickets
(one record per source file). `UtteranceWindowChunker` is used by
call_transcripts and will be filled in during Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class LogicalDoc:
    """One logical source document before chunking.

    - For non-chunked corpora, this maps 1:1 to a Record via NoopChunker.
    - For chunked corpora (kaia), `raw` carries corpus-specific raw material
      (e.g. the list of utterances) that the chunker knows how to slice.
    """

    parent_id: str
    title: str | None
    text: str
    metadata: dict[str, Any]
    source_path: str
    source_mtime: float
    raw: Any = None


@dataclass
class Record:
    """One indexable record = one row in the `records` table = one vector."""

    id: str
    parent_id: str
    title: str | None
    text: str
    metadata: dict[str, Any]
    source_path: str
    source_mtime: float


class Chunker(Protocol):
    name: str

    def chunk(self, doc: LogicalDoc) -> list[Record]: ...


class NoopChunker:
    """Identity chunker: one Record per LogicalDoc, id = parent_id."""

    name = "noop"

    def chunk(self, doc: LogicalDoc) -> list[Record]:
        return [
            Record(
                id=doc.parent_id,
                parent_id=doc.parent_id,
                title=doc.title,
                text=doc.text,
                metadata=doc.metadata,
                source_path=doc.source_path,
                source_mtime=doc.source_mtime,
            )
        ]


@dataclass
class UtteranceWindowChunker:
    """Windowed utterance chunker for call_transcripts.

    Consumes `doc.raw["utterances"]` (a list of dicts with keys
    `offsetMs`, `durationMs`, `speaker.displayName`, `speaker.inMeetingId`,
    `text`) plus `doc.raw["participants_by_id"]` (inMeetingId -> {name, role}).

    Produces one Record per window of `window` consecutive utterances, stride
    `stride` (so overlap = window - stride). Filters:
      * drop windows under `min_chars` of non-whitespace text
      * drop windows with fewer than `min_unique_tokens` unique alphabetic tokens
      * drop windows where every utterance is under 5 words
    """

    name: str = "utterance_window"
    window: int = 20
    stride: int = 18
    min_chars: int = 200
    min_unique_tokens: int = 30
    min_short_utt_words: int = 5

    def chunk(self, doc: LogicalDoc) -> list[Record]:
        import re

        raw = doc.raw or {}
        utterances = raw.get("utterances") or []
        participants_by_id: dict[int | str, dict[str, str]] = raw.get("participants_by_id") or {}

        if not utterances:
            return []

        out: list[Record] = []
        n = len(utterances)
        step = max(1, self.stride)
        size = max(1, self.window)
        for i, start in enumerate(range(0, n, step)):
            end = min(start + size, n)
            window_utts = utterances[start:end]
            if not window_utts:
                continue

            rendered, text_chars, unique_tokens, long_utt_count = _render_window(
                window_utts, participants_by_id
            )

            if text_chars < self.min_chars:
                continue
            if len(unique_tokens) < self.min_unique_tokens:
                continue
            if long_utt_count == 0:
                # Every utterance is under N words -> chatter-only window.
                continue

            start_ms = int(window_utts[0].get("offsetMs") or 0)
            last = window_utts[-1]
            end_ms = int((last.get("offsetMs") or 0) + (last.get("durationMs") or 0))
            roles_present = sorted(
                {
                    participants_by_id.get(u.get("speaker", {}).get("inMeetingId"), {}).get("role", "UNKNOWN")
                    for u in window_utts
                }
            )

            chunk_metadata = {
                **doc.metadata,
                "chunk_index": i,
                "chunk_start_ms": start_ms,
                "chunk_end_ms": end_ms,
                "chunk_start_mmss": _mmss(start_ms),
                "chunk_end_mmss": _mmss(end_ms),
                "chunk_speakers": roles_present,
                "chunk_utterance_count": len(window_utts),
            }

            chunk_id = f"{doc.parent_id}:c{i:04d}"
            out.append(
                Record(
                    id=chunk_id,
                    parent_id=doc.parent_id,
                    title=doc.title,
                    text=rendered,
                    metadata=chunk_metadata,
                    source_path=doc.source_path,
                    source_mtime=doc.source_mtime,
                )
            )

            if end >= n:
                break
        return out


_ALPHA_TOKEN_RE = None  # lazy compile in _render_window


def _render_window(
    utts: list[dict[str, Any]],
    participants_by_id: dict[int | str, dict[str, str]],
) -> tuple[str, int, set[str], int]:
    """Render a list of utterances into [Speaker, ROLE @ mm:ss] text form.

    Returns (rendered_text, non_ws_char_count, unique_token_set, long_utt_count).
    """
    import re
    global _ALPHA_TOKEN_RE
    if _ALPHA_TOKEN_RE is None:
        _ALPHA_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]+")

    lines: list[str] = []
    char_count = 0
    tokens: set[str] = set()
    long_utt = 0
    for u in utts:
        text = (u.get("text") or "").strip()
        if not text:
            continue
        sp = u.get("speaker") or {}
        who = sp.get("displayName") or "Unknown"
        pid = sp.get("inMeetingId")
        role = participants_by_id.get(pid, {}).get("role", "UNKNOWN")
        offset = int(u.get("offsetMs") or 0)
        lines.append(f"[{who}, {role} @ {_mmss(offset)}] {text}")
        char_count += sum(1 for c in text if not c.isspace())
        for tok in _ALPHA_TOKEN_RE.findall(text):
            tokens.add(tok.lower())
        if len(text.split()) >= 5:
            long_utt += 1
    return "\n".join(lines), char_count, tokens, long_utt


def _mmss(ms: int) -> str:
    total = max(0, int(ms) // 1000)
    return f"{total // 60:02d}:{total % 60:02d}"
