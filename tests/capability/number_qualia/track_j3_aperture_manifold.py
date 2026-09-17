"""TRACK (j3) — THE APERTURE MANIFOLD: "local/global is aperture, not magic".

Completes the arc of sub-experiment (j). Track (j) read a per-element isolation
coordinate and FAILED on the degree-regular PATH (criticality there is not a
within-instance outlier). Track (j2) RESCUED the path by matching the WHOLE
configuration's meta-shape against solved exemplars — but that was not a separate
mechanism. It was the SAME structural read at a COARSER APERTURE. This track shows
the collapse: the path's criticality falls out of the substrate's OWN aperture dial
(domains.order_n_concepts.nth_order_terms — the finite-difference machinery
falling_world uses to discover an order-2 generator from raw pixels), with NO
hand-authored meta-shape descriptor and NO exemplar library.

DESIGN PRINCIPLE (user: "there is no need to choose a single method"): we KEEP EVERY
APERTURE LIVE as parallel coordinates over the structural quantity and read the SHAPE
of the (node x order) manifold — we do NOT argmax to one aperture or switch to one
calculator. The property localizes wherever a bounded-radius outlier appears at SOME
aperture; the shape across apertures IS the confidence interval.

WHAT THIS SHOWS
  · M1 PATH LOCALIZES NATIVELY: the fresh path's criticality (the track-(j) failure,
    F1=0) is recovered from the multi-aperture manifold via order_n_concepts, F1=1.0 —
    NO meta-shape descriptor, NO library. "Local/global is aperture" demonstrated.
  · M2 SAME READ, DIFFERENT SHAPE: the star's hub is an order-0 outlier; the same
    manifold read flags it (F1=1.0) with no method switch. Local and global criticality
    are two aperture settings of one read.
  · M3 FELT PATH SOLVER-FREE: the aperture read runs 0 Tarjan calls (the exact solver
    is the separate verify step; spy stays 0).
  · M4 CYCLE DETECTED -> CYCLIC READING: on a plain cycle (no cut vertices) the cycle is
    DETECTED (2-core peel) and TRIGGERS the cycle-aware reading, which correctly reports no
    cut vertices (F1=1.0, confirmed) — a confident correct read, not an abstain.
  · M5 THE STEER — the cycle is DETECTED and TRIGGERS A DIFFERENT APPROACH: on a ring+tail
    the cycle is detected and the cycle-aware reading is triggered (a node purely on the ring
    is not critical; only where a part attaches is), reading it correctly (F1=1.0). No
    hardcoded veto and no distrust — a detected cycle is not untrustworthy, it just needs the
    cyclic reading. Distrust via a learned anti-shape is reserved for genuine no-rescue
    structures (e.g. bridged multi-cycles); see the anti-shape wiring.

REFRAME: the track-(j2) coverage ceiling ("works where the meta-shape matches a solved
exemplar") sharpens to a WITNESS-RADIUS ceiling: feel recovers any property with a
BOUNDED-radius witness at some aperture, and honestly abstains where the only witness is
UNBOUNDED-radius. The meta-shape "library" was order-4 doing by lookup what order-1 does
by finite difference — one aperture dial, not two mechanisms.

Run: PYTHONPATH=runners/dsl/python:. python3 tests/capability/number_qualia/track_j3_aperture_manifold.py
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))

import number_runner as R              # noqa: E402


def _ud(edges):
    adj = {}
    for a, b in edges:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return {v: sorted(ns) for v, ns in adj.items()}


def _path(n):  return _ud([("n%d" % i, "n%d" % (i + 1)) for i in range(n - 1)])
def _star(n):  return _ud([("h", "l%d" % i) for i in range(n - 1)])
def _cycle(n): return _ud([("y%d" % i, "y%d" % ((i + 1) % n)) for i in range(n)])


def _ring_tail(ring_n):
    # a cycle of ring_n nodes plus one pendant tail; the tail's attach point is the
    # ONLY cut vertex. A ring interior node LOOKS like a path interior to any local
    # coordinate (degree 2, a neighbour each side) but is NOT critical — the 'way
    # around' is the whole rest of the ring, an unbounded-radius fact.
    edges = [("y%d" % i, "y%d" % ((i + 1) % ring_n)) for i in range(ring_n)]
    edges.append(("y0", "tail"))
    return _ud(edges)


def _order_nodes(adj):
    """A traversal order for laying the structural coordinate out along a dimension.
    For paths/rings a DFS from a leaf (or any node) recovers the natural linear order;
    this is the 'which dimension to difference along' choice — part of the aperture,
    and (per the honest fence) something that must be earned/verified for novel
    structure. Here a simple DFS suffices for the linear families under test."""
    start = min(adj, key=lambda v: (len(adj[v]), v))   # a leaf if one exists
    seen, order, stack = set(), [], [start]
    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u); order.append(u)
        for w in sorted(adj[u], reverse=True):
            if w not in seen:
                stack.append(w)
    for v in adj:                                       # any disconnected remainder
        if v not in seen:
            order.append(v)
    return order


def main() -> int:
    print("=" * 78)
    print("TRACK (j3) — THE APERTURE MANIFOLD: local/global is aperture, not magic")
    print("=" * 78)

    felt_spy = R.SolverSpy()          # must stay 0 across every felt read below

    cases = [
        ("PATH-7        (track-(j) failure; global criticality)", _path(7), True),
        ("STAR-6        (node-local criticality; the hub)",       _star(6), True),
        ("CYCLE-6       (no cut vertices)",                        _cycle(6), False),
        ("RING+TAIL     (ring interior LOOKS critical, is not)",  _ring_tail(6), False),
    ]

    results = {}
    for label, g, _ in cases:
        order = _order_nodes(g)
        felt = R.felt_aperture_read(g, order, spy=felt_spy)   # FELT: solver-free
        truth = R.tarjan_cut_vertices(g)                      # VERIFY: separate
        results[label] = (felt, truth, order)

        print("\n" + "-" * 78)
        print(label)
        print("-" * 78)
        deg = [len(g[v]) for v in order]
        print("  order-0 coord (degree in traversal order): %s" % deg)
        for o in sorted(felt["manifold"]):
            outs = sorted(R.manifold_shape(felt["manifold"])[o])
            print("    order %d diffs=%s  outliers@idx=%s"
                  % (o, felt["manifold"][o], outs))
        print("  true cut-vertices: %s" % sorted(truth))
        if felt["committed"]:
            f1 = R.f1_score(felt["predicted"], truth)
            print("  FELT: COMMIT (%s)  predicted=%s  F1=%.2f  [apertures %s live, "
                  "no single method chosen]"
                  % (felt["reason"], sorted(felt["predicted"]), f1, felt["peaked"]))
        else:
            # what it WOULD have predicted, to show the abstain was protective
            man = R.aperture_manifold(g, order)
            shp = R.manifold_shape(man)
            deg_out = shp.get(0, set())
            pos = {v: i for i, v in enumerate(order)}
            would = set()
            for i, v in enumerate(order):
                flanked = (any(pos[u] < i for u in g[v])
                           and any(pos[u] > i for u in g[v]))
                if flanked and i not in deg_out:
                    would.add(v)
                elif i in deg_out and len(g[v]) > 2:
                    would.add(v)
            wf1 = R.f1_score(would, truth)
            print("  FELT: ABSTAIN (%s) -> route to VERIFY" % felt["reason"])
            print("        (had it committed it would have predicted %s at F1=%.2f "
                  "— the abstain PREVENTED a false peak)" % (sorted(would), wf1))

    # ---------------- claims ----------------
    print("\n" + "=" * 78)
    print("CLAIMS")
    print("=" * 78)

    path_felt, path_truth, _ = results["PATH-7        (track-(j) failure; global criticality)"]
    m1 = path_felt["committed"] and R.f1_score(path_felt["predicted"], path_truth) >= 0.99
    print("  M1 PATH localizes NATIVELY via order-N aperture (F1=1.0, no library): %s"
          % ("PASS" if m1 else "FAIL"))

    star_felt, star_truth, _ = results["STAR-6        (node-local criticality; the hub)"]
    m2 = star_felt["committed"] and R.f1_score(star_felt["predicted"], star_truth) >= 0.99
    print("  M2 STAR (node-local) via the SAME read, different shape (F1=1.0):        %s"
          % ("PASS" if m2 else "FAIL"))

    m3 = felt_spy.calls == 0
    print("  M3 FELT path solver-free (Tarjan calls during all felt reads = %d):      %s"
          % (felt_spy.calls, "PASS" if m3 else "FAIL"))

    cyc_felt, cyc_truth, _ = results["CYCLE-6       (no cut vertices)"]
    # Cycle DETECTION now triggers the cyclic reading: cycle6 is read the cyclic way and
    # confirmed (no cut vertices), a confident correct read rather than an abstain.
    m4 = (cyc_felt["committed"] and cyc_felt["reason"] == "cycle_detected_cyclic_reading"
          and R.f1_score(cyc_felt["predicted"], cyc_truth) >= 0.999)
    print("  M4 CYCLE-6 detected as cyclic -> cyclic reading -> confirmed (F1=1.0, no cut vs): %s"
          % ("PASS" if m4 else "FAIL"))

    rt_felt, rt_truth, _ = results["RING+TAIL     (ring interior LOOKS critical, is not)"]
    # The steer: the cycle is DETECTED and TRIGGERS a different reading. Ring+tail is read
    # the cyclic way (only the attachment point is critical) and confirmed F1=1.0 — no
    # hardcoded veto, no distrust; the cycle simply triggers the appropriate approach.
    rt_f1 = R.f1_score(rt_felt["predicted"], rt_truth) if rt_felt["committed"] else None
    m5 = (rt_felt["committed"] and rt_felt["reason"] == "cycle_detected_cyclic_reading"
          and rt_f1 is not None and rt_f1 >= 0.999)
    print("  M5 RING+TAIL: cycle DETECTED -> cyclic reading -> read correctly (F1=%s),"
          % ("%.2f" % rt_f1 if rt_f1 is not None else "n/a"))
    print("     the detected cycle triggers a different approach (steer):                %s"
          % ("PASS" if m5 else "FAIL"))

    ok = all([m1, m2, m3, m4, m5])
    print("\n  VERDICT: %s" % ("ALL PASS — aperture manifold; acyclic read by default, "
                               "cycle DETECTED -> cyclic reading, all confirmed"
                               if ok else "SOME FAILED — see above"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
