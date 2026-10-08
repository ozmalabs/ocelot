"""Re-runnable RS-050 supervisor/resource evidence contract.

This module validates an evidence *shape* and its canonical bindings.  It does
not create supervisor identity, attest a process, sign evidence, or promote a
claim.  Promotion requires a separately operated ``NativeSupervisor`` adapter
with the existing ``trusted``/``independent`` boundary.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .protocol import P5R0Error, digest, is_digest
from .supervisor import validate_supervisor_evidence

CONTRACT_PATH = Path(__file__).with_name("RS050_CONTRACT.json")
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
RS050_SCHEMA = CONTRACT["evidence_schema"]
RS050_INVOCATION_SCHEMA = CONTRACT["invocation_schema"]
RS050_IDENTITY_SCHEMA = CONTRACT["identity_schema"]
RS050_CLAIM_BOUNDARY = CONTRACT["claim_boundary"]


def contract_digest() -> str:
    """Return the digest of the committed, repository-controlled contract."""
    return digest(CONTRACT)


def _closed(value: Mapping[str, Any], fields: list[str], schema: str, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(fields) or value.get("schema") != schema:
        raise P5R0Error(label)
    return dict(value)


def _require_digest(value: Any, label: str) -> str:
    if not is_digest(value):
        raise P5R0Error(label)
    return value


def _validate_identity(value: Mapping[str, Any]) -> dict[str, Any]:
    identity = _closed(value, CONTRACT["identity_fields"], RS050_IDENTITY_SCHEMA, "RS050 supervisor identity schema")
    if not isinstance(identity["supervisor_id"], str) or not identity["supervisor_id"] or len(identity["supervisor_id"]) > 256:
        raise P5R0Error("RS050 supervisor identity name")
    _require_digest(identity["authority_key_digest"], "RS050 supervisor authority key")
    if identity["authentication_method"] not in set(CONTRACT["authentication_methods"]):
        raise P5R0Error("RS050 supervisor authentication method")
    expected = digest({key: identity[key] for key in identity if key != "identity_digest"})
    if identity["identity_digest"] != expected:
        raise P5R0Error("RS050 supervisor identity digest")
    return identity


def _validate_invocation(
    value: Mapping[str, Any], *, run_id: str, lock_digest: str, closure_digest: str,
    supervisor_digest: str, resource_profile_digest: str,
) -> dict[str, Any]:
    invocation = _closed(value, CONTRACT["invocation_fields"], RS050_INVOCATION_SCHEMA, "RS050 invocation schema")
    for key, expected in (("run_id", run_id), ("lock_digest", lock_digest), ("closure_digest", closure_digest), ("supervisor_digest", supervisor_digest), ("resource_profile_digest", resource_profile_digest)):
        if invocation[key] != expected:
            raise P5R0Error(f"RS050 invocation {key} binding")
    _require_digest(invocation["task_id"], "RS050 invocation task binding")
    _require_digest(invocation["resource_observation_digest"], "RS050 resource observation digest")
    if type(invocation["sequence"]) is not int or invocation["sequence"] < 1:
        raise P5R0Error("RS050 invocation sequence")
    if type(invocation["worker_exit"]) is not int or not -255 <= invocation["worker_exit"] <= 255:
        raise P5R0Error("RS050 invocation exit")
    for key in ("timed_out", "oom", "process_group_killed", "cleanup_verified", "observed"):
        if type(invocation[key]) is not bool:
            raise P5R0Error(f"RS050 invocation {key}")
    if invocation["observed"] is not True:
        raise P5R0Error("RS050 invocation is not observed")
    if invocation["timed_out"] and invocation["oom"]:
        raise P5R0Error("RS050 invocation timeout/OOM ambiguity")
    if invocation["worker_exit"] == 0 and (invocation["timed_out"] or invocation["oom"]):
        raise P5R0Error("RS050 resource failure has zero exit")
    if invocation["timed_out"] or invocation["oom"]:
        if invocation["process_group_killed"] is not True or invocation["cleanup_verified"] is not True:
            raise P5R0Error("RS050 resource failure cleanup")
    if invocation["process_group_killed"] and not invocation["cleanup_verified"]:
        raise P5R0Error("RS050 killed process group cleanup")
    if not invocation["cleanup_verified"]:
        raise P5R0Error("RS050 cleanup observation")
    expected = digest({key: invocation[key] for key in invocation if key != "evidence_digest"})
    if invocation["evidence_digest"] != expected:
        raise P5R0Error("RS050 invocation evidence digest")
    return invocation


def _aggregate_matches(supervisor_evidence: Mapping[str, Any], invocations: list[dict[str, Any]]) -> None:
    exits = [item["worker_exit"] for item in invocations]
    if type(supervisor_evidence["worker_invocations"]) is not int or supervisor_evidence["worker_invocations"] < 1:
        raise P5R0Error("RS050 aggregate invocation count")
    if type(supervisor_evidence["worker_exit"]) is not int or not -255 <= supervisor_evidence["worker_exit"] <= 255:
        raise P5R0Error("RS050 aggregate exit")
    if supervisor_evidence["worker_invocations"] != len(invocations):
        raise P5R0Error("RS050 aggregate invocation count")
    if supervisor_evidence["worker_exit"] == 0 and any(exit_code != 0 for exit_code in exits):
        raise P5R0Error("RS050 aggregate exit")
    if supervisor_evidence["worker_exit"] != 0 and all(exit_code == 0 for exit_code in exits):
        raise P5R0Error("RS050 aggregate exit")
    expected_flags = {
        "observed": True,
        "timed_out": any(item["timed_out"] for item in invocations),
        "oom": any(item["oom"] for item in invocations),
        "process_group_killed": any(item["process_group_killed"] for item in invocations),
        "cleanup_verified": all(item["cleanup_verified"] for item in invocations),
    }
    for key, expected in expected_flags.items():
        if supervisor_evidence[key] != expected:
            raise P5R0Error(f"RS050 aggregate {key}")


def validate_rs050_evidence(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate RS-050 structure and bindings, without authenticating it.

    The returned report deliberately has ``authenticated=False`` and
    ``promotable=False``.  A digest only proves that supplied bytes were
    reproduced; it does not prove who observed the worker or resource state.
    """
    evidence = _closed(value, CONTRACT["evidence_fields"], RS050_SCHEMA, "RS050 evidence schema")
    for key in ("run_id", "lock_digest", "closure_digest", "resource_profile_digest", "contract_digest"):
        _require_digest(evidence[key], f"RS050 evidence {key}")
    if evidence["contract_digest"] != contract_digest():
        raise P5R0Error("RS050 contract digest")
    if evidence["claim_boundary"] != RS050_CLAIM_BOUNDARY:
        raise P5R0Error("RS050 claim boundary")
    identity = _validate_identity(evidence["supervisor_identity"])
    supervisor_evidence = validate_supervisor_evidence(
        evidence["supervisor_evidence"], run_id=evidence["run_id"],
        lock_digest=evidence["lock_digest"], closure_digest=evidence["closure_digest"],
    )
    if supervisor_evidence["supervisor_digest"] != identity["identity_digest"]:
        raise P5R0Error("RS050 supervisor identity binding")
    if not isinstance(evidence["invocations"], list) or not evidence["invocations"]:
        raise P5R0Error("RS050 invocation ledger")
    invocations = [
        _validate_invocation(
            item, run_id=evidence["run_id"], lock_digest=evidence["lock_digest"],
            closure_digest=evidence["closure_digest"], supervisor_digest=identity["identity_digest"],
            resource_profile_digest=evidence["resource_profile_digest"],
        )
        for item in evidence["invocations"]
    ]
    if evidence["worker_invocations"] != len(invocations) or type(evidence["worker_invocations"]) is not int or evidence["worker_invocations"] < 1:
        raise P5R0Error("RS050 evidence invocation count")
    if [item["sequence"] for item in invocations] != list(range(1, len(invocations) + 1)):
        raise P5R0Error("RS050 invocation sequence closure")
    if len({item["task_id"] for item in invocations}) != len(invocations):
        raise P5R0Error("RS050 task binding uniqueness")
    _aggregate_matches(supervisor_evidence, invocations)
    expected = digest({key: evidence[key] for key in evidence if key != "evidence_digest"})
    if evidence["evidence_digest"] != expected:
        raise P5R0Error("RS050 evidence digest")
    return {
        "schema": "P5R0RS050ValidationReportV1",
        "contract_digest": evidence["contract_digest"],
        "evidence_digest": evidence["evidence_digest"],
        "run_id": evidence["run_id"],
        "lock_digest": evidence["lock_digest"],
        "closure_digest": evidence["closure_digest"],
        "worker_invocations": len(invocations),
        "authenticated": False,
        "promotable": False,
        "claim_boundary": RS050_CLAIM_BOUNDARY,
    }


def validate_authenticated_rs050_evidence(value: Mapping[str, Any], supervisor: Any) -> dict[str, Any]:
    """Authenticate RS-050 evidence through the existing supervisor seam.

    This function accepts no identity or evidence from the repository itself.
    The adapter must be trusted/independent and must validate both the closed
    supervisor observation and its bounded-resource claim.  A missing adapter,
    local digest, or self-declared identity therefore remains non-promotable.
    """
    report = validate_rs050_evidence(value)
    if getattr(supervisor, "trusted", False) is not True or getattr(supervisor, "independent", False) is not True:
        raise P5R0Error("RS050 supervisor trust boundary")
    validate_observation = getattr(supervisor, "validate_execution_evidence", None)
    validate_resource = getattr(supervisor, "validate_bounded_compute_claim", None)
    if not callable(validate_observation) or not callable(validate_resource):
        raise P5R0Error("RS050 supervisor adapter")
    try:
        observation_ok = validate_observation(value["supervisor_evidence"]) is True
        resource_claim = {
            "schema": "P5R0RS050ResourceClaimV1",
            "run_id": value["run_id"],
            "lock_digest": value["lock_digest"],
            "closure_digest": value["closure_digest"],
            "resource_profile_digest": value["resource_profile_digest"],
            "evidence_digest": value["evidence_digest"],
        }
        resource_ok = validate_resource(resource_claim) is True
    except Exception as exc:
        raise P5R0Error("RS050 supervisor authentication") from exc
    if not observation_ok or not resource_ok:
        raise P5R0Error("RS050 supervisor authentication")
    report["authenticated"] = True
    report["promotable"] = True
    return report


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an RS-050 evidence contract locally")
    parser.add_argument("--evidence", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.evidence.read_text(encoding="utf-8"))
        report = validate_rs050_evidence(value)
    except (OSError, json.JSONDecodeError, P5R0Error) as exc:
        print(f"RS-050 validation failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
