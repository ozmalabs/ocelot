#!/usr/bin/env python3
"""CEREBRAL ACHROMATOPSIA — colour-SIGN / chromatic-STRUCTURE dissociation (run).

Pre-registration: VISION_ACHROMATOPSIA_PREREG.md (committed BEFORE this run, §3).
A LESION-VALIDATION gate for the design's luminance-structure / colour-sign split
(VISION_VENTRAL_GROUNDING.md gate 5; Heywood & Cowey 1997). Ablate the colour-
IDENTITY sign layer (achromatopsia=1 ⇒ ci_mint_category + ci_assign suppressed) and
show: colour CATEGORIZATION is LOST while chromatic STRUCTURE (chromatic-border csal,
shape-from-colour, colour-defined boundary + its displacement) is BYTE-FOR-BYTE
PRESERVED. Every decision is a seed rule; this runner only CONSTRUCTS cone-cell
fields, blind-writes the per-arm flags, and READS both layers back (mechanical I/O).

Run from the gamma-substrate dir:
    PYTHONPATH=runners/dsl/python:. python scripts/achromatopsia_measure.py
"""
from __future__ import annotations
import json
import os
import time

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import achromatopsia_world as aw  # noqa: E402


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_colour", "vision_colour_identity"])
    return s, ag


# --- stimuli (mechanical cone-cell fields) -------------------------------------
# Equiluminant colours: A(crg=+10) and B(crg=-10), BOTH L+M=20, cS=20 (so cby=0).
A = dict(cL=15, cM=5, cS=20)     # crg=+10, cby=0, L+M=20
B = dict(cL=5, cM=15, cS=20)     # crg=-10, cby=0, L+M=20


def _equiluminant_figure(fig_cols=(1, 2, 3)):
    """6x6: ground B, a 3-row figure of A at rows 1-3, columns `fig_cols`. All cells
    L+M=20 (EQUILUMINANT) so the figure is defined by CHROMA alone (lsal=0)."""
    cells = []
    fcols = set(fig_cols)
    for r in range(6):
        for c in range(6):
            spec = dict(A) if (1 <= r <= 3 and c in fcols) else dict(B)
            cells.append(dict(rrow=r, rcol=c, **spec))
    return cells


def _run(cells, *, achromatopsia):
    s, _ = _boot()
    h = aw.add_field(s, cells=cells)
    aw.set_flags(s, salience=1.0, colour=1.0, identity=1.0,
                 achromatopsia=achromatopsia)
    aw.tick(s)
    return s, h


def _maxabs(xs):
    return max((abs(x) for x in xs), default=0.0)


# =========================================================================== #
#  DISSOCIATION (headline) + CONTROL_VALIDITY
# =========================================================================== #
def arm_dissociation():
    cells = _equiluminant_figure()
    si, hi = _run(cells, achromatopsia=0.0)   # INTACT
    sa, ha = _run(cells, achromatopsia=1.0)   # ABLATED (achromatopsia)

    # categorization
    n_cat_i, n_cat_a = aw.n_categories(si), aw.n_categories(sa)
    n_sig_i, n_sig_a = aw.n_signs_assigned(si, hi), aw.n_signs_assigned(sa, ha)
    signs_ok_i = aw.all_signs_correct(si, hi)

    # chromatic structure
    csal_i = aw.read_attr(si, hi, "csal")
    csal_a = aw.read_attr(sa, ha, "csal")
    lsal_i = aw.read_attr(si, hi, "lsal")
    csal_bytediff = max((abs(a - b) for a, b in zip(csal_i, csal_a)), default=0.0)
    n_csal_pos_i = len(aw.csal_positive_cells(si, hi))
    n_csal_pos_a = len(aw.csal_positive_cells(sa, ha))

    # control-validity: ablated structure ALIVE (§1.1)
    op_done_a = aw.read_attr(sa, ha, "op_done")
    ablated_structure_alive = (max(csal_a) > 0.0 and n_csal_pos_a > 0
                               and min(op_done_a) == 1.0)

    # colour-defined boundary DISPLACEMENT (motion substrate): shift figure +1 col.
    f1 = _equiluminant_figure(fig_cols=(1, 2, 3))
    f2 = _equiluminant_figure(fig_cols=(2, 3, 4))
    si1, hi1 = _run(f1, achromatopsia=0.0); si2, hi2 = _run(f2, achromatopsia=0.0)
    sa1, ha1 = _run(f1, achromatopsia=1.0); sa2, ha2 = _run(f2, achromatopsia=1.0)
    shift_i = aw.csal_centroid_col(si2, hi2) - aw.csal_centroid_col(si1, hi1)
    shift_a = aw.csal_centroid_col(sa2, ha2) - aw.csal_centroid_col(sa1, ha1)

    dissociation = (
        n_cat_i == 2 and n_cat_a == 0          # categorization lost
        and n_sig_i == 36 and n_sig_a == 0
        and csal_bytediff == 0.0               # structure BYTE-identical across arms
        and n_csal_pos_i == n_csal_pos_a and n_csal_pos_a > 0
        and max(csal_a) > 0.0 and _maxabs(lsal_i) == 0.0   # equiluminant: chroma only
        and abs(shift_i - 1.0) < 1e-9 and abs(shift_a - 1.0) < 1e-9  # +1 col, both
        and shift_i == shift_a
    )
    control_validity = (ablated_structure_alive and n_cat_i == 2 and signs_ok_i)

    return {
        "categories_intact": aw.categories(si), "n_categories_intact": n_cat_i,
        "n_categories_ablated": n_cat_a,
        "n_signs_intact": n_sig_i, "n_signs_ablated": n_sig_a,
        "all_signs_correct_intact": signs_ok_i,
        "max_csal_intact": max(csal_i), "max_csal_ablated": max(csal_a),
        "csal_max_abs_diff_across_arms": csal_bytediff,
        "n_csal_positive_intact": n_csal_pos_i, "n_csal_positive_ablated": n_csal_pos_a,
        "max_lsal_intact": _maxabs(lsal_i),
        "op_done_min_ablated": min(op_done_a),
        "boundary_shift_intact": shift_i, "boundary_shift_ablated": shift_a,
        "ablated_structure_alive": ablated_structure_alive,
        "pass_dissociation": bool(dissociation),
        "pass_control_validity": bool(control_validity),
        "pass": bool(dissociation and control_validity),
    }


# =========================================================================== #
#  SPLIT_CLEAN — luminance structure fully intact throughout (chroma-specific)
# =========================================================================== #
def arm_split_clean():
    # luminance vertical edge, ZERO chroma: left L+M=20, right L+M=40; crg=cby=0 both.
    cells = []
    for r in range(6):
        for c in range(6):
            if c <= 2:
                cells.append(dict(rrow=r, rcol=c, cL=10, cM=10, cS=20))   # L+M=20
            else:
                cells.append(dict(rrow=r, rcol=c, cL=20, cM=20, cS=40))   # L+M=40
    si, hi = _run(cells, achromatopsia=0.0)
    sa, ha = _run(cells, achromatopsia=1.0)
    lsal_i = aw.read_attr(si, hi, "lsal")
    lsal_a = aw.read_attr(sa, ha, "lsal")
    csal_i = aw.read_attr(si, hi, "csal")
    lsal_diff = max((abs(a - b) for a, b in zip(lsal_i, lsal_a)), default=0.0)
    passed = (max(lsal_i) > 0.0 and lsal_diff == 0.0 and _maxabs(csal_i) == 0.0)
    return {"max_lsal_intact": max(lsal_i), "max_lsal_ablated": max(lsal_a),
            "lsal_max_abs_diff_across_arms": lsal_diff,
            "max_csal": _maxabs(csal_i), "pass": bool(passed)}


# =========================================================================== #
#  FLOOR — achromatic ⇒ no colour in EITHER arm; not confounded with luminance
# =========================================================================== #
def arm_floor():
    # achromatic luminance ramp: cL=cM=v, cS=2v ⇒ crg=0, cby=0; L+M=2v varies.
    cells = []
    for r in range(6):
        for c in range(6):
            v = 5 + (6 * r + c)
            cells.append(dict(rrow=r, rcol=c, cL=v, cM=v, cS=2 * v))
    si, hi = _run(cells, achromatopsia=0.0)
    sa, ha = _run(cells, achromatopsia=1.0)
    csal_i = aw.read_attr(si, hi, "csal")
    csal_a = aw.read_attr(sa, ha, "csal")
    lsal_i = aw.read_attr(si, hi, "lsal")
    chrom_cat_i = aw.n_chromatic_categories(si)
    chrom_cat_a = aw.n_chromatic_categories(sa)
    passed = (_maxabs(csal_i) == 0.0 and _maxabs(csal_a) == 0.0     # no chroma structure
              and chrom_cat_i == 0 and chrom_cat_a == 0            # no colour sign
              and max(lsal_i) > 0.0)                               # luminance present
    return {"max_csal_intact": _maxabs(csal_i), "max_csal_ablated": _maxabs(csal_a),
            "n_chromatic_categories_intact": chrom_cat_i,
            "n_chromatic_categories_ablated": chrom_cat_a,
            "achromatic_grey_categories_intact": aw.n_categories(si),  # honest report
            "max_lsal_intact": max(lsal_i), "pass": bool(passed)}


# =========================================================================== #
#  OFFDAY (§9) — all flags default 0 ⇒ inert
# =========================================================================== #
def arm_offday():
    s, _ = _boot()
    h = aw.add_field(s, cells=_equiluminant_figure())
    aw.tick(s)  # flags left at default (all 0.0)
    max_cc = _maxabs(aw.read_attr(s, h, "cc_done"))
    max_op = _maxabs(aw.read_attr(s, h, "op_done"))
    max_sign = _maxabs(aw.read_attr(s, h, "sign_rg"))
    k = aw.n_categories(s)
    passed = (max_cc == 0.0 and k == 0 and max_op == 0.0 and max_sign == 0.0)
    return {"max_cc_done": max_cc, "n_categories": k, "max_op_done": max_op,
            "max_sign_rg": max_sign, "pass": bool(passed)}


def main():
    t0 = time.time()
    prov = provenance_line()
    results = {
        "provenance": prov,
        "DISSOCIATION": arm_dissociation(),
        "SPLIT_CLEAN": arm_split_clean(),
        "FLOOR": arm_floor(),
        "OFFDAY": arm_offday(),
    }
    all_pass = all(results[k]["pass"] for k in results
                   if isinstance(results.get(k), dict) and "pass" in results[k])
    results["ALL_PASS"] = all_pass
    results["elapsed_s"] = round(time.time() - t0, 2)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "achromatopsia_measure.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(prov)
    d = results["DISSOCIATION"]
    print(f"  DISSOCIATION      dissoc={d['pass_dissociation']} "
          f"control_validity={d['pass_control_validity']} "
          f"(cat {d['n_categories_intact']}->{d['n_categories_ablated']}, "
          f"csal_diff={d['csal_max_abs_diff_across_arms']})")
    for k in ("SPLIT_CLEAN", "FLOOR", "OFFDAY"):
        print(f"  {k:16s} pass={results[k]['pass']}")
    print("ALL_PASS:", all_pass, "| wrote", out, "|", results["elapsed_s"], "s")


if __name__ == "__main__":
    main()
