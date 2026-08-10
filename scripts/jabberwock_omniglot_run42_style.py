"""OMNIGLOT RUN 42, PHASE 1 -- EPISODE STYLE NORMALIZATION.

THE MECHANISM (see `domains/episode_style.py`'s own module docstring for the full estimator
derivation): every eval episode's 20 exemplars share ONE drawer (`ex_drawer`). That drawer's
STYLE -- shear/slant, aspect ratio, beyond what SC+TPS + the parse-marginal verdict already
absorb (translation + isotropic scale only, per `glyph_motor_world._normalize`'s own docstring:
"Slant / rotation / jitter survive -- that is the residual a 'hand' imposes") -- is estimable
from the drawer's OWN 20 glyphs but was never estimated before this run: each exemplar was
compared to the query raw. RUN 40 (commit 45dc2855) found exemplar-token badness drives mid+far
verdict errors. This run estimates the exemplar-drawer's style from its 20 glyphs, removes it
(canonicalizes the exemplars), and compares the query against canonical-form exemplars, on the
claim that canonical (population-typical) is on average CLOSER to an arbitrary other-drawer
query's style than the idiosyncratic exemplar-drawer style is (regression toward the mean).

PRE-REGISTERED ESTIMATOR (stated once here, matching `domains/episode_style.py` verbatim --
see that module for the full derivation and the exact-invariance proof this run relies on):
  - SHEAR:  Cov(x,y)/Var(y) on the run-36-normalized (center + abs-max), per-glyph pooled point
    cloud (`domains.episode_style.estimate_shear`).
  - ASPECT: 0.5*log(Var(y)/Var(x)) on the same normalized cloud
    (`domains.episode_style.estimate_aspect_log`).
  - CURVATURE BIAS (mean abs turn / arc length) is COMPUTED AND REPORTED but NOT applied --
    pre-registered here as report-only, per the launch brief's "report but only apply if
    pre-registered" clause; this run does not pre-register applying it.
  - Drawer-level style = the MEAN of the 20 per-glyph estimates (`episode_style.pool_style`) --
    a low-dimensional (2 free parameters), physically-meaningful nuisance-dimension correction,
    per the arc's own standing lesson that few-parameter corrections survive where high-
    dimensional fitting fragments (RUN 15's representation-grain corridor-exhaustion).
  - Query-side: the SAME per-glyph estimator applied to the query's OWN single glyph (noisier,
    unbiased -- `tests/test_episode_style_migrated.py::test_single_glyph_self_estimate_is_
    unbiased`). Query-side canonicalization IS ARM-SEPARATED (ARM E excludes it, ARM EQ
    includes it) -- this is the pre-registered arm design, not an afterthought.
  - Estimator constants (which normalization, which moment ratios) are FIXED a priori from the
    mechanism's own derivation, not calibrated against any eval outcome -- no background-
    alphabet calibration was needed (there is nothing to tune: the estimators have zero free
    hyperparameters beyond the choice of moment ratio itself, stated above).

ARMS (run-26 protocol: `scripts.jabberwock_omniglot_run25_number._block_spec`, POWER_SEED,
byte-identical block order -- alph OUTER, r INNER, 10 alphabets x R_TARGET=2 -> n=400):
  GUARD  -- unmodified full-dwell (`domains.abs_read.stage_parse_char` +
            `parse_marginal_verdict`, RUN 25's C0), 37C hygiene filter ON
            (`scripts.jabberwock_omniglot_run37c_hygiene.DropDegenerateFilter`), must reproduce
            80.5% / k=322 / n=400 EXACTLY (RUN 26's own standing control,
            `results/run26_checkpoints/eval_baseline.json`) -- this is also this run's GLOBAL
            comparator for the McNemar tests below (recomputed fresh under the SAME 37C-ON
            condition the arms use, rather than read from run26's own pre-37C cache, so the
            comparison is apples-to-apples on ingest hygiene too).
  ARM E  -- exemplar-side canonicalization only (37C ON).
  ARM EQ -- exemplar-side AND query-side canonicalization (37C ON).

PRIMARY ANALYSIS (pre-registered): paired McNemar (exact binomial on discordant pairs) per arm
vs GUARD/GLOBAL. PREDICTION (from RUN 40): fixes concentrate in the mid/far bands and in
episodes RUN 40 classified EXEMPLAR-OUTLIER / BOTH-OUTLIER
(`results/run40_checkpoints/classify.json`, read-only reference, joined by episode `idx` --
NOTE this file covers only 158/400 episodes, a stratified error+control sample, not all 400; the
enrichment check below is necessarily restricted to that 158-episode intersection and this
restriction is reported explicitly every time, per RUN 15's "eval-subset coverage is part of
every claim" standing rule). A win WITHOUT this enrichment is a DIFFERENT mechanism than
claimed and is reported as such, not silently accepted.

STOPS (pre-registered): if broken >= fixed in an arm, that arm HARMS -- stop it, do not retune
the estimator against the eval. If GUARD does not reproduce 322/400 exactly, STOP -- do not
trust any downstream number.

ALSO REPORTED (RUN 28's "report engagement separately from outcome" law): the style-parameter
distributions across the 20 eval blocks' drawers (how much style variance exists at all -- if
drawers are already near-canonical, a null outcome is EXPECTED and the mechanism is starved,
not falsified) alongside the per-band fixed/broken tables and Wilson-CI accuracies.

EXECUTION: staged + checkpointed (`--stage guard|arme|armeq|report`), state under
`results/run42_checkpoints/`. `results/run26_checkpoints/` and `results/run40_checkpoints/` are
READ-ONLY references (never written here). Each eval stage processes blocks up to a per-call
wall-clock budget and checkpoints after every block (re-invoke to continue). Every stage is one
blocking foreground call, never backgrounded. donkey=0 is not applicable (no torch anywhere in
this arc's dependency graph); no LLM call of any kind is made by this script.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run42_style.py --stage guard
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
from domains import episode_style as es
from domains import omniglot_world as ow

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run42_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")   # READ-ONLY reference.
RUN40_DIR = os.path.join(ROOT, "results", "run40_checkpoints")   # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

WAY = run25.WAY                                       # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET   # 20
R_TARGET = run25.R_TARGET                             # 2  -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS             # 10
POWER_SEED = run25.POWER_SEED                         # gate.SEED + 1500, byte-identical
GUARD_CONTROL = dict(acc=0.805, k=322, n=400)         # results/run26_checkpoints/eval_baseline.json

PER_CALL_BUDGET_SECONDS = 480.0                       # leaves >100s headroom under the 590s cap.

_ARMS = ("guard", "arme", "armeq")


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
    """alph OUTER, r INNER -- byte-identical order to run25/run26's own eval block order, so
    `idx = block_idx * 20 + qi` lines up with `results/run26_checkpoints/eval_baseline.json`
    and `results/run40_checkpoints/classify.json`'s own `idx` convention."""
    test_alphabets = _test_alphabets()
    return [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]


# ===================================================================================================
# ONE block's worth of work: style estimate (if applicable) + candidate staging + 20 verdicts.
# ===================================================================================================
def _block_style(drawer_files: list, ex_drawer: int, queries: list, arm: str) -> tuple:
    """Returns (style_by_path, style_report). `style_by_path` feeds `episode_style.
    StyleCanonFilter` directly. Mechanical only -- reads (`ow.load_strokes`, already 37C-
    filtered by the caller's own `DropDegenerateFilter` context) + a pooled mean, no decision."""
    style_by_path: dict = {}
    style_report = dict(drawer_style=None, per_exemplar_style=None, query_style_by_qi=None)
    if arm in ("arme", "armeq"):
        ex_paths = [drawer_files[ci][ex_drawer] for ci in range(WAY)]
        ex_styles = [es.style_for_path(p) for p in ex_paths]
        drawer_style = es.pool_style(ex_styles)
        style_report["drawer_style"] = drawer_style
        style_report["per_exemplar_style"] = ex_styles
        for p in ex_paths:
            style_by_path[p] = drawer_style
    if arm == "armeq":
        qstyles = {}
        for qi, q_drawer in queries:
            qpath = drawer_files[qi][q_drawer]
            q_style = es.style_for_path(qpath)
            qstyles[qi] = q_style
            style_by_path[qpath] = q_style
        style_report["query_style_by_qi"] = qstyles
    return style_by_path, style_report


def _run_block(alph: str, r: int, spec: dict, arm: str) -> tuple:
    drawer_files, ex_drawer, queries = spec["drawer_files"], spec["ex_drawer"], spec["queries"]
    style_by_path, style_report = _block_style(drawer_files, ex_drawer, queries, arm)

    recs = []
    with es.StyleCanonFilter(style_by_path):
        scratch0 = srs.Substrate()
        _, cand0 = run25._stage_candidates(scratch0, drawer_files, ex_drawer, WAY,
                                            thetas=ar.DEFAULT_PARSE_THETAS)
        for qi, q_drawer in queries:
            path = drawer_files[qi][q_drawer]
            qn0 = ar.stage_parse_char(scratch0, path, is_query=True,
                                       thetas=ar.DEFAULT_PARSE_THETAS)
            w0 = ar.parse_marginal_verdict(scratch0, qn0)
            pred = cand0.get(w0, -1) if w0 is not None else -1
            recs.append(dict(true=qi, alph=alph, r=r, pred_full=pred,
                              correct=bool(pred == qi)))
    return recs, style_report


# ===================================================================================================
# STAGE: eval -- one of guard / arme / armeq, checkpointed per block, resumable.
# ===================================================================================================
def stage_eval(arm: str) -> int:
    assert arm in _ARMS
    print(f"\n{SEP}\n  STAGE: eval-{arm}\n{SEP}")
    out_path = _ckpt(f"eval_{arm}.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_styles=[], block_idx=0, done=False)

    if state.get("done"):
        print(f"  eval-{arm} already COMPLETE (n={len(state['records'])}).")
        return 0

    blocks = _blocks()
    print(f"  arm={arm}  blocks={len(blocks)} (target n={len(blocks) * WAY})  "
          f"resuming at block {state['block_idx']}  [37C hygiene filter: ON]")

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        alph, r = blocks[i]
        run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    with DropDegenerateFilter():
        while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
            alph, r = blocks[state["block_idx"]]
            spec = run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)
            recs, style_report = _run_block(alph, r, spec, arm)
            for pos, rec in enumerate(recs):
                rec["idx"] = state["block_idx"] * WAY + pos
            state["records"].extend(recs)
            state["block_styles"].append(dict(block_idx=state["block_idx"], alph=alph, r=r,
                                               ex_drawer=spec["ex_drawer"], **style_report))
            state["block_idx"] += 1
            _save_json(state, out_path)
            print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
                  f"{len(state['records'])} episodes so far, {time.time() - t0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        k = sum(1 for rec in state["records"] if rec["correct"])
        n = len(state["records"])
        ci = _wilson(k, n)
        state["acc"] = dict(acc=k / n, ci=list(ci), k=k, n=n)
        _save_json(state, out_path)
        print(f"\n  EVAL COMPLETE for {arm}: n={n}  acc={100*k/n:.1f}%  "
              f"95% CI [{100*ci[0]:.1f}%, {100*ci[1]:.1f}%]  k={k}")
        if arm == "guard":
            ok = (k == GUARD_CONTROL["k"] and n == GUARD_CONTROL["n"])
            print(f"  GUARD vs standing control (acc={100*GUARD_CONTROL['acc']:.1f}%, "
                  f"k={GUARD_CONTROL['k']}, n={GUARD_CONTROL['n']}): "
                  f"{'PASS -- reproduced exactly' if ok else 'FAIL -- STOP, do not trust downstream'}")
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-invoke to continue.")
    return 0


# ===================================================================================================
# STAGE: report -- McNemar per arm vs GUARD, run-40 enrichment join, style-variance/engagement,
# per-band tables, accuracies + CIs.
# ===================================================================================================
def _require(arm: str) -> dict:
    p = _ckpt(f"eval_{arm}.json")
    if not os.path.exists(p):
        print(f"  WALL: run --stage {arm} to completion first.")
        sys.exit(1)
    d = _load_json(p)
    if not d.get("done"):
        print(f"  WALL: eval-{arm} not yet COMPLETE ({d['block_idx']}/20 blocks) -- resume it first.")
        sys.exit(1)
    return d


def _mcnemar(base_correct: list, arm_correct: list) -> dict:
    fixed = sum(1 for b, a in zip(base_correct, arm_correct) if (not b) and a)
    broken = sum(1 for b, a in zip(base_correct, arm_correct) if b and (not a))
    n_disc = fixed + broken
    p = float(binomtest(fixed, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    return dict(fixed=fixed, broken=broken, discordant=n_disc, p=p)


def _band_for_idx(classify_rows_by_idx: dict, idx: int):
    row = classify_rows_by_idx.get(idx)
    return row["band"] if row else None


def _enrichment(classify_rows_by_idx: dict, fixed_idx: set, broken_idx: set,
                 all_scored_idx: list, target_labels=("EXEMPLAR-OUTLIER", "BOTH-OUTLIER")) -> dict:
    """RUN 40 enrichment check: among the episodes THIS run's arm FIXED (guard-wrong ->
    arm-right) that are also present in `run40_checkpoints/classify.json` (idx-joined, 158/400
    coverage), what fraction carry an EXEMPLAR-OUTLIER/BOTH-OUTLIER `diagnosis_adjusted` label,
    vs the base rate of that label across ALL classify.json rows this arm touched at all
    (scored_and_classified)? A fixed-rate enrichment over the base rate supports the claimed
    mechanism; no enrichment means a real accuracy change (if any) has a DIFFERENT cause."""
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
    guard = _require("guard")
    n = len(guard["records"])
    guard_correct = [None] * n
    for rec in guard["records"]:
        guard_correct[rec["idx"]] = rec["correct"]

    classify_path = os.path.join(RUN40_DIR, "classify.json")
    classify = _load_json(classify_path) if os.path.exists(classify_path) else {"rows": []}
    classify_rows_by_idx = {row["idx"]: row for row in classify["rows"]}
    print(f"  run40 classify.json: {len(classify_rows_by_idx)} idx-labelled episodes "
          f"(READ-ONLY reference, {classify_path})")

    for arm in ("arme", "armeq"):
        d = _require(arm)
        arm_correct = [None] * n
        for rec in d["records"]:
            arm_correct[rec["idx"]] = rec["correct"]
        all_idx = list(range(n))

        mc = _mcnemar(guard_correct, arm_correct)
        fixed_idx = {i for i in all_idx if (not guard_correct[i]) and arm_correct[i]}
        broken_idx = {i for i in all_idx if guard_correct[i] and (not arm_correct[i])}
        enrich = _enrichment(classify_rows_by_idx, fixed_idx, broken_idx, all_idx)

        k_arm = sum(1 for c in arm_correct if c)
        ci_arm = _wilson(k_arm, n)

        print(f"\n  ---- ARM {arm.upper()} vs GUARD/GLOBAL ----")
        print(f"    accuracy: {100*k_arm/n:.1f}% [{100*ci_arm[0]:.1f}, {100*ci_arm[1]:.1f}]  "
              f"k={k_arm}/{n}   (guard: {100*sum(guard_correct)/n:.1f}% k={sum(guard_correct)}/{n})")
        print(f"    McNemar: fixed={mc['fixed']}  broken={mc['broken']}  "
              f"discordant={mc['discordant']}  p={mc['p']:.4g}   "
              f"{'ARM HARMS -- STOP' if mc['broken'] >= mc['fixed'] and mc['discordant'] else 'ok'}")
        print(f"    RUN-40 ENRICHMENT (idx-joined, {enrich['base_n']}/400 episodes have a "
              f"run-40 label):")
        print(f"      base rate of EXEMPLAR-OUTLIER/BOTH-OUTLIER among all joined episodes: "
              f"{enrich['base_hits']}/{enrich['base_n']} = {100*enrich['base_rate']:.1f}%")
        print(f"      among FIXED episodes (joined n={enrich['fixed_n']}): "
              f"{enrich['fixed_hits']}/{enrich['fixed_n']} = "
              f"{100*enrich['fixed_rate'] if enrich['fixed_n'] else float('nan'):.1f}%")
        print(f"      among BROKEN episodes (joined n={enrich['broken_n']}): "
              f"{enrich['broken_hits']}/{enrich['broken_n']} = "
              f"{100*enrich['broken_rate'] if enrich['broken_n'] else float('nan'):.1f}%")

        # Per-band table (restricted to the 158-episode classify.json sample -- stated).
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
        print(f"    per-band fixed/broken/unchanged (RESTRICTED to the {len(classify_rows_by_idx)}"
              f"/400 run-40-classified episodes):")
        for band in ("near", "mid", "far", "control"):
            c = band_counts.get(band, Counter())
            print(f"      {band:<8} fixed={c['fixed']:<3} broken={c['broken']:<3} "
                  f"unchanged={c['unchanged']:<3}")

        # Style engagement (run-28 law: report engagement separately from outcome).
        drawer_styles = [b["drawer_style"] for b in d["block_styles"] if b.get("drawer_style")]
        shears = [s["shear"] for s in drawer_styles]
        aspects = [s["aspect_log"] for s in drawer_styles]
        curvs = [s["curvature_bias"] for s in drawer_styles]
        ex_drawers = [b["ex_drawer"] for b in d["block_styles"]]
        print(f"    STYLE ENGAGEMENT ({len(drawer_styles)} blocks, "
              f"{len(set(ex_drawers))}/{len(ex_drawers)} distinct ex_drawer indices):")
        print(f"      drawer shear:       mean={np.mean(shears):+.4f}  std={np.std(shears):.4f}  "
              f"range=[{min(shears):+.4f}, {max(shears):+.4f}]")
        print(f"      drawer aspect_log:  mean={np.mean(aspects):+.4f}  std={np.std(aspects):.4f}  "
              f"range=[{min(aspects):+.4f}, {max(aspects):+.4f}]")
        print(f"      drawer curv. bias (report-only): mean={np.mean(curvs):.4f}  "
              f"std={np.std(curvs):.4f}")

        if arm == "armeq":
            qshears, qaspects = [], []
            for b in d["block_styles"]:
                for qi, qs in (b.get("query_style_by_qi") or {}).items():
                    qshears.append(qs["shear"])
                    qaspects.append(qs["aspect_log"])
            print(f"      query (self) shear:      mean={np.mean(qshears):+.4f}  "
                  f"std={np.std(qshears):.4f}  n={len(qshears)}")
            print(f"      query (self) aspect_log: mean={np.mean(qaspects):+.4f}  "
                  f"std={np.std(qaspects):.4f}  n={len(qaspects)}")

    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["guard", "arme", "armeq", "report"])
    args = p.parse_args()
    if args.stage in ("guard", "arme", "armeq"):
        rc = stage_eval(args.stage)
    else:
        rc = stage_report()
    assert "torch" not in sys.modules, "donkey!=0 -- torch imported somewhere"
    sys.exit(rc)


if __name__ == "__main__":
    main()
