#!/usr/bin/env python3
"""CAN ANY GRAPH-RESIDENT COMPARATOR SURVIVE TRANSLATION? — confirmatory runner.

Pre-registration: `VISION_INVARIANT_COMPARATOR_PREREG.md`, committed BEFORE this
was run at `c5f34f29fd332eaaac1bf07a1e30e5e2f2b41fd7`. Exactly the arms, gates,
corpora, n and statistics declared there.

USAGE:
    PYTHONPATH=runners/dsl/python:. python scripts/invariant_comparator_measure.py c3
    PYTHONPATH=runners/dsl/python:. python scripts/invariant_comparator_measure.py video
    PYTHONPATH=runners/dsl/python:. python scripts/invariant_comparator_measure.py replay
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

import numpy as np                                    # noqa: E402
import importlib.util as _iu                          # noqa: E402

import domains.seed_registry                          # noqa: F401,E402
from domains import invariant_comparator_world as iw  # noqa: E402

_spec = _iu.spec_from_file_location(
    "video_probe_measure", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
vp = _iu.module_from_spec(_spec)
_spec.loader.exec_module(vp)

# --- pre-registered constants (§2, §3, §4 of the prereg) ------------------- #
SEED_BLOCK = 57000
N_PHOTOS = 24
N_BASE = 50
DISPLACEMENTS = (0, 1, 2, 3, 4, 6)
DIAG_DISPLACEMENTS = (0, 1, 2, 3)
DELTAS = (1, 5, 25)
N_REGIONS = 16
CHANCE = 1.0 / N_REGIONS
MIN_SHUFFLE_GAP = 30
#: (id, encoder, rho). Q0 == the incumbent comparator, exactly.
COMPARATORS = (("Q0", "cell", 0), ("Q1", "cell", 1), ("Q2", "cell", 2),
               ("Q3", "cell", 3), ("R", "registered", 0), ("H", "hist", 0))
VIDEO_COMPARATORS = ("Q0", "Q1", "Q2", "R", "H")     # §8: Q3 off video, on cost
DIAG_COMPARATORS = ("Q0", "Q2")                       # §4.1: declared secondary


# --- statistics, exactly as pre-registered (§4) ---------------------------- #
def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


#: t(0.975, df) for the two group sizes this rung uses. Declared, not looked up
#: at runtime, so the interval is auditable from the file.
T975 = {23: 2.0687, 49: 2.0096}


def t_ci(xs, df=None):
    """Mean with a 95% t-CI. The unit is the PHOTO (C3) or the BASE FRAME
    (video) -- never the trial (§4.1)."""
    n = len(xs)
    if n < 2:
        return (float(xs[0]) if xs else 0.0, 0.0, 0.0)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    t = T975.get(df if df is not None else n - 1, 1.984)
    h = t * sd / math.sqrt(n)
    return (m, m - h, m + h)


def norm_entropy(names, k=N_REGIONS):
    if not names:
        return 0.0
    counts = {}
    for x in names:
        counts[x] = counts.get(x, 0) + 1
    n = len(names)
    h = -sum((c / n) * math.log(c / n) for c in counts.values() if c)
    return h / math.log(k)


def sep(a, b):
    """Is interval a's lower bound strictly above interval b's upper bound?"""
    return a[1] > b[2]


# --- one world: one codebook, every probe that shares it ------------------- #
def run_cell(qbase_src, base_origins, qprobe_sources, rho, encoder, seed):
    """`qprobe_sources` is `[(tag_prefix, quantized_source, origin_offset,
    shuffle)]`. Every probe shares ONE codebook, so this is one substrate."""
    rng = random.Random(seed)
    codebook = [qbase_src[r:r + iw.REGION, c:c + iw.REGION]
                for r, c in base_origins]
    order = list(range(N_REGIONS))
    rng.shuffle(order)
    w = iw.InvComparatorWorld()
    w.hold(codebook, order, encoder=encoder)
    for prefix, qsrc, (dr, dc), shuffle in qprobe_sources:
        # Pad by rho + the probe's OWN displacement, not by rho. Padding by rho
        # alone leaves the trailing-edge windows silently truncated inside
        # `orbit_windows`. At (dr,dc)==(0,0) `pad` is exactly `rho`, so every
        # zero-displacement path is byte-unchanged; and the C3 path was never
        # truncated anyway because its source is the FULL photo, whose own
        # margin -- not this padding -- is what bounds the window (measured,
        # `VISION_APERTURE_FIX_RESULTS.md` H3).
        pad = rho + max(abs(dr), abs(dc))
        padded = iw.pad_edge(qsrc, pad)
        for i, (r0, c0) in enumerate(base_origins):
            orbit = iw.orbit_windows(padded, (r0 + dr, c0 + dc), rho, pad=pad)
            if shuffle:
                orbit = [(j, iw.shuffle_arrangement(t, rng)) for j, t in orbit]
            w.present(orbit, truth=i, tag=f"{prefix}|{i}")
    t0 = time.perf_counter()
    w.run()
    ms = (time.perf_counter() - t0) * 1000.0
    return w.read(), ms


# --- corpora --------------------------------------------------------------- #
def bsds_photos(n=N_PHOTOS):
    from domains.vision_corpus import bsds_paths
    from PIL import Image
    out, names = [], []
    for p in bsds_paths("train")[:n]:
        out.append(np.asarray(Image.open(p).convert("L"), np.float32))
        names.append(os.path.basename(p))
    return out, names


def load_video(cid):
    idx = 0 if cid == "C1" else 3
    fr, meta = vp.jellyfin_frames(150, every=2, start_s=300, size=iw.GRID,
                                  episode_index=idx)
    return [np.asarray(f, float) for f in fr], meta


# --- aggregation ----------------------------------------------------------- #
def summarise(rows, pred, unit_key, df):
    sel = [r for r in rows if pred(r)]
    if not sel:
        return None
    hits = sum(1 for r in sel if r["said_idx"] == r["truth"])
    p, lo, hi = wilson(hits, len(sel))
    per_unit = {}
    for r in sel:
        per_unit.setdefault(r[unit_key], []).append(r["said_idx"] == r["truth"])
    accs = [sum(v) / len(v) for v in per_unit.values()]
    um, ulo, uhi = t_ci(accs, df)
    return {
        "n_trials": len(sel), "n_units": len(per_unit),
        "unit_acc": um, "unit_lo": ulo, "unit_hi": uhi,
        "trial_acc": p, "wilson_lo": lo, "wilson_hi": hi,
        "answer_entropy": norm_entropy([r["said"] for r in sel]),
        "mean_ntied": float(np.mean([r["icg_ntied"] for r in sel])),
        "frac_tied_gt1": float(np.mean([r["icg_ntied"] > 1 for r in sel])),
        "score_agreement_with_R2": float(np.mean(
            [r["icg_max"] == r["nn_score"] for r in sel])),
        "argmax_agreement_with_R2": float(np.mean(
            [r["said_idx"] == r["nn_idx"] for r in sel])),
        "true_achieves_max": float(np.mean([bool(r["true_is_max"]) for r in sel])),
        "per_unit_acc": accs,
    }


def paired_margin(rows, unit_key, arm_pred, floor_pred, df):
    """`M` = accuracy(arm) - accuracy(floor), as a PAIRED per-unit difference
    with a 95% t-CI on the difference (§4.2)."""
    def per_unit(pred):
        d = {}
        for r in rows:
            if pred(r):
                d.setdefault(r[unit_key], []).append(r["said_idx"] == r["truth"])
        return {u: sum(v) / len(v) for u, v in d.items()}
    a, b = per_unit(arm_pred), per_unit(floor_pred)
    us = sorted(set(a) & set(b))
    if not us:
        return None
    diffs = [a[u] - b[u] for u in us]
    m, lo, hi = t_ci(diffs, df)
    return {"n_units": len(us), "margin": m, "lo": lo, "hi": hi,
            "excludes_zero": bool(lo > 0.0)}


def machine_state():
    try:
        ps = subprocess.run(["ps", "-eo", "pcpu,args", "--sort=-pcpu"],
                            capture_output=True, text=True, timeout=20).stdout
        top = [ln.strip()[:120] for ln in ps.strip().split("\n")[1:6]]
    except Exception:                                    # noqa: BLE001
        top = ["<ps unavailable>"]
    return {"loadavg": os.getloadavg(), "top_processes": top}


# --- C3: KNOWN DISPLACEMENT ------------------------------------------------ #
def run_c3(out):
    photos, names = bsds_photos()
    out["corpora"]["C3"] = {"source": "BSDS300", "n_photos": len(photos),
                            "files": names}
    rows_by_cmp = {}
    for cid, encoder, rho in COMPARATORS:
        rows, t0 = [], time.time()
        for pi, ph in enumerate(photos):
            q = iw.quantize(ph)
            h, w_ = q.shape
            ar, ac = (h - iw.GRID) // 2, (w_ - iw.GRID) // 2
            origins = [(ar + r, ac + c) for r, c in iw.region_origins()]
            noise = np.asarray(np.random.RandomState(
                SEED_BLOCK + 900 + pi).randint(0, iw.K_LEVELS, q.shape), int)
            probes = []
            for d in DISPLACEMENTS:
                probes.append((f"A1|axis|d{d}", q, (0, d), False))
                probes.append((f"A3|axis|d{d}", q, (0, d), True))
            if cid in DIAG_COMPARATORS:
                for d in DIAG_DISPLACEMENTS:
                    probes.append((f"A1|diag|d{d}", q, (d, d), False))
                    probes.append((f"A3|diag|d{d}", q, (d, d), True))
            probes.append(("G2|axis|d0", noise, (0, 0), False))
            r, _ms = run_cell(q, origins, probes, rho, encoder,
                              SEED_BLOCK + pi)
            for x in r:
                x["photo"] = pi
            rows.extend(r)
            if pi % 6 == 0:
                print(f"  [C3 {cid}] photo {pi}/{len(photos)} "
                      f"({time.time() - t0:.0f}s)", flush=True)
        rows_by_cmp[cid] = rows
        print(f"  [C3 {cid}] done ({time.time() - t0:.0f}s)", flush=True)

        cell = {}
        for mode, ds in (("axis", DISPLACEMENTS), ("diag", DIAG_DISPLACEMENTS)):
            if mode == "diag" and cid not in DIAG_COMPARATORS:
                continue
            for arm in ("A1", "A3"):
                for d in ds:
                    pre = f"{arm}|{mode}|d{d}|"
                    s = summarise(rows, lambda r, p=pre: r["tag"].startswith(p),
                                  "photo", 23)
                    if s:
                        cell[f"{arm}|{mode}|d{d}"] = s
            # THE TWO HEADLINE STATISTICS
            m = paired_margin(rows, "photo",
                              lambda r, m=mode: r["tag"].startswith(f"A1|{m}|d0|"),
                              lambda r, m=mode: r["tag"].startswith(f"A3|{m}|d0|"),
                              23)
            cell[f"MARGIN|{mode}"] = m
            horizon = None
            for d in ds:
                a = cell.get(f"A1|{mode}|d{d}")
                f = cell.get(f"A3|{mode}|d{d}")
                if not (a and f):
                    continue
                if sep((a["unit_acc"], a["unit_lo"], a["unit_hi"]),
                       (f["unit_acc"], f["unit_lo"], f["unit_hi"])):
                    horizon = d
                else:
                    break
            cell[f"HORIZON|{mode}"] = horizon
        cell["G2_noise"] = summarise(rows, lambda r: r["tag"].startswith("G2|"),
                                     "photo", 23)
        out["c3"][cid] = cell
        with open(os.path.join(ROOT, "results",
                               f"invariant_comparator_rows_C3_{cid}.json"), "w") as fh:
            json.dump(rows, fh)
    return rows_by_cmp


# --- C1 / C2: REAL MOTION -------------------------------------------------- #
def run_video(out, which):
    for cid in which:
        try:
            frames, meta = load_video(cid)
        except Exception as e:                            # noqa: BLE001
            out["corpora"][cid] = {"error": f"{type(e).__name__}: {e}"}
            print(f"[corpus {cid}] ABSENT: {e}", flush=True)
            continue
        out["corpora"][cid] = meta
        qs = [iw.quantize(f) for f in frames]
        origins = list(iw.region_origins())
        mm = [float(np.mean(np.abs(frames[t + 1] - frames[t])))
              for t in range(min(N_BASE, len(frames) - 1))]
        out["motion"][cid] = {"mean": float(np.mean(mm)), "sd": float(np.std(mm)),
                              "min": float(np.min(mm)), "max": float(np.max(mm))}
        out["video"][cid] = {}
        for name, encoder, rho in COMPARATORS:
            if name not in VIDEO_COMPARATORS:
                continue
            rows, t0 = [], time.time()
            for t in range(N_BASE):
                rng = random.Random(SEED_BLOCK + 400 + t)
                far = [u for u in range(len(qs)) if abs(u - t) >= MIN_SHUFFLE_GAP]
                probes = []
                for d in DELTAS:
                    tj = min(t + d, len(qs) - 1)
                    probes.append((f"A1|d{d}", qs[tj], (0, 0), False))
                    probes.append((f"A2|d{d}", qs[rng.choice(far)], (0, 0), False))
                    probes.append((f"A3|d{d}", qs[tj], (0, 0), True))
                probes.append(("G1|d0", qs[t], (0, 0), False))
                probes.append(("G2|d0", np.asarray(np.random.RandomState(
                    SEED_BLOCK + 700 + t).randint(0, iw.K_LEVELS, qs[t].shape),
                    int), (0, 0), False))
                r, _ms = run_cell(qs[t], origins, probes, rho, encoder,
                                  SEED_BLOCK + 200 + t)
                for x in r:
                    x["base"] = t
                rows.extend(r)
                if t % 10 == 0:
                    print(f"  [{cid} {name}] base {t}/{N_BASE} "
                          f"({time.time() - t0:.0f}s)", flush=True)
            print(f"  [{cid} {name}] done ({time.time() - t0:.0f}s)", flush=True)
            cell = {}
            for arm in ("A1", "A2", "A3"):
                for d in DELTAS:
                    pre = f"{arm}|d{d}|"
                    s = summarise(rows, lambda r, p=pre: r["tag"].startswith(p),
                                  "base", 49)
                    if s:
                        cell[f"{arm}|d{d}"] = s
            for g in ("G1", "G2"):
                cell[g] = summarise(rows, lambda r, g=g: r["tag"].startswith(g + "|"),
                                    "base", 49)
            cell["MARGIN|d1"] = paired_margin(
                rows, "base", lambda r: r["tag"].startswith("A1|d1|"),
                lambda r: r["tag"].startswith("A3|d1|"), 49)
            horizon = None
            for d in DELTAS:
                a, f2, f3 = (cell.get(f"A1|d{d}"), cell.get(f"A2|d{d}"),
                             cell.get(f"A3|d{d}"))
                if not (a and f2 and f3):
                    continue
                ai = (a["unit_acc"], a["unit_lo"], a["unit_hi"])
                if (sep(ai, (f2["unit_acc"], f2["unit_lo"], f2["unit_hi"]))
                        and sep(ai, (f3["unit_acc"], f3["unit_lo"], f3["unit_hi"]))):
                    horizon = d
                else:
                    break
            cell["HORIZON|delta"] = horizon
            out["video"][cid][name] = cell
            with open(os.path.join(ROOT, "results",
                                   f"invariant_comparator_rows_{cid}_{name}.json"), "w") as fh:
                json.dump(rows, fh)


# --- the replay determinism check (§8: the incumbent's §4.2 risk) ---------- #
def run_replay(out):
    """Re-run a fixed C3 subset in THIS fresh process and compare answer-for-
    answer with the confirmatory rows. The incumbent found 272 rows that did not
    reproduce; a value read once from a non-deterministic evaluator is a coin
    flip, and the discipline that catches it is replay."""
    photos, _ = bsds_photos(4)
    diffs, n = 0, 0
    for cid, encoder, rho in COMPARATORS:
        try:
            with open(os.path.join(ROOT, "results",
                                   f"invariant_comparator_rows_C3_{cid}.json")) as fh:
                orig = json.load(fh)
        except FileNotFoundError:
            continue
        by_key = {(r["photo"], r["tag"]): r for r in orig}
        for pi, ph in enumerate(photos):
            q = iw.quantize(ph)
            h, w_ = q.shape
            ar, ac = (h - iw.GRID) // 2, (w_ - iw.GRID) // 2
            origins = [(ar + r, ac + c) for r, c in iw.region_origins()]
            noise = np.asarray(np.random.RandomState(
                SEED_BLOCK + 900 + pi).randint(0, iw.K_LEVELS, q.shape), int)
            probes = []
            for d in DISPLACEMENTS:
                probes.append((f"A1|axis|d{d}", q, (0, d), False))
                probes.append((f"A3|axis|d{d}", q, (0, d), True))
            if cid in DIAG_COMPARATORS:
                for d in DIAG_DISPLACEMENTS:
                    probes.append((f"A1|diag|d{d}", q, (d, d), False))
                    probes.append((f"A3|diag|d{d}", q, (d, d), True))
            probes.append(("G2|axis|d0", noise, (0, 0), False))
            r, _ = run_cell(q, origins, probes, rho, encoder, SEED_BLOCK + pi)
            for x in r:
                o = by_key.get((pi, x["tag"]))
                if o is None:
                    continue
                n += 1
                if o["said"] != x["said"] or o["icg_max"] != x["icg_max"]:
                    diffs += 1
    out["replay"] = {"n_compared": n, "n_disagreeing": diffs,
                     "deterministic": bool(diffs == 0)}
    print(f"[replay] {n} rows compared, {diffs} disagree", flush=True)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    path = os.path.join(ROOT, "results", f"invariant_comparator_{what}.json")
    prov = provenance_line()
    out = {"provenance": prov,
           "prereg": "VISION_INVARIANT_COMPARATOR_PREREG.md",
           "prereg_commit": "c5f34f29fd332eaaac1bf07a1e30e5e2f2b41fd7",
           "machine_state_at_start": machine_state(),
           "constants": {"seed_block": SEED_BLOCK, "n_photos": N_PHOTOS,
                         "n_base": N_BASE, "displacements": list(DISPLACEMENTS),
                         "diag_displacements": list(DIAG_DISPLACEMENTS),
                         "deltas": list(DELTAS), "n_regions": N_REGIONS,
                         "chance": CHANCE, "k_levels": iw.K_LEVELS,
                         "region": iw.REGION, "grid": iw.GRID,
                         "comparators": [list(c) for c in COMPARATORS],
                         "video_comparators": list(VIDEO_COMPARATORS),
                         "diag_comparators": list(DIAG_COMPARATORS)},
           "corpora": {}, "c3": {}, "video": {}, "motion": {}}
    print(f"[provenance] {prov}", flush=True)
    print(f"[machine] {out['machine_state_at_start']['loadavg']}", flush=True)
    if what in ("c3", "all"):
        run_c3(out)
    if what in ("video", "all"):
        run_video(out, ("C1", "C2"))
    if what == "c1":
        run_video(out, ("C1",))
    if what == "c2":
        run_video(out, ("C2",))
    if what == "replay":
        run_replay(out)
    out["machine_state_at_end"] = machine_state()
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {path}", flush=True)


if __name__ == "__main__":
    main()
