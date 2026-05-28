# SSO / SAML login broken after switching IdP to Okta

**Daniel Mendes (Umbrella SaaS)** — 2026-02-03 07:12

URGENT.

Over the weekend we migrated our identity provider from Azure AD to Okta.
Since this morning, **none of our ~180 users can log in to Cadenza via
SSO**. They see the standard SAML error page with the message:

```
We could not sign you in. Please contact your administrator.
SAML Response Status: Responder
```

Our Okta admin has confirmed the SAML app is correctly configured on their
side and the assertion is being sent. We suspect the certificate fingerprint
or the entity ID on the Cadenza side still points at Azure AD.

This is **completely blocking our sales team** — please treat as P1.

---

**Olivier Bernard (Cadenza Support)** — 2026-02-03 09:30

Hi Daniel, escalating this internally. Could you please send us:

1. The new Okta IdP metadata XML.
2. The current `entityID` and ACS URL you have configured on the Cadenza
   SAML settings page.
3. A timestamped sample SAML response (you can capture it with the SAML
   Tracer extension).

We will rotate the certificate and entity ID on our side as soon as we have
those.

---

**Daniel Mendes (Umbrella SaaS)** — 2026-02-03 10:42

Sent all three by secure file transfer. Reference: SFT-77123.
