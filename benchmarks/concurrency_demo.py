"""Concurrency demo: master + workers + async runner over the Rust
substrate.

Demonstrates the ACT-R / Global Workspace shape end-to-end:

* The master owns a `substrate_rs.Substrate` and is the only writer.
* A `WorkerPool` runs CPU work in parallel — here, computing per-node
  scores for a batch of `Cell` nodes. Each worker returns an
  `apply(agent)` closure that writes the score back via `set_attr`.
* An `AsyncRunner` does an I/O-shaped task (a `sleep` standing in
  for a teacher call) and delivers a result the master commits.
* A `MemoryConsolidationRunner` periodically scans for unconsolidated
  nodes and writes a "consolidated" attr on the master's thread.

Run: PYTHONPATH=. python3 benchmarks/concurrency_demo.py
"""
from __future__ import annotations

import asyncio
import time

import substrate_rs as srs
from domains.concurrency import (
    AsyncRunner,
    ConcurrencyLayer,
    MemoryConsolidationRunner,
    WorkerPool,
)


def build_substrate(n_cells: int = 200) -> srs.Substrate:
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Cell", var="src"),
        edge_type="adj",
        tgt=srs.NodePattern(type="Cell", var="tgt"),
        where=None, weight=None, provenance="demo:adj",
    ))
    for i in range(n_cells):
        s.add_node("Cell", {"id": i, "raw_value": i * 1.5})
    return s


def cpu_score(payload):
    """Worker task. Doesn't touch the substrate — does pure compute,
    returns an apply(agent) closure that writes the result back."""
    cell_nid, raw = payload
    # Pretend this is real work — fib-like calculation per cell.
    score = 0.0
    x = raw
    for _ in range(2000):
        x = (x * 1.0001) % 100.0
        score += x
    def apply(substrate):
        substrate.set_attr(cell_nid, "score", score)
    return apply


async def io_fetch(payload):
    """Async task. Stands in for a network/file call. Returns an
    apply(agent) closure that records the fetched value."""
    await asyncio.sleep(0.05)
    def apply(substrate):
        substrate.set_attr(payload["nid"], "fetched", payload["value"])
    return apply


def make_consolidator():
    """The consolidator's job is to return an `apply(agent)` closure;
    THE CLOSURE does all the graph work on the master's thread. The
    consolidator itself runs on the async runner's thread and MUST NOT
    touch the substrate — `substrate_rs.Substrate` is unsendable and
    cross-thread access panics.

    This split — schedule on a background thread, apply on the master
    — is the whole reason ACT-R/Global-Workspace style architectures
    are biology-faithful: parallel timing, serial commit.
    """
    def consolidate():
        # No substrate access here. The trigger fires periodically;
        # the work is performed by the apply closure on master.
        def apply(substrate):
            targets = []
            for nid in substrate.nodes("Cell"):
                node = substrate.node(nid)
                if "score" in node["attrs"] and "consolidated" not in node["attrs"]:
                    targets.append(nid)
            if not targets:
                return
            for nid in targets:
                substrate.set_attr(nid, "consolidated", True)
            print(f"  [consolidate] tagged {len(targets)} cells")
        return apply
    return consolidate


def main():
    print("Building substrate (200 cells, 1 permissive Γ)…")
    s = build_substrate(n_cells=200)

    # N workers + M async runners.
    pool = WorkerPool(n_workers=4, name="cpu")
    runner = AsyncRunner(max_concurrent=8, name="io")
    layer = ConcurrencyLayer()
    layer.add_pool(pool)
    layer.add_runner(runner)

    # Background memory consolidation (CLS-shape).
    mcr = MemoryConsolidationRunner(
        runner=runner,
        consolidate_fn=make_consolidator(),
        period_s=0.10,
    )
    mcr.start()

    # Submit work to both surfaces.
    print("Submitting 200 CPU scoring tasks to the worker pool…")
    cells = s.nodes("Cell")
    for nid in cells:
        attrs = s.node(nid)["attrs"]
        pool.submit(cpu_score, payload=(nid, attrs["raw_value"]))

    print("Submitting 20 async I/O fetches…")
    for i, nid in enumerate(cells[:20]):
        runner.submit(io_fetch, payload={"nid": nid, "value": f"data_{i}"})

    # Master loop: drain results, apply on master's thread.
    print("\nMaster ticking…")
    t0 = time.perf_counter()
    while True:
        stats = layer.tick(s)
        if stats["applied"] or stats["errored"]:
            scored = sum(1 for n in cells if "score" in s.node(n)["attrs"])
            fetched = sum(1 for n in cells if "fetched" in s.node(n)["attrs"])
            consolidated = sum(1 for n in cells if "consolidated" in s.node(n)["attrs"])
            print(f"  t={time.perf_counter() - t0:5.2f}s  "
                  f"applied={stats['applied']:3d}  "
                  f"scored={scored:3d}  fetched={fetched:3d}  "
                  f"consolidated={consolidated:3d}")
        # Stop when all CPU + I/O work + at least one consolidation pass landed.
        scored = sum(1 for n in cells if "score" in s.node(n)["attrs"])
        fetched = sum(1 for n in cells if "fetched" in s.node(n)["attrs"])
        consolidated = sum(1 for n in cells if "consolidated" in s.node(n)["attrs"])
        if scored == 200 and fetched == 20 and consolidated >= 100:
            break
        if time.perf_counter() - t0 > 5.0:
            print(f"timeout: scored={scored} fetched={fetched} consolidated={consolidated}")
            break
        time.sleep(0.01)

    layer.stop_all()
    mcr.stop()
    elapsed = time.perf_counter() - t0
    print(f"\nTotal wall: {elapsed:.2f}s")
    print(f"Final: {scored}/200 scored, {fetched}/20 fetched, "
          f"{consolidated}/200 consolidated\n")
    print("Master remained the only writer to the substrate throughout.")


if __name__ == "__main__":
    main()
