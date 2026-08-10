#!/usr/bin/env python3
"""CROSS-FRAME IDENTITY ON REAL PIXELS — the confirmatory runner.

Pre-registration: `VISION_CROSSFRAME_IDENTITY_PREREG.md`, committed BEFORE this
was run. Exactly the arms, gates, corpora, n and statistics declared there.

USAGE:
    PYTHONPATH=runners/dsl/python:. python scripts/crossframe_identity_measure.py
"""
from __future__ import annotations

import json
import math
import os
import random
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np                              # noqa: E402
import importlib.util as _iu                    # noqa: E402

import domains.seed_registry                    # noqa: F401,E402
from domains import crossframe_world as cw      # noqa: E402

_spec = _iu.spec_from_file_location(
    "video_probe_measure", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
vp = _iu.module_from_spec(_spec)
_spec.loader.exec_module(vp)

# --- pre-registered constants (§2, §5, §8 of the prereg) ------------------- #
SEED_BLOCK = 55000
N_BASE = 100
DELTAS = (1, 2, 5, 10, 25)
K_HEADLINE = 4
K_SENSITIVITY = (2, 8)
N_REGIONS = 16
CHANCE = 1.0 / N_REGIONS
MIN_SHUFFLE_GAP = 30
DISPLACEMENTS = (0, 1, 2, 3, 4, 6, 8)
N_BSDS = 12
G5_BASE_FRAMES = 30


# --- statistics, exactly as pre-registered (§7) ---------------------------- #
def wilson(k, n, z=1.959963984540054):
    """95% Wilson interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def t_ci(xs):
    """Mean with a 95% t-CI. n>=30 here, so the normal quantile is used for the
    t quantile -- declared, and the difference at n=100 is under 2%."""
    n = len(xs)
    if n < 2:
        return (float(xs[0]) if xs else 0.0, 0.0, 0.0)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    h = 1.984 * sd / math.sqrt(n)          # t(0.975, df=99)
    return (m, m - h, m + h)


def norm_entropy(names, k=N_REGIONS):
    """G3: normalized entropy of the answer distribution. A dead arm that always
    returns one name scores 0.0 while still sitting at chance accuracy."""
    if not names:
        return 0.0
    counts = {}
    for x in names:
        counts[x] = counts.get(x, 0) + 1
    n = len(names)
    h = -sum((c / n) * math.log(c / n) for c in counts.values() if c)
    return h / math.log(k)


def overlaps(a, b):
    """Do two (lo, hi) intervals overlap?"""
    return not (a[1] > b[2] or b[1] > a[2])


# --- corpora (§2) ---------------------------------------------------------- #
def load_corpus(cid):
    if cid == "C1":
        fr, meta = vp.jellyfin_frames(150, every=2, start_s=300, size=cw.GRID,
                                      episode_index=0)
    elif cid == "C2":
        fr, meta = vp.jellyfin_frames(150, every=2, start_s=300, size=cw.GRID,
                                      episode_index=3)
    else:
        raise ValueError(cid)
    return [np.asarray(f, float) for f in fr], meta


def bsds_photos(n=N_BSDS):
    from domains.vision_corpus import bsds_paths
    from PIL import Image
    out, names = [], []
    for p in bsds_paths("train")[:n]:
        out.append(np.asarray(Image.open(p).convert("L"), np.float32))
        names.append(os.path.basename(p))
    return out, names


# --- one base frame: every probe the design asks of it --------------------- #
def run_base_frame(frames, t, k, *, want_deltas, want_gates, seed):
    """Ingest one codebook and every probe that shares it, tick ONCE, read back.
    All arms share the codebook, so this is one substrate per (base frame, k)."""
    rng = random.Random(seed)
    q_base = cw.quantize(frames[t], k)
    tiles = cw.regions_of(q_base)
    order = list(range(N_REGIONS))
    rng.shuffle(order)

    w = cw.CrossFrameWorld()
    w.hold_codebook(tiles, order)

    n_frames = len(frames)
    for d in want_deltas:
        tj = min(t + d, n_frames - 1)
        probe_tiles = cw.regions_of(cw.quantize(frames[tj], k))
        # A2's distant frame: uniform over indices at least MIN_SHUFFLE_GAP away.
        far = [u for u in range(n_frames) if abs(u - t) >= MIN_SHUFFLE_GAP]
        shuf_tiles = cw.regions_of(cw.quantize(frames[rng.choice(far)], k))
        for i in range(N_REGIONS):
            w.present(probe_tiles[i], truth=i, tag=f"A1|d{d}|{i}")
            w.present(shuf_tiles[i], truth=i, tag=f"A2|d{d}|{i}")
            w.present(cw.shuffle_arrangement(probe_tiles[i], rng),
                      truth=i, tag=f"A3|d{d}|{i}")
    if want_gates:
        for i in range(N_REGIONS):
            w.present(tiles[i], truth=i, tag=f"G1|d0|{i}")
            w.present(cw.uniform_noise_tile(rng, k), truth=i, tag=f"G2|noise|{i}")

    t0 = time.perf_counter()
    w.run()
    ms = (time.perf_counter() - t0) * 1000.0
    rows = w.read()
    for r in rows:
        r["base"] = t
        r["k"] = k
    return rows, ms


def run_g5(frames, t, k, seed):
    """G5: A1 at delta=1 under a SECOND, independent codebook insertion order."""
    rng = random.Random(seed)
    tiles = cw.regions_of(cw.quantize(frames[t], k))
    order = list(range(N_REGIONS))
    rng.shuffle(order)
    w = cw.CrossFrameWorld()
    w.hold_codebook(tiles, order)
    probe = cw.regions_of(cw.quantize(frames[min(t + 1, len(frames) - 1)], k))
    for i in range(N_REGIONS):
        w.present(probe[i], truth=i, tag=f"G5|d1|{i}")
    w.run()
    rows = w.read()
    for r in rows:
        r["base"] = t
        r["k"] = k
    return rows


def run_aperture(photo, d, seed, k=K_HEADLINE):
    """C3: a 24x24 window over a real photograph, translated by a KNOWN d.

    A1  -- the same aperture position after the camera moved by d;
    A1c -- the aperture MOTION-COMPENSATED to the shifted position (the same
           content), the ceiling / positive control at each d;
    A3  -- arrangement-destroyed floor on the A1 probe."""
    rng = random.Random(seed)
    h, w_ = photo.shape
    r0, c0 = (h - cw.GRID) // 2, (w_ - cw.GRID) // 2
    base = photo[r0:r0 + cw.GRID, c0:c0 + cw.GRID]
    moved = photo[r0:r0 + cw.GRID, c0 + d:c0 + d + cw.GRID]

    tiles = cw.regions_of(cw.quantize(base, k))
    order = list(range(N_REGIONS))
    rng.shuffle(order)
    world = cw.CrossFrameWorld()
    world.hold_codebook(tiles, order)

    a1 = cw.regions_of(cw.quantize(moved, k))
    # A1c: undo the known shift -- literally the same content, re-quantized.
    comp = photo[r0:r0 + cw.GRID, c0:c0 + cw.GRID]
    a1c = cw.regions_of(cw.quantize(comp, k))
    for i in range(N_REGIONS):
        world.present(a1[i], truth=i, tag=f"A1|d{d}|{i}")
        world.present(a1c[i], truth=i, tag=f"A1c|d{d}|{i}")
        world.present(cw.shuffle_arrangement(a1[i], rng), truth=i, tag=f"A3|d{d}|{i}")
    world.run()
    rows = world.read()
    for r in rows:
        r["d"] = d
    return rows


# --- aggregation ----------------------------------------------------------- #
def summarise(rows, arm, delta=None, k=None):
    sel = [r for r in rows
           if r["tag"].split("|")[0] == arm
           and (delta is None or r["tag"].split("|")[1] == f"d{delta}")
           and (k is None or r["k"] == k)]
    if not sel:
        return None
    hits = sum(1 for r in sel if r["said_idx"] == r["truth"])
    p, lo, hi = wilson(hits, len(sel))
    per_frame = {}
    for r in sel:
        per_frame.setdefault(r["base"], []).append(r["said_idx"] == r["truth"])
    fr_acc = [sum(v) / len(v) for v in per_frame.values()]
    fm, flo, fhi = t_ci(fr_acc)
    ties = [r["xf_ntied"] for r in sel if r["xf_ntied"] is not None]
    nn_agree = sum(1 for r in sel if r["said_idx"] == r["nn_idx"])
    score_agree = sum(1 for r in sel if r["xf_max"] == r["nn_score"])
    untied = [r for r in sel if r["xf_ntied"] == 1 and r["nn_ties"] == 1]
    untied_agree = sum(1 for r in untied if r["said_idx"] == r["nn_idx"])
    return {
        "arm": arm, "delta": delta, "k": k, "n_trials": len(sel),
        "n_base_frames": len(per_frame),
        "trial_acc": p, "wilson_lo": lo, "wilson_hi": hi,
        "frame_acc": fm, "frame_lo": flo, "frame_hi": fhi,
        "mean_ntied": (sum(ties) / len(ties)) if ties else None,
        "frac_tied_gt1": (sum(1 for x in ties if x > 1) / len(ties)) if ties else None,
        "answer_entropy": norm_entropy([r["said"] for r in sel]),
        "nn_agreement": nn_agree / len(sel),
        "nn_score_agreement": score_agree / len(sel),
        "nn_agreement_untied": (untied_agree / len(untied)) if untied else None,
        "n_untied": len(untied),
        # POST-HOC DIAGNOSTIC, labelled as such: the rate at which the TRUE
        # region achieves the maximum score at all. Strict top-1 (the
        # pre-registered statistic) is this MINUS the trials lost to an
        # arbitrary tie-break, so this is an UPPER bound on each arm and the
        # A1-A3 margin computed from strict top-1 is an OVER-estimate of the
        # arrangement effect whenever A3 ties more than A1. Reported so the
        # bias is visible and signed, never to replace the pre-registered number.
        "true_achieves_max_upper_bound": (
            sum(1 for r in sel if r.get("true_is_max")) / len(sel)),
    }


def main():
    global N_BASE, G5_BASE_FRAMES, N_BSDS
    smoke = "--smoke" in sys.argv
    if smoke:
        # A WIRING CHECK ONLY. It writes to a different path and its numbers are
        # never reported: n is a third of the pre-registered power (§3.3).
        N_BASE, G5_BASE_FRAMES, N_BSDS = 3, 2, 2
    prov = provenance_line()
    load = os.getloadavg()
    try:
        ps = subprocess.run(["ps", "-eo", "pcpu,args", "--sort=-pcpu"],
                            capture_output=True, text=True, timeout=20).stdout
        top = [ln.strip()[:140] for ln in ps.strip().split("\n")[1:6]]
    except Exception:                                    # noqa: BLE001
        top = ["<ps unavailable>"]
    out = {"provenance": prov, "prereg": "VISION_CROSSFRAME_IDENTITY_PREREG.md",
           "machine_state_at_start": {"loadavg": load, "top_processes": top},
           "constants": {"n_base": N_BASE, "deltas": list(DELTAS),
                         "k_headline": K_HEADLINE, "k_sensitivity": list(K_SENSITIVITY),
                         "n_regions": N_REGIONS, "chance": CHANCE,
                         "min_shuffle_gap": MIN_SHUFFLE_GAP,
                         "seed_block": SEED_BLOCK, "grid": cw.GRID,
                         "region": cw.REGION},
           "corpora": {}, "arms": {}, "gates": {}, "aperture": {}, "motion": {}}
    print(f"[provenance] {prov}", flush=True)
    print(f"[machine] loadavg={load}", flush=True)

    for cid in ("C1", "C2"):
        try:
            frames, meta = load_corpus(cid)
        except Exception as e:                            # noqa: BLE001
            out["corpora"][cid] = {"error": f"{type(e).__name__}: {e}"}
            print(f"[corpus {cid}] ABSENT: {e}", flush=True)
            continue
        out["corpora"][cid] = meta
        print(f"[corpus {cid}] {meta.get('series')} — {len(frames)} frames", flush=True)

        # motion magnitude per base frame (so shot cuts are visible, not averaged)
        mm = [float(np.mean(np.abs(frames[t + 1] - frames[t])))
              for t in range(min(N_BASE, len(frames) - 1))]
        out["motion"][cid] = {"mean_abs_diff_d1": {
            "mean": float(np.mean(mm)), "sd": float(np.std(mm)),
            "min": float(np.min(mm)), "max": float(np.max(mm)),
            "per_base": [round(x, 3) for x in mm]}}

        rows, msg = [], []
        t0 = time.time()
        for t in range(N_BASE):
            r, ms = run_base_frame(frames, t, K_HEADLINE,
                                   want_deltas=DELTAS, want_gates=True,
                                   seed=SEED_BLOCK + t)
            rows.extend(r)
            msg.append(ms)
            if t % 20 == 0:
                print(f"  [{cid} k={K_HEADLINE}] base {t}/{N_BASE} "
                      f"({time.time() - t0:.0f}s)", flush=True)
        for ks in K_SENSITIVITY:
            for t in range(N_BASE):
                r, _ = run_base_frame(frames, t, ks, want_deltas=(1,),
                                      want_gates=False, seed=SEED_BLOCK + 300 + t)
                rows.extend(r)
            print(f"  [{cid} k={ks}] sensitivity done ({time.time() - t0:.0f}s)",
                  flush=True)
        g5 = []
        for t in range(G5_BASE_FRAMES):
            g5.extend(run_g5(frames, t, K_HEADLINE, SEED_BLOCK + 600 + t))
        rows.extend(g5)

        out["arms"][cid] = {}
        for arm in ("A1", "A2", "A3"):
            for d in DELTAS:
                s = summarise(rows, arm, d, K_HEADLINE)
                if s:
                    out["arms"][cid][f"{arm}|k4|d{d}"] = s
            for ks in K_SENSITIVITY:
                s = summarise(rows, arm, 1, ks)
                if s:
                    out["arms"][cid][f"{arm}|k{ks}|d1"] = s
        out["gates"][cid] = {
            "G1_ceiling": summarise(rows, "G1", 0, K_HEADLINE),
            "G2_noise": summarise([r for r in rows if r["tag"].startswith("G2")],
                                  "G2", None, K_HEADLINE),
            "G5_order": summarise(rows, "G5", 1, K_HEADLINE),
            "run_ms_per_base_frame": {"mean": float(np.mean(msg)),
                                      "sd": float(np.std(msg))},
        }
        with open(os.path.join(ROOT, "results",
                               ("crossframe_identity_SMOKE_rows_%s.json" % cid) if smoke else f"crossframe_identity_rows_{cid}.json"), "w") as fh:
            json.dump(rows, fh)

    # --- C3: known displacement over real photographs --------------------- #
    try:
        photos, names = bsds_photos(N_BSDS)
    except Exception as e:                                # noqa: BLE001
        out["aperture"] = {"error": f"{type(e).__name__}: {e}"}
        photos = []
    if photos:
        out["corpora"]["C3"] = {"source": "BSDS300", "n_photos": len(photos),
                                "files": names}
        arows = []
        for pi, ph in enumerate(photos):
            for d in DISPLACEMENTS:
                arows.extend(run_aperture(ph, d, SEED_BLOCK + 800 + pi * 10 + d))
        for arm in ("A1", "A1c", "A3"):
            for d in DISPLACEMENTS:
                sel = [r for r in arows
                       if r["tag"].startswith(arm + "|") and r["d"] == d]
                hits = sum(1 for r in sel if r["said_idx"] == r["truth"])
                p, lo, hi = wilson(hits, len(sel))
                out["aperture"][f"{arm}|d{d}"] = {
                    "n": len(sel), "acc": p, "wilson_lo": lo, "wilson_hi": hi,
                    "answer_entropy": norm_entropy([r["said"] for r in sel]),
                    "mean_ntied": float(np.mean([r["xf_ntied"] for r in sel])),
                    "nn_agreement": sum(1 for r in sel
                                        if r["said_idx"] == r["nn_idx"]) / len(sel)}
        print("[C3] aperture done", flush=True)

    # --- the pre-registered decision rule (§9), applied mechanically ------- #
    verdicts = {}
    for cid, arms in out["arms"].items():
        a1 = arms.get("A1|k4|d1")
        a2 = arms.get("A2|k4|d1")
        a3 = arms.get("A3|k4|d1")
        if not (a1 and a2 and a3):
            continue
        f1 = (a1["frame_acc"], a1["frame_lo"], a1["frame_hi"])
        f2 = (a2["frame_acc"], a2["frame_lo"], a2["frame_hi"])
        f3 = (a3["frame_acc"], a3["frame_lo"], a3["frame_hi"])
        w1 = (a1["trial_acc"], a1["wilson_lo"], a1["wilson_hi"])
        w2 = (a2["trial_acc"], a2["wilson_lo"], a2["wilson_hi"])
        w3 = (a3["trial_acc"], a3["wilson_lo"], a3["wilson_hi"])
        prim = (f1[1] > f2[2] and f1[1] > f3[2] and f1[1] > CHANCE)
        sec = (w1[1] > w2[2] and w1[1] > w3[2] and w1[1] > CHANCE)
        # H2: the identity horizon -- largest delta where A1 stays separated.
        horizon = None
        for d in DELTAS:
            x1, x2, x3 = (arms.get(f"A1|k4|d{d}"), arms.get(f"A2|k4|d{d}"),
                          arms.get(f"A3|k4|d{d}"))
            if not (x1 and x2 and x3):
                continue
            ok = (x1["frame_lo"] > x2["frame_hi"] and x1["frame_lo"] > x3["frame_hi"])
            if ok:
                horizon = d
            else:
                break
        verdicts[cid] = {
            "H1_primary_frame_level": "CROSSES" if prim else "NULL",
            "H1_secondary_trial_level_wilson": "CROSSES" if sec else "NULL",
            "H1_governing": "CROSSES" if prim else "NULL",
            "agree": prim == sec,
            "H2_identity_horizon_delta": horizon,
        }
    out["verdicts"] = verdicts
    out["machine_state_at_end"] = {"loadavg": os.getloadavg()}

    p = os.path.join(ROOT, "results",
                     "crossframe_identity_SMOKE.json" if smoke else "crossframe_identity.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {p}", flush=True)
    print(json.dumps(verdicts, indent=1), flush=True)


if __name__ == "__main__":
    main()
