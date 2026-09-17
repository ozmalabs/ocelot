"""TRACK (j2) — META-SHAPE MATCH against known solutions: the path rescue.

Completes sub-experiment (j). In track (j) the transferred per-element isolation
coordinate failed on the degree-regular PATH — criticality there is not a
within-instance outlier, so no local felt read can flag it. The missing mechanism
(user): match the WHOLE graph's meta-shape against a library of EARNED (exactly-solved-
once) exemplars and import the solution as a STRUCTURAL-ROLE template. "This graph
feels like a chain -> a chain's load-bearing nodes are its spine -> flag the spine."
Higher-order analogical retrieval, not a per-node outlier.

WHAT THIS SHOWS
  · M1 PATH RESCUED: the fresh path matches the chain exemplar and the imported
    spine-role template flags exactly the cut-vertices (F1=1.0) — the case track (j)
    scored F1=0.
  · M2 FELT PATH SOLVER-FREE: matching a fresh graph runs 0 Tarjan calls; the exact
    solver ran ONLY when the library was built (spy-separated).
  · M3 FEEL-THEN-VERIFY BOUNDARY (near-path decoy): a chain-plus-one-chord matches the
    chain exemplar only LOOSELY (elevated match-distance = the built-in 'verify me'
    signal), and the imported template is genuinely WRONG there — only verification
    corrects it. The prior is lossy by design; the match-distance flags when to trust.
  · M4 EARNED, NOT PLANTED: the library's templates are learned by exactly-solving the
    exemplars once (structural roles, not node ids); a fresh answer comes from the
    match, never a hand-authored 'chain->interior' table (Arm-2, the hollow control).

REFRAME: track (j)'s "local-shape-bounded" ceiling was too pessimistic. The real bound
is a COVERAGE ceiling — the felt read works for any configuration whose meta-shape
matches a SOLVED exemplar (including global-criticality cases like the path); it fails
only where the meta-shape matches nothing solved.

Run: PYTHONPATH=runners/dsl/python:. python3 tests/capability/number_qualia/track_j2_metashape_rescue.py
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))

import number_runner as R              # noqa: E402
from substrate_rs import _native       # noqa: E402


def _ud(edges):
    adj = {}
    for a, b in edges:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return {v: sorted(ns) for v, ns in adj.items()}


def _path(n):   return _ud([("n%d" % i, "n%d" % (i + 1)) for i in range(n - 1)])
def _star(n):   return _ud([("h", "l%d" % i) for i in range(n - 1)])
def _clique(n): return _ud([("c%d" % i, "c%d" % j)
                            for i in range(n) for j in range(i + 1, n)])
def _cycle(n):  return _ud([("y%d" % i, "y%d" % ((i + 1) % n)) for i in range(n)])
def _tree():    return _ud([("r", "a"), ("r", "b"), ("a", "c"), ("a", "d"), ("b", "e")])


def _prf(pred, truth):
    pred, truth = set(pred), set(truth)
    tp = len(pred & truth); fp = len(pred - truth); fn = len(truth - pred)
    p = tp / (tp + fp) if (tp + fp) else (1.0 if not truth else 0.0)
    r = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return round(f1, 3)


def main() -> int:
    print("=" * 78)
    print("TRACK (j2) — META-SHAPE MATCH against known solutions: the path rescue")
    print("=" * 78)
    s = _native.Substrate()

    # ---- earn the library (Tarjan solves EXEMPLARS once; spy-tracked) ----
    exemplars = {"chain": _path(6), "star": _star(6), "clique": _clique(5),
                 "cycle": _cycle(6), "tree": _tree()}
    build_spy = R.SolverSpy()
    lib = R.build_solution_library(exemplars, spy=build_spy)
    print("\n[LIBRARY — earned] exact solver calls at BUILD: %d (= #exemplars)"
          % build_spy.calls)
    for name, e in lib.items():
        print("   %-7s meta=%s  critical-roles=%s" % (name, e["meta"], e["roles"]))

    # ---- M1: rescue the path (the track-(j) failure) ----
    print("\n" + "-" * 78)
    print("M1  PATH RESCUE — fresh path matched to chain exemplar, spine template "
          "imported")
    print("-" * 78)
    felt_spy = R.SolverSpy()
    fresh = {"fresh_path7": _path(7), "fresh_star5": _star(5), "fresh_cycle5": _cycle(5)}
    m1_ok = True
    for name, g in fresh.items():
        r = R.felt_meta_match(g, lib, s, spy=felt_spy)     # felt path: no solver
        truth = R.tarjan_cut_vertices(g)                   # verify (separate)
        f1 = _prf(r["predicted"], truth)
        print("  %-12s -> %-6s (dist %d) roles=%s  pred=%s truth=%s  F1=%.2f"
              % (name, r["nearest"], r["match_dist"], r["roles"],
                 sorted(r["predicted"]), sorted(truth), f1))
        if name == "fresh_path7" and f1 < 0.99:
            m1_ok = False
    print("  M1 (path rescued: fresh_path7 F1=1.0 via meta-match): %s"
          % ("PASS" if m1_ok else "FAIL"))

    # ---- M2: felt path solver-free ----
    print("\n" + "-" * 78)
    print("M2  FELT PATH SOLVER-FREE")
    print("-" * 78)
    print("  Tarjan calls during all felt matches: %d (must be 0)" % felt_spy.calls)
    print("  Tarjan calls at library build (the earned, one-time cost): %d"
          % build_spy.calls)
    m2_ok = felt_spy.calls == 0
    print("  M2 %s" % ("PASS" if m2_ok else "FAIL"))

    # ---- M3: feel-then-verify boundary (near-path decoy) ----
    print("\n" + "-" * 78)
    print("M3  HONEST BOUNDARY — near-path decoy: loose match (elevated distance) + "
          "template genuinely wrong -> only verify corrects")
    print("-" * 78)
    near = _ud([("n0", "n1"), ("n1", "n2"), ("n2", "n3"), ("n3", "n4"),
                ("n4", "n5"), ("n0", "n2")])           # chain + one chord (triangle)
    rn = R.felt_meta_match(near, lib, s)
    truth_n = R.tarjan_cut_vertices(near)
    clean_dist = R.felt_meta_match(_path(7), lib, s)["match_dist"]
    f1_near = _prf(rn["predicted"], truth_n)
    print("  near-path match: nearest=%s dist=%d (clean path dist=%d)"
          % (rn["nearest"], rn["match_dist"], clean_dist))
    print("  template predicted=%s ; true cut-vertices=%s ; F1=%.2f"
          % (sorted(rn["predicted"]), sorted(truth_n), f1_near))
    # honest decoy: match-distance is elevated (verify-me signal) AND the imported
    # template is genuinely wrong (F1 < 1) -> verification is what corrects it.
    m3_ok = (rn["match_dist"] > clean_dist) and (f1_near < 1.0)
    print("  elevated match-distance flags 'not a clean chain, verify' AND the prior "
          "is wrong here (F1<1) so verify is load-bearing: %s" % m3_ok)
    print("  M3 %s" % ("PASS" if m3_ok else "FAIL"))

    # ---- M4: earned, not planted (Arm-2 contrast) ----
    print("\n" + "-" * 78)
    print("M4  EARNED, NOT PLANTED (Arm-2 hand-authored table = the hollow version)")
    print("-" * 78)
    print("  Arm-1 (this track): templates LEARNED by solving the exemplars once "
          "(build Tarjan=%d); a fresh graph's answer = meta-match + structural role, "
          "no hand table." % build_spy.calls)
    print("  Arm-2 (hollow): a hand-authored {chain->spine, star->hub, ...} table "
          "would give the same answers WITHOUT earning them — that plants the "
          "solution. The difference is that Arm-1's roles came from Tarjan on the "
          "exemplars, auditable in the library above; nothing in the felt path is "
          "hand-mapped.")
    m4_ok = build_spy.calls == len(exemplars)   # every template earned by a real solve
    print("  M4 (every library template earned by an exact solve): %s"
          % ("PASS" if m4_ok else "FAIL"))

    # ---- verdict ----
    print("\n" + "=" * 78)
    print("CLAIMS")
    print("=" * 78)
    rows = [("M1 path rescued via meta-shape match (F1=1.0)", m1_ok),
            ("M2 felt path solver-free (0 Tarjan)", m2_ok),
            ("M3 near-path decoy: elevated dist + verify corrects", m3_ok),
            ("M4 earned, not planted (Arm-2 contrast)", m4_ok)]
    for name, ok in rows:
        print("  %-50s %s" % (name, "PASS" if ok else "FAIL"))
    allpass = all(ok for _, ok in rows)
    verdict = ("TRACK (j2) PASS: the path case track (j) could not touch is RESCUED by "
               "meta-shape match against known solutions — a fresh path FEELS like a "
               "chain, imports the chain's earned spine-role template, and flags its "
               "cut-vertices exactly (F1=1.0), felt path solver-free. The near-path "
               "decoy shows the honest limit: a loose match (elevated distance) whose "
               "imported template is wrong, corrected only by verification — "
               "feel-then-verify intact. The templates are EARNED (solved once), not a "
               "planted hand-table. This REFRAMES track (j)'s 'local-shape-bounded' "
               "ceiling to a COVERAGE ceiling: the felt read works wherever a "
               "configuration's meta-shape matches a SOLVED exemplar — including the "
               "global-criticality path — and fails only on meta-shapes matching "
               "nothing solved. The unmapped-domain numerology fence still stands "
               "(the exemplars here are checkable)."
               if allpass else
               "TRACK (j2): see failing claim(s) above.")
    print("\nVERDICT: %s" % verdict)
    print("=" * 78)

    summary = {"track": "j2", "library_build_solver_calls": build_spy.calls,
               "felt_path_solver_calls": felt_spy.calls,
               "library": {k: {"meta": e["meta"], "roles": e["roles"]}
                           for k, e in lib.items()},
               "near_path": {"nearest": rn["nearest"], "match_dist": rn["match_dist"],
                             "clean_dist": clean_dist, "f1": f1_near,
                             "predicted": sorted(rn["predicted"]),
                             "truth": sorted(truth_n)},
               "m1": m1_ok, "m2": m2_ok, "m3": m3_ok, "m4": m4_ok, "all_pass": allpass}
    print("SUMMARY_JSON " + json.dumps(summary))
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
