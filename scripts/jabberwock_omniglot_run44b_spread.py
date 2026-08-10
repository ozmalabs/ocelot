"""OMNIGLOT RUN 44b -- THE SPREAD-MATCHED SUPPLEMENT (34a->34b principled redesign of RUN 44a's
Mahalanobis metric, commit 4990c69e's own launch brief).

THE DIAGNOSIS THIS RUN ACTS ON (RUN 44a, commit 4990c69e): the Mahalanobis-reweighted smoothdeform
term was directionally right (TRUE cheaper than WRONG on the reweighted term alone: 0.460 vs
7.101) but harmed catastrophically (34.0% vs the 80.5% GUARD, McNemar p=2.95e-48) because
REPLACING the whole-figure smoothdeform sub-term let its across-candidate SPREAD (~6.64) drown the
balanced recipe's other two terms (0.13-0.31 -- an implicit weight of 1.0, never named as a lever).
TWO BINDING RULES minted from that diagnosis (this run enforces both):
  (a) A NEW TERM ENTERS A BALANCED RECIPE AT MATCHED SPREAD OR NOT AT ALL.
  (b) BACKGROUND-SANITY IS A FREE PRE-EVAL STOP -- an arm catastrophically below the unmodified
      recipe's OWN background accuracy is stopped HERE, before a single real (test-alphabet) eval
      episode is spent.

THE REDESIGN (SUPPLEMENT, not REPLACE -- the opposite compositional choice from 44a, licensed by
44a's own diagnosis being about SCALE DOMINANCE, not wrong direction): the standing three-term
fused recipe (`abs_read.parse_marginal_pair_error_term` -- smoothdeform + part_w*marginal_part +
sc_w*shapecontext, RUN 25/26's own 80.5% [76.3, 84.1] @ n=400 GUARD) stays BYTE-IDENTICAL. A NEW,
PURE Mahalanobis affine-only term (`domains.deform_metric.mahalanobis_affine_term` -- rotation^2/
sigma_rotation^2 + shear^2/sigma_shear^2, NO residual/bending mixed in, unlike 44a's REPLACE-
shaped `reweighted_smoothdeform_term`) is ADDED at a weight `w_aff` DERIVED, not tuned:

    w_aff = median(spread_smoothdeform, spread_part, spread_sc) / spread_affine

where each `spread_*` is the across-candidate standard deviation (std over the 20 one-shot
candidates, per episode) of that term AS IT ENTERS the fused recipe (already at its own fusion
weight for part/sc), averaged over n=100 BACKGROUND 20-way episodes (5 LEARN alphabets, the SAME
split RUN 44a's own `tune_wbend`/`calibrate_affine_sigmas` use -- `evaluation`-split TEST
alphabets never touched by this measurement). `domains.deform_metric.derive_w_aff` is the held
arithmetic (a plain median/divide over already-computed background numbers, mirrors `calibrate_
affine_sigmas`'s own `_std`/`_mean` reduction discipline -- never a decision, never tuned against
an eval outcome). `sigma_rotation`/`sigma_shear` are READ from RUN 44a's OWN frozen `calibration.
json` (`results/run44_checkpoints/calibration.json`, READ-ONLY, never rewritten here) -- the SAME
`SmoothDeformComponents`-based pairwise background calibration this run's own affine term needs,
already computed once by 44a with an identical estimator; recomputing it here would be the same
number at the cost of a redundant background pass.

PRE-REGISTERED PIPELINE (design's own step order, each stage gated on the previous):
  1. STAGE `spread`  -- measure the four background spreads, derive `w_aff` (mechanical, no grid).
  2. STAGE `sanity`  -- THE HARD STOP, BEFORE any eval-alphabet spend: background (SAME n=100)
     accuracy with the UNMODIFIED recipe (`ar.parse_marginal_pair_error`) vs the ARMED supplement
     recipe (`dm.supplement_pair_error` at the derived `w_aff`). PRE-REGISTERED bound: STOP unless
     armed >= baseline - 0.03 (3 percentage points, `SANITY_MARGIN` below) -- 44a's own w_bend
     curve (41% vs ~83% baseline, EVERY grid point) would have been caught exactly here.
  3. STAGE `sensitivity` (OPTIONAL, gated on sanity PASSING WITH HEADROOM -- PRE-REGISTERED
     headroom bound: armed >= baseline - 0.01, `HEADROOM_MARGIN` below, STRICTER than the 3pp
     hard-stop, distinguishing "barely survived" from "comfortably passed") -- `w_aff x {0.5, 1.0,
     2.0}` on the SAME n=100 background (the 39b protocol: background-only calibration, legal;
     NEVER tuned against the real eval). Held Argmax over background accuracy freezes the FINAL
     `w_aff` used by the eval stage -- if this stage does not run (sanity failed, or passed
     without headroom), the eval stage uses the STAGE-1 derived `w_aff` unmodified.
  4. STAGE `eval`    -- ARM S (the spread-matched supplement, at the FINAL frozen `w_aff`) on the
     standard n=400 test-alphabet protocol (run25/26/40/43/44a's own byte-identical block order,
     POWER_SEED). GUARD is NOT recomputed -- `results/run44_checkpoints/eval_guard.json` (44a's
     own byte-identical reproduction of the RUN 25/26 C0 control, already verified "PASS --
     reproduced exactly", k=322/n=400) is READ, read-only, as this run's own comparator.
  5. STAGE `report`  -- SANITY numbers FIRST (they decide everything), then (only if sanity
     passed) McNemar ARM S vs GUARD, per-band/per-alphabet, margin-shift, spread table,
     w_aff derivation + sensitivity curve, wall-clock.

PREDICTIONS (pre-registered, same instrument RUN 40/43/44a used): fixes concentrate in the NEAR
band (`results/run40_checkpoints/classify.json`, READ-ONLY, idx-joined) and margins WIDEN on
GUARD-passed episodes (the opposite of RUN 43's dilution -- this mechanism's own success
criterion at the per-episode level). STOP (pre-registered, no retuning against eval): broken >=
fixed -> ARM S harms, stop, report as the finding.

FILES (this run only ever WRITES under `results/run44_checkpoints/`, new filenames distinct from
44a's own -- `calibration.json`/`wbend.json`/`tune_wbend_state.json`/`eval_guard.json`/
`eval_armm.json` are 44a's, READ-ONLY, NEVER opened for writing here):
  spread.json / spread_state.json   -- STAGE 1 (frozen once; per-block resumable state).
  sanity.json / sanity_state.json   -- STAGE 2 (frozen once; per-block resumable state x2 arms).
  waff_sensitivity.json / waff_sensitivity_state.json -- STAGE 3 (optional; frozen once).
  eval_arms.json                    -- STAGE 4 (per-block resumable, mirrors `eval_guard.json`'s
                                        own shape so `report` can compare idx-for-idx).
Other `results/run*_checkpoints/` directories (run25/26/40/43/44a) are READ-ONLY references,
never written. `seeds/stroke_shapes.json` is a PARALLEL-SESSION file -- this script never opens
it; its md5 is recorded before/after this run's own invocations purely as an untouched-file
witness (printed by the `report` stage).

EXECUTION (ops law, binding): every invocation <=540s foreground, `.venv` python (needs
`substrate_rs`), per-block checkpointing, no LLM call, donkey=0 not applicable.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run44b_spread.py --stage spread
  ... --stage sanity
  ... --stage sensitivity     (optional -- only proceeds if sanity passed WITH headroom)
  ... --stage eval
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
from scripts.jabberwock_omniglot_run37c_hygiene import DropDegenerateFilter
from domains import abs_read as ar
from domains import deform_metric as dm
from domains import omniglot_world as ow

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run44_checkpoints")   # SAME dir as 44a -- EXTEND it.
RUN40_DIR = os.path.join(ROOT, "results", "run40_checkpoints")  # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

# 44a's OWN files -- READ-ONLY, this script never opens any of these for writing.
CALIB_PATH_44A = os.path.join(CKPT_DIR, "calibration.json")
GUARD_PATH_44A = os.path.join(CKPT_DIR, "eval_guard.json")

STROKE_SHAPES_PATH = os.path.join(ROOT, "seeds", "stroke_shapes.json")  # parallel-session-owned,
                                                                          # never opened here --
                                                                          # md5 witnessed only.

WAY = run25.WAY                                       # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET   # 20
R_TARGET = run25.R_TARGET                             # 2  -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS             # 10
POWER_SEED = run25.POWER_SEED                         # gate.SEED + 1500, byte-identical
GUARD_CONTROL = dict(acc=0.805, k=322, n=400)         # results/run26_checkpoints/eval_baseline.json

PART_W = ar.DEFAULT_PARSE_PART_W
SC_W = ar.DEFAULT_PARSE_SC_W
BETA = ar.DEFAULT_PARSE_BETA

BACKGROUND_R_TARGET = 1        # 5 LEARN alphabets x 1 rep -> n=100, PRE-REGISTERED (44a's own).
SENSITIVITY_GRID = (0.5, 1.0, 2.0)             # multipliers of the STAGE-1 derived w_aff.
SANITY_MARGIN = 0.03           # HARD STOP: armed_bg_acc must be >= baseline_bg_acc - 0.03.
HEADROOM_MARGIN = 0.01         # STRICTER: sensitivity only runs if armed_bg_acc >= baseline - 0.01.
PER_CALL_BUDGET_SECONDS = 460.0

SPREAD_PATH = os.path.join(CKPT_DIR, "spread.json")
SPREAD_STATE_PATH = os.path.join(CKPT_DIR, "spread_state.json")
SANITY_PATH = os.path.join(CKPT_DIR, "sanity.json")
SANITY_STATE_PATH = os.path.join(CKPT_DIR, "sanity_state.json")
SENS_PATH = os.path.join(CKPT_DIR, "waff_sensitivity.json")
SENS_STATE_PATH = os.path.join(CKPT_DIR, "waff_sensitivity_state.json")
EVAL_ARMS_PATH = os.path.join(CKPT_DIR, "eval_arms.json")


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _wilson(k: int, n: int):
    return gate.wilson_ci(k, n)


def _md5(path: str) -> str:
    if not os.path.exists(path):
        return "(absent)"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


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
# Block plumbing -- byte-identical to run25/run26/run40/run43/run44a's own eval block order (the
# real n=400 protocol) and to run44a's own background-split variant (`_block_spec_split`, its own
# docstring: "`run25._block_spec`'s own body, `split` threaded through").
# ===================================================================================================
def _test_alphabets() -> list:
    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= WAY)
    return qualifying[:N_TEST_ALPHABETS]


def _blocks() -> list:
    test_alphabets = _test_alphabets()
    return [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]


def _background_alphabets() -> list:
    return ow.alphabets("background")[:dm.DEFAULT_LEARN_N]


def _background_blocks() -> list:
    alphs = _background_alphabets()
    return [(alph, r) for alph in alphs for r in range(BACKGROUND_R_TARGET)]


def _block_spec_split(alph: str, rng, way: int, episodes_per_alphabet: int, split: str) -> dict:
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


def _require_calib() -> dict:
    if not os.path.exists(CALIB_PATH_44A):
        print(f"  WALL: {CALIB_PATH_44A} not found -- run 44a's own `--stage calibrate` first "
              f"(this run READS it, never recomputes it).")
        sys.exit(1)
    return dm.load_calibration(CALIB_PATH_44A)


# ===================================================================================================
# STAGE: spread -- measure the four background across-candidate spreads, derive w_aff mechanically.
# ===================================================================================================
def _run_spread_block(alph: str, r: int, spec: dict, sigma_rotation: float,
                       sigma_shear: float) -> list:
    """One background block's per-episode component stds -- returns a list of dicts
    `{"smoothdeform": std, "part": std, "sc": std, "affine": std}`, one per episode (std taken
    over the WAY=20 candidates' raw `component_breakdown` values for that episode)."""
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    out = []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            per_cand = defaultdict(list)
            for ci in range(WAY):
                bd = dm.component_breakdown(scratch, qn, node_of_cand[ci],
                                             sigma_rotation=sigma_rotation,
                                             sigma_shear=sigma_shear, part_w=PART_W, sc_w=SC_W,
                                             beta=BETA)
                for k, v in bd.items():
                    per_cand[k].append(v)
            out.append({k: float(np.std(v)) for k, v in per_cand.items()})
    return out


def stage_spread() -> int:
    print(f"\n{SEP}\n  STAGE: spread\n{SEP}")
    if os.path.exists(SPREAD_PATH):
        frozen = _load_json(SPREAD_PATH)
        print(f"  ALREADY FROZEN: {SPREAD_PATH}")
        print(f"  spreads: {frozen['spreads']}")
        print(f"  target_spread(median of smoothdeform/part/sc)={frozen['target_spread']:.5f}  "
              f"w_aff={frozen['w_aff']:.6f}")
        return 0
    calib = _require_calib()
    sigma_rotation, sigma_shear = dm.sigma_from_calibration(calib)
    print(f"  sigma_rotation={sigma_rotation:.4f}  sigma_shear={sigma_shear:.4f}  "
          f"(READ from 44a's own frozen {CALIB_PATH_44A}, read-only)")
    print(f"  background alphabets={_background_alphabets()}")

    blocks = _background_blocks()
    n_target = len(blocks) * WAY
    state = _load_json(SPREAD_STATE_PATH) if os.path.exists(SPREAD_STATE_PATH) else dict(
        block_idx=0, per_episode=[])

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        _block_spec_split(blocks[i][0], rng, WAY, EPISODES_PER_ALPHABET, "background")

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
        alph, r = blocks[state["block_idx"]]
        spec = _block_spec_split(alph, rng, WAY, EPISODES_PER_ALPHABET, "background")
        recs = _run_spread_block(alph, r, spec, sigma_rotation, sigma_shear)
        state["per_episode"].extend(recs)
        state["block_idx"] += 1
        _save_json(state, SPREAD_STATE_PATH)
        print(f"  block {state['block_idx']}/{len(blocks)} ({alph!r}) -- "
              f"{len(state['per_episode'])}/{n_target} episodes, {time.time()-t0:.1f}s this call")

    if state["block_idx"] < len(blocks):
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-invoke to "
              f"continue.")
        return 0

    per_episode = state["per_episode"]
    spreads = {k: float(np.mean([e[k] for e in per_episode])) for k in
               ("smoothdeform", "part", "sc", "affine")}
    target_spread = float(np.median([spreads["smoothdeform"], spreads["part"], spreads["sc"]]))
    w_aff = dm.derive_w_aff(spreads["smoothdeform"], spreads["part"], spreads["sc"],
                             spreads["affine"])
    frozen = dict(spreads=spreads, target_spread=target_spread, w_aff=w_aff, n_episodes=n_target,
                  sigma_rotation=sigma_rotation, sigma_shear=sigma_shear,
                  background_alphabets=_background_alphabets())
    _save_json(frozen, SPREAD_PATH)
    print(f"\n  FROZEN spread table ({n_target} background episodes) -- {SPREAD_PATH}")
    for k in ("smoothdeform", "part", "sc", "affine"):
        print(f"    spread[{k:<11}] = {spreads[k]:.5f}")
    print(f"  target_spread (median of smoothdeform/part/sc) = {target_spread:.5f}")
    print(f"  w_aff = target_spread / spread[affine] = {w_aff:.6f}")
    return 0


def _require_spread() -> dict:
    if not os.path.exists(SPREAD_PATH):
        print("  WALL: run --stage spread to completion first.")
        sys.exit(1)
    return _load_json(SPREAD_PATH)


# ===================================================================================================
# STAGE: sanity -- THE HARD STOP. Background baseline vs armed accuracy, BEFORE any eval spend.
# ===================================================================================================
def _run_sanity_block(alph: str, r: int, spec: dict, w_aff: float, sigma_rotation: float,
                       sigma_shear: float) -> tuple:
    """One background block, BOTH arms scored in the SAME pass (identical staged candidates/
    queries -- a fair paired comparison): returns `(baseline_recs, armed_recs)`."""
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    baseline_recs, armed_recs = [], []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = getattr(scratch, "_inner", scratch)
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            base_pairs = [(ar.parse_marginal_pair_error(scratch, qn, node_of_cand[ci],
                                                          part_w=PART_W, sc_w=SC_W, beta=BETA), ci)
                          for ci in range(WAY)]
            armed_pairs = [(dm.supplement_pair_error(scratch, qn, node_of_cand[ci], w_aff=w_aff,
                                                       sigma_rotation=sigma_rotation,
                                                       sigma_shear=sigma_shear, part_w=PART_W,
                                                       sc_w=SC_W, beta=BETA), ci)
                           for ci in range(WAY)]
            base_w = native.evaluate(_argmin_pairs_term(base_pairs), {})
            armed_w = native.evaluate(_argmin_pairs_term(armed_pairs), {})
            base_pred = int(base_w[1]) if base_w is not None else -1
            armed_pred = int(armed_w[1]) if armed_w is not None else -1
            baseline_recs.append(dict(true=qi, correct=bool(base_pred == qi)))
            armed_recs.append(dict(true=qi, correct=bool(armed_pred == qi)))
    return baseline_recs, armed_recs


def stage_sanity() -> int:
    print(f"\n{SEP}\n  STAGE: sanity (THE HARD STOP -- decides everything downstream)\n{SEP}")
    if os.path.exists(SANITY_PATH):
        frozen = _load_json(SANITY_PATH)
        print(f"  ALREADY FROZEN: {SANITY_PATH}")
        _print_sanity(frozen)
        return 0
    spread = _require_spread()
    w_aff = spread["w_aff"]
    sigma_rotation, sigma_shear = spread["sigma_rotation"], spread["sigma_shear"]
    print(f"  w_aff (from --stage spread) = {w_aff:.6f}  sigma_rotation={sigma_rotation:.4f}  "
          f"sigma_shear={sigma_shear:.4f}")

    blocks = _background_blocks()
    n_target = len(blocks) * WAY
    state = _load_json(SANITY_STATE_PATH) if os.path.exists(SANITY_STATE_PATH) else dict(
        block_idx=0, baseline=[], armed=[])

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        _block_spec_split(blocks[i][0], rng, WAY, EPISODES_PER_ALPHABET, "background")

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
        alph, r = blocks[state["block_idx"]]
        spec = _block_spec_split(alph, rng, WAY, EPISODES_PER_ALPHABET, "background")
        base_recs, armed_recs = _run_sanity_block(alph, r, spec, w_aff, sigma_rotation,
                                                   sigma_shear)
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

    k_base = sum(1 for r in state["baseline"] if r["correct"])
    k_armed = sum(1 for r in state["armed"] if r["correct"])
    n = len(state["baseline"])
    acc_base, acc_armed = k_base / n, k_armed / n
    passed = acc_armed >= acc_base - SANITY_MARGIN
    headroom = acc_armed >= acc_base - HEADROOM_MARGIN
    frozen = dict(w_aff=w_aff, n=n, k_baseline=k_base, k_armed=k_armed,
                  acc_baseline=acc_base, acc_armed=acc_armed,
                  sanity_margin=SANITY_MARGIN, headroom_margin=HEADROOM_MARGIN,
                  passed=bool(passed), headroom=bool(headroom))
    _save_json(frozen, SANITY_PATH)
    _print_sanity(frozen)
    return 0


def _print_sanity(frozen: dict) -> None:
    print(f"\n  ---- BACKGROUND-SANITY GATE (n={frozen['n']}, w_aff={frozen['w_aff']:.6f}) ----")
    print(f"    baseline (unmodified recipe): acc={100*frozen['acc_baseline']:.1f}%  "
          f"k={frozen['k_baseline']}/{frozen['n']}")
    print(f"    armed    (spread-matched supplement): acc={100*frozen['acc_armed']:.1f}%  "
          f"k={frozen['k_armed']}/{frozen['n']}")
    delta = frozen["acc_armed"] - frozen["acc_baseline"]
    print(f"    delta = {100*delta:+.1f}pp   hard-stop bound = baseline - "
          f"{100*frozen['sanity_margin']:.0f}pp")
    print(f"    VERDICT: {'PASS -- proceed' if frozen['passed'] else 'STOP -- do NOT spend any eval budget'}")
    print(f"    HEADROOM (stricter, -{100*frozen['headroom_margin']:.0f}pp bound, gates the "
          f"optional sensitivity stage): {'yes' if frozen['headroom'] else 'no'}")


def _require_sanity() -> dict:
    if not os.path.exists(SANITY_PATH):
        print("  WALL: run --stage sanity to completion first.")
        sys.exit(1)
    return _load_json(SANITY_PATH)


# ===================================================================================================
# STAGE: sensitivity (OPTIONAL) -- w_aff x {0.5, 1.0, 2.0} on BACKGROUND, gated on sanity PASS
# WITH HEADROOM. Held Argmax over background accuracy freezes the FINAL w_aff for eval.
# ===================================================================================================
def _run_sensitivity_block(alph: str, r: int, spec: dict, w_aff: float, sigma_rotation: float,
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
            pairs = [(dm.supplement_pair_error(scratch, qn, node_of_cand[ci], w_aff=w_aff,
                                                sigma_rotation=sigma_rotation,
                                                sigma_shear=sigma_shear, part_w=PART_W, sc_w=SC_W,
                                                beta=BETA), ci) for ci in range(WAY)]
            winner = native.evaluate(_argmin_pairs_term(pairs), {})
            pred = int(winner[1]) if winner is not None else -1
            recs.append(dict(true=qi, correct=bool(pred == qi)))
    return recs


def stage_sensitivity() -> int:
    print(f"\n{SEP}\n  STAGE: sensitivity (OPTIONAL -- gated on sanity PASS+HEADROOM)\n{SEP}")
    sanity = _require_sanity()
    if not sanity["passed"]:
        print("  WALL: sanity STOPPED -- sensitivity does not run, no eval budget may be spent.")
        return 1
    if not sanity["headroom"]:
        print(f"  SKIP: sanity passed but WITHOUT headroom (armed {100*sanity['acc_armed']:.1f}% "
              f"vs baseline {100*sanity['acc_baseline']:.1f}%, -{100*HEADROOM_MARGIN:.0f}pp bound "
              f"not met) -- per pre-registration, sensitivity is not explored; the eval stage "
              f"will use the STAGE-1 derived w_aff unmodified.")
        _save_json(dict(ran=False, reason="no_headroom", final_w_aff=sanity["w_aff"]), SENS_PATH)
        return 0
    if os.path.exists(SENS_PATH):
        frozen = _load_json(SENS_PATH)
        print(f"  ALREADY FROZEN: {SENS_PATH}")
        if frozen.get("ran"):
            for g in frozen["grid_results"]:
                marker = " <== WINNER" if g["multiplier"] == frozen["winner_multiplier"] else ""
                print(f"    w_aff*{g['multiplier']:<4} = {g['w_aff']:.6f}  acc={100*g['acc']:.1f}%"
                      f"  k={g['k']}/{g['n']}{marker}")
            print(f"  FINAL w_aff = {frozen['final_w_aff']:.6f}")
        return 0

    w_aff_base = sanity["w_aff"]
    spread = _require_spread()
    sigma_rotation, sigma_shear = spread["sigma_rotation"], spread["sigma_shear"]
    blocks = _background_blocks()
    n_target = len(blocks) * WAY
    state = _load_json(SENS_STATE_PATH) if os.path.exists(SENS_STATE_PATH) else dict(
        grid_idx=0, block_idx=0,
        records_by_mult={str(m): [] for m in SENSITIVITY_GRID})

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["grid_idx"] < len(SENSITIVITY_GRID) and time.time() < hard_deadline:
        mult = SENSITIVITY_GRID[state["grid_idx"]]
        w_aff = w_aff_base * mult
        rng = np.random.default_rng(POWER_SEED)
        for i in range(state["block_idx"]):
            _block_spec_split(blocks[i][0], rng, WAY, EPISODES_PER_ALPHABET, "background")
        while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
            alph, r = blocks[state["block_idx"]]
            spec = _block_spec_split(alph, rng, WAY, EPISODES_PER_ALPHABET, "background")
            recs = _run_sensitivity_block(alph, r, spec, w_aff, sigma_rotation, sigma_shear)
            state["records_by_mult"][str(mult)].extend(recs)
            state["block_idx"] += 1
            _save_json(state, SENS_STATE_PATH)
            print(f"  w_aff*{mult:<4} block {state['block_idx']}/{len(blocks)} ({alph!r}) -- "
                  f"{len(state['records_by_mult'][str(mult)])} episodes, "
                  f"{time.time()-t0:.1f}s this call")
        if state["block_idx"] >= len(blocks):
            state["grid_idx"] += 1
            state["block_idx"] = 0
            _save_json(state, SENS_STATE_PATH)

    if state["grid_idx"] < len(SENSITIVITY_GRID):
        print(f"\n  PARTIAL: grid_idx={state['grid_idx']}/{len(SENSITIVITY_GRID)} -- re-invoke to "
              f"continue.")
        return 0

    grid_results = []
    for mult in SENSITIVITY_GRID:
        recs = state["records_by_mult"][str(mult)]
        k = sum(1 for r in recs if r["correct"])
        n = len(recs)
        grid_results.append(dict(multiplier=mult, w_aff=w_aff_base * mult,
                                  acc=k / n if n else 0.0, k=k, n=n))
    pairs = [(g["acc"], i) for i, g in enumerate(grid_results)]
    scratch = srs.Substrate()
    native = getattr(scratch, "_inner", scratch)
    winner = native.evaluate(_argmax_pairs_term(pairs), {})
    best_idx = int(winner[1]) if winner is not None else 1   # default multiplier=1.0
    frozen = dict(ran=True, w_aff_base=w_aff_base, grid_results=grid_results,
                  winner_multiplier=grid_results[best_idx]["multiplier"],
                  final_w_aff=grid_results[best_idx]["w_aff"], background_n=n_target)
    _save_json(frozen, SENS_PATH)
    print(f"\n  FROZEN sensitivity winner: multiplier={frozen['winner_multiplier']}  "
          f"final_w_aff={frozen['final_w_aff']:.6f} -- {SENS_PATH}")
    for g in grid_results:
        marker = " <== WINNER" if g["multiplier"] == frozen["winner_multiplier"] else ""
        print(f"    w_aff*{g['multiplier']:<4} = {g['w_aff']:.6f}  acc={100*g['acc']:.1f}%  "
              f"k={g['k']}/{g['n']}{marker}")
    return 0


def _final_w_aff() -> float:
    """The w_aff the EVAL stage uses: sensitivity's frozen winner if that stage ran and picked
    one, else the STAGE-1 mechanically-derived value unmodified."""
    if os.path.exists(SENS_PATH):
        sens = _load_json(SENS_PATH)
        return float(sens["final_w_aff"])
    return float(_require_spread()["w_aff"])


# ===================================================================================================
# STAGE: eval -- ARM S at n=400, the standard test-alphabet protocol. GUARD is READ from 44a's
# own `eval_guard.json` (read-only), never recomputed.
# ===================================================================================================
def _run_block_arm_s(alph: str, r: int, spec: dict, w_aff: float, sigma_rotation: float,
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
            pairs = [(dm.supplement_pair_error(scratch, qn, node_of_cand[ci], w_aff=w_aff,
                                                sigma_rotation=sigma_rotation,
                                                sigma_shear=sigma_shear, part_w=PART_W, sc_w=SC_W,
                                                beta=BETA), ci) for ci in range(WAY)]
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


def stage_eval() -> int:
    print(f"\n{SEP}\n  STAGE: eval (ARM S -- the spread-matched supplement)\n{SEP}")
    sanity = _require_sanity()
    if not sanity["passed"]:
        print("  WALL: sanity STOPPED (armed background accuracy fell below the pre-registered "
              "bound) -- per this run's own binding rule, NO eval budget may be spent. Report "
              "the sanity finding and stop here.")
        return 1
    if not os.path.exists(GUARD_PATH_44A):
        print(f"  WALL: {GUARD_PATH_44A} not found -- 44a's own GUARD reproduction is required "
              f"as this run's comparator (read-only, never recomputed here).")
        sys.exit(1)

    spread = _require_spread()
    sigma_rotation, sigma_shear = spread["sigma_rotation"], spread["sigma_shear"]
    w_aff = _final_w_aff()
    print(f"  FINAL w_aff = {w_aff:.6f}  ({'from --stage sensitivity' if os.path.exists(SENS_PATH) and _load_json(SENS_PATH).get('ran') else 'from --stage spread (mechanical derivation, unmodified)'})")

    out_path = EVAL_ARMS_PATH
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
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
        recs, margins = _run_block_arm_s(alph, r, spec, w_aff, sigma_rotation, sigma_shear)
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
        state["w_aff"] = w_aff
        k = sum(1 for rec in state["records"] if rec["correct"])
        n = len(state["records"])
        ci = _wilson(k, n)
        state["acc"] = dict(acc=k / n, ci=list(ci), k=k, n=n)
        state["wall_clock_seconds"] = state.get("wall_clock_seconds", 0.0) + (time.time() - t0)
        _save_json(state, out_path)
        print(f"\n  EVAL COMPLETE for arm-s: n={n}  acc={100*k/n:.1f}%  "
              f"95% CI [{100*ci[0]:.1f}%, {100*ci[1]:.1f}%]  k={k}")
    else:
        state["wall_clock_seconds"] = state.get("wall_clock_seconds", 0.0) + (time.time() - t0)
        _save_json(state, out_path)
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-invoke to "
              f"continue. ({time.time()-t0:.1f}s this call)")
    return 0


# ===================================================================================================
# STAGE: report -- SANITY numbers FIRST (they decide everything). McNemar/margins/tables only
# printed if sanity passed and eval ran.
# ===================================================================================================
def _mcnemar(base_correct: list, arm_correct: list) -> dict:
    fixed = sum(1 for b, a in zip(base_correct, arm_correct) if (not b) and a)
    broken = sum(1 for b, a in zip(base_correct, arm_correct) if b and (not a))
    n_disc = fixed + broken
    p = float(binomtest(fixed, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    return dict(fixed=fixed, broken=broken, discordant=n_disc, p=p)


def stage_report() -> int:
    print(f"\n{SEP}\n  STAGE: report\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_PATH)
    print(f"  seeds/stroke_shapes.json md5 (parallel-session-owned, this run never writes it): "
          f"{md5_now}")

    sanity = _require_sanity()
    print(f"\n{'='*40}  SANITY-GATE (decides everything)  {'='*40}")
    _print_sanity(sanity)

    spread = _require_spread()
    print(f"\n  ---- SPREAD TABLE (background n={spread['n_episodes']}, mean std over "
          f"{WAY} candidates per episode) ----")
    for k in ("smoothdeform", "part", "sc", "affine"):
        print(f"    spread[{k:<11}] = {spread['spreads'][k]:.5f}")
    print(f"    target_spread (median of smoothdeform/part/sc) = {spread['target_spread']:.5f}")
    print(f"    w_aff (mechanical derivation, stage 1) = {spread['w_aff']:.6f}")

    if os.path.exists(SENS_PATH):
        sens = _load_json(SENS_PATH)
        print(f"\n  ---- w_aff SENSITIVITY (background, optional stage) ----")
        if sens.get("ran"):
            for g in sens["grid_results"]:
                marker = " <== WINNER" if g["multiplier"] == sens["winner_multiplier"] else ""
                print(f"    w_aff*{g['multiplier']:<4} = {g['w_aff']:.6f}  acc={100*g['acc']:.1f}%"
                      f"  k={g['k']}/{g['n']}{marker}")
            print(f"    FINAL w_aff used by eval = {sens['final_w_aff']:.6f}")
        else:
            print(f"    SKIPPED ({sens.get('reason')}) -- eval used the stage-1 w_aff unmodified "
                  f"({sens['final_w_aff']:.6f})")

    if not sanity["passed"]:
        print(f"\n  {'='*30}  SANITY STOPPED -- NO EVAL WAS RUN, PER THIS RUN'S OWN BINDING "
              f"RULE  {'='*30}")
        print(f"  (armed background accuracy {100*sanity['acc_armed']:.1f}% fell more than "
              f"{100*sanity['sanity_margin']:.0f}pp below baseline {100*sanity['acc_baseline']:.1f}%"
              f" -- exactly the free pre-eval stop this run was designed to exercise)")
        return 0

    if not os.path.exists(EVAL_ARMS_PATH) or not os.path.exists(GUARD_PATH_44A):
        print("  WALL: sanity PASSED but --stage eval has not completed yet (or 44a's own "
              "eval_guard.json is missing) -- run it, then re-run report.")
        sys.exit(1)
    arms = _load_json(EVAL_ARMS_PATH)
    if not arms.get("done"):
        print(f"  WALL: eval-arm-s not yet COMPLETE ({arms['block_idx']}/20 blocks) -- resume it "
              f"first.")
        sys.exit(1)
    guard = _load_json(GUARD_PATH_44A)
    if not guard.get("done"):
        print("  WALL: 44a's own eval_guard.json is not COMPLETE -- inconsistent state.")
        sys.exit(1)

    n = len(guard["records"])
    assert n == len(arms["records"]), f"guard n={n} != arm-s n={len(arms['records'])}"
    guard_correct = [None] * n
    guard_alph = [None] * n
    for rec in guard["records"]:
        guard_correct[rec["idx"]] = rec["correct"]
        guard_alph[rec["idx"]] = rec["alph"]
    arm_correct = [None] * n
    for rec in arms["records"]:
        arm_correct[rec["idx"]] = rec["correct"]

    classify_path = os.path.join(RUN40_DIR, "classify.json")
    classify = _load_json(classify_path) if os.path.exists(classify_path) else {"rows": []}
    classify_rows_by_idx = {row["idx"]: row for row in classify["rows"]}
    print(f"\n  run40 classify.json: {len(classify_rows_by_idx)} idx-labelled episodes "
          f"(READ-ONLY reference, {classify_path})")

    all_idx = list(range(n))
    mc = _mcnemar(guard_correct, arm_correct)
    fixed_idx = {i for i in all_idx if (not guard_correct[i]) and arm_correct[i]}
    broken_idx = {i for i in all_idx if guard_correct[i] and (not arm_correct[i])}

    k_arm = sum(1 for c in arm_correct if c)
    ci_arm = _wilson(k_arm, n)
    k_guard = sum(guard_correct)
    ci_guard = _wilson(k_guard, n)

    print(f"\n  ---- McNEMAR: ARM S vs GUARD/GLOBAL (PRIMARY) ----")
    print(f"    GUARD accuracy: {100*k_guard/n:.1f}% [{100*ci_guard[0]:.1f}, {100*ci_guard[1]:.1f}]"
          f"  k={k_guard}/{n}")
    print(f"    ARM S accuracy: {100*k_arm/n:.1f}% [{100*ci_arm[0]:.1f}, {100*ci_arm[1]:.1f}]"
          f"  k={k_arm}/{n}")
    print(f"    McNemar: fixed={mc['fixed']}  broken={mc['broken']}  "
          f"discordant={mc['discordant']}  p={mc['p']:.4g}   "
          f"{'ARM S HARMS -- STOP' if mc['broken'] >= mc['fixed'] and mc['discordant'] else 'ok'}")

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

    print(f"\n  ---- PER-ALPHABET fixed/broken (fixed - broken net) ----")
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

    print(f"\n  ---- MARGIN-SHIFT DIAGNOSTIC (true-vs-best-impostor margin, PASSED episodes "
          f"under GUARD, ARM S vs GUARD) ----")
    guard_margins_by_idx = {m["idx"]: m for m in guard["margins"]}
    arm_margins_by_idx = {m["idx"]: m for m in arms["margins"]}
    guard_pass_idx = [i for i in all_idx if guard_correct[i]]
    deltas = []
    for i in guard_pass_idx:
        gm_, am_ = guard_margins_by_idx.get(i), arm_margins_by_idx.get(i)
        if gm_ is None or am_ is None or gm_["margin"] is None or am_["margin"] is None:
            continue
        deltas.append(am_["margin"] - gm_["margin"])
    if deltas:
        arr = np.array(deltas)
        print(f"    n={len(arr)}  mean(arms_margin - guard_margin)={arr.mean():+.5f}  "
              f"median={np.median(arr):+.5f}  std={arr.std():.5f}")
        print(f"    {'WIDENS' if arr.mean() > 0 else 'TIGHTENS'} the margin on average "
              f"(positive = this mechanism's own success criterion, the opposite of RUN 43's "
              f"dilution)")
        print(f"    fraction with a LARGER (widened) margin under ARM S: "
              f"{100*np.mean(arr > 0):.1f}%")
    else:
        print("    no scored episodes with both margins available.")

    print(f"\n  ---- WALL CLOCK ----")
    print(f"    guard eval (44a, read-only): {guard.get('wall_clock_seconds', float('nan')):.1f}s "
          f"total (n={n})")
    print(f"    arm-s eval: {arms.get('wall_clock_seconds', float('nan')):.1f}s total (n={n}, "
          f"{arms.get('wall_clock_seconds', float('nan'))/n:.3f}s/episode)")
    return 0


# ===================================================================================================
# CLI.
# ===================================================================================================
def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["spread", "sanity", "sensitivity", "eval", "report"])
    args = p.parse_args()
    return {
        "spread": stage_spread,
        "sanity": stage_sanity,
        "sensitivity": stage_sensitivity,
        "eval": stage_eval,
        "report": stage_report,
    }[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
