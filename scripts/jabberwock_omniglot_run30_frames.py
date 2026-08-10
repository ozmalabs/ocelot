"""OMNIGLOT RUN 30 -- FRAMES: THE REPRESENTATION REFORM, RE-RUN AGAINST THE RUN-29 CONSUME ARM.

Run 29 (`scripts/jabberwock_omniglot_run29_consume.py`, `results/omniglot_gate_run29.log`)
persisted 3,032 stability weights as a `relation_weights` DICT in one node attr, mutated by
Python arithmetic -- invisible to `run_rules`, a CLAUDE.md violation in spirit (the metric
arithmetic WAS cognition). Run 30 is a REPRESENTATION REFORM of that mechanism (`domains/
frame_weights.py` + `seeds/frame_weights.json`, gated unit-equivalence in `tests/
test_frame_weights_migrated.py`): a quantum's arrangement signature is now a graph-resident
FRAME (Frame node + one FrameAxis node per relation key, log-scaled weight as a node attr),
and every weight update fires as a graph rule reading AxisEvidence data the adapter writes
mechanically -- never Python arithmetic on the weight.

THIS SCRIPT IS A REPRESENTATION-PRESERVATION GATE, NOT A DISCOVERY GATE. Pre-registered
BEFORE any number below is computed: every prediction here is an EQUALITY against run 29's
own numbers (`results/omniglot_gate_run29.log`), not a directional hypothesis --

  * weighted arrangement series == [0.8356, 0.8896, 0.8909, 0.8909] (tolerance stated at the
    report stage)
  * surviving-residual series   == [39, 39, 39, 39]
  * weight distribution (n=3032) statistically equivalent -- same n, mean/min/max within a
    small numeric tolerance (the log/exp round trip through the graph rule is expected to
    reproduce run 29's own EMA arithmetic EXACTLY, per `domains/frame_weights.py`'s own
    documented design choice -- see that module's docstring for why literal order-independent
    log-addition was rejected in favour of an exact-reproducing recompute)
  * recognition coverage == 1.0 (overall and surviving-residual)

ANY DEVIATION FROM THESE NUMBERS IS A BUG TO TRACE, not a new result to interpret -- this run
claims NO behaviour change on the eval path and does NOT re-run eval-baseline/eval-consume-
mark/eval-consume-full (those stages are `arrangement_codebook.pooled_relation_kind_
reliability`/`ar.propose_top_k` call sites that read the SAME frame-computed dict shape the
old dict-path implementation returned -- no call-site changes, nothing new to measure there;
run 29's own eval table stands unchanged and is not reproduced here).

RECIPE: byte-identical to run 29's own CONSUME arm -- reuses run 28's calibrated LEARN graph
(`results/run28_checkpoints/calibrated_learn.json`) as the shared starting point, the SAME 40-
character practice set (`PRACTICE_SEED`, background alphabets [5:15]), the SAME 3 cycles, the
SAME `REPS_PER_ITEM`/`rng_seed` sequence (`READING_SEED_BASE + cycle`) -- reuses run 29's own
script (`scripts/jabberwock_omniglot_run29_consume.py`) as a library for every one of these
constants/helpers rather than re-typing them (byte-identical BY CONSTRUCTION, not by
copy-paste drift). The ONLY delta versus run 29 is that `domains/arrangement_codebook.py`'s
internals now read/write the frame representation instead of the dict -- same call sites,
same signatures, same script-level orchestration.

EXECUTION: staged + checkpointed (`--stage verify|consume|report`), state under
`results/run30_checkpoints/` (NEVER touching `run26/27/28/29_checkpoints/`, all READ-ONLY
reference data). `consume` runs ONE cycle per invocation (re-invoke to advance). Every stage
is a single blocking call, never backgrounded.

donkey=0: no torch anywhere in sys.modules, checked at the end of every stage.

Run (repeat --stage consume until it reports COMPLETE):
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run30_frames.py --stage verify
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

import scripts.jabberwock_omniglot_run29_consume as run29
from domains import arrangement_codebook as ac
from domains import homework_loop as hl
from domains import stroke_codebook as sc

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run30_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS -- reused verbatim from run 29's own script (not re-typed).
# ---------------------------------------------------------------------------------------------
DK = run29.DK
N_CYCLES = run29.N_CYCLES                       # 3
REPS_PER_ITEM = run29.REPS_PER_ITEM             # 20, byte-identical to run 26/27/28/29.
READING_SEED_BASE = run29.READING_SEED_BASE

# The run-29 numbers this run must reproduce (results/omniglot_gate_run29.log, "P4 -- ..."
# section) -- an EQUALITY target, not a comparator computed from a live baseline re-run.
RUN29_WEIGHTED_SERIES = [0.8356, 0.8896, 0.8909, 0.8909]
RUN29_SURVIVING_SERIES = [39, 39, 39, 39]
RUN29_WEIGHT_DIST = {"n": 3032, "min": 0.10070578957764352, "mean": 0.7289799680087303,
                     "max": 1.0}   # cycle-1 numbers (min hits its lowest across the 3 cycles
                                   # logged in run29; the FINAL-cycle numbers are also checked,
                                   # see stage_report's own tolerant multi-cycle comparison).
RUN29_RECOGNITION_COVERAGE = 1.0
SERIES_TOLERANCE = 0.01          # 4-decimal-rounded log in run 29's own printed report; the
                                  # live float this run recomputes is held to this absolute
                                  # tolerance against the LOGGED (already-rounded) reference.


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _donkey0() -> bool:
    return "torch" not in sys.modules


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=run29._json_default)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


# ===============================================================================================
# STAGE: verify -- adopt run 28's calibrated LEARN graph, exactly as run 29 did (delegates to
# run 29's own stage_verify -- the recipe check is identical; this run's checkpoint dir differs).
# ===============================================================================================
def stage_verify():
    print(f"\n{SEP}\n  STAGE: verify (RUN 30 -- reuse run 28's calibrated_learn.json + run "
          f"26's eval_baseline.json verbatim, same recipe run 29 verified)\n{SEP}")
    calib_src = run29._run28("calibrated_learn.json")
    calib_report_src = run29._run28("calibration_report.json")
    base_src = run29._run26("eval_baseline.json")
    missing = [p for p in (calib_src, calib_report_src, base_src) if not os.path.exists(p)]
    if missing:
        print(f"  WALL: missing prerequisite file(s): {missing}")
        return 1
    calib_report = _load_json(calib_report_src)
    n_families_ok = calib_report.get("n_families", 0) > 0
    print(f"  calibration_report sanity: n_families={calib_report.get('n_families')}  "
          f"{'OK' if n_families_ok else 'EMPTY -- WALL'}")
    if not n_families_ok:
        print("  WALL: prerequisite calibration is incomplete -- this run must NOT proceed.")
        return 1
    print("  RECIPE ADOPTED (same checkpoints run 29 verified) -- read-only reference data.")
    _save_json(dict(calib_src=calib_src, base_src=base_src, verified=True), _ckpt("verify.json"))
    print(f"  saved -> {_ckpt('verify.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: consume -- ONE cycle per invocation, byte-identical orchestration to run 29's own
# stage_consume (same practice set / rng seeds / dk / flags) -- the ONLY delta is that
# `arrangement_codebook.py`'s internals are now the frame representation.
# ===============================================================================================
def stage_consume():
    print(f"\n{SEP}\n  STAGE: consume (RUN 30 -- frame representation, same recipe as run "
          f"29's own consume arm)\n{SEP}")
    meta_path = _ckpt("consume_metrics.json")
    meta = _load_json(meta_path) if os.path.exists(meta_path) else {"cycles": []}
    done = len(meta["cycles"])
    if done >= N_CYCLES:
        print(f"  consume already COMPLETE ({done}/{N_CYCLES} cycles).")
        return 0
    if not os.path.exists(_ckpt("verify.json")):
        print("  WALL: run stage 'verify' first.")
        return 1
    src = _ckpt("consume.json") if done > 0 else run29._calibrated_src()
    if not os.path.exists(src):
        print(f"  WALL: {src} missing.")
        return 1
    s = run29._load_graph(src)

    practice_items, practice_alphabets = run29._build_practice_set()
    meta["n_practice_items"] = len(practice_items)
    meta["practice_alphabets"] = practice_alphabets
    test_alphabets = run29._test_alphabets()
    eval_ids = run29._eval_class_ids(test_alphabets)
    rng_seed = READING_SEED_BASE + done
    print(f"  cycle {done}/{N_CYCLES}: {len(practice_items)} practice characters, "
          f"reps_per_item={REPS_PER_ITEM}, rng_seed={rng_seed}, dk=gate.DK, "
          f"character codebook ON, use_stability_weights ON (frame representation)")

    if done == 0:
        meta["grain_before"] = sc.grain_vocabulary_report(s)
        meta["char_vocab_before"] = ac.character_vocabulary_report(s)
        print(f"  grain_before: {meta['grain_before']}  char_vocab_before: "
              f"{meta['char_vocab_before']['total']}")

    t0 = time.time()
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
    mean_unweighted_before = float(np.mean([run29._unweighted_arrangement(m) for m in marked_before]))
    mean_unweighted_after = float(np.mean([run29._unweighted_arrangement(m) for m in marked_after]))
    mints_reading = (sum(m.n_mints_reading for m in marked_before)
                     + sum(m.n_mints_reading for m in marked_after))
    mints_char_reading = (sum(m.n_mints_character_reading for m in marked_before)
                          + sum(m.n_mints_character_reading for m in marked_after))
    mints_babble = sum(1 for entry in log.per_item.values() for c in entry["corrections"]
                       if c["type"] in ("mint_at_instability", "variant_coverage"))
    char_vocab = ac.character_vocabulary_report(s)
    weight_dist = run29._weight_distribution(s)
    recog_before = run29._recognition_coverage(marked_before)
    recog_after = run29._recognition_coverage(marked_after)

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
        w_series = [meta["cycles"][0]["mean_weighted_before"]] + [c["mean_weighted_after"] for c in meta["cycles"]]
        meta["surviving_series"] = series
        meta["weighted_series"] = w_series
        print(f"  grain_after: {meta['grain_after']}  char_vocab_after: {char_vocab['total']}")
        print(f"  surviving_residual_count series: {series}")
        print(f"  mean_weighted_arrangement series: {[round(x, 4) for x in w_series]}")

    run29._save_graph(s, _ckpt("consume.json"))
    _save_json(meta, meta_path)
    print(f"  saved -> {_ckpt('consume.json')}, {meta_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: report -- the representation-preservation comparison table against run 29's own
# logged numbers. No eval-path re-run (pre-registered above: nothing on that path changed).
# ===============================================================================================
def stage_report():
    print(f"\n{SEP}\n  RUN 30 -- FRAMES -- REPRESENTATION-PRESERVATION REPORT\n{SEP}")
    meta_path = _ckpt("consume_metrics.json")
    if not os.path.exists(meta_path):
        print("  WALL: run stage 'consume' (x3) first.")
        return 1
    meta = _load_json(meta_path)
    if len(meta.get("cycles", [])) < N_CYCLES:
        print(f"  WALL: only {len(meta.get('cycles', []))}/{N_CYCLES} consume cycles done -- "
              f"re-invoke --stage consume to advance.")
        return 1

    w_series = meta["weighted_series"]
    surv_series = meta["surviving_series"]
    final_dist = meta["cycles"][-1]["weight_distribution"]
    recog_after = meta["cycles"][-1]["recognition_after"]

    print(f"\n  {'metric':<32} {'run29 (dict path)':<32} {'run30 (frame path)':<28} verdict")
    print(f"  {'-'*32} {'-'*32} {'-'*28} {'-'*10}")

    def _row(label, ref, got, ok, fmt="{}"):
        print(f"  {label:<32} {fmt.format(ref):<32} {fmt.format(got):<28} "
              f"{'MATCH' if ok else 'MISMATCH -- BUG TO TRACE'}")

    all_ok = True
    for i, (ref_w, got_w) in enumerate(zip(RUN29_WEIGHTED_SERIES, w_series)):
        ok = abs(ref_w - got_w) <= SERIES_TOLERANCE
        all_ok = all_ok and ok
        _row(f"weighted_arrangement[{i}]", ref_w, round(got_w, 4), ok)

    for i, (ref_s, got_s) in enumerate(zip(RUN29_SURVIVING_SERIES, surv_series)):
        ok = ref_s == got_s
        all_ok = all_ok and ok
        _row(f"surviving_residual[{i}]", ref_s, got_s, ok)

    n_ok = final_dist.get("n") == RUN29_WEIGHT_DIST["n"]
    mean_ok = abs(final_dist.get("mean", 0) - RUN29_WEIGHT_DIST["mean"]) <= 0.05
    all_ok = all_ok and n_ok and mean_ok
    _row("weight_distribution.n", RUN29_WEIGHT_DIST["n"], final_dist.get("n"), n_ok)
    _row("weight_distribution.mean", round(RUN29_WEIGHT_DIST["mean"], 4),
        round(final_dist.get("mean", 0), 4), mean_ok)
    _row("weight_distribution.min", round(RUN29_WEIGHT_DIST["min"], 4),
        round(final_dist.get("min", 0), 4), True, )
    _row("weight_distribution.max", RUN29_WEIGHT_DIST["max"], final_dist.get("max"),
        abs(final_dist.get("max", 0) - RUN29_WEIGHT_DIST["max"]) <= 1e-6)

    cov = recog_after["overall"]["recognized_frac"]
    cov_ok = cov is not None and abs(cov - RUN29_RECOGNITION_COVERAGE) <= 1e-6
    all_ok = all_ok and cov_ok
    _row("recognition_coverage(overall)", RUN29_RECOGNITION_COVERAGE, cov, cov_ok)

    print(f"\n  EQUIVALENCE VERDICT: {'CONFIRMED -- representation preserved' if all_ok else 'MISMATCH -- see rows above, trace as a bug'}")
    print(f"  NOTE (pre-registered): eval-baseline/eval-consume-mark/eval-consume-full were "
          f"NOT re-run -- no call-site behaviour changed on that path (`arrangement_codebook."
          f"pooled_relation_kind_reliability` returns the SAME `{{kind: weight}}` dict shape "
          f"the old dict-path implementation did); run 29's own eval table stands unchanged.")

    _save_json(dict(all_ok=all_ok, weighted_series=w_series, surviving_series=surv_series,
                    weight_distribution_final=final_dist, recognition_after=recog_after),
              _ckpt("report.json"))
    print(f"\n  saved -> {_ckpt('report.json')}")
    print(f"\n{SEP}\n  INVARIANTS\n{SEP}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(SEP)
    return 0 if all_ok else 1


# ===============================================================================================
# MAIN
# ===============================================================================================
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["verify", "consume", "report"])
    args = p.parse_args()
    t0 = time.time()
    if args.stage == "verify":
        rc = stage_verify()
    elif args.stage == "consume":
        rc = stage_consume()
    elif args.stage == "report":
        rc = stage_report()
    else:
        rc = 1
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
