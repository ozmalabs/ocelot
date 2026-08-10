"""value_flood_counterfactual -- would a DIFFERENT flood statistic fix protos?

A SIMULATION, labelled as such. It re-implements the exact semantics of
`bo_bgflood` / `bo_label` / `bo_mint_enclosed` (flood from the frame across
admissible edges; components under the same admissibility; G_figadj then
G_gnd2) in numpy, with the edge-admissibility predicate SWAPPED. It does not
touch the seed and claims nothing about the substrate's behaviour -- it
predicts what the substrate WOULD do under a changed statistic.

Its own validity check: under the incumbent predicate (exact equality) it must
reproduce the substrate's measured proto counts row for row. A simulation that
cannot reproduce the mechanism it is varying predicts nothing.

Statistics compared:
  eq    : |dv| == 0   -- the incumbent (value equality)
  step1 : |dv| <= 1   -- one quantizer level: the smallest difference the
                        observation can express (the falls-out tolerance)
  step2 : |dv| <= 2   -- deliberately LOOSER than anything that falls out,
                        included only to show the trend is not an artifact of
                        the derived value.
"""
from __future__ import annotations
import importlib.util
import json
import os
import sys
from collections import deque

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PREDS = {
    "eq":    lambda a, b: a == b,
    "step1": lambda a, b: abs(a - b) <= 1,
    "step2": lambda a, b: abs(a - b) <= 2,
}
NB = ((1, 0), (-1, 0), (0, 1), (0, -1))


def simulate(vals, ok):
    """Flood + label + the two mint gates, exactly as the seed sequences them."""
    a = np.asarray(vals, int)
    H, W = a.shape
    lab = -np.ones((H, W), int)
    comps = []
    for r0 in range(H):
        for c0 in range(W):
            if lab[r0, c0] >= 0:
                continue
            i = len(comps)
            lab[r0, c0] = i
            q, mem = deque([(r0, c0)]), []
            while q:
                r, c = q.popleft()
                mem.append((r, c))
                for dr, dc in NB:
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < H and 0 <= cc < W and lab[rr, cc] < 0 \
                            and ok(int(a[r, c]), int(a[rr, cc])):
                        lab[rr, cc] = i
                        q.append((rr, cc))
            comps.append(mem)
    # bg: a component is ground iff it contains a frame cell (the flood starts
    # at the frame and propagates along admissible edges only)
    ground = set()
    for i, mem in enumerate(comps):
        if any(r in (0, H - 1) or c in (0, W - 1) for r, c in mem):
            ground.add(i)
    n_bg = sum(len(comps[i]) for i in ground)

    protos, figadj, gnd2 = [], 0, 0
    for i, mem in enumerate(comps):
        if i in ground:
            continue
        mset = set(mem)
        touch_fig, gl = False, set()
        for r, c in mem:
            for dr, dc in NB:
                rr, cc = r + dr, c + dc
                if not (0 <= rr < H and 0 <= cc < W) or (rr, cc) in mset:
                    continue
                j = int(lab[rr, cc])
                if j in ground:
                    gl.add(j)
                else:
                    touch_fig = True
        if touch_fig:
            figadj += 1
        elif len(gl) > 1:
            gnd2 += 1
        else:
            protos.append(len(mem))
    return {"n_components": len(comps), "bg_frac": n_bg / (H * W),
            "n_enclosed_components": len(comps) - len(ground),
            "G_figadj": figadj, "G_gnd2": gnd2,
            "n_protos": len(protos),
            "n_protos_multicell": sum(1 for m in protos if m >= 2),
            "max_members": max(protos, default=0)}


def main():
    vf = importlib.util.spec_from_file_location(
        "vf", os.path.join(ROOT, "scripts", "value_flood_measure.py"))
    m = importlib.util.module_from_spec(vf)
    vf.loader.exec_module(m)
    meas = json.load(open(os.path.join(ROOT, "results", "value_flood.json")))
    by = {(r["corpus"], r["L"], r["k"], r["frame"]): r for r in meas["rows"]}

    vp = m._vp()
    out, mismatches = [], 0
    for cid, spec in m.CORPORA.items():
        for L in m.LATTICES:
            frames, meta = vp.jellyfin_frames(
                m.N_DECODE, every=2, start_s=300, size=L,
                episode_index=spec["episode_index"])
            if not str(meta["episode_id"]).startswith(spec["pin"]):
                raise SystemExit(f"PIN MISMATCH {cid} -- VOID")
            for k in m.K_LEVELS:
                for fi in m.FRAME_INDICES:
                    q = m.quantize(frames[fi], k)
                    row = {"corpus": cid, "L": L, "k": k, "frame": fi}
                    for name, ok in PREDS.items():
                        row[name] = simulate(q, ok)
                    ref = by[(cid, L, k, fi)]
                    row["substrate_n_protos"] = ref["n_protos"]
                    row["validates"] = bool(
                        row["eq"]["n_protos"] == ref["n_protos"]
                        and row["eq"]["n_protos_multicell"]
                        == ref["n_protos_multicell"])
                    mismatches += 0 if row["validates"] else 1
                    out.append(row)
            print(f"[{cid}|L={L}] simulated {len(m.K_LEVELS)*len(m.FRAME_INDICES)}"
                  f" rows", flush=True)

    rp = os.path.join(ROOT, "results", "value_flood_counterfactual.json")
    json.dump({"provenance": meas["provenance"],
               "prereg": "VISION_VALUE_FLOOD_PREREG.md",
               "validation_mismatches": mismatches, "rows": out},
              open(rp, "w"), indent=1)
    print(f"\n[validation] rows={len(out)} mismatched_vs_substrate={mismatches}",
          flush=True)
    if mismatches:
        print("SIMULATION DOES NOT REPRODUCE THE MECHANISM -- no claim made",
              flush=True)
        return
    print(f"[written] {rp}", flush=True)


if __name__ == "__main__":
    main()
