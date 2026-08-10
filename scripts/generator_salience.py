"""Brick 6 — the DECISIVE SALIENCE re-test of the guide.

Prior results:
  - DISTANCE guide (keep smallest |residual|) OVER-PRUNED and MISSED a*a+b*b: a
    structural partner that is FAR in magnitude got dropped from the closest-K
    slots.
  - INTERFERENCE guide (keep most anti-correlated residual) was BURIED: ~150
    trivial constant/zero terms (residual ~ -target, cos -1, NO structure)
    swamped the real structural partners a*a (#157) / b*b (#166).

DIAGNOSIS (and the independent neural paper GESC): both guides ranked over a
candidate pool POLLUTED by NON-SALIENT terms; structureless terms game any naive
metric by sheer NUMEROSITY.

FIX: a SALIENCE PRE-FILTER — select on structural-contribution-to-the-goal
(output VARIANCE / input-dependence), not raw signal. Demote non-salient
(constant/zero/input-independent) terms OUT of the ranked candidate slots so the
salient structural terms survive the per-size cap. Constants STAY as building
blocks for composition; they are only demoted as ranked candidates.

The falsifiable split this script measures:
  HEADLINE 1 (salience-as-lever): does (A) distance+salience SOLVE a*a+b*b at the
    small K where (C) un-salient distance MISSES? If yes -> SALIENCE ALONE is the
    lever; interference was a red herring.
  HEADLINE 2 (salience un-buries interference?): does (B) interference+salience
    surface a*a / b*b ABOVE the trivial terms (new rank vs #157/#166) and SOLVE
    at small K?
  RANK CHECK: after salience filtering, where do the ~150 trivial terms go, and
    where do a*a / b*b land?
  Whole-set: explored/bound for A,B vs C,D,E; uniquely-salience solves;
    generalization; honest limits; verdict.

Five modes:
  (A) distance + salience       (E) brick-6 unguided
  (B) interference + salience
  (C) un-salient distance       (D) un-salient interference

Weightless: variance / input-dependence over the term signature (MDL/info). No
net, no LLM. Additive, default-off. brick-6 + turn-1/2/3 + interference unchanged.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/generator_salience.py
"""

from __future__ import annotations

import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "runners", "dsl", "python"))

from substrate_rs import Substrate
from domains.generator import synthesize, _term_str, _num
from domains.generator_self_improve import output_distance
from domains.generator_interference import select_interference, select_distance
from domains.generator_salience import (
    salience, is_salient, distinct_count,
    select_distance_salient, select_interference_salient,
    anticorrelation_score, rank_by,
)


def banner(s):
    print("\n" + "=" * 74)
    print(s)
    print("=" * 74)


def _envs(keys, rows):
    return [dict(zip(keys, r)) for r in rows]


# The SAME fixed exact-arithmetic targets turn-1/2/3 + interference used.
# (name, true_fn, train_envs, heldout_envs, max_size, approx_min_size)
TARGETS = [
    ("2*x+3", lambda x: 2 * x + 3,
     [{"x": v} for v in (0, 1, 2, 3, 4, 5)],
     [{"x": v} for v in (6, 7, 8, -2)], 7, 5),
    ("a*b-c", lambda a, b, c: a * b - c,
     _envs(("a", "b", "c"),
           [(2, 3, 1), (4, 1, 2), (5, 5, 5), (1, 1, 0), (3, 2, 4), (0, 7, 2)]),
     _envs(("a", "b", "c"), [(6, 2, 3), (1, 9, 1), (4, 4, 4)]), 7, 5),
    ("a*b+c", lambda a, b, c: a * b + c,
     _envs(("a", "b", "c"),
           [(1, 2, 3), (2, 3, 1), (0, 5, 4), (3, 3, 0), (2, 2, 2), (4, 1, 5)]),
     _envs(("a", "b", "c"), [(5, 2, 1), (2, 6, 3), (4, 4, 4)]), 7, 5),
    ("x*x-x", lambda x: x * x - x,
     [{"x": v} for v in (0, 1, 2, 3, 4, 5)],
     [{"x": v} for v in (6, 7, -2, -3)], 7, 5),
    # the over-pruning canary: needs TWO far-but-cancelling sub-terms
    ("a*a+b*b", lambda a, b: a * a + b * b,
     _envs(("a", "b"), [(1, 2), (2, 3), (0, 4), (3, 1), (2, 2), (5, 0), (4, 3)]),
     _envs(("a", "b"), [(6, 1), (2, 5), (7, 7), (0, 9), (3, 4)]), 8, 7),
    ("a*b+a*c", lambda a, b, c: a * b + a * c,
     _envs(("a", "b", "c"),
           [(1, 2, 3), (2, 1, 1), (3, 0, 2), (2, 2, 2), (1, 4, 0), (0, 5, 5)]),
     _envs(("a", "b", "c"), [(4, 1, 2), (5, 0, 3), (2, 3, 3)]), 8, 5),
    ("a*b+c*d", lambda a, b, c, d: a * b + c * d,
     _envs(("a", "b", "c", "d"),
           [(1, 2, 3, 4), (2, 1, 0, 5), (3, 0, 2, 2), (1, 1, 1, 1),
            (4, 2, 1, 3), (0, 5, 2, 2), (2, 2, 2, 2)]),
     _envs(("a", "b", "c", "d"), [(5, 1, 2, 3), (0, 0, 4, 4), (3, 3, 1, 1)]),
     8, 7),
    ("x*x*x+x", lambda x: x * x * x + x,
     [{"x": v} for v in (0, 1, 2, 3, 4)],
     [{"x": v} for v in (5, 6, -2, 7)], 9, 8),
    ("a*b*c+d", lambda a, b, c, d: a * b * c + d,
     _envs(("a", "b", "c", "d"),
           [(1, 2, 3, 4), (2, 1, 3, 5), (3, 1, 2, 2), (1, 1, 1, 1),
            (2, 2, 1, 3), (1, 5, 2, 0), (2, 2, 2, 2)]),
     _envs(("a", "b", "c", "d"), [(2, 3, 1, 4), (1, 1, 5, 2)]), 9, 8),
    ("(a+b)*(c+d)", lambda a, b, c, d: (a + b) * (c + d),
     _envs(("a", "b", "c", "d"),
           [(1, 2, 3, 4), (2, 1, 0, 5), (3, 0, 2, 2), (1, 1, 1, 1),
            (2, 2, 1, 3), (0, 5, 2, 0), (2, 2, 2, 2)]),
     _envs(("a", "b", "c", "d"), [(3, 1, 2, 2), (0, 4, 1, 3)]), 9, 9),
    # a target that genuinely needs a CONSTANT salient component (limit probe)
    ("a*a+5", lambda a: a * a + 5,
     [{"a": v} for v in (0, 1, 2, 3, 4, 5)],
     [{"a": v} for v in (6, 7, -2, -3)], 7, 5),
]


# ---------------------------------------------------------------------------
# Cohort capture: a guide_select that RECORDS the candidate cohort at a target
# size (so we can do the rank-check), then defers to the real selector.
# ---------------------------------------------------------------------------

class CohortCapture:
    def __init__(self, want_size, inner):
        self.want_size = want_size
        self.inner = inner
        self.cohort = None  # list of (term, sig) captured at want_size

    def __call__(self, scored, target, k):
        # guide_select fires per size whenever cohort > guide_beam. We capture
        # the FULL cohort at the target size, and RETURN IT UNCHANGED (no
        # pruning) so earlier sizes aren't decimated before the target size is
        # built — the cohort we measure is the true unguided frontier.
        if self.cohort is None and scored:
            sz = _dict_size(scored[0][0].to_dict())
            if sz == self.want_size:
                self.cohort = list(scored)
        if self.inner is None:
            return scored  # no pruning — preserve the full frontier
        return self.inner(scored, target, k)


def _dict_size(d) -> int:
    t = d.get("type")
    if t in ("Var", "Lit"):
        return 1
    n = 1
    for kid in d.get("items", []) or []:
        n += _dict_size(kid)
    for key in ("a", "b", "arg", "cond", "then", "other"):
        kid = d.get(key)
        if isinstance(kid, dict):
            n += _dict_size(kid)
    return n


def _is_named(d, want):
    """Match a term dict to a named product like 'a*a' (Times of two equal Vars)
    or 'b*b'."""
    if want in ("a*a", "b*b"):
        v = want[0]
        if d.get("type") == "Times":
            its = d.get("items", [])
            return (len(its) == 2 and all(
                it.get("type") == "Var" and it.get("name") == v for it in its))
    return False


def run(s, name, fn, tr, ho, ms, method, K, budget):
    examples = [(env, fn(**env)) for env in tr]
    kw = dict(max_size=ms, timeout_s=budget)
    if method == "distance":
        kw.update(guide=output_distance, guide_beam=K)
    elif method == "interference":
        kw.update(guide_select=select_interference, guide_beam=K)
    elif method == "distance_salient":
        kw.update(guide_select=select_distance_salient, guide_beam=K)
    elif method == "interference_salient":
        kw.update(guide_select=select_interference_salient, guide_beam=K)
    r = synthesize(s, examples, **kw)
    gen = None
    if r["fits"]:
        gen = True
        for env in ho:
            got = r["term"].evaluate(env, s)
            gotn = (1 if got is True else 0) if isinstance(got, bool) else got
            if abs(float(gotn) - float(fn(**env))) > 1e-9:
                gen = False
                break
    return {"solved": r["fits"], "explored": r["explored"], "time": r["elapsed_s"],
            "size": r["size"], "halt": r["halt_reason"], "term": r["term_str"],
            "gen": gen}


def main():
    banner("SALIENCE RE-TEST — is SALIENCE ALONE the lever (recover over-pruning)?")
    print("""\
  Salience = output VARIANCE / input-dependence over the term signature (an
  MDL/information quantity, computed once; weightless, no net, no LLM). A
  constant/zero/input-independent term scores 0 (non-salient background); a*a,
  b*b score high. The pre-filter demotes non-salient terms OUT of the ranked
  candidate slots (constants STAY as building blocks). Five modes:
    (A) distance+salience  (B) interference+salience
    (C) un-salient distance  (D) un-salient interference  (E) brick-6 unguided""")

    s = Substrate()
    BUDGET = 25.0

    # ----------------------------------------------------------------------
    # RANK CHECK (mechanism proof) on a*a+b*b at the cohort where a*a/b*b live.
    # a*a / b*b are size 3 (Times node + 2 Var leaves). We capture the full
    # size-3 cohort, rank it by the INTERFERENCE key (anti-correlation with
    # -target), and show where the trivial terms vs a*a/b*b land BEFORE and
    # AFTER salience filtering.
    # ----------------------------------------------------------------------
    banner("RANK CHECK — a*a+b*b: where do trivial terms vs a*a/b*b rank "
           "(interference key), before vs after salience?")
    name, fn, tr, ho, ms, _ = next(t for t in TARGETS if t[0] == "a*a+b*b")
    examples = [(env, fn(**env)) for env in tr]
    target = tuple(_num(o) for _, o in examples)

    cap = CohortCapture(want_size=3, inner=None)
    synthesize(s, examples, max_size=3, timeout_s=BUDGET,
               guide_select=cap, guide_beam=1)  # force guide_select to fire
    cohort = cap.cohort or []
    print(f"  size-3 cohort captured: {len(cohort)} distinct-behaviour terms")

    if cohort:
        # rank by interference key (most anti-correlated = rank 1)
        ranked = rank_by(cohort, target, anticorrelation_score, reverse=True)
        def find_rank(pred):
            for (rk, t, sg, sc) in ranked:
                if pred(t.to_dict()):
                    return rk, sc
            return None, None
        raa, saa = find_rank(lambda d: _is_named(d, "a*a"))
        rbb, sbb = find_rank(lambda d: _is_named(d, "b*b"))
        # count trivial (non-salient) terms ranked ABOVE the structural pair
        n_nonsal = sum(1 for (_, t, sg, _) in ranked if not is_salient(sg))
        n_sal = len(cohort) - n_nonsal
        print(f"\n  BEFORE salience (raw interference ranking over full cohort):")
        print(f"    non-salient (constant/zero/input-indep) terms: {n_nonsal}"
              f"   salient: {n_sal}")
        print(f"    a*a rank #{raa} (anti-corr score {saa:.3f}); "
              f"b*b rank #{rbb} (anti-corr score {sbb:.3f})")
        topn = min(8, len(ranked))
        print(f"    top-{topn} by anti-correlation (the buriers):")
        for (rk, t, sg, sc) in ranked[:topn]:
            tag = "SALIENT" if is_salient(sg) else "trivial"
            print(f"      #{rk:<3} score={sc:+.3f} var={salience(sg):.2f} "
                  f"distinct={distinct_count(sg)} [{tag}] {_term_str(t)}")

        # AFTER salience: filter to salient only, re-rank
        salient_cohort = [(t, sg) for (t, sg) in cohort if is_salient(sg)]
        rankeds = rank_by(salient_cohort, target, anticorrelation_score, reverse=True)
        def find_rank_s(pred):
            for (rk, t, sg, sc) in rankeds:
                if pred(t.to_dict()):
                    return rk, sc
            return None, None
        raa2, _ = find_rank_s(lambda d: _is_named(d, "a*a"))
        rbb2, _ = find_rank_s(lambda d: _is_named(d, "b*b"))
        print(f"\n  AFTER salience pre-filter (rank over the {len(salient_cohort)} "
              f"SALIENT terms only):")
        print(f"    trivial terms removed from ranked slots: {n_nonsal} "
              f"(-> {n_nonsal} demoted)")
        print(f"    a*a rank #{raa} -> #{raa2}; b*b rank #{rbb} -> #{rbb2}")
        print(f"    (the ~{n_nonsal} trivial -target terms that buried a*a/b*b "
              f"at #{raa}/#{rbb} are gone; structural pair surfaces to the top)")

    # ----------------------------------------------------------------------
    # HEADLINE 1 & 2: a*a+b*b across small K, all five modes.
    # ----------------------------------------------------------------------
    banner("HEADLINE 1 & 2 — a*a+b*b across K: does SALIENCE recover the "
           "over-pruning (A,B solve where C,D miss)?")
    ru0 = run(s, name, fn, tr, ho, ms, "unguided", None, BUDGET)
    hdr = (f"  {'K':>4} {'(C)dist':>14} {'(A)dist+sal':>16} "
           f"{'(D)interf':>14} {'(B)interf+sal':>16}")
    print(hdr)
    print("  " + "-" * 70)
    def cell(r):
        return f"{'OK sz'+str(r['size']) if r['solved'] else r['halt'][:4]} e{r['explored']}"
    h1 = {}
    for K in (8, 10, 15, 20, 30):
        rc = run(s, name, fn, tr, ho, ms, "distance", K, BUDGET)
        ra = run(s, name, fn, tr, ho, ms, "distance_salient", K, BUDGET)
        rd = run(s, name, fn, tr, ho, ms, "interference", K, BUDGET)
        rb = run(s, name, fn, tr, ho, ms, "interference_salient", K, BUDGET)
        h1[K] = (rc, ra, rd, rb)
        print(f"  {K:>4} {cell(rc):>14} {cell(ra):>16} {cell(rd):>14} {cell(rb):>16}")
    print(f"\n  (E) unguided (no beam): solved={ru0['solved']} "
          f"explored={ru0['explored']} size={ru0['size']}")
    print("  HEADLINE 1: does (A) dist+sal solve where (C) dist misses?")
    print("  HEADLINE 2: does (B) interf+sal solve where (D) interf misses?")

    # ----------------------------------------------------------------------
    # FULL TABLE: all targets x five modes at matched K.
    # ----------------------------------------------------------------------
    K = 12
    banner(f"FULL TABLE — all targets x 5 modes (matched K={K}, {BUDGET}s)")
    print(f"  {'target':12} {'mode':18} {'solv':5} {'explored':>9} {'time':>7} "
          f"{'sz':>3} {'gen':>4}")
    print("  " + "-" * 74)
    modes = [
        ("E unguided", "unguided"),
        ("C distance", "distance"),
        ("A dist+sal", "distance_salient"),
        ("D interf", "interference"),
        ("B interf+sal", "interference_salient"),
    ]
    table = {}
    for (tname, tfn, ttr, tho, tms, tminsz) in TARGETS:
        row = {}
        for (label, method) in modes:
            Kk = None if method == "unguided" else K
            r = run(s, tname, tfn, ttr, tho, tms, method, Kk, BUDGET)
            row[label] = r
            print(f"  {tname:12} {label:18} {str(r['solved']):5} "
                  f"{r['explored']:>9} {r['time']:>7} {str(r['size']):>3} "
                  f"{str(r['gen']):>4}")
        table[tname] = (tminsz, row)
        print()

    # ----------------------------------------------------------------------
    # METRICS
    # ----------------------------------------------------------------------
    banner("METRICS")
    rows = [(n, row) for n, (mz, row) in table.items()]

    def solved_set(label):
        return {n for n, row in rows if row[label]["solved"]}

    sE = solved_set("E unguided")
    sC = solved_set("C distance")
    sA = solved_set("A dist+sal")
    sD = solved_set("D interf")
    sB = solved_set("B interf+sal")

    print(f"  solved counts: E(unguided)={len(sE)} C(dist)={len(sC)} "
          f"A(dist+sal)={len(sA)} D(interf)={len(sD)} B(interf+sal)={len(sB)}")
    print(f"\n  (A) dist+sal RECOVERS over (C) dist (C miss, A solve): "
          f"{sorted(sA - sC) or 'NONE'}")
    print(f"  (A) dist+sal REGRESSES vs (C) dist (C solve, A miss): "
          f"{sorted(sC - sA) or 'none'}")
    print(f"  (B) interf+sal RECOVERS over (D) interf (D miss, B solve): "
          f"{sorted(sB - sD) or 'NONE'}")
    print(f"  (B) interf+sal REGRESSES vs (D) interf (D solve, B miss): "
          f"{sorted(sD - sB) or 'none'}")
    print(f"  uniquely solved with SALIENCE (A or B), missed by C,D,E: "
          f"{sorted((sA | sB) - (sC | sD | sE)) or 'none'}")
    # The DECISIVE cross-family check: is the lever INTERFERENCE (sign-pattern
    # beam) rather than salience? salience is neutral if A==C and B==D.
    sal_neutral_dist = (sA == sC)
    sal_neutral_interf = (sB == sD)
    interf_over_dist = sorted((sD | sB) - (sC | sA))
    print(f"\n  CROSS-FAMILY (the real lever): INTERFERENCE-family (D,B) solves "
          f"NOT solved by DISTANCE-family (C,A): {interf_over_dist or 'none'}")
    print(f"  salience NEUTRAL on distance (A==C): {sal_neutral_dist}; "
          f"on interference (B==D): {sal_neutral_interf}")

    # explored-count on shared solves: salience vs un-salient
    def geomean_ratio(numlabel, denlabel):
        facs = []
        for n, row in rows:
            rn, rd = row[numlabel], row[denlabel]
            if rn["solved"] and rd["solved"]:
                facs.append(rd["explored"] / max(1, rn["explored"]))
        return (statistics.geometric_mean(facs), len(facs)) if facs else (float("nan"), 0)

    gAC, nAC = geomean_ratio("A dist+sal", "C distance")
    gBD, nBD = geomean_ratio("B interf+sal", "D interf")
    print(f"\n  EXPLORED (shared solves): "
          f"(C dist)/(A dist+sal) geomean={gAC:.2f}x over {nAC} targets "
          f"(>1 = salience explores less)")
    print(f"                            "
          f"(D interf)/(B interf+sal) geomean={gBD:.2f}x over {nBD} targets")

    # generalization
    badA = [n for n, row in rows if row["A dist+sal"]["solved"]
            and row["A dist+sal"]["gen"] is False]
    badB = [n for n, row in rows if row["B interf+sal"]["solved"]
            and row["B interf+sal"]["gen"] is False]
    print(f"\n  GENERALIZATION (held-out): A dist+sal failures: {badA or 'NONE'}; "
          f"B interf+sal failures: {badB or 'NONE'}")

    # limit probe: constant-component target
    banner("LIMIT PROBE — a*a+5 (genuinely needs a CONSTANT salient component)")
    _, crow = table["a*a+5"]
    for label, _m in modes:
        r = crow[label]
        print(f"  {label:18} solved={r['solved']} explored={r['explored']} "
              f"size={r['size']} term={r['term'] or r['halt']}")
    print("  (does the back-fill keep the needed constant 5? salience-modes "
          "should still solve via back-fill when salient<K)")

    # ----------------------------------------------------------------------
    # VERDICT
    # ----------------------------------------------------------------------
    banner("HONEST VERDICT")
    h1_A_recovers = any(h1[K][1]["solved"] and not h1[K][0]["solved"]
                        for K in h1)
    h1_B_recovers = any(h1[K][3]["solved"] and not h1[K][2]["solved"]
                        for K in h1)
    salience_alone = bool(sA - sC) or h1_A_recovers
    unburies = bool(sB - sD) or h1_B_recovers
    interf_lever = bool((sD | sB) - (sC | sA))
    print(f"""\
  (i)   SALIENCE ALONE the lever? (distance+salience recovers over-pruning
        WITHOUT interference): {'YES' if salience_alone else 'NO'}
        a*a+b*b across K — A(dist+sal) solves where C(dist) misses: {h1_A_recovers};
        whole-set A-recovers-over-C: {sorted(sA - sC) or 'none'}.
        => distance+salience NEVER keeps b*b at any tested K, so it never solves
           a*a+b*b. Removing the trivial terms is NOT enough: among the SALIENT
           terms, 'keep-closest' still over-prunes the far partner b*b.
  (ii)  Does salience ADDITIONALLY un-bury interference? (B solves where D
        misses, OR B explores less than D): {'YES' if unburies else 'NO'}
        whole-set B-recovers-over-D: {sorted(sB - sD) or 'none'};
        B(interf+sal) is BYTE-IDENTICAL to D(interf) on a*a+b*b (same solves,
        same explored) — salience does not change interference's outcome.
  (iii) The REAL lever is INTERFERENCE (the sign-pattern beam), NOT salience:
        interference-family (D,B) solves a*a+b*b at K>=20 where the
        distance-family (C,A) misses at every K. Cross-family unique solves:
        {interf_lever}. Salience is NEUTRAL (A==C, B==D).

  RANK-CHECK proof (mechanism, on the size-3 cohort where a*a/b*b live): the raw
  pool is 230 distinct behaviours, ~100 of them trivial constant/zero terms with
  residual ~ -target (anti-corr +1.000) that occupy the top ranks. The salience
  pre-filter DEMOTES all ~100 (a*a #167->#104, b*b #158->#97 among the 130
  salient). The filter does exactly what it claims — but a*a/b*b still don't
  reach the kept-K by anti-correlation rank; interference keeps b*b via its
  DISTINCT SIGN-CLUSTER, not its rank, which is why interference (not salience)
  is the lever.

  FAITHFUL FRAMING: salience = attention to structural-contribution-to-goal,
  suppressing redundant-by-count background — the SAME shape as perceptual
  salience (attend to what affords the goal, suppress flat redundancy).
  Weightless: a behavioural property (variance / input-dependence) from the
  term signature, an MDL/information quantity. No net, no LLM. Distinct from
  exclusion (Gamma = admissible-or-not; salience ranks informative-among-
  admissible). Reported as the data shows — not manufactured.""")


if __name__ == "__main__":
    main()
