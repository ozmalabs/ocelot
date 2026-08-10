"""VIDEO ACCUMULATION — THE CONFIRMATORY MEASUREMENT.

`VISION_VIDEO_ACCUMULATION_PREREG.md`, committed at `f9ec8971` (base
`5428104a`). Runs exactly the pre-registered arms. No sweeps, no re-runs, no
metric chosen after looking.

The script is a RUNNER: it presents pixels, ticks, and reads attributes back.
Every identity decision is `seeds/vision_identity_seam.json`'s.
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

N_FRAMES = 150
N_REGIONS = 16
N_CALIB = 8
N_PROBE = 64
CHECKPOINTS = [10, 25, 45, 65, 90]
CUT_WINDOW = 3                     # inherited from the seam rung, declared
SEED = 74000

CORPORA = {
    "C1": {"episode_index": 0, "pin": "08630d4b7b215c469df19b9c42d7b617",
           "what": "cartoon", "ci": 0},
    "C2": {"episode_index": 3, "pin": "119eca433329b36b19e5d69fef84966e",
           "what": "live-action", "ci": 1},
}


def _mod(name):
    spec = iu.spec_from_file_location(name, str(HERE / f"{name}.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ci95(xs):
    a = np.asarray([x for x in xs if x is not None], float)
    n = a.size
    if n < 2:
        return {"n": int(n), "mean": float(a.mean()) if n else None,
                "lo": None, "hi": None}
    from scipy import stats
    m, se = float(a.mean()), float(a.std(ddof=1) / np.sqrt(n))
    t = float(stats.t.ppf(0.975, n - 1))
    return {"n": int(n), "mean": m, "lo": m - t * se, "hi": m + t * se,
            "sd": float(a.std(ddof=1))}


def paired_ci95(xs, ys):
    return ci95([a - b for a, b in zip(xs, ys)
                 if a is not None and b is not None])


def sep_above(a, b):
    return bool(a["lo"] is not None and b["hi"] is not None
                and a["lo"] > b["hi"])


# ------------------------------------------------------------------ growth
def grow(order, qr, gr, seed, log, label):
    """Present training frames in `order`. Every mint is the graph's."""
    w = aw.AccumWorld("ncc")
    w.calibrate(np.random.RandomState(seed), N_CALIB)
    w.run()
    t0 = time.time()
    mints, traj = [], []
    for n, t in enumerate(order):
        k0 = w.codebook_size()
        for i in range(N_REGIONS):
            kk = w.codebook_size()
            w.present(qr[t][i], gr[t][i], tag=f"{t}_{i}")
            w.run()
            if w.codebook_size() > kk:
                mints.append({"frame": int(t), "region": int(i),
                              "n_train": int(n + 1)})
        traj.append({"n_train": n + 1, "frame": int(t),
                     "minted": w.codebook_size() - k0,
                     "K": w.codebook_size()})
    log(f"    grow[{label}]: {len(order)} frames -> K={w.codebook_size()} "
        f"({time.time()-t0:.1f}s)")
    return mints, traj, w.codebook_size()


# -------------------------------------------------------------- evaluation
def eval_pass(entries, qr, gr, held, seed):
    """A frozen evaluation pass over the held-out frames."""
    w = aw.AccumWorld("ncc")
    w.calibrate(np.random.RandomState(seed), N_CALIB)
    w.run()
    w.install_codebook(entries)
    w.freeze()
    acc_rows, max_rows, usage, hist = [], [], {}, {}
    for t in held:
        a, m = [], []
        for i in range(N_REGIONS):
            w.present(qr[t][i], gr[t][i], tag=f"ev_{t}_{i}")
            w.run()
            r = w.read_full()
            w.refreeze()
            hist[r["status"]] = hist.get(r["status"], 0) + 1
            held_ok = (r["status"] == "is_held")
            a.append(1.0 if held_ok else 0.0)
            m.append(float(r["is_max"]))
            if held_ok:
                usage[r["identity"]] = usage.get(r["identity"], 0) + 1
        acc_rows.append(float(np.mean(a)))
        max_rows.append(float(np.mean(m)))
    k, f = w.assert_frozen()
    return {"K": k, "floor": f, "status_hist": hist, "usage": usage,
            "acc_rows": acc_rows, "max_rows": max_rows,
            "accept": float(np.mean(acc_rows)),
            "mean_is_max": float(np.mean(max_rows))}


def probe_pass(entries, qr, gr, train, seed, bsds):
    """Section 3.6 refusal probes, in the frozen GROWN world."""
    w = aw.AccumWorld("ncc")
    w.calibrate(np.random.RandomState(seed), N_CALIB)
    w.run()
    w.install_codebook(entries)
    w.freeze()
    prng = np.random.RandomState(seed + 1)
    probes = []
    for j in range(N_PROBE):
        probes.append(("BSDS", *bsds(j)))
    for j in range(N_PROBE):
        probes.append(("NOISE",
                       prng.randint(0, aw.K_LEVELS, (aw.REGION, aw.REGION)),
                       prng.randint(0, 256,
                                    (aw.REGION, aw.REGION)).astype(float)))
    for j in range(N_PROBE):
        t = int(train[prng.randint(0, len(train))])
        i = int(prng.randint(0, N_REGIONS))
        probes.append(("SHUFFLE",
                       aw.shuffle_arrangement(qr[t][i], prng),
                       aw.shuffle_arrangement(gr[t][i], prng)))
    for j in range(N_PROBE):
        t = int(train[prng.randint(0, len(train))])
        i = int(prng.randint(0, N_REGIONS))
        probes.append(("CONTROL", qr[t][i], gr[t][i]))

    rows = []
    for j, (kind, qt, gt) in enumerate(probes):
        w.present(qt, gt, tag=f"pr_{kind}_{j}")
        w.run()
        r = w.read_full()
        w.refreeze()
        rows.append({"kind": kind, "status": r["status"],
                     "novel_handled": 1.0
                     if r["status"] in ("is_novel", "is_minted") else 0.0})
    w.assert_frozen()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", default="C1,C2")
    ap.add_argument("--out", default="results/video_accum.json")
    a = ap.parse_args()

    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    log(ep.provenance_line())
    seam = _mod("identity_seam_measure")
    vp = _mod("video_probe_measure")

    train, held = aw.block_split(N_FRAMES)
    assert not (set(train) & set(held)) and len(train) == 90 and len(held) == 50
    log(f"split: train={len(train)} held={len(held)}")

    out = {"provenance": ep.provenance_line(), "prereg": "f9ec8971",
           "train": train, "held": held, "checkpoints": CHECKPOINTS,
           "corpora": {}}

    for cid in a.corpora.split(","):
        C = CORPORA[cid]
        frames, meta = vp.jellyfin_frames(N_FRAMES, every=2, start_s=300,
                                          size=aw.GRID,
                                          episode_index=C["episode_index"])
        if meta.get("episode_id") != C["pin"]:
            raise SystemExit(f"EPISODE PIN MISMATCH {cid}: {meta.get('episode_id')}"
                             f" != {C['pin']} — run is VOID")
        steps, thr, cuts = aw.cut_flags(frames)
        cut_at = [t for t, c in enumerate(cuts) if c]
        log(f"[{cid}] {meta['episode_id']} otsu={thr:.4f} cuts={cut_at}")

        q = [aw.quantize(f) for f in frames]
        qr = [aw.regions_of(x) for x in q]
        gr = [aw.grey_regions_of(f) for f in frames]
        ci = C["ci"]

        R = {"meta": meta, "otsu": thr, "cut_steps": cut_at,
             "motion_steps": steps}

        # ---- GROWTH, in order ----------------------------------------
        mints, traj, K = grow(train, qr, gr, SEED + ci, log, f"{cid}/order")
        R["mints"], R["traj"], R["K_final"] = mints, traj, K

        # ---- GROWTH, shuffled order (section 3.5) --------------------
        sh = list(train)
        np.random.RandomState(SEED + 300 + ci).shuffle(sh)
        smints, straj, sK = grow(sh, qr, gr, SEED + ci, log, f"{cid}/shuffled")
        R["shuffled"] = {"order": [int(x) for x in sh], "mints": smints,
                         "traj": straj, "K_final": sK}

        # ---- CHECKPOINTS ---------------------------------------------
        uni_rng = np.random.RandomState(SEED + 100 + ci)
        cut_rng = np.random.RandomState(SEED + 200 + ci)
        R["checkpoints"] = {}
        for cp in CHECKPOINTS:
            sel = [m for m in mints if m["n_train"] <= cp]
            Kc = len(sel)
            if Kc == 0:
                log(f"  [{cid}] cp={cp}: K=0, skipped")
                continue
            pool = [(t, i) for t in train[:cp] for i in range(N_REGIONS)]
            pick = uni_rng.choice(len(pool), size=Kc, replace=False)
            arms = {
                "GROWN": [(f"{m['frame']}_{m['region']}",
                           qr[m["frame"]][m["region"]],
                           gr[m["frame"]][m["region"]]) for m in sel],
                "RAND_UNIFORM": [(f"ru{j}_{pool[p][0]}_{pool[p][1]}",
                                  qr[pool[p][0]][pool[p][1]],
                                  gr[pool[p][0]][pool[p][1]])
                                 for j, p in enumerate(pick)],
                "RAND_CUTMATCHED": [],
            }
            for j, m in enumerate(sel):
                i2 = int(cut_rng.randint(0, N_REGIONS))
                arms["RAND_CUTMATCHED"].append(
                    (f"cm{j}_{m['frame']}_{i2}",
                     qr[m["frame"]][i2], gr[m["frame"]][i2]))

            cpres = {"K": Kc, "arms": {}}
            for an, ents in arms.items():
                t0 = time.time()
                r = eval_pass(ents, qr, gr, held, SEED + 400 + ci)
                r["wall_s"] = round(time.time() - t0, 1)
                cpres["arms"][an] = r
                log(f"  [{cid}] cp={cp:3d} K={Kc:3d} {an:16s} "
                    f"accept={r['accept']:.4f} is_max={r['mean_is_max']:.4f} "
                    f"floor={r['floor']:.4f} ({r['wall_s']}s)")
            # paired contrasts vs the size-matched control
            g, u, c = (cpres["arms"]["GROWN"], cpres["arms"]["RAND_UNIFORM"],
                       cpres["arms"]["RAND_CUTMATCHED"])
            cpres["contrast"] = {
                "is_max_GROWN_minus_UNIFORM":
                    paired_ci95(g["max_rows"], u["max_rows"]),
                "is_max_GROWN_minus_CUTMATCHED":
                    paired_ci95(g["max_rows"], c["max_rows"]),
                "is_max_CUTMATCHED_minus_UNIFORM":
                    paired_ci95(c["max_rows"], u["max_rows"]),
                "accept_GROWN_minus_UNIFORM":
                    paired_ci95(g["acc_rows"], u["acc_rows"]),
                "accept_GROWN_minus_CUTMATCHED":
                    paired_ci95(g["acc_rows"], c["acc_rows"]),
            }
            R["checkpoints"][str(cp)] = cpres

        # ---- shuffled-order arm, evaluated at the final checkpoint ----
        sents = [(f"{m['frame']}_{m['region']}_s{j}",
                  qr[m["frame"]][m["region"]], gr[m["frame"]][m["region"]])
                 for j, m in enumerate(smints)]
        R["shuffled"]["eval"] = eval_pass(sents, qr, gr, held, SEED + 400 + ci)
        log(f"  [{cid}] SHUFFLED-ORDER K={sK} "
            f"accept={R['shuffled']['eval']['accept']:.4f} "
            f"is_max={R['shuffled']['eval']['mean_is_max']:.4f}")

        # ---- GATE 2: mint rate, first vs last training quartile -------
        qn = len(traj) // 4
        q1 = [t["minted"] for t in traj[:qn]]
        q4 = [t["minted"] for t in traj[-qn:]]
        R["mint_rate"] = {"Q1": ci95([float(x) for x in q1]),
                          "Q4": ci95([float(x) for x in q4]),
                          "declines": None}
        R["mint_rate"]["declines"] = sep_above(R["mint_rate"]["Q1"],
                                               R["mint_rate"]["Q4"])
        log(f"  [{cid}] mint/frame Q1={R['mint_rate']['Q1']['mean']:.4f} "
            f"Q4={R['mint_rate']['Q4']['mean']:.4f} "
            f"declines={R['mint_rate']['declines']}")

        # ---- GATE 3: refusal at the final checkpoint ------------------
        final = str(CHECKPOINTS[-1])
        gents = [(f"{m['frame']}_{m['region']}", qr[m["frame"]][m["region"]],
                  gr[m["frame"]][m["region"]]) for m in mints]
        prows = probe_pass(gents, qr, gr, train, SEED + 500 + ci,
                           seam._bsds_tile)
        by = {}
        for r in prows:
            by.setdefault(r["kind"], []).append(r["novel_handled"])
        ref = {k: ci95(v) for k, v in by.items()}
        for k in ("BSDS", "NOISE", "SHUFFLE"):
            ref[k + "_sep_above_control"] = sep_above(ref[k], ref["CONTROL"])
        ref["PASS"] = bool(ref["NOISE_sep_above_control"]
                           and ref["SHUFFLE_sep_above_control"])
        R["refusal"] = ref
        R["probe_rows"] = prows
        log(f"  [{cid}] refusal CONTROL={ref['CONTROL']['mean']:.4f} "
            f"BSDS={ref['BSDS']['mean']:.4f} NOISE={ref['NOISE']['mean']:.4f} "
            f"SHUFFLE={ref['SHUFFLE']['mean']:.4f} PASS={ref['PASS']}")

        # ---- CUT STRATIFICATION (section 3.4) -------------------------
        usage = R["checkpoints"][final]["arms"]["GROWN"]["usage"]
        ent = []
        for m in mints:
            nm = f"{m['frame']}_{m['region']}"
            d = aw.dist_to_cut(m["frame"], cuts)
            ent.append({"name": nm, "frame": m["frame"],
                        "region": m["region"], "dist_to_cut": d,
                        "usage": int(usage.get(nm, 0)),
                        "dead": 1.0 if usage.get(nm, 0) == 0 else 0.0,
                        "near_cut": None if d is None
                        else bool(d <= CUT_WINDOW)})
        near = [e for e in ent if e["near_cut"] is True]
        far = [e for e in ent if e["near_cut"] is False]
        R["entries"] = ent
        R["cut_strat"] = {
            "W": CUT_WINDOW,
            "n_near": len(near), "n_far": len(far),
            "dead_near": ci95([e["dead"] for e in near]),
            "dead_far": ci95([e["dead"] for e in far]),
            "usage_near": ci95([float(e["usage"]) for e in near]),
            "usage_far": ci95([float(e["usage"]) for e in far]),
            "usage_vs_dist": [[e["dist_to_cut"], e["usage"]] for e in ent],
        }
        log(f"  [{cid}] cut-strat near={len(near)} far={len(far)} "
            f"dead_near={R['cut_strat']['dead_near']['mean']} "
            f"dead_far={R['cut_strat']['dead_far']['mean']} "
            f"usage_near={R['cut_strat']['usage_near']['mean']} "
            f"usage_far={R['cut_strat']['usage_far']['mean']}")

        # ---- GATE 1 --------------------------------------------------
        fc = R["checkpoints"][final]["contrast"]
        d = fc["is_max_GROWN_minus_UNIFORM"]
        R["GATE1_is_max_grown_beats_sizematched"] = bool(
            d["lo"] is not None and d["lo"] > 0)
        R["GATE2_mint_rate_declines"] = R["mint_rate"]["declines"]
        R["GATE3_refusal_survives"] = ref["PASS"]
        R["CONJUNCTION"] = bool(R["GATE1_is_max_grown_beats_sizematched"]
                                and R["GATE2_mint_rate_declines"]
                                and R["GATE3_refusal_survives"])
        log(f"  [{cid}] GATE1={R['GATE1_is_max_grown_beats_sizematched']} "
            f"GATE2={R['GATE2_mint_rate_declines']} "
            f"GATE3={R['GATE3_refusal_survives']} "
            f"=> CONJUNCTION={R['CONJUNCTION']}")

        # rows are bulky; a successor needs them
        rp = ROOT / f"results/video_accum_rows_{cid}.json"
        rows = {cp: {an: {"acc_rows": v["acc_rows"], "max_rows": v["max_rows"],
                          "usage": v["usage"], "status_hist": v["status_hist"]}
                     for an, v in R["checkpoints"][cp]["arms"].items()}
                for cp in R["checkpoints"]}
        rp.write_text(json.dumps(rows, default=float))
        log(f"  [{cid}] rows -> {rp.name} ({rp.stat().st_size//1024} KB)")
        out["corpora"][cid] = R

    out["log"] = lines
    p = ROOT / a.out
    p.write_text(json.dumps(out, indent=1, default=float))
    log(f"wrote {p}")


if __name__ == "__main__":
    main()
