#!/usr/bin/env python3
"""HOLD THE PROPOSAL FIXED, VARY ONLY THE VERDICT — the runner.

Pre-registration: `VISION_VERDICT_PREREG.md`. Exactly the arms, corpora, n and
statistics declared there.

USAGE:
    PYTHONPATH=runners/dsl/python:. python scripts/verdict_comparator_measure.py pilot
    PYTHONPATH=runners/dsl/python:. python scripts/verdict_comparator_measure.py c3
    PYTHONPATH=runners/dsl/python:. python scripts/verdict_comparator_measure.py video
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

from domains import verdict_comparator_world as vw    # noqa: E402

_spec = _iu.spec_from_file_location(
    "video_probe_measure", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
vp = _iu.module_from_spec(_spec)
_spec.loader.exec_module(vp)

# --- pre-registered constants ---------------------------------------------- #
SEED_BLOCK = 70000
#: The PILOT uses the invariant-comparator rung's ALREADY-BURNED block, per
#: protocol section 3.3 (a power pilot must not consume confirmatory seeds).
PILOT_SEED_BLOCK = 57000
N_PHOTOS = 24
N_BASE = 50
N_PILOT_BASE = 10
#: C3 displacements. The tie mechanism the gate's clause 2 is about lives at
#: d=0 (`true_achieves_max` = 1.0000 there, so ALL loss is tie-break); d=1,2
#: check that a new verdict does not destroy the held horizon. The full 0..6
#: sweep measured HORIZON, which is the proposal layer and is NOT varied here.
DISPLACEMENTS = (0, 1, 2)
DELTAS = (1, 5, 25)
N_REGIONS = 16
CHANCE = 1.0 / N_REGIONS
MIN_SHUFFLE_GAP = 30
T975 = {9: 2.2622, 23: 2.0687, 49: 2.0096}


def t_ci(xs, df=None):
    """Mean with a 95% t-CI. The unit is the PHOTO (C3) or the BASE FRAME
    (video) -- never the trial. Held identical to the incumbent's."""
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


# --- THE CUT RULE: Otsu, which has NO free parameter ------------------------ #
def otsu_threshold(xs):
    """The threshold that maximises between-class variance on a 1-D sample.

    WHY OTSU AND NOT A PERCENTILE (protocol section 13): a percentile is a
    number chosen by me; Otsu's threshold is DETERMINED BY THE DATA'S OWN
    BIMODALITY and has no free parameter at all. The invariant-comparator rung
    measured both corpora as heavy-tailed -- "near-static steps punctuated by
    shot cuts" -- and `VISION_SALIENCE_RESCORE_RESULTS.md` section 4 found
    per-frame error count tracks per-frame motion at r = +0.968..+0.993 with
    100% of C1's short-delta errors in the top-10% motion frames. So the split
    this rung needs is exactly the split the data already has, and Otsu finds it
    without being told where it is.

    Returns `(threshold, n_low, n_high, mean_low, mean_high)`. The caller
    REPORTS the split; nothing here decides what to do with it."""
    a = sorted(float(x) for x in xs)
    n = len(a)
    if n < 2:
        return (float("inf"), n, 0, (a[0] if a else 0.0), 0.0)
    best, best_t = -1.0, a[0]
    total = sum(a)
    csum, ccnt = 0.0, 0
    for i in range(n - 1):
        csum += a[i]
        ccnt += 1
        if a[i + 1] == a[i]:
            continue
        w0 = ccnt / n
        w1 = 1.0 - w0
        m0 = csum / ccnt
        m1 = (total - csum) / (n - ccnt)
        v = w0 * w1 * (m0 - m1) ** 2
        if v > best:
            best, best_t = v, 0.5 * (a[i] + a[i + 1])
    lo = [x for x in a if x <= best_t]
    hi = [x for x in a if x > best_t]
    return (best_t, len(lo), len(hi),
            (sum(lo) / len(lo) if lo else 0.0),
            (sum(hi) / len(hi) if hi else 0.0))


# --- one world: one codebook, one verdict, every probe that shares it ------- #
def run_cell(verdict, qbase, gbase, base_origins, probes, seed):
    """`probes` is `[(tag_prefix, kind, qsrc, gsrc, origin_offset, shuffle)]`.
    Every probe shares ONE codebook, so this is ONE substrate.

    THE CANDIDATE SET IS BUILT HERE AND IS INDEPENDENT OF `verdict` -- the
    orbit geometry, the codebook tiles and the seeded insertion order are all
    functions of the arguments only. That is what "hold the proposal fixed"
    means operationally, and `check_proposal_identity` asserts it."""
    rng = random.Random(seed)
    codebook = [(qbase[r:r + vw.REGION, c:c + vw.REGION],
                 gbase[r:r + vw.REGION, c:c + vw.REGION])
                for r, c in base_origins]
    order = list(range(N_REGIONS))
    rng.shuffle(order)
    w = vw.VerdictWorld(verdict)
    w.hold(codebook, order)
    for prefix, kind, qsrc, gsrc, (dr, dc), shuffle in probes:
        # Pad by rho + the probe's own displacement, NOT by rho. Padding by rho
        # alone silently TRUNCATES the trailing-edge apertures at d>0 -- see
        # `orbit_windows`. At (dr,dc)==(0,0) this is exactly rho, so every
        # zero-displacement path (all of C1/C2) is byte-unchanged.
        pad = vw.RHO + max(abs(dr), abs(dc))
        qpad = vw.pad_edge(qsrc, pad)
        gpad = vw.pad_edge(gsrc, pad)
        for i, (r0, c0) in enumerate(base_origins):
            orbit = vw.orbit_windows(qpad, gpad, (r0 + dr, c0 + dc), vw.RHO,
                                     pad=pad)
            if shuffle:
                orbit = [(j, vw.shuffle_arrangement(q, rng),
                          vw.shuffle_arrangement(g, rng)) for j, q, g in orbit]
            w.present(orbit, truth=i, tag=f"{prefix}|{i}", kind=kind)
    t0 = time.perf_counter()
    w.run()
    ms = (time.perf_counter() - t0) * 1000.0
    return w.read(), ms


def check_proposal_identity(qbase, gbase, base_origins, probes, seed):
    """THE PROPOSAL-LAYER GATE. Rebuild the candidate set the way `run_cell`
    does and hash it, so the claim "only the verdict varies" is CHECKED rather
    than asserted. Returns a sha256 over every orbit tile and the codebook, in
    order. It must be identical for all four arms."""
    import hashlib
    h = hashlib.sha256()
    rng = random.Random(seed)
    for r, c in base_origins:
        h.update(np.ascontiguousarray(qbase[r:r + vw.REGION, c:c + vw.REGION]).tobytes())
        h.update(np.ascontiguousarray(gbase[r:r + vw.REGION, c:c + vw.REGION]).tobytes())
    order = list(range(N_REGIONS))
    rng.shuffle(order)
    h.update(str(order).encode())
    for prefix, kind, qsrc, gsrc, (dr, dc), shuffle in probes:
        pad = vw.RHO + max(abs(dr), abs(dc))
        qpad = vw.pad_edge(qsrc, pad)
        gpad = vw.pad_edge(gsrc, pad)
        for r0, c0 in base_origins:
            for j, q, g in vw.orbit_windows(qpad, gpad, (r0 + dr, c0 + dc),
                                            vw.RHO, pad=pad):
                if shuffle:
                    q = vw.shuffle_arrangement(q, rng)
                    g = vw.shuffle_arrangement(g, rng)
                h.update(np.ascontiguousarray(q).tobytes())
                h.update(np.ascontiguousarray(g).tobytes())
    return h.hexdigest()[:16]


# --- corpora ---------------------------------------------------------------- #
def bsds_photos(n):
    from domains.vision_corpus import bsds_paths
    from PIL import Image
    out, names = [], []
    for p in bsds_paths("train")[:n]:
        out.append(np.asarray(Image.open(p).convert("L"), np.float32))
        names.append(os.path.basename(p))
    return out, names


def load_video(cid):
    idx = 0 if cid == "C1" else 3
    fr, meta = vp.jellyfin_frames(150, every=2, start_s=300, size=vw.GRID,
                                  episode_index=idx)
    return [np.asarray(f, float) for f in fr], meta


def machine_state():
    try:
        ps = subprocess.run(["ps", "-eo", "pcpu,args", "--sort=-pcpu"],
                            capture_output=True, text=True, timeout=20).stdout
        top = [ln.strip()[:120] for ln in ps.strip().split("\n")[1:6]]
    except Exception:                                    # noqa: BLE001
        top = ["<ps unavailable>"]
    return {"loadavg": os.getloadavg(), "top_processes": top}


# --- video probes ----------------------------------------------------------- #
def video_probes(qs, gs, t, rng, seed):
    """The probe set for ONE base frame. A1 identity at t+delta; A2 a distant
    frame; A3 the arrangement-destroyed floor; G1 the identical frame; G2c the
    noise draw that CALIBRATES the refusal floor; G2t an INDEPENDENT noise draw
    that TESTS it. G2c/G2t are separate draws precisely so the refusal control
    is not the tautology 'the max of a set does not exceed itself'."""
    far = [u for u in range(len(qs)) if abs(u - t) >= MIN_SHUFFLE_GAP]
    probes = []
    for d in DELTAS:
        tj = min(t + d, len(qs) - 1)
        probes.append((f"A1|d{d}", "A1", qs[tj], gs[tj], (0, 0), False))
        u = rng.choice(far)
        probes.append((f"A2|d{d}", "A2", qs[u], gs[u], (0, 0), False))
        probes.append((f"A3|d{d}", "A3", qs[tj], gs[tj], (0, 0), True))
    probes.append(("G1|d0", "G1", qs[t], gs[t], (0, 0), False))
    for label, off in (("G2c", 700), ("G2t", 800)):
        r2 = np.random.RandomState(seed + off + t)
        nq = r2.randint(0, vw.K_LEVELS, qs[t].shape)
        ng = r2.randint(0, 256, qs[t].shape).astype(float)
        probes.append((f"{label}|d0", label, nq, ng, (0, 0), False))
    return probes


def c3_probes(q, g, pi, seed):
    probes = []
    for d in DISPLACEMENTS:
        probes.append((f"A1|d{d}", "A1", q, g, (0, d), False))
        probes.append((f"A3|d{d}", "A3", q, g, (0, d), True))
    probes.append(("G1|d0", "G1", q, g, (0, 0), False))
    for label, off in (("G2c", 900), ("G2t", 950)):
        r2 = np.random.RandomState(seed + off + pi)
        nq = r2.randint(0, vw.K_LEVELS, q.shape)
        ng = r2.randint(0, 256, q.shape).astype(float)
        probes.append((f"{label}|d0", label, nq, ng, (0, 0), False))
    return probes


# --- drivers ---------------------------------------------------------------- #
def run_c3(out, n_photos, seed_block, tag="c3"):
    photos, names = bsds_photos(n_photos)
    out["corpora"]["C3"] = {"source": "BSDS300", "n_photos": len(photos),
                            "files": names}
    hashes = {}
    for verdict in vw.VERDICTS:
        rows, t0 = [], time.time()
        for pi, ph in enumerate(photos):
            q, g = vw.quantize(ph), np.asarray(ph, float)
            h, w_ = q.shape
            ar, ac = (h - vw.GRID) // 2, (w_ - vw.GRID) // 2
            qb = q[ar:ar + vw.GRID, ac:ac + vw.GRID]
            gb = g[ar:ar + vw.GRID, ac:ac + vw.GRID]
            origins = list(vw.region_origins())
            probes = c3_probes(qb, gb, pi, seed_block)
            seed = seed_block + pi
            hashes.setdefault(verdict, []).append(
                check_proposal_identity(qb, gb, origins, probes, seed))
            r, _ms = run_cell(verdict, qb, gb, origins, probes, seed)
            for x in r:
                x["photo"] = pi
            rows.extend(r)
            if pi % 6 == 0:
                print(f"  [C3 {verdict}] photo {pi}/{len(photos)} "
                      f"({time.time() - t0:.0f}s)", flush=True)
        print(f"  [C3 {verdict}] done ({time.time() - t0:.0f}s)", flush=True)
        with open(os.path.join(ROOT, "results",
                               f"verdict_rows_C3_{verdict}.json"), "w") as fh:
            json.dump(rows, fh)
        out["c3"][verdict] = {"n_rows": len(rows),
                              "wall_s": time.time() - t0}
    out["proposal_hashes"]["C3"] = hashes
    out["proposal_identical"]["C3"] = bool(
        len({tuple(v) for v in hashes.values()}) == 1)


def run_video(out, which, n_base, seed_block):
    for cid in which:
        try:
            frames, meta = load_video(cid)
        except Exception as e:                            # noqa: BLE001
            out["corpora"][cid] = {"error": f"{type(e).__name__}: {e}"}
            print(f"[corpus {cid}] ABSENT: {e}", flush=True)
            continue
        out["corpora"][cid] = meta
        qs = [vw.quantize(f) for f in frames]
        gs = list(frames)
        origins = list(vw.region_origins())
        # per-STEP motion; the cut rule is Otsu on this, and for delta>1 a cut
        # ANYWHERE in the interval breaks identity, so the per-probe statistic
        # is the MAX over the interval.
        step = [float(np.mean(np.abs(frames[t + 1] - frames[t])))
                for t in range(len(frames) - 1)]
        thr, nlo, nhi, mlo, mhi = otsu_threshold(step)
        out["motion"][cid] = {
            "mean": float(np.mean(step[:n_base])), "sd": float(np.std(step[:n_base])),
            "min": float(np.min(step)), "max": float(np.max(step)),
            "otsu_threshold": thr, "n_low": nlo, "n_high": nhi,
            "mean_low": mlo, "mean_high": mhi,
            "step": step}
        cutflag = {}
        for t in range(n_base):
            for d in DELTAS:
                seg = step[t:min(t + d, len(step))]
                cutflag[f"{t}|{d}"] = bool(seg and max(seg) > thr)
        out["cut"][cid] = cutflag
        print(f"[{cid}] otsu {thr:.3f}  low {nlo} (mean {mlo:.3f})  "
              f"high {nhi} (mean {mhi:.3f})", flush=True)
        hashes = {}
        for verdict in vw.VERDICTS:
            rows, t0 = [], time.time()
            for t in range(n_base):
                rng = random.Random(seed_block + 400 + t)
                probes = video_probes(qs, gs, t, rng, seed_block)
                seed = seed_block + 200 + t
                hashes.setdefault(verdict, []).append(
                    check_proposal_identity(qs[t], gs[t], origins, probes, seed))
                r, _ms = run_cell(verdict, qs[t], gs[t], origins, probes, seed)
                for x in r:
                    x["base"] = t
                rows.extend(r)
                if t % 10 == 0:
                    print(f"  [{cid} {verdict}] base {t}/{n_base} "
                          f"({time.time() - t0:.0f}s)", flush=True)
            print(f"  [{cid} {verdict}] done ({time.time() - t0:.0f}s)", flush=True)
            with open(os.path.join(ROOT, "results",
                                   f"verdict_rows_{cid}_{verdict}.json"), "w") as fh:
                json.dump(rows, fh)
            out["video"].setdefault(cid, {})[verdict] = {
                "n_rows": len(rows), "wall_s": time.time() - t0}
        out["proposal_hashes"][cid] = hashes
        out["proposal_identical"][cid] = bool(
            len({tuple(v) for v in hashes.values()}) == 1)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    path = os.path.join(ROOT, "results", f"verdict_comparator_{what}.json")
    prov = provenance_line()
    out = {"provenance": prov,
           "prereg": "VISION_VERDICT_PREREG.md",
           "mode": what,
           "machine_state_at_start": machine_state(),
           "constants": {"seed_block": SEED_BLOCK,
                         "pilot_seed_block": PILOT_SEED_BLOCK,
                         "n_photos": N_PHOTOS, "n_base": N_BASE,
                         "displacements": list(DISPLACEMENTS),
                         "deltas": list(DELTAS), "n_regions": N_REGIONS,
                         "chance": CHANCE, "rho": vw.RHO,
                         "k_levels": vw.K_LEVELS, "region": vw.REGION,
                         "grid": vw.GRID, "verdicts": list(vw.VERDICTS)},
           "corpora": {}, "c3": {}, "video": {}, "motion": {}, "cut": {},
           "proposal_hashes": {}, "proposal_identical": {}}
    print(f"[provenance] {prov}", flush=True)
    print(f"[machine] {out['machine_state_at_start']['loadavg']}", flush=True)
    if what == "pilot":
        # PILOT: already-burned seeds only (protocol section 3.3).
        run_video(out, ("C2",), N_PILOT_BASE, PILOT_SEED_BLOCK)
    if what in ("c3", "all"):
        run_c3(out, N_PHOTOS, SEED_BLOCK)
    if what in ("video", "all"):
        run_video(out, ("C1", "C2"), N_BASE, SEED_BLOCK)
    if what == "c1":
        run_video(out, ("C1",), N_BASE, SEED_BLOCK)
    if what == "c2":
        run_video(out, ("C2",), N_BASE, SEED_BLOCK)
    out["machine_state_at_end"] = machine_state()
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {path}", flush=True)


if __name__ == "__main__":
    main()
