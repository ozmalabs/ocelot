from __future__ import annotations

from typing import Any

from .canonical import digest


class SchemaError(ValueError):
    pass


def closed(value: Any, fields: set[str], schema: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields or value.get("schema") != schema:
        raise SchemaError(f"closed schema {schema}")
    return value


def string(value: Any, name: str, *, digest_value: bool = False) -> str:
    if not isinstance(value, str) or not value:
        raise SchemaError(name)
    if digest_value and (len(value) != 71 or not value.startswith("sha256:") or any(c not in "0123456789abcdef" for c in value[7:])):
        raise SchemaError(name)
    return value


def run_start(value: Any) -> dict[str, Any]:
    out = closed(value, {"schema", "lock_digest", "manifest_digest", "worker_contract_digest", "idempotency_key"}, "P5R0RunStartRequestV1")
    string(out["lock_digest"], "lock_digest", digest_value=True)
    string(out["manifest_digest"], "manifest_digest", digest_value=True)
    string(out["worker_contract_digest"], "worker_contract_digest", digest_value=True)
    string(out["idempotency_key"], "idempotency_key")
    if len(out["idempotency_key"]) > 256:
        raise SchemaError("idempotency_key")
    return out


def next_task(value: Any) -> dict[str, Any]:
    out = closed(value, {"schema", "expected_sequence", "idempotency_key"}, "P5R0NextTaskRequestV1")
    if type(out["expected_sequence"]) is not int or out["expected_sequence"] < 1:
        raise SchemaError("expected_sequence")
    string(out["idempotency_key"], "idempotency_key")
    return out


def worker_reply(value: Any) -> dict[str, Any]:
    out = closed(value, {"schema", "action"}, "P5R0WorkerReplyV3")
    if out["action"] is not None and (type(out["action"]) is not int or out["action"] < 0):
        raise SchemaError("reply action")
    return out


def worker_exit(value: Any) -> dict[str, Any]:
    out = closed(value, {"schema", "code", "timed_out", "signal"}, "P5R0WorkerExitV1")
    if type(out["code"]) is not int or type(out["timed_out"]) is not bool or (out["signal"] is not None and type(out["signal"]) is not int):
        raise SchemaError("worker_exit")
    return out


def execution_evidence(value: Any) -> dict[str, Any]:
    out = closed(value, {"schema", "closure_digest", "runtime_digest", "host_digest", "kill_digest", "native_verified"}, "P5R0ExecutionEvidenceV1")
    for key in ("closure_digest", "runtime_digest", "host_digest", "kill_digest"):
        string(out[key], key, digest_value=True)
    if type(out["native_verified"]) is not bool:
        raise SchemaError("native_verified")
    if out["native_verified"] is not False:
        raise SchemaError("production service requires verified Confidential Space evidence")
    return out


def bounded_compute_claim(value: Any) -> dict[str, Any]:
    """Validate a supervisor-produced claim without accepting native caller claims.

    This helper is intentionally not part of ``task_result``: callers may not
    submit a bounded-compute claim as execution metadata.  A future trusted
    worker-supervisor integration can pass its own claim through this closed
    shape after the service has checked the active binding and timing chain.
    """
    out = closed(value, {"schema", "binding_digest", "evidence_digest", "timing_attestation_digest", "supervisor_evidence_digest"}, "P5R0BoundedComputeClaimV1")
    for key in ("binding_digest", "evidence_digest", "timing_attestation_digest", "supervisor_evidence_digest"):
        string(out[key], key, digest_value=True)
    return out


def task_result(value: Any, path_run_id: str, path_task_id: str) -> dict[str, Any]:
    out = closed(value, {"schema", "run_id", "task_id", "sequence", "task_digest", "reply", "worker_exit", "worker_invocation", "execution_evidence", "idempotency_key"}, "P5R0TaskResultRequestV1")
    if out["run_id"] != path_run_id or out["task_id"] != path_task_id:
        raise SchemaError("path identity")
    string(out["run_id"], "run_id", digest_value=True)
    string(out["task_id"], "task_id", digest_value=True)
    if type(out["sequence"]) is not int or out["sequence"] < 1:
        raise SchemaError("sequence")
    string(out["task_digest"], "task_digest", digest_value=True)
    worker_reply(out["reply"])
    worker_exit(out["worker_exit"])
    if out["worker_invocation"] not in {"native", "unknown"}:
        raise SchemaError("worker_invocation")
    execution_evidence(out["execution_evidence"])
    string(out["idempotency_key"], "idempotency_key")
    return out


def task_envelope(value: Any) -> dict[str, Any]:
    out = closed(value, {"schema", "run_id", "task_id", "sequence", "task_digest", "task", "issued_at_ms", "expires_at_ms", "authority_id", "key_id", "public_key_digest", "signature"}, "P5R0TaskEnvelopeV1")
    string(out["run_id"], "run_id", digest_value=True)
    string(out["task_id"], "task_id", digest_value=True)
    if type(out["sequence"]) is not int or out["sequence"] < 1:
        raise SchemaError("sequence")
    string(out["task_digest"], "task_digest", digest_value=True)
    if type(out["task"]) is not dict or out["task"].get("schema") != "P5R0WorkerTaskV3":
        raise SchemaError("task")
    for key in ("issued_at_ms", "expires_at_ms"):
        if type(out[key]) is not int or out[key] < 0:
            raise SchemaError(key)
    if out["expires_at_ms"] <= out["issued_at_ms"]:
        raise SchemaError("expiry")
    string(out["authority_id"], "authority_id")
    string(out["key_id"], "key_id")
    string(out["public_key_digest"], "public_key_digest", digest_value=True)
    string(out["signature"], "signature")
    return out


def task_response(value: dict[str, Any]) -> dict[str, Any]:
    # Kept as a construction assertion so accidental response-field drift fails locally.
    fields = {"schema", "run_id", "task_id", "sequence", "phase", "case_id", "side", "pair_id", "task_digest", "task", "task_envelope", "authority", "issued_at_ms", "expires_at_ms"}
    out = closed(value, fields, "P5R0NextTaskResponseV1")
    for key in ("issued_at_ms", "expires_at_ms"):
        if type(out[key]) is not int or out[key] < 0:
            raise SchemaError(key)
    if out["expires_at_ms"] <= out["issued_at_ms"]:
        raise SchemaError("expiry")
    task_envelope(out["task_envelope"])
    if out["task_envelope"]["task_digest"] != out["task_digest"] or digest(out["task"]) != out["task_digest"]:
        raise SchemaError("task digest binding")
    return out


def request_digest(value: dict[str, Any]) -> str:
    return digest(value)



def compute_class_seed(value: Any, path_run_id: str, path_task_id: str) -> dict[str, Any]:
    out = closed(value, {"schema", "run_id", "task_id", "sequence", "idempotency_key"}, "P5ComputeClassSeedRequestV1")
    if out["run_id"] != path_run_id or out["task_id"] != path_task_id:
        raise SchemaError("path identity")
    string(out["run_id"], "run_id", digest_value=True)
    string(out["task_id"], "task_id", digest_value=True)
    if type(out["sequence"]) is not int or out["sequence"] < 1:
        raise SchemaError("sequence")
    string(out["idempotency_key"], "idempotency_key")
    if len(out["idempotency_key"]) > 256:
        raise SchemaError("idempotency_key")
    return out


def compute_class_observation_request(value: Any, path_run_id: str) -> dict[str, Any]:
    fields = {"schema", "run_id", "task_id", "sequence", "task_digest", "seed_digest", "image_digest", "runtime_digest", "resource_profile_digest", "result_digest", "idempotency_key"}
    out = closed(value, fields, "P5ComputeClassObservationRequestV1")
    if out["run_id"] != path_run_id:
        raise SchemaError("path identity")
    string(out["run_id"], "run_id", digest_value=True)
    string(out["task_id"], "task_id", digest_value=True)
    if type(out["sequence"]) is not int or out["sequence"] < 1:
        raise SchemaError("sequence")
    for key in ("task_digest", "seed_digest", "image_digest", "runtime_digest", "resource_profile_digest", "result_digest"):
        string(out[key], key, digest_value=True)
    string(out["idempotency_key"], "idempotency_key")
    if len(out["idempotency_key"]) > 256:
        raise SchemaError("idempotency_key")
    return out


def compute_class_observation(value: Any) -> dict[str, Any]:
    fields = {"schema", "run_id", "task_id", "sequence", "task_digest", "seed_digest", "timing_observation_digests", "wall_time_bucket", "cpu_time_bucket", "image_digest", "runtime_digest", "resource_profile_digest", "result_digest", "wall_vs_cpu", "limitation", "issued_at_ms", "received_at_ms", "expires_at_ms", "authority_id", "key_id", "public_key", "public_key_digest", "observation_digest", "signature"}
    out = closed(value, fields, "P5ComputeClassObservationV2")
    string(out["run_id"], "run_id", digest_value=True)
    string(out["task_id"], "task_id", digest_value=True)
    if type(out["sequence"]) is not int or out["sequence"] < 1:
        raise SchemaError("sequence")
    for key in ("task_digest", "seed_digest", "image_digest", "runtime_digest", "resource_profile_digest", "result_digest", "public_key_digest", "observation_digest"):
        string(out[key], key, digest_value=True)
    timing_digests = out["timing_observation_digests"]
    if (not isinstance(timing_digests, dict) or set(timing_digests) != {"task", "result"}
            or any(not isinstance(v, str) or len(v) != 71 or not v.startswith("sha256:")
                   or any(c not in "0123456789abcdef" for c in v[7:]) for v in timing_digests.values())):
        raise SchemaError("timing_observation_digests")
    if out["wall_time_bucket"] not in {"<100ms", "<1s", "<10s", "<100s", "timeout"}:
        raise SchemaError("wall_time_bucket")
    if out["cpu_time_bucket"] != "not_observed":
        raise SchemaError("cpu_time_bucket")
    if out["wall_vs_cpu"] != "provider_wall_transport_interval_not_worker_cpu":
        raise SchemaError("wall_vs_cpu")
    string(out["limitation"], "limitation")
    for key in ("issued_at_ms", "received_at_ms", "expires_at_ms"):
        if type(out[key]) is not int or out[key] < 0:
            raise SchemaError(key)
    if not out["issued_at_ms"] <= out["received_at_ms"] <= out["expires_at_ms"]:
        raise SchemaError("timestamp order")
    for key in ("authority_id", "key_id", "public_key", "signature"):
        string(out[key], key)
    if digest(out["public_key"]) != out["public_key_digest"]:
        raise SchemaError("public key binding")
    return out
