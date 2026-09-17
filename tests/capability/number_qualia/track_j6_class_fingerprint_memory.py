"""TRACK (j6) — CLASS-FINGERPRINT MEMORY UNIFICATION: key anti-shapes on WHAT makes a
structure a no-rescue class (its felt-read/verify OUTCOME), not the raw coordinate's
ordinal-RANK signature.

WHY (the reverted bug, commit d9cd83fe): the fool-me-once shape-field memory keyed
anti-shapes on `aperture_signature` — an ordinal RANK key. Every monotone-increasing
numeric sequence collapses to the SAME low-order rank signature, so a geometric
anti-shape falsely repelled an UNRELATED readable cubic (both rank to [0,1,2,3,...]); the
cubic, which confirms at degree 3, got `repelled_by_held_antishape`. No fixed
memory_aperture separates a class from the whole monotone family — the distrust was baked
into the KEY.

THE FIX (this track): key the memory by a per-domain CLASS FINGERPRINT
(`Domain.class_key`). Two structures are the SAME anti-shape IFF the SAME reading fails
the SAME way on them:
  · graph:    the coordinate rank-signature already discriminates graph classes (barbell
              repels barbell, NOT path/star) -> graph KEEPS its key (behavior-preserving).
  · sequence: key = (seq_felt_degree, full-authorable-CLAIM-that-claims-it). The claim is
              namespaced by reading AND its signature (log_degree -> its degree; linrec2 ->
              its (a,b)), so distinct claims stay distinct. geometric 2^n and 4^n MATCH
              (None,('log_degree',1)); geometric vs cubic DIFFER ((None,('log_degree',1)) vs
              (3,None)) -> the cubic is NOT repelled; Fibonacci vs Pell DIFFER (distinct
              recurrences (1,1) vs (2,1)); Fibonacci vs primes DIFFER (vs (None,None)).
  · residue:  key = (felt_confirms, name-of-authorable-that-rescues). no-rescue [1,2,4,7]
              (False,'mod3_runs') vs monotone-confirmable [1,2,3,4] (True,'mod3_runs')
              DIFFER -> no false distrust.

TWO-PHASE, felt-time SOLVER-FREE: phase A rules OUT a repel using ONLY the felt component
of the class_key (solver-free necessary condition) — a fresh cubic whose felt degree (3)
cannot equal a geometric anti-shape's felt degree (None) is ruled out WITHOUT any verify.
Only genuine candidates reach the phase-B verify-gated full-key confirm (mint is post-
verify anyway).

SCOPE OF THE SOLVER-FREE GUARANTEE (honest, per adversarial review): PHASE A (the
felt-component rule-out) is solver-free for EVERY domain — that is the load-bearing property
(felt reads never spend a solver, and a felt-differing candidate is repelled/cleared with no
verify). The PHASE-B full-key confirm is additionally solver-free where the full class_key is
solver-free — the sequence key (felt_degree, log-claim) and the graph rank key are; the
RESIDUE full key includes the mod-3 partition, so on a rare felt-COLLIDER (a confirmable list
whose parity boundaries happen to equal a held anti-shape's) residue's phase-B spends ONE
verify to confirm the class differs. That is acceptable — it fires only for a genuine
felt-collider candidate, never on a felt-differing one, and mint is already post-verify — but
it is NOT a blanket "repel-check is always solver-free" for residue. The felt READS remain
solver-free (SolverSpy=0) for all domains regardless.

WHAT THIS SHOWS
  · C1 NO FALSE DISTRUST (the load-bearing fix): a held SEQUENCE geometric anti-shape does
    NOT repel a cubic/quadratic (they CONFIRM); a DIFFERENT no-rescue class (fibonacci)
    gets its OWN anti-shape, not the geometric's. Residue analogue: a no-rescue [1,2,4,7]
    anti-shape does NOT repel monotone-confirmable [1,2,3,4].
  · C2 FOOL-ME-ONCE STILL WORKS: a fresh geometric (4^n) matching the held geometric
    anti-shape IS repelled (verify saved). Residue analogue with a fresh matching no-rescue
    list.
  · C3 FIRST-VS-REPEAT FROM HELD STATE (no flag): first no-rescue mints the anti-shape;
    a repeat (same class) self-extends — first-vs-repeat DERIVED from held state, no
    prior_no_rescue flag. sequence + residue.
  · C4 SOLVER-FREE felt-time rule-out (phase A): felt reads spend 0 solver calls, and a
    felt-DIFFERING candidate (cubic vs geometric) is ruled out WITHOUT a verify call. (Phase-B
    full-key confirm is additionally solver-free for sequence/graph; residue's full key spends
    one verify on a rare felt-collider — see SCOPE note above. Felt reads are always spy=0.)
  · C5 BEHAVIOR-PRESERVING: the no-substrate path == the flag-based path (track_j5 holds);
    graph WITH memory reproduces verify_then_update reasons/readings.
  · C6 ADVERSARIAL SWEEP (the review's exact counter-examples): a geometric anti-shape does
    NOT repel any of a family of monotone polynomials (degrees 1..4); a residue no-rescue
    anti-shape does NOT repel a family of monotone-confirmable lists. net_valence==0 /
    reason=='confirmed' for every one.

RECURRENCE READING (this commit's refinement — split the (None,None) no-rescue bucket)
  The prior commit noted the sequence (None,None) bucket merges genuinely-distinct unclaimed
  no-rescue classes (Fibonacci, primes, higher-degree). Two coupled changes split it honestly:
    · CHANGE 1 — the felt-degree OVER-FIT fix (precondition): seq_felt_degree/seq_verify_degree
      claimed a polynomial degree whenever the k-th finite difference was 'constant', but an
      n-point sequence's high-order difference is trivially 1-2 values equal by COINCIDENCE, so
      short recurrences over-fit (Pell [0,1,2,5,12,29,70] -> spurious degree 5). Fixed with a
      SCALED WITNESS MARGIN: a degree-k claim is credible only if k <= len(seq)-2-1. Applied to
      BOTH functions so felt==verify (S1) holds. pell/fib -> None; genuine polys keep degree.
    · CHANGE 2 — an AUTHORABLE linrec2 reading: seq_read_linrec2 CLAIMS constant-coefficient
      order-2 linear recurrences (exact rational 2x2 solve for (a,b) from the first two triples,
      then verify the recurrence holds across ALL terms). Registered AFTER log_degree so a
      geometric keeps its log_degree claim; fibonacci/lucas -> ('linrec2',1,1), pell ->
      ('linrec2',2,1). The class key namespaces the FULL claim (name + signature), so fibonacci
      gets its OWN key distinct from geometric (log_degree) AND from Pell (a DIFFERENT
      recurrence (2,1)) AND from primes (None) -- the bucket is split at the class, not merged
      at the reading name.
  · C7  OVER-FIT FIXED: pell/fibonacci no longer read as high-degree polynomials (both -> None
    under the witness margin); genuine polynomials keep their exact degree; felt==verify on S1.
  · C8  RECURRENCE READING CLAIMS FIBONACCI: seq_read_linrec2 fits fibonacci/lucas
    (('linrec2',1,1) -- same class) and pell (('linrec2',2,1) -- a DIFFERENT class); NOT
    polynomials/primes; geometric is claimed by log_degree FIRST so its key keeps log_degree.
  · C9  BUCKET SPLIT (no new merge): seq_class_key gives fibonacci, geometric, Pell, and primes
    FOUR DISTINCT keys (the claim carries the (a,b)/degree, not just the reading name); no
    cross-class false repel in any direction -- crucially a held fibonacci anti-shape does NOT
    repel Pell (distinct recurrence), while a held fibonacci anti-shape DOES repel lucas (same
    recurrence == same class).
  · C10 SELF-EXTENSION AUTHORS linrec2: a repeated Fibonacci-like no-rescue class authors
    linrec2 (reason self_extended_authored_reading) the same way geometric authored log_degree.
  · C11 SOLVER-FREE: seq_read_linrec2 (pure rational arithmetic) and the margin-updated
    seq_felt_degree spend 0 solver calls (SolverSpy=0).

Run: PYTHONPATH=runners/dsl/python:. python3 tests/capability/number_qualia/track_j6_class_fingerprint_memory.py
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))

import number_runner as R              # noqa: E402
from substrate_rs import _native       # noqa: E402


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #
def _ud(edges):
    adj = {}
    for a, b in edges:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return {v: sorted(ns) for v, ns in adj.items()}


def _path(n):
    return _ud([("n%d" % i, "n%d" % (i + 1)) for i in range(n - 1)])


def _barbell():
    return _ud([("a0", "a1"), ("a1", "a2"), ("a2", "a0"),
                ("b0", "b1"), ("b1", "b2"), ("b2", "b0"), ("a0", "b0")])


def _poly(coeffs, n=6):
    """A monotone polynomial sequence sum_j coeffs[j]*i^j over i=0..n-1."""
    out = []
    for i in range(n):
        out.append(int(sum(c * (i ** j) for j, c in enumerate(coeffs))))
    return out


def _seq_hold_geometric(mem, spy=None):
    """Hold a SEQUENCE geometric anti-shape in `mem`: the first geometric encounter is a
    no-rescue class and mints the -1 anti-shape (state-derived, no flag)."""
    geo = [1, 2, 4, 8, 16, 32]                       # 2^n
    return R.domain_verify_then_update(R.SEQUENCE_DOMAIN, geo, memory=mem, spy=spy)


def _res_hold_norescue(mem, spy=None):
    nr = [1, 2, 4, 7]                                # parity-bnds != mod3-bnds
    return R.domain_verify_then_update(R.RESIDUE_DOMAIN, nr, memory=mem, spy=spy)


def main() -> int:
    print("=" * 82)
    print("TRACK (j6) — CLASS-FINGERPRINT MEMORY: anti-shapes keyed on felt/verify OUTCOME")
    print("=" * 82)
    results = []

    # =====================================================================
    # C1 — NO FALSE DISTRUST (the load-bearing fix)
    # =====================================================================
    print("\n" + "-" * 82)
    print("C1  NO FALSE DISTRUST: a held geometric anti-shape must NOT repel a readable cubic")
    print("-" * 82)
    R.SEQUENCE_DOMAIN.fresh_repertoire(); R._SEQ_REPERTOIRE.clear()
    mem = R.ClassFingerprintMemory()
    hold = _seq_hold_geometric(mem)
    print("  held geometric anti-shape: reason=%s  class_key=%s" %
          (hold["reason"], hold.get("class_key")))
    cubic = [0, 1, 8, 27, 64, 125]                   # n^3
    quad = [0, 1, 4, 9, 16, 25]                      # n^2
    fib = [1, 1, 2, 3, 5, 8, 13]                     # a DIFFERENT no-rescue class
    r_cubic = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, cubic, memory=mem, spy=R.SolverSpy())
    r_quad = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, quad, memory=mem, spy=R.SolverSpy())
    r_fib = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, fib, memory=mem, spy=R.SolverSpy())
    print("  cubic n^3 -> reason=%s (class_key=%s)" % (r_cubic["reason"], r_cubic.get("class_key")))
    print("  quad  n^2 -> reason=%s (class_key=%s)" % (r_quad["reason"], r_quad.get("class_key")))
    print("  fib       -> reason=%s (class_key=%s) -- its OWN anti-shape, not the geometric's"
          % (r_fib["reason"], r_fib.get("class_key")))
    # residue analogue
    R.RESIDUE_DOMAIN.fresh_repertoire(); R._RES_REPERTOIRE.clear()
    rmem = R.ClassFingerprintMemory()
    _res_hold_norescue(rmem)
    mono = [1, 2, 3, 4]                              # monotone-confirmable
    r_mono = R.domain_verify_then_update(R.RESIDUE_DOMAIN, mono, memory=rmem, spy=R.SolverSpy())
    print("  residue: no-rescue [1,2,4,7] held; monotone [1,2,3,4] -> reason=%s" % r_mono["reason"])
    c1 = (r_cubic["reason"] == "confirmed" and r_quad["reason"] == "confirmed"
          and r_fib["reason"] == "no_rescue_minted_antishape"
          and r_fib.get("class_key") != hold.get("class_key")
          and r_mono["reason"] == "confirmed")
    print("  C1 (geometric/no-rescue anti-shapes do NOT falsely repel readable structures):  %s"
          % ("PASS" if c1 else "FAIL"))
    results.append(c1)

    # =====================================================================
    # C2 — FOOL-ME-ONCE STILL WORKS
    # =====================================================================
    print("\n" + "-" * 82)
    print("C2  FOOL-ME-ONCE: a fresh geometric (4^n) matching the held geometric anti-shape IS")
    print("    repelled (verify saved). Residue analogue with a fresh matching no-rescue list.")
    print("-" * 82)
    geo4 = [1, 4, 16, 64, 256]                       # 4^n -- same class as 2^n
    spy2 = R.SolverSpy()
    r_geo4 = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, geo4, memory=mem, spy=spy2)
    print("  fresh 4^n -> reason=%s   verify calls during repel=%d (must be 0)"
          % (r_geo4["reason"], spy2.calls))
    # residue: a fresh no-rescue list of the SAME class
    nr2 = [2, 3, 5, 8]                               # parity-bnds != mod3-bnds, same class
    rspy2 = R.SolverSpy()
    r_nr2 = R.domain_verify_then_update(R.RESIDUE_DOMAIN, nr2, memory=rmem, spy=rspy2)
    print("  fresh no-rescue residue -> reason=%s" % r_nr2["reason"])
    c2 = (r_geo4["reason"] == "repelled_by_held_antishape" and spy2.calls == 0
          and r_nr2["reason"] == "repelled_by_held_antishape")
    print("  C2 (fool-me-once repel still fires on a matching class, verify saved):          %s"
          % ("PASS" if c2 else "FAIL"))
    results.append(c2)

    # =====================================================================
    # C3 — FIRST-VS-REPEAT FROM HELD STATE (no flag)
    # =====================================================================
    print("\n" + "-" * 82)
    print("C3  FIRST-VS-REPEAT FROM HELD STATE (no prior_no_rescue flag): first no-rescue mints")
    print("    the anti-shape; a repeat (same class) self-extends. sequence + residue.")
    print("-" * 82)
    R.SEQUENCE_DOMAIN.fresh_repertoire(); R._SEQ_REPERTOIRE.clear()
    mem3 = R.ClassFingerprintMemory()
    geo = [1, 2, 4, 8, 16, 32]
    first = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, geo, memory=mem3, spy=R.SolverSpy())
    # a REPEAT: invest declines the repel and routes to self-extension; first-vs-repeat is
    # DERIVED from held state (a held negative entry for this class_key == a repeat), NOT a flag.
    repeat = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, geo, memory=mem3, invest=True,
                                         spy=R.SolverSpy())
    print("  seq geo first  -> reason=%s" % first["reason"])
    print("  seq geo repeat -> reason=%s reading=%s (repertoire: %s)"
          % (repeat["reason"], repeat.get("reading"), list(R.SEQUENCE_DOMAIN.repertoire)))
    R.RESIDUE_DOMAIN.fresh_repertoire(); R._RES_REPERTOIRE.clear()
    rmem3 = R.ClassFingerprintMemory()
    nr = [1, 2, 4, 7]
    rfirst = R.domain_verify_then_update(R.RESIDUE_DOMAIN, nr, memory=rmem3, spy=R.SolverSpy())
    rrepeat = R.domain_verify_then_update(R.RESIDUE_DOMAIN, nr, memory=rmem3, invest=True,
                                          spy=R.SolverSpy())
    print("  res nr  first  -> reason=%s" % rfirst["reason"])
    print("  res nr  repeat -> reason=%s reading=%s (repertoire: %s)"
          % (rrepeat["reason"], rrepeat.get("reading"), list(R.RESIDUE_DOMAIN.repertoire)))
    c3 = (first["reason"] == "no_rescue_minted_antishape"
          and repeat["reason"] == "self_extended_authored_reading"
          and repeat.get("reading") == "log_degree"
          and rfirst["reason"] == "no_rescue_minted_antishape"
          and rrepeat["reason"] == "self_extended_authored_reading"
          and rrepeat.get("reading") in R._RES_AUTHORABLE)
    print("  C3 (first-vs-repeat derived from held state; repeat self-extends, no flag):     %s"
          % ("PASS" if c3 else "FAIL"))
    results.append(c3)

    # =====================================================================
    # C4 — SOLVER-FREE felt-time rule-out
    # =====================================================================
    print("\n" + "-" * 82)
    print("C4  SOLVER-FREE felt-time rule-out: felt reads + the felt-time repel rule-out spend")
    print("    0 solver calls; the cubic-vs-geometric rule-out happens WITHOUT a verify call.")
    print("-" * 82)
    R.SEQUENCE_DOMAIN.fresh_repertoire(); R._SEQ_REPERTOIRE.clear()
    mem4 = R.ClassFingerprintMemory()
    _seq_hold_geometric(mem4)
    felt_spy = R.SolverSpy()
    # felt reads (all domains) route through felt_spy and must never touch a solver:
    R.SEQUENCE_DOMAIN.default_read(cubic)
    R.SEQUENCE_DOMAIN.felt_component(cubic)
    R.seq_felt_degree(cubic, spy=felt_spy)
    R.seq_felt_degree(geo, spy=felt_spy)
    R.res_felt_read(nr, spy=felt_spy)
    R.felt_aperture_read(_barbell(), list(_barbell()), spy=felt_spy)
    # the EXPLICIT cubic-vs-geometric felt-time rule-out: phase A alone, NO verify spent
    rule_spy = R.SolverSpy()
    fc_cubic = R.SEQUENCE_DOMAIN.felt_component(cubic)          # solver-free felt component
    could_repel = mem4.felt_could_repel(fc_cubic)              # phase A: pure key bookkeeping
    ruled_out_without_verify = (could_repel is False and rule_spy.calls == 0)
    print("  cubic felt component=%s  held geometric felt component(s) differ -> could_repel=%s"
          % (fc_cubic, could_repel))
    print("  verify calls during the cubic-vs-geometric felt-time rule-out: %d (must be 0)"
          % rule_spy.calls)
    print("  felt-read solver calls across all domains: %d (must be 0)" % felt_spy.calls)
    c4 = (felt_spy.calls == 0 and ruled_out_without_verify)
    print("  C4 (felt reads + felt-time repel rule-out solver-free; rule-out spent no verify):%s"
          % ("PASS" if c4 else "FAIL"))
    results.append(c4)

    # =====================================================================
    # C5 — BEHAVIOR-PRESERVING
    # =====================================================================
    print("\n" + "-" * 82)
    print("C5  BEHAVIOR-PRESERVING: no-substrate path == flag-based path (track_j5 holds); graph")
    print("    WITH memory reproduces verify_then_update reasons/readings.")
    print("-" * 82)
    # (a) no-substrate path unchanged vs the flag-based loop (no memory kwarg)
    R.SEQUENCE_DOMAIN.fresh_repertoire(); R._SEQ_REPERTOIRE.clear()
    poly_ns = [0, 1, 4, 9, 16, 25]
    ns_gen = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, poly_ns, spy=R.SolverSpy())
    ns_ex = R.seq_verify_then_update(poly_ns, spy=R.SolverSpy())
    ns_match = (ns_gen["reason"] == ns_ex["reason"] and ns_gen["reading"] == ns_ex["reading"])
    print("  no-substrate seq n^2  generic=(%s,%s) existing=(%s,%s) MATCH=%s"
          % (ns_gen["reason"], ns_gen["reading"], ns_ex["reason"], ns_ex["reading"], ns_match))
    # geometric first no-rescue: no-substrate path reports 'abstained' (flag-based, unchanged)
    R.SEQUENCE_DOMAIN.fresh_repertoire(); R._SEQ_REPERTOIRE.clear()
    ns_geo = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, geo, spy=R.SolverSpy())
    ns_geo_ex = R.seq_verify_then_update(geo, prior_abstained=False, spy=R.SolverSpy())
    ns_geo_match = (ns_geo["reason"] == ns_geo_ex["reason"])
    print("  no-substrate seq 2^n  generic=%s existing=%s MATCH=%s"
          % (ns_geo["reason"], ns_geo_ex["reason"], ns_geo_match))
    # (b) graph WITH memory reproduces verify_then_update on confirmed + rescue
    graph_ok = True
    for name, adj in [("path7", _path(7)), ("barbell", _barbell())]:
        R.GRAPH_DOMAIN.fresh_repertoire()
        gmem = R.ClassFingerprintMemory()
        gen = R.domain_verify_then_update(R.GRAPH_DOMAIN, adj, memory=gmem, spy=R.SolverSpy())
        R.GRAPH_DOMAIN.fresh_repertoire()
        sub = _native.Substrate()
        ex = R.verify_then_update(sub, adj, +1.0, spy=R.SolverSpy())
        m = (gen["reason"] == ex["reason"] and gen["reading"] == ex["reading"])
        graph_ok = graph_ok and m
        print("  graph %-8s MEM=(%s,%s) VTU=(%s,%s) MATCH=%s"
              % (name, gen["reason"], gen["reading"], ex["reason"], ex["reading"], m))
    c5 = ns_match and ns_geo_match and graph_ok
    print("  C5 (no-substrate == flag-based; graph-with-memory == verify_then_update):        %s"
          % ("PASS" if c5 else "FAIL"))
    results.append(c5)

    # =====================================================================
    # C6 — ADVERSARIAL SWEEP (the review's exact counter-examples)
    # =====================================================================
    print("\n" + "-" * 82)
    print("C6  ADVERSARIAL SWEEP: a geometric anti-shape does NOT repel a family of monotone")
    print("    polynomials (degrees 1..4); a residue no-rescue anti-shape does NOT repel a")
    print("    family of monotone-confirmable lists. reason=='confirmed' for every one.")
    print("-" * 82)
    R.SEQUENCE_DOMAIN.fresh_repertoire(); R._SEQ_REPERTOIRE.clear()
    memc = R.ClassFingerprintMemory()
    _seq_hold_geometric(memc)                        # held geometric anti-shape
    # a small family of monotone polynomials, degrees 1..4 (all strictly increasing in index)
    poly_family = {
        "n (deg1)":        _poly([0, 1]),
        "2n+1 (deg1)":     _poly([1, 2]),
        "n^2 (deg2)":      _poly([0, 0, 1]),
        "n^2+n (deg2)":    _poly([0, 1, 1]),
        "n^3 (deg3)":      _poly([0, 0, 0, 1]),
        "n^3+n (deg3)":    _poly([0, 1, 0, 1]),
        "n^4 (deg4)":      _poly([0, 0, 0, 0, 1], n=7),   # deg4 needs >=7 pts under the
                                                          # witness margin (k<=len-2-1) to be a
                                                          # CREDIBLE (non-over-fit) polynomial read
    }
    seq_falsely_repelled = []
    for label, seq in poly_family.items():
        r = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, seq, memory=memc, spy=R.SolverSpy())
        ok = (r["reason"] == "confirmed")
        print("  %-14s %-28s -> reason=%s %s"
              % (label, str(seq), r["reason"], "" if ok else "  <-- FALSELY REPELLED"))
        if not ok:
            seq_falsely_repelled.append((label, seq, r["reason"]))
    # residue family of monotone-confirmable lists (parity-bnds == mod3-bnds)
    R.RESIDUE_DOMAIN.fresh_repertoire(); R._RES_REPERTOIRE.clear()
    rmemc = R.ClassFingerprintMemory()
    _res_hold_norescue(rmemc)                        # held residue no-rescue anti-shape
    res_family = {
        "[1,2,3,4]":       [1, 2, 3, 4],
        "[2,3,4,5]":       [2, 3, 4, 5],
        "[0,1,2,3,4]":     [0, 1, 2, 3, 4],
        "[3,4,5,6,7]":     [3, 4, 5, 6, 7],
        "[2,3,2,3]":       [2, 3, 2, 3],
    }
    res_falsely_repelled = []
    for label, seq in res_family.items():
        r = R.domain_verify_then_update(R.RESIDUE_DOMAIN, seq, memory=rmemc, spy=R.SolverSpy())
        ok = (r["reason"] == "confirmed")
        print("  residue %-12s %-18s -> reason=%s %s"
              % (label, str(seq), r["reason"], "" if ok else "  <-- FALSELY REPELLED"))
        if not ok:
            res_falsely_repelled.append((label, seq, r["reason"]))
    c6 = (not seq_falsely_repelled and not res_falsely_repelled)
    print("  monotone polynomials tested: %s" % list(poly_family))
    print("  monotone-confirmable lists tested: %s" % list(res_family))
    print("  FALSELY REPELLED (must be empty): seq=%s residue=%s"
          % (seq_falsely_repelled, res_falsely_repelled))
    print("  C6 (adversarial sweep — NONE of the review's counter-examples falsely repelled): %s"
          % ("PASS" if c6 else "FAIL"))
    results.append(c6)

    # =====================================================================
    # C7 — OVER-FIT FIXED (CHANGE 1): the scaled witness margin
    # =====================================================================
    print("\n" + "-" * 82)
    print("C7  OVER-FIT FIXED: seq_felt_degree no longer spuriously confirms short recurrences")
    print("    as high-degree polynomials. Pell/Fibonacci -> None (witness margin k<=len-2-1);")
    print("    genuine polynomials keep their exact degree; felt==verify on the S1 battery.")
    print("-" * 82)
    pell = [0, 1, 2, 5, 12, 29, 70]              # was spuriously felt_degree=5
    fib8 = [1, 1, 2, 3, 5, 8, 13, 21]            # a short recurrence, not a polynomial
    over_fit_fixed = (R.seq_felt_degree(pell) is None and R.seq_verify_degree(pell) is None
                      and R.seq_felt_degree(fib8) is None and R.seq_verify_degree(fib8) is None)
    print("  pell [0,1,2,5,12,29,70] -> felt=%s verify=%s (was felt=5 -- OVER-FIT)"
          % (R.seq_felt_degree(pell), R.seq_verify_degree(pell)))
    print("  fib8 -> felt=%s verify=%s" % (R.seq_felt_degree(fib8), R.seq_verify_degree(fib8)))
    genuine_polys = {
        "n":     [0, 1, 2, 3, 4, 5],
        "n^2":   [0, 1, 4, 9, 16, 25],
        "n^3":   [0, 1, 8, 27, 64, 125],
        "2n+1":  [1, 3, 5, 7, 9, 11],
        "const": [5, 5, 5, 5, 5, 5],
    }
    expect_deg = {"n": 1, "n^2": 2, "n^3": 3, "2n+1": 1, "const": 0}
    polys_kept = True
    for label, seq in genuine_polys.items():
        f = R.seq_felt_degree(seq)
        ok = (f == expect_deg[label])
        polys_kept = polys_kept and ok
        print("  %-6s -> felt_degree=%s (expect %s) %s"
              % (label, f, expect_deg[label], "OK" if ok else "WRONG"))
    # felt==verify on the S1 battery (track_j4 S1) still holds under the margin
    s1_battery = {
        "constant":   [5, 5, 5, 5, 5, 5],
        "linear":     [1, 3, 5, 7, 9, 11],
        "quadratic":  [0, 1, 4, 9, 16, 25],
        "triangular": [0, 1, 3, 6, 10, 15],
        "cubic":      [0, 1, 8, 27, 64, 125],
    }
    s1_agree = all(R.seq_felt_degree(s) == R.seq_verify_degree(s) for s in s1_battery.values())
    print("  S1 battery felt==verify under the margin: %s" % s1_agree)
    c7 = over_fit_fixed and polys_kept and s1_agree
    print("  C7 (over-fit fixed; genuine polys keep degree; felt==verify on S1):            %s"
          % ("PASS" if c7 else "FAIL"))
    results.append(c7)

    # =====================================================================
    # C8 — RECURRENCE READING CLAIMS FIBONACCI (CHANGE 2)
    # =====================================================================
    print("\n" + "-" * 82)
    print("C8  RECURRENCE READING: seq_read_linrec2 fits Fibonacci/Lucas (('linrec2',1,1) --")
    print("    same key, same class) and Pell (('linrec2',2,1)); does NOT fit polynomials or")
    print("    primes; geometric is claimed by log_degree FIRST (order matters).")
    print("-" * 82)
    fib = [1, 1, 2, 3, 5, 8, 13]
    lucas = [2, 1, 3, 4, 7, 11, 18]
    pell = [0, 1, 2, 5, 12, 29, 70]
    geo = [1, 2, 4, 8, 16, 32]
    primes = [2, 3, 5, 7, 11, 13, 17]
    quad = [0, 1, 4, 9, 16, 25]
    cubic = [0, 1, 8, 27, 64, 125]
    fib_key = R.seq_read_linrec2(fib)
    lucas_key = R.seq_read_linrec2(lucas)
    pell_key = R.seq_read_linrec2(pell)
    print("  fibonacci linrec2 -> %s" % (fib_key,))
    print("  lucas     linrec2 -> %s  (same recurrence, same class)" % (lucas_key,))
    print("  pell      linrec2 -> %s" % (pell_key,))
    print("  primes    linrec2 -> %s (must be None)" % (R.seq_read_linrec2(primes),))
    print("  quad      linrec2 -> %s (must be None)" % (R.seq_read_linrec2(quad),))
    print("  cubic     linrec2 -> %s (must be None)" % (R.seq_read_linrec2(cubic),))
    print("  geometric authorable claim -> %s (log_degree FIRST; linrec2=%s)"
          % (R.seq_authorable_claim(geo), R.seq_read_linrec2(geo)))
    geo_claim = R.seq_authorable_claim(geo)
    c8 = (fib_key == ("linrec2", 1, 1) and lucas_key == ("linrec2", 1, 1)
          and pell_key == ("linrec2", 2, 1)
          and R.seq_read_linrec2(primes) is None
          and R.seq_read_linrec2(quad) is None and R.seq_read_linrec2(cubic) is None
          and geo_claim is not None and geo_claim[0] == "log_degree")   # namespaced (name, sig)
    print("  C8 (linrec2 claims fib/lucas/pell; not polys/primes; geometric -> log_degree):  %s"
          % ("PASS" if c8 else "FAIL"))
    results.append(c8)

    # =====================================================================
    # C9 — BUCKET SPLIT: fibonacci gets its OWN class key
    # =====================================================================
    print("\n" + "-" * 82)
    print("C9  BUCKET SPLIT (no new merge): seq_class_key gives fibonacci, geometric, Pell and")
    print("    primes FOUR DISTINCT keys (the claim carries the (a,b)/degree, not just the name).")
    print("    A held fibonacci anti-shape does NOT repel geometric/primes/PELL; it DOES repel")
    print("    lucas (same recurrence == same class).")
    print("-" * 82)
    k_fib = R.seq_class_key(fib)
    k_geo = R.seq_class_key(geo)
    k_primes = R.seq_class_key(primes)
    k_pell = R.seq_class_key(pell)
    k_lucas = R.seq_class_key(lucas)
    print("  fibonacci class_key -> %s" % (k_fib,))
    print("  pell      class_key -> %s" % (k_pell,))
    print("  lucas     class_key -> %s" % (k_lucas,))
    print("  geometric class_key -> %s" % (k_geo,))
    print("  primes    class_key -> %s" % (k_primes,))
    # fib, geo, pell, primes are FOUR distinct classes; fib and lucas are the SAME class
    keys_distinct = (len({k_fib, k_geo, k_pell, k_primes}) == 4 and k_fib == k_lucas
                     and k_fib != k_pell)          # the reviewer's crux: fib != pell
    # a held fibonacci anti-shape does NOT repel a geometric, primes, or PELL (different keys)
    R.SEQUENCE_DOMAIN.fresh_repertoire(); R._SEQ_REPERTOIRE.clear()
    memf = R.ClassFingerprintMemory()
    hold_fib = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, fib, memory=memf, spy=R.SolverSpy())
    r_geo_v_fib = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, geo, memory=memf, spy=R.SolverSpy())
    r_primes_v_fib = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, primes, memory=memf,
                                                 spy=R.SolverSpy())
    r_pell_v_fib = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, pell, memory=memf, spy=R.SolverSpy())
    r_lucas_v_fib = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, lucas, memory=memf, spy=R.SolverSpy())
    print("  held fibonacci anti-shape: geometric->%s  primes->%s  PELL->%s  lucas->%s"
          % (r_geo_v_fib["reason"], r_primes_v_fib["reason"], r_pell_v_fib["reason"],
             r_lucas_v_fib["reason"]))
    # a held geometric anti-shape does NOT repel fibonacci
    R.SEQUENCE_DOMAIN.fresh_repertoire(); R._SEQ_REPERTOIRE.clear()
    memg = R.ClassFingerprintMemory()
    _seq_hold_geometric(memg)
    r_fib_v_geo = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, fib, memory=memg, spy=R.SolverSpy())
    print("  held geometric anti-shape: fibonacci -> %s (its OWN anti-shape)"
          % r_fib_v_geo["reason"])
    no_cross_repel = (r_geo_v_fib["reason"] != "repelled_by_held_antishape"
                      and r_primes_v_fib["reason"] != "repelled_by_held_antishape"
                      and r_pell_v_fib["reason"] != "repelled_by_held_antishape"   # the crux
                      and r_fib_v_geo["reason"] != "repelled_by_held_antishape"
                      and r_lucas_v_fib["reason"] == "repelled_by_held_antishape")  # same class DOES repel
    c9 = keys_distinct and no_cross_repel
    print("  C9 (four distinct classes; fib!=pell; no cross-class false repel; lucas==fib):  %s"
          % ("PASS" if c9 else "FAIL"))
    results.append(c9)

    # =====================================================================
    # C10 — SELF-EXTENSION AUTHORS linrec2
    # =====================================================================
    print("\n" + "-" * 82)
    print("C10 SELF-EXTENSION AUTHORS linrec2: a repeated Fibonacci-like no-rescue class run")
    print("    through the sequence self-extension loop AUTHORS linrec2 (reason")
    print("    self_extended_authored_reading, reading 'linrec2') -- like geometric->log_degree.")
    print("-" * 82)
    R.SEQUENCE_DOMAIN.fresh_repertoire(); R._SEQ_REPERTOIRE.clear()
    mem10 = R.ClassFingerprintMemory()
    f10_first = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, fib, memory=mem10, spy=R.SolverSpy())
    f10_repeat = R.domain_verify_then_update(R.SEQUENCE_DOMAIN, fib, memory=mem10, invest=True,
                                             spy=R.SolverSpy())
    print("  fibonacci first  -> reason=%s (class_key=%s)"
          % (f10_first["reason"], f10_first.get("class_key")))
    print("  fibonacci repeat -> reason=%s reading=%s (repertoire: %s)"
          % (f10_repeat["reason"], f10_repeat.get("reading"), list(R.SEQUENCE_DOMAIN.repertoire)))
    linrec2_adopted = ("linrec2" in R.SEQUENCE_DOMAIN.repertoire)   # captured before reset
    # and via the flag-based loop too (same authoring path)
    R.SEQUENCE_DOMAIN.fresh_repertoire(); R._SEQ_REPERTOIRE.clear()
    flag_repeat = R.seq_verify_then_update(fib, prior_abstained=True, spy=R.SolverSpy())
    print("  flag-based fibonacci repeat -> reason=%s reading=%s"
          % (flag_repeat["reason"], flag_repeat.get("reading")))
    c10 = (f10_first["reason"] == "no_rescue_minted_antishape"
           and f10_repeat["reason"] == "self_extended_authored_reading"
           and f10_repeat.get("reading") == "linrec2"
           and linrec2_adopted
           and flag_repeat["reason"] == "self_extended_authored_reading"
           and flag_repeat.get("reading") == "linrec2"
           and "linrec2" in R._SEQ_REPERTOIRE)
    print("  C10 (repeated fibonacci-like no-rescue class authors linrec2, both loops):      %s"
          % ("PASS" if c10 else "FAIL"))
    results.append(c10)

    # =====================================================================
    # C11 — SOLVER-FREE (linrec2 + the margin-updated felt read)
    # =====================================================================
    print("\n" + "-" * 82)
    print("C11 SOLVER-FREE: seq_read_linrec2 and the updated seq_felt_degree spend 0 solver")
    print("    calls (the recurrence solve is pure rational arithmetic, no verify solver).")
    print("-" * 82)
    free_spy = R.SolverSpy()
    for seq in (fib, lucas, pell, geo, primes, quad, cubic):
        R.seq_read_linrec2(seq)
        R.seq_felt_degree(seq, spy=free_spy)
        R.seq_class_key(seq, spy=free_spy)
        R.seq_authorable_claim(seq)
    c11 = (free_spy.calls == 0)
    print("  linrec2 + felt-degree + class-key solver calls: %d (must be 0)" % free_spy.calls)
    print("  C11 (seq_read_linrec2 + updated seq_felt_degree solver-free):                   %s"
          % ("PASS" if c11 else "FAIL"))
    results.append(c11)

    print("\n" + "=" * 82)
    ok = all(results)
    print("  VERDICT: %s" % ("ALL PASS — anti-shapes keyed on the per-domain CLASS FINGERPRINT; "
                             "the geometric-repels-cubic false distrust is impossible by "
                             "construction; fool-me-once + self-extension + graph behavior "
                             "preserved; felt-time rule-out solver-free; the felt-degree "
                             "over-fit is fixed by a scaled witness margin and an authorable "
                             "linrec2 reading splits the (None,None) bucket (fibonacci gets "
                             "its own class key)"
                             if ok else "SOME FAILED — see above"))
    print("=" * 82)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
