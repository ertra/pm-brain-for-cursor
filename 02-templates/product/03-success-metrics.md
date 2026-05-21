---
title: Success Metrics
jira: "PROJECT-#####"
date: [Date]
---

**Author:** [Your name]
**Status:** Draft | In Review | Approved
**Related docs:** [`01-product-brief.md`](./01-product-brief.md) · [`02-product-requirements.md`](./02-product-requirements.md)

## Summary

> *One paragraph: what outcomes this feature is expected to drive, and how we'll know. Anchor business impact to the brief (`01-product-brief.md` Section C) and tie each metric back to a use case in the PRD (`02-product-requirements.md` Section A).*

> *Follow your team's* *[how-to: create a feature dashboard and link to PRD]* <!-- TODO: link to your metrics dashboard guide --> *so dashboards stay standard across features.*

**Dashboard link:** [URL to the feature dashboard, or "pending"]

---

## 1. Business impact metrics

> *How does this feature impact the business? (e.g. drive new users to the platform, improve NPS, increase revenue by X%, reduce admin toil.)*
>
> *Also note any metrics this feature should **not** impact — guardrail / counter-metrics.*

| Metric | Definition | Baseline | Target | Confidence (H/M/L) | Dashboard |
|--------|------------|----------|--------|--------------------|-----------|
| [Metric 1] | [How it's calculated] | [Baseline or PLACEHOLDER] | [Target] | | |
| [Metric 2] | [How it's calculated] | [Baseline or PLACEHOLDER] | [Target] | | |

**Guardrail / counter-metrics (should not move negatively):**

- [Metric] — [Why it matters]

---

## 2. Activation

> *Activation = users quickly reach a meaningful first outcome. Measures a user's ability to discover, set up, and start using the feature effectively (e.g. time-to-first-approved-pack, % of eligible admins who complete setup within 7 days).*

| Metric | Definition | Baseline | Target | Confidence (H/M/L) | Dashboard |
|--------|------------|----------|--------|--------------------|-----------|
| [Metric 1] | | [Baseline or PLACEHOLDER] | [Target] | | |
| [Metric 2] | | | | | |

---

## 3. Adoption

> *Adoption = users engage with the feature regularly, proving it solves a real need (e.g. WAU, WAO, MAO, MAU, runs per active admin, % of orgs with an approved pack in use by agents).*

| Metric | Definition | Baseline | Target | Confidence (H/M/L) | Dashboard |
|--------|------------|----------|--------|--------------------|-----------|
| [Metric 1] | | | | | |
| [Metric 2] | | | | | |

---

## 4. Retention

> *Retention = the feature keeps bringing users back because it provides ongoing value (e.g. week-3 return rate, month-over-month active admins, pack-refresh rate).*

| Metric | Definition | Baseline | Target | Confidence (H/M/L) | Dashboard |
|--------|------------|----------|--------|--------------------|-----------|
| [Metric 1] | | | | | |
| [Metric 2] | | | | | |

---

## 5. Proposed new events

> *New events needed to power the metrics above, from any source (Snowflake, Amplitude, internal APIs, other telemetry).*
>
> *If using product analytics (e.g. Amplitude, Mixpanel), follow your team's* *[event naming best practices]* <!-- TODO: link to analytics naming guide --> *so metric names stay concise and aggregatable.*

| Event name | Source | Description | Key properties | Owner | Jira |
|------------|--------|-------------|----------------|-------|------|
| [event_name] | Analytics / warehouse / API | [What it captures] | [prop_a, prop_b] | [Name] | PROJECT-##### |

---

## 6. Open questions

- [ ] [Question 1] — Owner: [Name], target: [Date]
- [ ] [Question 2] — Owner: [Name], target: [Date]
