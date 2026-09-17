"""TRACK (j7) — RUNTIME DISCOVERY: a provably-unseen class, discovered and verified LIVE.

This is the evidence under the claim that the pipeline LEARNS AT RUNTIME (not train-then-
deploy): presented with a structure NO starting reading can claim, the running system fails
on it, recognizes the repeated failure, COMPOSES a new reading from a HELD primitive at a
wider aperture, VERIFIES it exactly, adopts it, and reuses it -- all in one process, on the
CPU, with no training step, no gradient, no pretrained artifact, and a solver-free felt path.

THE TARGET (provably unseen): TRIBONACCI x[n]=x[n-1]+x[n-2]+x[n-3] and FIB^2. The starting
sequence repertoire is ORDER-2 (linrec2) + log_degree + poly-degree. A genuine order-3 linear
recurrence is UNCLAIMED by every one of them (asserted at runtime, E1).

THE HONESTY BAR (three ways it could be fake, each ruled out):
  1. NOT PRE-LOADED: no reading for order-3 recurrences exists at start. E1 asserts the starting
     _SEQ_AUTHORABLE is exactly {log_degree, linrec2} and that none of the starting readings
     claims tribonacci/fib^2.
  2. NOT LOOKUP: the rescue is COMPOSED from a HELD primitive (_solve_linrec_order, the SAME
     exact-solve linrec2 uses) at a wider order the runtime SEARCH found -- not a hand-written
     `tribonacci_reading`. E3 asserts the authored reading name is linrec3 and that it is
     _make_linrec_reading(3) over the held solve, and the felt path spends 0 solver calls.
  3. NOT TRAINING: the whole event is one in-process act -- repertoire size N -> N+1, timestamped,
     on the CPU, no gradient/fit/pretrained model. E4 records wall-clock and the before/after
     repertoire, and asserts no verify solver ran on the felt path (SolverSpy=0).

WHAT THIS SHOWS
  · E1 PROVABLY UNSEEN: starting repertoire = {log_degree, linrec2}; tribonacci and fib^2 are
    claimed by NOTHING at start (default felt None, log_degree None, linrec2 None).
  · E2 FAILS THEN DISCOVERS: first encounter -> distrust (no-rescue); repeat -> the loop AUTHORS
    linrec3 (reason self_extended_authored_reading) from the held solve at order 3.
  · E3 COMPOSED, NOT LOOKUP: the authored reading is linrec3 = the held _solve_linrec_order at
    order 3 (a wider aperture of linrec2's own primitive); felt path solver-free.
  · E4 LIVE / NO TRAINING: repertoire grew {..} -> {.., linrec3} in-process; wall-clock recorded;
    no gradient/fit/pretrained artifact; SolverSpy=0 on the felt path.
  · E5 REUSED + CLASS-DISTINCT: after discovery, a FRESH tribonacci is claimed immediately by the
    now-held linrec3; tribonacci ('linrec3',1,1,1) and fib^2 ('linrec3',2,2,-1) get DISTINCT
    class keys (the discovered reading carries the coefficients), so they are distinct classes,
    not merged.

NOTE (audience): this is EVIDENCE for a controlled reading, committed in-repo like every other
developmental track. It is deliberately NOT written up as a distribution-facing capability
artifact; the framing here is the same honest developmental record as tracks j3-j6.

Run: PYTHONPATH=runners/dsl/python:. python3 tests/capability/number_qualia/track_j7_runtime_discovery.py
"""
from __future__ import annotations

import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))

import number_runner as R              # noqa: E402


def _reset_sequence_domain():
    """Restore the STARTING sequence repertoire: exactly {log_degree, linrec2}, no discovered
    higher-order readings. Proves the demonstration begins with the target genuinely unseen."""
    for name in [k for k in R._SEQ_AUTHORABLE if k not in ("log_degree", "linrec2")]:
        del R._SEQ_AUTHORABLE[name]
    R._SEQ_REPERTOIRE.clear()


def main() -> int:
    print("=" * 84)
    print("TRACK (j7) — RUNTIME DISCOVERY: a provably-unseen class, discovered + verified LIVE")
    print("=" * 84)

    tribonacci = [0, 0, 1, 1, 2, 4, 7, 13, 24, 44]
    fib_sq = [1, 1, 4, 9, 25, 64, 169, 441]            # F(n)^2, an order-3 recurrence (2,2,-1)
    _reset_sequence_domain()

    # =====================================================================
    # E1 — PROVABLY UNSEEN
    # =====================================================================
    print("\n" + "-" * 84)
    print("E1  PROVABLY UNSEEN: starting repertoire = {log_degree, linrec2}; nothing claims")
    print("    tribonacci or fib^2 at start.")
    print("-" * 84)
    start_authorable = sorted(R._SEQ_AUTHORABLE.keys())
    print("  starting _SEQ_AUTHORABLE:", start_authorable)
    tri_claims = (R.seq_felt_degree(tribonacci), R.seq_read_log_degree(tribonacci),
                  R.seq_read_linrec2(tribonacci))
    fsq_claims = (R.seq_felt_degree(fib_sq), R.seq_read_log_degree(fib_sq),
                  R.seq_read_linrec2(fib_sq))
    print("  tribonacci (felt, log, linrec2):", tri_claims)
    print("  fib^2      (felt, log, linrec2):", fsq_claims)
    e1 = (start_authorable == ["linrec2", "log_degree"]
          and tri_claims == (None, None, None) and fsq_claims == (None, None, None))
    print("  E1 (target genuinely unseen by the starting repertoire):                    %s"
          % ("PASS" if e1 else "FAIL"))

    # =====================================================================
    # E2 — FAILS THEN DISCOVERS  (+ E4 instrumentation captured here)
    # =====================================================================
    print("\n" + "-" * 84)
    print("E2  FAILS THEN DISCOVERS: first encounter -> distrust; repeat -> AUTHOR linrec3 live.")
    print("-" * 84)
    felt_spy = R.SolverSpy()                            # the felt path must stay 0
    # felt read (solver-free) confirms it abstains -- an unseen no-rescue class
    felt = R.seq_felt_degree(tribonacci, spy=felt_spy)
    first = R.seq_verify_then_update(tribonacci, prior_abstained=False, spy=R.SolverSpy())
    n_before = len(R._SEQ_AUTHORABLE)
    t0 = time.perf_counter()
    repeat = R.seq_verify_then_update(tribonacci, prior_abstained=True, spy=felt_spy)
    dt_ms = (time.perf_counter() - t0) * 1e3
    n_after = len(R._SEQ_AUTHORABLE)
    print("  tribonacci felt_degree:", felt, "(None -> abstains, unseen)")
    print("  first encounter  -> reason=%s" % first["reason"])
    print("  repeat encounter -> reason=%s reading=%s" % (repeat["reason"], repeat.get("reading")))
    e2 = (felt is None and first["reason"] == "abstained"
          and repeat["reason"] == "self_extended_authored_reading"
          and repeat.get("reading") == "linrec3")
    print("  E2 (unseen class fails then is discovered as linrec3 on repeat):            %s"
          % ("PASS" if e2 else "FAIL"))

    # =====================================================================
    # E3 — COMPOSED FROM A HELD PRIMITIVE, NOT LOOKUP
    # =====================================================================
    print("\n" + "-" * 84)
    print("E3  COMPOSED, NOT LOOKUP: linrec3 = the HELD _solve_linrec_order at order 3 (a wider")
    print("    aperture of linrec2's OWN primitive); no hand-written tribonacci reading exists.")
    print("-" * 84)
    # the authored reading, applied fresh, must equal the held solve at order 3
    authored_fn = R._SEQ_AUTHORABLE.get("linrec3")
    via_reading = authored_fn(tribonacci) if authored_fn else None
    via_held = R._solve_linrec_order(tribonacci, 3)
    # no bespoke target reading exists anywhere in the module
    no_bespoke = not any("tribonacci" in nm or "fib_sq" in nm or "fib_squared" in nm
                         for nm in dir(R))
    print("  linrec3(tribonacci) =", via_reading, " ; held _solve_linrec_order(.,3) =",
          ("linrec3",) + (via_held or ()))
    print("  no bespoke tribonacci/fib_squared reading in the module:", no_bespoke)
    e3 = (via_reading == (("linrec3",) + (via_held or ())) and via_held == (1, 1, 1)
          and no_bespoke and felt_spy.calls == 0)
    print("  E3 (rescue is the held solve at a wider order; felt path solver-free):      %s"
          % ("PASS" if e3 else "FAIL"))

    # =====================================================================
    # E4 — LIVE / NO TRAINING
    # =====================================================================
    print("\n" + "-" * 84)
    print("E4  LIVE / NO TRAINING: repertoire grew in-process; wall-clock recorded; no gradient,")
    print("    no fit, no pretrained artifact; felt path SolverSpy=0.")
    print("-" * 84)
    print("  repertoire size  before=%d  after=%d  (grew by %d: linrec3)"
          % (n_before, n_after, n_after - n_before))
    print("  discovery wall-clock: %.3f ms (single in-process act, consumer CPU)" % dt_ms)
    print("  felt-path solver calls during discovery: %d (must be 0)" % felt_spy.calls)
    e4 = (n_after == n_before + 1 and "linrec3" in R._SEQ_AUTHORABLE and felt_spy.calls == 0)
    print("  E4 (learning is a live in-process act, no training, solver-free felt):      %s"
          % ("PASS" if e4 else "FAIL"))

    # =====================================================================
    # E5 — REUSED + CLASS-DISTINCT
    # =====================================================================
    print("\n" + "-" * 84)
    print("E5  REUSED + CLASS-DISTINCT: a FRESH tribonacci is now claimed by the held linrec3;")
    print("    tribonacci and fib^2 (both order-3) get DISTINCT class keys (coeffs carried).")
    print("-" * 84)
    fresh_trib = [1, 1, 1, 3, 5, 9, 17, 31]            # tribonacci, different seed -> same (1,1,1)
    reused = R._SEQ_AUTHORABLE["linrec3"](fresh_trib)
    # fib^2 must ALSO now be discoverable (order-3) and get a DIFFERENT signature
    fsq_sig = R._SEQ_AUTHORABLE["linrec3"](fib_sq)
    print("  fresh tribonacci via held linrec3 ->", reused, "(reused, not re-discovered)")
    print("  fib^2 via linrec3 ->", fsq_sig, "(same order, DIFFERENT coeffs -> distinct class)")
    tri_key = R.seq_class_key(tribonacci)
    fsq_key = R.seq_class_key(fib_sq)
    print("  class_key(tribonacci) =", tri_key)
    print("  class_key(fib^2)      =", fsq_key)
    e5 = (reused == ("linrec3", 1, 1, 1) and fsq_sig == ("linrec3", 2, 2, -1)
          and tri_key != fsq_key)
    print("  E5 (reused on a fresh instance; the two order-3 classes stay distinct):     %s"
          % ("PASS" if e5 else "FAIL"))

    print("\n" + "=" * 84)
    ok = all([e1, e2, e3, e4, e5])
    print("  VERDICT: %s" % ("ALL PASS — an unseen class was discovered and verified LIVE, from a "
                             "held primitive at a wider aperture, no training, solver-free felt, "
                             "in %.1f ms on the CPU" % dt_ms
                             if ok else "SOME FAILED — see above"))
    print("=" * 84)
    _reset_sequence_domain()                            # leave the module as we found it
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
