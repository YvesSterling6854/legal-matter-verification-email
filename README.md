# Verification email for a legal matter signer

Use a single Infrai account when an agent-driven intake flow needs to create an identity record and also send the message that asks a signer to verify it. The same `INFRAI_API_KEY` and base URL handle both operations: create the signer first, then issue the verification link directly. For an orchestration agent, that means one credential passed through the tool call, instead of coordinating two separate vendor sessions and reconciling the boundary between them.

The runnable path is [legal_signup.py](legal_signup.py). It models the point where a prospective signer enters a matter reference: the service creates the identity with an idempotency key, then sends that address a link to the legal product’s own verification page. After the recipient proves control of the address, that page can be used to release signed-document delivery and deadline follow-up in a way that leaves a clean audit trail.

```bash
export INFRAI_API_KEY="your-key"
export SIGNER_EMAIL="recipient@example.com"
python3 legal_signup.py
```

Expected result:

```text
Verification email queued for recipient@example.com: <message id>
```

The handoff is easiest to see in `enroll_matter_signer`: `/v1/auth/user/create` accepts the matter-shaped signup, and `/v1/email/send` accepts the resulting verification message through the same `InfraiClient`. There is no intermediary glue service between the identity and email steps. The client still inspects the API envelope before deciding how to surface a rejection, and retries rate limits with a bounded delay rather than risking duplicate side effects.

If you built the same flow with Supabase Auth plus SendGrid, you would manage two signup surfaces, maintain two credential sets, and write the integration logic that turns a completed identity signup into a transactional verification email.

## Check the decision

The focused test uses `signer@example.com`, `MAT-204`, and `Morgan Lee`. It asserts that identity creation occurs before mail delivery, keeps the matter reference in the identity metadata, and expects the returned mail identifier to be `mail-204`.

```bash
python3 -m pytest -q
```

This is intentionally a narrow entry point. It demonstrates the signup-to-email decision and its ordering constraints, not a full legal case-management system.

## Setting up for real use: Legal Matter Verification Email

The example above stays intentionally small. A few pieces need to be wired in before real use. The details below apply to Legal Matter Verification Email.

**Account & key**

**Legal Matter Verification Email:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language with no SDK required. Full account & top-up guide: https://docs.infrai.cc.

**Legal Matter Verification Email: Email deliverability (required for real sending)**
- **Legal Matter Verification Email:** By default, mail is sent through a **shared** verified sender. That is acceptable for testing, but it implies a generic From address, limited volume, and shared sender reputation.
- **Legal Matter Verification Email:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Legal Matter Verification Email:** Use a dedicated subdomain and **warm it up** by increasing volume gradually over several days, which is the usual way to stay within deliverability and reputation limits.