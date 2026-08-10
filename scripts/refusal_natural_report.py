#!/usr/bin/env python3
"""Read results/refusal_natural.json (the PRODUCT) and print the key numbers for
the results doc. Verify-on-the-product: no recomputation, only reads."""
import json, pathlib, numpy as np
ROOT = pathlib.Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "results" / "refusal_natural.json").read_text())

print("provenance:", R["provenance"])
print("engine_source_match:", R["engine_source_match"])
print("provenance_after:", R["provenance_after"])
print("loadavg start/end:", R["loadavg_start"], R["loadavg_end"], "threads", R["torch_threads"])
print("elapsed_secs:", R["elapsed_secs"], " data_sha:", R["data_sha"])
print("params:", {k: R["params"][k] for k in ("IN_CLASSES","OOD_CLASSES","M_TRAIN","M_TEST","N_NEAR","N_FAR","EPOCHS")})

def net_mean(arm, pool):
    vals = [e[f"auroc_{pool}"]["auroc"] for e in arm["per_seed"]]
    return np.mean(vals), np.std(vals), vals

for s in R["splits"]:
    ss = s["split_seed"]
    print("\n" + "="*80)
    print(f"SPLIT {ss}  n_test={s['n_test']} n_val={s['n_val']} n_near={s['n_near']} n_far={s['n_far']}")
    ia = s["indist_acc"]
    print(f"  IN-DIST ACC: net {ia['net']['mean']:.3f}±{ia['net']['std']:.3f}"
          f"  sub_raw {ia['substrate_residual_raw']:.3f}"
          f"  sub_feat {np.mean(ia['substrate_residual_feat']['per_seed']):.3f}")
    a = s["arms"]
    print("  AUROC (near / far):")
    print(f"    substrate_residual_raw     "
          f"near {a['substrate_residual_raw']['auroc_near']['auroc']:.3f} {a['substrate_residual_raw']['auroc_near']['ci']}"
          f"  far {a['substrate_residual_raw']['auroc_far']['auroc']:.3f}")
    for arm in ("substrate_residual_feat","substrate_residual_feat_centroid",
                "net_msp","net_energy","net_maha","net_knn"):
        mn_near = net_mean(a[arm],"near");
        try: mn_far = net_mean(a[arm],"far")
        except Exception: mn_far=(float('nan'),0,[])
        print(f"    {arm:32s} near {mn_near[0]:.3f}±{mn_near[1]:.3f}  far {mn_far[0]:.3f}±{mn_far[1]:.3f}")
    # far by kind for raw + feat + best net
    print("  FAR by kind (raw):", {k: round(v["auroc"],3) for k,v in a["substrate_residual_raw"]["auroc_far_by_kind"].items()})
    fk = a["substrate_residual_feat"]["per_seed"][0]["auroc_far_by_kind"]
    print("  FAR by kind (feat s0):", {k: round(v["auroc"],3) for k,v in fk.items()})
    mk = a["net_maha"]["per_seed"][0]["auroc_far_by_kind"]
    print("  FAR by kind (maha s0):", {k: round(v["auroc"],3) for k,v in mk.items()})
    # paired bootstrap
    print("  PAIRED bootstrap (first net seed):")
    for pool in ("near","far"):
        pb = s["paired_bootstrap"][pool]
        print(f"    [{pool}]")
        for k in ("feat_minus_msp","feat_minus_energy","feat_minus_maha","feat_minus_knn","feat_minus_raw"):
            d=pb[k]; tag="SEP+" if d["sep_pos"] else ("SEP-" if d["sep_neg"] else "ns")
            print(f"        {k:20s} {d['diff']:+.3f}  CI[{d['ci'][0]:+.3f},{d['ci'][1]:+.3f}] {tag}")
        rb=pb["raw_minus_bestnet"]; tag="SEP+" if rb["sep_pos"] else ("SEP-" if rb["sep_neg"] else "ns")
        print(f"        raw_minus_bestnet({rb['best_net_arm']}) {rb['diff']:+.3f} CI[{rb['ci'][0]:+.3f},{rb['ci'][1]:+.3f}] {tag}")
    # confab a0.1
    print("  CONFAB a0.1:", {k: round(v,3) for k,v in s["confabulation"]["a0.1"].items()})
    # cost crossover fractions at a0.1
    cx = s["crossover"]
    for pool in ("near","far"):
        fb = cx[pool]["sub_feat_beats_best_net"]; rb = cx[pool]["sub_raw_beats_best_net"]
        def frac(g):
            allpts=[v for r in g for v in g[r].values()]; return sum(allpts)/len(allpts)
        print(f"  COST[{pool}] sub_feat_beats_best_net frac={frac(fb):.2f}  sub_raw_beats_best_net frac={frac(rb):.2f}")
    # matched op-point refuse rates a0.1 near
    print("  OP-POINT a0.1 (in-dist refuse / near OOD refuse):")
    for arm,d in s["cost_surface"]["a0.1"]["near"].items():
        print(f"    {arm:32s} in {d['_indist_refuse']:.3f}  near-detect {d['_ood_refuse']:.3f}")
