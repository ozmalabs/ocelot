"""Evaluator-owned P4-R0 append-only signed receipt chain."""
from __future__ import annotations
import fcntl
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evaluation.p0a.canonical import canonical_bytes, object_hash, parse_canonical, sign, verify_signature
from .protocol import P4ProtocolError, is_digest

KINDS = frozenset({"containment", "task_release", "proposal", "grant", "action", "outcome", "replan", "denial", "impasse", "terminal", "rollback", "result"})
_PAYLOAD_FIELDS = {"schema", "run_id", "lock_digest", "fixture_digest", "fixture_record_digest", "fixture_id", "fixture_selection_id", "graph_snapshot_digest", "resource_ledger", "outcome", "reason", "binding"}

@dataclass
class P4ReceiptLog:
    root: Path
    signer: Any
    authority_id: str = "p4-r0-evaluator"
    key_id: str = "p4-r0-local-evaluator"
    previous: str | None = field(init=False, default=None)
    sequence: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.is_symlink() or not self.root.is_dir():
            raise P4ProtocolError("receipt root")
        self.reload()

    @property
    def public_key(self) -> Any:
        return self.signer.public_key() if hasattr(self.signer, "public_key") else self.signer

    def _payload(self, kind: str, p: dict[str, Any]) -> None:
        if (set(p) != _PAYLOAD_FIELDS or p.get("schema") != "P4R0ReceiptPayloadV1"
                or not isinstance(p["run_id"], str) or not p["run_id"]
                or not all(is_digest(p[x]) for x in ("lock_digest", "fixture_digest", "fixture_record_digest", "graph_snapshot_digest"))
                or not all(isinstance(p[x], str) and p[x] for x in ("fixture_id", "fixture_selection_id"))
                or not isinstance(p["resource_ledger"], dict)
                or set(p["resource_ledger"]) != {"actions", "risk", "transactions"}
                or any(type(n) is not int or n < 0 for n in p["resource_ledger"].values())
                or p["outcome"] not in {"no_go", "impasse", "blocked", "released", "verified", "restored"}
                or not isinstance(p["reason"], str) or not isinstance(p["binding"], dict)):
            raise P4ProtocolError("receipt payload")

    def _validate_receipt(self, b: dict[str, Any], sequence: int, previous: str | None) -> None:
        fields = {"schema", "sequence", "previous_hash", "kind", "payload", "receipt_hash", "signature"}
        if (set(b) != fields or b["schema"] != "P4ReceiptV1" or b["sequence"] != sequence
                or b["previous_hash"] != previous or b["kind"] not in KINDS or not isinstance(b["payload"], dict)
                or not is_digest(b["receipt_hash"])):
            raise P4ProtocolError("receipt chain")
        self._payload(b["kind"], b["payload"])
        if b["receipt_hash"] != object_hash(b, "receipt_hash", "signature"):
            raise P4ProtocolError("receipt hash")
        try:
            verify_signature(b, self.public_key, "receipt_hash")
        except Exception as exc:
            raise P4ProtocolError("receipt signature") from exc

    def _records(self) -> list[dict[str, Any]]:
        previous = None
        records = []
        for sequence, path in enumerate(sorted(self.root.glob("*.json")), 1):
            if path.is_symlink() or not path.is_file():
                raise P4ProtocolError("receipt file")
            try:
                b = parse_canonical(path.read_bytes())
            except Exception as exc:
                raise P4ProtocolError("receipt canonical") from exc
            self._validate_receipt(b, sequence, previous)
            previous = b["receipt_hash"]
            records.append(b)
        return records

    def reload(self) -> None:
        records = self._records()
        self.previous = records[-1]["receipt_hash"] if records else None
        self.sequence = len(records)

    def get(self, receipt_hash: str) -> dict[str, Any]:
        if not is_digest(receipt_hash):
            raise P4ProtocolError("receipt digest")
        for receipt in self._records():
            if receipt["receipt_hash"] == receipt_hash:
                return receipt
        raise P4ProtocolError("unknown receipt")

    def append(self, kind: str, receipt_payload: dict[str, Any]) -> dict[str, Any]:
        if kind not in KINDS:
            raise P4ProtocolError("receipt kind")
        self._payload(kind, receipt_payload)
        fd = os.open(self.root / ".append.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            self.reload()
            b = {"schema": "P4ReceiptV1", "sequence": self.sequence + 1, "previous_hash": self.previous, "kind": kind, "payload": receipt_payload}
            b["receipt_hash"] = object_hash(b)
            b["signature"] = sign(b, self.signer, "receipt_hash")
            out = os.open(self.root / f"{b['sequence']:06d}.json", os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o400)
            try:
                os.write(out, canonical_bytes(b))
                os.fsync(out)
            finally:
                os.close(out)
            self.previous, self.sequence = b["receipt_hash"], b["sequence"]
            return b
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

def payload(*, run_id: str, lock_digest: str, fixture_digest: str, snapshot_digest: str, outcome: str, reason: str, resources: dict[str, int], binding: dict[str, Any] | None = None, fixture_record_digest: str | None = None, fixture_id: str = "opaque-fixture", fixture_selection_id: str = "opaque-selection", fixture_key: str = "opaque-fixture-key", selection_digest: str | None = None, arm_id: str = "graph_planner", arm_digest: str | None = None) -> dict[str, Any]:
    ledger = {"actions": 0, "risk": 0, "transactions": 0}
    ledger.update(resources)
    bound = dict(binding or {})
    return {"schema": "P4R0ReceiptPayloadV1", "run_id": run_id, "lock_digest": lock_digest, "fixture_digest": fixture_digest, "fixture_record_digest": fixture_record_digest or fixture_digest, "fixture_id": fixture_id, "fixture_selection_id": fixture_selection_id, "graph_snapshot_digest": snapshot_digest, "resource_ledger": ledger, "outcome": outcome, "reason": reason, "binding": bound}
