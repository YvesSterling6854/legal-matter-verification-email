import pytest

from legal_signup import InfraiClient, MatterSignup, enroll_matter_signer, main


class RecordingClient(InfraiClient):
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def post(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append((path, payload))
        if path == "/v1/email/send":
            return {"message_id": "mail-204"}
        return {"user_id": "user-204"}


def test_signer_is_created_before_the_verification_message() -> None:
    client = RecordingClient()

    receipt = enroll_matter_signer(
        client,
        MatterSignup("signer@example.com", "MAT-204", "Morgan Lee"),
    )

    assert [path for path, _ in client.calls] == [
        "/v1/auth/user/create",
        "/v1/email/send",
    ]
    assert client.calls[0][1]["metadata"] == {"matter_reference": "MAT-204"}
    assert "Verify email" in str(client.calls[1][1]["html"])
    assert receipt.message_id == "mail-204"


def test_main_requires_explicit_signer_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    monkeypatch.delenv("SIGNER_EMAIL", raising=False)
    with pytest.raises(KeyError, match="SIGNER_EMAIL"):
        main()
