#!/usr/bin/env python3
"""AN APPEARANCE-TOLERANT PAIRING FOR `TimeInfer` — IS IT PURCHASABLE?

The confirmatory measurement for `VISION_APPEARANCE_PREREG.md` (committed
7a888053 before any number).  Successor to the pixel-seam rung
(104000-104999), which isolated `TimeInfer`'s deficit on real photometry to
R6 -- appearance byte-identity -- and NOTHING else.

Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python3 scripts/appearance_measure.py --mode pilot
    PYTHONPATH=runners/dsl/python:. python3 scripts/appearance_measure.py --mode confirm

`--mode pilot` draws ONLY from ALREADY-BURNED seeds (104000+) and writes to a
pilot artifact.  `--mode confirm` is the registered run.  The default is
PILOT, deliberately: my predecessor invoked another rung's gate bare and it
defaulted to `confirm`, reburning that rung's block.  A gate that is safe to
READ is not therefore safe to RUN.

VERDICTS come from the AGENT'S OWN RULE (`time_axis` writes `status`).
`P_tol` is ALSO computed IN THIS FILE from the encoded frames, reaching no
substrate and no Term -- a diagnostic must not be computed by the component
it checks -- and the two are compared condition-by-condition (`n_disagree`).
"""
from __future__ import annotations
import argparse
import json
import math
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
EXPECT_ENGINE = "880607dff038"

# --- stimulus configuration (PROTOCOL 13: declared residuals; CONFIGURATION
# only, bound once, never a verdict threshold; inherited UNCHANGED from the
# phi / timephi / gapabduce / pixelseam rungs) -------------------------------
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
PRED_IDX = 0

# --- the INDEPENDENT VARIABLES: iterated, never compared against -------------
Q_GRID = [2, 4, 8, 16, 32, 64, 128, 256]
START_GRID = [60, 180, 300, 420, 540, 660, 780, 900]
N_GRID = [2, 3]
# every legal column a PATCH-wide support can occupy: the position AXIS the
# A2-RECT analytic expectation is enumerated over.
COL_GRID = list(range(0, FIELD_W - PATCH + 1))

FRAMES_NPZ = "results/gapseam_starts.npz"

# --- seeds: DIRECT elements of explicit ranges inside the declared block.
# NEVER `sd + K` -- an offset expression defeats the static ledger as
# completely as a CLI value does (the refusal-capacity rung's lesson).
SEED_A1 = list(range(109000, 109200))
SEED_SWAP = list(range(109200, 109400))
SEED_NOISE = list(range(109400, 109600))
SEED_RECT = list(range(109600, 109800))
SEED_RAGGED = list(range(109800, 110000))
# PILOT seeds -- ALREADY BURNED by the pixel-seam rung (104000-104199).
PILOT_SEEDS = list(range(104000, 104020))

PROBE_COLS = (0, 4, 8)
PROBE_VIOLATIONS: list[str] = []


# --------------------------------------------------------------------------- #
#  world: PIXELS -> cells.  Mechanical translation; no decision.
#  (quant / modal / c_all / c_thresh / c_mask / paste / render_dot are the
#   pixel-seam rung's, unchanged, so this rung's stimuli ARE its stimuli.)
# --------------------------------------------------------------------------- #
def quant(f, q):
    """Quantize luminance to `q` levels.  `q` is an AXIS."""
    return (np.asarray(f, dtype=np.float64).clip(0, 255).astype(np.int64) * q) // 256


def modal(fq):
    """The frame's OWN modal quantized luminance -- data-derived, no constant."""
    v, ct = np.unique(fq, return_counts=True)
    return int(v[int(np.argmax(ct))])


def c_all(fq):
    h, w = fq.shape
    return [["px", r, c, int(fq[r, c])] for r in range(h) for c in range(w)]


def c_thresh(fq):
    """FIGURE cells: luminance != the frame's own modal value.  SUPPLIED
    STRUCTURE, declared as such in the pre-registration."""
    m = modal(fq)
    rs, cs = np.nonzero(fq != m)
    return [["px", int(r), int(c), int(fq[r, c])] for r, c in zip(rs, cs)]


def c_mask(fq, mask):
    """GROUND-TRUTH support: exactly the cells of a known rectangle."""
    rs, cs = np.nonzero(mask)
    return [["px", int(r), int(c), int(fq[r, c])] for r, c in zip(rs, cs)]


def paste(patch, col):
    f = np.zeros((FIELD_H, FIELD_W), dtype=np.float64)
    ph, pw = patch.shape
    r0 = (FIELD_H - ph) // 2
    f[r0:r0 + ph, col:col + pw] = patch
    m = np.zeros((FIELD_H, FIELD_W), dtype=bool)
    m[r0:r0 + ph, col:col + pw] = True
    return f, m


def render_dot(col):
    f = np.full((FIELD_H, FIELD_W), BG, dtype=np.uint8)
    if col is not None:
        f[ROW:ROW + DOT, col:col + DOT] = FG
    return f


def strip(cells):
    """Remove the APPEARANCE slots, keeping predicate + coordinates.  With no
    non-coord slot beyond the predicate present, R6 is VACUOUS and BOTH of the
    engine's exactness checks (`infer_translate_offset` AND the `frames_equal`
    verification of every consecutive pair) reduce to predicate+coordinates.
    That is `P_tol` exactly -- registered as a CLAIM TO CHECK (`n_disagree`),
    never as an assumption."""
    keep = [PRED_IDX] + list(COORD_IDX)
    return [[cell[i] for i in keep] for cell in cells]


# --------------------------------------------------------------------------- #
#  `P_tol` -- THE APPEARANCE-TOLERANT PREDICATE, IMPLEMENTED HERE, reaching no
#  substrate and no Term.  Exact integer arithmetic throughout: there is no
#  tolerance in it and nowhere to put one.
# --------------------------------------------------------------------------- #
def sort_key(cell):
    """Sort by (predicate, coords) -- APPEARANCE EXCLUDED from the key, because
    an appearance change would otherwise scramble the pairing."""
    return tuple([cell[PRED_IDX]] + [cell[i] for i in COORD_IDX])


def p_tol(frames):
    """Return (accepted, offset, appearance_residual, reason).

    `appearance_residual` is COUNTED and REPORTED; it is never compared
    against anything and no branch reads it."""
    if len(frames) < 2:
        return False, None, 0, "R1"
    if any(len(f) == 0 for f in frames):
        return False, None, 0, "R3"
    if len(set(len(f) for f in frames)) != 1:
        return False, None, 0, "R4"
    a = sorted(frames[0], key=sort_key)
    b = sorted(frames[1], key=sort_key)
    off = tuple(b[0][i] - a[0][i] for i in COORD_IDX)
    resid = 0
    for t in range(len(frames) - 1):
        a = sorted(frames[t], key=sort_key)
        b = sorted(frames[t + 1], key=sort_key)
        for ra, rb in zip(a, b):
            if tuple(rb[i] - ra[i] for i in COORD_IDX) != off:
                return False, None, 0, "OFFSET"
            if ra[PRED_IDX] != rb[PRED_IDX]:
                return False, None, 0, "PRED"
            if len(ra) != len(rb):
                return False, None, 0, "ARITY"
            for k in range(len(ra)):
                if k in COORD_IDX or k == PRED_IDX:
                    continue
                if ra[k] != rb[k]:
                    resid += 1
                    break
    if all(o == 0 for o in off):
        return False, None, resid, "IDENTITY"
    return True, off, resid, "ok"


def p_strict(frames):
    """The INCUMBENT predicate (R1..R7), for the C1/C4 contrast.  Identical to
    `p_tol` except that EVERY non-coord slot must be byte-identical."""
    ok, off, resid, reason = p_tol(frames)
    if not ok:
        return False, None, reason
    if resid != 0:
        return False, None, "R6"
    return True, off, "ok"


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
    made 167 false accusations for the timephi rung, so it is never read here."""
    probe = [strip(c_thresh(quant(render_dot(c), 256))) for c in PROBE_COLS]
    t = srs.Term("TimeInfer", sequence=srs.Lit(probe),
                 codebook_type="ShapeSignature", max_b=MAX_B, field="coord_dims")
    cd = tuple(s.evaluate(t, {}) or ())
    if len(cd) == 0:
        PROBE_VIOLATIONS.append(tag)
    return cd


def present(frames, dt, tag, *, want_checked=True, probe=False, support=False):
    s, ag, native = _boot()
    s.add_node("ShapeSignature",
               {"name": "px_base", "signature": json.dumps(frames[0]),
                "kind": "faculty", "faculty": "px_base", "dim_types": dt})
    o = s.add_node("Observation", {"frames": frames, "dim_types": dt,
                                   "status": "motion_seq", "key": ["appearance"]})
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
           "n_cells": [len(f) for f in frames]}
    rec["offset"] = tuple(term("offset") or ()) if explained else None
    # `checked` is the INCUMBENT's search counter, and reading it off a REFUSAL
    # costs the full 2x2 linear enumeration (the pixel-seam rung measured
    # 83 520 steps).  It is DIAGNOSTIC ONLY -- no verdict function reads it --
    # and the guard-vs-full-search distinction this rung actually needs is
    # discharged by `SupportInfer`'s own `compared`, which is counted on EVERY
    # condition at no cost.  So it is read only where it is cheap (an EXPLAINED
    # condition, where it is 0 by construction) and the refusal-side value is
    # INHERITED FROM THE PREDECESSOR rather than re-measured here.
    rec["checked"] = 0 if explained else None
    if support:
        # THE SHIPPED TERM ITSELF, evaluated on the FULL (un-stripped) stimulus
        # in the SAME booted substrate.  ONE EVALUATION PER FIELD -- the shape
        # in which `GapAbduce`'s `finish()`-selection bug surfaces (a patch that
        # restored a measurement on a refusal SILENTLY DID NOTHING).
        def sup(field):
            return s.evaluate(srs.Term("SupportInfer", sequence=srs.Lit(frames),
                                       codebook_type="ShapeSignature",
                                       field=field), {})
        rec["term_explained"] = sup("explained")
        rec["term_residual"] = sup("appearance_residual")
        rec["term_compared"] = sup("compared")
        rec["term_reason"] = sup("reason")
        rec["term_offset"] = tuple(sup("offset") or ())
    if probe:
        rec["probe_coord_dims"] = _codebook_live(s, tag)
    return rec


def measure(frames, tag, *, want_checked=True, probe=False):
    """ONE condition, BOTH operators.  `tol` is the engine on the SLOT-STRIPPED
    stimulus; `strict` is the engine on the full stimulus.  `P_tol` / `p_strict`
    are computed here INDEPENDENTLY and compared."""
    tol = present([strip(f) for f in frames], DT_S, tag + ":tol",
                  want_checked=want_checked, probe=probe)
    strict = present(frames, DT_V, tag + ":strict", want_checked=want_checked,
                     support=True)
    ok_t, off_t, resid, reason = p_tol(frames)
    ok_s, off_s, reason_s = p_strict(frames)
    return {
        "tag": tag,
        "tol_explained": tol["explained"], "tol_offset": tol["offset"],
        "tol_checked": tol["checked"],
        "strict_explained": strict["explained"], "strict_offset": strict["offset"],
        "strict_checked": strict["checked"],
        "ind_tol": ok_t, "ind_strict": ok_s,
        "ind_offset": list(off_t) if off_t else None,
        "appearance_residual": resid,
        "reason": reason, "reason_strict": reason_s,
        "n_cells": tol["n_cells"],
        "probe_coord_dims": tol.get("probe_coord_dims"),
        "term_explained": strict.get("term_explained"),
        "term_residual": strict.get("term_residual"),
        "term_compared": strict.get("term_compared"),
        "term_reason": strict.get("term_reason"),
        "term_offset": strict.get("term_offset"),
        # AGREEMENT between my source reading and the engine, per condition.
        "agree_tol": bool(ok_t) == bool(tol["explained"]),
        "agree_strict": bool(ok_s) == bool(strict["explained"]),
        # THREE-WAY: the runner's predicate, the slot-stripped incumbent, and
        # the SHIPPED TERM must all say the same thing on every condition.
        "agree_term": bool(ok_t) == bool(strict.get("term_explained")),
    }


# --------------------------------------------------------------------------- #
#  ANALYTIC EXPECTATIONS -- enumerated EXHAUSTIVELY, in this file, BEFORE the
#  arms are read (the GapAbduce template, applied prospectively).
# --------------------------------------------------------------------------- #
def analytic_rect(n):
    """P(`P_tol` accepts a CONGRUENT support at `n` INDEPENDENTLY drawn column
    positions).  Congruent supports are translates of one another, so the
    predicate reduces to: the positions are equally spaced with a NON-ZERO
    step.  Enumerated EXACTLY over `COL_GRID`."""
    g = COL_GRID
    tot = len(g) ** n
    hit = 0
    if n == 2:
        for p0 in g:
            for p1 in g:
                if p1 - p0 != 0:
                    hit += 1
    elif n == 3:
        for p0 in g:
            for p1 in g:
                for p2 in g:
                    if p1 - p0 == p2 - p1 != 0:
                        hit += 1
    else:
        raise ValueError("enumerated for n in (2, 3) only")
    return hit / tot


def wilson(k, n):
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def ci_below(k1, n1, k2, n2):
    """Is arm 1's rate CI-separated STRICTLY BELOW arm 2's?  A comparison
    between two MEASURED quantities -- never against a literal."""
    return wilson(k1, n1)[1] < wilson(k2, n2)[0]


# --------------------------------------------------------------------------- #
#  arms
# --------------------------------------------------------------------------- #
def a0_controls():
    """WIRING CONTROLS, RUN FIRST.  The run ABORTS on either."""
    pos = present([strip(c_thresh(quant(render_dot(c), 256))) for c in (0, 4, 8)],
                  DT_S, "A0-POS", probe=True)
    neg = present([strip(c_thresh(quant(render_dot(0), 256))) for _ in range(3)],
                  DT_S, "A0-NEG")
    return {"pos": pos, "neg": neg}


def a1_conditions(Z, seeds):
    """THE CAPABILITY.  Pixel-seam E4t / E4g stimuli, N=3, real photometry,
    stratified by LIVENESS (exact array inequality; no tolerance)."""
    out = []
    for sd in seeds:
        r = np.random.default_rng(sd)
        start = START_GRID[int(r.integers(0, len(START_GRID)))]
        t0 = int(r.integers(0, 24 - 3))
        r0 = int(r.integers(0, 48 - PATCH))
        c0 = int(r.integers(0, 48 - PATCH))
        F = Z[str(start)]
        for q in Q_GRID:
            pats = [F[t0 + k][r0:r0 + PATCH, c0:c0 + PATCH] for k in range(3)]
            qp = [quant(p, q) for p in pats]
            live = not (np.array_equal(qp[0], qp[1]) and np.array_equal(qp[1], qp[2]))
            for arm in ("E4t", "E4g"):
                frames = []
                for k, p in enumerate(pats):
                    f, m = paste(p, 4 + k * S)
                    fq = quant(f, q)
                    frames.append(c_thresh(fq) if arm == "E4t" else c_mask(fq, m))
                out.append(("A1", arm, sd, q, live, frames))
    return out


def a2_swap(Z, seeds, n):
    """GT rectangular support translating rigidly by S; the CONTENT drawn from
    INDEPENDENT video times per frame.  The strict operator refuses; `P_tol`
    accepts.  THIS IS EXACTLY THE DISCRIMINATION THE TOLERANCE GIVES UP."""
    out = []
    for sd in seeds:
        r = np.random.default_rng(sd)
        start = START_GRID[int(r.integers(0, len(START_GRID)))]
        F = Z[str(start)]
        r0 = int(r.integers(0, 48 - PATCH))
        c0 = int(r.integers(0, 48 - PATCH))
        ts = [int(r.integers(0, 24)) for _ in range(n)]
        q = Q_GRID[int(r.integers(0, len(Q_GRID)))]
        frames = []
        for k in range(n):
            p = F[ts[k]][r0:r0 + PATCH, c0:c0 + PATCH]
            f, m = paste(p, 4 + k * S)
            frames.append(c_mask(quant(f, q), m))
        out.append(("A2-SWAP", f"n{n}", sd, q, None, frames))
    return out


def a2_noise(seeds, n):
    """Supports drawn INDEPENDENTLY per frame (equal cardinality, random
    cells).  NO rigid relation exists."""
    out = []
    m = PATCH * PATCH
    for sd in seeds:
        r = np.random.default_rng(sd)
        q = Q_GRID[int(r.integers(0, len(Q_GRID)))]
        frames = []
        for _ in range(n):
            idx = r.choice(FIELD_H * FIELD_W, size=m, replace=False)
            vals = r.integers(0, max(q, 1), size=m)
            frames.append([["px", int(i) // FIELD_W, int(i) % FIELD_W, int(v)]
                           for i, v in zip(idx, vals)])
        out.append(("A2-NOISE", f"n{n}", sd, q, None, frames))
    return out


def a2_rect(Z, seeds, n):
    """A CONGRUENT solid PATCH x PATCH support at `n` INDEPENDENTLY drawn
    positions, content independent.  NO OBJECT MOVES."""
    out = []
    for sd in seeds:
        r = np.random.default_rng(sd)
        start = START_GRID[int(r.integers(0, len(START_GRID)))]
        F = Z[str(start)]
        r0 = int(r.integers(0, 48 - PATCH))
        c0 = int(r.integers(0, 48 - PATCH))
        cols = [COL_GRID[int(r.integers(0, len(COL_GRID)))] for _ in range(n)]
        ts = [int(r.integers(0, 24)) for _ in range(n)]
        q = Q_GRID[int(r.integers(0, len(Q_GRID)))]
        frames = []
        for k in range(n):
            p = F[ts[k]][r0:r0 + PATCH, c0:c0 + PATCH]
            f, m = paste(p, cols[k])
            frames.append(c_mask(quant(f, q), m))
        out.append(("A2-RECT", f"n{n}", sd, q, None, frames))
    return out


def a2_ragged(Z, seeds, n):
    """Identical protocol to A2-RECT, but the support is the THRESHOLD
    SILHOUETTE of the real patch -- NOT congruent in general."""
    out = []
    for sd in seeds:
        r = np.random.default_rng(sd)
        start = START_GRID[int(r.integers(0, len(START_GRID)))]
        F = Z[str(start)]
        r0 = int(r.integers(0, 48 - PATCH))
        c0 = int(r.integers(0, 48 - PATCH))
        cols = [COL_GRID[int(r.integers(0, len(COL_GRID)))] for _ in range(n)]
        ts = [int(r.integers(0, 24)) for _ in range(n)]
        q = Q_GRID[int(r.integers(0, len(Q_GRID)))]
        frames = []
        for k in range(n):
            p = F[ts[k]][r0:r0 + PATCH, c0:c0 + PATCH]
            f, _ = paste(p, cols[k])
            frames.append(c_thresh(quant(f, q)))
        out.append(("A2-RAGGED", f"n{n}", sd, q, None, frames))
    return out


def a3_raster(Z):
    """THE PRIOR QUESTION, TESTED.  E0 (real video, every cell) and E2 (EXACT
    toroidal roll), under `P_tol`."""
    out = []
    for start in START_GRID:
        F = Z[str(start)]
        for q in Q_GRID:
            for arm in ("E0", "E2"):
                if arm == "E2":
                    base = F[0][:CROP, :CROP]
                    fq = [quant(np.roll(base, k * S, axis=1), q) for k in range(3)]
                else:
                    fq = [quant(F[i][:CROP, :CROP], q) for i in range(3)]
                out.append(("A3", arm, start, q, None, [c_all(f) for f in fq]))
    return out


def a4_retained():
    """THE RETAINED REFUSAL.  Each breaks a clause `P_tol` KEEPS.  FORCED --
    declared in advance, run only to confirm the source reading against the
    real engine."""
    q = 256
    card = [c_thresh(quant(render_dot(0), q)),
            c_thresh(quant(render_dot(4), q))[:-1]]
    accel = [c_thresh(quant(render_dot(c), q)) for c in (0, 4, 12)]
    shuf = [c_thresh(quant(render_dot(c), q)) for c in (0, 8, 4)]
    return [("A4", "CARDINALITY", 0, q, None, card),
            ("A4", "ACCEL", 0, q, None, accel),
            ("A4", "SHUFFLE", 0, q, None, shuf)]


# ======================= THE VERDICTS (PROTOCOL 13) ======================== #
#  Every verdict decides by EXACT EQUALITY on a logical or integer quantity,
#  a count `== 0`, or a CI comparison between two MEASURED quantities.
#  No ordering comparison against a non-zero constant decides anything.
#  `tests/test_appearance_ast_migrated.py` binds these BY NAME as AST
#  FunctionDef nodes, read from this tuple.
# ========================================================================== #
def v_c1_partition(R):
    """C1: the partition does not leak.  `fa_silent` must be EXACTLY 0."""
    return _fa_silent(R) == 0


def v_c2_rect_analytic(R):
    """C2: A2-RECT's accept rate lies WITHIN the Wilson CI of the EXACTLY
    ENUMERATED expectation, at every n."""
    for n in N_GRID:
        rows = [r for r in R if r["arm"] == "A2-RECT" and r["n"] == n]
        k = sum(1 for r in rows if r["tol_explained"])
        lo, hi = wilson(k, len(rows))
        e = analytic_rect(n)
        if not (lo <= e <= hi):
            return False
    return True


def v_c2_noise(R):
    """C2: A2-NOISE accepts nothing -- an exact count."""
    return sum(1 for r in R
               if r["arm"] == "A2-NOISE" and r["tol_explained"]) == 0


def v_c3_discriminates(R):
    """C3: every no-rigid-motion arm is CI-separated STRICTLY BELOW the
    rigid-motion arm.  A comparison between two MEASURED quantities."""
    live = [r for r in R if r["arm"] == "A1" and r["live"]]
    kl, nl = sum(1 for r in live if r["tol_explained"]), len(live)
    for arm in ("A2-NOISE", "A2-RECT", "A2-RAGGED"):
        rows = [r for r in R if r["arm"] == arm and r["n"] == 3]
        k = sum(1 for r in rows if r["tol_explained"])
        if not ci_below(k, len(rows), kl, nl):
            return False
    return True


def v_c4_no_regression(R):
    """C4: nothing the strict operator explained is lost."""
    return sum(1 for r in R
               if r["strict_explained"] and not r["tol_explained"]) == 0


def v_p0_raster(R):
    """P0: `P_tol` refuses the raster on BOTH E0 and E2 -- an exact count."""
    return sum(1 for r in R if r["arm"] == "A3" and r["tol_explained"]) == 0


def v_p0_identity(R):
    """P0's proviso: the raster refusals are diagnosed IDENTITY, not
    appearance.  An exact count of the rows that are NOT."""
    return sum(1 for r in R
               if r["arm"] == "A3" and r["reason"] != "IDENTITY") == 0


def v_p1_capability(R):
    """P1: at q >= 4, every LIVE A1 condition is explained by `P_tol` and
    none by the strict operator."""
    rows = [r for r in R if r["arm"] == "A1" and r["live"] and r["q"] != 2]
    return (sum(1 for r in rows if not r["tol_explained"]) == 0
            and sum(1 for r in rows if r["strict_explained"]) == 0)


def v_p5_third_frame(R):
    """P5: A2-RECT at n=3 is CI-separated BELOW n=2.  THE THIRD FRAME
    CONSTRAINS."""
    a = [r for r in R if r["arm"] == "A2-RECT" and r["n"] == 3]
    b = [r for r in R if r["arm"] == "A2-RECT" and r["n"] == 2]
    return ci_below(sum(1 for r in a if r["tol_explained"]), len(a),
                    sum(1 for r in b if r["tol_explained"]), len(b))


def v_p6_support_entropy(R):
    """P6: A2-RAGGED CI-separated BELOW A2-RECT at n=3.  THE MOST OPEN ARM."""
    a = [r for r in R if r["arm"] == "A2-RAGGED" and r["n"] == 3]
    b = [r for r in R if r["arm"] == "A2-RECT" and r["n"] == 3]
    return ci_below(sum(1 for r in a if r["tol_explained"]), len(a),
                    sum(1 for r in b if r["tol_explained"]), len(b))


def v_p8_retained(R):
    """P8: A4 refuses all three -- an exact count."""
    return sum(1 for r in R if r["arm"] == "A4" and r["tol_explained"]) == 0


def v_p9_agrees(R):
    """P9: my INDEPENDENT reading agrees with the engine on EVERY condition,
    for BOTH operators.  An exact count of disagreements."""
    return _n_disagree(R) == 0


def v_e_term_agrees(R):
    """THE SHIPPED TERM agrees with the slot-stripped incumbent AND with my
    independent reading, on EVERY condition.  A disagreement means the Rust
    does not implement the predicate this rung measured."""
    return sum(1 for r in R if not r["agree_term"]) == 0


def v_term_residual_is_MEASURED(R):
    """`appearance_residual` must take MORE THAN ONE value across the run.  A
    field that reads the same on every call cannot distinguish a measurement
    from a constructor default -- the bug that made a predecessor's restored
    `total` silently do nothing."""
    return len({r["term_residual"] for r in R if r["term_residual"] is not None}) != 1


VERDICTS = (v_e_term_agrees, v_term_residual_is_MEASURED, v_c1_partition, v_c2_rect_analytic, v_c2_noise, v_c3_discriminates,
            v_c4_no_regression, v_p0_raster, v_p0_identity, v_p1_capability,
            v_p5_third_frame, v_p6_support_entropy, v_p8_retained, v_p9_agrees)


def _fa_silent(R):
    """Accepted by `P_tol`, REFUSED by strict, and appearance_residual == 0."""
    return sum(1 for r in R
               if r["term_explained"] and not r["strict_explained"]
               and r["term_residual"] == 0)


def _n_disagree(R):
    return sum(1 for r in R if not (r["agree_tol"] and r["agree_strict"]
                                    and r["agree_term"]))


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("pilot", "confirm"), default="pilot")
    args = ap.parse_args()

    print(provenance_line())
    stamp = provenance_stamp()
    if EXPECT_ENGINE not in json.dumps(stamp) + provenance_line():
        print(f"ABORT: engine divergence -- expected {EXPECT_ENGINE}")
        return 2

    Z = np.load(FRAMES_NPZ)
    ctrl = a0_controls()
    if not (ctrl["pos"]["explained"] and tuple(ctrl["pos"]["offset"] or ()) == (0, 4)):
        print("ABORT: wiring control failed -- A0-POS DEAD", ctrl["pos"])
        return 3
    if ctrl["neg"]["explained"]:
        print("ABORT: wiring control failed -- A0-NEG DEAD", ctrl["neg"])
        return 3
    if PROBE_VIOLATIONS:
        print("ABORT: wiring control failed -- CODEBOOK PROBE", PROBE_VIOLATIONS)
        return 3
    print("A0 controls LIVE:", ctrl["pos"]["offset"], ctrl["pos"]["probe_coord_dims"])

    pilot = args.mode == "pilot"
    if pilot:
        sa1 = sswap = snoise = srect = sragged = PILOT_SEEDS
    else:
        sa1, sswap = SEED_A1, SEED_SWAP
        snoise, srect, sragged = SEED_NOISE, SEED_RECT, SEED_RAGGED

    conds = []
    conds += a1_conditions(Z, sa1)
    for n in N_GRID:
        conds += a2_swap(Z, sswap, n)
        conds += a2_noise(snoise, n)
        conds += a2_rect(Z, srect, n)
        conds += a2_ragged(Z, sragged, n)
    conds += a3_raster(Z)
    conds += a4_retained()

    print(f"conditions: {len(conds)}  mode={args.mode}  load={os.getloadavg()}")
    R = []
    t0 = time.time()
    for i, (arm, sub, sd, q, live, frames) in enumerate(conds):
        n = len(frames)
        rec = measure(frames, f"{arm}:{sub}:{sd}:{q}",
                      want_checked=(arm != "A3"))
        rec.update({"arm": arm, "sub": sub, "seed": sd, "q": q,
                    "live": live, "n": n})
        R.append(rec)
        if i % 200 == 0:
            print(f"  {i}/{len(conds)}  {time.time() - t0:.0f}s  "
                  f"load={os.getloadavg()}", flush=True)

    verdicts = {f.__name__: bool(f(R)) for f in VERDICTS}
    rates = {}
    for arm in ("A1", "A2-SWAP", "A2-NOISE", "A2-RECT", "A2-RAGGED", "A3", "A4"):
        for n in N_GRID + [None]:
            rows = [r for r in R if r["arm"] == arm and (n is None or r["n"] == n)]
            if not rows:
                continue
            k = sum(1 for r in rows if r["tol_explained"])
            ks = sum(1 for r in rows if r["strict_explained"])
            rates[f"{arm}|n={n}"] = {
                "n_cond": len(rows), "tol_accept": k, "tol_rate": k / len(rows),
                "tol_ci": wilson(k, len(rows)),
                "strict_accept": ks, "strict_rate": ks / len(rows),
            }
    live_rows = [r for r in R if r["arm"] == "A1" and r["live"]]
    out = {
        "mode": args.mode,
        "engine_provenance": stamp,
        "engine": EXPECT_ENGINE,
        "loadavg_end": os.getloadavg(),
        "wall_s": time.time() - t0,
        "n_conditions": len(R),
        "verdicts": verdicts,
        "fa_silent": _fa_silent(R),
        "n_disagree": _n_disagree(R),
        "analytic_rect": {str(n): analytic_rect(n) for n in N_GRID},
        "rates": rates,
        "a1_live": len(live_rows),
        "a1_live_tol": sum(1 for r in live_rows if r["tol_explained"]),
        "a1_live_strict": sum(1 for r in live_rows if r["strict_explained"]),
        "a0": ctrl,
        "rows": R,
    }
    path = ("results/appearance_pilot.json" if pilot else "results/appearance.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                     indent=1, default=str)[:4000])
    print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
