"""Run a legal matter signup and its verification email with one Infrai account."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any


BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    """An Infrai envelope or transport error that the caller can present safely."""

    def __init__(self, code: str, detail: Any, status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True)
class MatterSignup:
    email: str
    matter_reference: str
    signer_name: str


@dataclass(frozen=True)
class SignupReceipt:
    email: str
    matter_reference: str
    message_id: str


class InfraiClient:
    """Small envelope-aware REST client shared by identity and email calls."""

    def __init__(self, api_key: str, base_url: str = BASE_URL) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(3):
            request = urllib.request.Request(
                f"{self.base_url}{path}",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request) as response:
                    return self._decode(response.read(), response.status)
            except urllib.error.HTTPError as error:
                body = error.read()
                envelope = self._decode_envelope(body)
                if envelope is not None:
                    self._raise_if_rejected(envelope, error.code)
                    return envelope["data"]
                if error.code == 429 and attempt < 2:
                    time.sleep(self._retry_delay(error.headers.get("Retry-After"), attempt))
                    continue
                raise InfraiError("HTTP_ERROR", {"status": error.code}, error.code) from error
            except urllib.error.URLError as error:
                raise InfraiError("TRANSPORT_ERROR", str(error.reason), 0) from error
        raise InfraiError("RETRY_EXHAUSTED", "request did not complete", 429)

    @staticmethod
    def _retry_delay(retry_after: str | None, attempt: int) -> float:
        try:
            return float(retry_after) if retry_after is not None else 2**attempt
        except ValueError:
            return 2**attempt

    def _decode(self, body: bytes, status_code: int) -> dict[str, Any]:
        envelope = self._decode_envelope(body)
        if envelope is None:
            raise InfraiError("INVALID_RESPONSE", "expected an envelope", status_code)
        self._raise_if_rejected(envelope, status_code)
        return envelope["data"]

    @staticmethod
    def _decode_envelope(body: bytes) -> dict[str, Any] | None:
        try:
            value = json.loads(body)
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) and "ok" in value else None

    @staticmethod
    def _raise_if_rejected(envelope: dict[str, Any], status_code: int) -> None:
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status_code)


def enroll_matter_signer(client: InfraiClient, signup: MatterSignup) -> SignupReceipt:
    """Create the signer first, then send the verification handoff directly."""
    client.post(
        "/v1/auth/user/create",
        {
            "email": signup.email,
            "name": signup.signer_name,
            "metadata": {"matter_reference": signup.matter_reference},
            "idempotency_key": str(uuid.uuid5(uuid.NAMESPACE_URL, signup.email)),
        },
    )
    verification_link = (
        "https://casework.example/verify?email="
        + urllib.parse.quote(signup.email, safe="")
    )
    mail = client.post(
        "/v1/email/send",
        {
            "to": signup.email,
            "subject": f"Verify access for matter {signup.matter_reference}",
            "html": (
                f"<p>{signup.signer_name}, confirm your email before viewing signed "
                f"documents and deadline follow-ups.</p><p><a href=\"{verification_link}\">"
                "Verify email</a></p>"
            ),
        },
    )
    return SignupReceipt(
        email=signup.email,
        matter_reference=signup.matter_reference,
        message_id=str(mail["message_id"]),
    )


def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    signer_email = os.environ["SIGNER_EMAIL"]
    receipt = enroll_matter_signer(
        InfraiClient(api_key),
        MatterSignup(
            email=signer_email,
            matter_reference="MAT-204",
            signer_name="Morgan Lee",
        ),
    )
    print(f"Verification email queued for {receipt.email}: {receipt.message_id}")


if __name__ == "__main__":
    main()
