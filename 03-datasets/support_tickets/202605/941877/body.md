# Bulk CSV import failing on European characters

**Sofia Mendez (Quantum Logistics)** — 2026-05-14 12:15

Hi,

I'm trying to bulk-import a list of 8,300 prospects exported from our
internal CRM. The Cadenza UI accepts the file, but the import fails
silently for around 600 rows. Looking at the failed records, they all
contain accented or non-ASCII characters in names or companies:

- `Müller GmbH`
- `Hôtel-Dieu`
- `Plzeňské Energetické`
- `Ångström AB`

The CSV is saved as UTF-8 (I confirmed with `file -I` on macOS, returns
`charset=utf-8`). When I open the failed-records report from the Cadenza
import wizard, the affected names show up as garbled mojibake like
`MÃ¼ller GmbH`.

It looks like the import is decoding UTF-8 as Latin-1 somewhere in the
pipeline. Could you check?

We are about 70% of our pilot rollout this week and not being able to
import European prospects properly is annoying — we have to manually
re-enter them.

---

**Marek Novak (Cadenza Support)** — 2026-05-14 17:50

Hi Sofia, you're right — there is a known issue where the import wizard
defaults to Latin-1 when no `;` separator is detected (CSV exports from
older Excel versions). The fix in your case is to either:

1. Re-export from your CRM with explicit `BOM` headers (Excel-compatible
   UTF-8), or
2. Use the admin bulk-import endpoint via the API where you can specify
   the encoding explicitly with `--encoding utf-8`.

I attached a small Python script that takes your current CSV and writes
out the BOM version. After re-uploading, the previously-failed rows
should import cleanly.

We have a longer-term fix planned to auto-detect UTF-8 in the wizard, but
no committed ETA yet.
