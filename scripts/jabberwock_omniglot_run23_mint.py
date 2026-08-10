"""OMNIGLOT RUN 23 -- CONTINUOUS-NOVELTY MINTING (the LEARN-side attack on the runs-19-22
identity-grain wall, commit 9762130f's own closing clause). Read FIRST: CLAUDE.md (the Rust-
agent-runtime rule this script obeys as a thin, mechanical world adapter), scratchpad/
HANDWRITING_DESIGN.md, `git show -s d46ac9b3 9762130f` (runs 21-22, the identity wall), and
`domains/ink_decode.py` / `domains/stroke_codebook.py`'s own "RUN 23" docstring sections (the
new `continuous_mint_or_note` mechanism + `decode_ink`'s `enable_continuous_mint` flag).

STANDING: four runs (19, 20, 21, 22) all diagnosed the SAME wall from four angles -- the earned
stroke-quantum vocabulary saturates at 7 top-level entries with ONE identity carrying
14,675/14,676 background observations at run 21's coarse grain, and 14,655/14,676 strokes on
ONE sub-fine key at run 22's finer grain (8 of the 10 "new" keys were 1-2-observation noise).
Every conditioning-side lever (token-refit, coarse spatial priors, fine spatial priors) hit this
SAME identity-grain ceiling. Run 22's own closing clause named the next lever explicitly: apply
run 16's own law ("continuous beats quantized for VERDICTS") to GROWTH instead of reading --
a stroke that RECOGNIZES at some tier (its quantized signature already matches an existing
quantum, so it can never mint through the discrete OOV ladder) but whose real-valued (DtwTo)
shape sits far from that identity's own continuous prototype MINTS a peer quantum anyway.
Matching/recognition are UNTOUCHED (run 5's law, restated in run 22's own commit message: "no
bin change anywhere") -- only the codebook's own VOCABULARY grows.

PHASE 1 (diagnostics FIRST, pre-registered, before any accuracy number): LEARN at
`LEARN_STROKE_CAP` (RUN 15's own REDUCED, saturation-verified cap -- 1500 pen-down strokes,
NOT the base gate's un-reduced 3000 constant; every run since 15 has reused this SAME 1500
value, `r17.LEARN_STROKE_CAP`) at each of `MINT_THRESHOLDS` (3 values, spanning aggressive to
conservative growth relative to `stroke_codebook.DEFAULT_DTW_THRESHOLD`'s own empirically-
calibrated 0.108/0.50 jitter/different-shape bands), `enable_continuous_mint=True`. Per
threshold: vocabulary size (top-level "stroke" `ShapeSignature` count, includes original +
continuous-mint peers), an OBSERVATION HISTOGRAM (the family-nearest-neighbour ASSIGNMENT every
`continuous_mint_or_note` call already computes -- read straight off `decode_ink`'s own
returned `"continuous"` list, no extra decode), the growth curve (per-100-stroke-window
codebook-size deltas, the SAME `run_learn`-style windowing every prior run's own saturation
check uses), and identity diversity (distinct assignment keys with >= `FINE_MIN_OBS`(=10)
observations -- `spatial_priors.FINE_MIN_OBS`'s own pre-registered bar, reused verbatim, and
`MIN_DISTINCT_FOR_PROCEED`(=20) -- `spatial_priors.MIN_DISTINCT_FINE_KEYS`'s own pre-registered
bar, reused verbatim).

THE PRE-REGISTERED BRANCH (decided BEFORE any accuracy number, per every prior run's own
discipline): PROCEED to phase 2 only if AT LEAST ONE swept threshold satisfies ALL FOUR --
(a) vocabulary >= 20 quanta; (b) non-degenerate observation histogram (no single quantum's
assignment share > 70% of all continuous-mint-eligible observations); (c) the growth curve
SATURATES (last-2-windows' mean new-quanta count <= max(3, 0.3 * first-window's), the SAME
saturation formula every prior run's own gate already uses -- a threshold so loose it never
flattens is REJECTED even if it clears (a)/(b)/(d)); (d) identity diversity >= 20 distinct
assignment keys with >= 10 observations each. If NO threshold clears all four: STOP, report
the honest table, and do NOT run phase 2 -- the conclusion is that continuous-novelty minting
cannot diversify this featureset's vocabulary either, and the next lever is richer PRIMITIVES
(a representation change), the creator's call.

PHASE 2 (only on a phase-1 pass, best threshold): the powered gate -- (i) the parse-marginal
CONTROL (must reproduce ~79-80.5%; this arm uses NO codebook at all, `ar.stage_parse_char` /
`ar.parse_marginal_verdict` never reference `ink_decode`/`stroke_codebook` -- asserted here
structurally, not just empirically, since it is a STRUCTURAL invariance, not an accident of
this run's particular vocabulary); (ii) the re-armed FINE-KEYED spatial prior arm (run 22's own
`spatial_priors.mine_spatial_priors_fine`/`arrangement_log_prior_fine`/
`spatial_prior_marginal_rerank_fine` machinery, unchanged, now fed by the richer vocabulary this
run grew); (iii) coverage@5 / proposal-recall (`ar.abs_rerank`'s own `top_k` field) -- the
earned proposal layer should improve with a richer codebook; reported even if the accuracy arms
stay budget-limited.

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /usr/bin/python3 scripts/jabberwock_omniglot_run23_mint.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run17_close as r17
from domains import abs_read as ar
from domains import ink_decode as ink
from domains import omniglot_world as ow
from domains import spatial_priors as sp
from domains import stroke_codebook as sc

SEP = "=" * 92

# ---------------------------------------------------------------------------------------------
# CAPS -- logged verbatim, no silent truncation. `LEARN_STROKE_CAP` is RUN 15's own REDUCED,
# saturation-verified cap (1500), reused by EVERY run in this arc since -- NOT the base gate's
# un-reduced 3000 constant (`gate.LEARN_STROKE_CAP`), which no run has actually reached (the 5
# LEARN alphabets x 14 drawers simply don't carry 3000 pen-down strokes at this DK).
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = gate.LEARN_ALPHABETS_N
LEARN_DRAWERS = gate.LEARN_DRAWERS
LEARN_STROKE_CAP = r17.LEARN_STROKE_CAP
GROWTH_WINDOW = gate.GROWTH_WINDOW
DK = gate.DK

WAY = r17.WAY
EPISODES_PER_ALPHABET = r17.EPISODES_PER_ALPHABET
R_TARGET = r17.R_TARGET
POWER_SEED = r17.POWER_SEED
N_TEST_ALPHABETS = r17.N_TEST_ALPHABETS
FAMILY_A_ANCHOR = r17.FAMILY_A_ANCHOR
RUN17B_PARSE_MARGINAL = {"acc": 0.805, "ci": (0.763, 0.841), "n": 400}   # results/
                                                                          # omniglot_gate_run17_
                                                                          # close.log's own
                                                                          # RUN 17b completion.
RUN22_IDENTITY_WALL = {"n_fine_keys_with_min_obs": 1, "min_distinct_required": 20}  # results/
                                                                          # omniglot_gate_run22_
                                                                          # finepriors.log.

# THE SWEEP -- 3 values (breadth capped per the launch instructions: "cap the sweep breadth,
# not phase-1 itself"), spanning aggressive to conservative relative to
# `stroke_codebook.DEFAULT_DTW_THRESHOLD`(=0.15)'s own empirically-calibrated bands (realistic
# per-point jitter ~0.108, a genuinely different shape class ~0.50): 0.15 mints readily (even
# jitter-scale divergence from a family's CURRENT nearest member mints), 0.40 mints only for
# clearly distinct continuous shapes.
MINT_THRESHOLDS = (0.15, 0.25, 0.40)

# THE PRE-REGISTERED BRANCH BARS (reused verbatim from run 22's own pre-registered thresholds
# where they name the SAME concept -- `spatial_priors.FINE_MIN_OBS`/`MIN_DISTINCT_FINE_KEYS`;
# the growth-saturation formula is every prior run's own `sat_pass` check, restated once here
# as a function so this run's own phase-1 loop can call it per threshold).
MIN_OBS_FOR_TRUSTED_KEY = sp.FINE_MIN_OBS                  # 10
MIN_DISTINCT_FOR_PROCEED = sp.MIN_DISTINCT_FINE_KEYS       # 20
MIN_VOCAB_FOR_PROCEED = 20
MAX_DOMINANT_SHARE = 0.70

RUNTIME_BUDGET_SECONDS = 520.0
PHASE1_BUDGET_SECONDS = 420.0   # leaves headroom for phase 2 (mining + accuracy) under the
                                # foreground 600s cap -- honest early-stop, never a silent
                                # truncation: a threshold skipped this way is reported as such.


def _growth_saturates(growth: list) -> tuple:
    """The SAME saturation formula every prior run's own gate script inlines (see e.g.
    `jabberwock_omniglot_run22_priors.py`'s own `sat_pass` computation) -- factored out once
    here so phase 1's per-threshold loop can call it identically for each sweep value.
    Returns `(sat_pass_or_None, first, last)`."""
    if len(growth) < 3:
        return None, None, None
    first = float(np.mean([g["new_quanta"] for g in growth[:1]]))
    last = float(np.mean([g["new_quanta"] for g in growth[-2:]]))
    sat_pass = (last <= max(3.0, 0.3 * first)) if first > 0 else True
    return sat_pass, first, last


# ---------------------------------------------------------------------------------------------
# PHASE 1 -- LEARN with continuous-novelty minting ON, one threshold at a time. Mirrors
# `gate.run_learn`'s own windowed-growth structure exactly, ADDITIVELY threading
# `enable_continuous_mint`/`continuous_mint_threshold` through the SAME `ink.decode_ink` call
# (substroke composition is OUT OF SCOPE this run -- an independent branch this run's own
# launch instructions do not mention; leaving it off keeps LEARN at its established ~110s/1500-
# stroke cost instead of doubling it, and does not affect the outer stroke-grain vocabulary/
# growth-curve/identity-diversity diagnostics this run measures). The OBSERVATION HISTOGRAM is
# read straight off `decode_ink`'s own returned `"continuous"` list (`res["nearest"]` per
# checked span) -- no extra decode, no extra DtwTo calls beyond what `continuous_mint_or_note`
# itself already made for the mint decision.
# ---------------------------------------------------------------------------------------------
def run_learn_continuous(s, ag, native, alphabets, drawers, cap, dk, window, *,
                          threshold: float) -> dict:
    growth = []
    n_strokes = 0
    n_degenerate_skipped = 0
    win_recognized = win_oov = win_minted = 0
    win_codebook_start = 0
    assign_counter: Counter = Counter()
    t_start = time.time()

    for alph in alphabets:
        if n_strokes >= cap:
            break
        chars = ow.characters(alph, "background")
        for cdir in chars:
            if n_strokes >= cap:
                break
            files_by_drawer = {}
            for f in ow.drawings(cdir):
                d = f.split("/")[-1].split("_")[-1].replace(".txt", "")
                files_by_drawer[d] = f
            for d in drawers:
                if n_strokes >= cap:
                    break
                f = files_by_drawer.get(d)
                if f is None:
                    continue
                for st in ow.load_strokes(f):
                    if n_strokes >= cap:
                        break
                    if st.shape[0] < 2:
                        n_degenerate_skipped += 1
                        continue
                    ink_node = ink.ingest_ink(s, st.tolist(), writer=f"bg_{d}",
                                               max_knots=dk["max_knots"])
                    res = ink.decode_ink(
                        s, ink_node, writer=f"bg_{d}", min_span=dk["min_span"],
                        max_span=dk["max_span"], segments=dk["segments"],
                        turn_bins=dk["turn_bins"], len_bins=dk["len_bins"], grid=dk["grid"],
                        scale_bins=dk["scale_bins"], enable_continuous_mint=True,
                        continuous_mint_threshold=threshold)
                    n_strokes += 1
                    win_recognized += len(res["recognized"])
                    win_oov += len(res["oov"])
                    win_minted += len(res["minted"])
                    for c in res["continuous"]:
                        if c.get("checked"):
                            assign_counter[c["nearest"]] += 1
                    if n_strokes % window == 0:
                        cb = len(sc._existing_names(s, "stroke"))
                        reuse_rate = win_recognized / max(1, win_recognized + win_oov)
                        growth.append({
                            "n": n_strokes, "codebook": cb, "new_quanta": cb - win_codebook_start,
                            "recognized": win_recognized, "oov": win_oov, "minted": win_minted,
                            "reuse_rate": reuse_rate, "elapsed": time.time() - t_start,
                        })
                        win_codebook_start = cb
                        win_recognized = win_oov = win_minted = 0
                if n_strokes >= cap:
                    break
            if n_strokes >= cap:
                break

    return dict(growth=growth, n_strokes=n_strokes, n_degenerate_skipped=n_degenerate_skipped,
                elapsed=time.time() - t_start, assign_counter=assign_counter)


def _phase1_diagnostics(s, lr: dict) -> dict:
    vocab = len(sc._existing_names(s, "stroke"))
    n_continuous = sum(1 for n in sc._existing_names(s, "stroke") if "__cont_" in n)
    assign = lr["assign_counter"]
    total_obs = sum(assign.values())
    top10 = assign.most_common(10)
    dominant_share = (top10[0][1] / total_obs) if top10 and total_obs else 0.0
    n_distinct_with_min_obs = sum(1 for v in assign.values() if v >= MIN_OBS_FOR_TRUSTED_KEY)
    sat_pass, first_w, last_w = _growth_saturates(lr["growth"])

    fails_vocab = vocab < MIN_VOCAB_FOR_PROCEED
    fails_degenerate = dominant_share > MAX_DOMINANT_SHARE
    fails_growth = (sat_pass is False)
    fails_diversity = n_distinct_with_min_obs < MIN_DISTINCT_FOR_PROCEED
    proceed = not (fails_vocab or fails_degenerate or fails_growth or fails_diversity)

    return dict(vocab=vocab, n_continuous_mints=n_continuous, n_distinct_assignments=len(assign),
                total_observations=total_obs, top10=top10, dominant_share=dominant_share,
                n_distinct_with_min_obs=n_distinct_with_min_obs, sat_pass=sat_pass,
                first_window_new=first_w, last_window_new=last_w,
                fails_vocab=fails_vocab, fails_degenerate=fails_degenerate,
                fails_growth=fails_growth, fails_diversity=fails_diversity, proceed=proceed)


# ---------------------------------------------------------------------------------------------
# PHASE 2 -- powered arms (only reached on a phase-1 PASS).
# ---------------------------------------------------------------------------------------------
def _assert_control_invariant_to_mint():
    """Structural invariance check: the parse-marginal CONTROL arm (`ar.stage_parse_char` /
    `ar.parse_marginal_verdict`) must reference NEITHER `ink_decode` NOR `stroke_codebook` --
    it stages via the theta-grid renderer directly off the drawing FILE, never the earned
    stroke codebook, so it is invariant to the mint change BY CONSTRUCTION, not by accident of
    this run's particular vocabulary. A static source-text check (the same genre of audit
    `test_ink_decode_no_python_decisions` already runs on `ink_decode.py`)."""
    import inspect
    src = inspect.getsource(ar.stage_parse_char) + inspect.getsource(ar.parse_marginal_verdict)
    assert "ink_decode" not in src and "stroke_codebook" not in src, (
        "parse_marginal control must not reference the stroke codebook -- if this fires, the "
        "control arm is no longer structurally invariant to continuous-novelty minting")
    return True


def _stage_and_verdict(exemplar_paths, query_path, candidate_idxs, *, way: int) -> tuple:
    scratch = srs.Substrate()
    cand_of: dict[int, int] = {}
    for ci in candidate_idxs:
        node = ar.stage_parse_char(scratch, exemplar_paths[ci], is_query=False,
                                    thetas=ar.DEFAULT_PARSE_THETAS, whole_n=ar.DEFAULT_PARSE_WHOLE_N,
                                    per_part=ar.DEFAULT_PARSE_PER_PART, name=str(ci))
        cand_of[node] = ci
    qn = ar.stage_parse_char(scratch, query_path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS,
                              whole_n=ar.DEFAULT_PARSE_WHOLE_N, per_part=ar.DEFAULT_PARSE_PER_PART)
    winner = ar.parse_marginal_verdict(scratch, qn, part_w=r17.PARSE_PART_W, sc_w=r17.PARSE_SC_W,
                                        beta=r17.PARSE_BETA)
    pred = cand_of.get(winner, -1) if winner is not None else -1
    node_of_ci = {ci: n for n, ci in cand_of.items()}
    return pred, scratch, qn, node_of_ci


def _phase2_episode(s, native, dk, exemplar_composed, exemplar_stroke_points, exemplar_paths,
                     query_path, query_composed, query_stroke_points, way: int,
                     priors_fine: dict, priors_coarse: dict, qi: int) -> dict:
    w_control, scratch, qn, node_of_ci = _stage_and_verdict(exemplar_paths, query_path,
                                                             range(way), way=way)

    prior_res = sp.spatial_prior_marginal_rerank_fine(
        scratch, qn, node_of_ci, exemplar_composed, exemplar_stroke_points, list(range(way)),
        priors_fine, priors_coarse, native=native, lam=sp.DEFAULT_PRIOR_LAMBDA, grid=dk["grid"],
        turn_bins=dk["turn_bins"], scale_bins=dk["scale_bins"], segments=dk["segments"],
        alpha=sp.DEFAULT_PRIOR_ALPHA, min_obs=sp.FINE_MIN_OBS, part_w=r17.PARSE_PART_W,
        sc_w=r17.PARSE_SC_W, beta=r17.PARSE_BETA)
    w_fine_prior = prior_res["winner"] if prior_res["winner"] is not None else -1

    coverage_hit = 0
    if ar._stroke_render_live(native):
        abs_res = ar.abs_rerank(s, query_composed, query_stroke_points, exemplar_composed,
                                exemplar_stroke_points, k=ar.DEFAULT_TOPK,
                                turn_bins=dk["turn_bins"], len_bins=dk["len_bins"],
                                grid=dk["grid"], scale_bins=dk["scale_bins"])
        coverage_hit = 1 if qi in abs_res["top_k"] else 0

    return dict(w_control=w_control, w_fine_prior=w_fine_prior, coverage_hit=coverage_hit)


def main():
    t0 = time.time()
    print(SEP)
    print("OMNIGLOT RUN 23 -- CONTINUOUS-NOVELTY MINTING (the run-16 law, 'continuous beats")
    print("quantized,' applied to GROWTH -- run 22's own closing clause). PHASE 1: sweep the")
    print("mint threshold on BACKGROUND-ONLY LEARN data, diagnose FIRST, decide the branch")
    print("BEFORE any accuracy number. PHASE 2 (only on a pass): the powered gate.")
    print(SEP)

    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA}. Cannot run.")
        return 1

    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    print(f"\n  LEARN caps (RUN 15's own REDUCED, saturation-verified cap, reused verbatim by "
          f"every run since): {LEARN_ALPHABETS_N} background alphabets {learn_alphabets}, "
          f"drawers {LEARN_DRAWERS[0]}-{LEARN_DRAWERS[-1]}, capped at {LEARN_STROKE_CAP} "
          f"pen-down strokes. ink-decode params: {DK}.")
    print(f"  Sweep: MINT_THRESHOLDS={MINT_THRESHOLDS} (breadth capped per launch instructions "
          f"-- phase 1 itself runs at FULL LEARN budget per threshold).")
    print(f"  Pre-registered branch bars: vocab>={MIN_VOCAB_FOR_PROCEED}, dominant "
          f"share<={100*MAX_DOMINANT_SHARE:.0f}%, growth SATURATES, distinct assignment keys "
          f"with >={MIN_OBS_FOR_TRUSTED_KEY} obs >= {MIN_DISTINCT_FOR_PROCEED}.")

    print(f"\n{SEP}\n  PHASE 1: THRESHOLD SWEEP (background-only LEARN, diagnostics BEFORE any "
          f"accuracy number)\n{SEP}")

    per_threshold: dict[float, dict] = {}
    booted_agents: dict[float, tuple] = {}
    skipped_thresholds: list = []
    for thr in MINT_THRESHOLDS:
        if time.time() - t0 > PHASE1_BUDGET_SECONDS:
            skipped_thresholds.append(thr)
            print(f"\n  -- threshold={thr:.2f} -- SKIPPED: phase-1 time budget "
                  f"({PHASE1_BUDGET_SECONDS:.0f}s) exhausted after {len(per_threshold)} "
                  f"threshold(s) -- honest early stop, not a silent truncation.")
            continue
        t_thr = time.time()
        s, ag, native = gate.boot()
        lr = run_learn_continuous(s, ag, native, learn_alphabets, LEARN_DRAWERS,
                                   LEARN_STROKE_CAP, DK, GROWTH_WINDOW, threshold=thr)
        diag = _phase1_diagnostics(s, lr)
        per_threshold[thr] = dict(lr=lr, diag=diag, elapsed=time.time() - t_thr)
        booted_agents[thr] = (s, ag, native)
        print(f"\n  -- threshold={thr:.2f} -- processed {lr['n_strokes']} strokes "
              f"({lr['n_degenerate_skipped']} degenerate skipped) in {per_threshold[thr]['elapsed']:.1f}s")
        print(f"     vocabulary: {diag['vocab']} top-level stroke quanta "
              f"({diag['n_continuous_mints']} continuous-mint peers; RUN 15-22 all produced 7).")
        print(f"     observation histogram: {diag['n_distinct_assignments']} distinct "
              f"assignment keys over {diag['total_observations']} continuous-mint-eligible "
              f"observations; top10 counts: {diag['top10']}; dominant share: "
              f"{100*diag['dominant_share']:.1f}%.")
        print(f"     identity diversity: {diag['n_distinct_with_min_obs']} distinct keys with "
              f">= {MIN_OBS_FOR_TRUSTED_KEY} obs (target >= {MIN_DISTINCT_FOR_PROCEED}; run "
              f"22's own coarse/fine wall was {RUN22_IDENTITY_WALL['n_fine_keys_with_min_obs']}).")
        print(f"     growth curve: first-window new={diag['first_window_new']!r} -> "
              f"last-2-windows mean new={diag['last_window_new']!r}  SATURATION: "
              f"{'PASS' if diag['sat_pass'] else ('FAIL' if diag['sat_pass'] is False else 'N/A (too few windows)')}")
        print(f"     BRANCH per-criterion: vocab>=20 "
              f"{'FAIL' if diag['fails_vocab'] else 'pass'}; dominant<=70% "
              f"{'FAIL' if diag['fails_degenerate'] else 'pass'}; growth-saturates "
              f"{'FAIL' if diag['fails_growth'] else 'pass'}; diversity>=20 "
              f"{'FAIL' if diag['fails_diversity'] else 'pass'}  ==> "
              f"{'PROCEED-ELIGIBLE' if diag['proceed'] else 'STOP-ELIGIBLE'}")

    ran_thresholds = [thr for thr in MINT_THRESHOLDS if thr in per_threshold]
    print(f"\n{SEP}\n  PHASE-1 TABLE ({'all' if not skipped_thresholds else f'{len(ran_thresholds)}/{len(MINT_THRESHOLDS)}'} thresholds"
          f"{'; SKIPPED: ' + str(skipped_thresholds) if skipped_thresholds else ''})\n{SEP}")
    print(f"  {'threshold':>10} {'vocab':>6} {'cont_mints':>11} {'distinct_hist':>14} "
          f"{'dominant%':>10} {'div>=10obs':>11} {'sat':>6} {'verdict':>16}")
    for thr in ran_thresholds:
        d = per_threshold[thr]["diag"]
        sat_s = "PASS" if d["sat_pass"] else ("FAIL" if d["sat_pass"] is False else "N/A")
        print(f"  {thr:>10.2f} {d['vocab']:>6} {d['n_continuous_mints']:>11} "
              f"{d['n_distinct_assignments']:>14} {100*d['dominant_share']:>9.1f}% "
              f"{d['n_distinct_with_min_obs']:>11} {sat_s:>6} "
              f"{'PROCEED-ELIGIBLE' if d['proceed'] else 'STOP-ELIGIBLE':>16}")

    passing = [thr for thr in ran_thresholds if per_threshold[thr]["diag"]["proceed"]]
    print(f"\n{SEP}\n  PRE-REGISTERED BRANCH VERDICT (decided BEFORE any accuracy number)\n{SEP}")
    if not passing:
        print(f"\n  VERDICT: STOP after phase 1 -- NO swept threshold ({MINT_THRESHOLDS}) "
              f"clears all four bars (vocab>={MIN_VOCAB_FOR_PROCEED}, non-degenerate "
              f"histogram, growth SATURATES, identity diversity>={MIN_DISTINCT_FOR_PROCEED}).")
        print(f"\n  HONEST CONCLUSION: continuous-novelty minting does NOT diversify this "
              f"featureset's vocabulary either. Four runs (19, 20, 21, 22) diagnosed the SAME "
              f"identity-grain wall from the READING/conditioning side; this run attacked it "
              f"from the LEARN/growth side and the wall holds there too -- whatever geometry "
              f"the real ink actually carries beyond the ~7 discrete stroke classes this "
              f"codebook already earns is either (a) not separable by a DtwTo-distance-to-"
              f"prototype criterion at ANY of the swept thresholds, or (b) genuinely small "
              f"relative to real inter-drawer/inter-instance noise, so a threshold loose "
              f"enough to see it also sees noise (fails growth-saturation / dominant-share) "
              f"and a threshold tight enough to avoid noise sees nothing (fails vocab/"
              f"diversity). The next lever on this road is NOT more mint-criterion surgery on "
              f"THIS featureset -- it is richer PRIMITIVES (a representation change: e.g. "
              f"sub-stroke/junction-coarticulation detail feeding the BASE stroke signature "
              f"itself, rather than a distance threshold on top of it), the creator's call.")
        print(f"\n  Per-threshold timings: " +
              ", ".join(f"{thr:.2f}={per_threshold[thr]['elapsed']:.1f}s" for thr in ran_thresholds))
        donkey0 = "torch" not in sys.modules
        print(f"  donkey=0 (no torch anywhere in sys.modules): {'PASS' if donkey0 else 'FAIL'}")
        print(f"  total runtime: {time.time() - t0:.1f}s")
        print(SEP)
        print("  OVERALL: PASS (phase 1 ran honestly; phase 2 correctly SKIPPED per the "
              "pre-registered branch)" if donkey0 else "  OVERALL: FAIL")
        print(SEP)
        return 0

    best_thr = max(passing, key=lambda t: (per_threshold[t]["diag"]["n_distinct_with_min_obs"],
                                           per_threshold[t]["diag"]["vocab"]))
    print(f"\n  VERDICT: PROCEED to phase 2 -- passing thresholds: {passing}; best by identity "
          f"diversity (tie-break: vocab): threshold={best_thr:.2f}.")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 2 -- reuse the WINNING threshold's already-LEARNED agent (no re-LEARN).
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 2: POWERED GATE (threshold={best_thr:.2f})\n{SEP}")
    s, ag, native = booted_agents[best_thr]

    _assert_control_invariant_to_mint()
    print(f"  structural invariance CONFIRMED: parse_marginal control references neither "
          f"ink_decode nor stroke_codebook -- invariant to the mint change BY CONSTRUCTION.")

    print(f"\n  mining fine + coarse spatial priors (background-only, hygiene asserted inside "
          f"mine_spatial_priors_fine itself)...")
    t_mine0 = time.time()
    mined = sp.mine_spatial_priors_fine(s, DK, learn_alphabets, gate.LEARN_DRAWERS[:7],
                                         max_chars_per_alphabet=25)
    mine_elapsed = time.time() - t_mine0
    mined_fine, mined_coarse = mined["fine"], mined["coarse"]
    sp.persist_spatial_priors(s, mined_coarse)
    sp.persist_spatial_priors_fine(s, mined_fine)
    priors_coarse = sp.load_spatial_priors(s)
    priors_fine = sp.load_spatial_priors_fine(s)
    print(f"  mined {mined['n_chars']} background characters in {mine_elapsed:.1f}s: "
          f"{len(mined_coarse['position_counts'])} coarse identities, "
          f"{len(mined_fine['position_counts'])} fine identities (richer vocabulary from "
          f"continuous minting feeds INTO the fine key's own coarse-name prefix).")

    identity_diag_fine = sp.fine_identity_diagnostics(mined_fine, min_obs=sp.FINE_MIN_OBS)
    diag_fine_dxdydo = sp.prior_diagnostics(mined_fine, dims=("dx", "dy", "do"))
    print(f"  fine-prior identity diversity: {identity_diag_fine['n_fine_keys_with_min_obs']} "
          f"keys with >= {sp.FINE_MIN_OBS} obs; mean peakedness (dx/dy/do): "
          f"{diag_fine_dxdydo['mean_peakedness']:.3f}.")

    qualifying = sorted(a for a in ow.alphabets("evaluation")
                        if len(ow.characters(a, "evaluation")) >= WAY)
    test_alphabets = qualifying[:N_TEST_ALPHABETS]

    cache: dict = {}
    coverage_stroke_points: list = []
    coverage_rng = np.random.default_rng(POWER_SEED)
    for alph in test_alphabets[:2]:
        spec = r17._block_spec(alph, coverage_rng, WAY, EPISODES_PER_ALPHABET)
        drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
        for ci in range(WAY):
            d = gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, DK)
            coverage_stroke_points.append(d["stroke_points"])
        for qi, q_drawer in spec["queries"]:
            d = gate.decode_char_signature(s, drawer_files[qi][q_drawer], cache, DK)
            coverage_stroke_points.append(d["stroke_points"])
    coverage_diag = sp.fine_key_coverage(native, coverage_stroke_points,
                                         mined_fine["position_totals"], segments=DK["segments"],
                                         grid=DK["grid"], scale_bins=DK["scale_bins"],
                                         min_obs=sp.FINE_MIN_OBS)
    fine_verdict = sp.fine_prior_branch_verdict(identity_diag_fine, diag_fine_dxdydo, coverage_diag)
    print(f"  TEST-time fine-key coverage: {100*coverage_diag['coverage']:.1f}%. Fine-prior "
          f"branch (re-armed): {'PROCEED' if fine_verdict['proceed_to_accuracy'] else 'STOP (still under the run-22 bars)'}")

    print(f"\n  PHASE 2 accuracy run (WAY={WAY}, {N_TEST_ALPHABETS} alphabets, R={R_TARGET}, "
          f"budgeted to {RUNTIME_BUDGET_SECONDS:.0f}s total runtime)")
    official_rng = np.random.default_rng(POWER_SEED)
    all_records = []
    hard_deadline = t0 + RUNTIME_BUDGET_SECONDS
    stopped_early = None
    for alph in test_alphabets:
        for r in range(R_TARGET):
            if time.time() > hard_deadline:
                stopped_early = (alph, r)
                break
            spec = r17._block_spec(alph, official_rng, WAY, EPISODES_PER_ALPHABET)
            drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
            exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, DK)
                         for ci in range(WAY)]
            exemplar_composed = [e["composed_sig"] for e in exemplars]
            exemplar_stroke_points = [e["stroke_points"] for e in exemplars]
            exemplar_paths = [drawer_files[ci][ex_drawer] for ci in range(WAY)]
            for qi, q_drawer in spec["queries"]:
                query_path = drawer_files[qi][q_drawer]
                qd = gate.decode_char_signature(s, query_path, cache, DK)
                rec = _phase2_episode(s, native, DK, exemplar_composed, exemplar_stroke_points,
                                      exemplar_paths, query_path, qd["composed_sig"],
                                      qd["stroke_points"], WAY, priors_fine, priors_coarse, qi)
                rec["true"] = qi
                all_records.append(rec)
        if stopped_early:
            break
    if stopped_early:
        print(f"  HARD DEADLINE reached at {stopped_early!r} -- stopped early with "
              f"{len(all_records)} episodes scored (honest, not a crash).")

    trues = [r_["true"] for r_ in all_records]

    def _report(name, preds):
        acc, ci, k = r17._acc_ci(preds, trues)
        shuf = list(trues)
        np.random.default_rng(POWER_SEED + 1).shuffle(shuf)
        acc_s, _, _ = r17._acc_ci(preds, shuf)
        print(f"  {name:<28} n={len(trues):>4}  k={k:>3}  acc={100*acc:5.1f}%  "
              f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]  shuffled={100*acc_s:5.1f}%")
        return dict(acc=acc, ci=ci, k=k, n=len(trues))

    print(f"\n  {len(all_records)} episodes scored.\n")
    r_control = _report("CONTROL (parse-marginal)", [x["w_control"] for x in all_records])
    r_fine_prior = _report("+FINE-SPATIAL-PRIOR", [x["w_fine_prior"] for x in all_records])
    cov5 = float(np.mean([x["coverage_hit"] for x in all_records])) if all_records else 0.0
    print(f"  coverage@{ar.DEFAULT_TOPK} (proposal recall bound): {100*cov5:.1f}%")

    ci_c = r_control["ci"]
    overlaps_17b = not (ci_c[1] < RUN17B_PARSE_MARGINAL["ci"][0]
                        or RUN17B_PARSE_MARGINAL["ci"][1] < ci_c[0])
    print(f"\n  CONTROL REPRODUCTION: {100*r_control['acc']:.1f}% {[round(100*x,1) for x in ci_c]} "
          f"vs RUN 17b's 80.5% [76.3, 84.1] -- "
          f"{'CI-OVERLAP (consistent)' if overlaps_17b else 'CI-SEPARATED (investigate)'}")
    sep_fine = gate._ci_separated(r_fine_prior["ci"], ci_c)
    print(f"  +FINE-SPATIAL-PRIOR vs CONTROL: {100*r_fine_prior['acc']:.1f}% -- "
          f"{'CI-SEPARATED' if sep_fine else 'NOT CI-SEPARATED'}")

    donkey0 = "torch" not in sys.modules
    print(f"\n  donkey=0 (no torch anywhere in sys.modules): {'PASS' if donkey0 else 'FAIL'}")
    print(f"  total runtime: {time.time() - t0:.1f}s")
    print(SEP)
    print("  OVERALL: PASS" if donkey0 else "  OVERALL: FAIL")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
