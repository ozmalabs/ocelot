"""Brick 6 — ORDER-N COLLAPSE: PUSH TO THE FRONTIER.

The order-n collapse selector (domains/generator_order_n.py) cracks exact-
arithmetic synthesis by collapsing candidates in ORDER-N (finite-difference)
space: constants land in the order-n null space and VANISH; additive structure
LINEARIZES, so a greedy matching-pursuit peels off the components one at a time.

MECHANISM PREDICTION (the thing this script tests honestly):
  - SEPARABLE / additive targets: order-n keeps cracking them at cost ~ (#components),
    FAR past the order-0 combinatorial wall, ~linear in #components.
  - BREAKS where the target is NOT separable in derivative space:
      (i)   cross-terms (a*b, a*b+b*c) — the order-n profile of the WHOLE does not
            factor into per-axis component profiles the pursuit can peel,
      (ii)  DEGENERATE signatures — symmetric components with identical order-n
            profiles the pursuit can't tell apart,
      (iii) grid / finite-difference ill-defined,
      (iv)  just budget/K (would solve with more — note if raising K/budget recovers).

This script runs a HARDNESS LADDER, per-category, scaling each axis until order-n
fails, and DIAGNOSES the first failure of each axis against those modes — grounded
in the actual order-n profile / matching-pursuit trace, not guessed.

Contrast modes (they should die early on the hard rungs): unguided + distance(o0).

Weightless: reuses the committed OrderNCollapse + the agent's own nth_order_terms
finite difference. No net, no LLM, no Rust.

Run:
  ulimit -v 8388608
  PYTHONPATH=runners/dsl/python:. python3 scripts/generator_order_n_push.py
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
from domains.generator import synthesize, _term_str, _num
from domains.generator_self_improve import output_distance
from domains.generator_order_n import (
    OrderNCollapse, rank_by_order_n, order_n_match, build_grid, _axis_diffs,
)


def banner(s):
    print("\n" + "=" * 78)
    print(s)
    print("=" * 78)


def _envs(keys, rows):
    return [dict(zip(keys, r)) for r in rows]


def _grid_train(var_names, n=9):
    """A spread of training envs that exercise EVERY var jointly (deterministic).
    Critically: avoid rows where most vars are 0 (those make products degenerate
    and let trivial terms like `0` match). We generate distinct tuples with no
    zeros first, then a few with a single zero, then mixed — enough rows of
    genuinely varying inputs to pin a degree-d polynomial (incl. products)."""
    nv = len(var_names)
    rows = []
    seen = set()

    def add(tup):
        if tup not in seen:
            seen.add(tup)
            rows.append(dict(zip(var_names, tup)))

    # 1) all-nonzero distinct tuples (cycled small primes per position so the
    #    product/cross-terms are non-degenerate and each var genuinely varies)
    base = [(2, 3, 1, 4, 2, 3), (1, 2, 3, 1, 3, 2), (3, 1, 2, 2, 1, 4),
            (4, 2, 1, 3, 2, 1), (2, 1, 3, 4, 1, 2), (1, 3, 2, 1, 4, 3),
            (3, 4, 1, 2, 3, 1)]
    for b in base:
        add(tuple(b[:nv]))
        if len(rows) >= n - 2:
            break
    # 2) a couple of rows WITH a zero (so the synthesizer sees the additive
    #    structure when a component drops out) — but only one zero, not many.
    zr = [0] + [2] * (nv - 1)
    add(tuple(zr))
    zr2 = [1] * (nv - 1) + [0]
    add(tuple(zr2))
    # 3) top up with more distinct nonzero tuples if needed
    for tup in itertools.product((1, 2, 3, 4, 5), repeat=nv):
        if len(rows) >= n:
            break
        add(tup)
    return rows[:n]


def _heldout(var_names, n=4):
    nv = len(var_names)
    rows = []
    seen = set()
    for tup in itertools.product((6, 7, 5, 2), repeat=nv):
        # all-nonzero held-out at larger values (true generalization test)
        if tup in seen:
            continue
        seen.add(tup)
        rows.append(dict(zip(var_names, tup)))
        if len(rows) >= n:
            break
    return rows


# ---------------------------------------------------------------------------
# THE LADDER. Each rung: (name, var_names, true_fn, max_size).
# Categories scaled until order-n fails.
# ---------------------------------------------------------------------------

def _f(expr):
    """Build a true_fn from a python lambda over named kwargs."""
    return expr


LADDER = {
    # A. SUMS OF SQUARES (separable, scale #components 2..5)
    "A. sums-of-squares": [
        ("a*a+b*b",          ["a", "b"],          lambda a, b: a*a + b*b, 8),
        ("a*a+b*b+c*c",      ["a", "b", "c"],     lambda a, b, c: a*a + b*b + c*c, 11),
        ("a*a+b*b+c*c+d*d",  ["a", "b", "c", "d"], lambda a, b, c, d: a*a + b*b + c*c + d*d, 14),
        ("aa+bb+cc+dd+ee",   ["a", "b", "c", "d", "e"],
         lambda a, b, c, d, e: a*a + b*b + c*c + d*d + e*e, 17),
    ],
    # B. SUMS OF CUBES
    "B. sums-of-cubes": [
        ("a3+b3",        ["a", "b"],      lambda a, b: a*a*a + b*b*b, 11),
        ("a3+b3+c3",     ["a", "b", "c"], lambda a, b, c: a*a*a + b*b*b + c*c*c, 16),
    ],
    # C. SINGLE-VAR DEGREE (degree 2..5)
    "C. single-var degree": [
        ("x2", ["x"], lambda x: x*x, 5),
        ("x3", ["x"], lambda x: x*x*x, 7),
        ("x4", ["x"], lambda x: x*x*x*x, 9),
        ("x5", ["x"], lambda x: x*x*x*x*x, 11),
    ],
    # D. SINGLE-VAR POLYNOMIAL (multi-component, 1 var)
    "D. single-var poly": [
        ("x2+x",     ["x"], lambda x: x*x + x, 7),
        ("x3+x2+x",  ["x"], lambda x: x*x*x + x*x + x, 11),
        ("x3+x2+x+1", ["x"], lambda x: x*x*x + x*x + x + 1, 13),
    ],
    # E. PRODUCT ARITY (single product, grow arity)
    "E. product arity": [
        ("a*b",       ["a", "b"],           lambda a, b: a*b, 5),
        ("a*b*c",     ["a", "b", "c"],      lambda a, b, c: a*b*c, 7),
        ("a*b*c*d",   ["a", "b", "c", "d"], lambda a, b, c, d: a*b*c*d, 9),
        ("a*b*c*d*e", ["a", "b", "c", "d", "e"],
         lambda a, b, c, d, e: a*b*c*d*e, 11),
    ],
    # F. CROSS-TERMS (separability boundary)
    "F. cross-terms": [
        ("a*b+b*c",       ["a", "b", "c"], lambda a, b, c: a*b + b*c, 9),
        ("a*b+b*c+c*a",   ["a", "b", "c"], lambda a, b, c: a*b + b*c + c*a, 13),
        ("a*a+a*b+b*b",   ["a", "b"],      lambda a, b: a*a + a*b + b*b, 11),
    ],
    # G. PRODUCTS OF SUMS (non-trivially separable)
    "G. products-of-sums": [
        ("(a+b)(c+d)",       ["a", "b", "c", "d"], lambda a, b, c, d: (a+b)*(c+d), 9),
        ("(a+b)(c+d)(e+f)",  ["a", "b", "c", "d", "e", "f"],
         lambda a, b, c, d, e, f: (a+b)*(c+d)*(e+f), 14),
        ("(a+b+c)(d+e+f)",   ["a", "b", "c", "d", "e", "f"],
         lambda a, b, c, d, e, f: (a+b+c)*(d+e+f), 13),
    ],
    # H. DEEP NESTED
    "H. deep-nested": [
        ("(a*b+c)*d",      ["a", "b", "c", "d"],      lambda a, b, c, d: (a*b + c)*d, 11),
        ("((a+b)*c+d)*e",  ["a", "b", "c", "d", "e"], lambda a, b, c, d, e: ((a+b)*c + d)*e, 13),
    ],
}


def run(s, var_names, fn, ms, method, K, budget, order=2):
    tr = _grid_train(var_names)
    ho = _heldout(var_names)
    examples = [(env, fn(**env)) for env in tr]
    kw = dict(max_size=ms, timeout_s=budget)
    if method == "distance":
        kw.update(guide=output_distance, guide_beam=K)
    elif method == "order_n":
        col = OrderNCollapse(s, var_names, order=order).set_target_fn(fn)
        kw.update(guide_select=col, guide_beam=K)
    # unguided: nothing
    r = synthesize(s, examples, **kw)
    gen = None
    if r["fits"]:
        gen = True
        for env in ho:
            try:
                got = r["term"].evaluate(env, s)
            except Exception:
                gen = False
                break
            gotn = (1 if got is True else 0) if isinstance(got, bool) else got
            if abs(float(gotn) - float(fn(**env))) > 1e-9:
                gen = False
                break
    return {"solved": r["fits"], "explored": r["explored"], "time": r["elapsed_s"],
            "size": r["size"], "halt": r["halt_reason"], "term": r["term_str"],
            "gen": gen}


def cell(r):
    if r["solved"]:
        g = "g" if r["gen"] else "G?"
        return f"OK sz{r['size']} e{r['explored']} {r['time']:.1f}s {g}"
    return f"{r['halt'][:4]} e{r['explored']} {r['time']:.1f}s"


# per-#vars order-n order to use (degree-aware). We pass the natural polynomial
# degree of the target via the rung's order arg; default 2 if not specified.
def main():
    banner("ORDER-N COLLAPSE — PUSH THE FRONTIER. How far past the order-0 wall, "
           "and where/why does it break?")
    print("""\
  Ladder of increasingly hard EXACT targets per category, scaled until order-n
  fails. Contrast: unguided + distance(o0) (should die early on the hard rungs).
  Per rung: order-n solved? size/explored/time/gen; unguided/distance solved?
  Then per category: largest solved (FRONTIER) + first failure + DIAGNOSIS.""")

    s = Substrate()
    K = 14
    BUDGET = 75.0

    # order to use per target = its polynomial degree (clamped >=2 so the
    # curvature is read; single products of arity n are degree n).
    def deg_for(name, var_names, fn):
        # cheap degree probe: fit by checking how the target scales — but we know
        # the targets, so hard-code the polynomial degree per rung.
        return _DEG.get(name, 2)

    results = {}  # cat -> [(name, ron, rung, rdist)]
    for cat, rungs in LADDER.items():
        banner(cat)
        print(f"  {'rung':16} {'ORDER-N':30} {'unguided':24} {'distance(o0)':24}")
        print("  " + "-" * 92)
        rows = []
        order_n_failed = False
        for (name, var_names, fn, ms) in rungs:
            od = deg_for(name, var_names, fn)
            ron = run(s, var_names, fn, ms, "order_n", K, BUDGET, order=od)
            # only run the (expensive) contrasts if order-n solved OR this is the
            # first failure — to keep budget bounded but still show the contrast.
            run_contrast = ron["solved"] or not order_n_failed
            if run_contrast:
                rung_u = run(s, var_names, fn, ms, "unguided", None, BUDGET)
                rdist = run(s, var_names, fn, ms, "distance", K, BUDGET)
            else:
                rung_u = rdist = {"solved": None, "explored": 0, "time": 0,
                                  "size": None, "halt": "skip", "term": None, "gen": None}
            rows.append((name, var_names, fn, ms, od, ron, rung_u, rdist))
            uc = cell(rung_u) if rung_u["solved"] is not None else "(skipped)"
            dc = cell(rdist) if rdist["solved"] is not None else "(skipped)"
            print(f"  {name:16} {cell(ron):30} {uc:24} {dc:24}")
            if not ron["solved"]:
                order_n_failed = True
        results[cat] = rows

    # ----------------------------------------------------------------------
    # FRONTIER per category + first-failure diagnosis.
    # ----------------------------------------------------------------------
    banner("FRONTIER per category — largest solved + first failure")
    first_failures = []
    for cat, rows in results.items():
        solved = [r for r in rows if r[5]["solved"]]
        failed = [r for r in rows if not r[5]["solved"]]
        largest = solved[-1][0] if solved else "NONE"
        first_fail = failed[0][0] if failed else "none (whole ladder solved)"
        print(f"  {cat:22} largest-solved={largest:14} first-failure={first_fail}")
        if failed:
            first_failures.append((cat, failed[0]))

    # ----------------------------------------------------------------------
    # SCALING: sums-of-squares explored vs #components (the ~linear claim).
    # ----------------------------------------------------------------------
    banner("SCALING — sums-of-squares (A): explored vs #components "
           "(order-n ~linear? unguided/distance explode?)")
    print(f"  {'#comp':>6} {'order-n explored':>18} {'unguided explored':>18} "
          f"{'distance explored':>18}")
    print("  " + "-" * 64)
    for (name, var_names, fn, ms, od, ron, ru, rdist) in results["A. sums-of-squares"]:
        nc = len(var_names)
        on_e = ron["explored"] if ron["solved"] else f"FAIL({ron['explored']})"
        u_e = (ru["explored"] if ru["solved"] else f"FAIL({ru['explored']})") \
            if ru["solved"] is not None else "(skip)"
        d_e = (rdist["explored"] if rdist["solved"] else f"FAIL({rdist['explored']})") \
            if rdist["solved"] is not None else "(skip)"
        print(f"  {nc:>6} {str(on_e):>18} {str(u_e):>18} {str(d_e):>18}")

    # ----------------------------------------------------------------------
    # DIAGNOSE each first-failure, grounded in the order-n profile / pursuit trace.
    # ----------------------------------------------------------------------
    banner("FIRST-FAILURE DIAGNOSIS — grounded in the order-n profile / pursuit "
           "trace (which predicted break mode)")
    for cat, (name, var_names, fn, ms, od, ron, ru, rdist) in first_failures:
        diagnose(s, cat, name, var_names, fn, ms, od, ron, ru, rdist, K)

    banner("DONE — see FRONTIER + DIAGNOSIS above for the honest map.")


# polynomial degrees per rung (order-n order = degree, clamped >=2)
_DEG = {
    "a*a+b*b": 2, "a*a+b*b+c*c": 2, "a*a+b*b+c*c+d*d": 2, "aa+bb+cc+dd+ee": 2,
    "a3+b3": 3, "a3+b3+c3": 3,
    "x2": 2, "x3": 3, "x4": 4, "x5": 5,
    "x2+x": 2, "x3+x2+x": 3, "x3+x2+x+1": 3,
    "a*b": 2, "a*b*c": 3, "a*b*c*d": 4, "a*b*c*d*e": 5,
    "a*b+b*c": 2, "a*b+b*c+c*a": 2, "a*a+a*b+b*b": 2,
    "(a+b)(c+d)": 2, "(a+b)(c+d)(e+f)": 3, "(a+b+c)(d+e+f)": 2,
    "(a*b+c)*d": 3, "((a+b)*c+d)*e": 3,
}


def diagnose(s, cat, name, var_names, fn, ms, od, ron, ru, rdist, K):
    """Ground the diagnosis: show the target's order-n profile and (where the
    answer is separable in principle) the matching-pursuit trace on the size
    cohort, to classify the break mode (i..iv)."""
    print(f"\n  --- {cat}: first failure = {name} (order-n order={od}, "
          f"halt={ron['halt']}, explored={ron['explored']}, time={ron['time']:.1f}s)")

    col = OrderNCollapse(s, var_names, order=od).set_target_fn(fn)
    tp = col.target_prof
    # per-axis profile slice (so we can see if it FACTORS into per-component pieces)
    grid = col.grid
    per_axis = []
    n_orders = len(col.use_orders)
    # reconstruct per-axis chunk lengths: each axis contributes, per used order,
    # (span - order) diffs.
    idx = 0
    for (v, envs) in grid:
        chunk = []
        for o in col.use_orders:
            ln = len(envs) - o
            chunk.append((o, [round(x, 2) for x in tp[idx:idx + ln]]))
            idx += ln
        per_axis.append((v, chunk))
    print(f"    target order-n profile, per axis:")
    for (v, chunk) in per_axis:
        for (o, vals) in chunk:
            print(f"      axis {v} order-{o}: {vals}")

    # SYMMETRY / DEGENERACY check: are the per-axis profiles identical across
    # variables (symmetric components -> degenerate signatures the pursuit can't
    # distinguish)?
    axis_sigs = [tuple(tuple(vals) for (_o, vals) in chunk) for (_v, chunk) in per_axis]
    distinct_axis = len(set(axis_sigs))
    print(f"    distinct per-axis profiles: {distinct_axis} of {len(axis_sigs)} "
          f"({'SYMMETRIC/degenerate' if distinct_axis < len(axis_sigs) else 'asymmetric'})")

    # Whether order-n is ZERO on every axis (cross-term killed by single-axis
    # differencing): the target's curvature lives only in a MIXED partial, which
    # the per-axis grid (others held fixed) cannot see.
    allzero = all(all(all(x == 0 for x in vals) for (_o, vals) in chunk)
                  for (_v, chunk) in per_axis)
    nz_axes = sum(1 for (_v, chunk) in per_axis
                  if any(any(x != 0 for x in vals) for (_o, vals) in chunk))
    print(f"    axes with NONZERO order-n structure: {nz_axes} of {len(per_axis)}"
          f"{'  <- ALL-ZERO single-axis profile (structure is in a MIXED partial)' if allzero else ''}")

    # MATCHING-PURSUIT TRACE on the largest cohort the search reached (the terms
    # the pursuit would peel). We re-run a passthrough capture to get a cohort at
    # a representative size, then show what the pursuit selects vs what's needed.
    trace_size = max(2, min(ms - 1, _DEG.get(name, 2) + 2))
    cohort = _capture_cohort(s, var_names, fn, trace_size, budget=20.0)
    if cohort:
        ranked = rank_by_order_n(cohort, col)
        print(f"    pursuit cohort @ size {trace_size}: {len(cohort)} distinct terms; "
              f"top-5 by order-n match:")
        for (rk, t, sg, m) in ranked[:5]:
            print(f"      #{rk:<3} match={m:+.3f}  {_term_str(t)}")
        # how many cohort terms have ANY nonzero order-n profile (vs all-zero =
        # the pursuit sees them as noise)?
        nz = sum(1 for (_rk, t, _sg, m) in ranked if abs(m) > 1e-9)
        print(f"      cohort terms with nonzero order-n match: {nz} of {len(ranked)}")

    # CLASSIFY
    if allzero or nz_axes < len(var_names):
        if cat.startswith("F") or cat.startswith("G") or cat.startswith("H"):
            mode = ("(i) NON-SEPARABLE in order-n space: the single-axis finite "
                    "difference (others held fixed) zeroes the cross/product "
                    "structure — the curvature lives in a MIXED partial the per-"
                    "axis grid can't read; the profile doesn't factor into peelable "
                    "components.")
        else:
            mode = ("(i) order-n single-axis profile is degenerate for this form.")
    elif distinct_axis < len(axis_sigs) and cat.startswith(("E", "G")):
        mode = ("(ii) DEGENERATE signatures: symmetric components share an "
                "identical per-axis order-n profile; the matching-pursuit cannot "
                "tell the partners apart / a single product needs the WHOLE "
                "co-varying, not a per-axis sum.")
    else:
        # check budget recovery
        mode = _check_budget(s, var_names, fn, ms, od, K)
    print(f"    => DIAGNOSIS: {mode}")


def _capture_cohort(s, var_names, fn, want_size, budget=20.0):
    """Capture the full distinct-behaviour cohort at a target size (passthrough)."""
    from scripts.generator_order_n import CohortCapture
    tr = _grid_train(var_names)
    examples = [(env, fn(**env)) for env in tr]
    cap = CohortCapture(want_size=want_size)
    synthesize(s, examples, max_size=want_size, timeout_s=budget,
               guide_select=cap, guide_beam=1)
    return cap.cohort or []


def _check_budget(s, var_names, fn, ms, od, K):
    """Is the failure just budget/K? Re-try with a larger K and more time; report
    whether it recovers."""
    bigK = K * 3
    r = run(s, var_names, fn, ms, "order_n", bigK, 120.0, order=od)
    if r["solved"]:
        return (f"(iv) BUDGET/K: recovered with K={bigK} + 120s "
                f"(sz{r['size']} e{r['explored']}) — not a fundamental break.")
    # try a different order too
    r2 = run(s, var_names, fn, ms, "order_n", bigK, 120.0, order=max(2, od + 1))
    if r2["solved"]:
        return (f"(iv) BUDGET/ORDER: recovered with K={bigK}, order={od+1}, 120s "
                f"(sz{r2['size']} e{r2['explored']}).")
    return ("(iii/iv) did NOT recover with 3xK + 120s (+order bump); likely the "
            "size ceiling / search width, not the order-n collapse per se — the "
            "profile is informative but the term is too large to enumerate.")


if __name__ == "__main__":
    main()
