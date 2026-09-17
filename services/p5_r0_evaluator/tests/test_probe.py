import json
import json
from pathlib import Path

import pytest

from services.cs_attestation_probe import probe


def _claims(image_digest: str) -> dict:
    return {
        "iss": "https://confidentialcomputing.googleapis.com",
        "aud": "probe-audience",
        "sub": "probe-subject",
        "eat_nonce": "nonce-1234",
        "exp": 2_000_000_000,
        "swname": "CONFIDENTIAL_SPACE",
        "swversion": "1",
        "dbgstat": "disabled-since-boot",
        "hwmodel": "GCP_AMD_SEV",
        "secboot": True,
        "submods": {
            "container": {
                "image_digest": image_digest,
                "env": {"P5R0_EXPECTED_WORKLOAD": "evaluator"},
            },
            "gce": {"project_number": "123", "project_id": "project", "zone": "us-central1-a"},
            "confidential_space": {"support_attributes": {"sev": True}},
        },
    }


def test_probe_emits_bounded_non_secret_evidence(monkeypatch, capsys):
    token = "opaque-jwt"
    claims = _claims("sha256:" + "a" * 64)
    monkeypatch.setenv("CS_EXPECTED_IMAGE_DIGEST", "sha256:" + "a" * 64)
    monkeypatch.setenv("CS_ATTESTATION_AUDIENCE", "probe-audience")
    monkeypatch.setenv("CS_ATTESTATION_ISSUER", "https://confidentialcomputing.googleapis.com")
    monkeypatch.setattr(probe, "_nonce", lambda: "nonce-1234")
    monkeypatch.setattr(probe, "fetch_token", lambda **kwargs: token)
    monkeypatch.setattr(probe, "verify_jwt", lambda *args, **kwargs: claims)

    probe.main()

    output = capsys.readouterr().out.encode()
    parsed = json.loads(output)
    assert len(output) <= probe.MAX_EVIDENCE_BYTES + 1
    assert parsed["schema"] == "CSAttestationProbeV1"
    assert parsed["claims"]["expected_image_match"] is True
    assert "opaque-jwt" not in output.decode()
    assert "private_key" not in output.decode()
    assert "token_digest" in parsed["claims"]


def test_probe_defaults_to_google_sts_token_audience(monkeypatch, capsys):
    claims = _claims("sha256:" + "a" * 64)
    claims["aud"] = probe.DEFAULT_WIP_TOKEN_AUDIENCE
    monkeypatch.setenv("CS_EXPECTED_IMAGE_DIGEST", "sha256:" + "a" * 64)
    monkeypatch.delenv("CS_ATTESTATION_AUDIENCE", raising=False)
    monkeypatch.setenv("CS_ATTESTATION_ISSUER", "https://confidentialcomputing.googleapis.com")
    monkeypatch.setattr(probe, "_nonce", lambda: "nonce-1234")
    seen = {}
    monkeypatch.setattr(probe, "fetch_token", lambda **kwargs: seen.update(kwargs) or "jwt")
    monkeypatch.setattr(probe, "verify_jwt", lambda *args, **kwargs: claims)

    probe.main()

    assert seen["audience"] == probe.DEFAULT_WIP_TOKEN_AUDIENCE
    assert json.loads(capsys.readouterr().out)["claims"]["audience"] == probe.DEFAULT_WIP_TOKEN_AUDIENCE


def test_probe_fetches_over_launcher_socket_with_canonical_body(monkeypatch):
    class FakeSocket:
        def settimeout(self, value): assert value == 5
        def connect(self, path): assert path == probe.LAUNCHER_SOCKET
        def sendall(self, data):
            self.request = data
        def recv(self, size):
            body = json.dumps({"token": "jwt"}, separators=(",", ":")).encode()
            response = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
            if not hasattr(self, "sent"):
                self.sent = True
                return response
            return b""
        def close(self): pass

    sock = FakeSocket()
    monkeypatch.setattr(probe.socket, "socket", lambda *args: sock)
    assert probe.fetch_token(audience="aud", nonce="nonce-1234") == "jwt"
    assert sock.request.endswith(b'{"audience":"aud","nonces":["nonce-1234"],"token_type":"OIDC"}')
    assert sock.request.startswith(b"POST /v1/token HTTP/1.1\r\nHost: localhost\r\n")


def test_probe_rejects_oversized_or_mismatched_claims(monkeypatch):
    monkeypatch.setenv("CS_EXPECTED_IMAGE_DIGEST", "sha256:" + "a" * 64)
    monkeypatch.setenv("CS_ATTESTATION_AUDIENCE", "probe-audience")
    monkeypatch.setenv("CS_ATTESTATION_ISSUER", "issuer")
    monkeypatch.setattr(probe, "_nonce", lambda: "nonce-1234")
    monkeypatch.setattr(probe, "fetch_token", lambda **kwargs: "jwt")
    monkeypatch.setattr(probe, "verify_jwt", lambda *args, **kwargs: _claims("sha256:" + "b" * 64))
    with pytest.raises(RuntimeError, match="image digest mismatch"):
        probe.main()

    monkeypatch.setattr(probe, "fetch_token", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("launcher token is too large")))
    with pytest.raises(RuntimeError, match="too large"):
        probe.main()


def test_probe_recipe_is_pinned_minimal_and_non_root():
    dockerfile = (Path(__file__).parents[2] / "cs_attestation_probe" / "Dockerfile").read_text()
    assert "FROM python:3.12.8-slim-bookworm@sha256:" in dockerfile
    assert "COPY probe.py /probe.py" in dockerfile
    assert "USER 65532:65532" in dockerfile
    assert "ENTRYPOINT [\"python3\", \"/probe.py\"]" in dockerfile
    assert "google-auth==2.38.0" in dockerfile
    assert "CS_ATTESTATION_AUDIENCE" in dockerfile
    assert "CS_ATTESTATION_ISSUER" in dockerfile
    assert "truth" not in dockerfile.lower()
