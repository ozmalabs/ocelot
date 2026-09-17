"""P5-R0 signed append-only evidence receipts."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from evaluation.p0a.canonical import b64encode, canonical_bytes, object_hash, sign, parse_canonical, verify_signature
from .protocol import P5R0Error, TERMINAL_OUTCOMES, digest


class ReceiptChain:
    """An append-only chain with an independently reloadable V3 verifier.

    The default remains the historical V2 format.  V3 callers must opt in so
    that an old receipt directory can never be silently upgraded or rewritten.
    """
    def __init__(self, root: Path, signer: Any | None = None, authority_id: str = "p5-r0-evaluator", key_id: str = "p5-r0-receipt", *, public_key: Any | None = None, protocol: str = "V2", reload: bool = False):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.signer = signer; self.authority_id = authority_id; self.key_id = key_id
        self.protocol = protocol
        if protocol not in {"V2", "V3"}: raise P5R0Error("receipt protocol")
        self._public_key = public_key or (signer.public_key() if signer is not None else None)
        if self._public_key is None: raise P5R0Error("receipt public key")
        if any(self.root.glob("*.json")) and not reload: raise P5R0Error("receipt root already contains a run")
        self.records: list[dict[str, Any]] = []
        if reload: self.records = self.verify_chain()

    @classmethod
    def reload(cls, root: Path, public_key: Any, *, authority_id: str, key_id: str, protocol: str = "V3") -> "ReceiptChain":
        return cls(root, None, authority_id, key_id, public_key=public_key, protocol=protocol, reload=True)

    @property
    def public_key(self) -> Any:
        return self._public_key

    @property
    def public_key_digest(self) -> str:
        return digest(b64encode(self.public_key.public_bytes_raw()))

    @property
    def root_digest(self) -> str:
        return digest(str(self.root.resolve()))

    def append(self, *, run_id: str, kind: str, outcome: str, binding: dict[str, Any], resources: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.signer is None: raise P5R0Error("read-only receipt chain")
        if self.protocol == "V3" and not self.records and kind not in {"preregistered", "impasse"}: raise P5R0Error("V3 preregistration must be first")
        if outcome not in TERMINAL_OUTCOMES and outcome not in {"released", "verified", "restored"}: raise P5R0Error("receipt outcome")
        bound = dict(binding)
        if self.protocol == "V3" and not self.records:
            bound.setdefault("authority_id", self.authority_id); bound.setdefault("key_id", self.key_id); bound.setdefault("public_key_digest", self.public_key_digest)
        if self.protocol == "V3" and self.records:
            bound.setdefault("preregistration_receipt_hash", self.records[0]["receipt_hash"])
        suffix = self.protocol
        payload = {"schema": f"P5R0ReceiptPayload{suffix}", "run_id": run_id, "kind": kind, "outcome": outcome, "binding": bound, "resources": dict(resources or {})}
        record = {"schema": f"P5R0Receipt{suffix}", "sequence": len(self.records) + 1, "previous_hash": self.records[-1]["receipt_hash"] if self.records else None, "payload": payload, "receipt_hash": "", "signature": ""}
        record["receipt_hash"] = object_hash(record, "receipt_hash", "signature"); record["signature"] = sign(record, self.signer, "receipt_hash")
        path = self.root / f"{record['sequence']:06d}.json"
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
            try:
                os.write(fd, canonical_bytes(record)); os.fsync(fd)
            finally: os.close(fd)
        except OSError as exc:
            raise P5R0Error("receipt persistence") from exc
        self.records.append(record); return record

    def verify_chain(self) -> list[dict[str, Any]]:
        previous = None; verified: list[dict[str, Any]] = []
        paths = sorted(self.root.glob("*.json"))
        expected_schema = "P5R0ReceiptV3" if self.protocol == "V3" else None
        for expected, path in enumerate(paths, 1):
            try: record = parse_canonical(path.read_bytes())
            except Exception as exc: raise P5R0Error("receipt canonical") from exc
            allowed = {"P5R0ReceiptV1", "P5R0ReceiptV2"} if expected_schema is None else {expected_schema}
            if set(record) != {"schema", "sequence", "previous_hash", "payload", "receipt_hash", "signature"} or record["schema"] not in allowed or record["sequence"] != expected or record["previous_hash"] != previous or record["receipt_hash"] != object_hash(record, "receipt_hash", "signature"):
                raise P5R0Error("receipt chain")
            if record["payload"].get("schema") != ("P5R0ReceiptPayloadV3" if expected_schema else record["payload"].get("schema")):
                raise P5R0Error("receipt payload")
            try: verify_signature(record, self.public_key, "receipt_hash")
            except Exception as exc: raise P5R0Error("receipt signature") from exc
            if record["schema"] == "P5R0ReceiptV3" and expected == 1:
                first_binding = record["payload"].get("binding", {})
                if first_binding.get("authority_id") != self.authority_id or first_binding.get("key_id") != self.key_id or first_binding.get("public_key_digest") != self.public_key_digest: raise P5R0Error("receipt authority binding")
            verified.append(record); previous = record["receipt_hash"]
        self.records = verified
        return verified

    @property
    def digest(self) -> str:
        return digest(self.records)

    @property
    def final_digest(self) -> str:
        return self.digest
