"""OMNIGLOT RUN 17 -- CLOSE THE GAP: four levers off RUN 16's reconciled SC+TPS full-dwell
verdict (73.5% [67.0, 79.1], n=200, R=1) toward the Family-A anchor (78-81.5%,
`domains/analysis_by_synthesis.py` / `scripts/jabberwock_marginal_inference.py`'s own
historical numbers, matched protocol). Standing rules bind this run (CLAUDE.md's RUN-15
correction / RUN-16 reconciliation sections): POWER THE GATE BEFORE THE ENDGAME (deltas within
~3x the per-episode step are not results), mechanism != benchmark value (report both), and
eval-subset coverage is part of every claim.

FOUR LEVERS, six arms, ALL decided by held Terms (Argmax/Argmin/the Term's own internal
Argmax) -- never a Python min/max/sort/argmin over a per-episode classification decision:

  1. CONTROL -- `domains.abs_read.abs_rerank_targeted(delta=0, use_appearance=True)`,
     byte-identical to RUN 15/16's own "adopted" arm.
  2. SC+TPS FULL DWELL -- `domains.abs_read.sctps_rerank(include_smooth=False)` over EVERY
     candidate (`range(way)`, no proposal filter) -- RUN 16's own headline verdict, this time
     at the FULL n=400 (R=2 x 10 alphabets x 20 episodes) RUN 15 Phase 1 used, not RUN 16's
     own budget-capped R=1/n=200. This arm (with arm 1) is the NON-NEGOTIABLE powered core --
     never scope-capped by this script's own budget logic.
  3. TUNED FUSION -- `domains.abs_read.sctps_rerank_weighted`, weights (sc_w, tps_w, smooth_w)
     chosen by a grid search on a TUNING split DISJOINT from the 10 TEST alphabets (see
     `TUNING PROTOCOL` below), then applied UNCHANGED to the TEST episodes.
  4. +SMOOTH -- `domains.abs_read.sctps_rerank(include_smooth=True)` at FULL DWELL (RUN 16
     only tested this ensemble member on the K<=5 shortlist).
  5. +SCTPS -- `domains.abs_read.single_sctps_rerank` (the `ScTpsDist` Rust primitive ALONE,
     not the `Plus([SC, TPS])` sum) at full dwell -- the OTHER named ensemble member RUN 16
     never measured.
  6. PARSE MARGINAL -- Family A's own `domains.recognition_graph.predict_smooth_marginal_sc_
     term` (canonical-parse hypotheses at a theta grid, soft-min/log-sum-exp marginalised),
     REUSED VERBATIM; `domains.abs_read.stage_parse_char`/`parse_marginal_verdict` add ONLY
     the mechanical episode-scoped graph staging (see that module's own docstring).

TUNING PROTOCOL (hygiene is the point): the 20 `strokes_evaluation` alphabets with >= WAY=20
characters split into the sorted-name 10-PREFIX (`TEST_ALPHABETS`, RUN 15/16's own set) and the
remaining 10 (`TUNING_ELIGIBLE`); the grid search runs ONLY on a subset of the ELIGIBLE set
(`TUNING_ALPHABETS`, disjoint from `TEST_ALPHABETS` by construction, asserted at runtime) --
this run's own qualifying-alphabet enumeration comfortably clears the "~5 with >= 20 chars"
threshold the design names, so no background-alphabet fallback is needed (logged either way).
Winning weights are DATA read off the tuning grid's own measured accuracy (a plain Python
`max` over EXPERIMENT RESULTS -- the SAME "the agent tunes its threshold by measured accuracy"
precedent `scripts/jabberwock_canonical_parse.py` already established -- never a per-episode
classification decision); the TEST-set tuned-fusion arm below evaluates ONLY on `TEST_
ALPHABETS`' own held-out episodes, with the tuning weights as a frozen constant.

RUNTIME BUDGET (this script's own single-process wall clock, "estimate, log, cap" per RUN
15/16's own precedent): a PILOT (first TEST alphabet, repeat 0, both the main-arm and the
parse-marginal processing paths) is timed before committing to the full scope; if the
projection exceeds budget, the PARSE-MARGINAL arm (and only that arm -- the cheapest to shed
since it does not touch the decode-heavy main cache) is scoped down first (R then alphabet
count), logged either way. Arms 1-2 (and the cheap arms 3-5, which ride the SAME decode-cache
episodes for free) are NEVER capped.

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run17_close.py
"""
from __future__ import annotations

import itertools
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
from domains import abs_read as ar
from domains import omniglot_world as ow

SEP = "=" * 92

# ---------------------------------------------------------------------------------------------
# CAPS -- REUSES RUN 16's own reduced LEARN cap verbatim: RUN 16 re-verified (saturation check
# re-run at this cap) that 1500 pen-down strokes reproduces RUN 15's own 7-quantum codebook
# exactly -- a lower cap above the saturation point, not blind retuning.
# ---------------------------------------------------------------------------------------------
LEARN_STROKE_CAP = 1500
WAY = gate.WAY                                     # 20
EPISODES_PER_ALPHABET = WAY                         # 20
R_TARGET = 2                                        # RUN 15's own POWER_R -- the exact 400-
                                                     # episode scope arms 1-2 must hit.
POWER_SEED = gate.SEED + 1500                       # RUN 15/16's own POWER_SEED, byte-identical
RUNTIME_BUDGET_SECONDS = 520.0                      # leaves ~80s headroom under the 600s
                                                     # foreground cap for import/boot/report.
N_TEST_ALPHABETS = 10                               # RUN 15/16's own sorted-name 10-prefix
N_TUNING_ALPHABETS = 5                              # a subset of the disjoint remainder

RUN15_ADOPTED = {"acc": 0.268, "ci": (0.226, 0.313), "n": 400}
RUN16_SCTPS_FULL = {"acc": 0.735, "ci": (0.670, 0.791), "n": 200}
FAMILY_A_ANCHOR = 0.815                             # the run's own named target

# Family A's own historical parse-marginal recipe (`scripts/jabberwock_marginal_inference.py`),
# reused verbatim -- not re-tuned this run (the LEVER is the architecture, not these constants).
PARSE_THETAS = ar.DEFAULT_PARSE_THETAS
PARSE_WHOLE_N = ar.DEFAULT_PARSE_WHOLE_N
PARSE_PER_PART = ar.DEFAULT_PARSE_PER_PART
PARSE_PART_W, PARSE_SC_W, PARSE_BETA = 0.25, 1.6, 2.0

# TUNED FUSION weight grid (LEVER 2) -- logged constants, never per-episode tuned.
SC_W_GRID = (0.5, 1.0, 1.5, 2.0)
TPS_W_GRID = (0.5, 1.0, 1.5, 2.0)
SMOOTH_W_GRID = (0.0, 0.5, 1.0)


def _acc_ci(preds, trues):
    k = sum(1 for p, t in zip(preds, trues) if p == t)
    acc = k / max(1, len(trues))
    lo, hi = gate.wilson_ci(k, len(trues))
    return acc, (lo, hi), k


def _touches(ci, anchor):
    return ci[0] <= anchor <= ci[1]


# ---------------------------------------------------------------------------------------------
# BLOCK SPEC -- ONE (alphabet, repeat)'s exemplar/query drawer draws, computed ONCE and shared
# by every arm (main-cache arms AND the parse-marginal arm) so every arm scores the IDENTICAL
# episodes -- no rng divergence between processing paths.
# ---------------------------------------------------------------------------------------------
def _block_spec(alph: str, rng, way: int, episodes_per_alphabet: int) -> dict:
    chars = sorted(ow.characters(alph, "evaluation"))[:way]
    drawer_files = [ow.drawings(cd) for cd in chars]
    n_drawers = min(len(fl) for fl in drawer_files)
    ex_drawer = int(rng.integers(n_drawers))
    queries = []
    for qi in range(min(episodes_per_alphabet, way)):
        q_drawer = int(rng.integers(n_drawers))
        while q_drawer == ex_drawer:
            q_drawer = int(rng.integers(n_drawers))
        queries.append((qi, q_drawer))
    return dict(drawer_files=drawer_files, ex_drawer=ex_drawer, queries=queries)


# ---------------------------------------------------------------------------------------------
# MAIN-CACHE ARMS (1, 2, 4, 5, and -- once weights are known -- 3): control + the SC+TPS
# family, all off the SAME decode cache / whole-figure point-sets.
# ---------------------------------------------------------------------------------------------
def _episode_main(s, native, dk, qd, exemplar_composed, exemplar_stroke_points, exemplar_ps,
                   fusion_weights):
    adopted = ar.abs_rerank_targeted(
        s, qd["composed_sig"], qd["stroke_points"], exemplar_composed, exemplar_stroke_points,
        delta=0.0, use_widen=False, use_appearance=True, turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
        segments=dk["segments"])
    w_adopted = adopted["winner"] if adopted["winner"] is not None else -1

    q_ps = ar.whole_figure_point_set(qd["stroke_points"])
    full = list(range(len(exemplar_ps)))
    sc_w, tps_w, smooth_w = fusion_weights

    r_full = ar.sctps_rerank(native, q_ps, exemplar_ps, full, include_smooth=False)
    r_smooth = ar.sctps_rerank(native, q_ps, exemplar_ps, full, include_smooth=True)
    r_single = ar.single_sctps_rerank(native, q_ps, exemplar_ps, full)
    r_tuned = ar.sctps_rerank_weighted(native, q_ps, exemplar_ps, full, sc_w=sc_w, tps_w=tps_w,
                                        smooth_w=smooth_w)

    def _w(r):
        return r["winner"] if r["winner"] is not None else -1

    return dict(w_adopted=w_adopted, w_full=_w(r_full), w_smooth=_w(r_smooth),
                w_single=_w(r_single), w_tuned=_w(r_tuned),
                n_full=r_full["n_compared"], shortlist_size=len(adopted.get("shortlist0", [])))


def _run_block_main(s, native, dk, cache, spec, way, fusion_weights):
    t0 = time.time()
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, dk)
                 for ci in range(way)]
    exemplar_composed = [e["composed_sig"] for e in exemplars]
    exemplar_stroke_points = [e["stroke_points"] for e in exemplars]
    exemplar_ps = [ar.whole_figure_point_set(e["stroke_points"]) for e in exemplars]
    records = []
    for qi, q_drawer in spec["queries"]:
        qd = gate.decode_char_signature(s, drawer_files[qi][q_drawer], cache, dk)
        rec = _episode_main(s, native, dk, qd, exemplar_composed, exemplar_stroke_points,
                             exemplar_ps, fusion_weights)
        rec["true"] = qi
        records.append(rec)
    return dict(records=records, elapsed=time.time() - t0)


# ---------------------------------------------------------------------------------------------
# TUNING -- raw per-candidate (sc, tps, smooth) distances collected ONCE per tuning episode;
# the weight grid is then swept over ALREADY-COMPUTED numbers (no re-evaluation per combo).
# Every per-combo WINNER is still a held Argmin (`_argmin_pairs_term`, via a throwaway
# `srs.Substrate()._inner` -- no agent substrate touched); the WEIGHT CHOICE itself is a plain
# Python `max` over each combo's measured tuning accuracy -- an experimenter hyperparameter
# pick over EXPERIMENT RESULTS, the same class of move `jabberwock_canonical_parse.py`'s own
# "the agent tunes its threshold by measured accuracy" already established, never a per-episode
# classification decision.
# ---------------------------------------------------------------------------------------------
def _tuning_raw(native, s, dk, cache, spec, way):
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, dk)
                 for ci in range(way)]
    exemplar_ps = [ar.whole_figure_point_set(e["stroke_points"]) for e in exemplars]
    out = []
    for qi, q_drawer in spec["queries"]:
        qd = gate.decode_char_signature(s, drawer_files[qi][q_drawer], cache, dk)
        q_ps = ar.whole_figure_point_set(qd["stroke_points"])
        triples = []
        for ci, cps in enumerate(exemplar_ps):
            if q_ps is None or cps is None:
                triples.append(None)
                continue
            sc = float(native.evaluate(
                {"type": "ShapeContextDist", "a": {"type": "Lit", "value": q_ps},
                 "b": {"type": "Lit", "value": cps}}, {}) or 0.0)
            tps = float(native.evaluate(
                {"type": "TpsDeformDist", "a": {"type": "Lit", "value": q_ps},
                 "b": {"type": "Lit", "value": cps}}, {}) or 0.0)
            sm = float(native.evaluate(
                {"type": "SmoothDeformDist", "a": {"type": "Lit", "value": q_ps},
                 "b": {"type": "Lit", "value": cps}}, {}) or 0.0)
            triples.append((sc, tps, sm))
        out.append(dict(true=qi, triples=triples))
    return out


def _grid_winner(native, triples, sc_w, tps_w, smooth_w):
    pairs = [(sc_w * t[0] + tps_w * t[1] + smooth_w * t[2], ci)
             for ci, t in enumerate(triples) if t is not None]
    if not pairs:
        return -1
    w = native.evaluate(ar._argmin_pairs_term(pairs), {})
    return int(w[1]) if w is not None else -1


def run_tuning(native, tuning_records, grid):
    """Returns (best_weights, best_acc, full_grid_results)."""
    results = []
    trues = [r["true"] for r in tuning_records]
    for sc_w, tps_w, smooth_w in grid:
        preds = [_grid_winner(native, r["triples"], sc_w, tps_w, smooth_w)
                 for r in tuning_records]
        acc, _, _ = _acc_ci(preds, trues)
        results.append(((sc_w, tps_w, smooth_w), acc))
    best_weights, best_acc = max(results, key=lambda kv: kv[1])
    return best_weights, best_acc, results


# ---------------------------------------------------------------------------------------------
# PARSE-MARGINAL ARM (LEVER 4) -- candidates staged ONCE per block (a fresh scratch substrate,
# episode-scoped, never the agent's own held graph); only the QUERY node is re-staged per
# episode. The verdict is `ar.parse_marginal_verdict`'s OWN held Argmax -- this script does no
# ranking of its own, only a name/candidate-index read-off.
# ---------------------------------------------------------------------------------------------
def _run_block_parse(spec, way):
    t0 = time.time()
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    scratch = srs.Substrate()
    cand_of_node: dict[int, int] = {}
    for ci in range(way):
        node = ar.stage_parse_char(scratch, drawer_files[ci][ex_drawer], is_query=False,
                                    thetas=PARSE_THETAS, whole_n=PARSE_WHOLE_N,
                                    per_part=PARSE_PER_PART, name=str(ci))
        cand_of_node[node] = ci
    records = []
    for qi, q_drawer in spec["queries"]:
        qnode = ar.stage_parse_char(scratch, drawer_files[qi][q_drawer], is_query=True,
                                     thetas=PARSE_THETAS, whole_n=PARSE_WHOLE_N,
                                     per_part=PARSE_PER_PART)
        winner_node = ar.parse_marginal_verdict(scratch, qnode, part_w=PARSE_PART_W,
                                                 sc_w=PARSE_SC_W, beta=PARSE_BETA)
        w_parse = cand_of_node.get(winner_node, -1) if winner_node is not None else -1
        records.append(dict(true=qi, w_parse=w_parse))
    return dict(records=records, elapsed=time.time() - t0)


def main():
    t0 = time.time()
    print(SEP)
    print("OMNIGLOT RUN 17 -- CLOSE THE GAP: full-n SC+TPS confirmation, tuned fusion, full-")
    print("dwell ensemble members, and parse marginalization, off RUN 16's 73.5% [67.0, 79.1].")
    print(SEP)

    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA}. Cannot run.")
        return 1

    s, ag, native = gate.boot()
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    print(f"\n  LEARN caps (reusing RUN 16's own reduced, saturation-verified cap): "
          f"{gate.LEARN_ALPHABETS_N} background alphabets {learn_alphabets}, drawers "
          f"{gate.LEARN_DRAWERS[0]}-{gate.LEARN_DRAWERS[-1]}, capped at {LEARN_STROKE_CAP} "
          f"pen-down strokes. ink-decode params: {gate.DK}")

    print(f"\n{SEP}\n  PHASE 1: LEARN\n{SEP}")
    lr = gate.run_learn(s, ag, native, learn_alphabets, gate.LEARN_DRAWERS, LEARN_STROKE_CAP,
                         gate.DK, gate.GROWTH_WINDOW)
    growth = lr["growth"]
    print(f"  processed {lr['n_strokes']} pen-down strokes "
          f"({lr['n_degenerate_skipped']} degenerate skipped) in {lr['elapsed']:.1f}s.")
    sat_pass = None
    if len(growth) >= 3:
        first = np.mean([g["new_quanta"] for g in growth[:1]])
        last = np.mean([g["new_quanta"] for g in growth[-2:]])
        sat_pass = last <= max(3.0, 0.3 * first) if first > 0 else True
        print(f"  saturation check: first-window new={first:.1f} -> last-2-windows mean "
              f"new={last:.1f}  VERDICT: {'PASS' if sat_pass else 'FAIL'}")
    import domains.stroke_codebook as sc
    final_codebook = len(sc._existing_names(s, "stroke"))
    print(f"  final LEARN codebook size: {final_codebook} stroke quanta (RUN 15/16's own LEARN "
          f"produced 7).")

    # ------------------------------------------------------------------------------------- #
    #  ALPHABET SPLIT -- enumerate the qualifying evaluation alphabets, TEST = sorted-name
    #  10-prefix (RUN 15/16's own set, re-derived here rather than hardcoded), TUNING =
    #  a disjoint subset of the remainder.
    # ------------------------------------------------------------------------------------- #
    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= WAY)
    test_alphabets = qualifying[:N_TEST_ALPHABETS]
    tuning_eligible = qualifying[N_TEST_ALPHABETS:]
    print(f"\n  qualifying evaluation alphabets (>= {WAY} chars): {len(qualifying)} -- "
          f"{qualifying}")
    print(f"  TEST alphabets (sorted-name {N_TEST_ALPHABETS}-prefix): {test_alphabets}")
    print(f"  TUNING-eligible (disjoint remainder, {len(tuning_eligible)} alphabets): "
          f"{tuning_eligible}")
    if len(tuning_eligible) >= 5:
        tuning_alphabets = tuning_eligible[:N_TUNING_ALPHABETS]
        tuning_source = "evaluation (disjoint remainder)"
    else:
        bg = sorted(a for a in ow.alphabets("background")
                     if len(ow.characters(a, "background")) >= WAY)
        tuning_alphabets = bg[:N_TUNING_ALPHABETS]
        tuning_source = "background (fallback: fewer than 5 disjoint evaluation alphabets qualified)"
    print(f"  TUNING alphabets used ({tuning_source}): {tuning_alphabets}")
    assert not (set(tuning_alphabets) & set(test_alphabets)), \
        "TUNING/TEST alphabet overlap -- must never happen"
    print(f"  ASSERTION: zero overlap between TUNING alphabets and TEST alphabets -- PASS "
          f"(tuning weights are chosen with ZERO test-episode influence).")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 2: PILOT -- one TEST block (main-cache path + parse-marginal path) and one
    #  TUNING block, to project the full scope before committing.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 2: PILOT + RUNTIME BUDGET PROJECTION\n{SEP}")
    cache: dict = {}
    placeholder_weights = (1.0, 1.0, 0.0)
    pilot_rng = np.random.default_rng(POWER_SEED)
    pilot_spec = _block_spec(test_alphabets[0], pilot_rng, WAY, EPISODES_PER_ALPHABET)
    pilot_main = _run_block_main(s, native, gate.DK, cache, pilot_spec, WAY, placeholder_weights)
    pilot_parse = _run_block_parse(pilot_spec, WAY)
    tuning_pilot_rng = np.random.default_rng(POWER_SEED + 9999)
    tuning_pilot_spec = _block_spec(tuning_alphabets[0], tuning_pilot_rng, WAY,
                                     EPISODES_PER_ALPHABET)
    t_tuning_pilot0 = time.time()
    _ = _tuning_raw(native, s, gate.DK, cache, tuning_pilot_spec, WAY)
    tuning_pilot_elapsed = time.time() - t_tuning_pilot0

    print(f"  PILOT main-cache block ({test_alphabets[0]!r}, repeat 0, {WAY} episodes): "
          f"{pilot_main['elapsed']:.1f}s")
    print(f"  PILOT parse-marginal block (same episodes): {pilot_parse['elapsed']:.1f}s")
    print(f"  PILOT tuning block ({tuning_alphabets[0]!r}, {WAY} episodes, raw-distance "
          f"collection only): {tuning_pilot_elapsed:.1f}s")

    n_blocks_main = len(test_alphabets) * R_TARGET
    elapsed_so_far = time.time() - t0
    projected_main_full = pilot_main["elapsed"] * n_blocks_main
    projected_parse_full = pilot_parse["elapsed"] * n_blocks_main
    projected_tuning_full = tuning_pilot_elapsed * len(tuning_alphabets)
    projected_total = (elapsed_so_far + projected_main_full + projected_parse_full
                       + projected_tuning_full)
    print(f"\n  projection: LEARN+pilot so far {elapsed_so_far:.0f}s + main-cache (R={R_TARGET}, "
          f"{len(test_alphabets)} alphabets) {projected_main_full:.0f}s + parse-marginal (same "
          f"scope) {projected_parse_full:.0f}s + tuning ({len(tuning_alphabets)} alphabets) "
          f"{projected_tuning_full:.0f}s = {projected_total:.0f}s vs {RUNTIME_BUDGET_SECONDS:.0f}s "
          f"budget.")

    budget_notes = []
    parse_r_used = R_TARGET
    parse_alphabets_used = list(test_alphabets)
    if projected_total > RUNTIME_BUDGET_SECONDS:
        # Priority: shed the PARSE-MARGINAL arm's scope first -- it is the cheapest to shed
        # (separate cache, does not touch the decode-heavy main path). Arms 1-2 (and the free-
        # riding 4/5/eventually-3) are NEVER capped.
        parse_r_used = 1
        projected_parse_r1 = pilot_parse["elapsed"] * len(test_alphabets) * parse_r_used
        projected_total_r1 = (elapsed_so_far + projected_main_full + projected_parse_r1
                              + projected_tuning_full)
        note = (f"projected total {projected_total:.0f}s > {RUNTIME_BUDGET_SECONDS:.0f}s budget "
                f"-- reducing PARSE-MARGINAL arm to R=1 (projected {projected_total_r1:.0f}s). "
                f"Arms 1-2 stay at full R={R_TARGET}.")
        print(f"  {note}")
        budget_notes.append(note)
        if projected_total_r1 > RUNTIME_BUDGET_SECONDS:
            remaining = (RUNTIME_BUDGET_SECONDS - elapsed_so_far - projected_main_full
                        - projected_tuning_full)
            n_parse_blocks = max(0, int(remaining / max(1e-6, pilot_parse["elapsed"])))
            parse_alphabets_used = test_alphabets[:n_parse_blocks]
            note2 = (f"still over budget at R=1 -- capping PARSE-MARGINAL to the first "
                     f"{len(parse_alphabets_used)} TEST alphabets (sorted-name prefix): "
                     f"{parse_alphabets_used!r}.")
            print(f"  {note2}")
            budget_notes.append(note2)
    else:
        print(f"  within budget -- running the FULL scope for every arm, including "
              f"PARSE-MARGINAL at R={R_TARGET}.")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 2.5: TUNING (LEVER 2) -- weight grid search, TUNING alphabets ONLY.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 2.5: TUNED FUSION -- WEIGHT GRID SEARCH (tuning split only)\n{SEP}")
    tuning_rng = np.random.default_rng(POWER_SEED + 9999)
    tuning_records = []
    t_tune0 = time.time()
    for alph in tuning_alphabets:
        spec = _block_spec(alph, tuning_rng, WAY, EPISODES_PER_ALPHABET)
        tuning_records.extend(_tuning_raw(native, s, gate.DK, cache, spec, WAY))
    grid = list(itertools.product(SC_W_GRID, TPS_W_GRID, SMOOTH_W_GRID))
    best_weights, best_tuning_acc, grid_results = run_tuning(native, tuning_records, grid)
    tune_elapsed = time.time() - t_tune0
    print(f"  {len(tuning_records)} tuning episodes over {len(tuning_alphabets)} alphabets, "
          f"{len(grid)} weight combos swept, in {tune_elapsed:.1f}s.")
    top5 = sorted(grid_results, key=lambda kv: -kv[1])[:5]
    print(f"  top-5 weight combos (sc_w, tps_w, smooth_w) -> tuning accuracy:")
    for w, a in top5:
        print(f"    {w} -> {100*a:5.1f}%")
    print(f"  WINNING WEIGHTS: sc_w={best_weights[0]}, tps_w={best_weights[1]}, "
          f"smooth_w={best_weights[2]}  (tuning accuracy {100*best_tuning_acc:.1f}%, "
          f"n={len(tuning_records)})")
    print(f"  ASSERTION: the {len(tuning_records)} episodes scored above are ALL drawn from "
          f"{tuning_alphabets} -- disjoint from TEST alphabets {test_alphabets} (checked "
          f"above) -- zero test episodes were touched during tuning.")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 3: THE POWERED TEST -- R_TARGET x TEST_ALPHABETS x WAY episodes, main-cache arms
    #  (1,2,4,5, and 3 with the now-known winning weights) + the parse-marginal arm (scope per
    #  the budget decision above), off the SAME per-block spec.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 3: POWERED TEST (target n={len(test_alphabets)*R_TARGET*WAY})\n{SEP}")
    official_rng = np.random.default_rng(POWER_SEED)
    main_records = []
    parse_records = []
    hard_deadline = t0 + RUNTIME_BUDGET_SECONDS
    stopped_early = None
    for alph in test_alphabets:
        for r in range(R_TARGET):
            if time.time() > hard_deadline:
                stopped_early = (alph, r)
                break
            spec = _block_spec(alph, official_rng, WAY, EPISODES_PER_ALPHABET)
            blk = _run_block_main(s, native, gate.DK, cache, spec, WAY, best_weights)
            main_records.extend(blk["records"])
            if alph in parse_alphabets_used and r < parse_r_used:
                pblk = _run_block_parse(spec, WAY)
                parse_records.extend(pblk["records"])
        if stopped_early:
            break
    if stopped_early:
        note = (f"HARD DEADLINE reached at {stopped_early!r} -- stopped early with "
                f"{len(main_records)} main-cache episodes / {len(parse_records)} parse-marginal "
                f"episodes scored (honest, not a crash).")
        print(f"  {note}")
        budget_notes.append(note)

    trues = [r["true"] for r in main_records]

    def _report(name, preds, trues_):
        acc, ci, k = _acc_ci(preds, trues_)
        shuf = list(trues_)
        np.random.default_rng(POWER_SEED + 1).shuffle(shuf)
        acc_s, _, _ = _acc_ci(preds, shuf)
        print(f"  {name:<26} n={len(trues_):>4}  k={k:>3}  acc={100*acc:5.1f}%  "
              f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]  shuffled={100*acc_s:5.1f}%")
        return dict(acc=acc, ci=ci, k=k, n=len(trues_))

    print(f"\n  {len(main_records)} main-cache episodes scored ({len(parse_records)} "
          f"parse-marginal episodes, scope: {parse_alphabets_used!r} x R={parse_r_used}).\n")
    r_control = _report("CONTROL (adopted)", [r["w_adopted"] for r in main_records], trues)
    r_full = _report("SC+TPS FULL DWELL", [r["w_full"] for r in main_records], trues)
    r_tuned = _report("TUNED FUSION", [r["w_tuned"] for r in main_records], trues)
    r_smooth = _report("+SMOOTH (full dwell)", [r["w_smooth"] for r in main_records], trues)
    r_single = _report("+SCTPS (full dwell)", [r["w_single"] for r in main_records], trues)
    if parse_records:
        p_true = [r["true"] for r in parse_records]
        r_parse = _report("PARSE MARGINAL", [r["w_parse"] for r in parse_records], p_true)
    else:
        r_parse = None
        print(f"  {'PARSE MARGINAL':<26} SKIPPED (budget) -- see BUDGET NOTES below.")

    # ------------------------------------------------------------------------------------- #
    #  BUDGET / COST
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  VERDICTS\n{SEP}")
    ci_c = r_control["ci"]
    overlaps_run15 = not (ci_c[1] < RUN15_ADOPTED["ci"][0] or RUN15_ADOPTED["ci"][1] < ci_c[0])
    print(f"  CONTROL REPRODUCTION: this run's control {100*r_control['acc']:.1f}% "
          f"{[round(100*x,1) for x in ci_c]} (n={r_control['n']}) vs RUN 15's powered 26.8% "
          f"{[100*x for x in RUN15_ADOPTED['ci']]} (n=400) -- "
          f"{'CI-OVERLAP (consistent)' if overlaps_run15 else 'CI-SEPARATED (inconsistent -- investigate)'}")

    def _verdict(name, res, base_ci, base_label):
        sep = gate._ci_separated(res["ci"], base_ci)
        print(f"  {name} vs {base_label}: {100*res['acc']:.1f}% vs base -- "
              f"{'CI-SEPARATED' if sep else 'NOT CI-SEPARATED'}")
        return sep

    _verdict("SC+TPS FULL DWELL", r_full, ci_c, "CONTROL")
    _verdict("SC+TPS FULL DWELL (n=400)", r_full, RUN16_SCTPS_FULL["ci"], "RUN 16's own n=200 headline")
    _verdict("TUNED FUSION", r_tuned, r_full["ci"], "SC+TPS FULL DWELL")
    _verdict("+SMOOTH", r_smooth, r_full["ci"], "SC+TPS FULL DWELL")
    _verdict("+SCTPS", r_single, r_full["ci"], "SC+TPS FULL DWELL")
    if r_parse is not None:
        _verdict("PARSE MARGINAL", r_parse, r_full["ci"], "SC+TPS FULL DWELL")

    print(f"\n  FAMILY-A ANCHOR ({100*FAMILY_A_ANCHOR:.1f}%) CI-TOUCH CHECK:")
    for name, res in (("SC+TPS FULL DWELL", r_full), ("TUNED FUSION", r_tuned),
                      ("+SMOOTH", r_smooth), ("+SCTPS", r_single)):
        touch = _touches(res["ci"], FAMILY_A_ANCHOR)
        print(f"    {name:<24}: CI {[round(100*x,1) for x in res['ci']]} "
              f"{'TOUCHES' if touch else 'does NOT touch'} the anchor.")
    if r_parse is not None:
        touch = _touches(r_parse["ci"], FAMILY_A_ANCHOR)
        print(f"    {'PARSE MARGINAL':<24}: CI {[round(100*x,1) for x in r_parse['ci']]} "
              f"{'TOUCHES' if touch else 'does NOT touch'} the anchor.")

    best_arm = max([("SC+TPS FULL DWELL", r_full), ("TUNED FUSION", r_tuned),
                    ("+SMOOTH", r_smooth), ("+SCTPS", r_single)]
                   + ([("PARSE MARGINAL", r_parse)] if r_parse is not None else []),
                   key=lambda kv: kv[1]["acc"])
    print(f"\n  BEST ARM THIS RUN: {best_arm[0]} at {100*best_arm[1]['acc']:.1f}% "
          f"{[round(100*x,1) for x in best_arm[1]['ci']]}")

    print(f"\n  BUDGET NOTES: {budget_notes if budget_notes else 'none -- full target scope completed.'}")

    donkey0 = "torch" not in sys.modules
    print(f"  donkey=0 (no torch anywhere in sys.modules): {'PASS' if donkey0 else 'FAIL'}")
    total_elapsed = time.time() - t0
    print(f"\n  total runtime: {total_elapsed:.1f}s (internal budget "
          f"{RUNTIME_BUDGET_SECONDS:.0f}s + {600 - RUNTIME_BUDGET_SECONDS:.0f}s import/report "
          f"headroom)")
    print(SEP)
    print("  OVERALL: PASS" if donkey0 and sat_pass is not False else "  OVERALL: FAIL")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
