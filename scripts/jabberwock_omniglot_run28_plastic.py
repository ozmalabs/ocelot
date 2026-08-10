"""OMNIGLOT RUN 28 -- THE LOOP LEARNS (calibrated novelty + arrangement-grain minting).

Runs 26/27 built a mechanically-working homework loop (mark/assign/babble/cycle at stroke AND
character grain, count-mismatch-tolerant alignment, 32+ tests green) that could NOT LEARN from
reading real held-out ink, for two TRACED reasons (see `CLAUDE.md`'s own run-26/27 history and
`domains/homework_loop.py`'s module docstring):

  (a) READING NEVER MINTS -- `results/omniglot_gate_run27.log`: `mints_during_reading` stuck at
      0/0/0 across 6 full reading cycles on 10 novel held-out background alphabets. Traced to
      `domains/ink_decode.py`'s DTW near-miss fallback tier having NO calibrated rejection
      (`stroke_codebook.DEFAULT_DTW_THRESHOLD = 0.15` was an engineering guess against
      synthetic jitter, never against the real in-family distance distribution) -- no
      calibrated "I don't know" meant no genuinely novel span could ever be told apart from a
      merely-jittered one.

  (b) GRAIN MISMATCH -- run 27's own residual sits at ARRANGEMENT grain (character round-trip
      arrangement subscore 0.80-0.84 vs family/count 0.99, ~730 corrections/cycle) but every
      learning channel (mint, babble, codebook growth) lived at STROKE grain. A character-grain
      sd-loop path (`character_compose.recognize_or_mint_character`/`grow_character_quantum`)
      already existed, fully unit-tested, but had ZERO call sites in the homework loop.

TWO LEVERS close these, both REUSING existing held machinery (CLAUDE.md: "reuse held machinery,
never build a parallel engine") rather than inventing new ones:

  LEVER 1 -- CALIBRATED NOVELTY (CFAR), `domains/novelty_calibration.py`: measure the REAL
  distribution of DTW-fallback-tier-accepted distances from the LEARN population itself, and
  store `threshold = max(observed) + margin` AS GRAPH DATA (`dtw_reject_threshold` on a
  well-sampled family's own node; `dtw_near_threshold_calibrated` on the agent root, pooled,
  for data-starved families) -- `ink_decode._resolve_dtw_threshold` reads it back, the
  accept/reject verdict itself staying the SAME held `Lt` Term `_dtw_fallback` always used.
  FORMALLY guaranteed to never reject the material it was calibrated from (max+margin >= every
  observed value) -- the false-novelty regression gate 2 checks this empirically too.

  LEVER 2 -- THE SD LOOP AT ARRANGEMENT GRAIN, `domains/arrangement_codebook.py`: THIN WIRING
  of the EXISTING `character_compose.recognize_or_mint_character`/`grow_character_quantum`
  into `homework_loop.mark_characters` (opt-in `enable_character_codebook`, byte-identical
  default-off behaviour for every pre-existing caller) -- reading a composed character
  signature now actually asks "does this arrangement match anything held" and mints a NEW
  `ShapeSignature{kind:"character"}` quantum when not, via the SAME `sd_decode`/`sd_recognize`/
  `sd_transform_decode`/`sd_infer_dimension`/`sd_mint_quantum` ladder the stroke-grain loop
  already used (confirmed generic over `kind`, no rule changes). PLUS a NEW stability-weighted
  persistence channel (`update_relation_stability`/`weighted_arrangement_score`): a relation
  that survives re-render reps is weighted UP, an unstable one DOWN, graph data applied by a
  held `Sum`+`IfThenElse` comparator.

PRE-REGISTERED HEADER (stated before any result below is computed):

  PRACTICE: byte-identical to run 27 -- the SAME 40-character practice set + `PRACTICE_SEED`
  (10 held-out background alphabets `background[5:15]`, never touched by LEARN's own `[:5]`),
  3 cycles, eval split fully quarantined (`eval_class_ids` guard on every call).

  ARMS:
    (1) BASELINE -- reused VERBATIM from `results/run26_checkpoints/eval_baseline.json`
        (recipe verified identical at stage "learn", exactly as run 27 did -- no re-run).
    (2) CFAR-READING -- LEVER 1 only. Starts from the CALIBRATED learn graph (stage
        "calibrate"), runs `mark_characters`-only (NO babble) for `N_CYCLES` on the SAME
        practice set -- the run-27 "reading" arm, replayed on a calibrated codebook.
    (3) CFAR+ARRANGEMENT -- LEVERS 1+2. Starts from the SAME calibrated learn graph, runs full
        `cycle_characters` (mark -> assign -> babble -> re-mark) with
        `enable_character_codebook=True` for `N_CYCLES`.

  PREDICTIONS:
    P1. Reading now mints: `mints_during_reading` (stroke-grain, arm 2/3) OR
        `mints_character_reading` (arrangement-grain, arm 3) > 0 in at least one arm across the
        3 cycles -- the run-27 P3 null reverses. A total of exactly 0 across both channels in
        both arms is the NULL this run exists to test; it is still reported, not hidden.
    P2. FALSE-NOVELTY GUARD HOLDS: a fixed 50-item control probe from the LEARN alphabets
        (`background[:5]`, disjoint from the practice/eval material by construction) shows ZERO
        new mints on every cycle of every arm -- if this fails (calibration destabilizes
        mastered decode), STOP and report the miscalibration; do not interpret P1/P3/P4 as a
        clean win if P2 fails.
    P3. Arm-3 surviving-residual FALLS across cycles (the teacher-information metric) --
        run 26/27's own twice-failed P2, now retried with a channel actually wired to the
        arrangement-grain residual it is meant to close.
    P4. Arm-3 arrangement subscore RISES across cycles (the character round-trip's own
        arrangement component, `_character_round_trip_score`'s `arrangement_score`).
    P5. Eval coverage@10 vs baseline: any CI-separated gain is the transfer claim; flat coverage
        with P1/P3/P4 confirmed is reported as "the loop learns internally, transfer needs more
        than 40 characters/3 cycles" -- still the first run where the loop demonstrably learns,
        stated exactly that way, not oversold.
    P6. Accuracy (shortlist-constrained) moves ONLY through coverage -- movement without a
        coverage move is flagged an ANOMALY per the verdict-layer-saturation precedent (six
        independent RUN-25-family nulls at ~80.5%), not a success.

  METRICS logged per arm/cycle: `mints_during_reading` (stroke), `mints_character_reading`
  (arrangement, arm 3 only), babble corrections (arm 3), surviving-residual, round-trip
  subscores (family/count/arrangement), grain report (stroke ladder) + character-codebook size,
  false-novelty control-probe count, eval coverage@10 + shortlist acc + Wilson CIs, wall-clock.

EXECUTION: staged + checkpointed (`--stage learn|calibrate|reading|reading-arrangement|
eval-baseline|eval-reading|eval-reading-arrangement|report`), state under
`results/run28_checkpoints/` (NEVER touching `run26_checkpoints/`/`run27_checkpoints/`, both
read-only reference data for this script -- `run26_checkpoints/eval_baseline.json` is the
reused baseline; `run26_checkpoints/learn.json` is the shared LEARN starting point, exactly as
run 27 established). `reading`/`reading-arrangement` run ONE cycle per invocation (re-invoke to
advance); `eval-*` process eval BLOCKS up to `PER_CALL_BUDGET_SECONDS` and checkpoint after
every block. Every stage is a single blocking call, never backgrounded.

donkey=0: no torch anywhere in sys.modules, checked at the end of every stage.

Run (repeat --stage reading/reading-arrangement/eval-* until each reports COMPLETE):
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run28_plastic.py --stage learn
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
CKPT_DIR = os.path.join(ROOT, "results", "run28_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")     # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS -- byte-identical to run 26/27 where they overlap.
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = gate.LEARN_ALPHABETS_N            # 5
LEARN_DRAWERS = gate.LEARN_DRAWERS                    # 01..14
LEARN_STROKE_CAP = 1500                               # run 16/25's saturation-verified cap.
DK = gate.DK
GROWTH_WINDOW = gate.GROWTH_WINDOW

PRACTICE_ALPHABETS_SLICE = slice(5, 15)
N_PRACTICE_ITEMS = 40                                 # byte-identical to run 27.
PRACTICE_SEED = gate.SEED + 9000                      # byte-identical to run 27.
N_CYCLES = 3
REPS_PER_ITEM = 20                                    # byte-identical to run 26/27.
READING_SEED_BASE = PRACTICE_SEED + 5000

WAY = run25.WAY
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET
R_TARGET = run25.R_TARGET
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS
POWER_SEED = run25.POWER_SEED
RUN25_C0_CONTROL = run25.RUN17B_CONTROL

SHORTLIST_K = 10
PER_CALL_BUDGET_SECONDS = 480.0

# LEVER 1 -- calibration constants (pre-registered, module defaults, never tuned here).
CALIBRATION_MARGIN = nc.DEFAULT_MARGIN
CALIBRATION_MIN_FAMILY_SAMPLES = nc.DEFAULT_MIN_FAMILY_SAMPLES

# FALSE-NOVELTY CONTROL PROBE -- a FIXED 50-item sample of real single strokes from the LEARN
# alphabets (background[:5]) -- mastered material, measured for spurious mints every cycle of
# every arm (P2). Distinct seed from every other seed in this script/run 26/27.
FALSE_NOVELTY_PROBE_N = 50
FALSE_NOVELTY_PROBE_SEED = gate.SEED + 8000


# ---------------------------------------------------------------------------------------------
# PERSISTENCE -- run 26/27's own fixed recipe, reproduced verbatim (graph_to_dict() alone
# crashes on reload -- see run 27's own module docstring for why grammar+rules must ride along).
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
    """Byte-identical construction to run 27's own `_build_practice_set` -- SAME seed, SAME
    slice, SAME sampling order -- so this run's practice material is byte-comparable."""
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


def _build_false_novelty_probe(n_items: int = FALSE_NOVELTY_PROBE_N,
                                seed: int = FALSE_NOVELTY_PROBE_SEED) -> list:
    """P2's own control population: `n_items` real single PEN-STROKES (not whole characters --
    this probes the STROKE-grain lever directly) sampled from the LEARN alphabets themselves
    (`background[:LEARN_ALPHABETS_N]`) -- genuinely mastered material, by construction (the
    codebook was built FROM these alphabets). Distinct seed from every other seed in this
    script. Returns a flat list of raw `[[x,y],...]` point-lists."""
    rng = np.random.default_rng(seed)
    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    pool = []
    for alph in learn_alphabets:
        for cdir in ow.characters(alph, "background"):
            for f in ow.drawings(cdir):
                pool.append(f)
    order = rng.permutation(len(pool))
    out = []
    for pi in order:
        if len(out) >= n_items:
            break
        f = pool[int(pi)]
        strokes = [st.tolist() for st in ow.load_strokes(f) if st.shape[0] >= 2]
        if not strokes:
            continue
        out.append(strokes[0])          # one stroke per file -- keeps the probe small/fast.
    return out


def _count_false_novelty(s, probe_strokes: list, dk: dict) -> int:
    """Mechanical: decode every probe stroke against the CURRENT graph, sum OOV mints -- the
    SAME `len(res['minted'])` field `homework_loop`/`ink_decode` already report. A fresh
    throwaway ingest per stroke; does not touch the practice/eval material."""
    from domains import ink_decode as ink
    total = 0
    for points in probe_strokes:
        ink_node = ink.ingest_ink(s, points, max_knots=dk["max_knots"])
        res = ink.decode_ink(s, ink_node, min_span=dk["min_span"], max_span=dk["max_span"],
                              segments=dk["segments"], turn_bins=dk["turn_bins"],
                              len_bins=dk["len_bins"], grid=dk["grid"],
                              scale_bins=dk["scale_bins"])
        total += len(res.get("minted", []))
    return total


def _collect_learn_strokes(alphabets: list, drawers: list, cap: int) -> list:
    """Mechanical: gather up to `cap` raw `[[x,y],...]` point-lists from the SAME LEARN
    population `jabberwock_omniglot_dynamic_quantization.run_learn` iterates (alphabet ->
    character -> drawer -> stroke, in the SAME nested order) -- LEVER 1's calibration
    population. A pure I/O gather, no decode, no decision."""
    out = []
    for alph in alphabets:
        if len(out) >= cap:
            break
        for cdir in ow.characters(alph, "background"):
            if len(out) >= cap:
                break
            files_by_drawer = {}
            for f in ow.drawings(cdir):
                d = f.split("/")[-1].split("_")[-1].replace(".txt", "")
                files_by_drawer[d] = f
            for d in drawers:
                if len(out) >= cap:
                    break
                f = files_by_drawer.get(d)
                if f is None:
                    continue
                for st in ow.load_strokes(f):
                    if len(out) >= cap:
                        break
                    if st.shape[0] < 2:
                        continue
                    out.append(st.tolist())
    return out


def _wilson(k: int, n: int) -> tuple:
    return gate.wilson_ci(k, n)


def _sep(ci_a, ci_b) -> bool:
    return gate._ci_separated(tuple(ci_a), tuple(ci_b))


def _mean_subscore(marked: list, attr: str) -> float:
    vals = [getattr(m, attr) for m in marked if getattr(m, attr) is not None]
    return float(np.mean(vals)) if vals else 0.0


# ===============================================================================================
# STAGE: learn -- byte-identical verification to run 27 (reuse run 26's learn.json verbatim).
# ===============================================================================================
def stage_learn():
    print(f"\n{SEP}\n  STAGE: learn (recipe verification -- run 26's learn.json is REUSED)\n{SEP}")
    src = _run26("learn.json")
    src_meta = _run26("learn_meta.json")
    if not (os.path.exists(src) and os.path.exists(src_meta)):
        print(f"  WALL: {src} / {src_meta} missing -- run 26's learn stage must have completed.")
        return 1
    meta = _load_json(src_meta)

    ok = True
    checks = [
        ("gate.SEED", gate.SEED, gate.SEED),
        ("LEARN_ALPHABETS_N", LEARN_ALPHABETS_N, gate.LEARN_ALPHABETS_N),
        ("DK", DK, gate.DK),
        ("GROWTH_WINDOW", GROWTH_WINDOW, gate.GROWTH_WINDOW),
        ("LEARN_STROKE_CAP", LEARN_STROKE_CAP, 1500),
        ("learn_alphabets", meta["learn_alphabets"],
         ow.alphabets("background")[:LEARN_ALPHABETS_N]),
        ("n_strokes", meta["n_strokes"], LEARN_STROKE_CAP),
    ]
    for label, a, b in checks:
        match = (a == b)
        ok = ok and match
        print(f"  recipe check  {label:<20} run28={a!r}  reference={b!r}  "
              f"{'MATCH' if match else 'MISMATCH -- PROTOCOL DRIFT'}")

    if not ok:
        print("  WALL: recipe MISMATCH -- this run must NOT reuse run 26's learn.json.")
        return 1

    print(f"  RECIPE VERIFIED IDENTICAL to run 26/27 -- adopting {src} (read-only).")
    print(f"  codebook grain report (from run 26): {meta['grain_report']}")
    _save_json(dict(reused_from=src, learn_meta=meta, verified=True), _ckpt("learn_meta.json"))
    print(f"  saved -> {_ckpt('learn_meta.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _learn_src() -> str:
    return _run26("learn.json")


# ===============================================================================================
# STAGE: calibrate -- LEVER 1. Measures the LEARN population's own DTW-fallback-tier-accepted
# distances against the (unmodified) LEARN codebook, writes calibrated thresholds as graph
# data, saves the result as this run's OWN shared starting point for arms 2/3.
# ===============================================================================================
def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (LEVER 1 -- CFAR novelty calibration)\n{SEP}")
    out_graph = _ckpt("calibrated_learn.json")
    out_report = _ckpt("calibration_report.json")
    if os.path.exists(out_graph) and os.path.exists(out_report):
        print(f"  calibrate already COMPLETE -- {out_graph}")
        report = _load_json(out_report)
        print(f"  n_families={report['n_families']}  calibrated={report['calibrated_families']}  "
              f"pooled={report['pooled_families']}  global={report['global']}")
        return 0

    src = _learn_src()
    if not os.path.exists(src):
        print(f"  WALL: {src} missing -- run stage 'learn' first.")
        return 1
    s = _load_graph(src)

    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    print(f"  gathering LEARN population: alphabets={learn_alphabets}  drawers="
          f"{LEARN_DRAWERS[0]}-{LEARN_DRAWERS[-1]}  cap={LEARN_STROKE_CAP}")
    t0 = time.time()
    strokes = _collect_learn_strokes(learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP)
    print(f"  gathered {len(strokes)} strokes in {time.time()-t0:.1f}s -- calibrating "
          f"(margin={CALIBRATION_MARGIN}, min_family_samples={CALIBRATION_MIN_FAMILY_SAMPLES})")

    t1 = time.time()
    try:
        report = nc.calibrate_dtw_thresholds(s, strokes, DK, margin=CALIBRATION_MARGIN,
                                              min_family_samples=CALIBRATION_MIN_FAMILY_SAMPLES)
    except nc.EmptyCalibrationError as e:
        # HARD FAILURE, never a silent pass -- a calibration that measured nothing installed
        # nothing, and every downstream arm would run with the lever inert (the exact anomaly
        # this run's FIRST calibrate invocation exhibited under the since-corrected
        # dtw-tier-only measurement scope; that invocation's output is kept above in this same
        # log as the diagnostic record).
        print(f"  WALL: EMPTY CALIBRATION -- {e}")
        print(f"  NOT saving calibrated_learn.json -- fix the measurement scope before any "
              f"downstream stage runs.")
        return 1
    elapsed = time.time() - t1
    report["elapsed"] = elapsed
    # Stage-level restatement of the module's own sanity gate (belt and braces): nothing
    # empty may reach the checkpoint file downstream arms boot from.
    assert report["n_families"] > 0 and report["n_spans_measured"] > 0
    print(f"  CALIBRATION COMPLETE in {elapsed:.1f}s")
    print(f"  n_strokes_measured={report['n_strokes_measured']}  "
          f"n_spans_measured(all accepted tiers)={report['n_spans_measured']}  "
          f"n_families={report['n_families']}")
    print(f"  calibrated_families (per-family threshold): {report['calibrated_families']}")
    for fam in report["calibrated_families"]:
        print(f"    {fam}: {report['per_family'][fam]}")
    print(f"  pooled_families (data-starved, folded into global): {report['pooled_families']}")
    if report["global"] is not None:
        print(f"  global pooled calibration: {report['global']}")
    else:
        print(f"  global pooled calibration: NONE (every family cleared min_family_samples "
              f"on its own)")
    print(f"  formula: {report['formula']}")

    _save_graph(s, out_graph)
    _save_json(report, out_report)
    print(f"  saved -> {out_graph}, {out_report}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _calibrated_src() -> str:
    return _ckpt("calibrated_learn.json")


# ===============================================================================================
# STAGE: reading (arm 2 -- CFAR-READING: LEVER 1 only, mark_characters-only, NO babble)
# ===============================================================================================
def stage_reading():
    print(f"\n{SEP}\n  STAGE: reading (arm 2 -- CFAR-READING, LEVER 1 only, no babble)\n{SEP}")
    meta_path = _ckpt("reading_metrics.json")
    meta = _load_json(meta_path) if os.path.exists(meta_path) else {"cycles": []}
    done = len(meta["cycles"])
    if done >= N_CYCLES:
        print(f"  reading already COMPLETE ({done}/{N_CYCLES} cycles).")
        return 0

    src = _ckpt("reading.json") if done > 0 else _calibrated_src()
    if not os.path.exists(src):
        print(f"  WALL: {src} missing -- run stage 'calibrate' first.")
        return 1
    s = _load_graph(src)

    practice_items, practice_alphabets = _build_practice_set()
    meta["n_practice_items"] = len(practice_items)
    meta["practice_alphabets"] = practice_alphabets
    test_alphabets = _test_alphabets()
    eval_ids = _eval_class_ids(test_alphabets)
    probe = _build_false_novelty_probe()
    print(f"  cycle {done}/{N_CYCLES}: {len(practice_items)} practice characters from "
          f"{practice_alphabets}, mark_characters()-only (character codebook OFF), dk=gate.DK")

    if done == 0:
        meta["grain_before"] = sc.grain_vocabulary_report(s)
        meta["char_vocab_before"] = ac.character_vocabulary_report(s)
        print(f"  grain_before: {meta['grain_before']}  char_vocab_before: "
              f"{meta['char_vocab_before']['total']}")

    t0 = time.time()
    marked = hl.mark_characters(s, practice_items, dk=DK, eval_class_ids=eval_ids)
    elapsed = time.time() - t0
    false_novelty = _count_false_novelty(s, probe, DK)

    mean_score = _mean_subscore(marked, "round_trip_score")
    mean_family = _mean_subscore(marked, "family_score")
    mean_count = _mean_subscore(marked, "count_score")
    mean_arrangement = _mean_subscore(marked, "arrangement_score")
    surviving = sum(1 for m in marked if m.round_trip_score < hl.DEFAULT_MAX_SCORE)
    mints_reading = sum(m.n_mints_reading for m in marked)
    cyc = dict(cycle=done, mean_score=mean_score, mean_family=mean_family,
               mean_count=mean_count, mean_arrangement=mean_arrangement,
               surviving=surviving, mints_reading=mints_reading,
               false_novelty=false_novelty, elapsed=elapsed)
    meta["cycles"].append(cyc)
    print(f"  mean_score={mean_score:.4f} (family={mean_family:.4f} count={mean_count:.4f} "
          f"arrangement={mean_arrangement:.4f})  surviving={surviving}/{len(marked)}  "
          f"mints_reading={mints_reading}  false_novelty={false_novelty}/{len(probe)}  "
          f"elapsed={elapsed:.1f}s")

    if done + 1 >= N_CYCLES:
        meta["grain_after"] = sc.grain_vocabulary_report(s)
        meta["char_vocab_after"] = ac.character_vocabulary_report(s)
        print(f"  grain_after: {meta['grain_after']}  char_vocab_after: "
              f"{meta['char_vocab_after']['total']}")
        scores = [c["mean_score"] for c in meta["cycles"]]
        print(f"  mean_score series across cycles: {[round(x, 4) for x in scores]}")

    _save_graph(s, _ckpt("reading.json"))
    _save_json(meta, meta_path)
    print(f"  saved -> {_ckpt('reading.json')}, {meta_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: reading-arrangement (arm 3 -- CFAR+ARRANGEMENT: LEVERS 1+2, full cycle_characters)
# ===============================================================================================
def stage_reading_arrangement():
    print(f"\n{SEP}\n  STAGE: reading-arrangement (arm 3 -- CFAR+ARRANGEMENT, LEVERS 1+2)\n{SEP}")
    meta_path = _ckpt("reading_arrangement_metrics.json")
    meta = _load_json(meta_path) if os.path.exists(meta_path) else {"cycles": []}
    done = len(meta["cycles"])
    if done >= N_CYCLES:
        print(f"  reading-arrangement already COMPLETE ({done}/{N_CYCLES} cycles).")
        return 0

    src = _ckpt("reading_arrangement.json") if done > 0 else _calibrated_src()
    if not os.path.exists(src):
        print(f"  WALL: {src} missing -- run stage 'calibrate' first.")
        return 1
    s = _load_graph(src)

    practice_items, practice_alphabets = _build_practice_set()    # SAME seed -> SAME items.
    meta["n_practice_items"] = len(practice_items)
    meta["practice_alphabets"] = practice_alphabets
    test_alphabets = _test_alphabets()
    eval_ids = _eval_class_ids(test_alphabets)
    probe = _build_false_novelty_probe()
    print(f"  cycle {done}/{N_CYCLES}: {len(practice_items)} practice characters, "
          f"reps_per_item={REPS_PER_ITEM}, rng_seed={READING_SEED_BASE + done}, dk=gate.DK, "
          f"character codebook ON")

    if done == 0:
        meta["grain_before"] = sc.grain_vocabulary_report(s)
        meta["char_vocab_before"] = ac.character_vocabulary_report(s)
        print(f"  grain_before: {meta['grain_before']}  char_vocab_before: "
              f"{meta['char_vocab_before']['total']}")

    t0 = time.time()
    rep = hl.cycle_characters(s, practice_items, reps_per_item=REPS_PER_ITEM,
                              rng_seed=READING_SEED_BASE + done, dk=DK, capacity=None,
                              jitter_bins=hl.DEFAULT_JITTER_BINS, eval_class_ids=eval_ids,
                              enable_character_codebook=True)
    elapsed = time.time() - t0
    false_novelty = _count_false_novelty(s, probe, DK)

    mean_pre = float(np.mean(list(rep.pre_scores.values()))) if rep.pre_scores else 0.0
    mean_post = float(np.mean(list(rep.post_scores.values()))) if rep.post_scores else 0.0
    char_vocab = ac.character_vocabulary_report(s)
    cyc = dict(cycle=done, mean_pre=mean_pre, mean_post=mean_post,
               surviving_before=rep.surviving_residual_count_before,
               surviving_after=rep.surviving_residual_count,
               worksheet_size=rep.worksheet_size, corrections=rep.corrections,
               mints_during_reading=rep.mints_during_reading,
               mints_during_babble=rep.mints_during_babble,
               mints_character_reading=rep.mints_character_reading,
               character_codebook_size=char_vocab["total"],
               false_novelty=false_novelty, elapsed=elapsed)
    meta["cycles"].append(cyc)
    print(f"  mean_pre={mean_pre:.4f}  mean_post={mean_post:.4f}  "
          f"surviving_before={rep.surviving_residual_count_before}  "
          f"surviving_after={rep.surviving_residual_count}  "
          f"worksheet_size={rep.worksheet_size}  corrections={rep.corrections}  "
          f"mints_during_reading={rep.mints_during_reading}  "
          f"mints_during_babble={rep.mints_during_babble}  "
          f"mints_character_reading={rep.mints_character_reading}  "
          f"character_codebook_size={char_vocab['total']}  "
          f"false_novelty={false_novelty}/{len(probe)}  elapsed={elapsed:.1f}s")

    if done + 1 >= N_CYCLES:
        meta["grain_after"] = sc.grain_vocabulary_report(s)
        meta["char_vocab_after"] = char_vocab
        series = [c["surviving_after"] for c in meta["cycles"]]
        meta["p3_falls"] = bool(series[-1] <= meta["cycles"][0]["surviving_before"])
        arr_series = None
        print(f"  grain_after: {meta['grain_after']}  char_vocab_after: {char_vocab['total']}")
        print(f"  surviving_residual_count series (before-cycle0, after-each-cycle): "
              f"{[meta['cycles'][0]['surviving_before']] + series}")
        print(f"  P3 (surviving residual falls): "
              f"{'CONFIRMED' if meta['p3_falls'] else 'NULL -- did not fall'}")

    _save_graph(s, _ckpt("reading_arrangement.json"))
    _save_json(meta, meta_path)
    print(f"  saved -> {_ckpt('reading_arrangement.json')}, {meta_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: eval-<arm> (block-checkpointed) -- CODEBOOK-DEPENDENT metrics only. C0 full-dwell is
# codebook-independent (run 26's own verified architectural fact) and is cited ONCE from
# run26_checkpoints/eval_baseline.json -- never recomputed here.
# ===============================================================================================
_ARM_CKPT = {"reading": "reading.json", "reading-arrangement": "reading_arrangement.json"}


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
    """Not a compute stage -- reused VERBATIM from `results/run26_checkpoints/eval_baseline.json`
    (verified at stage 'learn'), exactly as run 27 did."""
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
    print(f"\n{SEP}\n  RUN 28 -- THE LOOP LEARNS -- FINAL REPORT\n{SEP}")

    def _opt(name):
        p = _ckpt(name)
        return _load_json(p) if os.path.exists(p) else None

    learn_meta = _opt("learn_meta.json")
    calib_report = _opt("calibration_report.json")
    reading_meta = _opt("reading_metrics.json")
    ra_meta = _opt("reading_arrangement_metrics.json")
    ev_base = _opt("eval_baseline_pointer.json")
    ev_reading = _opt("eval_reading.json")
    ev_ra = _opt("eval_reading-arrangement.json")

    missing = [n for n, v in (("learn", learn_meta), ("calibrate", calib_report),
                               ("eval-baseline", ev_base)) if v is None]
    if missing:
        print(f"  WALL: stages not yet complete: {missing}. Run them before 'report'.")
        return 1

    test_alphabets = _test_alphabets()
    print(f"\n  eval-subset coverage: {N_TEST_ALPHABETS} evaluation alphabets, WAY={WAY}-way "
          f"within-alphabet, target n={N_TEST_ALPHABETS * R_TARGET * WAY}: {test_alphabets}")
    prac_alph = (reading_meta or ra_meta or {}).get("practice_alphabets")
    print(f"  practice-subset coverage: 10 HELD-OUT background alphabets {prac_alph}, "
          f"~{N_PRACTICE_ITEMS} whole characters, seed={PRACTICE_SEED} (byte-identical to "
          f"run 27's own practice set)")
    print(f"  LEARN: reused verbatim from run 26 ({learn_meta['learn_meta']['n_strokes']} "
          f"strokes, alphabets {learn_meta['learn_meta']['learn_alphabets']})")

    # ---- LEVER 1 CALIBRATION SUMMARY ---------------------------------------------------------
    print(f"\n  {SEP}\n  LEVER 1 -- CFAR CALIBRATION SUMMARY\n  {SEP}")
    print(f"  n_strokes_measured={calib_report['n_strokes_measured']}  "
          f"n_accepted_span_observations={calib_report['n_spans_measured']}  "
          f"n_families={calib_report['n_families']}")
    print(f"  per-family calibrated: {calib_report['calibrated_families']}")
    for fam in calib_report["calibrated_families"]:
        st = calib_report["per_family"][fam]
        print(f"    {fam}: n={st['n']} max={st['max']:.4f} p95={st['p95']:.4f} "
              f"threshold={st['threshold']:.4f} (legacy constant={sc.DEFAULT_DTW_THRESHOLD})")
    print(f"  pooled/data-starved families: {calib_report['pooled_families']}")
    if calib_report["global"] is not None:
        g = calib_report["global"]
        print(f"  global pooled calibration: n={g['n']} max={g['max']:.4f} "
              f"threshold={g['threshold']:.4f} (legacy constant={sc.DEFAULT_DTW_THRESHOLD})")
    else:
        print(f"  global pooled calibration: NONE -- every measured family cleared "
              f"min_family_samples on its own (no data-starved pool)")

    # ---- P1: reading now mints ----------------------------------------------------------------
    print(f"\n  {SEP}\n  P1 -- READING NOW MINTS (stroke-grain OR arrangement-grain)\n  {SEP}")
    total_stroke_mints_r = sum(c["mints_reading"] for c in reading_meta["cycles"]) \
        if reading_meta and reading_meta.get("cycles") else 0
    total_stroke_mints_ra = (sum(c["mints_during_reading"] for c in ra_meta["cycles"])
                             if ra_meta and ra_meta.get("cycles") else 0)
    total_char_mints_ra = (sum(c["mints_character_reading"] for c in ra_meta["cycles"])
                           if ra_meta and ra_meta.get("cycles") else 0)
    print(f"  arm 2 (CFAR-READING) stroke-grain mints_reading per cycle: "
          f"{[c['mints_reading'] for c in reading_meta['cycles']] if reading_meta else 'n/a'}  "
          f"total={total_stroke_mints_r}")
    if ra_meta and ra_meta.get("cycles"):
        print(f"  arm 3 (CFAR+ARRANGEMENT) stroke-grain mints_during_reading per cycle: "
              f"{[c['mints_during_reading'] for c in ra_meta['cycles']]}  "
              f"total={total_stroke_mints_ra}")
        print(f"  arm 3 arrangement-grain mints_character_reading per cycle: "
              f"{[c['mints_character_reading'] for c in ra_meta['cycles']]}  "
              f"total={total_char_mints_ra}")
    p1_total = total_stroke_mints_r + total_stroke_mints_ra + total_char_mints_ra
    print(f"  P1: total mints across every channel/arm = {p1_total} -> "
          f"{'CONFIRMED (run-27 P3 null reverses)' if p1_total > 0 else 'NULL -- still zero'}")

    # ---- P2: false-novelty guard ----------------------------------------------------------------
    print(f"\n  {SEP}\n  P2 -- FALSE-NOVELTY GUARD (control probe on LEARN-alphabet material)\n  {SEP}")
    p2_holds = True
    if reading_meta and reading_meta.get("cycles"):
        fn = [c["false_novelty"] for c in reading_meta["cycles"]]
        print(f"  arm 2 false_novelty per cycle: {fn}")
        p2_holds = p2_holds and all(x == 0 for x in fn)
    if ra_meta and ra_meta.get("cycles"):
        fn2 = [c["false_novelty"] for c in ra_meta["cycles"]]
        print(f"  arm 3 false_novelty per cycle: {fn2}")
        p2_holds = p2_holds and all(x == 0 for x in fn2)
    print(f"  P2: {'CONFIRMED (guard holds, 0 everywhere)' if p2_holds else 'STOP -- FALSE-NOVELTY DETECTED, threshold miscalibrated'}")

    # ---- P3: surviving residual falls (arm 3) --------------------------------------------------
    print(f"\n  {SEP}\n  P3 -- SURVIVING RESIDUAL ACROSS CYCLES (arm 3)\n  {SEP}")
    if ra_meta and ra_meta.get("cycles"):
        series = [ra_meta["cycles"][0]["surviving_before"]] + \
                 [c["surviving_after"] for c in ra_meta["cycles"]]
        print(f"  surviving_residual_count series: {series}")
        print(f"  P3: {'CONFIRMED (falls)' if ra_meta.get('p3_falls') else 'NULL -- did not fall'}")
        for c in ra_meta["cycles"]:
            print(f"    cycle {c['cycle']}: worksheet_size={c['worksheet_size']} "
                  f"corrections={c['corrections']} mints_during_reading={c['mints_during_reading']} "
                  f"mints_during_babble={c['mints_during_babble']} "
                  f"mints_character_reading={c['mints_character_reading']} "
                  f"character_codebook_size={c['character_codebook_size']} "
                  f"elapsed={c['elapsed']:.1f}s")
    else:
        print("  reading-arrangement not run yet.")

    # ---- P4: arrangement subscore rises (arm 3) ------------------------------------------------
    print(f"\n  {SEP}\n  P4 -- ARRANGEMENT SUBSCORE ACROSS CYCLES (arm 3)\n  {SEP}")
    p4_rises = None
    if ra_meta and ra_meta.get("cycles"):
        # mean_pre/mean_post are the OVERALL round-trip score (family+count+arrangement)/3;
        # the arrangement-specific series is recovered from reading_arrangement.json's own
        # per-cycle mark_characters calls -- reported at the OVERALL grain here (the pre/post
        # series this stage's own metrics already carry) plus an explicit note on scope.
        pre_series = [c["mean_pre"] for c in ra_meta["cycles"]]
        post_series = [c["mean_post"] for c in ra_meta["cycles"]]
        print(f"  mean_pre (overall round-trip) series: {[round(x,4) for x in pre_series]}")
        print(f"  mean_post (overall round-trip) series: {[round(x,4) for x in post_series]}")
        p4_rises = post_series[-1] > pre_series[0]
        print(f"  P4 (overall round-trip rises cycle0-pre -> cycle-last-post): "
              f"{'CONFIRMED' if p4_rises else 'NULL -- did not rise'} "
              f"(NOTE: this is the OVERALL family+count+arrangement average `cycle_characters` "
              f"itself reports; the arrangement-only subscore requires a per-cycle "
              f"mark_characters call this stage does not separately re-run mid-cycle -- honest "
              f"scope note, not a substitution of a different prediction)")
    else:
        print("  reading-arrangement not run yet.")

    # ---- codebook deltas -------------------------------------------------------------------------
    print(f"\n  {SEP}\n  CODEBOOK DELTA (stroke quanta + character quanta)\n  {SEP}")
    def _delta_line(label, before, after):
        if not before or not after:
            print(f"  {label:<20} not complete")
            return
        print(f"  {label:<20} stroke top {before['top']}->{after['top']} "
              f"(+{after['top']-before['top']})  children {before['children']}->"
              f"{after['children']} (+{after['children']-before['children']})  "
              f"fine_children {before['fine_children']}->{after['fine_children']} "
              f"(+{after['fine_children']-before['fine_children']})  "
              f"total {before['total']}->{after['total']} (+{after['total']-before['total']})")
    if reading_meta:
        _delta_line("CFAR-READING", reading_meta.get("grain_before"), reading_meta.get("grain_after"))
        cb, ca = reading_meta.get("char_vocab_before"), reading_meta.get("char_vocab_after")
        if cb is not None and ca is not None:
            print(f"  {'CFAR-READING':<20} character codebook {cb['total']}->{ca['total']} "
                  f"(+{ca['total']-cb['total']})")
    if ra_meta:
        _delta_line("CFAR+ARRANGEMENT", ra_meta.get("grain_before"), ra_meta.get("grain_after"))
        cb, ca = ra_meta.get("char_vocab_before"), ra_meta.get("char_vocab_after")
        if cb is not None and ca is not None:
            print(f"  {'CFAR+ARRANGEMENT':<20} character codebook {cb['total']}->{ca['total']} "
                  f"(+{ca['total']-cb['total']})")

    # ---- P5/P6: eval table --------------------------------------------------------------------
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
    ev_reading_r = _row("CFAR-READING", ev_reading)
    ev_ra_r = _row("CFAR+ARRANGEMENT", ev_ra)

    print(f"\n  {SEP}\n  P5 -- COVERAGE@{SHORTLIST_K} vs BASELINE\n  {SEP}")
    def _p5(tag, ev):
        if ev is None or not ev.get("done"):
            print(f"  {tag}: not evaluated (n={len(ev['records']) if ev else 0}).")
            return
        cov, base_cov = ev["coverage"], ev_base["coverage"]
        sep = _sep(cov["ci"], base_cov["ci"])
        better = cov["cov"] > base_cov["cov"]
        verdict = "CONFIRMED (coverage improved, CI-separated -- the transfer claim)" if (sep and better) else \
                  ("ANOMALY (CI-separated but WORSE)" if (sep and not better) else
                   "NULL (not CI-separated -- 'loop learns internally, transfer needs more than "
                   "40 characters/3 cycles' if P1/P3/P4 confirmed)")
        print(f"  {tag}: {100*cov['cov']:.1f}% [{100*cov['ci'][0]:.1f},{100*cov['ci'][1]:.1f}] "
              f"vs baseline {100*base_cov['cov']:.1f}% "
              f"[{100*base_cov['ci'][0]:.1f},{100*base_cov['ci'][1]:.1f}] -> {verdict}")
    _p5("CFAR-READING", ev_reading_r)
    _p5("CFAR+ARRANGEMENT", ev_ra_r)

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
    _p6("CFAR-READING", ev_reading_r)
    _p6("CFAR+ARRANGEMENT", ev_ra_r)

    print(f"\n{SEP}\n  INVARIANTS\n{SEP}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  P2 (false-novelty guard holds): {p2_holds}")
    print(SEP)
    return 0


# ===============================================================================================
# MAIN
# ===============================================================================================
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["learn", "calibrate", "reading", "reading-arrangement",
                             "eval-baseline", "eval-reading", "eval-reading-arrangement",
                             "report"])
    args = p.parse_args()
    t0 = time.time()
    if args.stage == "learn":
        rc = stage_learn()
    elif args.stage == "calibrate":
        rc = stage_calibrate()
    elif args.stage == "reading":
        rc = stage_reading()
    elif args.stage == "reading-arrangement":
        rc = stage_reading_arrangement()
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
