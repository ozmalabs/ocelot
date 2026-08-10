"""CONNECT PERCEPT TO IDENTITY — the confirmatory measurement.

`VISION_IDENTITY_SEAM_PREREG.md`, committed at `100945b1099f07f` (base
`212212e30b767466`). Runs exactly the pre-registered arms and clauses. No
sweeps, no re-runs, no metric chosen after looking.

The script is a RUNNER: it presents pixels, ticks, and reads attributes back.
Every identity decision is the graph's.
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

N_BASE = 100
N_REGIONS = 16
N_CALIB = 8
N_PROBE = 64
SEED_BLOCK = 72000

CORPORA = {
    "C1": {"episode_index": 0, "pin": "08630d4b7b215c469df19b9c42d7b617",
           "what": "cartoon"},
    "C2": {"episode_index": 3, "pin": "119eca433329b36b19e5d69fef84966e",
           "what": "live-action"},
}


def _vp():
    spec = iu.spec_from_file_location("vp", str(HERE / "video_probe_measure.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ci95(xs):
    """95% t-CI. Unit of analysis is whatever the caller aggregated to."""
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
    d = [a - b for a, b in zip(xs, ys) if a is not None and b is not None]
    return ci95(d)


def load_corpus(cid):
    vp = _vp()
    frames, meta = vp.jellyfin_frames(150, every=2, start_s=300, size=sw.GRID,
                                      episode_index=CORPORA[cid]["episode_index"])
    got = meta.get("episode_id")
    if got != CORPORA[cid]["pin"]:
        raise SystemExit(f"EPISODE PIN MISMATCH for {cid}: {got} != "
                         f"{CORPORA[cid]['pin']} — run is VOID (prereg section 2)")
    return frames, meta


def cut_flags(frames):
    """Otsu on the corpus's own per-step motion. No free parameter."""
    steps = [float(np.mean(np.abs(np.asarray(frames[t + 1], float)
                                  - np.asarray(frames[t], float))))
             for t in range(len(frames) - 1)]
    thr = sw.otsu(steps)
    return steps, thr, [s > thr for s in steps]


def run_arm(cid, arm, frames, log):
    """One (corpus, arm): the main trajectory, then the two probe passes."""
    q = [sw.quantize(f) for f in frames]
    qregs = [sw.regions_of(x) for x in q]
    gregs = [sw.grey_regions_of(f) for f in frames]

    rng = np.random.RandomState(SEED_BLOCK + CORPORA[cid]["episode_index"] * 100
                                + (0 if arm == "stock" else 1))
    w = sw.SeamWorld(arm)
    w.calibrate(rng, N_CALIB)
    w.run()

    t_start = time.time()
    main, traj = [], []
    for t in range(N_BASE):
        k_before = w.codebook_size()
        for i in range(N_REGIONS):
            t0 = time.time()
            w.present(qregs[t][i], gregs[t][i], tag=f"{t}_{i}")
            w.run()
            r = w.read_last()
            r.update(frame=t, region=i, ms=round((time.time() - t0) * 1000, 2),
                     K=w.codebook_size())
            main.append(r)
        traj.append({"frame": t, "minted": w.codebook_size() - k_before,
                     "K": w.codebook_size()})
        if t % 20 == 0:
            log(f"    [{cid}/{arm}] t={t:3d} K={w.codebook_size():4d} "
                f"elapsed={time.time()-t_start:6.1f}s")
        if time.time() - t_start > 20 * 60:
            log(f"    [{cid}/{arm}] ABORT RULE FIRED at t={t} "
                f"({time.time()-t_start:.0f}s) — partial trajectory reported")
            break
    main_ms = time.time() - t_start
    n_done = len(traj)
    ident = {(r["frame"], r["region"]): r["identity"] for r in main}
    k_after_main = w.codebook_size()

    # ---- CLAUSE 1 FLOOR: shuffled-frame -------------------------------
    frng = np.random.RandomState(SEED_BLOCK + 500 + CORPORA[cid]["episode_index"])
    floor_rows = []
    for t in range(n_done):
        cands = [u for u in range(n_done) if abs(u - t) > 5]
        if not cands:
            continue
        tp = int(frng.choice(cands))
        for i in range(N_REGIONS):
            w.present(qregs[tp][i], gregs[tp][i], tag=f"flr_{t}_{i}")
            w.run()
            r = w.read_last()
            floor_rows.append({"frame": t, "region": i, "from_frame": tp,
                               "identity": r["identity"],
                               "status": r["status"]})
    k_after_floor = w.codebook_size()

    # ---- CLAUSE 3: novelty probes + matched held control ---------------
    prng = np.random.RandomState(SEED_BLOCK + 700 + CORPORA[cid]["episode_index"])
    probes = []
    for j in range(N_PROBE):                       # BSDS: a different corpus
        probes.append(("BSDS", *_bsds_tile(j)))
    for j in range(N_PROBE):                       # NOISE
        probes.append(("NOISE",
                       prng.randint(0, sw.K_LEVELS, (sw.REGION, sw.REGION)),
                       prng.randint(0, 256, (sw.REGION, sw.REGION)).astype(float)))
    for j in range(N_PROBE):                       # SHUFFLE: multiset preserved
        t, i = int(prng.randint(0, n_done)), int(prng.randint(0, N_REGIONS))
        probes.append(("SHUFFLE",
                       sw.shuffle_arrangement(qregs[t][i], prng),
                       sw.shuffle_arrangement(gregs[t][i], prng)))
    for j in range(N_PROBE):                       # CONTROL: genuine held region
        t, i = int(prng.randint(0, n_done)), int(prng.randint(0, N_REGIONS))
        probes.append(("CONTROL", qregs[t][i], gregs[t][i]))

    probe_rows = []
    for j, (kind, qt, gt) in enumerate(probes):
        k_before = w.codebook_size()
        w.present(qt, gt, tag=f"pr_{kind}_{j}")
        w.run()
        r = w.read_last()
        minted = w.codebook_size() > k_before
        refused = (r["identity"] == "novel")
        probe_rows.append({"kind": kind, "status": r["status"],
                           "identity": r["identity"], "minted": minted,
                           "refused": refused,
                           "novel_handled": 1 if (minted or refused) else 0})

    return {"main": main, "traj": traj, "floor": floor_rows,
            "probes": probe_rows, "ident": {f"{k[0]}_{k[1]}": v
                                            for k, v in ident.items()},
            "n_frames_done": n_done, "main_ms": main_ms,
            "k_after_main": k_after_main, "k_after_floor": k_after_floor,
            "k_final": w.codebook_size()}


_BSDS_CACHE = []


def _bsds_tile(j):
    """Genuinely novel regions from a DIFFERENT corpus (BSDS300 photographs)."""
    global _BSDS_CACHE
    if not _BSDS_CACHE:
        from PIL import Image
        from domains import vision_corpus as vc
        for p in vc.bsds_paths("train")[:8]:
            g = np.asarray(Image.open(p).convert("L"), float)
            h, wd = g.shape
            crop = g[h // 2 - 60:h // 2 + 60, wd // 2 - 60:wd // 2 + 60]
            small = vc.area_downsample(crop / 255.0, sw.GRID) * 255.0
            for qt, gt in zip(sw.regions_of(sw.quantize(small)),
                              sw.grey_regions_of(small)):
                _BSDS_CACHE.append((qt, gt))
    return _BSDS_CACHE[j % len(_BSDS_CACHE)]


def analyse(cid, arm, res, frames, cuts, log):
    """The pre-registered decision rule, applied mechanically."""
    n = res["n_frames_done"]
    ident = {(int(k.split("_")[0]), int(k.split("_")[1])): v
             for k, v in res["ident"].items()}
    gregs = [sw.grey_regions_of(f) for f in frames]

    # ---- CLAUSE 1 -----------------------------------------------------
    floor_by = {(r["frame"], r["region"]): r["identity"] for r in res["floor"]}
    persist = {"noncut": [], "cut": []}
    floor = {"noncut": [], "cut": []}
    for t in range(n - 1):
        stratum = "cut" if cuts[t] else "noncut"
        p = [1.0 if ident.get((t + 1, i)) == ident.get((t, i)) else 0.0
             for i in range(N_REGIONS)]
        f = [1.0 if floor_by.get((t, i)) == ident.get((t, i)) else 0.0
             for i in range(N_REGIONS)]
        persist[stratum].append(float(np.mean(p)))
        floor[stratum].append(float(np.mean(f)))
    c1 = {s: {"persist": ci95(persist[s]), "floor": ci95(floor[s]),
              "paired": paired_ci95(persist[s], floor[s])}
          for s in ("noncut", "cut")}
    nc = c1["noncut"]["paired"]
    c1["PASS"] = bool(nc["lo"] is not None and nc["lo"] > 0)

    # ---- CLAUSE 2 -----------------------------------------------------
    diffs = []
    for t in range(n):
        for i in range(N_REGIONS):
            for j in range(i + 1, N_REGIONS):
                diffs.append(sw.mean_abs_diff(gregs[t][i], gregs[t][j]))
    med = float(np.median(diffs))
    coll = {"DIFFERENT": [], "SIMILAR": []}
    ndist = []
    for t in range(n):
        buckets = {"DIFFERENT": [], "SIMILAR": []}
        for i in range(N_REGIONS):
            for j in range(i + 1, N_REGIONS):
                b = ("DIFFERENT"
                     if sw.mean_abs_diff(gregs[t][i], gregs[t][j]) > med
                     else "SIMILAR")
                same = (ident.get((t, i)) is not None
                        and ident.get((t, i)) == ident.get((t, j)))
                buckets[b].append(1.0 if same else 0.0)
        for b in buckets:
            if buckets[b]:
                coll[b].append(float(np.mean(buckets[b])))
        ndist.append(len({ident.get((t, i)) for i in range(N_REGIONS)}
                         - {None}))
    c2 = {"median_pixdiff": med,
          "collapse_DIFFERENT": ci95(coll["DIFFERENT"]),
          "collapse_SIMILAR": ci95(coll["SIMILAR"]),
          "paired_DIFF_minus_SIM": paired_ci95(coll["DIFFERENT"],
                                               coll["SIMILAR"]),
          "n_distinct_per_frame": ci95([float(x) for x in ndist])}
    pd = c2["paired_DIFF_minus_SIM"]
    c2["PASS"] = bool(pd["hi"] is not None and pd["hi"] < 0)

    # ---- CLAUSE 3 -----------------------------------------------------
    by = {}
    for r in res["probes"]:
        by.setdefault(r["kind"], []).append(float(r["novel_handled"]))
    ctrl = by.get("CONTROL", [])
    c3 = {"CONTROL": ci95(ctrl)}
    passes = []
    for k in ("BSDS", "NOISE", "SHUFFLE"):
        c3[k] = ci95(by.get(k, []))
        # unpaired: probe classes are independent draws, not matched pairs
        a, b = c3[k], c3["CONTROL"]
        sep = (a["lo"] is not None and b["hi"] is not None
               and a["lo"] > b["hi"])
        c3[k + "_sep_above_control"] = bool(sep)
        passes.append(sep)
        c3[k + "_mint_rate"] = float(np.mean(
            [1.0 if r["minted"] else 0.0
             for r in res["probes"] if r["kind"] == k]))
        c3[k + "_refuse_rate"] = float(np.mean(
            [1.0 if r["refused"] else 0.0
             for r in res["probes"] if r["kind"] == k]))
    c3["PASS"] = bool(all(passes))

    verdict = {"clause1": c1, "clause2": c2, "clause3": c3,
               "CONJUNCTION_PASS": bool(c1["PASS"] and c2["PASS"]
                                        and c3["PASS"])}
    log(f"  [{cid}/{arm}] clause1 {c1['PASS']}  clause2 {c2['PASS']}  "
        f"clause3 {c3['PASS']}  => {verdict['CONJUNCTION_PASS']}")
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", default="C1,C2")
    ap.add_argument("--arms", default="stock,ncc")
    ap.add_argument("--out", default="results/identity_seam.json")
    a = ap.parse_args()

    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    log(ep.provenance_line())
    out = {"provenance": ep.provenance_line(), "corpora": {}}
    for cid in a.corpora.split(","):
        frames, meta = load_corpus(cid)
        steps, thr, cuts = cut_flags(frames)
        log(f"[{cid}] {meta.get('episode_id')} otsu={thr:.3f} "
            f"cuts={sum(cuts[:N_BASE])}/{N_BASE}")
        out["corpora"][cid] = {"meta": meta, "otsu": thr,
                               "motion_steps": steps[:N_BASE],
                               "n_cut": int(sum(cuts[:N_BASE])), "arms": {}}
        for arm in a.arms.split(","):
            t0 = time.time()
            res = run_arm(cid, arm, frames, log)
            res["verdict"] = analyse(cid, arm, res, frames, cuts, log)
            res["wall_s"] = round(time.time() - t0, 1)
            # Per-observation rows go to their own file -- a successor needs
            # them, and they are too bulky for the summary.
            rp = ROOT / f"results/identity_seam_rows_{cid}_{arm}.json"
            rp.write_text(json.dumps(res["main"], default=float))
            log(f"  [{cid}/{arm}] rows -> {rp.name} "
                f"({rp.stat().st_size//1024} KB)")
            del res["main"]
            out["corpora"][cid]["arms"][arm] = res
            log(f"  [{cid}/{arm}] K_final={res['k_final']} "
                f"wall={res['wall_s']}s")

    out["log"] = lines
    p = ROOT / a.out
    p.write_text(json.dumps(out, indent=1, default=float))
    log(f"wrote {p}")


if __name__ == "__main__":
    main()
