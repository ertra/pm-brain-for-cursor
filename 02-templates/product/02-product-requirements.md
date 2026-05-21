---
title: Product Requirements
jira: "PROJECT-#####"
date: [Date]
---

**Author:** [Your name]
**Status:** Draft | In Review | Approved
**Related docs:** [`01-product-brief.md`](./01-product-brief.md) · [`03-success-metrics.md`](./03-success-metrics.md)

## Summary

> *One paragraph: what we're building, for whom, and the outcome we expect. Pull from the product brief — do not restate the full problem here.*

**Design / visuals:** [Link to Figma, mockups, or prototype — or "pending"]

---

# A. Use cases & requirements

> *List each major user flow or use case below. Describe the requirement, how the user benefits, and link to design elements (Figma) where relevant. Consider:*
>
> - *Out of the box — setup, admin & user experience*
> - *First time user experience — brand new users, first time for existing users*
> - *Admin experience — settings or configurations related to this feature*
> - *Refer to your team's* *[P0–P3 priority definitions]* <!-- TODO: link to your company's priority matrix -->

| # | Feature / use case | User benefit | Priority (P0–P3) | Design link | Notes |
|---|--------------------|--------------|------------------|-------------|-------|
| 1 | [Feature name] | [User benefit] | P0 | [Figma] | |
| 2 | [Feature name] | [User benefit] | P1 | [Figma] | |
| 3 | [Feature name] | [User benefit] | P2 | [Figma] | |

### Detailed requirements

**1. [Feature name]** — *P0*

- Requirement 1
- Requirement 2
- **Acceptance criteria:** [How we'll know it's done]

**2. [Feature name]** — *P1*

- Requirement 1
- Requirement 2
- **Acceptance criteria:** [How we'll know it's done]

---

# B. Experience considerations (Mobile, Email, Slack, Governance, etc.)

> *Consider whether this feature should be integrated into other experiences — Mobile, Email, Slack, browser extension, CRM, governance (admin-controlled), localization, side panels, etc.*
>
> *Also consider whether existing Platform solutions can be leveraged, and how Platform can be expanded to make future features easier to build (API ecosystem, authorization model, initial usage / scaling expectations).*

| Surface / concern | In scope? (Y/N) | Notes |
|-------------------|-----------------|-------|
| Mobile | | |
| Email | | |
| Slack | | |
| Browser extension / embed | | |
| Salesforce | | |
| Governance / admin controls | | |
| Localization | | |
| Accessibility | | |
| Side-panel / narrow views | | |

**Platform reuse / expansion:** [Which existing Platform capabilities (auth, API, context graph, RAG) this feature reuses, and what Platform would need to add.]

---

# C. Reporting considerations (Data sharing, in-app reporting, APIs, CRM sync, Audit, etc.)

> *Consider whether this feature should be included in downstream reporting platforms (Data sharing, in-app reporting, Public APIs, CRM Sync, Audit, AI considerations).*
>
> *Include whether this feature will introduce new data or change existing data — especially for downstream platforms like Lakehouse. As AI and data become increasingly important, treat data changes as a first-class consideration.*

- **New data introduced:** [Yes/No — describe]
- **Changes to existing data:** [Yes/No — describe]
- **Downstream impact:** [Data sharing / Lakehouse / Public APIs / CRM sync / Audit / AI]
- **Retention / PII / governance:** [Notes]

---

# D. Metering (if applicable)

> *Will metering of this functionality be required? What is the system action associated with this feature that would be metered?*
>
> *Reference your company's* *[metering / credits rate sheet]* <!-- TODO: link to internal metering documentation -->

- **Metering required:** [ ] Yes · [ ] No · [ ] Unsure
- **Metered action:** [What system action triggers a metered event]
- **Unit / rate:** [e.g. per call, per doc, per token — or TBD]

---

# E. Monetization intent

> *Does this feature have commercial value that may impact pricing, packaging, or monetization strategy?*
>
> *Reference your company's* *[pricing and packaging map]* <!-- TODO: link to current SKU / tier documentation -->

- [ ] **Yes — monetizable** (new SKU, usage-based, add-on, AI value)
- [ ] **No** — included in existing plans, no pricing / packaging impact
- [ ] **Unsure** — requires discussion with Pricing & Packaging

**If Yes — proposed monetization strategy (1–2 lines):**

[Short description]

---

# F. Open questions

- [ ] [Question 1] — Owner: [Name], target: [Date]
- [ ] [Question 2] — Owner: [Name], target: [Date]
