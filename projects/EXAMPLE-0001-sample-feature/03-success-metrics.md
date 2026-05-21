---
title: Onboarding checklist — success metrics (example)
jira: "PROJECT-0001"
date: 2026-05-19
---

**Author:** Example PM
**Status:** Draft
**Related docs:** [`01-product-brief.md`](./01-product-brief.md) · [`02-product-requirements.md`](./02-product-requirements.md)

## Summary

> Example doc — fictional metrics pack for PM Brain. Link your real dashboards in your company's copy.

Drive time-to-first-outbound down by ≥15% and improve week-4 active rep rate by ≥10 points within 90 days post-GA, without regressing manager satisfaction or support load.

**Dashboard link:** [pending]

---

## 1. Business impact metrics

| Metric | Definition | Baseline | Target | Confidence (H/M/L) | Dashboard |
|--------|------------|----------|--------|--------------------|-----------|
| Median days to first outbound (PRD §A use case 1) | Days from rep account creation to first logged outbound | [PLACEHOLDER] | −15% vs control | M | [pending] |
| Week-4 active rep rate (PRD §A use case 1) | % of reps with ≥1 logged outbound in week 4 post-start | [PLACEHOLDER] | +10pts vs control | M | [pending] |

**Guardrail / counter-metrics (should not move negatively):**

- Manager NPS on onboarding — must not drop more than 5 pts vs prior quarter.
- Support tickets tagged "onboarding" — must not increase >10% week-over-week post-GA.

---

## 2. Activation

| Metric | Definition | Baseline | Target | Confidence (H/M/L) | Dashboard |
|--------|------------|----------|--------|--------------------|-----------|
| % new reps opening checklist on day 1 (PRD §A use case 1) | First `onboarding_checklist_viewed` event within 24h of account creation | [PLACEHOLDER] | ≥ 80% | M | [pending] |
| Time-to-first-task-complete | Median time from first checklist view to first task completion | [PLACEHOLDER] | ≤ 24h | L | [pending] |

---

## 3. Adoption

| Metric | Definition | Baseline | Target | Confidence (H/M/L) | Dashboard |
|--------|------------|----------|--------|--------------------|-----------|
| % reps completing all P0 tasks by day 14 (PRD §A use cases 1–2) | All P0 tasks marked complete within 14 days of first login | [PLACEHOLDER] | ≥ 60% | M | [pending] |
| % managers opening team widget weekly (PRD §A use case 3) | At least one `manager_widget_viewed` event per ISO week | [PLACEHOLDER] | ≥ 70% | L | [pending] |

---

## 4. Retention

| Metric | Definition | Baseline | Target | Confidence (H/M/L) | Dashboard |
|--------|------------|----------|--------|--------------------|-----------|
| Week-8 active rep rate | % of reps with ≥1 logged outbound in week 8 post-start | [PLACEHOLDER] | +5pts vs control | L | [pending] |

---

## 5. Proposed new events

<!-- TODO: link to your company's event naming guide -->

| Event name | Source | Description | Key properties | Owner | Jira |
|------------|--------|-------------|----------------|-------|------|
| `onboarding_checklist_viewed` | Amplitude | Rep loads home with the checklist visible | `rep_id`, `day_since_signup`, `tier` | Example PM | PROJECT-0001 |
| `onboarding_task_completed` | Amplitude | Rep marks a task complete | `task_id`, `task_rank`, `rep_id` | Example PM | PROJECT-0001 |
| `manager_widget_viewed` | Amplitude | Manager views team completion widget | `manager_id`, `team_id` | Example PM | PROJECT-0001 |

---

## 6. Open questions

- [ ] Control-group methodology (cohort vs feature flag) — Owner: Analytics, target: TBD
- [ ] How long to run pre-GA holdout before reading targets? — Owner: PM, target: TBD
