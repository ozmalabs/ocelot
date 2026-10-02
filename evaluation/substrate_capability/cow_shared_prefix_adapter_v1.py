#!/usr/bin/env python3
"""Source-locked synthetic shared-prefix consumer compatibility probe."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
BACKENDS = ("shared_graph_pages", "full_copy")
SOURCES = (
    "evaluation/substrate_capability/cow_shared_prefix_adapter_v1.py",
    "scripts/analyze_cow_shared_prefix_adapter_v1.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/persist.rs",
)
RAW = ROOT / "evaluation/reports/cow_shared_prefix_adapter_v1.json"
BLOCK_BYTES = 1024
PREFIX_BLOCKS = 8
CONTINUATION_BLOCKS = 4


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def smaps() -> dict[str, int]:
    values = {}
    for line in Path("/proc/self/smaps_rollup").read_text(encoding="ascii").splitlines():
        name, sep, tail = line.partition(":")
        if sep and name in {"Rss", "Pss", "Private_Clean", "Private_Dirty", "Shared_Clean", "Shared_Dirty", "Swap"}:
            values[name] = int(tail.strip().split()[0]) * 1024
    needed = {"Rss", "Pss", "Private_Clean", "Private_Dirty", "Shared_Clean", "Shared_Dirty"}
    if needed - values.keys():
        raise RuntimeError(f"smaps_rollup missing {sorted(needed - values.keys())}")
    return values


def digest(blocks: list[dict]) -> str:
    payload = json.dumps(blocks, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


class PrefixStore:
    """Adapter: prefix ownership and request handles over snapshot/fork."""

    def __init__(self, snapshot, prefix_ids: list[int], base_revision: tuple[int, ...]):
        self.snapshot = snapshot
        self.prefix_ids = list(prefix_ids)
        self.base_revision = tuple(base_revision)
        self.requests: dict[str, dict] = {}
        self.next_request_id = 1

    @classmethod
    def publish(cls, primary, backend: str):
        snapshot = primary.snapshot() if backend == "public_default" else primary._snapshot_with_backend(backend)
        return cls(snapshot, primary.nodes("PrefixBlock"), tuple(snapshot.source_revision))

    def fork(self, expected_revision: tuple[int, ...]) -> str:
        if tuple(expected_revision) != self.base_revision:
            raise ValueError("prefix revision mismatch")
        request_id = f"request-{self.next_request_id}"
        self.next_request_id += 1
        self.requests[request_id] = {"branch": self.snapshot.fork(), "continuation_ids": [], "cancelled": False}
        return request_id

    def append(self, request_id: str, payload: str) -> int:
        request = self.requests[request_id]
        if request["cancelled"]:
            raise RuntimeError("request is cancelled")
        index = len(request["continuation_ids"])
        nid = request["branch"].add_node("ContinuationBlock", {
            "request_id": request_id, "ordinal": index, "payload": payload,
        })
        request["continuation_ids"].append(nid)
        return nid

    def read(self, request_id: str) -> list[dict]:
        request = self.requests[request_id]
        branch = request["branch"]
        ids = self.prefix_ids + request["continuation_ids"]
        return [branch.node(nid) for nid in ids]

    def cancel(self, request_id: str) -> None:
        request = self.requests.pop(request_id)
        request["cancelled"] = True
        del request

    def active_request_blocks(self) -> int:
        return sum(len(row["continuation_ids"]) for row in self.requests.values())

    def receipt(self) -> dict:
        return {"snapshot_id": self.snapshot.id, "base_revision": list(self.base_revision),
                "prefix_block_ids": self.prefix_ids,
                "requests": {key: {"continuation_block_ids": row["continuation_ids"],
                                   "cancelled": row["cancelled"]}
                             for key, row in sorted(self.requests.items())}}


def fixture(size: int):
    import substrate_rs as srs
    primary = srs.Substrate()
    for i in range(PREFIX_BLOCKS):
        payload = (f"prefix-{i:02d}:" + "p" * BLOCK_BYTES)[:BLOCK_BYTES]
        primary.add_node("PrefixBlock", {"ordinal": i, "payload": payload})
    previous = None
    for nid in primary.nodes("PrefixBlock"):
        if previous is not None:
            primary.add_edge_unchecked(previous, "prefix_next", nid)
        previous = nid
    for i in range(size):
        primary.add_node("Background", {"ordinal": i})
    return primary


def worker(size: int, backend: str, repetition: int) -> dict:
    timings = {}
    primary = fixture(size)
    prefix_before = [primary.node(nid) for nid in primary.nodes("PrefixBlock")]
    started = time.perf_counter_ns()
    store = PrefixStore.publish(primary, backend)
    timings["publish_ms"] = (time.perf_counter_ns() - started) / 1_000_000
    captured = store.base_revision
    gc.collect()
    memory = {"primary_baseline": smaps(), "snapshot_live": smaps()}

    # Deliberately change the primary revision after publication. The captured
    # snapshot remains valid, while a caller's newer revision token is refused.
    primary.add_node("PostPublicationMarker", {"repetition": repetition})
    newer = tuple(primary._inner.experiment_graph_rule_revision())
    stale_refused = False
    try:
        store.fork(newer)
    except ValueError:
        stale_refused = True
    stale_rejection_atomic = len(store.requests) == 0
    started = time.perf_counter_ns()
    req_a = store.fork(captured)
    req_b = store.fork(captured)
    timings["fork_two_requests_ms"] = (time.perf_counter_ns() - started) / 1_000_000
    started = time.perf_counter_ns()
    for i in range(CONTINUATION_BLOCKS):
        store.append(req_a, (f"a-{i}:" + "a" * BLOCK_BYTES)[:BLOCK_BYTES])
        store.append(req_b, (f"b-{i}:" + "b" * BLOCK_BYTES)[:BLOCK_BYTES])
    timings["write_eight_continuation_blocks_ms"] = (time.perf_counter_ns() - started) / 1_000_000
    started = time.perf_counter_ns()
    seq_a = store.read(req_a)
    seq_b = store.read(req_b)
    timings["read_two_sequences_ms"] = (time.perf_counter_ns() - started) / 1_000_000
    memory["two_requests_live"] = smaps()
    prefix_a = seq_a[:PREFIX_BLOCKS]
    prefix_b = seq_b[:PREFIX_BLOCKS]
    sibling_isolation = (seq_a[PREFIX_BLOCKS:] != seq_b[PREFIX_BLOCKS:]
                         and all(row["type"] == "PrefixBlock" for row in prefix_a + prefix_b)
                         and [row["attrs"] for row in prefix_a] == [row["attrs"] for row in prefix_b]
                         and len(primary.nodes("ContinuationBlock")) == 0)
    read_a_digest, read_b_digest = digest(seq_a), digest(seq_b)
    cancelled_ids = list(store.requests[req_a]["continuation_ids"])
    started = time.perf_counter_ns()
    store.cancel(req_a)
    timings["cancel_one_request_ms"] = (time.perf_counter_ns() - started) / 1_000_000
    gc.collect()
    memory["one_request_cancelled"] = smaps()
    sibling_survives_cancel = digest(store.read(req_b)) == read_b_digest
    started = time.perf_counter_ns()
    req_c = store.fork(captured)
    seq_c = store.read(req_c)
    timings["fork_and_read_after_cancel_ms"] = (time.perf_counter_ns() - started) / 1_000_000
    later_fork_is_clean = (len(seq_c) == PREFIX_BLOCKS
                           and [row["attrs"] for row in seq_c] == [row["attrs"] for row in prefix_before])
    started = time.perf_counter_ns()
    store.cancel(req_b)
    store.cancel(req_c)
    timings["cancel_remaining_requests_ms"] = (time.perf_counter_ns() - started) / 1_000_000
    gc.collect()
    memory["all_requests_cancelled"] = smaps()
    no_active_requests = len(store.requests) == 0 and store.active_request_blocks() == 0

    # A later fork after cancellation still sees the exact published prefix.
    started = time.perf_counter_ns()
    req_d = store.fork(captured)
    seq_d = store.read(req_d)
    timings["fork_and_read_reused_base_ms"] = (time.perf_counter_ns() - started) / 1_000_000
    reusable_after_cancel = len(seq_d) == PREFIX_BLOCKS and [row["attrs"] for row in seq_d] == [row["attrs"] for row in prefix_before]
    started = time.perf_counter_ns()
    store.cancel(req_d)
    snapshot_id = store.snapshot.id
    del store
    gc.collect()
    timings["cancel_and_release_snapshot_ms"] = (time.perf_counter_ns() - started) / 1_000_000
    memory["snapshot_released"] = smaps()
    del primary
    gc.collect()
    memory["primary_released"] = smaps()
    return {
        "schema": "CowSharedPrefixAdapterWorkerV1", "size_background_nodes": size,
        "backend": backend, "repetition": repetition, "pid": os.getpid(),
        "snapshot_id": snapshot_id, "base_revision": list(captured),
        "prefix_before_digest": digest(prefix_before), "request_a_digest": read_a_digest,
        "request_b_digest": read_b_digest, "cancelled_request_block_ids": [x.value for x in cancelled_ids],
        "stale_revision_refused": stale_refused, "stale_rejection_atomic": stale_rejection_atomic,
        "sibling_isolation": sibling_isolation,
        "sibling_survives_cancel": sibling_survives_cancel,
        "later_fork_clean": later_fork_is_clean, "reusable_after_cancel": reusable_after_cancel,
        "no_active_requests_after_cancel": no_active_requests,
        "logical_active_request_blocks_after_cancel": 0,
        "timings_ms": timings,
        "memory_samples_bytes": memory,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--size", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--backend", choices=("public_default", "full_copy"), help=argparse.SUPPRESS)
    parser.add_argument("--repetition", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--out", type=Path, default=RAW)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.size, args.backend, args.repetition), sort_keys=True))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    sizes, repeats, warmups = (0, 1000, 10000), 5, 1
    rng = random.Random(20261001)
    rows, schedule = [], []
    exe = Path(__file__).resolve()
    for size in sizes:
        for rep in range(warmups + repeats):
            order = ["public_default", "full_copy"]
            rng.shuffle(order)
            for backend in order:
                done = subprocess.run([sys.executable, str(exe), "--worker", "--size", str(size),
                                       "--backend", backend, "--repetition", str(rep)],
                                      cwd=ROOT, text=True, capture_output=True)
                if done.returncode:
                    raise RuntimeError(f"worker failed size={size} backend={backend} rep={rep}: {done.stderr[-4000:]}")
                row = json.loads(done.stdout)
                gates = ("stale_revision_refused", "stale_rejection_atomic", "sibling_isolation", "sibling_survives_cancel",
                         "later_fork_clean", "reusable_after_cancel", "no_active_requests_after_cancel")
                if not all(row[name] for name in gates):
                    raise RuntimeError(f"worker semantic gate failed: {size=} {backend=} {rep=}: {row}")
                schedule.append({"size": size, "repetition": rep, "backend": backend})
                if rep >= warmups:
                    rows.append(row)
            print(f"[{len(schedule)}/{len(sizes) * (warmups + repeats) * 2}] size={size} repetition={rep}", flush=True)
    import substrate_rs as srs
    binary = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "CowSharedPrefixAdapterCaptureV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "runner": {"path": str(exe), "sha256": sha(exe)},
        "binary": {"path": str(binary), "sha256": sha(binary)},
        "source_sha256": {path: sha(ROOT / path) for path in SOURCES},
        "protocol": {"background_sizes": list(sizes), "repeats": repeats, "warmups": warmups,
                     "backends": ["public_default", "full_copy"], "backend_order": "randomized per size/repetition",
                     "prefix_blocks": PREFIX_BLOCKS, "continuation_blocks_per_request": CONTINUATION_BLOCKS,
                     "synthetic_block_payload_bytes": BLOCK_BYTES,
                     "memory": "Linux smaps_rollup stage samples; descriptive process-level accounting"},
        "schedule": schedule, "rows": rows,
    }
    dest = args.out if args.out.is_absolute() else ROOT / args.out
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest)
    subprocess.run([sys.executable, str(ROOT / "scripts/analyze_cow_shared_prefix_adapter_v1.py"), str(dest)],
                   cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
