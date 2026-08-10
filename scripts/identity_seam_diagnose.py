"""POST-HOC DIAGNOSTICS for the identity seam. NOT pre-registered.

The confirmatory run (`identity_seam_measure.py`) is untouched and its verdict
stands. This script diagnoses TWO things it exposed:

D1. **THE CODEBOOK WAS CONTAMINATED BEFORE CLAUSE 3 RAN.** The pre-registered
    pass order was main -> clause-1 floor -> clause-3 probes, all in ONE
    substrate. The floor pass presents 1,600 distant-frame regions, which MINT.
    So clause 3 was measured against a codebook several times larger than the
    one clause 1 was measured against. D1 re-runs clause 3 with the probes
    presented IMMEDIATELY after the main pass, and reports both numbers.
    **This does not revise the pre-registered verdict** (protocol section 5) --
    it says what the verdict was measured on.

D2. **DOES THE MEASURED FLOOR RISE WITH K, AND DOES IT EAT GENUINE
    RECOGNITIONS?** The confirmatory run showed 12.5% of GENUINE re-presented
    held regions being minted as novel. If the floor rises with codebook size,
    the seam gets progressively less able to recognise what it already holds --
    a scaling property of the measured-floor construction, not a bug in a rule.

D3. Are the mint BURSTS aligned with the scene cuts?
"""
from __future__ import annotations

import argparse
import importlib.util as iu
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

import numpy as np  # noqa: E402

from domains import identity_seam_world as sw  # noqa: E402

import importlib  # noqa: E402
msr = importlib.import_module("scripts.identity_seam_measure") \
    if (HERE / "__init__.py").exists() else None
if msr is None:
    spec = iu.spec_from_file_location("msr", str(HERE / "identity_seam_measure.py"))
    msr = iu.module_from_spec(spec)
    spec.loader.exec_module(msr)


def d1_clean_clause3(cid, arm, frames, cuts):
    """Clause 3, with the probe pass FIRST — no floor-pass contamination."""
    q = [sw.quantize(f) for f in frames]
    qregs = [sw.regions_of(x) for x in q]
    gregs = [sw.grey_regions_of(f) for f in frames]

    rng = np.random.RandomState(
        msr.SEED_BLOCK + msr.CORPORA[cid]["episode_index"] * 100
        + (0 if arm == "stock" else 1))
    w = sw.SeamWorld(arm)
    w.calibrate(rng, msr.N_CALIB)
    w.run()

    floors_by_k = []
    for t in range(msr.N_BASE):
        for i in range(msr.N_REGIONS):
            w.present(qregs[t][i], gregs[t][i], tag=f"{t}_{i}")
            w.run()
            r = w.read_last()
            if r["is_floor"] is not None:
                floors_by_k.append((w.codebook_size(), float(r["is_floor"])))
    k_main = w.codebook_size()

    prng = np.random.RandomState(msr.SEED_BLOCK + 700
                                 + msr.CORPORA[cid]["episode_index"])
    probes = []
    for j in range(msr.N_PROBE):
        probes.append(("BSDS", *msr._bsds_tile(j)))
    for j in range(msr.N_PROBE):
        probes.append(("NOISE",
                       prng.randint(0, sw.K_LEVELS, (sw.REGION, sw.REGION)),
                       prng.randint(0, 256, (sw.REGION, sw.REGION)).astype(float)))
    for j in range(msr.N_PROBE):
        t, i = int(prng.randint(0, msr.N_BASE)), int(prng.randint(0, msr.N_REGIONS))
        probes.append(("SHUFFLE", sw.shuffle_arrangement(qregs[t][i], prng),
                       sw.shuffle_arrangement(gregs[t][i], prng)))
    for j in range(msr.N_PROBE):
        t, i = int(prng.randint(0, msr.N_BASE)), int(prng.randint(0, msr.N_REGIONS))
        probes.append(("CONTROL", qregs[t][i], gregs[t][i]))

    rows = []
    for j, (kind, qt, gt) in enumerate(probes):
        k0 = w.codebook_size()
        w.present(qt, gt, tag=f"pr_{kind}_{j}")
        w.run()
        r = w.read_last()
        rows.append({"kind": kind, "minted": w.codebook_size() > k0,
                     "refused": r["identity"] == "novel",
                     "is_max": r["is_max"], "is_floor": r["is_floor"],
                     "K": k0})

    by = {}
    for r in rows:
        by.setdefault(r["kind"], []).append(
            1.0 if (r["minted"] or r["refused"]) else 0.0)
    out = {"k_at_clause3": k_main, "n_probes": len(rows),
           "floors_by_k": floors_by_k[::40]}
    for k in ("BSDS", "NOISE", "SHUFFLE", "CONTROL"):
        out[k] = msr.ci95(by.get(k, []))
    for k in ("BSDS", "NOISE", "SHUFFLE"):
        a, b = out[k], out["CONTROL"]
        out[k + "_sep_above_control"] = bool(
            a["lo"] is not None and b["hi"] is not None and a["lo"] > b["hi"])
    return out, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", default="C1,C2")
    ap.add_argument("--arms", default="stock,ncc")
    ap.add_argument("--out", default="results/identity_seam_diagnose.json")
    a = ap.parse_args()
    print(ep.provenance_line(), flush=True)
    out = {"provenance": ep.provenance_line(), "corpora": {}}
    for cid in a.corpora.split(","):
        frames, meta = msr.load_corpus(cid)
        steps, thr, cuts = msr.cut_flags(frames)
        # D3: are the mint bursts aligned with the cuts?
        conf = json.loads((ROOT / f"results/identity_seam_{cid}.json").read_text())
        d3 = {}
        for arm in a.arms.split(","):
            tr = conf["corpora"][cid]["arms"][arm]["traj"]
            m = np.array([t["minted"] for t in tr], float)
            cut_at = np.array([1.0 if cuts[t] else 0.0
                               for t in range(len(tr))], float)
            # mints in the 3 frames following a cut, vs base rate
            near = np.zeros(len(tr))
            for t in range(len(tr)):
                if any(cuts[u] for u in range(max(0, t - 3), t + 1)):
                    near[t] = 1.0
            d3[arm] = {
                "mints_near_cut": float(m[near > 0].sum()),
                "frames_near_cut": int((near > 0).sum()),
                "mints_far": float(m[near == 0].sum()),
                "frames_far": int((near == 0).sum()),
                "rate_near": float(m[near > 0].mean()) if (near > 0).any() else None,
                "rate_far": float(m[near == 0].mean()) if (near == 0).any() else None,
            }
        out["corpora"][cid] = {"D3_mint_vs_cut": d3, "arms": {}}
        for arm in a.arms.split(","):
            t0 = time.time()
            d1, rows = d1_clean_clause3(cid, arm, frames, cuts)
            d1["wall_s"] = round(time.time() - t0, 1)
            out["corpora"][cid]["arms"][arm] = d1
            print(f"[{cid}/{arm}] D1 clean clause3 @K={d1['k_at_clause3']}: "
                  f"BSDS {d1['BSDS']['mean']:.3f} NOISE {d1['NOISE']['mean']:.3f} "
                  f"SHUFFLE {d1['SHUFFLE']['mean']:.3f} "
                  f"CONTROL {d1['CONTROL']['mean']:.3f}", flush=True)
    (ROOT / a.out).write_text(json.dumps(out, indent=1, default=float))
    print("wrote", ROOT / a.out)


if __name__ == "__main__":
    main()
