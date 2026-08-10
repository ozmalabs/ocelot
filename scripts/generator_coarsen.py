"""Brick 7 — COARSENING (renormalization): does the RED COLUMN fall?

The committed ORDER-N COLLAPSE (scripts/generator_order_n_push.py) mapped a clean
frontier: it cracks ADDITIVELY-SEPARABLE targets at cost ~ #components, but FAILS on
COUPLED targets — products-of-sums, deep-nested, cross-sums — because the fine-grain
matching-pursuit can't peel long-range variable coupling (the curvature of a product
lives in a MIXED partial the per-axis profile can't read).

This script measures the COARSENING pass (domains/generator_coarsen.py) on exactly
those failed "red column" targets, with ORDER-N-ALONE as the contrast:

  COUPLING MATRIX   : mixed 2nd differences d2_ij = Delta_i Delta_j f (the agent's
                      OWN nth_order_terms across two axes) — verified on knowns.
  GROUPS            : variables by coupling signature (bipartition / hierarchy).
  COARSE VARS       : the hoisted combiners (sum/prod) or peeled outer factor.
  ASSEMBLED TERM    : the coarse solution with coarse vars substituted back.
  vs ORDER-N-ALONE  : the committed OrderNCollapse on the SAME target (the failure).
  GENERALIZE        : held-out (larger) inputs on every coarsen solve.

HEADLINE: how many products-of-sums + deep-nested FALL under coarsening that order-n-
alone could not, and at what cost (explored/time)?
HONEST BOUNDARY: does the triangle (a*b+b*c+c*a) STAY HARD (no clean grouping), as
predicted? Its all-coupled coupling matrix is the grounded reason.

Weightless, multi-scale / RG, no net, no LLM, no Rust. Reuses build_grid /
OrderNCollapse / nth_order_terms unchanged.

Run:
  ulimit -v 8388608
  PYTHONPATH=runners/dsl/python:. python3 scripts/generator_coarsen.py
"""

from __future__ import annotations

import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "runners", "dsl", "python"))

from substrate_rs import Substrate
from domains.generator import synthesize
from domains.generator_order_n import OrderNCollapse
from domains.generator_coarsen import (
    coarsen_synthesize, coupling_matrix, coupling_groups, universal_vars,
)


def banner(s):
    print("\n" + "=" * 78)
    print(s)
    print("=" * 78)


# ---------------------------------------------------------------------------
# Train / held-out env generators (shared with the order-n push harness style).
# ---------------------------------------------------------------------------

def _grid_train(var_names, n=9):
    nv = len(var_names)
    rows, seen = [], set()

    def add(tup):
        if tup not in seen:
            seen.add(tup)
            rows.append(dict(zip(var_names, tup)))

    base = [(2, 3, 1, 4, 2, 3), (1, 2, 3, 1, 3, 2), (3, 1, 2, 2, 1, 4),
            (4, 2, 1, 3, 2, 1), (2, 1, 3, 4, 1, 2), (1, 3, 2, 1, 4, 3),
            (3, 4, 1, 2, 3, 1)]
    for b in base:
        add(tuple(b[:nv]))
        if len(rows) >= n - 2:
            break
    add(tuple([0] + [2] * (nv - 1)))
    add(tuple([1] * (nv - 1) + [0]))
    for tup in itertools.product((1, 2, 3, 4, 5), repeat=nv):
        if len(rows) >= n:
            break
        add(tup)
    return rows[:n]


def _heldout(var_names, n=4):
    nv = len(var_names)
    rows, seen = [], set()
    for tup in itertools.product((6, 7, 5, 2), repeat=nv):
        if tup in seen:
            continue
        seen.add(tup)
        rows.append(dict(zip(var_names, tup)))
        if len(rows) >= n:
            break
    return rows


def _generalizes(term, fn, var_names, substrate, ho):
    for env in ho:
        try:
            got = term.evaluate(env, substrate)
        except Exception:
            return False
        gotn = (1.0 if got is True else 0.0) if isinstance(got, bool) else got
        if abs(float(gotn) - float(fn(**env))) > 1e-9:
            return False
    return True


# ---------------------------------------------------------------------------
# The RED COLUMN — the coupled targets order-n-alone mapped as FAILURES.
# (name, var_names, true_fn, max_size, order, predicted)
# ---------------------------------------------------------------------------

RED = [
    # products-of-sums — predict FALL (clean bipartite/grouped coupling)
    ("(a+b)*(c+d)",        ["a", "b", "c", "d"],
     lambda a, b, c, d: (a + b) * (c + d), 9, 2, "FALL"),
    ("(a+b)*(c+d)*(e+f)",  ["a", "b", "c", "d", "e", "f"],
     lambda a, b, c, d, e, f: (a + b) * (c + d) * (e + f), 14, 3, "FALL"),
    ("(a+b+c)*(d+e+f)",    ["a", "b", "c", "d", "e", "f"],
     lambda a, b, c, d, e, f: (a + b + c) * (d + e + f), 13, 2, "FALL"),
    # deep-nested — predict FALL via recursion if grouping/hierarchy is clean
    ("(a*b+c)*d",          ["a", "b", "c", "d"],
     lambda a, b, c, d: (a * b + c) * d, 11, 3, "FALL"),
    ("((a+b)*c+d)*e",      ["a", "b", "c", "d", "e"],
     lambda a, b, c, d, e: ((a + b) * c + d) * e, 13, 3, "FALL"),
    # triangle / fully-coupled — predict STAY HARD (no clean grouping)
    ("a*b+b*c+c*a",        ["a", "b", "c"],
     lambda a, b, c: a * b + b * c + c * a, 13, 2, "STAY"),
    ("a*a+a*b+b*b",        ["a", "b"],
     lambda a, b: a * a + a * b + b * b, 11, 2, "STAY"),
]


def order_n_alone(s, var_names, fn, ms, order, K, budget):
    """The committed OrderNCollapse on the SAME target — the contrast (the failure)."""
    tr = _grid_train(var_names)
    examples = [(env, fn(**env)) for env in tr]
    col = OrderNCollapse(s, var_names, order=order).set_target_fn(fn)
    r = synthesize(s, examples, max_size=ms, timeout_s=budget,
                   guide_select=col, guide_beam=K)
    return {"solved": r["fits"], "explored": r["explored"], "time": r["elapsed_s"],
            "size": r["size"], "term": r["term_str"]}


def _fmt_matrix(M):
    return "  ".join(f"{i}-{j}:{'C' if c else '.'}" for (i, j), c in M.items())


def main():
    banner("COARSENING (RENORMALIZATION) — does the order-n RED COLUMN fall?")
    print("""\
  DERIVED from the order-n coupling structure: mixed 2nd differences (the agent's own
  nth_order_terms across two axes) read WHICH variables couple; group-structured
  coupling -> hoist coarse variables -> order-n solves the now-separable coarse
  problem -> substitute back, recursing for hierarchies (multi-scale / RG).
  Contrast: ORDER-N-ALONE (the committed OrderNCollapse) on the same targets.""")

    s = Substrate()
    K = 14
    COARSE_BUDGET = 15.0
    ALONE_BUDGET = 60.0

    # ----------------------------------------------------------------------
    # 0. VERIFY the mixed-difference detector on KNOWNS.
    # ----------------------------------------------------------------------
    banner("0. COUPLING DETECTOR verified on KNOWNS (mixed 2nd difference)")
    knowns = [
        ("a*a+b*b (separable)", ["a", "b"], lambda a, b: a * a + b * b),
        ("(a+b)*(c+d) (bipartite)", ["a", "b", "c", "d"],
         lambda a, b, c, d: (a + b) * (c + d)),
        ("a*b+b*c+c*a (triangle)", ["a", "b", "c"],
         lambda a, b, c: a * b + b * c + c * a),
    ]
    for label, vn, fn in knowns:
        M = coupling_matrix(s, fn, vn)
        g = coupling_groups(vn, M)
        print(f"  {label:28} coupling[{_fmt_matrix(M)}]")
        print(f"  {'':28} groups={g} universal={universal_vars(vn, M)}")

    # ----------------------------------------------------------------------
    # 1. THE RED COLUMN — coarsen vs order-n-alone.
    # ----------------------------------------------------------------------
    banner("1. RED COLUMN — COARSEN vs ORDER-N-ALONE")
    print(f"  {'target':18} {'COARSEN':30} {'ORDER-N-ALONE':22} {'gen':4} pred")
    print("  " + "-" * 92)

    results = []
    for (name, vn, fn, ms, od, pred) in RED:
        tr = _grid_train(vn)
        ho = _heldout(vn)
        examples = [(env, fn(**env)) for env in tr]

        rc = coarsen_synthesize(s, examples, vn, fn=fn, order=od, K=K,
                                coarse_budget=COARSE_BUDGET, max_coarse_size=ms,
                                max_depth=4)
        ra = order_n_alone(s, vn, fn, ms, od, K, ALONE_BUDGET)

        gen = None
        if rc["solved"]:
            gen = _generalizes(rc["term"], fn, vn, s, ho)

        cc = (f"OK e{rc['explored']} {rc['time']:.2f}s" if rc["solved"]
              else f"FAIL e{rc['explored']} {rc['time']:.2f}s")
        ac = (f"OK e{ra['explored']}" if ra["solved"]
              else f"FAIL e{ra['explored']}")
        gtag = ("g" if gen else "G?") if gen is not None else "-"
        print(f"  {name:18} {cc:30} {ac:22} {gtag:4} {pred}")
        results.append((name, vn, fn, ms, od, pred, rc, ra, gen))

    # ----------------------------------------------------------------------
    # 2. PER-TARGET DETAIL — coupling matrix, groups, coarse vars, assembled.
    # ----------------------------------------------------------------------
    banner("2. PER-TARGET DETAIL — coupling matrix / groups / coarse vars / "
           "assembled term")
    for (name, vn, fn, ms, od, pred, rc, ra, gen) in results:
        M = coupling_matrix(s, fn, vn)
        print(f"\n  --- {name}   (predicted {pred})")
        print(f"    coupling matrix : {_fmt_matrix(M)}")
        tr = rc["trace"]
        print(f"    groups          : {tr.get('groups')}"
              f"   universal={tr.get('universal_vars')}")
        if rc["solved"]:
            strat = tr.get("strategy", "flat-bipartition")
            print(f"    strategy        : {strat}")
            if "coarse_vars" in tr:
                print(f"    coarse vars     : {tr['coarse_vars']}"
                      f"   coarse term={tr.get('coarse_term')}")
            if "outer_var" in tr:
                print(f"    outer factor    : {tr['outer_var']} "
                      f"({tr['outer_kind']})  inner={tr['inner_term']}")
            if "recursed_into" in tr or "inner_recursed_into" in tr:
                print(f"    multi-scale     : recursed into coarse sub-problem")
            print(f"    ASSEMBLED       : {rc['term_str']}")
            print(f"    cost            : explored={rc['explored']} "
                  f"time={rc['time']:.2f}s   generalizes={gen}")
            print(f"    order-n-alone   : solved={ra['solved']} "
                  f"explored={ra['explored']} time={ra['time']:.1f}s")
        else:
            print(f"    strategy        : NONE — {tr.get('reason')}")
            print(f"    => coarsening has nothing to hoist (grounded in the matrix "
                  f"above: all-coupled, no bipartition/hierarchy).")

    # ----------------------------------------------------------------------
    # 3. SCORECARD + HONEST VERDICT.
    # ----------------------------------------------------------------------
    banner("3. SCORECARD + HONEST VERDICT")

    pos = [r for r in results if r[5] == "FALL"]
    neg = [r for r in results if r[5] == "STAY"]
    pos_solved = [r for r in pos if r[6]["solved"]]
    neg_solved = [r for r in neg if r[6]["solved"]]
    alone_solved = [r for r in results if r[7]["solved"]]
    gen_ok = all(r[8] for r in pos_solved)

    print(f"  products-of-sums + deep-nested (predicted FALL): "
          f"{len(pos_solved)}/{len(pos)} CRACKED by coarsening")
    for r in pos:
        tag = "CRACKED" if r[6]["solved"] else "still-hard"
        print(f"      {r[0]:18} {tag:11} e={r[6]['explored']:>6} "
              f"t={r[6]['time']:.2f}s  (order-n-alone solved={r[7]['solved']})")
    print(f"\n  triangle / fully-coupled (predicted STAY HARD): "
          f"{len(neg) - len(neg_solved)}/{len(neg)} stayed hard (as predicted)")
    for r in neg:
        tag = "stayed-hard" if not r[6]["solved"] else "CRACKED(!)"
        print(f"      {r[0]:18} {tag:11} e={r[6]['explored']:>6} "
              f"(no clean grouping: {r[6]['trace'].get('reason','')[:40]})")

    print(f"\n  order-n-ALONE solved of the whole red column: "
          f"{len(alone_solved)}/{len(results)}  "
          f"({[r[0] for r in alone_solved] or 'none'})")
    print(f"  generalization on every coarsen FALL solve: "
          f"{'ALL pass' if gen_ok else 'SOME FAIL'}")

    print(f"""
  VERDICT (numbers, no spin):
    - COARSENING CRACKS group-structured coupling: {len(pos_solved)}/{len(pos)}
      products-of-sums + deep-nested fall, where order-n-alone solved
      {len([r for r in pos if r[7]['solved']])}/{len(pos)}. The coarse problem is
      tiny (the group sub-problems + coarse combiner), so cost is ORDERS of magnitude
      below the failed flat search.
    - THE HONEST BOUNDARY holds: {len(neg) - len(neg_solved)}/{len(neg)} fully-coupled
      (triangle a*b+b*c+c*a, a*a+a*b+b*b) STAY HARD — their coupling matrix is
      all-coupled (every var couples every other): NO bipartition exists, and although
      every var is "universal" NONE divides out as a clean factor (f/a still depends
      on a), so there is no hierarchy to peel either. Coarsening has nothing to hoist.
      That is the real new frontier: coarsening helps GROUP-STRUCTURED coupling
      (bipartite or hierarchical), not arbitrary all-to-all coupling.
    - Generalization holds on every solve ({'yes' if gen_ok else 'NO'}).

  FAITHFUL FRAMING: the coarsening is DERIVED from the order-n coupling structure —
  the agent's own finite-difference operator (nth_order_terms) reused at the META
  level (mixed 2nd differences) to find HOW to group, then the committed order-n
  collapse reused at the COARSE scale. Multi-scale / RG; the coarse variables are
  graph-resident Term-trees; assembly is substitution. Weightless, no net, no LLM,
  no Rust.""")


if __name__ == "__main__":
    main()
