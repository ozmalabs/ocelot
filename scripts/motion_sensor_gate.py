"""motion_sensor_gate — THE ACCURACY GATE FOR THE MOTION SENSOR.

A RUNNABLE GATE, NOT A ONE-OFF MEASUREMENT. Every motion number in this arc
rests on `domains.motion_group_world.vector_field`, and until now nothing
checked it. Two rungs measured it wrong and both had to caveat their headline:

  * 84000-84999 measured ~11% WRONG PER BLOCK on a pan whose answer is KNOWN
    and UNIFORM, and recorded that it "BOUNDS EVERY COUNT in the rung";
  * 86000-86999 predicted `(0,0)` for S>4, measured `(0,4)` at S=5-7, and
    called it "a sensor defect worth its own gate".

The standing rule this rung is built on: ABOVE-THE-NULL IS NOT GATE-GRADE -- a
hard gate is priced by the feature's ERROR RATE, not its effect size. The
motion signal IS used as a hard grouping criterion. This prices it.

USAGE
-----
    python3 scripts/motion_sensor_gate.py --mode pilot        # burned seeds
    python3 scripts/motion_sensor_gate.py --mode confirm      # 94000-block
    python3 scripts/motion_sensor_gate.py --mode confirm --write-baseline
    python3 scripts/motion_sensor_gate.py --degrade tiebreak_corner   # control

A future rung checks the sensor before trusting it by running the default
invocation and reading the exit code.

WHAT THE GATE ASSERTS, AND WHY NONE OF IT IS A CHOSEN NUMBER
------------------------------------------------------------
TWO EXACT STRUCTURAL INVARIANTS -- no tolerance, no constant, the strongest
§13 outcome (not a number that falls out, but NO NUMBER):

  I1 ZERO IDENTITY. On `b is a` (bit-identical frames) EVERY block must report
     EXACTLY (0,0). The stimulus deliberately contains a FLAT region, because
     on flat content every offset ties at SAD 0 and only the Occam tie-break
     ("keep the smallest displacement") gives (0,0). A raw row-major scan --
     the footgun `vector_field`'s own docstring says it avoids -- returns
     (-r,-r) there. I1 is the gate that would have caught that.

  I2 UNIQUE-MINIMUM FIDELITY. Where the TRUE offset is the UNIQUE SAD
     minimiser inside the search window, the sensor MUST return it. This is a
     statement about the sensor's ARITHMETIC and it admits no tolerance: given
     the objective, the answer is forced.

Neither invariant can be satisfied by a dead instrument, and neither can be
tuned. Everything BEYOND them is a REGRESSION comparison against this tree's
own committed baseline -- the comparison point falls OUT of a prior
measurement rather than being chosen (§13: a number fixed by the system's own
measured statistics, not by the answer I wanted).

THE REFERENCE IMPLEMENTATION IS PROVEN BIT-IDENTICAL TO THE REAL SENSOR
----------------------------------------------------------------------
The degradation arms need a sensor with ONE thing changed. Re-implementing it
would let the "undegraded" arm silently drift away from the instrument under
test -- so `_sensor(..., degrade="none")` is asserted BIT-IDENTICAL to
`mgw.vector_field` on a battery of inputs EVERY TIME THE GATE RUNS
(`assert_reference_is_the_real_sensor`). A degradation is then the same code
path with one line different, and the control means what it says.

GROUND TRUTH IS BY CONSTRUCTION, NEVER SENSED
---------------------------------------------
See `scripts/motion_sensor_lib.py`. Textures are synthesised in the Fourier
domain and are therefore PERIODIC, so an integer `np.roll` is an EXACT rigid
translation with no border fabrication and the true vector is defined at EVERY
block. The recorded rule -- a diagnostic must not be computed by the component
it checks -- is honoured: `t` is an INPUT to the construction.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

from domains import motion_group_world as mgw           # noqa: E402
from scripts import motion_sensor_lib as L              # noqa: E402

SEED_BLOCK = 94000
PILOT_SEEDS = tuple(range(0, 14))        # ALREADY BURNED -- §3 permits a power
                                         # pilot only on burned seeds.

GRID = L.GRID
BLOCK = L.BLOCK

# The stimulus axes. These are the PARAMETERS THE ERROR IS A FUNCTION OF, and
# they are the question, not a tuning surface: displacement magnitude against
# block size, texture/contrast, and number of true bodies.
MAGNITUDES = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12)
N_DIRECTIONS = 12                        # 30 degrees apart: axis-aligned,
                                         # diagonal AND off-lattice directions,
                                         # so the profile is not read off the
                                         # four directions a lattice flatters.
BLOCKS = (2, 4, 8)
CONTRASTS = (2.0, 4.0, 8.0, 16.0, 32.0, 64.0)
BETAS = (0.0, 1.0, 2.0)
BODY_COUNTS = (1, 2, 3, 4)
ROTATIONS = (1.0, 2.0, 5.0, 10.0, 90.0)
NOISE_SDS = (0.0, 1.0, 2.0, 4.0)

# THE ONE COMPARISON CONSTANT IN THIS RUNG, AND WHAT IT FALLS OUT OF (§13).
# The sensor reports on the INTEGER lattice. A within-block deformation smaller
# than half a step CANNOT change any integer vector it could emit -- it rounds
# away. So "is one vector per block a complete description of this block?" is
# answered by the sensor's OWN output quantisation, not by a number I picked:
# half of the smallest step it can represent. (The in-frame-is-INTEGER
# invariant, used as a resolution limit rather than as a tuning knob.)
INTEGER_STEP = 1.0
SUBPIXEL_INVISIBLE = INTEGER_STEP / 2.0


# --- the reference sensor, and its equality proof ---------------------------

def _sensor(a, b, block: int, radius: int | None = None, degrade: str = "none"):
    """`vector_field` re-expressed with ONE degradation switch.

    `degrade="none"` is asserted bit-identical to `mgw.vector_field`. The
    degradations are REAL bugs, not caricatures:

      tiebreak_corner -- visit offsets in raw row-major order. This is exactly
                         the bug the real docstring claims to have avoided
                         ("a raw row-major scan would silently bias every tie
                         to the corner offset (-r,-r)"), so the control tests
                         whether the gate would have caught the sensor's own
                         named footgun.
      radius_half     -- shrink the search window to block//2. A plausible
                         "speed it up" edit; it cannot be seen in any output
                         except accuracy.
      sad_coarse      -- score SAD on every other pixel of the block. The
                         classic subsampling speedup; it changes the objective
                         while leaving the interface identical.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    r = block if radius is None else int(radius)
    if degrade == "radius_half":
        r = max(1, block // 2)
    H, W = a.shape
    nh, nw = H // block, W // block

    def blocks(x):
        return (x[:nh * block, :nw * block]
                .reshape(nh, block, nw, block).transpose(0, 2, 1, 3))

    A = blocks(a)
    bp = np.pad(b, r, mode="edge")
    best = np.full((nh, nw), np.inf)
    vy = np.zeros((nh, nw))
    vx = np.zeros((nh, nw))

    offsets = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)]
    if degrade != "tiebreak_corner":
        offsets.sort(key=lambda o: (o[0] * o[0] + o[1] * o[1], o[0], o[1]))

    for dy, dx in offsets:
        sh = bp[r + dy:r + dy + H, r + dx:r + dx + W]
        d = np.abs(A - blocks(sh))
        if degrade == "sad_coarse":
            d = d[:, :, ::2, ::2]
        sad = d.sum(axis=(2, 3))
        upd = sad < best
        best = np.where(upd, sad, best)
        vy = np.where(upd, float(dy), vy)
        vx = np.where(upd, float(dx), vx)

    return np.stack([vy, vx], axis=-1)


def assert_reference_is_the_real_sensor():
    """RUN EVERY TIME. The whole positive control rests on this equality, so
    it is checked rather than asserted in a comment."""
    rng = np.random.default_rng(0)
    checks = 0
    for block in BLOCKS:
        for beta in (0.0, 1.0, 2.0):
            for contrast in (2.0, 32.0):
                a = L.texture(rng, GRID, beta=beta, contrast=contrast)
                for dy, dx in ((0, 0), (1, 0), (0, 3), (-2, 5), (4, 4), (-7, 2)):
                    b = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
                    got = _sensor(a, b, block)
                    want = mgw.vector_field(a, b, block)
                    if not np.array_equal(got, want):
                        raise SystemExit(
                            "REFERENCE DIVERGES FROM THE REAL SENSOR at "
                            f"block={block} beta={beta} contrast={contrast} "
                            f"D=({dy},{dx}). THE GATE IS VOID.")
                    checks += 1
    return checks


# --- the structural invariants ----------------------------------------------

def invariant_zero_identity(seeds, degrade="none"):
    """I1. `b` bit-identical to `a` => EVERY block exactly (0,0).

    The stimulus is a texture with a FLAT REGION pasted into it. On flat
    content every offset ties at SAD 0, so only the Occam tie-break yields
    (0,0); this is the clause that bites a row-major scan.
    """
    bad = []
    for s in seeds:
        rng = np.random.default_rng(s)
        a = L.texture(rng, GRID, beta=1.0, contrast=32.0)
        a[24:48, 24:48] = 128.0                     # a genuinely flat region
        a = L.quantise(a)
        for block in BLOCKS:
            v = _sensor(a, a.copy(), block, degrade=degrade)
            n_wrong = int((np.abs(v) > 0).any(axis=-1).sum())
            if n_wrong:
                bad.append({"seed": int(s), "block": block,
                            "blocks_reporting_motion_on_identical_frames": n_wrong,
                            "n_blocks": int(v.shape[0] * v.shape[1])})
    return {"name": "I1_zero_identity", "passed": not bad, "violations": bad}


def invariant_unique_minimum(seeds, degrade="none"):
    """I2. Where the TRUE offset is the UNIQUE SAD minimiser in the window, the
    sensor MUST return it. No tolerance: the objective forces the answer."""
    bad = []
    n_checked = 0
    for s in seeds:
        rng = np.random.default_rng(s)
        a = L.texture(rng, GRID, beta=1.0, contrast=32.0)
        for dy, dx in ((0, 1), (2, 0), (-1, 3), (3, 3), (-2, -4), (4, 0)):
            b = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
            t = L.true_uniform(a.shape, BLOCK, dy, dx)
            uniq = L.true_offset_is_unique_minimum(a, b, BLOCK, BLOCK, t)
            v = _sensor(a, b, BLOCK, degrade=degrade)
            n_checked += int(uniq.sum())
            miss = uniq & ((np.abs(v - t) > 0).any(axis=-1))
            if miss.any():
                bad.append({"seed": int(s), "D": [dy, dx],
                            "resolvable_blocks_missed": int(miss.sum()),
                            "resolvable_blocks": int(uniq.sum())})
    return {"name": "I2_unique_minimum_fidelity", "passed": not bad,
            "resolvable_blocks_checked": n_checked, "violations": bad}


# --- the profile ------------------------------------------------------------

def _directions(n):
    return [(float(np.sin(2 * np.pi * i / n)), float(np.cos(2 * np.pi * i / n)))
            for i in range(n)]


def _rates(cls, mask=None):
    """The THREE rates, over the population each is defined on."""
    mv = cls["moving"] if mask is None else (cls["moving"] & mask)
    st = cls["static"] if mask is None else (cls["static"] & mask)
    nm, ns = int(mv.sum()), int(st.sum())
    out = {"n_moving_blocks": nm, "n_static_blocks": ns}
    for k in ("silent_miss", "confidently_wrong", "correct"):
        sel = cls[k] & mv
        out[k] = (float(sel.sum()) / nm) if nm else None
        out[k + "_n"] = int(sel.sum())
    sel = cls["false_motion"] & st
    out["false_motion"] = (float(sel.sum()) / ns) if ns else None
    out["false_motion_n"] = int(sel.sum())
    sel = cls["silent_miss_within_tol"] & mv
    out["silent_miss_that_would_pass_tolerance_n"] = int(sel.sum())
    return out


def collect_errors(seeds, degrade="none"):
    """PASS 1 -- collect the observed error magnitudes so the tolerance can be
    DERIVED from them (§13). No rate is computed here; the tolerance must not
    be chosen with the rates in view."""
    errs = []
    for s in seeds:
        rng = np.random.default_rng(s)
        a = L.texture(rng, GRID, beta=1.0, contrast=32.0)
        for m in MAGNITUDES:
            for uy, ux in _directions(N_DIRECTIONS):
                dy, dx = int(round(m * uy)), int(round(m * ux))
                b = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
                t = L.true_uniform(a.shape, BLOCK, dy, dx)
                v = _sensor(a, b, BLOCK, degrade=degrade)
                errs.append(np.linalg.norm(v - t, axis=-1).ravel())
    return np.concatenate(errs) if errs else np.zeros(0)


def collect_errors_within_aperture(seeds, degrade="none"):
    """PASS 1b -- the SAME collection restricted to displacements the sensor
    COULD have got right (|D| <= radius).

    WHY TWO POOLS, FIXED IN THE PILOT AND BEFORE ANY CONFIRMATORY NUMBER. Otsu
    splits whatever it is given, so WHAT IT IS GIVEN is the whole decision. The
    full pool is dominated by the beyond-aperture regime, where the true answer
    is not reachable at all; the split it returns there is a statement about
    THE APERTURE, not about accuracy. Restricting to |D| <= radius asks the
    question the tolerance is for: among answers the sensor could have got
    right, where does correct end and wrong begin? BOTH are reported, and so is
    the exact (zero-tolerance) reading, so no rate here is conditional on one
    pooling choice.
    """
    errs = []
    for s in seeds:
        rng = np.random.default_rng(s)
        a = L.texture(rng, GRID, beta=1.0, contrast=32.0)
        for m in MAGNITUDES:
            for uy, ux in _directions(N_DIRECTIONS):
                dy, dx = int(round(m * uy)), int(round(m * ux))
                if np.hypot(dy, dx) > BLOCK:
                    continue
                b = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
                t = L.true_uniform(a.shape, BLOCK, dy, dx)
                v = _sensor(a, b, BLOCK, degrade=degrade)
                errs.append(np.linalg.norm(v - t, axis=-1).ravel())
    return np.concatenate(errs) if errs else np.zeros(0)


def arm_figure_on_uniform(seeds, tol, degrade="none"):
    """A8 -- A FIGURE ON A UNIFORM FIELD. The phi rung's exact stimulus class,
    now with ground truth by construction.

    This is where SILENT MISS actually lives. On a textured field every block
    has evidence and the sensor essentially never abstains; on a UNIFORM field
    every offset ties and only the Occam tie-break speaks, so a figure that has
    moved beyond its own extent produces (0,0) -- "one vanished, another
    appeared". The phi rung read exactly this and could not separate it from a
    true zero.

    Figure blocks (fully inside the figure in frame `a`) have an unambiguous
    true vector; background blocks are truly static and are reported
    separately as invented motion.
    """
    rows = []
    for fsize in (4, 8, 16):
        for m in (1, 2, 4, 6, 8, 12):
            fig = {"silent_miss": [], "confidently_wrong": [], "correct": []}
            bg_false = []
            for s in seeds:
                rng = np.random.default_rng(s)
                acc = {k: [0, 0] for k in fig}
                bacc = [0, 0]
                for uy, ux in _directions(4):
                    dy, dx = int(round(m * uy)), int(round(m * ux))
                    if dy == 0 and dx == 0:
                        continue
                    a = np.full((GRID, GRID), 32.0)
                    y0 = x0 = GRID // 2 - fsize // 2
                    a[y0:y0 + fsize, x0:x0 + fsize] = 224.0
                    b = np.full((GRID, GRID), 32.0)
                    b[y0 + dy:y0 + dy + fsize, x0 + dx:x0 + dx + fsize] = 224.0
                    nh = GRID // BLOCK
                    yy, xx = np.mgrid[0:nh, 0:nh]
                    on_fig = ((yy * BLOCK >= y0) & ((yy + 1) * BLOCK <= y0 + fsize)
                              & (xx * BLOCK >= x0) & ((xx + 1) * BLOCK <= x0 + fsize))
                    t = np.zeros((nh, nh, 2))
                    t[on_fig, 0], t[on_fig, 1] = float(dy), float(dx)
                    v = _sensor(a, b, BLOCK, degrade=degrade)
                    cls = L.classify(v, t, tol)
                    for k in acc:
                        acc[k][0] += int((cls[k] & cls["moving"] & on_fig).sum())
                        acc[k][1] += int((cls["moving"] & on_fig).sum())
                    bacc[0] += int((cls["false_motion"] & cls["static"]).sum())
                    bacc[1] += int(cls["static"].sum())
                for k, (num, den) in acc.items():
                    if den:
                        fig[k].append(num / den)
                if bacc[1]:
                    bg_false.append(bacc[0] / bacc[1])
            row = {"figure_size_px": fsize, "nominal_magnitude": m,
                   "displacement_over_figure": m / fsize}
            for k, xs in fig.items():
                mu, lo, hi = L.mean_ci(xs)
                row[k] = mu if xs else None
                row[k + "_ci"] = [lo, hi] if xs else None
            mu, lo, hi = L.mean_ci(bg_false)
            row["background_false_motion"] = mu if bg_false else None
            rows.append(row)
    return rows


def arm_magnitude(seeds, tol, degrade="none"):
    """A1 -- error as a function of DISPLACEMENT MAGNITUDE and DIRECTION, at
    the canonical block. The unit of aggregation is the SEED (§4)."""
    rows = []
    for m in MAGNITUDES:
        per_seed = {"silent_miss": [], "confidently_wrong": [], "correct": [],
                    "false_motion": []}
        actual_mags = []
        for s in seeds:
            rng = np.random.default_rng(s)
            a = L.texture(rng, GRID, beta=1.0, contrast=32.0)
            acc = {k: [0, 0] for k in per_seed}
            for uy, ux in _directions(N_DIRECTIONS):
                dy, dx = int(round(m * uy)), int(round(m * ux))
                actual_mags.append(float(np.hypot(dy, dx)))
                b = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
                t = L.true_uniform(a.shape, BLOCK, dy, dx)
                v = _sensor(a, b, BLOCK, degrade=degrade)
                cls = L.classify(v, t, tol)
                for k in ("silent_miss", "confidently_wrong", "correct"):
                    acc[k][0] += int((cls[k] & cls["moving"]).sum())
                    acc[k][1] += int(cls["moving"].sum())
                acc["false_motion"][0] += int((cls["false_motion"] & cls["static"]).sum())
                acc["false_motion"][1] += int(cls["static"].sum())
            for k, (num, den) in acc.items():
                if den:
                    per_seed[k].append(num / den)
        row = {"nominal_magnitude": m,
               "mean_actual_magnitude": float(np.mean(actual_mags)),
               "block": BLOCK, "radius": BLOCK}
        for k, xs in per_seed.items():
            mu, lo, hi = L.mean_ci(xs)
            row[k] = mu if xs else None
            row[k + "_ci"] = [lo, hi] if xs else None
        rows.append(row)
    return rows


def arm_block_size(seeds, tol, degrade="none"):
    """A2 -- the SAME displacement against DIFFERENT block sizes. This is the
    axis that says whether ~11% is a property of the sensor or of the 4-pixel
    aperture the arc happens to run it at."""
    rows = []
    for block in BLOCKS:
        for m in (1, 2, 4, 6, 8):
            per_seed = {"silent_miss": [], "confidently_wrong": [], "correct": []}
            for s in seeds:
                rng = np.random.default_rng(s)
                a = L.texture(rng, GRID, beta=1.0, contrast=32.0)
                acc = {k: [0, 0] for k in per_seed}
                for uy, ux in _directions(N_DIRECTIONS):
                    dy, dx = int(round(m * uy)), int(round(m * ux))
                    if dy == 0 and dx == 0:
                        continue
                    b = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
                    t = L.true_uniform(a.shape, block, dy, dx)
                    v = _sensor(a, b, block, degrade=degrade)
                    cls = L.classify(v, t, tol)
                    for k in acc:
                        acc[k][0] += int((cls[k] & cls["moving"]).sum())
                        acc[k][1] += int(cls["moving"].sum())
                for k, (num, den) in acc.items():
                    if den:
                        per_seed[k].append(num / den)
            row = {"block": block, "radius": block, "nominal_magnitude": m,
                   "magnitude_over_block": m / block}
            for k, xs in per_seed.items():
                mu, lo, hi = L.mean_ci(xs)
                row[k] = mu if xs else None
                row[k + "_ci"] = [lo, hi] if xs else None
            rows.append(row)
    return rows


def arm_texture(seeds, tol, degrade="none"):
    """A3 -- CONTRAST and SPECTRAL SLOPE, varied ORTHOGONALLY.

    THIS ARM EXISTS TO RESOLVE A RECORDED DISAGREEMENT. The motion rung found
    the flattest texture quartile 4x more error-prone on C1 and NO monotone
    relationship on C2. On found frames "texture quartile" is a MEASURED
    property confounded with everything else in the scene; here contrast and
    spectral slope are INPUTS and can be separated.
    """
    rows = []
    for contrast in CONTRASTS:
        for beta in BETAS:
            per_seed = {"silent_miss": [], "confidently_wrong": [], "correct": []}
            texs = []
            for s in seeds:
                rng = np.random.default_rng(s)
                a = L.texture(rng, GRID, beta=beta, contrast=contrast)
                nh = GRID // BLOCK
                bt = (a[:nh * BLOCK, :nh * BLOCK]
                      .reshape(nh, BLOCK, nh, BLOCK).transpose(0, 2, 1, 3)
                      .std(axis=(2, 3)))
                texs.append(float(bt.mean()))
                acc = {k: [0, 0] for k in per_seed}
                for m in (1, 2, 3, 4):
                    for uy, ux in _directions(N_DIRECTIONS):
                        dy, dx = int(round(m * uy)), int(round(m * ux))
                        if dy == 0 and dx == 0:
                            continue
                        b = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
                        t = L.true_uniform(a.shape, BLOCK, dy, dx)
                        v = _sensor(a, b, BLOCK, degrade=degrade)
                        cls = L.classify(v, t, tol)
                        for k in acc:
                            acc[k][0] += int((cls[k] & cls["moving"]).sum())
                            acc[k][1] += int(cls["moving"].sum())
                for k, (num, den) in acc.items():
                    if den:
                        per_seed[k].append(num / den)
            row = {"contrast_sd": contrast, "beta": beta,
                   "mean_block_std": float(np.mean(texs))}
            for k, xs in per_seed.items():
                mu, lo, hi = L.mean_ci(xs)
                row[k] = mu if xs else None
                row[k + "_ci"] = [lo, hi] if xs else None
            rows.append(row)
    return rows


def arm_bodies(seeds, tol, degrade="none"):
    """A4 -- k TRUE VELOCITIES in one field. Blocks straddling a body seam have
    NO single true vector and are reported SEPARATELY, never pooled: "this
    block has two true answers" is a different fact from "the sensor is
    wrong"."""
    rows = []
    for k in BODY_COUNTS:
        per_seed = {"silent_miss": [], "confidently_wrong": [], "correct": []}
        mixed_rate = []
        for s in seeds:
            rng = np.random.default_rng(s)
            vels = [(int(round(3 * np.sin(2 * np.pi * i / max(k, 1) + 0.4))),
                     int(round(3 * np.cos(2 * np.pi * i / max(k, 1) + 0.4))))
                    for i in range(k)]
            a, b, t, mixed = L.multi_body(rng, GRID, BLOCK, vels)
            v = _sensor(a, b, BLOCK, degrade=degrade)
            cls = L.classify(v, t, tol)
            clean = ~mixed
            mixed_rate.append(float(mixed.mean()))
            for kk in per_seed:
                den = int((cls["moving"] & clean).sum())
                if den:
                    per_seed[kk].append(
                        int((cls[kk] & cls["moving"] & clean).sum()) / den)
        row = {"n_bodies": k, "seam_block_share": float(np.mean(mixed_rate))}
        for kk, xs in per_seed.items():
            mu, lo, hi = L.mean_ci(xs)
            row[kk] = mu if xs else None
            row[kk + "_ci"] = [lo, hi] if xs else None
        rows.append(row)
    return rows


def arm_rotation(seeds, tol, degrade="none"):
    """A5 -- ROTATION. Reported split by whether ONE VECTOR PER BLOCK is even a
    valid model there: blocks whose within-block deformation exceeds half a
    pixel are not a sensor failure, they are a REPRESENTATION failure, and
    conflating the two would flatter or damn the sensor at will."""
    rows = []
    for deg in ROTATIONS:
        per_seed = {"silent_miss": [], "confidently_wrong": [], "correct": []}
        per_seed_def = {"confidently_wrong": []}
        share_def = []
        for s in seeds:
            rng = np.random.default_rng(s)
            a, b, t, deform = L.rotation(rng, GRID, BLOCK, deg)
            v = _sensor(a, b, BLOCK, degrade=degrade)
            cls = L.classify(v, t, tol)
            rigid = deform <= SUBPIXEL_INVISIBLE
            share_def.append(float((~rigid).mean()))
            for kk in per_seed:
                den = int((cls["moving"] & rigid).sum())
                if den:
                    per_seed[kk].append(
                        int((cls[kk] & cls["moving"] & rigid).sum()) / den)
            den = int((cls["moving"] & ~rigid).sum())
            if den:
                per_seed_def["confidently_wrong"].append(
                    int((cls["confidently_wrong"] & cls["moving"] & ~rigid).sum()) / den)
        row = {"degrees": deg,
               "share_blocks_not_translational": float(np.mean(share_def))}
        for kk, xs in per_seed.items():
            mu, lo, hi = L.mean_ci(xs)
            row[kk + "_on_translational_blocks"] = mu if xs else None
            row[kk + "_on_translational_blocks_ci"] = [lo, hi] if xs else None
        mu, lo, hi = L.mean_ci(per_seed_def["confidently_wrong"])
        row["confidently_wrong_on_deforming_blocks"] = \
            mu if per_seed_def["confidently_wrong"] else None
        rows.append(row)
    return rows


def arm_zero(seeds, degrade="none"):
    """A6 -- THE GENUINE ZERO FIELD, with and without sensor noise.

    `noise_sd = 0` is the bit-identical case (I1's population). The noisy cases
    are the realistic static scene: a camera looking at a still world still
    delivers different pixels. FALSE MOTION here is motion INVENTED, and it is
    the disease behind the phi rung's constant `(-3,-1)`."""
    rows = []
    for sd in NOISE_SDS:
        per_seed = []
        per_seed_mag = []
        for s in seeds:
            rng = np.random.default_rng(s)
            a = L.texture(rng, GRID, beta=1.0, contrast=32.0)
            b = L.quantise(a + rng.normal(0.0, sd, a.shape)) if sd > 0 else a.copy()
            t = L.true_uniform(a.shape, BLOCK, 0.0, 0.0)
            v = _sensor(a, b, BLOCK, degrade=degrade)
            cls = L.classify(v, t, 0.0)
            per_seed.append(float((cls["false_motion"] & cls["static"]).mean()))
            mags = np.linalg.norm(v, axis=-1)
            nz = mags[mags > 0]
            per_seed_mag.append(float(nz.mean()) if nz.size else 0.0)
        mu, lo, hi = L.mean_ci(per_seed)
        rows.append({"noise_sd": sd, "false_motion": mu,
                     "false_motion_ci": [lo, hi],
                     "mean_magnitude_of_invented_vectors":
                         float(np.mean(per_seed_mag))})
    return rows


def arm_bordered(seeds, tol, degrade="none"):
    """A7 -- THE BORDERED PAN, reported separately from the toroidal one.

    A real pan brings NEW content in at one edge and takes content out at the
    other; `vector_field` pads with `mode="edge"`, i.e. it FABRICATES the
    content it matches against there. Blocks whose source lies off-frame are
    FLAGGED, not pooled -- their true vector is real but the evidence for it
    genuinely is not in the frame.
    """
    rows = []
    big = GRID + 32
    for m in (1, 2, 4, 6, 8):
        per_seed_int, per_seed_edge = [], []
        for s in seeds:
            rng = np.random.default_rng(s)
            full = L.texture(rng, big, beta=1.0, contrast=32.0)
            acc_i, acc_e = [0, 0], [0, 0]
            for uy, ux in _directions(N_DIRECTIONS):
                dy, dx = int(round(m * uy)), int(round(m * ux))
                if dy == 0 and dx == 0:
                    continue
                o = 16
                a = full[o:o + GRID, o:o + GRID]
                b = full[o - dy:o - dy + GRID, o - dx:o - dx + GRID]
                t = L.true_uniform(a.shape, BLOCK, dy, dx)
                v = _sensor(a, b, BLOCK, degrade=degrade)
                cls = L.classify(v, t, tol)
                nh = GRID // BLOCK
                yy, xx = np.mgrid[0:nh, 0:nh]
                pad = int(np.ceil(max(abs(dy), abs(dx)) / BLOCK)) + 1
                edge = ((yy < pad) | (yy >= nh - pad)
                        | (xx < pad) | (xx >= nh - pad))
                for sel, acc in ((~edge, acc_i), (edge, acc_e)):
                    den = int((cls["moving"] & sel).sum())
                    acc[0] += int((cls["confidently_wrong"] & cls["moving"] & sel).sum())
                    acc[1] += den
            if acc_i[1]:
                per_seed_int.append(acc_i[0] / acc_i[1])
            if acc_e[1]:
                per_seed_edge.append(acc_e[0] / acc_e[1])
        mi, li, hi_ = L.mean_ci(per_seed_int)
        me, le, he = L.mean_ci(per_seed_edge)
        rows.append({"nominal_magnitude": m,
                     "confidently_wrong_interior": mi,
                     "confidently_wrong_interior_ci": [li, hi_],
                     "confidently_wrong_border": me,
                     "confidently_wrong_border_ci": [le, he]})
    return rows


def ambiguity_decomposition(seeds, tol, degrade="none"):
    """THE DECOMPOSITION, DECLARED SECONDARY.

    It splits the error into STIMULUS AMBIGUITY (the true answer is not
    recoverable under the SAD objective) and SENSOR DEFECT (it was recoverable
    and the sensor missed it). This shares the objective with the sensor, so it
    is NOT independent evidence about the arithmetic -- it is reported as a
    decomposition and never as the headline. What licenses it at all is that it
    is GROUND-TRUTH-CONDITIONAL: it asks about the KNOWN `t`, which the sensor
    has no access to.
    """
    rows = []
    for m in (1, 2, 3, 4, 5, 6, 8):
        res, unres_err, res_err = [], [], []
        for s in seeds:
            rng = np.random.default_rng(s)
            a = L.texture(rng, GRID, beta=1.0, contrast=32.0)
            for uy, ux in _directions(4):
                dy, dx = int(round(m * uy)), int(round(m * ux))
                if dy == 0 and dx == 0:
                    continue
                b = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
                t = L.true_uniform(a.shape, BLOCK, dy, dx)
                uniq = L.true_offset_is_unique_minimum(a, b, BLOCK, BLOCK, t)
                v = _sensor(a, b, BLOCK, degrade=degrade)
                cls = L.classify(v, t, tol)
                bad = (cls["confidently_wrong"] | cls["silent_miss"]) & cls["moving"]
                res.append(float(uniq.mean()))
                if uniq.sum():
                    res_err.append(float((bad & uniq).sum()) / float(uniq.sum()))
                if (~uniq).sum():
                    unres_err.append(float((bad & ~uniq).sum()) / float((~uniq).sum()))
        rows.append({
            "nominal_magnitude": m,
            "share_blocks_where_truth_is_the_unique_sad_minimum": float(np.mean(res)),
            "error_rate_on_resolvable_blocks_SENSOR_DEFECT":
                float(np.mean(res_err)) if res_err else None,
            "error_rate_on_ambiguous_blocks_STIMULUS_AMBIGUITY":
                float(np.mean(unres_err)) if unres_err else None,
        })
    return rows


# --- the operating point, and the bound it forces ---------------------------

def operating_point(seeds, tol, degrade="none"):
    """THE NUMBER EVERY LANDED MOTION COUNT INHERITS.

    Measured at the arc's own operating point and on the arc's own known-answer
    stimulus: BLOCK=4, radius=4, a global pan of exactly one block -- the SAME
    construction `scripts/motion_texture_diagnostic.py` used to read ~11%. This
    is the reproduction check: if this rung's constructed-truth apparatus is
    sound, this arm must land near that recorded figure on a comparable
    stimulus.
    """
    rows = []
    for contrast in (8.0, 32.0):
        acc = {"silent_miss": [], "confidently_wrong": [], "correct": []}
        for s in seeds:
            rng = np.random.default_rng(s)
            a = L.texture(rng, GRID, beta=1.0, contrast=contrast)
            b = np.roll(np.roll(a, BLOCK, axis=0), BLOCK, axis=1)
            t = L.true_uniform(a.shape, BLOCK, BLOCK, BLOCK)
            v = _sensor(a, b, BLOCK, degrade=degrade)
            cls = L.classify(v, t, tol)
            den = int(cls["moving"].sum())
            for k in acc:
                acc[k].append(int((cls[k] & cls["moving"]).sum()) / den)
        row = {"contrast_sd": contrast, "stimulus": "global pan of one block"}
        for k, xs in acc.items():
            mu, lo, hi = L.mean_ci(xs)
            row[k] = mu
            row[k + "_ci"] = [lo, hi]
        rows.append(row)
    return rows


def grouping_bound(seeds, degrade="none"):
    """THE BOUND, MEASURED RATHER THAN ARGUED.

    Runs the ACTUAL grouping pipeline (`seeds/vision_motion_group.json` via
    `motion_group_world`) on fields whose TRUE body count is known by
    construction, and reports how many multi-cell groups it mints. The
    over-grouping factor here has GROUND TRUTH in its denominator, which the
    landed 23x does not (that compares against a static-form control).

    This is the arm a future rung cites when it wants to know what "3.95
    multi-cell groups per frame" is allowed to mean.
    """
    from substrate.boot_core import boot_core, load_seeds_into    # noqa: E402
    rows = []
    # (k, label, velocity generator). THE SECOND FAMILY WAS ADDED AFTER THE
    # FIRST RAN, AND THE REASON IS DISCLOSED RATHER THAN BURIED (§6: controls
    # must correspond to the ACTUAL experiment). The first family's velocities
    # have |D| ~ 3.2, comfortably inside the aperture, where the sensor's
    # confidently-wrong rate is ~3%. THE LANDED GLOBAL-PAN CONTROL RAN AT
    # `dom_v = (4,4)` -- the APERTURE CORNER, where this rung measures ~10.7%.
    # A bound read at 3% and quoted against a claim made at 10.7% would not be
    # a bound. This is not metric surgery (§5): no arm is re-run and no number
    # is reinterpreted; a NON-COMPARABLE arm is joined by a comparable one, and
    # both are reported.
    families = [("inside_aperture", lambda k, i: (
                    int(round(3 * np.sin(2 * np.pi * i / k + 0.4))),
                    int(round(3 * np.cos(2 * np.pi * i / k + 0.4))))),
                ("aperture_corner", lambda k, i: (
                    BLOCK if i % 2 == 0 else -BLOCK,
                    BLOCK if i < 2 else -BLOCK))]
    for fam, gen in families:
      for k in (1, 2, 3):
        minted, true_k, checks = [], [], []
        for s in seeds:
            rng = np.random.default_rng(s)
            vels = [gen(k, i) for i in range(k)]
            a, b, _t, _mixed = L.multi_body(rng, GRID, BLOCK, vels)
            vf = _sensor(a, b, BLOCK, degrade=degrade)
            s_, ag_ = boot_core()
            load_seeds_into(s_, ag_, ["vision_motion_group"])
            h = mgw.add_mfield(s_, vf)
            mgw.settle(s_, marm=1.0, mcontrast=1.0, mtol_exact=0.0)
            chk = mgw.assert_settled(s_, h)
            if chk["cells_without_tolerance"] or chk["unsettled_pairs"]:
                raise SystemExit(f"UNSETTLED FLOOD at k={k} seed={s}: {chk}. VOID.")
            objs = [o for o in mgw.objects(s_) if o["members"] > 1]
            minted.append(len(objs))
            true_k.append(k)
            checks.append(chk)
        mu, lo, hi = L.mean_ci(minted)
        rows.append({"family": fam, "true_bodies": k,
                     "velocities": [list(map(int, gen(k, i))) for i in range(k)],
                     "multi_cell_groups_minted": mu,
                     "multi_cell_groups_minted_ci": [lo, hi],
                     "over_grouping_factor_vs_ground_truth": mu / k})
    return rows


# --- the gate verdict --------------------------------------------------------

BASELINE = os.path.join(ROOT, "results", "motion_sensor_gate_baseline.json")


def verdict(report, baseline):
    """PASS/FAIL. Two exact invariants plus a REGRESSION comparison against the
    committed baseline. The regression bound is the baseline's OWN recorded
    seed-level CI -- a comparison point that falls out of a prior measurement
    rather than one written here."""
    fails = []
    for inv in report["invariants"]:
        if not inv["passed"]:
            fails.append(f"{inv['name']} VIOLATED: {inv['violations'][:3]}")
    if baseline:
        for row_new, row_old in zip(report["operating_point"],
                                    baseline["operating_point"]):
            for k in ("silent_miss", "confidently_wrong"):
                hi = row_old[k + "_ci"][1]
                if row_new[k] > hi:
                    fails.append(
                        f"REGRESSION at contrast {row_new['contrast_sd']}: "
                        f"{k} {row_new[k]:.4f} above baseline upper CI {hi:.4f}")
        for row_new, row_old in zip(report["zero_field"], baseline["zero_field"]):
            hi = row_old["false_motion_ci"][1]
            if row_new["false_motion"] > hi:
                fails.append(
                    f"REGRESSION at noise_sd {row_new['noise_sd']}: false_motion "
                    f"{row_new['false_motion']:.4f} above baseline upper CI {hi:.4f}")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="confirm", choices=("pilot", "confirm"))
    ap.add_argument("--degrade", default="none",
                    choices=("none", "tiebreak_corner", "radius_half", "sad_coarse"))
    ap.add_argument("--n-seeds", type=int, default=24)
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--skip-grouping", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    prov = provenance_line()
    print("PROVENANCE (from INSIDE the measuring process):", prov, flush=True)

    checks = assert_reference_is_the_real_sensor()
    print(f"reference == mgw.vector_field on {checks} inputs (bit-identical)",
          flush=True)

    if args.mode == "pilot":
        seeds = list(PILOT_SEEDS)
    else:
        seeds = list(range(SEED_BLOCK, SEED_BLOCK + args.n_seeds))
    print(f"mode={args.mode} degrade={args.degrade} "
          f"seeds={seeds[0]}..{seeds[-1]} (n={len(seeds)})", flush=True)

    invs = [invariant_zero_identity(seeds, args.degrade),
            invariant_unique_minimum(seeds, args.degrade)]
    for i in invs:
        print(f"  {i['name']}: {'PASS' if i['passed'] else 'FAIL'}", flush=True)

    errs = collect_errors(seeds, args.degrade)
    tol_all = L.otsu_split(errs)
    errs_in = collect_errors_within_aperture(seeds, args.degrade)
    tol = L.otsu_split(errs_in)
    print(f"  OTSU over ALL {errs.size} observed error magnitudes: "
          f"{tol_all:.4f}  (EMERGENT -- names the APERTURE)", flush=True)
    print(f"  OTSU within aperture, {errs_in.size} magnitudes: "
          f"{tol:.4f}  (EMERGENT -- the accuracy tolerance)", flush=True)

    rep = {
        "provenance": prov,
        "mode": args.mode,
        "degrade": args.degrade,
        "seeds": [int(seeds[0]), int(seeds[-1])],
        "n_seeds": len(seeds),
        "reference_equality_checks": checks,
        "config": {"GRID": GRID, "BLOCK": BLOCK, "radius": "= block",
                   "MAGNITUDES": MAGNITUDES, "N_DIRECTIONS": N_DIRECTIONS,
                   "BLOCKS": BLOCKS, "CONTRASTS": CONTRASTS, "BETAS": BETAS},
        "tolerance_otsu_within_aperture_emergent": tol,
        "tolerance_otsu_all_conditions_emergent": tol_all,
        "tolerance_exact": 0.0,
        "invariants": invs,
        "operating_point": operating_point(seeds, tol, args.degrade),
        "zero_field": arm_zero(seeds, args.degrade),
        "magnitude": arm_magnitude(seeds, tol, args.degrade),
        "block_size": arm_block_size(seeds, tol, args.degrade),
        "texture": arm_texture(seeds, tol, args.degrade),
        "bodies": arm_bodies(seeds, tol, args.degrade),
        "rotation": arm_rotation(seeds, tol, args.degrade),
        "bordered": arm_bordered(seeds, tol, args.degrade),
        "figure_on_uniform": arm_figure_on_uniform(seeds, tol, args.degrade),
        "ambiguity": ambiguity_decomposition(seeds, tol, args.degrade),
    }
    # The same three rates at the EXACT tolerance, so the headline is never
    # conditional on Otsu alone (the motion rung reported both arms too).
    rep["operating_point_exact_tolerance"] = operating_point(seeds, 0.0, args.degrade)

    if not args.skip_grouping:
        rep["grouping_bound"] = grouping_bound(seeds[:8], args.degrade)

    baseline = None
    if os.path.exists(BASELINE) and not args.write_baseline:
        with open(BASELINE) as fh:
            baseline = json.load(fh)
    fails = verdict(rep, baseline)
    rep["verdict"] = "PASS" if not fails else "FAIL"
    rep["failures"] = fails
    rep["baseline_compared"] = bool(baseline)
    rep["elapsed_s"] = round(time.time() - t0, 1)

    name = args.out or (f"motion_sensor_gate_{args.mode}"
                        + (f"_{args.degrade}" if args.degrade != "none" else "")
                        + ".json")
    out = os.path.join(ROOT, "results", name)
    with open(out, "w") as fh:
        json.dump(rep, fh, indent=1, default=str)
    print("wrote", out, "in", rep["elapsed_s"], "s")

    if args.write_baseline:
        with open(BASELINE, "w") as fh:
            json.dump(rep, fh, indent=1, default=str)
        print("wrote baseline", BASELINE)

    print(f"VERDICT: {rep['verdict']}"
          + ("" if not fails else "\n  " + "\n  ".join(fails)))
    return 0 if rep["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
