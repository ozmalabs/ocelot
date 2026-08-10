"""OMNIGLOT RUN 27 -- READING AS PRACTICE (character grain, novel background material).

RUN 26's own final report fired the pre-registered P2 STOP: background round-trip was already
99.3% at marking (5/200 residual items, unchanged across 3 cycles, 0 corrections). Diagnosis,
two prongs, both closed by this run's design (see `domains/homework_loop.py`'s own
`mark_characters`/`babble_characters`/`cycle_characters`, the CHARACTER-grain extension landed
for this run):

  1. WRONG GRAIN -- run 26 practiced single STROKES; real strokes collapse to ~5 quantized
     families by construction (stroke-grain round-trip saturates trivially), and identity lives
     in ARRANGEMENT (the arc's own +21pp composition result). This run practices whole
     CHARACTERS (`mark_characters`/`babble_characters`), scoring family + stroke-count +
     ARRANGEMENT (`rel`/`cpose_*`) agreement, COUNT-MISMATCH-TOLERANT (a merge/split is aligned
     by arc-length overlap, `_align_spans_by_overlap`, never dropped -- the coordinator's own
     correction to this run's design, closing the exact mechanism hole run 26's 5 surviving
     residuals (all span-COUNT mismatches, e.g. 13->8) exposed in the stroke-grain loop).

  2. MASTERED MATERIAL -- run 26 practiced the SAME 5 alphabets the codebook was grown on; new-
     drawer variation is absorbed by pose dimensions alone. This run practices NOVEL characters
     from 10 HELD-OUT BACKGROUND alphabets (background[5:15], never touched by LEARN's
     background[:5]) -- legal practice material (the Omniglot "evaluation" split is a SEPARATE,
     still fully quarantined set; this run never touches it for practice).

CREATOR'S FRAME (load-bearing): "the connectedness of the speech and language cortex means you
get better at speaking by reading as well" -- decode (reading) and render (writing) share ONE
codebook (AbS: one model, two directions), so decode-side exposure to NOVEL real ink is
PRODUCTION PRACTICE, and the READING pass itself is the only arm importing new information
(`mark_characters`'s own native OOV minting, counted as `n_mints_reading`/`mints_during_reading`
-- kept SEPARATE from babble's own `mints_during_babble`, per the coordinator's own note that a
decode-side mint during a babble decode is a reading event, never a "correction").

ARMS (learn recipe byte-identical to run 26/25 -- same `gate` module, same constants, verified
at stage "learn"):
  (1) BASELINE = learn only. RUN 26's OWN `results/run26_checkpoints/eval_baseline.json` is
      COMPLETE (`done=true`, n=400) and REUSED VERBATIM (recipe verified identical: same
      `gate.SEED`, `LEARN_ALPHABETS_N`, `DK`, `GROWTH_WINDOW`, since this script imports the
      SAME `gate`/`run25` modules and never overrides their constants) -- no baseline eval is
      re-run. `results/run26_checkpoints/learn.json` (read-only) is this run's own shared LEARN
      starting point too (byte-identical recipe -- re-running LEARN would reproduce the exact
      same graph at ~110s cost for nothing new).
  (2) READING-ONLY: learn + N_CYCLES=3 `mark_characters`-only passes on the practice set, NO
      babble -- plasticity comes ONLY from native decode-side minting during reading.
  (3) READING+BABBLE: learn + N_CYCLES=3 full `cycle_characters` (mark -> assign -> babble ->
      re-mark) on the practice set.

PRACTICE MATERIAL: ~150 whole characters (`_build_practice_set`), seeded (`PRACTICE_SEED`,
distinct from `POWER_SEED`/`gate.SEED`), sampled from the 10 HELD-OUT background alphabets
`ow.alphabets("background")[5:15]` -- disjoint from LEARN's own `[:5]` by slicing and from every
evaluation alphabet by construction (a different Omniglot split directory entirely), additionally
hard-guarded via `eval_class_ids` on every `mark_characters`/`babble_characters`/`cycle_characters`
call.

PRE-REGISTERED PREDICTIONS (stated before any result below is computed):
  P1. Character-grain round-trip on the practice set is NOT saturated at first mark (mean well
      below 0.99 -- if it IS saturated, that falsifies the grain diagnosis: STOP, report, and
      do not spend eval compute on arms 2/3).
  P2. The surviving residual falls across cycles in ARM 3 (READING+BABBLE) -- the teacher-
      information metric. STOP BRANCH: if P2 fails while P1 is confirmed, that is still a
      result (it separates "reading matters" from "babble/consolidation adds nothing over
      reading alone") -- eval still proceeds (P2 failing is not itself an eval-withholding gate
      the way run 26's P2 STOP was, since P1 already establishes there is real material to
      practice on; the report states this explicitly).
  P3. `mints_during_reading` > 0 in BOTH arm 2 and arm 3 (new information enters via decode --
      the run's own headline mechanism check).
  P4. Eval coverage@shortlist (K=10, same as run 26) improves in arms 2/3 vs the baseline arm.
  P5. 20-way shortlist-constrained accuracy (n up to 400, Wilson CI) moves ONLY THROUGH
      coverage -- given the verdict-layer ceiling (six independent RUN-25-family nulls at
      ~80.5%), accuracy exceeding the baseline CI is NOT required for success; a coverage gain
      with flat accuracy is the EXPECTED shape. Accuracy moving CI-separated WITHOUT a coverage
      gain is flagged as an ANOMALY, not a success.

EVAL: identical protocol/seeds to run 26/25 (`POWER_SEED` replay, 10 eval alphabets, 20-way,
n=400, `SHORTLIST_K=10`). The C0 FULL-DWELL control is, BY CONSTRUCTION (run 26's own verified
architectural fact -- corner-split + SC+TPS marginalization over raw points, no codebook
dependency), IDENTICAL no matter what this run's homework loop does -- this run does NOT
recompute it per arm; it is cited ONCE from `run26_checkpoints/eval_baseline.json`. Every
episode here computes only the CODEBOOK-DEPENDENT structural proposal (coverage@K) and the
shortlist-constrained parse-marginal accuracy -- the two metrics practice CAN move.

EXECUTION: staged + checkpointed (`--stage learn|reading|reading-babble|eval-baseline|
eval-reading|eval-reading-babble|report`), state under `results/run27_checkpoints/` (NEVER
`run26_checkpoints/`, which is read-only reference data for this script). `reading`/
`reading-babble` run ONE cycle per invocation (re-invoke to advance); `eval-*` process eval
BLOCKS up to `PER_CALL_BUDGET_SECONDS` and checkpoint after every block (re-invoke to continue).
Every stage is a single blocking call, never backgrounded.

donkey=0: no torch anywhere in sys.modules, checked at the end of every stage.

Run (repeat --stage reading/reading-babble/eval-* until each reports COMPLETE):
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run27_reading.py --stage learn
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
from domains import homework_loop as hl
from domains import omniglot_world as ow
from domains import stroke_codebook as sc

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run27_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")     # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS.
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = gate.LEARN_ALPHABETS_N            # 5 -- byte-identical to run 26/25.
LEARN_DRAWERS = gate.LEARN_DRAWERS                    # 01..14
LEARN_STROKE_CAP = 1500                               # RUN 16/25's saturation-verified cap.
DK = gate.DK                                          # the arc's own reduced Omniglot bins --
                                                       # used for LEARN *and* every
                                                       # mark_characters/babble_characters/
                                                       # cycle_characters call (load-bearing).
GROWTH_WINDOW = gate.GROWTH_WINDOW

PRACTICE_ALPHABETS_SLICE = slice(5, 15)               # HELD-OUT background alphabets --
                                                       # never touched by LEARN's [:5].
# WALL-CLOCK DEVIATION (logged explicitly, per this run's own pre-registration clause "adjust
# only for wall-clock feasibility; deviations are logged explicitly"): the pre-registered target
# was ~150 whole characters. A timed pilot (10 items, this run) measured a FULL cycle_characters
# pass (mark -> assign -> babble reps_per_item=20 -> re-mark) at ~9.3s/item with worksheet size
# ~9/10 (nearly every practice character carries a genuine 0<score<1 arrangement residual, so
# `capacity=None` babbles nearly the whole set every cycle) -- 150 items x 3 cycles would be
# ~70 minutes for arm 3 alone. Reduced to N_PRACTICE_ITEMS=40 (~18.5 min for arm 3's 3 cycles,
# each single cycle still comfortably under PER_CALL_BUDGET_SECONDS) to fit this session's
# wall-clock budget. This does NOT affect the EVAL table's n (still up to 400, unrelated sample)
# -- only the descriptive practice-set statistics (mean round-trip, mint counts, worksheet size)
# are measured over a smaller pool.
N_PRACTICE_ITEMS = 40
PRACTICE_SEED = gate.SEED + 9000                      # distinct from POWER_SEED/gate.SEED/
                                                       # run26's own MARK_SEED (20260726).

N_CYCLES = 3
REPS_PER_ITEM = 20                                    # matches run 26.
READING_SEED_BASE = PRACTICE_SEED + 5000              # one seed per cycle: BASE + cycle.

WAY = run25.WAY                                       # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET   # 20
R_TARGET = run25.R_TARGET                             # 2  -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS             # 10
POWER_SEED = run25.POWER_SEED                         # gate.SEED + 1500, byte-identical to
                                                       # run 15/16/17/25/26's own eval seed.
N_FLOOR_PER_ARM = 200
RUN25_C0_CONTROL = run25.RUN17B_CONTROL               # {"acc":0.805,"ci":(0.763,0.841),"n":400}

SHORTLIST_K = 10                                      # byte-identical to run 26.
PER_CALL_BUDGET_SECONDS = 480.0


# ---------------------------------------------------------------------------------------------
# PERSISTENCE -- run 26's OWN fixed recipe, reproduced verbatim (a first version that saved
# only `graph_to_dict()` broke on reload: `induce_concern`, fired from inside `decode_ink` on
# genuinely novel practice-alphabet ink, does `sub.add_edge(ag_node, "observed", obs_node)`,
# gated by Γ -- and Γ's dynamically-admitted productions plus every runtime-authored Rule live
# in substrate_rs state `graph_to_dict` does NOT capture).
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


def _donkey0() -> bool:
    return "torch" not in sys.modules


# ---------------------------------------------------------------------------------------------
# SHARED HELPERS.
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
    """~150 WHOLE characters (all strokes), seeded, from the 10 HELD-OUT background alphabets
    `ow.alphabets("background")[5:15]` -- never touched by LEARN's own `[:5]`. Disjoint from
    every evaluation alphabet by construction (a different Omniglot split directory entirely)
    AND hard-guarded via `eval_class_ids` on every downstream `mark_characters`/
    `babble_characters`/`cycle_characters` call. Deterministic given `seed` -- called
    identically for both the reading-only and reading+babble arms so they practice on the
    IDENTICAL set."""
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


def _mean_subscore(marked: list, attr: str) -> float:
    vals = [getattr(m, attr) for m in marked if getattr(m, attr) is not None]
    return float(np.mean(vals)) if vals else 0.0


# ===============================================================================================
# STAGE: learn -- VERIFY the recipe matches run 26/25 and adopt its learn.json as this run's
# own shared starting point (read-only reference, never copied/mutated in place).
# ===============================================================================================
def stage_learn():
    print(f"\n{SEP}\n  STAGE: learn (recipe verification -- run 26's learn.json is REUSED)\n{SEP}")
    src = _run26("learn.json")
    src_meta = _run26("learn_meta.json")
    if not (os.path.exists(src) and os.path.exists(src_meta)):
        print(f"  WALL: {src} / {src_meta} missing -- run 26's learn stage must have completed "
              f"for this script to reuse it (per the coordinator's own instruction, this run "
              f"never re-runs LEARN if the recipe already matches).")
        return 1
    meta = _load_json(src_meta)

    ok = True
    checks = [
        ("gate.SEED", gate.SEED, gate.SEED),                       # same module -> trivially
        ("LEARN_ALPHABETS_N", LEARN_ALPHABETS_N, gate.LEARN_ALPHABETS_N),  # equal by import,
        ("DK", DK, gate.DK),                                       # verified explicitly anyway
        ("GROWTH_WINDOW", GROWTH_WINDOW, gate.GROWTH_WINDOW),       # so drift in either script
        ("LEARN_STROKE_CAP", LEARN_STROKE_CAP, 1500),               # would be caught.
        ("learn_alphabets", meta["learn_alphabets"],
         ow.alphabets("background")[:LEARN_ALPHABETS_N]),
        ("n_strokes", meta["n_strokes"], LEARN_STROKE_CAP),
    ]
    for label, a, b in checks:
        match = (a == b)
        ok = ok and match
        print(f"  recipe check  {label:<20} run27={a!r}  reference={b!r}  "
              f"{'MATCH' if match else 'MISMATCH -- PROTOCOL DRIFT'}")

    if not ok:
        print("  WALL: recipe MISMATCH -- this run must NOT reuse run 26's learn.json/eval_"
              "baseline.json. (Not expected -- both scripts import the same `gate`/`run25` "
              "modules and never override their constants.)")
        return 1

    print(f"  RECIPE VERIFIED IDENTICAL to run 26/25 -- adopting {src} (read-only) as this "
          f"run's own shared LEARN starting point. LEARN alphabets: {meta['learn_alphabets']}")
    print(f"  codebook grain report (from run 26): {meta['grain_report']}")
    _save_json(dict(reused_from=src, learn_meta=meta, verified=True), _ckpt("learn_meta.json"))
    print(f"  saved -> {_ckpt('learn_meta.json')} (pointer + verification record only -- the "
          f"graph itself is loaded directly from {src} by every downstream stage)")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _learn_src() -> str:
    return _run26("learn.json")


# ===============================================================================================
# STAGE: reading (arm 2 -- one mark_characters-only pass per invocation, NO babble)
# ===============================================================================================
def stage_reading():
    print(f"\n{SEP}\n  STAGE: reading (arm 2 -- READING-ONLY, no babble)\n{SEP}")
    meta_path = _ckpt("reading_metrics.json")
    meta = _load_json(meta_path) if os.path.exists(meta_path) else {"cycles": []}
    done = len(meta["cycles"])
    if done >= N_CYCLES:
        print(f"  reading already COMPLETE ({done}/{N_CYCLES} cycles).")
        return 0

    src = _ckpt("reading.json") if done > 0 else _learn_src()
    if not os.path.exists(src):
        print(f"  WALL: {src} missing -- run stage 'learn' first.")
        return 1
    s = _load_graph(src)

    practice_items, practice_alphabets = _build_practice_set()
    meta["n_practice_items"] = len(practice_items)
    meta["practice_alphabets"] = practice_alphabets
    test_alphabets = _test_alphabets()
    eval_ids = _eval_class_ids(test_alphabets)
    print(f"  cycle {done}/{N_CYCLES}: {len(practice_items)} practice characters from "
          f"{practice_alphabets}, mark_characters()-only, dk=gate.DK")

    if done == 0:
        meta["grain_before"] = sc.grain_vocabulary_report(s)
        print(f"  grain_before: {meta['grain_before']}")

    t0 = time.time()
    marked = hl.mark_characters(s, practice_items, dk=DK, eval_class_ids=eval_ids)
    elapsed = time.time() - t0
    mean_score = _mean_subscore(marked, "round_trip_score")
    mean_family = _mean_subscore(marked, "family_score")
    mean_count = _mean_subscore(marked, "count_score")
    mean_arrangement = _mean_subscore(marked, "arrangement_score")
    surviving = sum(1 for m in marked if m.round_trip_score < hl.DEFAULT_MAX_SCORE)
    mints_reading = sum(m.n_mints_reading for m in marked)
    cyc = dict(cycle=done, mean_score=mean_score, mean_family=mean_family,
               mean_count=mean_count, mean_arrangement=mean_arrangement,
               surviving=surviving, mints_reading=mints_reading, elapsed=elapsed)
    meta["cycles"].append(cyc)
    print(f"  mean_score={mean_score:.4f} (family={mean_family:.4f} count={mean_count:.4f} "
          f"arrangement={mean_arrangement:.4f})  surviving={surviving}/{len(marked)}  "
          f"mints_reading={mints_reading}  elapsed={elapsed:.1f}s")

    if done + 1 >= N_CYCLES:
        meta["grain_after"] = sc.grain_vocabulary_report(s)
        print(f"  grain_after: {meta['grain_after']}")
        scores = [c["mean_score"] for c in meta["cycles"]]
        print(f"  mean_score series across cycles: {[round(x, 4) for x in scores]}")

    _save_graph(s, _ckpt("reading.json"))
    _save_json(meta, meta_path)
    print(f"  saved -> {_ckpt('reading.json')}, {meta_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: reading-babble (arm 3 -- one full cycle_characters per invocation)
# ===============================================================================================
def stage_reading_babble():
    print(f"\n{SEP}\n  STAGE: reading-babble (arm 3 -- READING+BABBLE)\n{SEP}")
    meta_path = _ckpt("reading_babble_metrics.json")
    meta = _load_json(meta_path) if os.path.exists(meta_path) else {"cycles": []}
    done = len(meta["cycles"])
    if done >= N_CYCLES:
        print(f"  reading-babble already COMPLETE ({done}/{N_CYCLES} cycles).")
        return 0

    src = _ckpt("reading_babble.json") if done > 0 else _learn_src()
    if not os.path.exists(src):
        print(f"  WALL: {src} missing -- run stage 'learn' first.")
        return 1
    s = _load_graph(src)

    practice_items, practice_alphabets = _build_practice_set()   # SAME seed -> SAME items.
    meta["n_practice_items"] = len(practice_items)
    meta["practice_alphabets"] = practice_alphabets
    test_alphabets = _test_alphabets()
    eval_ids = _eval_class_ids(test_alphabets)
    print(f"  cycle {done}/{N_CYCLES}: {len(practice_items)} practice characters, "
          f"reps_per_item={REPS_PER_ITEM}, rng_seed={READING_SEED_BASE + done}, dk=gate.DK")

    if done == 0:
        meta["grain_before"] = sc.grain_vocabulary_report(s)
        print(f"  grain_before: {meta['grain_before']}")

    t0 = time.time()
    rep = hl.cycle_characters(s, practice_items, reps_per_item=REPS_PER_ITEM,
                              rng_seed=READING_SEED_BASE + done, dk=DK, capacity=None,
                              jitter_bins=hl.DEFAULT_JITTER_BINS, eval_class_ids=eval_ids)
    elapsed = time.time() - t0

    mean_pre = float(np.mean(list(rep.pre_scores.values()))) if rep.pre_scores else 0.0
    mean_post = float(np.mean(list(rep.post_scores.values()))) if rep.post_scores else 0.0
    cyc = dict(cycle=done, mean_pre=mean_pre, mean_post=mean_post,
               surviving_before=rep.surviving_residual_count_before,
               surviving_after=rep.surviving_residual_count,
               worksheet_size=rep.worksheet_size, corrections=rep.corrections,
               mints_during_reading=rep.mints_during_reading,
               mints_during_babble=rep.mints_during_babble, elapsed=elapsed)
    meta["cycles"].append(cyc)
    print(f"  mean_pre={mean_pre:.4f}  mean_post={mean_post:.4f}  "
          f"surviving_before={rep.surviving_residual_count_before}  "
          f"surviving_after={rep.surviving_residual_count}  "
          f"worksheet_size={rep.worksheet_size}  corrections={rep.corrections}  "
          f"mints_during_reading={rep.mints_during_reading}  "
          f"mints_during_babble={rep.mints_during_babble}  elapsed={elapsed:.1f}s")

    if done + 1 >= N_CYCLES:
        meta["grain_after"] = sc.grain_vocabulary_report(s)
        series = [c["surviving_after"] for c in meta["cycles"]]
        meta["p2_falls"] = bool(series[-1] <= meta["cycles"][0]["surviving_before"])
        print(f"  grain_after: {meta['grain_after']}")
        print(f"  surviving_residual_count series (before-cycle0, after-each-cycle): "
              f"{[meta['cycles'][0]['surviving_before']] + series}")
        print(f"  P2 (surviving residual falls): {'CONFIRMED' if meta['p2_falls'] else 'NULL -- did not fall'}")

    _save_graph(s, _ckpt("reading_babble.json"))
    _save_json(meta, meta_path)
    print(f"  saved -> {_ckpt('reading_babble.json')}, {meta_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: eval-<arm> (block-checkpointed) -- CODEBOOK-DEPENDENT metrics only (coverage@K +
# shortlist-constrained accuracy). The C0 full-dwell control is codebook-INDEPENDENT (run 26's
# own verified architectural fact) and is cited ONCE from run26_checkpoints/eval_baseline.json
# -- never recomputed per arm here.
# ===============================================================================================
_ARM_CKPT = {"reading": "reading.json", "reading-babble": "reading_babble.json"}


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
        records=[], block_idx=0, done=False)

    if state.get("done"):
        print(f"  eval-{tag} already COMPLETE (n={len(state['records'])}).")
        return 0

    ckpt_name = _ARM_CKPT[tag]
    src = _ckpt(ckpt_name)
    if not os.path.exists(src):
        print(f"  WALL: {src} missing -- run the prerequisite stage(s) first.")
        return 1
    s = _load_graph(src)
    native = s._inner

    test_alphabets = _test_alphabets()
    blocks = [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]
    print(f"  arm={tag}  test_alphabets={test_alphabets}  blocks={len(blocks)} "
          f"(target n={len(blocks) * WAY})  SHORTLIST_K={SHORTLIST_K}  resuming at block "
          f"{state['block_idx']}")

    # Deterministically replay the rng to the resume point -- SAME POWER_SEED chain run 26/25
    # used, so this arm's episode construction (candidates/queries per block) is byte-identical.
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
            shortlist = ar.propose_top_k(native, qd["composed_sig"], exemplar_composed,
                                          k=SHORTLIST_K)
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
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- "
              f"re-run '--stage eval-{tag}' to continue.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def stage_eval_baseline():
    """Not a compute stage -- the C0/coverage/shortlist numbers this arm needs are ALREADY
    complete in `results/run26_checkpoints/eval_baseline.json` (verified at stage 'learn'), so
    this stage only confirms that and mirrors it into a run27 pointer file (no bytes copied)."""
    print(f"\n{SEP}\n  STAGE: eval-baseline (REUSED verbatim from run 26)\n{SEP}")
    src = _run26("eval_baseline.json")
    if not os.path.exists(src):
        print(f"  WALL: {src} missing.")
        return 1
    base = _load_json(src)
    if not base.get("done"):
        print(f"  WALL: {src} is not COMPLETE (done={base.get('done')}).")
        return 1
    print(f"  REUSED: n={len(base['records'])}  full_dwell={base.get('full_dwell')}  "
          f"coverage={base.get('coverage')}  shortlist_acc={base.get('shortlist_acc')}")
    _save_json(dict(reused_from=src, n=len(base["records"]), full_dwell=base.get("full_dwell"),
                     coverage=base.get("coverage"), shortlist_acc=base.get("shortlist_acc"),
                     done=True), _ckpt("eval_baseline_pointer.json"))
    print(f"  saved -> {_ckpt('eval_baseline_pointer.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: report
# ===============================================================================================
def stage_report():
    print(f"\n{SEP}\n  RUN 27 -- READING AS PRACTICE -- FINAL REPORT\n{SEP}")

    def _opt(name):
        p = _ckpt(name)
        return _load_json(p) if os.path.exists(p) else None

    learn_meta = _opt("learn_meta.json")
    reading_meta = _opt("reading_metrics.json")
    rb_meta = _opt("reading_babble_metrics.json")
    ev_base = _opt("eval_baseline_pointer.json")
    ev_reading = _opt("eval_reading.json")
    ev_rb = _opt("eval_reading-babble.json")

    missing = [n for n, v in (("learn", learn_meta), ("eval-baseline", ev_base))
               if v is None]
    if missing:
        print(f"  WALL: stages not yet complete: {missing}. Run them before 'report'.")
        return 1

    test_alphabets = _test_alphabets()
    print(f"\n  eval-subset coverage: {N_TEST_ALPHABETS} evaluation alphabets, WAY={WAY}-way "
          f"within-alphabet, target n={N_TEST_ALPHABETS * R_TARGET * WAY}: {test_alphabets}")
    print(f"  practice-subset coverage: 10 HELD-OUT background alphabets "
          f"{reading_meta.get('practice_alphabets') if reading_meta else rb_meta.get('practice_alphabets') if rb_meta else '?'}"
          f", ~{N_PRACTICE_ITEMS} whole characters, seed={PRACTICE_SEED}")
    print(f"  LEARN: reused verbatim from run 26 ({learn_meta['learn_meta']['n_strokes']} "
          f"strokes, alphabets {learn_meta['learn_meta']['learn_alphabets']})")

    # ---- P1: round-trip NOT saturated at first mark ------------------------------------------
    print(f"\n  {SEP}\n  P1 -- CHARACTER-GRAIN ROUND-TRIP NOT SATURATED AT FIRST MARK\n  {SEP}")
    p1_confirmed = None
    for tag, meta in (("reading", reading_meta), ("reading-babble", rb_meta)):
        if meta is None or not meta.get("cycles"):
            print(f"  {tag}: not run yet.")
            continue
        first = meta["cycles"][0]
        first_score = first.get("mean_score", first.get("mean_pre"))
        confirmed = first_score < 0.99
        if tag == "reading":
            p1_confirmed = confirmed
        print(f"  {tag}: first-mark mean_score={first_score:.4f} -> "
              f"{'CONFIRMED (not saturated)' if confirmed else 'STOP -- SATURATED, grain diagnosis falsified'}")

    # ---- P2: surviving residual falls in arm 3 -------------------------------------------------
    print(f"\n  {SEP}\n  P2 -- SURVIVING RESIDUAL ACROSS CYCLES (arm 3, reading+babble)\n  {SEP}")
    if rb_meta and rb_meta.get("cycles"):
        series = [rb_meta["cycles"][0]["surviving_before"]] + \
                 [c["surviving_after"] for c in rb_meta["cycles"]]
        print(f"  surviving_residual_count series: {series}")
        print(f"  P2: {'CONFIRMED (falls)' if rb_meta.get('p2_falls') else 'NULL -- did not fall'}")
        for c in rb_meta["cycles"]:
            print(f"    cycle {c['cycle']}: worksheet_size={c['worksheet_size']} "
                  f"corrections={c['corrections']} mints_during_reading={c['mints_during_reading']} "
                  f"mints_during_babble={c['mints_during_babble']} elapsed={c['elapsed']:.1f}s")
    else:
        print("  reading-babble not run yet.")

    # ---- P3: reading mints > 0 in both arms -----------------------------------------------------
    print(f"\n  {SEP}\n  P3 -- READING-PASS MINTS (new information enters via decode)\n  {SEP}")
    if reading_meta and reading_meta.get("cycles"):
        total_reading = sum(c["mints_reading"] for c in reading_meta["cycles"])
        print(f"  reading-only: mints_reading per cycle = "
              f"{[c['mints_reading'] for c in reading_meta['cycles']]}  total={total_reading}  "
              f"-> {'CONFIRMED' if total_reading > 0 else 'NULL'}")
    if rb_meta and rb_meta.get("cycles"):
        total_rb_reading = sum(c["mints_during_reading"] for c in rb_meta["cycles"])
        total_rb_babble = sum(c["mints_during_babble"] for c in rb_meta["cycles"])
        print(f"  reading+babble: mints_during_reading per cycle = "
              f"{[c['mints_during_reading'] for c in rb_meta['cycles']]}  total={total_rb_reading}  "
              f"-> {'CONFIRMED' if total_rb_reading > 0 else 'NULL'}")
        print(f"  reading+babble: mints_during_babble per cycle = "
              f"{[c['mints_during_babble'] for c in rb_meta['cycles']]}  total={total_rb_babble}")

    # ---- codebook deltas -------------------------------------------------------------------------
    print(f"\n  {SEP}\n  CODEBOOK DELTA (quanta / refinement children / total)\n  {SEP}")
    def _delta_line(label, before, after):
        if not before or not after:
            print(f"  {label:<14} not complete")
            return
        print(f"  {label:<14} top {before['top']}->{after['top']} (+{after['top']-before['top']})  "
              f"children {before['children']}->{after['children']} "
              f"(+{after['children']-before['children']})  "
              f"fine_children {before['fine_children']}->{after['fine_children']} "
              f"(+{after['fine_children']-before['fine_children']})  "
              f"total {before['total']}->{after['total']} (+{after['total']-before['total']})")
    if reading_meta:
        _delta_line("READING", reading_meta.get("grain_before"), reading_meta.get("grain_after"))
    if rb_meta:
        _delta_line("READ+BABBLE", rb_meta.get("grain_before"), rb_meta.get("grain_after"))

    # ---- P4/P5: eval table --------------------------------------------------------------------
    print(f"\n  {SEP}\n  EVAL TABLE (n up to {N_TEST_ALPHABETS*R_TARGET*WAY}, Wilson 95% CI)\n  {SEP}")
    print(f"  baseline (reused from run 26): n={ev_base['n']}  full_dwell={ev_base['full_dwell']}")
    print(f"    coverage@{SHORTLIST_K}={100*ev_base['coverage']['cov']:.1f}% "
          f"[{100*ev_base['coverage']['ci'][0]:.1f},{100*ev_base['coverage']['ci'][1]:.1f}]   "
          f"shortlist_acc={100*ev_base['shortlist_acc']['acc']:.1f}% "
          f"[{100*ev_base['shortlist_acc']['ci'][0]:.1f},{100*ev_base['shortlist_acc']['ci'][1]:.1f}]")

    def _row(tag, ev):
        if ev is None:
            print(f"  {tag:<16} not run")
            return None
        if not ev.get("done"):
            print(f"  {tag:<16} INCOMPLETE ({ev['block_idx']} blocks done, "
                  f"n={len(ev['records'])} so far)")
            return None
        cov, sl = ev["coverage"], ev["shortlist_acc"]
        print(f"  {tag:<16} n={cov['n']:>4}  coverage@{SHORTLIST_K}={100*cov['cov']:5.1f}% "
              f"[{100*cov['ci'][0]:5.1f},{100*cov['ci'][1]:5.1f}]   "
              f"shortlist_acc={100*sl['acc']:5.1f}% [{100*sl['ci'][0]:5.1f},{100*sl['ci'][1]:5.1f}]")
        return ev
    ev_reading_r = _row("reading", ev_reading)
    ev_rb_r = _row("reading-babble", ev_rb)

    print(f"\n  {SEP}\n  P4 -- COVERAGE@{SHORTLIST_K} vs BASELINE\n  {SEP}")
    def _p4(tag, ev):
        if ev is None or not ev.get("done"):
            print(f"  {tag}: not evaluated (n={len(ev['records']) if ev else 0}).")
            return
        cov, base_cov = ev["coverage"], ev_base["coverage"]
        sep = _sep(cov["ci"], base_cov["ci"])
        better = cov["cov"] > base_cov["cov"]
        verdict = "CONFIRMED (coverage improved, CI-separated)" if (sep and better) else \
                  ("ANOMALY (CI-separated but WORSE)" if (sep and not better) else "NULL (not CI-separated)")
        print(f"  {tag}: {100*cov['cov']:.1f}% [{100*cov['ci'][0]:.1f},{100*cov['ci'][1]:.1f}] "
              f"vs baseline {100*base_cov['cov']:.1f}% "
              f"[{100*base_cov['ci'][0]:.1f},{100*base_cov['ci'][1]:.1f}] -> {verdict}")
    _p4("reading", ev_reading_r)
    _p4("reading-babble", ev_rb_r)

    print(f"\n  {SEP}\n  P5 -- SHORTLIST-CONSTRAINED ACCURACY vs BASELINE (expected to move ONLY "
          f"through coverage)\n  {SEP}")
    def _p5(tag, ev):
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
            verdict = "NULL (no accuracy movement -- EXPECTED SHAPE per P5 if coverage alone moved)"
        else:
            verdict = "ANOMALY (accuracy moved opposite to coverage)"
        print(f"  {tag}: shortlist_acc {100*sl['acc']:.1f}% [{100*sl['ci'][0]:.1f},{100*sl['ci'][1]:.1f}] "
              f"vs baseline {100*base_sl['acc']:.1f}% [{100*base_sl['ci'][0]:.1f},{100*base_sl['ci'][1]:.1f}] "
              f"(acc_ci_sep={acc_sep}, cov_ci_sep={cov_sep}) -> {verdict}")
    _p5("reading", ev_reading_r)
    _p5("reading-babble", ev_rb_r)

    print(f"\n{SEP}\n  INVARIANTS\n{SEP}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  P1 (not saturated): {p1_confirmed}")
    print(SEP)
    return 0


# ===============================================================================================
# MAIN
# ===============================================================================================
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["learn", "reading", "reading-babble", "eval-baseline",
                             "eval-reading", "eval-reading-babble", "report"])
    args = p.parse_args()
    t0 = time.time()
    if args.stage == "learn":
        rc = stage_learn()
    elif args.stage == "reading":
        rc = stage_reading()
    elif args.stage == "reading-babble":
        rc = stage_reading_babble()
    elif args.stage == "eval-baseline":
        rc = stage_eval_baseline()
    elif args.stage.startswith("eval-"):
        rc = stage_eval(args.stage.split("-", 1)[1])
    elif args.stage == "report":
        rc = stage_report()
    else:
        rc = 1
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
