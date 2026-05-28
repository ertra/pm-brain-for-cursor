#!/usr/bin/env python3
"""Support tickets retrieval helper: tag-derived incidence flags + date filter.

Wraps `query.run_query` for the `support_tickets` corpus and adds a small set of
incidence flags derived from `metadata.tags`. Pure post-processing — no DB
roundtrip beyond what `run_query` already does.

Per-result `incidence` block:
  * is_internal_triage   bool  — CSR-only / silent solve / triage skip
  * business_impact      str?  — "P1".."P4" (highest severity wins) or null
  * is_followup          bool  — `followup_ticket` tag present
  * is_feature_request   bool  — `feature_request` tag present
  * support_topics       list  — `support_topic_*` suffixes
  * end_user_topics      list  — `end_user_topic_*` suffixes
  * support_resolution   str?  — first `support_resolution_*` suffix
  * crm_topic            str?  — first `crm_topic_*` suffix
  * customer_status      str?  — first `customer_status_*` suffix

Top-level `incidence_summary`:
  results_returned, internal_triage_count, by_business_impact (P1..P4 + none),
  feature_request_count, followup_count, internal_triage_pct.

`--created-from / --created-to YYYY-MM-DD` filter on `metadata.created_at`
(inclusive, day-level). Mirrors the call_transcripts call-date design: applied
post-retrieval, with `--k` widened automatically to reduce empty result sets.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from _tools.query import (  # noqa: E402
    _metadata_date_in_range,
    _parse_iso_date_arg,
    run_query,
)

_INTERNAL_TRIAGE_TAGS = frozenset({
    "icr_internal_note",
    "silent_solve",
    "forethought_support_triage_skip",
})

# Severity rank: lower index = more severe. Highest severity wins when multiple
# `agent_business_impact_p*` tags coexist.
_BUSINESS_IMPACT_RANK = ("p1", "p2", "p3", "p4")

# Heuristic candidate-pool widening when a created_at filter is active. Mirrors
# the call_transcripts call-date widening in query.py; kept here as separate constants
# because the right knobs may differ per corpus over time.
_DATE_FILTER_K_MULTIPLIER = 40
_DATE_FILTER_K_FLOOR = 800


def _tags(md: dict[str, Any]) -> list[str]:
    raw = md.get("tags") or []
    return [str(t).lower() for t in raw if t]


def is_internal_triage(tags: list[str]) -> bool:
    return any(t in _INTERNAL_TRIAGE_TAGS for t in tags)


def business_impact(tags: list[str]) -> str | None:
    for level in _BUSINESS_IMPACT_RANK:
        if f"agent_business_impact_{level}" in tags:
            return level.upper()
    return None


def has_tag(tags: list[str], name: str) -> bool:
    return name in tags


def tag_suffix_first(tags: list[str], prefix: str) -> str | None:
    plen = len(prefix)
    for t in tags:
        if t.startswith(prefix) and len(t) > plen:
            return t[plen:]
    return None


def tag_suffix_all(tags: list[str], prefix: str) -> list[str]:
    plen = len(prefix)
    out: list[str] = []
    seen: set[str] = set()
    for t in tags:
        if t.startswith(prefix) and len(t) > plen:
            suffix = t[plen:]
            if suffix not in seen:
                out.append(suffix)
                seen.add(suffix)
    return out


def derive_incidence(md: dict[str, Any]) -> dict[str, Any]:
    tags = _tags(md)
    return {
        "is_internal_triage": is_internal_triage(tags),
        "business_impact": business_impact(tags),
        "is_followup": has_tag(tags, "followup_ticket"),
        "is_feature_request": has_tag(tags, "feature_request"),
        "support_topics": tag_suffix_all(tags, "support_topic_"),
        "end_user_topics": tag_suffix_all(tags, "end_user_topic_"),
        "support_resolution": tag_suffix_first(tags, "support_resolution_"),
        "crm_topic": tag_suffix_first(tags, "crm_topic_"),
        "customer_status": tag_suffix_first(tags, "customer_status_"),
    }


def _compute_incidence_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Tally summary fields from rows that already carry an `incidence` block.

    Always re-derived from the current results; the caller is responsible for
    ensuring each row has been enriched.
    """
    by_impact: dict[str, int] = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "none": 0}
    triage_n = 0
    feature_n = 0
    followup_n = 0
    for rec in results:
        inc = rec.get("incidence") or {}
        if inc.get("is_internal_triage"):
            triage_n += 1
        if inc.get("is_feature_request"):
            feature_n += 1
        if inc.get("is_followup"):
            followup_n += 1
        impact = inc.get("business_impact") or "none"
        by_impact[impact] = by_impact.get(impact, 0) + 1

    n = len(results)
    return {
        "results_returned": n,
        "internal_triage_count": triage_n,
        "by_business_impact": by_impact,
        "feature_request_count": feature_n,
        "followup_count": followup_n,
        "internal_triage_pct": (round(triage_n / n, 4) if n else 0.0),
    }


def enrich_support_incidence(
    payload: dict[str, Any],
    *,
    corpus: str,
) -> dict[str, Any]:
    """Add per-result `incidence` block + top-level `incidence_summary`."""
    if corpus != "support_tickets":
        payload["incidence_note"] = (
            "support_incidence only applies to support_tickets"
        )
        return payload

    results = payload.get("results") or []
    for rec in results:
        rec["incidence"] = derive_incidence(rec.get("metadata") or {})

    payload["incidence_summary"] = _compute_incidence_summary(results)
    return payload


def guard_corpus_for_created_at(
    corpus: str,
    *,
    created_from: str | None,
    created_to: str | None,
) -> str | None:
    """Return an error message if the date filter is incompatible with corpus.

    `--created-from / --created-to` reads `metadata.created_at`, which only
    `support_tickets` records carry in this layout. Using the filter on any
    other corpus would silently drop every row (fail-closed in the date
    helper); reject up front instead.
    """
    if (created_from or created_to) and corpus != "support_tickets":
        return (
            "--created-from / --created-to are only supported for corpus "
            f"'support_tickets' (received corpus={corpus!r}); other corpora do "
            "not store metadata.created_at in the expected shape."
        )
    try:
        _parse_iso_date_arg(created_from)
        _parse_iso_date_arg(created_to)
    except RuntimeError as err:
        return str(err)
    return None


def _apply_created_at_filter(
    payload: dict[str, Any],
    *,
    created_from: str | None,
    created_to: str | None,
) -> dict[str, Any]:
    d_from = _parse_iso_date_arg(created_from)
    d_to = _parse_iso_date_arg(created_to)
    if d_from is None and d_to is None:
        return payload
    results = payload.get("results") or []
    before = len(results)
    kept = [
        r for r in results
        if _metadata_date_in_range(
            r.get("metadata") or {},
            field="created_at",
            d_from=d_from,
            d_to=d_to,
        )
    ]
    payload["results"] = kept
    after = len(kept)
    payload.setdefault("filters", {}).update({
        "created_from": created_from,
        "created_to": created_to,
        "candidates_before_date_filter": before,
        "candidates_after_date_filter": after,
    })
    return payload


def _apply_exclude_internal_triage(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop rows flagged is_internal_triage=true; re-tally summary + filters.

    The summary is fully recomputed from the surviving rows so every field
    (including `by_business_impact`, `feature_request_count`, `followup_count`)
    reflects what is actually in `results`. The pre-exclusion population is
    recoverable by re-running without `--exclude-internal-triage`.
    """
    results = payload.get("results") or []
    before = len(results)
    kept = [
        r for r in results
        if not (r.get("incidence") or {}).get("is_internal_triage")
    ]
    payload["results"] = kept
    if "incidence_summary" in payload:
        payload["incidence_summary"] = _compute_incidence_summary(kept)
    payload.setdefault("filters", {})["excluded_internal_triage"] = before - len(kept)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "support_tickets keyword/hybrid search with tag-derived incidence "
            "flags and an optional created_at date filter."
        ),
    )
    ap.add_argument("--corpus", default="support_tickets",
                    help="Corpus name (default: support_tickets).")
    ap.add_argument("--k", type=int, default=20, help="Top-K results.")
    ap.add_argument("--mode", choices=["hybrid", "vector", "keyword"], default="keyword",
                    help="Retrieval mode (default keyword for the large support index).")
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
        "--created-from",
        default=None,
        metavar="YYYY-MM-DD",
        help="Drop tickets whose metadata.created_at is before this day (inclusive).",
    )
    ap.add_argument(
        "--created-to",
        default=None,
        metavar="YYYY-MM-DD",
        help="Drop tickets whose metadata.created_at is after this day (inclusive).",
    )
    ap.add_argument(
        "--exclude-internal-triage",
        action="store_true",
        help=(
            "After enrichment, drop rows flagged is_internal_triage=true. "
            "Requires the default tag enrichment (cannot be combined with "
            "--no-incidence-enrich)."
        ),
    )
    ap.add_argument(
        "--no-incidence-enrich",
        action="store_true",
        help="Skip tag-derived incidence annotation (raw query output only).",
    )
    ap.add_argument("question", nargs="+", help="Search question / keywords.")
    args = ap.parse_args()

    if args.exclude_internal_triage and args.no_incidence_enrich:
        print(json.dumps({
            "error": (
                "--exclude-internal-triage requires the default tag enrichment; "
                "drop --no-incidence-enrich or omit --exclude-internal-triage."
            ),
        }, ensure_ascii=False))
        return 2

    guard_err = guard_corpus_for_created_at(
        args.corpus,
        created_from=args.created_from,
        created_to=args.created_to,
    )
    if guard_err:
        print(json.dumps({"error": guard_err}, ensure_ascii=False))
        return 2

    question = " ".join(args.question)

    # Widen retrieval when a created_at filter is active so post-hoc filtering
    # still yields ~k rows even for narrow date windows. Same heuristic shape
    # as the call_transcripts call-date widening in query.py.
    date_filter_active = bool(args.created_from or args.created_to)
    k_for_query = (
        max(args.k * _DATE_FILTER_K_MULTIPLIER, _DATE_FILTER_K_FLOOR)
        if date_filter_active else args.k
    )

    try:
        out = run_query(
            corpus=args.corpus,
            question=question,
            k=k_for_query,
            mode=args.mode,
            min_score=args.min_score,
            group_by_parent=args.group,
            provider=args.provider,
            model=args.model,
            topic=args.topic,
        )
    except (FileNotFoundError, RuntimeError) as err:
        print(json.dumps({"error": str(err)}, ensure_ascii=False))
        return 2

    if date_filter_active:
        out = _apply_created_at_filter(
            out,
            created_from=args.created_from,
            created_to=args.created_to,
        )
        # Truncate back to the user-requested k after date filtering, before
        # enrichment, so summary counts reflect what's actually emitted.
        if len(out.get("results") or []) > args.k:
            out["results"] = out["results"][: args.k]

    if not args.no_incidence_enrich:
        out = enrich_support_incidence(out, corpus=args.corpus)

    if args.exclude_internal_triage:
        out = _apply_exclude_internal_triage(out)

    try:
        json.dump(out, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    except BrokenPipeError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
