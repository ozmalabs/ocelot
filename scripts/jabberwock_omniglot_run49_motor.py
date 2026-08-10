"""jabberwock_omniglot_run49_motor.py -- RUN 49: THE MOTOR-PROGRAM VERDICT, gated on real pen
data (DigiLeTs), where the motor information demonstrably EXISTS (run 46: 17.1x class-grain
info at the stroke grain) but every prior attempt to USE it was a PROPOSAL, recall-limited, and
nulled three times (UCI/QuickDraw/DigiLeTs, `OMNIGLOT_ARC.md` Addendum 2 + run 48, `8e4b7aee`).
This run builds a real MOTOR DISTANCE (`domains/motor_verdict.py`, designed in PART 1 by the
agent's own composer, `scripts/jabberwock_designs_motor_verdict.py`) and FUSES it into the
whole-shape continuous verdict (never replaces it -- RUN 37A's law) over the FULL candidate set,
no hard shortlist -- run 48's own diagnosis of why the two-layer union harmed (a hard shortlist
gate DISCARDS a correct-but-unshortlisted candidate outright) does not apply here: `argmin` runs
over every candidate, always.

MACHINERY REUSE (per this arc's own convention): imports `scripts.jabberwock_omniglot_
run47_pendata` (`ps.program_score` -- the geo_score(SC+TPS) comparator, `wilson_ci`, `_mcnemar`,
`_md5`, `_donkey0`, `_save_json`/`_load_json`, `RNG_SEED`, `MAX_STROKES`, `DK`,
`_stroke_point_sets_from_arrays`) and `scripts.jabberwock_omniglot_run48_digilets`
(`_load_split`, `_way20_classes`/`_way20_classes_clean` -- the SAME seeded 20-way / homoglyph-
free 20-way-clean class subsets run 48 already used, reused not re-derived, so both runs'
episode draws are directly comparable, `_index_by_writer_class`, `_is_homoglyph_pair`,
`_homoglyph_arm_stats`, `N_BACKGROUND_WRITERS`, `WRITER_SPLIT_SEED`). `domains/pen_world.py` for
the corpus loader. `domains/motor_verdict.py` (this run's own PART 2 build) for the motor
program/distance/fusion.

NO NEW LEARN STAGE: `domains/motor_verdict.py` never fits an edge set of its own -- the FROZEN
adaptive turn/length/delta edges are read READ-ONLY from `results/run48_checkpoints/learn.json`
(that run's own LEARN stage, on the SAME 40 background writers / `WRITER_SPLIT_SEED`) -- this
run never re-fits, never re-grows a codebook, and (since `domains/motor_verdict.py` mints
nothing -- source-audited, `tests/test_motor_verdict_migrated.py`) never touches
`seeds/stroke_shapes.json` at all. The seed-write guard is asserted anyway (this run's own
launch brief's "belt-and-suspenders" requirement), before AND after every stage.

TWO ARMS ONLY (this run drops run 48's hard-gate arm entirely -- it is not the mechanism under
test here, and run 48 already found it harmful under a coverage ceiling that does not even apply
to a no-shortlist fusion):
  (i)  CONTINUOUS-ONLY: `per_stroke_abs.program_score`, `argmin` over candidates -- the number to
       beat (run 48's own DigiLeTs citation: 65.0% [58.5,71.0] 20-way raw / 67.3% [60.8,73.1]
       20-way-clean, n=220, cross-writer).
  (ii) MOTOR-FUSED: `final = geo_score + lam * w_m * m(query, candidate)`, `w_m` spread-matched
       (`--stage spread`) then lambda-scaled (`--stage calibrate`, background-sanity STOP,
       SAME `-3pp` bound run 48/45 used), `argmin` over the FULL candidate set (no shortlist).
PRIMARY: paired McNemar (ii) vs (i), on the SAME episodes, both 20-way and 20-way-CLEAN.
PRE-REGISTERED PREDICTION (stated before any Gate B number is computed): on pen data, the motor
distance ADDS where whole-shape-only cannot -- fixes concentrate in near-duplicate geometry pairs
that DIFFER in stroke program (drawn differently), the orthogonal evidence run 36's own failure
taxonomy said the whole-shape comparator structurally lacks. STOP (pre-registered, no retuning
against eval): background-sanity fail -> report the background curve, hard-stop before eval;
(ii) broken >= fixed on held-out -> the motor verdict does not add even on pen data, a MAJOR
finding reported honestly (either the motor representation is too lossy, or SC+TPS already
implicitly captures the discriminative motor information) -- never retuned against eval.

CONTEXT HONESTY (unchanged from run 48): DigiLeTs is 62-class cross-writer, a HARDER
discrimination than Omniglot's within-alphabet 20-way; the continuous-only baseline is the
comparison, NOT Omniglot's 80.5.

EXECUTION (ops law, binding, unchanged): every invocation <=540s foreground, intra-stage
checkpoints, `.venv` python (needs `substrate_rs`), checkpointed to `results/run49_checkpoints/`
(every other `results/run*_checkpoints/` directory is READ-ONLY reference, never written here).
NEVER run in background; NEVER end a turn with a live process.

Run (from the gamma-substrate repo root):
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run49_motor.py --stage <STAGE>
Stages, in dependency order:
  unit_sanity -> spread -> calibrate -> gate_b_20way -> gate_b_20way_clean -> summary
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import substrate_rs as srs

import scripts.jabberwock_omniglot_run47_pendata as run47
import scripts.jabberwock_omniglot_run48_digilets as run48
from domains import motor_verdict as mv
from domains import pen_world as pw

SEP = "=" * 92
EPS = 1e-9

CKPT_DIR = os.path.join(ROOT, "results", "run49_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
RUN48_CKPT_DIR = os.path.join(ROOT, "results", "run48_checkpoints")
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS -- reused VERBATIM from run 48 where this run shares the same
# population/split/episode convention (never re-derived, so both runs are directly comparable).
# ------------------------------------------------------------------------------------------- #
CALIBRATION_N_EPISODES = run48.CALIBRATION_N_EPISODES     # 150, background-only.
GATE_B_N_EPISODES = run48.GATE_B_N_EPISODES               # 220, matches run 47/48's convention.
LAMBDA_GRID = [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0]          # this run's own pre-registered grid --
                                                           # wider than run 48's since `w_m` has
                                                           # already spread-matched the SCALE, so
                                                           # `lam` here plays run 48's own role
                                                           # (0=off, >1 = motor dominates).
SANITY_MARGIN = run48.SANITY_MARGIN                        # -3pp, transplanted from run 45/48.


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _run48_ckpt(name: str) -> str:
    return os.path.join(RUN48_CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    run47._save_json(obj, path)


def _load_json(path: str):
    return run47._load_json(path)


# ============================================================================================= #
#  STAGE: unit_sanity -- reuse run 47/48's own checkpoints (READ-ONLY citation), verify the
#  seed-write guard, verify domains.motor_verdict mints nothing against REAL DigiLeTs strokes.
# ============================================================================================= #
def stage_unit_sanity():
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    ok_all = True
    md5_before = run47._md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 (BEFORE this run touches anything): {md5_before}")

    print("\n  (a) run-48 LEARN checkpoint present (READ-ONLY citation -- NOT re-fit here)")
    learn_path = _run48_ckpt("learn.json")
    ok_a = os.path.exists(learn_path)
    print(f"      {learn_path}  present={ok_a}")
    ok_all &= ok_a
    if ok_a:
        frozen = _load_json(learn_path)
        print(f"      level_edges (n={len(frozen['level_edges'])})  "
              f"delta_edges (n={len(frozen['delta_edges'])})  tol_deg={frozen['tol_deg']:.4f}  "
              f"seed_guard_ok(run48)={frozen.get('seed_guard_ok')}")

    print("\n  (b) DigiLeTs writer-split loader round-trip (via domains.pen_world, matches "
          "run 48's own split)")
    samples = pw.load_digilets_samples()
    background, heldout = pw.digilets_writer_split(samples, n_background=run48.N_BACKGROUND_WRITERS,
                                                     seed=run48.WRITER_SPLIT_SEED)
    bg_writers = {s["writer_id"] for s in background}
    ho_writers = {s["writer_id"] for s in heldout}
    ok_b = (bg_writers.isdisjoint(ho_writers) and len(background) + len(heldout) == len(samples)
            and len(samples) == 77 * 62 * 5)
    print(f"      n_samples={len(samples)}  n_background={len(background)} "
          f"n_heldout={len(heldout)}  disjoint={bg_writers.isdisjoint(ho_writers)}  -> "
          f"{'PASS' if ok_b else 'FAIL'}")
    ok_all &= ok_b

    print("\n  (c) domains.motor_verdict mints nothing -- CANARY on REAL DigiLeTs strokes "
          "(not synthetic; this run's own launch brief requires re-checking the seed-write "
          "guard regardless of the durable teach() guard landed in 21aa6123)")
    frozen = _load_json(learn_path)
    edges = {"tol_deg": frozen["tol_deg"], "level_edges": frozen["level_edges"],
             "delta_edges": frozen["delta_edges"]}
    canary_samples = heldout[:3]
    native = srs.Substrate()._inner
    progs = [mv.glyph_motor_program(s["strokes"], edges=edges, segments=run47.DK["segments"],
                                     max_knots=run47.DK["max_knots"], max_strokes=run47.MAX_STROKES)
             for s in canary_samples]
    _ = mv.motor_distance(native, progs[0], progs[1])
    md5_after_canary = run47._md5(STROKE_SHAPES_SEED)
    ok_c = (md5_after_canary == md5_before)
    print(f"      canary: {len(progs)} real glyph motor programs built + 1 motor_distance call")
    print(f"      seeds/stroke_shapes.json md5 AFTER canary: {md5_after_canary}  -> "
          f"{'PASS (unchanged)' if ok_c else 'FAIL -- SEED WRITE LEAK, STOP EVERYTHING'}")
    ok_all &= ok_c
    if not ok_c:
        raise SystemExit("HARD STOP: seed-write guard failed on a REAL-DATA canary.")

    print(f"\n{SEP}\n  UNIT SANITY: {'ALL PASS' if ok_all else 'SOME FAILED -- DO NOT PROCEED'}"
          f"\n{SEP}")
    _save_json({"ok_all": ok_all, "stroke_shapes_md5_before": md5_before,
                "n_background_writers": len(bg_writers), "n_heldout_writers": len(ho_writers)},
               _ckpt("unit_sanity.json"))
    print(f"  donkey=0: {'PASS' if run47._donkey0() else 'FAIL'}")
    if not ok_all:
        raise SystemExit(1)
    return 0


def _require_unit_sanity() -> dict:
    path = _ckpt("unit_sanity.json")
    if not os.path.exists(path):
        raise SystemExit("WALL: run --stage unit_sanity first.")
    d = _load_json(path)
    if not d.get("ok_all"):
        raise SystemExit("WALL: unit_sanity did not pass.")
    return d


def _frozen_edges() -> dict:
    frozen = _load_json(_run48_ckpt("learn.json"))
    return {"tol_deg": frozen["tol_deg"], "level_edges": frozen["level_edges"],
            "delta_edges": frozen["delta_edges"]}


# ============================================================================================= #
#  SHARED: writer-split population loading (identical to run 48's own split).
# ============================================================================================= #
def _load_split():
    return run48._load_split()


# ============================================================================================= #
#  EPISODE SCORING -- geo_score (SC+TPS, identical to run 47/48) + motor distance m, ONE pass.
#  A per-process memoization cache on `glyph_motor_program` keyed by (writer_id, class, instance)
#  avoids recomputing the SAME exemplar's motor program across episodes that happen to redraw it
#  (mechanical performance caching, per CLAUDE.md's own explicit carve-out -- "Python may cache
#  for performance, but the substrate is the source of truth"; this cache holds no agent state,
#  no decision, just a pure-function memo keyed on immutable inputs).
# ============================================================================================= #
_PROG_CACHE: dict = {}


def _cached_motor_program(sample: dict, edges: dict) -> dict:
    key = (sample["writer_id"], sample["class"], sample["instance"])
    hit = _PROG_CACHE.get(key)
    if hit is not None:
        return hit
    prog = mv.glyph_motor_program(sample["strokes"], edges=edges, segments=run47.DK["segments"],
                                   max_knots=run47.DK["max_knots"], max_strokes=run47.MAX_STROKES)
    _PROG_CACHE[key] = prog
    return prog


def _score_episodes(samples: list, way_classes: list, n_episodes: int, seed: int,
                     edges: dict, native) -> list:
    """Mirrors `run48._score_episodes` EXACTLY (same RNG-consumption order, same population
    indexing, same cross-writer exemplar/query draw) so this run's own episode draws are
    reproducible against that run's own citation -- the ONLY addition is `m_scores` (this run's
    own motor distance), computed alongside `geo_scores` in the SAME pass."""
    idx = run48._index_by_writer_class(samples)
    writers = sorted(w for w in idx if all(c in idx[w] and len(idx[w][c]) >= 1
                                            for c in way_classes))
    n_way = len(way_classes)
    assert len(writers) >= 2, "need >=2 writers with every way_class present"
    rng = np.random.default_rng(seed)
    episodes = []
    for ep in range(n_episodes):
        true_cls = way_classes[int(rng.integers(0, n_way))]
        ex_writer, ex_sample = {}, {}
        for c in way_classes:
            w = writers[int(rng.integers(0, len(writers)))]
            insts = idx[w][c]
            ex_writer[c] = w
            ex_sample[c] = insts[int(rng.integers(0, len(insts)))]
        other_writers = [w for w in writers if w != ex_writer[true_cls]]
        qw = other_writers[int(rng.integers(0, len(other_writers)))]
        q_insts = idx[qw][true_cls]
        query = q_insts[int(rng.integers(0, len(q_insts)))]

        candidate_samples = [ex_sample[c] for c in way_classes]
        q_ps = run47._stroke_point_sets_from_arrays(query["strokes"])
        cand_ps = [run47._stroke_point_sets_from_arrays(cs["strokes"]) for cs in candidate_samples]
        if not q_ps or any(not cps for cps in cand_ps):
            continue        # degenerate (no usable points) -- honest skip, never a crash.
        geo_scores = [run47.ps.program_score(q_ps, cps) for cps in cand_ps]

        query_prog = _cached_motor_program(query, edges)
        cand_progs = [_cached_motor_program(cs, edges) for cs in candidate_samples]
        m_scores = [mv.motor_distance(native, query_prog, cp)["m"] for cp in cand_progs]

        true_idx = way_classes.index(true_cls)
        episodes.append({"geo_scores": geo_scores, "m_scores": m_scores, "true_idx": true_idx,
                          "ex_writer_true": ex_writer[true_cls], "q_writer": qw})
        if (ep + 1) % 50 == 0:
            print(f"    ... scored {ep+1}/{n_episodes} episodes  "
                  f"[motor-program cache size={len(_PROG_CACHE)}]", flush=True)
    return episodes


# ============================================================================================= #
#  STAGE: spread -- background episodes, derive w_m mechanically (RUN 44b protocol).
# ============================================================================================= #
def stage_spread():
    print(f"\n{SEP}\n  STAGE: spread (background episodes -> spread-matched w_m, RUN 44b "
          f"protocol)\n{SEP}")
    t0 = time.time()
    _require_unit_sanity()
    edges = _frozen_edges()
    background, _ = _load_split()
    native = srs.Substrate()._inner

    way20 = run48._way20_classes()
    way20_clean = run48._way20_classes_clean()
    print(f"  20-way class subset (cited from run 48, NOT re-derived): {way20}")
    print(f"  20-way-CLEAN class subset (cited from run 48, NOT re-derived): {way20_clean}")

    out = {}
    for label, way_classes, seed in (("20way", way20, run47.RNG_SEED + 200),
                                      ("20way_clean", way20_clean, run47.RNG_SEED + 201)):
        print(f"\n  -- background spread, {label} ({len(way_classes)}-way, "
              f"n={CALIBRATION_N_EPISODES}) --")
        episodes = _score_episodes(background, way_classes, CALIBRATION_N_EPISODES, seed,
                                    edges, native)
        geo_per_ep = [e["geo_scores"] for e in episodes]
        m_per_ep = [e["m_scores"] for e in episodes]
        spread_geo = mv.spread_of_scores(geo_per_ep)
        spread_m = mv.spread_of_scores(m_per_ep)
        w_m = mv.derive_w_m(spread_geo, spread_m)
        print(f"    n_episodes_scored={len(episodes)}  spread(geo_score)={spread_geo:.5f}  "
              f"spread(m)={spread_m:.5f}  w_m = spread_geo/spread_m = {w_m:.5f}")
        out[label] = {"way_classes": way_classes, "n_episodes": len(episodes),
                      "spread_geo": spread_geo, "spread_m": spread_m, "w_m": w_m}
        print(f"    [elapsed so far: {time.time()-t0:.1f}s]")

    _save_json(out, _ckpt("spread.json"))
    print(f"\n  saved -> {_ckpt('spread.json')}")
    md5_after = run47._md5(STROKE_SHAPES_SEED)
    us = _require_unit_sanity()
    print(f"  seeds/stroke_shapes.json md5 AFTER spread: {md5_after}  "
          f"UNCHANGED={md5_after == us['stroke_shapes_md5_before']}")
    if md5_after != us["stroke_shapes_md5_before"]:
        raise SystemExit("HARD STOP: seed write detected during --stage spread.")
    print(f"  donkey=0: {'PASS' if run47._donkey0() else 'FAIL'}")
    print(f"  [spread wall time: {time.time()-t0:.1f}s]")
    return 0


def _require_spread() -> dict:
    path = _ckpt("spread.json")
    if not os.path.exists(path):
        raise SystemExit("WALL: run --stage spread first.")
    return _load_json(path)


# ============================================================================================= #
#  STAGE: calibrate -- background-sanity STOP + lambda sweep, FROZEN on background episodes.
# ============================================================================================= #
def _calibrate_one_way(background: list, way_classes: list, w_m: float, edges: dict, label: str,
                        seed: int, native) -> dict:
    print(f"\n  -- calibrating on BACKGROUND writers, {label} ({len(way_classes)}-way, "
          f"n={CALIBRATION_N_EPISODES}, w_m={w_m:.5f} frozen from --stage spread) --")
    t0 = time.time()
    episodes = _score_episodes(background, way_classes, CALIBRATION_N_EPISODES, seed, edges, native)
    baseline_correct = [int(np.argmin(e["geo_scores"])) == e["true_idx"] for e in episodes]
    acc_baseline = sum(baseline_correct) / len(baseline_correct)

    sweep = []
    for lam in LAMBDA_GRID:
        correct = [mv.fused_argmin(native, e["geo_scores"], e["m_scores"], w_m, lam) == e["true_idx"]
                   for e in episodes]
        acc = sum(correct) / len(correct)
        sweep.append({"lam": lam, "acc": acc, "delta_vs_baseline": acc - acc_baseline})
        print(f"    lambda={lam:5.2f}  acc={100*acc:5.1f}%  delta={100*(acc-acc_baseline):+.1f}pp")

    passing = [row for row in sweep if row["delta_vs_baseline"] >= -SANITY_MARGIN]
    if passing:
        best = max(passing, key=lambda r: (r["acc"], -r["lam"]))
        sanity_pass = True
    else:
        best = max(sweep, key=lambda r: r["acc"])
        sanity_pass = False
    print(f"\n  BACKGROUND-SANITY ({label}): baseline={100*acc_baseline:.1f}%  "
          f"best_lambda={best['lam']}  best_acc={100*best['acc']:.1f}%  "
          f"delta={100*best['delta_vs_baseline']:+.1f}pp  bound=-{100*SANITY_MARGIN:.0f}pp  "
          f"-> {'PASS' if sanity_pass else 'HARD STOP'}")
    return {"label": label, "n_way": len(way_classes), "n_episodes": len(episodes), "w_m": w_m,
            "acc_baseline": acc_baseline, "sweep": sweep, "frozen_lambda": best["lam"],
            "frozen_lambda_acc": best["acc"], "sanity_pass": bool(sanity_pass),
            "elapsed": time.time() - t0}


def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (background-sanity STOP + lambda sweep, FROZEN "
          f"w_m from --stage spread)\n{SEP}")
    t0 = time.time()
    edges = _frozen_edges()
    spread = _require_spread()
    background, _ = _load_split()
    native = srs.Substrate()._inner

    cal20 = _calibrate_one_way(background, spread["20way"]["way_classes"], spread["20way"]["w_m"],
                                edges, "20-way", run47.RNG_SEED + 210, native)
    cal20_clean = _calibrate_one_way(background, spread["20way_clean"]["way_classes"],
                                      spread["20way_clean"]["w_m"], edges, "20-way-clean",
                                      run47.RNG_SEED + 211, native)

    out = {"cal20": cal20, "cal20_clean": cal20_clean}
    _save_json(out, _ckpt("calibrate.json"))
    print(f"\n  saved -> {_ckpt('calibrate.json')}")
    md5_after = run47._md5(STROKE_SHAPES_SEED)
    us = _require_unit_sanity()
    print(f"  seeds/stroke_shapes.json md5 AFTER calibrate: {md5_after}  "
          f"UNCHANGED={md5_after == us['stroke_shapes_md5_before']}")
    if md5_after != us["stroke_shapes_md5_before"]:
        raise SystemExit("HARD STOP: seed write detected during --stage calibrate.")
    print(f"  donkey=0: {'PASS' if run47._donkey0() else 'FAIL'}")
    print(f"  [calibrate wall time: {time.time()-t0:.1f}s]")
    return 0


def _require_calibrate() -> dict:
    path = _ckpt("calibrate.json")
    if not os.path.exists(path):
        raise SystemExit("WALL: run --stage calibrate first.")
    return _load_json(path)


# ============================================================================================= #
#  GATE B -- the real held-out-WRITER eval, TWO ARMS, McNemar-paired.
# ============================================================================================= #
def _gate_b_report(episodes: list, way_classes: list, w_m: float, lam: float, native) -> dict:
    n = len(episodes)
    n_way = len(way_classes)
    pred_i, pred_ii, correct_i, correct_ii = [], [], [], []
    for e in episodes:
        pi = int(np.argmin(e["geo_scores"]))
        pii = mv.fused_argmin(native, e["geo_scores"], e["m_scores"], w_m, lam)
        pred_i.append(pi)
        pred_ii.append(pii)
        correct_i.append(pi == e["true_idx"])
        correct_ii.append(pii == e["true_idx"])
    acc_i = sum(correct_i) / n
    acc_ii = sum(correct_ii) / n
    ci_i = run47.wilson_ci(sum(correct_i), n)
    ci_ii = run47.wilson_ci(sum(correct_ii), n)
    mc = run47._mcnemar(correct_i, correct_ii)

    n_engaged = sum(1 for a, b in zip(pred_i, pred_ii) if a != b)
    n_fixed = sum(1 for e, a, b in zip(episodes, correct_i, correct_ii) if (not a) and b)
    n_broken = sum(1 for e, a, b in zip(episodes, correct_i, correct_ii) if a and (not b))

    def sym(way_idx: int) -> str:
        return pw.DIGILETS_SYMBOLS[way_classes[way_idx]]

    confusion_i, confusion_ii = Counter(), Counter()
    homo_err_i = homo_err_ii = 0
    for e, pi, pii in zip(episodes, pred_i, pred_ii):
        t = e["true_idx"]
        if pi != t:
            confusion_i[(sym(t), sym(pi))] += 1
            if run48._is_homoglyph_pair(sym(t), sym(pi)):
                homo_err_i += 1
        if pii != t:
            confusion_ii[(sym(t), sym(pii))] += 1
            if run48._is_homoglyph_pair(sym(t), sym(pii)):
                homo_err_ii += 1
    n_err_i, n_err_ii = n - sum(correct_i), n - sum(correct_ii)

    m_vals = np.asarray([m for e in episodes for m in e["m_scores"]], dtype=float)

    return dict(n=n, n_way=n_way, w_m=w_m, lam=lam,
                acc_continuous_only=acc_i, ci_continuous_only=list(ci_i),
                acc_motor_fused=acc_ii, ci_motor_fused=list(ci_ii),
                mcnemar_fused_vs_continuous=mc,
                stop_fused_harms=bool(mc["broken"] >= mc["fixed"]),
                n_engaged=n_engaged, engagement_frac=n_engaged / n,
                n_fixed=n_fixed, n_broken=n_broken,
                acc_excl_homoglyph_i=(sum(correct_i) + homo_err_i) / n,
                acc_excl_homoglyph_ii=(sum(correct_ii) + homo_err_ii) / n,
                n_homoglyph_errors_i=homo_err_i, n_homoglyph_errors_ii=homo_err_ii,
                n_errors_i=n_err_i, n_errors_ii=n_err_ii,
                top_confusions_i=[{"true": a, "pred": b, "count": c}
                                   for (a, b), c in confusion_i.most_common(8)],
                top_confusions_ii=[{"true": a, "pred": b, "count": c}
                                    for (a, b), c in confusion_ii.most_common(8)],
                m_score_mean=float(m_vals.mean()) if m_vals.size else None,
                m_score_std=float(m_vals.std()) if m_vals.size else None)


def _print_gate_b_report(rep: dict, label: str) -> None:
    print(f"\n  {label}: n={rep['n']}  N-way={rep['n_way']}  w_m={rep['w_m']:.5f}  "
          f"lambda={rep['lam']}")
    print(f"  (i)  CONTINUOUS-ONLY: acc={100*rep['acc_continuous_only']:.1f}%  "
          f"CI=[{100*rep['ci_continuous_only'][0]:.1f},{100*rep['ci_continuous_only'][1]:.1f}]")
    print(f"  (ii) MOTOR-FUSED:     acc={100*rep['acc_motor_fused']:.1f}%  "
          f"CI=[{100*rep['ci_motor_fused'][0]:.1f},{100*rep['ci_motor_fused'][1]:.1f}]")
    mc = rep["mcnemar_fused_vs_continuous"]
    print(f"  McNemar (ii) vs (i): fixed={mc['fixed']}  broken={mc['broken']}  p={mc['p']:.4g}  "
          f"STOP(fused harms)={rep['stop_fused_harms']}")
    print(f"  ENGAGEMENT: the fused verdict picked a DIFFERENT candidate than continuous-only "
          f"in {rep['n_engaged']}/{rep['n']} episodes ({100*rep['engagement_frac']:.1f}%) -- "
          f"of those, {rep['n_fixed']} FIXED (wrong->right), {rep['n_broken']} BROKEN "
          f"(right->wrong).")
    print(f"  m-score distribution (all candidates, all episodes): mean={rep['m_score_mean']:.4f} "
          f"std={rep['m_score_std']:.4f}")
    print(f"  homoglyph accounting: (i) raw={100*rep['acc_continuous_only']:.1f}% "
          f"excl={100*rep['acc_excl_homoglyph_i']:.1f}% ({rep['n_homoglyph_errors_i']}/"
          f"{rep['n_errors_i']} errors homoglyph)  "
          f"(ii) raw={100*rep['acc_motor_fused']:.1f}% excl={100*rep['acc_excl_homoglyph_ii']:.1f}% "
          f"({rep['n_homoglyph_errors_ii']}/{rep['n_errors_ii']} errors homoglyph)")
    print(f"  top confusions (i):  {rep['top_confusions_i'][:6]}")
    print(f"  top confusions (ii): {rep['top_confusions_ii'][:6]}")


def _run_gate_b(label: str, way_classes: list, cal: dict, seed: int) -> int:
    print(f"\n{SEP}\n  STAGE: gate_b_{label} (one-shot {len(way_classes)}-way, cross-WRITER, "
          f"held-out only)\n{SEP}")
    t0 = time.time()
    if not cal["sanity_pass"]:
        print(f"  BACKGROUND-SANITY STOP fired for {label} at --stage calibrate "
              f"(lambda={cal['frozen_lambda']} scored {100*cal['frozen_lambda_acc']:.1f}% vs "
              f"baseline {100*cal['acc_baseline']:.1f}%, outside the -{100*SANITY_MARGIN:.0f}pp "
              f"bound). STOPPING -- not spending held-out eval budget on a failed calibration.")
        out = {"skipped": True, "reason": "background_sanity_stop", "calibration": cal}
        _save_json(out, _ckpt(f"gate_b_{label}.json"))
        return 0

    edges = _frozen_edges()
    _, heldout = _load_split()
    native = srs.Substrate()._inner
    lam = cal["frozen_lambda"]
    w_m = cal["w_m"]
    print(f"  n_way={len(way_classes)}  frozen_w_m={w_m:.5f}  frozen_lambda={lam}  "
          f"n_heldout_instances={len(heldout)}")

    episodes = _score_episodes(heldout, way_classes, GATE_B_N_EPISODES, seed, edges, native)
    print(f"  n_episodes_scored={len(episodes)} (target {GATE_B_N_EPISODES})  "
          f"[{time.time()-t0:.1f}s]")
    rep = _gate_b_report(episodes, way_classes, w_m, lam, native)
    _print_gate_b_report(rep, f"GATE B {label.upper()}")

    out = {"skipped": False, "report": rep,
           "calibration_used": {"frozen_lambda": lam, "w_m": w_m,
                                 "cal_sanity_pass": cal["sanity_pass"]}}
    _save_json(out, _ckpt(f"gate_b_{label}.json"))
    print(f"\n  saved -> {_ckpt(f'gate_b_{label}.json')}")
    md5_after = run47._md5(STROKE_SHAPES_SEED)
    us = _require_unit_sanity()
    print(f"  seeds/stroke_shapes.json md5 AFTER gate_b_{label}: {md5_after}  "
          f"UNCHANGED={md5_after == us['stroke_shapes_md5_before']}")
    if md5_after != us["stroke_shapes_md5_before"]:
        raise SystemExit(f"HARD STOP: seed write detected during --stage gate_b_{label}.")
    print(f"  donkey=0: {'PASS' if run47._donkey0() else 'FAIL'}")
    print(f"  [gate_b_{label} wall time: {time.time()-t0:.1f}s]")
    return 0


def stage_gate_b_20way():
    cal = _require_calibrate()
    spread = _require_spread()
    return _run_gate_b("20way", spread["20way"]["way_classes"], cal["cal20"], run47.RNG_SEED + 220)


def stage_gate_b_20way_clean():
    cal = _require_calibrate()
    spread = _require_spread()
    return _run_gate_b("20way_clean", spread["20way_clean"]["way_classes"], cal["cal20_clean"],
                        run47.RNG_SEED + 221)


# ============================================================================================= #
#  STAGE: summary
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 49 SCOREBOARD (THE MOTOR-PROGRAM VERDICT)\n{SEP}")
    needed = ["unit_sanity.json", "spread.json", "calibrate.json",
              "gate_b_20way.json", "gate_b_20way_clean.json"]
    missing = [n for n in needed if not os.path.exists(_ckpt(n))]
    if missing:
        print(f"  INCOMPLETE -- missing checkpoints: {missing}")
        return 1
    data = {n: _load_json(_ckpt(n)) for n in needed}

    md5_before = data["unit_sanity.json"]["stroke_shapes_md5_before"]
    md5_after = run47._md5(STROKE_SHAPES_SEED)
    print(f"\n  SEED-GUARD (belt-and-suspenders, this run's own launch brief): "
          f"seeds/stroke_shapes.json md5 before={md5_before}  after={md5_after}  "
          f"UNCHANGED={md5_before == md5_after}")

    print(f"\n  BACKGROUND-SANITY (reported FIRST, per this run's own launch brief):")
    for key, cal in (("20-way", data["calibrate.json"]["cal20"]),
                      ("20-way-clean", data["calibrate.json"]["cal20_clean"])):
        print(f"    {key}: w_m={cal['w_m']:.5f}  frozen_lambda={cal['frozen_lambda']}  "
              f"baseline={100*cal['acc_baseline']:.1f}%  armed={100*cal['frozen_lambda_acc']:.1f}%  "
              f"sanity_pass={cal['sanity_pass']}")

    print(f"\n  RUN-48 CITED CONTINUOUS-ONLY BASELINE (DigiLeTs, NOT re-derived):")
    for key in ("gate_b_20way.json", "gate_b_20way_clean.json"):
        p = _run48_ckpt(key)
        if os.path.exists(p):
            d = _load_json(p)
            if not d.get("skipped"):
                r = d["report"]
                print(f"    run48 {key}: acc_continuous_only={100*r['acc_continuous_only']:.1f}% "
                      f"CI=[{100*r['ci_continuous_only'][0]:.1f},{100*r['ci_continuous_only'][1]:.1f}]")

    for key in ("gate_b_20way.json", "gate_b_20way_clean.json"):
        gb = data[key]
        label = key.replace("gate_b_", "").replace(".json", "").upper()
        print(f"\n  GATE B {label}:")
        if gb.get("skipped"):
            print(f"    SKIPPED -- {gb.get('reason')}")
            continue
        rep = gb["report"]
        print(f"    n={rep['n']}  (i) continuous={100*rep['acc_continuous_only']:.1f}%  "
              f"(ii) motor-fused={100*rep['acc_motor_fused']:.1f}%")
        print(f"    McNemar(ii vs i): fixed={rep['mcnemar_fused_vs_continuous']['fixed']} "
              f"broken={rep['mcnemar_fused_vs_continuous']['broken']} "
              f"p={rep['mcnemar_fused_vs_continuous']['p']:.4g}  "
              f"STOP(fused harms)={rep['stop_fused_harms']}")
        print(f"    engagement={100*rep['engagement_frac']:.1f}%  fixed={rep['n_fixed']}  "
              f"broken={rep['n_broken']}")

    print(f"\n  HONESTY NOTE: DigiLeTs is 62-class cross-writer, harder than Omniglot's "
          f"within-alphabet 20-way. The continuous-only baseline (this run's own arm (i), "
          f"reproduced fresh on THIS run's own episode draws) is the comparison, not Omniglot's "
          f"80.5%.")

    print(f"\n{SEP}\n  RUN 49 COMPLETE -- see final agent report for full narrative.\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                   choices=["unit_sanity", "spread", "calibrate",
                            "gate_b_20way", "gate_b_20way_clean", "summary"])
    args = p.parse_args()
    fn = {"unit_sanity": stage_unit_sanity, "spread": stage_spread, "calibrate": stage_calibrate,
          "gate_b_20way": stage_gate_b_20way, "gate_b_20way_clean": stage_gate_b_20way_clean,
          "summary": stage_summary}[args.stage]
    return fn()


if __name__ == "__main__":
    sys.exit(main())
