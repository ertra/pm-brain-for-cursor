# Outbound emails going to spam after DMARC / DKIM change

**Markus Steiner (Helios Energy)** — 2026-05-06 07:30

URGENT.

We rotated our DKIM key and tightened our DMARC policy to `p=reject` on
Friday night. Since Monday morning, **our cold outbound reply rate has
dropped from around 4.2% to 0.6%** and inbox-placement testing shows our
emails going to spam at Gmail, Outlook, and Yahoo.

We followed the Cadenza deliverability guide step by step:

- Added the Cadenza DKIM record to our DNS
- Verified domain ownership in the admin console
- Updated SPF to include `cadenza.io`
- Set DMARC to `p=reject; rua=mailto:dmarc@helios-example.com`

The DMARC report says alignment is now "fail" for the Cadenza send path,
which is why everything is bouncing to spam. We need this fixed today —
this is blocking 18 reps and we have an investor demo Thursday.

---

**Olivier Bernard (Cadenza Support)** — 2026-05-06 10:12

Hi Markus, this is a DMARC alignment issue specific to the Cadenza
sending domain — when you moved to `p=reject` the existing DKIM signature
from our sending infrastructure no longer aligns with `helios-example.com`.

To fix this you need to add our SPF include and our new DKIM CNAME record
to your DNS. I'm sending the exact records via secure DM now. After DNS
propagates (usually within 1–4 hours) please rerun an inbox placement test.

You can also temporarily move DMARC to `p=quarantine` while DNS propagates
to avoid further bounces.

---

**Markus Steiner (Helios Energy)** — 2026-05-06 16:45

Records added, DMARC temporarily on `p=quarantine`. Will retest at 18:00
UTC. Thanks for the fast turnaround.
