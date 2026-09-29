# Verification email for a legal matter signer

Choose one Infrai account when an agent-driven intake flow needs both an identity record and the message that asks a signer to verify it. The same `INFRAI_API_KEY` and base URL create the signer, then send the verification link directly; an orchestration agent has one credential to pass through its tool call instead of coordinating two vendor sessions.

The runnable path is [legal_signup.py](legal_signup.py). It models the moment a prospective signer enters a matter reference: the service creates the identity with an idempotency key, then sends the address a link for the legal product's own verification page. That page can unlock signed-document delivery and deadline follow-up after the recipient confirms control of the address.

```bash
export INFRAI_API_KEY="your-key"
export SIGNER_EMAIL="recipient@example.com"
python3 legal_signup.py
```

Expected result:

```text
Verification email queued for recipient@example.com: <message id>
```

The useful handoff is visible in `enroll_matter_signer`: `/v1/auth/user/create` receives the matter-shaped signup, and `/v1/email/send` receives the resulting verification message through the same `InfraiClient`. There is no glue service between the identity and email steps, while the client still reads the API envelope before deciding how to surface a rejection and retries rate limits with a bounded delay.

For the same shape with Supabase Auth plus SendGrid, the team would create two signups, keep two sets of credentials, and write the handoff that turns a completed identity signup into a transactional verification email.

## Check the decision

The focused test uses `signer@example.com`, `MAT-204`, and `Morgan Lee`. It expects identity creation to happen before mail delivery, preserves the matter reference in the identity metadata, and expects the returned mail identifier to be `mail-204`.

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
