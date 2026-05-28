# Partner integration hitting REST API rate limit on bulk pull

**Vikram Iyer (Globex Industries)** — 2026-04-09 08:55

Hi team,

Our internal data warehouse pulls a daily snapshot of prospect activity from
the Cadenza REST API for our BI dashboards. Since yesterday morning we are
hitting a `429 Too Many Requests` response repeatedly:

```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 0
Retry-After: 60
```

We pull about 1.2 million records per day and we did not change anything on
our side. Was the rate limit lowered recently, or is there a way to request
a higher tier for partner integrations?

We need this resolved by end of week — our BI dashboards are out of date
and our sales leaders are starting to ask.

---

**Eva Smith (Cadenza Support)** — 2026-04-09 14:30

Hi Vikram, the global default was lowered for the public REST API last
week to protect platform health. For partner integrations like yours we
offer an elevated quota — I'm submitting the request now. Could you share:

1. Your OAuth application ID and integration name
2. Expected daily request volume (you mentioned ~1.2M; is that steady?)
3. The time window your daily snapshot runs in

We typically approve elevated quotas within 24–48 hours for existing
customers.

---

**Vikram Iyer (Globex Industries)** — 2026-04-10 13:12

Thanks Eva, replied to your DM with the details. The 1.2M is steady, give
or take 10%. The job runs between 02:00 and 04:00 UTC.

Also — would it make sense to switch this to the bulk export endpoint
instead of paginated pulls? We saw it mentioned in the changelog last
month.
