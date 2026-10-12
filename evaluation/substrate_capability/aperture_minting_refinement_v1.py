#!/usr/bin/env python3
"""WP1 measurement: aperture minting and exact refinement over a random panel.

For a seeded panel of random 2-relation shapes, observers at three apertures
({pred} < {pred,val} < {pred,val,obj}) each perceive one shape and hold
nothing. An independent Python oracle computes, from the shapes alone, which
axes must exist (content-keyed) and which refinement links must hold. The
substrate's mints and refines_at_aperture edges are compared to it exactly.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
OUT = ROOT / "evaluation/reports/aperture_minting_refinement_v1_20261006.json"
DT = ["pred", "val", "obj"]
APERTURES = {"coarse": ["pred"], "mid": ["pred", "val"], "fine": ["pred", "val", "obj"]}
DOT = "\u00b7"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def project(sig, ap):
    return sorted([[slot if dt in ap else DOT for slot, dt in zip(rel, DT)] for rel in sig])


def panel(seed, n_shapes):
    rng = random.Random(seed)
    preds, vals, objs = ["a", "b", "c"], ["p", "q"], ["x", "y", "z"]
    shapes = []
    for i in range(n_shapes):
        shapes.append([[rng.choice(preds), rng.choice(vals), rng.choice(objs)] for _ in range(2)])
    observers = []
    for i, sig in enumerate(shapes):
        for lvl in APERTURES:
            if rng.random() < 0.7:
                observers.append((f"o{i}_{lvl}", lvl, sig))
    return shapes, observers


def oracle(observers):
    axes = {}
    for name, lvl, sig in observers:
        key = (lvl, json.dumps(project(sig, APERTURES[lvl])))
        axes.setdefault(key, set()).add(name)
    links = set()
    for (lf, sf), (lc, sc) in itertools.permutations(axes, 2):
        apf, apc = set(APERTURES[lf]), set(APERTURES[lc])
        if apc < apf and json.dumps(project(json.loads(sf), APERTURES[lc])) == sc:
            links.add(((lf, sf), (lc, sc)))
    return axes, links


def run(seed, n_shapes):
    from substrate.boot_core import boot_core, load_seeds_into
    from domains import reflective_faculty as rf
    shapes, observers = panel(seed, n_shapes)
    s, ag = boot_core()
    load_seeds_into(s, ag, ["aperture_minting"])
    native = rf._native_eval2(s)
    for name, lvl, sig in observers:
        o = s.add_node("Observer", {"name": name, "resolves": APERTURES[lvl], "ap_scope_n": 0.0,
                                    "ap_gen": 0.0, "mint_at_aperture": 1})
        sh = s.add_node("ShapeSignature", {"name": f"{name}_sees", "kind": "world", "signature": sig, "dim_types": DT})
        s.add_edge(o, "perceives", sh)
    t0 = time.perf_counter()
    steps = native.run_rules()
    dt = time.perf_counter() - t0
    lvl_of = {tuple(v): k for k, v in APERTURES.items()}
    got_axes = {}
    for n in s.nodes("CapabilityAxis"):
        a = s.node(n)["attrs"]
        if a.get("source") != "aperture_mint":
            continue
        got_axes[n] = (lvl_of[tuple(a["minted_aperture"])], json.dumps(sorted([list(r) for r in a["minted_from_signature"]])))
    got_links = {(got_axes[f], got_axes[c]) for f in got_axes for c in s.neighbours(f, "refines_at_aperture")}
    exp_axes, exp_links = oracle(observers)
    return {"seed": seed, "n_shapes": n_shapes, "observers": len(observers), "rule_steps": steps,
            "closure_seconds": dt, "axes_expected": len(exp_axes), "axes_got": len(got_axes),
            "axes_exact": set(got_axes.values()) == set(exp_axes) and len(got_axes) == len(set(got_axes.values())),
            "links_expected": len(exp_links), "links_got": len(got_links),
            "false_links": len(got_links - exp_links), "missed_links": len(exp_links - got_links)}


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    srcs = ["seeds/aperture_minting.json", "seeds/observer_aperture.json", "seeds/shape_decode_loop.json",
            "scripts/gen_aperture_minting_seed.py", "evaluation/substrate_capability/aperture_minting_refinement_v1.py",
            "runners/dsl/python/substrate_rs/_native.abi3.so"]
    before = {p: sha(ROOT / p) for p in srcs}
    rows = [run(seed, n) for n in (4, 8, 16, 32) for seed in (1, 2, 3)]
    after = {p: sha(ROOT / p) for p in srcs}
    gates = {"axes_exact_all": all(r["axes_exact"] for r in rows),
             "zero_false_links": sum(r["false_links"] for r in rows) == 0,
             "zero_missed_links": sum(r["missed_links"] for r in rows) == 0,
             "nontrivial_links": sum(r["links_expected"] for r in rows) > 0,
             "sources_stable": before == after}
    rep = {"schema": "ApertureMintingRefinementV1", "sources_sha256": before, "gates": gates,
           "all_pass": all(gates.values()), "rows": rows}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": rep["all_pass"], **gates}, indent=1))
    for r in rows:
        print(r["n_shapes"], r["seed"], r["observers"], r["axes_got"], r["links_got"], r["false_links"], r["missed_links"], f"{r['closure_seconds']*1e3:.1f}ms")
    return 0 if rep["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
