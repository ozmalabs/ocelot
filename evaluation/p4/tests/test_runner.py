from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from evaluation.p0a.canonical import b64encode, sign
from evaluation.p4.evaluator import P4R0Evaluator
from evaluation.p4.podman import P4PodmanLauncher
from evaluation.p4.protocol import P4ProtocolError
from evaluation.p4.receipts import P4ReceiptLog
from evaluation.p4.runner import _lock_content, run_local
from evaluation.p4.tests.helpers import local_lock, staged_spec


def _evaluator(tmp_path, lock):
    # These no-go and containment tests never enter native execution, so they
    # deliberately use an unbound evaluator instead of supplying an authority.
    return P4R0Evaluator(b"seed", {"root": 1}), P4ReceiptLog(tmp_path / "receipts", Ed25519PrivateKey.generate())


def test_local_result_is_no_go_and_non_promotional(tmp_path):
    _, spec = staged_spec(tmp_path)
    lock = local_lock(tmp_path, spec)
    ev, log = _evaluator(tmp_path, lock)
    result = run_local(lock, ev, log)
    assert result["outcome"] == "no_go" and result["classification"] == "local_readiness_only"
    assert result["adopted"] is False and result["promotion_authority"] is False
    assert result["rollback_digest"] == ev.pre_run_graph_snapshot_digest
    log.reload()


def test_tampered_preregistration_lock_is_rejected(tmp_path):
    _, spec = staged_spec(tmp_path, "sha256:" + "b" * 64)
    lock = local_lock(tmp_path, spec)
    lock["image_digest"] = "sha256:" + "c" * 64
    ev, log = _evaluator(tmp_path, lock)
    with pytest.raises(P4ProtocolError):
        run_local(lock, ev, log)


def test_lock_substitution_is_rejected_by_staged_trust_binding(tmp_path):
    _, spec = staged_spec(tmp_path)
    lock = local_lock(tmp_path, spec)
    attacker = Ed25519PrivateKey.generate()
    replacement = dict(lock)
    replacement["test_public_key"] = b64encode(attacker.public_key().public_bytes_raw())
    replacement["evaluator_authority"] = {"schema": "P4R0EvaluatorAuthorityV1", "authority_id": "attacker", "key_id": "attacker-key", "public_key": replacement["test_public_key"]}
    replacement["lock_digest"] = _lock_content(replacement)
    replacement["signature"] = sign(replacement, attacker, "lock_digest")
    ev, log = _evaluator(tmp_path, replacement)
    result = run_local(replacement, ev, log, podman_spec=spec, launcher=P4PodmanLauncher())
    assert result["execution"] == "impasse" and result["outcome"] == "no_go"


def test_staged_authority_tamper_fails_before_podman_preflight(tmp_path):
    _, spec = staged_spec(tmp_path)
    lock = local_lock(tmp_path, spec)
    spec.trusted_evaluator_artifact().write_text("{}")
    result = run_local(lock, *_evaluator(tmp_path, lock), podman_spec=spec, launcher=P4PodmanLauncher())
    assert result["execution"] == "impasse" and result["outcome"] == "no_go"


def test_arbitrary_launcher_cannot_certify_readiness(tmp_path):
    _, spec = staged_spec(tmp_path)
    lock = local_lock(tmp_path, spec)

    class ArbitraryLauncher:
        def preflight(self, *_):
            raise AssertionError("must not be called")

    result = run_local(lock, *_evaluator(tmp_path, lock), podman_spec=spec, launcher=ArbitraryLauncher())
    assert result["execution"] == "impasse" and result["outcome"] == "no_go"


def test_changed_closure_fails_before_preflight(tmp_path):
    _, spec = staged_spec(tmp_path)
    lock = local_lock(tmp_path, spec)
    spec.input_root.joinpath("fixture.json").write_text('{"changed":true}')
    result = run_local(lock, *_evaluator(tmp_path, lock), podman_spec=spec, launcher=P4PodmanLauncher())
    assert result["execution"] == "impasse" and result["outcome"] == "no_go"


def test_real_local_podman_preflight_fails_closed_without_pinned_fixture_image(tmp_path):
    import shutil
    if shutil.which("podman") is None:
        pytest.skip("Podman unavailable")
    _, spec = staged_spec(tmp_path)
    lock = local_lock(tmp_path, spec)
    result = run_local(lock, *_evaluator(tmp_path, lock), podman_spec=spec, launcher=P4PodmanLauncher())
    assert result["outcome"] == "no_go" and result["execution"] == "impasse"
