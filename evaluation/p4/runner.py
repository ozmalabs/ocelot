import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from evaluation.p0a.canonical import b64decode, b64encode, canonical_bytes, object_hash, parse_canonical, sha256, sign, verify_signature
from .fixtures import load_bundle, materialize
from .podman import (P4PodmanLauncher, P4PodmanSpec, PodmanPolicyUnavailable,
                     PROCFS_STARTUP_EVIDENCE, build_local_image)
from .protocol import (ARMS, ARM_CATALOG_SCHEMA, P4ProtocolError, SELECTION_SCHEMA,
                       SUPPORTED_ACTION_KINDS, arm_digest, is_digest, validate_arm)
from .receipts import payload
from .runtime import post_build_runtime_probe, stage_embedded_image_context, stage_runtime_context
from .seccomp import validate_seccomp_profile
from .staging import closure_digests, digest_file, validate_closure

LIMITS = {"domains": 2, "steps": 8, "information_interventions": 1, "mistaken_actions": 1, "replans": 1, "candidate_branches": 12, "hypotheses": 2, "action_grants": 8, "risk_units": 8, "transactions": 8, "frame_bytes": 65536, "wall_seconds": 3}
ROOT = Path(__file__).resolve().parents[2]
_CLOSURE_KEYS = {"worker", "agent", "input", "seccomp", "container_spec"}
_RUNTIME_CLOSURE_KEYS = _CLOSURE_KEYS | {"runtime"}
_ARTIFACT_KEYS = {"preregistration", "fixtures", "arms", "native_export"}
_GRANT_KINDS = tuple(sorted(SUPPORTED_ACTION_KINDS))
_ARM_CATALOG_PATH = Path(__file__).resolve().parent / "fixtures" / "p4_r0_mechanics_arms_v1.json"
_AUTHORITY_FIELDS = {"schema", "authority_id", "key_id", "public_key"}
_TRUST_ARTIFACT_NAME = "p4-trusted-evaluator.json"
_TRUST_ARTIFACT_FIELDS = {"schema", "lock_digest", "evaluator_authority", "fixture_catalog", "arm_catalog", "fixture_selection"}
_FIXTURE_SELECTION_FIELDS = {"schema", "bundle_digest", "fixture_key", "actions", "observations", "steps", "record_digest", "selection_id"}


def _inputs(preregistration: Path, fixtures: Path) -> dict[str, str]:
    paths = {"preregistration": preregistration, "fixtures": fixtures, "arms": _ARM_CATALOG_PATH, "native_export": ROOT / "runners/dsl/src/p4_readiness.rs"}
    out = {}
    for name, path in paths.items():
        path = Path(path)
        if path.is_symlink() or not path.is_file():
            raise P4ProtocolError(f"locked {name}")
        out[name] = sha256(path.read_bytes())
    return out


def _lock_content(lock: dict[str, Any]) -> str:
    # The trust artifact is embedded in the image and contains this stable
    # authority/content identity.  The final image digest is signed separately
    # (see sign(..., "lock_digest")) and independently checked after build;
    # excluding it here avoids the image/trust digest cycle.
    return object_hash(lock, "trusted_evaluator_digest", "image_digest", "lock_digest", "signature")


def _valid_identifier(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and len(value) <= 128 and all(char.isascii() and (char.isalnum() or char in "-_.:") for char in value)


def _validate_evaluator_authority(authority: Any) -> dict[str, str]:
    if not isinstance(authority, dict) or set(authority) != _AUTHORITY_FIELDS or authority.get("schema") != "P4R0EvaluatorAuthorityV1":
        raise P4ProtocolError("evaluator authority")
    if not _valid_identifier(authority.get("authority_id")) or not _valid_identifier(authority.get("key_id")) or not isinstance(authority.get("public_key"), str):
        raise P4ProtocolError("evaluator authority")
    try:
        if len(b64decode(authority["public_key"])) != 32:
            raise ValueError
        Ed25519PublicKey.from_public_bytes(b64decode(authority["public_key"]))
    except Exception as exc:
        raise P4ProtocolError("evaluator authority") from exc
    return dict(authority)


def _validate_fixture_selection(selection: Any) -> dict[str, Any]:
    if (not isinstance(selection, dict) or set(selection) != _FIXTURE_SELECTION_FIELDS
            or selection.get("schema") != "P4R0FixtureMaterializationV1"
            or not is_digest(selection.get("bundle_digest"))
            or not is_digest(selection.get("record_digest"))
            or not _valid_identifier(selection.get("fixture_key"))
            or not _valid_identifier(selection.get("selection_id"))
            or selection.get("actions") != ["inspect", "reverse", "advance"]
            or selection.get("steps") != 8
            or not isinstance(selection.get("observations"), list)
            or any(not isinstance(item, dict) or set(item) != {"signal"} or type(item["signal"]) is not int for item in selection["observations"])):
        raise P4ProtocolError("fixture selection")
    canonical = {key: selection[key] for key in ("schema", "bundle_digest", "fixture_key", "actions", "observations", "steps")}
    if object_hash(canonical) != selection["record_digest"]:
        raise P4ProtocolError("fixture record digest")
    expected_selection = "sel-" + sha256(("p4-r0-selection:" + selection["fixture_key"] + ":" + selection["bundle_digest"]).encode())[7:23]
    if selection["selection_id"] != expected_selection:
        raise P4ProtocolError("fixture selection id")
    return dict(selection)


def _load_arm_catalog() -> list[dict[str, Any]]:
    try:
        value = parse_canonical(_ARM_CATALOG_PATH.read_bytes())
    except Exception as exc:
        raise P4ProtocolError("mechanics arm catalog") from exc
    if set(value) != {"schema", "arms"} or value["schema"] != ARM_CATALOG_SCHEMA or not isinstance(value["arms"], list):
        raise P4ProtocolError("mechanics arm catalog")
    arms = [validate_arm(row) for row in value["arms"]]
    if [row["arm_id"] for row in arms] != list(ARMS):
        raise P4ProtocolError("mechanics arm catalog order")
    return arms


def _fixture_catalog(fixtures: Path) -> list[dict[str, Any]]:
    records = materialize(fixtures, "p4-r0-locked-catalog")
    return [{key: record[key] for key in _FIXTURE_SELECTION_FIELDS} for record in records]


def _runtime_selection(lock: Mapping[str, Any], run_id: str, fixture_key: str | None = None, arm_id: str | None = None, signer: Any | None = None) -> dict[str, Any]:
    records = lock.get("fixture_catalog")
    arms = lock.get("arm_catalog")
    if not isinstance(records, list) or not isinstance(arms, list):
        raise P4ProtocolError("locked runtime catalog")
    record = next((row for row in records if fixture_key is None or row.get("fixture_key") == fixture_key), None)
    if record is None:
        raise P4ProtocolError("unavailable fixture")
    arm = next((row for row in arms if arm_id is None or row.get("arm_id") == arm_id), None)
    if arm is None:
        raise P4ProtocolError("unavailable arm")
    _validate_fixture_selection(record)
    validate_arm(arm)
    fixture_id = "run-" + sha256((run_id + record["fixture_key"]).encode())[7:23]
    envelope = {"schema": SELECTION_SCHEMA, "run_id": run_id, "fixture_key": record["fixture_key"], "selection_id": record["selection_id"], "fixture_id": fixture_id, "bundle_digest": record["bundle_digest"], "fixture_record_digest": record["record_digest"], "arm_id": arm["arm_id"], "arm_digest": arm["arm_digest"]}
    envelope["selection_digest"] = object_hash(envelope)
    if signer is not None:
        envelope["signature"] = sign(envelope, signer)
    return {**record, "fixture_id": fixture_id, "fixture_digest": record["bundle_digest"], "arm": arm, **envelope}


def _runtime_fixture(lock: Mapping[str, Any], run_id: str, fixture_key: str | None = None, arm_id: str | None = None, signer: Any | None = None) -> dict[str, Any]:
    return _runtime_selection(lock, run_id, fixture_key, arm_id, signer)


def _lock_fixture_selection(fixtures: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _fixture_catalog(fixtures), _load_arm_catalog()

def validate_local_lock(lock: dict[str, Any]) -> dict[str, Any]:
    fields = {"schema", "non_release", "classification", "custody", "adopted", "promotion_authority", "artifacts", "fixture_catalog", "fixture_selection", "arm_catalog", "closure", "image_digest", "limits", "arms", "grant_kinds", "test_key_id", "test_public_key", "evaluator_authority", "trusted_evaluator_digest", "lock_digest", "signature"}
    if (not isinstance(lock, dict) or set(lock) != fields or lock.get("schema") != "P4R0LocalLockV1"
            or lock.get("non_release") is not True or lock.get("classification") != "local_readiness_only"
            or lock.get("custody") != "local" or lock.get("adopted") is not False or lock.get("promotion_authority") is not False
            or lock.get("limits") != LIMITS or lock.get("arms") != list(ARMS) or lock.get("grant_kinds") != list(_GRANT_KINDS) or not is_digest(lock.get("image_digest"))
            or not isinstance(lock.get("fixture_catalog"), list) or not lock["fixture_catalog"]
            or not isinstance(lock.get("fixture_selection"), dict) or lock["fixture_selection"] != lock["fixture_catalog"][0]
            or any(_validate_fixture_selection(row) != row for row in lock["fixture_catalog"])
            or not isinstance(lock.get("arm_catalog"), list) or [validate_arm(row)["arm_id"] for row in lock["arm_catalog"]] != list(ARMS)
            or not isinstance(lock.get("artifacts"), dict) or set(lock["artifacts"]) != _ARTIFACT_KEYS
            or not isinstance(lock.get("closure"), dict) or set(lock["closure"]) not in (_CLOSURE_KEYS, _RUNTIME_CLOSURE_KEYS)
            or any(not is_digest(value) for value in lock["artifacts"].values())
            or any(not is_digest(value) for value in lock["closure"].values())
            or not is_digest(lock.get("trusted_evaluator_digest"))
            or lock.get("lock_digest") != _lock_content(lock)):
        raise P4ProtocolError("local lock")
    _validate_evaluator_authority(lock.get("evaluator_authority"))
    try:
        verify_signature(lock, Ed25519PublicKey.from_public_bytes(b64decode(lock["test_public_key"])), "lock_digest")
    except Exception as exc:
        raise P4ProtocolError("local lock signature") from exc
    return lock


def _trust_artifact_path(staging_root: Path) -> Path:
    root = Path(staging_root)
    if root.is_symlink() or not root.is_dir():
        raise P4ProtocolError("staging root")
    return root / _TRUST_ARTIFACT_NAME


def _write_trust_artifact(path: Path, trust: dict[str, Any]) -> str:
    if path.is_symlink() or path.exists():
        raise P4ProtocolError("trusted evaluator artifact already exists")
    raw = canonical_bytes(trust)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            os.write(fd, raw)
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise P4ProtocolError("trusted evaluator artifact") from exc
    return sha256(raw)


def _read_trust_artifact(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise P4ProtocolError("trusted evaluator artifact")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            raw = bytearray()
            while block := os.read(fd, 65536):
                raw.extend(block)
                if len(raw) > LIMITS["frame_bytes"]:
                    raise P4ProtocolError("trusted evaluator artifact")
        finally:
            os.close(fd)
        trust = parse_canonical(bytes(raw))
    except (OSError, ValueError) as exc:
        raise P4ProtocolError("trusted evaluator artifact") from exc
    if set(trust) != _TRUST_ARTIFACT_FIELDS or trust.get("schema") != "P4R0TrustedEvaluatorArtifactV1" or not is_digest(trust.get("lock_digest")):
        raise P4ProtocolError("trusted evaluator artifact")
    trust["evaluator_authority"] = _validate_evaluator_authority(trust.get("evaluator_authority"))
    if not isinstance(trust.get("fixture_catalog"), list) or not isinstance(trust.get("arm_catalog"), list):
        raise P4ProtocolError("trusted evaluator catalog")
    trust["fixture_catalog"] = [_validate_fixture_selection(row) for row in trust["fixture_catalog"]]
    trust["fixture_selection"] = _validate_fixture_selection(trust["fixture_selection"])
    trust["arm_catalog"] = [validate_arm(row) for row in trust["arm_catalog"]]
    return trust


def _staged_evaluator_authority(spec: P4PodmanSpec, lock: Mapping[str, Any]) -> dict[str, str]:
    path = spec.trusted_evaluator_artifact()
    root = Path(spec.staging_root).resolve(strict=True)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise P4ProtocolError("trusted evaluator artifact") from exc
    if root not in resolved.parents or path.is_symlink() or digest_file(path) != lock["trusted_evaluator_digest"]:
        raise P4ProtocolError("trusted evaluator artifact")
    trust = _read_trust_artifact(path)
    authority = trust["evaluator_authority"]
    if trust["lock_digest"] != lock["lock_digest"] or authority != lock["evaluator_authority"] or trust["fixture_catalog"] != lock["fixture_catalog"] or trust["arm_catalog"] != lock["arm_catalog"] or trust["fixture_selection"] != lock["fixture_selection"]:
        raise P4ProtocolError("lock-bound evaluator authority")
    return authority


def preregister_local(preregistration: Path, fixtures: Path, staging_root: Path, out: Path, *, image_digest: str | None, worker_binary: Path, agent_root: Path, input_root: Path, seccomp_profile: Path, container_spec: Path, evaluator_public_key: str | None = None, evaluator_key_id: str = "p4-r0-local-evaluator", evaluator_authority_id: str = "p4-r0-evaluator") -> dict[str, Any]:
    load_bundle(fixtures)
    fixture_catalog, arm_catalog = _lock_fixture_selection(fixtures)
    if image_digest is not None and not is_digest(image_digest):
        raise P4ProtocolError("digest-pinned image required")
    if not _valid_identifier(evaluator_key_id) or not _valid_identifier(evaluator_authority_id):
        raise P4ProtocolError("evaluator authority")
    if evaluator_public_key is None:
        evaluator_public_key = b64encode(Ed25519PrivateKey.generate().public_key().public_bytes_raw())
    evaluator_authority = _validate_evaluator_authority({"schema": "P4R0EvaluatorAuthorityV1", "authority_id": evaluator_authority_id, "key_id": evaluator_key_id, "public_key": evaluator_public_key})
    staging_root = Path(staging_root)
    if staging_root.is_symlink():
        raise P4ProtocolError("symlink staging")
    staging_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    worker_binary = Path(worker_binary)
    seccomp_profile = Path(seccomp_profile)
    runtime_path = staging_root / "runtime"
    native_worker = False
    try:
        native_worker = worker_binary.read_bytes()[:4] == b"\x7fELF"
    except OSError as exc:
        raise P4ProtocolError("native worker unavailable") from exc
    if not native_worker and image_digest is None:
        raise P4ProtocolError("digest-pinned image required")
    provisional_image_digest = image_digest or ("sha256:" + "0" * 64)
    if native_worker:
        # Native readiness cannot be registered from a host-dependent loader.
        # Measure startup first, then stage the exact finite closure locally.
        post_build_runtime_probe(worker_binary)
        try:
            validate_seccomp_profile(seccomp_profile, worker=worker_binary)
        except P4ProtocolError:
            raise
        stage_runtime_context(context=runtime_path, worker=worker_binary,
                              containerfile=Path(container_spec))
    closure_paths = {"worker": worker_binary, "agent": Path(agent_root), "input": Path(input_root), "seccomp": seccomp_profile, "container_spec": Path(container_spec)}
    if native_worker:
        closure_paths["runtime"] = runtime_path
    closure = closure_digests(staging_root, closure_paths)
    validate_closure(staging_root, closure_paths, closure)
    key = Ed25519PrivateKey.generate()
    pub = b64encode(key.public_key().public_bytes_raw())
    body = {"schema": "P4R0LocalLockV1", "non_release": True, "classification": "local_readiness_only", "custody": "local", "adopted": False, "promotion_authority": False, "artifacts": _inputs(preregistration, fixtures), "fixture_catalog": fixture_catalog, "fixture_selection": fixture_catalog[0], "arm_catalog": arm_catalog, "closure": closure, "image_digest": provisional_image_digest, "limits": LIMITS, "arms": list(ARMS), "grant_kinds": list(_GRANT_KINDS), "test_key_id": "p4-r0-ephemeral-local-lock-key", "test_public_key": pub, "evaluator_authority": evaluator_authority, "trusted_evaluator_digest": "sha256:" + "0" * 64}
    body["lock_digest"] = _lock_content(body)
    trust = {"schema": "P4R0TrustedEvaluatorArtifactV1", "lock_digest": body["lock_digest"], "evaluator_authority": evaluator_authority, "fixture_catalog": fixture_catalog, "fixture_selection": fixture_catalog[0], "arm_catalog": arm_catalog}
    body["trusted_evaluator_digest"] = _write_trust_artifact(_trust_artifact_path(staging_root), trust)
    if native_worker:
        # Build only after the authority artifact exists, so the exact bytes
        # embedded in /trust and /input are part of the finite image context.
        image_context = staging_root / "image-context"
        stage_embedded_image_context(context=image_context, worker=worker_binary,
                                     containerfile=Path(container_spec),
                                     trust_artifact=_trust_artifact_path(staging_root),
                                     fixture=Path(fixtures),
                                     arms=_ARM_CATALOG_PATH)
        tag = "localhost/p4-r0-local-" + provisional_image_digest[-16:].replace(":", "")
        built_digest = build_local_image(
            podman="podman", context=image_context, tag=tag,
            expected_digest=image_digest)
        body["image_digest"] = built_digest
    body["signature"] = sign(body, key, "lock_digest")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(canonical_bytes(body))
    return body


def _assert_evaluator_authority(lock: Mapping[str, Any], evaluator: Any, receipts: Any, authority: Mapping[str, str]) -> dict[str, str]:
    authority = _validate_evaluator_authority(authority)
    if (authority != lock["evaluator_authority"] or getattr(evaluator, "lock", None) != lock or getattr(evaluator, "receipts", None) is not receipts
            or not hasattr(receipts, "public_key")
            or b64encode(receipts.public_key.public_bytes_raw()) != authority["public_key"]
            or getattr(receipts, "authority_id", authority["authority_id"]) != authority["authority_id"]
            or getattr(receipts, "key_id", authority["key_id"]) != authority["key_id"]):
        raise P4ProtocolError("lock-bound evaluator authority")
    return authority


def _native_request(lock: dict[str, Any], evaluator: Any, receipts: Any, run_id: str, snapshot: str, authority: Mapping[str, str] | None = None, *, fixture_key: str | None = None, arm_id: str | None = None) -> dict[str, Any]:
    authority = _assert_evaluator_authority(lock, evaluator, receipts, authority or lock["evaluator_authority"])
    fixture = _runtime_fixture(lock, run_id, fixture_key, arm_id, receipts.signer)
    selection = {key: fixture[key] for key in ("schema", "run_id", "fixture_key", "selection_id", "fixture_id", "bundle_digest", "fixture_record_digest", "arm_id", "arm_digest", "selection_digest", "signature")}
    evaluator.bind_selection(selection)
    resources = {"actions": 0, "risk": 0, "transactions": 0}
    receipt_context = {"fixture_key": fixture["fixture_key"], "fixture_record_digest": fixture["record_digest"], "fixture_id": fixture["fixture_id"], "fixture_selection_id": fixture["selection_id"], "selection_digest": fixture["selection_digest"], "arm_id": fixture["arm_id"], "arm_digest": fixture["arm_digest"]}
    release = evaluator.release(run_id, fixture["fixture_id"], 1, None)
    receipts.append("task_release", payload(run_id=run_id, lock_digest=lock["lock_digest"], fixture_digest=fixture["bundle_digest"], snapshot_digest=snapshot, outcome="released", reason="native_readiness_release", resources=resources, binding={"envelope_digest": release["envelope_digest"], **receipt_context}, fixture_record_digest=fixture["record_digest"], fixture_id=fixture["fixture_id"], fixture_selection_id=fixture["selection_id"], fixture_key=fixture["fixture_key"], selection_digest=fixture["selection_digest"], arm_id=fixture["arm_id"], arm_digest=fixture["arm_digest"]))
    replan = receipts.append("replan", payload(run_id=run_id, lock_digest=lock["lock_digest"], fixture_digest=fixture["bundle_digest"], snapshot_digest=snapshot, outcome="verified", reason="verified_replan", resources=resources, binding=receipt_context, fixture_record_digest=fixture["record_digest"], fixture_id=fixture["fixture_id"], fixture_selection_id=fixture["selection_id"], fixture_key=fixture["fixture_key"], selection_digest=fixture["selection_digest"], arm_id=fixture["arm_id"], arm_digest=fixture["arm_digest"]))
    proposal = {"schema": "GraphActionProposalV1", "proposal_id": "p4-r0-native-action", "run_id": run_id, "sequence": 3, "kind": fixture["actions"][0], "causal_parent_receipt_hash": replan["receipt_hash"], "reservation": {"actions": 1, "risk": 1, "transactions": 1}, "graph_digest": snapshot, "selection_digest": fixture["selection_digest"], "arm_digest": fixture["arm_digest"]}
    proposal["proposal_digest"] = object_hash(proposal)
    outcome = evaluator.act(proposal, evaluator.grant(proposal, 0), 0)
    native = evaluator.verified_native_outcome(outcome)
    if (native["run_id"] != run_id or native["snapshot_digest"] != snapshot
            or native["proposal_digest"] != proposal["proposal_digest"]
            or native["fixture_record_digest"] != fixture["record_digest"]
            or native["selection_digest"] != fixture["selection_digest"]
            or native["arm_digest"] != fixture["arm_digest"]):
        raise P4ProtocolError("native outcome binding")
    return {"schema": "P4NativeReadinessRequestV1", "run_id": run_id, "runtime_selection": selection, "selection_id": fixture["selection_id"], "fixture_key": fixture["fixture_key"], "fixture_id": fixture["fixture_id"], "bundle_digest": fixture["bundle_digest"], "record_digest": fixture["record_digest"], "arm_id": fixture["arm_id"], "arm_digest": fixture["arm_digest"], "selection_digest": fixture["selection_digest"], "actions": fixture["actions"], "observations": fixture["observations"], "steps": fixture["steps"], "snapshot_digest": snapshot, "replan_receipt_digest": replan["receipt_hash"], "proposal_digest": proposal["proposal_digest"], "reservation_digest": native["reservation_digest"], "outcome_receipt_digest": native["outcome_receipt_digest"], "outcomes": [evaluator.serialized_verified_native_outcome(outcome).decode("ascii")]}


def _invoke_native_worker(launcher: P4PodmanLauncher, spec: P4PodmanSpec, lock: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    frame = canonical_bytes(request)
    if len(frame) > LIMITS["frame_bytes"]:
        raise P4ProtocolError("native worker input frame bound")
    argv = launcher.argv(spec, lock["closure"], lock["trusted_evaluator_digest"])
    try:
        completed = subprocess.run(argv, input=frame, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   timeout=LIMITS["wall_seconds"], check=False,
                                   env={"PATH": os.environ.get("PATH", "")})
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise P4ProtocolError("native worker unavailable") from exc
    if (completed.returncode != 0
            or len(completed.stdout) > LIMITS["frame_bytes"]
            or len(completed.stderr) > LIMITS["frame_bytes"]):
        evidence = completed.stderr.decode("utf-8", "replace").strip()
        if PROCFS_STARTUP_EVIDENCE in evidence:
            raise PodmanPolicyUnavailable(f"procfs startup unavailable: {PROCFS_STARTUP_EVIDENCE}")
        raise P4ProtocolError("native worker rejected")
    try:
        reply = parse_canonical(completed.stdout)
    except Exception as exc:
        raise P4ProtocolError("native worker reply") from exc
    if reply != {"schema": "P4NativeReadinessReplyV1", "status": "complete"}:
        raise P4ProtocolError("native worker rejected")
    return reply


def run_local(lock: dict[str, Any], evaluator: Any, receipts: Any, run_id: str = "p4-r0", *, podman_spec: Any | None = None, launcher: Any | None = None) -> dict[str, Any]:
    lock = validate_local_lock(lock)
    snap = evaluator.pre_run_graph_snapshot_digest
    fixture = _runtime_fixture(lock, run_id)
    fixture_args = {"fixture_digest": fixture["bundle_digest"], "fixture_record_digest": fixture["record_digest"], "fixture_id": fixture["fixture_id"], "fixture_selection_id": fixture["selection_id"], "fixture_key": fixture["fixture_key"], "selection_digest": fixture["selection_digest"], "arm_id": fixture["arm_id"], "arm_digest": fixture["arm_digest"]}
    resources = {"actions": 0, "risk": 0, "transactions": 0}
    try:
        # Readiness certification has one production containment boundary. Test
        # harnesses may invoke a worker directly but cannot call this path.
        if type(podman_spec) is not P4PodmanSpec or type(launcher) is not P4PodmanLauncher:
            raise P4ProtocolError("hardened Podman containment required")
        if podman_spec.image_digest != lock["image_digest"] or podman_spec.seccomp_digest != lock["closure"]["seccomp"]:
            raise P4ProtocolError("locked containment substitution")
        validate_closure(podman_spec.staging_root, podman_spec.closure_artifacts(), lock["closure"])
        authority = _staged_evaluator_authority(podman_spec, lock)
        launcher.preflight(podman_spec, lock["closure"], lock["trusted_evaluator_digest"])
        request = _native_request(lock, evaluator, receipts, run_id, snap, authority)
        _invoke_native_worker(launcher, podman_spec, lock, request)
        receipts.append("terminal", payload(run_id=run_id, lock_digest=lock["lock_digest"], snapshot_digest=snap, outcome="verified", reason="native_complete", resources=evaluator.reserved, **fixture_args))
        execution = "complete"
    except Exception as exc:
        detail = str(exc).replace("\n", " ")[:256]
        reason = f"containment:{type(exc).__name__}"
        if detail:
            reason += f":{detail}"
        receipts.append("impasse", payload(run_id=run_id, lock_digest=lock["lock_digest"], snapshot_digest=snap, outcome="impasse", reason=reason, resources=resources, **fixture_args))
        execution = "impasse"
    receipts.append("result", payload(run_id=run_id, lock_digest=lock["lock_digest"], snapshot_digest=snap, outcome="no_go", reason="local_readiness_only", resources=resources, **fixture_args))
    restored = evaluator.restore()
    rollback_binding = {"pre_run_snapshot_digest": snap, "restored_snapshot_digest": restored, "snapshot_encoding": "canonical-deep"}
    if evaluator.active_selection is not None:
        rollback_binding.update({"fixture_key": fixture["fixture_key"], "selection_digest": fixture["selection_digest"], "arm_id": fixture["arm_id"], "arm_digest": fixture["arm_digest"], "fixture_record_digest": fixture["record_digest"]})
    rollback = receipts.append("rollback", payload(run_id=run_id, lock_digest=lock["lock_digest"], snapshot_digest=restored, outcome="restored", reason="exact_pre_run_snapshot", resources=resources, binding=rollback_binding, **fixture_args))
    return {"classification": "local_readiness_only", "custody": "local", "outcome": "no_go", "adopted": False, "promotion_authority": False, "rollback_digest": restored, "rollback_receipt_digest": rollback["receipt_hash"], "execution": execution}


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    command = subparsers.add_parser("preregister-local")
    for name in ("preregistration", "fixtures", "staging-root", "out", "worker-binary", "agent-root", "input-root", "seccomp-profile", "container-spec"):
        command.add_argument(f"--{name}", required=True)
    command.add_argument("--image-digest", required=False)
    command.add_argument("--evaluator-public-key", required=False)
    command.add_argument("--evaluator-key-id", default="p4-r0-local-evaluator")
    args = parser.parse_args()
    if args.cmd == "preregister-local":
        print(json.dumps(preregister_local(Path(args.preregistration), Path(args.fixtures), Path(args.staging_root), Path(args.out), image_digest=args.image_digest, worker_binary=Path(args.worker_binary), agent_root=Path(args.agent_root), input_root=Path(args.input_root), seccomp_profile=Path(args.seccomp_profile), container_spec=Path(args.container_spec), evaluator_public_key=args.evaluator_public_key, evaluator_key_id=args.evaluator_key_id), sort_keys=True))


if __name__ == "__main__":
    main()
