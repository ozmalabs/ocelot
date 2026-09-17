"""TRACK (j4) — CROSS-DOMAIN SELF-EXTENSION: the SAME loop over a NON-graph coordinate.

The arc (commits 56e4468c..949c4e83) built a self-growing thought pipeline over GRAPHS:
felt read at multiple apertures -> commit/abstain -> caught wrong? search a rescuing reading
-> repeated no-rescue? AUTHOR a new reading composed from held primitives -> verify, adopt,
no regression. The honest ceiling: every authorable primitive was graph-structural. Is the
LOOP domain-general, or a graph trick?

This track instantiates the IDENTICAL loop over NUMERIC SEQUENCES (the number-qualia integer
axis) and shows only the PRIMITIVE VOCABULARY changes, not the machinery:

  domain      coordinate            felt read (cheap)              verify (exact)        authored reading (held prims)
  --------    ------------------    ---------------------------    ------------------    ----------------------------
  graph       degree in order       aperture manifold outliers     Tarjan cut-vertices   bridge (cycle_core + bridge edge)
  sequence    values in index       constant finite-diff order     exact differencing    log_degree (log + finite-diff)

The SAME aperture dial (order_n_concepts.nth_order_terms) drives BOTH felt reads. A geometric
sequence (2^n) is the sequence-domain no-rescue class (no constant finite difference); on a
REPEAT the loop authors the 'log_degree' reading from held numeric primitives (a geometric
sequence is degree-1 in log space) and rescues it -- the exact analogue of `bridge` rescuing
the barbell, in a different domain.

WHAT THIS SHOWS
  · S1 SEQUENCE FELT READ: polynomial sequences (constant..cubic) get the correct felt degree
    from the SAME aperture dial, solver-free (spy=0), verify-confirmed.
  · S2 NO-RESCUE CLASS: a geometric sequence's felt read ABSTAINS (no constant finite diff) --
    the sequence-domain analogue of the barbell.
  · S3 CROSS-DOMAIN SELF-EXTENSION: on a REPEAT the loop AUTHORS 'log_degree' from held numeric
    primitives, verify-gated, and rescues the geometric class -- the SAME distrust->author->
    rescue loop as the graph domain, different primitives.
  · S4 NO REGRESSION: the authored log-space reading does NOT mis-read polynomials (it returns
    None on n^2), exactly as the graph `bridge` reading did not regress cycles.
  · S5 LOOP IS THE SAME: the sequence felt read is solver-free (spy=0) and verify is the
    separate exact step -- the same feel-then-verify discipline, one aperture dial for both.

Run: PYTHONPATH=runners/dsl/python:. python3 tests/capability/number_qualia/track_j4_cross_domain_self_extension.py
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))

import number_runner as R          # noqa: E402


def main() -> int:
    print("=" * 82)
    print("TRACK (j4) — CROSS-DOMAIN SELF-EXTENSION: the same loop over numeric sequences")
    print("=" * 82)

    felt_spy = R.SolverSpy()        # ONLY the felt reads use this — must stay 0
    verify_spy = R.SolverSpy()      # verify + authoring legitimately spend this

    # ---- S1: the sequence felt read (same aperture dial) is correct on polynomials ----
    print("\n" + "-" * 82)
    print("S1  SEQUENCE FELT READ — polynomial degree via the SAME order_n aperture dial:")
    print("-" * 82)
    polys = {
        "constant [5]*6":       [5, 5, 5, 5, 5, 5],
        "linear 2n+1":          [1, 3, 5, 7, 9, 11],
        "quadratic n^2":        [0, 1, 4, 9, 16, 25],
        "triangular (fall)":    [0, 1, 3, 6, 10, 15],
        "cubic n^3":            [0, 1, 8, 27, 64, 125],
    }
    s1_ok = True
    for name, seq in polys.items():
        felt = R.seq_felt_degree(seq, spy=felt_spy)     # solver-free
        true = R.seq_verify_degree(seq, spy=verify_spy) # exact verify (separate)
        ok = (felt == true)
        s1_ok = s1_ok and ok
        print("  %-20s felt_degree=%s verify_degree=%s  %s"
              % (name, felt, true, "OK" if ok else "MISMATCH"))
    print("  S1 (felt degree correct on polynomials, from the shared aperture dial): %s"
          % ("PASS" if s1_ok else "FAIL"))

    # ---- S2: the geometric no-rescue class (felt read abstains) ----
    print("\n" + "-" * 82)
    print("S2  NO-RESCUE CLASS — a geometric sequence's felt read ABSTAINS (no constant diff):")
    print("-" * 82)
    geo = [1, 2, 4, 8, 16, 32]
    # felt read (solver-free) directly, to keep the felt_spy accounting clean
    geo_felt = R.seq_felt_degree(geo, spy=felt_spy)
    r_first = R.seq_verify_then_update(geo, prior_abstained=False, spy=verify_spy)
    s2_ok = (geo_felt is None and r_first["reason"] == "abstained")
    print("  geometric 2^n first encounter -> %s (felt_degree=%s)"
          % (r_first["reason"], r_first["felt_degree"]))
    print("  S2 (geometric abstains — the sequence-domain no-rescue class):           %s"
          % ("PASS" if s2_ok else "FAIL"))

    # ---- S3: cross-domain self-extension on a REPEAT ----
    print("\n" + "-" * 82)
    print("S3  CROSS-DOMAIN SELF-EXTENSION — a REPEAT authors 'log_degree' from held numeric")
    print("    primitives (log + finite-diff) and rescues the geometric class:")
    print("-" * 82)
    R._SEQ_REPERTOIRE.clear()       # fresh (nothing authored yet)
    r_repeat = R.seq_verify_then_update(geo, prior_abstained=True, spy=verify_spy)
    s3_ok = (r_repeat["reason"] == "self_extended_authored_reading"
             and r_repeat["reading"] == "log_degree"
             and "log_degree" in R._SEQ_REPERTOIRE)
    print("  geometric 2^n REPEAT -> %s (reading=%s); repertoire now: %s"
          % (r_repeat["reason"], r_repeat["reading"], list(R._SEQ_REPERTOIRE)))
    # a fresh geometric of a different ratio is rescued by the now-held reading
    lk = R.seq_read_log_degree([1, 3, 9, 27, 81])
    print("  fresh geometric 3^n via authored log_degree reading -> degree %s (geometric)" % lk)
    print("  S3 (repeat -> author from held numeric primitives -> rescued):           %s"
          % ("PASS" if s3_ok else "FAIL"))

    # ---- S4: no regression (authored reading does not mis-read polynomials) ----
    print("\n" + "-" * 82)
    print("S4  NO REGRESSION — the authored log-space reading does NOT mis-read polynomials:")
    print("-" * 82)
    poly_lk = R.seq_read_log_degree([1, 4, 9, 16, 25])     # n^2 (shifted +ve)
    s4_ok = (poly_lk is None)
    print("  quadratic n^2 via log_degree -> %s  (must be None: not geometric)" % poly_lk)
    print("  S4 (authored reading is per-class, verify-gated, no regression):         %s"
          % ("PASS" if s4_ok else "FAIL"))

    # ---- S5: the loop is the same (FELT reads solver-free; verify separate) ----
    print("\n" + "-" * 82)
    print("S5  LOOP IS THE SAME — FELT reads solver-free; verify/authoring is the separate step:")
    print("-" * 82)
    s5_ok = (felt_spy.calls == 0 and verify_spy.calls > 0)
    print("  felt-read solver calls: %d (must be 0)   verify/authoring solver calls: %d (>0)"
          % (felt_spy.calls, verify_spy.calls))
    print("  S5 (feel-then-verify preserved cross-domain; one aperture dial for both): %s"
          % ("PASS" if s5_ok else "FAIL"))

    print("\n" + "=" * 82)
    ok = all([s1_ok, s2_ok, s3_ok, s4_ok, s5_ok])
    print("  VERDICT: %s" % ("ALL PASS — the recognise->compose->verify->adopt loop is "
                             "DOMAIN-GENERAL; only the primitive vocabulary changes"
                             if ok else "SOME FAILED — see above"))
    print("=" * 82)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
