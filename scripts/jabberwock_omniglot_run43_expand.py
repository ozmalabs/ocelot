"""OMNIGLOT RUN 43, PHASE 3 -- EXEMPLAR EXPANSION UNDER A BACKGROUND-CALIBRATED VARIATION MODEL.

THE MECHANISM (see `domains/exemplar_expand.py`'s own module docstring for the full estimator
derivation -- this header states only the run's arms/gate, not the estimator math): RUN 40
(commit 45dc2855) found exemplar-token badness drives the mid+far verdict error bands -- a
single raw exemplar render is often an unrepresentative token of its class. This run compares
each candidate to a SET (its own original render + K=8 calibrated variants) instead of one
token, scoring a candidate as the MIN pairwise error over that set. RUN 25's C3 (`write_with_
hand` nuisance-variant marginalization) nulled this SHAPE at ARBITRARY magnitudes
(6da31cee); this run is different in the two ways `exemplar_expand.py`'s docstring states up
front: magnitudes are CALIBRATED from the 5 LEARN alphabets' own within-class drawer spread
(not guessed), and only WRITER dimensions are varied (rotation/shear/per-stroke pose jitter --
RUN 42's binding law: never aspect, that dimension is alphabet-characteristic).

ARMS (run-26 protocol: `scripts.jabberwock_omniglot_run25_number._block_spec`, POWER_SEED,
byte-identical block order -- alph OUTER, r INNER, 10 alphabets x R_TARGET=2 -> n=400):
  GUARD -- unmodified full-dwell (`domains.abs_read.stage_parse_char` + `parse_marginal_
           verdict`, RUN 25's C0), 37C hygiene filter ON, must reproduce 80.5% / k=322 / n=400
           EXACTLY (`results/run26_checkpoints/eval_baseline.json`) -- this run's own GLOBAL
           McNemar comparator too (recomputed fresh under 37C-ON, not read from a pre-37C cache).
  ARM X -- min-over-set verdict: for each of the 20 candidates, stage the ORIGINAL exemplar
           node (byte-identical staging to GUARD) PLUS `exemplar_expand.VARIANT_GRID`'s 8
           calibrated-variant nodes (via `exemplar_expand.VariantStrokesFilter`, a synthetic-key
           monkeypatch of `omniglot_world.load_strokes` -- `abs_read.stage_parse_char` and the
           per-pair comparator (`abs_read.parse_marginal_pair_error`, the SAME per-(query,
           candidate) term GUARD's own fused Argmax ranks by internally) are UNCHANGED; only
           which ink a given staged node's `load_strokes` call resolves to changes). Per query,
           per candidate: `_min_score_term` (held `MinOver`) over the candidate's own
           {original, 8 variants} pairwise-error set; across the 20 candidates' own min-scores,
           `_argmin_pairs_term` (held `Argmin`, the SAME idiom `abs_read.widen_decision`/
           `refit_bidir_plus_marginal_rerank` already use) picks the predicted winner. The
           original is ALWAYS a member of its own candidate's set, so a candidate's min-over-set
           score is STRUCTURALLY <= its own original-only score -- this can still HARM: an
           IMPOSTOR candidate's variant may land closer to the query than its own original did,
           which is exactly the risk RUN 25's C3 already measured a base rate for (a null, not a
           different failure mode this run invents) and this run's own STOP condition below
           re-measures directly.

PRIMARY ANALYSIS (pre-registered): paired McNemar (exact binomial on discordant pairs), ARM X
vs GUARD/GLOBAL. PREDICTIONS: fixes concentrate in the mid/far bands and in episodes RUN 40
classified EXEMPLAR-OUTLIER / BOTH-OUTLIER (`results/run40_checkpoints/classify.json`,
READ-ONLY, idx-joined, 158/400 coverage -- reported as a restriction every time, RUN 15's own
law); broken episodes concentrate in the NEAR band (impostor-variant collisions are more likely
where the true-vs-impostor margin was already thin). STOP (pre-registered, no retuning against
the eval): broken >= fixed -> ARM X harms, stop, report as the finding.

ALSO REPORTED: the calibrated magnitudes themselves (`exemplar_expand.calibrate_or_load`'s own
frozen numbers, including the reported-but-excluded global log-scale std -- RUN 28's "report
engagement separately from outcome" law); a per-episode MARGIN-SHIFT diagnostic (does
min-over-set tighten or widen the true-vs-best-impostor margin on episodes GUARD already got
right -- the dilution-risk read, comparing the ORIGINAL-ONLY per-candidate score set, computed
from the SAME ARM X staging via tag=0 subsetting, against the min-over-set score set); wall-
clock (the (K+1) x 20 pairwise evaluates per query is the cost this run pays for the mechanism).

EXECUTION (ops law, binding): every invocation <=540s foreground, per-block checkpointing under
`results/run43_checkpoints/` (run26/run40 checkpoint dirs READ-ONLY references, never written
here), `--stage pilot` runs ONE block fully instrumented (timing breakdown) before committing to
the full n=400 budget. `.venv` python (needs `substrate_rs`) for every stage; the unit tests
(`tests/test_exemplar_expand_migrated.py`) run under system `python3` per this arc's own
convention (substrate_rs is importable there too). No LLM call of any kind; donkey=0 is not
applicable (no torch in this arc's dependency graph).

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run43_expand.py --stage calibrate
  ... --stage pilot
  ... --stage guard
  ... --stage armx
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
from domains import exemplar_expand as ee
from domains import omniglot_world as ow

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run43_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")   # READ-ONLY reference.
RUN40_DIR = os.path.join(ROOT, "results", "run40_checkpoints")   # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

WAY = run25.WAY                                       # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET   # 20
R_TARGET = run25.R_TARGET                             # 2  -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS             # 10
POWER_SEED = run25.POWER_SEED                         # gate.SEED + 1500, byte-identical
GUARD_CONTROL = dict(acc=0.805, k=322, n=400)         # results/run26_checkpoints/eval_baseline.json

CALIB_PATH = os.path.join(CKPT_DIR, "calibration.json")
PER_CALL_BUDGET_SECONDS = 460.0                       # leaves >120s headroom under the 590s cap.


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
    """alph OUTER, r INNER -- byte-identical order to run25/run26/run42's own eval block order,
    so `idx = block_idx * 20 + qi` lines up with `results/run26_checkpoints/eval_baseline.json`
    and `results/run40_checkpoints/classify.json`'s own `idx` convention."""
    test_alphabets = _test_alphabets()
    return [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]


# ===================================================================================================
# Held Term builders -- duplicated locally per this codebase's own established convention
# (`domains.abs_read`'s/`domains.ink_decode`'s own small pure Term builders are each repeated
# call-site-local rather than shared-imported); byte-identical shape to `abs_read._min_score_
# term`/`abs_read._argmin_pairs_term`.
# ===================================================================================================
def _min_score_term(pairs) -> dict:
    return {"type": "MinOver", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}},
            "default": {"type": "Lit", "value": 0.0}}


def _argmin_pairs_term(pairs) -> dict:
    return {"type": "Argmin", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


# ===================================================================================================
# STAGE: calibrate -- freeze `exemplar_expand`'s four calibrated magnitudes once.
# ===================================================================================================
def stage_calibrate() -> int:
    print(f"\n{SEP}\n  STAGE: calibrate\n{SEP}")
    fresh = not os.path.exists(CALIB_PATH)
    t0 = time.time()
    calib = ee.calibrate_or_load(CALIB_PATH)
    dt = time.time() - t0
    print(f"  {'COMPUTED + FROZEN' if fresh else 'READ FROZEN'} ({dt:.2f}s): {CALIB_PATH}")
    print(f"  learn_alphabets: {calib['learn_alphabets']}")
    print(f"  n_classes={calib['n_classes']}  n_glyphs={calib['n_glyphs']}  "
          f"n_pose_samples={calib['n_pose_samples']}")
    print(f"  shear_std      = {calib['shear_std']:.4f}  (n={calib['n_shear_samples']})")
    print(f"  rotation_std   = {calib['rotation_std']:.4f} rad "
          f"({np.degrees(calib['rotation_std']):.2f} deg)  (n={calib['n_rotation_samples']})")
    print(f"  log_scale_std  = {calib['log_scale_std']:.4f}  (n={calib['n_scale_samples']}) "
          f"-- REPORT-ONLY, excluded from VARIANT_GRID (structural no-op, see module docstring)")
    print(f"  pose_x_std     = {calib['pose_x_std']:.4f}")
    print(f"  pose_y_std     = {calib['pose_y_std']:.4f}")
    print(f"  pose_o_std     = {calib['pose_o_std']:.4f} rad "
          f"({np.degrees(calib['pose_o_std']):.2f} deg)")
    print(f"  pose_s_std     = {calib['pose_s_std']:.4f}")
    print(f"  Z_QUANTILE = {ee.Z_QUANTILE}  VARIANT_GRID (K={len(ee.VARIANT_GRID)}) = "
          f"{ee.VARIANT_GRID}")
    return 0


def _require_calib() -> dict:
    if not os.path.exists(CALIB_PATH):
        print("  WALL: run --stage calibrate first (freezes results/run43_checkpoints/"
              "calibration.json).")
        sys.exit(1)
    return ee.load_calibration(CALIB_PATH)


# ===================================================================================================
# ONE block's worth of ARM X staging: 20 candidates, each with its own {orig, v0..v7} node set.
# ===================================================================================================
def _stage_armx_candidates(scratch, drawer_files, ex_drawer, calib: dict) -> dict:
    """Returns `{ci: [node_orig, node_v0, ..., node_v7]}` (index 0 is always the ORIGINAL,
    byte-identical staging to `run25._stage_candidates`'s own per-candidate call). Mechanical
    staging only -- no decision. `ow.load_strokes` is called for the REAL path exactly once per
    candidate (37C-filtered by the caller's own `DropDegenerateFilter` context) to build the
    variant set; `ee.VariantStrokesFilter` then redirects the K synthetic keys for the
    `stage_parse_char` calls that follow."""
    nodes_of_cand: dict[int, list] = {}
    for ci in range(WAY):
        path = drawer_files[ci][ex_drawer]
        node0 = ar.stage_parse_char(scratch, path, is_query=False,
                                     thetas=ar.DEFAULT_PARSE_THETAS, name=str(ci))
        nodes = [node0]
        raw_strokes = ow.load_strokes(path)
        variants = ee.render_variant_set(raw_strokes, calib) if raw_strokes else []
        variants_by_key = {ee.variant_key(path, k): v for k, v in enumerate(variants)}
        if variants_by_key:
            with ee.VariantStrokesFilter(variants_by_key):
                for k in range(len(variants)):
                    key = ee.variant_key(path, k)
                    vnode = ar.stage_parse_char(scratch, key, is_query=False,
                                                 thetas=ar.DEFAULT_PARSE_THETAS,
                                                 name=f"{ci}_v{k}")
                    scratch.set_attr(vnode, "is_word", 0.0)
                    nodes.append(vnode)
        nodes_of_cand[ci] = nodes
    return nodes_of_cand


def _run_block_armx(alph: str, r: int, spec: dict, calib: dict) -> tuple:
    """One block (byte-identical query/exemplar draw to GUARD): 20-candidate min-over-set
    verdict per query + the margin-shift diagnostic ingredients (per-candidate ORIGINAL-only
    score IS the tag-0 entry of the same staged set, no second staging)."""
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    recs, margins = [], []
    with DropDegenerateFilter():
        scratch = srs.Substrate()
        nodes_of_cand = _stage_armx_candidates(scratch, drawer_files, ex_drawer, calib)
        native = getattr(scratch, "_inner", scratch)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)

            min_pairs, orig_pairs = [], []
            for ci in range(WAY):
                inner = [(ar.parse_marginal_pair_error(scratch, qn, nid), k)
                         for k, nid in enumerate(nodes_of_cand[ci])]
                min_score = float(native.evaluate(_min_score_term(inner), {}))
                min_pairs.append((min_score, ci))
                orig_pairs.append((inner[0][0], ci))     # tag 0 == the original node's own score

            winner = native.evaluate(_argmin_pairs_term(min_pairs), {})
            pred = int(winner[1]) if winner is not None else -1
            owinner = native.evaluate(_argmin_pairs_term(orig_pairs), {})
            opred = int(owinner[1]) if owinner is not None else -1

            true_min = next(s for s, ci in min_pairs if ci == qi)
            true_orig = next(s for s, ci in orig_pairs if ci == qi)
            rest_min = [p for p in min_pairs if p[1] != qi]
            rest_orig = [p for p in orig_pairs if p[1] != qi]
            best_imp_min = (float(native.evaluate(_min_score_term(rest_min), {}))
                             if rest_min else None)
            best_imp_orig = (float(native.evaluate(_min_score_term(rest_orig), {}))
                              if rest_orig else None)

            recs.append(dict(true=qi, alph=alph, r=r, pred_full=pred, correct=bool(pred == qi),
                              pred_orig_only=opred, correct_orig_only=bool(opred == qi)))
            margins.append(dict(true=qi, true_score_min=true_min, true_score_orig=true_orig,
                                 best_impostor_min=best_imp_min,
                                 best_impostor_orig=best_imp_orig,
                                 margin_min=(best_imp_min - true_min) if best_imp_min is not None
                                            else None,
                                 margin_orig=(best_imp_orig - true_orig)
                                             if best_imp_orig is not None else None))
    return recs, margins


# ===================================================================================================
# STAGE: pilot -- ONE block, fully instrumented (timing breakdown), before the full n=400 run.
# ===================================================================================================
def stage_pilot() -> int:
    print(f"\n{SEP}\n  STAGE: pilot (one block)\n{SEP}")
    calib = _require_calib()
    blocks = _blocks()
    alph, r = blocks[0]
    rng = np.random.default_rng(POWER_SEED)
    with DropDegenerateFilter():
        spec = run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)
    t0 = time.time()
    recs, margins = _run_block_armx(alph, r, spec, calib)
    dt = time.time() - t0
    k = sum(1 for x in recs if x["correct"])
    ko = sum(1 for x in recs if x["correct_orig_only"])
    print(f"  block ({alph!r}, r={r}, {len(recs)} episodes): {dt:.2f}s "
          f"({dt/len(recs):.3f}s/episode)")
    print(f"  armx acc this block: {k}/{len(recs)}   orig-only-restaged acc: {ko}/{len(recs)} "
          f"(sanity check vs GUARD's own fused verdict -- expected close, not necessarily "
          f"identical: same per-pair term, different wrapping)")
    print(f"  projected full n=400 (20 blocks): ~{dt * 20:.1f}s eval time "
          f"(excludes calibration, already frozen)")
    return 0


# ===================================================================================================
# STAGE: guard -- byte-identical reproduction of run25/run26/run42's own GUARD arm.
# ===================================================================================================
def _run_block_guard(alph: str, r: int, spec: dict) -> list:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    recs = []
    with DropDegenerateFilter():
        scratch0 = srs.Substrate()
        _, cand0 = run25._stage_candidates(scratch0, drawer_files, ex_drawer, WAY,
                                            thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn0 = ar.stage_parse_char(scratch0, path, is_query=True,
                                       thetas=ar.DEFAULT_PARSE_THETAS)
            w0 = ar.parse_marginal_verdict(scratch0, qn0)
            pred = cand0.get(w0, -1) if w0 is not None else -1
            recs.append(dict(true=qi, alph=alph, r=r, pred_full=pred, correct=bool(pred == qi)))
    return recs


def _stage_eval_generic(name: str, block_fn) -> int:
    print(f"\n{SEP}\n  STAGE: eval-{name}\n{SEP}")
    out_path = _ckpt(f"eval_{name}.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], extra=[], block_idx=0, done=False)

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
        result = block_fn(alph, r, spec)
        recs, extra = (result, []) if name == "guard" else result
        for pos, rec in enumerate(recs):
            rec["idx"] = state["block_idx"] * WAY + pos
        for pos, ex in enumerate(extra):
            ex["idx"] = state["block_idx"] * WAY + pos
        state["records"].extend(recs)
        state["extra"].extend(extra)
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


def stage_armx() -> int:
    calib = _require_calib()
    return _stage_eval_generic("armx", lambda a, r, spec: _run_block_armx(a, r, spec, calib))


# ===================================================================================================
# STAGE: report -- McNemar, band + enrichment tables, calibrated magnitudes, margin-shift,
# wall-clock.
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


def _enrichment(classify_rows_by_idx: dict, fixed_idx: set, broken_idx: set,
                all_scored_idx: list, target_labels=("EXEMPLAR-OUTLIER", "BOTH-OUTLIER")) -> dict:
    scored_and_classified = [i for i in all_scored_idx if i in classify_rows_by_idx]
    base_n = len(scored_and_classified)
    base_hits = sum(1 for i in scored_and_classified
                     if classify_rows_by_idx[i]["diagnosis_adjusted"] in target_labels)
    base_rate = base_hits / base_n if base_n else float("nan")

    fixed_joined = [i for i in fixed_idx if i in classify_rows_by_idx]
    fixed_hits = sum(1 for i in fixed_joined
                      if classify_rows_by_idx[i]["diagnosis_adjusted"] in target_labels)
    fixed_rate = fixed_hits / len(fixed_joined) if fixed_joined else float("nan")

    broken_joined = [i for i in broken_idx if i in classify_rows_by_idx]
    broken_hits = sum(1 for i in broken_joined
                       if classify_rows_by_idx[i]["diagnosis_adjusted"] in target_labels)
    broken_rate = broken_hits / len(broken_joined) if broken_joined else float("nan")

    return dict(base_rate=base_rate, base_n=base_n, base_hits=base_hits,
                fixed_rate=fixed_rate, fixed_n=len(fixed_joined), fixed_hits=fixed_hits,
                broken_rate=broken_rate, broken_n=len(broken_joined), broken_hits=broken_hits)


def stage_report() -> int:
    print(f"\n{SEP}\n  STAGE: report\n{SEP}")
    calib = _require_calib()
    guard = _require("guard")
    armx = _require("armx")
    n = len(guard["records"])
    assert n == len(armx["records"]), f"guard n={n} != armx n={len(armx['records'])}"

    guard_correct = [None] * n
    for rec in guard["records"]:
        guard_correct[rec["idx"]] = rec["correct"]
    armx_correct = [None] * n
    orig_correct = [None] * n
    for rec in armx["records"]:
        armx_correct[rec["idx"]] = rec["correct"]
        orig_correct[rec["idx"]] = rec["correct_orig_only"]

    classify_path = os.path.join(RUN40_DIR, "classify.json")
    classify = _load_json(classify_path) if os.path.exists(classify_path) else {"rows": []}
    classify_rows_by_idx = {row["idx"]: row for row in classify["rows"]}
    print(f"  run40 classify.json: {len(classify_rows_by_idx)} idx-labelled episodes "
          f"(READ-ONLY reference, {classify_path})")

    all_idx = list(range(n))
    mc = _mcnemar(guard_correct, armx_correct)
    fixed_idx = {i for i in all_idx if (not guard_correct[i]) and armx_correct[i]}
    broken_idx = {i for i in all_idx if guard_correct[i] and (not armx_correct[i])}
    enrich = _enrichment(classify_rows_by_idx, fixed_idx, broken_idx, all_idx)

    k_arm = sum(1 for c in armx_correct if c)
    ci_arm = _wilson(k_arm, n)
    k_guard = sum(guard_correct)
    ci_guard = _wilson(k_guard, n)
    k_orig = sum(1 for c in orig_correct if c)

    print(f"\n  ---- McNEMAR: ARM X vs GUARD/GLOBAL ----")
    print(f"    GUARD accuracy:  {100*k_guard/n:.1f}% [{100*ci_guard[0]:.1f}, "
          f"{100*ci_guard[1]:.1f}]  k={k_guard}/{n}")
    print(f"    ARM X accuracy:  {100*k_arm/n:.1f}% [{100*ci_arm[0]:.1f}, {100*ci_arm[1]:.1f}]  "
          f"k={k_arm}/{n}")
    print(f"    orig-only-restaged accuracy (sanity check vs GUARD): {100*k_orig/n:.1f}% "
          f"k={k_orig}/{n}")
    print(f"    McNemar: fixed={mc['fixed']}  broken={mc['broken']}  "
          f"discordant={mc['discordant']}  p={mc['p']:.4g}   "
          f"{'ARM X HARMS -- STOP' if mc['broken'] >= mc['fixed'] and mc['discordant'] else 'ok'}")

    print(f"\n  ---- RUN-40 ENRICHMENT (idx-joined, {enrich['base_n']}/400 episodes have a "
          f"run-40 label) ----")
    print(f"    base rate of EXEMPLAR-OUTLIER/BOTH-OUTLIER among all joined episodes: "
          f"{enrich['base_hits']}/{enrich['base_n']} = {100*enrich['base_rate']:.1f}%")
    print(f"    among FIXED (joined n={enrich['fixed_n']}): {enrich['fixed_hits']}/"
          f"{enrich['fixed_n']} = "
          f"{100*enrich['fixed_rate'] if enrich['fixed_n'] else float('nan'):.1f}%")
    print(f"    among BROKEN (joined n={enrich['broken_n']}): {enrich['broken_hits']}/"
          f"{enrich['broken_n']} = "
          f"{100*enrich['broken_rate'] if enrich['broken_n'] else float('nan'):.1f}%")

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
          f"{len(classify_rows_by_idx)}/400 run-40-classified episodes) ----")
    for band in ("near", "mid", "far", "control"):
        c = band_counts.get(band, Counter())
        print(f"    {band:<8} fixed={c['fixed']:<3} broken={c['broken']:<3} "
              f"unchanged={c['unchanged']:<3}")

    print(f"\n  ---- CALIBRATED VARIATION MAGNITUDES (frozen, {calib['n_classes']} classes / "
          f"{calib['n_glyphs']} glyphs, {calib['learn_alphabets']}) ----")
    print(f"    shear_std      = {calib['shear_std']:.4f}")
    print(f"    rotation_std   = {calib['rotation_std']:.4f} rad "
          f"({np.degrees(calib['rotation_std']):.2f} deg)")
    print(f"    log_scale_std  = {calib['log_scale_std']:.4f}  "
          f"(REPORT-ONLY -- excluded from VARIANT_GRID, structural no-op under whole-figure "
          f"scale renormalization)")
    print(f"    pose_x_std / pose_y_std = {calib['pose_x_std']:.4f} / {calib['pose_y_std']:.4f}")
    print(f"    pose_o_std     = {calib['pose_o_std']:.4f} rad "
          f"({np.degrees(calib['pose_o_std']):.2f} deg)")
    print(f"    pose_s_std     = {calib['pose_s_std']:.4f}")
    engagement_note = ("engaged (non-trivial spread)" if min(
        calib["shear_std"], calib["rotation_std"], calib["pose_o_std"]) > 0.02
        else "STARVED -- within-class writer-dim variance is tiny, mechanism cannot fire")
    print(f"    ENGAGEMENT: {engagement_note}")

    print(f"\n  ---- MARGIN-SHIFT DIAGNOSTIC (true-vs-best-impostor margin, PASSED episodes "
          f"under GUARD, min-over-set vs original-only) ----")
    guard_pass_idx = [i for i in all_idx if guard_correct[i]]
    armx_extra_by_idx = {e["idx"]: e for e in armx["extra"]}
    deltas = []
    for i in guard_pass_idx:
        e = armx_extra_by_idx.get(i)
        if e is None or e["margin_min"] is None or e["margin_orig"] is None:
            continue
        deltas.append(e["margin_min"] - e["margin_orig"])
    if deltas:
        arr = np.array(deltas)
        print(f"    n={len(arr)}  mean(margin_min - margin_orig)={arr.mean():+.5f}  "
              f"median={np.median(arr):+.5f}  std={arr.std():.5f}")
        print(f"    {'TIGHTENS' if arr.mean() < 0 else 'WIDENS'} the margin on average "
              f"(negative = min-over-set margin is SMALLER than original-only -- dilution risk; "
              f"positive = min-over-set margin is LARGER -- the mechanism helps even on "
              f"already-correct episodes)")
        print(f"    fraction with a SMALLER (diluted) margin under min-over-set: "
              f"{100*np.mean(arr < 0):.1f}%")
    else:
        print("    no scored episodes with both margins available.")

    print(f"\n  ---- WALL CLOCK ----")
    print(f"    guard eval: {guard.get('wall_clock_seconds', float('nan')):.1f}s total "
          f"(n={n})")
    print(f"    armx  eval: {armx.get('wall_clock_seconds', float('nan')):.1f}s total "
          f"(n={n}, {armx.get('wall_clock_seconds', float('nan'))/n:.3f}s/episode)")
    return 0


# ===================================================================================================
# CLI.
# ===================================================================================================
def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["calibrate", "pilot", "guard", "armx", "report"])
    args = p.parse_args()
    return {
        "calibrate": stage_calibrate,
        "pilot": stage_pilot,
        "guard": stage_guard,
        "armx": stage_armx,
        "report": stage_report,
    }[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
