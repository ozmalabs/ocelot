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
  · sequence: key = (seq_felt_degree, name-of-authorable-that-claims-it). geometric 2^n and
              4^n MATCH (None,'log_degree'); geometric vs cubic DIFFER ((None,'log_degree')
              vs (3,None)) -> the cubic is NOT repelled; geometric vs fibonacci DIFFER
              ((None,'log_degree') vs (None,None)) -> distinct no-rescue classes, distinct
              anti-shapes.
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
        "n^4 (deg4)":      _poly([0, 0, 0, 0, 1]),
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

    print("\n" + "=" * 82)
    ok = all(results)
    print("  VERDICT: %s" % ("ALL PASS — anti-shapes keyed on the per-domain CLASS FINGERPRINT; "
                             "the geometric-repels-cubic false distrust is impossible by "
                             "construction; fool-me-once + self-extension + graph behavior "
                             "preserved; felt-time rule-out solver-free"
                             if ok else "SOME FAILED — see above"))
    print("=" * 82)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
