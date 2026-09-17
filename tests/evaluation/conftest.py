from __future__ import annotations

# pytest can put this package ahead of the checkout and resolve an unrelated
# installed `evaluation` distribution.  The harness is repository-local.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p0a.broker import ActionBroker
from evaluation.p0a.canonical import canonical_bytes, object_hash, sha256, sign
from evaluation.p0a.manifest import ManifestVerifier
from evaluation.p0a.provenance import make_native_graph_export_attestation
from evaluation.p0a.receipt_log import ReceiptLog
from evaluation.p0a.simulator import METHOD

NOW = 1_000
DIGESTS = {name: "sha256:" + char * 64 for name, char in (
    ("control_plane_digest", "a"), ("broker_image_digest", "b"),
    ("agent_build_digest", "c"), ("input_snapshot_digest", "d"),
    ("seed_snapshot_digest", "e"),
)}
PRIVATE = Ed25519PrivateKey.from_private_bytes(b"\x01" * 32)
PUBLIC = PRIVATE.public_key()
# A distinct local test authority exercises evaluator-side signing.  It is
# deliberately documented as a same-user fixture, not a cross-user custody boundary.
EXPORT_AUTHORITY_PRIVATE = Ed25519PrivateKey.from_private_bytes(b"\x02" * 32)
EXPORT_AUTHORITY_PUBLIC = EXPORT_AUTHORITY_PRIVATE.public_key()
EXPORT_AUTHORITY_KEYS = {"ed25519:local-test-authority": EXPORT_AUTHORITY_PUBLIC}


def manifest(*, run_id="123e4567-e89b-42d3-a456-426614174000", methods=()):
    body = {"schema": "EvaluationManifestV1", "run_id": run_id, "evaluation": True,
            "issuer": "evaluator.example", "key_id": "ed25519:test", "issued_at_unix_ms": 0,
            "expires_at_unix_ms": 10_000, **DIGESTS, "enabled_methods": list(methods),
            "limits": {"wall_ms": 1, "cpu_ms": 1, "memory_bytes": 1, "max_requests": 10,
                       "max_receipts": 20}, "revocation_generation": 0}
    body["signature"] = sign(body, PRIVATE)
    return body


def verified(*, methods=(), allow_fixture=False, run_id="123e4567-e89b-42d3-a456-426614174000"):
    return ManifestVerifier({"ed25519:test": PUBLIC}, now_ms=lambda: NOW).verify(
        manifest(run_id=run_id, methods=methods), expected_digests=DIGESTS,
        allow_fixture_methods=allow_fixture)


def request(run_id, *, request_id="123e4567-e89b-42d3-a456-426614174001", nonce="A" * 43,
            method=METHOD, args=None):
    body = {"schema": "ActionRequestV1", "request_id": request_id, "run_id": run_id,
            "sequence": 1, "nonce": nonce, "created_at_unix_ms": 0, "expires_at_unix_ms": 9_000,
            "method": method, "args": args if args is not None else {"steps": 2}, "input_refs": [],
            "input_snapshot_digest": DIGESTS["input_snapshot_digest"],
            "causal_parent_receipt_hash": None,
            "requested_budget": {"wall_ms": 0, "cpu_ms": 0, "memory_bytes": 0, "writes": 0,
                                 "network_bytes": 0}}
    body["request_hash"] = object_hash(body)
    return body


def grant(req, *, run_id=None, method=None, args_hash=None, expires=9_000, uses=1, revocation=0):
    body = {"schema": "CapabilityGrantV1", "grant_id": "123e4567-e89b-42d3-a456-426614174002",
            "run_id": run_id or req["run_id"], "issuer": "evaluator.example", "key_id": "ed25519:test",
            "request_hash": req["request_hash"], "method": method or req["method"],
            "normalized_args_hash": args_hash or sha256(req["args"]),
            "input_snapshot_digest": req["input_snapshot_digest"], "not_before_unix_ms": 0,
            "expires_at_unix_ms": expires,
            "quota": {"uses": uses, "wall_ms": 0, "cpu_ms": 0, "memory_bytes": 0, "writes": 0,
                      "network_bytes": 0}, "revocation_generation": revocation}
    body["signature"] = sign(body, PRIVATE)
    return body


def broker(tmp_path, *, p0=False):
    vm = verified(methods=() if p0 else (METHOD,), allow_fixture=not p0)
    log = ReceiptLog(tmp_path, manifest_hash=vm.manifest_hash,
                     broker_image_digest=DIGESTS["broker_image_digest"],
                     input_digest=DIGESTS["input_snapshot_digest"], signer=PRIVATE,
                     writer_public_key=PUBLIC, now_ms=lambda: NOW)
    return ActionBroker(vm, grant_keys={"ed25519:test": PUBLIC}, receipt_log=log,
                        now_ms=lambda: NOW, fixture_registry=True)


def raw(obj):
    return canonical_bytes(obj)



def native_graph_export(*proposals, run_id="123e4567-e89b-42d3-a456-426614174000",
                        expires_at_unix_ms=10_000):
    """Canonical native capture fixture; caller must also provide its attestation."""
    evidence = [{
        "proposal_id": proposal["proposal_id"],
        "proposal_digest": proposal["proposal_digest"],
        "proposal": proposal,
        "source": proposal["source"],
        "causal_parent_receipt_hash": proposal["causal_parent_receipt_hash"],
        "graph_logical_time": proposal["graph_logical_time"],
    } for proposal in proposals]
    body = {
        "schema": "NativeGraphEvidenceExportV1", "run_id": run_id,
        "input_snapshot_digest": DIGESTS["input_snapshot_digest"],
        "issued_at_unix_ms": 0, "expires_at_unix_ms": expires_at_unix_ms,
        "evidence": evidence,
    }
    body["export_digest"] = object_hash(body, "export_digest")
    return canonical_bytes(body)


def native_graph_export_attestation(native_export, *, run_id, capture_sequence=1,
                                     captured_at_unix_ms=NOW, signer=EXPORT_AUTHORITY_PRIVATE,
                                     key_id="ed25519:local-test-authority"):
    """Same-user local test fixture, not a claim of evaluator custody."""
    return make_native_graph_export_attestation(
        native_export, run_id=run_id, agent_build_digest=DIGESTS["agent_build_digest"],
        control_plane_digest=DIGESTS["control_plane_digest"],
        input_snapshot_digest=DIGESTS["input_snapshot_digest"],
        capture_sequence=capture_sequence, captured_at_unix_ms=captured_at_unix_ms,
        signer=signer, key_id=key_id,
    )


from fake_sandbox import FakeCgroupController, FakeSandboxLauncher, fake_sandbox



def staged_receipt_log(tmp_path, body):
    """Evaluator-owned receipt root for protocol fixture runs."""
    from evaluation.p0a.run_paths import RunPaths
    control_root = tmp_path / "evaluator-control"
    paths = RunPaths.for_verified_run(control_root, run_id=body["run_id"], verified_manifest_hash=object_hash(body))
    log = ReceiptLog(paths.receipts_root, manifest_hash=object_hash(body),
                     broker_image_digest=DIGESTS["broker_image_digest"],
                     input_digest=DIGESTS["input_snapshot_digest"], signer=PRIVATE,
                     writer_public_key=PUBLIC, now_ms=lambda: NOW, run_paths=paths)
    return log, control_root
