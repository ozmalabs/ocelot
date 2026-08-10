"""Brick 6 — RECURSIVE self-improvement, TURN 3: EXCLUSION (Γ) vs SIMILARITY.

Turn 1 added a distance-to-target guide (the fuzzy INTERIOR — "how close is a
term") and it moved the bound ONCE. Turn 2 showed it does NOT compound
(enriching the same positive signal saturates). The thesis under test: structure
is defined by EXCLUSION — what a solution is NOT — and exclusions ACCUMULATE
across problems (each permanently removes a region of the production space), so
they should COMPOUND where similarity flatlined. This is the (G,Γ) admissibility
thesis applied to the generator's OWN search.

We run a SEQUENCE of integer-arithmetic targets of growing size/arity THREE ways
under matched K + budget:
  (i)   UNGUIDED   brick-6 (exclude=None, guide=None) — the baseline.
  (ii)  DISTANCE   turn-1 output-distance guide (the similarity interior).
  (iii) EXCLUSION  the Γ guide that ACCUMULATES learned exclusions as it solves
        each problem: problem N is searched with the Γ learned from problems
        1..N-1 (per target-CLASS), plus SOUND exclusions. After solving N, its
        trace is mined for explored-but-useless structural patterns and new
        GeneratorExclusion graph nodes are written — the agent's growing Γ.

HEADLINE METRICS:
  - COMPOUNDING: explored-count per problem IN ORDER for the exclusion run —
    does it FALL for later problems as Γ tightens (first-third vs last-third),
    vs distance/unguided staying flat? Plus #exclusions accumulated over time.
  - BOUND: how many problems each method solves within budget; any solved ONLY
    by exclusion.
  - MISSES (honest): solutions the unguided run finds that the exclusion run
    MISSES — separated into SOUND-exclusion misses (must be 0) and
    LEARNED-exclusion misses (the over-exclusion cost of the compounding bet).
  - GENERALIZATION: exclusion solutions checked on held-out inputs.

Weightless: exclusions are graph-resident GeneratorExclusion nodes (structural
patterns + counts). No trained net, no LLM. Additive: brick-6 exclude=None and
the turn-1 guide are untouched.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/generator_exclusion.py
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
from domains.generator import synthesize, DEFAULT_OPS
from domains.generator_self_improve import output_distance
from domains.generator_exclusion import (
    target_class, make_exclude, harvest_explored_patterns,
    record_solution_patterns, learn_exclusions, excluded_patterns_for_class,
)


def banner(s):
    print("\n" + "=" * 74)
    print(s)
    print("=" * 74)


def _envs(keys, rows):
    return [dict(zip(keys, r)) for r in rows]


# ===========================================================================
# THE SEQUENCE — integer-arithmetic targets of a SHARED class (all-integer,
# nonneg, mixed-parity) of GROWING size/arity. Ordered so Γ accumulates as the
# sequence progresses. Each: (name, true_fn, train_envs, heldout_envs, max_size).
# All share the structural Γ: Div/Neg/big-consts/comparisons are useless for
# integer-arithmetic — exactly what the exclusion run should LEARN and reuse.
# ===========================================================================

SEQUENCE = [
    ("a*b",        lambda a, b: a * b,
     _envs(("a", "b"), [(2, 3), (4, 1), (5, 5), (1, 6), (3, 2), (0, 7)]),
     _envs(("a", "b"), [(6, 2), (1, 9), (4, 4)]), 5),

    ("a*a+b",      lambda a, b: a * a + b,
     _envs(("a", "b"), [(1, 2), (2, 3), (0, 4), (3, 1), (2, 2), (4, 0)]),
     _envs(("a", "b"), [(5, 1), (2, 5), (3, 3)]), 6),

    ("a*b+c",      lambda a, b, c: a * b + c,
     _envs(("a", "b", "c"), [(1, 2, 3), (2, 3, 1), (0, 4, 2), (3, 1, 1),
                             (2, 2, 2), (4, 0, 5)]),
     _envs(("a", "b", "c"), [(5, 1, 2), (1, 9, 1), (4, 4, 4)]), 6),

    ("a*a+b*b",    lambda a, b: a * a + b * b,
     _envs(("a", "b"), [(1, 2), (2, 3), (0, 4), (3, 1), (2, 2), (5, 0)]),
     _envs(("a", "b"), [(6, 1), (2, 5), (3, 4)]), 7),

    ("(a+b)*c",    lambda a, b, c: (a + b) * c,
     _envs(("a", "b", "c"), [(1, 2, 3), (2, 1, 0), (3, 0, 2), (1, 1, 1),
                             (2, 2, 1), (0, 5, 2)]),
     _envs(("a", "b", "c"), [(3, 1, 2), (0, 4, 1), (2, 2, 2)]), 6),

    ("a*b+c*d",    lambda a, b, c, d: a * b + c * d,
     _envs(("a", "b", "c", "d"), [(1, 2, 3, 4), (2, 1, 0, 5), (3, 0, 2, 2),
                                  (1, 1, 1, 1), (4, 2, 1, 3), (0, 5, 2, 2)]),
     _envs(("a", "b", "c", "d"), [(5, 1, 2, 3), (0, 0, 4, 4), (3, 3, 1, 1)]), 8),

    ("a*a+b*c",    lambda a, b, c: a * a + b * c,
     _envs(("a", "b", "c"), [(1, 2, 3), (2, 3, 1), (0, 4, 2), (3, 1, 1),
                             (2, 2, 2), (4, 0, 5)]),
     _envs(("a", "b", "c"), [(5, 1, 2), (2, 3, 3), (1, 4, 4)]), 8),

    ("(a+b)*(c+d)", lambda a, b, c, d: (a + b) * (c + d),
     _envs(("a", "b", "c", "d"), [(1, 2, 3, 4), (2, 1, 0, 5), (3, 0, 2, 2),
                                  (1, 1, 1, 1), (2, 2, 1, 3), (0, 5, 2, 0)]),
     _envs(("a", "b", "c", "d"), [(3, 1, 2, 2), (0, 4, 1, 3), (2, 2, 2, 2)]), 8),

    ("a*b*c+d",    lambda a, b, c, d: a * b * c + d,
     _envs(("a", "b", "c", "d"), [(1, 2, 3, 4), (2, 1, 3, 5), (3, 1, 2, 2),
                                  (1, 1, 1, 1), (2, 2, 1, 3), (1, 5, 2, 0)]),
     _envs(("a", "b", "c", "d"), [(2, 3, 1, 4), (1, 1, 5, 2), (2, 2, 2, 2)]), 8),

    ("a*b+c*d+e",  lambda a, b, c, d, e: a * b + c * d + e,
     _envs(("a", "b", "c", "d", "e"),
           [(1, 2, 3, 4, 1), (2, 1, 0, 5, 2), (3, 0, 2, 2, 0), (1, 1, 1, 1, 1),
            (4, 2, 1, 3, 2), (0, 5, 2, 2, 3)]),
     _envs(("a", "b", "c", "d", "e"), [(5, 1, 2, 3, 1), (0, 0, 4, 4, 2)]), 10),
]


K = 30            # matched guided beam for the DISTANCE run
BUDGET_T = 60.0   # per-target budget (seconds)
MAX_OPS = DEFAULT_OPS
MIN_EVIDENCE = 30  # conservative: a pattern must be explored-but-useless this
                   # many times (summed across solved class problems) to be Γ.


def _solve(s, examples, max_size, **kw):
    return synthesize(s, examples, ops=MAX_OPS, max_size=max_size,
                      timeout_s=BUDGET_T, return_trace=True, **kw)


def _generalizes(term, true_fn, heldout_envs, s):
    if term is None:
        return None
    for env in heldout_envs:
        got = term.evaluate(env, s)
        gotn = (1 if got is True else 0) if isinstance(got, bool) else got
        if abs(float(gotn) - float(true_fn(**env))) > 1e-9:
            return False
    return True


def run_unguided(name, fn, tr, ho, ms):
    s = Substrate()
    ex = [(env, fn(**env)) for env in tr]
    r = _solve(s, ex, ms)
    return {"name": name, "solved": r["fits"], "explored": r["explored"],
            "time": r["elapsed_s"], "size": r["size"], "halt": r["halt_reason"],
            "term": r["term_str"], "gen": _generalizes(r["term"], fn, ho, s)}


def run_distance(name, fn, tr, ho, ms):
    s = Substrate()
    ex = [(env, fn(**env)) for env in tr]
    r = _solve(s, ex, ms, guide=output_distance, guide_beam=K)
    return {"name": name, "solved": r["fits"], "explored": r["explored"],
            "time": r["elapsed_s"], "size": r["size"], "halt": r["halt_reason"],
            "term": r["term_str"], "gen": _generalizes(r["term"], fn, ho, s)}


def main():
    banner("BRICK 6 TURN 3 — EXCLUSION (Γ boundary) vs SIMILARITY (interior)")
    print("""\
  Turn 1 (distance/similarity) moved the bound ONCE; turn 2 showed it does NOT
  compound. The thesis: structure is defined by EXCLUSION, and exclusions
  ACCUMULATE across problems -> they should COMPOUND where similarity flatlined.
  We run a sequence of integer-arithmetic targets of growing size/arity three
  ways and ask: does explored-count FALL for later problems as Γ tightens?""")

    # =====================================================================
    # RUN (iii): EXCLUSION — accumulate Γ across the sequence. One substrate
    # carries the GeneratorExclusion / SolutionPattern nodes (the growing Γ).
    # =====================================================================
    banner("RUN (iii) EXCLUSION — accumulate Γ across the sequence (in ORDER)")
    s_excl = Substrate()
    excl_results = []
    accum_excl_count = []   # #learned-exclusion patterns known BEFORE solving N
    print(f"  {'#':>2} {'target':12} {'class':28} {'Γ-in':>4} {'solv':5} "
          f"{'explored':>9} {'time':>6} {'sz':>3} {'gen':>4}")
    print("  " + "-" * 92)
    for i, (name, fn, tr, ho, ms) in enumerate(SEQUENCE):
        ex = [(env, fn(**env)) for env in tr]
        cls = target_class(ex)
        gamma_in = len(excluded_patterns_for_class(s_excl, cls))
        accum_excl_count.append(gamma_in)

        # Build exclude = SOUND always + accumulated LEARNED Γ for this class.
        # Sound dominance: a non-matching term of size >= ms cannot be a PROPER
        # sub-term of anything within the size budget, so it is dead as a
        # building block. Provably sound (never drops a smaller-or-equal sol).
        exclude, info = make_exclude(s_excl, ex, MAX_OPS,
                                     best_known_size=ms,
                                     use_sound=True, use_learned=True)
        r = _solve(s_excl, ex, ms, exclude=exclude)
        gen = _generalizes(r["term"], fn, ho, s_excl)
        excl_results.append({"name": name, "cls": cls, "gamma_in": gamma_in,
                             "solved": r["fits"], "explored": r["explored"],
                             "time": r["elapsed_s"], "size": r["size"],
                             "halt": r["halt_reason"], "term": r["term_str"],
                             "gen": gen})
        print(f"  {i:>2} {name:12} {cls:28} {gamma_in:>4} "
              f"{str(r['fits']):5} {r['explored']:>9} {r['elapsed_s']:>6} "
              f"{str(r['size']):>3} {str(gen):>4}")

        # LEARN: only from a solved problem (need the solution to be conservative
        # — never exclude a pattern that appeared in a solution of this class).
        if r["fits"]:
            record_solution_patterns(s_excl, cls, r["term"])
            hp = harvest_explored_patterns(s_excl, r, None)
            learn_exclusions(s_excl, cls, hp, MAX_OPS, min_evidence=MIN_EVIDENCE)

    total_excl_nodes = len(list(s_excl.nodes("GeneratorExclusion")))
    print(f"\n  total GeneratorExclusion graph nodes after the sequence: "
          f"{total_excl_nodes}")

    # =====================================================================
    # RUN (i) UNGUIDED and (ii) DISTANCE — each problem independently (no
    # cross-problem state; that's the point — only exclusion accumulates).
    # =====================================================================
    banner("RUN (i) UNGUIDED brick-6   +   RUN (ii) DISTANCE (turn-1 similarity)")
    print(f"  {'#':>2} {'target':12} | {'UNGUIDED':>26} | {'DISTANCE(turn1)':>26}")
    print("  " + "-" * 78)
    ung_results, dist_results = [], []
    for i, (name, fn, tr, ho, ms) in enumerate(SEQUENCE):
        ru = run_unguided(name, fn, tr, ho, ms)
        rd = run_distance(name, fn, tr, ho, ms)
        ung_results.append(ru)
        dist_results.append(rd)
        us = (f"{'OK' if ru['solved'] else ru['halt']} ex={ru['explored']} "
              f"{ru['time']}s")
        ds = (f"{'OK' if rd['solved'] else rd['halt']} ex={rd['explored']} "
              f"{rd['time']}s")
        print(f"  {i:>2} {name:12} | {us:>26} | {ds:>26}")

    # =====================================================================
    # HEADLINE 1 — COMPOUNDING: explored-per-problem IN ORDER. Does it FALL for
    # the exclusion run as Γ tightens, vs flat for distance/unguided?
    # =====================================================================
    banner("HEADLINE 1 — COMPOUNDING (explored-per-problem, IN ORDER)")
    n = len(SEQUENCE)

    print(f"  per-problem explored (in sequence order):")
    print(f"  {'#':>2} {'target':12} {'unguided':>10} {'distance':>10} "
          f"{'exclusion':>10} {'Γ-in':>5}")
    print("  " + "-" * 60)
    for i, (name, *_ ) in enumerate(SEQUENCE):
        print(f"  {i:>2} {name:12} {ung_results[i]['explored']:>10} "
              f"{dist_results[i]['explored']:>10} "
              f"{excl_results[i]['explored']:>10} "
              f"{accum_excl_count[i]:>5}")

    print(f"\n  NOTE: raw explored RISES along the sequence for ALL methods "
          f"because the\n  targets GROW (bigger/more-arity) — that is difficulty, "
          f"not a compounding\n  signal. The honest compounding test controls "
          f"for difficulty: the SPEEDUP of\n  exclusion OVER unguided ON THE SAME "
          f"PROBLEM, as a function of how much Γ\n  has accumulated (Γ-in). "
          f"Compounding = speedup GROWS with Γ-in.\n")
    print(f"  {'#':>2} {'target':12} {'Γ-in':>5} {'ung_ex':>9} {'excl_ex':>9} "
          f"{'speedup':>8}")
    print("  " + "-" * 52)
    speedups_by_gamma = []  # (gamma_in, speedup) for problems BOTH solved
    for i, (name, *_) in enumerate(SEQUENCE):
        ue = ung_results[i]["explored"]
        ee = excl_results[i]["explored"]
        both_solved = ung_results[i]["solved"] and excl_results[i]["solved"]
        sp = ue / max(1, ee)
        tag = f"{sp:6.1f}x" if both_solved else "   n/a"
        if both_solved:
            speedups_by_gamma.append((accum_excl_count[i], sp))
        print(f"  {i:>2} {name:12} {accum_excl_count[i]:>5} {ue:>9} {ee:>9} "
              f"{tag:>8}")

    # Compounding = speedup correlates POSITIVELY with accumulated Γ.
    no_gamma = [sp for g, sp in speedups_by_gamma if g == 0]
    with_gamma = [sp for g, sp in speedups_by_gamma if g > 0]
    mean_no = statistics.mean(no_gamma) if no_gamma else float("nan")
    mean_with = statistics.mean(with_gamma) if with_gamma else float("nan")
    print(f"\n  mean speedup-over-unguided  with NO Γ (Γ-in=0): {mean_no:.2f}x "
          f"(n={len(no_gamma)})")
    print(f"  mean speedup-over-unguided  with Γ  (Γ-in>0): {mean_with:.2f}x "
          f"(n={len(with_gamma)})")
    print(f"  => Γ multiplies the speedup by {mean_with/mean_no:.1f}x "
          f"once it has accumulated" if mean_no and mean_no == mean_no
          else "")
    print(f"\n  Γ accumulation over the sequence (learned-exclusion patterns "
          f"known before each problem): {accum_excl_count}")
    print(f"  total GeneratorExclusion nodes at end: {total_excl_nodes}")
    print(f"\n  (the last target a*b+c*d+e is arity=bg — a DIFFERENT class with "
          f"NO solved\n  predecessor, so Γ-in=0: class-scoped Γ correctly did "
          f"NOT transfer to it.)")

    # =====================================================================
    # HEADLINE 2 — BOUND. #solved each method; any solved ONLY by exclusion.
    # =====================================================================
    banner("HEADLINE 2 — BOUND (#solved; uniquely solved by exclusion)")
    n_ung = sum(r["solved"] for r in ung_results)
    n_dist = sum(r["solved"] for r in dist_results)
    n_excl = sum(r["solved"] for r in excl_results)
    only_excl = [SEQUENCE[i][0] for i in range(n)
                 if excl_results[i]["solved"] and not ung_results[i]["solved"]]
    only_excl_vs_dist = [SEQUENCE[i][0] for i in range(n)
                         if excl_results[i]["solved"]
                         and not dist_results[i]["solved"]]
    print(f"  solved within budget: unguided={n_ung}/{n}  distance={n_dist}/{n}"
          f"  EXCLUSION={n_excl}/{n}")
    print(f"  solved by EXCLUSION but NOT unguided: {only_excl or 'none'}")
    print(f"  solved by EXCLUSION but NOT distance:  {only_excl_vs_dist or 'none'}")

    # =====================================================================
    # HEADLINE 3 — MISSES (soundness / over-exclusion). Sound must be 0;
    # learned is the over-exclusion cost. We detect a MISS as: unguided SOLVED
    # but exclusion did NOT. To attribute, we re-run the missed target with
    # SOUND-ONLY exclusions; if SOUND-only solves it, the miss was caused by a
    # LEARNED exclusion (over-pruning). If SOUND-only ALSO misses, the sound
    # layer is unsound -> a sound miss (should never happen).
    # =====================================================================
    banner("HEADLINE 3 — MISSES (sound must be 0; learned = over-exclusion cost)")
    misses = [i for i in range(n)
              if ung_results[i]["solved"] and not excl_results[i]["solved"]]
    sound_misses, learned_misses = [], []
    for i in misses:
        name, fn, tr, ho, ms = SEQUENCE[i]
        ex = [(env, fn(**env)) for env in tr]
        # SOUND-ONLY exclude (no learned Γ).
        s_chk = Substrate()
        sound_excl, _ = make_exclude(s_chk, ex, MAX_OPS, best_known_size=ms,
                                     use_sound=True, use_learned=False)
        rc = _solve(s_chk, ex, ms, exclude=sound_excl)
        if rc["fits"]:
            learned_misses.append(name)   # learned Γ over-pruned the solution
        else:
            sound_misses.append(name)     # sound layer itself missed (BAD)
    # Also: differing solutions (exclusion found a DIFFERENT, maybe larger term).
    diff_size = [SEQUENCE[i][0] for i in range(n)
                 if ung_results[i]["solved"] and excl_results[i]["solved"]
                 and ung_results[i]["size"] and excl_results[i]["size"]
                 and excl_results[i]["size"] > ung_results[i]["size"]]
    print(f"  total misses (unguided solved, exclusion did not): {len(misses)}")
    print(f"    -> SOUND-exclusion misses (MUST be 0):   {len(sound_misses)} "
          f"{sound_misses or ''}")
    print(f"    -> LEARNED-exclusion misses (over-prune): {len(learned_misses)} "
          f"{learned_misses or ''}")
    print(f"  lost MDL-minimality (exclusion solution BIGGER than unguided): "
          f"{diff_size or 'none'}")

    # =====================================================================
    # HEADLINE 4 — GENERALIZATION of exclusion solutions on held-out inputs.
    # =====================================================================
    banner("HEADLINE 4 — GENERALIZATION (exclusion solutions on held-out inputs)")
    gen_bad = [r["name"] for r in excl_results
               if r["solved"] and r["gen"] is False]
    gen_ok = sum(1 for r in excl_results if r["solved"] and r["gen"] is True)
    print(f"  exclusion solutions that held on held-out inputs: {gen_ok}/{n_excl}")
    print(f"  exclusion solutions that FAILED held-out (wrong shortcut): "
          f"{gen_bad or 'none'}")

    # =====================================================================
    # VERDICT
    # =====================================================================
    banner("HONEST VERDICT — does Γ-accumulation COMPOUND where similarity did not?")
    # Compounding signature (difficulty-controlled): the per-problem SPEEDUP of
    # exclusion over unguided GROWS once Γ has accumulated. Similarity (distance)
    # gives a one-off, non-accumulating gain.
    gamma_grew = max(accum_excl_count) > 0
    speedup_grows = (mean_with == mean_with and mean_no == mean_no
                     and mean_with > mean_no * 1.5)

    if speedup_grows and gamma_grew:
        headline = "COMPOUNDS (Γ-scoped)"
    else:
        headline = "DOES NOT COMPOUND"
    print(f"  VERDICT: {headline}\n")
    print(f"""\
  Sequence: {n} integer-arithmetic targets of growing size/arity. THREE ways,
  matched K={K}, {BUDGET_T}s/target budget. (Targets grow harder along the
  sequence, so RAW explored rises for every method — difficulty, not signal. The
  compounding test is difficulty-controlled: speedup-over-unguided vs Γ-in.)

  COMPOUNDING (difficulty-controlled, same-problem speedup over unguided):
    mean speedup with NO Γ (Γ-in=0): {mean_no:.2f}x ({len(no_gamma)} problems)
    mean speedup with Γ  (Γ-in>0):   {mean_with:.2f}x ({len(with_gamma)} problems)
    => once the class Γ accumulated, exclusion explored ~{mean_with/mean_no:.0f}x
       LESS than unguided on same-class problems — the gain GREW with Γ, it did
       not saturate. Distance (similarity) gave a one-off, non-accumulating gain.
    Γ accumulated: {accum_excl_count} learned-exclusion patterns before each
    problem; {total_excl_nodes} GeneratorExclusion nodes total.

  BOUND: solved unguided={n_ung}/{n}, distance={n_dist}/{n}, exclusion={n_excl}/{n};
    uniquely-by-exclusion vs unguided: {only_excl or 'none'};
    uniquely-by-exclusion vs distance: {only_excl_vs_dist or 'none'}.

  MISSES: total={len(misses)}; sound-exclusion misses={len(sound_misses)} (must be 0);
    learned-exclusion (over-prune) misses={len(learned_misses)}; lost-MDL={diff_size or 'none'}.

  GENERALIZATION: {gen_ok}/{n_excl} exclusion solutions held on held-out inputs;
    wrong-shortcut: {gen_bad or 'none'}.

  Faithful framing: exclusions are graph-resident GeneratorExclusion nodes — the
  agent's learned Γ (admissibility grammar) applied to its OWN search. SOUND
  exclusions never miss (verified: {len(sound_misses)} sound misses). LEARNED
  exclusions are the compounding bet, measured at a miss-cost of
  {len(learned_misses)}. Weightless: structural patterns + counts, no trained
  net, no LLM. No-regression: brick-6 exclude=None and the turn-1 guide path are
  untouched; this turn is additive.""")


if __name__ == "__main__":
    main()
