#!/usr/bin/env python3
"""WP5 measurement: depth of composition reachable through chunking.

For L = 2..6 and 6 random primitive sequences per L (seeded), a curriculum
presents the prefixes of length 2..L applied to BASE; the length-L sequence is
then tested on a DIFFERENT, held-out base. Arms:
  off          -- gen_chunk_enabled absent (current behaviour)
  on           -- chunking on, with curriculum
  on_nocurr    -- chunking on, test only (no prefix exposure)
A case is "shallow" if the off arm already recognises the held-out target
(the sequence aliases to length <= 2); those are reported separately.
False-chunk control: 12 scrambled observations per arm-on world mint no chunk.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests")]
OUT = ROOT / "evaluation/reports/chunk_composite_depth_v1_1_20261006.json"
SEED = 20261006

from test_chunk_composite_migrated import BASE, OTHER, DT, rot, refl, scale, norm, boot, observe, chunks  # noqa: E402


def refl_c(c): return norm([[p, r, -cc, v] for p, r, cc, v in norm(c)])


def shear_a(c): return norm([[p, r + cc, cc, v] for p, r, cc, v in norm(c)])
def shear_b(c): return norm([[p, r, r + cc, v] for p, r, cc, v in norm(c)])


# v1.1 amendment: D4 x scale2 collapses most random sequences to length <= 2
# (v1 found 5 deep cases of 30). Two held integer shears (as GenMint mints
# them: kind linear) generate an infinite group, so depth is genuine.
PRIMS = {"rotation90": rot, "reflection_r": refl, "scale2": scale, "shear_a": shear_a, "shear_b": shear_b}
SHEARS = {"shear_a": [1, 1, 0, 1], "shear_b": [1, 0, 1, 1]}


def boot_with_shears(chunk):
    s, ag, n = boot(chunk)
    for name, m in SHEARS.items():
        s.add_node("DimensionGenerator", {"name": name, "kind": "linear", "coord_dims": [1, 2],
                                          "params": [1], "matrix": m})
    return s, ag, n


def apply(seq, base):
    c = base
    for g in seq:
        c = PRIMS[g](c)
    return c


def sequences(L, rng, n):
    out = []
    while len(out) < n:
        seq = []
        while len(seq) < L:
            g = rng.choice(list(PRIMS))
            if seq and g == seq[-1]:
                continue
            if g == "scale2" and seq.count("scale2") >= 2:
                continue
            seq.append(g)
        if seq not in out:
            out.append(seq)
    return out


def run_case(seq, arm):
    s, ag, n = boot_with_shears(arm != "off")
    t0 = time.perf_counter()
    if arm != "on_nocurr":
        for k in range(2, len(seq) + 1):
            observe(s, ag, n, apply(seq[:k], BASE), f"curr{k}")
    s.add_node("ShapeSignature", {"name": "heldout", "signature": json.dumps(OTHER), "kind": "faculty",
                                  "faculty": "heldout", "dim_types": DT})
    t1 = time.perf_counter()
    status = observe(s, ag, n, apply(seq, OTHER), "test")
    t2 = time.perf_counter()
    return {"status": status, "chunks": len(chunks(s)), "curriculum_s": t1 - t0, "test_s": t2 - t1}


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    rng = random.Random(SEED)
    rows = []
    for L in range(2, 7):
        for seq in sequences(L, rng, 10):
            r = {"L": L, "seq": seq}
            for arm in ("off", "on", "on_nocurr"):
                r[arm] = run_case(seq, arm)
            r["shallow"] = r["off"]["status"] == "recognized_transformed"
            rows.append(r)
            print(L, seq, {a: r[a]["status"][:5] for a in ("off", "on", "on_nocurr")}, "chunks", r["on"]["chunks"],
                  f"test {r['on']['test_s']*1e3:.0f}ms", flush=True)
    # false-chunk control
    s, ag, n = boot_with_shears(True)
    frng = random.Random(SEED + 1)
    false_status = []
    for i in range(12):
        goal = [["cell", frng.randint(0, 6), frng.randint(0, 6), frng.choice(["red", "blue"])] for _ in range(5)]
        false_status.append(observe(s, ag, n, goal, f"scr{i}"))
    false_chunks = len(chunks(s))
    summ = {}
    for L in range(2, 7):
        deep = [r for r in rows if r["L"] == L and not r["shallow"]]
        summ[L] = {"deep_cases": len(deep), "shallow_cases": sum(1 for r in rows if r["L"] == L and r["shallow"]),
                   "on_recognized": sum(r["on"]["status"] == "recognized_transformed" for r in deep),
                   "nocurr_recognized": sum(r["on_nocurr"]["status"] == "recognized_transformed" for r in deep),
                   "off_recognized": 0,
                   "median_test_ms_on": sorted(r["on"]["test_s"] for r in deep)[len(deep) // 2] * 1e3 if deep else None,
                   "median_chunks_on": sorted(r["on"]["chunks"] for r in deep)[len(deep) // 2] if deep else None}
    deep_all = [r for r in rows if not r["shallow"] and r["L"] >= 3]
    gates = {"depth3plus_on_recognized_all": all(r["on"]["status"] == "recognized_transformed" for r in deep_all),
             "depth3plus_off_none": all(r["off"]["status"] != "recognized_transformed" for r in deep_all),
             "zero_false_chunks": false_chunks == 0, "nontrivial": len(deep_all) >= 12}
    rep = {"schema": "ChunkCompositeDepthV1_1", "seed": SEED,
           "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest(),
           "seed_sha256": hashlib.sha256((ROOT / "seeds/shape_decode_loop.json").read_bytes()).hexdigest(),
           "rows": rows, "summary": summ, "false_control": {"statuses": false_status, "chunks": false_chunks},
           "gates": gates, "all_pass": all(gates.values())}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"summary": summ, "gates": gates, "false_chunks": false_chunks}, indent=1))
    return 0 if rep["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
