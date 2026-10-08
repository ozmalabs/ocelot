#!/usr/bin/env python3
"""Tranche 2 gate 5: MDL witness through the full sd loop (feature build).
20 Omniglot drawings x 3 planted maps outside the held codebook.
outlier: 2 cells displaced by 3 (count-preserving cases only); cross: M.B for another
character (false-recognition control); exact: M.A. Arms: gen_mdl_enabled absent / 1."""
import hashlib, json, random, sys, argparse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import geninfer_grain_ladder_omniglot_v1 as w  # noqa: E402
OUT = ROOT / "evaluation/reports/mdl_sd_loop_v1_20261007.json"

def run(base, goal, mdl):
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    s, ag = boot_core(); n = rf._native_eval2(s); rf._ensure_shape_decode_loop(s, n, ag)
    s.set_attr(ag, "gen_infer_enabled", 1.0); s.set_attr(ag, "gen_linear_exact_enabled", 1.0)
    if mdl: s.set_attr(ag, "gen_mdl_enabled", 1)
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(base), "kind": "faculty", "faculty": "base", "dim_types": w.DT})
    o = s.add_node("Observation", {"signature": goal, "key": ["m"], "status": "decoded", "residual": goal, "decoded_epoch": 0.0, "dim_types": w.DT})
    s.add_edge(ag, "observed", o); steps = n.run_rules(100000)
    a = s.node(o)["attrs"]
    gens = [list(s.node(g)["attrs"]["matrix"]) for g in s.nodes("DimensionGenerator") if s.node(g)["attrs"].get("kind") == "linear"]
    return {"status": a.get("status"), "matrix": gens[0] if gens else None, "outliers": len(a.get("mdl_outliers") or []),
            "mdl_axes": sum(1 for x in s.nodes("CapabilityAxis") if s.node(x)["attrs"].get("source") == "mdl_outlier"), "steps": steps}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--native", type=Path, required=True); args = ap.parse_args()
    if OUT.exists(): raise SystemExit("refusing to overwrite")
    tmp = w.install(args.native.resolve()); rng = random.Random(20261007); ds = w.drawings(); rows = []
    for i, (_, p) in enumerate(ds):
        A = w.raster(w.strokes(p)); B = w.raster(w.strokes(ds[(i + 7) % len(ds)][1]))
        for mn, M in w.MAPS.items():
            mov = list(w.apply(M, A))
            for j in rng.sample(range(len(mov)), 2): mov[j] = (mov[j][0] + 3, mov[j][1] + 3)
            goals = {"exact": w.apply(M, A), "outlier": sorted(set(mov)), "cross": w.apply(M, B)}
            for cond, g in goals.items():
                if cond == "outlier" and len(g) != len(A): continue
                r = {"i": i, "map": mn, "cond": cond, "planted": M}
                for arm in (0, 1):
                    r[f"mdl{arm}"] = x = run(w.sig(A), w.sig(g), arm)
                    x["recovered"] = x["matrix"] == M
                rows.append(r)
        print(i, flush=True)
    summ = {}
    for cond in ("exact", "outlier", "cross"):
        rs = [r for r in rows if r["cond"] == cond]
        for arm in (0, 1):
            summ[f"{cond}:mdl{arm}"] = {"n": len(rs), "recovered": sum(r[f"mdl{arm}"]["recovered"] for r in rs),
                                         "any_generator": sum(r[f"mdl{arm}"]["matrix"] is not None for r in rs),
                                         "with_outliers": sum(r[f"mdl{arm}"]["status"] == "recognized_with_outliers" for r in rs)}
    ex, ou, cr = summ["exact:mdl1"], summ["outlier:mdl1"], summ["cross:mdl1"]
    gates = {"exact_unchanged": ex["recovered"] == ex["n"] == summ["exact:mdl0"]["recovered"],
             "outlier_recovered_all": ou["recovered"] == ou["n"] and ou["with_outliers"] == ou["n"],
             "outlier_off_none": summ["outlier:mdl0"]["any_generator"] == 0,
             "cross_zero_generators": cr["any_generator"] == 0,
             "terminates": all(r[a]["steps"] < 100000 for r in rows for a in ("mdl0", "mdl1"))}
    rep = {"schema": "MdlSdLoopV1", "native_sha256": hashlib.sha256(args.native.read_bytes()).hexdigest(),
           "seed_sha256": hashlib.sha256((ROOT / "seeds/shape_decode_loop.json").read_bytes()).hexdigest(),
           "summary": summ, "gates": gates, "all_pass": all(gates.values()), "rows": rows}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"summary": summ, "gates": gates}, indent=1)); tmp.cleanup()

main()
