#!/usr/bin/env python3
"""Tranche 2 gate 4 measurement: held-generator (DimInfer) recognition at a
substrate-chosen grain on real handwriting, through the full sd loop.

20 Omniglot drawings (16x16), held maps rot90/rot180/rot270/refl_r/refl_c
(all in the seeded DimensionGenerator codebook), conditions:
  exact  goal = M.A
  jitter goal = M.A' (A re-rendered with +-0.35 cell jitter)
  cross  goal = M.B (another character; false-recognition control)
Arms: agent.dim_grains absent (current) vs [0,1,2].
Recognition = status recognized_transformed AND covered_by == the base.
"""
import hashlib, json, random, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(Path(__file__).resolve().parent)]
from geninfer_grain_ladder_omniglot_v1 import drawings, strokes, raster  # noqa: E402
OUT = ROOT / "evaluation/reports/diminfer_grain_omniglot_v1_20261007.json"
DT = ["pred", "coord:r", "coord:c"]
MAPS = {"rot90": lambda r, c: (c, -r), "rot180": lambda r, c: (-r, -c), "rot270": lambda r, c: (-c, r),
        "refl_r": lambda r, c: (-r, c), "refl_c": lambda r, c: (r, -c)}

def norm(cs):
    mr = min(r for r, _ in cs); mc = min(c for _, c in cs)
    return sorted({(r - mr, c - mc) for r, c in cs})

def sig(cs): return [["cell", r, c] for r, c in cs]

def run(base, goal, grains):
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    s, ag = boot_core(); n = rf._native_eval2(s); rf._ensure_shape_decode_loop(s, n, ag)
    if grains is not None:
        s.set_attr(ag, "dim_grains", grains)
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(base), "kind": "faculty", "faculty": "base", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    o = s.add_node("Observation", {"signature": goal, "key": ["g4"], "status": "decoded", "residual": goal, "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", o)
    t0 = time.perf_counter(); n.run_rules(); dt = time.perf_counter() - t0
    a = s.node(o)["attrs"]
    return {"recognized": a.get("status") == "recognized_transformed" and a.get("covered_by") == "base",
            "status": a.get("status"), "grain": a.get("dim_grain"), "grain_residual_axes": sum(
                1 for x in s.nodes("CapabilityAxis") if s.node(x)["attrs"].get("source") == "grain_residual"), "seconds": dt}

def main():
    if OUT.exists(): raise SystemExit(f"refusing to overwrite {OUT}")
    rng = random.Random(20261007)
    ds = drawings(); As = [raster(strokes(p)) for _, p in ds]; Js = [raster(strokes(p), 0.35, rng) for _, p in ds]
    rows = []
    for i, A in enumerate(As):
        for mn, f in MAPS.items():
            goals = {"exact": norm([f(*x) for x in A]), "jitter": norm([f(*x) for x in Js[i]]),
                     "cross": norm([f(*x) for x in As[(i + 7) % len(As)]])}
            for cond, g in goals.items():
                rows.append({"i": i, "map": mn, "cond": cond, "off": run(sig(A), sig(g), None), "ladder": run(sig(A), sig(g), [0, 1, 2])})
        print(i, flush=True)
    summ = {f"{c}:{a}": sum(r[a]["recognized"] for r in rows if r["cond"] == c) for c in ("exact", "jitter", "cross") for a in ("off", "ladder")}
    grains = {c: sorted({r["ladder"]["grain"] for r in rows if r["cond"] == c and r["ladder"]["recognized"]}) for c in ("exact", "jitter", "cross")}
    n = sum(1 for r in rows if r["cond"] == "exact")
    gates = {"exact_unchanged": summ["exact:off"] == summ["exact:ladder"] == n,
             "jitter_gain": summ["jitter:ladder"] > summ["jitter:off"],
             "cross_false_recognitions_zero": summ["cross:ladder"] == 0}
    rep = {"schema": "DimInferGrainOmniglotV1", "n_per_condition": n,
           "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest(),
           "seed_sha256": hashlib.sha256((ROOT / "seeds/shape_decode_loop.json").read_bytes()).hexdigest(),
           "summary": summ, "grains": grains, "gates": gates, "all_pass": all(gates.values()), "rows": rows}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"summary": summ, "grains": grains, "gates": gates}, indent=1))

if __name__ == "__main__":
    main()
