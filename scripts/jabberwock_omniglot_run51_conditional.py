"""OMNIGLOT RUN 51 -- THE CONDITIONAL RELATIONAL VERDICT: the end-to-end test of run 50's
license, built from the two halves each prior run had (run 45's CONDITIONAL FRAME + run 50's
ORTHOGONAL EVIDENCE).

THE MECHANISM (creator's own framing, launch brief verbatim): "after the geo verdict, WHEN the
top-2 geo margin is below a BACKGROUND-frozen threshold, let r ADJUDICATE among the geo top-K...
when geo is confident, geo stands unchanged. This is top-down-in-miniature: geometry proposes,
the concept's variation model decides the doubtful cases." Run 50 (commit 563322d3) proved the
background-learned relational-variation distance `r` (`domains/relational_variation.py`) is
ORTHOGONAL to SC+TPS (corr 0.093, ~5x less correlated than run 49's motor 0.48) and lifts the
geo-WRONG cases (41.2% rank-better, 20.6% outright-fix, conditional on geo wrong) but is WEAKER
overall (1.32x separation vs geo's 2.05x) -- run 44b's law says a weaker channel added
UNCONDITIONALLY/variance-matched only DILUTES. Run 45 (commit 1ea5a473) already built and
validated the CONDITIONAL-FIRE + spread-matched-supplement scaffold for exactly this situation
(there, the evidence -- difference-region distance -- turned out redundant; the scaffold itself
was sound). This run composes the two: run 45's scaffold, run 50's evidence.

REUSE, NOT REBUILD (no new domains/ module -- run 50 already placed `relational_distance`/
`class_slot_variances`/`slot_weights` in `domains/relational_variation.py`, not script-local, so
there is nothing to "promote"):
  - `domains/conditional_foveation.py`'s `top2_from_pairs`/`top2_margin`/`derive_threshold`/
    `fires`/`supplement_pairs` are ALL generic arithmetic over `[(score, candidate_index), ...]`
    pairs and a `{candidate_index: scalar}` terms dict -- nothing in them is foveation-specific.
    Reused verbatim; only `foveate_terms`/`difference_elements_aligned` (the EVIDENCE-specific
    half of that module) are NOT reused -- this run's evidence is `relational_variation.
    relational_distance`, not a difference-region score.
  - `domains/deform_metric.py`'s `derive_w_aff` (the spread-matching arithmetic) is reused
    verbatim for `w_r` (renamed in this run's own reporting, same formula: `w_r =
    median(spread_smoothdeform, spread_part, spread_sc) / spread_r`).
  - `results/run50_checkpoints/learn_relational.json`'s own frozen `weights` (the per-slot
    tightness weights, background-learned, READ-ONLY) -- NOT recomputed here; this run tests
    whether the ALREADY-LICENSED evidence converts to accuracy, not whether it can be relearned.
  - `results/run26_checkpoints/learn.json` (the standing grown codebook, READ-ONLY) -- decode
    calls need it (`gate.decode_char_signature` requires the same quantization the codebook was
    grown at, `gate.DK`).
  - `results/run44_checkpoints/spread.json` (44b's own background spreads, READ-ONLY) and
    `results/run44_checkpoints/eval_guard.json` (44a's own GUARD reproduction, READ-ONLY).

PRE-REGISTERED DESIGN CHOICES (stated here, before any real episode is scored):

  1. EPISODE SET: the FULL run-25/26/45 protocol (10 sorted-name test alphabets x R_TARGET=2 x
     WAY=20 = n=400, `POWER_SEED`, alph-outer/r-inner block order) -- NOT run 50's own
     within-alphabet-on-4-multi-stroke-alphabets subset. This keeps GUARD comparable to the
     canonical 80.5% [76.3, 84.1] k=322/n=400 baseline every prior run in this arc cites, and
     lets the reader compare THIS run's accuracy numbers directly against every other arm in the
     campaign (37A/44a/44b/45 all used this exact protocol). The cost: many of the 400 queries
     are single-stroke (no relations to adjudicate with) -- reported honestly below as the
     MULTI-STROKE COVERAGE fraction, and the mechanism structurally never fires on those queries
     (fixes/harm can only occur on the multi-stroke subset; see condition #2).
  2. THE CONDITION (fires iff BOTH): (a) the top-2 GLOBAL margin is STRICTLY BELOW the
     BACKGROUND-frozen threshold (`MARGIN_PCTL`-th percentile of top-2 margins over the SAME
     n=100 background episode set run 44b/45 use -- 5 LEARN alphabets x BACKGROUND_R_TARGET=1,
     `run44b._background_blocks`/`_block_spec_split`, reused verbatim); (b) the QUERY drawing
     has >= `MIN_STROKES_QUERY` = 2 raw pen-strokes (run 50's own "multi-stroke" convention,
     applied at the QUERY grain here rather than the class grain -- a single-stroke query has NO
     `rel` relations of its own to align, so `r` carries no query-side evidence for it; geo
     stands unmodified). Condition (a) alone is calibrated on ALL background episodes regardless
     of stroke count (mirrors run 45's own calibrate stage exactly); condition (b) is a
     structural gate, not a tuned parameter.
  3. THE ADJUDICATION RULE: `score'(ci) = fused(ci) + w_r * r(ci)` for `ci` in the fired
     episode's own GLOBAL top-2 ONLY (K=2) -- geo's OWN top-2, not an independently-chosen
     shortlist. K=2 is chosen to match the firing SIGNAL itself (the top-2 margin is what
     triggers adjudication, so the top-2 is what gets adjudicated -- no second shortlist
     parameter to justify) and to reuse `cf.supplement_pairs` byte-identically as run 45's own
     additive-at-matched-spread mechanism (fused + w*term, term absent => 0 => untouched). Every
     other candidate's score is untouched -- an unfired OR non-multi-stroke episode's `score'`
     is PROVABLY byte-identical to `full_pairs` (asserted at every episode, not merely assumed,
     mirroring run 45's own structural check).
  4. `w_r` is DERIVED, never tuned: `w_r = median(spread_smoothdeform, spread_part, spread_sc) /
     spread_r` (`domains.deform_metric.derive_w_aff`, reused verbatim) where the three numerator
     spreads are READ from `results/run44_checkpoints/spread.json` (44b's own frozen background
     measurement, READ-ONLY) and `spread_r` is measured FRESH on the SAME n=100 background
     episodes as the threshold (mean per-episode std of the length-20 term vector that is 0.0
     for every candidate except the fired episode's own top-2, which get `r(ci)` -- the same
     "honest shape this term actually has once fired" measurement run 45 performed for its own
     diff-region term).
  5. BACKGROUND-SANITY STOP (standing rule since commit 465d57da): armed (conditional relational)
     accuracy on the SAME n=100 background episodes must be >= baseline - 3pp, checked BEFORE any
     eval-alphabet spend, reported regardless of pass/fail.

PRIMARY (pre-registered, `--stage report`): paired McNemar, ARM C vs GUARD, BOTH overall (n=400)
AND restricted to FIRED episodes (the only episodes ARM C can possibly differ from GUARD on, by
construction of design choice #3). PREDICTIONS (pre-registered, stated before any eval number is
computed): fixes concentrate in the fired (geo-uncertain, low-margin, multi-stroke) subset; among
fired episodes, run 50's own 41% rank-improvement lift converts to net-positive fixed>broken;
every non-fired episode's `score'` is byte-identical to `full_pairs` (verified, not assumed).
STOP CONDITION (never re-tuned against this eval): `broken >= fixed` overall -- even an orthogonal,
conditionally-gated channel does not convert to accuracy; the finding is that the fusion
MECHANISM (a bolt-on additive supplement over a small shortlist) is insufficient, and the next
lever is the FULL top-down loop (the concept model re-scoring or re-deriving the geo comparison
itself), not a bigger/differently-weighted bolt-on. A WIN (fixed>broken, CI-separated or
McNemar-significant) is reported as the first crack in the twelve-null 80.5% ceiling via
top-down evidence.

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run51.log`, per-block checkpoints under `results/run51_checkpoints/`
(every OTHER `results/run*_checkpoints/` directory is READ-ONLY reference, never written here),
NEVER `run_in_background`. `.venv` python (needs `substrate_rs`).

Stages, in dependency order:
  unit_sanity  seed-guard (before) + run tests/test_conditional_relational_migrated.py +
               tests/test_relational_variation_migrated.py (run 50's own suite, must stay green).
  calibrate    background margin threshold (p25) + spread_r -> w_r, frozen once.
  sanity       THE HARD STOP -- background baseline vs armed accuracy, before any eval spend.
  guard        protocol reproduction vs `results/run44_checkpoints/eval_guard.json` (80.5%).
  eval         ARM C at n=400, standard test-alphabet protocol (re-invoke until COMPLETE).
  report       background-sanity FIRST, McNemar overall + fired-only, accuracies, fire-rate,
               frozen threshold/K/w_r, fixed/broken structure, the does-it-convert verdict.

Run (from the gamma-substrate repo root):
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run51_conditional.py --stage <STAGE>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")   # belt-and-suspenders, see run50's own
                                                             # precedent -- decode calls on a
                                                             # background/eval drawer could in
                                                             # principle OOV-mint.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from scipy.stats import binomtest

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run25_number as run25
import scripts.jabberwock_omniglot_run26_homework as run26
import scripts.jabberwock_omniglot_run44b_spread as run44b
from scripts.jabberwock_omniglot_run37c_hygiene import DropDegenerateFilter
from domains import abs_read as ar
from domains import conditional_foveation as cf
from domains import deform_metric as dm
from domains import omniglot_world as ow
from domains import relational_variation as rv

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run51_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")     # READ-ONLY reference.
RUN40_DIR = os.path.join(ROOT, "results", "run40_checkpoints")     # READ-ONLY reference.
RUN44_DIR = os.path.join(ROOT, "results", "run44_checkpoints")     # READ-ONLY reference.
RUN50_DIR = os.path.join(ROOT, "results", "run50_checkpoints")     # READ-ONLY reference.
SPREAD_PATH_44B = os.path.join(RUN44_DIR, "spread.json")           # READ-ONLY (44b's own).
GUARD_PATH_44A = os.path.join(RUN44_DIR, "eval_guard.json")        # READ-ONLY (44a's own).
LEARN_RELATIONAL_PATH_50 = os.path.join(RUN50_DIR, "learn_relational.json")  # READ-ONLY (50's).
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

WAY = run25.WAY                                        # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET    # 20
R_TARGET = run25.R_TARGET                              # 2 -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS              # 10
POWER_SEED = run25.POWER_SEED                          # gate.SEED + 1500, byte-identical
BACKGROUND_R_TARGET = run44b.BACKGROUND_R_TARGET       # 1 -> n=100 (5 LEARN alphabets x 1)
DK = gate.DK                                           # the SAME reduced bins the standing
                                                        # codebook was grown at -- load-bearing.

PART_W = ar.DEFAULT_PARSE_PART_W
SC_W = ar.DEFAULT_PARSE_SC_W
BETA = ar.DEFAULT_PARSE_BETA

MARGIN_PCTL = 25.0               # PRE-REGISTERED: p25 of background top-2 margins (run 45's own
                                  # precedent, reused verbatim -- see design choice #2).
MIN_STROKES_QUERY = 2            # PRE-REGISTERED: query raw pen-stroke count for "multi-stroke"
                                  # (run 50's own class-grain convention, applied at query grain).
SANITY_MARGIN = 0.03             # HARD STOP: armed_bg_acc must be >= baseline_bg_acc - 3pp.
PER_CALL_BUDGET_SECONDS = 460.0

CALIB_PATH = os.path.join(CKPT_DIR, "calibrate.json")
CALIB_STATE_PATH = os.path.join(CKPT_DIR, "calibrate_state.json")
SANITY_PATH = os.path.join(CKPT_DIR, "sanity.json")
SANITY_STATE_PATH = os.path.join(CKPT_DIR, "sanity_state.json")
GUARD_PATH = os.path.join(CKPT_DIR, "guard.json")
EVAL_PATH = os.path.join(CKPT_DIR, "eval_armc.json")
REPORT_PATH = os.path.join(CKPT_DIR, "report.json")

BASELINE_FULL_DWELL = dict(acc=0.805, ci=(0.7633481418022936, 0.8408493586537856), n=400, k=322)

# RUN 50's OWN CITED FINDING (commit 563322d3) -- the license this run's own eval either converts
# or localizes; cited verbatim, never re-derived here.
RUN50_CORR = 0.093
RUN50_CONDITIONAL_LIFT = 0.412
RUN50_R_SEPARATION = 1.32
RUN50_GEO_SEPARATION = 2.05


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
# ONE EPISODE'S full_pairs (the GLOBAL fused-error vector over all WAY candidates) -- BYTE-
# IDENTICAL idiom to run 25/26/44/45's own `_full_pairs`/`_argmin_ci`.
# ===================================================================================================
def _full_pairs(scratch, qn, node_of_cand: dict) -> list:
    return [(ar.parse_marginal_pair_error(scratch, qn, node_of_cand[ci], part_w=PART_W,
                                           sc_w=SC_W, beta=BETA), ci) for ci in range(WAY)]


def _argmin_ci(native, pairs: list) -> int:
    w = native.evaluate(ar._argmin_pairs_term(pairs), {})
    return int(w[1]) if w is not None else -1


# ===================================================================================================
# THE CONDITION -- generic scaffold (`cf.fires`/`cf.top2_from_pairs`/`cf.top2_margin`, reused
# verbatim) PLUS the query-multi-stroke structural gate (design choice #2b).
# ===================================================================================================
def _is_multistroke(path: str) -> bool:
    return len(ow.load_strokes(path)) >= MIN_STROKES_QUERY


def _fires_conditional(margin: float, threshold: float, multistroke: bool) -> bool:
    """THE CONDITION, both halves: (a) `cf.fires` -- the background-frozen margin threshold
    (generic, reused verbatim); (b) the query has relations to adjudicate with at all. Neither
    half alone is sufficient (a low-margin single-stroke query has no `r` evidence; a
    multi-stroke query with a comfortable margin needs no adjudication)."""
    return bool(cf.fires(margin, threshold) and multistroke)


# ===================================================================================================
# THE EVIDENCE -- `relational_variation.relational_distance` over the geo top-2 ONLY (K=2, design
# choice #3), taking ALREADY-DECODED `(stroke_points, composed_sig)` tuples so this function is
# hermetically unit-testable (no file I/O, no substrate) independent of the real-decode caller
# below.
# ===================================================================================================
def _relational_terms_for_top2(native, q_decoded: tuple, c1_decoded: tuple, c2_decoded: tuple,
                                cand1_idx: int, cand2_idx: int, weights: dict) -> dict:
    q_pts, q_sig = q_decoded
    c1_pts, c1_sig = c1_decoded
    c2_pts, c2_sig = c2_decoded
    r1 = rv.relational_distance(native, q_pts, q_sig, c1_pts, c1_sig, weights)["r"]
    r2 = rv.relational_distance(native, q_pts, q_sig, c2_pts, c2_sig, weights)["r"]
    return {cand1_idx: r1, cand2_idx: r2}


def _armc_from_terms(native, full_pairs: list, fired: bool, terms: dict, w_r: float) -> tuple:
    """THE PURE CORE (hermetically testable): given an already-decided `fired` flag and an
    already-computed `terms` dict, apply `cf.supplement_pairs` (generic, reused verbatim) and
    the held Argmin. When NOT fired, `terms` MUST be empty -- asserted, not merely assumed, so a
    caller that forgets to gate `terms` on `fired` is caught immediately, not silently masked by
    `supplement_pairs`' own no-op-on-empty-dict behaviour."""
    if not fired:
        assert not terms, "terms must be empty when the condition did not fire"
        pairs_prime = cf.supplement_pairs(full_pairs, {}, w_r)
        assert pairs_prime == full_pairs
        return _argmin_ci(native, pairs_prime), pairs_prime
    pairs_prime = cf.supplement_pairs(full_pairs, terms, w_r)
    return _argmin_ci(native, pairs_prime), pairs_prime


# ===================================================================================================
# THE CODEBOOK SUBSTRATE (READ-ONLY reference, `results/run26_checkpoints/learn.json`) -- decode
# calls need the SAME quantization the standing codebook was grown at. Loaded ONCE per stage
# invocation (run 50's own precedent); an in-memory substrate, never written back to
# `seeds/stroke_shapes.json` (belt-and-suspenders env var above, on top of the durable
# commit-21aa6123 guard).
# ===================================================================================================
def _load_codebook_substrate():
    return run26._load_graph(os.path.join(RUN26_DIR, "learn.json"))


def _decode(codebook_s, cache: dict, path: str) -> tuple:
    d = gate.decode_char_signature(codebook_s, path, cache, DK)
    return d["stroke_points"], d["composed_sig"]


def _require_weights() -> dict:
    if not os.path.exists(LEARN_RELATIONAL_PATH_50):
        print(f"  WALL: {LEARN_RELATIONAL_PATH_50} not found -- run 50's own "
              f"--stage learn_relational is required as a READ-ONLY reference (this run never "
              f"recomputes the relational-variation model).")
        sys.exit(1)
    return _load_json(LEARN_RELATIONAL_PATH_50)["weights"]


# ===================================================================================================
# STAGE: unit_sanity -- seed-guard + this run's own unit suite + run 50's own suite (must stay
# green -- this run reuses `relational_variation.py` unmodified).
# ===================================================================================================
def stage_unit_sanity() -> int:
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    md5_before = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5 (BEFORE this run touches anything): {md5_before}")
    print(f"  OZMA_SEED_PERSIST_DISABLED={os.environ.get('OZMA_SEED_PERSIST_DISABLED')!r}")

    ok_all = True
    for test_file in ("tests/test_conditional_relational_migrated.py",
                       "tests/test_relational_variation_migrated.py"):
        print(f"\n  running {test_file} ...")
        proc = subprocess.run([sys.executable, "-m", "pytest", test_file, "-q"],
                               cwd=ROOT, env={**os.environ}, capture_output=True, text=True,
                               timeout=180)
        print(proc.stdout[-4000:])
        if proc.returncode != 0:
            print(proc.stderr[-4000:])
        ok = proc.returncode == 0
        print(f"      -> {'PASS' if ok else 'FAIL'}")
        ok_all &= ok

    md5_after = _md5(STROKE_SHAPES_SEED)
    ok_seed = md5_after == md5_before
    print(f"\n  seeds/stroke_shapes.json md5 AFTER unit_sanity: {md5_after}  UNCHANGED={ok_seed}")
    ok_all &= ok_seed
    if not ok_seed:
        raise SystemExit("HARD STOP: seed write detected during --stage unit_sanity.")

    print(f"\n{SEP}\n  UNIT SANITY: {'ALL PASS' if ok_all else 'SOME FAILED -- DO NOT PROCEED'}"
          f"\n{SEP}")
    _save_json({"ok_all": bool(ok_all), "stroke_shapes_md5_before": md5_before},
               os.path.join(CKPT_DIR, "unit_sanity.json"))
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    if not ok_all:
        raise SystemExit(1)
    return 0


def _require_unit_sanity() -> dict:
    p = os.path.join(CKPT_DIR, "unit_sanity.json")
    if not os.path.exists(p):
        raise SystemExit("WALL: run --stage unit_sanity first.")
    d = _load_json(p)
    if not d.get("ok_all"):
        raise SystemExit("WALL: unit_sanity did not pass.")
    return d


# ===================================================================================================
# STAGE: calibrate -- background margin threshold (p25) + spread_r -> w_r. Mirrors run 45's own
# `stage_calibrate` exactly, with the diff-region term replaced by the relational-distance term
# over the geo top-2, gated additionally by query-multi-stroke (design choice #2b) -- computed
# for EVERY background episode regardless of the not-yet-frozen threshold (a single-stroke query
# contributes an all-zero term vector, exactly its real-eval shape).
# ===================================================================================================
def _run_calibrate_block(spec: dict, codebook_s, codebook_native, cache: dict,
                          weights: dict) -> list:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    out = []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = scratch._inner
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            full_pairs = _full_pairs(scratch, qn, node_of_cand)
            top2 = cf.top2_from_pairs(native, full_pairs)
            margin = cf.top2_margin(top2)
            multistroke = _is_multistroke(path)
            term_vec = [0.0] * WAY
            if len(top2) >= 2 and multistroke:
                cand1_idx, cand2_idx = top2[0][1], top2[1][1]
                q_dec = _decode(codebook_s, cache, path)
                c1_dec = _decode(codebook_s, cache, drawer_files[cand1_idx][ex_drawer])
                c2_dec = _decode(codebook_s, cache, drawer_files[cand2_idx][ex_drawer])
                terms = _relational_terms_for_top2(codebook_native, q_dec, c1_dec, c2_dec,
                                                    cand1_idx, cand2_idx, weights)
                for ci, val in terms.items():
                    term_vec[ci] = val
            out.append(dict(margin=margin, r_spread=float(np.std(term_vec)),
                             multistroke=multistroke))
    return out


def stage_calibrate() -> int:
    print(f"\n{SEP}\n  STAGE: calibrate -- background margin threshold + relational-term spread "
          f"(-> w_r)\n{SEP}")
    if os.path.exists(CALIB_PATH):
        frozen = _load_json(CALIB_PATH)
        print(f"  ALREADY FROZEN: {CALIB_PATH}")
        _print_calibrate(frozen)
        return 0
    _require_unit_sanity()
    if not os.path.exists(SPREAD_PATH_44B):
        print(f"  WALL: {SPREAD_PATH_44B} not found -- 44b's own --stage spread is required as "
              f"a READ-ONLY reference (this run never recomputes it).")
        sys.exit(1)
    spread44b = _load_json(SPREAD_PATH_44B)
    weights = _require_weights()
    print(f"  READ (read-only) 44b's own background spreads: smoothdeform="
          f"{spread44b['spreads']['smoothdeform']:.5f}  part={spread44b['spreads']['part']:.5f}  "
          f"sc={spread44b['spreads']['sc']:.5f}")
    print(f"  READ (read-only) run 50's own frozen relational weights: {weights}")

    md5_before = _md5(STROKE_SHAPES_SEED)
    blocks = run44b._background_blocks()
    n_target = len(blocks) * WAY
    state = _load_json(CALIB_STATE_PATH) if os.path.exists(CALIB_STATE_PATH) else dict(
        block_idx=0, per_episode=[])

    codebook_s = _load_codebook_substrate()
    codebook_native = codebook_s._inner
    cache: dict = {}

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        run44b._block_spec_split(blocks[i][0], rng, WAY, EPISODES_PER_ALPHABET, "background")

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
        alph, r = blocks[state["block_idx"]]
        spec = run44b._block_spec_split(alph, rng, WAY, EPISODES_PER_ALPHABET, "background")
        recs = _run_calibrate_block(spec, codebook_s, codebook_native, cache, weights)
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
    spread_r = float(np.mean([e["r_spread"] for e in per_episode]))
    n_multistroke = sum(1 for e in per_episode if e["multistroke"])
    w_r = dm.derive_w_aff(spread44b["spreads"]["smoothdeform"], spread44b["spreads"]["part"],
                           spread44b["spreads"]["sc"], spread_r)
    frozen = dict(n_episodes=n_target, n_finite_margins=len(margins), margin_pctl=MARGIN_PCTL,
                  threshold=threshold, n_multistroke=n_multistroke,
                  multistroke_frac=n_multistroke / len(per_episode) if per_episode else 0.0,
                  spread_r=spread_r, w_r=w_r,
                  spread44b_smoothdeform=spread44b["spreads"]["smoothdeform"],
                  spread44b_part=spread44b["spreads"]["part"],
                  spread44b_sc=spread44b["spreads"]["sc"],
                  margins=margins, background_alphabets=run44b._background_alphabets(),
                  weights=weights)
    _save_json(frozen, CALIB_PATH)
    print(f"\n  FROZEN calibration ({n_target} background episodes) -- {CALIB_PATH}")
    _print_calibrate(frozen)

    md5_after = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 AFTER calibrate: {md5_after}  "
          f"UNCHANGED={md5_after == md5_before}")
    if md5_after != md5_before:
        raise SystemExit("HARD STOP: seed write detected during --stage calibrate.")
    return 0


def _print_calibrate(frozen: dict) -> None:
    print(f"    n_episodes={frozen['n_episodes']}  n_finite_margins={frozen['n_finite_margins']}")
    print(f"    n_multistroke={frozen['n_multistroke']}  multistroke_frac="
          f"{100*frozen['multistroke_frac']:.1f}% (background)")
    print(f"    threshold (p{frozen['margin_pctl']:.0f} of background top-2 margins) = "
          f"{frozen['threshold']:.6f}")
    print(f"    spread_r (background, relational term over geo top-2) = "
          f"{frozen['spread_r']:.6f}")
    print(f"    target_spread (44b median smoothdeform/part/sc, read-only) -- smoothdeform="
          f"{frozen['spread44b_smoothdeform']:.5f} part={frozen['spread44b_part']:.5f} "
          f"sc={frozen['spread44b_sc']:.5f}")
    print(f"    w_r = median(smoothdeform,part,sc) / spread_r = {frozen['w_r']:.6f}")
    print(f"    K (adjudication shortlist) = 2 (the geo top-2 itself, PRE-REGISTERED)")


def _require_calibrate() -> dict:
    if not os.path.exists(CALIB_PATH):
        print("  WALL: run --stage calibrate to completion first.")
        sys.exit(1)
    return _load_json(CALIB_PATH)


# ===================================================================================================
# ONE EPISODE'S ARM-C prediction (shared by --stage sanity and --stage eval).
# ===================================================================================================
def _armc_episode(native, scratch, qn, node_of_cand: dict, drawer_files: list, ex_drawer,
                   path: str, threshold: float, w_r: float, weights: dict, codebook_s,
                   codebook_native, cache: dict) -> dict:
    full_pairs = _full_pairs(scratch, qn, node_of_cand)
    pred_full = _argmin_ci(native, full_pairs)
    top2 = cf.top2_from_pairs(native, full_pairs)
    margin = cf.top2_margin(top2)
    multistroke = _is_multistroke(path)
    fired = len(top2) >= 2 and _fires_conditional(margin, threshold, multistroke)

    if not fired:
        pred_armc, _ = _armc_from_terms(native, full_pairs, False, {}, w_r)
        return dict(pred_full=pred_full, pred_armc=pred_armc, fired=False, margin=margin,
                    multistroke=multistroke, full_pairs=full_pairs)

    cand1_idx, cand2_idx = top2[0][1], top2[1][1]
    q_dec = _decode(codebook_s, cache, path)
    c1_dec = _decode(codebook_s, cache, drawer_files[cand1_idx][ex_drawer])
    c2_dec = _decode(codebook_s, cache, drawer_files[cand2_idx][ex_drawer])
    terms = _relational_terms_for_top2(codebook_native, q_dec, c1_dec, c2_dec, cand1_idx,
                                        cand2_idx, weights)
    pred_armc, pairs_prime = _armc_from_terms(native, full_pairs, True, terms, w_r)
    return dict(pred_full=pred_full, pred_armc=pred_armc, fired=True, margin=margin,
                multistroke=multistroke, full_pairs=full_pairs, cand1_idx=cand1_idx,
                cand2_idx=cand2_idx, r1=terms[cand1_idx], r2=terms[cand2_idx],
                winner_in_top2=bool(pred_armc in (cand1_idx, cand2_idx)))


# ===================================================================================================
# STAGE: sanity -- THE HARD STOP. Background baseline vs armed accuracy, BEFORE any eval spend.
# ===================================================================================================
def _run_sanity_block(spec: dict, threshold: float, w_r: float, weights: dict, codebook_s,
                       codebook_native, cache: dict) -> tuple:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    baseline_recs, armed_recs = [], []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = scratch._inner
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            r_ = _armc_episode(native, scratch, qn, node_of_cand, drawer_files, ex_drawer, path,
                                threshold, w_r, weights, codebook_s, codebook_native, cache)
            baseline_recs.append(dict(true=qi, correct=bool(r_["pred_full"] == qi)))
            armed_recs.append(dict(true=qi, correct=bool(r_["pred_armc"] == qi),
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
    weights = _require_weights()
    threshold, w_r = calib["threshold"], calib["w_r"]
    print(f"  threshold={threshold:.6f}  w_r={w_r:.6f}  (from --stage calibrate)")

    blocks = run44b._background_blocks()
    n_target = len(blocks) * WAY
    state = _load_json(SANITY_STATE_PATH) if os.path.exists(SANITY_STATE_PATH) else dict(
        block_idx=0, baseline=[], armed=[])

    codebook_s = _load_codebook_substrate()
    codebook_native = codebook_s._inner
    cache: dict = {}

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        run44b._block_spec_split(blocks[i][0], rng, WAY, EPISODES_PER_ALPHABET, "background")

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
        alph, r = blocks[state["block_idx"]]
        spec = run44b._block_spec_split(alph, rng, WAY, EPISODES_PER_ALPHABET, "background")
        base_recs, armed_recs = _run_sanity_block(spec, threshold, w_r, weights, codebook_s,
                                                   codebook_native, cache)
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
    frozen = dict(threshold=threshold, w_r=w_r, n=n, n_fired=n_fired,
                  k_baseline=k_base, k_armed=k_armed, acc_baseline=acc_base, acc_armed=acc_armed,
                  sanity_margin=SANITY_MARGIN, passed=bool(passed))
    _save_json(frozen, SANITY_PATH)
    _print_sanity(frozen)
    return 0


def _print_sanity(frozen: dict) -> None:
    print(f"\n  ---- BACKGROUND-SANITY GATE (n={frozen['n']}, fired={frozen['n_fired']}, "
          f"threshold={frozen['threshold']:.6f}, w_r={frozen['w_r']:.6f}) ----")
    print(f"    baseline (unmodified fused recipe): acc={100*frozen['acc_baseline']:.1f}%  "
          f"k={frozen['k_baseline']}/{frozen['n']}")
    print(f"    armed    (conditional relational adjudication): acc={100*frozen['acc_armed']:.1f}%"
          f"  k={frozen['k_armed']}/{frozen['n']}")
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
    md5_now = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5: {md5_now}")
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
# STAGE: eval -- ARM C at n=400, the standard test-alphabet protocol.
# ===================================================================================================
def _run_block_arm_c(alph: str, r: int, spec: dict, threshold: float, w_r: float, weights: dict,
                      codebook_s, codebook_native, cache: dict) -> list:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    recs = []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        native = scratch._inner
        node_of_cand, _ = run25._stage_candidates(scratch, drawer_files, ex_drawer, WAY,
                                                   thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            r_ = _armc_episode(native, scratch, qn, node_of_cand, drawer_files, ex_drawer, path,
                                threshold, w_r, weights, codebook_s, codebook_native, cache)
            recs.append(dict(true=qi, alph=alph, r=r, pred_full=r_["pred_full"],
                              pred_armc=r_["pred_armc"], correct_full=bool(r_["pred_full"] == qi),
                              correct_armc=bool(r_["pred_armc"] == qi), fired=r_["fired"],
                              multistroke=r_["multistroke"], margin=r_["margin"],
                              cand1_idx=r_.get("cand1_idx"), cand2_idx=r_.get("cand2_idx"),
                              r1=r_.get("r1"), r2=r_.get("r2"),
                              winner_in_top2=r_.get("winner_in_top2")))
    return recs


def stage_eval() -> int:
    print(f"\n{SEP}\n  STAGE: eval (ARM C -- conditional relational adjudication)\n{SEP}")
    calib = _require_calibrate()
    sanity = _require_sanity()
    _require_guard()
    weights = _require_weights()
    if not sanity["passed"]:
        print("  WALL: sanity STOPPED -- per this run's own binding rule, NO eval budget may "
              "be spent. Report the sanity finding and stop here.")
        return 1
    threshold, w_r = calib["threshold"], calib["w_r"]
    print(f"  threshold={threshold:.6f}  w_r={w_r:.6f}")

    state = _load_json(EVAL_PATH) if os.path.exists(EVAL_PATH) else dict(
        records=[], block_idx=0, done=False)
    if state.get("done"):
        print(f"  eval already COMPLETE (n={len(state['records'])}).")
        return 0

    blocks = _blocks()
    print(f"  blocks={len(blocks)} (target n={len(blocks) * WAY})  "
          f"resuming at block {state['block_idx']}  [37C hygiene filter: ON]")

    codebook_s = _load_codebook_substrate()
    codebook_native = codebook_s._inner
    cache: dict = {}

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
        recs = _run_block_arm_c(alph, r, spec, threshold, w_r, weights, codebook_s,
                                 codebook_native, cache)
        for pos, rec in enumerate(recs):
            rec["idx"] = state["block_idx"] * WAY + pos
        state["records"].extend(recs)
        state["block_idx"] += 1
        _save_json(state, EVAL_PATH)
        print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
              f"{len(state['records'])} episodes so far, {time.time()-bt0:.1f}s this block, "
              f"{time.time()-t0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        k_full = sum(1 for rec in state["records"] if rec["correct_full"])
        k_armc = sum(1 for rec in state["records"] if rec["correct_armc"])
        n = len(state["records"])
        state["acc_full"] = dict(acc=k_full / n, ci=list(_wilson(k_full, n)), k=k_full, n=n)
        state["acc_armc"] = dict(acc=k_armc / n, ci=list(_wilson(k_armc, n)), k=k_armc, n=n)
        state["wall_clock_seconds"] = state.get("wall_clock_seconds", 0.0) + (time.time() - t0)
        _save_json(state, EVAL_PATH)
        print(f"\n  EVAL COMPLETE: n={n}  GLOBAL(own recompute) acc={100*k_full/n:.1f}% k={k_full}"
              f"  ARM C acc={100*k_armc/n:.1f}% k={k_armc}")
    else:
        state["wall_clock_seconds"] = state.get("wall_clock_seconds", 0.0) + (time.time() - t0)
        _save_json(state, EVAL_PATH)
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-invoke to "
              f"continue. ({time.time()-t0:.1f}s this call)")
    return 0


# ===================================================================================================
# STAGE: report -- background-sanity FIRST, fire-rate + multi-stroke coverage, McNemar overall +
# fired-only, accuracies + CIs, frozen threshold/K/w_r, fixed/broken structure, honest anomalies.
# ===================================================================================================
def _mcnemar(correct_a: list, correct_b: list) -> dict:
    """`fixed`: a WRONG -> b RIGHT. `broken`: a RIGHT -> b WRONG."""
    fixed = sum(1 for a, b in zip(correct_a, correct_b) if (not a) and b)
    broken = sum(1 for a, b in zip(correct_a, correct_b) if a and (not b))
    n_disc = fixed + broken
    p = float(binomtest(fixed, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    return dict(fixed=fixed, broken=broken, discordant=n_disc, p=p)


def stage_report() -> int:
    print(f"\n{SEP}\n  RUN 51 -- CONDITIONAL RELATIONAL VERDICT -- FINAL REPORT\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5: {md5_now}")

    calib = _require_calibrate()
    sanity = _require_sanity()
    print(f"\n{'='*35}  SANITY-GATE (decides everything)  {'='*35}")
    _print_sanity(sanity)
    print(f"\n  ---- CALIBRATION ----")
    _print_calibrate(calib)
    print(f"\n  ---- RUN 50's OWN CITED LICENSE (verbatim, commit 563322d3) ----")
    print(f"    corr(r,geo)={RUN50_CORR}  conditional-on-geo-wrong lift={100*RUN50_CONDITIONAL_LIFT:.1f}%"
          f"  r_separation={RUN50_R_SEPARATION}x  geo_separation={RUN50_GEO_SEPARATION}x")

    if not sanity["passed"]:
        print(f"\n  {'='*30}  SANITY STOPPED -- NO EVAL WAS RUN, PER THIS RUN'S OWN BINDING "
              f"RULE  {'='*30}")
        print(f"  (armed background accuracy {100*sanity['acc_armed']:.1f}% fell more than "
              f"{100*sanity['sanity_margin']:.0f}pp below baseline {100*sanity['acc_baseline']:.1f}%)")
        print(f"\n  VERDICT: even before an eval-alphabet episode was spent, the conditional "
              f"relational adjudication HARMS background accuracy beyond the free-gate bound. "
              f"This localizes the finding to the FUSION MECHANISM even more directly than an "
              f"eval-level null would: the orthogonal signal (run 50) does not survive this "
              f"particular bolt-on shape even in-sample on background.")
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
          f"{'MATCH' if global_ok else 'MISMATCH -- STOP, protocol bug, do not trust ARM C'}")
    if not global_ok:
        return 1

    n_multistroke = sum(1 for r_ in records if r_["multistroke"])
    fired_recs = [r_ for r_ in records if r_["fired"]]
    n_fired = len(fired_recs)
    print(f"\n  ---- MULTI-STROKE COVERAGE + FIRE RATE ----")
    print(f"    multi-stroke queries: {n_multistroke}/{n} = {100*n_multistroke/n:.1f}%")
    print(f"    fired: {n_fired}/{n} = {100*n_fired/n:.1f}%  (of multi-stroke queries: "
          f"{100*n_fired/n_multistroke if n_multistroke else 0:.1f}%)")
    print(f"    threshold={calib['threshold']:.6f} (background p{calib['margin_pctl']:.0f})  "
          f"K=2 (geo top-2)  w_r={calib['w_r']:.6f}")

    # ---- Non-fired structural identity check. ------------------------------------------------
    nonfired_mismatches = [r_ for r_ in records if not r_["fired"]
                            and r_["pred_full"] != r_["pred_armc"]]
    print(f"\n  ---- STRUCTURAL CHECK ----")
    print(f"    non-fired episodes with pred_full != pred_armc: {len(nonfired_mismatches)}/"
          f"{n - n_fired} (must be 0 -- `supplement_pairs` with an empty terms dict is a no-op)")

    correct_full = [r_["correct_full"] for r_ in records]
    correct_armc = [r_["correct_armc"] for r_ in records]
    k_armc = sum(correct_armc)

    mc_overall = _mcnemar(correct_full, correct_armc)
    print(f"\n  ---- McNEMAR OVERALL (n={n}) ----")
    print(f"    GLOBAL: k={k_full}/{n}  ARM C: k={k_armc}/{n}")
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
    correct_armc_fired = [r_["correct_armc"] for r_ in fired_recs]
    mc_fired = _mcnemar(correct_full_fired, correct_armc_fired) if fired_recs else dict(
        fixed=0, broken=0, discordant=0, p=1.0)
    print(f"\n  ---- McNEMAR RESTRICTED TO FIRED EPISODES (n={n_fired}) ----")
    print(f"    fixed={mc_fired['fixed']}  broken={mc_fired['broken']}  "
          f"discordant={mc_fired['discordant']}  p={mc_fired['p']:.4g}")

    ci_full = _wilson(k_full, n)
    ci_armc = _wilson(k_armc, n)
    print(f"\n  ---- ACCURACIES (Wilson 95% CI) ----")
    print(f"    GLOBAL: acc={100*k_full/n:.1f}%  [{100*ci_full[0]:.1f}%, {100*ci_full[1]:.1f}%]  "
          f"k={k_full}/{n}")
    print(f"    ARM C:  acc={100*k_armc/n:.1f}%  [{100*ci_armc[0]:.1f}%, {100*ci_armc[1]:.1f}%]  "
          f"k={k_armc}/{n}")
    print(f"    CI-separated: {gate._ci_separated(tuple(ci_armc), tuple(ci_full))}  (McNemar "
          f"above is the powered test for this effect size)")

    # ---- fixed/broken structure: margin + run40 band (idx-joined, read-only, coverage caveat). -
    classify_path = os.path.join(RUN40_DIR, "classify.json")
    classify = _load_json(classify_path) if os.path.exists(classify_path) else {"rows": []}
    classify_by_idx = {row["idx"]: row for row in classify["rows"]}
    print(f"\n  run40 classify.json: {len(classify_by_idx)}/{n} idx-labelled episodes "
          f"(READ-ONLY reference, coverage caveat)")
    fixed_idx = {r_["idx"] for r_ in records if (not r_["correct_full"]) and r_["correct_armc"]}
    broken_idx = {r_["idx"] for r_ in records if r_["correct_full"] and (not r_["correct_armc"])}
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

    fired_margins = [r_["margin"] for r_ in fired_recs if np.isfinite(r_["margin"])]
    fixed_margins = [r_["margin"] for r_ in fired_recs if r_["idx"] in fixed_idx
                      and np.isfinite(r_["margin"])]
    broken_margins = [r_["margin"] for r_ in fired_recs if r_["idx"] in broken_idx
                       and np.isfinite(r_["margin"])]
    print(f"\n  ---- FIRED-EPISODE MARGIN STRUCTURE (does the mechanism concentrate at the "
          f"LOWEST margins within the fired set?) ----")
    print(f"    fired margins: mean={np.mean(fired_margins) if fired_margins else float('nan'):.5f}"
          f"  n={len(fired_margins)}")
    print(f"    fixed margins: mean="
          f"{np.mean(fixed_margins) if fixed_margins else float('nan'):.5f}  n={len(fixed_margins)}")
    print(f"    broken margins: mean="
          f"{np.mean(broken_margins) if broken_margins else float('nan'):.5f}  n={len(broken_margins)}")

    n_r_would_have_fixed = sum(1 for r_ in fired_recs if r_["idx"] in fixed_idx)
    n_r_would_have_broken = sum(1 for r_ in fired_recs if r_["idx"] in broken_idx)
    print(f"\n  ---- HONEST ANOMALIES ----")
    print(f"    fired episodes where the ARM-C winner escaped the geo top-2 entirely "
          f"(w_r pushed both top-2 candidates behind a third): "
          f"{sum(1 for r_ in fired_recs if r_.get('winner_in_top2') is False)}/{n_fired}")
    print(f"    fired episodes with a NaN/degenerate r1 or r2: "
          f"{sum(1 for r_ in fired_recs if r_.get('r1') != r_.get('r1') or r_.get('r2') != r_.get('r2'))}")

    out = dict(n=n, n_multistroke=n_multistroke, n_fired=n_fired,
               mcnemar_overall=mc_overall, mcnemar_fired=mc_fired,
               acc_full=dict(acc=k_full/n, ci=list(ci_full), k=k_full),
               acc_armc=dict(acc=k_armc/n, ci=list(ci_armc), k=k_armc),
               band_counts={b: dict(c) for b, c in band_counts.items()},
               fired_margin_mean=float(np.mean(fired_margins)) if fired_margins else None,
               fixed_margin_mean=float(np.mean(fixed_margins)) if fixed_margins else None,
               broken_margin_mean=float(np.mean(broken_margins)) if broken_margins else None,
               nonfired_mismatches=len(nonfired_mismatches), threshold=calib["threshold"],
               w_r=calib["w_r"], K=2)
    _save_json(out, REPORT_PATH)
    print(f"\n  report.json written.")

    print(f"\n  {'='*30}  DOES IT CONVERT?  {'='*30}")
    if mc_overall["discordant"] and mc_overall["fixed"] > mc_overall["broken"] and \
            gate._ci_separated(tuple(ci_armc), tuple(ci_full)):
        print(f"  WIN: the orthogonal top-down signal (run 50) CONVERTS to accuracy under "
              f"conditional adjudication -- the first crack in the twelve-null 80.5% ceiling.")
    elif mc_overall["discordant"] and mc_overall["fixed"] > mc_overall["broken"]:
        print(f"  WEAK POSITIVE: fixed > broken but not CI-separated / not the powered McNemar "
              f"threshold -- suggestive, not conclusive; report as a lead, not a result.")
    elif mc_overall["discordant"] and mc_overall["broken"] >= mc_overall["fixed"]:
        print(f"  NULL (STOP CONDITION): broken >= fixed -- even this orthogonal, conditionally-"
              f"gated channel does not convert to accuracy. This LOCALIZES the gap to the FUSION "
              f"MECHANISM: an additive bolt-on over a K=2 shortlist cannot cash in evidence that "
              f"is real (run 50's own diagnostic) but weaker (1.32x vs 2.05x separation) and only "
              f"informative for a genuine subset of episodes. The next lever is the FULL top-down "
              f"loop (the concept's variation model re-deriving or re-weighting the geo comparison "
              f"itself, not a small additive supplement), not a bigger/differently-tuned bolt-on.")
    else:
        print(f"  NULL: no discordant pairs / no effect either direction.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  seeds/stroke_shapes.json md5 (post-run, must equal the pre-run value above): "
          f"{_md5(STROKE_SHAPES_SEED)}")
    return 0


STAGES = {"unit_sanity": stage_unit_sanity, "calibrate": stage_calibrate, "sanity": stage_sanity,
          "guard": stage_guard, "eval": stage_eval, "report": stage_report}


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
