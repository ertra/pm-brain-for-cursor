"""Per-corpus flatteners.

Each flattener turns a raw source file (cr ticket JSON, support ticket
folder, kaia recording folder) into a single LogicalDoc. The chunker then
turns each LogicalDoc into one-or-more Records.

Phase 1 ships `cr_tickets` and `support_tickets`. Phase 2 adds
`call_transcripts` + UtteranceWindowChunker.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .adf import adf_to_text
from .chunker import LogicalDoc

log = logging.getLogger(__name__)


# ----- cr_tickets ------------------------------------------------------------

CR_PIPELINE_VERSION = "cr:v1"


def iter_cr_tickets(corpus_root: Path) -> Iterator[Path]:
    """Yield every CR-*.json file under the corpus root (non-recursive)."""
    for p in sorted(corpus_root.glob("CR-*.json")):
        if p.is_file():
            yield p


def flatten_cr_ticket(source: Path) -> LogicalDoc | None:
    """Flatten one CR-*.json into a LogicalDoc. Returns None if unreadable."""
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        log.warning("cr_tickets: skipping %s: %s", source, err)
        return None

    key = data.get("key") or source.stem
    summary = (data.get("summary") or "").strip()
    description = adf_to_text(data.get("description"), source_hint=str(source))
    workaround = adf_to_text(data.get("workaround"), source_hint=str(source))

    parts: list[str] = []
    if summary:
        parts.append(summary)
    if description:
        parts.append(description)
    if workaround:
        parts.append("Workaround:\n" + workaround)
    text = "\n\n".join(parts).strip() or summary or key

    metadata: dict[str, Any] = {
        "corpus": "cr_tickets",
        "status": data.get("status"),
        "priority": data.get("priority"),
        "customer_priority": data.get("customer_priority"),
        "issuetype": data.get("issuetype"),
        "assignee": data.get("assignee"),
        "reporter": data.get("reporter"),
        "resolution": data.get("resolution"),
        "account_name": data.get("account_name"),
        "contact_email": data.get("contact_email"),
        "labels": data.get("labels") or [],
        "components": data.get("components") or [],
        "created": _date_only(data.get("created")),
        "updated": _date_only(data.get("updated")),
        "jira_id": data.get("id"),
    }

    try:
        source_mtime = source.stat().st_mtime
    except OSError:
        source_mtime = 0.0

    return LogicalDoc(
        parent_id=key,
        title=summary or None,
        text=text,
        metadata=metadata,
        source_path=str(source),
        source_mtime=source_mtime,
    )


# ----- support_tickets -------------------------------------------------------

SUPPORT_PIPELINE_VERSION = "support:v1"


def iter_support_tickets(corpus_root: Path) -> Iterator[Path]:
    """Yield every ticket folder under `<corpus_root>/<YYYYMM>/<ticket_id>/`.

    We emit the `meta.json` path as the canonical source file (mtime comes
    from it). `body.md` is read alongside it.
    """
    for partition in sorted(corpus_root.iterdir()):
        if not partition.is_dir():
            continue
        for ticket_dir in sorted(partition.iterdir()):
            if not ticket_dir.is_dir():
                continue
            meta_path = ticket_dir / "meta.json"
            if meta_path.is_file():
                yield meta_path


def flatten_support_ticket(meta_path: Path) -> LogicalDoc | None:
    """Flatten one support ticket folder into a LogicalDoc."""
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        log.warning("support_tickets: skipping %s: %s", meta_path, err)
        return None

    ticket_dir = meta_path.parent
    partition = ticket_dir.parent.name  # "201801" etc
    ticket_id = meta.get("TICKET_ID") or ticket_dir.name
    subject = (meta.get("TICKET_SUBJECT") or "").strip()

    body_path = ticket_dir / "body.md"
    body = ""
    if body_path.is_file():
        try:
            body = body_path.read_text(encoding="utf-8").strip()
        except OSError as err:
            log.warning("support_tickets: unreadable body %s: %s", body_path, err)

    tags = _parse_tag_list(meta.get("TAG_LIST"))

    parts: list[str] = []
    if tags:
        parts.append(f"[tags: {', '.join(tags)}]")
    if subject and not body.lstrip().startswith(f"# {subject}"):
        parts.append(f"# {subject}")
    if body:
        parts.append(body)
    text = "\n\n".join(parts).strip() or subject or ticket_id

    metadata: dict[str, Any] = {
        "corpus": "support_tickets",
        "subject": subject,
        "status": meta.get("TICKET_STATUS"),
        "priority": meta.get("TICKET_PRIORITY"),
        "tags": tags,
        "jira_key": meta.get("JIRA_KEY"),
        "jira_status": meta.get("JIRA_STATUS"),
        "jira_priority": meta.get("JIRA_PRIORITY"),
        "organization_id": meta.get("ORGANIZATION_ID"),
        "requester_email": meta.get("REQUESTER_EMAIL"),
        "requester_name": meta.get("REQUESTER_NAME"),
        "assignee_id": meta.get("ASSIGNEE_ID"),
        "assigned_to": meta.get("ASSIGNED_TO"),
        "group_name": meta.get("GROUP_NAME"),
        "via_channel": meta.get("VIA_CHANNEL"),
        "created_at": _date_only(meta.get("CREATED_AT")),
        "updated_at": _date_only(meta.get("UPDATED_AT")),
        "partition": partition,
        "sat_score": meta.get("SAT_SCORE"),
    }

    parent_id = f"support:{ticket_id}"

    try:
        source_mtime = meta_path.stat().st_mtime
        if body_path.is_file():
            source_mtime = max(source_mtime, body_path.stat().st_mtime)
    except OSError:
        source_mtime = 0.0

    return LogicalDoc(
        parent_id=parent_id,
        title=subject or None,
        text=text,
        metadata=metadata,
        source_path=str(meta_path),
        source_mtime=source_mtime,
    )


# ----- helpers ---------------------------------------------------------------


def _date_only(value: Any) -> str | None:
    """Best-effort ISO date (YYYY-MM-DD) from a timestamp-ish field."""
    if not value or not isinstance(value, str):
        return None
    return value[:10] if len(value) >= 10 else value


def _parse_tag_list(raw: Any) -> list[str]:
    """TAG_LIST is a JSON-encoded array of strings; be tolerant of weirdness."""
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(t) for t in raw if t]
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(t) for t in parsed if t]
        except json.JSONDecodeError:
            pass
    return []


# ----- registry --------------------------------------------------------------

FLATTENER_REGISTRY: dict[str, dict[str, Any]] = {
    "cr_tickets": {
        "pipeline_version": CR_PIPELINE_VERSION,
        "iter_sources": iter_cr_tickets,
        "flatten": flatten_cr_ticket,
        "chunker_name": "noop",
        "corpus_dir_name": "cr_tickets",
    },
    "support_tickets": {
        "pipeline_version": SUPPORT_PIPELINE_VERSION,
        "iter_sources": iter_support_tickets,
        "flatten": flatten_support_ticket,
        "chunker_name": "noop",
        "corpus_dir_name": "support_tickets",
    },
    "call_transcripts": {
        "pipeline_version": "call:v1;chunker=window20_stride18_min200",
        "iter_sources": None,  # filled below
        "flatten": None,       # filled below
        "chunker_name": "utterance_window",
        "corpus_dir_name": "call_transcripts",
    },
}


# ----- call_transcripts ------------------------------------------------------


def iter_call_transcripts(corpus_root: Path) -> Iterator[Path]:
    """Yield every `transcript.json` under `<account_id>/<YYYYMM>/<recording_id>/`.

    Skips accounts with only `.DS_Store` / text files.
    """
    for account_dir in sorted(corpus_root.iterdir()):
        if not account_dir.is_dir():
            continue
        for month_dir in sorted(account_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for recording_dir in sorted(month_dir.iterdir()):
                if not recording_dir.is_dir():
                    continue
                transcript = recording_dir / "transcript.json"
                if transcript.is_file():
                    yield transcript


def flatten_call_recording(transcript_path: Path) -> LogicalDoc | None:
    """Flatten a single kaia recording folder into a LogicalDoc.

    The returned doc carries the raw utterance list in `raw["utterances"]`
    so `UtteranceWindowChunker` can slice it into chunks.
    """
    recording_dir = transcript_path.parent
    account_dir = recording_dir.parent.parent
    recording_id = recording_dir.name
    recording_path = recording_dir / "recording.json"

    try:
        transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        log.warning("call_transcripts: bad transcript %s: %s", transcript_path, err)
        return None

    rec_meta: dict[str, Any] = {}
    if recording_path.is_file():
        try:
            rec_meta = json.loads(recording_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            log.warning("call_transcripts: bad recording.json %s: %s", recording_path, err)

    attrs = (rec_meta.get("attributes") or {}) if isinstance(rec_meta, dict) else {}
    title = (attrs.get("title") or "").strip()
    participants_raw = attrs.get("participants") or []
    participants_by_id: dict[int | str, dict[str, str]] = {}
    participants_summary: list[dict[str, str]] = []
    for p in participants_raw:
        if not isinstance(p, dict):
            continue
        pid = p.get("inMeetingId")
        name = p.get("displayName") or p.get("firstName") or "Unknown"
        role = p.get("type") or "UNKNOWN"
        if pid is not None:
            participants_by_id[pid] = {"name": name, "role": role}
        participants_summary.append({"name": name, "role": role})

    utterances = transcript.get("utterances") or []

    # Account info
    account_id = account_dir.name
    account_name = ""
    name_txt = account_dir / "name.txt"
    if name_txt.is_file():
        try:
            account_name = name_txt.read_text(encoding="utf-8").strip()
        except OSError:
            account_name = ""

    created_at = attrs.get("createdAt") or ""
    duration_seconds = None
    if attrs.get("mediaDurationSeconds"):
        try:
            duration_seconds = int(float(attrs["mediaDurationSeconds"]))
        except (ValueError, TypeError):
            duration_seconds = None

    parent_id = f"call:{recording_id}"

    metadata: dict[str, Any] = {
        "corpus": "call_transcripts",
        "account_id": account_id,
        "account_name": account_name or None,
        "recording_id": recording_id,
        "call_date": _date_only(created_at),
        "duration_seconds": duration_seconds,
        "participant_count": attrs.get("participantCount"),
        "participants": participants_summary,
        "recording_title": title or None,
        "recording_url": attrs.get("recordingUrl"),
    }

    # `text` here is informational only (a brief header); the chunker rebuilds
    # proper chunk text from `raw["utterances"]`. We still set something so the
    # LogicalDoc is well-formed for inspection / dry-run.
    participants_line = ", ".join(f"{p['name']} [{p['role']}]" for p in participants_summary) or "unknown"
    text_header_lines = [
        title if title else f"recording {recording_id}",
        f"account: {account_name or account_id}",
        f"date: {_date_only(created_at) or 'unknown'}",
        f"participants: {participants_line}",
    ]

    try:
        source_mtime = transcript_path.stat().st_mtime
    except OSError:
        source_mtime = 0.0

    return LogicalDoc(
        parent_id=parent_id,
        title=title or f"recording {recording_id}",
        text="\n".join(text_header_lines),
        metadata=metadata,
        source_path=str(transcript_path),
        source_mtime=source_mtime,
        raw={
            "utterances": utterances,
            "participants_by_id": participants_by_id,
        },
    )


# Wire the kaia entries now that the functions exist.
FLATTENER_REGISTRY["call_transcripts"]["iter_sources"] = iter_call_transcripts
FLATTENER_REGISTRY["call_transcripts"]["flatten"] = flatten_call_recording
