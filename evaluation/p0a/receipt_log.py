from __future__ import annotations

import builtins
import json
import os
from pathlib import Path
from typing import Any

from .canonical import ProtocolError, canonical_bytes, object_hash, sign, verify_signature


class ReceiptLog:
    def __init__(self, root: Path, *, manifest_hash: str, broker_image_digest: str,
                 input_digest: str, signer, writer_public_key, now_ms, run_paths=None):
        """Create an evaluator-owned receipt writer.

        P0 callers pass ``run_paths`` and may only write the derived receipt
        directory.  The optional argument preserves legacy fixture readers but
        is not a substitute for the isolated entrypoint's ownership checks.
        """
        self.root = Path(root)
        if run_paths is not None and self.root != Path(run_paths.receipts_root):
            raise ProtocolError("receipt log run path mismatch")
        self.run_paths = run_paths
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "receipts.ndjson"
        self.head_path = self.root / "head.json"
        self.manifest_hash = manifest_hash
        self.broker_image_digest = broker_image_digest
        self.input_digest = input_digest
        self.signer = signer
        self.writer_public_key = writer_public_key
        # Trusted setup captures receipt-writer primitives before evaluation-mode
        # defense-in-depth interception is activated.
        self._open = builtins.open
        self._fsync = os.fsync
        self._replace = os.replace
        self.now_ms = now_ms
        self.records: list[dict[str, Any]] = []
        self.sequence, self.previous = self.validate()

    @property
    def last_receipt(self) -> dict[str, Any] | None:
        return self.records[-1] if self.records else None

    def validate(self) -> tuple[int, str | None]:
        previous = None
        sequence = 0
        records: list[dict[str, Any]] = []
        try:
            with self._open(self.path, "rb") as handle:
                lines = handle.read().splitlines()
        except FileNotFoundError:
            lines = []
        for line in lines:
            receipt = json.loads(line)
            if receipt.get("receipt_sequence") != sequence + 1:
                raise ProtocolError("receipt sequence gap")
            if receipt.get("previous_receipt_hash") != previous:
                raise ProtocolError("receipt predecessor mismatch")
            if receipt.get("receipt_hash") != object_hash(receipt, "receipt_hash", "writer_signature"):
                raise ProtocolError("receipt hash mismatch")
            signed_receipt = dict(receipt)
            signed_receipt["signature"] = signed_receipt.pop("writer_signature", None)
            verify_signature(signed_receipt, self.writer_public_key, "receipt_hash")
            if receipt.get("schema") not in {"ActionReceiptV1", "ActionReceiptV2", "ActionReceiptV3"}:
                raise ProtocolError("receipt schema")
            if receipt.get("schema") in {"ActionReceiptV2", "ActionReceiptV3"} and not all(
                    name in receipt for name in (
                        "graph_proposal_id", "graph_proposal_digest", "causal_parent_receipt_hash",
                        "request_id", "nonce_digest", "request_sequence")):
                raise ProtocolError("graph receipt fields")
            if receipt.get("schema") == "ActionReceiptV3" and not all(
                    name in receipt for name in ("native_export_digest", "native_attestation_digest")):
                raise ProtocolError("native graph receipt fields")
            sequence += 1
            previous = receipt["receipt_hash"]
            records.append(receipt)
        try:
            with self._open(self.head_path, "rb") as handle:
                head = json.loads(handle.read())
        except FileNotFoundError:
            head = None
        expected = {"sequence": sequence, "head": previous}
        if records and head is None:
            raise ProtocolError("receipt head missing")
        if head is not None and head != expected:
            raise ProtocolError("receipt head mismatch")
        self.records = records
        return sequence, previous

    def append(self, *, run_id: str, outcome: str, reason_code: str | None,
               request_hash: str | None = None, grant_hash: str | None = None,
               method: str | None = None, normalized_args_hash: str | None = None,
               result_blob_hash: str | None = None, request_id: str | None = None,
               nonce_digest: str | None = None, grant_id: str | None = None,
               request_sequence: int | None = None,
               graph_proposal_id: str | None = None, graph_proposal_digest: str | None = None,
               causal_parent_receipt_hash: str | None = None,
               native_export_digest: str | None = None, native_attestation_digest: str | None = None) -> dict[str, Any]:
        # Every action acknowledgement revalidates the durable chain.  A
        # modified, forked, or partially published chain is terminal rather
        # than an opportunity to append around the mismatch.
        if self.run_paths is not None and (run_id != self.run_paths.run_id or
                                           self.manifest_hash != self.run_paths.verified_manifest_hash):
            raise ProtocolError("receipt log run binding mismatch")
        sequence, previous = self.validate()
        if (sequence, previous) != (self.sequence, self.previous):
            raise ProtocolError("receipt chain changed")
        graph = graph_proposal_id is not None or graph_proposal_digest is not None
        if graph and (graph_proposal_id is None or graph_proposal_digest is None):
            raise ProtocolError("incomplete graph receipt")
        if native_export_digest is not None and not graph:
            raise ProtocolError("native export without graph receipt")
        if native_attestation_digest is not None and native_export_digest is None:
            raise ProtocolError("native attestation without export")
        receipt = {
            "schema": "ActionReceiptV3" if native_export_digest is not None else ("ActionReceiptV2" if graph else "ActionReceiptV1"), "run_id": run_id,
            "receipt_sequence": self.sequence + 1, "timestamp_unix_ms": self.now_ms(),
            "outcome": outcome, "reason_code": reason_code,
            "request_hash": request_hash, "grant_hash": grant_hash, "method": method,
            "normalized_args_hash": normalized_args_hash, "manifest_hash": self.manifest_hash,
            "broker_image_digest": self.broker_image_digest,
            "sealed_input_snapshot_digest": self.input_digest,
            "usage": {"wall_ms": 0, "cpu_ms": 0, "memory_bytes": 0, "writes": 0,
                      "network_bytes": 0}, "result_blob_hash": result_blob_hash,
            "previous_receipt_hash": self.previous,
        }
        if graph:
            receipt.update({
                "graph_proposal_id": graph_proposal_id,
                "graph_proposal_digest": graph_proposal_digest,
                "causal_parent_receipt_hash": causal_parent_receipt_hash,
                "request_id": request_id,
                "nonce_digest": nonce_digest,
                "grant_id": grant_id,
                "request_sequence": request_sequence,
                "native_export_digest": native_export_digest,
                "native_attestation_digest": native_attestation_digest,
            })
        receipt["receipt_hash"] = object_hash(receipt, "receipt_hash", "writer_signature")
        receipt["writer_signature"] = sign(receipt, self.signer, "receipt_hash")
        line = canonical_bytes(receipt) + b"\n"
        with self._open(self.path, "ab") as handle:
            handle.write(line)
            handle.flush()
            self._fsync(handle.fileno())
        head = {"sequence": receipt["receipt_sequence"], "head": receipt["receipt_hash"]}
        temporary = self.head_path.with_suffix(".tmp")
        with self._open(temporary, "wb") as handle:
            handle.write(canonical_bytes(head))
            handle.flush()
            self._fsync(handle.fileno())
        self._replace(temporary, self.head_path)
        self.sequence, self.previous = head["sequence"], head["head"]
        self.records.append(receipt)
        return receipt
