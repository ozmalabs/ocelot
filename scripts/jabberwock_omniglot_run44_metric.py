"""OMNIGLOT RUN 44, PHASE 2 -- THE LAST UNTRIED VERDICT-CHANGE CLASS: A BACKGROUND-LEARNED
DEFORMATION METRIC (change what the comparator CHARGES, not what it sees).

THE STANDING PROBLEM (nine prior attempts, all null against the SAME 80.5% [76.3, 84.1] @
n=400 GUARD, `results/run26_checkpoints/eval_baseline.json`): six RUN 25-era verdict-lever
nulls, RUN 34b upstream denoise, RUN 39b orthogonal supplement, RUN 43 nuisance expansion --
every one changed the EVIDENCE the comparator sees or its weighting. None changed the DISTANCE
FUNCTION itself with background discriminative information.

THE MECHANISM (`domains/deform_metric.py`'s own module docstring has the full derivation --
this header states the run's arms/gate only): the standing GUARD verdict
(`domains.abs_read.parse_marginal_verdict` -> `recognition_graph.predict_smooth_marginal_sc_
term`) fuses `smoothdeform_error(s,w) [whole-figure SmoothDeformDist] + part_w * marginal_part_
error(s,w) [per-part PointSetDist, parse-marginalised] + sc_w * shapecontext_error(s,w) [whole-
figure ShapeContextDist]`. CORRECTION TO THE LAUNCH BRIEF (stated up front, this arc's own
honesty law): the brief names `TpsDeformDist`/`ShapeContextDist` as "what the comparator sums"
-- reading the actual standing verdict shows the whole-figure warp term is `SmoothDeformDist`
(a free-form-deformation field), NOT `TpsDeformDist` (a different, non-adopted verdict this arc
tried earlier). `SmoothDeformDist`'s own distortion-cost regulariser (`residual + 1.5 * dc`,
`dc` = mean squared TOTAL displacement) prices every direction of displacement identically -- a
writer-typical global rotation/shear costs exactly as much per unit displacement as genuine
non-affine bending. A NEW additive Rust Term, `SmoothDeformComponents` (`runners/dsl/src/
deform_metric.rs`, `smooth_deform_dist` itself untouched), decomposes the SAME FFD field into
an affine part (rotation/shear/log-scale/translation, closed-form least squares) and the
non-affine "bending" residual. ARM M's reweighted comparator REPLACES ONLY the smoothdeform
sub-term:

    reweighted_smoothdeform(s,w) = residual + w_bend*bending
                                  + rotation^2/sigma_rotation^2 + shear^2/sigma_shear^2

`marginal_part_error`/`shapecontext_error` are UNCHANGED (no warp/affine structure to
decompose -- out of this mechanism's scope, `deform_metric.py`'s own doc names this explicitly).
`sigma_rotation`/`sigma_shear` are FRESH background pairwise stds (`domains.deform_metric.
calibrate_affine_sigmas`, the SAME `SmoothDeformComponents` Term, on same-class pairs from the
5 LEARN alphabets -- NOT a literal reuse of RUN 43's `calibration.json` numbers, which measure a
DIFFERENT quantity; see `deform_metric.py`'s own doc for the units-mismatch rationale. RUN 43's
numbers are still READ (read-only) into this run's own report as a qualitative cross-check).
`w_bend` is calibrated ONCE on BACKGROUND 20-way one-shot episodes (the SAME 5 LEARN alphabets,
`evaluation`-split TEST alphabets never touched) over a PRE-REGISTERED grid, frozen before the
real eval ever runs:

    W_BEND_GRID = (0.5, 1.5, 3.0, 6.0, 12.0, 24.0)   -- anchored on SmoothDeformDist's OWN
                                                          pre-existing 1.5 magic constant,
                                                          halved/doubled outward. Winner picked
                                                          by a held Argmax over background
                                                          accuracy (never a bare Python max()).

ARMS (run-26 protocol: `scripts.jabberwock_omniglot_run25_number._block_spec`, POWER_SEED,
byte-identical block order -- alph OUTER, r INNER, 10 alphabets x R_TARGET=2 -> n=400):
  GUARD -- byte-identical reproduction of RUN 25/26's own C0 control, but exposed as a PER-PAIR
           `Argmin` (`ar.parse_marginal_pair_error` + held `Argmin` over the 20 candidates,
           PROVEN identical to `ar.parse_marginal_verdict`'s own internal Argmax on a live
           sub-sample before this run trusted it for the full n=400 -- `Argmax(-err) ==
           Argmin(err)` by construction, `abs_read.py`'s own doc) so a per-episode MARGIN
           (best-impostor-error minus true-error) is available for BOTH arms, the same
           instrument RUN 43 used. Must reproduce 80.5% / k=322 / n=400 EXACTLY.
  ARM M -- the reweighted metric: `domains.deform_metric.reweighted_pair_error` in place of
           `ar.parse_marginal_pair_error`, SAME staging (`ar.stage_parse_char`,
           `run25._stage_candidates`), SAME held-Argmin-over-pairs idiom.

PRIMARY ANALYSIS (pre-registered): paired McNemar (exact binomial on discordant pairs), ARM M
vs GUARD/GLOBAL. PREDICTIONS: fixes concentrate in the NEAR band (`results/run40_checkpoints/
classify.json`, READ-ONLY, idx-joined -- RUN 40's own finding: near-band errors are genuine
geometric near-duplicates, exactly what a sharper metric buys via arbitration) and in Ge_ez/
Kannada (RUN 43's own named alphabets); broken should NOT concentrate anywhere (a better metric
should not manufacture confusions). STOP (pre-registered, no retuning against eval): broken >=
fixed -> ARM M harms, stop, report as the finding, no reweighting against eval.

ALSO REPORTED: the margin-shift diagnostic (on GUARD-correct episodes, does ARM M's own margin
WIDEN vs GUARD's -- the opposite of RUN 43's dilution, this run's OWN success criterion at the
per-episode level); the calibrated sigmas + w_bend grid curve; the component-variance
(engagement) table; per-alphabet accuracy; wall-clock.

EXECUTION (ops law, binding): every invocation <=540s foreground, per-block checkpointing under
`results/run44_checkpoints/` (run26/run40/run43 checkpoint dirs READ-ONLY references, never
written here). `.venv` python (needs `substrate_rs`) for every stage. No LLM call; donkey=0 not
applicable (no torch in this arc's dependency graph).

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run44_metric.py --stage calibrate
  ... --stage tune_wbend
  ... --stage guard
  ... --stage armm
  ... --stage report
"""
from __future__ import annotations

import argparse
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
from scripts.jabberwock_omniglot_run37c_hygiene import DropDegenerateFilter
from domains import abs_read as ar
from domains import deform_metric as dm
from domains import omniglot_world as ow

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run44_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")   # READ-ONLY reference.
RUN40_DIR = os.path.join(ROOT, "results", "run40_checkpoints")   # READ-ONLY reference.
RUN43_DIR = os.path.join(ROOT, "results", "run43_checkpoints")   # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

WAY = run25.WAY                                       # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET   # 20
R_TARGET = run25.R_TARGET                             # 2  -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS             # 10
POWER_SEED = run25.POWER_SEED                         # gate.SEED + 1500, byte-identical
GUARD_CONTROL = dict(acc=0.805, k=322, n=400)         # results/run26_checkpoints/eval_baseline.json

PART_W = ar.DEFAULT_PARSE_PART_W
SC_W = ar.DEFAULT_PARSE_SC_W
BETA = ar.DEFAULT_PARSE_BETA

CALIB_PATH = os.path.join(CKPT_DIR, "calibration.json")
WBEND_PATH = os.path.join(CKPT_DIR, "wbend.json")
PER_CALL_BUDGET_SECONDS = 460.0                       # leaves >120s headroom under the 590s cap.

# PRE-REGISTERED w_bend grid (stated in this module's own docstring above, before any
# background accuracy number exists) -- anchored on SmoothDeformDist's own pre-existing 1.5
# magic constant for the (structurally different, but same-order-of-magnitude) `dc` term.
W_BEND_GRID = (0.5, 1.5, 3.0, 6.0, 12.0, 24.0)
BACKGROUND_R_TARGET = 1        # 5 LEARN alphabets x 1 rep -> n=100 per grid point, PRE-REGISTERED.


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _wilson(k: int, n: int):
    return gate.wilson_ci(k, n)


def _test_alphabets() -> list:
    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= WAY)
    return qualifying[:N_TEST_ALPHABETS]


def _blocks() -> list:
    """alph OUTER, r INNER -- byte-identical order to run25/run26/run40/run43's own eval block
    order, so `idx = block_idx * 20 + qi` lines up with `results/run26_checkpoints/eval_
    baseline.json` and `results/run40_checkpoints/classify.json`'s own `idx` convention."""
    test_alphabets = _test_alphabets()
    return [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]


def _background_alphabets() -> list:
    """The SAME 5 LEARN alphabets `deform_metric.calibrate_affine_sigmas`/`exemplar_expand.
    calibrate_background` use (`ow.alphabets("background")[:DEFAULT_LEARN_N]`) -- verified
    (this run's own calibrate stage) each has >=20 characters, qualifying for a 20-way block."""
    return ow.alphabets("background")[:dm.DEFAULT_LEARN_N]


def _background_blocks() -> list:
    alphs = _background_alphabets()
    return [(alph, r) for alph in alphs for r in range(BACKGROUND_R_TARGET)]


def _block_spec_split(alph: str, rng, way: int, episodes_per_alphabet: int, split: str) -> dict:
    """`run25._block_spec`'s own body, `split` threaded through instead of hardcoded
    `"evaluation"` -- lets `tune_wbend` draw background-split blocks via the IDENTICAL
    character-selection/exemplar-drawer/query-drawer logic (deterministic-seed reproducibility)
    the real eval already uses, just pointed at a different, non-overlapping split."""
    chars = sorted(ow.characters(alph, split))[:way]
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


# ===================================================================================================
# Held Term builders -- duplicated locally per this codebase's own established convention.
# ===================================================================================================
def _argmin_pairs_term(pairs) -> dict:
    return {"type": "Argmin", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


def _argmax_pairs_term(pairs) -> dict:
    return {"type": "Argmax", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


def _min_score_term(pairs) -> dict:
    return {"type": "MinOver", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}},
            "default": {"type": "Lit", "value": 0.0}}


# ===================================================================================================
# STAGE: calibrate -- freeze `deform_metric`'s pairwise affine sigmas; report RUN 43's own
# numbers alongside (read-only cross-check, NOT fed into this run's sigmas).
# ===================================================================================================
def stage_calibrate() -> int:
    print(f"\n{SEP}\n  STAGE: calibrate\n{SEP}")
    scratch = srs.Substrate()
    native = getattr(scratch, "_inner", scratch)
    fresh = not os.path.exists(CALIB_PATH)
    t0 = time.time()
    calib = dm.calibrate_or_load(native, CALIB_PATH)
    dt = time.time() - t0
    print(f"  {'COMPUTED + FROZEN' if fresh else 'READ FROZEN'} ({dt:.2f}s): {CALIB_PATH}")
    print(f"  learn_alphabets: {calib['learn_alphabets']}")
    print(f"  n_classes={calib['n_classes']}  n_pairs={calib['n_pairs']}")
    print(f"  rotation_std = {calib['rotation_std']:.4f} rad "
          f"({np.degrees(calib['rotation_std']):.2f} deg)  mean={calib['rotation_mean']:+.5f}")
    print(f"  shear_std    = {calib['shear_std']:.4f}  mean={calib['shear_mean']:+.5f}")
    print(f"  bending_mean = {calib['bending_mean']:.6f}  bending_std = {calib['bending_std']:.6f}")

    run43_calib_path = os.path.join(RUN43_DIR, "calibration.json")
    if os.path.exists(run43_calib_path):
        r43 = _load_json(run43_calib_path)
        print(f"\n  RUN 43 calibration.json (READ-ONLY cross-reference, DIFFERENT estimator -- "
              f"per-glyph-vs-class-mean, not pairwise -- see deform_metric.py's own doc for why "
              f"this run does NOT feed these numbers directly into its own sigmas):")
        print(f"    shear_std={r43['shear_std']:.4f}  rotation_std={r43['rotation_std']:.4f} rad "
              f"({np.degrees(r43['rotation_std']):.2f} deg)")
    else:
        print("\n  (run43 calibration.json not found -- cross-reference skipped, not required)")
    return 0


def _require_calib() -> dict:
    if not os.path.exists(CALIB_PATH):
        print("  WALL: run --stage calibrate first.")
        sys.exit(1)
    return dm.load_calibration(CALIB_PATH)


# ===================================================================================================
# STAGE: tune_wbend -- background 20-way one-shot episodes (5 LEARN alphabets, evaluation-split
# TEST alphabets never touched), pre-registered grid, held Argmax over background accuracy.
# ===================================================================================================
def _run_background_block(alph: str, r: int, spec: dict, w_bend: float, sigma_rotation: float,
                           sigma_shear: float) -> list:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    recs = []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = getattr(scratch, "_inner", scratch)
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            pairs = [(dm.reweighted_pair_error(scratch, qn, node_of_cand[ci], w_bend=w_bend,
                                                sigma_rotation=sigma_rotation,
                                                sigma_shear=sigma_shear, part_w=PART_W,
                                                sc_w=SC_W, beta=BETA), ci)
                     for ci in range(WAY)]
            winner = native.evaluate(_argmin_pairs_term(pairs), {})
            pred = int(winner[1]) if winner is not None else -1
            recs.append(dict(true=qi, correct=bool(pred == qi)))
    return recs


def stage_tune_wbend() -> int:
    print(f"\n{SEP}\n  STAGE: tune_wbend\n{SEP}")
    if os.path.exists(WBEND_PATH):
        frozen = _load_json(WBEND_PATH)
        print(f"  ALREADY FROZEN: w_bend={frozen['w_bend']} ({WBEND_PATH})")
        print(f"  grid results: {frozen['grid_results']}")
        return 0
    calib = _require_calib()
    sigma_rotation, sigma_shear = dm.sigma_from_calibration(calib)
    print(f"  sigma_rotation={sigma_rotation:.4f}  sigma_shear={sigma_shear:.4f}  "
          f"grid={W_BEND_GRID}  background alphabets={_background_alphabets()}")

    out_path = _ckpt("tune_wbend_state.json")
    blocks = _background_blocks()
    n_target = len(blocks) * WAY
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        grid_idx=0, block_idx=0, records_by_grid={str(w): [] for w in W_BEND_GRID}, done=False)

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["grid_idx"] < len(W_BEND_GRID) and time.time() < hard_deadline:
        w_bend = W_BEND_GRID[state["grid_idx"]]
        rng = np.random.default_rng(POWER_SEED)  # SAME seed every grid point -- same episodes.
        for i in range(state["block_idx"]):
            _block_spec_split(blocks[i][0], rng, WAY, EPISODES_PER_ALPHABET, "background")
        while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
            alph, r = blocks[state["block_idx"]]
            spec = _block_spec_split(alph, rng, WAY, EPISODES_PER_ALPHABET, "background")
            recs = _run_background_block(alph, r, spec, w_bend, sigma_rotation, sigma_shear)
            state["records_by_grid"][str(w_bend)].extend(recs)
            state["block_idx"] += 1
            _save_json(state, out_path)
            n_so_far = len(state["records_by_grid"][str(w_bend)])
            print(f"  w_bend={w_bend:<5} block {state['block_idx']}/{len(blocks)} "
                  f"({alph!r}) -- {n_so_far} episodes, {time.time()-t0:.1f}s this call")
        if state["block_idx"] >= len(blocks):
            state["grid_idx"] += 1
            state["block_idx"] = 0
            _save_json(state, out_path)

    if state["grid_idx"] >= len(W_BEND_GRID):
        grid_results = []
        for w in W_BEND_GRID:
            recs = state["records_by_grid"][str(w)]
            k = sum(1 for r in recs if r["correct"])
            n = len(recs)
            grid_results.append(dict(w_bend=w, acc=k / n if n else 0.0, k=k, n=n))
        pairs = [(g["acc"], i) for i, g in enumerate(grid_results)]
        scratch = srs.Substrate()
        native = getattr(scratch, "_inner", scratch)
        winner = native.evaluate(_argmax_pairs_term(pairs), {})
        best_idx = int(winner[1]) if winner is not None else 0
        frozen = dict(w_bend=grid_results[best_idx]["w_bend"], grid_results=grid_results,
                      sigma_rotation=sigma_rotation, sigma_shear=sigma_shear,
                      background_n=n_target)
        _save_json(frozen, WBEND_PATH)
        print(f"\n  FROZEN w_bend = {frozen['w_bend']} -- {WBEND_PATH}")
        for g in grid_results:
            marker = " <== WINNER" if g["w_bend"] == frozen["w_bend"] else ""
            print(f"    w_bend={g['w_bend']:<6} acc={100*g['acc']:.1f}%  k={g['k']}/{g['n']}{marker}")
    else:
        print(f"\n  PARTIAL: grid_idx={state['grid_idx']}/{len(W_BEND_GRID)} "
              f"block_idx={state['block_idx']}/{len(blocks)} -- re-invoke to continue.")
    return 0


def _require_wbend() -> dict:
    if not os.path.exists(WBEND_PATH):
        print("  WALL: run --stage tune_wbend to completion first.")
        sys.exit(1)
    return _load_json(WBEND_PATH)


# ===================================================================================================
# STAGE: guard / armm -- the real eval, byte-identical staging, per-pair Argmin + margins.
# ===================================================================================================
def _run_block_guard(alph: str, r: int, spec: dict) -> tuple:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    recs, margins = [], []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = getattr(scratch, "_inner", scratch)
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            pairs = [(ar.parse_marginal_pair_error(scratch, qn, node_of_cand[ci],
                                                    part_w=PART_W, sc_w=SC_W, beta=BETA), ci)
                     for ci in range(WAY)]
            winner = native.evaluate(_argmin_pairs_term(pairs), {})
            pred = int(winner[1]) if winner is not None else -1
            true_err = pairs[qi][0]
            rest = [p for p in pairs if p[1] != qi]
            best_imp = float(native.evaluate(_min_score_term(rest), {})) if rest else None
            margin = (best_imp - true_err) if best_imp is not None else None
            recs.append(dict(true=qi, alph=alph, r=r, pred=pred, correct=bool(pred == qi)))
            margins.append(dict(true=qi, true_err=true_err, best_impostor_err=best_imp,
                                 margin=margin))
    return recs, margins


def _run_block_armm(alph: str, r: int, spec: dict, w_bend: float, sigma_rotation: float,
                     sigma_shear: float) -> tuple:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    recs, margins = [], []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = getattr(scratch, "_inner", scratch)
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            pairs = [(dm.reweighted_pair_error(scratch, qn, node_of_cand[ci], w_bend=w_bend,
                                                sigma_rotation=sigma_rotation,
                                                sigma_shear=sigma_shear, part_w=PART_W,
                                                sc_w=SC_W, beta=BETA), ci)
                     for ci in range(WAY)]
            winner = native.evaluate(_argmin_pairs_term(pairs), {})
            pred = int(winner[1]) if winner is not None else -1
            true_err = pairs[qi][0]
            rest = [p for p in pairs if p[1] != qi]
            best_imp = float(native.evaluate(_min_score_term(rest), {})) if rest else None
            margin = (best_imp - true_err) if best_imp is not None else None
            recs.append(dict(true=qi, alph=alph, r=r, pred=pred, correct=bool(pred == qi)))
            margins.append(dict(true=qi, true_err=true_err, best_impostor_err=best_imp,
                                 margin=margin))
    return recs, margins


def _stage_eval_generic(name: str, block_fn) -> int:
    print(f"\n{SEP}\n  STAGE: eval-{name}\n{SEP}")
    out_path = _ckpt(f"eval_{name}.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], margins=[], block_idx=0, done=False)

    if state.get("done"):
        print(f"  eval-{name} already COMPLETE (n={len(state['records'])}).")
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
        recs, margins = block_fn(alph, r, spec)
        for pos, rec in enumerate(recs):
            rec["idx"] = state["block_idx"] * WAY + pos
        for pos, m in enumerate(margins):
            m["idx"] = state["block_idx"] * WAY + pos
        state["records"].extend(recs)
        state["margins"].extend(margins)
        state["block_idx"] += 1
        _save_json(state, out_path)
        print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
              f"{len(state['records'])} episodes so far, {time.time()-bt0:.1f}s this block, "
              f"{time.time()-t0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        k = sum(1 for rec in state["records"] if rec["correct"])
        n = len(state["records"])
        ci = _wilson(k, n)
        state["acc"] = dict(acc=k / n, ci=list(ci), k=k, n=n)
        state["wall_clock_seconds"] = state.get("wall_clock_seconds", 0.0) + (time.time() - t0)
        _save_json(state, out_path)
        print(f"\n  EVAL COMPLETE for {name}: n={n}  acc={100*k/n:.1f}%  "
              f"95% CI [{100*ci[0]:.1f}%, {100*ci[1]:.1f}%]  k={k}")
        if name == "guard":
            ok = (k == GUARD_CONTROL["k"] and n == GUARD_CONTROL["n"])
            print(f"  GUARD vs standing control (acc={100*GUARD_CONTROL['acc']:.1f}%, "
                  f"k={GUARD_CONTROL['k']}, n={GUARD_CONTROL['n']}): "
                  f"{'PASS -- reproduced exactly' if ok else 'FAIL -- STOP, do not trust downstream'}")
    else:
        state["wall_clock_seconds"] = state.get("wall_clock_seconds", 0.0) + (time.time() - t0)
        _save_json(state, out_path)
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-invoke to "
              f"continue. ({time.time()-t0:.1f}s this call)")
    return 0


def stage_guard() -> int:
    return _stage_eval_generic("guard", lambda a, r, spec: _run_block_guard(a, r, spec))


def stage_armm() -> int:
    calib = _require_calib()
    wbend = _require_wbend()
    sigma_rotation, sigma_shear = dm.sigma_from_calibration(calib)
    return _stage_eval_generic(
        "armm", lambda a, r, spec: _run_block_armm(
            a, r, spec, wbend["w_bend"], sigma_rotation, sigma_shear))


# ===================================================================================================
# STAGE: report -- McNemar FIRST, near-band + margin-shift diagnostics, calibration, wall-clock.
# ===================================================================================================
def _require(name: str) -> dict:
    p = _ckpt(f"eval_{name}.json")
    if not os.path.exists(p):
        print(f"  WALL: run --stage {name} to completion first.")
        sys.exit(1)
    d = _load_json(p)
    if not d.get("done"):
        print(f"  WALL: eval-{name} not yet COMPLETE ({d['block_idx']}/20 blocks) -- resume it "
              f"first.")
        sys.exit(1)
    return d


def _mcnemar(base_correct: list, arm_correct: list) -> dict:
    fixed = sum(1 for b, a in zip(base_correct, arm_correct) if (not b) and a)
    broken = sum(1 for b, a in zip(base_correct, arm_correct) if b and (not a))
    n_disc = fixed + broken
    p = float(binomtest(fixed, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    return dict(fixed=fixed, broken=broken, discordant=n_disc, p=p)


def stage_report() -> int:
    print(f"\n{SEP}\n  STAGE: report\n{SEP}")
    calib = _require_calib()
    wbend = _require_wbend()
    guard = _require("guard")
    armm = _require("armm")
    n = len(guard["records"])
    assert n == len(armm["records"]), f"guard n={n} != armm n={len(armm['records'])}"

    guard_correct = [None] * n
    guard_alph = [None] * n
    for rec in guard["records"]:
        guard_correct[rec["idx"]] = rec["correct"]
        guard_alph[rec["idx"]] = rec["alph"]
    armm_correct = [None] * n
    for rec in armm["records"]:
        armm_correct[rec["idx"]] = rec["correct"]

    classify_path = os.path.join(RUN40_DIR, "classify.json")
    classify = _load_json(classify_path) if os.path.exists(classify_path) else {"rows": []}
    classify_rows_by_idx = {row["idx"]: row for row in classify["rows"]}
    print(f"  run40 classify.json: {len(classify_rows_by_idx)} idx-labelled episodes "
          f"(READ-ONLY reference, {classify_path})")

    all_idx = list(range(n))
    mc = _mcnemar(guard_correct, armm_correct)
    fixed_idx = {i for i in all_idx if (not guard_correct[i]) and armm_correct[i]}
    broken_idx = {i for i in all_idx if guard_correct[i] and (not armm_correct[i])}

    k_arm = sum(1 for c in armm_correct if c)
    ci_arm = _wilson(k_arm, n)
    k_guard = sum(guard_correct)
    ci_guard = _wilson(k_guard, n)

    print(f"\n  ---- McNEMAR: ARM M vs GUARD/GLOBAL (PRIMARY) ----")
    print(f"    GUARD accuracy: {100*k_guard/n:.1f}% [{100*ci_guard[0]:.1f}, {100*ci_guard[1]:.1f}]"
          f"  k={k_guard}/{n}")
    print(f"    ARM M accuracy: {100*k_arm/n:.1f}% [{100*ci_arm[0]:.1f}, {100*ci_arm[1]:.1f}]"
          f"  k={k_arm}/{n}")
    print(f"    McNemar: fixed={mc['fixed']}  broken={mc['broken']}  "
          f"discordant={mc['discordant']}  p={mc['p']:.4g}   "
          f"{'ARM M HARMS -- STOP' if mc['broken'] >= mc['fixed'] and mc['discordant'] else 'ok'}")

    band_counts = defaultdict(lambda: Counter())
    for i in all_idx:
        row = classify_rows_by_idx.get(i)
        if row is None:
            continue
        if i in fixed_idx:
            band_counts[row["band"]]["fixed"] += 1
        elif i in broken_idx:
            band_counts[row["band"]]["broken"] += 1
        else:
            band_counts[row["band"]]["unchanged"] += 1
    print(f"\n  ---- PER-BAND fixed/broken/unchanged (RESTRICTED to the "
          f"{len(classify_rows_by_idx)}/{n} run-40-classified episodes) ----")
    for band in ("near", "mid", "far", "control"):
        c = band_counts.get(band, Counter())
        print(f"    {band:<8} fixed={c['fixed']:<3} broken={c['broken']:<3} "
              f"unchanged={c['unchanged']:<3}")

    print(f"\n  ---- PER-ALPHABET fixed/broken (fixed - broken net, alphabets named in the "
          f"pre-registered prediction: Ge_ez, Kannada) ----")
    alph_counts = defaultdict(lambda: Counter())
    for i in all_idx:
        a = guard_alph[i]
        if i in fixed_idx:
            alph_counts[a]["fixed"] += 1
        elif i in broken_idx:
            alph_counts[a]["broken"] += 1
    for a in sorted(alph_counts):
        c = alph_counts[a]
        print(f"    {a:<24} fixed={c['fixed']:<3} broken={c['broken']:<3} "
              f"net={c['fixed']-c['broken']:+d}")

    print(f"\n  ---- CALIBRATION (frozen, {calib['n_classes']} classes / {calib['n_pairs']} "
          f"pairs, {calib['learn_alphabets']}) ----")
    print(f"    sigma_rotation = {calib['rotation_std']:.4f} rad "
          f"({np.degrees(calib['rotation_std']):.2f} deg)   sigma_shear = {calib['shear_std']:.4f}")
    print(f"    rotation_mean = {calib['rotation_mean']:+.5f}  shear_mean = {calib['shear_mean']:+.5f}"
          f"  (should sit near 0 -- writer variation is symmetric)")
    print(f"    bending_mean (background, genuine same-class pairs) = {calib['bending_mean']:.6f}"
          f"  bending_std = {calib['bending_std']:.6f}")
    engaged = min(calib["rotation_std"], calib["shear_std"]) > 0.01
    print(f"    ENGAGEMENT: {'engaged (non-trivial background spread)' if engaged else 'STARVED'}")

    print(f"\n  ---- w_bend CALIBRATION CURVE (background, frozen choice marked) ----")
    print(f"    FROZEN w_bend = {wbend['w_bend']}  (background n={wbend['background_n']})")
    for g in wbend["grid_results"]:
        marker = " <== FROZEN" if g["w_bend"] == wbend["w_bend"] else ""
        print(f"    w_bend={g['w_bend']:<6} acc={100*g['acc']:.1f}%  k={g['k']}/{g['n']}{marker}")

    print(f"\n  ---- MARGIN-SHIFT DIAGNOSTIC (true-vs-best-impostor margin, PASSED episodes "
          f"under GUARD, ARM M vs GUARD) ----")
    guard_margins_by_idx = {m["idx"]: m for m in guard["margins"]}
    armm_margins_by_idx = {m["idx"]: m for m in armm["margins"]}
    guard_pass_idx = [i for i in all_idx if guard_correct[i]]
    deltas = []
    for i in guard_pass_idx:
        gm_, am_ = guard_margins_by_idx.get(i), armm_margins_by_idx.get(i)
        if gm_ is None or am_ is None or gm_["margin"] is None or am_["margin"] is None:
            continue
        deltas.append(am_["margin"] - gm_["margin"])
    if deltas:
        arr = np.array(deltas)
        print(f"    n={len(arr)}  mean(armm_margin - guard_margin)={arr.mean():+.5f}  "
              f"median={np.median(arr):+.5f}  std={arr.std():.5f}")
        print(f"    {'WIDENS' if arr.mean() > 0 else 'TIGHTENS'} the margin on average "
              f"(positive = ARM M's margin is LARGER than GUARD's -- the mechanism's own success "
              f"criterion, the opposite of RUN 43's dilution; negative = dilution, same failure "
              f"mode RUN 43 found)")
        print(f"    fraction with a LARGER (widened) margin under ARM M: "
              f"{100*np.mean(arr > 0):.1f}%")
    else:
        print("    no scored episodes with both margins available.")

    print(f"\n  ---- WALL CLOCK ----")
    print(f"    guard eval: {guard.get('wall_clock_seconds', float('nan')):.1f}s total (n={n})")
    print(f"    armm  eval: {armm.get('wall_clock_seconds', float('nan')):.1f}s total (n={n}, "
          f"{armm.get('wall_clock_seconds', float('nan'))/n:.3f}s/episode)")
    return 0


# ===================================================================================================
# CLI.
# ===================================================================================================
def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["calibrate", "tune_wbend", "guard", "armm", "report"])
    args = p.parse_args()
    return {
        "calibrate": stage_calibrate,
        "tune_wbend": stage_tune_wbend,
        "guard": stage_guard,
        "armm": stage_armm,
        "report": stage_report,
    }[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
