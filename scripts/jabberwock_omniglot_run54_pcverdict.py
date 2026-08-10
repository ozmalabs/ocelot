"""OMNIGLOT RUN 54 -- THE LOOP-FLIP: A COMPOSITIONAL PREDICTIVE-CODING VERDICT.

THE PIVOT (creator correction, load-bearing -- see `domains/compositional_verdict.py`'s own
header): a graph HOLDS a character at MULTIPLE GRAINS AT ONCE. So the verdict is NOT "per-stroke
INSTEAD OF whole-shape" (that framing was an error). It is the whole-shape SC+TPS residual (the
standing 80.5% GUARD's OWN parse-marginal error, `abs_read.parse_marginal_pair_error`) as the
TOP-LEVEL term, WITH the per-stroke and relational levels ADDED beneath it:

    TOTAL[cand] = w_whole*whole_shape + w_stroke*Sum(per-stroke SC+TPS) + w_rel*Sum(precision*rel)

argmin over candidates = the verdict.

WHY THIS IS NOT THE FAILED BOLT-ON (runs 45/49/51 -- one SCALAR correction term, redundant/weak):
this adds MULTI-GRAIN GRAPH STRUCTURE where run 50 PROVED the grains carry ORTHOGONAL information
(whole-shape coherence at the top, part geometry in the middle, arrangement at the relations --
corr(r, geo)=0.093, LICENSED). Summing prediction-error across ORTHOGONAL levels reads
COMPLEMENTARY structure, not the same evidence re-added. And because the whole-shape term stays
IN as `w_whole`, the verdict STRUCTURALLY CANNOT badly underperform the GUARD: at `w_stroke=0,
w_rel=0, w_whole=1` it reduces to the whole-shape verdict BYTE-IDENTICALLY (the GUARD-reduction
invariant, gated in `tests/test_compositional_verdict_migrated.py`) -- worst case the additions
calibrate to ~0.

KEY UNIFICATION (A structural + C mechanism = ONE computation): run 50's per-relation TIGHTNESS IS
predictive-coding's PRECISION. A tight relation (identity-bearing, low within-class variance) is a
HIGH-precision prediction whose residual counts fully; a loose relation is LOW-precision, residual
discounted. So the run-50 tightness-weighting IS the precision term; `relation_residual` (=
`relational_variation.relational_distance`) is the precision-weighted arrangement prediction error.

PROTOCOL (run-26/44b lineage, MULTI-STROKE FOCUS -- relations exist AND the 80.5 lives on
multi-stroke glyphs). LEVEL WEIGHTS are SPREAD-MATCHED + BACKGROUND-FROZEN (run 44a/44b binding
rule (a): "a new term enters at MATCHED SPREAD OR NOT AT ALL") -- each added level enters at the
weight making its across-candidate spread EQUAL the whole-shape term's, measured on BACKGROUND
multi-stroke episodes, NEVER tuned against eval. The run-50 PRECISION weights are FROZEN read-only
(`results/run50_checkpoints/learn_relational.json`). BACKGROUND-SANITY STOP (commit 465d57da): the
armed multi-grain verdict must score >= GUARD-3pp on background BEFORE any eval budget is spent.
Calibrate + sanity on BACKGROUND (5 LEARN alphabets, the 4 that host >=20 multi-stroke classes);
EVAL on held-out EVALUATION alphabets (the frozen background weights tested OUT-of-sample -- the
proper powered design), first `N_EVAL_ALPHABETS` with >=20 multi-stroke classes.

GUARD (this run's own, reproduced on the multi-stroke set -- multi-stroke-restricted, may differ
from 80.5, reported exact; it is the number to BEAT): `ar.parse_marginal_pair_error` argmin, the
whole-shape verdict. Both arms score EVERY candidate on the SAME staged episode (paired). NOTE:
raw `ow.load_strokes` throughout (no 37c DropDegenerateFilter) so the decode feeding the relation
term matches run 50's OWN frozen-weight learning conditions exactly -- the GUARD is thus this run's
own consistent reproduction, paired with ARM PC, not necessarily the 80.5 headline number.

PRIMARY: paired McNemar ARM PC vs GUARD. THE QUESTION: does a verdict WITH PARTS (multi-grain
graph structure) beat the structureless whole-shape verdict? WIN = the loop-flip converts (first
ceiling crack, the concept participates natively). NULL (broken >= fixed) = adding the part+
relation levels does not help beyond whole-shape -> localizes toward fork-option-B's fuller
generative inference (the concept must PREDICT the parse, not add graded residual levels).

EXECUTION (ops law, binding): every invocation <=540s FOREGROUND, `stdbuf -oL ... | tee -a
results/omniglot_gate_run54.log`, per-alphabet checkpoints under `results/run54_checkpoints/`
(every OTHER `results/run*_checkpoints/` is READ-ONLY reference), NEVER `run_in_background`.
`.venv` python (needs `substrate_rs`). `OZMA_SEED_PERSIST_DISABLED=1` at import + a before/after
md5 seed-guard on every stage.

Stages, in dependency order:
  unit_sanity  seed-guard + `tests/test_compositional_verdict_migrated.py` +
               `tests/test_relational_variation_migrated.py` (run 50's suite, unaffected) +
               `tests/test_character_composition_migrated.py`; assert learn_relational.json present.
  calibrate    BACKGROUND multi-stroke episodes: collect per-candidate (whole, stroke, rel)
               residuals (resumable per alphabet), derive spread-matched level weights, run the
               BACKGROUND-SANITY STOP (ARM PC vs GUARD). FREEZE calibrate.json.
  eval         EVALUATION multi-stroke episodes (frozen weights, OUT-of-sample): collect raw +
               GUARD/PC preds, resumable per alphabet.
  report       background-sanity FIRST, GUARD baseline, McNemar + CIs, fixed/broken + arrangement-
               differ, per-level residual contribution, weights, precision distribution,
               segmentation stats, anomalies.

Run (from the gamma-substrate repo root):
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run54_pcverdict.py --stage <STAGE>
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

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from scipy.stats import binomtest

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run50_relational as run50
from domains import abs_read as ar
from domains import compositional_verdict as cv
from domains import omniglot_world as ow

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run54_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
RUN50_DIR = os.path.join(ROOT, "results", "run50_checkpoints")       # READ-ONLY reference.
LEARN_RELATIONAL_PATH_50 = os.path.join(RUN50_DIR, "learn_relational.json")
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS.
# ------------------------------------------------------------------------------------------- #
RUN54_SEED = gate.SEED + 12000            # this run's own seed, distinct from every prior run's.
DK = gate.DK
WAY = 20
N_BLOCKS = 1                              # one block per episode-alphabet.
N_EVAL_ALPHABETS = 8                      # first 8 eval alphabets with >=WAY multi-stroke classes
                                           # -> eval n = WAY*8 = 160 (matches run50/52's own gate0).
EX_DRAWERS_POOL = run50.EX_DRAWERS_POOL   # drawers 15-20 (run 50's own convention).
SANITY_MARGIN = 0.03                      # HARD STOP: armed_acc must be >= GUARD_acc - 3pp.
PER_CALL_BUDGET_SECONDS = 420.0           # leaves headroom under the 590s foreground timeout.

CALIB_STATE_PATH = os.path.join(CKPT_DIR, "calibrate_state.json")
CALIB_PATH = os.path.join(CKPT_DIR, "calibrate.json")
EVAL_STATE_PATH = os.path.join(CKPT_DIR, "eval_state.json")
EVAL_PATH = os.path.join(CKPT_DIR, "eval.json")


def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _json_default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serializable: {type(o)}")


def _save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_json_default)


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _md5(path):
    if not os.path.exists(path):
        return "MISSING"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def _donkey0():
    return "torch" not in sys.modules


def _wilson(k, n):
    return gate.wilson_ci(k, n)


def _argmin_pairs_term(pairs):
    return {"type": "Argmin", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


def _mcnemar(correct_a, correct_b):
    """`fixed`: a WRONG -> b RIGHT. `broken`: a RIGHT -> b WRONG."""
    fixed = sum(1 for a, b in zip(correct_a, correct_b) if (not a) and b)
    broken = sum(1 for a, b in zip(correct_a, correct_b) if a and (not b))
    n_disc = fixed + broken
    p = float(binomtest(fixed, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    return dict(fixed=fixed, broken=broken, discordant=n_disc, p=p)


# ============================================================================================= #
# STAGE: unit_sanity
# ============================================================================================= #
def stage_unit_sanity():
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    ok_all = True
    md5_before = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 (BEFORE): {md5_before}")
    print(f"  OZMA_SEED_PERSIST_DISABLED={os.environ.get('OZMA_SEED_PERSIST_DISABLED')!r}")

    for test_file in ("tests/test_compositional_verdict_migrated.py",
                      "tests/test_relational_variation_migrated.py",
                      "tests/test_character_composition_migrated.py"):
        print(f"\n  running {test_file} ...")
        proc = subprocess.run([sys.executable, "-m", "pytest", test_file, "-q"],
                              cwd=ROOT, env={**os.environ}, capture_output=True, text=True,
                              timeout=300)
        print(proc.stdout[-3500:])
        if proc.returncode != 0:
            print(proc.stderr[-3500:])
        ok = proc.returncode == 0
        print(f"      -> {'PASS' if ok else 'FAIL'}")
        ok_all &= ok

    if not os.path.exists(LEARN_RELATIONAL_PATH_50):
        print(f"\n  WALL: {LEARN_RELATIONAL_PATH_50} missing (run 50's frozen weights required).")
        ok_all = False

    md5_after = _md5(STROKE_SHAPES_SEED)
    ok_seed = md5_after == md5_before
    print(f"\n  seeds/stroke_shapes.json md5 AFTER unit_sanity: {md5_after}  UNCHANGED={ok_seed}")
    ok_all &= ok_seed
    if not ok_seed:
        raise SystemExit("HARD STOP: seed write detected during --stage unit_sanity.")

    print(f"\n{SEP}\n  UNIT SANITY: {'ALL PASS' if ok_all else 'SOME FAILED -- DO NOT PROCEED'}"
          f"\n{SEP}")
    _save_json({"ok_all": bool(ok_all), "stroke_shapes_md5_before": md5_before},
               _ckpt("unit_sanity.json"))
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    if not ok_all:
        raise SystemExit(1)
    return 0


def _require_unit_sanity():
    p = _ckpt("unit_sanity.json")
    if not os.path.exists(p):
        raise SystemExit("WALL: run --stage unit_sanity first.")
    d = _load_json(p)
    if not d.get("ok_all"):
        raise SystemExit("WALL: unit_sanity did not pass.")
    return d


def _require_weights_precision():
    return _load_json(LEARN_RELATIONAL_PATH_50)["weights"]


# ============================================================================================= #
# SHARED -- multi-stroke episode populations + one block's residual collection.
# ============================================================================================= #
def _multi_stroke_classes(alphabets, split):
    """`{alphabet: [class_dir, ...]}` -- median raw pen-stroke count (over all 20 drawers) >= 2.
    Deterministic (sorted), no RNG. Mirrors run50._multi_stroke_classes but parameterized split."""
    out = {}
    for alph in alphabets:
        chars = ow.characters(alph, split)
        qualifying = []
        for cdir in chars:
            counts = [len(ow.load_strokes(f)) for f in ow.drawings(cdir)]
            if counts and float(np.median(counts)) >= 2:
                qualifying.append(cdir)
        out[alph] = sorted(qualifying)
    return out


def _background_population():
    """The 4 LEARN background alphabets that host >=WAY multi-stroke classes (run 50's own)."""
    learn_alphs = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    multi = _multi_stroke_classes(learn_alphs, "background")
    ep_alphs = [a for a in learn_alphs if len(multi[a]) >= WAY]
    return {a: multi[a][:WAY] for a in ep_alphs}


def _eval_population():
    """The first N_EVAL_ALPHABETS EVALUATION alphabets that host >=WAY multi-stroke classes."""
    eval_alphs = ow.alphabets("evaluation")
    multi = _multi_stroke_classes(eval_alphs, "evaluation")
    ep_alphs = [a for a in eval_alphs if len(multi[a]) >= WAY][:N_EVAL_ALPHABETS]
    return {a: multi[a][:WAY] for a in ep_alphs}


def _files_by_drawer(cdir):
    return run50._files_by_drawer(cdir)


def _run_one_block(s, way_classes, files_by_drawer, rng, cache, weights_prec):
    """One block (one exemplar drawer draw + WAY queries): returns a list of per-query records
    `{true_idx, per: [{whole, stroke, rel} x WAY], n_q_strokes}`, or `None` (honest skip -- an
    alphabet lacking the exemplar drawer for some class, run 50/52's own precedent, BEFORE any
    query RNG draw so replay stays deterministic)."""
    native_s = s._inner
    scratch = srs.Substrate()
    native = scratch._inner
    ex_drawer = EX_DRAWERS_POOL[int(rng.integers(len(EX_DRAWERS_POOL)))]
    ex_files = [files_by_drawer[cdir].get(ex_drawer) for cdir in way_classes]
    if any(f is None for f in ex_files):
        return None

    node_of_cand = {}
    ex_decode = []
    ex_drawn = []
    for ci, cdir in enumerate(way_classes):
        node_of_cand[ci] = ar.stage_parse_char(scratch, ex_files[ci], is_query=False,
                                                name=str(ci), thetas=ar.DEFAULT_PARSE_THETAS)
        ex_decode.append(gate.decode_char_signature(s, ex_files[ci], cache, DK))
        ex_drawn.append(ow.load_strokes(ex_files[ci]))

    records = []
    for true_idx in range(WAY):
        q_drawer = f"{int(rng.integers(20)) + 1:02d}"
        tries = 0
        while (q_drawer == ex_drawer or
               files_by_drawer[way_classes[true_idx]].get(q_drawer) is None):
            q_drawer = f"{int(rng.integers(20)) + 1:02d}"
            tries += 1
            if tries > 40:
                break
        q_file = files_by_drawer[way_classes[true_idx]].get(q_drawer)
        if q_file is None:
            continue
        qn = ar.stage_parse_char(scratch, q_file, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
        qd = gate.decode_char_signature(s, q_file, cache, DK)
        q_drawn = ow.load_strokes(q_file)

        per = []
        for ci in range(WAY):
            whole = ar.parse_marginal_pair_error(scratch, qn, node_of_cand[ci])
            stroke = cv.per_stroke_residual(native, q_drawn, ex_drawn[ci])
            rel = cv.relation_residual(native, qd["stroke_points"], qd["composed_sig"],
                                       ex_decode[ci]["stroke_points"],
                                       ex_decode[ci]["composed_sig"], weights_prec)
            per.append(dict(whole=float(whole), stroke=float(stroke), rel=float(rel)))
        records.append(dict(true_idx=int(true_idx), per=per, n_q_strokes=int(len(q_drawn))))
    return records


def _collect_population(population, state_path, weights_prec, stage_label):
    """Drive the per-alphabet collection loop with per-alphabet checkpointing + RNG replay (run
    52's own resume-by-replay discipline). Returns the completed `state` or None if PARTIAL."""
    ep_alphs = sorted(population)
    print(f"  episode-alphabets (>= {WAY} multi-stroke classes): {ep_alphs}")
    if not ep_alphs:
        raise SystemExit("WALL: no episode-alphabet qualifies.")

    state = _load_json(state_path) if os.path.exists(state_path) else dict(alph_idx=0, records=[])
    s = run50._load_codebook_substrate()
    cache = {}
    rng = np.random.default_rng(RUN54_SEED)
    # Replay every fully-processed alphabet's own RNG draws (re-run + discard) so a resumed call
    # continues the SAME deterministic stream (run 52's discipline; a no-op would de-sync).
    for i in range(state["alph_idx"]):
        way_classes = population[ep_alphs[i]]
        fbd = {c: _files_by_drawer(c) for c in way_classes}
        for _b in range(N_BLOCKS):
            _run_one_block(s, way_classes, fbd, rng, cache, weights_prec)

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["alph_idx"] < len(ep_alphs) and time.time() < hard_deadline:
        alph = ep_alphs[state["alph_idx"]]
        way_classes = population[alph]
        fbd = {c: _files_by_drawer(c) for c in way_classes}
        a0 = time.time()
        for _b in range(N_BLOCKS):
            recs = _run_one_block(s, way_classes, fbd, rng, cache, weights_prec)
            if recs:
                state["records"].extend(recs)
        state["alph_idx"] += 1
        _save_json(state, state_path)
        print(f"  [{stage_label}] alphabet {state['alph_idx']}/{len(ep_alphs)} ({alph!r}) done -- "
              f"{len(state['records'])} episodes, {time.time()-a0:.1f}s this alphabet, "
              f"{time.time()-t0:.1f}s this call", flush=True)

    if state["alph_idx"] < len(ep_alphs):
        print(f"\n  PARTIAL [{stage_label}]: {state['alph_idx']}/{len(ep_alphs)} alphabets done -- "
              f"re-invoke to continue.")
        return None
    return state


# ============================================================================================= #
# Residual reductions -- pure statistics over already-computed per-candidate values.
# ============================================================================================= #
def _episode_spreads(records):
    """Per level, the mean across-candidate std over episodes (44b's own spread estimator)."""
    out = {}
    for lvl in ("whole", "stroke", "rel"):
        per_ep = [float(np.std([c[lvl] for c in r["per"]])) for r in records]
        out[lvl] = float(np.mean(per_ep)) if per_ep else 0.0
    return out


def _preds(records, weights_level):
    """GUARD (whole-only) and ARM PC (multi-grain) predictions per episode via held Argmin."""
    native = srs.Substrate()._inner
    wl = weights_level
    guard, pc = [], []
    for r in records:
        guard.append(cv.verdict_pred(native, r["per"], w_whole=1.0, w_stroke=0.0, w_rel=0.0))
        pc.append(cv.verdict_pred(native, r["per"], w_whole=wl["w_whole"],
                                  w_stroke=wl["w_stroke"], w_rel=wl["w_rel"]))
    return guard, pc


# ============================================================================================= #
# STAGE: calibrate -- BACKGROUND collection, spread-matched weights, BACKGROUND-SANITY STOP.
# ============================================================================================= #
def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (BACKGROUND multi-stroke: spreads + weights + SANITY STOP)"
          f"\n{SEP}")
    if os.path.exists(CALIB_PATH):
        frozen = _load_json(CALIB_PATH)
        print(f"  ALREADY FROZEN: {CALIB_PATH}")
        _print_calibrate(frozen)
        return 0
    _require_unit_sanity()
    weights_prec = _require_weights_precision()
    print(f"  READ (read-only) run 50's frozen PRECISION weights: {weights_prec}")
    md5_before = _md5(STROKE_SHAPES_SEED)

    state = _collect_population(_background_population(), CALIB_STATE_PATH, weights_prec, "calib")
    if state is None:
        return 0

    records = state["records"]
    n = len(records)
    spreads = _episode_spreads(records)
    weights_level = cv.spread_match_weights(spreads["whole"], spreads["stroke"], spreads["rel"])
    print(f"\n  background spreads (mean across-candidate std): {spreads}")
    print(f"  spread-matched level weights: {weights_level}")

    guard, pc = _preds(records, weights_level)
    trues = [r["true_idx"] for r in records]
    k_guard = sum(1 for g, t in zip(guard, trues) if g == t)
    k_pc = sum(1 for p, t in zip(pc, trues) if p == t)
    acc_guard, acc_pc = k_guard / n, k_pc / n
    passed = acc_pc >= acc_guard - SANITY_MARGIN

    frozen = dict(n=n, spreads=spreads, weights_level=weights_level,
                  weights_precision=weights_prec, k_guard=k_guard, k_pc=k_pc,
                  acc_guard=acc_guard, acc_pc=acc_pc, sanity_margin=SANITY_MARGIN,
                  passed=bool(passed), ep_alphs=sorted(_background_population()))
    _save_json(frozen, CALIB_PATH)
    _print_calibrate(frozen)

    md5_after = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 AFTER calibrate: {md5_after}  "
          f"UNCHANGED={md5_after == md5_before}")
    if md5_after != md5_before:
        raise SystemExit("HARD STOP: seed write detected during --stage calibrate.")
    return 0


def _print_calibrate(frozen):
    print(f"\n  ---- BACKGROUND-SANITY GATE (n={frozen['n']}, {frozen['ep_alphs']}) ----")
    wl = frozen["weights_level"]
    print(f"    spread-matched weights: w_whole={wl['w_whole']:.4f} w_stroke={wl['w_stroke']:.4f} "
          f"w_rel={wl['w_rel']:.4f}")
    print(f"    GUARD (whole-shape only):     acc={100*frozen['acc_guard']:.1f}%  "
          f"k={frozen['k_guard']}/{frozen['n']}")
    print(f"    ARM PC (multi-grain verdict): acc={100*frozen['acc_pc']:.1f}%  "
          f"k={frozen['k_pc']}/{frozen['n']}")
    delta = frozen["acc_pc"] - frozen["acc_guard"]
    print(f"    delta = {100*delta:+.1f}pp   hard-stop bound = GUARD - "
          f"{100*frozen['sanity_margin']:.0f}pp")
    print(f"    VERDICT: {'PASS -- proceed to --stage eval' if frozen['passed'] else 'STOP -- do NOT spend any eval budget'}")


def _require_calibrate():
    if not os.path.exists(CALIB_PATH):
        print("  WALL: run --stage calibrate to completion first.")
        sys.exit(1)
    return _load_json(CALIB_PATH)


# ============================================================================================= #
# STAGE: eval -- EVALUATION multi-stroke episodes, frozen weights, OUT-of-sample.
# ============================================================================================= #
def stage_eval():
    print(f"\n{SEP}\n  STAGE: eval (EVALUATION multi-stroke, frozen weights)\n{SEP}")
    calib = _require_calibrate()
    if not calib["passed"]:
        print("  WALL: calibrate SANITY STOPPED -- NO eval budget may be spent. Report and stop.")
        return 1
    weights_prec = calib["weights_precision"]
    weights_level = calib["weights_level"]
    print(f"  frozen level weights: {weights_level}")
    md5_before = _md5(STROKE_SHAPES_SEED)

    state = _collect_population(_eval_population(), EVAL_STATE_PATH, weights_prec, "eval")
    if state is None:
        return 0

    records = state["records"]
    n = len(records)
    guard, pc = _preds(records, weights_level)
    trues = [r["true_idx"] for r in records]
    guard_correct = [g == t for g, t in zip(guard, trues)]
    pc_correct = [p == t for p, t in zip(pc, trues)]
    k_guard, k_pc = sum(guard_correct), sum(pc_correct)
    out = dict(n=n, guard_pred=guard, pc_pred=pc, trues=trues,
               guard_correct=[bool(x) for x in guard_correct],
               pc_correct=[bool(x) for x in pc_correct],
               k_guard=k_guard, k_pc=k_pc, records=records,
               weights_level=weights_level, ep_alphs=sorted(_eval_population()), done=True)
    _save_json(out, EVAL_PATH)
    print(f"\n  EVAL COMPLETE: n={n}  GUARD acc={100*k_guard/n:.1f}% k={k_guard}  "
          f"ARM PC acc={100*k_pc/n:.1f}% k={k_pc}")

    md5_after = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 AFTER eval: {md5_after}  "
          f"UNCHANGED={md5_after == md5_before}")
    if md5_after != md5_before:
        raise SystemExit("HARD STOP: seed write detected during --stage eval.")
    return 0


def _require_eval():
    if not os.path.exists(EVAL_PATH) or not _load_json(EVAL_PATH).get("done"):
        print("  WALL: run --stage eval to completion first.")
        sys.exit(1)
    return _load_json(EVAL_PATH)


# ============================================================================================= #
# STAGE: report
# ============================================================================================= #
def stage_report():
    print(f"\n{SEP}\n  RUN 54 -- COMPOSITIONAL PREDICTIVE-CODING VERDICT -- FINAL REPORT\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5: {md5_now}")

    calib = _require_calibrate()
    lr = _load_json(LEARN_RELATIONAL_PATH_50)
    split = lr["tight_loose_split"]

    print(f"\n{'='*33}  BACKGROUND-SANITY (decides everything)  {'='*33}")
    _print_calibrate(calib)

    print(f"\n  ---- TIGHT/LOOSE PRECISION DISTRIBUTION (run 50 frozen, READ-ONLY) ----")
    for slot in split["ordered_tightest_first"]:
        tag = "TIGHT" if slot in split["tight"] else "LOOSE"
        print(f"    {slot:<9} weight={calib['weights_precision'][slot]:7.4f}  "
              f"variance={split['variances'][slot]:8.4f}  [{tag}]")

    if not calib["passed"]:
        print(f"\n  {'='*28}  SANITY STOPPED -- NO EVAL WAS RUN  {'='*28}")
        print(f"  ARM PC background accuracy {100*calib['acc_pc']:.1f}% fell more than "
              f"{100*calib['sanity_margin']:.0f}pp below GUARD {100*calib['acc_guard']:.1f}% -- "
              f"the multi-grain verdict harms in-sample before any eval spend. This localizes "
              f"toward fork-option-B's fuller generative inference (the concept must PREDICT the "
              f"parse, not add graded residual levels).")
        return 0

    ev = _require_eval()
    records = ev["records"]
    n = ev["n"]
    guard_correct = ev["guard_correct"]
    pc_correct = ev["pc_correct"]
    guard_pred = ev["guard_pred"]
    trues = ev["trues"]
    wl = ev["weights_level"]
    k_guard, k_pc = ev["k_guard"], ev["k_pc"]
    ci_guard = _wilson(k_guard, n)
    ci_pc = _wilson(k_pc, n)

    print(f"\n  ---- EVAL (n={n}, OUT-of-sample eval alphabets {ev['ep_alphs']}) ----")
    print(f"    GUARD (whole-shape SC+TPS): acc={100*k_guard/n:.1f}%  "
          f"[{100*ci_guard[0]:.1f}%,{100*ci_guard[1]:.1f}%]  k={k_guard}/{n}  (the number to BEAT)")
    print(f"    ARM PC (multi-grain):       acc={100*k_pc/n:.1f}%  "
          f"[{100*ci_pc[0]:.1f}%,{100*ci_pc[1]:.1f}%]  k={k_pc}/{n}")
    print(f"    CI-separated: {gate._ci_separated(tuple(ci_pc), tuple(ci_guard))}")

    mc = _mcnemar(guard_correct, pc_correct)
    print(f"\n  ---- McNEMAR (ARM PC vs GUARD, n={n}) ----")
    print(f"    fixed={mc['fixed']}  broken={mc['broken']}  discordant={mc['discordant']}  "
          f"p={mc['p']:.4g}")

    # --- fixed/broken + arrangement-differ check: for fixed vs broken episodes, the per-level
    #     residual gap between the TRUE class and the GUARD-picked class (which grain separated
    #     them?). A positive gap = the true class is CHEAPER on that level than GUARD's pick.
    fixed_idx = [i for i in range(n) if (not guard_correct[i]) and pc_correct[i]]
    broken_idx = [i for i in range(n) if guard_correct[i] and (not pc_correct[i])]

    def _level_gaps(idxs):
        acc = {"whole": [], "stroke": [], "rel": []}
        for i in idxs:
            gp = guard_pred[i]
            t = trues[i]
            if gp < 0 or gp == t:
                continue
            per = records[i]["per"]
            for lvl in acc:
                acc[lvl].append(per[gp][lvl] - per[t][lvl])   # >0 => true cheaper on this level.
        return {lvl: (float(np.mean(v)) if v else float("nan")) for lvl, v in acc.items()}

    print(f"\n  ---- FIXED vs BROKEN structure (arrangement-differ check) ----")
    print(f"    fixed episodes (GUARD wrong -> PC right): n={len(fixed_idx)}")
    fg = _level_gaps(fixed_idx)
    print(f"      mean (GUARD-pick minus TRUE) residual gap by level "
          f"[>0 = true is cheaper, the grain that RESCUED it]:")
    print(f"        whole={fg['whole']:+.4f}  stroke={fg['stroke']:+.4f}  rel={fg['rel']:+.4f}")
    print(f"    broken episodes (GUARD right -> PC wrong): n={len(broken_idx)}")
    bg = _level_gaps(broken_idx)
    print(f"        whole={bg['whole']:+.4f}  stroke={bg['stroke']:+.4f}  rel={bg['rel']:+.4f}")

    # --- per-level residual contribution: the mean WEIGHTED across-candidate spread on eval
    #     (which grain does work in the sum), and which added grain flipped the winner.
    ev_spreads = _episode_spreads(records)
    contrib = {"whole": wl["w_whole"] * ev_spreads["whole"],
               "stroke": wl["w_stroke"] * ev_spreads["stroke"],
               "rel": wl["w_rel"] * ev_spreads["rel"]}
    print(f"\n  ---- PER-LEVEL CONTRIBUTION (weight x eval across-candidate spread) ----")
    for lvl in ("whole", "stroke", "rel"):
        print(f"    {lvl:<7} spread={ev_spreads[lvl]:.4f}  weight={wl['w_'+lvl]:.4f}  "
              f"contribution={contrib[lvl]:.4f}")

    # which grain is responsible where PC != GUARD: recompute PC with each added grain alone.
    native = srs.Substrate()._inner
    stroke_only, rel_only = [], []
    for r in records:
        stroke_only.append(cv.verdict_pred(native, r["per"], w_whole=wl["w_whole"],
                                           w_stroke=wl["w_stroke"], w_rel=0.0))
        rel_only.append(cv.verdict_pred(native, r["per"], w_whole=wl["w_whole"],
                                        w_stroke=0.0, w_rel=wl["w_rel"]))
    stroke_flips = sum(1 for i in range(n) if stroke_only[i] != guard_pred[i])
    rel_flips = sum(1 for i in range(n) if rel_only[i] != guard_pred[i])
    print(f"    episodes where the STROKE grain alone changes the whole-shape pick: {stroke_flips}")
    print(f"    episodes where the REL grain alone changes the whole-shape pick:    {rel_flips}")

    seg = [r["n_q_strokes"] for r in records]
    print(f"\n  ---- SEGMENTATION (pen-up BREAK, query glyphs) ----")
    print(f"    strokes/glyph: mean={np.mean(seg):.2f}  min={min(seg)}  max={max(seg)}  "
          f"(all >=2 by the multi-stroke restriction)")

    out = dict(n=n, acc_guard=dict(acc=k_guard / n, ci=list(ci_guard), k=k_guard),
               acc_pc=dict(acc=k_pc / n, ci=list(ci_pc), k=k_pc), mcnemar=mc,
               weights_level=wl, weights_precision=calib["weights_precision"],
               fixed_level_gaps=fg, broken_level_gaps=bg, contribution=contrib,
               stroke_flips=stroke_flips, rel_flips=rel_flips,
               seg_mean=float(np.mean(seg)))
    _save_json(out, _ckpt("report.json"))
    print(f"\n  report.json written.")

    print(f"\n  {'='*24}  DOES A VERDICT WITH PARTS BEAT WHOLE-SHAPE?  {'='*24}")
    if mc["discordant"] and mc["fixed"] > mc["broken"] and \
            gate._ci_separated(tuple(ci_pc), tuple(ci_guard)):
        print(f"  WIN: the multi-grain predictive-coding verdict CONVERTS -- the loop-flip landed "
              f"as graph structure, the concept participates natively, first crack in the whole-"
              f"shape ceiling. Adding the orthogonal part+relation grains beats the structureless "
              f"whole-shape verdict, CI-separated.")
    elif mc["discordant"] and mc["fixed"] > mc["broken"]:
        print(f"  WEAK POSITIVE: fixed > broken but not CI-separated -- suggestive, not "
              f"conclusive; report as a lead validating the multi-grain DIRECTION.")
    elif mc["discordant"] and mc["broken"] >= mc["fixed"]:
        print(f"  NULL (STOP CONDITION): broken >= fixed -- adding the part+relation grains does "
              f"not beat whole-shape. The grains are orthogonal (run 50) but summing graded "
              f"prediction-error across them does not convert to accuracy: this localizes toward "
              f"fork-option-B's fuller GENERATIVE inference -- the concept must PREDICT the parse "
              f"itself, not contribute a graded residual level. Forward progress: it narrows what "
              f"'participate in the verdict' must mean (structure alone is not enough; the concept "
              f"must be generative).")
    else:
        print(f"  NULL: no discordant pairs / no effect either direction.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  seeds/stroke_shapes.json md5 (post-run): {_md5(STROKE_SHAPES_SEED)}")
    return 0


STAGES = {"unit_sanity": stage_unit_sanity, "calibrate": stage_calibrate, "eval": stage_eval,
          "report": stage_report}


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
