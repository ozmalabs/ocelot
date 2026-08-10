"""surface_assignment_measure -- put a mirror or a screen in real video and
measure what the proto layer does with it.

Pre-registration: VISION_SURFACE_ASSIGNMENT_PREREG.md, committed c3eb4b9a
BEFORE any real-frame number. Seeds 87000-87999.

Mechanical I/O + read-out ONLY. Every decision is the seed's
(`vision_border_ownership` v1.1.0): the flood, the labelling, the ownership
competition and the mint are ALL rules. This script composites stimulus fields,
ticks to a fixpoint, and measures set relations against a ground-truth rectangle
the graph cannot read.

THREE INSTRUMENT DISCIPLINES ARE LOAD-BEARING HERE:

1. PROVENANCE IS PRINTED FROM INSIDE THIS PROCESS. A concurrent rung rebuilt the
   canonical engine from different Rust source mid-pilot; the migrated gate
   reported 7 passed while a plain script resolved the wrong artifact. A green
   gate in a DIFFERENT process is not provenance. See PREREG s0.4.

2. THE DISCRIMINATOR'S POSITIVE CONTROL MUST ACTUALLY FIRE. A synthetic uniform
   tile with one square must read S == R exactly, under BOTH arms, at BOTH
   sizes. A discriminator that cannot report SURFACE would make "no SURFACE" a
   PROTOCOL s1.1 dead-arm floor. The run ABORTS if it does not fire.

3. "OBJECTS APPEARED IN THE MIRROR" IS NOT EVIDENCE. Every claim is a paired
   difference against `plain` -- the SAME rectangle in the SAME frame with no
   surface in it -- so the base rate is measured, not assumed.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                  # noqa: E402

ep.engine_preamble()

SEED_BLOCK = 87000

# G72, unchanged -- VISION_RESOLUTION_SCALE_RESULTS.md s10.
GRID = 72
REGION = 18
K_MAIN = 16
TILE_ORDINAL = 5            # fixed position, declared in advance
SIDES = (8, 14)
N_FRAMES = 100
START_S = 900               # fresh material (the G72 rungs used 300)
EVERY = 2

ARMS = {"incumbent": 0.0, "replacement": 1.0}
CONTENT_ARMS = ("plain", "flat", "screen", "mirror", "scramble")

CORPORA = {
    "C1": {"what": "cartoon", "episode_index": 0, "pin": "08630d4b"},
    "C2": {"what": "live-action", "episode_index": 3, "pin": "119eca43"},
}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _fr():
    """The G72 proto driver -- quantize / region_origins / tile / run_one are
    reused VERBATIM so this rung measures the same instrument the ladder does."""
    return _load("fr", os.path.join(ROOT, "scripts",
                                    "figadj_replacement_measure.py"))


# --------------------------------------------------------------------------- #
#  STIMULUS -- pure compositing. No decision; R is held here and never written
#  into the graph.
# --------------------------------------------------------------------------- #
def rect_cells(off, side):
    return {(r, c) for r in range(off, off + side)
            for c in range(off, off + side)}


def area_resize(a, side):
    """Area-average resample of a 2-D array to (side, side). Mechanical."""
    a = np.asarray(a, float)
    h, w = a.shape
    out = np.zeros((side, side), float)
    rb = np.linspace(0, h, side + 1)
    cb = np.linspace(0, w, side + 1)
    for i in range(side):
        for j in range(side):
            blk = a[int(rb[i]):max(int(rb[i]) + 1, int(rb[i + 1])),
                    int(cb[j]):max(int(cb[j]) + 1, int(cb[j + 1]))]
            out[i, j] = float(blk.mean()) if blk.size else 0.0
    return out


def rescale_into(a, lo, hi):
    """Map `a` onto [lo, hi] so the inset is not separable by brightness."""
    a = np.asarray(a, float)
    amin, amax = float(a.min()), float(a.max())
    if amax <= amin:
        return np.full_like(a, (lo + hi) / 2.0)
    return lo + (a - amin) / (amax - amin) * (hi - lo)


def build_stimulus(base, other, r0, c0, off, side, content, rng):
    """Return a 72x72 field with `content` composited into R, and R itself.

    `base`  -- this corpus's frame (72x72)
    `other` -- the OTHER corpus's frame at the same index (the screen source)
    (r0,c0) -- the tile origin; (off,side) -- R in TILE-LOCAL coords
    """
    f = np.array(base, float)
    tl = f[r0:r0 + REGION, c0:c0 + REGION]
    lo, hi = float(tl.min()), float(tl.max())
    R0, C0 = r0 + off, c0 + off

    if content == "plain":
        pass
    elif content == "flat":
        f[R0:R0 + side, C0:C0 + side] = float(np.median(tl))
    elif content == "screen":
        f[R0:R0 + side, C0:C0 + side] = rescale_into(
            area_resize(np.asarray(other, float), side), lo, hi)
    elif content == "mirror":
        # the scene reflected: the cells immediately LEFT of R, flipped.
        src = f[R0:R0 + side, max(0, C0 - side):C0]
        if src.shape[1] < side:                     # pad at the frame edge
            src = np.pad(src, ((0, 0), (side - src.shape[1], 0)), mode="edge")
        f[R0:R0 + side, C0:C0 + side] = src[:, ::-1]
    elif content == "scramble":
        src = rescale_into(area_resize(np.asarray(other, float), side), lo, hi)
        flat = src.reshape(-1).copy()
        rng.shuffle(flat)
        f[R0:R0 + side, C0:C0 + side] = flat.reshape(side, side)
    else:
        raise ValueError(content)
    return f, rect_cells(off, side)


# --------------------------------------------------------------------------- #
#  THE DISCRIMINATOR -- set relations only. No thresholds (PROTOCOL s13).
# --------------------------------------------------------------------------- #
def classify(support, R):
    """support: {root -> [(r,c), ...]} in TILE-LOCAL coords. R: set of (r,c)."""
    n_overlap = n_inside = n_surface = n_spill = 0
    surface_ratio = None
    exact = 0
    for cells in support.values():
        S = {tuple(x) for x in cells}
        if not (S & R):
            continue
        n_overlap += 1
        if S <= R:
            if S == R:
                exact += 1
                n_surface += 1
                surface_ratio = 1.0
            else:
                n_inside += 1
        elif R <= S:
            n_surface += 1
            ratio = len(S) / len(R)
            surface_ratio = ratio if surface_ratio is None else min(
                surface_ratio, ratio)
        else:
            n_spill += 1
    return {"n_overlap": n_overlap, "n_inside": n_inside,
            "n_surface": n_surface, "n_spill": n_spill,
            "n_surface_exact": exact, "surface_ratio": surface_ratio}


def verdict(cl):
    if cl["n_overlap"] == 0:
        return "REFUSE"
    if cl["n_surface"] >= 1:
        return "SURFACE"
    if cl["n_inside"] >= 1:
        return "CONTENT_IN_SCENE"
    return "SPILL_ONLY"


# --------------------------------------------------------------------------- #
#  s3.3 -- the instrument positive control. MUST FIRE or the run is void.
# --------------------------------------------------------------------------- #
def instrument_control(fr, log):
    out = {}
    ok = True
    for side in SIDES:
        off = (REGION - side) // 2
        g = [[3] * REGION for _ in range(REGION)]
        for r in range(off, off + side):
            for c in range(off, off + side):
                g[r][c] = 9
        R = rect_cells(off, side)
        for arm in ARMS:
            r_ = fr.run_one(g, arm)
            cl = classify(r_["support"], R)
            fired = cl["n_surface_exact"] == 1 and cl["n_inside"] == 0
            ok = ok and fired
            out[f"s{side}|{arm}"] = {"n_protos": r_["n_protos"],
                                     "fired_exact_S_eq_R": bool(fired), **cl}
            log(f"  [CTRL s={side:2d} {arm:11s}] protos={r_['n_protos']} "
                f"S==R exactly: {fired}")
    out["ALL_FIRED"] = bool(ok)
    return out


# --------------------------------------------------------------------------- #
#  s6 -- the assignment CUE. Frame data only; never touches the proto layer.
# --------------------------------------------------------------------------- #
def cue_correlation(fields, R, off, side):
    """r(Delta_in, Delta_out) over consecutive composited tiles."""
    din, dout = [], []
    mask = np.zeros((REGION, REGION), bool)
    mask[off:off + side, off:off + side] = True
    for t in range(len(fields) - 1):
        d = np.abs(fields[t + 1] - fields[t])
        din.append(float(d[mask].mean()))
        dout.append(float(d[~mask].mean()))
    a, b = np.asarray(din), np.asarray(dout)
    if a.std() < 1e-12 or b.std() < 1e-12:
        return None
    return float(np.corrcoef(a, b)[0, 1])


# --------------------------------------------------------------------------- #
def main():
    t_start = time.time()
    logf = open(os.path.join(ROOT, "results", "surface_assignment.log"), "w")

    def log(m):
        print(m)
        logf.write(m + "\n")
        logf.flush()

    prov = ep.provenance_line()
    log("== PROVENANCE (printed from INSIDE the measuring process) ==")
    log(prov)
    if "WRONG ENGINE" in prov or "DIVERGED" in prov:
        raise SystemExit("ENGINE PROVENANCE FAILED -- RUN VOID")

    fr = _fr()
    vp = fr._vp()
    origins = fr.region_origins()
    r0, c0 = origins[TILE_ORDINAL]
    log(f"== G72: tile ordinal {TILE_ORDINAL} at origin ({r0},{c0}), "
        f"{REGION}x{REGION}; sides {SIDES}; n={N_FRAMES}/corpus")

    log("== s3.3 INSTRUMENT POSITIVE CONTROL (must fire) ==")
    ctrl = instrument_control(fr, log)
    if not ctrl["ALL_FIRED"]:
        raise SystemExit("INSTRUMENT CONTROL DID NOT FIRE -- RUN VOID")

    # ---- decode both corpora up front; the screen arm needs the cross pair --
    decoded = {}
    for cid in ("C1", "C2"):
        spec = CORPORA[cid]
        frames, meta = vp.jellyfin_frames(
            N_FRAMES, every=EVERY, start_s=START_S, size=GRID,
            episode_index=spec["episode_index"])
        got = str(meta["episode_id"])
        if not got.startswith(spec["pin"]):
            raise SystemExit(f"PIN MISMATCH {cid}: expected {spec['pin']}... "
                             f"got {got} -- RUN VOID")
        decoded[cid] = frames
        log(f"[{cid}] {spec['what']} decoded {len(frames)} @ {GRID}x{GRID} "
            f"pin {got[:8]} ok, start_s={START_S}")

    n = min(len(decoded["C1"]), len(decoded["C2"]))
    out = {"prereg": "VISION_SURFACE_ASSIGNMENT_PREREG.md",
           "prereg_commit": "c3eb4b9a",
           "engine_provenance": prov,
           "seed_block": [SEED_BLOCK, SEED_BLOCK + 999],
           "config": {"grid": GRID, "region": REGION, "k": K_MAIN,
                      "tile_ordinal": TILE_ORDINAL, "tile_origin": [r0, c0],
                      "sides": list(SIDES), "n_frames": n,
                      "start_s": START_S, "every": EVERY},
           "instrument_control": ctrl,
           "corpora": {cid: {"what": CORPORA[cid]["what"],
                             "pin": CORPORA[cid]["pin"], "n": n}
                       for cid in CORPORA},
           "rows": [], "cue": {}}

    # ---- the design ------------------------------------------------------- #
    # RNG ordinals are STATICALLY RESOLVABLE for scripts/seed_audit.py: an
    # explicit (ordinal, id) tuple sequence and a literal side ordinal, never a
    # dict subscript. A --check that passes with UNKNOWN sinks has verified
    # nothing.
    for ci, cid in ((0, "C1"), (1, "C2")):
        other = "C2" if cid == "C1" else "C1"
        for si, side in ((0, 8), (1, 14)):
            off = (REGION - side) // 2
            R = rect_cells(off, side)
            for coi, content in ((0, "plain"), (1, "flat"), (2, "screen"),
                                 (3, "mirror"), (4, "scramble")):
                rng = np.random.RandomState(
                    SEED_BLOCK + 100 * ci + 10 * si + coi)
                fields = []
                per_arm = {a: [] for a in ARMS}
                for fi in range(n):
                    f, _ = build_stimulus(decoded[cid][fi], decoded[other][fi],
                                          r0, c0, off, side, content, rng)
                    fields.append(f[r0:r0 + REGION, c0:c0 + REGION])
                    q = fr.quantize(f, K_MAIN)
                    for arm in ARMS:
                        res = fr.run_one(fr.tile(q, r0, c0), arm)
                        cl = classify(res["support"], R)
                        per_arm[arm].append({
                            "frame": fi, "n_protos": res["n_protos"],
                            "settled": res["settled"], **cl,
                            "verdict": verdict(cl)})
                for arm in ARMS:
                    rows = per_arm[arm]
                    vs = [r_["verdict"] for r_ in rows]
                    out["rows"].append({
                        "corpus": cid, "side": side, "content": content,
                        "arm": arm, "n": len(rows),
                        "verdicts": {v: vs.count(v) for v in
                                     ("REFUSE", "SURFACE",
                                      "CONTENT_IN_SCENE", "SPILL_ONLY")},
                        "mean_n_inside": float(np.mean(
                            [r_["n_inside"] for r_ in rows])),
                        "mean_n_surface": float(np.mean(
                            [r_["n_surface"] for r_ in rows])),
                        "mean_n_overlap": float(np.mean(
                            [r_["n_overlap"] for r_ in rows])),
                        "mean_n_spill": float(np.mean(
                            [r_["n_spill"] for r_ in rows])),
                        "mean_n_protos": float(np.mean(
                            [r_["n_protos"] for r_ in rows])),
                        "n_surface_exact": int(sum(
                            r_["n_surface_exact"] for r_ in rows)),
                        "all_settled": bool(all(r_["settled"] for r_ in rows)),
                        "per_frame_n_inside": [r_["n_inside"] for r_ in rows],
                    })
                    log(f"[{cid}|s{side:2d}|{content:8s}|{arm:11s}] "
                        f"REF={vs.count('REFUSE'):3d} SURF={vs.count('SURFACE'):3d} "
                        f"CONT={vs.count('CONTENT_IN_SCENE'):3d} "
                        f"SPILL={vs.count('SPILL_ONLY'):3d} "
                        f"| mean inside={np.mean([r_['n_inside'] for r_ in rows]):.2f} "
                        f"surface={np.mean([r_['n_surface'] for r_ in rows]):.2f}")
                out["cue"][f"{cid}|s{side}|{content}"] = cue_correlation(
                    fields, R, off, side)

    # ---- paired differences against `plain`, per PREREG s3.2 -------------- #
    idx = {(r_["corpus"], r_["side"], r_["content"], r_["arm"]): r_
           for r_ in out["rows"]}
    out["paired_vs_plain"] = []
    for ci, cid in ((0, "C1"), (1, "C2")):
        for si, side in ((0, 8), (1, 14)):
            for arm in ARMS:
                base = idx[(cid, side, "plain", arm)]["per_frame_n_inside"]
                for content in CONTENT_ARMS:
                    if content == "plain":
                        continue
                    cur = idx[(cid, side, content, arm)]["per_frame_n_inside"]
                    d = np.asarray(cur, float) - np.asarray(base, float)
                    m, sd = float(d.mean()), float(d.std(ddof=1))
                    se = sd / np.sqrt(len(d))
                    from scipy import stats
                    t = float(stats.t.ppf(0.975, len(d) - 1))
                    out["paired_vs_plain"].append({
                        "corpus": cid, "side": side, "content": content,
                        "arm": arm, "n": len(d), "delta_mean": m,
                        "lo": m - t * se, "hi": m + t * se, "sd": sd})
                    log(f"  [D {cid}|s{side:2d}|{content:8s}|{arm:11s}] "
                        f"delta n_inside = {m:+.3f} "
                        f"[{m - t * se:+.3f}, {m + t * se:+.3f}]")

    log("== CUE (frame data only) ==")
    for k, v in out["cue"].items():
        log(f"  r(dIn,dOut) {k:22s} = " + ("None" if v is None else f"{v:+.4f}"))

    out["wall_s"] = time.time() - t_start
    with open(os.path.join(ROOT, "results", "surface_assignment.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    log(f"== done in {out['wall_s']:.0f}s")
    logf.close()


if __name__ == "__main__":
    main()
