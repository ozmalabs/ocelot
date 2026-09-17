"""Run-bound signed terminal evidence for evaluator-owned P0 runtime failures."""
from __future__ import annotations

import builtins
import os
from pathlib import Path
from typing import Any

from .canonical import ProtocolError, canonical_bytes, parse_canonical, sign, verify_signature
from .run_paths import RunPaths

_FIELDS = frozenset({"schema", "run_id", "verified_manifest_hash", "last_valid_receipt_sequence",
                     "last_valid_receipt_hash", "last_valid_head_hash", "reason_code", "error",
                     "timestamp_unix_ms", "signer_key_id", "signature"})


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == 71


class RuntimeFailureRecord:
    """Atomically publish one signed runtime failure for one run binding."""
    def __init__(self, root: Path | RunPaths, *, signer, signer_public_key, signer_key_id: str, now_ms,
                 run_id: str | None = None, verified_manifest_hash: str | None = None):
        if not signer_key_id:
            raise ValueError("runtime failure signer key id")
        if isinstance(root, RunPaths):
            run_id, verified_manifest_hash, root = root.run_id, root.verified_manifest_hash, root.terminal_root
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "runtime-failure.json"
        self.run_id = run_id
        self.verified_manifest_hash = verified_manifest_hash
        self.signer, self.signer_public_key, self.signer_key_id, self.now_ms = signer, signer_public_key, signer_key_id, now_ms
        self._open, self._fsync, self._replace = builtins.open, os.fsync, os.replace

    @classmethod
    def for_run_paths(cls, paths: RunPaths, receipt_log, *, now_ms):
        return cls(paths, signer=receipt_log.signer, signer_public_key=receipt_log.writer_public_key,
                   signer_key_id=getattr(receipt_log, "writer_key_id", "receipt-log-writer"), now_ms=now_ms)

    @classmethod
    def for_receipt_writer(cls, receipt_log, *, now_ms):
        # Compatibility constructor. New P0 callers must use for_run_paths.
        return cls(receipt_log.root / "control-plane", signer=receipt_log.signer,
                   signer_public_key=receipt_log.writer_public_key,
                   signer_key_id=getattr(receipt_log, "writer_key_id", "receipt-log-writer"), now_ms=now_ms)

    def read(self) -> dict[str, Any] | None:
        try:
            with self._open(self.path, "rb") as handle:
                record = parse_canonical(handle.read())
        except FileNotFoundError:
            return None
        if set(record) != _FIELDS or record.get("schema") != "EvaluationRuntimeFailureV1" or record.get("signer_key_id") != self.signer_key_id:
            raise ProtocolError("runtime failure record schema")
        if (not isinstance(record.get("run_id"), str) or not _is_digest(record.get("verified_manifest_hash")) or
                type(record.get("last_valid_receipt_sequence")) is not int or record["last_valid_receipt_sequence"] < 0 or
                record.get("last_valid_receipt_hash") is not None and not _is_digest(record.get("last_valid_receipt_hash")) or
                record.get("last_valid_head_hash") != record.get("last_valid_receipt_hash") or
                not isinstance(record.get("reason_code"), str) or not isinstance(record.get("error"), str) or
                type(record.get("timestamp_unix_ms")) is not int):
            raise ProtocolError("runtime failure record fields")
        if self.run_id is not None and (record["run_id"], record["verified_manifest_hash"]) != (self.run_id, self.verified_manifest_hash):
            raise ProtocolError("runtime failure record binding")
        verify_signature(record, self.signer_public_key)
        return record

    def record(self, *, run_id: str, verified_manifest_hash: str, last_valid_receipt_sequence: int,
               last_valid_receipt_hash: str | None, reason_code: str, error: Exception | str) -> dict[str, Any]:
        if self.run_id is not None and (run_id, verified_manifest_hash) != (self.run_id, self.verified_manifest_hash):
            raise ProtocolError("runtime failure binding mismatch")
        existing = self.read()
        if existing is not None:
            return existing
        record = {"schema": "EvaluationRuntimeFailureV1", "run_id": run_id,
                  "verified_manifest_hash": verified_manifest_hash,
                  "last_valid_receipt_sequence": last_valid_receipt_sequence,
                  "last_valid_receipt_hash": last_valid_receipt_hash,
                  "last_valid_head_hash": last_valid_receipt_hash, "reason_code": reason_code,
                  "error": str(error), "timestamp_unix_ms": self.now_ms(), "signer_key_id": self.signer_key_id}
        record["signature"] = sign(record, self.signer)
        temporary = self.path.with_suffix(".tmp")
        try:
            with self._open(temporary, "xb") as handle:
                handle.write(canonical_bytes(record)); handle.flush(); self._fsync(handle.fileno())
            self._replace(temporary, self.path)
        except FileExistsError:
            pass
        return self.read() or (_ for _ in ()).throw(ProtocolError("runtime failure record unavailable"))
