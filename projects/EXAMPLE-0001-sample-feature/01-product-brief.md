---
title: Onboarding checklist for new reps (example)
jira: "PROJECT-0001"
date: 2026-05-19
braindump: example only — fictional feature hub for PM Brain
---

**Author:** Example PM
**Date:** 2026-05-19
**Status:** Proposed
**Ask:** Approval to scope a v1 PRD for the Q3 hiring cohort
**Decision Deadline:** 2026-06-15

> **Example document.** This feature hub demonstrates naming, structure, and how a brief maps section-for-section to `02-templates/product/01-product-brief.md`. Replace the content with your own initiative when you fork.

# A. Overview

**Feature / initiative name:** Onboarding checklist for new reps

**One-line summary:** An in-app onboarding checklist (with manager visibility) that gets new sales reps to consistent activity in ~3 weeks instead of 6–8.

---

# B. What customer pain/problem are we solving?

New sales reps take **6–8 weeks** to reach consistent activity levels. Reps lack a single, in-app sequence of "what to do first"; managers lack a shared view of where each rep is stuck.

The pain is felt most acutely by **new reps in their first 30 days** and their **frontline managers** during ramp. Frequency is daily during ramp (reps unsure what to do next; managers chasing status in Slack), and severity is high enough to delay first outbound activity by weeks.

Evidence is partial: the last "first 30 days" CSAT survey dropped 8 points QoQ, and enablement reports rising 1:1 time from managers. We do **not** have logged-event data on time-to-first-outbound yet — see open question in §E.

Today, reps cobble onboarding together from the wiki, the LMS, and Slack threads. Managers build personal spreadsheets. Some competitors market "time-to-first-meeting" as a differentiator in their pitch decks.

### Impact of not solving

Q3 hiring adds ~40 reps. Without a shared checklist we expect the same 6–8 week ramp, ~6 weeks of lost outbound capacity per rep, and continued manager toil. Competitively, we keep ceding the "fast ramp" narrative.

---

# C. Why should we do this? What are the benefits?

A shorter, more predictable ramp converts directly into earlier pipeline and lower manager overhead. It also gives us a defensible "time-to-first-meeting" talk track that several competitors lead with.

### Why now?

- **Strategic fit:** Aligns with the FY27 platform direction of in-app guidance (vs. external enablement tools).
- **Competitive pressure / market timing:** Two named competitors shipped onboarding flows in the last 6 months.
- **Customer urgency:** Q3 hiring plan adds ~40 reps; CSAT on "first 30 days" dropped last quarter.
- **Opportunity cost:** Waiting one quarter loses the Q3 cohort as our first validation population.

### Expected impact on metrics

| Metric | Current | Target | Confidence (High / Med / Low) |
|--------|---------|--------|--------------------------------|
| Median days to first outbound | [PLACEHOLDER] | −15% vs control | Med |
| Week-4 active rep rate | [PLACEHOLDER] | +10 pts vs control | Med |
| Manager hours on 1:1 onboarding | [PLACEHOLDER] | Decrease (secondary) | Low |

> These rows seed Section 1 of `03-success-metrics.md`. Baselines are placeholders — analytics needs to confirm before we lock targets.

---

# D. What is your high-level proposed approach?

Ship a **rep-facing onboarding checklist** in the primary web app home, plus a **manager summary widget** for team-level visibility. v1 is web-only; mobile and LMS integration deferred.

### What this IS (in scope)

- 10–15 task cards (connect mailbox, complete first workflow, log first customer touchpoint) auto-shown on app home for accounts < 30 days old.
- Task completion persisted server-side; weekly email digest to managers.
- Per-segment task lists (Enterprise vs Starter) configured by admins.

### What this is NOT (out of scope)

- Mobile app surface (defer to v1.1 after adoption signal).
- Slack-based delivery of tasks (rely on email digest for v1).
- LMS / SCORM integration or quizzes.
- Salesforce-driven task triggers.

1. **Key workflow changes:** New reps see the checklist on first login; managers get a weekly digest plus a dashboard widget. No change to existing rep workflows once they pass 30 days.

2. **Major dependencies or constraints:** Reuses existing auth, notifications, and admin console — no new infra. Localization needed for EN/DE/FR at GA.

3. **Assumptions:** Most reps land on `/home` within their first session; admins are willing to maintain segment-level task lists.

---

# E. Risks and open questions

### Risks

| Risk | Likelihood (L/M/H) | Impact (L/M/H) | Mitigation |
|------|--------------------|----------------|------------|
| Checklist feels like busywork; reps dismiss it | M | M | Personalize by role/segment; limit to ≤15 tasks |
| Low manager adoption of digest/widget | M | M | Default-on for new managers; surface in existing dashboard |
| Time-to-first-outbound baseline turns out to be noisy | M | L | Use control-group methodology; revisit targets post-baseline |

### Open questions

- [ ] Default task list for Enterprise vs Starter tier? — Owner: PM, target: 2026-06-30
- [ ] Time-to-first-outbound baseline — what's the actual current median? — Owner: Analytics, target: 2026-06-15

---

# F. Next steps (if approved)

1. Validate task list with 5 managers (interviews) — **Owner:** PM, **By:** 2026-06-15
2. PRD for v1 scope (web only) — **Owner:** PM, **By:** 2026-06-30
3. Target beta with one sales pod — **Owner:** EM, **By:** 2026-07-31
