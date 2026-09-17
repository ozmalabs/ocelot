"""Immutable, evaluator-signed P3 release lock."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from evaluation.p0a.canonical import object_hash, sign, verify_signature
from .protocol import P3ProtocolError, is_digest

ARTIFACT_NAMES = (
 "broker_image", "broker_allowlist", "grant_schema", "policy_authority_image", "policy_verification_key", "receipt_writer_image", "receipt_verification_key", "kill_supervisor_policy", "native_evaluator", "native_evaluator_image", "native_worker", "runtime_closure", "p3_schemas", "task_release_service", "task_release_verification_key", "scoring_oracle", "benchmark_grammar", "distribution_manifest", "semantic_dedup_report", "private_split_commitment", "seed_commitment", "resource_limits", "failure_score_definition", "statistical_seed_commitment", "result_seal_schema", "mount_channel_layout",
)
THRESHOLDS = {"primary_unit": "milli_percentage_points", "primary_min": 0, "primary_max": 100000, "improve_delta_min": 5000, "harm_delta_max": -5000, "bootstrap_resamples": 100000, "sign_permutations": 100000, "familywise_alpha_milli": 50, "pairs_per_distribution": 30, "distribution_count": 12, "cpu_count": 1, "memory_bytes": 4 * 1024**3, "wall_seconds": 60, "graph_transactions": 10000, "network_bytes": 0}
GO_BINDINGS = ("p0_go_digest", "p1_go_digest", "p2_go_digest")

@dataclass(frozen=True)
class P3ReleaseLockV1:
    body: dict[str, Any]
    @property
    def digest(self) -> str: return self.body["content_hash"]
    @property
    def artifacts(self) -> dict[str, str]: return dict(self.body["artifacts"])

def _content(lock: Mapping[str, Any]) -> str: return object_hash(dict(lock), "content_hash")
def make_release_lock(*, signing_key: Any, key_id: str, p0_go_digest: str, p1_go_digest: str,
                      p2_go_digest: str, artifacts: Mapping[str, str], candidate_digest: str,
                      pre_snapshot_digest: str, native_export_digest: str) -> dict[str, Any]:
    body = {"schema":"P3ReleaseLockV1", "key_id":key_id, "p0_go_digest":p0_go_digest,
            "p1_go_digest":p1_go_digest, "p2_go_digest":p2_go_digest, "artifacts":dict(artifacts),
            "thresholds":dict(THRESHOLDS), "candidate_digest":candidate_digest,
            "pre_snapshot_digest":pre_snapshot_digest, "native_export_digest":native_export_digest}
    body["content_hash"] = _content(body); body["signature"] = sign(body, signing_key); return body

def validate_lock(value: Mapping[str, Any], trusted_keys: Mapping[str, Any]) -> P3ReleaseLockV1:
    keys = {"schema","key_id",*GO_BINDINGS,"artifacts","thresholds","candidate_digest","pre_snapshot_digest","native_export_digest","content_hash","signature"}
    if not isinstance(value, Mapping) or set(value) != keys or value.get("schema") != "P3ReleaseLockV1": raise P3ProtocolError("P3 lock schema")
    if not isinstance(trusted_keys, Mapping) or value.get("key_id") not in trusted_keys: raise P3ProtocolError("P3 untrusted lock key")
    if value.get("content_hash") != _content(value): raise P3ProtocolError("P3 lock hash")
    if value.get("thresholds") != THRESHOLDS: raise P3ProtocolError("P3 lock thresholds")
    if not isinstance(value.get("artifacts"), Mapping) or set(value["artifacts"]) != set(ARTIFACT_NAMES) or any(not is_digest(v) for v in value["artifacts"].values()): raise P3ProtocolError("P3 artifact closure")
    if any(not is_digest(value.get(field)) for field in (*GO_BINDINGS, "candidate_digest", "pre_snapshot_digest", "native_export_digest")): raise P3ProtocolError("P3 lock binding")
    try: verify_signature(dict(value), trusted_keys[value["key_id"]])
    except Exception as exc: raise P3ProtocolError("P3 lock signature") from exc
    return P3ReleaseLockV1(dict(value))
