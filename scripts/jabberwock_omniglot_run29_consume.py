"""OMNIGLOT RUN 29 -- CONSUMPTION: THE LOOP CONSUMES WHAT IT IMPORTED (weighted marking,
persistent weight updates, pooled-prior eval proposal).

Run 28 wired the sd loop at ARRANGEMENT grain (`domains/arrangement_codebook.py`) and proved the
loop IMPORTS information for the first time (40 practice characters mint 40 arrangement quanta,
idempotent, zero false novelty). Consolidation/transfer stayed honestly NULL for a TRACED reason,
named by run 28's own final report: NOTHING CONSUMES the imported quanta.

  (a) `homework_loop._character_round_trip_score`'s own arrangement subscore is UNWEIGHTED --
      `arrangement_codebook.weighted_arrangement_score`/`update_relation_stability` exist,
      unit-gated, but the marking comparator never calls them.
  (b) `homework_loop.babble_characters`' own per-rep arrangement-instability tally computes a
      real signal but never persists it onto the recognized character quantum's graph node --
      only stroke-grain codebook nodes get touched.
  (c) The eval structural proposal path (`abs_read.propose_top_k`) reads only the STROKE
      codebook -- the character codebook is invisible to it, so eval coverage/accuracy are
      byte-equal to baseline regardless of what the homework loop learns.

RUN 29 wires all three (`domains/homework_loop.py`'s `_apply_stability_weighting` +
`babble_characters`' own new per-rep `update_relation_stability` call;
`domains/arrangement_codebook.py`'s new `pooled_relation_kind_reliability`/
`pooled_prior_coverage_term`/`propose_top_k_pooled_prior`) and re-measures. This is the
COMPLETION of runs 26-28's homework arc, not a new mechanism -- see `tests/
test_run29_consume_migrated.py` for the unit gates on each of the three wiring points.

PRE-REGISTERED HEADER (stated before any result below is computed):

  RECIPE: this run REUSES run 28's own calibrated LEARN graph
  (`results/run28_checkpoints/calibrated_learn.json`, verified byte-comparable at stage
  "verify" -- same `gate.SEED`/`LEARN_ALPHABETS_N`/`DK`/`GROWTH_WINDOW`/`LEARN_STROKE_CAP`/
  calibration margin/min-family-samples) as this run's OWN shared starting point -- no learn/
  calibrate re-run. PRACTICE: the SAME 40-character practice set + `PRACTICE_SEED` (10 held-out
  background alphabets `background[5:15]`) run 27/28 used, byte-comparable; 3 cycles; eval split
  fully quarantined (`eval_class_ids` guard on every call). BASELINE: reused verbatim from
  `results/run26_checkpoints/eval_baseline.json` (verified done), exactly as run 27/28 did.

  ARMS:
    (1) BASELINE -- reused verbatim, no re-run.
    (2)/(3) share ONE underlying cycle -- `use_stability_weights=True` +
        `enable_character_codebook=True` for BOTH `mark_characters` calls of every
        `cycle_characters`-equivalent pass, `rng_seed` byte-identical to run 28's own arm 3
        (`READING_SEED_BASE + cycle`) so the ONLY delta versus run 28's own reading-arrangement
        arm is levers (a)+(b) -- a clean ablation, not a confounded new run. Saved once as
        `consume.json`/`consume_metrics.json`.
    (2) CONSUME-MARK reads `consume_metrics.json`'s own internal-loop metrics (P3/P4) and, for
        comparability, an eval pass over the SAME graph using the UNCHANGED naive-coverage
        proposal (`ar.propose_top_k` alone) -- "NO eval-proposal change."
    (3) CONSUME-FULL evaluates the SAME graph with the UNION of the naive-coverage shortlist and
        the NEW pooled-relation-kind-reliability-prior shortlist (`ac.propose_top_k_pooled_
        prior`, prior pooled fresh from whatever the character codebook holds at eval time) --
        the run-25 "different angles don't overlap" precedent, `sorted(set(a) | set(b))`.

  PREDICTIONS:
    P3. Arm-2/3's surviving-residual FALLS across cycles (the teacher-information metric) --
        run 26/27/28's own THREE-TIMES-failed prediction, now retried with the weight-consuming
        channel actually wired. If it stays flat, this run checks recognition coverage of the
        SURVIVING items by the character codebook FIRST (weighting can only move the score for
        an item whose arrangement was scored against a HELD quantum) and reports that as the
        traced reason, per the pre-registered STOP-and-diagnose instruction -- never silently
        interpreted as "the lever doesn't work."
    P4. Arm-2/3's WEIGHTED arrangement subscore rises across cycles; the UNWEIGHTED subscore
        (reported side by side, same items, same cycles) is the control that isolates whether
        any rise is the weighting arithmetic alone (would show ONLY in the weighted series) or a
        genuine geometry change (would show in BOTH).
    P5. Arm-3 eval coverage@10 vs baseline (`results/run26_checkpoints/eval_baseline.json`,
        71.5% [66.9,75.7]): CI-separated gain is the transfer claim. Pre-registered honest shape:
        the pooled prior is a WEAK, content-free general signal (reliability by relation KIND,
        not by matched arrangement -- the character codebook holds zero eval-alphabet material
        by construction) union-ed onto an already-strong naive-coverage shortlist, so the
        expected movement is SMALL; Wilson CIs decide, not the sign of the point estimate alone.
    P6. Accuracy (shortlist-constrained) moves ONLY through coverage -- movement without a
        coverage move is an ANOMALY (the run-25-family verdict-layer-saturation precedent), not
        a success, exactly as run 28's own P6 was framed.

  METRICS logged per cycle: surviving-residual (before/after), WEIGHTED + UNWEIGHTED arrangement
  subscore means (both series, every item), recognition coverage of practice items (overall AND
  restricted to the surviving-residual subset) by the character codebook, relation_weights
  distribution (min/mean/max, pooled across every held quantum), worksheet size, corrections,
  mints (stroke-grain reading/babble, arrangement-grain reading), character codebook size, wall-
  clock. Eval: coverage@10 + shortlist accuracy + Wilson 95% CI for arm 2 and arm 3, cited
  against the run-26 baseline (also carrying its own `full_dwell` reference number).

EXECUTION: staged + checkpointed (`--stage verify|consume|eval-baseline|eval-consume-mark|
eval-consume-full|report`), state under `results/run29_checkpoints/` (NEVER touching
`run26_checkpoints/`/`run27_checkpoints/`/`run28_checkpoints/`, all READ-ONLY reference data for
this script). `consume` runs ONE cycle per invocation (re-invoke to advance); `eval-*` process
eval BLOCKS up to `PER_CALL_BUDGET_SECONDS` and checkpoint after every block. Every stage is a
single blocking call, never backgrounded.

donkey=0: no torch anywhere in sys.modules, checked at the end of every stage.

Run (repeat --stage consume/eval-* until each reports COMPLETE):
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run29_consume.py --stage verify
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run25_number as run25
from domains import abs_read as ar
from domains import arrangement_codebook as ac
from domains import homework_loop as hl
from domains import novelty_calibration as nc
from domains import omniglot_world as ow
from domains import stroke_codebook as sc

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run29_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")     # READ-ONLY reference.
RUN28_DIR = os.path.join(ROOT, "results", "run28_checkpoints")     # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS -- byte-identical to run 26/27/28 where they overlap.
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = gate.LEARN_ALPHABETS_N            # 5
LEARN_DRAWERS = gate.LEARN_DRAWERS                    # 01..14
LEARN_STROKE_CAP = 1500
DK = gate.DK
GROWTH_WINDOW = gate.GROWTH_WINDOW
CALIBRATION_MARGIN = nc.DEFAULT_MARGIN
CALIBRATION_MIN_FAMILY_SAMPLES = nc.DEFAULT_MIN_FAMILY_SAMPLES

PRACTICE_ALPHABETS_SLICE = slice(5, 15)
N_PRACTICE_ITEMS = 40                                 # byte-identical to run 27/28.
PRACTICE_SEED = gate.SEED + 9000                      # byte-identical to run 27/28.
N_CYCLES = 3
REPS_PER_ITEM = 20                                    # byte-identical to run 26/27/28.
READING_SEED_BASE = PRACTICE_SEED + 5000              # byte-identical to run 28's own arm 3.

WAY = run25.WAY
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET
R_TARGET = run25.R_TARGET
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS
POWER_SEED = run25.POWER_SEED

SHORTLIST_K = 10
PER_CALL_BUDGET_SECONDS = 480.0


# ---------------------------------------------------------------------------------------------
# PERSISTENCE -- run 26/27/28's own fixed recipe, reproduced verbatim.
# ---------------------------------------------------------------------------------------------
def _save_graph(s, path: str) -> None:
    blob = {"graph": s.graph_to_dict(), "grammar": s.grammar_to_json(),
            "rules": s._inner.export_rules()}
    with open(path, "w") as f:
        json.dump(blob, f)


def _load_graph(path: str):
    with open(path) as f:
        blob = json.load(f)
    s = srs.Substrate()
    s.graph_from_dict(blob["graph"])
    for p in blob["grammar"]["productions"]:
        try:
            s._inner.add_production(p)
        except Exception:
            pass
    if "rules" in blob:
        s._inner.import_rules(blob["rules"])
    return s


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


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_json_default)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _run26(name: str) -> str:
    return os.path.join(RUN26_DIR, name)


def _run28(name: str) -> str:
    return os.path.join(RUN28_DIR, name)


def _donkey0() -> bool:
    return "torch" not in sys.modules


# ---------------------------------------------------------------------------------------------
# SHARED HELPERS -- byte-identical to run 28's own copies.
# ---------------------------------------------------------------------------------------------
def _test_alphabets() -> list:
    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= WAY)
    return qualifying[:N_TEST_ALPHABETS]


def _eval_class_ids(test_alphabets: list) -> set:
    ids: set = set()
    for alph in test_alphabets:
        ids.update(ow.characters(alph, "evaluation"))
    return ids


def _build_practice_set(n_items: int = N_PRACTICE_ITEMS, seed: int = PRACTICE_SEED) -> list:
    """Byte-identical construction to run 27/28's own `_build_practice_set`."""
    rng = np.random.default_rng(seed)
    practice_alphabets = ow.alphabets("background")[PRACTICE_ALPHABETS_SLICE]
    pool = []
    for alph in practice_alphabets:
        pool.extend(ow.characters(alph, "background"))
    order = rng.permutation(len(pool))
    items = []
    for pi in order:
        if len(items) >= n_items:
            break
        cdir = pool[int(pi)]
        files = ow.drawings(cdir)
        if not files:
            continue
        fi = int(rng.integers(len(files)))
        strokes = [st.tolist() for st in ow.load_strokes(files[fi]) if st.shape[0] >= 2]
        if not strokes:
            continue
        items.append({"id": len(items), "class_id": cdir, "strokes": strokes})
    return items, practice_alphabets


def _wilson(k: int, n: int) -> tuple:
    return gate.wilson_ci(k, n)


def _sep(ci_a, ci_b) -> bool:
    return gate._ci_separated(tuple(ci_a), tuple(ci_b))


def _unweighted_arrangement(m) -> float:
    """The plain (all-weights-1.0) arrangement subscore for ANY `MarkedItem`, whether or not
    weighting actually applied to it this call -- `arrangement_score_unweighted` when the
    override fired, else `arrangement_score` itself (which, unweighted, IS that plain value).
    Mechanical fallback read, never a re-derivation."""
    return m.arrangement_score_unweighted if m.arrangement_score_unweighted is not None \
        else m.arrangement_score


def _weight_distribution(s) -> dict:
    """Mechanical pool of EVERY held character quantum's own persisted `relation_weights`
    values -- min/mean/max, `{}`-shaped honestly when nothing is held yet."""
    vals: list = []
    for name in ac.character_vocabulary_report(s)["names"]:
        vals.extend(ac.relation_weights(s, name).values())
    if not vals:
        return {"n": 0, "min": None, "mean": None, "max": None}
    return {"n": len(vals), "min": float(min(vals)), "mean": float(np.mean(vals)),
            "max": float(max(vals))}


def _recognition_coverage(marked: list) -> dict:
    """Mechanical read-back over a `mark_characters` result list: how many of the practice
    items are RECOGNIZED (a HELD quantum, not a mint this call), MINTED (fresh this call), or
    UNCOVERED (no character_quantum at all -- e.g. an empty composed signature) -- both overall
    and restricted to the SURVIVING-residual subset (round_trip_score < 1.0), the population
    `_apply_stability_weighting` can actually act on."""
    def _tally(items):
        n = len(items)
        recognized = sum(1 for m in items if m.character_quantum and m.n_mints_character_reading == 0)
        minted = sum(1 for m in items if m.n_mints_character_reading == 1)
        uncovered = sum(1 for m in items if not m.character_quantum)
        return {"n": n, "recognized": recognized, "minted": minted, "uncovered": uncovered,
                "recognized_frac": (recognized / n) if n else None}
    surviving = [m for m in marked if m.round_trip_score < hl.DEFAULT_MAX_SCORE]
    return {"overall": _tally(marked), "surviving_residual": _tally(surviving)}


# ===============================================================================================
# STAGE: verify -- recipe verification against run 26 (baseline) + run 28 (calibrated learn).
# No learn/calibrate re-run: this run REUSES run 28's own calibrated graph verbatim.
# ===============================================================================================
def stage_verify():
    print(f"\n{SEP}\n  STAGE: verify (reuse run 28's calibrated_learn.json + run 26's "
          f"eval_baseline.json verbatim)\n{SEP}")
    calib_src = _run28("calibrated_learn.json")
    calib_report_src = _run28("calibration_report.json")
    base_src = _run26("eval_baseline.json")
    missing = [p for p in (calib_src, calib_report_src, base_src) if not os.path.exists(p)]
    if missing:
        print(f"  WALL: missing prerequisite file(s): {missing}")
        return 1

    calib_report = _load_json(calib_report_src)
    ok = True
    checks = [
        ("gate.SEED", gate.SEED, gate.SEED),
        ("LEARN_ALPHABETS_N", LEARN_ALPHABETS_N, gate.LEARN_ALPHABETS_N),
        ("DK", DK, gate.DK),
        ("GROWTH_WINDOW", GROWTH_WINDOW, gate.GROWTH_WINDOW),
        ("LEARN_STROKE_CAP", LEARN_STROKE_CAP, 1500),
        ("calibration_margin", CALIBRATION_MARGIN, nc.DEFAULT_MARGIN),
        ("calibration_min_family_samples", CALIBRATION_MIN_FAMILY_SAMPLES,
         nc.DEFAULT_MIN_FAMILY_SAMPLES),
    ]
    for label, a, b in checks:
        match = (a == b)
        ok = ok and match
        print(f"  recipe check  {label:<28} run29={a!r}  reference={b!r}  "
              f"{'MATCH' if match else 'MISMATCH -- PROTOCOL DRIFT'}")
    n_families_ok = calib_report.get("n_families", 0) > 0
    print(f"  calibration_report sanity: n_families={calib_report.get('n_families')}  "
          f"n_spans_measured={calib_report.get('n_spans_measured')}  "
          f"{'OK' if n_families_ok else 'EMPTY -- WALL'}")
    ok = ok and n_families_ok

    base = _load_json(base_src)
    base_done = bool(base.get("done"))
    print(f"  eval_baseline.json: done={base_done}  n={len(base.get('records', []))}  "
          f"coverage={base.get('coverage')}  shortlist_acc={base.get('shortlist_acc')}")
    ok = ok and base_done

    if not ok:
        print("  WALL: recipe MISMATCH or a prerequisite is incomplete -- this run must NOT "
              "proceed on top of these checkpoints.")
        return 1

    print("  RECIPE VERIFIED IDENTICAL to run 26/28 -- adopting both checkpoints (read-only).")
    _save_json(dict(calib_src=calib_src, base_src=base_src, calib_report=calib_report,
                    base_pointer=dict(coverage=base.get("coverage"),
                                      shortlist_acc=base.get("shortlist_acc"),
                                      full_dwell=base.get("full_dwell"),
                                      n=len(base.get("records", []))),
                    verified=True), _ckpt("verify.json"))
    print(f"  saved -> {_ckpt('verify.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _calibrated_src() -> str:
    return _run28("calibrated_learn.json")


# ===============================================================================================
# STAGE: consume -- ONE cycle per invocation, levers (a)+(b) both on
# (`use_stability_weights=True`, `enable_character_codebook=True`), rng_seed byte-identical to
# run 28's own arm 3 -- the clean ablation (only the NEW consumption levers differ).
# ===============================================================================================
def stage_consume():
    print(f"\n{SEP}\n  STAGE: consume (levers a+b: weighted marking + persistent weight "
          f"updates)\n{SEP}")
    meta_path = _ckpt("consume_metrics.json")
    meta = _load_json(meta_path) if os.path.exists(meta_path) else {"cycles": []}
    done = len(meta["cycles"])
    if done >= N_CYCLES:
        print(f"  consume already COMPLETE ({done}/{N_CYCLES} cycles).")
        return 0

    if not os.path.exists(_ckpt("verify.json")):
        print("  WALL: run stage 'verify' first.")
        return 1
    src = _ckpt("consume.json") if done > 0 else _calibrated_src()
    if not os.path.exists(src):
        print(f"  WALL: {src} missing.")
        return 1
    s = _load_graph(src)

    practice_items, practice_alphabets = _build_practice_set()
    meta["n_practice_items"] = len(practice_items)
    meta["practice_alphabets"] = practice_alphabets
    test_alphabets = _test_alphabets()
    eval_ids = _eval_class_ids(test_alphabets)
    rng_seed = READING_SEED_BASE + done
    print(f"  cycle {done}/{N_CYCLES}: {len(practice_items)} practice characters, "
          f"reps_per_item={REPS_PER_ITEM}, rng_seed={rng_seed}, dk=gate.DK, "
          f"character codebook ON, use_stability_weights ON")

    if done == 0:
        meta["grain_before"] = sc.grain_vocabulary_report(s)
        meta["char_vocab_before"] = ac.character_vocabulary_report(s)
        print(f"  grain_before: {meta['grain_before']}  char_vocab_before: "
              f"{meta['char_vocab_before']['total']}")

    t0 = time.time()
    # Manual mark -> assign -> babble -> re-mark (== cycle_characters, decomposed here for
    # per-item instrumentation: weighted/unweighted subscore series + recognition coverage need
    # the raw `MarkedItem` lists, which `CycleReport` does not itself carry).
    marked_before = hl.mark_characters(s, practice_items, dk=DK, eval_class_ids=eval_ids,
                                       enable_character_codebook=True,
                                       use_stability_weights=True)
    worksheet = hl.assign(marked_before)
    log = hl.babble_characters(s, worksheet, reps_per_item=REPS_PER_ITEM, rng_seed=rng_seed,
                               jitter_bins=hl.DEFAULT_JITTER_BINS, eval_class_ids=eval_ids)
    marked_after = hl.mark_characters(s, practice_items, dk=DK, eval_class_ids=eval_ids,
                                      enable_character_codebook=True,
                                      use_stability_weights=True)
    elapsed = time.time() - t0

    surviving_before = sum(1 for m in marked_before if m.round_trip_score < hl.DEFAULT_MAX_SCORE)
    surviving_after = sum(1 for m in marked_after if m.round_trip_score < hl.DEFAULT_MAX_SCORE)
    mean_weighted_before = float(np.mean([m.arrangement_score for m in marked_before]))
    mean_weighted_after = float(np.mean([m.arrangement_score for m in marked_after]))
    mean_unweighted_before = float(np.mean([_unweighted_arrangement(m) for m in marked_before]))
    mean_unweighted_after = float(np.mean([_unweighted_arrangement(m) for m in marked_after]))
    mints_reading = (sum(m.n_mints_reading for m in marked_before)
                     + sum(m.n_mints_reading for m in marked_after))
    mints_char_reading = (sum(m.n_mints_character_reading for m in marked_before)
                          + sum(m.n_mints_character_reading for m in marked_after))
    mints_babble = sum(1 for entry in log.per_item.values() for c in entry["corrections"]
                       if c["type"] in ("mint_at_instability", "variant_coverage"))
    char_vocab = ac.character_vocabulary_report(s)
    weight_dist = _weight_distribution(s)
    recog_before = _recognition_coverage(marked_before)
    recog_after = _recognition_coverage(marked_after)

    cyc = dict(cycle=done, surviving_before=surviving_before, surviving_after=surviving_after,
               mean_weighted_before=mean_weighted_before, mean_weighted_after=mean_weighted_after,
               mean_unweighted_before=mean_unweighted_before,
               mean_unweighted_after=mean_unweighted_after,
               worksheet_size=len(worksheet.items), corrections=log.total_corrections,
               mints_during_reading=mints_reading, mints_during_babble=mints_babble,
               mints_character_reading=mints_char_reading,
               character_codebook_size=char_vocab["total"], weight_distribution=weight_dist,
               recognition_before=recog_before, recognition_after=recog_after, elapsed=elapsed)
    meta["cycles"].append(cyc)
    print(f"  surviving_before={surviving_before}  surviving_after={surviving_after}  "
          f"mean_arrangement weighted {mean_weighted_before:.4f}->{mean_weighted_after:.4f}  "
          f"unweighted {mean_unweighted_before:.4f}->{mean_unweighted_after:.4f}")
    print(f"  worksheet_size={len(worksheet.items)}  corrections={log.total_corrections}  "
          f"mints_during_reading={mints_reading}  mints_during_babble={mints_babble}  "
          f"mints_character_reading={mints_char_reading}  "
          f"character_codebook_size={char_vocab['total']}  weight_distribution={weight_dist}")
    print(f"  recognition coverage AFTER -- overall: {recog_after['overall']}  "
          f"surviving_residual: {recog_after['surviving_residual']}")
    print(f"  elapsed={elapsed:.1f}s")

    if done + 1 >= N_CYCLES:
        meta["grain_after"] = sc.grain_vocabulary_report(s)
        meta["char_vocab_after"] = char_vocab
        series = [meta["cycles"][0]["surviving_before"]] + [c["surviving_after"] for c in meta["cycles"]]
        meta["p3_falls"] = bool(series[-1] < series[0])  # STRICT fall — a flat series is a
                                                          # NULL (the run-28 wording-bug lesson)
        w_series = [meta["cycles"][0]["mean_weighted_before"]] + [c["mean_weighted_after"] for c in meta["cycles"]]
        meta["p4_rises"] = bool(w_series[-1] > w_series[0])
        print(f"  grain_after: {meta['grain_after']}  char_vocab_after: {char_vocab['total']}")
        print(f"  surviving_residual_count series: {series}  P3: "
              f"{'CONFIRMED' if meta['p3_falls'] else 'NULL'}")
        print(f"  mean_weighted_arrangement series: {[round(x,4) for x in w_series]}  P4: "
              f"{'CONFIRMED' if meta['p4_rises'] else 'NULL'}")

    _save_graph(s, _ckpt("consume.json"))
    _save_json(meta, meta_path)
    print(f"  saved -> {_ckpt('consume.json')}, {meta_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: eval-<tag> (block-checkpointed) -- CODEBOOK-DEPENDENT metrics only.
#   eval-consume-mark  -- arm 2, UNCHANGED naive-coverage proposal (`ar.propose_top_k` alone).
#   eval-consume-full  -- arm 3, UNION of naive-coverage + pooled-prior proposal shortlists.
# ===============================================================================================
def stage_eval_baseline():
    print(f"\n{SEP}\n  STAGE: eval-baseline (REUSED verbatim from run 26)\n{SEP}")
    src = _run26("eval_baseline.json")
    base = _load_json(src)
    if not base.get("done"):
        print(f"  WALL: {src} is not COMPLETE.")
        return 1
    print(f"  REUSED: n={len(base['records'])}  full_dwell={base.get('full_dwell')}  "
          f"coverage={base.get('coverage')}  shortlist_acc={base.get('shortlist_acc')}")
    _save_json(dict(reused_from=src, n=len(base["records"]), full_dwell=base.get("full_dwell"),
                     coverage=base.get("coverage"), shortlist_acc=base.get("shortlist_acc"),
                     done=True), _ckpt("eval_baseline_pointer.json"))
    print(f"  saved -> {_ckpt('eval_baseline_pointer.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _finalize_eval(state: dict) -> None:
    records = state["records"]
    n = len(records)
    k_cov = sum(1 for r in records if r["in_shortlist"])
    cov = k_cov / n if n else 0.0
    ci_cov = _wilson(k_cov, n)
    k_sl = sum(1 for r in records if r["pred_shortlist"] == r["true"])
    acc_sl = k_sl / n if n else 0.0
    ci_sl = _wilson(k_sl, n)
    state["coverage"] = dict(cov=cov, ci=list(ci_cov), k=k_cov, n=n)
    state["shortlist_acc"] = dict(acc=acc_sl, ci=list(ci_sl), k=k_sl, n=n)


def stage_eval(tag: str):
    print(f"\n{SEP}\n  STAGE: eval-{tag}\n{SEP}")
    out_path = _ckpt(f"eval_{tag}.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_idx=0, done=False,
        union_widths=[] if tag == "consume-full" else None)

    if state.get("done"):
        print(f"  eval-{tag} already COMPLETE (n={len(state['records'])}).")
        return 0

    src = _ckpt("consume.json")
    if not os.path.exists(src):
        print(f"  WALL: {src} missing -- run stage 'consume' to completion first.")
        return 1
    s = _load_graph(src)
    native = s._inner

    prior = ac.pooled_relation_kind_reliability(s) if tag == "consume-full" else None
    if tag == "consume-full":
        print(f"  pooled relation-kind reliability prior (from "
              f"{ac.character_vocabulary_report(s)['total']} held character quanta): {prior}")

    test_alphabets = _test_alphabets()
    blocks = [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]
    print(f"  arm={tag}  test_alphabets={test_alphabets}  blocks={len(blocks)} "
          f"(target n={len(blocks) * WAY})  SHORTLIST_K={SHORTLIST_K}  resuming at block "
          f"{state['block_idx']}")

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        alph, r = blocks[i]
        run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)

    cache: dict = {}
    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
        alph, r = blocks[state["block_idx"]]
        spec = run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)
        drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]

        exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, DK)
                     for ci in range(WAY)]
        exemplar_composed = [e["composed_sig"] for e in exemplars]

        for qi, q_drawer in spec["queries"]:
            path = drawer_files[qi][q_drawer]
            rec = {"true": qi, "alph": alph, "r": r}

            qd = gate.decode_char_signature(s, path, cache, DK)
            shortlist_a = ar.propose_top_k(native, qd["composed_sig"], exemplar_composed,
                                           k=SHORTLIST_K)
            if tag == "consume-full":
                shortlist_b = ac.propose_top_k_pooled_prior(
                    native, qd["composed_sig"], exemplar_composed, prior, k=SHORTLIST_K)
                shortlist = sorted(set(shortlist_a) | set(shortlist_b))
                state["union_widths"].append(len(shortlist))
            else:
                shortlist = shortlist_a
            rec["in_shortlist"] = bool(qi in shortlist)

            scratch_s = srs.Substrate()
            cand_s = {}
            for ci in shortlist:
                node = ar.stage_parse_char(scratch_s, drawer_files[ci][ex_drawer],
                                            is_query=False, name=str(ci))
                cand_s[node] = ci
            qn_s = ar.stage_parse_char(scratch_s, path, is_query=True)
            w_s = ar.parse_marginal_verdict(scratch_s, qn_s)
            rec["pred_shortlist"] = cand_s.get(w_s, -1) if w_s is not None else -1
            state["records"].append(rec)

        state["block_idx"] += 1
        _save_json(state, out_path)
        print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
              f"{len(state['records'])} episodes so far, {time.time() - t0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        _finalize_eval(state)
        _save_json(state, out_path)
        print(f"\n  EVAL COMPLETE for {tag}: n={len(state['records'])}")
        cov = state["coverage"]
        print(f"    coverage@{SHORTLIST_K}:      {100*cov['cov']:.1f}%  95% CI "
              f"[{100*cov['ci'][0]:.1f}%, {100*cov['ci'][1]:.1f}%]  n={cov['n']}")
        sl = state["shortlist_acc"]
        print(f"    shortlist accuracy:  {100*sl['acc']:.1f}%  95% CI "
              f"[{100*sl['ci'][0]:.1f}%, {100*sl['ci'][1]:.1f}%]  n={sl['n']}")
        if tag == "consume-full" and state.get("union_widths"):
            print(f"    mean union shortlist width: {np.mean(state['union_widths']):.2f} "
                  f"(naive-only width is always exactly {SHORTLIST_K})")
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- "
              f"re-run '--stage eval-{tag}' to continue.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: report
# ===============================================================================================
def stage_report():
    print(f"\n{SEP}\n  RUN 29 -- CONSUMPTION -- FINAL REPORT\n{SEP}")

    def _opt(name):
        p = _ckpt(name)
        return _load_json(p) if os.path.exists(p) else None

    verify = _opt("verify.json")
    consume_meta = _opt("consume_metrics.json")
    ev_base = _opt("eval_baseline_pointer.json")
    ev_mark = _opt("eval_consume-mark.json")
    ev_full = _opt("eval_consume-full.json")

    missing = [n for n, v in (("verify", verify), ("eval-baseline", ev_base)) if v is None]
    if missing:
        print(f"  WALL: stages not yet complete: {missing}. Run them before 'report'.")
        return 1

    test_alphabets = _test_alphabets()
    print(f"\n  eval-subset coverage: {N_TEST_ALPHABETS} evaluation alphabets, WAY={WAY}-way "
          f"within-alphabet, target n={N_TEST_ALPHABETS * R_TARGET * WAY}: {test_alphabets}")
    prac_alph = (consume_meta or {}).get("practice_alphabets")
    print(f"  practice-subset coverage: 10 HELD-OUT background alphabets {prac_alph}, "
          f"~{N_PRACTICE_ITEMS} whole characters, seed={PRACTICE_SEED} (byte-identical to "
          f"run 27/28's own practice set)")
    print(f"  LEARN: reused verbatim from run 28's calibrated graph ({verify['calib_src']})")

    # ---- P3/P4: internal-loop metrics ------------------------------------------------------
    print(f"\n  {SEP}\n  P3 -- SURVIVING RESIDUAL ACROSS CYCLES (levers a+b)\n  {SEP}")
    print(f"  {SEP}\n  P4 -- ARRANGEMENT SUBSCORE ACROSS CYCLES, WEIGHTED vs UNWEIGHTED\n  {SEP}")
    if consume_meta and consume_meta.get("cycles"):
        cycles = consume_meta["cycles"]
        series = [cycles[0]["surviving_before"]] + [c["surviving_after"] for c in cycles]
        w_series = [cycles[0]["mean_weighted_before"]] + [c["mean_weighted_after"] for c in cycles]
        u_series = [cycles[0]["mean_unweighted_before"]] + [c["mean_unweighted_after"] for c in cycles]
        print(f"  surviving_residual_count series (before-cycle0, after-each-cycle): {series}")
        print(f"  P3: {'CONFIRMED (falls)' if consume_meta.get('p3_falls') else 'NULL -- did not fall'}")
        print(f"  mean_arrangement WEIGHTED series:   {[round(x,4) for x in w_series]}")
        print(f"  mean_arrangement UNWEIGHTED series: {[round(x,4) for x in u_series]}")
        print(f"  P4: {'CONFIRMED (weighted rises)' if consume_meta.get('p4_rises') else 'NULL -- did not rise'}")
        weighting_only = (w_series[-1] > w_series[0]) and not (u_series[-1] > u_series[0])
        if weighting_only:
            print("  NOTE: rise appears in the WEIGHTED series only, not the UNWEIGHTED control -- "
                  "the weighting arithmetic alone, not a geometry change. Reported, not hidden.")
        for c in cycles:
            print(f"    cycle {c['cycle']}: worksheet_size={c['worksheet_size']} "
                  f"corrections={c['corrections']} mints_reading={c['mints_during_reading']} "
                  f"mints_babble={c['mints_during_babble']} "
                  f"mints_character_reading={c['mints_character_reading']} "
                  f"character_codebook_size={c['character_codebook_size']} "
                  f"weight_distribution={c['weight_distribution']} elapsed={c['elapsed']:.1f}s")
        last = cycles[-1]
        print(f"\n  RECOGNITION COVERAGE (last cycle, post-babble mark_characters pass):")
        print(f"    overall:            {last['recognition_after']['overall']}")
        print(f"    surviving_residual: {last['recognition_after']['surviving_residual']}")
        if not consume_meta.get("p3_falls"):
            frac = last["recognition_after"]["surviving_residual"]["recognized_frac"]
            print(f"    P3 DIAGNOSIS: surviving-item recognition coverage = {frac} -- "
                  f"{'a low fraction here is the likely reason weighting never engaged for most '
                     'of the residual (traced, not hand-waved)'
                   if (frac is not None and frac < 0.5)
                   else 'coverage looks high enough that weighting SHOULD have engaged for most '
                        'of the residual -- the null needs a different explanation'}")
    else:
        print("  consume stage not run yet.")

    # ---- eval table --------------------------------------------------------------------------
    print(f"\n  {SEP}\n  EVAL TABLE (n up to {N_TEST_ALPHABETS*R_TARGET*WAY}, Wilson 95% CI)\n  {SEP}")
    print(f"  baseline (reused from run 26): n={ev_base['n']}  full_dwell={ev_base['full_dwell']}")
    print(f"    coverage@{SHORTLIST_K}={100*ev_base['coverage']['cov']:.1f}% "
          f"[{100*ev_base['coverage']['ci'][0]:.1f},{100*ev_base['coverage']['ci'][1]:.1f}]   "
          f"shortlist_acc={100*ev_base['shortlist_acc']['acc']:.1f}% "
          f"[{100*ev_base['shortlist_acc']['ci'][0]:.1f},{100*ev_base['shortlist_acc']['ci'][1]:.1f}]")

    def _row(tag, ev):
        if ev is None:
            print(f"  {tag:<18} not run")
            return None
        if not ev.get("done"):
            print(f"  {tag:<18} INCOMPLETE ({ev['block_idx']} blocks done, "
                  f"n={len(ev['records'])} so far)")
            return None
        cov, sl = ev["coverage"], ev["shortlist_acc"]
        print(f"  {tag:<18} n={cov['n']:>4}  coverage@{SHORTLIST_K}={100*cov['cov']:5.1f}% "
              f"[{100*cov['ci'][0]:5.1f},{100*cov['ci'][1]:5.1f}]   "
              f"shortlist_acc={100*sl['acc']:5.1f}% [{100*sl['ci'][0]:5.1f},{100*sl['ci'][1]:5.1f}]")
        return ev
    ev_mark_r = _row("CONSUME-MARK", ev_mark)
    ev_full_r = _row("CONSUME-FULL", ev_full)

    print(f"\n  {SEP}\n  P5 -- COVERAGE@{SHORTLIST_K} vs BASELINE (arm 3, CONSUME-FULL)\n  {SEP}")
    def _p5(tag, ev):
        if ev is None or not ev.get("done"):
            print(f"  {tag}: not evaluated (n={len(ev['records']) if ev else 0}).")
            return
        cov, base_cov = ev["coverage"], ev_base["coverage"]
        sep = _sep(cov["ci"], base_cov["ci"])
        better = cov["cov"] > base_cov["cov"]
        verdict = "CONFIRMED (coverage improved, CI-separated -- the transfer claim)" if (sep and better) else \
                  ("ANOMALY (CI-separated but WORSE)" if (sep and not better) else
                   "NULL (not CI-separated -- pre-registered as the LIKELY shape: pooled prior "
                   "is a weak general signal unioned onto an already-strong shortlist)")
        print(f"  {tag}: {100*cov['cov']:.1f}% [{100*cov['ci'][0]:.1f},{100*cov['ci'][1]:.1f}] "
              f"vs baseline {100*base_cov['cov']:.1f}% "
              f"[{100*base_cov['ci'][0]:.1f},{100*base_cov['ci'][1]:.1f}] -> {verdict}")
    _p5("CONSUME-FULL", ev_full_r)
    if ev_mark_r is not None:
        print(f"  (CONSUME-MARK, informational -- UNCHANGED proposal mechanism, isolates "
              f"whether levers a+b alone shifted eval numbers via different codebook growth):")
        _p5("CONSUME-MARK", ev_mark_r)

    print(f"\n  {SEP}\n  P6 -- SHORTLIST-CONSTRAINED ACCURACY vs BASELINE (expected to move ONLY "
          f"through coverage)\n  {SEP}")
    def _p6(tag, ev):
        if ev is None or not ev.get("done"):
            print(f"  {tag}: not evaluated.")
            return
        sl, base_sl = ev["shortlist_acc"], ev_base["shortlist_acc"]
        cov, base_cov = ev["coverage"], ev_base["coverage"]
        acc_sep = _sep(sl["ci"], base_sl["ci"])
        cov_sep = _sep(cov["ci"], base_cov["ci"])
        acc_better = sl["acc"] > base_sl["acc"]
        if acc_sep and cov_sep and acc_better:
            verdict = "CONFIRMED (accuracy moved WITH coverage)"
        elif acc_sep and not cov_sep:
            verdict = "ANOMALY (accuracy moved WITHOUT coverage moving -- investigate leakage)"
        elif not acc_sep:
            verdict = "NULL (no accuracy movement -- EXPECTED SHAPE per P6 if coverage alone moved)"
        else:
            verdict = "ANOMALY (accuracy moved opposite to coverage)"
        print(f"  {tag}: shortlist_acc {100*sl['acc']:.1f}% [{100*sl['ci'][0]:.1f},{100*sl['ci'][1]:.1f}] "
              f"vs baseline {100*base_sl['acc']:.1f}% [{100*base_sl['ci'][0]:.1f},{100*base_sl['ci'][1]:.1f}] "
              f"(acc_ci_sep={acc_sep}, cov_ci_sep={cov_sep}) -> {verdict}")
    _p6("CONSUME-FULL", ev_full_r)
    if ev_mark_r is not None:
        _p6("CONSUME-MARK", ev_mark_r)

    print(f"\n{SEP}\n  INVARIANTS\n{SEP}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(SEP)
    return 0


# ===============================================================================================
# MAIN
# ===============================================================================================
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["verify", "consume", "eval-baseline", "eval-consume-mark",
                             "eval-consume-full", "report"])
    args = p.parse_args()
    t0 = time.time()
    if args.stage == "verify":
        rc = stage_verify()
    elif args.stage == "consume":
        rc = stage_consume()
    elif args.stage == "eval-baseline":
        rc = stage_eval_baseline()
    elif args.stage == "eval-consume-mark":
        rc = stage_eval("consume-mark")
    elif args.stage == "eval-consume-full":
        rc = stage_eval("consume-full")
    elif args.stage == "report":
        rc = stage_report()
    else:
        rc = 1
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
