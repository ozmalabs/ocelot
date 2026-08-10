#!/usr/bin/env python3
"""GRAPH-RESIDENT ABSTENTION ON A DISCONTINUED PRIOR — the runner.

Pre-registration: `VISION_CUT_ABSTENTION_PREREG.md`. Exactly the arms, corpora,
n and statistics declared there.

USAGE:
    PYTHONPATH=runners/dsl/python:. python scripts/cut_abstention_measure.py video
    PYTHONPATH=runners/dsl/python:. python scripts/cut_abstention_measure.py stress
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
from domains.cut_abstention_world import CutAbstentionWorld  # noqa: E402

_spec = _iu.spec_from_file_location(
    "video_probe_measure", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
vp = _iu.module_from_spec(_spec)
_spec.loader.exec_module(vp)

# --- pre-registered constants ---------------------------------------------- #
#: THIS RUNG'S BLOCK. A concurrent rung holds 72000-72999; nothing outside
#: 73000-73999 is drawn anywhere in this file.
SEED_BLOCK = 73000
N_BASE = 50
DELTAS = (1, 5, 25)
N_REGIONS = 16
MIN_SHUFFLE_GAP = 30
T975 = {49: 2.0096}
#: The three armings compared. "" is the seed LOADED BUT INERT -- the baseline
#: carries the identical graph construction, so the byte-identity arm compares
#: like with like.
ARMINGS = ("", "mag", "xcorr")
#: The protected arm is V3 (ncc), the only one that passed the verdict rung's
#: gate. V2 (ssdg) is the contrast whose refusal that rung proved dead.
VERDICTS = ("ncc", "ssdg")
#: Arm 2b's stress velocities, in pixels per step. NAMED AS HAND-SET (section
#: 13): they do not fall out of anything. They are a sweep across a stress
#: axis, not a fitted parameter, and no verdict is chosen from them post hoc.
PAN_VELOCITIES = (1, 2, 4, 8)


def otsu_threshold(xs):
    """The numpy REFERENCE Otsu, copied verbatim from
    `verdict_comparator_measure.py`. It decides nothing here -- the graph
    computes its own threshold in `ca_otsu`, and this exists so that claim can
    be CHECKED rather than trusted."""
    a = sorted(float(x) for x in xs)
    n = len(a)
    if n < 2:
        return float("inf")
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
    return best_t


def t_ci(xs, df=49):
    n = len(xs)
    if n < 2:
        return (float(xs[0]) if xs else 0.0, 0.0, 0.0)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    h = T975.get(df, 1.984) * sd / math.sqrt(n)
    return (m, m - h, m + h)


def machine_state():
    try:
        ps = subprocess.run(["ps", "-eo", "pcpu,args", "--sort=-pcpu"],
                            capture_output=True, text=True, timeout=20).stdout
        top = [ln.strip()[:120] for ln in ps.strip().split("\n")[1:6]]
    except Exception:                                    # noqa: BLE001
        top = ["<ps unavailable>"]
    return {"loadavg": os.getloadavg(), "top_processes": top}


def load_video(cid):
    idx = 0 if cid == "C1" else 3
    fr, meta = vp.jellyfin_frames(150, every=2, start_s=300, size=vw.GRID,
                                  episode_index=idx)
    return [np.asarray(f, float) for f in fr], meta


# --- the probe set, HELD IDENTICAL to the verdict rung's --------------------- #
def video_probes(qs, gs, t, rng, seed):
    """Byte-for-byte the verdict rung's `video_probes`, plus each probe's OWN
    span -- the half-open step interval the probe was CONSTRUCTED from. A2 is a
    randomly chosen distant frame and G1/G2 are at d=0, so no interval exists
    for them: an empty span is a structural fact about the probe, not a choice
    about which probes deserve protection."""
    far = [u for u in range(len(qs)) if abs(u - t) >= MIN_SHUFFLE_GAP]
    n_steps = len(qs) - 1
    probes = []
    for d in DELTAS:
        tj = min(t + d, len(qs) - 1)
        span = tuple(range(t, min(t + d, n_steps)))
        probes.append((f"A1|d{d}", "A1", qs[tj], gs[tj], (0, 0), False, span))
        u = rng.choice(far)
        probes.append((f"A2|d{d}", "A2", qs[u], gs[u], (0, 0), False, ()))
        probes.append((f"A3|d{d}", "A3", qs[tj], gs[tj], (0, 0), True, span))
    probes.append(("G1|d0", "G1", qs[t], gs[t], (0, 0), False, ()))
    for label, off in (("G2c", 700), ("G2t", 800)):
        r2 = np.random.RandomState(seed + off + t)
        nq = r2.randint(0, vw.K_LEVELS, qs[t].shape)
        ng = r2.randint(0, 256, qs[t].shape).astype(float)
        probes.append((f"{label}|d0", label, nq, ng, (0, 0), False, ()))
    return probes


def run_cell(verdict, armed, frames, qbase, gbase, base_origins, probes, seed):
    """ONE substrate: one codebook, one verdict, one arming, the whole frame
    sequence, every probe. The candidate set is built exactly as the verdict
    rung builds it and is INDEPENDENT of `armed` -- that is what the
    byte-identity arm means operationally."""
    rng = random.Random(seed)
    codebook = [(qbase[r:r + vw.REGION, c:c + vw.REGION],
                 gbase[r:r + vw.REGION, c:c + vw.REGION])
                for r, c in base_origins]
    order = list(range(N_REGIONS))
    rng.shuffle(order)
    w = CutAbstentionWorld(verdict, armed)
    w.hold_sequence(frames)
    w.hold(codebook, order)
    for prefix, kind, qsrc, gsrc, (dr, dc), shuffle, span in probes:
        pad = vw.RHO + max(abs(dr), abs(dc))
        qpad = vw.pad_edge(qsrc, pad)
        gpad = vw.pad_edge(gsrc, pad)
        for i, (r0, c0) in enumerate(base_origins):
            orbit = vw.orbit_windows(qpad, gpad, (r0 + dr, c0 + dc), vw.RHO,
                                     pad=pad)
            if shuffle:
                orbit = [(j, vw.shuffle_arrangement(q, rng),
                          vw.shuffle_arrangement(g, rng)) for j, q, g in orbit]
            w.present(orbit, truth=i, tag=f"{prefix}|{i}", kind=kind, span=span)
    t0 = time.perf_counter()
    w.run()
    ms = (time.perf_counter() - t0) * 1000.0
    return w.read(), w.step_readout(), w.marker_inventory(), ms


# --- drivers ---------------------------------------------------------------- #
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
        ref_step = [float(np.mean(np.abs(frames[t + 1] - frames[t])))
                    for t in range(len(frames) - 1)]
        ref_thr = otsu_threshold(ref_step)
        out["reference"][cid] = {
            "step": ref_step, "numpy_otsu": ref_thr,
            "numpy_cut_steps": [t for t, x in enumerate(ref_step) if x > ref_thr]}
        for verdict in VERDICTS:
            for armed in ARMINGS:
                rows, t0 = [], time.time()
                sr_first, mk_first = None, None
                for t in range(n_base):
                    rng = random.Random(seed_block + 400 + t)
                    probes = video_probes(qs, gs, t, rng, seed_block)
                    seed = seed_block + 200 + t
                    r, sr, mk, _ms = run_cell(verdict, armed, frames, qs[t],
                                              gs[t], origins, probes, seed)
                    for x in r:
                        x["base"] = t
                    rows.extend(r)
                    if sr_first is None:
                        sr_first, mk_first = sr, mk
                    if t % 10 == 0:
                        print(f"  [{cid} {verdict} armed={armed!r}] base {t}/{n_base} "
                              f"({time.time() - t0:.0f}s)", flush=True)
                key = f"{cid}|{verdict}|{armed or 'inert'}"
                with open(os.path.join(ROOT, "results",
                                       f"cut_rows_{cid}_{verdict}_{armed or 'inert'}.json"),
                          "w") as fh:
                    json.dump(rows, fh)
                out["runs"][key] = {
                    "n_rows": len(rows), "wall_s": time.time() - t0,
                    "graph_threshold": sr_first["cut_threshold"],
                    "graph_cut_steps": [s["t"] for s in sr_first["steps"] if s["is_cut"]],
                    "graph_mag": [s["mag"] for s in sr_first["steps"]],
                    "markers": mk_first}
                print(f"  [{key}] done ({time.time() - t0:.0f}s) "
                      f"thr={sr_first['cut_threshold']} "
                      f"cuts={out['runs'][key]['graph_cut_steps']}", flush=True)


# --- ARM 2b and ARM 4: the two arms the pre-registration expects to FAIL ----- #
def _sequence_only(frames, armed):
    """Run ONLY the cut-detection layer on a frame sequence: no codebook, no
    probes, no comparator. What the graph marks is the whole measurement."""
    w = CutAbstentionWorld("ncc", armed)
    w.hold_sequence(frames)
    w.run()
    return w.step_readout()


def run_stress(out, n_base, seed_block):
    """ARM 2b -- a fast RIGID PAN has no discontinuity and an arbitrarily large
    frame difference. ARM 4 -- a CUT-FREE sequence has no discontinuity at all.
    Both are the same question from two sides: has this mechanism learned
    `broken prior`, or merely `large change`?"""
    for cid in ("C1", "C2"):
        try:
            frames, _meta = load_video(cid)
        except Exception as e:                            # noqa: BLE001
            print(f"[stress {cid}] ABSENT: {e}", flush=True)
            continue
        ref_step = [float(np.mean(np.abs(frames[t + 1] - frames[t])))
                    for t in range(len(frames) - 1)]
        ref_thr = otsu_threshold(ref_step)
        cuts = [t for t, x in enumerate(ref_step) if x > ref_thr]

        # ARM 2b: rigid pan built from ONE real frame. np.roll wraps, which
        # makes the translation EXACTLY rigid -- no new content enters, so
        # there is no discontinuity anywhere in the sequence by construction.
        for v in PAN_VELOCITIES:
            seq = [np.roll(frames[0], (0, v * t), axis=(0, 1))
                   for t in range(len(frames))]
            ref = [float(np.mean(np.abs(seq[t + 1] - seq[t])))
                   for t in range(len(seq) - 1)]
            for armed in ("mag", "xcorr"):
                sr = _sequence_only(seq, armed)
                out["arm2b"][f"{cid}|pan{v}|{armed}"] = {
                    "n_steps": len(sr["steps"]), "n_cut": sr["n_cut"],
                    "cut_fraction": sr["n_cut"] / max(1, len(sr["steps"])),
                    "graph_threshold": sr["cut_threshold"],
                    "mean_ref_motion": float(np.mean(ref)),
                    "corpus_otsu_threshold": ref_thr,
                    "exceeds_corpus_threshold": bool(np.mean(ref) > ref_thr)}
                print(f"  [arm2b {cid} pan{v} {armed}] cut {sr['n_cut']}/"
                      f"{len(sr['steps'])} mean_motion={np.mean(ref):.3f}", flush=True)

        # ARM 4: the longest CONTIGUOUS CUT-FREE run of the real corpus. Real
        # data, real texture, real camera motion -- and no discontinuity.
        bounds = [-1] + cuts + [len(ref_step)]
        best = max(range(len(bounds) - 1),
                   key=lambda i: bounds[i + 1] - bounds[i])
        lo, hi = bounds[best] + 1, bounds[best + 1]
        seq = frames[lo:hi + 1]
        for armed in ("mag", "xcorr"):
            sr = _sequence_only(seq, armed)
            out["arm4"][f"{cid}|{armed}"] = {
                "frame_range": [lo, hi], "n_steps": len(sr["steps"]),
                "n_cut": sr["n_cut"],
                "cut_fraction": sr["n_cut"] / max(1, len(sr["steps"])),
                "graph_threshold": sr["cut_threshold"],
                "marked_steps": [s["t"] for s in sr["steps"] if s["is_cut"]],
                "max_motion_in_run": float(max(ref_step[lo:hi] or [0.0])),
                "corpus_otsu_threshold": ref_thr}
            print(f"  [arm4 {cid} {armed}] frames {lo}..{hi} "
                  f"cut {sr['n_cut']}/{len(sr['steps'])}", flush=True)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    path = os.path.join(ROOT, "results", f"cut_abstention_{what}.json")
    prov = provenance_line()
    out = {"provenance": prov,
           "prereg": "VISION_CUT_ABSTENTION_PREREG.md",
           "mode": what,
           "machine_state_at_start": machine_state(),
           "constants": {"seed_block": SEED_BLOCK, "n_base": N_BASE,
                         "deltas": list(DELTAS), "n_regions": N_REGIONS,
                         "armings": list(ARMINGS), "verdicts": list(VERDICTS),
                         "pan_velocities": list(PAN_VELOCITIES),
                         "rho": vw.RHO, "k_levels": vw.K_LEVELS,
                         "region": vw.REGION, "grid": vw.GRID},
           "corpora": {}, "reference": {}, "runs": {},
           "arm2b": {}, "arm4": {}}
    print(f"[provenance] {prov}", flush=True)
    if what in ("video", "all"):
        run_video(out, ("C1", "C2"), N_BASE, SEED_BLOCK)
    if what in ("stress", "all"):
        run_stress(out, N_BASE, SEED_BLOCK)
    out["machine_state_at_end"] = machine_state()
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {path}", flush=True)


if __name__ == "__main__":
    main()
