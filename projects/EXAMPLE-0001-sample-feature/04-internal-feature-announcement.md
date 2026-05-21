---
title: "Onboarding checklist for new reps — Internal Feature Announcement (example)"
jira: "PROJECT-0001"
date: 2026-05-19
audience: Internal only
source: example only — fictional feature hub for PM Brain
---

> **INTERNAL USE ONLY** — Example document. Replace with your own initiative when you fork.

# Onboarding checklist for new reps

**Related docs:** [`01-product-brief.md`](./01-product-brief.md) · [`02-product-requirements.md`](./02-product-requirements.md) · [`03-success-metrics.md`](./03-success-metrics.md)

**Internal Feature Announcement & Product Documentation**

| | |
|---|---|
| **Roadmap item** | [PROJECT-0001 in tracker](https://example.com/tracker/PROJECT-0001) |
| **Alpha** | TBD |
| **Private beta** | 2026-08-01 (target) |
| **GA** | 2026-09-15 (target) |

**Key contacts**

| Role | Name |
|------|------|
| PM | Example PM |
| EM | Example EM |
| PMM | Example PMM |

## Slack announcement

New reps now get an in-app onboarding checklist on the web home, with manager visibility through a weekly digest and dashboard widget. v1 is web-only; mobile and Slack delivery deferred. PRD pack and metrics: see Related docs above. Questions to Example PM in `#proj-onboarding-checklist`.

---

## Feature overview

### What is it?

A guided checklist that appears on the primary web app home for the first 30 days of a rep's account. Reps tick off setup tasks (mailbox, first workflow, first customer touchpoint); managers see team-level completion in a dashboard widget and a weekly email digest.

### Why did we build it? What problems are we solving, and for whom?

New sales reps take 6–8 weeks to reach consistent activity because onboarding content is scattered across the wiki, LMS, and Slack, and managers have no shared view of where each rep is stuck. The checklist gives reps a single in-app sequence and gives managers passive visibility — targeting Q3 hiring cohorts first.

### Top 2–3 use cases

1. Rep sees checklist on app home after first login and works through P0 tasks at their own pace.
2. Rep marks tasks complete; progress persists across sessions and devices.
3. Manager views team completion percentage on a dashboard widget without chasing reps in Slack.

---

## Feature details

### Image(s)

Figma — pending. Final screenshots to be attached before beta sign-off.

### Key capabilities

- Auto-shown checklist on `/home` for accounts < 30 days old; older accounts can opt in via banner.
- Optimistic UI on task completion; server confirms within 500ms.
- Per-segment task lists (Enterprise vs Starter) configured by admins.
- Manager dashboard widget with team completion % (team-scoped).
- Weekly email digest to managers via existing email pipeline.

### Product differentiation

Workarounds today: wiki + LMS + Slack threads + personal manager spreadsheets. Two named competitors have shipped onboarding flows in the last 6 months; our differentiator is in-app placement on the primary web home (no separate app to open) plus reuse of existing admin segmenting.

### How it works

On first web login, a new rep sees the checklist card stack on `/home`. Each card has a title, short description, and "Mark complete" CTA. Completion state syncs server-side and is visible to the rep's manager (aggregated, not per-task) via the team dashboard widget and the weekly digest email.

### How to configure

- **Admins:** Enable the feature flag for the tenant; define the task list per segment (Enterprise vs Starter) in the admin console.
- **Managers:** No setup; widget appears automatically once at least one rep on the team has the checklist active.
- **Reps:** No setup; checklist appears on first login.

---

## Internal context

### Phased rollout

| Phase | Scope | Availability |
|-------|--------|--------------|
| Internal alpha | One internal sales pod | TBD |
| Private beta | 2–3 design-partner customers, Enterprise tier | 2026-08-01 (target) |
| GA | All tenants with rep seats | 2026-09-15 (target) |

### Limitations / dependencies

- v1 is **web-only** — no mobile app surface, no Slack delivery.
- Localization at GA: EN / DE / FR only; other locales follow in v1.1.
- No Salesforce-driven task triggers in v1.
- Depends on existing notifications service for the manager digest email.

### Metric calculations

Time-to-first-outbound and week-4 active rep rate are defined in `03-success-metrics.md` §1 and powered by the new events listed in §5. Baselines are placeholder until Analytics confirms — see `03-success-metrics.md` §6.

---

## Release notes (external) — PM deliverable

**Summary**

New sales reps now get a built-in onboarding checklist on the web home for their first 30 days, helping them get to first outbound activity faster. Managers can see team progress at a glance without chasing status.

**Details**

- In-app checklist with tasks like connecting your mailbox, completing your first workflow, and logging your first customer touchpoint.
- Progress saves automatically and stays in sync across sessions and devices.
- Managers see team completion in a dashboard widget and a weekly summary email.
- Admins can tailor the task list per customer segment.
- Available in the web app today; mobile coming in a future release.

---

## Frequently asked questions — PM deliverable

### Question 1 — When does the checklist appear, and to whom?

The checklist appears automatically on the web app home for any rep whose account is less than 30 days old. Reps with older accounts can opt in from a banner.

### Question 2 — Can my admin change which tasks reps see?

Yes. Admins can configure the task list per segment (e.g. Enterprise vs Starter) from the admin console. Changes take effect for reps on the next page load.

### Question 3 — How do managers see progress?

Managers see team completion on a dashboard widget in the web app and in a weekly email digest. The widget shows aggregate completion percentage, not per-task detail.

### Question 4 — Is this available on mobile or in Slack?

Not in v1. The first release is web-only. Mobile and Slack delivery are being evaluated for a future release.

---

### Example (illustrative)

**Question —** Will dismissing a task remove it permanently?

**Answer —** No. Tasks remain in the checklist until they are marked complete. If a rep accidentally dismisses the card, the task reappears on the next page load.

*(Replace this example with FAQs specific to your feature.)*
