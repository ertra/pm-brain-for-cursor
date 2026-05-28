# Sequences not sending at their scheduled time

**Miguel Rios (Acme Corporation)** — 2026-03-04 16:20

Hi team,

We are seeing a strange scheduling issue. Sequences scheduled to send at
**9:00 AM CET** are actually firing at **10:00 AM CET** consistently for
the past week. This started right after the daylight-saving-time switch in
Europe.

Examples (account 4400123, user `miguel.rios@acme-example.com`):

- Sequence "EMEA SDR Day 1 — Outbound" — scheduled 09:00, sent 10:01
- Sequence "EMEA Re-engagement — Cooling" — scheduled 09:00, sent 10:02
- Sequence "Renewal — 90 days out" — scheduled 09:00, sent 10:03

Other timezones (US users) are unaffected. It looks like the system is
still applying the old UTC offset for the EMEA region.

This is a problem because prospects open emails in the 9–10 window much
more than after 10. Can you check whether the DST update went through
correctly?

---

**Hannah Lee (Cadenza Support)** — 2026-03-05 09:08

Hi Miguel, thanks — the DST update is the suspected cause. We've identified
a cached timezone offset on the sequence scheduler that did not flip when
DST ended. Engineering is rolling out a fix today and we will rerun the
scheduling for any affected sequences. I'll keep you posted.
