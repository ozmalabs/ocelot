"""Brick 6 — the DECISIVE falsifiable test of the steal-list: does SIGN-PHASE
INTERFERENCE pay on EXACT arithmetic synthesis (the reliable-feature regime the
derived law REQUIRES), or does it lose even there (interference-as-capability
buried across domains)?

THE LAW (from a concurrent recognition session): interference is a genuine
quantum process (Born |psi|^2, complex amplitudes); the STRUCTURAL prediction
CONFIRMED (order-effects, interference signatures) but the CAPABILITY claim DIED
on a NOISY cross-speaker task — interference AMPLIFIES unreliable features, so on
noise you average, not interfere. Derived law: interference pays where features
are RELIABLE, hurts where NOISY. Exact arithmetic synthesis = the reliable-
feature regime = the principled test, WITH the failure mode named in advance
(deep search -> ambiguous residuals -> 'noisy' -> interference should hurt).

Three methods at matched K/budget on the SAME fixed exact-arithmetic targets
turn-1/2/3 used:
  (i)   UNGUIDED brick-6 (guide=None).
  (ii)  DISTANCE guide  (turn-1 foil: keep K smallest |residual|).
  (iii) INTERFERENCE    (phase-diverse / sign-pattern beam: keep terms whose
        residuals are sign-complementary so far-but-cancelling partners survive).

HEADLINE — RECOVERY: at the small K where DISTANCE MISSES a*a+b*b (a needed
far-but-cancelling sub-term pruned), does INTERFERENCE recover it? That is the
crisp 'interference != distance and it pays' signal.

Then: explored-count, bound, the FAILURE-MODE boundary (where interference flips
to hurting as residuals get noisy/ambiguous with depth), generalization, verdict.

Weightless: signed residual sign-patterns + a beam rule. No complex amplitudes,
no net, no LLM. brick-6 + turn-1/2/3 untouched (additive, default-off).

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/generator_interference.py
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
from domains.generator import synthesize
from domains.generator_self_improve import output_distance
from domains.generator_interference import select_interference


def banner(s):
    print("\n" + "=" * 72)
    print(s)
    print("=" * 72)


def _envs(keys, rows):
    return [dict(zip(keys, r)) for r in rows]


# The SAME fixed exact-arithmetic target set turn-1/2/3 used, ordered by depth
# (arity / min-size) so the depth->noise failure-mode boundary is legible.
# (name, true_fn, train_envs, heldout_envs, max_size, approx_min_size)
TARGETS = [
    # --- shallow / reliable (min size 5-7) ---
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
    # --- the over-pruning canary: needs TWO far-but-cancelling sub-terms ---
    ("a*a+b*b", lambda a, b: a * a + b * b,
     _envs(("a", "b"), [(1, 2), (2, 3), (0, 4), (3, 1), (2, 2), (5, 0), (4, 3)]),
     _envs(("a", "b"), [(6, 1), (2, 5), (7, 7), (0, 9), (3, 4)]), 8, 7),
    ("a*b+a*c", lambda a, b, c: a * b + a * c,
     _envs(("a", "b", "c"),
           [(1, 2, 3), (2, 1, 1), (3, 0, 2), (2, 2, 2), (1, 4, 0), (0, 5, 5)]),
     _envs(("a", "b", "c"), [(4, 1, 2), (5, 0, 3), (2, 3, 3)]), 8, 5),
    # --- deeper / residuals get ambiguous (the predicted noisy regime) ---
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
    ("a*b+c*d+e", lambda a, b, c, d, e: a * b + c * d + e,
     _envs(("a", "b", "c", "d", "e"),
           [(1, 2, 3, 4, 1), (2, 1, 0, 5, 2), (3, 0, 2, 2, 0), (1, 1, 1, 1, 1),
            (4, 2, 1, 3, 2), (0, 5, 2, 2, 3), (2, 2, 2, 2, 2)]),
     _envs(("a", "b", "c", "d", "e"), [(5, 1, 2, 3, 1), (0, 0, 4, 4, 2)]),
     10, 9),
]


def run(s, name, fn, tr, ho, ms, method, K, budget):
    examples = [(env, fn(**env)) for env in tr]
    kw = dict(max_size=ms, timeout_s=budget)
    if method == "distance":
        kw.update(guide=output_distance, guide_beam=K)
    elif method == "interference":
        kw.update(guide_select=select_interference, guide_beam=K)
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
    banner("STEAL-LIST DECISIVE TEST — sign-phase INTERFERENCE on EXACT synthesis")
    print("""\
  Does sign-phase interference (keep far-but-cancelling residual-complementary
  terms) PAY on exact arithmetic — the reliable-feature regime the derived law
  requires — or lose even there? Three methods at matched K/budget. Failure mode
  named in advance: as depth grows, residuals get ambiguous -> interference
  should flip from helping to HURTING (the law's amplify-noise prediction).""")

    s = Substrate()
    BUDGET = 20.0

    # --- HEADLINE: the recovery test at the small K where distance MISSES ---
    banner("HEADLINE — RECOVERY: a*a+b*b across K (distance over-prunes the "
           "far-but-cancelling sub-terms a*a, b*b)")
    name, fn, tr, ho, ms, _ = next(t for t in TARGETS if t[0] == "a*a+b*b")
    print(f"  {'K':>4} {'unguided':>22} {'distance':>22} {'interference':>22}")
    print("  " + "-" * 74)
    ru0 = run(s, name, fn, tr, ho, ms, "unguided", None, BUDGET)
    for K in (8, 10, 15, 20, 30):
        rd = run(s, name, fn, tr, ho, ms, "distance", K, BUDGET)
        ri = run(s, name, fn, tr, ho, ms, "interference", K, BUDGET)
        def cell(r):
            return f"{'OK' if r['solved'] else r['halt'][:4]} ex={r['explored']}"
        print(f"  {K:>4} {'(K-free) '+cell(ru0):>22} {cell(rd):>22} {cell(ri):>22}")
    print(f"\n  unguided (no beam): solved={ru0['solved']} explored={ru0['explored']} "
          f"size={ru0['size']}")
    print("  RECOVERY = does interference SOLVE at a K where distance MISSES? "
          "(read the rows above)")

    # --- FULL TABLE: all targets, three methods, matched K ---
    K = 20
    banner(f"FULL TABLE — all targets x {{unguided, distance, interference}} "
           f"(matched K={K}, {BUDGET}s)")
    print(f"  {'target':12} {'method':12} {'solv':5} {'explored':>9} {'time':>7} "
          f"{'sz':>3} {'gen':>4}  term/halt")
    print("  " + "-" * 92)
    table = {}
    for (name, fn, tr, ho, ms, minsz) in TARGETS:
        row = {}
        for method in ("unguided", "distance", "interference"):
            Kk = None if method == "unguided" else K
            r = run(s, name, fn, tr, ho, ms, method, Kk, BUDGET)
            row[method] = r
            print(f"  {name:12} {method:12} {str(r['solved']):5} "
                  f"{r['explored']:>9} {r['time']:>7} {str(r['size']):>3} "
                  f"{str(r['gen']):>4}  {(r['term'] or r['halt'])[:34]}")
        table[name] = (minsz, row)
        print()

    # --- METRICS ---
    banner("METRICS")
    interf = [(n, row) for n, (mz, row) in table.items()]

    # recovery vs distance
    rec = [n for n, row in interf
           if (not row["distance"]["solved"]) and row["interference"]["solved"]]
    lost = [n for n, row in interf
            if row["distance"]["solved"] and (not row["interference"]["solved"])]
    bound = [n for n, row in interf
             if (not row["unguided"]["solved"]) and row["interference"]["solved"]]

    print("  (a) RECOVERY (distance MISSED, interference SOLVED): "
          f"{rec or 'NONE'}")
    print("  (a') REGRESSION (distance SOLVED, interference MISSED): "
          f"{lost or 'none'}")
    print("  (b) BOUND (unguided MISSED, interference SOLVED within budget): "
          f"{bound or 'none'}")

    # explored on shared solves: interference vs distance, vs unguided
    print("\n  (c) EXPLORED-COUNT on shared solves (interference vs distance):")
    facs_d, facs_u = [], []
    for n, row in interf:
        ri, rd, ru = row["interference"], row["distance"], row["unguided"]
        if ri["solved"] and rd["solved"]:
            f = rd["explored"] / max(1, ri["explored"])
            facs_d.append(f)
            tag = "interf fewer" if f > 1.02 else ("distance fewer" if f < 0.98 else "tie")
            print(f"      {n:12} distance {rd['explored']:>8} / interf "
                  f"{ri['explored']:>8} = {f:5.2f}x  ({tag})")
        if ri["solved"] and ru["solved"]:
            facs_u.append(ru["explored"] / max(1, ri["explored"]))
    if facs_d:
        print(f"      geomean distance/interf = "
              f"{statistics.geometric_mean(facs_d):.2f}x "
              f"(>1 = interference explores less)")
    if facs_u:
        print(f"      geomean unguided/interf = "
              f"{statistics.geometric_mean(facs_u):.2f}x")

    # --- THE FAILURE-MODE BOUNDARY: helped vs hurt by depth ---
    banner("FAILURE-MODE BOUNDARY — interference vs distance/unguided by DEPTH")
    print("  (the law's prediction: as residuals get ambiguous with depth, "
          "interference should flip from helping to HURTING)\n")
    print(f"  {'target':12} {'minsz':>5} {'i_solv':>6} {'d_solv':>6} {'u_solv':>6} "
          f"{'i_ex':>8} {'d_ex':>8} {'verdict':>16}")
    print("  " + "-" * 78)
    for n, (mz, row) in sorted(table.items(), key=lambda kv: kv[1][0]):
        ri, rd, ru = row["interference"], row["distance"], row["unguided"]
        if ri["solved"] and rd["solved"]:
            f = rd["explored"] / max(1, ri["explored"])
            v = "HELP" if f > 1.05 else ("HURT" if f < 0.95 else "tie")
        elif ri["solved"] and not rd["solved"]:
            v = "HELP(recovers)"
        elif rd["solved"] and not ri["solved"]:
            v = "HURT(loses)"
        else:
            v = "both-miss"
        print(f"  {n:12} {mz:>5} {str(ri['solved']):>6} {str(rd['solved']):>6} "
              f"{str(ru['solved']):>6} {ri['explored']:>8} {rd['explored']:>8} "
              f"{v:>16}")

    # --- generalization ---
    banner("GENERALIZATION (held-out inputs on every interference solve)")
    bad = [n for n, row in interf
           if row["interference"]["solved"] and row["interference"]["gen"] is False]
    print(f"  interference solutions that FAIL held-out inputs (wrong shortcut): "
          f"{bad or 'NONE — all held'}")

    # --- VERDICT ---
    banner("HONEST VERDICT")
    pays = bool(rec) and not lost
    print(f"""\
  RECOVERY (the crisp signal): interference recovered {rec or 'NOTHING'} that
  distance over-pruned; regressions vs distance: {lost or 'none'}.
  BOUND beyond unguided: {bound or 'none'}.
  EXPLORED vs distance (shared): geomean
  {statistics.geometric_mean(facs_d):.2f}x (>1 = interference explores less).

  VERDICT: {'INTERFERENCE PAYS on exact synthesis' if pays else 'INTERFERENCE DOES NOT PAY — buried across domains'}.

  FAITHFUL FRAMING: sign-phase interference is the Euclidean-frame residue of the
  complex phase the ear resolved — here, the SIGN-PATTERN/direction of the signed
  residual r(t)=t(x)-target, with a phase-diverse beam keeping sign-complementary
  partners. Weightless: residual patterns + a beam rule, no complex amplitudes,
  no net, no LLM. This tests the DERIVED LAW (interference pays on reliable
  features) in the one regime that meets its condition. Reported as the data
  shows — not manufactured.""")


if __name__ == "__main__":
    main()
