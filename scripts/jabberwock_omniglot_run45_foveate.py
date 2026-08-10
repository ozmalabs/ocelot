"""OMNIGLOT RUN 45 -- PHASE 4 (FINAL PHASE OF THE HUMAN-GAP PLAN): CONDITIONAL FOVEATION.

RUN 37A (commit cca938fd) built a contrastive verdict -- look SPECIFICALLY at where the global
top-2 candidates differ and re-judge on that region alone -- and it harmed badly (82 broken /
16 fixed at n=400). The post-mortem named THREE independent failure causes, all present at
once: (1) UNCONDITIONAL (fired on every episode, including the ~80% the global verdict already
got comfortably right); (2) a REPLACEMENT (the focused score OVERRODE the global verdict
outright rather than entering as one more piece of fused evidence); (3) FRAME-CONTAMINATED (the
difference-region comparison normalized the query and EACH candidate INDEPENDENTLY, so a real
small distinguishing feature competed against per-glyph normalization noise on an even footing).
The human mechanism this run builds: "align the wholes FIRST, arbitrate on the difference only
when the wholes genuinely tie, as EXTRA evidence, in the ALIGNED frame" -- 37A retried with all
three causes fixed:

  1. CONDITION (fixes cause 1) -- fire ONLY when the top-2 global margin is TINY. The threshold
     is `domains.conditional_foveation.derive_threshold`'s p25 of the top-2 margin over n=100
     BACKGROUND 20-way episodes (5 LEARN alphabets x R=1, `run44b._block_spec_split`'s own
     "background" split, reused verbatim) -- frozen BEFORE any real (test-alphabet) episode is
     scored, per this run's own `--stage calibrate`.
  2. ALIGNED FRAME (fixes cause 3) -- `domains.conditional_foveation.difference_elements_
     aligned` normalizes the query AND both top-2 candidates INTO ONE SHARED FRAME (pooled
     centre+scale over their union) rather than three independent per-glyph frames -- see that
     module's own top-of-file doc for why this is the pre-registered FALLBACK ("a shared-frame
     alignment"), not a literal read of the global comparator's own `SmoothDeformComponents`
     fit (that Term's exposed decomposition cannot be inverted into a per-point transform: only
     the GEOMETRIC-MEAN `log_scale` is exposed, not `scaleX`/`scaleY` separately, and the
     non-affine "bending" field is only exposed as an aggregate scalar, never per-point).
  3. SUPPLEMENT AT MATCHED SPREAD (fixes cause 2) -- `score'(ci) = fused(ci) + w_f *
     diff_region_term(ci)` for `ci` in the fired episode's OWN top-2 ONLY (every other
     candidate's score is untouched); `w_f` is DERIVED, never tuned, via RUN 44b's own
     `deform_metric.derive_w_aff` mechanics: `w_f = median(spread_smoothdeform, spread_part,
     spread_sc) / spread_diff_region`, where the THREE numerator spreads are READ verbatim from
     `results/run44_checkpoints/spread.json` (44b's own frozen background measurement,
     READ-ONLY, never recomputed here -- same background split, same protocol) and
     `spread_diff_region` is measured FRESH on the SAME n=100 background episodes (mirrors
     44b's own "spread = mean per-episode std over the 20 one-shot candidates" statistic,
     computed here for a term that is 0.0 for 18/20 candidates and the diff-region evidence for
     the other 2 -- the honest shape this term actually has once fired).
  4. BACKGROUND-SANITY STOP (standing rule since RUN 44b, commit 465d57da) -- armed recipe must
     score >= baseline - 3pp on the SAME n=100 background episodes, checked BEFORE any eval
     (test-alphabet) spend. Reported regardless of pass/fail.

GATE (clones the RUN 26/34/37A/44b eval skeleton; `run25._block_spec`, `POWER_SEED = gate.SEED +
1500`, WAY=20, R_TARGET=2, N_TEST_ALPHABETS=10 sorted-name prefix, alph OUTER / r INNER block
order -- byte-identical to `results/run26_checkpoints/eval_baseline.json` /
`results/run44_checkpoints/eval_guard.json`). RUN 37C's `DropDegenerateFilter` is ACTIVE for
every stroke load in every stage below (background calibration/sanity AND the real eval),
mirroring RUN 37A's own mandatory wrapping.

  GUARD        -- reproduces 80.5% [76.3, 84.1] k=322/n=400 EXACTLY (this run's own `--stage
                  guard` recomputes block 0 and diffs against `results/run44_checkpoints/
                  eval_guard.json`'s own first 20 records, the SAME 44a reproduction of the
                  RUN 25/26 C0 control every prior phase-4-adjacent run has used as GUARD).
  ARM F        -- the conditional, aligned-frame, spread-matched supplement described above.

PRIMARY (pre-registered, `stage_report`): paired McNemar on same-episode flips, BOTH overall
(n=400) AND restricted to FIRED episodes only (the only episodes ARM F can possibly differ from
GUARD on -- a non-fired episode's `score'` is BYTE-IDENTICAL to `full_pairs`, structurally, by
construction of `conditional_foveation.supplement_pairs` with an empty `terms` dict; this run's
own `--stage eval` asserts this for every non-fired episode rather than merely assuming it).
PREDICTIONS (pre-registered, stated here before any eval number is computed): the condition
fires on a MINORITY of the 400 episodes; among FIRED episodes, fixed > broken, concentrated in
RUN 36's own rank-1/2 near-duplicate confusion class and the NEAR band
(`results/run40_checkpoints/classify.json`, idx-joined, READ-ONLY, coverage caveat: only
158/400 episodes are idx-labelled). STOP (pre-registered, never re-tuned against this eval):
`broken >= fixed` overall means the mechanism harms -- report and stop.

THIS RUN CLOSES THE HUMAN-GAP PLAN either way: a win is the near-band's first crack across four
phases (style normalization P1, the deformation metric P2/P2b, exemplar expansion P3, and this
conditional foveation P4); a null/harm completes the plan with every phase honestly measured.

FILES (`results/run45_checkpoints/` only; every other `run*_checkpoints/` dir -- including
run26's `eval_baseline.json`, run37a's own contrastive machinery, run40's `classify.json`, and
run44/44b's `calibration.json`/`spread.json`/`eval_guard.json` -- READ-ONLY, never written
here). `seeds/stroke_shapes.json` is a PARALLEL-SESSION file: this script never opens it; its
md5 is recorded before/after purely as an untouched-file witness.

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run45.log`, per-block checkpoints, NEVER `run_in_background`. `.venv`
python (needs `substrate_rs`).

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run45_foveate.py --stage calibrate
  ... --stage sanity
  ... --stage guard
  ... --stage eval        (re-invoke until COMPLETE -- checkpointed per block)
  ... --stage report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from scipy.stats import binomtest

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run25_number as run25
import scripts.jabberwock_omniglot_run44b_spread as run44b
from scripts.jabberwock_omniglot_run37c_hygiene import DropDegenerateFilter
from domains import abs_read as ar
from domains import conditional_foveation as cf
from domains import deform_metric as dm
from domains import omniglot_world as ow

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run45_checkpoints")
RUN40_DIR = os.path.join(ROOT, "results", "run40_checkpoints")     # READ-ONLY reference.
RUN44_DIR = os.path.join(ROOT, "results", "run44_checkpoints")     # READ-ONLY reference.
SPREAD_PATH_44B = os.path.join(RUN44_DIR, "spread.json")           # READ-ONLY (44b's own).
GUARD_PATH_44A = os.path.join(RUN44_DIR, "eval_guard.json")        # READ-ONLY (44a's own).
STROKE_SHAPES_PATH = os.path.join(ROOT, "seeds", "stroke_shapes.json")  # parallel-session-owned,
                                                                          # never opened here.
os.makedirs(CKPT_DIR, exist_ok=True)

WAY = run25.WAY                                        # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET    # 20
R_TARGET = run25.R_TARGET                              # 2 -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS              # 10
POWER_SEED = run25.POWER_SEED                          # gate.SEED + 1500, byte-identical
BACKGROUND_R_TARGET = run44b.BACKGROUND_R_TARGET       # 1 -> n=100 (5 LEARN alphabets x 1)

PART_W = ar.DEFAULT_PARSE_PART_W
SC_W = ar.DEFAULT_PARSE_SC_W
BETA = ar.DEFAULT_PARSE_BETA

MARGIN_PCTL = 25.0              # PRE-REGISTERED: p25 of background top-2 margins.
SANITY_MARGIN = 0.03            # HARD STOP: armed_bg_acc must be >= baseline_bg_acc - 3pp.
PER_CALL_BUDGET_SECONDS = 460.0

CALIB_PATH = os.path.join(CKPT_DIR, "calibrate.json")
CALIB_STATE_PATH = os.path.join(CKPT_DIR, "calibrate_state.json")
SANITY_PATH = os.path.join(CKPT_DIR, "sanity.json")
SANITY_STATE_PATH = os.path.join(CKPT_DIR, "sanity_state.json")
GUARD_PATH = os.path.join(CKPT_DIR, "guard.json")
EVAL_PATH = os.path.join(CKPT_DIR, "eval_armf.json")
REPORT_PATH = os.path.join(CKPT_DIR, "report.json")

BASELINE_FULL_DWELL = dict(acc=0.805, ci=(0.7633481418022936, 0.8408493586537856), n=400, k=322)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _md5(path: str) -> str:
    if not os.path.exists(path):
        return "(absent)"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def _wilson(k: int, n: int) -> tuple:
    return gate.wilson_ci(k, n)


def _donkey0() -> bool:
    return "torch" not in sys.modules


def _test_alphabets() -> list:
    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= WAY)
    return qualifying[:N_TEST_ALPHABETS]


def _blocks() -> list:
    test_alphabets = _test_alphabets()
    return [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]


# ===================================================================================================
# ONE EPISODE'S full_pairs (the GLOBAL fused-error vector over all WAY candidates) -- the SAME
# per-candidate quantity `abs_read.parse_marginal_pair_error` produces everywhere else in this
# arc (run25/26/37a/44a/44b's own idiom).
# ===================================================================================================
def _full_pairs(scratch, qn, node_of_cand: dict) -> list:
    return [(ar.parse_marginal_pair_error(scratch, qn, node_of_cand[ci], part_w=PART_W,
                                           sc_w=SC_W, beta=BETA), ci) for ci in range(WAY)]


def _argmin_ci(native, pairs: list) -> int:
    w = native.evaluate(ar._argmin_pairs_term(pairs), {})
    return int(w[1]) if w is not None else -1


# ===================================================================================================
# STAGE: calibrate -- ONE background pass (n=100): background top-2 margins (-> threshold) AND
# the diff-region term's own across-candidate spread (-> w_f, RUN 44b's derive-w mechanics).
# ===================================================================================================
def _run_calibrate_block(alph: str, r: int, spec: dict) -> list:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    out = []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = scratch._inner
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        exemplar_raw = {ci: ow.load_strokes(drawer_files[ci][ex_drawer]) for ci in range(WAY)}
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            full_pairs = _full_pairs(scratch, qn, node_of_cand)
            top2 = cf.top2_from_pairs(native, full_pairs)
            margin = cf.top2_margin(top2)
            term_vec = [0.0] * WAY
            if len(top2) >= 2:
                cand1_idx, cand2_idx = top2[0][1], top2[1][1]
                query_raw = ow.load_strokes(path)
                ft = cf.foveate_terms(native, query_raw, exemplar_raw[cand1_idx],
                                       exemplar_raw[cand2_idx], cand1_idx, cand2_idx)
                for ci, val in ft["terms"].items():
                    term_vec[ci] = val
            out.append(dict(margin=margin, diff_spread=float(np.std(term_vec))))
    return out


def stage_calibrate() -> int:
    print(f"\n{SEP}\n  STAGE: calibrate -- background margin threshold + diff-region spread "
          f"(-> w_f)\n{SEP}")
    if os.path.exists(CALIB_PATH):
        frozen = _load_json(CALIB_PATH)
        print(f"  ALREADY FROZEN: {CALIB_PATH}")
        _print_calibrate(frozen)
        return 0
    if not os.path.exists(SPREAD_PATH_44B):
        print(f"  WALL: {SPREAD_PATH_44B} not found -- 44b's own --stage spread is required as "
              f"a READ-ONLY reference (this run never recomputes it).")
        sys.exit(1)
    spread44b = _load_json(SPREAD_PATH_44B)
    print(f"  READ (read-only) 44b's own background spreads: smoothdeform="
          f"{spread44b['spreads']['smoothdeform']:.5f}  part={spread44b['spreads']['part']:.5f}  "
          f"sc={spread44b['spreads']['sc']:.5f}")

    blocks = run44b._background_blocks()
    n_target = len(blocks) * WAY
    state = _load_json(CALIB_STATE_PATH) if os.path.exists(CALIB_STATE_PATH) else dict(
        block_idx=0, per_episode=[])

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        run44b._block_spec_split(blocks[i][0], rng, WAY, EPISODES_PER_ALPHABET, "background")

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
        alph, r = blocks[state["block_idx"]]
        spec = run44b._block_spec_split(alph, rng, WAY, EPISODES_PER_ALPHABET, "background")
        recs = _run_calibrate_block(alph, r, spec)
        state["per_episode"].extend(recs)
        state["block_idx"] += 1
        _save_json(state, CALIB_STATE_PATH)
        print(f"  block {state['block_idx']}/{len(blocks)} ({alph!r}) -- "
              f"{len(state['per_episode'])}/{n_target} episodes, {time.time()-t0:.1f}s this call")

    if state["block_idx"] < len(blocks):
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-invoke to "
              f"continue.")
        return 0

    per_episode = state["per_episode"]
    margins = [e["margin"] for e in per_episode if np.isfinite(e["margin"])]
    threshold = cf.derive_threshold(margins, pctl=MARGIN_PCTL)
    spread_diff_region = float(np.mean([e["diff_spread"] for e in per_episode]))
    w_f = dm.derive_w_aff(spread44b["spreads"]["smoothdeform"], spread44b["spreads"]["part"],
                           spread44b["spreads"]["sc"], spread_diff_region)
    frozen = dict(n_episodes=n_target, n_finite_margins=len(margins), margin_pctl=MARGIN_PCTL,
                  threshold=threshold, spread_diff_region=spread_diff_region, w_f=w_f,
                  spread44b_smoothdeform=spread44b["spreads"]["smoothdeform"],
                  spread44b_part=spread44b["spreads"]["part"],
                  spread44b_sc=spread44b["spreads"]["sc"],
                  margins=margins, background_alphabets=run44b._background_alphabets())
    _save_json(frozen, CALIB_PATH)
    print(f"\n  FROZEN calibration ({n_target} background episodes) -- {CALIB_PATH}")
    _print_calibrate(frozen)
    return 0


def _print_calibrate(frozen: dict) -> None:
    print(f"    n_episodes={frozen['n_episodes']}  n_finite_margins={frozen['n_finite_margins']}")
    print(f"    threshold (p{frozen['margin_pctl']:.0f} of background top-2 margins) = "
          f"{frozen['threshold']:.6f}")
    print(f"    spread_diff_region (background) = {frozen['spread_diff_region']:.6f}")
    print(f"    target_spread (44b median smoothdeform/part/sc, read-only) -- smoothdeform="
          f"{frozen['spread44b_smoothdeform']:.5f} part={frozen['spread44b_part']:.5f} "
          f"sc={frozen['spread44b_sc']:.5f}")
    print(f"    w_f = median(smoothdeform,part,sc) / spread_diff_region = {frozen['w_f']:.6f}")


def _require_calibrate() -> dict:
    if not os.path.exists(CALIB_PATH):
        print("  WALL: run --stage calibrate to completion first.")
        sys.exit(1)
    return _load_json(CALIB_PATH)


# ===================================================================================================
# ONE EPISODE'S ARM-F prediction (shared by --stage sanity and --stage eval): GLOBAL full_pairs
# computed once, the CONDITION checked, and -- only when fired -- the aligned-frame supplement
# applied to a NEW pairs list the final held Argmin decides over. NON-FIRED episodes are
# provably byte-identical to the GLOBAL argmin (`cf.supplement_pairs` with an empty `terms`
# dict is a no-op) -- asserted here, not merely assumed.
# ===================================================================================================
def _armf_episode(native, scratch, qn, node_of_cand: dict, exemplar_raw: dict, path: str,
                   threshold: float, w_f: float) -> dict:
    full_pairs = _full_pairs(scratch, qn, node_of_cand)
    pred_full = _argmin_ci(native, full_pairs)
    top2 = cf.top2_from_pairs(native, full_pairs)
    margin = cf.top2_margin(top2)
    fired = len(top2) >= 2 and cf.fires(margin, threshold)

    if not fired:
        pred_armf = pred_full
        assert cf.supplement_pairs(full_pairs, {}, w_f) == full_pairs   # structural guarantee.
        return dict(pred_full=pred_full, pred_armf=pred_armf, fired=False, margin=margin,
                    decision="not_fired", full_pairs=full_pairs)

    cand1_idx, cand2_idx = top2[0][1], top2[1][1]
    query_raw = ow.load_strokes(path)
    ft = cf.foveate_terms(native, query_raw, exemplar_raw[cand1_idx], exemplar_raw[cand2_idx],
                          cand1_idx, cand2_idx)
    pairs_prime = cf.supplement_pairs(full_pairs, ft["terms"], w_f)
    pred_armf = _argmin_ci(native, pairs_prime)
    return dict(pred_full=pred_full, pred_armf=pred_armf, fired=True, margin=margin,
                decision=ft["decision"], full_pairs=full_pairs,
                cand1_idx=cand1_idx, cand2_idx=cand2_idx,
                winner_in_top2=bool(pred_armf in (cand1_idx, cand2_idx)),
                n_nonfinite=ft.get("n_nonfinite", 0))


# ===================================================================================================
# STAGE: sanity -- THE HARD STOP. Background baseline vs armed accuracy, BEFORE any eval spend.
# ===================================================================================================
def _run_sanity_block(alph: str, r: int, spec: dict, threshold: float, w_f: float) -> tuple:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    baseline_recs, armed_recs = [], []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = scratch._inner
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        exemplar_raw = {ci: ow.load_strokes(drawer_files[ci][ex_drawer]) for ci in range(WAY)}
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            r_ = _armf_episode(native, scratch, qn, node_of_cand, exemplar_raw, path,
                                threshold, w_f)
            baseline_recs.append(dict(true=qi, correct=bool(r_["pred_full"] == qi)))
            armed_recs.append(dict(true=qi, correct=bool(r_["pred_armf"] == qi),
                                    fired=r_["fired"]))
    return baseline_recs, armed_recs


def stage_sanity() -> int:
    print(f"\n{SEP}\n  STAGE: sanity (THE HARD STOP -- decides everything downstream)\n{SEP}")
    if os.path.exists(SANITY_PATH):
        frozen = _load_json(SANITY_PATH)
        print(f"  ALREADY FROZEN: {SANITY_PATH}")
        _print_sanity(frozen)
        return 0
    calib = _require_calibrate()
    threshold, w_f = calib["threshold"], calib["w_f"]
    print(f"  threshold={threshold:.6f}  w_f={w_f:.6f}  (from --stage calibrate)")

    blocks = run44b._background_blocks()
    n_target = len(blocks) * WAY
    state = _load_json(SANITY_STATE_PATH) if os.path.exists(SANITY_STATE_PATH) else dict(
        block_idx=0, baseline=[], armed=[])

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        run44b._block_spec_split(blocks[i][0], rng, WAY, EPISODES_PER_ALPHABET, "background")

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
        alph, r = blocks[state["block_idx"]]
        spec = run44b._block_spec_split(alph, rng, WAY, EPISODES_PER_ALPHABET, "background")
        base_recs, armed_recs = _run_sanity_block(alph, r, spec, threshold, w_f)
        state["baseline"].extend(base_recs)
        state["armed"].extend(armed_recs)
        state["block_idx"] += 1
        _save_json(state, SANITY_STATE_PATH)
        print(f"  block {state['block_idx']}/{len(blocks)} ({alph!r}) -- "
              f"{len(state['baseline'])}/{n_target} episodes, {time.time()-t0:.1f}s this call")

    if state["block_idx"] < len(blocks):
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-invoke to "
              f"continue.")
        return 0

    k_base = sum(1 for r_ in state["baseline"] if r_["correct"])
    k_armed = sum(1 for r_ in state["armed"] if r_["correct"])
    n = len(state["baseline"])
    n_fired = sum(1 for r_ in state["armed"] if r_["fired"])
    acc_base, acc_armed = k_base / n, k_armed / n
    passed = acc_armed >= acc_base - SANITY_MARGIN
    frozen = dict(threshold=threshold, w_f=w_f, n=n, n_fired=n_fired,
                  k_baseline=k_base, k_armed=k_armed, acc_baseline=acc_base, acc_armed=acc_armed,
                  sanity_margin=SANITY_MARGIN, passed=bool(passed))
    _save_json(frozen, SANITY_PATH)
    _print_sanity(frozen)
    return 0


def _print_sanity(frozen: dict) -> None:
    print(f"\n  ---- BACKGROUND-SANITY GATE (n={frozen['n']}, fired={frozen['n_fired']}, "
          f"threshold={frozen['threshold']:.6f}, w_f={frozen['w_f']:.6f}) ----")
    print(f"    baseline (unmodified fused recipe): acc={100*frozen['acc_baseline']:.1f}%  "
          f"k={frozen['k_baseline']}/{frozen['n']}")
    print(f"    armed    (conditional foveation supplement): acc={100*frozen['acc_armed']:.1f}%  "
          f"k={frozen['k_armed']}/{frozen['n']}")
    delta = frozen["acc_armed"] - frozen["acc_baseline"]
    print(f"    delta = {100*delta:+.1f}pp   hard-stop bound = baseline - "
          f"{100*frozen['sanity_margin']:.0f}pp")
    print(f"    VERDICT: {'PASS -- proceed' if frozen['passed'] else 'STOP -- do NOT spend any eval budget'}")


def _require_sanity() -> dict:
    if not os.path.exists(SANITY_PATH):
        print("  WALL: run --stage sanity to completion first.")
        sys.exit(1)
    return _load_json(SANITY_PATH)


# ===================================================================================================
# STAGE: guard -- protocol reproduction against 44a's OWN eval_guard.json block 0 (read-only).
# ===================================================================================================
def stage_guard() -> int:
    print(f"\n{SEP}\n  STAGE: guard -- protocol reproduction vs 44a's eval_guard.json\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_PATH)
    print(f"  seeds/stroke_shapes.json md5 (parallel-session-owned, never written here): "
          f"{md5_now}")
    if not os.path.exists(GUARD_PATH_44A):
        print(f"  WALL: {GUARD_PATH_44A} not found.")
        sys.exit(1)
    guard44a = _load_json(GUARD_PATH_44A)
    baseline_records = guard44a["records"][:WAY]

    test_alphabets = _test_alphabets()
    rng = np.random.default_rng(POWER_SEED)
    spec = run25._block_spec(test_alphabets[0], rng, WAY, EPISODES_PER_ALPHABET)
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]

    t0 = time.time()
    got = []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = scratch._inner
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            full_pairs = _full_pairs(scratch, qn, node_of_cand)
            pred_full = _argmin_ci(native, full_pairs)
            got.append(dict(true=qi, pred=pred_full, correct=bool(pred_full == qi)))
    print(f"  block 0 ({test_alphabets[0]!r}) computed in {time.time()-t0:.1f}s.")

    mismatches = []
    for i, (g, b) in enumerate(zip(got, baseline_records)):
        if g["pred"] != b["pred"]:
            mismatches.append((i, g["pred"], b["pred"]))
    ok = not mismatches
    print(f"  GLOBAL (full_pairs argmin) vs eval_guard.json block 0 ({len(got)} episodes): "
          f"{'EXACT MATCH' if ok else f'{len(mismatches)} MISMATCHES'}")
    for i, gv, bv in mismatches[:10]:
        print(f"    MISMATCH episode {i}: got pred={gv} eval_guard.json={bv}")

    out = dict(guard_ok=ok, spot_check_mismatches=len(mismatches), stroke_shapes_md5=md5_now)
    _save_json(out, GUARD_PATH)
    print(f"\n  GUARD: {'PASS -- proceed to --stage eval' if ok else 'FAIL -- STOP'}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0 if ok else 1


def _require_guard():
    if not os.path.exists(GUARD_PATH):
        print("  WALL: run --stage guard first.")
        sys.exit(1)
    g = _load_json(GUARD_PATH)
    if not g.get("guard_ok"):
        print("  WALL: --stage guard did not PASS.")
        sys.exit(1)
    return g


# ===================================================================================================
# STAGE: eval -- ARM F at n=400, the standard test-alphabet protocol.
# ===================================================================================================
def _run_block_arm_f(alph: str, r: int, spec: dict, threshold: float, w_f: float) -> tuple:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    recs, margins = [], []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = scratch._inner
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        exemplar_raw = {ci: ow.load_strokes(drawer_files[ci][ex_drawer]) for ci in range(WAY)}
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            r_ = _armf_episode(native, scratch, qn, node_of_cand, exemplar_raw, path,
                                threshold, w_f)
            full_pairs = r_["full_pairs"]
            true_err = full_pairs[qi][0]
            rest = [p for p in full_pairs if p[1] != qi]
            best_imp = (float(native.evaluate(
                {"type": "MinOver", "source": {"type": "Lit", "value": rest}, "var_name": "c",
                 "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                           "index": {"type": "Lit", "value": 0}},
                 "default": {"type": "Lit", "value": 0.0}}, {})) if rest else None)
            margin_ti = (best_imp - true_err) if best_imp is not None else None
            recs.append(dict(true=qi, alph=alph, r=r, pred_full=r_["pred_full"],
                              pred_armf=r_["pred_armf"], correct_full=bool(r_["pred_full"] == qi),
                              correct_armf=bool(r_["pred_armf"] == qi), fired=r_["fired"],
                              cond_margin=r_["margin"], decision=r_["decision"],
                              winner_in_top2=r_.get("winner_in_top2"),
                              n_nonfinite=r_.get("n_nonfinite", 0)))
            margins.append(dict(true=qi, true_err=true_err, best_impostor_err=best_imp,
                                 margin=margin_ti))
    return recs, margins


def stage_eval() -> int:
    print(f"\n{SEP}\n  STAGE: eval (ARM F -- conditional foveation)\n{SEP}")
    calib = _require_calibrate()
    sanity = _require_sanity()
    _require_guard()
    if not sanity["passed"]:
        print("  WALL: sanity STOPPED -- per this run's own binding rule, NO eval budget may "
              "be spent. Report the sanity finding and stop here.")
        return 1
    threshold, w_f = calib["threshold"], calib["w_f"]
    print(f"  threshold={threshold:.6f}  w_f={w_f:.6f}")

    state = _load_json(EVAL_PATH) if os.path.exists(EVAL_PATH) else dict(
        records=[], margins=[], block_idx=0, done=False)
    if state.get("done"):
        print(f"  eval already COMPLETE (n={len(state['records'])}).")
        return 0

    blocks = _blocks()
    print(f"  blocks={len(blocks)} (target n={len(blocks) * WAY})  "
          f"resuming at block {state['block_idx']}  [37C hygiene filter: ON]")

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        alph, r = blocks[i]
        run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
        alph, r = blocks[state["block_idx"]]
        spec = run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)
        bt0 = time.time()
        recs, margins = _run_block_arm_f(alph, r, spec, threshold, w_f)
        for pos, rec in enumerate(recs):
            rec["idx"] = state["block_idx"] * WAY + pos
        for pos, m in enumerate(margins):
            m["idx"] = state["block_idx"] * WAY + pos
        state["records"].extend(recs)
        state["margins"].extend(margins)
        state["block_idx"] += 1
        _save_json(state, EVAL_PATH)
        print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
              f"{len(state['records'])} episodes so far, {time.time()-bt0:.1f}s this block, "
              f"{time.time()-t0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        k_full = sum(1 for rec in state["records"] if rec["correct_full"])
        k_armf = sum(1 for rec in state["records"] if rec["correct_armf"])
        n = len(state["records"])
        state["acc_full"] = dict(acc=k_full / n, ci=list(_wilson(k_full, n)), k=k_full, n=n)
        state["acc_armf"] = dict(acc=k_armf / n, ci=list(_wilson(k_armf, n)), k=k_armf, n=n)
        state["wall_clock_seconds"] = state.get("wall_clock_seconds", 0.0) + (time.time() - t0)
        _save_json(state, EVAL_PATH)
        print(f"\n  EVAL COMPLETE: n={n}  GLOBAL(own recompute) acc={100*k_full/n:.1f}% k={k_full}"
              f"  ARM F acc={100*k_armf/n:.1f}% k={k_armf}")
    else:
        state["wall_clock_seconds"] = state.get("wall_clock_seconds", 0.0) + (time.time() - t0)
        _save_json(state, EVAL_PATH)
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-invoke to "
              f"continue. ({time.time()-t0:.1f}s this call)")
    return 0


# ===================================================================================================
# STAGE: report -- SANITY numbers FIRST, fire-rate, McNemar overall + fired-only, bands,
# margin diagnostics, accuracies + CIs, honest anomalies.
# ===================================================================================================
def _mcnemar(correct_a: list, correct_b: list) -> dict:
    """`fixed`: a WRONG -> b RIGHT. `broken`: a RIGHT -> b WRONG."""
    fixed = sum(1 for a, b in zip(correct_a, correct_b) if (not a) and b)
    broken = sum(1 for a, b in zip(correct_a, correct_b) if a and (not b))
    n_disc = fixed + broken
    p = float(binomtest(fixed, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    return dict(fixed=fixed, broken=broken, discordant=n_disc, p=p)


def stage_report() -> int:
    print(f"\n{SEP}\n  RUN 45 -- CONDITIONAL FOVEATION -- FINAL REPORT (PHASE 4, PLAN CLOSURE)\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_PATH)
    print(f"  seeds/stroke_shapes.json md5 (parallel-session-owned, never written here): "
          f"{md5_now}")

    calib = _require_calibrate()
    sanity = _require_sanity()
    print(f"\n{'='*35}  SANITY-GATE (decides everything)  {'='*35}")
    _print_sanity(sanity)
    print(f"\n  ---- CALIBRATION ----")
    _print_calibrate(calib)

    if not sanity["passed"]:
        print(f"\n  {'='*30}  SANITY STOPPED -- NO EVAL WAS RUN, PER THIS RUN'S OWN BINDING "
              f"RULE  {'='*30}")
        print(f"  (armed background accuracy {100*sanity['acc_armed']:.1f}% fell more than "
              f"{100*sanity['sanity_margin']:.0f}pp below baseline {100*sanity['acc_baseline']:.1f}%)")
        print(f"\n  PLAN CLOSURE: the human-gap plan's FOURTH and final phase STOPS at the "
              f"free background-sanity gate -- no eval budget spent. Phases 1-3 remain the "
              f"plan's own record (P1 style-norm harm, P2/P2b deformation-metric catastrophic-"
              f"then-null, P3 exemplar-expansion null); P4 adds a background-sanity STOP as its "
              f"own honest result.")
        return 0

    guard = _require_guard()
    if not os.path.exists(EVAL_PATH) or not _load_json(EVAL_PATH).get("done"):
        print("  WALL: sanity PASSED but --stage eval has not completed yet -- run it, then "
              "re-run report.")
        sys.exit(1)
    ev = _load_json(EVAL_PATH)
    records = ev["records"]
    n = len(records)
    print(f"\n  n={n}")

    k_full = sum(1 for r_ in records if r_["correct_full"])
    global_ok = (k_full == BASELINE_FULL_DWELL["k"])
    print(f"\n  GLOBAL (protocol re-check, this run's own recompute): k={k_full}/{n} "
          f"(must equal cited k={BASELINE_FULL_DWELL['k']}) -- "
          f"{'MATCH' if global_ok else 'MISMATCH -- STOP, protocol bug, do not trust ARM F'}")
    if not global_ok:
        return 1

    fired_recs = [r_ for r_ in records if r_["fired"]]
    n_fired = len(fired_recs)
    print(f"\n  ---- FIRE RATE ----")
    print(f"    fired: {n_fired}/{n} = {100*n_fired/n:.1f}%  "
          f"(threshold={calib['threshold']:.6f}, background p{calib['margin_pctl']:.0f})")
    decisions = Counter(r_["decision"] for r_ in fired_recs)
    print(f"    decision breakdown among fired episodes: {dict(decisions)}")
    escaped = sum(1 for r_ in fired_recs if r_.get("winner_in_top2") is False)
    print(f"    fired episodes where ARM F's winner escaped the ORIGINAL top-2 "
          f"(w_f pushed BOTH top-2 candidates behind a third): {escaped}/{n_fired}")
    n_nonfinite_total = sum(r_.get("n_nonfinite", 0) or 0 for r_ in records)
    print(f"    total non-finite region-score floor engagements (honest anomaly counter): "
          f"{n_nonfinite_total}")

    # ---- Non-fired structural identity check. ------------------------------------------------
    nonfired_mismatches = [r_ for r_ in records if not r_["fired"]
                            and r_["pred_full"] != r_["pred_armf"]]
    print(f"\n  ---- STRUCTURAL CHECK ----")
    print(f"    non-fired episodes with pred_full != pred_armf: {len(nonfired_mismatches)}/"
          f"{n - n_fired} (must be 0 -- `supplement_pairs` with an empty terms dict is a no-op)")

    correct_full = [r_["correct_full"] for r_ in records]
    correct_armf = [r_["correct_armf"] for r_ in records]
    k_armf = sum(correct_armf)

    mc_overall = _mcnemar(correct_full, correct_armf)
    print(f"\n  ---- McNEMAR OVERALL (n={n}) ----")
    print(f"    GLOBAL: k={k_full}/{n}  ARM F: k={k_armf}/{n}")
    print(f"    fixed={mc_overall['fixed']}  broken={mc_overall['broken']}  "
          f"discordant={mc_overall['discordant']}  p={mc_overall['p']:.4g}")
    if mc_overall["discordant"] and mc_overall["broken"] >= mc_overall["fixed"]:
        print(f"    STOP CONDITION: broken >= fixed overall -- the mechanism HARMS or is a "
              f"wash. Per pre-registration this is reported as the finding, never re-tuned.")
    elif mc_overall["discordant"]:
        print(f"    fixed > broken overall: the mechanism nets POSITIVE on this sample.")
    else:
        print(f"    no discordant pairs at all.")

    correct_full_fired = [r_["correct_full"] for r_ in fired_recs]
    correct_armf_fired = [r_["correct_armf"] for r_ in fired_recs]
    mc_fired = _mcnemar(correct_full_fired, correct_armf_fired) if fired_recs else dict(
        fixed=0, broken=0, discordant=0, p=1.0)
    print(f"\n  ---- McNEMAR RESTRICTED TO FIRED EPISODES (n={n_fired}) ----")
    print(f"    fixed={mc_fired['fixed']}  broken={mc_fired['broken']}  "
          f"discordant={mc_fired['discordant']}  p={mc_fired['p']:.4g}")

    ci_full = _wilson(k_full, n)
    ci_armf = _wilson(k_armf, n)
    print(f"\n  ---- ACCURACIES (Wilson 95% CI) ----")
    print(f"    GLOBAL: acc={100*k_full/n:.1f}%  [{100*ci_full[0]:.1f}%, {100*ci_full[1]:.1f}%]  "
          f"k={k_full}/{n}")
    print(f"    ARM F:  acc={100*k_armf/n:.1f}%  [{100*ci_armf[0]:.1f}%, {100*ci_armf[1]:.1f}%]  "
          f"k={k_armf}/{n}")
    print(f"    CI-separated: {gate._ci_separated(tuple(ci_armf), tuple(ci_full))}  (McNemar "
          f"above is the powered test for this effect size)")

    # ---- run40 band / rank concentration (idx-joined, read-only, coverage caveat). ------------
    classify_path = os.path.join(RUN40_DIR, "classify.json")
    classify = _load_json(classify_path) if os.path.exists(classify_path) else {"rows": []}
    classify_by_idx = {row["idx"]: row for row in classify["rows"]}
    print(f"\n  run40 classify.json: {len(classify_by_idx)}/{n} idx-labelled episodes "
          f"(READ-ONLY reference, coverage caveat: {len(classify_by_idx)}/{n})")
    fixed_idx = {r_["idx"] for r_ in records if (not r_["correct_full"]) and r_["correct_armf"]}
    broken_idx = {r_["idx"] for r_ in records if r_["correct_full"] and (not r_["correct_armf"])}
    band_counts: dict = defaultdict(Counter)
    for r_ in records:
        row = classify_by_idx.get(r_["idx"])
        if row is None:
            continue
        if r_["idx"] in fixed_idx:
            band_counts[row["band"]]["fixed"] += 1
        elif r_["idx"] in broken_idx:
            band_counts[row["band"]]["broken"] += 1
        else:
            band_counts[row["band"]]["unchanged"] += 1
    print(f"\n  ---- PER-BAND fixed/broken/unchanged (restricted to classified episodes) ----")
    for band in ("near", "mid", "far", "control"):
        c = band_counts.get(band, Counter())
        print(f"    {band:<8} fixed={c['fixed']:<3} broken={c['broken']:<3} "
              f"unchanged={c['unchanged']:<3}")

    print(f"\n  ---- PER-ALPHABET fixed/broken (fixed - broken net) ----")
    alph_counts: dict = defaultdict(Counter)
    for r_ in records:
        if r_["idx"] in fixed_idx:
            alph_counts[r_["alph"]]["fixed"] += 1
        elif r_["idx"] in broken_idx:
            alph_counts[r_["alph"]]["broken"] += 1
    for a in sorted(alph_counts):
        c = alph_counts[a]
        print(f"    {a:<24} fixed={c['fixed']:<3} broken={c['broken']:<3} "
              f"net={c['fixed']-c['broken']:+d}")

    # ---- Margin-shift on GUARD-passed, FIRED episodes (this mechanism's own success shape). --
    guard_margins_by_idx = {m["idx"]: m for m in guard["margins"]}
    arm_margins_by_idx = {m["idx"]: m for m in ev["margins"]}
    fired_idx_set = {r_["idx"] for r_ in fired_recs}
    guard_pass_fired_idx = [r_["idx"] for r_ in records
                             if r_["correct_full"] and r_["idx"] in fired_idx_set]
    deltas = []
    for i in guard_pass_fired_idx:
        gm_, am_ = guard_margins_by_idx.get(i), arm_margins_by_idx.get(i)
        if gm_ is None or am_ is None or gm_.get("margin") is None or am_.get("margin") is None:
            continue
        deltas.append(am_["margin"] - gm_["margin"])
    print(f"\n  ---- MARGIN-SHIFT DIAGNOSTIC (true-vs-best-impostor margin, GUARD-passed AND "
          f"FIRED episodes, ARM F vs 44a's GUARD) ----")
    if deltas:
        arr = np.array(deltas)
        print(f"    n={len(arr)}  mean(armf_margin - guard_margin)={arr.mean():+.5f}  "
              f"median={np.median(arr):+.5f}  std={arr.std():.5f}")
        print(f"    {'WIDENS' if arr.mean() > 0 else 'TIGHTENS'} the margin on average")
        print(f"    fraction WIDENED: {100*np.mean(arr > 0):.1f}%")
    else:
        print(f"    n=0 -- no GUARD-passed+fired episodes with both margins available.")

    out = dict(n=n, n_fired=n_fired, decisions=dict(decisions), escaped=escaped,
               n_nonfinite_total=n_nonfinite_total, mcnemar_overall=mc_overall,
               mcnemar_fired=mc_fired, acc_full=dict(acc=k_full/n, ci=list(ci_full), k=k_full),
               acc_armf=dict(acc=k_armf/n, ci=list(ci_armf), k=k_armf),
               band_counts={b: dict(c) for b, c in band_counts.items()},
               alph_counts={a: dict(c) for a, c in alph_counts.items()},
               margin_shift_n=len(deltas),
               margin_shift_mean=float(np.mean(deltas)) if deltas else None,
               nonfired_mismatches=len(nonfired_mismatches))
    _save_json(out, REPORT_PATH)
    print(f"\n  report.json written.")

    print(f"\n  {'='*30}  PLAN CLOSURE  {'='*30}")
    if mc_overall["discordant"] and mc_overall["fixed"] > mc_overall["broken"] and \
            gate._ci_separated(tuple(ci_armf), tuple(ci_full)):
        print(f"  WIN: the near-band's first crack across the 4-phase human-gap plan.")
    elif mc_overall["discordant"] and mc_overall["broken"] >= mc_overall["fixed"]:
        print(f"  HARM: RUN 45 stops per its own pre-registered STOP condition (broken >= "
              f"fixed). The human-gap plan closes with all four phases measured: P1 style-norm "
              f"harm, P2 metric catastrophic-then-null (P2b spread-matched), P3 exemplar-"
              f"expansion null, P4 conditional-foveation harm/null.")
    else:
        print(f"  NULL: no CI-separated or McNemar-significant effect. The human-gap plan "
              f"closes with all four phases measured and none moving the 80.5% verdict "
              f"ceiling beyond noise.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  seeds/stroke_shapes.json md5 (post-run, must equal the pre-run value above): "
          f"{_md5(STROKE_SHAPES_PATH)}")
    return 0


STAGES = {"calibrate": stage_calibrate, "sanity": stage_sanity, "guard": stage_guard,
          "eval": stage_eval, "report": stage_report}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=list(STAGES.keys()))
    args = ap.parse_args()
    t0 = time.time()
    rc = STAGES[args.stage]()
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
