"""motion_objects_measure — does COMMON MOTION group cells into FEW, LARGE
proto-objects that cohere, persist, refuse background, and decline on stills?

Pre-registration: VISION_MOTION_OBJECTS_PREREG.md, committed 55d46a09 BEFORE
any real-frame number. Seeds 84000-84999.

Mechanical I/O + read-out ONLY. Every decision is the seed's
(`vision_motion_group`): the dispersion, the tolerance, the common-fate flood,
the reference frame and the mint are ALL rules. This script builds vector
fields, advances the clock, and measures.

THREE INSTRUMENT DISCIPLINES ARE LOAD-BEARING HERE:

1. `assert_settled` recomputes the flood's fixpoint and the tolerance
   broadcast INDEPENDENTLY, in the reader, from the settled graph. This engine
   has been observed to report a genuine fixpoint over an unsettled flood, and
   a partially-flooded field is indistinguishable by eye from a legitimately
   fragmented one -- while inflating the object count, which is the headline.
   Any run with a non-zero verdict is DISCARDED, not reported.

2. A proto mechanism that mints VACUOUSLY looks like success (three times in
   this thread). The dead-instrument control must ACTUALLY FIRE, and the run
   ABORTS if it does not.

3. EVERY FLOOR IS RE-EARNED AT THIS CONFIGURATION. The incumbent is re-run on
   this rung's own 18x18 whole-frame lattice rather than compared to its
   published G72 number, because floors in this arc have moved 3.6x and in
   opposite directions between configurations, and an inherited floor produced
   a phantom 3x gain in the previous rung.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
import time
from collections import Counter

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                  # noqa: E402

ep.engine_preamble()

from substrate.boot_core import boot_core, load_seeds_into   # noqa: E402
from domains import motion_group_world as mgw                # noqa: E402
from domains import border_ownership_world as bow            # noqa: E402

SEED_BLOCK = 84000

# The sensor's aperture. BLOCK is a DECLARED magic-number residual (§13),
# exactly as `k` is; RADIUS = BLOCK falls out of overlap (beyond its own extent
# a block shares no pixels with its source). GRID matches the incumbent's decode.
GRID = 72
BLOCK = 4
NCELL = GRID // BLOCK          # 18x18 motion cells, WHOLE FRAME (not tiled)
K_LUM = 16                     # the incumbent's headline quantization, inherited

N_FRAMES = 45                  # consecutive; every=1 -- motion needs t, t+1
N_PAIRS_M3 = 40                # fixed in advance, matches the incumbent's N_CONSECUTIVE
SAMPLED = (0, 6, 12, 18, 24, 30, 36)   # 7 sampled pairs for per-frame counts
MAX_STEPS = 200_000

CORPORA = (("C1", "cartoon", 0, "08630d4b"),
           ("C2", "live-action", 3, "119eca43"))


def _vp():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# --- statistics -------------------------------------------------------------
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
    d = [x - y for x, y in zip(xs, ys) if x is not None and y is not None]
    return ci95(d)


def iou(u, v):
    su, sv = set(u), set(v)
    return len(su & sv) / len(su | sv) if (su or sv) else 0.0


def best_iou_score(sup_a, sup_b):
    """Mean over objects at t of the best IoU against any object at t+1."""
    if not sup_a or not sup_b:
        return None
    return float(np.mean([max(iou(a, b) for b in sup_b.values())
                          for a in sup_a.values()]))


def random_partition(cells, sizes, rng):
    """A size-matched BFS-CONNECTED arbitrary partition of the same cells --
    FLOOR-B. Re-earned here; not inherited from the incumbent's configuration."""
    remaining = set(cells)
    out = {}
    for i, sz in enumerate(sorted(sizes, reverse=True)):
        if not remaining:
            break
        seed = tuple(rng.permutation(sorted(remaining))[0])
        blob, frontier = {seed}, [seed]
        remaining.discard(seed)
        while frontier and len(blob) < sz:
            r, c = frontier.pop(0)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in remaining and len(blob) < sz:
                    blob.add(nb)
                    remaining.discard(nb)
                    frontier.append(nb)
        out[i] = sorted(blob)
    return out


# --- the substrate runs -----------------------------------------------------
def run_motion(vf, *, mcontrast=1.0, mtol_exact=0.0):
    """One vector field through the seed to its fixpoint."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_motion_group"])
    h = mgw.add_mfield(s, vf)
    t0 = time.time()
    sweeps = mgw.settle(s, marm=1.0, mcontrast=mcontrast,
                        mtol_exact=mtol_exact, max_steps=MAX_STEPS)
    ms = (time.time() - t0) * 1e3
    objs = mgw.objects(s)
    chk = mgw.assert_settled(s, h)
    sup = mgw.support(s, h, [o["root"] for o in objs])
    return {"sweeps": sweeps, "ms": ms, "check": chk,
            "mtol": float(mgw.field_attr(s, h, "mtol") or 0.0),
            "dom_v": tuple(float(x) for x in (mgw.field_attr(s, h, "dom_v") or (0., 0.))),
            "objects": objs, "support": sup,
            "labels": mgw.labels(s, h)}


def run_incumbent(lum18):
    """THE MATCHED CONTROL: the incumbent static-form criterion (competitive
    border ownership, the previous rung's own replacement arm) re-run on THIS
    rung's 18x18 whole-frame lattice, on the same frames. Not its published
    G72 number -- that is a different configuration and a different cell count."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    h = bow.add_field(s, lum18)
    bow.set_flag(s, bown=1.0, bown_own=1.0)
    sweeps = bow.tick(s, max_steps=MAX_STEPS)
    protos = bow.protos(s)
    at = {rc: s.node(n)["attrs"] for rc, n in h["index"].items()}
    sup = {}
    for p in protos:
        lab = float(p["root"])
        sup[p["root"]] = sorted(rc for rc, a in at.items()
                                if float(a.get("glabel", -1.0)) == lab)
    return {"sweeps": sweeps, "protos": protos, "support": sup}


def quantize(frame, k):
    f = np.asarray(frame, float)
    lo, hi = float(f.min()), float(f.max())
    if hi <= lo:
        return [[0 for _ in row] for row in f]
    q = np.clip(((f - lo) / (hi - lo) * k).astype(int), 0, k - 1)
    return [[int(v) for v in row] for row in q]


def downsample18(frame):
    f = np.asarray(frame, float)
    return f.reshape(NCELL, BLOCK, NCELL, BLOCK).mean(axis=(1, 3))


def multi(objs):
    return [o for o in objs if o["members"] > 1]


# --- M2 cohesion: a DIRECT VECTOR READ --------------------------------------
def cohesion(vf, sup, objs):
    """WITHIN-group vector dispersion against BETWEEN-group.

    Both are dispersions OF VECTORS -- mean distance to the group's own mean
    vector (within) and mean pairwise distance between group mean vectors
    (between). Not an aggregate over pairwise per-cell scalar comparisons."""
    if len(objs) < 2:
        return {"within": None, "between": None, "ratio": None}
    means, withins = [], []
    for o in objs:
        cells = sup.get(o["root"], [])
        if not cells:
            continue
        V = np.array([vf[r, c] for r, c in cells], float)
        mu = V.mean(axis=0)
        means.append(mu)
        withins.append(float(np.linalg.norm(V - mu, axis=1).mean()))
    if len(means) < 2:
        return {"within": None, "between": None, "ratio": None}
    M = np.array(means)
    d = [float(np.linalg.norm(M[i] - M[j]))
         for i in range(len(M)) for j in range(i + 1, len(M))]
    w, b = float(np.mean(withins)), float(np.mean(d))
    return {"within": w, "between": b, "ratio": (w / b) if b > 0 else None}


# --- controls ---------------------------------------------------------------
def synth(seed, *, figure=True, fig_dv=(0, 1), bg_dv=(0, 0)):
    """A textured field; optionally a 6x4-cell rectangle translating within it."""
    rng = np.random.default_rng(seed)
    PX = GRID
    base = rng.integers(0, 256, size=(PX * 3, PX * 3)).astype(float)
    a = base[PX:2 * PX, PX:2 * PX].copy()
    b = base[PX + bg_dv[0] * BLOCK:2 * PX + bg_dv[0] * BLOCK,
             PX + bg_dv[1] * BLOCK:2 * PX + bg_dv[1] * BLOCK].copy()
    if figure:
        r0, r1 = 4 * BLOCK, 10 * BLOCK
        c0, c1 = 5 * BLOCK, 9 * BLOCK
        fy, fx = fig_dv[0] * BLOCK, fig_dv[1] * BLOCK
        patch = base[PX + r0:PX + r1, PX + c0:PX + c1]
        a[r0:r1, c0:c1] = patch
        b[r0 + fy:r1 + fy, c0 + fx:c1 + fx] = patch
    return a, b


def controls():
    out = {}

    # D1 -- the positive control.
    a, b = synth(84900, figure=True, fig_dv=(0, 1), bg_dv=(0, 0))
    r = run_motion(mgw.vector_field(a, b, BLOCK))
    out["D1"] = {"n_obj": len(r["objects"]), "n_multi": len(multi(r["objects"])),
                 "largest": max((o["members"] for o in r["objects"]), default=0),
                 "check": r["check"], "mtol": r["mtol"]}

    # D2 -- the DEAD-INSTRUMENT arm. A uniformly translating field contains NO
    # figure. With the contrast DISARMED the mechanism must mint one object
    # covering the whole field; with it ARMED it must mint nothing.
    a, b = synth(84901, figure=False, bg_dv=(0, 1))
    vf = mgw.vector_field(a, b, BLOCK)
    dis = run_motion(vf, mcontrast=0.0)
    arm = run_motion(vf, mcontrast=1.0)
    out["D2_disarmed"] = {"n_obj": len(dis["objects"]),
                          "largest": max((o["members"] for o in dis["objects"]), default=0),
                          "check": dis["check"]}
    out["D2_armed"] = {"n_obj": len(arm["objects"]),
                       "n_multi": len(multi(arm["objects"])),
                       "check": arm["check"]}

    # D3 -- a large STATIC textured background patch beside a moving figure.
    # The crisp form of "a stable patch of wall is not an object".
    a, b = synth(84902, figure=True, fig_dv=(0, 1), bg_dv=(0, 0))
    r3 = run_motion(mgw.vector_field(a, b, BLOCK))
    dom = r3["dom_v"]
    static_minted = sum(1 for o in r3["objects"]
                        if math.dist(o["v"], dom) == 0.0)
    out["D3_static_bg"] = {"n_obj": len(r3["objects"]),
                           "dom_v": dom,
                           "objects_moving_with_dominant": static_minted,
                           "check": r3["check"]}

    # NOISE -- an iid random VECTOR field (not a random image): the grouping
    # criterion applied to structureless motion.
    rng = np.random.default_rng(84200)
    nvf = rng.integers(-BLOCK, BLOCK + 1, size=(NCELL, NCELL, 2)).astype(float)
    rn = run_motion(nvf)
    out["NOISE"] = {"n_obj": len(rn["objects"]),
                    "n_multi": len(multi(rn["objects"])),
                    "largest": max((o["members"] for o in rn["objects"]), default=0),
                    "check": rn["check"], "mtol": rn["mtol"]}
    return out


def stills(frames):
    """M5 -- STILLS DECLINE. Near-zero objects is the PASS condition.
    BSDS300 is ABSENT from this tree, so this is frozen-frame + global pan."""
    out = {}
    f = frames[0]
    r = run_motion(mgw.vector_field(f, f, BLOCK))
    out["frozen"] = {"n_obj": len(r["objects"]), "n_multi": len(multi(r["objects"])),
                     "check": r["check"]}
    pan = np.roll(np.roll(f, BLOCK, axis=0), BLOCK, axis=1)
    r2 = run_motion(mgw.vector_field(f, pan, BLOCK))
    out["global_pan"] = {"n_obj": len(r2["objects"]),
                         "n_multi": len(multi(r2["objects"])),
                         "dom_v": r2["dom_v"], "check": r2["check"]}
    return out


def main():
    t_start = time.time()
    vp = _vp()
    report = {"config": {"GRID": GRID, "BLOCK": BLOCK, "NCELL": NCELL,
                         "K_LUM": K_LUM, "N_FRAMES": N_FRAMES,
                         "N_PAIRS_M3": N_PAIRS_M3, "seed_block": SEED_BLOCK,
                         "engine": ep.engine_hash()
                         if hasattr(ep, "engine_hash") else None},
              "bsds300": "ABSENT (data/ does not exist) -- stills arm is "
                         "frozen-frame + global pan, declared in the prereg"}

    print("== controls (the run ABORTS if the dead-instrument arm does not fire)")
    ctl = controls()
    report["controls"] = ctl
    print("   ", json.dumps(ctl, default=str)[:600])
    if ctl["D2_disarmed"]["largest"] < NCELL * NCELL * 0.9:
        raise SystemExit(
            f"DEAD-INSTRUMENT CONTROL DID NOT FIRE: largest object under the "
            f"disarmed contrast is {ctl['D2_disarmed']['largest']}, expected "
            f"~{NCELL*NCELL} on a field containing no figure. RUN VOID.")
    if ctl["D2_armed"]["n_multi"] != 0:
        raise SystemExit(
            f"D2 ARMED minted {ctl['D2_armed']['n_multi']} multi-cell objects on "
            f"a uniformly translating field. RUN VOID.")

    for name, what, epi, pin in CORPORA:
        print(f"== {name} ({what})")
        frames, meta = vp.jellyfin_frames(N_FRAMES, every=1, start_s=300,
                                          size=GRID, episode_index=epi)
        if not str(meta.get("episode_id", "")).startswith(pin):
            raise SystemExit(f"{name} PIN MISMATCH: {meta.get('episode_id')} "
                             f"!= {pin}... RUN VOID.")
        arms = {}
        for arm, exact in (("otsu", 0.0), ("exact", 1.0)):
            runs, incs = [], []
            npairs = min(N_PAIRS_M3, len(frames) - 1)
            for t in range(npairs):
                vf = mgw.vector_field(frames[t], frames[t + 1], BLOCK)
                r = run_motion(vf, mtol_exact=exact)
                r["vf"] = vf
                r["dlum"] = np.abs(downsample18(frames[t + 1])
                                   - downsample18(frames[t]))
                runs.append(r)
                if arm == "otsu":
                    incs.append(run_incumbent(
                        quantize(downsample18(frames[t]), K_LUM)))
                if t % 10 == 0:
                    print(f"   {arm} pair {t}/{npairs} "
                          f"obj={len(r['objects'])} multi={len(multi(r['objects']))} "
                          f"chk={r['check']} {time.time()-t_start:.0f}s", flush=True)

            good = [r for r in runs
                    if r["check"]["unsettled_pairs"] == 0
                    and r["check"]["cells_without_tolerance"] == 0]
            discarded = len(runs) - len(good)

            # ---- M1 COUNT (the headline) --------------------------------
            counts = [len(r["objects"]) for r in good]
            mcounts = [len(multi(r["objects"])) for r in good]
            sizes = [o["members"] for r in good for o in multi(r["objects"])]
            allsizes = [o["members"] for r in good for o in r["objects"]]

            # ---- M2 COHESION --------------------------------------------
            coh = [cohesion(r["vf"], r["support"], multi(r["objects"]))
                   for r in good]
            wr = [c["within"] for c in coh if c["ratio"] is not None]
            br = [c["between"] for c in coh if c["ratio"] is not None]

            # ---- M3 CONTINUITY ------------------------------------------
            rng = np.random.default_rng(84300 if arm == "otsu" else 84301)
            srng = np.random.default_rng(84400 if arm == "otsu" else 84401)
            persist, floorA, floorB = [], [], []
            for t in range(len(good) - 1):
                sa = {k: v for k, v in good[t]["support"].items() if len(v) > 1}
                sb = {k: v for k, v in good[t + 1]["support"].items() if len(v) > 1}
                p = best_iou_score(sa, sb)
                if p is None:
                    continue
                persist.append(p)
                u = int(srng.integers(0, len(good)))
                tries = 0
                while abs(u - t) <= 5 and tries < 20:
                    u = int(srng.integers(0, len(good)))
                    tries += 1
                su = {k: v for k, v in good[u]["support"].items() if len(v) > 1}
                floorA.append(best_iou_score(sa, su) or 0.0)
                cells = [rc for v in sa.values() for rc in v]
                rp = random_partition(cells, [len(v) for v in sa.values()], rng)
                floorB.append(best_iou_score(sa, rp) or 0.0)

            # ---- M4 BACKGROUND, on an INDEPENDENT measure ---------------
            # Temporal LUMINANCE change over each minted object's support vs the
            # field mean. The rule refuses background by MOTION contrast; this
            # checks it using a quantity the rule never reads.
            obj_dlum, fld_dlum, quiet = [], [], 0
            nobj = 0
            for r in good:
                fm = float(r["dlum"].mean())
                fld_dlum.append(fm)
                for o in multi(r["objects"]):
                    cells = r["support"].get(o["root"], [])
                    if not cells:
                        continue
                    m = float(np.mean([r["dlum"][rr, cc] for rr, cc in cells]))
                    obj_dlum.append(m)
                    nobj += 1
                    if m < fm:
                        quiet += 1

            arms[arm] = {
                "n_runs": len(runs), "n_discarded_unsettled": discarded,
                "M1_objects_per_frame": ci95(counts),
                "M1_MULTI_per_frame": ci95(mcounts),
                "M1_multi_size": {"mean": float(np.mean(sizes)) if sizes else None,
                                  "median": float(np.median(sizes)) if sizes else None,
                                  "max": int(max(sizes)) if sizes else 0,
                                  "n": len(sizes)},
                "M1_all_size_mean": float(np.mean(allsizes)) if allsizes else None,
                "M2_within": ci95(wr), "M2_between": ci95(br),
                "M2_paired_between_minus_within": paired_ci95(br, wr),
                "M3_persist": ci95(persist),
                "M3_floorA_shuffle": ci95(floorA),
                "M3_floorB_partition": ci95(floorB),
                "M3_vs_A": paired_ci95(persist, floorA),
                "M3_vs_B": paired_ci95(persist, floorB),
                "M4_obj_dlum": ci95(obj_dlum), "M4_field_dlum": ci95(fld_dlum),
                "M4_n_multi_objects": nobj,
                "M4_share_quieter_than_field": (quiet / nobj) if nobj else None,
                "mtol": ci95([r["mtol"] for r in good]),
                "ms_per_run": ci95([r["ms"] for r in good]),
            }
            if arm == "otsu":
                ip = [len(i["protos"]) for i in incs]
                imulti = [sum(1 for p in i["protos"] if p["members"] > 1)
                          for i in incs]
                isz = [p["members"] for i in incs for p in i["protos"]
                       if p["members"] > 1]
                arms["incumbent_matched"] = {
                    "what": "vision_border_ownership (bown_own=1, the previous "
                            "rung's own replacement arm) re-run on THIS rung's "
                            "18x18 whole-frame lattice, same frames. The floor is "
                            "RE-EARNED, not inherited from G72.",
                    "protos_per_frame": ci95(ip),
                    "MULTI_per_frame": ci95(imulti),
                    "multi_size": {"mean": float(np.mean(isz)) if isz else None,
                                   "median": float(np.median(isz)) if isz else None,
                                   "max": int(max(isz)) if isz else 0},
                }
        report[name] = {"meta": {k: meta.get(k) for k in
                                 ("episode_id", "series", "name", "n_frames")},
                        "arms": arms}
        print(f"   {name} M1 otsu multi/frame="
              f"{arms['otsu']['M1_MULTI_per_frame']['mean']:.2f} "
              f"incumbent={arms['incumbent_matched']['MULTI_per_frame']['mean']:.2f}",
              flush=True)

        if name == "C1":
            report["stills"] = stills(frames)
            print("   stills:", report["stills"], flush=True)

    report["elapsed_s"] = round(time.time() - t_start, 1)
    out = os.path.join(ROOT, "results", "motion_objects.json")
    with open(out, "w") as fh:
        json.dump(report, fh, indent=1, default=str)
    print("wrote", out, "in", report["elapsed_s"], "s")


if __name__ == "__main__":
    main()
