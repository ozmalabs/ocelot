"""Fail-closed P5-R0 runner with one worker/evaluator path for all evidence."""
from __future__ import annotations
import os, shutil, signal, subprocess, time
from copy import deepcopy
from pathlib import Path
from typing import Any
import json
from typing import Any, Callable
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from evaluation.p0a.canonical import b64encode, canonical_bytes, parse_canonical
from .bounded_compute import (attach_bounded_compute_evidence,
                               bounded_compute_evidence_digest,
                               recompute_bounded_compute_evidence,
                               validate_bounded_compute_evidence)
from .evaluator import P5R0Evaluator
from .fixture_generator import private_store_for, validate_manifest_integrity
from .mutations import record_mutation, record_rejected_reset
from .native import DEFAULT_LIMITS, closure_digest, hardened_crun_argv, runtime_digest, seccomp_digest
from .native_worker import run as validate_worker, validate_reply_v3, validate_task
from .protocol import ARMS, P5R0Error, digest
from .preregister import validate_lock
from .repair import validate_repair_lock
from .receipts import ReceiptChain
from .rollback import Snapshot, rollback_receipt
from .split import build_split_commitment, contrast_matrix
from .scoring import evaluate_gate, score_records


def closure_status(*, podman: str = "podman", image_digest: str | None = None, seccomp_profile: Path | None = None, crun_required: bool = True, locked_closure: dict[str, Any] | None = None, limits: dict[str, Any] | None = None, closure_paths: dict[str, Path] | None = None) -> dict[str, Any]:
    locked = locked_closure or {}; v3 = locked.get("schema") == "P5R0ClosureBindingV3"; expected_digest = locked.get("image_digest")
    if locked and (locked.get("bound") is False or not expected_digest):
        return {"available": False, "reason": "exact locked image/seccomp/closure binding unavailable", "network": "none", "pull": "never", "runtime": "crun"}
    image_digest = image_digest or expected_digest
    if locked and image_digest != expected_digest:
        return {"available": False, "reason": "image digest differs from lock", "network": "none", "pull": "never", "runtime": "crun"}
    if v3 and (closure_paths is None or not {"worker", "runtime"}.issubset(closure_paths) or not isinstance(locked.get("files"), dict)):
        return {"available": False, "reason": "V3 worker/runtime closure staging unavailable", "network": "none", "pull": "never", "runtime": "crun"}
    podman_path = shutil.which(podman); crun_path = shutil.which("crun") if crun_required else "not-required"
    runtime_value = locked.get("runtime_path", crun_path if crun_required else "")
    if v3 and not isinstance(runtime_value, str):
        return {"available": False, "reason": "V3 crun runtime binding unavailable", "network": "none", "pull": "never", "runtime": "crun"}
    profile = Path(seccomp_profile or locked.get("seccomp_profile", "")); runtime_path = Path(runtime_value)
    if not podman_path or (crun_required and not crun_path) or not image_digest or len(image_digest) != 71 or not image_digest.startswith("sha256:") or profile.is_symlink() or not profile.is_file() or (v3 and (runtime_path.is_symlink() or not runtime_path.is_file())):
        return {"available": False, "reason": "locked local crun/Podman image/seccomp closure unavailable", "network": "none", "pull": "never", "runtime": "crun"}
    try:
        info = subprocess.run([podman_path, "info", "--format", "{{.Host.Security.Rootless}}"], text=True, capture_output=True, timeout=2, check=False)
        runtime = subprocess.run([podman_path, "info", "--format", "{{.Host.OCIRuntime.Name}}"], text=True, capture_output=True, timeout=2, check=False)
        image = subprocess.run([podman_path, "image", "inspect", image_digest, "--format", "{{.Id}}"], text=True, capture_output=True, timeout=2, check=False)
        profile_hash = seccomp_digest(profile); runtime_hash = runtime_digest(runtime_path) if v3 else None
        profile_data = json.loads(profile.read_text())
        profile_syscalls = sorted({name for group in profile_data.get("syscalls", []) if group.get("action") == "SCMP_ACT_ALLOW" for name in group.get("names", [])})
        profile_default = profile_data.get("defaultAction")
        argv = hardened_crun_argv(podman=podman_path, image_digest=image_digest, seccomp_profile=profile, limits=dict(limits or DEFAULT_LIMITS))
        staged_paths = dict(closure_paths or {}); staged_paths.setdefault("seccomp_profile", profile)
        if v3 and set(staged_paths) != set(locked.get("files", {})):
            raise P5R0Error("V3 closure file set")
        staged_closure = closure_digest(staged_paths, dict(limits or DEFAULT_LIMITS), schema="P5R0ClosureV3" if v3 else "P5R0ClosureV2") if closure_paths is not None else None
        staged_worker_hash = digest(Path(closure_paths["worker"]).read_bytes()) if v3 else None
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired, P5R0Error):
        return {"available": False, "reason": "Podman preflight failed", "network": "none", "pull": "never", "runtime": "crun"}
    selected = runtime.stdout.strip().lower(); raw_image_id = image.stdout.strip(); image_id = raw_image_id if raw_image_id.startswith("sha256:") else (f"sha256:{raw_image_id}" if raw_image_id else raw_image_id)
    checks = {"rootless": info.returncode == 0 and info.stdout.strip().lower() == "true", "runtime": runtime.returncode == 0 and selected == "crun", "runtime_path": not v3 or str(runtime_path.resolve()) == locked.get("runtime_path"), "runtime_digest": not v3 or runtime_hash == locked.get("runtime_digest"), "image": image.returncode == 0 and image_id == image_digest, "image_ref": not v3 or (isinstance(locked.get("image_ref"), str) and locked["image_ref"].endswith("@" + image_digest)), "seccomp": not locked or profile_hash == locked.get("seccomp_digest"), "syscalls": not locked or (profile_default == locked.get("seccomp_default_action") and profile_syscalls == sorted(locked.get("allowed_syscalls", [])) and digest(profile_syscalls) == locked.get("allowed_syscalls_digest")), "profile_path": not locked or str(profile.resolve()) == locked.get("seccomp_profile"), "worker": not v3 or (staged_worker_hash == locked.get("worker_digest") and locked.get("files", {}).get("worker") == locked.get("worker_digest")), "closure": not locked or (staged_closure is not None and staged_closure == locked.get("closure_digest")), "argv": not locked or digest({"entrypoint": locked.get("entrypoint", "/runtime/p5_r0_worker"), "limits": dict(limits or DEFAULT_LIMITS), "runtime": "crun", "network": "none", "pull": "never"}) == locked.get("argv_digest", digest({"entrypoint": locked.get("entrypoint", "/runtime/p5_r0_worker"), "limits": dict(limits or DEFAULT_LIMITS), "runtime": "crun", "network": "none", "pull": "never"}))}
    available = all(checks.values())
    return {"available": available, "reason": "verified exact rootless crun image/seccomp/worker/runtime closure" if available else "Podman runtime/image/closure identity mismatch", "podman": podman_path, "crun": str(crun_path), "runtime": selected, "runtime_path": str(runtime_path.resolve()), "runtime_digest": runtime_hash, "image_digest": image_id, "locked_image_digest": image_digest, "seccomp_digest": profile_hash, "checks": checks, "argv": argv, "network": "none", "pull": "never", "runtime_required": "crun", "closure_digest": locked.get("closure_digest")}


def _communicate_native(argv: list[str], task_bytes: bytes, *, timeout: int, env: dict[str, str]) -> tuple[Any, int]:
    """Run one worker and explicitly reap its whole process group on timeout."""
    try:
        process = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            close_fds=True, start_new_session=True, env=env,
        )
    except OSError as exc:
        raise P5R0Error("native worker unavailable") from exc
    try:
        stdout, stderr = process.communicate(input=task_bytes, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        cleanup_error: BaseException | None = None
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError as kill_error:
            cleanup_error = kill_error
        try:
            process.wait(timeout=max(1, timeout))
            # Drain pipes after the group is dead.  A second timeout means
            # descendants or the supervisor remain alive; no evidence is safe.
            stdout, stderr = process.communicate(timeout=max(1, timeout))
        except (OSError, subprocess.TimeoutExpired) as wait_error:
            cleanup_error = cleanup_error or wait_error
        if cleanup_error is not None or process.poll() is None:
            raise P5R0Error("native worker timeout cleanup uncertain") from cleanup_error
        raise P5R0Error("native worker timed out") from exc
    except OSError as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=max(1, timeout))
        except Exception:
            raise P5R0Error("native worker cleanup uncertain") from exc
        raise P5R0Error("native worker unavailable") from exc
    return type("Completed", (), {"returncode": process.returncode, "stdout": stdout, "stderr": stderr})(), process.returncode


def _invoke_native_case(*, podman: str, image_digest: str, seccomp_profile: Path, task: dict[str, Any], limits: dict[str, Any] | None = None, allow_invalid: bool = False, protocol_v3: bool = False, return_evidence: bool = False, hardware_profile: dict[str, Any] | None = None, runtime_digest_value: str | None = None, closure_digest_value: str | None = None, run_id: str | None = None, task_id: str | None = None, sequence: int | None = None, attestation_digest: str | None = None, attestation_status: str = "unattested_local") -> int | None | tuple[int | None, dict[str, Any]]:
    # Validate the complete worker frame before constructing or invoking the
    # native subprocess.  This is the V3 privacy/mutation boundary.
    if protocol_v3:
        validate_task(task)
    effective_limits = dict(DEFAULT_LIMITS); effective_limits.update(limits or {})
    if attestation_digest is not None or attestation_status != "unattested_local":
        raise P5R0Error("local native path cannot claim Confidential Space verification")
    argv = hardened_crun_argv(podman=podman, image_digest=image_digest, seccomp_profile=seccomp_profile, limits=limits)
    task_bytes = canonical_bytes(task)
    started_ns = time.monotonic_ns()
    completed, _ = _communicate_native(argv, task_bytes, timeout=int(effective_limits["wall_seconds"]), env={"PATH": str(Path(podman).parent)})
    duration_ms = (time.monotonic_ns() - started_ns) // 1_000_000
    if duration_ms > int(effective_limits["wall_seconds"]) * 1_000:
        raise P5R0Error("native worker exceeded deadline")
    if completed.returncode != 0 or len(completed.stdout) > int(effective_limits["frame_bytes"]) or len(completed.stderr) > int(effective_limits["frame_bytes"]):
        raise P5R0Error("native worker containment/protocol failure")
    try:
        reply = parse_canonical(completed.stdout)
    except Exception as exc:
        raise P5R0Error("native worker reply") from exc
    if protocol_v3:
        validate_reply_v3(reply, task, allow_invalid=allow_invalid)
    elif reply.get("schema") not in {"P5R0WorkerReplyV1", "P5R0WorkerReplyV2", "P5R0WorkerReplyV3"} or set(reply) != {"schema", "action"}:
        raise P5R0Error("native worker reply schema")
    action = reply["action"]
    if not allow_invalid and action is not None and (type(action) is not int or not 0 <= action < len(task.get("legal_actions", []))): raise P5R0Error("native worker action")
    if not return_evidence:
        return action
    evidence = recompute_bounded_compute_evidence(
        task=task, reply=reply, image_digest=image_digest, limits=effective_limits,
        duration_ms=duration_ms, hardware_profile=hardware_profile,
        runtime_digest_value=runtime_digest_value, closure_digest_value=closure_digest_value,
        run_id=run_id, task_id=task_id, sequence=sequence,
        attestation_digest=None, attestation_status="unattested_local",
    )
    validate_bounded_compute_evidence(
        evidence, task=task, reply=reply, image_digest=image_digest, limits=effective_limits,
        duration_ms=duration_ms, hardware_profile=hardware_profile,
        runtime_digest_value=runtime_digest_value, closure_digest_value=closure_digest_value,
        run_id=run_id, task_id=task_id, sequence=sequence,
    )
    return action, evidence


def invoke_native_case_with_evidence(**kwargs: Any) -> tuple[int | None, dict[str, Any]]:
    """Evidence-returning native path; action-only callers remain unchanged."""
    result = _invoke_native_case(return_evidence=True, **kwargs)
    if not isinstance(result, tuple) or len(result) != 2 or not isinstance(result[1], dict):
        raise P5R0Error("native bounded evidence unavailable")
    return result


def _append_close(chain: ReceiptChain, run_id: str, lock_digest: str | None, outcome: str, binding: dict[str, Any] | None = None) -> dict[str, Any]:
    return chain.append(run_id=run_id, kind="run_closed", outcome=outcome, binding={"lock_digest": lock_digest, **(binding or {}), "chain_digest_before_close": chain.digest})


def _host_evidence(*, closure: dict[str, Any], run_id: str, lock_digest: str | None, native_invocations: int, worker_exit: int = 0) -> dict[str, dict[str, Any]]:
    files = closure.get("files", {}) if isinstance(closure, dict) else {}
    closure_digest_value = closure.get("closure_digest")
    return {
        "host_execution_evidence": {"schema": "P5R0HostExecutionEvidenceV3", "run_id": run_id, "lock_digest": lock_digest, "closure_digest": closure_digest_value, "runner_digest": files.get("host_runner"), "native_digest": files.get("host_native"), "invocations": native_invocations, "worker_exit": worker_exit},
        "runtime_evidence": {"schema": "P5R0RuntimeEvidenceV3", "run_id": run_id, "lock_digest": lock_digest, "closure_digest": closure_digest_value, "runtime": closure.get("runtime"), "runtime_path": closure.get("runtime_path"), "runtime_digest": closure.get("runtime_digest"), "network": closure.get("network"), "pull": closure.get("pull")},
        "kill_evidence": {"schema": "P5R0KillEvidenceV3", "run_id": run_id, "lock_digest": lock_digest, "closure_digest": closure_digest_value, "supervisor_digest": files.get("host_kill"), "policy": "bounded_process_group_kill", "observed": True},
    }


def _impasse(chain: ReceiptChain, snap: Snapshot, evaluator: P5R0Evaluator | None, run_id: str, closure: dict[str, Any], reason: str, lock_digest: str | None = None, mutation_artifacts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    chain.append(run_id=run_id, kind="impasse", outcome="containment_failure", binding={"reason": reason[:256], "closure": closure, "lock_digest": lock_digest})
    try:
        restored = evaluator.restore() if evaluator is not None else snap.restore({"graph": {}, "codebook": {}, "counter": 0})
        rb = rollback_receipt(run_id=run_id, pre_snapshot=snap.digest, restored_snapshot=restored, chain_digest=chain.digest); chain.append(run_id=run_id, kind="rollback", outcome="restored" if rb["exact"] else "rollback_impasse", binding=rb)
    except Exception as exc:
        rb = {"schema": "P5R0RollbackReceiptV2", "run_id": run_id, "outcome": "rollback_impasse", "exact": False, "error": str(exc)[:256]}; chain.append(run_id=run_id, kind="rollback", outcome="rollback_impasse", binding=rb)
    _append_close(chain, run_id, lock_digest, "rollback_impasse" if not rb.get("exact") else "containment_failure"); chain.verify_chain()
    v3 = chain.protocol == "V3"
    result = {"schema": "P5R0ResultSealV3" if v3 else "P5R0ResultSealV2", "run_id": run_id, "disposition": "impasse", "outcome": "local_readiness_only/no_go", "manifest_digest": None, "lock_digest": lock_digest, "policy_digest": digest({}), "closure_digest": digest(closure), "receipt_public_key_digest": chain.public_key_digest if v3 else digest(chain.public_key.public_bytes_raw()), "record_count": 0, "control_count": 0, "closure": closure, "gate_reasons": [reason[:256]], "records": [], "controls": [], "mutation_artifacts": list(mutation_artifacts or []), "receipts": len(chain.records), "chain_digest": chain.digest, "rollback": rb, "rollback_cleanup": "exact" if rb.get("exact") else "impasse", "score_report_digest": None, "claim_boundary": "No P5 release, adoption, positive transfer, or general intelligence claim."}
    if v3:
        result.update({"evaluator_authority_id": chain.authority_id, "evaluator_key_id": chain.key_id, "receipt_key_id": chain.key_id, "receipt_public_key": b64encode(chain.public_key.public_bytes_raw()), "evaluator_public_key_digest": chain.public_key_digest, "signature_metadata": {"algorithm": "Ed25519", "receipt_schema": "P5R0ReceiptV3", "authority_id": chain.authority_id, "key_id": chain.key_id, "public_key_digest": chain.public_key_digest}, "receipt_chain_root": str(chain.root.resolve()), "receipt_chain_path": str(chain.root.resolve()), "receipt_chain_root_digest": chain.root_digest, "receipt_chain_final_digest": chain.final_digest, "first_receipt_hash": chain.records[0]["receipt_hash"] if chain.records else None, "final_receipt_hash": chain.records[-1]["receipt_hash"] if chain.records else None})
    return result


def _control_catalog(evaluator: P5R0Evaluator, public_cases: list[dict[str, Any]], records: list[dict[str, Any]], execute: Callable[[dict[str, Any]], dict[str, Any]]) -> list[dict[str, Any]]:
    first = next(c for c in public_cases if c["split"] == "held_out"); controls: list[dict[str, Any]] = []
    definitions = [("exact_memorization", "abstain", {"action": None}), ("template_memorization", "abstain", {"action": None}), ("label_permutation", "invariant", {"action": 0}), ("mechanics_permutation", "paired_rerun", {"action": 0}), ("altered_semantics", "reject", {"action": 0, "altered": True}), ("illegal_action", "protocol_error", {"illegal": True}), ("resource_exhaustion", "resource_exhausted", {"action": 0, "exhausted": True}), ("safety_control", "safety_violation", {"action": 0, "unsafe": True}), ("leakage_audit", "no_private_fields", {"action": 0}), ("containment_audit", "containment_failure", {"action": 0, "write_attempt": True}), ("negative_transfer", "none", {"action": 0})]
    for control_id, expected, options in definitions:
        evidence = execute({"control_id": control_id, "case": first, **options}); observed = evidence.get("observed", "rejected" if options.get("altered") else evidence.get("outcome", "protocol_error"))
        passed = observed == expected
        if control_id == "leakage_audit":
            passed = evidence.get("leakage_free", False); observed = "no_private_fields" if passed else "private_fields"
        if control_id in {"label_permutation", "mechanics_permutation"}:
            passed = bool(evidence.get("transform_digest")) and observed in {"complete_correct", "complete_wrong", "abstain"}
        elif control_id == "altered_semantics":
            passed = observed == "rejected"
        elif control_id == "containment_audit":
            passed = observed == "containment_failure"
        elif control_id in {"exact_memorization", "template_memorization"}:
            passed = observed == "abstain"
        if control_id == "negative_transfer": passed = not any(r.get("outcome") == "negative_transfer" for r in records); observed = "none" if passed else "negative_transfer"
        controls.append({"schema": "P5R0ControlEvidenceV3", "control_id": control_id, "expected": expected, "observed": observed, "passed": passed, "task_digest": evidence.get("task_digest"), "worker_invocation": evidence.get("worker_invocation"), "worker_exit": evidence.get("worker_exit"), "evaluator_outcome": evidence.get("outcome"), "receipt_hash": None, "transform_digest": evidence.get("transform_digest"), "write_set_digest": evidence.get("write_set_digest"), "bounded_compute_evidence_digest": evidence.get("bounded_compute_evidence_digest")})
    return controls



def _run_contrast_matrix(*, evaluator: P5R0Evaluator, bundle: dict[str, Any], chain: ReceiptChain, run_id: str, policy: dict[str, Any], require_native: bool, closure: dict[str, Any], image_digest: str | None, seccomp_profile: Path | None, lock: dict[str, Any] | None, execute_case: Callable[[dict[str, Any], dict[str, Any]], int | None] | None) -> list[dict[str, Any]]:
    cases = {(case["domain_token"], case["combination_id"], case["ordinal"]): case for case in bundle["case_index"]}; order = digest([case["case_id"] for case in bundle["case_index"]]); evidence = []
    for pair in policy.get("contrast_matrix", []):
        for domain in pair.get("domains", []):
            for ordinal in pair.get("ordinals", []):
                left_case = cases[(domain, pair["left"], ordinal)]; right_case = cases[(domain, pair["right"], ordinal)]
                for arm in pair.get("arms", []):
                    side_results = {}
                    for side, case in (("left", left_case), ("right", right_case)):
                        evaluator.restore(); context = evaluator.arm_context(arm, order); evaluator.begin_case(case["case_id"], 0); private = evaluator.private_case(case["case_id"]); nonce = digest({"run": run_id, "pair": pair["pair_id"], "domain": domain, "ordinal": ordinal, "arm": arm}); task = evaluator.task(private, nonce, context)
                        native_evidence = None
                        if require_native:
                            action, native_evidence = invoke_native_case_with_evidence(
                                podman=closure["podman"], image_digest=(closure.get("locked_image_digest") or closure.get("image_digest") or image_digest) or "",
                                seccomp_profile=seccomp_profile or Path(""), task=task, limits=lock["limits"] if lock else None,
                                protocol_v3=bool(lock and lock.get("schema") == "P5R0LocalLockV3"), run_id=run_id,
                                task_id=digest(task), sequence=ordinal + 1,
                                runtime_digest_value=closure.get("runtime_digest"), closure_digest_value=closure.get("closure_digest"),
                            )
                        elif execute_case:
                            action = validate_worker(task, lambda t: execute_case(t, {"case_id": case["case_id"], "case_digest": case["case_digest"], "arm": arm, "contrast": pair["pair_id"], "side": side}))
                        else:
                            action = validate_worker(task)
                        outcome = evaluator.evaluate(case, arm, action); transition = outcome.get("transition", {}); behavior_digest = digest({"observation": task.get("observation"), "outcome": outcome.get("outcome"), "safe": outcome.get("safe"), "terminal": transition.get("terminal"), "success": transition.get("success"), "reward": transition.get("reward"), "violation": transition.get("violation"), "post_state_digest": outcome.get("post_state_digest")})
                        binding = {"pair_id": pair["pair_id"], "side": side, "factor": pair["factor"], "relation": pair["relation"], "domain_token": domain, "ordinal": ordinal, "arm": arm, "case_id": case["case_id"], "case_digest": case["case_digest"], "task_digest": digest(task), "worker_invocation": "native" if require_native else "native_worker", "worker_exit": 0, "evaluator_outcome": outcome["outcome"], "lock_digest": lock.get("lock_digest") if lock else None, "behavior_digest": behavior_digest}
                        if native_evidence is not None:
                            _, binding = attach_bounded_compute_evidence({}, binding, native_evidence)
                        receipt = chain.append(run_id=run_id, kind="contrast", outcome=outcome["outcome"], binding=binding)
                        side_results[side] = {"case_id": case["case_id"], "receipt_hash": receipt["receipt_hash"], "behavior_digest": behavior_digest, "task_digest": digest(task), "worker_invocation": "native" if require_native else "native_worker", "worker_exit": 0, "evaluator_outcome": outcome["outcome"], "bounded_compute_evidence_digest": bounded_compute_evidence_digest(native_evidence) if native_evidence is not None else None}
                    evidence.append({"schema": "P5R0ContrastEvidenceV1", "pair_id": pair["pair_id"], "factor": pair["factor"], "relation": pair["relation"], "domain_token": domain, "ordinal": ordinal, "arm": arm, "left_case_id": side_results["left"]["case_id"], "right_case_id": side_results["right"]["case_id"], "left_receipt_hash": side_results["left"]["receipt_hash"], "right_receipt_hash": side_results["right"]["receipt_hash"], "left_behavior_digest": side_results["left"]["behavior_digest"], "right_behavior_digest": side_results["right"]["behavior_digest"], "left_task_digest": side_results["left"]["task_digest"], "right_task_digest": side_results["right"]["task_digest"], "left_worker_invocation": side_results["left"]["worker_invocation"], "right_worker_invocation": side_results["right"]["worker_invocation"], "left_worker_exit": side_results["left"]["worker_exit"], "right_worker_exit": side_results["right"]["worker_exit"], "left_evaluator_outcome": side_results["left"]["evaluator_outcome"], "right_evaluator_outcome": side_results["right"]["evaluator_outcome"], "left_bounded_compute_evidence_digest": side_results["left"]["bounded_compute_evidence_digest"], "right_bounded_compute_evidence_digest": side_results["right"]["bounded_compute_evidence_digest"]})
    evaluator.restore(); return evidence


def run_readiness_gate(bundle: dict[str, Any], *, receipts_root: Path, image_digest: str | None = None, podman: str = "podman", seccomp_profile: Path | None = None, closure_paths: dict[str, Path] | None = None, execute_case: Callable[[dict[str, Any], dict[str, Any]], int | None] | None = None, require_native: bool = True, lock: dict[str, Any] | None = None, trusted_authority: dict[str, Any] | None = None, receipt_signer: Ed25519PrivateKey | None = None, warm_reset_session_id: str | None = None) -> dict[str, Any]:
    if bundle.get("schema") != "P5R0ManifestV2": raise P5R0Error("production requires locked public manifest")
    v3 = bool(lock and lock.get("schema") == "P5R0LocalLockV3")
    signer = receipt_signer or Ed25519PrivateKey.generate()
    protocol = "V3" if v3 else "V2"
    authority_id = trusted_authority.get("authority_id", "p5-r0-evaluator") if trusted_authority else "p5-r0-evaluator"
    key_id = trusted_authority.get("key_id", "p5-r0-receipt") if trusted_authority else "p5-r0-receipt"
    chain = ReceiptChain(receipts_root, signer, authority_id=authority_id, key_id=key_id, protocol=protocol)
    run_id = digest({"manifest": bundle["manifest_digest"], "lock": lock.get("lock_digest") if lock else None, "root": str(receipts_root.resolve()), "protocol": protocol})
    if v3:
        if trusted_authority is None:
            return _impasse(chain, Snapshot({"graph": {}, "codebook": {}, "counter": 0}), None, run_id, {"available": False, "reason": "V3 external authority required", "network": "none", "pull": "never", "runtime": "crun"}, "V3 external authority required")
        try: validate_repair_lock(lock, trusted_authority=trusted_authority, expected_manifest_digest=bundle["manifest_digest"])
        except Exception as exc: return _impasse(chain, Snapshot({"graph": {}, "codebook": {}, "counter": 0}), None, run_id, {"available": False, "reason": str(exc), "network": "none", "pull": "never", "runtime": "crun"}, "V3 native worker is mandatory; invalid V3 external lock" if require_native is not False else "V3 native worker is mandatory; V3 fallback disabled", lock.get("lock_digest"))
        if b64encode(signer.public_key().public_bytes_raw()) != trusted_authority["public_key"]:
            return _impasse(chain, Snapshot({"graph": {}, "codebook": {}, "counter": 0}), None, run_id, {"available": False, "reason": "receipt signer is not externally bound", "network": "none", "pull": "never", "runtime": "crun"}, "V3 receipt signer authority mismatch", lock.get("lock_digest"))
        try:
            validate_manifest_integrity(bundle)
            if lock.get("case_index_digest") != bundle.get("index_digest") or lock.get("truth_digest") != bundle.get("truth_digest") or lock.get("store_digest") != bundle.get("store_digest"):
                raise P5R0Error("V3 lock/store commitment")
        except Exception as exc:
            return _impasse(chain, Snapshot({"graph": {}, "codebook": {}, "counter": 0}), None, run_id, {"available": False, "reason": str(exc)[:256], "network": "none", "pull": "never", "runtime": "crun"}, "V3 manifest/private commitment", lock.get("lock_digest"))
    elif require_native:
        # V2 remains historical evidence; it is never a production activation input.
        if lock is None or trusted_authority is None:
            return _impasse(chain, Snapshot({"graph": {}, "codebook": {}, "counter": 0}), None, run_id, {"available": False, "reason": "V3 lock and trusted external authority required", "network": "none", "pull": "never", "runtime": "crun"}, "production requires V3 lock")
        try: validate_lock(lock, trusted_authority=trusted_authority, expected_manifest_digest=bundle["manifest_digest"])
        except Exception as exc: return _impasse(chain, Snapshot({"graph": {}, "codebook": {}, "counter": 0}), None, run_id, {"available": False, "reason": str(exc), "network": "none", "pull": "never", "runtime": "crun"}, "historical V2 lock rejected")
        return _impasse(chain, Snapshot({"graph": {}, "codebook": {}, "counter": 0}), None, run_id, {"available": False, "reason": "historical V2 lock rejected for production", "network": "none", "pull": "never", "runtime": "crun"}, "historical V2 lock rejected")
    closure = closure_status(podman=podman, image_digest=image_digest, seccomp_profile=seccomp_profile, locked_closure=(lock or {}).get("closure"), limits=(lock or {}).get("limits"), closure_paths=closure_paths)
    evaluator: P5R0Evaluator | None = None
    if v3 and (require_native is not True or not closure["available"]):
        reason = "V3 native worker is mandatory; in-process worker fallback is disabled" if require_native is not True else closure["reason"]
        return _impasse(chain, Snapshot({"graph": {}, "codebook": {}, "counter": 0}), evaluator, run_id, closure, reason, lock.get("lock_digest") if lock else None)
    if require_native and not closure["available"]: return _impasse(chain, Snapshot({"graph": {}, "codebook": {}, "counter": 0}), evaluator, run_id, closure, closure["reason"], lock.get("lock_digest") if lock else None)
    preregistration_hash: str | None = None
    if v3:
        declared_order = [case["case_id"] for case in bundle["case_index"]]
        preregistration = {"schema": "P5R0PreregistrationBindingV3", "content_digest": digest(bundle), "order": declared_order, "order_digest": digest(declared_order), "parent_lock_digest": lock["parent_lock_digest"], "parent_manifest_digest": lock["parent_manifest_digest"], "parent_case_index_digest": lock["parent_case_index_digest"], "parent_truth_digest": lock["parent_truth_digest"], "parent_store_digest": lock["parent_store_digest"], "lock_digest": lock["lock_digest"], "manifest_digest": bundle["manifest_digest"], "case_index_digest": bundle["index_digest"], "truth_digest": bundle["truth_digest"], "store_digest": bundle["store_digest"], "split_commitment_digest": digest(lock["parent_split_commitment"]), "policy_digest": digest(lock["policy"]), "worker_contract_digest": lock["worker_contract"]["digest"], "evaluator_contract_digest": lock["evaluator_contract"]["digest"], "closure_digest": digest(lock["closure"]), "authority_id": trusted_authority["authority_id"], "key_id": trusted_authority["key_id"], "public_key_digest": trusted_authority["public_key_digest"]}
        first = chain.append(run_id=run_id, kind="preregistered", outcome="verified", binding=preregistration)
        preregistration_hash = first["receipt_hash"]
    try:
        private_store_for(bundle); evaluator = P5R0Evaluator(bundle); initial = Snapshot(evaluator.state); records: list[dict[str, Any]] = []; mutation_artifacts: list[dict[str, Any]] = []; mutation_root = receipts_root / "mutations"; order = digest([c["case_id"] for c in bundle["case_index"]])
        if v3 and warm_reset_session_id is not None:
            evaluator.arm_context("warm_adaptive", order)
            pre_reset = evaluator.session_digest()
            try:
                evaluator.arm_context("warm_adaptive", order, session_id=warm_reset_session_id)
            except P5R0Error:
                mutation = record_rejected_reset(chain=chain, artifact_root=mutation_root, run_id=run_id, lock_digest=lock["lock_digest"], ordinal=0, task_digest=None, pre_state_digest=pre_reset, proposed_session_id=warm_reset_session_id)
                mutation_artifacts.append(mutation)
                return _impasse(chain, initial, evaluator, run_id, closure, "warm reset rejected before native invocation", lock["lock_digest"], mutation_artifacts)
            raise P5R0Error("warm reset unexpectedly accepted")
        for arm in ARMS:
            if evaluator._active_context is not None:
                evaluator._active_context = None
            context = evaluator.arm_context(arm, order)
            for ordinal, case in enumerate(bundle["case_index"]):
                if case["split"] not in {"train", "development", "held_out"}: raise P5R0Error("case split")
                session = evaluator.begin_case(case["case_id"], ordinal); private = evaluator.private_case(case["case_id"]); task = evaluator.task(private, digest({"run": run_id, "case": case["case_digest"], "arm": arm}), context)
                worker_exit = 0; native_evidence = None
                if require_native:
                    action, native_evidence = invoke_native_case_with_evidence(
                        podman=closure["podman"], image_digest=(closure.get("locked_image_digest") or closure.get("image_digest") or image_digest) or "",
                        seccomp_profile=seccomp_profile or Path(""), task=task, limits=lock["limits"] if lock else None,
                        protocol_v3=bool(lock and lock.get("schema") == "P5R0LocalLockV3"),
                        run_id=run_id, task_id=digest(task), sequence=ordinal + 1,
                        runtime_digest_value=closure.get("runtime_digest"), closure_digest_value=closure.get("closure_digest"),
                    )
                elif execute_case: action = validate_worker(task, lambda t: execute_case(t, {"case_id": case["case_id"], "case_digest": case["case_digest"], "arm": arm}))
                else: action = validate_worker(task)
                outcome = evaluator.evaluate(case, arm, action)
                if v3 and arm == "warm_adaptive":
                    mutation_outcome = "applied" if outcome.get("pre_state_digest") != outcome.get("post_state_digest") else "rejected"
                    mutation_artifacts.append(record_mutation(chain=chain, artifact_root=mutation_root, run_id=run_id, lock_digest=lock["lock_digest"], mutation_kind="adoption", target="warm_session_namespace", ordinal=ordinal, task_digest=digest(task), pre_state_digest=outcome["pre_state_digest"], proposed_state_digest=outcome["post_state_digest"], post_state_digest=outcome["post_state_digest"], write_set_digest=outcome["write_set_digest"], expected_effect_digest=outcome.get("effect_digest") or digest({}), observed_effect_digest=outcome.get("effect_digest") or digest({}), outcome=mutation_outcome, rollback_exact=True))
                record = {"case_id": case["case_id"], "case_digest": case["case_digest"], "domain_token": case["domain_token"], "split": case["split"], "case_index_ordinal": case["ordinal"], "arm": arm, "outcome": outcome["outcome"], "evidence_digest": digest(outcome), "pre_state_digest": outcome["pre_state_digest"], "post_state_digest": outcome["post_state_digest"], "write_set_digest": outcome["write_set_digest"], "adaptation_count": outcome["adaptation_count"], "session_id": outcome["session_id"], "ordinal": outcome["case_ordinal"], "mechanics_digest": outcome["mechanics_digest"], "effect_digest": outcome["effect_digest"], "truth_digest": outcome["truth_digest"], "worker_invocation": "native" if require_native else "native_worker", "worker_exit": worker_exit}
                base_binding = {"case_id": case["case_id"], "case_digest": case["case_digest"], "arm": arm, "split": case["split"], "case_index_ordinal": case["ordinal"], "lock_digest": lock.get("lock_digest") if lock else None, "session_id": outcome["session_id"], "ordinal": outcome["case_ordinal"], "pre_state_digest": outcome["pre_state_digest"], "post_state_digest": outcome["post_state_digest"], "evidence_digest": digest(outcome), "worker_invocation": record["worker_invocation"], "worker_exit": record["worker_exit"]}
                if native_evidence is not None:
                    record, base_binding = attach_bounded_compute_evidence(record, base_binding, native_evidence)
                record["record_digest"] = digest(record)
                base_binding["record_digest"] = record["record_digest"]
                receipt = chain.append(run_id=run_id, kind="terminal", outcome=outcome["outcome"], binding=base_binding, resources={"steps": private["truth"]["expected_steps"], "frame_bytes": len(canonical_bytes(task)), "worker_exit": worker_exit})
                record["receipt_hash"] = receipt["receipt_hash"]
                records.append(record)
        def execute_control(spec: dict[str, Any]) -> dict[str, Any]:
            control_id = spec["control_id"]; case = spec["case"]; private = evaluator.private_case(case["case_id"]); context = evaluator._active_context
            train_commitment = digest(sorted(c["case_digest"] for c in bundle["case_index"] if c["split"] == "train"))
            control_metadata = {"control_id": control_id, "training_commitment": train_commitment, "challenge_commitment": case["case_digest"], "policy": "abstain_if_no_exact_or_template_match" if control_id in {"exact_memorization", "template_memorization"} else "harness_stimulus"}
            task = evaluator.task(private, digest({"run": run_id, "control": control_id}), context, control_metadata=control_metadata)
            # In native mode the worker reply is authoritative.  In particular,
            # a memorization control's null reply must pass through unchanged.
            action = spec.get("action", 0); native_evidence = None; worker_invocation = "native" if require_native else "native_worker"; worker_exit = 0
            try:
                if spec.get("illegal") and not require_native: action = len(task["legal_actions"])
                elif require_native:
                    action, native_evidence = invoke_native_case_with_evidence(
                        podman=closure["podman"], image_digest=(closure.get("locked_image_digest") or closure.get("image_digest") or image_digest) or "",
                        seccomp_profile=seccomp_profile or Path(""), task=task, limits=lock["limits"] if lock else None,
                        allow_invalid=bool(spec.get("illegal")), protocol_v3=bool(lock and lock.get("schema") == "P5R0LocalLockV3"),
                        run_id=run_id, task_id=digest(task), sequence=len(records) + 1,
                        runtime_digest_value=closure.get("runtime_digest"), closure_digest_value=closure.get("closure_digest"),
                    )
                else:
                    validate_worker(task)
                    action = action if not spec.get("illegal") else len(task["legal_actions"])
                if spec.get("illegal") and type(action) is int and 0 <= action < len(task["legal_actions"]):
                    return {"observed": "control_failure", "outcome": "control_failure", "passed": False, "task_digest": digest(task), "worker_invocation": worker_invocation, "worker_exit": worker_exit, "error": "locked illegal-action stimulus returned a legal action", "transform_digest": digest({"control": control_id, "case": case["case_digest"]}), "write_set_digest": digest({}), "bounded_compute_evidence_digest": bounded_compute_evidence_digest(native_evidence) if native_evidence is not None else None}
            except Exception as exc:
                return {"observed": "protocol_error", "outcome": "protocol_error", "passed": control_id == "illegal_action", "task_digest": digest(task), "worker_invocation": worker_invocation, "worker_exit": 1, "error": str(exc)[:160], "transform_digest": digest({"control": control_id, "case": case["case_digest"]}), "write_set_digest": digest({}), "bounded_compute_evidence_digest": bounded_compute_evidence_digest(native_evidence) if native_evidence is not None else None}
            try:
                if spec.get("altered"):
                    altered = dict(case); altered["mechanics_digest"] = digest({"altered": case["mechanics_digest"]}); result = evaluator.evaluate(altered, evaluator.state["arm"], action)
                elif spec.get("write_attempt"):
                    saved_arm = evaluator.state["arm"]; evaluator.state["arm"] = "frozen_transfer"
                    try: result = evaluator.evaluate(case, "frozen_transfer", action, write_attempt=True)
                    finally: evaluator.state["arm"] = saved_arm
                else: result = evaluator.evaluate(case, evaluator.state["arm"], action, exhausted=bool(spec.get("exhausted")), safe=False if spec.get("unsafe") else None)
                observed = result["outcome"]
            except P5R0Error:
                result = {"outcome": "rejected"}; observed = "rejected"
            return {"observed": observed, "outcome": result.get("outcome"), "passed": False, "leakage_free": all(k not in task for k in ("truth", "secret_seed", "private_parameters", "private_domain_family", "target_action")), "task_digest": digest(task), "worker_invocation": worker_invocation, "worker_exit": worker_exit, "write_set_digest": result.get("write_set_digest") or digest({}), "transform_digest": digest({"control": control_id, "case": case["case_digest"]}), "bounded_compute_evidence_digest": bounded_compute_evidence_digest(native_evidence) if native_evidence is not None else None}
        controls = _control_catalog(evaluator, bundle["case_index"], records, execute_control); control_receipts = []
        for control in controls:
            control["lock_digest"] = lock.get("lock_digest") if lock else None
            control["control_digest"] = digest({key: value for key, value in control.items() if key not in {"receipt_hash", "lock_digest"}})
            binding = {key: control.get(key) for key in ("control_id", "task_digest", "worker_invocation", "worker_exit", "evaluator_outcome", "expected", "observed", "passed", "transform_digest", "write_set_digest", "bounded_compute_evidence_digest", "control_digest")}
            binding["lock_digest"] = lock.get("lock_digest") if lock else None
            rec = chain.append(run_id=run_id, kind="control", outcome="verified" if control["passed"] else "containment_failure", binding=binding)
            control["receipt_hash"] = rec["receipt_hash"]
            control_receipts.append(control)
        policy = (lock or {}).get("policy", {"expected_primary_records": len(records), "expected_cases": len(bundle["case_index"]), "required_control_ids": [c["control_id"] for c in controls], "contrast_matrix": contrast_matrix(), "minimum_held_out": 36, "max_safety_violations": 0, "max_resource_exhaustions": 0, "max_leakage": 0, "max_rollback_impasses": 0, "native_required": True})
        contrast_evidence = _run_contrast_matrix(evaluator=evaluator, bundle=bundle, chain=chain, run_id=run_id, policy=policy, require_native=require_native, closure=closure, image_digest=image_digest, seccomp_profile=seccomp_profile, lock=lock, execute_case=execute_case)
        restored = evaluator.restore(); rb = rollback_receipt(run_id=run_id, pre_snapshot=initial.digest, restored_snapshot=restored, chain_digest=chain.digest); rb["lock_digest"] = lock.get("lock_digest") if lock else None
        if v3: rb["preregistration_receipt_hash"] = preregistration_hash
        rollback_record = chain.append(run_id=run_id, kind="rollback", outcome="restored" if rb["exact"] else "rollback_impasse", binding=rb); close_record = _append_close(chain, run_id, lock.get("lock_digest") if lock else None, "verified"); verified_chain = chain.verify_chain(); final_chain_digest = digest(verified_chain)
        report = score_records(records, baselines=controls)
        if v3:
            report = dict(report)
            report["schema"] = "P5R0ScoreReportV3"
            report.pop("retention", None); report.pop("interference", None)
            report["canonical_comparison"] = {"schema": "P5R0CanonicalComparisonV1", "status": "requires_independent_run", "authoritative": True}
        host_evidence = _host_evidence(closure=closure, run_id=run_id, lock_digest=lock.get("lock_digest") if lock else None, native_invocations=len(records) + len(controls) + len(contrast_evidence) * 2)
        evidence = {"run_id": run_id, "records": records, "case_index": bundle["case_index"], "case_index_digest": bundle["index_digest"], "split_digest": bundle["split_digest"], "split_commitment": (lock or {}).get("split_commitment", build_split_commitment()), "controls": control_receipts, "contrast_evidence": contrast_evidence, "score_report": report, "receipt_chain": chain, "chain_digest": final_chain_digest, "lock_digest": lock.get("lock_digest") if lock else None, "closure": closure, "closure_digest": closure.get("closure_digest"), **host_evidence, "native_verified": require_native and closure["available"], "external_authority_verified": bool(require_native and trusted_authority), "native_controls_verified": all(c.get("worker_invocation") == ("native" if require_native else "native_worker") and c.get("task_digest") and c.get("worker_exit") == 0 for c in controls), "mechanics_contrasts_verified": bool(contrast_evidence) and (require_native or execute_case is not None), "session_state_verified": all(r.get("session_id") and isinstance(r.get("ordinal"), int) for r in records), "rollback_exact": rb["exact"], "rollback_impasses": 0 if rb["exact"] else 1, "rollback": rb, "leakage_findings": sum(1 for c in controls if c["control_id"] == "leakage_audit" and not c["passed"]), "controls_passed": all(c["passed"] for c in controls), "held_out_complete": sum(1 for r in records if r["split"] == "held_out") >= int(policy.get("minimum_held_out", 36))}
        decision = evaluate_gate(evidence, policy)
        result = {"schema": "P5R0ResultSealV3" if v3 else "P5R0ResultSealV2", "run_id": run_id, "disposition": decision["disposition"], "outcome": decision["disposition"], "manifest_digest": bundle["manifest_digest"], "lock_digest": lock.get("lock_digest") if lock else None, "policy_digest": digest(policy), "closure_digest": digest(closure), "receipt_public_key_digest": chain.public_key_digest if v3 else digest(chain.public_key.public_bytes_raw()), "record_count": len(records), "control_count": len(control_receipts), "closure": closure, "records": records, "controls": control_receipts, "score_report": report, "score_report_digest": digest(report), "receipts": len(chain.records), "chain_digest": final_chain_digest, "contrast_evidence": contrast_evidence, "mutation_artifacts": mutation_artifacts, "rollback": rb, "rollback_cleanup": "exact" if rb["exact"] else "impasse", "claim_boundary": decision["claim_boundary"], "gate_reasons": decision["reasons"], "case_index": bundle["case_index"], "case_index_digest": bundle["index_digest"], "split_digest": bundle["split_digest"], "split_commitment": (lock or {}).get("split_commitment", build_split_commitment()), "policy": policy, "native_verified": require_native and closure["available"], "external_authority_verified": bool(trusted_authority), "native_controls_verified": all(c.get("worker_invocation") == ("native" if require_native else "native_worker") and c.get("task_digest") and c.get("worker_exit") == 0 for c in control_receipts), "mechanics_contrasts_verified": bool(contrast_evidence) and (require_native or execute_case is not None), "session_state_verified": all(r.get("session_id") and isinstance(r.get("ordinal"), int) for r in records), "controls_passed": all(c["passed"] for c in control_receipts), "held_out_complete": sum(1 for r in records if r["split"] == "held_out") >= int(policy.get("minimum_held_out", 36)), "rollback_impasses": 0 if rb["exact"] else 1, "rollback_exact": rb["exact"], "leakage_findings": sum(1 for c in control_receipts if c["control_id"] == "leakage_audit" and not c["passed"]), "truth_digest": bundle["truth_digest"], "store_digest": bundle["store_digest"], "preregistration_content_digest": digest(bundle), "preregistration_policy_digest": digest(policy), "preregistration_worker_contract_digest": lock["worker_contract"]["digest"] if v3 else None, "preregistration_evaluator_contract_digest": lock["evaluator_contract"]["digest"] if v3 else None, "preregistration_closure_digest": digest(lock["closure"]) if v3 else None}
        if v3:
            public_key = b64encode(chain.public_key.public_bytes_raw())
            result.update({"closure_digest": digest(closure), "host_execution_evidence": host_evidence["host_execution_evidence"], "runtime_evidence": host_evidence["runtime_evidence"], "kill_evidence": host_evidence["kill_evidence"], "evaluator_authority_id": trusted_authority["authority_id"], "evaluator_key_id": trusted_authority["key_id"], "receipt_key_id": trusted_authority["key_id"], "receipt_public_key": public_key, "evaluator_public_key_digest": chain.public_key_digest, "signature_metadata": {"algorithm": "Ed25519", "receipt_schema": "P5R0ReceiptV3", "authority_id": trusted_authority["authority_id"], "key_id": trusted_authority["key_id"], "public_key_digest": chain.public_key_digest}, "receipt_chain_root": str(chain.root.resolve()), "receipt_chain_path": str(chain.root.resolve()), "receipt_chain_root_digest": chain.root_digest, "receipt_chain_final_digest": final_chain_digest, "first_receipt_hash": preregistration_hash, "final_receipt_hash": verified_chain[-1]["receipt_hash"], "preregistration": {"receipt_hash": preregistration_hash, "content_digest": digest(bundle), "order": [case["case_id"] for case in bundle["case_index"]], "order_digest": digest([case["case_id"] for case in bundle["case_index"]]), "parent_lock_digest": lock["parent_lock_digest"], "parent_manifest_digest": lock["parent_manifest_digest"], "parent_case_index_digest": lock["parent_case_index_digest"], "parent_truth_digest": lock["parent_truth_digest"], "parent_store_digest": lock["parent_store_digest"], "lock_digest": lock["lock_digest"], "manifest_digest": bundle["manifest_digest"], "truth_digest": bundle["truth_digest"], "store_digest": bundle["store_digest"]}})
        return result
    except Exception as exc:
        return _impasse(chain, initial if "initial" in locals() else Snapshot({"graph": {}, "codebook": {}, "counter": 0}), evaluator, run_id, closure, str(exc), lock.get("lock_digest") if lock else None)

run_local = run_readiness_gate
