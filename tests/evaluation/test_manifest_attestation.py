import pytest

from evaluation.p0a.canonical import ProtocolError
from evaluation.p0a.manifest import ManifestVerifier, make_attestation
from conftest import DIGESTS, NOW, PRIVATE, PUBLIC, manifest, verified


def test_manifest_rejects_unsigned_unknown_and_digest_or_method_tampering():
    verifier = ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW)
    unsigned = manifest(); unsigned.pop("signature")
    with pytest.raises(ProtocolError): verifier.verify(unsigned, expected_digests=DIGESTS)
    unknown = manifest(); unknown["key_id"] = "ed25519:unknown"
    with pytest.raises(ProtocolError): verifier.verify(unknown, expected_digests=DIGESTS)
    wrong = manifest(); wrong["agent_build_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ProtocolError): verifier.verify(wrong, expected_digests=DIGESTS)
    with pytest.raises(ProtocolError): verifier.verify(manifest(methods=["x"]), expected_digests=DIGESTS)


def test_manifest_run_id_is_one_time_and_attestation_is_explicitly_local_only():
    verifier = ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW)
    got = verifier.verify(manifest(), expected_digests=DIGESTS)
    attestation = make_attestation(got, endpoint="unix:/run/p0a/test/broker.sock",
                                   started_at_unix_ms=NOW, signer=PRIVATE, key_id="ed25519:test")
    assert attestation["local_harness_only"] is True
    with pytest.raises(ProtocolError): verifier.verify(manifest(), expected_digests=DIGESTS)
