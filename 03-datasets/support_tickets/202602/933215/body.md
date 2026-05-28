# Feature request: audit log UI for admins

**Lukas Berg (Initech)** — 2026-02-18 13:44

Hi,

This is more of a feature request than a bug report.

We need a **UI for admins to browse the audit log** — currently the only way
to investigate who changed what (e.g. who deleted a sequence, who modified
a shared template, who removed a user) is to file a support ticket and ask
your team to pull it from the backend. That is too slow for our security
and compliance reviews.

What we would love:

- Searchable audit log table (by user, action, object type, time window)
- Filter by sensitive actions: user deletions, permission changes, sequence
  deletions, bulk exports
- Export to CSV for our quarterly SOC 2 audits

Right now we have to maintain a separate internal spreadsheet because we
cannot self-serve this in the product, and our security team has flagged it
as a renewal-risk item.

---

**Marek Novak (Cadenza Support)** — 2026-02-19 10:20

Hi Lukas, thanks for the detailed write-up — passing this along to the
product team. I've tagged this with `feature_request` so it shows up in
their review. There is no committed ETA today but I know audit-log
self-serve has come up from other enterprise customers as well.
