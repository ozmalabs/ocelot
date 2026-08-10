"""OMNIGLOT RUN 54b -- THE RELIABILITY-WEIGHTED MULTI-GRAIN VERDICT (run 54's principled
recalibration; 34a->34b precedent: background-derived, NOT eval-tuned).

RUN 54 built the right ARCHITECTURE (a graph HOLDS a character at MULTIPLE GRAINS AT ONCE: whole-
shape SC+TPS residual as the top-level term, per-stroke geometry + precision-weighted relations
added beneath) but tested it with a KNOWN-WRONG level-weight CALIBRATION. Run 54's level weights
were SPREAD-MATCHED (each added grain entered at the weight equalizing its across-candidate
variance to whole-shape's). Run 44b ALREADY PROVED that is the wrong rule: spread-matching
equalizes VARIANCE, not DISCRIMINATIVE POWER. Spread-matching two WEAK grains (per-stroke ~38%
standalone, relation ~30%) each to the strong whole-shape's variance (85%) made 2/3 of the
decision variance come from weak grains -> dilution -> -20pp at the background-sanity gate.

THE FIX (this run's ONLY change from run 54): the LEVEL-WEIGHT CALIBRATION. Reuse
`domains/compositional_verdict.py`'s Term builders + the GUARD-reduction invariant VERBATIM; swap
`spread_match_weights` for `reliability_weights`. Each grain is weighted by its DISCRIMINATIVE
RELIABILITY -- the PRECISION principle applied to LEVELS (the same unification run 50 used WITHIN
the relation grain: reliability = precision). Pre-registered reliability measure:

    reliability(grain) = clip((standalone_bg_acc - chance) / (1 - chance), 0, +inf)

(chance-corrected standalone background accuracy; 1.0 = perfect, 0.0 = no better than chance). The
strong whole-shape grain (85% -> reliability ~0.84) is the reference (w_whole=1); each weaker grain
enters at its spread-match scale TIMES its reliability relative to whole-shape's:

    w_grain = (reliability_grain / reliability_whole) * (spread_whole / spread_grain)

so whole-shape DOMINATES and weak grains enter proportional to their small reliability. Frozen from
BACKGROUND (the 5 LEARN alphabets that host >=WAY multi-stroke classes) BEFORE eval.

BACKGROUND RESIDUAL SOURCE: the per-candidate (whole, stroke, rel) residual triples are the run 54
frozen background records (`results/run54_checkpoints/calibrate_state.json`, READ-ONLY). Those
triples are produced by the UNCHANGED `compositional_verdict.per_stroke_residual` /
`relation_residual` Term reads over the SAME background population + SAME RUN54 seed, so they are
byte-identical to what this run would re-collect -- reusing them read-only makes run 54b's ONLY
difference from run 54 the LEVEL WEIGHTS (the cleanest possible paired recalibration), and
reproduces run 54's 85% whole-shape background exactly. (If that file is absent this run
re-collects the background itself into its OWN checkpoints; the eval stage always collects fresh.)

PRE-REGISTERED PREDICTION (the discriminating outcomes):
  (i)  reliability-weighting REDUCES the verdict toward the whole-shape GUARD (whole dominant, weak
       grains near-0, background ~= GUARD, and if eval ran McNemar ~0/0) -> STATIC weighting
       confirmed insufficient: the orthogonal relational signal (run 50) is CONDITIONAL (helps only
       geo-wrong cases) and NO static grain weight can exploit it -> this LICENSES option B (the
       concept must PREDICT with per-instance DYNAMIC precision, not a static grain weight).
  (ii) reliability-weighting ADDS (background passes AND eval McNemar fixed>broken) -> static
       multi-grain WITH correct weighting CONVERTS: the first ceiling crack, the graph-holds-all-
       levels architecture works.

STOP: broken>=fixed at eval, or background-sanity fail (armed < GUARD - 3pp). Report background-
sanity FIRST (does reliability-weighting recover GUARD-level background, vs run 54's -20pp harm?).

EXECUTION (ops law, binding): every invocation <=540s FOREGROUND, `stdbuf -oL ... | tee -a
results/omniglot_gate_run54b.log`, per-stage checkpoints under `results/run54b_checkpoints/`
(run54_checkpoints + run50_checkpoints are READ-ONLY reference; parallel-session files untouched).
`.venv` python (needs `substrate_rs`). `OZMA_SEED_PERSIST_DISABLED=1` at import + a before/after
md5 seed-guard on every stage.

Stages:
  unit_sanity  seed-guard + `tests/test_compositional_verdict_migrated.py` (run 54's 9) +
               `tests/test_compositional_verdict_run54b.py` (this run's reliability unit gate) +
               `tests/test_relational_variation_migrated.py`; assert run 50 frozen weights present.
  calibrate    SOURCE background residuals (run 54 frozen, read-only), derive per-grain standalone
               accuracies (held Argmin) + spreads, derive reliability weights, run the BACKGROUND-
               SANITY STOP (ARM R vs GUARD). FREEZE calibrate.json.
  eval         (only if sanity passed) EVALUATION multi-stroke episodes, frozen weights, fresh.
  report       background-sanity FIRST, weights + reliabilities, (if eval ran) McNemar + CIs +
               per-grain contribution, the sep-ratio robustness variant, which outcome (i/ii).

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run54b_reliability.py --stage <STAGE>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

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
CKPT_DIR = os.path.join(ROOT, "results", "run54b_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
RUN54_DIR = os.path.join(ROOT, "results", "run54_checkpoints")      # READ-ONLY reference.
RUN50_DIR = os.path.join(ROOT, "results", "run50_checkpoints")      # READ-ONLY reference.
RUN54_CALIB_STATE = os.path.join(RUN54_DIR, "calibrate_state.json")  # background residual SOURCE.
LEARN_RELATIONAL_PATH_50 = os.path.join(RUN50_DIR, "learn_relational.json")
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

# PRE-REGISTERED CONSTANTS.
RUN54B_SEED = gate.SEED + 12000           # SAME stream as run 54 (so the background source matches).
DK = gate.DK
WAY = 20
CHANCE = 1.0 / WAY
N_BLOCKS = 1
N_EVAL_ALPHABETS = 8
EX_DRAWERS_POOL = run50.EX_DRAWERS_POOL
SANITY_MARGIN = 0.03                       # HARD STOP: armed_acc must be >= GUARD_acc - 3pp.
PER_CALL_BUDGET_SECONDS = 420.0

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
                      "tests/test_compositional_verdict_run54b.py",
                      "tests/test_relational_variation_migrated.py"):
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
# SHARED -- multi-stroke populations + one block's residual collection (verbatim run 54).
# ============================================================================================= #
def _multi_stroke_classes(alphabets, split):
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
    learn_alphs = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    multi = _multi_stroke_classes(learn_alphs, "background")
    ep_alphs = [a for a in learn_alphs if len(multi[a]) >= WAY]
    return {a: multi[a][:WAY] for a in ep_alphs}


def _eval_population():
    eval_alphs = ow.alphabets("evaluation")
    multi = _multi_stroke_classes(eval_alphs, "evaluation")
    ep_alphs = [a for a in eval_alphs if len(multi[a]) >= WAY][:N_EVAL_ALPHABETS]
    return {a: multi[a][:WAY] for a in ep_alphs}


def _files_by_drawer(cdir):
    return run50._files_by_drawer(cdir)


def _run_one_block(s, way_classes, files_by_drawer, rng, cache, weights_prec):
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
    ep_alphs = sorted(population)
    print(f"  episode-alphabets (>= {WAY} multi-stroke classes): {ep_alphs}")
    if not ep_alphs:
        raise SystemExit("WALL: no episode-alphabet qualifies.")

    state = _load_json(state_path) if os.path.exists(state_path) else dict(alph_idx=0, records=[])
    s = run50._load_codebook_substrate()
    cache = {}
    rng = np.random.default_rng(RUN54B_SEED)
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
    out = {}
    for lvl in ("whole", "stroke", "rel"):
        per_ep = [float(np.std([c[lvl] for c in r["per"]])) for r in records]
        out[lvl] = float(np.mean(per_ep)) if per_ep else 0.0
    return out


def _standalone_accuracies(records):
    """Each grain's STANDALONE background accuracy -- its OWN single-grain argmin, via the held
    `verdict_pred` (w on that grain only). No Python argmin; the ranking is the held Argmin."""
    native = srs.Substrate()._inner
    trues = [r["true_idx"] for r in records]
    n = len(records)
    out = {}
    for lvl, w in (("whole", (1.0, 0.0, 0.0)), ("stroke", (0.0, 1.0, 0.0)),
                   ("rel", (0.0, 0.0, 1.0))):
        preds = [cv.verdict_pred(native, r["per"], w_whole=w[0], w_stroke=w[1], w_rel=w[2])
                 for r in records]
        out[lvl] = sum(1 for p, t in zip(preds, trues) if p == t) / n if n else 0.0
    return out


def _preds(records, weights_level):
    native = srs.Substrate()._inner
    wl = weights_level
    guard, arm = [], []
    for r in records:
        guard.append(cv.verdict_pred(native, r["per"], w_whole=1.0, w_stroke=0.0, w_rel=0.0))
        arm.append(cv.verdict_pred(native, r["per"], w_whole=wl["w_whole"],
                                   w_stroke=wl["w_stroke"], w_rel=wl["w_rel"]))
    return guard, arm


def _sep_ratio_reliability(records, spreads):
    """ROBUSTNESS variant (reported, NOT the gate): reliability = clip(false/true separation - 1,
    0, +inf) instead of chance-corrected accuracy. Shows the outcome is invariant to the exact
    reliability formalization. Pure statistics; the ranking stays the held Argmin in `_preds`."""
    sep = {}
    for lvl in ("whole", "stroke", "rel"):
        ts = [r["per"][r["true_idx"]][lvl] for r in records]
        fs = [float(np.mean([c[lvl] for i, c in enumerate(r["per"]) if i != r["true_idx"]]))
              for r in records]
        mt = float(np.mean(ts))
        sep[lvl] = (float(np.mean(fs)) / mt) if mt > 0 else 0.0
    rel = {lvl: float(np.clip(sep[lvl] - 1.0, 0.0, None)) for lvl in sep}
    wl = {"w_whole": 1.0}
    for lvl in ("stroke", "rel"):
        if rel["whole"] > 0 and rel[lvl] > 0 and spreads[lvl] > 0 and spreads["whole"] > 0:
            wl["w_" + lvl] = (rel[lvl] / rel["whole"]) * (spreads["whole"] / spreads[lvl])
        else:
            wl["w_" + lvl] = 0.0
    return dict(sep_ratio=sep, reliability=rel, weights_level=wl)


# ============================================================================================= #
# STAGE: calibrate -- background residuals (run 54 frozen source) -> reliability weights + SANITY.
# ============================================================================================= #
def _source_background_records():
    """Prefer run 54's frozen background residual records (READ-ONLY, byte-identical to a fresh
    collect under the SAME seed + population + unchanged Term reads). Fall back to a fresh collect
    into this run's OWN checkpoints if that source is absent."""
    if os.path.exists(RUN54_CALIB_STATE):
        st = _load_json(RUN54_CALIB_STATE)
        recs = st.get("records", [])
        if recs:
            print(f"  background residual SOURCE: run 54 frozen {RUN54_CALIB_STATE} "
                  f"(READ-ONLY, {len(recs)} records) -- identical Term reads + RUN54 seed, so run "
                  f"54b's ONLY change from run 54 is the LEVEL WEIGHTS.")
            return recs, f"run54:{os.path.basename(RUN54_CALIB_STATE)}"
    print("  run 54 frozen background source ABSENT -- collecting fresh into this run's own state.")
    weights_prec = _require_weights_precision()
    state = _collect_population(_background_population(), CALIB_STATE_PATH, weights_prec, "calib")
    if state is None:
        return None, "collecting"
    return state["records"], f"run54b:{os.path.basename(CALIB_STATE_PATH)}"


def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (reliability weights + BACKGROUND-SANITY STOP)\n{SEP}")
    if os.path.exists(CALIB_PATH):
        frozen = _load_json(CALIB_PATH)
        print(f"  ALREADY FROZEN: {CALIB_PATH}")
        _print_calibrate(frozen)
        return 0
    _require_unit_sanity()
    weights_prec = _require_weights_precision()
    print(f"  READ (read-only) run 50's frozen PRECISION weights: {weights_prec}")
    md5_before = _md5(STROKE_SHAPES_SEED)

    records, source = _source_background_records()
    if records is None:
        return 0                                   # partial fresh collection -- re-invoke.

    n = len(records)
    spreads = _episode_spreads(records)
    accs = _standalone_accuracies(records)
    weights_level = cv.reliability_weights(accs["whole"], accs["stroke"], accs["rel"],
                                           spreads["whole"], spreads["stroke"], spreads["rel"],
                                           chance=CHANCE)
    print(f"\n  background spreads (mean across-candidate std): {spreads}")
    print(f"  standalone per-grain background accuracies: "
          f"{ {k: round(v, 4) for k, v in accs.items()} }")
    print(f"  reliability-weighted level weights: {weights_level}")

    guard, arm = _preds(records, weights_level)
    trues = [r["true_idx"] for r in records]
    k_guard = sum(1 for g, t in zip(guard, trues) if g == t)
    k_arm = sum(1 for p, t in zip(arm, trues) if p == t)
    acc_guard, acc_arm = k_guard / n, k_arm / n
    passed = acc_arm >= acc_guard - SANITY_MARGIN

    sep_variant = _sep_ratio_reliability(records, spreads)
    _, arm_sep = _preds(records, sep_variant["weights_level"])
    k_arm_sep = sum(1 for p, t in zip(arm_sep, trues) if p == t)
    sep_variant["acc_arm"] = k_arm_sep / n
    sep_variant["k_arm"] = k_arm_sep

    frozen = dict(n=n, source=source, spreads=spreads, standalone_acc=accs,
                  weights_level=weights_level, weights_precision=weights_prec,
                  k_guard=k_guard, k_arm=k_arm, acc_guard=acc_guard, acc_arm=acc_arm,
                  sanity_margin=SANITY_MARGIN, passed=bool(passed),
                  sep_variant=sep_variant, ep_alphs=sorted(_background_population()))
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
    print(f"    background residual source: {frozen.get('source')}")
    acc = frozen["standalone_acc"]
    print(f"    standalone per-grain bg accuracy: whole={100*acc['whole']:.1f}%  "
          f"stroke={100*acc['stroke']:.1f}%  rel={100*acc['rel']:.1f}%")
    rel = frozen["weights_level"]["reliability"]
    print(f"    chance-corrected reliability:     whole={rel['whole']:.4f}  "
          f"stroke={rel['stroke']:.4f}  rel={rel['rel']:.4f}  (chance={CHANCE:.3f})")
    wl = frozen["weights_level"]
    print(f"    reliability weights: w_whole={wl['w_whole']:.4f} w_stroke={wl['w_stroke']:.4f} "
          f"w_rel={wl['w_rel']:.4f}   (whole-shape dominant? "
          f"{wl['w_whole'] >= wl['w_stroke'] and wl['w_whole'] >= wl['w_rel']})")
    print(f"    GUARD (whole-shape only):        acc={100*frozen['acc_guard']:.1f}%  "
          f"k={frozen['k_guard']}/{frozen['n']}")
    print(f"    ARM R (reliability multi-grain): acc={100*frozen['acc_arm']:.1f}%  "
          f"k={frozen['k_arm']}/{frozen['n']}")
    delta = frozen["acc_arm"] - frozen["acc_guard"]
    print(f"    delta = {100*delta:+.1f}pp   hard-stop bound = GUARD - "
          f"{100*frozen['sanity_margin']:.0f}pp")
    sv = frozen.get("sep_variant", {})
    if sv:
        svw = sv["weights_level"]
        print(f"    [ROBUSTNESS] sep-ratio reliability weights: w_stroke={svw['w_stroke']:.4f} "
              f"w_rel={svw['w_rel']:.4f} -> ARM acc={100*sv['acc_arm']:.1f}% "
              f"(delta {100*(sv['acc_arm']-frozen['acc_guard']):+.1f}pp)")
    print(f"    VERDICT: {'PASS -- proceed to --stage eval' if frozen['passed'] else 'STOP -- do NOT spend any eval budget'}")
    # Contrast to run 54's spread-matched -20pp harm, for the report headline.
    print(f"    (run 54 spread-matched ARM PC was 65.0% = -20.0pp; reliability-weighting recovers "
          f"{100*delta:+.1f}pp relative to GUARD)")


def _require_calibrate():
    if not os.path.exists(CALIB_PATH):
        print("  WALL: run --stage calibrate to completion first.")
        sys.exit(1)
    return _load_json(CALIB_PATH)


# ============================================================================================= #
# STAGE: eval -- EVALUATION multi-stroke episodes, frozen weights, OUT-of-sample (only if passed).
# ============================================================================================= #
def stage_eval():
    print(f"\n{SEP}\n  STAGE: eval (EVALUATION multi-stroke, frozen reliability weights)\n{SEP}")
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
    guard, arm = _preds(records, weights_level)
    trues = [r["true_idx"] for r in records]
    guard_correct = [g == t for g, t in zip(guard, trues)]
    arm_correct = [p == t for p, t in zip(arm, trues)]
    k_guard, k_arm = sum(guard_correct), sum(arm_correct)
    out = dict(n=n, guard_pred=guard, arm_pred=arm, trues=trues,
               guard_correct=[bool(x) for x in guard_correct],
               arm_correct=[bool(x) for x in arm_correct],
               k_guard=k_guard, k_arm=k_arm, records=records,
               weights_level=weights_level, ep_alphs=sorted(_eval_population()), done=True)
    _save_json(out, EVAL_PATH)
    print(f"\n  EVAL COMPLETE: n={n}  GUARD acc={100*k_guard/n:.1f}% k={k_guard}  "
          f"ARM R acc={100*k_arm/n:.1f}% k={k_arm}")

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
    print(f"\n{SEP}\n  RUN 54b -- RELIABILITY-WEIGHTED MULTI-GRAIN VERDICT -- FINAL REPORT\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5: {md5_now}")

    calib = _require_calibrate()

    print(f"\n{'='*30}  BACKGROUND-SANITY (decides everything)  {'='*30}")
    _print_calibrate(calib)

    if not calib["passed"]:
        print(f"\n  {'='*24}  SANITY STOPPED -- NO EVAL WAS RUN  {'='*24}")
        delta = calib["acc_arm"] - calib["acc_guard"]
        print(f"  Reliability-weighting recovered the level weights to whole-shape-DOMINANT "
              f"(w_whole=1.0 > w_stroke={calib['weights_level']['w_stroke']:.3f}, "
              f"w_rel={calib['weights_level']['w_rel']:.3f}) and cut run 54's -20pp harm to "
              f"{100*delta:+.1f}pp -- but ARM R still fell below GUARD by more than "
              f"{100*calib['sanity_margin']:.0f}pp. STATIC multi-grain does not recover GUARD even "
              f"with correctly-calibrated (reliability) weights: a positively-informative-but-"
              f"weaker grain still DILUTES a static sum (the run 44b/49 law), and the run-50 "
              f"orthogonal relational signal is CONDITIONAL (helps only geo-wrong cases) so no "
              f"static grain weight can exploit it. OUTCOME (i): static weighting confirmed "
              f"insufficient -> LICENSES option B (the concept must PREDICT with per-instance "
              f"DYNAMIC precision, not a static grain weight).")
        print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
        print(f"  seeds/stroke_shapes.json md5 (post-run): {_md5(STROKE_SHAPES_SEED)}")
        return 0

    ev = _require_eval()
    records = ev["records"]
    n = ev["n"]
    guard_correct = ev["guard_correct"]
    arm_correct = ev["arm_correct"]
    guard_pred = ev["guard_pred"]
    trues = ev["trues"]
    wl = ev["weights_level"]
    k_guard, k_arm = ev["k_guard"], ev["k_arm"]
    ci_guard = _wilson(k_guard, n)
    ci_arm = _wilson(k_arm, n)

    print(f"\n  ---- EVAL (n={n}, OUT-of-sample eval alphabets {ev['ep_alphs']}) ----")
    print(f"    GUARD (whole-shape SC+TPS): acc={100*k_guard/n:.1f}%  "
          f"[{100*ci_guard[0]:.1f}%,{100*ci_guard[1]:.1f}%]  k={k_guard}/{n}  (the number to BEAT)")
    print(f"    ARM R (reliability multi-grain): acc={100*k_arm/n:.1f}%  "
          f"[{100*ci_arm[0]:.1f}%,{100*ci_arm[1]:.1f}%]  k={k_arm}/{n}")
    print(f"    CI-separated: {gate._ci_separated(tuple(ci_arm), tuple(ci_guard))}")

    mc = _mcnemar(guard_correct, arm_correct)
    print(f"\n  ---- McNEMAR (ARM R vs GUARD, n={n}) ----")
    print(f"    fixed={mc['fixed']}  broken={mc['broken']}  discordant={mc['discordant']}  "
          f"p={mc['p']:.4g}")

    ev_spreads = _episode_spreads(records)
    contrib = {"whole": wl["w_whole"] * ev_spreads["whole"],
               "stroke": wl["w_stroke"] * ev_spreads["stroke"],
               "rel": wl["w_rel"] * ev_spreads["rel"]}
    print(f"\n  ---- PER-LEVEL CONTRIBUTION (weight x eval across-candidate spread) ----")
    for lvl in ("whole", "stroke", "rel"):
        print(f"    {lvl:<7} spread={ev_spreads[lvl]:.4f}  weight={wl['w_'+lvl]:.4f}  "
              f"contribution={contrib[lvl]:.4f}")

    out = dict(n=n, acc_guard=dict(acc=k_guard / n, ci=list(ci_guard), k=k_guard),
               acc_arm=dict(acc=k_arm / n, ci=list(ci_arm), k=k_arm), mcnemar=mc,
               weights_level=wl, contribution=contrib)
    _save_json(out, _ckpt("report.json"))

    print(f"\n  {'='*22}  DOES RELIABILITY-WEIGHTED MULTI-GRAIN CONVERT?  {'='*22}")
    if mc["discordant"] and mc["fixed"] > mc["broken"] and \
            gate._ci_separated(tuple(ci_arm), tuple(ci_guard)):
        print(f"  OUTCOME (ii) -- WIN: reliability-weighted multi-grain CONVERTS, CI-separated. "
              f"The graph-holds-all-levels architecture works with correct (reliability) weighting "
              f"-- first crack in the whole-shape ceiling.")
    elif mc["discordant"] and mc["fixed"] > mc["broken"]:
        print(f"  OUTCOME (ii, weak): fixed > broken but not CI-separated -- suggestive lead for "
              f"the multi-grain direction, not conclusive.")
    else:
        print(f"  OUTCOME (i): eval fixed <= broken -- even a background-PASSING reliability "
              f"weighting does not convert. Static multi-grain insufficient -> LICENSES option B.")
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
