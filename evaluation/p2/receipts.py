"""Durable signed P2 terminal receipts and independent append-failure seals."""
from __future__ import annotations
import fcntl
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from evaluation.p0a.canonical import canonical_bytes, object_hash, parse_canonical, sign, verify_signature
from .protocol import P2ProtocolError

_REQUIRED = frozenset({"lock_status", "lock_digest", "input_digest", "proposal_digest", "reconstruction_digest", "worker_image_digest", "evaluator_binary_digest", "outcome", "scoring_vector"})
# This optional field is non-authoritative evidence. `input_digest` is populated
# only after the release lock has been verified against the trusted key.
_OPTIONAL_DIGEST_FIELDS = frozenset({"submitted_input_evidence_hash"})
_HOSTILE_BYPASS_EVIDENCE_FIELD = "hostile_bypass_evidence"
_OPTIONAL_TERMINAL_FIELDS = _OPTIONAL_DIGEST_FIELDS | {_HOSTILE_BYPASS_EVIDENCE_FIELD}
_NATIVE_BYPASS_ROUTES = frozenset({"agent_write", "callback", "evaluator_path", "host_protocol", "id_only_route", "input_write", "network", "shell", "undeclared_binary"})
_PYTHON_BYPASS_ROUTES = _NATIVE_BYPASS_ROUTES | {"python_execution"}
_FORBIDDEN = frozenset({"hidden_state", "authoritative_world_state", "transition_table", "enactment_rank", "secret_seed", "fixture_path"})
_DIGEST_FIELDS = ("lock_digest", "input_digest", "proposal_digest", "reconstruction_digest", "worker_image_digest", "evaluator_binary_digest")
_LOCK_BOUND_DIGEST_FIELDS = ("lock_digest", "input_digest", "worker_image_digest", "evaluator_binary_digest")
_LOCK_STATUSES = frozenset({"verified", "unverified"})


def _safe_mapping(value: Any) -> None:
    if isinstance(value, dict):
        if _FORBIDDEN & set(value):
            raise P2ProtocolError("hidden receipt field")
        for child in value.values():
            _safe_mapping(child)
    elif isinstance(value, list):
        for child in value:
            _safe_mapping(child)


def _receipt_digest(value: Any) -> None:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        raise P2ProtocolError("receipt digest")


def _hostile_bypass_evidence(value: Any) -> None:
    """Validate the complete bounded hostile-probe record carried by a receipt."""
    if not isinstance(value, dict) or set(value) != {"schema", "status", "native_attempts", "python_attempts", "evaluator_mounts"}:
        raise P2ProtocolError("hostile bypass evidence")
    if value["schema"] != "P2HostileBypassEvidenceV2" or value["status"] != "contained":
        raise P2ProtocolError("hostile bypass evidence")
    for field, routes, no_effect_route in (("native_attempts", _NATIVE_BYPASS_ROUTES, None),
                                           ("python_attempts", _PYTHON_BYPASS_ROUTES, "python_execution")):
        attempts = value[field]
        if not isinstance(attempts, dict) or set(attempts) != routes:
            raise P2ProtocolError("hostile bypass routes")
        for route in routes:
            record = attempts[route]
            expected_result = "executed_no_effect" if route == no_effect_route else "blocked"
            if (not isinstance(record, dict) or set(record) != {"attempted", "result"}
                    or record["attempted"] is not True or record["result"] != expected_result):
                raise P2ProtocolError("hostile bypass route result")
    mounts = value["evaluator_mounts"]
    if not isinstance(mounts, dict) or set(mounts) != {"agent", "input"}:
        raise P2ProtocolError("hostile bypass mounts")
    for mount in mounts.values():
        if not isinstance(mount, dict) or set(mount) != {"before", "after"}:
            raise P2ProtocolError("hostile bypass mount commitment")
        _receipt_digest(mount["before"])
        _receipt_digest(mount["after"])
        if mount["before"] != mount["after"]:
            raise P2ProtocolError("hostile bypass mount mutation")


def _terminal(receipt: dict[str, Any]) -> None:
    _safe_mapping(receipt)
    legacy_verified = "lock_status" not in receipt
    if _REQUIRED - set(receipt) - ({"lock_status"} if legacy_verified else set()) or set(receipt) - _REQUIRED - _OPTIONAL_TERMINAL_FIELDS:
        raise P2ProtocolError("terminal receipt fields")
    lock_status = receipt.get("lock_status", "verified")
    if lock_status not in _LOCK_STATUSES:
        raise P2ProtocolError("receipt lock status")
    if not isinstance(receipt["outcome"], dict) or not isinstance(receipt["scoring_vector"], dict):
        raise P2ProtocolError("terminal receipt payload")
    if lock_status == "unverified":
        if any(receipt[name] is not None for name in _LOCK_BOUND_DIGEST_FIELDS):
            raise P2ProtocolError("unverified receipt authority")
        if "submitted_input_evidence_hash" not in receipt:
            raise P2ProtocolError("unverified receipt evidence")
    for name in (*_DIGEST_FIELDS, *_OPTIONAL_DIGEST_FIELDS):
        if name not in receipt:
            continue
        value = receipt[name]
        if value is None and lock_status == "unverified" and name in _LOCK_BOUND_DIGEST_FIELDS:
            continue
        _receipt_digest(value)
    if _HOSTILE_BYPASS_EVIDENCE_FIELD in receipt:
        evidence = receipt[_HOSTILE_BYPASS_EVIDENCE_FIELD]
        _hostile_bypass_evidence(evidence)
        if receipt["outcome"].get("hostile_bypass_evidence_hash") != object_hash(evidence):
            raise P2ProtocolError("hostile bypass evidence hash")
        if receipt["outcome"].get("hostile_bypass_status") != evidence["status"]:
            raise P2ProtocolError("hostile bypass evidence status")


def _write_all(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("receipt short write")
        view = view[written:]


def _durable_probe(root: Path) -> None:
    """Exercise the same directory durability primitives used by append before launch."""
    target = root / ".receipt-preflight"
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
        try:
            _write_all(fd, b"P2 receipt preflight\n")
            os.fsync(fd)
        finally:
            os.close(fd)
        os.unlink(target)
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as exc:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise P2ProtocolError("receipt append preflight") from exc


@dataclass
class ReceiptLog:
    """Exclusive append with verified restart recovery and a signed hash chain."""
    root: Path
    signer: Any
    previous: str | None = field(init=False, default=None)
    sequence: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        if self.root.is_symlink():
            raise P2ProtocolError("receipt root symlink")
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not self.root.is_dir() or self.root.is_symlink():
            raise P2ProtocolError("receipt root")
        self._reload()

    @property
    def _public_key(self):
        return self.signer.public_key() if hasattr(self.signer, "public_key") else self.signer

    def preflight(self) -> None:
        self._reload()
        _durable_probe(self.root)

    def _reload(self) -> None:
        previous = None
        sequence = 0
        records = sorted(self.root.glob("*.json"))
        for expected, target in enumerate(records, start=1):
            if target.is_symlink() or target.name != f"{expected:06d}.json":
                raise P2ProtocolError("receipt chain layout")
            try:
                body = parse_canonical(target.read_bytes())
            except Exception as exc:
                raise P2ProtocolError("receipt canonical") from exc
            receipt_fields = {"schema", "sequence", "previous_receipt_hash", *_REQUIRED, "receipt_hash", "signature"}
            legacy_receipt_fields = receipt_fields - {"lock_status"}
            fields = set(body)
            if not ((receipt_fields <= fields and fields - receipt_fields <= _OPTIONAL_TERMINAL_FIELDS)
                    or (legacy_receipt_fields <= fields and fields - legacy_receipt_fields <= _OPTIONAL_TERMINAL_FIELDS)):
                raise P2ProtocolError("receipt schema")
            if body["schema"] != "P2ScoreReceiptV1" or body["sequence"] != expected or body["previous_receipt_hash"] != previous:
                raise P2ProtocolError("receipt chain")
            _terminal({key: body[key] for key in _REQUIRED | _OPTIONAL_TERMINAL_FIELDS if key in body})
            if body["receipt_hash"] != object_hash({key: value for key, value in body.items() if key not in {"receipt_hash", "signature"}}):
                raise P2ProtocolError("receipt hash")
            try:
                verify_signature(body, self._public_key, "receipt_hash")
            except Exception as exc:
                raise P2ProtocolError("receipt signature") from exc
            previous, sequence = body["receipt_hash"], expected
        self.previous, self.sequence = previous, sequence

    def append(self, receipt: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(receipt, dict):
            raise P2ProtocolError("receipt object")
        _terminal(receipt)
        lock_path = self.root / ".append.lock"
        lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            self._reload()
            body = {"schema": "P2ScoreReceiptV1", "sequence": self.sequence + 1, "previous_receipt_hash": self.previous, **receipt}
            body["receipt_hash"] = object_hash(body)
            body["signature"] = sign(body, self.signer, "receipt_hash")
            payload = canonical_bytes(body)
            target = self.root / f"{body['sequence']:06d}.json"
            try:
                fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
            except FileExistsError as exc:
                raise P2ProtocolError("receipt append collision") from exc
            try:
                _write_all(fd, payload)
                os.fsync(fd)
            finally:
                os.close(fd)
            os.chmod(target, 0o400)
            directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            self.previous, self.sequence = body["receipt_hash"], body["sequence"]
            return body
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)


@dataclass
class ReceiptFailureLog:
    """Evaluator-authority-only durable failure chain used when the normal receipt path fails."""
    root: Path
    signer: Any
    previous: str | None = field(init=False, default=None)
    sequence: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        if self.root.is_symlink():
            raise P2ProtocolError("receipt failure root symlink")
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not self.root.is_dir() or self.root.is_symlink():
            raise P2ProtocolError("receipt failure root")
        self._reload()

    @property
    def _public_key(self):
        return self.signer.public_key() if hasattr(self.signer, "public_key") else self.signer

    def preflight(self) -> None:
        self._reload()
        _durable_probe(self.root)

    def _reload(self) -> None:
        previous = None
        sequence = 0
        records = sorted(self.root.glob("*.json"))
        for expected, target in enumerate(records, start=1):
            if target.is_symlink() or target.name != f"{expected:06d}.json":
                raise P2ProtocolError("receipt failure chain layout")
            try:
                body = parse_canonical(target.read_bytes())
            except Exception as exc:
                raise P2ProtocolError("receipt failure canonical") from exc
            receipt_fields = {"schema", "sequence", "previous_failure_hash", *_REQUIRED, "attempted_classification", "failure_code", "failure_hash", "signature"}
            legacy_receipt_fields = receipt_fields - {"lock_status"}
            fields = set(body)
            if (not ((receipt_fields <= fields and fields - receipt_fields <= _OPTIONAL_TERMINAL_FIELDS)
                     or (legacy_receipt_fields <= fields and fields - legacy_receipt_fields <= _OPTIONAL_TERMINAL_FIELDS))
                    or body["schema"] != "P2ReceiptAppendFailureV1"):
                raise P2ProtocolError("receipt failure schema")
            if body["sequence"] != expected or body["previous_failure_hash"] != previous:
                raise P2ProtocolError("receipt failure chain")
            _terminal({key: body[key] for key in _REQUIRED | _OPTIONAL_TERMINAL_FIELDS if key in body})
            if not isinstance(body["attempted_classification"], str) or not isinstance(body["failure_code"], str):
                raise P2ProtocolError("receipt failure fields")
            if body["failure_hash"] != object_hash({key: value for key, value in body.items() if key not in {"failure_hash", "signature"}}):
                raise P2ProtocolError("receipt failure hash")
            try:
                verify_signature(body, self._public_key, "failure_hash")
            except Exception as exc:
                raise P2ProtocolError("receipt failure signature") from exc
            previous, sequence = body["failure_hash"], expected
        self.previous, self.sequence = previous, sequence

    def append(self, receipt: dict[str, Any], *, attempted_classification: str, failure_code: str) -> dict[str, Any]:
        if not isinstance(receipt, dict) or not isinstance(attempted_classification, str) or not isinstance(failure_code, str):
            raise P2ProtocolError("receipt failure record")
        _terminal(receipt)
        lock_path = self.root / ".append.lock"
        lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            self._reload()
            body = {"schema": "P2ReceiptAppendFailureV1", "sequence": self.sequence + 1,
                    "previous_failure_hash": self.previous, **receipt,
                    "attempted_classification": attempted_classification, "failure_code": failure_code}
            body["failure_hash"] = object_hash(body)
            body["signature"] = sign(body, self.signer, "failure_hash")
            payload = canonical_bytes(body)
            target = self.root / f"{body['sequence']:06d}.json"
            try:
                fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
            except FileExistsError as exc:
                raise P2ProtocolError("receipt failure append collision") from exc
            try:
                _write_all(fd, payload)
                os.fsync(fd)
            finally:
                os.close(fd)
            os.chmod(target, 0o400)
            directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            self.previous, self.sequence = body["failure_hash"], body["sequence"]
            return body
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
