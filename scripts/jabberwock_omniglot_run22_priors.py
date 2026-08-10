"""OMNIGLOT RUN 22 -- FINE-KEYED SPATIAL PRIORS (git show -s d46ac9b3, run 21's diagnosis):
run 21's learned spatial-prior lever (`domains.spatial_priors`, keyed on the COARSE `strokeq`
identity) hit a REPRESENTATION-BOUND wall -- the position table collapsed to ONE identity
carrying 14,675/14,676 background observations, so the learned prior degenerated to flat + a
spurious scale spike that PENALIZED the winning parse-marginal verdict (67.0% vs control's
79.0%, not separated). Run 21's own commit message named the committed fix: the run-6
matching/identity split -- MATCHING stays coarse (untouched: this run does not touch
`ink_decode.py`/`character_compose.py`/`stroke_codebook.py`), but CONDITIONING keys on a FINE
identity instead. `domains/spatial_priors.py`'s new `mine_spatial_priors_fine`/
`arrangement_log_prior_fine`/`spatial_prior_marginal_rerank_fine` (additive; the run-21 coarse
functions are byte-identical, untouched) key every decoded background stroke's own position/
transition observation on its SUB-FINE (`SUBFINE_TURN_BINS`/`SUBFINE_LEN_BINS`) invariant
`StrokeQuantize` signature, content-hashed the SAME way `ink_decode._signature_key`/
`character_compose.substroke_arrangement_key` already hash a signature into a stable name.
Fine identity does NOT gate recognition (a stroke recognized as coarse quantum "line" stays
"line" for matching purposes, byte-identically) -- so the run-5 fragmentation law ("a finer
BASE grain hurts MATCHING") does not apply to it; only the CONDITIONING table a lookup consults
changes. A three-level BACKOFF ladder (fine -> coarse -> global) is used at scoring time so a
genuinely novel sub-fine variant the mining pass never observed still gets a sane conditioning
value rather than a fabricated zero-count table.

ORDER OF OPERATIONS (the intermediate-gate discipline, hard requirement, per the run-22 launch
instructions): MINE at fine identity + DIAGNOSE FIRST -- identity diversity (distinct fine
keys, observation histogram), per-identity peakedness of the position/transition distributions
(dx/dy/do dims), and TEST-time key coverage (the recall of the prior) are all reported BEFORE
any accuracy number. The PRE-REGISTERED branch (`domains.spatial_priors.fine_prior_branch_
verdict`): if distinct keys with >= FINE_MIN_OBS(=10) observations < 20, OR mean peakedness on
dx/dy/do stays < 0.15, OR TEST-time key coverage < 30% -- the wall holds at fine grain too:
STOP, report the numbers, do NOT run the accuracy arm. Only if the diagnostics pass does this
script proceed to the accuracy arms: CONTROL (parse-marginal, must reproduce ~79-80.5%) and
+FINE-SPATIAL-PRIOR (with backoff) -- the SAME staging/held-Argmin protocol as run 21 (lambda
unit, mean-normalized, byte-identity at lambda=0). The run-21 coarse-only +SPATIAL-PRIOR arm
and the full generative stack are NOT re-run here (both already measured; run 21's own log is
the anchor for the coarse arm; the full stack was shed by run 21's own competitiveness gate) --
this run's core question is specifically whether FINE-keying (not coarse-keying) unlocks the
lever, so its accuracy phase is the two-arm CORE PAIR only.

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /usr/bin/python3 scripts/jabberwock_omniglot_run22_priors.py
"""
from __future__ import annotations

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
import scripts.jabberwock_omniglot_run17_close as r17
from domains import abs_read as ar
from domains import omniglot_world as ow
from domains import spatial_priors as sp

SEP = "=" * 92

WAY = r17.WAY
EPISODES_PER_ALPHABET = r17.EPISODES_PER_ALPHABET
R_TARGET = r17.R_TARGET
POWER_SEED = r17.POWER_SEED
N_TEST_ALPHABETS = r17.N_TEST_ALPHABETS
LEARN_STROKE_CAP = r17.LEARN_STROKE_CAP
FAMILY_A_ANCHOR = r17.FAMILY_A_ANCHOR
RUN17B_PARSE_MARGINAL = {"acc": 0.805, "ci": (0.763, 0.841), "n": 400}   # results/
                                                                          # omniglot_gate_run17_
                                                                          # close.log's RUN 17b
                                                                          # completion block.
RUN21_SPATIAL_PRIOR_COARSE = {"acc": 0.670, "n": None}   # results/omniglot_gate_run21_priors.log
                                                          # -- the WALL this run's diagnostics
                                                          # phase is checking whether fine-
                                                          # keying actually breaks.

# Family A's own marginal-inference recipe, REUSED VERBATIM (tuning-free run: no new weights on
# the CONTROL/marginal side -- the only new knobs this run introduces are `PRIOR_LAMBDA`/
# `PRIOR_ALPHA` (run 21's own "unit first" defaults, unchanged) and `FINE_MIN_OBS` (the
# pre-registered backoff threshold, a module constant in `domains.spatial_priors`, never tuned
# here).
PARSE_THETAS = ar.DEFAULT_PARSE_THETAS
PARSE_WHOLE_N = ar.DEFAULT_PARSE_WHOLE_N
PARSE_PER_PART = ar.DEFAULT_PARSE_PER_PART
PARSE_PART_W, PARSE_SC_W, PARSE_BETA = r17.PARSE_PART_W, r17.PARSE_SC_W, r17.PARSE_BETA
PRIOR_LAMBDA = sp.DEFAULT_PRIOR_LAMBDA   # 1.0 -- "unit first," reused verbatim from run 21.
PRIOR_ALPHA = sp.DEFAULT_PRIOR_ALPHA     # 1.0 -- Laplace smoothing, unit, not tuned.
FINE_MIN_OBS = sp.FINE_MIN_OBS           # 10 -- pre-registered backoff threshold.

# Mining scope: BYTE-IDENTICAL to run 21's own bounded drawer/character subset (widened once
# already, from run 21's own 3-drawer pilot collapse) -- the SAME 5 background alphabets /
# drawers 01-07 / up to 25 chars-per-alphabet pool, so this run's coarse-table byproduct (the
# "coarse" half of `mine_spatial_priors_fine`'s return) reproduces run 21's mined coarse table
# from the SAME inputs, and only the identity KEY differs between the two runs' own tables.
MINE_DRAWERS = gate.LEARN_DRAWERS[:7]
MINE_MAX_CHARS_PER_ALPHABET = 25

# TEST-time coverage probe: how many TEST characters to decode PURELY for the phase-1 coverage
# diagnostic (before any accuracy number) -- reuses the SAME `_block_spec`/cache the powered
# phase will draw on later (byte-identical rng draw order), so this decode work is NOT wasted
# even when the branch proceeds to the accuracy phase.
COVERAGE_PROBE_ALPHABETS = 2   # first N (sorted-name) qualifying test alphabets' pilot blocks.

RUNTIME_BUDGET_SECONDS = 520.0           # RUN 17/19/20/21's own budget value, reused verbatim.


def _stage_and_verdict(exemplar_paths, query_path, candidate_idxs, *, way: int) -> tuple:
    """Mechanical scratch-substrate staging + ONE `parse_marginal_verdict` evaluate -- the
    CONTROL arm, byte-identical to RUN 17b/19/20/21's own theta-grid-only staging. Returns
    `(predicted_index, scratch, query_node, {candidate_index: node_id})`."""
    scratch = srs.Substrate()
    cand_of: dict[int, int] = {}
    for ci in candidate_idxs:
        node = ar.stage_parse_char(scratch, exemplar_paths[ci], is_query=False,
                                    thetas=PARSE_THETAS, whole_n=PARSE_WHOLE_N,
                                    per_part=PARSE_PER_PART, name=str(ci))
        cand_of[node] = ci
    qn = ar.stage_parse_char(scratch, query_path, is_query=True, thetas=PARSE_THETAS,
                              whole_n=PARSE_WHOLE_N, per_part=PARSE_PER_PART)
    winner = ar.parse_marginal_verdict(scratch, qn, part_w=PARSE_PART_W, sc_w=PARSE_SC_W,
                                        beta=PARSE_BETA)
    pred = cand_of.get(winner, -1) if winner is not None else -1
    node_of_ci = {ci: n for n, ci in cand_of.items()}
    return pred, scratch, qn, node_of_ci


def _episode_run22(native, dk, exemplar_composed, exemplar_stroke_points, exemplar_paths,
                    query_path, way: int, priors_fine: dict, priors_coarse: dict) -> dict:
    t_parts = {}

    t0 = time.time()
    w_control, scratch, qn, node_of_ci = _stage_and_verdict(exemplar_paths, query_path,
                                                             range(way), way=way)
    t_parts["parse_control"] = time.time() - t0

    t0 = time.time()
    prior_res = sp.spatial_prior_marginal_rerank_fine(
        scratch, qn, node_of_ci, exemplar_composed, exemplar_stroke_points, list(range(way)),
        priors_fine, priors_coarse, native=native, lam=PRIOR_LAMBDA, grid=dk["grid"],
        turn_bins=dk["turn_bins"], scale_bins=dk["scale_bins"], segments=dk["segments"],
        alpha=PRIOR_ALPHA, min_obs=FINE_MIN_OBS, part_w=PARSE_PART_W, sc_w=PARSE_SC_W,
        beta=PARSE_BETA)
    w_fine_prior = prior_res["winner"] if prior_res["winner"] is not None else -1
    t_parts["fine_spatial_prior"] = time.time() - t0

    return dict(w_control=w_control, w_fine_prior=w_fine_prior, timing=t_parts)


def _run_block(s, native, dk, cache, spec, way, priors_fine, priors_coarse) -> dict:
    t0 = time.time()
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, dk)
                 for ci in range(way)]
    exemplar_composed = [e["composed_sig"] for e in exemplars]
    exemplar_stroke_points = [e["stroke_points"] for e in exemplars]
    exemplar_paths = [drawer_files[ci][ex_drawer] for ci in range(way)]
    records = []
    for qi, q_drawer in spec["queries"]:
        query_path = drawer_files[qi][q_drawer]
        gate.decode_char_signature(s, query_path, cache, dk)   # populate/refresh the cache
        rec = _episode_run22(native, dk, exemplar_composed, exemplar_stroke_points,
                              exemplar_paths, query_path, way, priors_fine, priors_coarse)
        rec["true"] = qi
        records.append(rec)
    return dict(records=records, elapsed=time.time() - t0)


def main():
    t0 = time.time()
    print(SEP)
    print("OMNIGLOT RUN 22 -- FINE-KEYED SPATIAL PRIORS (run 21's fix): MINE at fine identity,")
    print("DIAGNOSE FIRST (identity diversity / peakedness / TEST-time coverage), THEN -- only")
    print("if the pre-registered branch passes -- CONTROL vs +FINE-SPATIAL-PRIOR (backoff).")
    print(SEP)

    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA}. Cannot run.")
        return 1

    s, ag, native = gate.boot()
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    print(f"\n  LEARN caps (RUN 15-21's own reduced, saturation-verified cap): "
          f"{gate.LEARN_ALPHABETS_N} background alphabets, drawers "
          f"{gate.LEARN_DRAWERS[0]}-{gate.LEARN_DRAWERS[-1]}, capped at {LEARN_STROKE_CAP} "
          f"pen-down strokes. ink-decode params: {gate.DK}")
    print(f"  Parse recipe (Family A's own, REUSED VERBATIM): thetas={PARSE_THETAS}, "
          f"whole_n={PARSE_WHOLE_N}, per_part={PARSE_PER_PART}, part_w={PARSE_PART_W}, "
          f"sc_w={PARSE_SC_W}, beta={PARSE_BETA}. prior_lambda={PRIOR_LAMBDA} (unit, run 21's "
          f"default), prior_alpha={PRIOR_ALPHA} (Laplace smoothing, unit), "
          f"fine_min_obs={FINE_MIN_OBS} (pre-registered backoff threshold).")

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
    print(f"  final LEARN codebook size: {final_codebook} stroke quanta "
          f"(RUN 15-21 all produced 7).")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 1.5: MINE FINE + COARSE SPATIAL PRIORS (background-only, hygiene asserted inside
    #  `mine_spatial_priors_fine` itself). ONE decode pass produces BOTH tables.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 1.5: MINE SPATIAL PRIORS -- FINE identity (RUN 22's fix) + COARSE "
          f"(RUN 21's, for direct comparison), background-only\n{SEP}")
    assert set(learn_alphabets) <= set(ow.alphabets("background")), \
        "mining alphabets must be a subset of the background split (hygiene)."
    t_mine0 = time.time()
    mined = sp.mine_spatial_priors_fine(s, gate.DK, learn_alphabets, MINE_DRAWERS,
                                         max_chars_per_alphabet=MINE_MAX_CHARS_PER_ALPHABET)
    mine_elapsed = time.time() - t_mine0
    mined_fine, mined_coarse = mined["fine"], mined["coarse"]
    print(f"  mined {mined['n_chars']} background characters ({len(learn_alphabets)} alphabets x "
          f"drawers {MINE_DRAWERS} x up to {MINE_MAX_CHARS_PER_ALPHABET} chars/alphabet) in "
          f"{mine_elapsed:.1f}s (ONE decode pass feeds BOTH tables below).")
    print(f"  COARSE table (run 21's key -- 'strokeq' identity): "
          f"{len(mined_coarse['position_counts'])} distinct identities, "
          f"{sum(mined_coarse['position_totals'].values())} total stroke observations.")
    print(f"  FINE table (run 22's key -- sub-fine content-hashed identity): "
          f"{len(mined_fine['position_counts'])} distinct identities, "
          f"{sum(mined_fine['position_totals'].values())} total stroke observations.")

    persisted_coarse = sp.persist_spatial_priors(s, mined_coarse)
    persisted_fine = sp.persist_spatial_priors_fine(s, mined_fine)
    print(f"  persisted {persisted_coarse['installed']} coarse SpatialPrior nodes "
          f"(category={sp.CATEGORY!r}) + {persisted_fine['installed']} fine SpatialPrior nodes "
          f"(category={sp.CATEGORY_FINE!r}) via teach() -- seed byproducts.")
    priors_coarse = sp.load_spatial_priors(s)
    priors_fine = sp.load_spatial_priors_fine(s)

    # ------------------------------------------------------------------------------------- #
    #  PHASE 1.6: THE INTERMEDIATE GATE -- identity diversity, peakedness, TEST-time coverage,
    #  ALL reported BEFORE any accuracy number, per the run-22 launch instructions' hard
    #  "diagnose first" requirement.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 1.6: INTERMEDIATE-GATE DIAGNOSTICS (read BEFORE any accuracy "
          f"number below)\n{SEP}")

    identity_diag_coarse = sp.fine_identity_diagnostics(mined_coarse, min_obs=FINE_MIN_OBS)
    identity_diag_fine = sp.fine_identity_diagnostics(mined_fine, min_obs=FINE_MIN_OBS)
    print(f"\n  (1) IDENTITY DIVERSITY -- 'ONE identity carried "
          f"{RUN21_SPATIAL_PRIOR_COARSE['acc']*100:.0f}%-ish of observations' was run 21's wall:")
    print(f"    COARSE (run 21's key): {identity_diag_coarse['n_distinct_fine_keys']} distinct "
          f"identities, dominant identity share = "
          f"{100*identity_diag_coarse['dominant_key_share']:.1f}% of "
          f"{identity_diag_coarse['total_observations']} total observations "
          f"(top10 counts: {identity_diag_coarse['top10_observation_counts']}).")
    print(f"    FINE (run 22's key):   {identity_diag_fine['n_distinct_fine_keys']} distinct "
          f"identities, {identity_diag_fine['n_fine_keys_with_min_obs']} with >= "
          f"{FINE_MIN_OBS} observations, dominant identity share = "
          f"{100*identity_diag_fine['dominant_key_share']:.1f}% of "
          f"{identity_diag_fine['total_observations']} total observations "
          f"(top10 counts: {identity_diag_fine['top10_observation_counts']}).")

    diag_fine_all = sp.prior_diagnostics(mined_fine)
    diag_fine_dxdydo = sp.prior_diagnostics(mined_fine, dims=("dx", "dy", "do"))
    diag_coarse_all = sp.prior_diagnostics(mined_coarse)
    print(f"\n  (2) PEAKEDNESS (0=flat/uninformative, 1=maximally peaked; the pre-registered "
          f"branch reads dx/dy/do ONLY, excluding scale):")
    print(f"    COARSE, all 4 dims:  mean peakedness = {diag_coarse_all['mean_peakedness']:.3f}  "
          f"(mean samples/row = {diag_coarse_all['mean_total_samples']:.1f})")
    print(f"    FINE, all 4 dims:    mean peakedness = {diag_fine_all['mean_peakedness']:.3f}  "
          f"(mean samples/row = {diag_fine_all['mean_total_samples']:.1f})")
    print(f"    FINE, dx/dy/do ONLY (the branch's own test): mean peakedness = "
          f"{diag_fine_dxdydo['mean_peakedness']:.3f}  (mean samples/row = "
          f"{diag_fine_dxdydo['mean_total_samples']:.1f}, n_rows={len(diag_fine_dxdydo['rows'])})")
    # A representative sample of the most-observed fine identities' own per-dim peakedness --
    # NOT the full row dump (fine identities can number in the tens-to-hundreds; a full dump
    # would flood the log with little added signal over the mean already reported above).
    top_fine_names = [n for n, _ in sorted(mined_fine["position_totals"].items(),
                                            key=lambda kv: kv[1], reverse=True)[:8]]
    print(f"    Top-8 most-observed FINE identities, per-dim peakedness (dx/dy/do/ds):")
    for name in top_fine_names:
        rows_for_name = [r for r in diag_fine_all["rows"]
                          if r["kind"] == "position" and r["name"] == name]
        by_dim = {r["dim"]: r for r in rows_for_name}
        print(f"      {name:<40} n={mined_fine['position_totals'][name]:>5}  " +
              "  ".join(f"{d}={by_dim[d]['peakedness']:.2f}" for d in sp.DIMS if d in by_dim))

    qualifying = sorted(a for a in ow.alphabets("evaluation")
                        if len(ow.characters(a, "evaluation")) >= WAY)
    test_alphabets = qualifying[:N_TEST_ALPHABETS]
    print(f"\n  TEST alphabets (sorted-name {N_TEST_ALPHABETS}-prefix, RUN 15-21's own set): "
          f"{test_alphabets}")

    print(f"\n  (3) TEST-TIME COVERAGE -- decoding {COVERAGE_PROBE_ALPHABETS} pilot block(s) "
          f"from the TEST/evaluation split PURELY to measure fine-key recall (this decode work "
          f"is byte-identically reused by the powered phase below if the branch proceeds -- "
          f"nothing wasted):")
    cache: dict = {}
    coverage_stroke_points: list = []
    coverage_rng = np.random.default_rng(POWER_SEED)
    probe_specs = []
    for alph in test_alphabets[:COVERAGE_PROBE_ALPHABETS]:
        spec = r17._block_spec(alph, coverage_rng, WAY, EPISODES_PER_ALPHABET)
        probe_specs.append((alph, spec))
        drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
        for ci in range(WAY):
            d = gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, gate.DK)
            coverage_stroke_points.append(d["stroke_points"])
        for qi, q_drawer in spec["queries"]:
            d = gate.decode_char_signature(s, drawer_files[qi][q_drawer], cache, gate.DK)
            coverage_stroke_points.append(d["stroke_points"])
    coverage_diag = sp.fine_key_coverage(native, coverage_stroke_points,
                                         mined_fine["position_totals"], segments=gate.DK["segments"],
                                         grid=gate.DK["grid"], scale_bins=gate.DK["scale_bins"],
                                         min_obs=FINE_MIN_OBS)
    print(f"    probed {len(coverage_stroke_points)} TEST-time decoded characters "
          f"({coverage_diag['n_total_strokes']} individual strokes) across "
          f"{[a for a, _ in probe_specs]}.")
    print(f"    fine-key coverage (fraction of TEST strokes whose OWN fine key has >= "
          f"{FINE_MIN_OBS} background observations): {100*coverage_diag['coverage']:.1f}% "
          f"({coverage_diag['n_covered']}/{coverage_diag['n_total_strokes']}).")

    # ------------------------------------------------------------------------------------- #
    #  THE PRE-REGISTERED BRANCH VERDICT.
    # ------------------------------------------------------------------------------------- #
    verdict = sp.fine_prior_branch_verdict(identity_diag_fine, diag_fine_dxdydo, coverage_diag)
    print(f"\n{SEP}\n  PRE-REGISTERED BRANCH VERDICT (decided BEFORE any accuracy number)\n{SEP}")
    print(f"  (a) distinct fine keys with >= {FINE_MIN_OBS} obs: "
          f"{identity_diag_fine['n_fine_keys_with_min_obs']} "
          f"{'< 20 -> FAILS' if verdict['fails_diversity'] else '>= 20 -> passes'}")
    print(f"  (b) mean peakedness (dx/dy/do): {diag_fine_dxdydo['mean_peakedness']:.3f} "
          f"{'< 0.15 -> FAILS' if verdict['fails_peakedness'] else '>= 0.15 -> passes'}")
    print(f"  (c) TEST-time fine-key coverage: {100*coverage_diag['coverage']:.1f}% "
          f"{'< 30% -> FAILS' if verdict['fails_coverage'] else '>= 30% -> passes'}")
    print(f"\n  VERDICT: {'PROCEED to the accuracy arms' if verdict['proceed_to_accuracy'] else 'STOP -- the wall holds at fine grain too'}")

    donkey0 = "torch" not in sys.modules
    if not verdict["proceed_to_accuracy"]:
        print(f"\n  HONEST CONCLUSION: fine-keying the conditioning identity does NOT unlock "
              f"the spatial-prior lever on this featureset -- the position/transition signal "
              f"this arc's stroke-quantum vocabulary carries is insufficient at ANY grain this "
              f"codebook currently distinguishes (coarse: 7 quanta collapsing to ~1 dominant "
              f"identity; fine: sub-fine content-hash variants, still failing the pre-registered "
              f"bar above). The next lever on this road is NOT more conditioning-side surgery "
              f"(run 19-22's shared shape: token-refit, coarse priors, fine priors all hit the "
              f"SAME identity-grain ceiling) -- it is the GRAIN LADDER AT SCALE on the LEARN "
              f"side: a richer stroke-quantum vocabulary (more top-level quanta, or the "
              f"sub-stroke/character-composition machinery already built for BRANCH A extended "
              f"to genuinely diversify what a 'stroke identity' even IS) so there is more than "
              f"a handful of positions/transitions to condition on in the first place. That is "
              f"a LEARN-side change (stroke_codebook.py's vocabulary-growth mint criteria, or "
              f"richer primitives entirely), not a spatial_priors.py conditioning-side one.")
        print(f"\n  mining cost: {mine_elapsed:.1f}s for {mined['n_chars']} background characters.")
        print(f"  donkey=0 (no torch anywhere in sys.modules): {'PASS' if donkey0 else 'FAIL'}")
        print(f"  total runtime: {time.time() - t0:.1f}s")
        print(SEP)
        print("  OVERALL: PASS (diagnostics ran honestly; accuracy arm correctly SKIPPED per "
              "the pre-registered branch)" if donkey0 and sat_pass is not False else
              "  OVERALL: FAIL")
        print(SEP)
        return 0

    # ------------------------------------------------------------------------------------- #
    #  PHASE 2: PILOT + BUDGET PROJECTION (only reached if the branch above PROCEEDS).
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 2: PILOT + BUDGET PROJECTION\n{SEP}")
    pilot_rng = np.random.default_rng(POWER_SEED)
    pilot_spec = r17._block_spec(test_alphabets[0], pilot_rng, WAY, EPISODES_PER_ALPHABET)
    pilot = _run_block(s, native, gate.DK, cache, pilot_spec, WAY, priors_fine, priors_coarse)
    n_blocks = len(test_alphabets) * R_TARGET
    per_part_totals: dict = {}
    for rec in pilot["records"]:
        for k, v in rec["timing"].items():
            per_part_totals[k] = per_part_totals.get(k, 0.0) + v
    print(f"  PILOT block ({test_alphabets[0]!r}, repeat 0, {WAY} episodes, BOTH ARMS): "
          f"{pilot['elapsed']:.1f}s total. Per-arm-part totals (this one block): "
          + ", ".join(f"{k}={v:.2f}s" for k, v in per_part_totals.items()))

    pilot_trues = [r_["true"] for r_ in pilot["records"]]

    def _pilot_report(name, preds):
        acc, ci, k = r17._acc_ci(preds, pilot_trues)
        print(f"    {name:<38} n={len(pilot_trues):>3}  k={k:>2}  acc={100*acc:5.1f}%  "
              f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]")
        return acc

    print(f"\n  PILOT-SCALE per-arm accuracy (n={WAY}, ONE block, UNPOWERED -- mechanism check "
          f"only, not a claim):")
    _pilot_report("CONTROL (parse-marginal)", [x["w_control"] for x in pilot["records"]])
    _pilot_report("+FINE-SPATIAL-PRIOR", [x["w_fine_prior"] for x in pilot["records"]])

    elapsed_so_far = time.time() - t0
    per_block = pilot["elapsed"]
    projected = elapsed_so_far + per_block * n_blocks

    r_used = R_TARGET
    budget_notes = []
    if projected > RUNTIME_BUDGET_SECONDS:
        r_used = 1
        projected_r1 = elapsed_so_far + per_block * len(test_alphabets) * r_used
        note = (f"projected R={R_TARGET} run {projected:.0f}s > {RUNTIME_BUDGET_SECONDS:.0f}s "
                f"budget -- reducing to R={r_used} (projected {projected_r1:.0f}s), per "
                f"'shed R, never the core pair' (this run has no arm 3 to shed first -- the "
                f"core pair IS the whole scope).")
        print(f"  {note}")
        budget_notes.append(note)
    else:
        print(f"  within budget (projected {projected:.0f}s vs {RUNTIME_BUDGET_SECONDS:.0f}s "
              f"budget) -- running the full scope (R={r_used}, {len(test_alphabets)} alphabets).")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 3: POWERED TEST
    # ------------------------------------------------------------------------------------- #
    n_target = len(test_alphabets) * r_used * WAY
    print(f"\n{SEP}\n  PHASE 3: POWERED TEST (target n={n_target})\n{SEP}")
    official_rng = np.random.default_rng(POWER_SEED)
    all_records = []
    hard_deadline = t0 + RUNTIME_BUDGET_SECONDS
    stopped_early = None
    for alph in test_alphabets:
        for r in range(r_used):
            if time.time() > hard_deadline:
                stopped_early = (alph, r)
                break
            spec = r17._block_spec(alph, official_rng, WAY, EPISODES_PER_ALPHABET)
            blk = _run_block(s, native, gate.DK, cache, spec, WAY, priors_fine, priors_coarse)
            all_records.extend(blk["records"])
        if stopped_early:
            break
    if stopped_early:
        note = (f"HARD DEADLINE reached at {stopped_early!r} -- stopped early with "
                f"{len(all_records)} episodes scored (honest, not a crash).")
        print(f"  {note}")
        budget_notes.append(note)

    trues = [r_["true"] for r_ in all_records]

    def _report(name, preds, trues_):
        acc, ci, k = r17._acc_ci(preds, trues_)
        shuf = list(trues_)
        np.random.default_rng(POWER_SEED + 1).shuffle(shuf)
        acc_s, _, _ = r17._acc_ci(preds, shuf)
        print(f"  {name:<32} n={len(trues_):>4}  k={k:>3}  acc={100*acc:5.1f}%  "
              f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]  shuffled={100*acc_s:5.1f}%")
        return dict(acc=acc, ci=ci, k=k, n=len(trues_))

    print(f"\n  {len(all_records)} episodes scored (R={r_used}).\n")
    r_control = _report("CONTROL (parse-marginal)", [x["w_control"] for x in all_records], trues)
    r_fine_prior = _report("+FINE-SPATIAL-PRIOR", [x["w_fine_prior"] for x in all_records], trues)

    print(f"\n{SEP}\n  VERDICTS (n={len(all_records)})\n{SEP}")
    ci_c = r_control["ci"]
    overlaps_17b = not (ci_c[1] < RUN17B_PARSE_MARGINAL["ci"][0]
                        or RUN17B_PARSE_MARGINAL["ci"][1] < ci_c[0])
    print(f"  CONTROL REPRODUCTION: {100*r_control['acc']:.1f}% "
          f"{[round(100*x,1) for x in ci_c]} vs RUN 17b's 80.5% [76.3, 84.1] (n=400) -- "
          f"{'CI-OVERLAP (consistent)' if overlaps_17b else 'CI-SEPARATED (investigate)'}")

    def _verdict(name, res, base_ci, base_label):
        sep = gate._ci_separated(res["ci"], base_ci)
        print(f"  {name} vs {base_label}: {100*res['acc']:.1f}% -- "
              f"{'CI-SEPARATED' if sep else 'NOT CI-SEPARATED'}")
        return sep

    print()
    sep_from_control = _verdict("+FINE-SPATIAL-PRIOR", r_fine_prior, ci_c, "CONTROL")

    print(f"\n  FAMILY-A ANCHOR ({100*FAMILY_A_ANCHOR:.1f}%) / 96.7 (BPL's own reported ceiling) "
          f"/ RUN 21's coarse-prior wall ({100*RUN21_SPATIAL_PRIOR_COARSE['acc']:.1f}%) "
          f"CI-TOUCH CHECK:")
    for name, res in (("CONTROL", r_control), ("+FINE-SPATIAL-PRIOR", r_fine_prior)):
        touch_a = r17._touches(res["ci"], FAMILY_A_ANCHOR)
        touch_96 = r17._touches(res["ci"], 0.967)
        touch_r21 = r17._touches(res["ci"], RUN21_SPATIAL_PRIOR_COARSE["acc"])
        print(f"    {name:<22}: CI {[round(100*x,1) for x in res['ci']]} "
              f"Family-A-anchor {'TOUCHES' if touch_a else 'does NOT touch'}; "
              f"96.7 {'TOUCHES' if touch_96 else 'does NOT touch'}; "
              f"run-21-coarse-wall {'TOUCHES' if touch_r21 else 'does NOT touch'}.")
    best_arm = max([("CONTROL", r_control), ("+FINE-SPATIAL-PRIOR", r_fine_prior)],
                   key=lambda kv: kv[1]["acc"])
    print(f"\n  BEST ARM: {best_arm[0]} at {100*best_arm[1]['acc']:.1f}% "
          f"{[round(100*x,1) for x in best_arm[1]['ci']]}")

    print(f"\n  THE MECHANISM CHECK (must-hold per the launch instructions): the FINE-keyed "
          f"spatial-prior arm {'DID' if sep_from_control and r_fine_prior['acc'] > r_control['acc'] else 'did NOT'} "
          f"separate ABOVE control ({100*r_control['acc']:.1f}% -> {100*r_fine_prior['acc']:.1f}%); "
          f"{'CI-SEPARATED' if sep_from_control else 'NOT CI-SEPARATED'} in EITHER direction. "
          f"Contrast with RUN 21's COARSE-keyed prior, which was BELOW control "
          f"({100*RUN21_SPATIAL_PRIOR_COARSE['acc']:.1f}% vs 79-80.5%) -- fine-keying's own "
          f"delta from that wall is the headline this run measures.")

    print(f"\n  BUDGET NOTES: {budget_notes if budget_notes else 'none -- full scope completed.'}")
    print(f"  mining cost: {mine_elapsed:.1f}s for {mined['n_chars']} background characters.")
    print(f"  donkey=0 (no torch anywhere in sys.modules): {'PASS' if donkey0 else 'FAIL'}")
    print(f"\n  total runtime: {time.time() - t0:.1f}s (internal budget "
          f"{RUNTIME_BUDGET_SECONDS:.0f}s + {600 - RUNTIME_BUDGET_SECONDS:.0f}s import/report "
          f"headroom)")
    print(SEP)
    print("  OVERALL: PASS" if donkey0 and sat_pass is not False else "  OVERALL: FAIL")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
