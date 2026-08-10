#!/usr/bin/env python3
"""COLOUR SALIENCE — pop-out for the EQUILUMINANT target (confirmatory run).

Pre-registration: VISION_COLOUR_PREREG.md (committed BEFORE this run, §3). Colour
is the pop-out channel where luminance salience is ZERO: a near-equiluminant target
(zero luminance contrast) with high cone-opponent contrast becomes salient via
COLOUR and is streamed in by the bounded stream, where a luminance-only salience
MISSES it. The opponent-contrast computation and the interactive combine are the
vision_colour RULES (cc_contrast / cc_salience); the bounded spend is the unchanged
vision_stream rule. This runner only CONSTRUCTS cone-cell fields and READS the
stream/salience back (mechanical I/O, §0), and COMPUTES metrics OVER them.

Run from the gamma-substrate dir:
    PYTHONPATH=runners/dsl/python:. python scripts/colour_measure.py
"""
from __future__ import annotations
import json
import os
import random
import time

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import colour_world as cw  # noqa: E402
from scripts.stream_measure import tunnel  # noqa: E402  (REUSE the sibling readout)


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_stream", "vision_colour"])
    return s, ag


def _run(s, handle, *, salience, colour, stream=True):
    """Two mechanical phases (no decision): (1) arm flags, tick -> compute the
    residual field to fixpoint; (2) set the stream flag, tick -> spend the budget."""
    cw.set_flags(s, salience=salience, colour=colour)
    cw.tick(s)
    if stream:
        cw.set_stream(s, 1.0)
        cw.tick(s)
    return handle


# --------------------------------------------------------------------------- #
#  Stimulus builders (mechanical; a cone-cell grid).
# --------------------------------------------------------------------------- #
def _grid(nrows, ncols, base, target=None, target_rc=None):
    """A uniform `base` (cL,cM,cS) field with an optional single `target` cell."""
    cells = []
    for r in range(nrows):
        for c in range(ncols):
            spec = dict(base)
            if target is not None and (r, c) == target_rc:
                spec = dict(target)
            cells.append(dict(rrow=r, rcol=c, **spec))
    return cells


# =========================================================================== #
#  ARM H — EQUILUMINANT POP-OUT (the headline discriminator)
# =========================================================================== #
def arm_equiluminant():
    base = dict(cL=10, cM=10, cS=10)              # lum=20, rg=0
    target = dict(cL=15, cM=5, cS=10)             # lum=20 (EQUILUMINANT), rg=10
    cells = _grid(5, 5, base, target, (2, 2))
    B = 1
    # COLOUR arm.
    s, _ = _boot()
    h = cw.add_field(s, budget=B, cells=cells, nrows=5, ncols=5)
    _run(s, h, salience=1.0, colour=1.0)
    colour_order = cw.cell_order(s, h, 2, 2)
    colour_spent = cw.read_spent(s, h)
    tgt_csal = cw.cell_attr(s, h, 2, 2, "csal")
    tgt_lsal = cw.cell_attr(s, h, 2, 2, "lsal")
    # LUMINANCE-ONLY arm (colour=0), SAME field.
    s2, _ = _boot()
    h2 = cw.add_field(s2, budget=B, cells=cells, nrows=5, ncols=5)
    _run(s2, h2, salience=1.0, colour=0.0)
    lum_order = cw.cell_order(s2, h2, 2, 2)
    lum_spent = cw.read_spent(s2, h2)
    passed = (colour_order == 0 and colour_spent == 1
              and lum_order == -1 and lum_spent == 0
              and tgt_lsal == 0.0 and tgt_csal > 0.0)
    return {"arm": "H_equiluminant", "pass": bool(passed),
            "target_csal": tgt_csal, "target_lsal": tgt_lsal,
            "colour_target_order": colour_order, "colour_spent": colour_spent,
            "lum_only_target_order": lum_order, "lum_only_spent": lum_spent}


# =========================================================================== #
#  ARM I — INTERACTIVE COMBINATION (not a trivial sum)
# =========================================================================== #
def arm_interactive():
    base = dict(cL=10, cM=10, cS=10)              # lum=20, rg=0
    target = dict(cL=25, cM=5, cS=10)             # lum=30 (Δlum), rg=20
    cells = _grid(5, 5, base, target, (2, 2))
    B = 1
    s, _ = _boot()
    h = cw.add_field(s, budget=B, cells=cells, nrows=5, ncols=5)
    _run(s, h, salience=1.0, colour=1.0)
    order = cw.cell_order(s, h, 2, 2)
    lsal = cw.cell_attr(s, h, 2, 2, "lsal")
    csal = cw.cell_attr(s, h, 2, 2, "csal")
    residual = cw.cell_attr(s, h, 2, 2, "residual")
    trivial_sum = lsal + csal
    interaction = residual - trivial_sum        # == lsal*csal if interactive
    passed = (order == 0 and lsal > 0.0 and csal > 0.0
              and residual > trivial_sum         # strictly non-additive
              and abs(interaction - lsal * csal) < 1e-9)
    return {"arm": "I_interactive", "pass": bool(passed), "target_order": order,
            "lsal": lsal, "csal": csal, "residual": residual,
            "trivial_sum": trivial_sum, "interaction_term": interaction,
            "expected_lsal_times_csal": lsal * csal}


# =========================================================================== #
#  ARM L — LUMINANCE-ONLY STILL WORKS (colour is additive capability)
# =========================================================================== #
def arm_luminance_only_works():
    # A GENUINELY chroma-neutral luminance target. NB (found during the run, see
    # RESULTS "what I got wrong"): the blue-yellow opponent axis by = S-(L+M) is
    # NOT luminance-invariant, so raising L+M at fixed S injects real chromatic
    # contrast. To make a PURE-luminance target (csal == 0 exactly) the S cone must
    # CO-VARY with L+M: base by = 30-20 = 10; target by = 50-40 = 10 (SAME), rg = 0
    # (SAME) -> both opponent axes constant, only luminance differs.
    base = dict(cL=10, cM=10, cS=30)              # lum=20, rg=0, by=10
    target = dict(cL=20, cM=20, cS=50)            # lum=40 (Δlum), rg=0, by=10 (chroma SAME)
    cells = _grid(5, 5, base, target, (2, 2))
    B = 1
    # WITH colour on.
    s, _ = _boot()
    h = cw.add_field(s, budget=B, cells=cells, nrows=5, ncols=5)
    _run(s, h, salience=1.0, colour=1.0)
    colour_order = cw.cell_order(s, h, 2, 2)
    tgt_csal = cw.cell_attr(s, h, 2, 2, "csal")
    # WITHOUT colour (luminance-only path).
    s2, _ = _boot()
    h2 = cw.add_field(s2, budget=B, cells=cells, nrows=5, ncols=5)
    _run(s2, h2, salience=1.0, colour=0.0)
    lum_order = cw.cell_order(s2, h2, 2, 2)
    passed = (colour_order == 0 and lum_order == 0 and tgt_csal == 0.0)
    return {"arm": "L_luminance_only_works", "pass": bool(passed),
            "with_colour_target_order": colour_order,
            "lum_only_target_order": lum_order, "target_csal": tgt_csal}


# =========================================================================== #
#  ARM U — UNIFORM-COLOUR FLOOR (anti-overfit, deterministic, exact 0)
# =========================================================================== #
def arm_uniform_floor():
    base = dict(cL=10, cM=10, cS=10)
    cells = _grid(10, 10, base)                   # no opponent contrast anywhere
    B = 8
    s, _ = _boot()
    h = cw.add_field(s, budget=B, cells=cells, nrows=10, ncols=10)
    _run(s, h, salience=1.0, colour=1.0)
    csal = cw.read_attr(s, h, "csal")
    spent = cw.read_spent(s, h)
    n_pos_csal = sum(1 for v in csal if v > 0.0)
    passed = (max(csal) == 0.0 and n_pos_csal == 0 and spent == 0)
    return {"arm": "U_uniform_floor", "pass": bool(passed),
            "max_csal": max(csal), "n_positive_csal": n_pos_csal, "spent": spent}


# =========================================================================== #
#  ARM N — COLOUR-NOISE FLOOR (anti-overfit, n=100, seeds 34000-34099, exact 0)
# =========================================================================== #
def arm_noise_floor(n=100, seed0=34000):
    B = 4
    false_pops = 0
    for k in range(n):
        rng = random.Random(seed0 + k)
        cells = [dict(rrow=r, rcol=c,
                      cL=rng.randint(0, 20), cM=rng.randint(0, 20),
                      cS=rng.randint(0, 20))
                 for r in range(10) for c in range(10)]
        s, _ = _boot()
        h = cw.add_field(s, budget=B, cells=cells, nrows=10, ncols=10)
        _run(s, h, salience=1.0, colour=1.0)
        order = cw.read_order(s, h)
        spent = cw.read_spent(s, h)
        regions = [{"residual": v} for v in cw.read_attr(s, h, "residual")]
        if tunnel(regions, order, spent, B):
            false_pops += 1
    passed = (false_pops == 0)
    return {"arm": "N_noise_floor", "pass": bool(passed), "n": n,
            "false_pops": false_pops}


# =========================================================================== #
#  §9 OFF-day — the seed is inert with both flags OFF (default).
# =========================================================================== #
def arm_offday():
    base = dict(cL=10, cM=10, cS=10)
    target = dict(cL=15, cM=5, cS=10)
    cells = _grid(5, 5, base, target, (2, 2))
    s, _ = _boot()
    h = cw.add_field(s, budget=3, cells=cells, nrows=5, ncols=5)
    # DO NOT arm the colour flags (default 0.0). Only the stream flag.
    cw.set_stream(s, 1.0)
    cw.tick(s)
    order = cw.read_order(s, h)
    spent = cw.read_spent(s, h)
    residual = cw.read_attr(s, h, "residual")
    cc_done = cw.read_attr(s, h, "cc_done")
    passed = (spent == 0 and all(o < 0 for o in order)
              and max(residual) == 0.0 and max(cc_done) == 0.0)
    return {"arm": "X_offday", "pass": bool(passed), "spent": spent,
            "max_residual": max(residual), "max_cc_done": max(cc_done),
            "all_unresolved": all(o < 0 for o in order)}


def main():
    t0 = time.time()
    prov = provenance_line()
    print("PROVENANCE:", prov)
    arms = [arm_equiluminant(), arm_interactive(), arm_luminance_only_works(),
            arm_uniform_floor(), arm_offday(), arm_noise_floor()]
    out = {"provenance": prov, "arms": arms,
           "elapsed_s": round(time.time() - t0, 1)}
    os.makedirs("results", exist_ok=True)
    with open("results/colour_measure.json", "w") as f:
        json.dump(out, f, indent=2)
    print()
    for a in arms:
        print(f"  {a['arm']:24s} {'PASS' if a['pass'] else 'FAIL'}")
    print(f"\n  elapsed {out['elapsed_s']}s -> results/colour_measure.json")


if __name__ == "__main__":
    main()
