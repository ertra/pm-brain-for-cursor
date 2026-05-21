---
title: Onboarding checklist — product requirements (example)
jira: "PROJECT-0001"
date: 2026-05-19
---

**Author:** Example PM
**Status:** Draft
**Related docs:** [`01-product-brief.md`](./01-product-brief.md) · [`03-success-metrics.md`](./03-success-metrics.md)

## Summary

> Example doc — fictional feature hub for PM Brain. Replace with your own initiative.

Ship a **rep-facing onboarding checklist** and a **manager summary** in the primary web app so new reps reach consistent activity in ~3 weeks instead of 6–8. v1 is web-only; mobile and LMS integration are out of scope.

**Design / visuals:** [Figma — pending]

---

# A. Use cases & requirements

| # | Feature / use case | User benefit | Priority (P0–P3) | Design link | Notes |
|---|--------------------|--------------|------------------|-------------|-------|
| 1 | Rep sees checklist on app home after first login | Clear first-day priorities | P0 | [Figma — pending] | Default task list per role |
| 2 | Rep marks tasks complete; progress persists across sessions | Visible momentum | P0 | [Figma — pending] | Auto-save |
| 3 | Manager views team completion % on a dashboard widget | See progress without chasing in Slack | P1 | [Figma — pending] | Team-scoped |
| 4 | Admin configures task list per segment (Enterprise vs Starter) | Tailored onboarding by tier | P2 | [Figma — pending] | Defer to v1.1 if eng-bound |

### Detailed requirements

**1. Rep sees checklist on app home** — *P0*

- Checklist auto-appears for accounts < 30 days old; older accounts can opt in from a banner.
- **Acceptance criteria:** New rep landing on `/home` on first login sees ≥1 task card with title, description, and "Mark complete" CTA within 200ms of page paint.

**2. Rep marks tasks complete; progress persists** — *P0*

- Optimistic UI; server confirms within 500ms or shows retry.
- **Acceptance criteria:** Refreshing the page or logging in from another device shows the same completion state within 2s.

---

# B. Experience considerations (Mobile, Email, Slack, Governance, etc.)

| Surface / concern | In scope? (Y/N) | Notes |
|-------------------|-----------------|-------|
| Mobile | N | v1 web-only; revisit after adoption signal |
| Email | Y | Weekly digest to managers (existing email pipeline) |
| Slack | N | Defer; rely on email digest for v1 |
| Browser extension / embed | N/A | — |
| Salesforce | N | No CRM-driven task completion in v1 |
| Governance / admin controls | Y | Per-tenant feature flag + segment-level task lists |
| Localization | Y | EN/DE/FR strings at GA |
| Accessibility | Y | WCAG 2.1 AA on the checklist surface |
| Side-panel / narrow views | N | Full-width home only |

**Platform reuse / expansion:** Reuses existing auth, notifications, and admin console. No new infra.

---

# C. Reporting considerations (Data sharing, in-app reporting, APIs, CRM sync, Audit, etc.)

- **New data introduced:** Yes — task completion events per rep.
- **Changes to existing data:** No.
- **Downstream impact:** Product analytics (Amplitude); manager dashboard widget.
- **Retention / PII / governance:** Standard rep-level event retention; no new PII categories.

---

# D. Metering (if applicable)

- **Metering required:** No — included in existing rep seat entitlement.
- **Metered action:** N/A.
- **Unit / rate:** N/A.

---

# E. Monetization intent

- [ ] **Yes — monetizable**
- [x] **No** — included in existing plans, no pricing / packaging impact
- [ ] **Unsure**

---

# F. Open questions

- [ ] Default task list for Enterprise vs Starter tier? — Owner: PM, target: TBD
- [ ] Nudge frequency caps to avoid checklist fatigue? — Owner: Design, target: TBD
