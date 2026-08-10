"""phi_measure — DOES THE SUBSTRATE SEE PHI?

Pre-registration: VISION_PHI_PREREG.md, committed 8edacf62 BEFORE any phi
number. Seeds 86000-86999.

Two dots flashing in alternation. A system computing motion from pixel
differences sees TWO SEPARATE ON/OFF EVENTS. A system inferring motion as the
EXPLANATION of change sees ONE DOT MOVING. Humans see the second.

THREE LEVELS ARE MEASURED, NOT ONE (prereg 0.1) -- because "does THE SUBSTRATE
see phi" is a different question from "does the motion sensor see phi", and the
motion rung consumed only L1:

  L1  motion_group_world.vector_field    SAD block match, radius = block = 4px
  L2  Substrate::segment_and_track       radius = span + 2.0 (Manhattan)
  L3  Substrate::track_identity          radius is a CALLER ARGUMENT

Every verdict is EXACT EQUALITY -- v == (0,S) vs v == (0,0); matched vs
births+deaths. No threshold is introduced by this rung (PROTOCOL 13).

C-POS IS THE DEAD-INSTRUMENT ARM AND THE RUN ABORTS IF IT DOES NOT FIRE.
C-RIGID IS THE INTERPRETIVE CONTROL: it is what makes a null diagnosable
(correspondence-across-a-gap failing, versus general blindness).
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

import substrate_rs as srs                                   # noqa: E402
from domains import motion_group_world as mgw                # noqa: E402

SEED_BLOCK = 86000

# INHERITED UNCHANGED from VISION_MOTION_OBJECTS so the C1 re-reading is
# like-for-like. BLOCK is the motion rung's own DECLARED magic-number residual.
GRID = 72
BLOCK = 4
NCELL = GRID // BLOCK          # 18x18
K_LUM = 16

DOT = BLOCK                    # one lattice cell -- the smallest thing the
                               # sensor can represent; inherited from BLOCK.
ROW = 36                       # mid-field
COL = 16                       # source column; 16 + S stays on-field for S<=20

SEPS = tuple(range(1, 21))            # M2 -- the independent variable
ISIS = (0, 1, 2, 3, 4)                # M3 -- blank frames between
ISI_SEPS = (2, 4, 8)
L3_RADII = (1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0)
L3_SEPS = (2, 4, 8, 16)

N_PAIRS_M6 = 40                       # the motion rung's own registered n
N_FRAMES_M6 = 45
M6_RADII = (4, 8, 16, 32)
CORPORA = (("C1", "cartoon", 0, "08630d4b"),
           ("C2", "live-action", 3, "119eca43"))


def _vp():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    m = importlib.util.module_from_spec(spec)
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
    return {"n": int(n), "mean": m, "lo": m - t * se, "hi": m + t * se}


# --- stimuli ----------------------------------------------------------------
def uniform_bg():
    """A constant field -- a textureless block SADs to a tie at every offset and
    the tie-break returns (0,0), so any non-zero vector is attributable to the
    dot. Draws NO seed: kept a separate function so the seed audit reports the
    truth (a `background(kind, seed)` with an early return would statically
    resolve a seed at a sink the uniform branch never reaches)."""
    return np.full((GRID, GRID), 32.0)


def textured_bg(seed):
    """iid background -- realistic and harder: the background is matchable, so
    the dot's cell must compete with it."""
    return np.random.default_rng(seed).integers(
        0, 256, size=(GRID, GRID)).astype(float)


def background(kind, seed=None):
    return uniform_bg() if kind == "uniform" else textured_bg(seed)


def with_dot(bg, row, col):
    f = bg.copy()
    f[row:row + DOT, col:col + DOT] = 255.0
    return f


def phi_sequence(bg, sep, isi):
    """Frame 1: dot at COL. `isi` frames of BACKGROUND ALONE. Frame 2: dot at
    COL+sep. This is the only way a frame-sequential system admits an ISI."""
    return ([with_dot(bg, ROW, COL)] + [bg.copy()] * isi
            + [with_dot(bg, ROW, COL + sep)])


def rigid_sequence(bg, sep):
    """C-RIGID -- the SAME TOTAL displacement delivered as CONTINUOUS motion:
    per-frame step <= BLOCK, so every hop is inside the sensor's aperture.
    If the sensor tracks this and fails phi, the failure is specifically
    correspondence ACROSS A GAP, not general blindness."""
    frames, c = [], COL
    while c < COL + sep:
        frames.append(with_dot(bg, ROW, c))
        c = min(c + BLOCK, COL + sep)
    frames.append(with_dot(bg, ROW, COL + sep))
    return frames


def src_cell():
    return (ROW // BLOCK, COL // BLOCK)


# --- L1 ---------------------------------------------------------------------
def l1_field(a, b, radius=None):
    return mgw.vector_field(a, b, BLOCK, radius=radius)


def l1_raw(vf):
    """The RAW field: reported as output, never as interpretation."""
    nz = [((int(r), int(c)), (float(vf[r, c, 0]), float(vf[r, c, 1])))
          for r in range(vf.shape[0]) for c in range(vf.shape[1])
          if vf[r, c, 0] != 0.0 or vf[r, c, 1] != 0.0]
    dist = {}
    for _, v in nz:
        dist[str(v)] = dist.get(str(v), 0) + 1
    return {"n_nonzero": len(nz), "distinct_vectors": dist,
            "nonzero_cells": nz[:24]}


def l1_verdict(vf, sep):
    """EXACT equality. No threshold, no partial credit (prereg 2/M1)."""
    r, c = src_cell()
    v = (float(vf[r, c, 0]), float(vf[r, c, 1]))
    if v == (0.0, float(sep)):
        return "PHI", v
    if v == (0.0, 0.0):
        return "TWO_EVENTS", v
    return "OTHER", v


def l1_sequence_response(frames, sep):
    """M3's response, defined over the WHOLE sequence and DELIBERATELY
    GENEROUS: 1 iff ANY consecutive pair links the source cell to the full
    displacement. A system that bridged the gap would be credited."""
    per_pair = []
    hit = 0
    for i in range(len(frames) - 1):
        vf = l1_field(frames[i], frames[i + 1])
        vd, v = l1_verdict(vf, sep)
        per_pair.append({"pair": i, "verdict": vd, "v_src": v,
                         "n_nonzero": int(np.count_nonzero(vf.any(axis=-1)))})
        if vd == "PHI":
            hit = 1
    return hit, per_pair


# --- L3 ---------------------------------------------------------------------
def l3(sep, radius):
    """track_identity on two Entity nodes at the two dot CENTROIDS -- the
    generous case: perfect segmentation is handed to it for free."""
    s = srs._native.Substrate()
    cy = float(ROW) + DOT / 2.0
    prev = s.add_node("Entity", {"feat": [cy, float(COL) + DOT / 2.0]})
    cur = s.add_node("Entity", {"feat": [cy, float(COL + sep) + DOT / 2.0]})
    res = s.track_identity([prev], [cur], "feat", "identity", float(radius))
    return {"matched": len(res["matched"]), "births": len(res["births"]),
            "deaths": len(res["deaths"]),
            "verdict": "MATCHED" if res["matched"] else "TWO_EVENTS"}


# --- L2 ---------------------------------------------------------------------
def quantize(frame, k):
    f = np.asarray(frame, float)
    lo, hi = float(f.min()), float(f.max())
    if hi <= lo:
        return np.zeros_like(f, dtype=int)
    return np.clip(((f - lo) / (hi - lo) * k).astype(int), 0, k - 1)


def l2_setup():
    """`segment_and_track` writes `game -has_region-> Region` and
    `cell -within-> Region` through the ADMISSIBILITY-CHECKED `add_edge`.
    On a bare Substrate those productions do not exist, the edges are silently
    REFUSED, and every frame then sees ZERO priors -- so the mechanism reports
    TWO_EVENTS at every separation and looks like a clean phi null while being
    a DEAD INSTRUMENT. `seeds/region_grouping.json` declares them
    (WorldInstance -has_region-> Region, WorldInstance -within-> Region), so
    the hub and the cells must both be WorldInstance. The productions are READ
    OFF THAT SEED FILE, not hand-written here -- `region_grouping` is absent
    from `substrate/seeds.py`'s registry so it cannot be loaded by id, but its
    graph data is still the source. `l2_selftest` proves the wiring is live
    before any L2 verdict is read."""
    s = srs._native.Substrate()
    with open(os.path.join(ROOT, "seeds", "region_grouping.json")) as fh:
        for prod in json.load(fh)["productions"]:
            s.add_production(prod)
    game = s.add_node("WorldInstance", {"frame": 0.0})
    cells = []
    for r in range(GRID):
        for c in range(GRID):
            cells.append(s.add_node("WorldInstance",
                                    {"row": float(r), "col": float(c)}))
    cell_ids = [int(str(n).lstrip("#")) for n in cells]
    return s, game, cell_ids


def l2_regions(s, game):
    out = []
    for n in s.neighbours(game, "has_region"):
        a = s.node(n)["attrs"]
        out.append({"id": int(str(n).lstrip("#")),
                    "value": float(a.get("rvalue", -1)),
                    "count": float(a.get("count", 0)),
                    "cy": float(a.get("cy", 0)), "cx": float(a.get("cx", 0)),
                    "drow": float(a.get("drow", 0)),
                    "dcol": float(a.get("dcol", 0))})
    return out


def l2_run(frames):
    """segment_and_track over a frame SEQUENCE. The dot Region SURVIVING with a
    non-zero dcol is correspondence; the Region being removed and a fresh one
    minted is two events. `remove_node` makes death DESTRUCTIVE here, so
    survival is read by NODE ID."""
    s, game, cell_ids = l2_setup()
    hist = []
    for f in frames:
        q = quantize(f, K_LUM)
        s.segment(game, GRID, GRID, [int(v) for v in q.ravel()], cell_ids)
        hist.append(l2_regions(s, game))
    return hist


def l2_verdict(hist, sep):
    """The DOT region is the non-ground one (ground = the largest component).
    Correspondence <=> the same node id carries a non-zero dcol equal to sep."""
    if len(hist) < 2:
        return "NO_DATA", {}
    first = min(hist[0], key=lambda r: r["count"]) if hist[0] else None
    last = min(hist[-1], key=lambda r: r["count"]) if hist[-1] else None
    if first is None or last is None:
        return "NO_DATA", {}
    same_id = (first["id"] == last["id"])
    dcol = last["dcol"]
    return ("MATCHED" if same_id and dcol != 0.0 else "TWO_EVENTS"), {
        "first_id": first["id"], "last_id": last["id"], "same_id": same_id,
        "last_dcol": dcol, "last_drow": last["drow"],
        "n_regions_first": len(hist[0]), "n_regions_last": len(hist[-1])}


def l2_selftest():
    """L2's DEAD-INSTRUMENT ARM. A dot that does NOT move at all must be
    MATCHED (a stationary region trivially overlaps its own prior). If the
    `has_region` wiring is refused, priors are always empty, nothing is ever
    matched, and L2 reports TWO_EVENTS at EVERY separation -- a perfect,
    entirely fake phi null. This arm fires on the wiring, not on the
    hypothesis, so it separates 'L2 says no' from 'L2 cannot say yes'."""
    bg = uniform_bg()
    f = with_dot(bg, ROW, COL)
    hist = l2_run([f, f])
    vd, det = l2_verdict(hist, 0)
    alive = (len(hist[0]) > 0 and len(hist[-1]) > 0 and det.get("same_id") is True)
    return {"n_regions": [len(h) for h in hist], "detail": det,
            "wiring_live": bool(alive)}


# --- controls ---------------------------------------------------------------
def controls():
    out = {}
    tex = background("textured", 86000)

    # C-POS -- the DEAD-INSTRUMENT arm. Must ACTUALLY FIRE.
    vf = l1_field(with_dot(tex, ROW, COL), with_dot(tex, ROW, COL + BLOCK))
    vd, v = l1_verdict(vf, BLOCK)
    out["C_POS"] = {"verdict": vd, "v_src": v, "raw": l1_raw(vf)}

    # C-NULL -- no change at all.
    f = with_dot(tex, ROW, COL)
    vf0 = l1_field(f, f)
    out["C_NULL"] = {"n_nonzero": int(np.count_nonzero(vf0.any(axis=-1))),
                     "all_zero": bool(not vf0.any())}

    # C-RIGID -- the SAME total displacement, delivered CONTINUOUSLY.
    rigid = {}
    for kind, seed in (("uniform", None), ("textured", 86100)):
        bg = background(kind, seed)
        for sep in SEPS:
            frames = rigid_sequence(bg, sep)
            hops = []
            for i in range(len(frames) - 1):
                vfr = l1_field(frames[i], frames[i + 1])
                step = min(BLOCK, COL + sep - (COL + i * BLOCK))
                r, c = ROW // BLOCK, (COL + i * BLOCK) // BLOCK
                hops.append((float(vfr[r, c, 0]), float(vfr[r, c, 1])) ==
                            (0.0, float(step)))
            rigid[f"{kind}_S{sep}"] = {"n_hops": len(hops),
                                       "tracked_all": bool(all(hops)),
                                       "n_tracked": int(sum(hops))}
    out["C_RIGID"] = rigid

    # NOISE -- a dot at an independent random position in each frame.
    rng = np.random.default_rng(86200)
    bg = uniform_bg()
    verdicts = []
    for _ in range(20):
        c1 = int(rng.integers(0, (GRID - DOT) // BLOCK)) * BLOCK
        c2 = int(rng.integers(0, (GRID - DOT) // BLOCK)) * BLOCK
        r1 = int(rng.integers(0, (GRID - DOT) // BLOCK)) * BLOCK
        r2 = int(rng.integers(0, (GRID - DOT) // BLOCK)) * BLOCK
        vfn = l1_field(with_dot(bg, r1, c1), with_dot(bg, r2, c2))
        verdicts.append(int(np.count_nonzero(vfn.any(axis=-1))))
    out["NOISE"] = {"n_trials": len(verdicts),
                    "mean_nonzero_cells": float(np.mean(verdicts)),
                    "max_nonzero_cells": int(max(verdicts))}
    return out


# --- M6 ---------------------------------------------------------------------
def m6_corpus(frames):
    """The C1 RE-READING. Per lattice cell, the four-way classification split at
    EXACTLY ZERO (a constant-free split): Delta = max|a-b| over the block's own
    pixels, against whether the sensor issued a vector."""
    per = {"identical_pairs": 0, "n_pairs": 0,
           "still": 0, "spurious": 0, "change_no_motion": 0, "motion": 0,
           "cells": 0}
    conv = {r: 0 for r in M6_RADII}
    cnm_total = 0
    share_motion = []
    for t in range(min(N_PAIRS_M6, len(frames) - 1)):
        a, b = np.asarray(frames[t], float), np.asarray(frames[t + 1], float)
        per["n_pairs"] += 1
        if np.array_equal(a, b):
            per["identical_pairs"] += 1
        d = np.abs(a - b).reshape(NCELL, BLOCK, NCELL, BLOCK).max(axis=(1, 3))
        vf = l1_field(a, b)
        nzv = vf.any(axis=-1)
        chg = d > 0.0
        per["still"] += int(np.count_nonzero(~chg & ~nzv))
        per["spurious"] += int(np.count_nonzero(~chg & nzv))
        cnm = chg & ~nzv
        per["change_no_motion"] += int(np.count_nonzero(cnm))
        per["motion"] += int(np.count_nonzero(chg & nzv))
        per["cells"] += int(nzv.size)
        share_motion.append(float(np.count_nonzero(nzv)) / nzv.size)
        # THE APERTURE DIAGNOSTIC (prereg M6): do the change-without-motion
        # cells acquire a vector at a WIDER radius? An instrument, not an arm.
        cnm_total += int(np.count_nonzero(cnm))
        for rad in M6_RADII:
            vfr = l1_field(a, b, radius=rad)
            conv[rad] += int(np.count_nonzero(cnm & vfr.any(axis=-1)))
    n = max(per["cells"], 1)
    return {**per,
            "frac_identical_pairs": per["identical_pairs"] / max(per["n_pairs"], 1),
            "share_still": per["still"] / n,
            "share_spurious": per["spurious"] / n,
            "share_change_no_motion": per["change_no_motion"] / n,
            "share_motion": per["motion"] / n,
            "nonzero_vector_share_ci": ci95(share_motion),
            "cnm_total": cnm_total,
            "cnm_converted_at_radius": {str(r): conv[r] for r in M6_RADII},
            "cnm_convert_frac_at_radius": {
                str(r): (conv[r] / cnm_total if cnm_total else None)
                for r in M6_RADII}}


def main():
    t0 = time.time()
    rep = {"provenance": ep.provenance_line(),
           "config": {"GRID": GRID, "BLOCK": BLOCK, "NCELL": NCELL,
                      "DOT": DOT, "ROW": ROW, "COL": COL, "K_LUM": K_LUM,
                      "seed_block": SEED_BLOCK}}

    print("== controls (the run ABORTS if the dead-instrument arm does not fire)")
    ctl = controls()
    rep["controls"] = ctl
    if ctl["C_POS"]["verdict"] != "PHI":
        raise SystemExit(
            f"C-POS DEAD-INSTRUMENT CONTROL DID NOT FIRE: a dot translating by "
            f"exactly one block reported {ctl['C_POS']['v_src']}, expected "
            f"(0.0, {float(BLOCK)}). The sensor cannot see motion it CAN reach; "
            f"nothing downstream is interpretable. RUN VOID.")
    if not ctl["C_NULL"]["all_zero"]:
        raise SystemExit("C-NULL: an unchanged frame pair produced a non-zero "
                         "field. RUN VOID.")
    print("   C-POS fired:", ctl["C_POS"]["verdict"], ctl["C_POS"]["v_src"])

    l2s = l2_selftest()
    rep["controls"]["L2_selftest"] = l2s
    if not l2s["wiring_live"]:
        raise SystemExit(
            f"L2 WIRING IS DEAD: a STATIONARY dot was not matched to its own "
            f"prior ({l2s}). segment_and_track's has_region/within edges are "
            f"being refused, so priors are always empty and L2 would report "
            f"TWO_EVENTS at every separation -- a fake phi null. RUN VOID.")
    print("   L2 wiring live:", l2s["n_regions"], l2s["detail"].get("same_id"))

    # ---- M1 -- the RAW report, first -----------------------------------
    m1 = {}
    for kind, seed in (("uniform", None), ("textured", 86000)):
        bg = background(kind, seed)
        vf = l1_field(with_dot(bg, ROW, COL), with_dot(bg, ROW, COL + 8))
        vd, v = l1_verdict(vf, 8)
        tr, tc = ROW // BLOCK, (COL + 8) // BLOCK
        m1[kind] = {"S": 8, "verdict": vd, "v_source_cell": v,
                    "v_target_cell": (float(vf[tr, tc, 0]), float(vf[tr, tc, 1])),
                    "raw": l1_raw(vf)}
    rep["M1_raw"] = m1
    print("== M1", json.dumps(m1, default=str)[:400])

    # ---- M2 -- separation dependence -----------------------------------
    m2 = {}
    for kind, seed in (("uniform", None), ("textured", 86000)):
        bg = background(kind, seed)
        rows = []
        for sep in SEPS:
            vf = l1_field(with_dot(bg, ROW, COL), with_dot(bg, ROW, COL + sep))
            vd, v = l1_verdict(vf, sep)
            rows.append({"S": sep, "verdict": vd, "v_src": v,
                         "n_nonzero": int(np.count_nonzero(vf.any(axis=-1)))})
        m2[kind] = rows
        hi = [r["S"] for r in rows if r["verdict"] == "PHI"]
        m2[f"{kind}_max_S_with_correspondence"] = max(hi) if hi else None
    rep["M2_separation_L1"] = m2
    print("== M2 L1 max S:", m2["uniform_max_S_with_correspondence"],
          m2["textured_max_S_with_correspondence"])

    # L2 + L3 separation
    m2b = {"L2": [], "L3": []}
    bgu = uniform_bg()
    for sep in SEPS:
        hist = l2_run([with_dot(bgu, ROW, COL), with_dot(bgu, ROW, COL + sep)])
        vd, det = l2_verdict(hist, sep)
        m2b["L2"].append({"S": sep, "verdict": vd, **det})
    for sep in L3_SEPS:
        for rad in L3_RADII:
            m2b["L3"].append({"S": sep, "radius": rad, **l3(sep, rad)})
    hiL2 = [r["S"] for r in m2b["L2"] if r["verdict"] == "MATCHED"]
    m2b["L2_max_S_with_correspondence"] = max(hiL2) if hiL2 else None
    m2b["L3_min_radius_matching"] = {
        str(sep): min((r["radius"] for r in m2b["L3"]
                       if r["S"] == sep and r["verdict"] == "MATCHED"),
                      default=None) for sep in L3_SEPS}
    rep["M2_separation_L2_L3"] = m2b
    print("== M2 L2 max S:", m2b["L2_max_S_with_correspondence"],
          "L3 min radius:", m2b["L3_min_radius_matching"])

    # ---- M3 -- ISI dependence ------------------------------------------
    m3 = {}
    for kind, seed in (("uniform", None), ("textured", 86000)):
        bg = background(kind, seed)
        for sep in ISI_SEPS:
            for isi in ISIS:
                frames = phi_sequence(bg, sep, isi)
                hit, per_pair = l1_sequence_response(frames, sep)
                key = f"{kind}_S{sep}_ISI{isi}"
                m3[key] = {"L1_response": hit, "L1_pairs": per_pair}
                if kind == "uniform":
                    hist = l2_run(frames)
                    vd, det = l2_verdict(hist, sep)
                    m3[key]["L2_verdict"] = vd
                    m3[key]["L2_detail"] = det
    rep["M3_isi"] = m3
    curve = {f"S{sep}": [m3[f"uniform_S{sep}_ISI{i}"]["L1_response"]
                         for i in ISIS] for sep in ISI_SEPS}
    rep["M3_isi_curve_L1_uniform"] = {"isi": list(ISIS), **curve}
    print("== M3 ISI curve (L1, uniform):", curve)

    # ---- M6 -- the C1 re-reading ---------------------------------------
    vp = _vp()
    m6 = {}
    for name, what, epi, pin in CORPORA:
        frames, meta = vp.jellyfin_frames(N_FRAMES_M6, every=1, start_s=300,
                                          size=GRID, episode_index=epi)
        if not str(meta.get("episode_id", "")).startswith(pin):
            raise SystemExit(f"{name} PIN MISMATCH: {meta.get('episode_id')} "
                             f"!= {pin}... RUN VOID.")
        m6[name] = {"what": what, "episode_id": meta.get("episode_id"),
                    **m6_corpus(frames)}
        print(f"== M6 {name}: motion={m6[name]['share_motion']:.4f} "
              f"cnm={m6[name]['share_change_no_motion']:.4f} "
              f"identical_pairs={m6[name]['frac_identical_pairs']:.3f} "
              f"convert={m6[name]['cnm_convert_frac_at_radius']}", flush=True)
    rep["M6_c1_rereading"] = m6

    rep["elapsed_s"] = round(time.time() - t0, 1)
    out = os.path.join(ROOT, "results", "phi_measure.json")
    with open(out, "w") as fh:
        json.dump(rep, fh, indent=1, default=str)
    print("wrote", out, "in", rep["elapsed_s"], "s")


if __name__ == "__main__":
    main()
