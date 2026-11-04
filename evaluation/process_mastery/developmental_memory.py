"""Charged finite storage for P21 episode and chunk evidence.

This module implements byte accounting and retrieval mechanics only. It does
not select evidence, infer a process, or choose curriculum tasks.
"""
from __future__ import annotations

from collections import OrderedDict
import hashlib
import json
import zlib


class ChargedMemory:
    """Deterministic byte-bounded store; evicted payloads cannot be retrieved."""

    def __init__(self, *, capacity_bytes: int, overhead_bytes: int = 32):
        if capacity_bytes <= 0 or overhead_bytes < 0:
            raise ValueError("memory capacity must be positive and overhead nonnegative")
        self.capacity_bytes = int(capacity_bytes)
        self.overhead_bytes = int(overhead_bytes)
        self._records: OrderedDict[str, tuple[bytes, int, bool, str]] = OrderedDict()
        self.evictions: list[dict] = []
        self.retrieval_bytes = 0
        self.decode_work_bytes = 0

    @staticmethod
    def _encode(record: dict) -> str:
        return json.dumps(record, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)

    def used_bytes(self) -> int:
        return sum(size for _, size, _, _ in self._records.values())

    def put(self, key: str, record: dict, *, protected: bool = False) -> dict:
        if not key or key in self._records:
            raise ValueError("memory keys must be nonempty and unique")
        payload = self._encode(record)
        encoded_bytes = len(payload.encode("utf-8"))
        charged = encoded_bytes + self.overhead_bytes + len(key.encode("utf-8"))
        if charged > self.capacity_bytes:
            return {"status": "rejected_capacity", "key": key,
                    "charged_bytes": charged, "used_bytes": self.used_bytes()}
        removed = []
        while self.used_bytes() + charged > self.capacity_bytes:
            victim = next((candidate for candidate, (_, _, keep, _)
                           in self._records.items() if not keep), None)
            if victim is None:
                return {"status": "rejected_protected_capacity", "key": key,
                        "charged_bytes": charged, "used_bytes": self.used_bytes()}
            _, _, victim_protected, _ = self._records.pop(victim)
            assert not victim_protected
            removed.append(victim)
            self.evictions.append({"key": victim, "reason": "capacity"})
        self._records[key] = (payload.encode("utf-8"), charged, bool(protected), "json")
        return {"status": "stored", "key": key, "charged_bytes": charged,
                "used_bytes": self.used_bytes(), "evicted": removed,
                "protected": bool(protected)}

    def put_verified_chunk(self, key: str, source_keys: list[str]) -> dict:
        """Losslessly replace resident source records with a charged decoder chunk."""
        if not source_keys or len(set(source_keys)) != len(source_keys) or key in self._records:
            raise ValueError("chunk requires unique resident sources and a fresh key")
        if any(source not in self._records for source in source_keys):
            return {"status": "source_unavailable", "key": key}
        decoded = []
        source_bytes = 0
        protected = False
        for source in source_keys:
            raw, charged, keep, encoding = self._records[source]
            text = zlib.decompress(raw).decode("utf-8") if encoding == "zlib-json" else raw.decode("utf-8")
            decoded.append(json.loads(text))
            source_bytes += charged
            protected = protected or keep
        chunk_text = self._encode({"source_keys": source_keys, "records": decoded,
                                   "lossless": True})
        packed = zlib.compress(chunk_text.encode("utf-8"), level=9)
        charged = (len(packed) + self.overhead_bytes + len(key.encode("utf-8"))
                   + 24 + sum(len(source.encode("utf-8")) for source in source_keys))
        if charged >= source_bytes:
            return {"status": "not_cost_effective", "key": key,
                    "source_bytes": source_bytes, "chunk_bytes": charged}
        remaining = self.used_bytes() - source_bytes
        if remaining + charged > self.capacity_bytes:
            return {"status": "rejected_protected_capacity", "key": key,
                    "source_bytes": source_bytes, "chunk_bytes": charged}
        for source in source_keys:
            del self._records[source]
        self._records[key] = (packed, charged, protected, "zlib-json")
        return {"status": "stored", "key": key, "charged_bytes": charged,
                "source_bytes": source_bytes, "used_bytes": self.used_bytes(),
                "protected": protected, "source_keys": list(source_keys)}

    def retrieve(self, key: str) -> tuple[dict | None, dict]:
        item = self._records.get(key)
        if item is None:
            return None, {"status": "unavailable", "key": key, "work_bytes": 0}
        payload, charged, protected, encoding = item
        self._records.move_to_end(key)
        work = len(payload)
        self.retrieval_bytes += work
        if encoding == "zlib-json":
            self.decode_work_bytes += len(payload)
            decoded = json.loads(zlib.decompress(payload).decode("utf-8"))
        else:
            decoded = json.loads(payload.decode("utf-8"))
        return decoded, {"status": "retrieved", "key": key, "work_bytes": work,
                         "charged_bytes": charged, "protected": protected,
                         "encoding": encoding,
                         "payload_sha256": hashlib.sha256(payload).hexdigest()}

    def contains(self, key: str) -> bool:
        return key in self._records

    def audit(self) -> dict:
        return {"capacity_bytes": self.capacity_bytes, "used_bytes": self.used_bytes(),
                "record_count": len(self._records), "evictions": list(self.evictions),
                "retrieval_bytes": self.retrieval_bytes,
                "decode_work_bytes": self.decode_work_bytes,
                "keys": list(self._records)}
