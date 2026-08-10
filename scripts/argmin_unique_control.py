#!/usr/bin/env python3
"""ARM P — THE POSITIVE CONTROL, IN BOTH DIRECTIONS. Runs BEFORE any Δ.

*A dead reader and a perfect refuser produce byte-identical output.*
`Argmin` already returns `None` on an EMPTY source; a tie-refusal returns
`None` too. So this control must show, in ONE process, on ONE reader:

  P-A  a TIE           -> null, `ties` +1, `empties` +0        (refusal is REAL)
  P-B  a UNIQUE min    -> the SAME node Argmin returns, `ties` +0
                                                          (refusal is SPECIFIC)
  P-C  an EMPTY source -> null, `empties` +1, `ties` +0        (empty != tie)
  P-D  the reader is alive: it reports a NON-null on P-B in the same process.

A reader that returns None universally fails P-B and P-D together.
A mechanism that refuses everything fails P-B.
A mechanism that refuses nothing fails P-A.

Randomised replicate: 200 draws, seeds 110000-110199 (LITERAL elements of the
declared block -- never `base + K`, which is the offset expression that defeats
the static ledger).
"""
import json
import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from domains import engine_provenance  # noqa: E402
engine_provenance.engine_preamble()

import numpy as np  # noqa: E402
import substrate_rs as srs  # noqa: E402
native = srs._native  # noqa: E402

EXPECT_ENGINE = os.environ.get("EXPECT_ENGINE", "")
PROV = engine_provenance.provenance_line()
if EXPECT_ENGINE and EXPECT_ENGINE not in PROV:
    raise SystemExit(f"ENGINE MISMATCH: expected {EXPECT_ENGINE!r} in {PROV!r}")


def build(values):
    """A substrate holding one Cand node per value."""
    s = srs.Substrate()
    for i, v in enumerate(values):
        s.add_node("Cand", {"score": float(v), "idx": i})
    return s


def term(kind):
    """`kind{ c in NodesOfType(Cand) : Attr(c, score) }`."""
    return srs.Term(kind,
                    source=srs.Term("NodesOfType", node_type="Cand"),
                    var_name="c",
                    value=srs.Attr(srs.Var("c"), "score"),
                    default=None)


def run_one(values, kind, mode):
    s = build(values)
    native.argmin_tie_reset()
    native.argmin_tie_enable(mode)
    try:
        out = s.evaluate(term(kind))
    finally:
        native.argmin_tie_enable("off")
    st = native.argmin_tie_stats()
    return out, st


def main():
    rows = []
    load = os.getloadavg()
    print(f"provenance: {PROV}")
    print(f"loadavg at start: {load}")

    # ---- P-A / P-B / P-C, deterministic, on the EXPLICIT ArgminUnique Term ---
    five_identical = [7.0] * 5
    unique_min = [7.0, 7.0, 3.0, 7.0, 7.0]
    empty = []

    checks = {}

    # The BASELINE fact this rung exists because of: plain Argmin on 5 identical.
    base_out, base_st = run_one(five_identical, "Argmin", "count")
    checks["baseline_argmin_on_5_identical_returns_a_winner"] = (
        base_out is not None)
    checks["baseline_argmin_tie_is_SEEN_by_the_counter"] = (
        base_st["ties"] == 1 and base_st["empties"] == 0)

    # P-A: the ArgminUnique Term itself refuses.
    pa_out, pa_st = run_one(five_identical, "ArgminUnique", "count")
    checks["P_A_tie_refused"] = pa_out is None
    checks["P_A_tie_counted_not_empty"] = (
        pa_st["ties"] == 1 and pa_st["empties"] == 0
        and pa_st["refusals"] == 1)

    # P-B: a unique extremum -> the SAME element Argmin returns.
    pb_min, _ = run_one(unique_min, "Argmin", "off")
    pb_uni, pb_st = run_one(unique_min, "ArgminUnique", "count")
    checks["P_B_unique_not_refused"] = pb_uni is not None
    checks["P_B_same_winner_as_Argmin"] = (str(pb_min) == str(pb_uni))
    checks["P_B_no_tie_counted"] = (
        pb_st["ties"] == 0 and pb_st["refusals"] == 0)

    # P-C: an EMPTY source -> null, but counted as EMPTY, not as a tie.
    pc_out, pc_st = run_one(empty, "ArgminUnique", "count")
    checks["P_C_empty_is_null"] = pc_out is None
    checks["P_C_empty_counted_not_tie"] = (
        pc_st["empties"] == 1 and pc_st["ties"] == 0
        and pc_st["refusals"] == 0)

    # P-D: the reader is ALIVE -- it reported a non-null in this same process.
    checks["P_D_reader_alive"] = (pb_uni is not None and base_out is not None)

    # THE DISCRIMINATION THAT MATTERS: P-A and P-C return the SAME bytes.
    checks["P_AC_same_output_different_counters"] = (
        (pa_out is None) and (pc_out is None)
        and (pa_st["ties"], pa_st["empties"]) != (pc_st["ties"], pc_st["empties"]))

    # ---- the coercion instrument, same three cases -------------------------
    co_out, co_st = run_one(five_identical, "Argmin", "refuse_min")
    checks["coerce_refuse_min_refuses_a_tied_Argmin"] = (
        co_out is None and co_st["refusals"] == 1)
    cu_out, cu_st = run_one(unique_min, "Argmin", "refuse_min")
    checks["coerce_refuse_min_passes_a_unique_Argmin"] = (
        cu_out is not None and cu_st["refusals"] == 0)
    cx_out, cx_st = run_one(five_identical, "Argmax", "refuse_min")
    checks["coerce_refuse_min_does_NOT_touch_Argmax"] = (
        cx_out is not None and cx_st["refusals"] == 0 and cx_st["ties"] == 1)
    cy_out, cy_st = run_one(five_identical, "Argmax", "refuse_all")
    checks["coerce_refuse_all_DOES_refuse_Argmax"] = (
        cy_out is None and cy_st["refusals"] == 1)

    # ---- count mode must not change BEHAVIOUR ------------------------------
    off_out, _ = run_one(five_identical, "Argmin", "off")
    cnt_out, _ = run_one(five_identical, "Argmin", "count")
    checks["count_mode_does_not_change_behaviour"] = (
        str(off_out) == str(cnt_out) and off_out is not None)

    # ---- randomised replicate, seeds 110000-110199 (LITERAL) ---------------
    SEEDS = list(range(110000, 110200))
    n_tie_correct = 0
    n_uniq_correct = 0
    for sd in SEEDS:
        rng = np.random.default_rng(sd)
        k = int(rng.integers(2, 8))
        if sd % 2 == 0:
            # a TIE by construction: k copies of one value
            vals = [float(rng.integers(0, 5))] * k
            out, st = run_one(vals, "ArgminUnique", "count")
            if out is None and st["ties"] == 1 and st["empties"] == 0:
                n_tie_correct += 1
        else:
            # a STRICT minimum by construction
            hi = float(rng.integers(5, 20))
            vals = [hi] * k + [hi - 1.0]
            out, st = run_one(vals, "ArgminUnique", "count")
            ref, _ = run_one(vals, "Argmin", "off")
            if out is not None and st["ties"] == 0 and str(out) == str(ref):
                n_uniq_correct += 1
    n_tie = sum(1 for sd in SEEDS if sd % 2 == 0)
    n_uniq = len(SEEDS) - n_tie
    checks["replicate_ties_all_refused"] = (n_tie_correct == n_tie)
    checks["replicate_uniques_all_passed"] = (n_uniq_correct == n_uniq)

    out = {
        "provenance": PROV,
        "loadavg_start": list(load),
        "loadavg_end": list(os.getloadavg()),
        "seeds": [110000, 110199],
        "replicate": {
            "n_tie": n_tie, "n_tie_correct": n_tie_correct,
            "n_unique": n_uniq, "n_unique_correct": n_uniq_correct,
        },
        "checks": checks,
        "all_pass": all(checks.values()),
    }
    print(json.dumps(out, indent=2))
    dest = ROOT / "results" / "argmin_unique_control.json"
    dest.write_text(json.dumps(out, indent=2))
    if not out["all_pass"]:
        failed = [k for k, v in checks.items() if not v]
        raise SystemExit(
            "ABORT (pre-registered): positive control FAILED -> "
            f"{failed}. NO delta is reported.")
    print("\nARM P PASSES IN BOTH DIRECTIONS. Delta measurement is licensed.")


if __name__ == "__main__":
    main()
