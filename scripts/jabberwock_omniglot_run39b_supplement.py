"""OMNIGLOT RUN 39B -- THE FULL GATE: the MOTOR-PLAN AGREEMENT SCORE as an ADDITIVE evidence
channel, two arms, both licensed by RUN 39 GATE 0 (commit 6b85f14c, `scripts/jabberwock_
omniglot_run39_motorplan.py`): TRANSITIONS (pen-up travel sector) and START POSITION (first
pen-down grid cell) are LIVE (class-shuffled-null excess); ORDER/DIRECTION are DEAD and never
used. `domains/motor_plan.py` (this run's own module) turns those two features into a single
QUERY-VS-CANDIDATE agreement score `m in [0, 1]` (see that module's own top-of-file docstring
for the pre-registered formula: `m = 0.5*start_agree + 0.5*transitions_frac`, weights fixed a
priori, transitions honestly SKIPPED -- never imputed -- on a stroke-count mismatch).

RUN 36 (5aa6bcb6) found 78 full-dwell errors at n=400, 32.1% of which pick the rank-1/2
impostor on near-identical geometry -- the motor plan is orthogonal evidence, untried at the
verdict layer. BINDING LAW 37A (cca938fd): focused/auxiliary evidence SUPPLEMENTS integrated
evidence, never replaces it (no whole-verdict substitution) -- both arms below obey this
structurally, not by discipline alone (`lam=0.0` in `motor_plan.combined_verdict` is BYTE-
IDENTICAL to the GLOBAL verdict; `motor_plan.propose_by_motor_plan`'s output is only ever
UNIONED via `committed_shape.union_candidates`, a pure superset). NO TEST-SET TUNING: `lam`
(ARM V) and `threshold` (ARM P) are calibrated ONCE on background-alphabet episodes (the 5
LEARN alphabets -- `gate.LEARN_ALPHABETS_N`, background split, quarantined from the 10
evaluation alphabets this gate's own eval touches) and FROZEN before any eval number exists.

TWO ARMS, on the SAME 400 evaluation episodes (`run25._block_spec`, `POWER_SEED = gate.SEED +
1500`, WAY=20, R_TARGET=2, N_TEST_ALPHABETS=10 sorted-name prefix -- byte-identical to
`results/run26_checkpoints/eval_baseline.json`):

  ARM V -- VERDICT SUPPLEMENT (the prize, targets RUN 36's 78 full-dwell errors): final score
  = `abs_read.parse_marginal_pair_error` (the GLOBAL verdict's own per-candidate error, lower =
  better) MINUS `lam * m(query, candidate)` -- `motor_plan.combined_verdict`, held `Argmin`.
  `lam` is chosen from the pre-registered grid `motor_plan.LAMBDA_GRID = (0.05, 0.1, 0.2, 0.4)`
  by maximizing BACKGROUND calibration accuracy (ties -> smallest lam), frozen by `--stage
  calibrate` into `results/run39_checkpoints/calibration.json`, read (never recomputed) by
  `--stage eval_v`. SECONDARY (reported if wall-clock allows -- computed FOR FREE from
  `--stage eval_v`'s own per-episode top-2 margin, no extra native evaluate calls): the
  PARAMETER-FREE TIE-BREAK variant -- `m` decides only when the top-2 GLOBAL margin is BELOW
  the median within-episode margin gap over the whole eval set (`stage_report`'s own analysis,
  a corpus-level descriptive statistic, not a per-candidate ranking decision).

  ARM P -- PROPOSAL MODALITY #4 (targets coverage, additive into the RUN 37B union): candidates
  with `m >= threshold` (background-calibrated, `motor_plan.THRESHOLD_GRID = (1.0, 0.75,
  0.5)`, chosen by maximizing the Youden-style `recall_true(threshold) - fpr_other(threshold)`
  over the SAME background calibration set, ties -> LARGEST threshold i.e. the more
  conservative/lower-noise choice) OR, when none clear it, the top `motor_plan.K_ADD_DEFAULT`
  (5) by `m` -- `motor_plan.propose_by_motor_plan`, additive-only union on top of RUN 37B's own
  UNION (structural shortlist@10 unioned with committed-shape proposals, `results/run37b_
  checkpoints`'s own mechanism, `domains/committed_shape.py`), never touching the verdict
  mechanism itself (`abs_read.parse_marginal_verdict`, restaged only over whichever candidate
  set is asked, exactly RUN 37B's own additive-invariant optimization).

CALIBRATION (`--stage calibrate`, background split, `_block_spec_bg` -- this script's own
evaluation-split-free clone of `run25._block_spec`, needed because that function hardcodes
`ow.characters(alph, "evaluation")`): 5 LEARN alphabets x R_CALIB=2 blocks x WAY=20 =
`N_CALIB=200` episodes, `CALIB_SEED` distinct from `POWER_SEED` (never reused for eval). This
uses ONLY the full-dwell GLOBAL protocol (`ar.stage_parse_char`/`parse_marginal_pair_error`,
NO fitted codebook, NO `learn.json` dependency at all -- `DEFAULT_PARSE_THETAS`/`part_w`/
`sc_w`/`beta` are RUN 18's own fixed constants, not fit on any LEARN data) so this calibration
is clean of the codebook-fitting contamination risk a structural-shortlist/committed-shape
pass on the SAME 5 LEARN alphabets would carry (that machinery's own `tol_deg`/`level_edges`/
`delta_edges`, cited from `results/run35_checkpoints/programs.json`, WAS fit on those
alphabets) -- `threshold`'s own calibration objective (below) is likewise computed purely from
`m` and each episode's own true-class label, never touching the structural codebook either.
  LAMBDA objective: accuracy of `motor_plan.combined_verdict(..., lam)` on the N_CALIB
  episodes, maximized over `LAMBDA_GRID`, ties -> smallest lam (stated a priori).
  THRESHOLD objective (Youden-style, pooling every (candidate, is_true_class) pair across all
  N_CALIB x WAY = 4000 candidate instances): `recall_true(t) = mean(m >= t | true class)`,
  `fpr_other(t) = mean(m >= t | not true class)`; `threshold* = argmax_t recall_true(t) -
  fpr_other(t)` over `THRESHOLD_GRID`, ties -> LARGEST t (fewer, higher-precision proposals).

GUARDS (checked in `--stage report`, never silently bypassed): the UNSUPPLEMENTED global
verdict must reproduce RUN 25/37A's cited 80.5% [76.3, 84.1] k=322/400 EXACTLY (ARM V's own
baseline); the RUN 37B UNION arm must reproduce ITS OWN cited 76.5%/66.0% coverage/accuracy
(k=306/400, k=264/400 -- `results/run37b_checkpoints/report.json`'s own `union_coverage`/
`union_shortlist_acc` blocks, ARM P's own baseline). A guard mismatch is a protocol bug, STOP
-- report and do not trust the arm above it.

PRIMARY ANALYSES (pre-registered, `--stage report`): ARM V -- paired McNemar on accuracy flips
(GLOBAL wrong -> ARM-V right = fixed; GLOBAL right -> ARM-V wrong = broken), PREDICTION: fixes
concentrate in RUN 36's own rank-1/2-impostor error class and in Ge_ez/Kannada (RUN 36's own
near-rank-mass alphabets). ARM P -- paired McNemar on COVERAGE flips vs the 37B union (fixed =
newly covered, broken = MUST be 0, a pure-additive union, asserted as a structural invariant
exactly RUN 37B's own STOP discipline) and a SECONDARY McNemar on accuracy flips, PREDICTION:
gains concentrate in 1-2-stroke true classes (RUN 36's own bucket convention, `run36._bucket`,
reused verbatim). STOPS: broken >= fixed in either arm's PRIMARY McNemar means that arm HARMS
-- report and stop recommending it, never re-tune `lam`/`threshold` against the eval outcome.

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run39.log`, per-BLOCK checkpoints under `results/run39_checkpoints/`
(gate0.json already there, extended -- not overwritten; every OTHER run*_checkpoints dir,
including run26's own `learn.json`/`eval_baseline.json`, run35's own `programs.json`, and
run37b's own `report.json`, READ-ONLY reference, never written here). `.venv` python (needs
`substrate_rs`). `seeds/stroke_shapes.json` is READ (md5 recorded before/after, parallel-
session-owned) but never written -- verified every stage.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run39b_supplement.py --stage guard
  ... --stage calibrate
  ... --stage eval_v      (re-invoke until COMPLETE -- checkpointed per block)
  ... --stage eval_p      (re-invoke until COMPLETE -- checkpointed per block)
  ... --stage report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np
from scipy.stats import binomtest

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run25_number as run25
import scripts.jabberwock_omniglot_run26_homework as run26
import scripts.jabberwock_omniglot_run36_failures as run36
import scripts.jabberwock_omniglot_run39_motorplan as gate0
from domains import abs_read as ar
from domains import committed_shape as cs
from domains import motor_plan as mp
from domains import omniglot_world as ow
from scripts.jabberwock_omniglot_run37c_hygiene import DropDegenerateFilter

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run39_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")     # READ-ONLY reference.
RUN35_DIR = os.path.join(ROOT, "results", "run35_checkpoints")     # READ-ONLY reference.
RUN37B_DIR = os.path.join(ROOT, "results", "run37b_checkpoints")   # READ-ONLY reference.
STROKE_SHAPES_PATH = os.path.join(ROOT, "seeds", "stroke_shapes.json")   # parallel-session-
                                                                          # owned -- READ-ONLY.
os.makedirs(CKPT_DIR, exist_ok=True)

WAY = run25.WAY                                        # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET    # 20
R_TARGET = run25.R_TARGET                              # 2 -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS              # 10
POWER_SEED = run25.POWER_SEED                          # gate.SEED + 1500, the arc's own eval
                                                        # seed -- unchanged, never reused below
                                                        # for calibration.
SHORTLIST_K = run26.SHORTLIST_K                        # 10 (of 20)
DK = gate.DK                                            # segments=8, max_knots=16.
K_ADD_37B = cs.K_ADD_DEFAULT                            # 5 -- run37b's own committed-shape cap.
K_ADD_MOTOR = mp.K_ADD_DEFAULT                          # 5 -- this run's own motor-plan cap.
MAX_UNION_WIDTH_CAP = SHORTLIST_K + K_ADD_37B + K_ADD_MOTOR   # 20 == WAY, a trivial explosion
                                                               # ceiling reported honestly.
PER_CALL_BUDGET_V = 480.0      # ARM V's own protocol (run37a's own shape) is cheap, ~55s/400.
PER_CALL_BUDGET_P = 420.0      # ARM P's own protocol (run37b's own shape) is expensive,
                                # ~430-500s/400 -- leaves headroom under the 540s foreground cap
                                # and expects >=2 invocations to complete.

# Cited VERBATIM -- ARM V's own GLOBAL guard target (results/run26_checkpoints/eval_
# baseline.json == RUN 25/17b/37A's own C0 control).
BASELINE_FULL_DWELL = dict(acc=0.805, ci=(0.7633481418022936, 0.8408493586537856), n=400, k=322)
# Cited VERBATIM -- ARM P's own 37B-UNION guard target (results/run37b_checkpoints/
# report.json's own `union_coverage`/`union_shortlist_acc` blocks).
BASELINE_37B_UNION_COVERAGE = dict(k=306, n=400,
                                    ci=(0.721049458815452, 0.8039090251873708))
BASELINE_37B_UNION_ACC = dict(k=264, n=400, ci=(0.6122516850900368, 0.7047043807229884))

# ---------------------------------------------------------------------------------------------
# Calibration population -- 5 LEARN alphabets (background split), a seed DISTINCT from
# POWER_SEED (never used for eval), R_CALIB=2 blocks/alphabet -> N_CALIB = 5*2*20 = 200.
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = gate.LEARN_ALPHABETS_N              # 5
CALIB_SEED = gate.SEED + 3700                            # distinct from POWER_SEED (SEED+1500).
R_CALIB = 2


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    run26._save_json(obj, path)


def _load_json(path: str):
    return run26._load_json(path)


def _md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def _donkey0() -> bool:
    return run26._donkey0()


def _test_alphabets():
    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= WAY)
    return qualifying[:N_TEST_ALPHABETS]


def _calib_alphabets():
    return ow.alphabets("background")[:LEARN_ALPHABETS_N]


def _wilson(k: int, n: int) -> tuple:
    return gate.wilson_ci(k, n)


def _block_spec_bg(alph: str, rng, way: int, episodes_per_alphabet: int) -> dict:
    """`run25._block_spec`'s own byte-identical mechanic, BACKGROUND split -- that function
    hardcodes `ow.characters(alph, "evaluation")`, so this run needs its own copy to touch the
    5 LEARN alphabets without risking an accidental edit to `run25.py` (a read-only reference
    module for every other run in this arc)."""
    chars = sorted(ow.characters(alph, "background"))[:way]
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


def _top2_margin(native, full_pairs: list) -> tuple:
    """Held-Term top-2 margin over an ALREADY-COMPUTED `(err, ci)` list -- `contrastive_
    verdict.top2_candidates`'s own repeated-held-Argmin idiom, inlined here since this script
    already has `full_pairs` in hand (no re-staging). Returns `(top1_err, top2_err, margin)`,
    any of which may be `None` for a degenerate (<2-candidate) pool -- an honest non-crash."""
    w1 = native.evaluate(ar._argmin_pairs_term(full_pairs), {})
    if w1 is None:
        return None, None, None
    top1_err, top1_ci = float(w1[0]), int(w1[1])
    remaining = [(e, ci) for e, ci in full_pairs if ci != top1_ci]
    if not remaining:
        return top1_err, None, None
    w2 = native.evaluate(ar._argmin_pairs_term(remaining), {})
    top2_err = float(w2[0]) if w2 is not None else None
    margin = (top2_err - top1_err) if top2_err is not None else None
    return top1_err, top2_err, margin


# =============================================================================================
# STAGE: guard -- protocol reproduction (GLOBAL + 37B-union block 0) + a cheap motor-plan
# engagement spot-check, mirroring run37a/run37b's own stage_guard precedent.
# =============================================================================================
def stage_guard() -> int:
    print(f"\n{SEP}\n  STAGE: guard -- protocol reproduction (GLOBAL + 37B union) + motor-plan "
          f"engagement spot-check\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_PATH)
    print(f"  seeds/stroke_shapes.json md5 (parallel-session-owned, this run never writes "
          f"there): {md5_now}")

    baseline_records = _load_json(os.path.join(RUN26_DIR, "eval_baseline.json"))["records"][:WAY]
    test_alphabets = _test_alphabets()
    rng = np.random.default_rng(POWER_SEED)
    spec = run25._block_spec(test_alphabets[0], rng, WAY, EPISODES_PER_ALPHABET)

    # ---- ARM V: full-dwell GLOBAL, block 0. ----------------------------------------------------
    drawer_files_ = spec["drawer_files"]
    scratch0 = srs.Substrate()
    native0 = scratch0._inner
    node0, cand0 = run25._stage_candidates(scratch0, drawer_files_, spec["ex_drawer"], WAY,
                                            thetas=ar.DEFAULT_PARSE_THETAS)
    t0 = time.time()
    with DropDegenerateFilter():
        exemplar_xy = [gate0.normalize_glyph_xy(ow.load_strokes(drawer_files_[ci][spec["ex_drawer"]]))
                       for ci in range(WAY)]
        got_v = []
        for qi, q_drawer in spec["queries"]:
            path = drawer_files_[qi][q_drawer]
            qn0 = ar.stage_parse_char(scratch0, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
            w0 = ar.parse_marginal_verdict(scratch0, qn0)
            pred_full = cand0.get(w0, -1) if w0 is not None else -1
            query_xy = gate0.normalize_glyph_xy(ow.load_strokes(path))
            m_res = {ci: mp.motor_plan_agreement(native0, query_xy, exemplar_xy[ci])
                     for ci in range(WAY)}
            got_v.append(dict(pred_full=pred_full,
                               skip_reasons={ci: r["skip_reason"] for ci, r in m_res.items()}))
    print(f"  ARM V block 0 ({test_alphabets[0]!r}) computed in {time.time()-t0:.1f}s.")

    mismatches = [(i, g["pred_full"], b["pred_full"])
                  for i, (g, b) in enumerate(zip(got_v, baseline_records))
                  if g["pred_full"] != b["pred_full"]]
    global_ok = not mismatches
    print(f"  GLOBAL arm vs eval_baseline.json, block 0 ({len(got_v)} episodes): "
          f"{'EXACT MATCH' if global_ok else f'{len(mismatches)} MISMATCHES'}")
    for i, gv, bv in mismatches[:10]:
        print(f"    MISMATCH episode {i}: got pred_full={gv} baseline={bv}")

    skip_counts: dict = defaultdict(int)
    for g in got_v:
        for reason in g["skip_reasons"].values():
            skip_counts[reason or "computed"] += 1
    print(f"  motor-plan m computation on block 0 ({len(got_v)*WAY} query-candidate pairs): "
          f"{dict(skip_counts)}")

    # ---- ARM P: shortlist + committed-shape UNION, block 0 (mirrors run37b's own guard). -------
    edges = cs.load_cited_program_edges(os.path.join(RUN35_DIR, "programs.json"))
    print(f"  CITED committed-shape edges (results/run35_checkpoints/programs.json): "
          f"tol_deg={edges['tol_deg']:.4f}  level_edges({len(edges['level_edges'])-1} bins)  "
          f"delta_edges({len(edges['delta_edges'])-1} bins)")
    src = os.path.join(RUN26_DIR, "learn.json")
    t0 = time.time()
    s = run26._load_graph(src)
    native_learn = s._inner
    print(f"  learn.json loaded ({time.time()-t0:.1f}s).")
    cache: dict = {}
    t0 = time.time()
    baseline_37b_records = _load_json(os.path.join(RUN37B_DIR, "eval_run37b.json"))["records"][:WAY]
    with DropDegenerateFilter():
        got_p = _run_block_p(s, native_learn, cache, edges, test_alphabets[0], 0, spec,
                              threshold=mp.THRESHOLD_GRID[0])
    print(f"  ARM P block 0 ({test_alphabets[0]!r}) computed in {time.time()-t0:.1f}s.")

    mismatches_p = []
    for i, (g, b) in enumerate(zip(got_p, baseline_37b_records)):
        if g["in_union_37b"] != b["in_union"]:
            mismatches_p.append((i, "in_union_37b", g["in_union_37b"], b["in_union"]))
        if g["pred_37b_union"] != b["pred_union"]:
            mismatches_p.append((i, "pred_37b_union", g["pred_37b_union"], b["pred_union"]))
    union_ok = not mismatches_p
    print(f"  37B-UNION arm vs run37b's own eval_run37b.json, block 0 ({len(got_p)} episodes): "
          f"{'EXACT MATCH' if union_ok else f'{len(mismatches_p)} MISMATCHES'}")
    for i, key, gv, bv in mismatches_p[:10]:
        print(f"    MISMATCH episode {i} {key}: got={gv} baseline={bv}")

    n_motor_added = sum(1 for g in got_p if g["motor_added"] > 0)
    print(f"  motor-plan proposal engagement (block 0, threshold not yet frozen -- using "
          f"THRESHOLD_GRID[0]={mp.THRESHOLD_GRID[0]} as a spot-check only, NOT the frozen "
          f"eval value): episodes with a genuine addition: {n_motor_added}/{len(got_p)}")

    guard_ok = global_ok and union_ok
    out = dict(guard_ok=guard_ok, global_ok=global_ok, union_ok=union_ok,
               spot_check_mismatches_v=len(mismatches), spot_check_mismatches_p=len(mismatches_p),
               stroke_shapes_md5=md5_now, edges=edges, skip_counts_block0=dict(skip_counts),
               n_motor_added_block0=n_motor_added)
    _save_json(out, _ckpt("guard.json"))
    print(f"\n  GUARD: {'PASS -- proceed to --stage calibrate' if guard_ok else 'FAIL -- STOP'}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0 if guard_ok else 1


def _require_guard():
    p = _ckpt("guard.json")
    if not os.path.exists(p):
        print("  WALL: run --stage guard first.")
        sys.exit(1)
    g = _load_json(p)
    if not g.get("guard_ok"):
        print("  WALL: --stage guard did not PASS -- fix the protocol mismatch first.")
        sys.exit(1)
    return g


# =============================================================================================
# ARM P per-episode body -- structural shortlist + committed-shape UNION (run37b's own
# mechanism, reused) + motor-plan proposal UNIONED on top (this run's own addition), verdict
# staged only over whichever candidate set changed (run37b's own additive-invariant
# optimization, extended one union further).
# =============================================================================================
def _run_block_p(s, native, cache, edges, alph: str, r: int, spec: dict,
                  threshold: float | None = None) -> list:
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, DK)
                 for ci in range(WAY)]
    exemplar_composed = [e["composed_sig"] for e in exemplars]
    exemplar_commits = [
        cs.commit_shape(ow.load_strokes(drawer_files[ci][ex_drawer]),
                         segments=DK["segments"], max_knots=DK["max_knots"], **edges)
        for ci in range(WAY)
    ]
    exemplar_xy = [gate0.normalize_glyph_xy(ow.load_strokes(drawer_files[ci][ex_drawer]))
                   for ci in range(WAY)]

    records = []
    for qi, q_drawer in spec["queries"]:
        path = drawer_files[qi][q_drawer]
        rec = {"true": qi, "alph": alph, "r": r}

        qd = gate.decode_char_signature(s, path, cache, DK)
        shortlist = ar.propose_top_k(native, qd["composed_sig"], exemplar_composed, k=SHORTLIST_K)

        query_commit = cs.commit_shape(ow.load_strokes(path), segments=DK["segments"],
                                        max_knots=DK["max_knots"], **edges)
        committed = cs.propose_by_committed_shape(query_commit, exemplar_commits, k=K_ADD_37B)
        union_37b = cs.union_candidates(shortlist, committed)
        rec["in_union_37b"] = bool(qi in union_37b)

        query_xy = gate0.normalize_glyph_xy(ow.load_strokes(path))
        m_scores = [(ci, mp.motor_plan_agreement(native, query_xy, exemplar_xy[ci])["m"])
                    for ci in range(WAY)]
        rec["m_scores"] = {ci: m for ci, m in m_scores}
        if threshold is None:
            union_39b = list(union_37b)     # guard/spot-check path: no frozen threshold yet.
            motor_candidates: list = []
        else:
            motor_candidates = mp.propose_by_motor_plan(native, m_scores, threshold=threshold,
                                                          k_add=K_ADD_MOTOR)
            union_39b = cs.union_candidates(union_37b, motor_candidates)
        rec["motor_candidates"] = motor_candidates
        rec["in_union_39b"] = bool(qi in union_39b)
        rec["union_39b_width"] = len(union_39b)
        rec["motor_added"] = len(union_39b) - len(union_37b)

        scratch_37b = srs.Substrate()
        cand_37b = {}
        for ci in union_37b:
            node = ar.stage_parse_char(scratch_37b, drawer_files[ci][ex_drawer], is_query=False,
                                        name=str(ci))
            cand_37b[node] = ci
        qn_37b = ar.stage_parse_char(scratch_37b, path, is_query=True)
        w_37b = ar.parse_marginal_verdict(scratch_37b, qn_37b)
        rec["pred_37b_union"] = cand_37b.get(w_37b, -1) if w_37b is not None else -1

        if set(union_39b) == set(union_37b):
            rec["pred_39b_union"] = rec["pred_37b_union"]
        else:
            scratch_39b = srs.Substrate()
            cand_39b = {}
            for ci in union_39b:
                node = ar.stage_parse_char(scratch_39b, drawer_files[ci][ex_drawer],
                                            is_query=False, name=str(ci))
                cand_39b[node] = ci
            qn_39b = ar.stage_parse_char(scratch_39b, path, is_query=True)
            w_39b = ar.parse_marginal_verdict(scratch_39b, qn_39b)
            rec["pred_39b_union"] = cand_39b.get(w_39b, -1) if w_39b is not None else -1
        records.append(rec)
    return records


# =============================================================================================
# STAGE: calibrate -- 200 background (LEARN-alphabet) episodes, full-dwell GLOBAL protocol
# only (no learn.json, no structural codebook -- see module docstring for the contamination
# rationale). Freezes lam (ARM V) and threshold (ARM P) into calibration.json.
# =============================================================================================
def stage_calibrate() -> int:
    print(f"\n{SEP}\n  STAGE: calibrate -- N_CALIB=200 background (LEARN-alphabet) episodes, "
          f"CALIB_SEED={CALIB_SEED} (distinct from POWER_SEED)\n{SEP}")
    _require_guard()
    out_path = _ckpt("calibration_records.json")
    calib_alphabets = _calib_alphabets()
    print(f"  calibration alphabets (background split, LEARN_ALPHABETS_N={LEARN_ALPHABETS_N}): "
          f"{calib_alphabets}")
    blocks = [(alph, r) for alph in calib_alphabets for r in range(R_CALIB)]
    print(f"  blocks={len(blocks)} (target N_CALIB={len(blocks)*WAY})")

    rng = np.random.default_rng(CALIB_SEED)
    records: list = []
    t0 = time.time()
    with DropDegenerateFilter():
        for alph, r in blocks:
            spec = _block_spec_bg(alph, rng, WAY, EPISODES_PER_ALPHABET)
            drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
            scratch0 = srs.Substrate()
            native0 = scratch0._inner
            node0, cand0 = run25._stage_candidates(scratch0, drawer_files, ex_drawer, WAY,
                                                    thetas=ar.DEFAULT_PARSE_THETAS)
            exemplar_xy = [gate0.normalize_glyph_xy(ow.load_strokes(drawer_files[ci][ex_drawer]))
                           for ci in range(WAY)]
            for qi, q_drawer in spec["queries"]:
                path = drawer_files[qi][q_drawer]
                qn0 = ar.stage_parse_char(scratch0, path, is_query=True,
                                           thetas=ar.DEFAULT_PARSE_THETAS)
                full_pairs = [(ar.parse_marginal_pair_error(scratch0, qn0, node0[ci]), ci)
                              for ci in range(WAY)]
                query_xy = gate0.normalize_glyph_xy(ow.load_strokes(path))
                m_scores = {ci: mp.motor_plan_agreement(native0, query_xy, exemplar_xy[ci])["m"]
                            for ci in range(WAY)}
                records.append(dict(true=qi, alph=alph, r=r, full_pairs=full_pairs,
                                     m_scores=m_scores))
            print(f"  block ({alph!r} r={r}) done -- {len(records)}/{len(blocks)*WAY} episodes, "
                  f"{time.time()-t0:.1f}s so far")
    _save_json(dict(records=records, n=len(records)), out_path)
    print(f"\n  N_CALIB={len(records)} episodes computed, {time.time()-t0:.1f}s total.")

    # ---- LAMBDA: maximize combined_verdict accuracy over LAMBDA_GRID, ties -> smallest. --------
    native_scratch = srs.Substrate()._inner
    lambda_curve = {}
    acc0 = sum(1 for rec in records
               if mp.combined_verdict(native_scratch, rec["full_pairs"], rec["m_scores"], 0.0)
               == rec["true"]) / len(records)
    lambda_curve["0.0"] = acc0
    for lam in mp.LAMBDA_GRID:
        k = sum(1 for rec in records
                if mp.combined_verdict(native_scratch, rec["full_pairs"], rec["m_scores"], lam)
                == rec["true"])
        lambda_curve[str(lam)] = k / len(records)
    best_lam = min(mp.LAMBDA_GRID, key=lambda L: (-lambda_curve[str(L)], L))
    print(f"\n  LAMBDA calibration curve (accuracy on N_CALIB={len(records)}): "
          f"lam=0.0(reference)={100*acc0:.1f}%  " +
          "  ".join(f"lam={L}={100*lambda_curve[str(L)]:.1f}%" for L in mp.LAMBDA_GRID))
    print(f"  CHOSEN lam* = {best_lam} (argmax over LAMBDA_GRID, ties->smallest; "
          f"{'BEATS' if lambda_curve[str(best_lam)] > acc0 else 'does NOT beat'} the lam=0 "
          f"reference -- reported honestly either way, frozen regardless per pre-registration)")

    # ---- THRESHOLD: Youden-style recall_true - fpr_other over THRESHOLD_GRID, ties->largest. ---
    threshold_curve = {}
    for t in mp.THRESHOLD_GRID:
        true_hits = other_hits = n_true = n_other = 0
        for rec in records:
            for ci, m in rec["m_scores"].items():
                is_true = (int(ci) == rec["true"])
                if is_true:
                    n_true += 1
                    true_hits += int(m >= t)
                else:
                    n_other += 1
                    other_hits += int(m >= t)
        recall_true = true_hits / n_true if n_true else 0.0
        fpr_other = other_hits / n_other if n_other else 0.0
        threshold_curve[str(t)] = dict(recall_true=recall_true, fpr_other=fpr_other,
                                        youden=recall_true - fpr_other)
    best_threshold = max(mp.THRESHOLD_GRID,
                          key=lambda T: (threshold_curve[str(T)]["youden"], T))
    print(f"\n  THRESHOLD calibration curve (Youden = recall_true - fpr_other, pooled over "
          f"{len(records)*WAY} candidate instances):")
    for t in mp.THRESHOLD_GRID:
        c = threshold_curve[str(t)]
        print(f"    t={t:<5} recall_true={100*c['recall_true']:.1f}%  "
              f"fpr_other={100*c['fpr_other']:.1f}%  youden={c['youden']:+.4f}")
    print(f"  CHOSEN threshold* = {best_threshold} (argmax Youden over THRESHOLD_GRID, "
          f"ties->largest)")

    calibration = dict(lam=best_lam, threshold=best_threshold, lambda_curve=lambda_curve,
                        threshold_curve=threshold_curve, n_calib=len(records),
                        calib_seed=CALIB_SEED, calib_alphabets=calib_alphabets)
    _save_json(calibration, _ckpt("calibration.json"))
    print(f"\n  FROZEN -> {_ckpt('calibration.json')}  lam={best_lam}  threshold={best_threshold}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _require_calibration():
    p = _ckpt("calibration.json")
    if not os.path.exists(p):
        print("  WALL: run --stage calibrate first.")
        sys.exit(1)
    return _load_json(p)


# =============================================================================================
# STAGE: eval_v -- ARM V, full n=400, GLOBAL + combined_verdict(lam), filter ON.
# =============================================================================================
def stage_eval_v() -> int:
    print(f"\n{SEP}\n  STAGE: eval_v -- ARM V, n=400, GLOBAL + motor-plan supplement, filter ON"
          f"\n{SEP}")
    _require_guard()
    calib = _require_calibration()
    lam = calib["lam"]
    print(f"  FROZEN lam={lam} (from calibration.json, N_CALIB={calib['n_calib']}) -- never "
          f"recomputed here.")
    out_path = _ckpt("eval_v.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_idx=0, done=False)
    if state.get("done"):
        print(f"  eval_v already COMPLETE (n={len(state['records'])}).")
        return 0

    test_alphabets = _test_alphabets()
    blocks = [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]
    print(f"  test_alphabets={test_alphabets}")
    print(f"  blocks={len(blocks)} (target n={len(blocks)*WAY}) resuming at block "
          f"{state['block_idx']}")

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        alph, r = blocks[i]
        run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)

    hard_deadline = time.time() + PER_CALL_BUDGET_V
    t0 = time.time()
    with DropDegenerateFilter():
        while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
            alph, r = blocks[state["block_idx"]]
            spec = run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)
            drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
            scratch0 = srs.Substrate()
            native0 = scratch0._inner
            node0, cand0 = run25._stage_candidates(scratch0, drawer_files, ex_drawer, WAY,
                                                    thetas=ar.DEFAULT_PARSE_THETAS)
            exemplar_xy = [gate0.normalize_glyph_xy(ow.load_strokes(drawer_files[ci][ex_drawer]))
                           for ci in range(WAY)]
            for qi, q_drawer in spec["queries"]:
                path = drawer_files[qi][q_drawer]
                rec = {"true": qi, "alph": alph, "r": r}
                qn0 = ar.stage_parse_char(scratch0, path, is_query=True,
                                           thetas=ar.DEFAULT_PARSE_THETAS)
                w0 = ar.parse_marginal_verdict(scratch0, qn0)
                rec["pred_full"] = cand0.get(w0, -1) if w0 is not None else -1

                full_pairs = [(ar.parse_marginal_pair_error(scratch0, qn0, node0[ci]), ci)
                              for ci in range(WAY)]
                top1_err, top2_err, margin = _top2_margin(native0, full_pairs)
                rec["margin"] = margin

                query_xy = gate0.normalize_glyph_xy(ow.load_strokes(path))
                m_by_idx = {ci: mp.motor_plan_agreement(native0, query_xy, exemplar_xy[ci])["m"]
                            for ci in range(WAY)}
                rec["pred_v"] = mp.combined_verdict(native0, full_pairs, m_by_idx, lam)
                state["records"].append(rec)
            state["block_idx"] += 1
            _save_json(state, out_path)
            print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
                  f"{len(state['records'])} episodes so far, {time.time()-t0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        _save_json(state, out_path)
        print(f"\n  eval_v COMPLETE: n={len(state['records'])}")
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-run "
              f"'--stage eval_v' to continue.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# =============================================================================================
# STAGE: eval_p -- ARM P, full n=400, 37B union + motor-plan proposal, filter ON.
# =============================================================================================
def stage_eval_p() -> int:
    print(f"\n{SEP}\n  STAGE: eval_p -- ARM P, n=400, 37B union + motor-plan proposal, filter ON"
          f"\n{SEP}")
    guard = _require_guard()
    calib = _require_calibration()
    threshold = calib["threshold"]
    print(f"  FROZEN threshold={threshold} (from calibration.json, N_CALIB={calib['n_calib']}) "
          f"-- never recomputed here.")
    edges = guard["edges"]
    out_path = _ckpt("eval_p.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_idx=0, done=False)
    if state.get("done"):
        print(f"  eval_p already COMPLETE (n={len(state['records'])}).")
        return 0

    src = os.path.join(RUN26_DIR, "learn.json")
    t0 = time.time()
    s = run26._load_graph(src)
    native = s._inner
    print(f"  learn.json loaded ({time.time()-t0:.1f}s) -- READ-ONLY reference.")

    test_alphabets = _test_alphabets()
    blocks = [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]
    print(f"  test_alphabets={test_alphabets}")
    print(f"  blocks={len(blocks)} (target n={len(blocks)*WAY}) resuming at block "
          f"{state['block_idx']}")

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        alph, r = blocks[i]
        run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)

    cache: dict = {}
    hard_deadline = time.time() + PER_CALL_BUDGET_P
    t_loop0 = time.time()
    with DropDegenerateFilter():
        while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
            alph, r = blocks[state["block_idx"]]
            spec = run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)
            recs = _run_block_p(s, native, cache, edges, alph, r, spec, threshold=threshold)
            state["records"].extend(recs)
            state["block_idx"] += 1
            _save_json(state, out_path)
            print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
                  f"{len(state['records'])} episodes so far, {time.time()-t_loop0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        _save_json(state, out_path)
        print(f"\n  eval_p COMPLETE: n={len(state['records'])}")
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-run "
              f"'--stage eval_p' to continue.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# =============================================================================================
# STAGE: report -- ARM V McNemar FIRST, then ARM P, guards, calibration, breakdowns, anomalies.
# =============================================================================================
def _class_stroke_buckets(records: list, test_alphabets: list) -> dict:
    chars_by_alph = {a: sorted(ow.characters(a, "evaluation"))[:WAY] for a in test_alphabets}
    stroke_count: dict = {}
    out = {}
    for i, r in enumerate(records):
        cd = chars_by_alph[r["alph"]][r["true"]]
        if cd not in stroke_count:
            counts = [len(ow.load_strokes(f)) for f in ow.drawings(cd)]
            stroke_count[cd] = float(np.median(counts))
        out[i] = run36._bucket(stroke_count[cd])
    return out


def stage_report() -> int:
    print(f"\n{SEP}\n  RUN 39B -- MOTOR-PLAN SUPPLEMENT -- FINAL REPORT\n{SEP}")
    ev_v_path, ev_p_path = _ckpt("eval_v.json"), _ckpt("eval_p.json")
    if not os.path.exists(ev_v_path) or not _load_json(ev_v_path).get("done"):
        print("  eval_v not yet COMPLETE -- run --stage eval_v to completion first.")
        return 1
    if not os.path.exists(ev_p_path) or not _load_json(ev_p_path).get("done"):
        print("  eval_p not yet COMPLETE -- run --stage eval_p to completion first.")
        return 1
    calib = _require_calibration()
    records_v = _load_json(ev_v_path)["records"]
    records_p = _load_json(ev_p_path)["records"]
    n_v, n_p = len(records_v), len(records_p)
    print(f"  n_v={n_v}  n_p={n_p}  lam={calib['lam']}  threshold={calib['threshold']}")

    # =========================================================================================
    #  ARM V -- THE 80.5 QUESTION, FIRST.
    # =========================================================================================
    print(f"\n{'#'*92}\n  ARM V -- VERDICT SUPPLEMENT (lam={calib['lam']})\n{'#'*92}")
    k_full = sum(1 for r in records_v if r["pred_full"] == r["true"])
    global_ok = (k_full == BASELINE_FULL_DWELL["k"])
    ci_full = _wilson(k_full, n_v)
    print(f"\n  GLOBAL (protocol guard): acc={100*k_full/n_v:.1f}% [{100*ci_full[0]:.1f}%, "
          f"{100*ci_full[1]:.1f}%] k={k_full}/{n_v} (cited k={BASELINE_FULL_DWELL['k']}) -- "
          f"{'MATCH' if global_ok else 'MISMATCH -- STOP, protocol bug'}")
    if not global_ok:
        return 1

    k_v = sum(1 for r in records_v if r["pred_v"] == r["true"])
    ci_v = _wilson(k_v, n_v)
    fixed_v = [r for r in records_v if r["pred_full"] != r["true"] and r["pred_v"] == r["true"]]
    broken_v = [r for r in records_v if r["pred_full"] == r["true"] and r["pred_v"] != r["true"]]
    n_fixed_v, n_broken_v = len(fixed_v), len(broken_v)
    n_disc_v = n_fixed_v + n_broken_v
    p_v = float(binomtest(n_fixed_v, n_disc_v, 0.5, alternative="two-sided").pvalue) \
        if n_disc_v else 1.0
    print(f"\n  {'='*80}\n  McNEMAR (PRIMARY, ARM V) -- accuracy flips vs GLOBAL:\n  {'='*80}")
    print(f"    fixed  (GLOBAL wrong -> ARM-V right): {n_fixed_v}")
    print(f"    broken (GLOBAL right -> ARM-V wrong): {n_broken_v}")
    print(f"    discordant total: {n_disc_v}   p-value: {p_v:.4f}")
    if n_disc_v == 0:
        print(f"    (no discordant pairs -- the two arms never disagree)")
    elif n_broken_v >= n_fixed_v:
        print(f"    STOP CONDITION: broken >= fixed -- ARM V HARMS or is a wash on this "
              f"sample, reported as the finding, never re-tuned against this outcome.")
    else:
        print(f"    fixed > broken: ARM V nets POSITIVE "
              f"({'significant at p<0.05' if p_v < 0.05 else 'not significant at p<0.05'}).")
    print(f"\n  ACCURACIES (Wilson 95% CI): GLOBAL={100*k_full/n_v:.1f}% "
          f"[{100*ci_full[0]:.1f}%,{100*ci_full[1]:.1f}%]  ARM-V={100*k_v/n_v:.1f}% "
          f"[{100*ci_v[0]:.1f}%,{100*ci_v[1]:.1f}%]  "
          f"CI-separated={gate._ci_separated(tuple(ci_v), tuple(ci_full))}")

    per_alph_v: dict = {}
    for r in records_v:
        d = per_alph_v.setdefault(r["alph"], dict(fixed=0, broken=0, n=0))
        d["n"] += 1
    for r in fixed_v:
        per_alph_v[r["alph"]]["fixed"] += 1
    for r in broken_v:
        per_alph_v[r["alph"]]["broken"] += 1
    print(f"\n  PER-ALPHABET fixed/broken (prediction: concentrates in Ge_ez/Kannada):")
    for alph in sorted(per_alph_v):
        d = per_alph_v[alph]
        print(f"    {alph:<22} n={d['n']:>3}  fixed={d['fixed']:>2}  broken={d['broken']:>2}")

    test_alphabets = _test_alphabets()
    buckets_v = _class_stroke_buckets(records_v, test_alphabets)
    fixed_idx_v = {i for i, r in enumerate(records_v)
                   if r["pred_full"] != r["true"] and r["pred_v"] == r["true"]}
    bucket_order = ["1", "2", "3", "4", "5+"]
    print(f"\n  RANK-OF-FIXED by stroke-count bucket of the TRUE class (prediction: fixes land "
          f"on RUN 36's own near-rank-1/2-impostor errors, not stroke-count-correlated):")
    bucket_fixed_v = {b: 0 for b in bucket_order}
    for i in fixed_idx_v:
        bucket_fixed_v[buckets_v[i]] += 1
    for b in bucket_order:
        print(f"    strokes={b:<3}  fixed={bucket_fixed_v[b]}")

    # TIE-BREAK secondary variant -- computed FOR FREE from eval_v's own margin field.
    margins = [r["margin"] for r in records_v if r.get("margin") is not None]
    median_margin = float(np.median(margins)) if margins else float("inf")
    k_tb = sum(1 for r in records_v
               if (r["pred_v"] if (r.get("margin") is not None and r["margin"] < median_margin)
                   else r["pred_full"]) == r["true"])
    ci_tb = _wilson(k_tb, n_v)
    fixed_tb = broken_tb = 0
    for r in records_v:
        use_v = r.get("margin") is not None and r["margin"] < median_margin
        pred_tb = r["pred_v"] if use_v else r["pred_full"]
        if r["pred_full"] != r["true"] and pred_tb == r["true"]:
            fixed_tb += 1
        elif r["pred_full"] == r["true"] and pred_tb != r["true"]:
            broken_tb += 1
    print(f"\n  SECONDARY -- parameter-free TIE-BREAK variant (m decides only when the top-2 "
          f"GLOBAL margin < median margin={median_margin:.4f}, computed post-hoc, no extra "
          f"native evaluates): acc={100*k_tb/n_v:.1f}% [{100*ci_tb[0]:.1f}%,"
          f"{100*ci_tb[1]:.1f}%] k={k_tb}/{n_v}  fixed={fixed_tb}  broken={broken_tb}")

    # =========================================================================================
    #  ARM P -- COVERAGE, SECOND.
    # =========================================================================================
    print(f"\n{'#'*92}\n  ARM P -- PROPOSAL MODALITY #4 (threshold={calib['threshold']})\n{'#'*92}")
    k_cov_37b = sum(1 for r in records_p if r["in_union_37b"])
    k_acc_37b = sum(1 for r in records_p if r["pred_37b_union"] == r["true"])
    cov_ok = (k_cov_37b == BASELINE_37B_UNION_COVERAGE["k"])
    acc_ok = (k_acc_37b == BASELINE_37B_UNION_ACC["k"])
    print(f"\n  37B-UNION (protocol guard): coverage k={k_cov_37b}/{n_p} (cited k="
          f"{BASELINE_37B_UNION_COVERAGE['k']}) -- {'MATCH' if cov_ok else 'MISMATCH'}; "
          f"accuracy k={k_acc_37b}/{n_p} (cited k={BASELINE_37B_UNION_ACC['k']}) -- "
          f"{'MATCH' if acc_ok else 'MISMATCH'}")
    if not (cov_ok and acc_ok):
        print("  STOP: protocol bug -- 37B-UNION does not reproduce the cited numbers, do not "
              "trust ARM P below.")
        return 1

    k_cov_39b = sum(1 for r in records_p if r["in_union_39b"])
    k_acc_39b = sum(1 for r in records_p if r["pred_39b_union"] == r["true"])
    ci_cov_37b, ci_cov_39b = _wilson(k_cov_37b, n_p), _wilson(k_cov_39b, n_p)
    ci_acc_37b, ci_acc_39b = _wilson(k_acc_37b, n_p), _wilson(k_acc_39b, n_p)

    cov_fixed = [r for r in records_p if not r["in_union_37b"] and r["in_union_39b"]]
    cov_broken = [r for r in records_p if r["in_union_37b"] and not r["in_union_39b"]]
    n_cf, n_cb = len(cov_fixed), len(cov_broken)
    print(f"\n  {'='*80}\n  McNEMAR #1 (PRIMARY, ARM P) -- COVERAGE flips vs the 37B union:"
          f"\n  {'='*80}")
    print(f"    fixed  (37B-union NOT covered -> 39B-union covered): {n_cf}")
    print(f"    broken (37B-union covered -> 39B-union NOT covered): {n_cb}")
    if n_cb > 0:
        print(f"    STOP: broken coverage > 0 is IMPOSSIBLE under a pure-additive union -- "
              f"this is a PROTOCOL BUG in the union wiring, not a research finding.")
        return 1
    print(f"    broken == 0 -- CONFIRMED structurally additive (as designed).")
    n_cov_disc = n_cf + n_cb
    p_cov = float(binomtest(n_cf, n_cov_disc, 0.5, alternative="two-sided").pvalue) \
        if n_cov_disc else 1.0
    print(f"    discordant total: {n_cov_disc}   p-value: {p_cov:.4g}")

    buckets_p = _class_stroke_buckets(records_p, test_alphabets)
    fixed_idx_p = {i for i, r in enumerate(records_p)
                   if not r["in_union_37b"] and r["in_union_39b"]}
    bucket_totals_p = {b: 0 for b in bucket_order}
    bucket_fixed_p = {b: 0 for b in bucket_order}
    for i in range(n_p):
        b = buckets_p[i]
        bucket_totals_p[b] += 1
        if i in fixed_idx_p:
            bucket_fixed_p[b] += 1
    print(f"\n  PER-STROKE-BUCKET concentration of gained-coverage episodes (prediction: "
          f"concentrates in 1-2):")
    for b in bucket_order:
        tot, fx = bucket_totals_p[b], bucket_fixed_p[b]
        rate = f"{100*fx/tot:.1f}%" if tot else "n/a"
        print(f"    strokes={b:<3}  gained={fx:>3}/{tot:<3}  share={rate}")

    acc_fixed = [r for r in records_p
                 if r["pred_37b_union"] != r["true"] and r["pred_39b_union"] == r["true"]]
    acc_broken = [r for r in records_p
                  if r["pred_37b_union"] == r["true"] and r["pred_39b_union"] != r["true"]]
    n_af, n_ab = len(acc_fixed), len(acc_broken)
    n_acc_disc = n_af + n_ab
    p_acc = float(binomtest(n_af, n_acc_disc, 0.5, alternative="two-sided").pvalue) \
        if n_acc_disc else 1.0
    print(f"\n  {'='*80}\n  McNEMAR #2 (SECONDARY, ARM P) -- accuracy flips vs the 37B union:"
          f"\n  {'='*80}")
    print(f"    fixed  (37B-union wrong -> 39B-union right): {n_af}")
    print(f"    broken (37B-union right -> 39B-union wrong): {n_ab}")
    print(f"    discordant total: {n_acc_disc}   p-value: {p_acc:.4f}")
    if n_acc_disc and n_ab >= n_af:
        print(f"    NOTE: broken >= fixed on accuracy -- the added candidates diluted the "
              f"verdict as often as (or more than) they helped it (the run-11 dilution risk).")
    conversion = (n_af / n_cf) if n_cf else float("nan")
    print(f"    CONVERSION: {n_af}/{n_cf} = "
          f"{100*conversion:.1f}% of gained-coverage episodes converted to a correct verdict."
          if n_cf else "    CONVERSION: n/a (0 gained-coverage episodes).")

    print(f"\n  COVERAGE (Wilson 95% CI): 37B-UNION={100*k_cov_37b/n_p:.1f}% "
          f"[{100*ci_cov_37b[0]:.1f}%,{100*ci_cov_37b[1]:.1f}%]  "
          f"39B-UNION={100*k_cov_39b/n_p:.1f}% [{100*ci_cov_39b[0]:.1f}%,"
          f"{100*ci_cov_39b[1]:.1f}%]")
    print(f"  ACCURACY (Wilson 95% CI): 37B-UNION={100*k_acc_37b/n_p:.1f}% "
          f"[{100*ci_acc_37b[0]:.1f}%,{100*ci_acc_37b[1]:.1f}%]  "
          f"39B-UNION={100*k_acc_39b/n_p:.1f}% [{100*ci_acc_39b[0]:.1f}%,"
          f"{100*ci_acc_39b[1]:.1f}%]")

    widths = [r["union_39b_width"] for r in records_p]
    added = [r["motor_added"] for r in records_p]
    max_width = max(widths)
    print(f"\n  UNION-39B WIDTH (cap={MAX_UNION_WIDTH_CAP}): mean={np.mean(widths):.2f}  "
          f"max={max_width}  motor_added: mean={np.mean(added):.2f}  "
          f"episodes_with_addition={sum(1 for a in added if a>0)}/{n_p} "
          f"({100*sum(1 for a in added if a>0)/n_p:.1f}%)")
    width_exploded = max_width > MAX_UNION_WIDTH_CAP

    # ---- engagement: skip-rate + m distribution across BOTH arms' own m_scores. ---------------
    all_m_v = []
    for r in records_v:
        pass  # eval_v does not persist per-candidate skip reasons (guard already spot-checked
              # them on block 0) -- engagement below is read off eval_p's own m_scores, the
              # SAME motor_plan_agreement computation, same population.
    for r in records_p:
        all_m_v.extend(r["m_scores"].values())
    m_arr = np.asarray(all_m_v, dtype=float)
    print(f"\n  ENGAGEMENT -- m distribution over {m_arr.size} query-candidate pairs (eval_p's "
          f"own m_scores, ARM V's population is byte-identical by construction): "
          f"mean={m_arr.mean():.3f}  median={np.median(m_arr):.3f}  "
          f"frac_m_ge_0.5={float((m_arr>=0.5).mean()):.3f}  frac_m_eq_1.0={float((m_arr>=0.999).mean()):.3f}")
    n_v_changed = sum(1 for r in records_v if r["pred_v"] != r["pred_full"])
    print(f"  ARM V: episodes where the supplement changed the decision: {n_v_changed}/{n_v} "
          f"({100*n_v_changed/n_v:.1f}%)")

    print(f"\n  {'='*80}\n  HONEST ANOMALIES\n  {'='*80}")
    anomalies = []
    if n_broken_v >= n_fixed_v and n_disc_v:
        anomalies.append("ARM V: broken >= fixed -- the verdict supplement harms or washes on "
                          "this sample.")
    if width_exploded:
        anomalies.append(f"ARM P: union-39b width exceeded the pre-registered cap "
                          f"({max_width} > {MAX_UNION_WIDTH_CAP}).")
    if n_acc_disc and n_ab >= n_af:
        anomalies.append("ARM P: accuracy broken >= fixed -- widening diluted as often as it "
                          "helped (the run-11 dilution family).")
    if n_cf == 0:
        anomalies.append("ARM P: zero gained-coverage episodes -- the motor-plan modality "
                          "never engaged where the 37B union was already blind.")
    if not anomalies:
        print("  none -- both arms behaved as designed.")
    else:
        for a in anomalies:
            print(f"  - {a}")

    out = dict(
        n_v=n_v, n_p=n_p, lam=calib["lam"], threshold=calib["threshold"],
        arm_v=dict(global_acc=k_full/n_v, global_ci=list(ci_full), global_k=k_full,
                   armv_acc=k_v/n_v, armv_ci=list(ci_v), armv_k=k_v,
                   n_fixed=n_fixed_v, n_broken=n_broken_v, mcnemar_p=p_v,
                   per_alphabet=per_alph_v, bucket_fixed=bucket_fixed_v,
                   tiebreak_acc=k_tb/n_v, tiebreak_ci=list(ci_tb), tiebreak_fixed=fixed_tb,
                   tiebreak_broken=broken_tb, median_margin=median_margin,
                   n_decision_changed=n_v_changed),
        arm_p=dict(cov37b_k=k_cov_37b, cov39b_k=k_cov_39b, cov37b_ci=list(ci_cov_37b),
                   cov39b_ci=list(ci_cov_39b), acc37b_k=k_acc_37b, acc39b_k=k_acc_39b,
                   acc37b_ci=list(ci_acc_37b), acc39b_ci=list(ci_acc_39b),
                   mcnemar_coverage=dict(fixed=n_cf, broken=n_cb, p=p_cov),
                   mcnemar_accuracy=dict(fixed=n_af, broken=n_ab, p=p_acc),
                   conversion=conversion, bucket_totals=bucket_totals_p,
                   bucket_fixed=bucket_fixed_p,
                   union_width=dict(mean=float(np.mean(widths)), max=max_width)),
        calibration=calib, anomalies=anomalies,
    )
    _save_json(out, _ckpt("report.json"))
    print(f"\n  report.json written -> {_ckpt('report.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


STAGES = {"guard": stage_guard, "calibrate": stage_calibrate, "eval_v": stage_eval_v,
          "eval_p": stage_eval_p, "report": stage_report}


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
