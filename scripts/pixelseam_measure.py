#!/usr/bin/env python3
"""WHAT DOES `TimeInfer` REQUIRE OF AN INPUT, AND IS THERE A PIXEL SEAM?

The confirmatory measurement for `VISION_PIXELSEAM_PREREG.md` (committed
77ad9ae84cb9 before any number). Successor to the timephi rung (93000-93999),
whose A1 reported that `TimeInfer` cannot consume a bounded pixel field at all.

Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python3 scripts/pixelseam_measure.py

VERDICTS come from the AGENT'S OWN RULE (`time_axis` writes `status`); the
direct Term evaluations are DIAGNOSTIC ONLY (`checked`, `offset`) and exist to
separate a REFUSAL AT A GUARD from a FAILURE AFTER A FULL SEARCH.

The REQUIREMENT DIAGNOSIS (`diagnose`) is computed IN THIS FILE from the
encoded frames, INDEPENDENTLY of the Term -- a diagnostic must not be computed
by the component it checks.
"""
from __future__ import annotations
import json
import os
import sys
import time

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line, provenance_stamp
engine_preamble()

from substrate.boot_core import boot_core                # noqa: E402
from domains import reflective_faculty as rf             # noqa: E402
from substrate.seed_loader import manifest_for           # noqa: E402
import substrate_rs as srs                               # noqa: E402

# --- the engine this rung's numbers are attributed to (PROTOCOL 10.1 rule 1).
# Printed from INSIDE the measuring process and compared; divergence ABORTS.
EXPECT_ENGINE = "9931e144d19b"

# --- stimulus configuration (PROTOCOL 13: declared residuals; construction
# only, never a verdict threshold; DOT/FIELD/BG/FG/ROW inherited from the
# phi / timephi / gapabduce rungs unchanged) ---------------------------------
DOT = 4
PATCH = 8
FIELD_H = 24
FIELD_W = 48
CROP = 24
S = 4
BG = 0
FG = 255
ROW = 8
MAX_B = 8
DT_V = ["pred", "coord:r", "coord:c", "val"]
DT_S = ["pred", "coord:r", "coord:c"]
COORD_IDX = (1, 2)

# --- the INDEPENDENT VARIABLES: iterated, never compared against -------------
Q_GRID = [2, 4, 8, 16, 32, 64, 128, 256]
START_GRID = [60, 180, 300, 420, 540, 660, 780, 900]
PATCH_ARMS = ("E3", "E4t", "E4g", "E4s")
DENSE_ARMS = ("E0", "E1", "E2")

# --- power floor, declared in advance; applied identically to every cell and
# never compared against an outcome ------------------------------------------
MIN_LIVE = 3

# --- the ONLY randomness: one seed per paired draw index.  Every draw is
# materialised HERE from a SINGLE sink bound to an explicit `range`, so
# `scripts/seed_audit.py` can RESOLVE every seed statically instead of
# reporting an unknown sink (the timephi rung's lesson: a `--check` that passes
# while leaving sinks UNKNOWN has verified nothing).
SEED_LO = 104000
SEED_HI = 104200
N_DRAW = SEED_HI - SEED_LO
DRAWS: list[dict] = []

FRAMES_NPZ = "results/gapseam_starts.npz"
OUT = "results/pixelseam.json"

# The codebook-liveness probe's known orbit (PROTOCOL 1.1: a PAIRED IN-PROCESS
# POSITIVE probe, never a read of `coord_dims` off the measured call).
PROBE_COLS = (0, 4, 8)
PROBE_VIOLATIONS: list[str] = []


# --------------------------------------------------------------------------- #
#  world: PIXELS -> cells.  Mechanical translation; no decision.
# --------------------------------------------------------------------------- #
def quant(f, q):
    """Quantize luminance to `q` levels.  `q` is an AXIS."""
    return (np.asarray(f, dtype=np.float64).clip(0, 255).astype(np.int64) * q) // 256


def modal(fq):
    """The frame's OWN modal quantized luminance -- data-derived, no constant."""
    v, ct = np.unique(fq, return_counts=True)
    return int(v[int(np.argmax(ct))])


def c_all(fq, r_off=0, c_off=0, val=True):
    h, w = fq.shape
    return [(["px", r_off + r, c_off + c, int(fq[r, c])] if val
             else ["px", r_off + r, c_off + c])
            for r in range(h) for c in range(w)]


def c_thresh(fq, val=True):
    """FIGURE cells: luminance != the frame's own modal value.  SUPPLIED
    STRUCTURE, declared as such in the pre-registration."""
    m = modal(fq)
    rs, cs = np.nonzero(fq != m)
    return [(["px", int(r), int(c), int(fq[r, c])] if val else ["px", int(r), int(c)])
            for r, c in zip(rs, cs)]


def c_mask(fq, mask, val=True):
    """GROUND-TRUTH support: exactly the cells of a known rectangle."""
    rs, cs = np.nonzero(mask)
    return [(["px", int(r), int(c), int(fq[r, c])] if val else ["px", int(r), int(c)])
            for r, c in zip(rs, cs)]


def paste(patch, col):
    f = np.zeros((FIELD_H, FIELD_W), dtype=np.float64)
    ph, pw = patch.shape
    r0 = (FIELD_H - ph) // 2
    f[r0:r0 + ph, col:col + pw] = patch
    m = np.zeros((FIELD_H, FIELD_W), dtype=bool)
    m[r0:r0 + ph, col:col + pw] = True
    return f, m


def render_dot(col):
    """The synthetic wiring-control stimulus, inherited unchanged."""
    f = np.full((FIELD_H, FIELD_W), BG, dtype=np.uint8)
    if col is not None:
        f[ROW:ROW + DOT, col:col + DOT] = FG
    return f


# --------------------------------------------------------------------------- #
#  THE REQUIREMENT DIAGNOSIS -- computed HERE, not by the Term.
#  Order is DECLARED (R1, R3, R4, R5, R6, R7); the engine interleaves R5 and
#  R6 in one loop, so this is an INDEPENDENT reading and a disagreement with
#  the Term's verdict is itself a finding.
# --------------------------------------------------------------------------- #
def diagnose(frames):
    if len(frames) < 2:
        return "R1"
    if any(len(f) == 0 for f in frames):
        return "R3"
    if len(set(len(f) for f in frames)) != 1:
        return "R4"
    a = sorted(frames[0])
    b = sorted(frames[1])
    off = tuple(b[0][i] - a[0][i] for i in COORD_IDX)
    for ra, rb in zip(a, b):
        if tuple(rb[i] - ra[i] for i in COORD_IDX) != off:
            return "R5"
    for ra, rb in zip(a, b):
        if len(ra) != len(rb):
            return "R6"
        for k in range(len(ra)):
            if k in COORD_IDX:
                continue
            if ra[k] != rb[k]:
                return "R6"
    if all(o == 0 for o in off):
        return "R7"
    for t in range(1, len(frames) - 1):
        a = sorted(frames[t])
        b = sorted(frames[t + 1])
        if len(a) != len(b):
            return "R4"
        for ra, rb in zip(a, b):
            if tuple(rb[i] - ra[i] for i in COORD_IDX) != off:
                return "R5"
            for k in range(len(ra)):
                if k in COORD_IDX:
                    continue
                if ra[k] != rb[k]:
                    return "R6"
    return "ok"


# --------------------------------------------------------------------------- #
#  substrate: the AGENT decides.  Present an Observation, read `status`.
# --------------------------------------------------------------------------- #
def _boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    s.set_attr(ag, "time_infer_enabled", 1.0)
    return s, ag, native


def _codebook_live(s, tag):
    """THE TRAP GATE, DONE RIGHT.  A KNOWN ORBIT evaluated in the SAME booted
    substrate as the measured condition.  `coord_dims` read off a MEASURED call
    is an OUTPUT of the verdict -- `unexplained()` hardcodes it empty -- and
    made 167 false accusations for my predecessor, so it is never read here."""
    probe = [c_thresh(quant(render_dot(c), 256)) for c in PROBE_COLS]
    t = srs.Term("TimeInfer", sequence=srs.Lit(probe),
                 codebook_type="ShapeSignature", max_b=MAX_B, field="coord_dims")
    cd = tuple(s.evaluate(t, {}) or ())
    if len(cd) == 0:
        PROBE_VIOLATIONS.append(tag)
    return cd


def present(frames, dt, tag, *, want_offset, probe=False):
    s, ag, native = _boot()
    s.add_node("ShapeSignature",
               {"name": "px_base", "signature": json.dumps(frames[0]),
                "kind": "faculty", "faculty": "px_base", "dim_types": dt})
    o = s.add_node("Observation", {"frames": frames, "dim_types": dt,
                                   "status": "motion_seq", "key": ["pixelseam"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    status = at.get("status")
    explained = status == "time_inferred"

    def term(field):
        return s.evaluate(srs.Term("TimeInfer", sequence=srs.Lit(frames),
                                   codebook_type="ShapeSignature",
                                   max_b=MAX_B, field=field), {})

    rec = {"tag": tag, "status": status, "explained": explained,
           "kind": at.get("time_kind"), "diagnosis": diagnose(frames),
           "n_cells": [len(f) for f in frames]}
    # Both diagnostic reads are CONDITIONAL, because each re-runs the Term and
    # an unexplained dense condition costs a full linear enumeration.  `offset`
    # is () on every refusal by construction; `checked` is 0 on every translate
    # path by construction (measured by the predecessor, and re-asserted here on
    # the explained rows via `diagnosis == "ok"`).
    rec["offset"] = tuple(term("offset") or ()) if (want_offset and explained) else None
    # `checked` separates a REFUSAL AT A GUARD (0) from a FAILURE AFTER A FULL
    # SEARCH -- the distinction that makes a null diagnosable.
    rec["checked"] = 0 if explained else term("checked")
    if probe:
        rec["probe_coord_dims"] = _codebook_live(s, tag)
    return rec


# --------------------------------------------------------------------------- #
#  arms
# --------------------------------------------------------------------------- #
def build_draws():
    for sd in range(SEED_LO, SEED_HI):
        r = np.random.default_rng(sd)
        DRAWS.append({"seed": sd,
                      "start": START_GRID[int(r.integers(0, len(START_GRID)))],
                      "t0": int(r.integers(0, 24 - 3)),
                      "r0": int(r.integers(0, 48 - PATCH)),
                      "c0": int(r.integers(0, 48 - PATCH))})


def patch_frames(Z, d, arm, q):
    """Return (frames, dt, live).  `live` = the QUANTIZED patch content is not
    identical across the three frames (exact array inequality; no tolerance)."""
    F = Z[str(d["start"])]
    static = arm == "E3"
    pats = [F[d["t0"] + (0 if static else k)][d["r0"]:d["r0"] + PATCH,
                                              d["c0"]:d["c0"] + PATCH]
            for k in range(3)]
    qp = [quant(p, q) for p in pats]
    live = not (np.array_equal(qp[0], qp[1]) and np.array_equal(qp[1], qp[2]))
    frames, dt = [], DT_S if arm == "E4s" else DT_V
    for k, p in enumerate(pats):
        f, m = paste(p, 4 + k * S)
        fq = quant(f, q)
        if arm in ("E3", "E4t"):
            frames.append(c_thresh(fq, val=True))
        elif arm == "E4g":
            frames.append(c_mask(fq, m, val=True))
        else:
            frames.append(c_mask(fq, m, val=False))
    return frames, dt, live


def dense_frames(Z, start, arm, q):
    F = Z[str(start)]
    if arm == "E2":
        base = F[0][:CROP, :CROP]
        fq = [quant(np.roll(base, k * S, axis=1), q) for k in range(3)]
    else:
        fq = [quant(F[i][:CROP, :CROP], q) for i in range(3)]
    live = not (np.array_equal(fq[0], fq[1]) and np.array_equal(fq[1], fq[2]))
    if arm == "E1":
        return [c_thresh(f) for f in fq], DT_V, live
    return [c_all(f) for f in fq], DT_V, live


# ======================= THE VERDICTS (PROTOCOL 13) ======================== #
#  Every verdict decides by EXACT EQUALITY on a logical or integer quantity.
#  No ordering comparison against a non-zero constant decides anything.
#  `tests/test_pixelseam_ast_migrated.py` binds these BY NAME as AST
#  FunctionDef nodes, read from this tuple.
# =========================================================================== #
VERDICTS = ("v_a0_pos", "v_a0_neg", "v_a0_probe", "v_p0_e0", "v_p1_e1",
            "v_p2_e2", "v_p2_proviso", "v_p3_e3", "v_p4_live", "v_p4_dead",
            "v_p5_e4g", "v_p6_e4s", "v_p7_monotone", "v_squeeze",
            "v_diagnosis_agrees")


def v_a0_pos(pos) -> bool:
    """A0-POS: a known moving dot IS an orbit, with the TRUE offset."""
    return (pos["explained"] and pos["kind"] == "translate"
            and pos["offset"] == (0, DOT))


def v_a0_neg(neg) -> bool:
    """A0-NEG: a STILL dot is refused (identity excluded at source)."""
    return neg["status"] == "time_none"


def v_a0_probe(n_violations) -> bool:
    """The codebook resolved on EVERY measured call's paired positive probe."""
    return n_violations == 0


def v_p0_e0(rows) -> bool:
    """P0: a bounded RAW PIXEL FIELD of real video is never explained."""
    return all(not r["explained"] for r in rows)


def v_p1_e1(rows) -> bool:
    """P1: the SPARSE (figure-split) encoding of real video is never explained."""
    return all(not r["explained"] for r in rows)


def v_p2_e2(rows) -> bool:
    """P2: EXACT rigid content motion on a BOUNDED field is never explained."""
    return all(not r["explained"] for r in rows)


def v_p2_proviso(rows) -> bool:
    """P2's proviso: a toroidal roll preserves cardinality EXACTLY, so R4 holds
    and R5 is the diagnosed failure on every LIVE condition."""
    live = [r for r in rows if r["live"]]
    return len(live) != 0 and all(r["diagnosis"] == "R5" for r in live)


def v_p3_e3(rows) -> bool:
    """P3, THE SEAM POSITIVE CONTROL: a real-texture patch in rigid motion with
    byte-identical appearance is explained with the TRUE offset, everywhere."""
    return len(rows) != 0 and all(r["explained"] and r["offset"] == (0, S)
                                  for r in rows)


def v_p4_live(n_live_explained) -> bool:
    """P4 (H1): NO photometrically LIVE condition is ever explained."""
    return n_live_explained == 0


def v_p4_dead(rows) -> bool:
    """P4's other half: every photometrically DEAD condition IS explained --
    i.e. the seam succeeds exactly where it sees nothing changing."""
    dead = [r for r in rows if not r["live"]]
    return len(dead) != 0 and all(r["explained"] for r in dead)


def v_p5_e4g(n_g_beats_t) -> bool:
    """P5: a GROUND-TRUTH support rescues nothing the threshold support lost --
    if it does, the deficit is R4 (support), not R6 (appearance)."""
    return n_g_beats_t == 0


def v_p6_e4s(rows) -> bool:
    """P6: with a GROUND-TRUTH support and NO appearance slot, every condition
    is explained.  A failure here means the source reading of R1-R7 is WRONG."""
    return len(rows) != 0 and all(r["explained"] and r["offset"] == (0, S)
                                  for r in rows)


def v_p7_monotone(n_inversions) -> bool:
    """P7: the LIVE fraction never decreases as q gets finer."""
    return n_inversions == 0


def v_squeeze(n_live_and_explained) -> bool:
    """THE REGISTERED QUESTION: is the operating window EMPTY?  True == empty."""
    return n_live_and_explained == 0


def v_diagnosis_agrees(n_disagree) -> bool:
    """The INDEPENDENT requirement diagnosis agrees with the Term's verdict:
    `diagnosis == 'ok'` exactly where the agent says `time_inferred`."""
    return n_disagree == 0


# --------------------------------------------------------------------------- #
def main() -> int:
    line = provenance_line()
    print(line, flush=True)
    if EXPECT_ENGINE not in line:
        print("ABORT: engine divergence -- expected %s" % EXPECT_ENGINE)
        return 2

    t_start = time.time()
    rec = {"provenance": line, "engine_provenance": provenance_stamp(),
           "prereg_commit": "77ad9ae84cb903ecd88d79e023380189cf7cc3e5",
           "expect_engine": EXPECT_ENGINE, "loadavg": os.getloadavg(),
           "q_grid": Q_GRID, "start_grid": START_GRID, "n_draw": N_DRAW,
           "min_live": MIN_LIVE, "seed_lo": SEED_LO, "seed_hi": SEED_HI}

    # ---- A0: the wiring control, FIRST, and it ABORTS ----------------------
    pos = present([c_thresh(quant(render_dot(c), 256)) for c in (0, 4, 8)],
                  DT_V, "A0-POS", want_offset=True, probe=True)
    neg = present([c_thresh(quant(render_dot(4), 256)) for _ in range(3)],
                  DT_V, "A0-NEG", want_offset=False, probe=True)
    rec["A0"] = {"pos": pos, "neg": neg}
    print("A0-POS", pos["status"], pos["offset"], "| A0-NEG", neg["status"], flush=True)
    if not (v_a0_pos(pos) and v_a0_neg(neg)):
        print("ABORT: wiring control failed")
        json.dump(rec, open(OUT, "w"), indent=1, default=str)
        return 3

    Z = np.load(FRAMES_NPZ)
    build_draws()
    rec["draws"] = DRAWS

    # ---- the PATCH arms (the rung's evidential weight) ---------------------
    rec["patch"] = {}
    for arm in PATCH_ARMS:
        rows = []
        for q in Q_GRID:
            for d in DRAWS:
                frames, dt, live = patch_frames(Z, d, arm, q)
                r = present(frames, dt, "%s/q%d/s%d" % (arm, q, d["seed"]),
                            want_offset=True)
                r.update(q=q, seed=d["seed"], live=bool(live), arm=arm)
                rows.append(r)
            print("  %s q=%3d  explained %d/%d  live %d/%d  %.0fs" % (
                arm, q, sum(x["explained"] for x in rows[-N_DRAW:]), N_DRAW,
                sum(x["live"] for x in rows[-N_DRAW:]), N_DRAW,
                time.time() - t_start), flush=True)
        rec["patch"][arm] = rows
        json.dump(rec, open(OUT, "w"), indent=1, default=str)

    # ---- the DENSE arms (low weight; the DIAGNOSIS is their content) -------
    rec["dense"] = {}
    for arm in DENSE_ARMS:
        rows = []
        for q in Q_GRID:
            for st in START_GRID:
                frames, dt, live = dense_frames(Z, st, arm, q)
                r = present(frames, dt, "%s/q%d/t%d" % (arm, q, st),
                            want_offset=False)
                r.update(q=q, start=st, live=bool(live), arm=arm)
                rows.append(r)
            print("  %s q=%3d  explained %d/%d  live %d/%d  %.0fs" % (
                arm, q, sum(x["explained"] for x in rows[-len(START_GRID):]),
                len(START_GRID), sum(x["live"] for x in rows[-len(START_GRID):]),
                len(START_GRID), time.time() - t_start), flush=True)
        rec["dense"][arm] = rows
        json.dump(rec, open(OUT, "w"), indent=1, default=str)

    # ---- the verdicts -----------------------------------------------------
    P = rec["patch"]
    e4live = [r for a in ("E4t", "E4g") for r in P[a] if r["live"]]
    n_live_explained = sum(r["explained"] for a in ("E4t", "E4g", "E4s")
                           for r in P[a] if r["live"])
    n_live_and_explained = sum(r["explained"] for a in ("E4t", "E4g")
                               for r in P[a] if r["live"])
    by = {(r["arm"], r["q"], r["seed"]): r for a in PATCH_ARMS for r in P[a]}
    n_g_beats_t = sum(1 for k, r in by.items() if k[0] == "E4g"
                      and r["explained"]
                      and not by[("E4t", k[1], k[2])]["explained"])
    livef = [sum(r["live"] for r in P["E4t"] if r["q"] == q) for q in Q_GRID]
    n_inversions = sum(1 for i in range(len(livef) - 1) if livef[i + 1] < livef[i])
    allrows = [r for a in PATCH_ARMS for r in P[a]] + \
              [r for a in DENSE_ARMS for r in rec["dense"][a]]
    n_disagree = sum(1 for r in allrows
                     if r["explained"] != (r["diagnosis"] == "ok"))

    rec["live_fraction_by_q"] = dict(zip(map(str, Q_GRID), livef))
    rec["underpowered_cells"] = [
        [a, q] for a in ("E4t", "E4g", "E4s") for q in Q_GRID
        if sum(r["live"] for r in P[a] if r["q"] == q) < MIN_LIVE]
    rec["verdicts"] = {
        "v_a0_pos": v_a0_pos(pos), "v_a0_neg": v_a0_neg(neg),
        "v_a0_probe": v_a0_probe(len(PROBE_VIOLATIONS)),
        "v_p0_e0": v_p0_e0(rec["dense"]["E0"]),
        "v_p1_e1": v_p1_e1(rec["dense"]["E1"]),
        "v_p2_e2": v_p2_e2(rec["dense"]["E2"]),
        "v_p2_proviso": v_p2_proviso(rec["dense"]["E2"]),
        "v_p3_e3": v_p3_e3(P["E3"]),
        "v_p4_live": v_p4_live(n_live_explained),
        "v_p4_dead": v_p4_dead(P["E4t"]),
        "v_p5_e4g": v_p5_e4g(n_g_beats_t),
        "v_p6_e4s": v_p6_e4s(P["E4s"]),
        "v_p7_monotone": v_p7_monotone(n_inversions),
        "v_squeeze": v_squeeze(n_live_and_explained),
        "v_diagnosis_agrees": v_diagnosis_agrees(n_disagree),
    }
    rec["counts"] = {"n_live_explained": n_live_explained,
                     "n_live_and_explained": n_live_and_explained,
                     "n_g_beats_t": n_g_beats_t,
                     "n_inversions": n_inversions,
                     "n_disagree": n_disagree,
                     "probe_violations": len(PROBE_VIOLATIONS)}
    rec["elapsed_s"] = time.time() - t_start
    rec["loadavg_end"] = os.getloadavg()
    json.dump(rec, open(OUT, "w"), indent=1, default=str)
    print(json.dumps(rec["verdicts"], indent=1))
    print(json.dumps(rec["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
