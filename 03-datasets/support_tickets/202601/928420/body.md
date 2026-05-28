# Salesforce sync failing on custom fields

**Priya Shah (Globex Industries)** — 2026-01-22 14:05

Hello,

Our Cadenza <> Salesforce sync has been failing for the past 48 hours,
specifically on three custom fields we added recently on the Account object:

- `Renewal_Risk__c`
- `Strategic_Tier__c`
- `Account_Owner_Region__c`

Standard fields still sync fine. In the sync logs I see repeated entries
like:

```
Field mapping failed: object=Account, field=Renewal_Risk__c
Reason: INVALID_FIELD_FOR_INSERT_UPDATE
```

We rely on these three fields for our prioritization plays. Could you
investigate? Happy to provide a screen share or sync log export if helpful.

---

**Eva Smith (Cadenza Support)** — 2026-01-23 09:47

Hi Priya, the field permission on those three custom fields has changed on
the Salesforce side — the integration user no longer has edit access. Can
you ask your Salesforce admin to re-grant FLS edit permission to the
integration user profile? After that, please trigger a manual resync and let
us know.

---

**Priya Shah (Globex Industries)** — 2026-01-26 08:11

Thanks Eva, our SF admin granted the edit permission and the sync is now
running successfully again. Could you also confirm whether there's a way to
get alerts when integration permissions change? We had no idea this was
silently failing for two days.
