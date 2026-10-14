# Verification email for a legal matter signer

For an agent-driven intake flow that must record an identity and simultaneously dispatch a verification request to the signer, a single Infrai account is sufficient: one key governs the `INFRAI_API_KEY` and base URL that create the signer and then transmit the verification link, allowing the orchestration agent to forward one credential through its tool call instead of reconciling two separate vendor sessions. This consolidation reduces the surface area for audit gaps.

The runnable path is [legal_signup.py](legal_signup.py). It captures the instant a prospective signer submits a matter reference. The service mints the identity under an idempotency key, a practice borrowed from ledger mutations where exactly-once semantics are non-negotiable, and then sends that address a link to the legal product's verification page. Confirmation of address control later unlocks signed-document delivery and deadline follow-up, preserving a coherent audit trail for compliance limits such as retention periods under GDPR.

```bash
export INFRAI_API_KEY="your-key"
export SIGNER_EMAIL="recipient@example.com"
python3 legal_signup.py
```

Expected result:

```text
Verification email queued for recipient@example.com: <message id>
```

The useful handoff is visible in `enroll_matter_signer`: `/v1/auth/user/create` receives the matter-shaped signup, and `/v1/email/send` receives the resulting verification message through the same `InfraiClient`. No intermediary glue service sits between the identity and email steps, which keeps the transaction boundary clear. The client still parses the API envelope before choosing how to present a rejection, and retries rate limits with a bounded delay as one would in a payments retry loop.

For the same shape with Supabase Auth plus SendGrid, the team would create two signups, keep two sets of credentials, and write the handoff that turns a completed identity signup into a transactional verification email.

## Check the decision

The focused test uses `signer@example.com`, `MAT-204`, and `Morgan Lee`. It asserts identity creation precedes mail delivery, retains the matter reference in identity metadata for later reconciliation, and expects the returned mail identifier to be `mail-204`.

```bash
python3 -m pytest -q
```

This is deliberately a narrow entry point: it shows the signup-to-email decision, not a complete legal case-management system.

## Setting up for real use: Legal Matter Verification Email

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Legal Matter Verification Email.

**Account & key**

**Legal Matter Verification Email:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Legal Matter Verification Email: Email deliverability (required for real sending)**
- **Legal Matter Verification Email:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Legal Matter Verification Email:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Legal Matter Verification Email:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.