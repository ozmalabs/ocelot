"""CUT-MINT POLICY — THE CONFIRMATORY MEASUREMENT.

`VISION_CUT_MINT_POLICY_PREREG.md`, committed at `9c0ac19d` (base `17cb3f3d`).
Runs exactly the pre-registered arms. No sweeps, no re-runs, no metric chosen
after looking.

The script is a RUNNER: it presents pixels, ticks, and reads attributes back.
Which steps are cuts is `seeds/vision_cut_abstention.json`'s decision; which
observations are novel is `seeds/vision_identity_seam.json`'s; whether to
decline the mint is `seeds/vision_cut_mint_policy.json`'s.

THE EVALUATION PATH IS THE INCUMBENT'S, IMPORTED RATHER THAN RE-WRITTEN:
`video_accum_measure.eval_pass` is called verbatim, so the UNIFORM arm here is
directly comparable to the accumulation rung's published one.
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

from domains import video_accumulation_world as aw  # noqa: E402
from domains.cut_mint_world import CutMintWorld  # noqa: E402

N_FRAMES = 150
N_REGIONS = 16
N_CALIB = 8
SEED = 75000

CORPORA = {
    "C1": {"episode_index": 0, "pin": "08630d4b7b215c469df19b9c42d7b617",
           "ci": 0, "reference_cuts": [34, 47, 79]},
    "C2": {"episode_index": 3, "pin": "119eca433329b36b19e5d69fef84966e",
           "ci": 1, "reference_cuts": [23, 85, 143]},
}


def _mod(name):
    spec = iu.spec_from_file_location(name, str(HERE / f"{name}.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------- growth
def grow(policy, order, frames, qr, gr, seed, log, label):
    """Present the training frames. Every mint AND every abstention is the
    graph's; this loop only presents and reads."""
    w = CutMintWorld(policy=policy)
    w.calibrate(np.random.RandomState(seed), N_CALIB)
    w.run()
    t0 = time.time()
    w.hold_sequence(frames)
    log(f"    [{label}] steps={len(frames)-1} thr={w.cut_threshold()} "
        f"marked={w.marked_steps()} ({time.time()-t0:.1f}s)")
    t0, mints = time.time(), []
    for n, t in enumerate(order):
        for i in range(N_REGIONS):
            k = w.codebook_size()
            w.present_at(qr[t][i], gr[t][i], tag=f"{t}_{i}", frame=int(t))
            w.run()
            if w.codebook_size() > k:
                mints.append({"frame": int(t), "region": int(i),
                              "n_train": int(n + 1)})
    log(f"    [{label}] {len(order)} frames -> K={w.codebook_size()} "
        f"abstentions={len(w.abstentions())} ({time.time()-t0:.1f}s)")
    return w, mints


# ----------------------------------------------------- numpy value pricing
def _nv(qt, gt):
    from domains.identity_seam_world import encode
    return np.asarray(encode(qt, gt)["nvals"], float)


def price_entries(entry_keys, qr, gr, held, targets):
    """LEAVE-ONE-OUT VALUE, in numpy, OUTSIDE the graph.

    `entry_keys` is the full codebook as (frame, region); `targets` the subset
    to price. For each target: how many held-out observations' best-match NCC
    FALLS when it is removed, and by how much. This is the incumbent rung's D2
    re-derivation method, which reproduced the graph's own mean to six
    decimals.
    """
    book = np.stack([_nv(qr[f][i], gr[f][i]) for f, i in entry_keys])
    obs = np.stack([_nv(qr[t][i], gr[t][i])
                    for t in held for i in range(N_REGIONS)])
    sims = obs @ book.T                       # (n_obs, K)
    best = sims.max(axis=1)
    out = []
    for f, i in targets:
        j = entry_keys.index((f, i))
        keep = [c for c in range(len(entry_keys)) if c != j]
        b2 = sims[:, keep].max(axis=1)
        drop = best - b2
        hit = drop > 0
        out.append({"frame": int(f), "region": int(i),
                    "n_obs_improved": int(hit.sum()),
                    "n_obs": int(obs.shape[0]),
                    "mean_drop": float(drop.mean()),
                    "mean_drop_where_hit": float(drop[hit].mean())
                    if hit.any() else 0.0,
                    "max_drop": float(drop.max()),
                    "n_argmax": int((sims.argmax(axis=1) == j).sum())})
    return out


def longest_cutfree_run(train, cuts):
    """The longest contiguous run of TRAINING frames containing no reference
    cut step. Arm 4's population, computed mechanically."""
    banned = {f for c in cuts for f in (c, c + 1)}
    best, cur = [], []
    for t in sorted(train):
        if t in banned or (cur and t != cur[-1] + 1):
            cur = [] if t in banned else [t]
        else:
            cur.append(t)
        if len(cur) > len(best):
            best = list(cur)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", default="C1,C2")
    ap.add_argument("--out", default="results/cut_mint.json")
    a = ap.parse_args()

    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    log(ep.provenance_line())
    vam = _mod("video_accum_measure")
    vp = _mod("video_probe_measure")

    train, held = aw.block_split(N_FRAMES)
    assert not (set(train) & set(held)) and len(train) == 90 and len(held) == 50
    log(f"split: train={len(train)} held={len(held)}")

    incumbent = json.loads((ROOT / "results/video_accum.json").read_text())

    out = {"provenance": ep.provenance_line(), "prereg": "9c0ac19d",
           "train": train, "held": held, "corpora": {}}

    for cid in a.corpora.split(","):
        C = CORPORA[cid]
        frames, meta = vp.jellyfin_frames(N_FRAMES, every=2, start_s=300,
                                          size=aw.GRID,
                                          episode_index=C["episode_index"])
        if meta.get("episode_id") != C["pin"]:
            raise SystemExit(f"EPISODE PIN MISMATCH {cid}: "
                             f"{meta.get('episode_id')} != {C['pin']} — VOID")
        q = [aw.quantize(f) for f in frames]
        qr = [aw.regions_of(x) for x in q]
        gr = [aw.grey_regions_of(f) for f in frames]
        ci = C["ci"]
        R = {"meta": meta, "reference_cuts": C["reference_cuts"]}

        # ---- GROWTH, both policies, identical calibration seed ------------
        wa, amints = grow(True, train, frames, qr, gr, SEED + ci, log,
                          f"{cid}/ABSTAIN")
        wn, nmints = grow(False, train, frames, qr, gr, SEED + ci, log,
                          f"{cid}/NOABSTAIN")
        K_a, K_n = len(amints), len(nmints)
        R["K_abstain"], R["K_noabstain"] = K_a, K_n
        R["mints_abstain"], R["mints_noabstain"] = amints, nmints
        R["marked_steps"] = wa.marked_steps()
        R["graph_threshold"] = wa.cut_threshold()
        R["step_mags"] = wa.step_mags()
        R["abstentions"] = wa.abstentions()

        # the DISARMED arm must reproduce the incumbent's committed growth
        inc = [(m["frame"], m["region"])
               for m in incumbent["corpora"][cid]["mints"]]
        got = [(m["frame"], m["region"]) for m in nmints]
        R["reproduces_incumbent_growth"] = bool(inc == got)
        log(f"  [{cid}] K_abstain={K_a} K_noabstain={K_n} "
            f"reproduces_incumbent={R['reproduces_incumbent_growth']}")

        # ---- ARMS, ALL AT K = K_a -----------------------------------------
        uni_rng = np.random.RandomState(SEED + 100 + ci)
        sub_rng = np.random.RandomState(SEED + 200 + ci)
        pool = [(t, i) for t in train for i in range(N_REGIONS)]
        pick = uni_rng.choice(len(pool), size=K_a, replace=False)
        sub = sorted(sub_rng.choice(K_n, size=K_a, replace=False).tolist())

        def ents(keys, pfx):
            return [(f"{pfx}{j}_{f}_{i}", qr[f][i], gr[f][i])
                    for j, (f, i) in enumerate(keys)]

        akeys = [(m["frame"], m["region"]) for m in amints]
        nkeys = [(m["frame"], m["region"]) for m in nmints]
        arms = {
            "ABSTAIN": ents(akeys, "ab"),
            "NOABSTAIN_SUB": ents([nkeys[j] for j in sub], "ns"),
            "NOABSTAIN_PRE": ents(nkeys[:K_a], "np"),
            "UNIFORM": ents([pool[p] for p in pick], "ru"),
        }
        R["arm_keys"] = {k: [list(x) for x in
                             (akeys if k == "ABSTAIN" else
                              [nkeys[j] for j in sub] if k == "NOABSTAIN_SUB"
                              else nkeys[:K_a] if k == "NOABSTAIN_PRE"
                              else [pool[p] for p in pick])]
                         for k in arms}
        R["arms"] = {}
        for an, e in arms.items():
            t0 = time.time()
            r = vam.eval_pass(e, qr, gr, held, SEED + 400 + ci)
            r["wall_s"] = round(time.time() - t0, 1)
            R["arms"][an] = r
            log(f"  [{cid}] K={K_a:3d} {an:14s} accept={r['accept']:.4f} "
                f"is_max={r['mean_is_max']:.4f} floor={r['floor']:.4f} "
                f"({r['wall_s']}s)")

        A, S, P, U = (R["arms"]["ABSTAIN"], R["arms"]["NOABSTAIN_SUB"],
                      R["arms"]["NOABSTAIN_PRE"], R["arms"]["UNIFORM"])
        R["contrast"] = {
            "C_A_ABSTAIN_minus_UNIFORM":
                vam.paired_ci95(A["max_rows"], U["max_rows"]),
            "C_B_ABSTAIN_minus_NOABSTAIN_SUB":
                vam.paired_ci95(A["max_rows"], S["max_rows"]),
            "C_C_NOABSTAIN_SUB_minus_UNIFORM":
                vam.paired_ci95(S["max_rows"], U["max_rows"]),
            "C_D_ABSTAIN_minus_NOABSTAIN_PRE":
                vam.paired_ci95(A["max_rows"], P["max_rows"]),
            "accept_ABSTAIN_minus_UNIFORM":
                vam.paired_ci95(A["acc_rows"], U["acc_rows"]),
            "accept_ABSTAIN_minus_NOABSTAIN_SUB":
                vam.paired_ci95(A["acc_rows"], S["acc_rows"]),
        }
        for k, v in R["contrast"].items():
            log(f"  [{cid}] {k:38s} {v['mean']:+.4f} "
                f"[{v['lo']:+.4f}, {v['hi']:+.4f}]")

        # ---- FALSE-POSITIVE COST (prereg section 6) ------------------------
        marked = set(wa.marked_steps())
        ref = set(C["reference_cuts"])
        prevented = sorted(set(nkeys) - set(akeys))
        R["fp"] = {
            "marked_steps": sorted(marked),
            "false_positive_steps": sorted(marked - ref),
            "missed_reference_steps": sorted(ref - marked),
            "n_prevented_mints": len(prevented),
            "prevented_mints": [list(x) for x in prevented],
            "prevented_frames": sorted({f for f, _ in prevented}),
        }
        if prevented:
            R["fp"]["prevented_value"] = price_entries(nkeys, qr, gr, held,
                                                       prevented)
        log(f"  [{cid}] marked={sorted(marked)} FP={sorted(marked-ref)} "
            f"prevented={len(prevented)} at frames "
            f"{R['fp']['prevented_frames']}")

        # counterfactual: the marker on a cut-free run of TRAINING frames
        run = longest_cutfree_run(train, C["reference_cuts"])
        wf = CutMintWorld(policy=True)
        wf.hold_sequence([frames[t] for t in run])
        fm = wf.marked_steps()
        vetoed = sorted({(m["frame"], m["region"]) for m in nmints
                         if m["frame"] in
                         {run[s] for s in fm} | {run[s + 1] for s in fm}})
        R["fp"]["cutfree"] = {
            "frames": run, "n_steps": len(run) - 1,
            "marked": fm, "threshold": wf.cut_threshold(),
            "mags": wf.step_mags(),
            "would_veto_mints": [list(x) for x in vetoed],
        }
        log(f"  [{cid}] cut-free run {run[0]}..{run[-1]} "
            f"({len(run)-1} steps): marked {len(fm)} -> would veto "
            f"{len(vetoed)} incumbent mints")
        out["corpora"][cid] = R

    out["log"] = lines
    p = ROOT / a.out
    p.write_text(json.dumps(out, indent=1, default=float))
    log(f"wrote {p}")


if __name__ == "__main__":
    main()
