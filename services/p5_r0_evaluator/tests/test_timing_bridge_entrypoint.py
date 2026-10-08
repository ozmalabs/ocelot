from io import BytesIO
from pathlib import Path
import importlib

import pytest

from services.p5_r0_evaluator.canonical import digest, parse_canonical
from services.p5_r0_evaluator import timing_bridge_entrypoint as entrypoint


def _call(app):
    response = {}

    def start_response(status, headers):
        response["status"] = status
        response["headers"] = dict(headers)

    body = b"{}"
    response["body"] = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/v1/timing",
                "CONTENT_TYPE": "application/json",
                "CONTENT_LENGTH": str(len(body)),
                "wsgi.input": BytesIO(body),
            },
            start_response,
        )
    )
    return response


def test_missing_configuration_keeps_imported_entrypoint_locked(monkeypatch):
    for name in entrypoint._BRIDGE_CONFIG_ENV:
        monkeypatch.delenv(name, raising=False)
    module = importlib.reload(entrypoint)
    response = _call(module.application)
    assert response["status"].startswith("503 ")
    assert parse_canonical(response["body"]) == {
        "error": "service unavailable",
        "schema": "P5R0ErrorV1",
    }
    assert b"traceback" not in response["body"]


def test_oidc_authenticator_binds_exact_audience_and_subject(monkeypatch):
    seen = {}

    class _Verifier:
        def __init__(self, audience, subjects):
            seen["audience"] = audience
            seen["subjects"] = subjects

        def verify(self, authorization):
            seen["authorization"] = authorization
            return "principal"

    monkeypatch.setattr(entrypoint, "GoogleOIDCVerifier", _Verifier)
    authenticate = entrypoint._oidc_authenticator(
        {
            entrypoint.OIDC_AUDIENCE_ENV: "https://bridge.example.test",
            entrypoint.ALLOWED_EVALUATOR_SUBJECT_ENV: "evaluator-subject",
        }
    )
    assert authenticate({"authorization": "Bearer token", "x-p5-authorization": "ignored"}) == "principal"
    assert seen == {
        "audience": "https://bridge.example.test",
        "subjects": {"evaluator-subject"},
        "authorization": "Bearer token",
    }


def test_bootstrap_uses_adc_only_for_explicit_bridge_factory(monkeypatch, tmp_path):
    ca = tmp_path / "freetsa-ca.pem"
    ca.write_bytes(b"reviewed public CA")
    env = {
        "P5R0_BRIDGE_FREETSA_CA_PEM_PATH": str(ca),
        "P5R0_BRIDGE_FREETSA_CA_PEM_SHA256": digest(ca.read_bytes()),
        entrypoint.OIDC_AUDIENCE_ENV: "https://bridge.example.test",
        entrypoint.ALLOWED_EVALUATOR_SUBJECT_ENV: "evaluator-subject",
    }
    seen = {}

    class _Runtime:
        application = lambda environ, start_response: []

    def adc_loader(*, scopes):
        seen["scopes"] = scopes
        return "adc-credentials", "project-id"

    def factory(**kwargs):
        seen["factory"] = kwargs
        return _Runtime()

    monkeypatch.setattr(entrypoint, "create_production_bridge", factory)
    monkeypatch.setattr(entrypoint, "GoogleOIDCVerifier", lambda audience, subjects: object())
    runtime = entrypoint._bootstrap(env, adc_loader=adc_loader)
    assert runtime.application is not None
    assert seen["scopes"] == ["https://www.googleapis.com/auth/cloud-platform"]
    assert seen["factory"]["credentials"] == "adc-credentials"
    assert seen["factory"]["env"] == env
    assert callable(seen["factory"]["authenticator"])


def test_ca_digest_mismatch_fails_before_cloud_bootstrap(tmp_path):
    ca = tmp_path / "freetsa-ca.pem"
    ca.write_bytes(b"reviewed public CA")
    env = {
        "P5R0_BRIDGE_FREETSA_CA_PEM_PATH": str(ca),
        "P5R0_BRIDGE_FREETSA_CA_PEM_SHA256": digest(b"different CA"),
    }
    with pytest.raises(ValueError, match="digest mismatch"):
        entrypoint._verify_ca_pin(env)


def test_bridge_recipe_is_pinned_non_root_and_has_no_build_time_ca_fetch():
    dockerfile = (Path(__file__).parents[1] / "Dockerfile.timing-bridge").read_text()
    assert "FROM python:3.12.8-slim-bookworm@sha256:" in dockerfile
    assert "requirements.txt" in dockerfile
    assert "USER 65532:65532" in dockerfile
    assert "timing_bridge_entrypoint:application" in dockerfile
    assert "P5R0_BRIDGE_FREETSA_CA_PEM_PATH" in dockerfile
    assert "curl" not in dockerfile.lower()
    assert "wget" not in dockerfile.lower()
    assert "private_key" not in dockerfile.lower()
    assert "-----begin" not in dockerfile.lower()
