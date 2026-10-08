#!/usr/bin/env python3
"""Tranche 2 gate 3: chunk codebook cost and capacity-bounded retention.

Part 1 (cost): DimInfer work on an UNEXPLAINABLE observation (the full
length-2 pass runs) as held chunk count G grows: 0, 4, 16, 64.
Part 2 (retention): a 40-episode stream mixing 4 recurring depth-3 tasks
with one-off distractor tasks (each episode = its length-2 prefix then the
length-3 target, on BASE). Afterwards each recurring task's length-3
composition is probed on a held-out base WITHOUT curriculum. Arms:
unbounded, capacity 8, capacity 4. Reports recall, live chunks, and the
probe's DimInfer checked count / time.
"""
from __future__ import annotations

import hashlib
import json
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(Path(__file__).resolve().parent)]
OUT = ROOT / "evaluation/reports/chunk_retention_recurrence_v1_20261007.json"
SEED = 20261007

from test_chunk_composite_migrated import BASE, OTHER, DT, observe, chunks  # noqa: E402
from chunk_composite_depth_v1 import PRIMS, apply, boot_with_shears  # noqa: E402

SCRAMBLED = [["cell", 0, 0, "red"], ["cell", 5, 1, "red"], ["cell", 3, 3, "blue"], ["cell", 1, 4, "red"], ["cell", 2, 2, "red"]]


def diminfer(s, goal, field):
    return s._inner.evaluate({"type": "DimInfer", "goal": {"type": "Lit", "value": goal}, "max_dims": 2, "field": field}, {})


def part1(rng):
    out = []
    names = list(PRIMS)
    pairs = [(a, b) for a in names for b in names if a != b]
    for G in (0, 4, 16, 64):
        s, ag, n = boot_with_shears(True)
        made = 0
        while made < G:
            a, b = rng.choice(pairs)
            ka, kb = rng.choice([1, 2]), rng.choice([1, 2])
            s.add_node("DimensionGenerator", {"name": f"chunk_t{made}", "kind": "composite", "steps": [a, b],
                                              "ks": [ka, kb], "params": [1]})
            made += 1
        ts = []
        for _ in range(5):
            t0 = time.perf_counter(); chk = diminfer(s, SCRAMBLED, "checked"); ts.append(time.perf_counter() - t0)
        out.append({"G": G, "checked": chk, "median_ms": statistics.median(ts) * 1e3})
        print("G", G, chk, f"{statistics.median(ts)*1e3:.2f}ms", flush=True)
    return out


def seq3(rng):
    while True:
        s = [rng.choice(list(PRIMS)) for _ in range(3)]
        if s[0] != s[1] and s[1] != s[2]:
            return s


def deep(seq):
    s, ag, n = boot_with_shears(False)
    s.add_node("ShapeSignature", {"name": "heldout", "signature": json.dumps(OTHER), "kind": "faculty", "faculty": "heldout", "dim_types": DT})
    return observe(s, ag, n, apply(seq, OTHER), "probe") != "recognized_transformed"


def part2(rng, recur=0.10, n_eps=120):
    tasks = []
    while len(tasks) < 4:
        q = seq3(rng)
        if q not in tasks and deep(q):
            tasks.append(q)
    stream = []
    # SPARSE stream: 120 episodes, recurring tasks 10% of the stream (each
    # task ~3 times, spread out), distractors 90%.
    for i in range(n_eps):
        if rng.random() < recur:
            stream.append(("task", rng.randrange(4)))
        else:
            q = seq3(rng)
            stream.append(("distractor", q))
    out = {}
    for arm, cap, prot in (("unbounded", None, None), ("capacity8", 8, None), ("capacity4", 4, None),
                           ("protect2_capacity4", 4, 2), ("protect2_capacity8", 8, 2)):
        s, ag, n = boot_with_shears(True)
        if cap is not None:
            s.set_attr(ag, "gen_chunk_capacity", cap)
        if prot is not None:
            s.set_attr(ag, "gen_chunk_protect_uses", prot)
        for i, (kind, x) in enumerate(stream):
            q = tasks[x] if kind == "task" else x
            observe(s, ag, n, apply(q[:2], BASE), f"e{i}p")
            observe(s, ag, n, apply(q, BASE), f"e{i}t")
        s.add_node("ShapeSignature", {"name": "heldout", "signature": json.dumps(OTHER), "kind": "faculty", "faculty": "heldout", "dim_types": DT})
        live = [c for c in chunks(s) if c.get("retired") != 1]
        recall, checked, ms = [], [], []
        for j, q in enumerate(tasks):
            goal = apply(q, OTHER)
            t0 = time.perf_counter(); chk = diminfer(s, goal, "checked"); ms.append((time.perf_counter() - t0) * 1e3)
            checked.append(chk)
            recall.append(observe(s, ag, n, goal, f"probe{j}") == "recognized_transformed")
        seen = {x for k, x in stream if k == "task"}
        cnt = {j: sum(1 for k, x in stream if k == "task" and x == j) for j in range(len(tasks))}
        out[arm] = {"recall_recurred": sum(r for j, r in enumerate(recall) if cnt[j] >= 2),
                    "n_recurred": sum(1 for j in cnt if cnt[j] >= 2), "recall": sum(recall), "of": len(tasks), "chunks_total": len(chunks(s)), "chunks_live": len(live),
                    "probe_checked_median": statistics.median(checked), "probe_ms_median": statistics.median(ms)}
        print(arm, out[arm], flush=True)
    return {"tasks": tasks, "stream": stream, "arms": out}


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    rng = random.Random(SEED)
    p1 = []
    p2 = {"sparse": part2(random.Random(SEED), 0.10, 120), "dense": part2(random.Random(SEED + 5), 0.5, 40),
          "sparse2": part2(random.Random(SEED + 9), 0.10, 120)}
    gates = {f"{k}_protect2_capacity4_keeps_recurred": v["arms"]["protect2_capacity4"]["recall_recurred"] == v["arms"]["unbounded"]["recall_recurred"]
             for k, v in p2.items()}
    gates.update({f"{k}_protect2_capacity4_cheaper_than_unbounded": v["arms"]["protect2_capacity4"]["probe_checked_median"] < v["arms"]["unbounded"]["probe_checked_median"]
                  for k, v in p2.items()})
    rep = {"schema": "ChunkRetentionRecurrenceV1", "seed": SEED,
           "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest(),
           "seed_sha256": hashlib.sha256((ROOT / "seeds/shape_decode_loop.json").read_bytes()).hexdigest(),
           "part1": p1, "part2": p2, "gates": gates, "all_pass": all(gates.values())}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    print(json.dumps(gates, indent=1))
    return 0 if rep["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
