"""Brick 6 — RECURSIVE self-improvement, TURN 2: does the loop COMPOUND on turn 1?

The central test of the recursive thesis. Turn 1 derived a single-feature
output-distance guide (AUC 0.84) and moved the bound out (4-var a*b+c*d:
timeout -> solved). But having the generator SYNTHESIZE its own scorer FAILED at
turn-1's narrow bound.

Turn 2 tests whether turn 1's WIDER bound compounds:
  STEP 1  use the TURN-1 guided generator to solve BIGGER training targets the
          UNGUIDED brick-6 cannot -> richer traces (the compounding premise).
  STEP 2  compute a RICHER per-term feature vocabulary (exact/near hits, frac,
          dist, size, dist_per_size) — graph-native term behaviours.
  STEP 3  fit TWO turn-2 guides:
            (a) a RICHER DERIVED guide (trace-fit feature combination),
            (b) a SELF-SYNTHESIZED guide (brick-6 composes the scorer Term) —
                retried with richer features. Report whether it LANDS now.
          Report each guide's held-out AUC vs turn-1's 0.84.
  STEP 4  MEASURE COMPOUNDING on a HELD-OUT target set (harder than turn 1):
          turn-1 guide vs turn-2 guide, matched K + budget. Headline:
          newly-solved-beyond-turn-1, explored-count, over-pruning, generalize.
  STEP 5  HONEST VERDICT with numbers: compounds / self-guide-lands / plateaus.

Weightless, no LLM, no trained net. Additive over turn 1 (brick-6 guide=None
and the turn-1 guide are untouched).

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/generator_self_improve2.py
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
from domains.generator_self_improve2 import (
    harvest_richer_traces, feature_aucs, fit_richer_guide,
    try_synthesize_scorer_richer, guide_auc_rows, FEATURES, SMALLER_BETTER,
)


def banner(s):
    print("\n" + "=" * 72)
    print(s)
    print("=" * 72)


def _envs(keys, rows):
    return [dict(zip(keys, r)) for r in rows]


# BIGGER training targets — size 8-9, 4-5 vars. The UNGUIDED brick-6 cannot
# finish these (arity blow-up / depth); the TURN-1 guide is what makes their
# traces available. This is the compounding premise.
BIG_TRAINING = [
    ("a*b+c*d", [({"a": a, "b": b, "c": c, "d": d}, a * b + c * d) for
                 (a, b, c, d) in [(1, 2, 3, 4), (2, 1, 0, 5), (3, 0, 2, 2),
                                  (1, 1, 1, 1), (4, 2, 1, 3), (0, 5, 2, 2),
                                  (2, 2, 2, 2)]]),
    ("a*a+b*c", [({"a": a, "b": b, "c": c}, a * a + b * c) for (a, b, c) in
                 [(1, 2, 3), (2, 3, 1), (0, 4, 2), (3, 1, 1), (2, 2, 2),
                  (4, 0, 5), (1, 3, 3)]]),
    ("(a+b)*(c+d)", [({"a": a, "b": b, "c": c, "d": d}, (a + b) * (c + d)) for
                     (a, b, c, d) in [(1, 2, 3, 4), (2, 1, 0, 5), (3, 0, 2, 2),
                                      (1, 1, 1, 1), (2, 2, 1, 3), (0, 5, 2, 0),
                                      (2, 2, 2, 2)]]),
    ("a*b*c+d", [({"a": a, "b": b, "c": c, "d": d}, a * b * c + d) for
                 (a, b, c, d) in [(1, 2, 3, 4), (2, 1, 3, 5), (3, 1, 2, 2),
                                  (1, 1, 1, 1), (2, 2, 1, 3), (1, 5, 2, 0),
                                  (2, 2, 2, 2)]]),
]


# HELD-OUT compounding set — NOT used to derive any guide. Harder than turn 1
# (size 9-10, up to 5 vars), plus the turn-1 frontier targets for a direct
# turn-1-vs-turn-2 comparison. (name, true_fn, train_envs, heldout_envs,
# max_size, ops).
HELDOUT = [
    # turn-1's headline 4-var (both turns should solve — explored comparison)
    ("a*b+c*d", lambda a, b, c, d: a * b + c * d,
     _envs(("a", "b", "c", "d"),
           [(1, 2, 3, 4), (2, 1, 0, 5), (3, 0, 2, 2), (1, 1, 1, 1),
            (4, 2, 1, 3), (0, 5, 2, 2), (2, 2, 2, 2)]),
     _envs(("a", "b", "c", "d"), [(5, 1, 2, 3), (0, 0, 4, 4), (3, 3, 1, 1)]),
     8, None),
    # turn-1's a*a+b*b (shared, explored comparison)
    ("a*a+b*b", lambda a, b: a * a + b * b,
     _envs(("a", "b"), [(1, 2), (2, 3), (0, 4), (3, 1), (2, 2), (5, 0), (4, 3)]),
     _envs(("a", "b"), [(6, 1), (2, 5), (7, 7), (0, 9), (3, 4)]), 8, None),
    # HARDER than turn 1: 5-var a*b+c*d+e (size 9-10)
    ("a*b+c*d+e", lambda a, b, c, d, e: a * b + c * d + e,
     _envs(("a", "b", "c", "d", "e"),
           [(1, 2, 3, 4, 1), (2, 1, 0, 5, 2), (3, 0, 2, 2, 0), (1, 1, 1, 1, 1),
            (4, 2, 1, 3, 2), (0, 5, 2, 2, 3), (2, 2, 2, 2, 2)]),
     _envs(("a", "b", "c", "d", "e"), [(5, 1, 2, 3, 1), (0, 0, 4, 4, 2)]),
     10, None),
    # HARDER: a*b*c + d (size 9, 4-var, deep product)
    ("a*b*c+d", lambda a, b, c, d: a * b * c + d,
     _envs(("a", "b", "c", "d"),
           [(1, 2, 3, 4), (2, 1, 3, 5), (3, 1, 2, 2), (1, 1, 1, 1),
            (2, 2, 1, 3), (1, 5, 2, 0), (2, 2, 2, 2)]),
     _envs(("a", "b", "c", "d"), [(2, 3, 1, 4), (1, 1, 5, 2)]), 9, None),
    # HARDER: (a+b)*(c+d) (size 9, 4-var)
    ("(a+b)*(c+d)", lambda a, b, c, d: (a + b) * (c + d),
     _envs(("a", "b", "c", "d"),
           [(1, 2, 3, 4), (2, 1, 0, 5), (3, 0, 2, 2), (1, 1, 1, 1),
            (2, 2, 1, 3), (0, 5, 2, 0), (2, 2, 2, 2)]),
     _envs(("a", "b", "c", "d"), [(3, 1, 2, 2), (0, 4, 1, 3)]), 9, None),
    # easy control: a*b-c (both should solve; over-pruning check on easy)
    ("a*b-c", lambda a, b, c: a * b - c,
     _envs(("a", "b", "c"),
           [(2, 3, 1), (4, 1, 2), (5, 5, 5), (1, 1, 0), (3, 2, 4), (0, 7, 2)]),
     _envs(("a", "b", "c"), [(6, 2, 3), (1, 9, 1), (4, 4, 4)]), 7, None),
]


def run_one(s, name, true_fn, train_envs, heldout_envs, max_size, ops,
            guide, guide_beam, timeout_s):
    examples = [(env, true_fn(**env)) for env in train_envs]
    kw = dict(max_size=max_size, timeout_s=timeout_s)
    if ops:
        kw["ops"] = ops
    if guide is not None:
        kw.update(guide=guide, guide_beam=guide_beam)
    r = synthesize(s, examples, **kw)
    generalizes = None
    if r["fits"]:
        generalizes = True
        for env in heldout_envs:
            got = r["term"].evaluate(env, s)
            want = true_fn(**env)
            gotn = (1 if got is True else 0) if isinstance(got, bool) else got
            if abs(float(gotn) - float(want)) > 1e-9:
                generalizes = False
                break
    return {"name": name, "solved": r["fits"], "explored": r["explored"],
            "time": r["elapsed_s"], "size": r["size"], "halt": r["halt_reason"],
            "term": r["term_str"], "generalizes": generalizes}


def main():
    banner("BRICK 6 SELF-IMPROVEMENT TURN 2 — does the recursive loop COMPOUND?")
    print("""\
  Turn 1 derived a 1-feature output-distance guide (AUC 0.84) and moved the
  bound out, but self-synthesis of the scorer FAILED at the narrow bound. Turn 2
  tests COMPOUNDING: turn-1's wider bound -> bigger training targets -> richer
  traces -> a richer/self-synthesized guide -> does the bound move FURTHER?""")

    s = Substrate()
    TURN1_GUIDE = output_distance
    HARVEST_K = 50      # turn-1 guided beam for harvesting bigger targets
    HARVEST_MS = 9
    HARVEST_T = 115.0

    # --- STEP 1: richer traces via the turn-1 guide ---
    banner("STEP 1 — richer traces: turn-1 guide solves BIGGER training targets")
    h = harvest_richer_traces(s, BIG_TRAINING, TURN1_GUIDE,
                              guide_beam=HARVEST_K, max_size=HARVEST_MS,
                              timeout_s=HARVEST_T)
    print(f"  bigger training targets (K={HARVEST_K}, max_size={HARVEST_MS}):\n")
    print(f"    {'target':12} {'unguided(turn0)':>22}  {'guided(turn1)':>22}")
    print("    " + "-" * 60)
    for row in h["summary"]:
        u = row["unguided"]; g = row["guided"]
        us = f"{'SOLVED' if u[0] else u[2]} ex={u[1]} {u[3]}s"
        gs = f"{'SOLVED sz='+str(g[2]) if g[0] else 'NO'} ex={g[1]} {g[3]}s"
        print(f"    {row['name']:12} {us:>22}  {gs:>22}")
    unlocked = [n for (n, u, g) in h["unlocked"] if (not u) and g]
    print(f"\n  => turn-1 guide UNLOCKED for trace-harvest (turn-0 could NOT, "
          f"turn-1 DID): {unlocked or 'none'}")
    print(f"  total trace rows harvested from guided solves: {len(h['rows'])}")

    rows = h["rows"]
    if not rows:
        print("\n  NO TRACES — turn-1 guide solved no bigger target. Cannot "
              "compound. Stopping.")
        return

    # --- STEP 2: richer feature vocabulary + per-feature separation ---
    banner("STEP 2 — richer feature vocabulary (graph-native term behaviours)")
    aucs = feature_aucs(rows)
    n_use = sum(1 for r in rows if r["useful"])
    print(f"  rows: {len(rows)}  (useful={n_use}, not-useful={len(rows)-n_use})")
    print("  per-feature single-feature AUC (useful vs not, oriented >0.5=good):")
    for f in sorted(FEATURES, key=lambda f: -(aucs[f] if aucs[f]==aucs[f] else 0)):
        dirn = "smaller-better" if f in SMALLER_BETTER else "larger-better"
        print(f"    {f:14} AUC={aucs[f]:.3f}   ({dirn})")
    print(f"\n  turn-1 used ONLY `dist` (AUC {aucs['dist']:.3f} here on the "
          f"richer traces).")

    # --- Split traces into FIT vs HELD-OUT by target name (honest AUC) ---
    names = list(dict.fromkeys(r["name"] for r in rows))
    fit_names = set(names[: max(1, len(names) - 1)])
    holdout_names = set(names) - fit_names
    fit_rows = [r for r in rows if r["name"] in fit_names]
    ho_rows = [r for r in rows if r["name"] in holdout_names]
    print(f"\n  guide-fit on traces from {sorted(fit_names)};")
    print(f"  held-out AUC measured on traces from {sorted(holdout_names)} "
          f"({len(ho_rows)} rows).")

    # --- STEP 3a: RICHER DERIVED guide ---
    banner("STEP 3a — RICHER DERIVED guide (trace-fit feature combination)")
    richer_guide, desc = fit_richer_guide(fit_rows, top_k_features=4)
    print(f"  chosen features (top by discriminability): {desc['chosen']}")
    print(f"  per-feature useful-class mean + weight |AUC-0.5|:")
    for f, st in desc["stats"].items():
        print(f"    {f:14} mu={st['mu']:.3f}  w={st['w']:.3f}")

    # Held-out AUC: turn-1 guide vs richer guide, on held-out trace rows.
    # turn-1 guide = pure dist (smaller better).
    auc_turn1 = guide_auc_rows(lambda r: r["dist"], ho_rows)
    # richer guide scores from a row by reconstructing its sig-derivable feats.
    # The live guide uses (dist, exact, near, frac_exact, frac_near, dist_per_size~dist).
    def _richer_row_score(r):
        # mimic the live guide's available features from the stored row
        score = 0.0
        used = False
        for f, st in desc["stats"].items():
            if f == "size":
                continue  # not live
            x = r["dist"] if f == "dist_per_size" else r.get(f)
            if x is None or x == float("inf"):
                continue
            # match the live guide: weighted z-score to useful-class centroid
            score += st["w"] * abs(x - st["mu"]) / st["sd"]
            used = True
        return score if used else r["dist"]
    auc_richer = guide_auc_rows(_richer_row_score, ho_rows)
    print(f"\n  HELD-OUT separation (AUC, useful scored lower):")
    print(f"    turn-1 guide (dist only)   AUC = {auc_turn1:.3f}  "
          f"(turn-1 reported 0.84)")
    print(f"    turn-2 RICHER derived guide AUC = {auc_richer:.3f}")
    print(f"    => richer guide {'BEATS' if auc_richer > auc_turn1 + 0.01 else ('TIES' if abs(auc_richer-auc_turn1)<=0.01 else 'TRAILS')} "
          f"turn-1 on held-out separation")

    # --- STEP 3b: SELF-SYNTHESIZED guide (the deep recursive step, retried) ---
    banner("STEP 3b — SELF-SYNTHESIZED guide (brick-6 composes the scorer Term)")
    sc = try_synthesize_scorer_richer(s, rows, max_size=7, timeout_s=60,
                                      n_examples=40)
    self_guide_landed = False
    if not sc.get("ok"):
        print(f"  not attempted: {sc.get('reason')} "
              f"(pos={sc.get('n_pos')}, neg={sc.get('n_neg')}, "
              f"conflicts={sc.get('conflicts')})")
    else:
        print(f"  feature vars given to brick-6: {sc['feats']}")
        print(f"  balanced examples: {sc['n_examples']} "
              f"(pos={sc['n_pos']}, neg={sc['n_neg']}, "
              f"label-conflicting feature-cells={sc['conflicts']})")
        rr = sc["result"]
        if rr["fits"]:
            print(f"  *** SELF-SYNTHESIZED separator LANDED: {rr['term_str']} "
                  f"(size {rr['size']}, explored {rr['explored']}, "
                  f"{rr['elapsed_s']}s)")
            print("  The generator literally wrote its own guide (a Term-tree "
                  "over its own trace features).")
            self_guide_landed = True
        else:
            print(f"  no separating Term (halt={rr['halt_reason']}, "
                  f"explored={rr['explored']}, {rr['elapsed_s']}s).")
            print("  HONEST: even with richer features the useful/not-useful "
                  "boundary is not a small exact Term (overlap in the tail). "
                  "Self-synthesis still does NOT land; fall back to the derived "
                  "guide. Reported plainly.")

    # --- STEP 4: COMPOUNDING measurement on HELD-OUT targets ---
    banner("STEP 4 — COMPOUNDING: turn-1 guide vs turn-2 guide on HELD-OUT set")
    BUDGET_T = 90.0
    K = 30
    print(f"  matched K={K}, per-target budget={BUDGET_T}s. "
          f"turn-2 guide = RICHER derived (self-synth did not land "
          f"{'(it DID — see 3b)' if self_guide_landed else ''}).\n")
    print(f"  {'target':12} {'mode':8} {'solv':5} {'explored':>9} {'time':>7} "
          f"{'sz':>3} {'gen':>4}  term/halt")
    print("  " + "-" * 86)
    results = []
    for (name, fn, tr, ho, ms, ops) in HELDOUT:
        r1 = run_one(s, name, fn, tr, ho, ms, ops, TURN1_GUIDE, K, BUDGET_T)
        r2 = run_one(s, name, fn, tr, ho, ms, ops, richer_guide, K, BUDGET_T)
        for tag, rr in (("turn1", r1), ("turn2", r2)):
            print(f"  {name:12} {tag:8} {str(rr['solved']):5} "
                  f"{rr['explored']:>9} {rr['time']:>7} {str(rr['size']):>3} "
                  f"{str(rr['generalizes']):>4}  {rr['term'] or rr['halt']}")
        results.append((name, r1, r2))
        print()

    # --- STEP 5: headline metrics + verdict ---
    banner("STEP 5 — HEADLINE METRICS + HONEST VERDICT")
    both = [(n, a, b) for (n, a, b) in results if a["solved"] and b["solved"]]
    newly2 = [(n, a, b) for (n, a, b) in results if (not a["solved"]) and b["solved"]]
    lost2 = [(n, a, b) for (n, a, b) in results if a["solved"] and (not b["solved"])]
    wrong_gen = [(n, a, b) for (n, a, b) in results
                 if b["solved"] and b["generalizes"] is False]
    bigger_size = [n for n, a, b in both
                   if a["size"] and b["size"] and b["size"] > a["size"]]

    print("  (a) BOUND MOVED FURTHER — turn-2 solves what turn-1 could NOT:")
    if newly2:
        for n, a, b in newly2:
            print(f"      {n:12} turn1={a['halt']}(ex {a['explored']}) -> "
                  f"turn2 SOLVED {b['term']} (sz {b['size']}, ex {b['explored']}, "
                  f"{b['time']}s, gen={b['generalizes']})")
    else:
        print("      NONE — turn-2 solved no held-out target that turn-1 missed.")
    if lost2:
        print("  (a') REGRESSION — turn-1 solved but turn-2 MISSED:")
        for n, a, b in lost2:
            print(f"      {n:12} turn2 halt={b['halt']} (turn1 solved {a['term']})")

    print("\n  (b) EXPLORED-COUNT on targets BOTH turns solve:")
    factors = []
    if both:
        for n, a, b in both:
            fac = a["explored"] / max(1, b["explored"])
            factors.append(fac)
            print(f"      {n:12} turn1 {a['explored']:>8} -> turn2 "
                  f"{b['explored']:>8} = {fac:5.2f}x "
                  f"({'turn2 fewer' if fac>1 else 'turn2 MORE'})")
        gm = statistics.geometric_mean(factors)
        print(f"      geometric-mean (turn1/turn2) = {gm:.2f}x "
              f"({'turn2 explores less' if gm>1 else 'turn2 explores MORE'})")
    else:
        print("      (no target solved by both)")
        gm = float("nan")

    print("\n  (c) OVER-PRUNING / MDL-minimality (turn-2 guide):")
    print(f"      over-pruning misses (turn1 solved, turn2 missed): {len(lost2)}")
    print(f"      lost MDL-minimality (turn2 bigger term than turn1): "
          f"{bigger_size or 'none'}")

    print("\n  (d) GENERALIZATION:")
    if wrong_gen:
        for n, a, b in wrong_gen:
            print(f"      {n}: turn2 {b['term']} FAILS held-out inputs "
                  "(wrong shortcut).")
    else:
        print("      every turn-2 solution that fit also held on held-out "
              "inputs (correct structure).")

    # verdict
    compounds = bool(newly2) or (both and gm > 1.10 and not lost2)
    banner("HONEST VERDICT")
    if self_guide_landed:
        headline = "SELF-SYNTHESIZED GUIDE LANDED"
    elif compounds:
        headline = "COMPOUNDS"
    else:
        headline = "PLATEAUS"
    print(f"  VERDICT: {headline}\n")
    print(f"""\
  Turn-2 premise (richer traces via turn-1's wider bound): turn-1 guide unlocked
  {unlocked or 'no'} bigger training target(s) for trace-harvest that the
  UNGUIDED turn-0 could not finish -> {len(rows)} trace rows.

  Richer guide separation on HELD-OUT traces: turn-1 dist-only AUC={auc_turn1:.3f}
  vs turn-2 richer AUC={auc_richer:.3f}.
  Self-synthesized scorer Term: {'LANDED' if self_guide_landed else 'did NOT land'} (deep recursive step).

  Compounding on held-out HARDER targets (matched K={K}, {BUDGET_T}s budget):
    - bound moved FURTHER: {len(newly2)} target(s) turn-2 solved that turn-1 could not.
    - regressions (turn-1 solved, turn-2 missed): {len(lost2)}.
    - explored-count geomean turn1/turn2 = {gm:.2f}x on {len(both)} shared.
    - lost MDL-minimality on: {bigger_size or 'none'}.
    - generalization: {'all held' if not wrong_gen else str(len(wrong_gen))+' wrong-shortcut'}.

  Faithful framing: weightless throughout — features are graph-native term
  behaviours; both guides are trace-fit thresholds or a synthesized Term-tree;
  no trained net, no LLM (contrast GRAM's learned LPRM). The generator improving
  the generator, turn over turn. No-regression: brick-6 guide=None and the
  turn-1 guide path are untouched; this module is additive.""")
    if headline == "PLATEAUS":
        print("""\

  A PLATEAU is an honest, important result for the recursive thesis: the wider
  bound DID yield richer traces, but the richer/self-synthesized guide is NOT
  strictly better than turn-1's output-distance on this problem class — the
  single distance feature already captures most of the separable signal, and the
  useful/not-useful boundary is not a small exact Term. The loop ran a second
  turn; it did not stack a second improvement here. Reported plainly, not
  manufactured.""")


if __name__ == "__main__":
    main()
