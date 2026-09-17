"""Signed launch-failure evidence, scoped to a fresh attempt or verified run."""
from __future__ import annotations

import builtins
import os
from pathlib import Path
from typing import Any

from .canonical import ProtocolError, canonical_bytes, parse_canonical, sign, verify_signature
from .run_paths import LaunchAttemptPaths, RunPaths

_CONTEXT_HASH_FIELDS = frozenset({"manifest_candidate_hash", "expected_digests_hash", "native_graph_export_hash", "receipt_log_configuration_hash"})
_FIELDS = frozenset({"schema", "launch_attempt_id", "run_id", "verified_manifest_hash", "observed_receipt_log_manifest_hash", "reason_code", "context_hashes", "timestamp_unix_ms", "signer_key_id", "signature"})


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == 71


class LaunchFailureRecord:
    def __init__(self, root: Path | LaunchAttemptPaths | RunPaths, *, signer, signer_public_key, signer_key_id: str,
                 now_ms, launch_attempt_id: str | None = None):
        if isinstance(root, LaunchAttemptPaths):
            launch_attempt_id, root = root.launch_attempt_id, root.root
        elif isinstance(root, RunPaths):
            root = root.terminal_root
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "launch-failure.json"
        self.launch_attempt_id = launch_attempt_id
        self.signer, self.signer_public_key, self.signer_key_id, self.now_ms = signer, signer_public_key, signer_key_id, now_ms
        self._open, self._replace = builtins.open, os.replace

    @classmethod
    def for_attempt_paths(cls, paths: LaunchAttemptPaths, receipt_log, *, now_ms):
        return cls(paths, signer=receipt_log.signer, signer_public_key=receipt_log.writer_public_key,
                   signer_key_id=getattr(receipt_log, "writer_key_id", "receipt-log-writer"), now_ms=now_ms)

    @classmethod
    def for_receipt_writer(cls, receipt_log, *, now_ms):
        # Compatibility only; P0 launcher creates an evaluator-owned attempt path.
        return cls(receipt_log.root / "control-plane", signer=receipt_log.signer,
                   signer_public_key=receipt_log.writer_public_key,
                   signer_key_id=getattr(receipt_log, "writer_key_id", "receipt-log-writer"), now_ms=now_ms)

    def read(self) -> dict[str, Any] | None:
        try:
            with self._open(self.path, "rb") as handle: record = parse_canonical(handle.read())
        except FileNotFoundError: return None
        if set(record) != _FIELDS or record.get("schema") != "EvaluationLaunchFailureV2" or record.get("signer_key_id") != self.signer_key_id:
            raise ProtocolError("launch failure record schema")
        if (not isinstance(record.get("launch_attempt_id"), str) or
                record.get("run_id") is not None and not isinstance(record.get("run_id"), str) or
                record.get("verified_manifest_hash") is not None and not _is_digest(record.get("verified_manifest_hash")) or
                record.get("observed_receipt_log_manifest_hash") is not None and not _is_digest(record.get("observed_receipt_log_manifest_hash")) or
                not isinstance(record.get("reason_code"), str) or type(record.get("timestamp_unix_ms")) is not int or
                not isinstance(record.get("context_hashes"), dict) or set(record["context_hashes"]) != _CONTEXT_HASH_FIELDS or
                any(not _is_digest(value) for value in record["context_hashes"].values())):
            raise ProtocolError("launch failure record fields")
        if self.launch_attempt_id is not None and record["launch_attempt_id"] != self.launch_attempt_id:
            raise ProtocolError("launch attempt binding")
        verify_signature(record, self.signer_public_key); return record

    def record(self, *, run_id: str | None, verified_manifest_hash: str | None,
               observed_receipt_log_manifest_hash: str | None, reason_code: str, context_hashes: dict[str, str]) -> dict[str, Any]:
        existing = self.read()
        if existing is not None: return existing
        attempt = self.launch_attempt_id or "legacy-attempt"
        record = {"schema": "EvaluationLaunchFailureV2", "launch_attempt_id": attempt, "run_id": run_id,
                  "verified_manifest_hash": verified_manifest_hash,
                  "observed_receipt_log_manifest_hash": observed_receipt_log_manifest_hash,
                  "reason_code": reason_code, "context_hashes": context_hashes,
                  "timestamp_unix_ms": self.now_ms(), "signer_key_id": self.signer_key_id}
        record["signature"] = sign(record, self.signer)
        temporary = self.path.with_suffix(".tmp")
        try:
            with self._open(temporary, "xb") as handle:
                handle.write(canonical_bytes(record)); handle.flush(); os.fsync(handle.fileno())
            self._replace(temporary, self.path)
        except FileExistsError: pass
        return self.read() or (_ for _ in ()).throw(ProtocolError("launch failure record unavailable"))
