"""Read results/figadj_replacement.json and print the four-arm verdict.

Pure read-out over the committed JSON. No re-running, no re-deciding: the
decision rules are VISION_FIGADJ_REPLACEMENT_PREREG.md §3, applied mechanically.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "figadj_replacement.json")


def main():
    with open(RES) as fh:
        d = json.load(fh)

    print(f"provenance : {d['provenance']}")
    print(f"prereg     : {d['prereg']} @ {d['prereg_commit']}")
    print(f"config     : GRID={d['config']['GRID']} REGION={d['config']['REGION']} "
          f"tiles={d['config']['n_tiles']} k_main={d['config']['k_main']} "
          f"consecutive={d['config']['n_consecutive']}")

    # ---- CONTROLS ---------------------------------------------------------
    print("\n=== DEAD-INSTRUMENT / POSITIVE / NEGATIVE CONTROLS ===")
    c = d["controls"]
    for arm in ("incumbent", "replacement"):
        print(f"  D1  {arm:12s} reproduces={c[f'D1_{arm}']['reproduces']} "
              f"protos={c[f'D1_{arm}']['n_protos']} "
              f"members={c[f'D1_{arm}']['max_members']}")
    for arm in ("incumbent", "replacement"):
        a = c[f"D2a_{arm}"]
        print(f"  D2a {arm:12s} FIRED={a['fired']} protos={a['n_protos']} "
              f"members={a['max_members']} n_frame={a['n_frame']} "
              f"reach={a['reach']} (figadj={a['G_figadj']} "
              f"ownlost={a['G_own_lost']})")
    for arm in ("incumbent", "replacement"):
        b = c[f"D2b_{arm}"]
        print(f"  D2b {arm:12s} FIRED={b['fired']} protos={b['n_protos']} "
              f"members={b['max_members']} n_frame={b['n_frame']} "
              f"reach={b['reach']}")
    for arm in ("incumbent", "replacement"):
        n = c[f"NOISE_{arm}"]
        print(f"  NOISE {arm:10s} REGISTERED(n=10) passes="
              f"{n['REGISTERED_CONTROL_PASSES']} "
              f"({n['fields_minting_registered_n']}/10) | "
              f"full n=100 rate={n['false_mint_rate']:.2f} "
              f"max_false_proto={n['max_false_proto_size']}")

    # ---- ARM 1 ------------------------------------------------------------
    print("\n=== ARM 1: do multi-cell protos appear on real frames? ===")
    print(f"{'corpus':7s} {'arm':12s} {'k':>3s} {'comps':>6s} {'refused':>8s} "
          f"{'gnd2':>5s} {'pass':>5s} {'protos':>7s} {'MULTI':>6s} {'maxfrac':>8s}")
    for cid in ("C1", "C2"):
        for arm in ("incumbent", "replacement"):
            for k in d["config"]["k_levels"]:
                rows = [r for r in d["m1_rows"]
                        if r["corpus"] == cid and r["arm"] == arm and r["k"] == k]
                if not rows:
                    continue
                n = len(rows)
                comps = sum(r["n_components"] for r in rows) / n
                ref = sum(r["G_figadj"] + r["G_own_lost"] for r in rows) / n
                gnd2 = sum(r["G_gnd2"] for r in rows) / n
                pas = sum(r["G_pass"] for r in rows) / n
                pro = sum(r["n_protos"] for r in rows) / n
                mul = sum(r["n_protos_multicell"] for r in rows) / n
                mf = max(r["max_members_frac"] for r in rows)
                share = (100.0 * ref / comps) if comps else 0.0
                print(f"{cid:7s} {arm:12s} {k:3d} {comps:6.1f} "
                      f"{ref:6.1f}({share:4.1f}%) {gnd2:5.1f} {pas:5.1f} "
                      f"{pro:7.1f} {mul:6.1f} {mf:8.3f}")

    # ---- RECONCILIATION ---------------------------------------------------
    print("\n=== RECONCILIATION (the read-out must measure the RULE) ===")
    for arm in ("incumbent", "replacement"):
        rows = [r for r in d["m1_rows"] if r["arm"] == arm]
        bad = [r for r in rows if r["G_pass"] != r["n_protos"]]
        rim = sum(r["rim_mismatch"] for r in rows)
        note = ("" if arm == "replacement" else
                "  (rim NOT materialised on this arm -- bo_rim is gated on "
                "bown_own; a non-zero count here is the flag working, not a "
                "defect, and is not a reconciliation claim)")
        print(f"  {arm:12s} rows={len(rows)} G_pass!=n_protos: {len(bad)} | "
              f"rim_mismatch={rim}{note}")

    # ---- ARM 2 ------------------------------------------------------------
    print("\n=== ARM 2: do the protos CORRESPOND to anything? ===")
    print(f"{'corpus|arm':26s} {'pairs':>5s} {'persist':>8s} {'floorA':>8s} "
          f"{'floorB':>8s} {'vsA lo':>8s} {'vsB lo':>8s}  verdict")
    for key, m in d["m2"].items():
        a_lo = m["paired_vs_floorA"]["lo"]
        b_lo = m["paired_vs_floorB"]["lo"]
        ok = (a_lo is not None and a_lo > 0 and b_lo is not None and b_lo > 0)
        print(f"{key:26s} {m['n_pairs_scored']:5d} "
              f"{m['persist']['mean']:8.3f} "
              f"{m['floorA_temporal_shuffle']['mean']:8.3f} "
              f"{m['floorB_arbitrary_partition']['mean']:8.3f} "
              f"{a_lo:8.3f} {b_lo:8.3f}  "
              f"{'PASS' if ok else 'FAIL'}")

    # ---- ARM 4 / M4 -------------------------------------------------------
    print("\n=== M4: has the background SWALLOWED the field? ===")
    for arm in ("incumbent", "replacement"):
        rows = [r for r in d["m1_rows"] if r["arm"] == arm]
        mx = max(r["max_members_frac"] for r in rows)
        print(f"  {arm:12s} max over all rows of max_members/324 = {mx:.3f}")


if __name__ == "__main__":
    main()
