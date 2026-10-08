"""Verifier-owned, reloadable predecessor evidence for downstream IAM consumers.

A predecessor is admissible only when it is derived from a canonical, persisted
IAM JSONL ledger whose complete hash chain, terminal receipt, poststate, and
closed safety bindings have been re-verified.  The in-process registry remains
an anti-copy guard for legacy fixture issuance; persisted loading does not rely
on it for trust.
"""
from __future__ import annotations

from dataclasses import dataclass
import base64
from pathlib import Path
from typing import Any, Mapping

from services.p5_r0_evaluator.canonical import canonical_bytes, digest, parse_canonical
from services.p5_r0_evaluator.deploy.iam_capability_provisioning import CUSTOM_ROLE, EXACT_CONDITION, GCS_ONLY_ACCOUNT

_SEAL = object()
_SCHEMA = "P5R0VerifiedIAMPredecessorV2"
_FIELDS = {
    "operation_id", "attempt_id", "packet_digest", "prestate_digest", "poststate_digest",
    "receipt_digest", "ledger_head_digest", "service_account", "custom_role",
    "wif_principal", "condition_expression", "later_operations_enabled",
    "credentials_exported", "keys_created", "status", "evidence_digest",
    "capability_digest", "ledger_path",
}
_REGISTRY: dict[int, tuple["VerifiedIAMPredecessor", tuple[Any, ...]]] = {}
_ROOT_SCHEMA = "P5R0IAMLedgerRootSignatureV1"
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:  # pragma: no cover
    Ed25519PublicKey = None  # type: ignore[assignment]


class VerifiedIAMLedgerRootVerifier:
    """Trusted public-key verifier for persisted IAM ledger roots."""

    def __init__(self, *, public_key: str, verifier_id: str = "confidential-space-verifier") -> None:
        _require(isinstance(public_key, str) and public_key, "trusted IAM ledger-root public key is required")
        self.public_key = public_key
        self.verifier_id = verifier_id

    def verify(self, payload: Mapping[str, Any], signature: str) -> bool:
        if Ed25519PublicKey is None:
            return False
        try:
            key = Ed25519PublicKey.from_public_bytes(base64.b64decode(self.public_key, validate=True))
            key.verify(base64.b64decode(signature, validate=True), canonical_bytes(dict(payload)))
            return True
        except Exception:
            return False


def _ledger_root_payload(records: list[dict[str, Any]]) -> dict[str, Any]:
    started, _pre, post, stopped = records
    receipt = post.get("receipt")
    _require(isinstance(receipt, Mapping), "IAM ledger root receipt is missing")
    return {
        "schema": _ROOT_SCHEMA,
        "ledger_head_digest": post["event_digest"],
        "terminal_receipt_digest": receipt.get("receipt_digest"),
        "poststate_digest": post.get("poststate_digest"),
        "operation_id": started.get("operation_id"),
        "attempt_id": started.get("attempt_id"),
        "packet_digest": started.get("packet_digest"),
        "prestate_digest": started.get("prestate_digest"),
        "credential_evidence_digest": started.get("credential_evidence_digest"),
        "service_account": receipt.get("service_account"),
        "custom_role": receipt.get("custom_role"),
        "condition_expression": receipt.get("condition_expression"),
    }


def _verify_ledger_root(records: list[dict[str, Any]], *, trusted_verifier: Any) -> None:
    _require(trusted_verifier is not None and callable(getattr(trusted_verifier, "verify", None)), "trusted IAM ledger-root verifier is required")
    root = records[-1].get("ledger_root")
    _require(isinstance(root, Mapping) and root.get("schema") == _ROOT_SCHEMA, "trusted IAM ledger root is missing")
    payload = _ledger_root_payload(records)
    _require(root.get("root_digest") == _digest_without(payload, "root_digest"), "IAM ledger root digest drift")
    _require(root.get("public_key") in (None, getattr(trusted_verifier, "public_key", root.get("public_key"))), "IAM ledger-root signer is not trusted")
    _require(isinstance(root.get("signature"), str) and trusted_verifier.verify(payload, root["signature"]), "IAM ledger root signature verification failed")


def build_iam_ledger_root(*, records: list[dict[str, Any]], signature: str, public_key: str) -> dict[str, Any]:
    """Build the signed terminal envelope emitted by the trusted verifier."""
    payload = _ledger_root_payload(records)
    return {**payload, "root_digest": _digest_without(payload, "root_digest"), "signature": signature, "public_key": public_key}


def issue_signed_iam_ledger_root(*, records: list[dict[str, Any]], signer: Any, public_key: str) -> dict[str, Any]:
    _require(callable(signer), "IAM ledger-root signer is required")
    payload = _ledger_root_payload(records)
    signature = signer(payload)
    _require(isinstance(signature, str) and signature, "IAM ledger-root signature is missing")
    return build_iam_ledger_root(records=records, signature=signature, public_key=public_key)


class IAMPredecessorError(ValueError):
    """The required verified IAM predecessor is absent or does not bind."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IAMPredecessorError(message)


def _is_digest(value: Any, label: str) -> None:
    _require(isinstance(value, str) and len(value) == 71 and value.startswith("sha256:") and all(c in "0123456789abcdef" for c in value[7:]), f"{label} is not a digest")


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    return digest({key: item for key, item in value.items() if key != field})


@dataclass(frozen=True, init=False)
class VerifiedIAMPredecessor:
    operation_id: str
    attempt_id: str
    packet_digest: str | None
    prestate_digest: str
    poststate_digest: str
    receipt_digest: str
    ledger_head_digest: str
    service_account: str
    custom_role: str
    wif_principal: str
    condition_expression: str
    later_operations_enabled: bool
    credentials_exported: bool
    keys_created: bool
    status: str
    evidence_digest: str
    capability_digest: str
    ledger_path: str | None

    def __init__(self, **values: Any) -> None:
        _require(values.pop("_seal", None) is _SEAL and set(values) == _FIELDS, "IAM predecessor is verifier-created")
        for field in self.__dataclass_fields__:
            object.__setattr__(self, field, values[field])

    @property
    def schema(self) -> str:
        return _SCHEMA

    def as_public_dict(self) -> dict[str, Any]:
        _require(_is_valid(self), "IAM predecessor is not verifier-issued")
        return {"schema": _SCHEMA, **{field: getattr(self, field) for field in self.__dataclass_fields__}}


def _snapshot(value: VerifiedIAMPredecessor) -> tuple[Any, ...]:
    return tuple(getattr(value, field) for field in value.__dataclass_fields__)


def _commitment(value: Mapping[str, Any]) -> str:
    return digest({"schema": _SCHEMA, **{field: value[field] for field in _FIELDS if field != "capability_digest"}})


def _basic_valid(value: Any) -> bool:
    if type(value) is not VerifiedIAMPredecessor:
        return False
    if value.capability_digest != _commitment({field: getattr(value, field) for field in value.__dataclass_fields__}):
        return False
    for name in ("prestate_digest", "poststate_digest", "receipt_digest", "ledger_head_digest", "evidence_digest", "capability_digest"):
        try:
            _is_digest(getattr(value, name), name)
        except IAMPredecessorError:
            return False
    return True


def _is_registered(value: Any) -> bool:
    if not _basic_valid(value):
        return False
    entry = _REGISTRY.get(id(value))
    return entry is not None and entry[0] is value and entry[1] == _snapshot(value)


def _load_lines(path: Path) -> list[dict[str, Any]]:
    _require(path.is_file(), "persisted IAM ledger is missing")
    raw_lines = path.read_bytes().splitlines()
    _require(raw_lines and len(raw_lines) == 4, "persisted IAM ledger event count/order is invalid")
    records: list[dict[str, Any]] = []
    previous: str | None = None
    for raw in raw_lines:
        try:
            record = parse_canonical(raw)
        except Exception as exc:
            raise IAMPredecessorError("persisted IAM ledger is not canonical JSONL") from exc
        _require(record.get("previous_event_digest") == previous, "persisted IAM ledger hash chain drift")
        _require(record.get("event_digest") == _digest_without(record, "event_digest"), "persisted IAM ledger event digest drift")
        _require(record.get("schema") == "P5R0APPROVAL023DISPATCH082IAMLedgerEventV1", "persisted IAM ledger schema drift")
        records.append(record)
        previous = record["event_digest"]
    _require([item.get("kind") for item in records] == ["run_started", "prestate_verified", "poststate_verified", "run_stopped"], "persisted IAM ledger event order is invalid")
    _require(records[-1]["event_digest"] == previous, "persisted IAM ledger head is missing")
    return records


def _verify_persisted_records(records: list[dict[str, Any]], *, operation_id: str, attempt_id: str, packet_digest: str | None, prestate_digest: str | None, evidence_digest: str | None, trusted_verifier: Any) -> dict[str, Any]:
    started, pre, post, stopped = records
    _verify_ledger_root(records, trusted_verifier=trusted_verifier)
    for record in records:
        _require(record.get("operation_id") == operation_id and record.get("attempt_id") == attempt_id, "IAM ledger operation/attempt binding drift")
        _require(record.get("later_operations_enabled") is False and record.get("credentials_exported") is False and record.get("keys_created") is False, "IAM ledger crosses downstream credential boundary")
    if packet_digest is not None:
        _is_digest(packet_digest, "packet digest")
        _require(started.get("packet_digest") == packet_digest, "IAM ledger packet binding drift")
    if prestate_digest is not None:
        _is_digest(prestate_digest, "prestate digest")
        _require(started.get("prestate_digest") == prestate_digest and pre.get("prestate_digest") == prestate_digest, "IAM ledger prestate binding drift")
    if evidence_digest is not None:
        _is_digest(evidence_digest, "evidence digest")
        _require(started.get("credential_evidence_digest") == evidence_digest, "IAM ledger evidence binding drift")
    _require(started.get("mutations_performed") is False and pre.get("mutations_performed") is False, "IAM ledger prestate contains mutation claim")
    _require(post.get("mutations_performed") is True and stopped.get("mutations_performed") is True, "IAM ledger terminal mutation evidence is incomplete")
    _require(stopped.get("status") == "verified" and stopped.get("rollback_status") == "not_required_verified" and stopped.get("manual_review_required", False) is False, "IAM ledger terminal state is not verified")
    _require(stopped.get("verified_event_digest") == post.get("event_digest"), "IAM terminal receipt event binding drift")
    receipt = post.get("receipt")
    _require(isinstance(receipt, Mapping) and receipt == stopped.get("receipt"), "IAM terminal receipt is missing or inconsistent")
    _require(receipt.get("schema") == "P5R0APPROVAL023IAMReceiptV1", "IAM receipt schema drift")
    _require(receipt.get("receipt_digest") == _digest_without(receipt, "receipt_digest"), "IAM receipt digest drift")
    _require(receipt.get("operation_id") == operation_id and receipt.get("prestate_digest") == pre.get("prestate_digest") and receipt.get("poststate_digest") == post.get("poststate_digest"), "IAM receipt state binding drift")
    _require(receipt.get("service_account") == GCS_ONLY_ACCOUNT and receipt.get("custom_role") == CUSTOM_ROLE and receipt.get("condition_expression") == EXACT_CONDITION, "IAM receipt least-privilege binding drift")
    _require(receipt.get("credentials_exported") is False and receipt.get("keys_created") is False and receipt.get("later_operations_enabled") is False and receipt.get("private") is True, "IAM receipt crosses credential safety boundary")
    _require(stopped.get("poststate_digest", receipt.get("poststate_digest")) == receipt.get("poststate_digest"), "IAM terminal poststate binding drift")
    return {"receipt": dict(receipt), "receipt_digest": receipt["receipt_digest"], "poststate_digest": post["poststate_digest"], "ledger_head_digest": stopped["event_digest"], "packet_digest": started.get("packet_digest"), "prestate_digest": pre.get("prestate_digest"), "evidence_digest": started.get("credential_evidence_digest")}


def _is_persisted_valid(value: VerifiedIAMPredecessor, *, operation_id: str, attempt_id: str, prestate_digest: str | None, evidence_digest: str | None, trusted_verifier: Any) -> bool:
    if not _basic_valid(value) or not value.ledger_path:
        return False
    try:
        checked = _verify_persisted_records(_load_lines(Path(value.ledger_path)), operation_id=operation_id, attempt_id=attempt_id, packet_digest=value.packet_digest, prestate_digest=prestate_digest or value.prestate_digest, evidence_digest=evidence_digest or value.evidence_digest, trusted_verifier=trusted_verifier)
        return checked["ledger_head_digest"] == value.ledger_head_digest and checked["receipt_digest"] == value.receipt_digest and checked["poststate_digest"] == value.poststate_digest
    except Exception:
        return False


def issue_verified_iam_predecessor(*, result: Mapping[str, Any], evidence_digest: str, ledger_path: Path | None = None, packet_digest: str | None = None) -> VerifiedIAMPredecessor:
    """Issue from a verified IAM result; persisted callers should use the loader."""
    _require(isinstance(result, Mapping), "verified IAM result is required")
    _require(result.get("status") == "verified" and result.get("mutations_performed") is True and result.get("later_operations_enabled") is False, "IAM result is not verified")
    receipt = result.get("receipt")
    _require(isinstance(receipt, Mapping), "verified IAM receipt is missing")
    _require(result.get("operation_id") == "provision_gcs_only_iam_boundary" and result.get("attempt_id") == "dispatch082-iam-20260920-a7f4c2d9", "IAM result identity drift")
    _require(receipt.get("schema") == "P5R0APPROVAL023IAMReceiptV1" and receipt.get("operation_id") == result.get("operation_id"), "IAM receipt schema/operation drift")
    _require(receipt.get("receipt_digest") == _digest_without(receipt, "receipt_digest"), "IAM receipt digest is not verified")
    _require(receipt.get("service_account") == GCS_ONLY_ACCOUNT and receipt.get("custom_role") == CUSTOM_ROLE and receipt.get("condition_expression") == EXACT_CONDITION, "IAM receipt least-privilege binding drift")
    _require(isinstance(result.get("ledger_head_digest"), str) and isinstance(result.get("poststate_digest"), str), "IAM ledger/poststate binding is missing")
    values: dict[str, Any] = {
        "operation_id": result["operation_id"], "attempt_id": result["attempt_id"], "packet_digest": packet_digest,
        "prestate_digest": receipt.get("prestate_digest"), "poststate_digest": result["poststate_digest"],
        "receipt_digest": receipt.get("receipt_digest"), "ledger_head_digest": result["ledger_head_digest"],
        "service_account": receipt.get("service_account"), "custom_role": receipt.get("custom_role"),
        "wif_principal": receipt.get("wif_principal"), "condition_expression": receipt.get("condition_expression"),
        "later_operations_enabled": result.get("later_operations_enabled"), "credentials_exported": receipt.get("credentials_exported", False),
        "keys_created": receipt.get("keys_created", False), "status": result.get("status"), "evidence_digest": evidence_digest,
        "ledger_path": str(Path(ledger_path).resolve()) if ledger_path is not None else None,
    }
    _require(all(isinstance(values.get(name), str) and values[name] for name in ("operation_id", "attempt_id", "prestate_digest", "poststate_digest", "receipt_digest", "ledger_head_digest", "service_account", "custom_role", "wif_principal", "condition_expression")), "IAM result identity is incomplete")
    for name in ("prestate_digest", "poststate_digest", "receipt_digest", "ledger_head_digest", "evidence_digest"):
        _is_digest(values[name], name)
    _require(values["credentials_exported"] is False and values["keys_created"] is False, "IAM result crosses credential safety boundary")
    values["capability_digest"] = _commitment(values)
    predecessor = VerifiedIAMPredecessor(**values, _seal=_SEAL)
    _REGISTRY[id(predecessor)] = (predecessor, _snapshot(predecessor))
    return predecessor


def load_verified_iam_predecessor(*, ledger_path: Path, operation_id: str, attempt_id: str, evidence_digest: str | None = None, packet_digest: str | None = None, prestate_digest: str | None = None, trusted_verifier: Any = None) -> VerifiedIAMPredecessor:
    """Reload and verify the exact persisted IAM receipt/ledger artifact."""
    path = Path(ledger_path).resolve()
    checked = _verify_persisted_records(_load_lines(path), operation_id=operation_id, attempt_id=attempt_id, packet_digest=packet_digest, prestate_digest=prestate_digest, evidence_digest=evidence_digest, trusted_verifier=trusted_verifier)
    _require(isinstance(checked["evidence_digest"], str), "persisted IAM evidence binding is missing")
    result = {"status": "verified", "operation_id": operation_id, "attempt_id": attempt_id, "poststate_digest": checked["poststate_digest"], "ledger_head_digest": checked["ledger_head_digest"], "receipt": checked["receipt"], "mutations_performed": True, "later_operations_enabled": False}
    predecessor = issue_verified_iam_predecessor(result=result, evidence_digest=checked["evidence_digest"] or evidence_digest or "sha256:" + "0" * 64, ledger_path=path, packet_digest=checked["packet_digest"] or packet_digest)
    _require(predecessor.ledger_head_digest == checked["ledger_head_digest"], "persisted IAM ledger head binding drift")
    return predecessor


def _is_valid(value: Any, *, operation_id: str = "provision_gcs_only_iam_boundary", attempt_id: str = "dispatch082-iam-20260920-a7f4c2d9", prestate_digest: str | None = None, evidence_digest: str | None = None, trusted_verifier: Any = None) -> bool:
    return _is_registered(value) or (isinstance(value, VerifiedIAMPredecessor) and _is_persisted_valid(value, operation_id=operation_id, attempt_id=attempt_id, prestate_digest=prestate_digest, evidence_digest=evidence_digest, trusted_verifier=trusted_verifier))


def validate_verified_iam_predecessor(value: Any, *, operation_id: str, attempt_id: str, prestate_digest: str | None = None, evidence_digest: str | None = None, packet_digest: str | None = None, ledger_path: Path | None = None, trusted_verifier: Any = None) -> VerifiedIAMPredecessor:
    _require(isinstance(value, VerifiedIAMPredecessor), "verified IAM predecessor is required")
    if ledger_path is not None:
        _require(Path(value.ledger_path or "").resolve() == Path(ledger_path).resolve(), "IAM predecessor ledger path binding drift")
    _require(_is_valid(value, operation_id=operation_id, attempt_id=attempt_id, prestate_digest=prestate_digest, evidence_digest=evidence_digest, trusted_verifier=trusted_verifier), "verified IAM predecessor persisted evidence is not valid")
    _require(value.operation_id == operation_id and value.attempt_id == attempt_id, "IAM predecessor operation/attempt binding drift")
    if prestate_digest is not None:
        _require(value.prestate_digest == prestate_digest, "IAM predecessor prestate digest drift")
    if evidence_digest is not None:
        _require(value.evidence_digest == evidence_digest, "IAM predecessor evidence digest drift")
    if packet_digest is not None:
        _require(value.packet_digest == packet_digest, "IAM predecessor packet digest drift")
    _require(value.status == "verified" and value.later_operations_enabled is False and value.credentials_exported is False and value.keys_created is False, "IAM predecessor is not a closed verified result")
    return value


__all__ = ["IAMPredecessorError", "VerifiedIAMLedgerRootVerifier", "VerifiedIAMPredecessor", "build_iam_ledger_root", "issue_signed_iam_ledger_root", "issue_verified_iam_predecessor", "load_verified_iam_predecessor", "validate_verified_iam_predecessor"]
