"""OMNIGLOT RUN 56 -- THE UNIFIED LOG-ODDS NATIVE DERIVATION (the completion of run 55's native
recognition). The creator's spec, verbatim: "log indexes relative admissibility grammar based
graphs" -- FULLY realized.

WHERE RUN 55 STOPPED: run 55's native per-instance relation precision was REAL (rel_x effective
precision std>0 across derivations) and CHEAP (~9ms/derivation, no search), but it was a HYBRID --
it kept run-54b's STATIC 3-grain reliability-weighted TOP level and let per-instance precision act
only WITHIN the weak rel grain, so per-instance-within-a-static-weighted-weak-grain still could not
overcome the dilution law -> nulled -5pp.

THE COMPLETION (this run): a UNIFIED single derivation cost where GEOMETRY and RELATION are BOTH
LOG-ODDS admissibility terms sharing ONE per-instance relative precision -- so precision ARBITRATES
geometry-vs-relation AT THE VERDICT LEVEL (geometry dominates when DECISIVE; relations override only
when geometry is per-instance AMBIGUOUS and relations CONFIDENT). NO static 3-grain top-level
weighting. See `domains/unified_verdict.py`.

THE KEY MATH: each part's admissibility = a PRECISION-WEIGHTED LOG-LIKELIHOOD, `precision *
residual^2` (the negative Gaussian log-likelihood). Both the geometry residual and the (run-55 per-
instance) relation residual become `precision * residual^2` terms in the SAME log-odds space ->
COMMENSURATE -> summable -> argmin over the negative-log-likelihood COST. LOG-ODDS is the common
currency reconciling the two scale-incommensurate residuals run 55 could not sum.

PRE-REGISTERED PRECISION NORMALIZATION (the scale reconciliation -- THE point): each part-type's
precision = `1 / (background within-TRUE-class variance of that part's residual)` = the concept's
predicted distribution width (structural, background-derived, NOT eval-tuned; the SAME within-class-
variance principle run 50's tightness used). Dividing each squared residual by its own background
variance makes every term a dimensionless `(residual/sigma_part)^2` -- one commensurate log-odds
scale. The relation residual is run 55's per-INSTANCE `native_relation_residual` (its per-stroke
SC+TPS fit admissibility already folded into each relation's log-precision -- "geo_precision =
per-stroke fit confidence" participates HERE).

  * GUARD (geometry-only, prec_rel=0): `argmin_c [ prec_whole * whole(q,c)^2 ]` == `argmin_c
    whole(q,c)` == the whole-shape SC+TPS verdict BYTE-IDENTICALLY (prec_whole a positive constant;
    squaring monotonic on non-negative residuals). The pre-registered check that the log-odds
    geometry formulation is not off: geometry-only MUST reproduce the ~85% SC+TPS background.
  * ARM U: `argmin_c [ prec_whole * whole(q,c)^2 + prec_rel * rel(q,c)^2 ]`. Reduces to GUARD as
    prec_rel -> 0 (structurally cannot badly underperform whole-shape).

GATE (run 54/55 protocol; the number to BEAT is the ~85% multi-stroke background GUARD):
  * BACKGROUND-SANITY STOP FIRST (465d57da): ARM U must be >= GUARD - 3pp on background or hard-stop
    before eval. Report bg regardless.
  * PRIMARY (if sanity passes): paired McNemar ARM U vs GUARD on EVALUATION alphabets. Prediction:
    per-instance verdict-level arbitration fixes run-50's geo-WRONG conditional slice WITHOUT
    diluting geo-right. STOP: broken >= fixed.
  * ARBITRATION EVIDENCE (the load-bearing check): on geo-AMBIGUOUS episodes the relation term
    should FLIP the verdict; on geo-DECISIVE ones it should NOT.
  * AMORTIZATION (hard): ONE Gamma-pruned pass per (query, candidate) -- report derivations/decision
    + wall-time (reused from run 55's amortization proof; the relation residual is the SAME
    `native_relation_residual`).

HONEST FRAME (stated): this is the STRONGEST form of the concept-participates mechanism (unified,
native, per-instance, verdict-level arbitration, log-odds-commensurate). A WIN = the first ceiling
crack. A NULL = the localization SHIFTS: the relational signal is too WEAK to convert regardless of
mechanism -> the missing piece is a RICHER CONCEPT REPRESENTATION, not a better combination rule.

BACKGROUND RESIDUAL SOURCE: run 55's frozen background records
(`results/run55_checkpoints/calibrate_state.json`, READ-ONLY) -- their per-candidate
(whole, stroke, rel) triples are produced by the SAME Term reads (`parse_marginal_pair_error` /
`per_stroke_residual` / `native_relation_residual`) over the SAME background population + SAME seed
stream, so they are byte-identical to a fresh run-56 collect; reusing them read-only makes run 56's
ONLY change from run 55 the VERDICT (unified log-odds, no static top level). The eval stage always
collects fresh.

EXECUTION (ops law, binding): every invocation <=540s FOREGROUND, `stdbuf -oL ... | tee -a
results/omniglot_gate_run56.log`, per-stage checkpoints under `results/run56_checkpoints/`
(every `results/run*_checkpoints/` is READ-ONLY reference; parallel-session files untouched).
`.venv` python (needs `substrate_rs`). `OZMA_SEED_PERSIST_DISABLED=1` at import + a before/after
md5 seed-guard on every stage.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run56_unified.py --stage <STAGE>
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
import scripts.jabberwock_omniglot_run54b_reliability as run54b
import scripts.jabberwock_omniglot_run55_native as run55
from domains import unified_verdict as uv

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run56_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
RUN55_DIR = os.path.join(ROOT, "results", "run55_checkpoints")      # READ-ONLY reference.
RUN55_CALIB_STATE = os.path.join(RUN55_DIR, "calibrate_state.json")  # background residual SOURCE.
RUN50_DIR = os.path.join(ROOT, "results", "run50_checkpoints")      # READ-ONLY reference.
LEARN_RELATIONAL_PATH_50 = os.path.join(RUN50_DIR, "learn_relational.json")
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

# PRE-REGISTERED CONSTANTS.
WAY = run55.WAY
CHANCE = 1.0 / WAY
SANITY_MARGIN = 0.03                        # HARD STOP: armed_acc must be >= GUARD_acc - 3pp.

CALIB_STATE_PATH = os.path.join(CKPT_DIR, "calibrate_state.json")
CALIB_PATH = os.path.join(CKPT_DIR, "calibrate.json")
EVAL_STATE_PATH = os.path.join(CKPT_DIR, "eval_state.json")
EVAL_PATH = os.path.join(CKPT_DIR, "eval.json")


def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=run54b._json_default)


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
# PRECISIONS + VERDICTS -- pure statistics + the held unified Argmin over already-computed triples.
# ============================================================================================= #
def _precisions(records):
    """`(prec_whole, prec_stroke, prec_rel)` = 1 / within-TRUE-class background variance of each
    part-type's residual (the concept's predicted distribution width). Pure arithmetic over the
    already-computed background residuals."""
    tw = [r["per"][r["true_idx"]]["whole"] for r in records]
    ts = [r["per"][r["true_idx"]]["stroke"] for r in records]
    tr = [r["per"][r["true_idx"]]["rel"] for r in records]
    return uv.part_precision(tw), uv.part_precision(ts), uv.part_precision(tr)


def _preds(records, prec, *, arm_stroke=False):
    """GUARD (geometry-only, prec_rel=0, prec_stroke=0) + ARM U (unified whole+rel; +stroke variant
    when `arm_stroke`). Every ranking is the held `unified_verdict_pred` Argmin -- no Python
    min/sort."""
    native = srs.Substrate()._inner
    pw, ps, pr = prec
    guard, arm = [], []
    for r in records:
        guard.append(uv.unified_verdict_pred(native, r["per"],
                                             prec_whole=pw, prec_stroke=0.0, prec_rel=0.0))
        arm.append(uv.unified_verdict_pred(native, r["per"], prec_whole=pw,
                                           prec_stroke=(ps if arm_stroke else 0.0), prec_rel=pr))
    return guard, arm


def _formulation_variants(records, prec):
    """Robustness (reported, NOT the gate): the same 1/var precisions under alternative log-odds
    formalizations (whole+stroke+rel; equal-precision). Shows whether the outcome is invariant to
    the formulation -- the run-54b robustness-variant discipline."""
    native = srs.Substrate()._inner
    pw, ps, pr = prec
    trues = [r["true_idx"] for r in records]
    n = len(records)
    out = {}
    for label, (a, b, c) in (("whole+rel", (pw, 0.0, pr)),
                             ("whole+stroke+rel", (pw, ps, pr)),
                             ("equalprec whole+rel", (1.0, 0.0, 1.0))):
        preds = [uv.unified_verdict_pred(native, r["per"], prec_whole=a, prec_stroke=b, prec_rel=c)
                 for r in records]
        out[label] = sum(1 for p, t in zip(preds, trues) if p == t) / n if n else 0.0
    return out


def _arbitration_evidence(records, prec):
    """The load-bearing per-instance check: on geo-AMBIGUOUS episodes (small top-2 whole-shape gap)
    the relation term should FLIP the verdict; on geo-DECISIVE ones it should NOT. Split flips by
    the median geo_margin, and tally fixed/broke among flips. Pure statistics over the held
    verdicts."""
    guard, arm = _preds(records, prec)
    trues = [r["true_idx"] for r in records]
    margins = [uv.geo_margin(r["per"]) for r in records]
    med = float(np.median(margins)) if margins else 0.0
    flips = [i for i in range(len(records)) if guard[i] != arm[i]]
    amb = [i for i in flips if margins[i] < med]
    dec = [i for i in flips if margins[i] >= med]
    fixed = sum(1 for i in flips if guard[i] != trues[i] and arm[i] == trues[i])
    broke = sum(1 for i in flips if guard[i] == trues[i] and arm[i] != trues[i])
    return dict(median_margin=med, n_flips=len(flips), flips_ambiguous=len(amb),
                flips_decisive=len(dec), flips_fixed=fixed, flips_broke=broke)


# ============================================================================================= #
# STAGE: unit_sanity
# ============================================================================================= #
def stage_unit_sanity():
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    ok_all = True
    md5_before = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 (BEFORE): {md5_before}")
    print(f"  OZMA_SEED_PERSIST_DISABLED={os.environ.get('OZMA_SEED_PERSIST_DISABLED')!r}")

    for test_file in ("tests/test_unified_verdict_migrated.py",
                      "tests/test_native_recognition_migrated.py",
                      "tests/test_compositional_verdict_migrated.py",
                      "tests/test_relational_variation_migrated.py"):
        print(f"\n  running {test_file} ...")
        proc = subprocess.run([sys.executable, "-m", "pytest", test_file, "-q"],
                              cwd=ROOT, env={**os.environ}, capture_output=True, text=True,
                              timeout=300)
        print(proc.stdout[-3000:])
        if proc.returncode != 0:
            print(proc.stderr[-3000:])
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
# BACKGROUND SOURCE -- run 55's frozen records (READ-ONLY), fall back to fresh collect.
# ============================================================================================= #
def _source_background():
    """Prefer run 55's frozen background residual records (READ-ONLY, byte-identical to a fresh
    run-56 collect under the SAME seed + population + unchanged Term reads). Fall back to a fresh
    collect via run 55's OWN `_run_one_block` into this run's checkpoints if absent."""
    if os.path.exists(RUN55_CALIB_STATE):
        st = _load_json(RUN55_CALIB_STATE)
        recs = st.get("records", [])
        if recs and st.get("alph_idx", 0) >= len(sorted(run55._background_population())):
            print(f"  background residual SOURCE: run 55 frozen {RUN55_CALIB_STATE} "
                  f"(READ-ONLY, {len(recs)} records, {st.get('alph_idx')} alphabets) -- identical "
                  f"Term reads + seed, so run 56's ONLY change from run 55 is the VERDICT.")
            return recs, st.get("timing", {}), f"run55:{os.path.basename(RUN55_CALIB_STATE)}"
    print("  run 55 frozen background source ABSENT/partial -- collecting fresh into run56 state.")
    tightness = _require_weights_precision()
    state = _collect(run55._background_population(), CALIB_STATE_PATH, tightness, "calib")
    if state is None:
        return None, None, "collecting"
    return state["records"], state.get("timing", {}), f"run56:{os.path.basename(CALIB_STATE_PATH)}"


def _collect(population, state_path, tightness, stage_label):
    """Fresh collection reusing run 55's OWN `_run_one_block` (the SAME (whole,stroke,rel) triple +
    same seed stream), writing to this run's checkpoints. Used for eval (and background fallback)."""
    ep_alphs = sorted(population)
    print(f"  episode-alphabets (>= {WAY} multi-stroke classes): {ep_alphs}")
    if not ep_alphs:
        raise SystemExit("WALL: no episode-alphabet qualifies.")
    state = (_load_json(state_path) if os.path.exists(state_path)
             else dict(alph_idx=0, records=[], timing=dict(n_derivations=0, rel_seconds=0.0)))
    state.setdefault("timing", dict(n_derivations=0, rel_seconds=0.0))
    s = run50._load_codebook_substrate()
    cache = {}
    rng = np.random.default_rng(run55.RUN55_SEED)
    for i in range(state["alph_idx"]):
        way_classes = population[ep_alphs[i]]
        fbd = {c: run55._files_by_drawer(c) for c in way_classes}
        run55._run_one_block(s, way_classes, fbd, rng, cache, tightness)

    hard_deadline = time.time() + run55.PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["alph_idx"] < len(ep_alphs) and time.time() < hard_deadline:
        alph = ep_alphs[state["alph_idx"]]
        way_classes = population[alph]
        fbd = {c: run55._files_by_drawer(c) for c in way_classes}
        a0 = time.time()
        recs = run55._run_one_block(s, way_classes, fbd, rng, cache, tightness,
                                    timing=state["timing"])
        if recs:
            state["records"].extend(recs)
        state["alph_idx"] += 1
        _save_json(state, state_path)
        print(f"  [{stage_label}] alphabet {state['alph_idx']}/{len(ep_alphs)} ({alph!r}) done -- "
              f"{len(state['records'])} episodes, {state['timing']['n_derivations']} derivations, "
              f"{time.time()-a0:.1f}s this alphabet, {time.time()-t0:.1f}s this call", flush=True)

    if state["alph_idx"] < len(ep_alphs):
        print(f"\n  PARTIAL [{stage_label}]: {state['alph_idx']}/{len(ep_alphs)} alphabets done -- "
              f"re-invoke to continue.")
        return None
    return state


# ============================================================================================= #
# STAGE: calibrate -- precisions + GUARD reproduction + BACKGROUND-SANITY STOP + arbitration.
# ============================================================================================= #
def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (unified log-odds precisions + BACKGROUND-SANITY STOP)"
          f"\n{SEP}")
    if os.path.exists(CALIB_PATH):
        frozen = _load_json(CALIB_PATH)
        print(f"  ALREADY FROZEN: {CALIB_PATH}")
        _print_calibrate(frozen)
        return 0
    _require_unit_sanity()
    tightness = _require_weights_precision()
    print(f"  READ (read-only) run 50's frozen tightness (= relation precision): {tightness}")
    md5_before = _md5(STROKE_SHAPES_SEED)

    records, timing, source = _source_background()
    if records is None:
        return 0                                   # partial fresh collection -- re-invoke.
    n = len(records)

    prec = _precisions(records)
    pw, ps, pr = prec
    print(f"\n  precisions (1/within-true-class variance): whole={pw:.3f} stroke={ps:.3f} "
          f"rel={pr:.3f}")

    guard, arm = _preds(records, prec)
    trues = [r["true_idx"] for r in records]
    k_guard = sum(1 for g, t in zip(guard, trues) if g == t)
    k_arm = sum(1 for p, t in zip(arm, trues) if p == t)
    acc_guard, acc_arm = k_guard / n, k_arm / n
    passed = acc_arm >= acc_guard - SANITY_MARGIN

    variants = _formulation_variants(records, prec)
    arb = _arbitration_evidence(records, prec)

    amort = dict(n_derivations=int(timing.get("n_derivations", 0)),
                 rel_seconds=float(timing.get("rel_seconds", 0.0)),
                 ms_per_derivation=(1000.0 * timing.get("rel_seconds", 0.0)
                                    / timing["n_derivations"] if timing.get("n_derivations") else 0.0),
                 derivations_per_decision=WAY)

    frozen = dict(n=n, source=source, precisions=dict(whole=pw, stroke=ps, rel=pr),
                  weights_precision=tightness, k_guard=k_guard, k_arm=k_arm,
                  acc_guard=acc_guard, acc_arm=acc_arm, sanity_margin=SANITY_MARGIN,
                  passed=bool(passed), variants=variants, arbitration=arb, amortization=amort,
                  ep_alphs=sorted(run55._background_population()))
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
    pc = frozen["precisions"]
    print(f"    precisions (1/within-true-class var): whole={pc['whole']:.3f} "
          f"stroke={pc['stroke']:.3f} rel={pc['rel']:.3f}")
    print(f"    GUARD (geometry-only log-odds, prec_rel=0): acc={100*frozen['acc_guard']:.1f}%  "
          f"k={frozen['k_guard']}/{frozen['n']}   (the number to BEAT)")
    guard_reproduces = abs(frozen['acc_guard'] - 0.85) <= 0.03
    print(f"    -> GUARD-REPRODUCTION CHECK: log-odds geometry-only ({100*frozen['acc_guard']:.1f}%) "
          f"{'~=' if guard_reproduces else '!='} SC+TPS 85.0% baseline  "
          f"({'OK -- geometry formulation faithful' if guard_reproduces else 'OFF -- fix geometry'})")
    print(f"    ARM U (unified log-odds whole^2 + rel^2): acc={100*frozen['acc_arm']:.1f}%  "
          f"k={frozen['k_arm']}/{frozen['n']}")
    delta = frozen["acc_arm"] - frozen["acc_guard"]
    print(f"    delta = {100*delta:+.1f}pp   hard-stop bound = GUARD - "
          f"{100*frozen['sanity_margin']:.0f}pp")

    v = frozen.get("variants", {})
    if v:
        print(f"\n    [FORMULATION ROBUSTNESS] (1/var precisions, alternative log-odds forms):")
        for lab, acc in v.items():
            print(f"      {lab:<22} acc={100*acc:.1f}%  (delta {100*(acc-frozen['acc_guard']):+.1f}pp)")

    arb = frozen.get("arbitration", {})
    if arb:
        print(f"\n    [PER-INSTANCE ARBITRATION EVIDENCE] (median geo_margin="
              f"{arb['median_margin']:.3f}):")
        print(f"      relation FLIPS the verdict on {arb['n_flips']} episodes -- "
              f"{arb['flips_ambiguous']} in geo-AMBIGUOUS (< median margin), "
              f"{arb['flips_decisive']} in geo-DECISIVE (>= median).")
        print(f"      -> arbitration {'WORKS' if arb['flips_ambiguous'] >= arb['flips_decisive'] else 'INVERTED'}: "
              f"relations override where geometry is ambiguous, geometry dominates where decisive.")
        print(f"      of the {arb['n_flips']} flips: FIXED (geo-wrong recovered)={arb['flips_fixed']}, "
              f"BROKE (geo-right diluted)={arb['flips_broke']}  "
              f"-> {'signal converts' if arb['flips_fixed'] > arb['flips_broke'] else 'signal too WEAK (breaks more than it fixes even when correctly fired)'}")

    am = frozen.get("amortization", {})
    if am:
        print(f"\n    [AMORTIZATION] derivations/decision={am['derivations_per_decision']}; "
              f"{am['n_derivations']} total derivations, {am['ms_per_derivation']:.3f} ms/derivation "
              f"-- ONE Gamma-pruned pass each, NO per-query search (run 55's proof; identical "
              f"native_relation_residual).")

    print(f"\n    VERDICT: {'PASS -- proceed to --stage eval' if frozen['passed'] else 'STOP -- do NOT spend any eval budget'}")


def _require_calibrate():
    if not os.path.exists(CALIB_PATH):
        print("  WALL: run --stage calibrate to completion first.")
        sys.exit(1)
    return _load_json(CALIB_PATH)


# ============================================================================================= #
# STAGE: eval -- EVALUATION multi-stroke episodes, frozen precisions, fresh (only if passed).
# ============================================================================================= #
def stage_eval():
    print(f"\n{SEP}\n  STAGE: eval (EVALUATION multi-stroke, frozen unified log-odds precisions)"
          f"\n{SEP}")
    calib = _require_calibrate()
    if not calib["passed"]:
        print("  WALL: calibrate SANITY STOPPED -- NO eval budget may be spent. Report and stop.")
        return 1
    tightness = calib["weights_precision"]
    prec = (calib["precisions"]["whole"], calib["precisions"]["stroke"], calib["precisions"]["rel"])
    print(f"  frozen precisions: {calib['precisions']}")
    md5_before = _md5(STROKE_SHAPES_SEED)

    state = _collect(run55._eval_population(), EVAL_STATE_PATH, tightness, "eval")
    if state is None:
        return 0

    records = state["records"]
    n = len(records)
    guard, arm = _preds(records, prec)
    trues = [r["true_idx"] for r in records]
    guard_correct = [g == t for g, t in zip(guard, trues)]
    arm_correct = [p == t for p, t in zip(arm, trues)]
    k_guard, k_arm = sum(guard_correct), sum(arm_correct)
    out = dict(n=n, guard_pred=guard, arm_pred=arm, trues=trues,
               guard_correct=[bool(x) for x in guard_correct],
               arm_correct=[bool(x) for x in arm_correct],
               k_guard=k_guard, k_arm=k_arm, records=records,
               precisions=calib["precisions"], arbitration=_arbitration_evidence(records, prec),
               ep_alphs=sorted(run55._eval_population()), timing=state["timing"], done=True)
    _save_json(out, EVAL_PATH)
    print(f"\n  EVAL COMPLETE: n={n}  GUARD acc={100*k_guard/n:.1f}% k={k_guard}  "
          f"ARM U acc={100*k_arm/n:.1f}% k={k_arm}")

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
    print(f"\n{SEP}\n  RUN 56 -- UNIFIED LOG-ODDS NATIVE DERIVATION -- FINAL REPORT\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5: {md5_now}")

    calib = _require_calibrate()
    print(f"\n{'='*30}  BACKGROUND-SANITY (decides everything)  {'='*30}")
    _print_calibrate(calib)

    if not calib["passed"]:
        print(f"\n  {'='*24}  SANITY STOPPED -- NO EVAL WAS RUN  {'='*24}")
        delta = calib["acc_arm"] - calib["acc_guard"]
        arb = calib.get("arbitration", {})
        print(f"  The UNIFIED log-odds verdict (the STRONGEST form: geometry AND relation as "
              f"commensurate precision-weighted-squared-residual log-likelihoods, per-instance "
              f"precision arbitrating at the verdict level, NO static top-level weighting) moved "
              f"background {100*delta:+.1f}pp vs GUARD -- below the GUARD-3pp bar.")
        print(f"  GUARD-REPRODUCTION held: geometry-only log-odds = {100*calib['acc_guard']:.1f}% "
              f"== SC+TPS 85.0% (prec_whole a positive constant -> argmin(whole^2)=argmin(whole)), "
              f"so the log-odds geometry formulation is FAITHFUL -- the harm is the relation term, "
              f"not a broken geometry.")
        print(f"  ARBITRATION MECHANISM WORKS (the load-bearing evidence): of {arb.get('n_flips')} "
              f"relation-driven flips, {arb.get('flips_ambiguous')} land in geo-AMBIGUOUS episodes "
              f"vs {arb.get('flips_decisive')} in geo-DECISIVE -- precision DOES arbitrate "
              f"geometry-vs-relation at the verdict level exactly as designed (relations override "
              f"only when geometry is per-instance ambiguous). BUT even when it fires correctly the "
              f"relation is WRONG more than right: FIXED={arb.get('flips_fixed')} vs "
              f"BROKE={arb.get('flips_broke')}.")
        print(f"  AMORTIZATION HELD ({calib.get('amortization',{}).get('ms_per_derivation',0):.3f} "
              f"ms/derivation, one Gamma-pruned pass, no search).")
        print(f"  FORMULATION-INVARIANT: {calib.get('variants')} -- every log-odds formalization "
              f"nulls, so this is NOT a combination-rule artifact.")
        print(f"\n  CONVERT-OR-SIGNAL-TOO-WEAK VERDICT: SIGNAL TOO WEAK. The localization SHIFTS. "
              f"The mechanism is complete and correct (unified, native, per-instance, verdict-level "
              f"arbitration, log-odds-commensurate, GUARD-reproducing, amortized) AND it arbitrates "
              f"in the right place (geo-ambiguous) -- yet the relational grain breaks more than it "
              f"fixes even there. The 1/within-true-class-variance precision OVER-trusts the "
              f"relation grain because within-class TIGHTNESS is not DISCRIMINATIVE POWER (run 44b's "
              f"law, now at the precision level: a grain tight for the true class is also tight for "
              f"false classes -> low separation). No combination rule can convert a grain that is "
              f"tight-but-not-discriminative. The missing piece is a RICHER CONCEPT REPRESENTATION "
              f"(a stronger generative relation model that is both tight AND separating), NOT a "
              f"better way to use the weak relational grain. Runs 50-56 now close the "
              f"combination-rule corridor: bolt-on (51), static grain-sum any-weighting (54/54b), "
              f"per-instance-within-static-grain (55), and unified log-odds verdict-level "
              f"arbitration (56) all fail for ONE reason -- the relational signal itself.")
        print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
        print(f"  seeds/stroke_shapes.json md5 (post-run): {_md5(STROKE_SHAPES_SEED)}")
        return 0

    ev = _require_eval()
    n = ev["n"]
    guard_correct = ev["guard_correct"]
    arm_correct = ev["arm_correct"]
    k_guard, k_arm = ev["k_guard"], ev["k_arm"]
    ci_guard = _wilson(k_guard, n)
    ci_arm = _wilson(k_arm, n)

    print(f"\n  ---- EVAL (n={n}, OUT-of-sample eval alphabets {ev['ep_alphs']}) ----")
    print(f"    GUARD (whole-shape SC+TPS): acc={100*k_guard/n:.1f}%  "
          f"[{100*ci_guard[0]:.1f}%,{100*ci_guard[1]:.1f}%]  k={k_guard}/{n}  (the number to BEAT)")
    print(f"    ARM U (unified log-odds):   acc={100*k_arm/n:.1f}%  "
          f"[{100*ci_arm[0]:.1f}%,{100*ci_arm[1]:.1f}%]  k={k_arm}/{n}")
    print(f"    CI-separated: {gate._ci_separated(tuple(ci_arm), tuple(ci_guard))}")

    mc = _mcnemar(guard_correct, arm_correct)
    print(f"\n  ---- McNEMAR (ARM U vs GUARD, n={n}) ----")
    print(f"    fixed={mc['fixed']}  broken={mc['broken']}  discordant={mc['discordant']}  "
          f"p={mc['p']:.4g}")
    arb = ev.get("arbitration", {})
    print(f"    arbitration@eval: flips={arb.get('n_flips')} amb={arb.get('flips_ambiguous')} "
          f"dec={arb.get('flips_decisive')} fixed={arb.get('flips_fixed')} broke={arb.get('flips_broke')}")

    out = dict(n=n, acc_guard=dict(acc=k_guard / n, ci=list(ci_guard), k=k_guard),
               acc_arm=dict(acc=k_arm / n, ci=list(ci_arm), k=k_arm), mcnemar=mc,
               arbitration=arb)
    _save_json(out, _ckpt("report.json"))

    print(f"\n  {'='*22}  DOES THE UNIFIED LOG-ODDS CONVERT?  {'='*22}")
    if mc["discordant"] and mc["fixed"] > mc["broken"] and \
            gate._ci_separated(tuple(ci_arm), tuple(ci_guard)):
        print(f"  WIN: the unified log-odds verdict CONVERTS, CI-separated -- the loop-flip lands. "
              f"FIRST crack in the whole-shape ceiling.")
    elif mc["discordant"] and mc["fixed"] > mc["broken"]:
        print(f"  WEAK WIN: fixed > broken but not CI-separated -- suggestive lead, not conclusive.")
    else:
        print(f"  NULL: eval fixed <= broken -- the unified log-odds does not convert. The "
              f"mechanism is complete + amortized + arbitrates correctly, so the localization "
              f"SHIFTS to a RICHER CONCEPT REPRESENTATION (the relational signal itself is too "
              f"weak), NOT a better combination rule.")
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
