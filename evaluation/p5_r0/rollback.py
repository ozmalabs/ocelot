"""Exact evaluator snapshot/restore and signed rollback evidence."""
from __future__ import annotations
from copy import deepcopy
from typing import Any
from evaluation.p0a.canonical import canonical_bytes
from .protocol import P5R0Error, digest

class Snapshot:
    def __init__(self, state: dict[str, Any]):
        self._bytes = canonical_bytes(deepcopy(state))
        self.digest = digest(self._bytes)
    def restore(self, state: dict[str, Any]) -> str:
        from evaluation.p0a.canonical import parse_canonical
        restored = parse_canonical(self._bytes)
        state.clear(); state.update(restored)
        if canonical_bytes(state) != self._bytes or digest(self._bytes) != self.digest: raise P5R0Error("rollback mismatch")
        return self.digest

def rollback_receipt(*, run_id: str, pre_snapshot: str, restored_snapshot: str, chain_digest: str, outcome: str = "restored") -> dict[str, Any]:
    if pre_snapshot != restored_snapshot: outcome = "rollback_impasse"
    return {"schema": "P5R0RollbackReceiptV2", "run_id": run_id, "pre_snapshot_digest": pre_snapshot, "restored_snapshot_digest": restored_snapshot, "receipt_chain_digest": chain_digest, "outcome": outcome, "exact": outcome == "restored", "rollback_digest": digest({"run_id": run_id, "pre": pre_snapshot, "restored": restored_snapshot, "chain": chain_digest})}
