from __future__ import annotations

from dataclasses import replace

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from services.p5_r0_evaluator.attestation_binding import (
    AttestationBindingError,
    VerifiedAttestationBinding,
    _build_verified_attestation_binding,
)
from services.p5_r0_evaluator.canonical import b64encode, canonical_bytes, digest, parse_canonical, signing_digest
from services.p5_r0_evaluator.confidential_space import (
    AttestationError,
    AttestationGate,
    CapabilityFactory,
    ConfidentialSpaceAdapter,
    ConfidentialSpaceError,
    DEFAULT_TIMING_BRIDGE_FREETSA_CA_PATH,
    FederatedAccessToken,
    LockedBootstrapConfig,
    create_timing_bridge_attestor,
    MAX_METADATA_TOKEN_BYTES,
    MAX_STARTUP_EVIDENCE_BYTES,
    LauncherTokenSource,
    RunScopedObjectStore,
    ScopedObjectStore,
    SignedTimingAttestor,
    STSError,
)
from services.p5_r0_evaluator.interfaces import Object, StoreError
from services.p5_r0_evaluator.signing import KMSConfigurationError, KMSEd25519Signer
from services.p5_r0_evaluator.store import GCSStore, MemoryStore
from services.p5_r0_evaluator.timing import TimingAttestationError, TimingAuthorityConfig, validate_attestation
from services.p5_r0_evaluator.timing_bridge_auth import (
    IAMCredentialsAccessTokenFactory,
    IAMCredentialsError,
    IAM_CREDENTIALS_ENDPOINT,
)
from services.p5_r0_evaluator.rfc3161 import FREETSA_CA_PEM_SHA256, FREETSA_TSA_CERTIFICATE_SHA256


class FakeSource:
    def __init__(self, token="attestation-token"):
        self.token = token
        self.calls = []

    def fetch(self, *, audience, nonce):
        self.calls.append((audience, nonce))
        return self.token


class FakeVerifier:
    def __init__(self, claims):
        self.claims = claims
        self.calls = []

    def verify(self, token, *, audience):
        self.calls.append((token, audience))
        return dict(self.claims)


class FakeSTS:
    def __init__(self, token="federated"):
        self.token = token
        self.calls = []

    def exchange(self, *, subject_token, audience, provider):
        self.calls.append((subject_token, audience, provider))
        return FederatedAccessToken(self.token, 1_200)


class FakeBlob:
    def __init__(self, data=b"", generation=1):
        self.data = data
        self.generation = generation

    def reload(self):
        return None

    def download_as_bytes(self):
        return self.data

    def upload_from_string(self, data, **kwargs):
        self.data = bytes(data)
        self.generation += 1


class FakeBucket:
    def __init__(self):
        self.blobs = {}

    def blob(self, name):
        return self.blobs.setdefault(name, FakeBlob())


class FakeGCSClient:
    def __init__(self):
        self.bucket_obj = FakeBucket()

    def bucket(self, name):
        assert name == "private-bucket"
        return self.bucket_obj


class MissingBlob:
    def reload(self):
        error = RuntimeError("not found")
        error.code = 404
        raise error


class MissingBucket:
    def blob(self, name):
        assert name == "missing"
        return MissingBlob()


class MissingGCSClient:
    def bucket(self, name):
        assert name == "private-bucket"
        return MissingBucket()


class FakeKMSClient:
    def __init__(self, key):
        self.key = key
        self.public_calls = []
        self.sign_calls = []

    def get_public_key(self, *, request):
        self.public_calls.append(request)
        public = self.key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()

        class Response:
            algorithm = "EC_SIGN_ED25519"
            pem = public

        return Response()

    def asymmetric_sign(self, *, request):
        self.sign_calls.append(request)

        class Response:
            signature = self.key.sign(request["data"])

        return Response()


def test_gcs_store_preserves_create_only_missing_object_boundary():
    store = GCSStore("private-bucket", client=MissingGCSClient())
    with pytest.raises(StoreError, match="object not found"):
        store.get("missing")


def _config(nonce_factory=lambda: "nonce-1234"):
    key = Ed25519PrivateKey.generate()
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {"schema": "P5R0AuthorityV3", "authority_id": "authority", "key_id": "key", "public_key": public, "public_key_digest": digest(public), "transport_attestation": {"provider": "wip", "event": "fixed"}}
    return LockedBootstrapConfig(
        authority=authority,
        caller_audience="runner-audience",
        allowed_subjects=frozenset({"runner"}),
        attestation_audience="https://sts.googleapis.com",
        wip_provider="//iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/pool/providers/provider",
        project_number="123",
        project_id="project",
        zone="us-central1-a",
        image_digest="sha256:" + "a" * 64,
        debug_state="disabled-since-boot",
        tee="CONFIDENTIAL_SPACE",
        secure_boot=True,
        bucket="private-bucket",
        prefix="v3",
        kms_key_version="projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1",
        runtime_digest="sha256:" + "b" * 64,
        resource_profile_digest="sha256:" + "c" * 64,
        expected_issuer="https://confidentialcomputing.googleapis.com",
        hardware_model="GCP_AMD_SEV",
        clock=lambda: 1_000,
        nonce_factory=nonce_factory,
    ), key


def _claims(config, nonce="nonce-1234", **overrides):
    claims = {
        "aud": config.attestation_audience,
        "iss": "https://confidentialcomputing.googleapis.com",
        "iat": 999,
        "exp": 2_000,
        "eat_nonce": nonce,
        "sub": "runner",
        "swname": config.tee,
        "dbgstat": config.debug_state,
        "hwmodel": config.hardware_model,
        "secboot": config.secure_boot,
        "submods": {
            "container": {
                "image_digest": config.image_digest,
                "env": {"P5R0_EXPECTED_WORKLOAD": config.workload, "P5R0_CONFIDENTIAL_SPACE_SMOKE": "1" if config.confidential_space_smoke else "0"},
            },
            "gce": {
                "project_number": config.project_number,
                "project_id": config.project_id,
                "zone": config.zone,
            },
            "confidential_space": {"support_attributes": ["STABLE"]},
        },
    }
    aliases = {
        "image_digest": ("submods", "container", "image_digest"),
        "project_number": ("submods", "gce", "project_number"),
        "project_id": ("submods", "gce", "project_id"),
        "zone": ("submods", "gce", "zone"),
        "debug_state": ("dbgstat",),
        "tee": ("swname",),
        "hardware_model": ("hwmodel",),
        "secure_boot": ("secboot",),
        "workload": ("submods", "container", "env", "P5R0_EXPECTED_WORKLOAD"),
        "smoke": ("submods", "container", "env", "P5R0_CONFIDENTIAL_SPACE_SMOKE"),
        "nonce": ("eat_nonce",),
        "issuer": ("iss",),
    }
    for name, value in overrides.items():
        path = aliases.get(name, (name,))
        target = claims
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
    return claims


def test_locked_bootstrap_does_not_create_clients_or_read_truth():
    config, _ = _config()
    source = FakeSource()
    verifier = FakeVerifier(_claims(config))
    sts = FakeSTS()
    made = []
    adapter = ConfidentialSpaceAdapter(config, source=source, verifier=verifier, sts=sts, capability_factory=type("Factory", (), {"build": lambda self, token: made.append(token) or object()})(), service_factory=lambda caps: object())
    assert adapter.attested is False
    assert made == [] and source.calls == [] and sts.calls == []
    status, _, body = adapter.dispatch("GET", "/healthz", b"", {})
    assert status == 200 and parse_canonical(body)["status"] == "locked"


def test_locked_bootstrap_defaults_wip_token_audience_to_google_sts_and_rejects_provider_as_audience():
    config, key = _config()
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {
        "schema": "P5R0PublicAuthorityV4", "authority_id": "authority", "key_id": "key",
        "public_key": public, "public_key_digest": digest(public),
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1", "provider": config.wip_provider,
            "audience": config.attestation_audience, "event": "confidential_space_attestation",
        },
    }
    env = _env_for_config(config, authority)
    env.pop("P5R0_ATTESTATION_AUDIENCE")
    parsed = LockedBootstrapConfig.from_env(env)
    assert parsed.attestation_audience == "https://sts.googleapis.com"

    forged = dict(env)
    forged["P5R0_ATTESTATION_AUDIENCE"] = config.wip_provider
    with pytest.raises(RuntimeError, match="separate HTTPS audience"):
        LockedBootstrapConfig.from_env(forged)


def test_wip_token_validation_covers_nonce_issuer_and_fixed_claims():
    config, _ = _config()
    cases = (
        ({"iss": "wrong-issuer"}, "issuer mismatch"),
        ({"nonce": "wrong-nonce"}, "nonce mismatch"),
        ({"secure_boot": False}, "secure_boot mismatch"),
        ({"hardware_model": "GCP_INTEL_TDX"}, "hardware_model mismatch"),
        ({"workload": "wrong-workload"}, "workload mismatch"),
        ({"smoke": "1"}, "smoke mismatch"),
    )
    for overrides, message in cases:
        gate = AttestationGate(config, FakeSource(), FakeVerifier(_claims(config, **overrides)))
        with pytest.raises(AttestationError, match=message):
            gate.verify_startup()


def test_google_jwt_verifier_fails_closed_on_signature_error(monkeypatch):
    import sys
    import types
    from services.p5_r0_evaluator.confidential_space import GoogleJwtAttestationVerifier

    def reject(*args, **kwargs):
        raise ValueError("bad signature")

    google = types.ModuleType("google")
    auth = types.ModuleType("google.auth")
    transport = types.ModuleType("google.auth.transport")
    requests = types.ModuleType("google.auth.transport.requests")
    requests.Request = object
    oauth2 = types.ModuleType("google.oauth2")
    id_token = types.ModuleType("google.oauth2.id_token")
    id_token.verify_token = reject
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.auth", auth)
    monkeypatch.setitem(sys.modules, "google.auth.transport", transport)
    monkeypatch.setitem(sys.modules, "google.auth.transport.requests", requests)
    monkeypatch.setitem(sys.modules, "google.oauth2", oauth2)
    monkeypatch.setitem(sys.modules, "google.oauth2.id_token", id_token)
    with pytest.raises(AttestationError, match="signature verification failed"):
        GoogleJwtAttestationVerifier().verify("jwt", audience="https://sts.googleapis.com")


# Local mock-only happy path: the token exchanged after attestation is the only
# credential material passed to the fake GCS/KMS client factories.
def test_local_mock_post_attestation_builds_federated_gcs_and_kms_clients():
    config, key = _config()
    source, verifier, sts = FakeSource(), FakeVerifier(_claims(config)), FakeSTS()
    gcs, kms = FakeGCSClient(), FakeKMSClient(key)
    seen_tokens = []
    factory = CapabilityFactory(config, storage_client_factory=lambda token: seen_tokens.append(token) or gcs, kms_client_factory=lambda token: seen_tokens.append(token) or kms)
    captured = []
    adapter = ConfidentialSpaceAdapter(config, source=source, verifier=verifier, sts=sts, capability_factory=factory, service_factory=lambda caps: captured.append(caps) or object())
    service = adapter.activate_attested_service()
    assert service is not None and captured
    assert source.calls and source.calls[0][0] == "https://sts.googleapis.com"
    assert verifier.calls and verifier.calls[0][1] == "https://sts.googleapis.com"
    assert sts.calls == [("attestation-token", config.wip_provider, config.wip_provider)]
    assert kms.public_calls == [{"name": config.kms_key_version}]
    assert kms.sign_calls == []
    assert seen_tokens and all(isinstance(token, FederatedAccessToken) and token.access_token == "federated" for token in seen_tokens)
    binding = captured[0].verified_attestation_binding
    assert isinstance(binding, VerifiedAttestationBinding)
    assert binding.token_digest == digest("attestation-token")
    assert binding.federated_token_digest == digest("federated")
    assert binding.image_digest == config.image_digest
    assert binding.provider == config.wip_provider
    public_binding = binding.as_public_dict()
    claimed_binding_digest = public_binding.pop("binding_digest")
    assert claimed_binding_digest == digest(public_binding)
    timing = captured[0].timing_attestor.record(run_id="run", task_id="task", event="task_issued", payload_digest=digest("task"))
    validate_attestation(timing, run_id="run", task_id="task", event="task_issued", payload_digest=digest("task"))
    assert kms.sign_calls and kms.sign_calls[0]["name"] == config.kms_key_version
    evidence = parse_canonical(canonical_bytes(adapter.startup_evidence))
    assert len(canonical_bytes(evidence)) <= MAX_STARTUP_EVIDENCE_BYTES
    assert "federated" not in str(evidence) and "attestation-token" not in str(evidence)




def test_timing_bridge_factory_fails_closed_when_configuration_is_missing():
    config, _ = _config()
    with pytest.raises(STSError, match="configuration is incomplete"):
        create_timing_bridge_attestor(FederatedAccessToken("federated", 4_000_000_000), config)


def _bridge_config(config, ca_path, ca_pin, cert_pin):
    return replace(
        config,
        timing_authority_id="bridge-authority",
        timing_key_id="bridge-key",
        timing_ledger_id="bridge-ledger",
        timing_public_key_digest="sha256:" + "e" * 64,
        timing_bridge_endpoint="https://timing-bridge.example.test/v1/timing",
        timing_bridge_service_account="bridge-service@example.iam.gserviceaccount.com",
        timing_bridge_audience="https://timing-bridge.example.test",
        timing_bridge_freetsa_ca_pem_path=str(ca_path),
        timing_bridge_freetsa_ca_pem_sha256=ca_pin,
        timing_bridge_freetsa_certificate_sha256=cert_pin,
    )


def test_timing_bridge_factory_wires_post_sts_token_endpoint_audience_and_pins(tmp_path):
    ca = tmp_path / "freetsa-ca.pem"
    ca.write_bytes(b"reviewed public CA")
    config, _ = _config()
    config = _bridge_config(config, ca, digest(ca.read_bytes()), digest("tsa certificate"))
    token = FederatedAccessToken("post-attestation-federated", 4_000_000_000)
    client = create_timing_bridge_attestor(token, config)
    auth_factory = client.config.authorization_header.__self__
    assert auth_factory.credentials is token
    assert auth_factory.service_account == config.timing_bridge_service_account
    assert auth_factory.audience == config.timing_bridge_audience
    assert client.config.endpoint == config.timing_bridge_endpoint
    assert client.config.authority == TimingAuthorityConfig(
        authority_id=config.timing_authority_id,
        key_id=config.timing_key_id,
        ledger_id=config.timing_ledger_id,
        public_key_digest=config.timing_public_key_digest,
    )
    assert client.config.rfc3161_config.endpoint == "https://freetsa.org/tsr"
    assert client.config.rfc3161_config.tsa_ca_pem_sha256 == digest(ca.read_bytes())


@pytest.mark.parametrize("change, match", [
    ("timing_bridge_endpoint", "timing bridge endpoint"),
    ("timing_bridge_audience", "bridge audience must be HTTPS"),
    ("timing_bridge_freetsa_ca_pem_sha256", "CA pin mismatch"),
])
def test_timing_bridge_factory_rejects_endpoint_audience_or_pin_mismatch(tmp_path, change, match):
    ca = tmp_path / "freetsa-ca.pem"
    ca.write_bytes(b"reviewed public CA")
    config, _ = _config()
    config = _bridge_config(config, ca, digest(ca.read_bytes()), digest("tsa certificate"))
    values = {
        "timing_bridge_endpoint": "https://timing-bridge.example.test/v1/timing?redirect=1",
        "timing_bridge_audience": "http://timing-bridge.example.test",
        "timing_bridge_freetsa_ca_pem_sha256": digest(b"different CA"),
    }
    with pytest.raises(STSError, match=match):
        create_timing_bridge_attestor(FederatedAccessToken("federated", 4_000_000_000), replace(config, **{change: values[change]}))


def test_adapter_injects_successful_bridge_attestor_after_sts(monkeypatch):
    config, signing_key = _config()
    config = replace(
        config,
        timing_authority_id="bridge-authority", timing_key_id="bridge-key",
        timing_ledger_id="bridge-ledger", timing_public_key_digest="sha256:" + "e" * 64,
        capability_service_account="p5-evaluator@ocelot-proof.iam.gserviceaccount.com",
    )
    seen = []
    authority = TimingAuthorityConfig(
        authority_id=config.timing_authority_id, key_id=config.timing_key_id,
        ledger_id=config.timing_ledger_id, public_key_digest=config.timing_public_key_digest,
    )

    class Attestor:
        independent = True
        def __init__(self):
            self.authority = authority

    def attestor_factory(token, received_config):
        seen.append((token, received_config))
        return Attestor()

    monkeypatch.setattr(CapabilityFactory, "_storage_client", lambda self, token: FakeGCSClient())
    monkeypatch.setattr(CapabilityFactory, "_kms_client", lambda self, token: FakeKMSClient(signing_key))
    captured = []
    adapter = ConfidentialSpaceAdapter(
        config, source=FakeSource(), verifier=FakeVerifier(_claims(config)), sts=FakeSTS(),
        capability_factory=CapabilityFactory(
            config,
            impersonation_factory=lambda token: FederatedAccessToken("impersonated", 1_150),
            timing_attestor_factory=attestor_factory,
        ),
        service_factory=lambda capabilities: captured.append(capabilities) or object(),
    )
    adapter.activate_attested_service()
    assert seen and seen[0][0].access_token == "federated"
    assert seen[0][1] is config
    assert captured[0].timing_attestor.independent is True


    config, _ = _config()

    class FailingSTS:
        def exchange(self, **kwargs):
            raise STSError("exchange failed")

    made = []
    factory = type("Factory", (), {"build": lambda self, token: made.append(token)})()
    adapter = ConfidentialSpaceAdapter(config, source=FakeSource(), verifier=FakeVerifier(_claims(config)), sts=FailingSTS(), capability_factory=factory, service_factory=lambda caps: object())
    with pytest.raises(STSError):
        adapter.activate_attested_service()
    assert not adapter.attested and made == []


def test_scoped_store_is_fail_closed_for_worker_inappropriate_paths():
    inner = MemoryStore()
    store = ScopedObjectStore(inner)
    with pytest.raises(Exception):
        store.get("admin/list")
    with pytest.raises(Exception):
        store.create("truth/new.json", b"secret")
    with pytest.raises(Exception):
        store.get("runs/../truth/private.json")
    created = store.create("runs/run/state.json", b"{}")
    assert created.generation == 1


def test_metadata_config_requires_immutable_attestation_policy():
    with pytest.raises(RuntimeError, match="P5R0_EXPECTED_IMAGE_DIGEST"):
        LockedBootstrapConfig.from_env({"P5R0_AUTHORITY_JSON": "{}", "P5R0_ALLOWED_SUBJECTS": "runner"})



def test_sts_serializes_canonical_provider_audience_and_validates_bearer_response():
    from urllib.parse import parse_qs
    from services.p5_r0_evaluator.confidential_space import GoogleSTSClient

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
        def read(self, limit=None):
            return b'{"access_token":"federated","token_type":"Bearer","expires_in":120}'

    requests = []
    def opener(request, timeout):
        requests.append((request, timeout))
        return Response()

    provider = "//iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/pool/providers/provider"
    token = GoogleSTSClient(opener=opener, clock=lambda: 1000).exchange(subject_token="jwt", audience=provider, provider=provider)
    assert token.access_token == "federated" and token.expires_at == 1120
    form = parse_qs(requests[0][0].data.decode())
    assert form["audience"] == [provider] and form["subject_token"] == ["jwt"]
    with pytest.raises(STSError):
        GoogleSTSClient(opener=opener).exchange(subject_token="jwt", audience="https://sts.googleapis.com", provider=provider)
    with pytest.raises(STSError):
        GoogleSTSClient(opener=opener).exchange(subject_token="jwt", audience="projects/123/providers/p", provider="projects/123/providers/p")
    with pytest.raises(STSError, match="endpoint is immutable"):
        GoogleSTSClient(endpoint="https://attacker.invalid/token")


def test_generate_access_token_is_fixed_bounded_and_expiry_bound():
    import json

    token = FederatedAccessToken("federated-source", 4_000)
    endpoint = f"{IAM_CREDENTIALS_ENDPOINT}/p5-evaluator@ocelot-proof.iam.gserviceaccount.com:generateAccessToken"

    class Response:
        status = 200
        headers = {"Content-Type": "application/json"}
        def geturl(self):
            return endpoint
        def read(self, limit):
            return b'{"accessToken":"impersonated","expireTime":"1970-01-01T00:33:20Z"}'[:limit]

    class Opener:
        def __init__(self):
            self.requests = []
        def open(self, request, timeout):
            self.requests.append((request, timeout))
            return Response()

    opener = Opener()
    factory = IAMCredentialsAccessTokenFactory(
        "p5-evaluator@ocelot-proof.iam.gserviceaccount.com", token,
        opener=opener, clock=lambda: 1_000,
    )
    effective = factory()
    assert effective == FederatedAccessToken("impersonated", 2_000)
    request, timeout = opener.requests[0]
    assert request.full_url == endpoint
    assert request.get_header("Authorization") == "Bearer federated-source"
    assert json.loads(request.data) == {"lifetime": "2970s", "scope": ["https://www.googleapis.com/auth/cloud-platform"]}
    assert timeout == 5.0

    with pytest.raises(IAMCredentialsError, match="target service account"):
        IAMCredentialsAccessTokenFactory("not-an-account", token)


def test_generate_access_token_rejects_redirect_duplicate_expiry_and_oversize():
    endpoint = f"{IAM_CREDENTIALS_ENDPOINT}/p5-evaluator@ocelot-proof.iam.gserviceaccount.com:generateAccessToken"
    token = FederatedAccessToken("federated-source", 4_000)

    class Response:
        status = 200
        headers = {"Content-Type": "application/json"}
        def __init__(self, body, url=endpoint):
            self.body, self.url = body, url
        def geturl(self):
            return self.url
        def read(self, limit):
            return self.body[:limit]

    cases = (
        (b'{"accessToken":"x","accessToken":"y","expireTime":"1970-01-01T00:33:20Z"}', endpoint, "response schema"),
        (b'{"accessToken":"x","expireTime":"1970-01-01T01:23:20Z"}', endpoint, "outside the allowed lifetime"),
        (b'{"accessToken":"x","expireTime":"1970-01-01T00:33:20Z"}', "https://attacker.invalid", "redirect"),
        (b"x" * (16 * 1024 + 1), endpoint, "too large"),
    )
    for body, url, message in cases:
        class Opener:
            def open(self, request, timeout):
                return Response(body, url)
        factory = IAMCredentialsAccessTokenFactory(
            "p5-evaluator@ocelot-proof.iam.gserviceaccount.com", token,
            opener=Opener(), clock=lambda: 1_000,
        )
        with pytest.raises(IAMCredentialsError, match=message):
            factory()


def test_capability_factory_uses_impersonated_token_for_gcs_and_kms_but_not_timing():
    config, key = _config()
    config = replace(config, capability_service_account="p5-evaluator@ocelot-proof.iam.gserviceaccount.com")
    seen = []
    factory = CapabilityFactory(
        config,
        impersonation_factory=lambda token: FederatedAccessToken("impersonated", 1_150),
        storage_client_factory=lambda token: seen.append(("gcs", token)) or FakeGCSClient(),
        kms_client_factory=lambda token: seen.append(("kms", token)) or FakeKMSClient(key),
    )
    factory.build(FederatedAccessToken("federated", 4_000_000_000))
    assert [(kind, token.access_token) for kind, token in seen] == [("gcs", "impersonated"), ("kms", "impersonated")]


def test_gcs_store_rejects_ambient_adc_client_creation():
    from services.p5_r0_evaluator.store import GCSStore
    with pytest.raises(StoreError, match="explicit federated"):
        GCSStore("private-bucket")



def test_expired_federated_capability_relocks_adapter():
    from dataclasses import replace
    now = [1000]
    config, _ = _config()
    config = replace(config, clock=lambda: now[0])

    class ExpiringSTS(FakeSTS):
        def exchange(self, **kwargs):
            return FederatedAccessToken("federated", 1001)

    factory = type("Factory", (), {"build": lambda self, token: object()})()
    adapter = ConfidentialSpaceAdapter(config, source=FakeSource(), verifier=FakeVerifier(_claims(config)), sts=ExpiringSTS(), capability_factory=factory, service_factory=lambda caps: object())
    adapter.activate_attested_service()
    assert adapter.attested
    now[0] = 1001
    assert not adapter.attested
    status, _, body = adapter.dispatch("GET", "/healthz", b"", {})
    assert status == 200 and parse_canonical(body)["status"] == "locked"



def _env_for_config(config, authority):
    from dataclasses import replace
    config = replace(config, authority=authority, timing_authority_id="independent-authority", timing_key_id="independent-key", timing_ledger_id="independent-ledger", timing_public_key_digest="sha256:" + "e" * 64, timing_bridge_endpoint="https://timing-bridge.example.test/v1/timing", timing_bridge_service_account="bridge-service@example.iam.gserviceaccount.com", timing_bridge_audience="https://timing-bridge.example.test", timing_bridge_freetsa_ca_pem_path="/app/services/p5_r0_evaluator/deploy/freetsa-cacert.pem", timing_bridge_freetsa_ca_pem_sha256="sha256:" + "f" * 64, timing_bridge_freetsa_certificate_sha256="sha256:" + "1" * 64, base_image_digest="sha256:" + "f" * 64, service_name="p5-evaluator", region="us-central1", cpu_limit="1", memory_limit="512Mi")
    provider = config.wip_provider
    env = {
        "P5R0_AUTHORITY_JSON": __import__("json").dumps(authority, sort_keys=True, separators=(",", ":")),
        "P5R0_AUDIENCE": config.caller_audience,
        "P5R0_ALLOWED_SUBJECTS": "runner",
        "P5R0_ATTESTATION_AUDIENCE": config.attestation_audience,
        "P5R0_WIP_PROVIDER": provider,
        "P5R0_EXPECTED_PROJECT_NUMBER": config.project_number,
        "P5R0_EXPECTED_PROJECT_ID": config.project_id,
        "P5R0_EXPECTED_ZONE": config.zone,
        "P5R0_EXPECTED_IMAGE_DIGEST": config.image_digest,
        "P5R0_EXPECTED_DEBUG_STATE": config.debug_state,
        "P5R0_EXPECTED_TEE": config.tee,
        "P5R0_EXPECTED_HARDWARE_MODEL": config.hardware_model,
        "P5R0_EXPECTED_WORKLOAD": config.workload,
        "P5R0_EXPECTED_SECURE_BOOT": "true",
        "P5R0_ATTESTATION_ISSUER": config.expected_issuer,
        "P5R0_BUCKET": config.bucket,
        "P5R0_PREFIX": "v3",
        "P5R0_KMS_KEY_VERSION": config.kms_key_version,
        "P5R0_CAPABILITY_SERVICE_ACCOUNT": config.capability_service_account or "",
        "P5R0_RUNTIME_DIGEST": config.runtime_digest,
        "P5R0_RESOURCE_PROFILE_DIGEST": config.resource_profile_digest,
        "P5R0_BASE_IMAGE_DIGEST": config.base_image_digest,
        "P5R0_SERVICE_NAME": config.service_name,
        "P5R0_REGION": config.region,
        "P5R0_CPU_LIMIT": config.cpu_limit,
        "P5R0_MEMORY_LIMIT": config.memory_limit,
        "P5R0_POLICY_DIGEST": config.policy_digest,
        "P5R0_CLAIM_PATHS_DIGEST": config.claim_paths_digest,
        "P5R0_ATTESTATION_CLAIMS_DIGEST": config.attestation_claims_digest,
        "P5R0_WIP_POLICY_DIGEST": config.wip_policy_digest,
        "P5R0_TIMING_AUTHORITY_ID": "independent-authority",
        "P5R0_TIMING_KEY_ID": "independent-key",
        "P5R0_TIMING_LEDGER_ID": "independent-ledger",
        "P5R0_TIMING_PUBLIC_KEY_DIGEST": "sha256:" + "e" * 64,
        "P5R0_TIMING_BRIDGE_ENDPOINT": "https://timing-bridge.example.test/v1/timing",
        "P5R0_TIMING_BRIDGE_SERVICE_ACCOUNT": "bridge-service@example.iam.gserviceaccount.com",
        "P5R0_TIMING_BRIDGE_AUDIENCE": "https://timing-bridge.example.test",
        "P5R0_TIMING_BRIDGE_FREETSA_CA_PEM_PATH": "/app/services/p5_r0_evaluator/deploy/freetsa-cacert.pem",
        "P5R0_TIMING_BRIDGE_FREETSA_CA_PEM_SHA256": "sha256:" + "f" * 64,
        "P5R0_TIMING_BRIDGE_FREETSA_CERTIFICATE_SHA256": "sha256:" + "1" * 64,
    }
    if config.attestation_subject_prefix is not None:
        env["P5R0_ATTESTATION_SUBJECT_PREFIX"] = config.attestation_subject_prefix
    return env


def _set_production_env(monkeypatch, config):
    from dataclasses import replace

    prefix = f"https://www.googleapis.com/compute/v1/projects/{config.project_id}/zones/{config.zone}/instances/"
    config = replace(config, attestation_subject_prefix=prefix, capability_service_account="p5-evaluator@ocelot-proof.iam.gserviceaccount.com")
    key = Ed25519PrivateKey.generate()
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {
        "schema": "P5R0PublicAuthorityV4", "authority_id": "authority", "key_id": "key",
        "public_key": public, "public_key_digest": digest(public),
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1", "provider": config.wip_provider,
            "audience": config.attestation_audience, "event": "confidential_space_attestation",
        },
    }
    for name, value in _env_for_config(config, authority).items():
        monkeypatch.setenv(name, value)
    return config


def test_production_from_env_requires_exact_vm_subject_prefix(monkeypatch):
    from dataclasses import replace

    config, key = _config()
    prefix = "https://www.googleapis.com/compute/v1/projects/project/zones/us-central1-a/instances/"
    config = replace(config, attestation_subject_prefix=prefix, capability_service_account="p5-evaluator@ocelot-proof.iam.gserviceaccount.com")
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {
        "schema": "P5R0PublicAuthorityV4", "authority_id": "authority", "key_id": "key",
        "public_key": public, "public_key_digest": digest(public),
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1", "provider": config.wip_provider,
            "audience": config.attestation_audience, "event": "confidential_space_attestation",
        },
    }
    env = _env_for_config(config, authority)
    env.pop("P5R0_ATTESTATION_SUBJECT_PREFIX")
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(RuntimeError, match="P5R0_ATTESTATION_SUBJECT_PREFIX is required"):
        LockedBootstrapConfig.from_env(None)

    monkeypatch.setenv("P5R0_ATTESTATION_SUBJECT_PREFIX", prefix)
    parsed = LockedBootstrapConfig.from_env(None)
    assert parsed.attestation_subject_prefix == prefix
    monkeypatch.delenv("P5R0_CAPABILITY_SERVICE_ACCOUNT")
    with pytest.raises(RuntimeError, match="P5R0_CAPABILITY_SERVICE_ACCOUNT is required"):
        LockedBootstrapConfig.from_env(None)
    monkeypatch.setenv("P5R0_CAPABILITY_SERVICE_ACCOUNT", "not-an-account")
    with pytest.raises(RuntimeError, match="P5R0_CAPABILITY_SERVICE_ACCOUNT is invalid"):
        LockedBootstrapConfig.from_env(None)
    monkeypatch.setenv("P5R0_CAPABILITY_SERVICE_ACCOUNT", "p5-evaluator@ocelot-proof.iam.gserviceaccount.com")
    for invalid in (
        prefix[:-1],
        prefix.replace("/zones/us-central1-a/", "/zones/europe-west1-b/"),
        "https://attacker.example/compute/v1/projects/project/zones/us-central1-a/instances/",
    ):
        monkeypatch.setenv("P5R0_ATTESTATION_SUBJECT_PREFIX", invalid)
        with pytest.raises(RuntimeError, match="ATTESTATION_SUBJECT_PREFIX"):
            LockedBootstrapConfig.from_env(None)


def test_legacy_fixture_subject_binding_remains_exact_and_prefix_binds_separate_identity_domain():
    from dataclasses import replace

    legacy, _ = _config()
    prefix = "https://www.googleapis.com/compute/v1/projects/project/zones/us-central1-a/instances/"
    prefixed = replace(legacy, attestation_subject_prefix=prefix)
    AttestationGate(prefixed, FakeSource(), FakeVerifier(_claims(prefixed, sub=prefix + "evaluator-cs"))).verify_startup()
    with pytest.raises(AttestationError, match="subject mismatch"):
        AttestationGate(prefixed, FakeSource(), FakeVerifier(_claims(prefixed, sub="runner"))).verify_startup()
    AttestationGate(legacy, FakeSource(), FakeVerifier(_claims(legacy, sub="runner"))).verify_startup()
    assert legacy.policy_digest != prefixed.policy_digest
    assert legacy.attestation_claims_digest != prefixed.attestation_claims_digest
    assert legacy.wip_policy_digest != prefixed.wip_policy_digest



    config, key = _config()
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {"schema": "P5R0PublicAuthorityV4", "authority_id": "authority", "key_id": "key", "public_key": public, "public_key_digest": digest(public), "transport_attestation": {"schema": "P5R0AuthorityTransportV1", "provider": config.wip_provider, "audience": config.attestation_audience, "event": "confidential_space_attestation"}}
    env = _env_for_config(config, authority)
    parsed = LockedBootstrapConfig.from_env(env)
    assert parsed.wip_provider == config.wip_provider
    assert parsed.expected_issuer == "https://confidentialcomputing.googleapis.com"
    assert parsed.hardware_model == "GCP_AMD_SEV"
    assert parsed.claim_paths["nonce"] == "eat_nonce"
    assert parsed.claim_paths["image_digest"] == "submods.container.image_digest"
    assert parsed.claim_paths["workload"] == "submods.container.env.P5R0_EXPECTED_WORKLOAD"
    wrong_issuer = dict(env)
    wrong_issuer["P5R0_ATTESTATION_ISSUER"] = "https://confidential-space.google.com"
    with pytest.raises(RuntimeError, match="Google Cloud Attestation issuer"):
        LockedBootstrapConfig.from_env(wrong_issuer)
    extra = dict(env)
    extra["P5R0_AUTHORITY_JSON"] = __import__("json").dumps({**authority, "private_key": "must-never-be-accepted"}, sort_keys=True, separators=(",", ":"))
    with pytest.raises(RuntimeError, match="closed authority"):
        LockedBootstrapConfig.from_env(extra)
    mismatch = dict(env)
    mismatch["P5R0_WIP_PROVIDER"] = config.wip_provider.rsplit("/", 1)[0] + "/other"
    with pytest.raises(RuntimeError, match="authority transport"):
        LockedBootstrapConfig.from_env(mismatch)


def test_launcher_posts_canonical_oidc_request_and_bounds_response():
    class FakeSocket:
        def __init__(self, *args):
            self.request = b""
        def settimeout(self, value):
            assert value == 5
        def connect(self, path):
            assert path == "/run/container_launcher/teeserver.sock"
        def sendall(self, data):
            self.request = data
        def recv(self, size):
            body = canonical_bytes({"token": "jwt"})
            response = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body
            if not hasattr(self, "sent"):
                self.sent = True
                return response
            return b""
        def close(self):
            pass

    sockets = []
    def factory(*args):
        value = FakeSocket(*args)
        sockets.append(value)
        return value

    source = LauncherTokenSource(socket_factory=factory)
    assert source.fetch(audience="aud", nonce="nonce-1234") == "jwt"
    request = sockets[0].request
    assert request.startswith(b"POST /v1/token HTTP/1.1\r\nHost: localhost\r\n")
    assert request.endswith(canonical_bytes({"audience": "aud", "token_type": "OIDC", "nonces": ["nonce-1234"]}))

    with pytest.raises(AttestationError, match="10-74"):
        source.fetch(audience="aud", nonce="short")
    with pytest.raises(AttestationError, match="10-74"):
        source.fetch(audience="aud", nonce="x" * 75)


def test_launcher_accepts_live_chunked_json_and_text_html_raw_jwt_responses():
    cases = (
        (
            b"Content-Type: application/json\r\nTransfer-Encoding: chunked",
            canonical_bytes({"token": "chunked-jwt"}),
            "chunked-jwt",
        ),
        (
            b"Content-Type: text/html\r\nContent-Length: 24",
            b"header.payload.signature",
            "header.payload.signature",
        ),
    )
    for headers, body, expected in cases:
        framed_body = body
        if b"Transfer-Encoding: chunked" in headers:
            framed_body = (b"%x\r\n" % len(body)) + body + b"\r\n0\r\n\r\n"
        raw = b"HTTP/1.1 200 OK\r\n" + headers + b"\r\n\r\n" + framed_body

        class FakeSocket:
            def __init__(self):
                self.chunks = [raw, b""]
                self.request = b""

            def settimeout(self, value):
                assert value == 5

            def connect(self, path):
                assert path == "/run/container_launcher/teeserver.sock"

            def sendall(self, data):
                self.request = data

            def recv(self, size):
                del size
                return self.chunks.pop(0)

            def close(self):
                pass

        sock = FakeSocket()
        assert LauncherTokenSource(socket_factory=lambda *args: sock).fetch(
            audience="aud", nonce="nonce-1234"
        ) == expected
        assert sock.request.startswith(b"POST /v1/token HTTP/1.1\r\nHost: localhost\r\n")


def test_launcher_redacts_invalid_response_body_from_production_errors():
    secret = b"header.payload.extra.secret-never-log-this"
    raw = (
        b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: "
        + str(len(secret)).encode("ascii")
        + b"\r\n\r\n"
        + secret
    )

    class FakeSocket:
        def settimeout(self, value):
            pass

        def connect(self, path):
            pass

        def sendall(self, data):
            pass

        def recv(self, size):
            del size
            if not hasattr(self, "sent"):
                self.sent = True
                return raw
            return b""

        def close(self):
            pass

    with pytest.raises(AttestationError, match="not_token") as error:
        LauncherTokenSource(socket_factory=lambda *args: FakeSocket()).fetch(
            audience="aud", nonce="nonce-1234"
        )
    assert secret.decode("ascii") not in str(error.value)


def test_launcher_rejects_oversized_response():
    class OversizedSocket:
        def settimeout(self, value): pass
        def connect(self, path): pass
        def sendall(self, data): pass
        def recv(self, size):
            return b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 65537\r\n\r\n"
        def close(self): pass

    with pytest.raises(AttestationError, match="too large"):
        LauncherTokenSource(socket_factory=lambda *args: OversizedSocket()).fetch(audience="aud", nonce="nonce-1234")


    from services.p5_r0_evaluator.confidential_space import CONFIDENTIAL_SPACE_LAUNCHER_SOCKET
    with pytest.raises(AttestationError):
        LauncherTokenSource("/tmp/attacker.sock")
    assert CONFIDENTIAL_SPACE_LAUNCHER_SOCKET == "/run/container_launcher/teeserver.sock"
    inner = MemoryStore()
    run_a = RunScopedObjectStore(inner, "sha256:" + "a" * 64)
    run_b = RunScopedObjectStore(inner, "sha256:" + "b" * 64)
    run_a.create("runs/sha256:" + "a" * 64 + "/receipts/000001.json", b"{}")
    run_a.create("runs/sha256:" + "a" * 64 + "/timing/000001-task_issued.json", b"{}")
    run_a.create("runs/sha256:" + "a" * 64 + "/evidence/000001.json", b"{}")
    run_a.create("runs/sha256:" + "a" * 64 + "/compute-class/observation-000001.json", b"{}")
    run_a.create("runs/sha256:" + "a" * 64 + "/idempotency/start-sha256:" + "c" * 64 + ".json", b"{}")
    with pytest.raises(Exception):
        run_a.get("runs/sha256:" + "b" * 64 + "/state.json")
    with pytest.raises(Exception):
        run_b.get("runs/sha256:" + "a" * 64 + "/state.json")
    with pytest.raises(Exception):
        run_a.create("/runs/sha256:" + "a" * 64 + "/state.json", b"{}")


def test_independent_timing_signature_and_sequence_are_verified():
    from datetime import datetime, timezone
    from services.p5_r0_evaluator.timing import TimingAttestationError
    key = Ed25519PrivateKey.generate()
    public = b64encode(key.public_key().public_bytes_raw())
    payload = digest("payload")
    value = {"schema": "P5R0IndependentTimingAttestationV2", "ledger_id": "ledger", "run_id": "run", "task_id": "task", "event": "task_issued", "sequence": 1, "previous_digest": None, "seed_digest": digest("seed"), "payload_digest": payload, "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "authority_id": "independent", "key_id": "ledger-key", "public_key": public, "public_key_digest": digest(public), "signature": ""}
    value["signature"] = b64encode(key.sign(signing_digest(value)))
    validate_attestation(value, run_id="run", task_id="task", event="task_issued", payload_digest=payload, expected_authority_id="independent", expected_key_id="ledger-key", expected_public_key_digest=digest(public), last_sequence=0)
    value["payload_digest"] = digest("forged")
    with pytest.raises(TimingAttestationError):
        validate_attestation(value, run_id="run", task_id="task", event="task_issued", payload_digest=payload, expected_authority_id="independent", expected_key_id="ledger-key", expected_public_key_digest=digest(public), last_sequence=0)



def test_locked_policy_nested_values_are_immutable():
    config, _ = _config()
    with pytest.raises(TypeError):
        config.claim_paths["audience"] = "forged"
    with pytest.raises(TypeError):
        config.authority["public_key"] = "forged"
    with pytest.raises(TypeError):
        config.authority["transport_attestation"]["provider"] = "forged"



def test_runtime_policy_rejects_foreign_wip_project():
    config, key = _config()
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {"schema": "P5R0PublicAuthorityV4", "authority_id": "authority", "key_id": "key", "public_key": public, "public_key_digest": digest(public), "transport_attestation": {"schema": "P5R0AuthorityTransportV1", "provider": config.wip_provider, "audience": config.attestation_audience, "event": "confidential_space_attestation"}}
    env = _env_for_config(config, authority)
    foreign = "//iam.googleapis.com/projects/999/locations/global/workloadIdentityPools/pool/providers/provider"
    env["P5R0_WIP_PROVIDER"] = foreign
    env["P5R0_ATTESTATION_AUDIENCE"] = foreign
    with pytest.raises(RuntimeError, match="canonical WIP provider"):
        LockedBootstrapConfig.from_env(env)



# These boundary tests use only local fakes; no ADC, credentials, network, or cloud resources.
def test_local_mocks_reject_ambient_gcs_and_kms_client_construction():
    with pytest.raises(StoreError, match="explicit federated GCS client"):
        GCSStore("private-bucket")

    config, _ = _config()
    with pytest.raises(KMSConfigurationError, match="explicit federated KMS client"):
        KMSEd25519Signer(config.kms_key_version, config.authority)


def test_local_locked_bootstrap_has_no_secret_or_client_access_before_attestation():
    config, _ = _config()
    source = FakeSource()
    verifier = FakeVerifier(_claims(config))
    sts = FakeSTS()
    built = []
    factory = type("LocalMockCapabilityFactory", (), {
        "build": lambda self, token: built.append(token) or object(),
    })()
    adapter = ConfidentialSpaceAdapter(
        config, source=source, verifier=verifier, sts=sts,
        capability_factory=factory, service_factory=lambda capabilities: object(),
    )

    assert adapter.attested is False
    status, _, body = adapter.dispatch("GET", "/healthz", b"", {})
    assert status == 200 and parse_canonical(body)["status"] == "locked"
    assert source.calls == [] and verifier.calls == [] and sts.calls == [] and built == []


def test_local_mock_wip_claim_mismatch_is_rejected_before_federation():
    config, _ = _config()
    source = FakeSource()
    verifier = FakeVerifier(_claims(config, project_id="foreign-project"))
    gate = AttestationGate(config, source, verifier)

    with pytest.raises(AttestationError, match="project_id mismatch"):
        gate.verify_startup()

    assert source.calls and verifier.calls


@pytest.mark.parametrize(
    "binding",
    ("P5R0_POLICY_DIGEST", "P5R0_CLAIM_PATHS_DIGEST", "P5R0_ATTESTATION_CLAIMS_DIGEST", "P5R0_WIP_POLICY_DIGEST"),
)
def test_local_policy_commitment_mutation_is_rejected(binding):
    config, key = _config()
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {
        "schema": "P5R0PublicAuthorityV4", "authority_id": "authority", "key_id": "key",
        "public_key": public, "public_key_digest": digest(public),
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1", "provider": config.wip_provider,
            "audience": config.attestation_audience, "event": "confidential_space_attestation",
        },
    }
    env = _env_for_config(config, authority)
    env[binding] = digest({"forged": binding})

    with pytest.raises(RuntimeError, match="does not match immutable policy"):
        LockedBootstrapConfig.from_env(env)


def _local_timing_v2(key, *, run_id="run", task_id="task", event="task_issued", sequence=1,
                     previous_digest=None, authority_id="independent", key_id="ledger-key",
                     ledger_id="ledger", payload_digest=None):
    from datetime import datetime, timezone

    value = {
        "schema": "P5R0IndependentTimingAttestationV2", "ledger_id": ledger_id,
        "run_id": run_id, "task_id": task_id, "event": event, "sequence": sequence,
        "previous_digest": previous_digest, "seed_digest": digest("seed"),
        "payload_digest": payload_digest or digest("payload"),
        "observed_at": datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority_id": authority_id, "key_id": key_id,
        "public_key": b64encode(key.public_key().public_bytes_raw()), "public_key_digest": "",
        "signature": "",
    }
    value["public_key_digest"] = digest(value["public_key"])
    value["signature"] = b64encode(key.sign(signing_digest(value)))
    return value


def test_local_timing_rejects_authority_substitution_and_replayed_record():
    key = Ed25519PrivateKey.generate()
    public_digest = digest(b64encode(key.public_key().public_bytes_raw()))
    payload = digest("payload")
    substituted = _local_timing_v2(key, authority_id="attacker")
    with pytest.raises(TimingAttestationError, match="authority mismatch"):
        validate_attestation(
            substituted, run_id="run", task_id="task", event="task_issued", payload_digest=payload,
            expected_authority_id="independent", expected_key_id="ledger-key",
            expected_ledger_id="ledger", expected_public_key_digest=public_digest,
            last_sequence=0,
        )

    first = _local_timing_v2(key, payload_digest=payload)
    validate_attestation(
        first, run_id="run", task_id="task", event="task_issued", payload_digest=payload,
        expected_authority_id="independent", expected_key_id="ledger-key",
        expected_ledger_id="ledger", expected_public_key_digest=public_digest,
        last_sequence=0,
    )
    with pytest.raises(TimingAttestationError, match="sequence"):
        validate_attestation(
            first, run_id="run", task_id="task", event="task_issued", payload_digest=payload,
            expected_authority_id="independent", expected_key_id="ledger-key",
            expected_ledger_id="ledger", expected_public_key_digest=public_digest,
            last_sequence=1,
        )

    second = _local_timing_v2(key, sequence=2, previous_digest=digest("not-the-first-record"), payload_digest=payload)
    with pytest.raises(TimingAttestationError, match="chain"):
        validate_attestation(
            second, run_id="run", task_id="task", event="task_issued", payload_digest=payload,
            expected_authority_id="independent", expected_key_id="ledger-key",
            expected_ledger_id="ledger", expected_public_key_digest=public_digest,
            previous_digest=digest(first), last_sequence=1,
        )



def test_startup_attestation_evidence_is_non_secret_and_tracks_activation():
    config, key = _config()
    source, verifier, sts = FakeSource(), FakeVerifier(_claims(config)), FakeSTS()
    gcs, kms = FakeGCSClient(), FakeKMSClient(key)
    factory = CapabilityFactory(
        config,
        storage_client_factory=lambda token: gcs,
        kms_client_factory=lambda token: kms,
    )
    adapter = ConfidentialSpaceAdapter(
        config,
        source=source,
        verifier=verifier,
        sts=sts,
        capability_factory=factory,
        service_factory=lambda capabilities: object(),
    )

    status, _, raw = adapter.dispatch("GET", "/startup-attestation", b"", {})
    locked = parse_canonical(raw)
    assert status == 200 and locked["status"] == "locked"
    assert "attestation-token" not in raw.decode()

    adapter.activate_attested_service()
    status, _, raw = adapter.dispatch("GET", "/startup-attestation", b"", {})
    evidence = parse_canonical(raw)
    assert status == 200 and evidence["status"] == "attested"
    assert evidence["attestation"]["verified"] is True
    assert evidence["federation"]["provider"] == config.wip_provider
    assert evidence["attestation"]["token_digest"] == digest("attestation-token")
    assert "attestation-token" not in raw.decode()
    assert "federated" not in raw.decode()


def test_startup_attestation_failure_stays_locked_and_is_observable_without_secret():
    config, _ = _config()

    class FailingSource:
        def fetch(self, **kwargs):
            raise AttestationError("metadata unavailable")

    adapter = ConfidentialSpaceAdapter(
        config,
        source=FailingSource(),
        verifier=FakeVerifier(_claims(config)),
        sts=FakeSTS(),
        capability_factory=type("Factory", (), {"build": lambda self, token: object()})(),
        service_factory=lambda capabilities: object(),
    )
    status, _, _ = adapter.dispatch("POST", "/v1/runs", b"{}", {})
    assert status == 503 and not adapter.attested
    status, _, raw = adapter.dispatch("GET", "/startup-attestation", b"", {})
    evidence = parse_canonical(raw)
    assert status == 200 and evidence["status"] == "locked"
    assert evidence["last_failure"] == "AttestationError"
    assert "metadata unavailable" not in raw.decode()



def test_launcher_token_and_startup_evidence_have_hard_bounds():
    class OversizedSocket:
        def settimeout(self, value): pass
        def connect(self, path): pass
        def sendall(self, data): pass
        def recv(self, size):
            return b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 65537\r\n\r\n"
        def close(self): pass

    source = LauncherTokenSource(socket_factory=lambda *args: OversizedSocket())
    with pytest.raises(AttestationError, match="too large"):
        source.fetch(audience="audience", nonce="nonce-1234")




def test_official_nested_token_fixture_matches_default_production_claim_paths():
    import json
    from pathlib import Path

    config, _ = _config()
    fixture = json.loads((Path(__file__).parent / "fixtures" / "confidential_space_official_token.json").read_text())
    verified = AttestationGate(config, FakeSource(), FakeVerifier(fixture)).verify_startup()
    assert verified.claims["iss"] == "https://confidentialcomputing.googleapis.com"
    assert config.claim_paths == {
        "audience": "aud",
        "nonce": "eat_nonce",
        "issued_at": "iat",
        "expires_at": "exp",
        "issuer": "iss",
        "subject": "sub",
        "image_digest": "submods.container.image_digest",
        "project_number": "submods.gce.project_number",
        "project_id": "submods.gce.project_id",
        "zone": "submods.gce.zone",
        "debug_state": "dbgstat",
        "tee": "swname",
        "hardware_model": "hwmodel",
        "secure_boot": "secboot",
        "workload": "submods.container.env.P5R0_EXPECTED_WORKLOAD",
        "smoke": "submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE",
    }



def test_confidential_space_smoke_disabled_by_default(monkeypatch):
    import importlib
    import os

    config, _ = _config()
    _set_production_env(monkeypatch, config)
    monkeypatch.delenv("P5R0_CONFIDENTIAL_SPACE_SMOKE", raising=False)
    app = importlib.import_module("services.p5_r0_evaluator.confidential_space_app")
    assert app.service.config.confidential_space_smoke is False
    assert app.service.attested is False


def test_confidential_space_smoke_redacts_timing_record(monkeypatch):
    import importlib
    from types import SimpleNamespace

    config, _ = _config()
    _set_production_env(monkeypatch, config)
    app = importlib.import_module("services.p5_r0_evaluator.confidential_space_app")
    emitted = []

    class Attestor:
        independent = True
        def __init__(self):
            self.calls = []
        def record(self, **kwargs):
            self.calls.append(kwargs)
            assert kwargs == {
                "run_id": "sha256:" + "0" * 64,
                "task_id": "sha256:" + "1" * 64,
                "event": "task_issued",
                "payload_digest": "sha256:" + "2" * 64,
            }
            return {"schema": "P5R0IndependentTimingAttestationV3", "sequence": 1, "proof": "secret-proof", "token": "secret-token"}
    attestor = Attestor()
    service = SimpleNamespace(timing_certified=True, timing_attestor=attestor)
    adapter = SimpleNamespace(
        config=replace(config, confidential_space_smoke=True),
        startup_evidence={"schema": "P5R0StartupAttestationEvidenceV1", "status": "attested"},
        activate_attested_service=lambda: service,
    )
    result = app.run_startup_smoke(adapter, emit=emitted.append)
    assert result == {
        "schema": "P5R0ConfidentialSpaceSmokeV1", "status": "passed",
        "startup_evidence_digest": digest(adapter.startup_evidence), "startup_status": "attested", "bootstrap_failure": None,
        "timing_record_digest": digest({"schema": "P5R0IndependentTimingAttestationV3", "sequence": 1, "proof": "secret-proof", "token": "secret-token"}),
        "timing_schema": "P5R0IndependentTimingAttestationV3", "timing_sequence": 1,
    }
    assert len(emitted) == 1
    assert len(attestor.calls) == 1
    assert "secret-proof" not in emitted[0] and "secret-token" not in emitted[0]


def test_confidential_space_smoke_timing_failure_is_redacted_and_fail_closed(monkeypatch):
    import importlib
    from types import SimpleNamespace

    config, _ = _config()
    _set_production_env(monkeypatch, config)
    app = importlib.import_module("services.p5_r0_evaluator.confidential_space_app")
    emitted = []

    class Attestor:
        independent = True
        def record(self, **kwargs):
            raise RuntimeError("raw bridge response and token must not escape")

    service = SimpleNamespace(timing_certified=True, timing_attestor=Attestor())
    adapter = SimpleNamespace(
        config=replace(config, confidential_space_smoke=True),
        startup_evidence={"schema": "P5R0StartupAttestationEvidenceV1", "status": "attested"},
        activate_attested_service=lambda: service,
    )
    with pytest.raises(ConfidentialSpaceError, match="failed closed"):
        app.run_startup_smoke(adapter, emit=emitted.append)
    assert len(emitted) == 1
    assert "raw bridge response" not in emitted[0] and "token" not in emitted[0]
    assert '"status":"failed"' in emitted[0]


def test_verified_binding_rejects_expired_token_and_policy_image_mismatch():
    from dataclasses import replace

    config, _ = _config()
    attestation = AttestationGate(config, FakeSource(), FakeVerifier(_claims(config))).verify_startup()
    with pytest.raises(AttestationBindingError, match="expired"):
        _build_verified_attestation_binding(attestation, FederatedAccessToken("federated", 1), config)

    forged_policy = replace(config, claim_paths={**config.claim_paths, "image_digest": "dbgstat"})
    with pytest.raises(AttestationBindingError, match="image_digest mismatch"):
        _build_verified_attestation_binding(attestation, FederatedAccessToken("federated", 4_000_000_000), forged_policy)

    forged_image = replace(config, image_digest="sha256:" + "f" * 64)
    with pytest.raises(AttestationBindingError, match="image_digest mismatch"):
        _build_verified_attestation_binding(attestation, FederatedAccessToken("federated", 4_000_000_000), forged_image)


def test_verified_binding_cannot_be_constructed_from_public_dict_or_seal():
    config, _ = _config()
    attestation = AttestationGate(config, FakeSource(), FakeVerifier(_claims(config))).verify_startup()
    binding = _build_verified_attestation_binding(attestation, FederatedAccessToken("federated", 4_000_000_000), config)
    public = binding.as_public_dict()
    assert not isinstance(public, VerifiedAttestationBinding)
    with pytest.raises(TypeError, match="adapter-created"):
        VerifiedAttestationBinding(**{key: value for key, value in public.items() if key != "schema"})
    with pytest.raises(TypeError, match="adapter-created"):
        VerifiedAttestationBinding(**{key: value for key, value in public.items() if key != "schema"}, _seal=object())



def test_default_service_retains_binding_but_missing_independent_timing_stays_fail_closed():
    config, key = _config()
    gcs, kms = FakeGCSClient(), FakeKMSClient(key)
    factory = CapabilityFactory(
        config,
        storage_client_factory=lambda token: gcs,
        kms_client_factory=lambda token: kms,
    )
    adapter = ConfidentialSpaceAdapter(
        config,
        source=FakeSource(),
        verifier=FakeVerifier(_claims(config)),
        sts=FakeSTS(),
        capability_factory=factory,
    )
    service = adapter.activate_attested_service()
    assert isinstance(service, __import__("services.p5_r0_evaluator.service", fromlist=["EvaluatorService"]).EvaluatorService)
    assert service.attestation_binding is adapter.attestation_binding
    assert service.attestation_binding is not None
    assert service.timing_certified is False
    assert service.bounded_compute_ready is False
    assert service.bounded_compute_certified is False



def test_gcs_only_capability_account_cannot_activate_shared_kms_factory():
    config, _ = _config()
    config = replace(config, capability_service_account="p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com")
    factory = CapabilityFactory(config, storage_client_factory=lambda token: object(), kms_client_factory=lambda token: object())
    with pytest.raises(STSError, match="separate KMS path is required"):
        factory.build(FederatedAccessToken("federated", 4_000_000_000))
