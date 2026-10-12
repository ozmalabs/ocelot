from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.p5_r0_evaluator.canonical import b64encode, canonical_bytes, digest
from services.p5_r0_evaluator.confidential_space import FederatedAccessToken
from services.p5_r0_evaluator.rfc3161 import FREETSA_ENDPOINT, FREETSA_POLICY_OID
from services.p5_r0_evaluator.timing import TimingAuthorityConfig
from services.p5_r0_evaluator.timing_bridge_auth import (
    IAMCredentialsIDTokenFactory,
    IAM_CREDENTIALS_ENDPOINT,
)
from services.p5_r0_evaluator.timing_bridge_production import (
    BridgeKMSEd25519Signer,
    BridgeProductionConfig,
    GCSDurableTimingBridgeLedger,
    TimingBridgeProductionError,
)


class _NotFound(Exception):
    code = 404


class _Blob:
    def __init__(self, name):
        self.name = name
        self.data = None
        self.generation = None

    def reload(self):
        if self.data is None:
            raise _NotFound()

    def download_as_bytes(self):
        return self.data

    def upload_from_string(self, data, **kwargs):
        expected = kwargs["if_generation_match"]
        actual = 0 if self.generation is None else self.generation
        if expected != actual:
            raise RuntimeError("precondition failed")
        self.data = bytes(data)
        self.generation = actual + 1


class _Bucket:
    def __init__(self):
        self.objects = {}

    def blob(self, name):
        return self.objects.setdefault(name, _Blob(name))


class _GCS:
    def __init__(self):
        self.store = _Bucket()

    def bucket(self, name):
        return self.store


class _KMS:
    def __init__(self, key):
        self.key = key
        self.sign_requests = []

    def get_public_key(self, *, request):
        public = self.key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        class Response:
            algorithm = "EC_SIGN_ED25519"
            pem = public

        return Response()

    def asymmetric_sign(self, *, request):
        self.sign_requests.append(request)
        signature = self.key.sign(request["data"])

        class Response:
            pass

        response = Response()
        response.signature = signature
        return response


class _Response:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, value, url):
        self.value = value
        self.url = url

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.value[:limit]


class _Opener:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        return self.response


def _authority(key):
    public = b64encode(key.public_key().public_bytes_raw())
    return {
        "schema": "P5R0PublicAuthorityV4",
        "authority_id": "bridge-authority",
        "key_id": "bridge-key",
        "public_key": public,
        "public_key_digest": digest(public),
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1",
            "provider": "bridge-provider",
            "audience": "https://bridge.example.test",
            "event": "bridge_attestation",
        },
    }


def test_gcs_ledger_uses_exact_scoped_name_and_generation_preconditions():
    gcs = _GCS()
    ledger = GCSDurableTimingBridgeLedger("private-bucket", "bridge-v3", client=gcs)
    assert ledger.object_name("run-1") == "bridge-v3/runs/run-1/timing-bridge/ledger.json"
    ledger.append(
        "run-1", request_digest=digest("request"), record_digest=digest("record"),
        sequence=1, previous_digest=None, task_id="task", event="task_issued",
    )
    assert ledger.head("run-1").sequence == 1
    with pytest.raises(Exception, match="generation conflict"):
        # Simulate another worker committing the head between read and write.
        original = ledger._read
        ledger._read = lambda run_id: (original(run_id)[0], 999)
        ledger.append(
            "run-1", request_digest=digest("request-2"), record_digest=digest("record-2"),
            sequence=2, previous_digest=digest("record"), task_id="task-2", event="result_received",
        )
    assert set(gcs.store.objects) == {"bridge-v3/runs/run-1/timing-bridge/ledger.json"}


def test_bridge_kms_signer_matches_public_authority_without_private_export():
    key = Ed25519PrivateKey.generate()
    authority = _authority(key)
    signer = BridgeKMSEd25519Signer(
        "projects/project/locations/us/keyRings/r/cryptoKeys/bridge/cryptoKeyVersions/1",
        authority,
        client=_KMS(key),
    )
    signature = signer.sign_digest(b"x" * 32)
    assert signature
    assert "private" not in repr(signer).lower()
    assert not hasattr(signer, "private_key")


def test_bridge_config_requires_pinned_freetsa_material(tmp_path: Path):
    pem = tmp_path / "freetsa-ca.pem"
    pem.write_bytes(b"reviewed FreeTSA CA")
    key = Ed25519PrivateKey.generate()
    authority = _authority(key)
    env = {
        "P5R0_BRIDGE_AUTHORITY_JSON": canonical_bytes(authority).decode(),
        "P5R0_BRIDGE_LEDGER_ID": "bridge-ledger",
        "P5R0_BRIDGE_KMS_KEY_VERSION": "projects/project/locations/us/keyRings/r/cryptoKeys/bridge/cryptoKeyVersions/1",
        "P5R0_BRIDGE_BUCKET": "private-bucket",
        "P5R0_BRIDGE_PREFIX": "bridge-v3",
        "P5R0_BRIDGE_FREETSA_CA_PEM_PATH": str(pem),
        "P5R0_BRIDGE_FREETSA_CA_PEM_SHA256": digest(pem.read_bytes()),
        "P5R0_BRIDGE_FREETSA_CERTIFICATE_SHA256": digest("reviewed certificate"),
    }
    config = BridgeProductionConfig.from_env(env)
    assert config.rfc3161_config.endpoint == FREETSA_ENDPOINT
    assert config.rfc3161_config.policy_oid == FREETSA_POLICY_OID
    missing = dict(env)
    missing.pop("P5R0_BRIDGE_FREETSA_CERTIFICATE_SHA256")
    with pytest.raises(TimingBridgeProductionError, match="CERTIFICATE_SHA256"):
        BridgeProductionConfig.from_env(missing)


def test_production_factory_constructs_only_with_all_pinned_inputs(tmp_path: Path):
    from services.p5_r0_evaluator.timing_bridge_production import create_production_bridge

    pem = tmp_path / "freetsa-ca.pem"
    pem.write_bytes(b"reviewed FreeTSA CA")
    key = Ed25519PrivateKey.generate()
    authority = _authority(key)
    env = {
        "P5R0_BRIDGE_AUTHORITY_JSON": canonical_bytes(authority).decode(),
        "P5R0_BRIDGE_LEDGER_ID": "bridge-ledger",
        "P5R0_BRIDGE_KMS_KEY_VERSION": "projects/project/locations/us/keyRings/r/cryptoKeys/bridge/cryptoKeyVersions/1",
        "P5R0_BRIDGE_BUCKET": "private-bucket",
        "P5R0_BRIDGE_PREFIX": "bridge-v3",
        "P5R0_BRIDGE_FREETSA_CA_PEM_PATH": str(pem),
        "P5R0_BRIDGE_FREETSA_CA_PEM_SHA256": digest(pem.read_bytes()),
        "P5R0_BRIDGE_FREETSA_CERTIFICATE_SHA256": digest("reviewed certificate"),
    }
    runtime = create_production_bridge(
        env=env, gcs_client=_GCS(), kms_client=_KMS(key), authenticator=lambda headers: True,
    )
    assert runtime.service.production_ready is True
    assert runtime.service.ledger.durable is True
    assert callable(runtime.application)
    with pytest.raises(TimingBridgeProductionError, match="authenticator"):
        create_production_bridge(env=env, gcs_client=_GCS(), kms_client=_KMS(key))


    token = FederatedAccessToken("verified-federated", 2_000)
    endpoint = f"{IAM_CREDENTIALS_ENDPOINT}/bridge-service@example.iam.gserviceaccount.com:generateIdToken"
    opener = _Opener(_Response(b'{"token":"id-token"}', endpoint))
    factory = IAMCredentialsIDTokenFactory(
        "bridge-service@example.iam.gserviceaccount.com",
        "https://bridge.example.test",
        token,
        opener=opener,
        clock=lambda: 1_000,
    )
    assert factory.authorization_header() == "Bearer id-token"
    request, timeout = opener.requests[0]
    assert request.full_url == endpoint
    assert request.get_header("Authorization") == "Bearer verified-federated"
    assert b"https://bridge.example.test" in request.data
    assert timeout == 5.0


def test_iam_credentials_factory_rejects_expired_token_and_redirect():
    with pytest.raises(Exception, match="federated access token"):
        IAMCredentialsIDTokenFactory(
            "bridge-service@example.iam.gserviceaccount.com", "https://bridge.example.test",
            FederatedAccessToken("expired", 100), clock=lambda: 1_000,
        )
    token = FederatedAccessToken("verified-federated", 2_000)
    opener = _Opener(_Response(b'{"token":"id-token"}', "https://other.example.test"))
    factory = IAMCredentialsIDTokenFactory(
        "bridge-service@example.iam.gserviceaccount.com", "https://bridge.example.test",
        token, opener=opener, clock=lambda: 1_000,
    )
    with pytest.raises(Exception, match="redirect"):
        factory()
