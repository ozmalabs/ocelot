#!/usr/bin/env python3
"""Tranche 5: bounding protected (recurred) chunks on a long, shifting stream.

Phase A (150 episodes): 8 recurring depth-3 tasks at 30%, distractors 70%.
Phase B (150 episodes): a DIFFERENT 4 recurring tasks at 30%.
At the end, phase-B tasks are probed on a held-out base without curriculum.
Arms: protect2+cap4 (protected set unbounded), protect2+cap4+pcap6, +pcap4.
"""
import json, random, statistics, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(Path(__file__).resolve().parent)]
OUT = ROOT / "evaluation/reports/chunk_protect_bound_v1_20261007.json"
from test_chunk_composite_migrated import BASE, OTHER, DT, observe, chunks  # noqa: E402
from chunk_composite_depth_v1 import apply, boot_with_shears  # noqa: E402
from chunk_retention_cost_v1 import seq3, deep, diminfer  # noqa: E402


def main():
    if OUT.exists(): raise SystemExit("refusing to overwrite")
    rng = random.Random(20261007)
    tasks = []
    while len(tasks) < 12:
        q = seq3(rng)
        if q not in tasks and deep(q): tasks.append(q)
    A, B = tasks[:8], tasks[8:]
    stream = [("A" if rng.random() < .3 else "D", rng.randrange(8)) for _ in range(150)] + \
             [("B" if rng.random() < .3 else "D", rng.randrange(4)) for _ in range(150)]
    stream = [(k, (A[i] if k == "A" else B[i] if k == "B" else seq3(rng))) for k, i in stream]
    out = {}
    for arm, pcap in (("protect2_cap4", None), ("protect2_cap4_pcap6", 6), ("protect2_cap4_pcap4", 4)):
        s, ag, n = boot_with_shears(True)
        s.set_attr(ag, "gen_chunk_capacity", 4); s.set_attr(ag, "gen_chunk_protect_uses", 2)
        if pcap: s.set_attr(ag, "gen_chunk_protect_capacity", pcap)
        t0 = time.time()
        for i, (_, q) in enumerate(stream):
            observe(s, ag, n, apply(q[:2], BASE), f"e{i}p"); observe(s, ag, n, apply(q, BASE), f"e{i}t")
        s.add_node("ShapeSignature", {"name": "heldout", "signature": json.dumps(OTHER), "kind": "faculty", "faculty": "heldout", "dim_types": DT})
        live = [c for c in chunks(s) if c.get("retired") != 1]
        chk, rec = [], []
        for j, q in enumerate(B):
            g = apply(q, OTHER); chk.append(diminfer(s, g, "checked"))
            rec.append(observe(s, ag, n, g, f"pb{j}") == "recognized_transformed")
        out[arm] = {"recall_B": sum(rec), "of": len(B), "live": len(live), "total": len(chunks(s)),
                    "probe_checked_median": statistics.median(chk), "stream_s": time.time() - t0}
        print(arm, out[arm], flush=True)
    gates = {"pcap6_keeps_B": out["protect2_cap4_pcap6"]["recall_B"] == out["protect2_cap4"]["recall_B"],
             "pcap6_bounds_live": out["protect2_cap4_pcap6"]["live"] <= 6 + 4,
             "pcap6_cheaper": out["protect2_cap4_pcap6"]["probe_checked_median"] < out["protect2_cap4"]["probe_checked_median"]}
    OUT.write_text(json.dumps({"schema": "ChunkProtectBoundV1", "arms": out, "gates": gates, "tasks": tasks}, indent=1) + "\n")
    print(json.dumps(gates, indent=1))

main()
