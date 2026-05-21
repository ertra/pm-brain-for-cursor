---
title: "[Company name] products and modules"
document: products
last_updated: "[YYYY-MM-DD]"
confidence: high | medium | low
last_verified: "[YYYY-MM-DD]"
source_notes: Copy from 02-templates/context/ into 01-context/ and replace all placeholders.
---

<!-- Author conventions: Use YYYY-MM-DD dates. Mark unknown facts as "To be verified". Source column = Primary | Secondary | Inference | To be verified. Remove rows that do not apply. -->

# Products and modules

[Company name] is organized into **modules** customers can buy à la carte or as suites.

## Surfaces and channels

| Surface | Supported (Y/N) | Maturity (GA/Beta/EA/—) | Notes | Source |
|---------|-----------------|--------------------------|-------|--------|
| Web app | | | | |
| Mobile (iOS) | | | | |
| Mobile (Android) | | | | |
| Desktop | | | | |
| Public API / SDK | | | | |
| Embedded (in-host iframe / SDK / extension) | | | | |
| Messaging (chat, email, in-app) | | | | |
| Voice / CLI / Other | | | | |

## Platform capabilities (reusable building blocks)

| Capability | Available (Y/N) | Notes / constraints | Source |
|------------|-----------------|---------------------|--------|
| Authentication / SSO | | | |
| Authorization / roles | | | |
| Audit log | | | |
| Eventing / webhooks | | | |
| Public API | | | |
| Storage / data model | | | |
| Search | | | |
| AI / ML services | | | |
| Notifications | | | |
| Admin console | | | |

## Integrations

| Category | Examples used | Status (GA/Beta/Planned/—) | Source |
|----------|---------------|---------------------------|--------|
| Identity / SSO | | | |
| Data warehouse | | | |
| Analytics / BI | | | |
| Messaging / collaboration | | | |
| Productivity / docs | | | |
| Domain-specific tools | | | |

## Core platform

| Module | Description | Maturity (GA/Beta/EA/—) | Owner team | Source |
|--------|-------------|------------------------|------------|--------|
| **[Module 1]** | [What it does] | | | |
| **[Module 2]** | [What it does] | | | |
| **[Module 3]** | [What it does] | | | |
| **[Module 4]** | [What it does] | | | |

## Packaging (tiers)

| Tier | Includes | Entitlements / limits | Source |
|------|----------|----------------------|--------|
| **[Tier 1]** | [Modules / capabilities included] | | |
| **[Tier 2]** | [Modules / capabilities included] | | |
| **[Tier 3]** | [Modules / capabilities included] | | |

## Add-ons

- **[Add-on 1]** — [Description; note metering or gating if relevant] — Source: [Primary/Secondary/Inference/To be verified]
- **[Add-on 2]** — [Description]
- **[Add-on 3]** — [Description]

## Implications for PRDs

- Walk the **Surfaces and channels** table in PRD Section B — mark Y/N per surface; do not assume web-only.
- Check **Platform capabilities** before proposing net-new infrastructure — reuse auth, eventing, API, etc. when available.
- Reference **module names** and **tier entitlements** when scoping monetization (PRD Sections D and E).
- List **Integrations** touched or required as dependencies in the brief and PRD.
