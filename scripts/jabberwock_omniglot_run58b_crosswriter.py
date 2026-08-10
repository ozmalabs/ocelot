"""OMNIGLOT RUN 58b -- CROSS-WRITER-ROBUST DISCRIMINABILITY (the principled fix to run 58).

RUN 58 (aa95ed97) applied the run-57 discrimination faculty to pen data (DigiLeTs multi-stroke).
STAGE 1 LICENSED for the first time ever: junction `frac_none` (do two strokes touch?) separated
classes with Fisher 1.328 (8x mouse's arrangement max), orthogonal to geometry. But the held-out
CROSS-WRITER eval HARMED -8.2pp (GUARD 57.7% -> ARM DP 49.5%, McNemar 13/31 p=0.0096). THE
DIAGNOSIS: run 58's Fisher measured within-class variance over a POOLED background population, so it
captured WRITER-CORRELATED-with-class structure (junction/touch choices are STYLE) that COLLAPSES on
a held-out writer. The in-distribution background-sanity gate PASSED (+0.5pp) while eval harmed
-8.2pp -- the faculty over-trusted a non-transferable signal and the sanity gate did not catch it.

THE FIX (34a->34b precedent; = BPL learning class-defining-vs-stylistic FROM MANY WRITERS), in
`domains/crosswriter_discrimination.py`:
  1. CROSS-WRITER FISHER -- a WRITER-BLOCKED variance decomposition: within-class variance = the
     BETWEEN-WRITER scatter of per-writer class means (each writer weighted equally). A feature that
     VARIES by writer for the same class gets high within-class var -> LOW Fisher -> distrusted.
  2. CROSS-WRITER-HELD-OUT SANITY -- calibrate discriminability on background writers A, sanity-check
     accuracy on DIFFERENT background writers B. A non-transferable signal now FAILS sanity BEFORE
     the held-out eval, closing the run-58 hole.

STAGES (ops law -- each <=540s FOREGROUND, stdbuf -oL | tee, per-class checkpoints):
  unit_sanity : run58b + run58 + run57 + unified_verdict + relational_variation suites; seed guard.
  falsifier   : STAGE 1 -- cross-writer Fisher of relations vs run-58 POOLED Fisher, side by side.
                Did the writer-idiosyncratic junction relations DROP? Which, if any, RETAIN
                cross-writer separation (transferable)? Orthogonality to geometry as run 58.
  calibrate   : STAGE 2 -- split background writers A/B; cross-writer slot weights + part precisions
                on A; GUARD (geometry-only) vs ARM X (cross-writer discriminability precision) on B.
                CROSS-WRITER-HELD-OUT SANITY STOP before eval.
  eval        : STAGE 2 -- the SAME held-out cross-writer episodes as run 58 (comparable). McNemar.
  report      : STAGE-1 drop table, sanity result, STAGE-2 McNemar, the outcome (i clean-null /
                ii converts), faculty-correctness assessment.

PRE-REGISTERED (before any real-data number):
  BAR A (survives cross-writer): arrangement cross-writer max Fisher > 1.5 x mouse (0.167) = 0.2505.
  BAR B (above geometry-redundant baseline): arrangement cross-writer max > cpose cross-writer max
        (the whole-char geometry-redundant slots) -- transferable arrangement must beat the
        geometry-redundant relations.
  BAR C (orthogonal to geometry): |Pearson corr(whole, rel)| < 0.5 on background cross-writer episodes.
  The GATE decision to spend eval is the CROSS-WRITER-HELD-OUT SANITY (calibrate on A, sanity on B):
  proceed iff ARM X >= GUARD - 3pp on the SANITY writers.

OUTCOMES (pre-registered):
  (i)  cross-writer Fisher zeroes the writer-idiosyncratic relations -> ARM X's rel precision ~0 ->
       ARM reduces to geometry -> sanity passes, eval ~= GUARD, ZERO harm (unlike run 58's -8.2pp).
       CONFIRMS the fix: the faculty now distrusts non-transferable signal; geometry is the only
       transferable fine-separator; concept-participation reaches a CLEAN TERMINUS.
  (ii) SOME relation RETAINS cross-writer Fisher AND converts (McNemar fixed>broken at eval) ->
       genuinely class-defining arrangement structure = entry-38 CONSTRUCTIVE confirmation.
  STOP: cross-writer-sanity fail (the gate now catches what run 58 missed); broken>=fixed at eval.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run58b_crosswriter.py --stage <STAGE>
Stages: unit_sanity -> falsifier -> calibrate -> eval -> report
"""
from __future__ import annotations

import argparse
import os
import sys
import time

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import subprocess

import numpy as np

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run47_pendata as run47
import scripts.jabberwock_omniglot_run58_pendiscrim as r58     # READ-ONLY reuse of run-58 helpers.
from domains import pen_world as pw
from domains import discrimination as disc
from domains import crosswriter_discrimination as cwd
from domains import relational_variation as rv
from domains import unified_verdict as uv

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run58b_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
RUN58_FALSIFIER = os.path.join(ROOT, "results", "run58_checkpoints", "falsifier.json")   # READ-ONLY.
RUN58_EVAL = os.path.join(ROOT, "results", "run58_checkpoints", "eval.json")              # READ-ONLY.

TB = gate.DK["turn_bins"]

# ---- reuse run 58's PRE-REGISTERED constants verbatim (comparable protocol) ---- #
N_BACKGROUND_WRITERS = r58.N_BACKGROUND_WRITERS
WRITER_SPLIT_SEED = r58.WRITER_SPLIT_SEED
MS_CLASS_FRAC = r58.MS_CLASS_FRAC
N_WAY_TARGET = r58.N_WAY_TARGET
N_BACKGROUND_EPISODES = r58.N_BACKGROUND_EPISODES
N_EVAL_EPISODES = r58.N_EVAL_EPISODES
BG_EPISODE_SEED = r58.BG_EPISODE_SEED
EVAL_EPISODE_SEED = r58.EVAL_EPISODE_SEED
SANITY_MARGIN = r58.SANITY_MARGIN
PER_CALL_BUDGET_SECONDS = 480

ARRANGEMENT_SLOTS = r58.ARRANGEMENT_SLOTS       # rel_* + junction (excludes whole-char cpose_*).
CPOSE_SLOTS = r58.CPOSE_SLOTS
MOUSE_ARRANGEMENT_MAX = 0.167
BAR_A_FACTOR = 1.5                              # survives cross-writer: > 1.5x mouse.

# ---- cross-writer-held-out split of the BACKGROUND writers (calibrate A, sanity B) ---- #
CW_SPLIT_SEED = 20260706                        # deterministic A/B split of background writers.
CALIB_EPISODE_SEED = 20260901
SANITY_EPISODE_SEED = 20260902

FALSIFIER_STATE = os.path.join(CKPT_DIR, "falsifier_state.json")
FALSIFIER_PATH = os.path.join(CKPT_DIR, "falsifier.json")
CALIB_PATH = os.path.join(CKPT_DIR, "calibrate.json")
EVAL_PATH = os.path.join(CKPT_DIR, "eval.json")

# reuse run 58's mechanical I/O helpers (identical implementations -- import, don't copy).
_save_json = r58._save_json
_load_json = r58._load_json
_md5 = r58._md5
_donkey0 = r58._donkey0
_mcnemar = r58._mcnemar
_valid_strokes = r58._valid_strokes
_is_multistroke = r58._is_multistroke
qualifying_classes = r58.qualifying_classes
_index_by_writer_class = r58._index_by_writer_class
_draw_episodes = r58._draw_episodes
_compose = r58._compose
_geo_ps = r58._geo_ps
_class_slot_means = r58._class_slot_means


def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _seed_guard(stage, md5_before):
    md5_after = _md5(STROKE_SHAPES_SEED)
    ok = md5_after == md5_before
    print(f"\n  seeds/stroke_shapes.json md5 AFTER {stage}: {md5_after}  UNCHANGED={ok}")
    if not ok:
        raise SystemExit(f"HARD STOP: seed write detected during --stage {stage}.")


# ============================================================================================= #
#  PER-CANDIDATE RESIDUAL RECORDS carrying the QUERY WRITER (for writer-blocked part precision).
# ============================================================================================= #
def _records(native, episodes, weights, cache, geo_cache, timing=None):
    """Per episode: for each candidate the (whole, rel) residual pair, PLUS the query writer id and
    the true index. whole = per-stroke SC+TPS geometry (the GUARD); rel = arrangement residual under
    `weights`. Mirrors r58._episode_records but retains q_writer + the ortho pairs. Mechanical."""
    out = []
    for e in episodes:
        q = e["query"]
        q_ps = _geo_ps(q, geo_cache)
        q_sp, q_sig = _compose(native, q, cache)
        if not q_ps or not q_sp:
            continue
        per, ortho, ok = [], [], True
        t0 = time.time()
        for c in e["classes"]:
            cand = e["ex_sample"][c]
            c_ps = _geo_ps(cand, geo_cache)
            c_sp, c_sig = _compose(native, cand, cache)
            if not c_ps or not c_sp:
                ok = False
                break
            whole = float(run47.ps.program_score(q_ps, c_ps))
            rel = float(rv.relational_distance(native, q_sp, q_sig, c_sp, c_sig, weights)["r"])
            per.append(dict(whole=whole, stroke=0.0, rel=rel))
            ortho.append((whole, rel))
        if not ok or not per:
            continue
        if timing is not None:
            timing["n_derivations"] += len(per)
            timing["rel_seconds"] += time.time() - t0
        out.append(dict(true_idx=int(e["true_idx"]), per=per, ortho=ortho,
                        q_writer=e["q_writer"]))
    return out


def _residual_split_by_writer(records, parts=("whole", "rel")):
    """{part: {"true": {writer: [res]}, "false": {writer: [res]}}} -- residuals grouped by the QUERY
    writer, for the cross-writer (writer-blocked) part discriminability."""
    res = {p: {"true": {}, "false": {}} for p in parts}
    for r in records:
        w, ti = r["q_writer"], r["true_idx"]
        for ci, c in enumerate(r["per"]):
            side = "true" if ci == ti else "false"
            for p in parts:
                res[p][side].setdefault(w, []).append(c[p])
    return res


def _crosswriter_part_precisions(records, parts=("whole", "rel")):
    """Cross-writer discriminability precision per part, stored as graph log_weight EDGES (run 57's
    install/read path, UNCHANGED) so the verdict reads GRAPH DATA."""
    res = _residual_split_by_writer(records, parts)
    prec = {p: cwd.crosswriter_part_discriminability(res[p]["true"], res[p]["false"]) for p in parts}
    prec.setdefault("stroke", 0.0)
    sub = srs.Substrate()
    frame = disc.install_part_precisions(sub, {k: prec[k] for k in ("whole", "stroke", "rel")})
    return disc.read_part_precisions(sub, frame, parts=("whole", "stroke", "rel"))


def _preds(native, records, prec):
    guard, arm = [], []
    pw_, pr = prec["whole"], prec["rel"]
    for r in records:
        guard.append(uv.unified_verdict_pred(native, r["per"], prec_whole=pw_, prec_stroke=0.0,
                                             prec_rel=0.0))
        arm.append(uv.unified_verdict_pred(native, r["per"], prec_whole=pw_, prec_stroke=0.0,
                                           prec_rel=pr))
    return guard, arm


# ============================================================================================= #
#  STAGE: unit_sanity
# ============================================================================================= #
def stage_unit_sanity():
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    md5_before = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5 (BEFORE): {md5_before}")
    ok_all = True
    for test_file in ("tests/test_crosswriter_migrated.py",
                      "tests/test_pendiscrim_migrated.py",
                      "tests/test_discrimination_migrated.py",
                      "tests/test_unified_verdict_migrated.py",
                      "tests/test_relational_variation_migrated.py"):
        print(f"\n  running {test_file} ...")
        proc = subprocess.run([sys.executable, "-m", "pytest", test_file, "-q"],
                              cwd=ROOT, env={**os.environ}, capture_output=True, text=True,
                              timeout=400)
        print(proc.stdout[-1500:])
        if proc.returncode != 0:
            print(proc.stderr[-2000:])
        ok = proc.returncode == 0
        print(f"      -> {'PASS' if ok else 'FAIL'}")
        ok_all &= ok
    _seed_guard("unit_sanity", md5_before)
    print(f"\n{SEP}\n  UNIT SANITY: {'ALL PASS' if ok_all else 'SOME FAILED -- DO NOT PROCEED'}\n{SEP}")
    _save_json({"ok_all": bool(ok_all), "stroke_shapes_md5_before": md5_before}, _ckpt("unit_sanity.json"))
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    if not ok_all:
        raise SystemExit(1)
    return 0


def _require_unit_sanity():
    p = _ckpt("unit_sanity.json")
    if not os.path.exists(p) or not _load_json(p).get("ok_all"):
        raise SystemExit("WALL: run --stage unit_sanity (to PASS) first.")


# ============================================================================================= #
#  WRITER-AWARE per-(class,writer) accumulation -- pose slots (aligned) + junction (histogram).
# ============================================================================================= #
def _accumulate_writer_cells(native, cls_samples, pose, junction, per_class_var, cache):
    """Fold ONE class's instances into per-(class,writer) accumulators:
        pose[slot][cls][writer]     = [one aligned per-writer mean]     (needs rv alignment)
        junction[slot][cls][writer] = [per-instance junction fracs]     (alignment-free histogram)
    plus the class's pooled pose variance (for a fallback weight). By WRITER so `crosswriter_fisher`
    can measure BETWEEN-writer scatter within the class."""
    cls_key = str(cls_samples[0]["class"])
    by_writer = {}
    for s in cls_samples:
        by_writer.setdefault(s["writer_id"], []).append(s)
    # --- junction: per instance, per writer (cheap) ---
    for w, insts in by_writer.items():
        for s in insts:
            sp, _sig = _compose(native, s, cache)
            if not sp:
                continue
            prof = disc.junction_profile(rv.stroke_points_only(sp))
            for slot in disc.JUNCTION_SLOTS:
                junction[slot].setdefault(cls_key, {}).setdefault(str(w), []).append(prof[slot])
    # --- pose: one aligned mean-vector per (class, writer) ---
    pooled_for_var = []
    for w, insts in by_writer.items():
        decoded = [_compose(native, s, cache) for s in insts]
        decoded = [(sp, sig) for (sp, sig) in decoded if sp]
        if not decoded:
            continue
        ref_sp, ref_sig = decoded[0]
        others = decoded[1:]
        means = _class_slot_means(native, ref_sp, ref_sig, others)
        if means is None:
            continue
        for slot in rv.ALL_SLOTS:
            pose[slot].setdefault(cls_key, {}).setdefault(str(w), []).append(float(means[slot]))
        if len(decoded) >= 2:
            var = rv.class_slot_variances(native, ref_sp, ref_sig, others, turn_bins=TB)
            if var is not None:
                pooled_for_var.append({s: var.get(s, 0.0) for s in rv.ALL_SLOTS})
    if pooled_for_var:
        per_class_var.append({s: float(np.mean([d[s] for d in pooled_for_var]))
                              for s in rv.ALL_SLOTS})


# ============================================================================================= #
#  STAGE: falsifier -- STAGE 1: cross-writer Fisher vs run-58 pooled Fisher, side by side.
# ============================================================================================= #
def stage_falsifier():
    print(f"\n{SEP}\n  STAGE: falsifier (STAGE 1 -- CROSS-WRITER Fisher vs run-58 POOLED Fisher)\n{SEP}")
    _require_unit_sanity()
    md5_before = _md5(STROKE_SHAPES_SEED)

    samples = pw.load_digilets_samples()
    background, heldout = pw.digilets_writer_split(samples, n_background=N_BACKGROUND_WRITERS,
                                                   seed=WRITER_SPLIT_SEED)
    classes = qualifying_classes(samples, frac=MS_CLASS_FRAC)
    bg_ms = [s for s in background if _is_multistroke(s) and s["class"] in set(classes)]
    print(f"  qualifying multi-stroke classes={len(classes)}  background writers="
          f"{len({s['writer_id'] for s in background})}  bg multi-stroke instances={len(bg_ms)}")

    by_cls = {}
    for s in bg_ms:
        by_cls.setdefault(s["class"], []).append(s)
    ordered_classes = [c for c in classes if c in by_cls]

    # ---- checkpointed per-class accumulation ----
    state = (_load_json(FALSIFIER_STATE) if os.path.exists(FALSIFIER_STATE)
             else dict(cls_idx=0, pose={}, junction={}, per_class_var=[]))
    pose = {slot: {} for slot in rv.ALL_SLOTS}
    for slot, d in state["pose"].items():
        pose[slot] = {c: {w: list(v) for w, v in byw.items()} for c, byw in d.items()}
    junction = {slot: {} for slot in disc.JUNCTION_SLOTS}
    for slot, d in state["junction"].items():
        junction[slot] = {c: {w: list(v) for w, v in byw.items()} for c, byw in d.items()}
    per_class_var = [dict(x) for x in state["per_class_var"]]

    native = srs.Substrate()._inner
    cache = {}
    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    while state["cls_idx"] < len(ordered_classes) and time.time() < hard_deadline:
        c = ordered_classes[state["cls_idx"]]
        _accumulate_writer_cells(native, by_cls[c], pose, junction, per_class_var, cache)
        state["cls_idx"] += 1
        state["pose"] = pose
        state["junction"] = junction
        state["per_class_var"] = per_class_var
        _save_json(state, FALSIFIER_STATE)
        print(f"    [falsifier] class {state['cls_idx']}/{len(ordered_classes)} "
              f"({pw.DIGILETS_SYMBOLS[c]!r}) folded", flush=True)
    if state["cls_idx"] < len(ordered_classes):
        print(f"\n  PARTIAL [falsifier]: {state['cls_idx']}/{len(ordered_classes)} -- re-invoke.")
        return 0

    # ---- cross-writer vs pooled Fisher, per slot ----
    all_cw = {**cwd.crosswriter_slot_fisher(pose), **cwd.crosswriter_slot_fisher(junction)}
    all_pool = {**cwd.pooled_slot_fisher(pose), **cwd.pooled_slot_fisher(junction)}
    arr_slots = [s for s in ARRANGEMENT_SLOTS if s in all_cw]
    cw_arr = {s: all_cw[s] for s in arr_slots}
    pool_arr = {s: all_pool[s] for s in arr_slots}
    cw_cpose = {s: all_cw[s] for s in CPOSE_SLOTS if s in all_cw}
    cw_arr_max = max(cw_arr.values()) if cw_arr else 0.0
    top_cw_slot = max(cw_arr, key=cw_arr.get) if cw_arr else None
    cpose_cw_max = max(cw_cpose.values()) if cw_cpose else 0.0

    print(f"\n  ---- CROSS-WRITER vs POOLED (run-58) Fisher, DigiLeTs multi-stroke background ----")
    print(f"    {'slot':<10} {'pooled(run58)':>14} {'cross-writer':>14} {'drop':>8}")
    for s in arr_slots:
        drop = pool_arr[s] - cw_arr[s]
        print(f"    {s:<10} {pool_arr[s]:>14.4f} {cw_arr[s]:>14.4f} {drop:>8.4f}")
    print(f"    -- geometry-redundant cpose_* (cross-writer): "
          f"{{{', '.join(f'{k}={cw_cpose.get(k,0):.4f}' for k in CPOSE_SLOTS)}}}")
    print(f"    ARRANGEMENT cross-writer max (rel_*+junction, excl cpose)={cw_arr_max:.4f} "
          f"@ {top_cw_slot!r}  (pooled frac_none was {pool_arr.get('frac_none',0):.4f})")

    # ---- pre-registered bars ----
    bar_a = cw_arr_max > BAR_A_FACTOR * MOUSE_ARRANGEMENT_MAX
    bar_b = cw_arr_max > cpose_cw_max

    # ---- orthogonality (cross-writer background episodes, corr(whole, rel)) ----
    weights = cwd.normalize_weights(all_cw, rv.ALL_SLOTS)
    n_way = min(N_WAY_TARGET, len(ordered_classes))
    way_classes = ordered_classes[:n_way]
    idx_way = _index_by_writer_class(bg_ms, way_classes)
    eps = _draw_episodes(idx_way, way_classes, N_BACKGROUND_EPISODES, BG_EPISODE_SEED)
    geo_cache = {}
    recs = _records(native, eps, weights, cache, geo_cache)
    wr = np.array([w for r in recs for (w, _r) in r["ortho"]], dtype=float)
    rl = np.array([rv_ for r in recs for (_w, rv_) in r["ortho"]], dtype=float)
    corr = float(np.corrcoef(wr, rl)[0, 1]) if wr.size >= 3 and np.std(wr) > 0 and np.std(rl) > 0 else 0.0
    bar_c = abs(corr) < 0.5

    licensed = bool(bar_a and bar_b and bar_c)
    out = dict(n_qualifying_classes=len(ordered_classes), n_way=n_way, way_classes=way_classes,
               way_symbols=[pw.DIGILETS_SYMBOLS[c] for c in way_classes],
               crosswriter_fisher=cw_arr, pooled_fisher=pool_arr, cpose_crosswriter=cw_cpose,
               crosswriter_arrangement_max=cw_arr_max, top_crosswriter_slot=top_cw_slot,
               cpose_crosswriter_max=cpose_cw_max, mouse_arrangement_max=MOUSE_ARRANGEMENT_MAX,
               bar_a_survives=bool(bar_a), bar_b_above_cpose=bool(bar_b),
               orthogonality_corr=corr, bar_c_orthogonal=bool(bar_c), licensed=licensed,
               rel_weights=weights, n_bg_episodes=len(recs))
    _save_json(out, FALSIFIER_PATH)
    _seed_guard("falsifier", md5_before)

    print(f"\n  {'='*28}  STAGE-1 CROSS-WRITER FALSIFIER  {'='*28}")
    print(f"    BAR A survives cross-writer (> {BAR_A_FACTOR}x mouse = "
          f"{BAR_A_FACTOR*MOUSE_ARRANGEMENT_MAX:.4f}): {bar_a}  (cw max {cw_arr_max:.4f})")
    print(f"    BAR B above geometry-redundant cpose ({cpose_cw_max:.4f}): {bar_b}")
    print(f"    BAR C orthogonal-to-geometry (|corr| {abs(corr):.4f} < 0.5): {bar_c}")
    if licensed:
        print(f"    => cross-writer arrangement RETAINS transferable separation @ {top_cw_slot!r} "
              f"-- STAGE 2 tests whether it CONVERTS (outcome ii candidate).")
    else:
        print(f"    => the writer-idiosyncratic arrangement relations DROPPED under cross-writer "
              f"variance (they were STYLE). Predicts outcome (i): ARM X reduces to geometry, eval "
              f"~= GUARD, ZERO harm. STAGE 2 MEASURES this (the sanity gate now holds out writers).")
    print(f"    donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _require_falsifier():
    if not os.path.exists(FALSIFIER_PATH):
        raise SystemExit("WALL: run --stage falsifier first.")
    return _load_json(FALSIFIER_PATH)


# ============================================================================================= #
#  STAGE: calibrate -- STAGE 2: cross-writer-held-out sanity (calibrate A, sanity B).
# ============================================================================================= #
def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (STAGE 2 -- cross-writer slot weights + part precisions on "
          f"writers A; CROSS-WRITER-HELD-OUT SANITY on writers B)\n{SEP}")
    _require_unit_sanity()
    fals = _require_falsifier()
    md5_before = _md5(STROKE_SHAPES_SEED)

    samples = pw.load_digilets_samples()
    background, _ = pw.digilets_writer_split(samples, n_background=N_BACKGROUND_WRITERS,
                                             seed=WRITER_SPLIT_SEED)
    way_classes = fals["way_classes"]
    weights = {k: float(v) for k, v in fals["rel_weights"].items()}   # cross-writer slot weights.
    bg_ms = [s for s in background if _is_multistroke(s) and s["class"] in set(way_classes)]

    bg_writers = sorted({s["writer_id"] for s in bg_ms})
    calib_w, sanity_w = cwd.split_writers(bg_writers, frac_calib=0.5, seed=CW_SPLIT_SEED)
    print(f"  background writers={len(bg_writers)}  -> calibrate A={len(calib_w)}  sanity B="
          f"{len(sanity_w)}  (disjoint={set(calib_w).isdisjoint(sanity_w)})")

    calib_ms = [s for s in bg_ms if s["writer_id"] in set(calib_w)]
    sanity_ms = [s for s in bg_ms if s["writer_id"] in set(sanity_w)]
    idx_cal = _index_by_writer_class(calib_ms, way_classes)
    idx_san = _index_by_writer_class(sanity_ms, way_classes)
    eps_cal = _draw_episodes(idx_cal, way_classes, N_BACKGROUND_EPISODES, CALIB_EPISODE_SEED)
    eps_san = _draw_episodes(idx_san, way_classes, N_BACKGROUND_EPISODES, SANITY_EPISODE_SEED)

    native = srs.Substrate()._inner
    cache, geo_cache = {}, {}
    timing = dict(n_derivations=0, rel_seconds=0.0)
    # calibrate cross-writer PART precisions on writers A.
    recs_cal = _records(native, eps_cal, weights, cache, geo_cache, timing=timing)
    prec = _crosswriter_part_precisions(recs_cal)
    # sanity on writers B (held-out from calibration).
    recs_san = _records(native, eps_san, weights, cache, geo_cache)
    n_san = len(recs_san)
    guard, arm = _preds(native, recs_san, prec)
    trues = [r["true_idx"] for r in recs_san]
    k_guard = sum(g == t for g, t in zip(guard, trues))
    k_arm = sum(p == t for p, t in zip(arm, trues))
    acc_guard, acc_arm = k_guard / max(n_san, 1), k_arm / max(n_san, 1)
    passed = acc_arm >= acc_guard - SANITY_MARGIN
    ms_per = 1000.0 * timing["rel_seconds"] / max(timing["n_derivations"], 1)

    out = dict(n_calib=len(recs_cal), n_sanity=n_san, n_way=len(way_classes), precisions=prec,
               acc_guard=acc_guard, acc_arm=acc_arm, k_guard=k_guard, k_arm=k_arm,
               sanity_margin=SANITY_MARGIN, passed=bool(passed), calib_writers=calib_w,
               sanity_writers=sanity_w, rel_weights=weights, way_classes=way_classes,
               amortization=dict(n_derivations=timing["n_derivations"], ms_per_derivation=ms_per))
    _save_json(out, CALIB_PATH)
    print(f"\n  ---- CROSS-WRITER-HELD-OUT SANITY (calibrate A, sanity B, {len(way_classes)}-way) ----")
    print(f"    cross-writer part precisions (from graph edges): "
          f"{{{', '.join(f'{k}={v:.5f}' for k,v in prec.items())}}}")
    print(f"    GUARD (geometry-only) on B: acc={100*acc_guard:.1f}% k={k_guard}/{n_san}")
    print(f"    ARM X (cross-writer discriminability rel) on B: acc={100*acc_arm:.1f}% k={k_arm}/{n_san} "
          f"delta={100*(acc_arm-acc_guard):+.1f}pp")
    print(f"    [AMORTIZATION] {timing['n_derivations']} derivations, {ms_per:.3f} ms/derivation")
    if passed:
        print(f"    VERDICT: PASS (ARM X does not harm held-out background writers) -- proceed to eval.")
    else:
        print(f"    VERDICT: STOP -- ARM X HARMS held-out background writers B ({100*(acc_arm-acc_guard):+.1f}pp"
              f" < -{100*SANITY_MARGIN:.0f}pp). THE CROSS-WRITER SANITY GATE CAUGHT the non-transferable "
              f"signal that run 58's in-distribution sanity MISSED (+0.5pp). No eval budget spent.")
    _seed_guard("calibrate", md5_before)
    return 0


def _require_calibrate():
    if not os.path.exists(CALIB_PATH):
        raise SystemExit("WALL: run --stage calibrate first.")
    return _load_json(CALIB_PATH)


# ============================================================================================= #
#  STAGE: eval -- STAGE 2: SAME held-out cross-writer episodes as run 58, frozen precisions.
# ============================================================================================= #
def stage_eval():
    print(f"\n{SEP}\n  STAGE: eval (STAGE 2 -- SAME held-out cross-writer episodes as run 58)\n{SEP}")
    calib = _require_calibrate()
    if not calib["passed"]:
        print("  WALL: calibrate cross-writer-sanity STOPPED -- NO eval budget.")
        return 1
    md5_before = _md5(STROKE_SHAPES_SEED)
    prec = calib["precisions"]
    weights = {k: float(v) for k, v in calib["rel_weights"].items()}
    way_classes = calib["way_classes"]

    samples = pw.load_digilets_samples()
    _, heldout = pw.digilets_writer_split(samples, n_background=N_BACKGROUND_WRITERS,
                                          seed=WRITER_SPLIT_SEED)
    ho_ms = [s for s in heldout if _is_multistroke(s) and s["class"] in set(way_classes)]
    idx = _index_by_writer_class(ho_ms, way_classes)
    eps = _draw_episodes(idx, way_classes, N_EVAL_EPISODES, EVAL_EPISODE_SEED)   # run-58 seed.

    native = srs.Substrate()._inner
    cache, geo_cache = {}, {}
    records = _records(native, eps, weights, cache, geo_cache)
    n = len(records)
    guard, arm = _preds(native, records, prec)
    trues = [r["true_idx"] for r in records]
    guard_correct = [g == t for g, t in zip(guard, trues)]
    arm_correct = [p == t for p, t in zip(arm, trues)]
    out = dict(n=n, n_way=len(way_classes), guard_correct=[bool(x) for x in guard_correct],
               arm_correct=[bool(x) for x in arm_correct], k_guard=sum(guard_correct),
               k_arm=sum(arm_correct), precisions=prec, done=True)
    _save_json(out, EVAL_PATH)
    print(f"\n  EVAL COMPLETE: n={n} {len(way_classes)}-way  GUARD={100*out['k_guard']/n:.1f}%  "
          f"ARM X={100*out['k_arm']/n:.1f}%")
    # comparability check vs run 58 GUARD (geometry-only, identical episodes).
    if os.path.exists(RUN58_EVAL):
        r58e = _load_json(RUN58_EVAL)
        print(f"    [comparability] run58 GUARD k={r58e['k_guard']}/{r58e['n']} ; "
              f"run58b GUARD k={out['k_guard']}/{n} (geometry-only should reproduce)")
    _seed_guard("eval", md5_before)
    return 0


# ============================================================================================= #
#  STAGE: report
# ============================================================================================= #
def stage_report():
    print(f"\n{SEP}\n  RUN 58b -- CROSS-WRITER-ROBUST DISCRIMINABILITY -- FINAL REPORT\n{SEP}")
    print(f"  seeds/stroke_shapes.json md5: {_md5(STROKE_SHAPES_SEED)}")
    fals = _require_falsifier()
    print(f"\n  {'='*26}  STAGE 1 -- CROSS-WRITER FISHER vs run-58 POOLED  {'='*26}")
    print(f"    {'slot':<10} {'pooled(run58)':>14} {'cross-writer':>14} {'drop':>8}")
    for s, pv in fals["pooled_fisher"].items():
        cv = fals["crosswriter_fisher"].get(s, 0.0)
        print(f"    {s:<10} {pv:>14.4f} {cv:>14.4f} {pv-cv:>8.4f}")
    print(f"    ARRANGEMENT cross-writer max={fals['crosswriter_arrangement_max']:.4f} @ "
          f"{fals['top_crosswriter_slot']!r}  (mouse {fals['mouse_arrangement_max']:.4f}; "
          f"cpose-redundant cross-writer max {fals['cpose_crosswriter_max']:.4f})")
    print(f"    BAR A survives={fals['bar_a_survives']}  BAR B above-cpose={fals['bar_b_above_cpose']}  "
          f"BAR C orthogonal={fals['bar_c_orthogonal']} (corr {fals['orthogonality_corr']:.4f})")
    print(f"    LICENSED (transferable arrangement): {fals['licensed']}")

    if os.path.exists(CALIB_PATH):
        cal = _load_json(CALIB_PATH)
        print(f"\n  {'='*26}  STAGE 2 -- CROSS-WRITER-HELD-OUT SANITY  {'='*26}")
        print(f"    calibrate writers A={len(cal['calib_writers'])}  sanity writers B="
              f"{len(cal['sanity_writers'])}  (disjoint background subsets)")
        print(f"    cross-writer part precisions: "
              f"{{{', '.join(f'{k}={v:.5f}' for k,v in cal['precisions'].items())}}}")
        print(f"    GUARD on B={100*cal['acc_guard']:.1f}%  ARM X on B={100*cal['acc_arm']:.1f}%  "
              f"delta={100*(cal['acc_arm']-cal['acc_guard']):+.1f}pp  -> "
              f"{'PASS' if cal['passed'] else 'STOP (gate caught non-transferable signal)'}")

    print(f"\n  {'='*30}  VERDICT  {'='*30}")
    if os.path.exists(CALIB_PATH) and not _load_json(CALIB_PATH)["passed"]:
        print(f"    STOP AT CROSS-WRITER SANITY -- the gate now CATCHES what run 58 missed. Run 58's "
              f"in-distribution background-sanity PASSED +0.5pp while eval harmed -8.2pp; run 58b's "
              f"CROSS-WRITER-held-out sanity STOPS before any eval spend. FACULTY-CORRECTNESS FIX "
              f"CONFIRMED: background-sanity that holds out WRITERS refuses a non-transferable signal.")
    elif os.path.exists(EVAL_PATH) and _load_json(EVAL_PATH).get("done"):
        ev = _load_json(EVAL_PATH)
        n = ev["n"]
        ci_g = gate.wilson_ci(ev["k_guard"], n)
        ci_a = gate.wilson_ci(ev["k_arm"], n)
        mc = _mcnemar(ev["guard_correct"], ev["arm_correct"])
        delta = 100 * (ev["k_arm"] - ev["k_guard"]) / n
        print(f"    ---- EVAL (n={n}, {ev['n_way']}-way cross-writer held-out, run-58 episodes) ----")
        print(f"      GUARD (geometry-only): {100*ev['k_guard']/n:.1f}% [{100*ci_g[0]:.1f},{100*ci_g[1]:.1f}]")
        print(f"      ARM X (cross-writer):  {100*ev['k_arm']/n:.1f}% [{100*ci_a[0]:.1f},{100*ci_a[1]:.1f}]")
        print(f"      delta ARM X - GUARD = {delta:+.1f}pp  (run 58 ARM DP was -8.2pp)")
        print(f"      McNemar: fixed={mc['fixed']} broken={mc['broken']} p={mc['p']:.4g}")
        if os.path.exists(RUN58_EVAL):
            r58e = _load_json(RUN58_EVAL)
            print(f"      [comparability] run58 GUARD {100*r58e['k_guard']/r58e['n']:.1f}% ; "
                  f"run58b GUARD {100*ev['k_guard']/n:.1f}% (geometry-only reproduction)")
        if mc["fixed"] > mc["broken"] and mc["p"] < 0.05:
            print(f"      OUTCOME (ii) CONVERTS: cross-writer arrangement is genuinely class-defining "
                  f"-- ENTRY-38 CONSTRUCTIVE confirmation, first ceiling movement.")
        elif abs(delta) <= 100 * SANITY_MARGIN and mc["broken"] <= mc["fixed"] + 3:
            print(f"      OUTCOME (i) CLEAN NULL, ZERO HARM: cross-writer precision distrusted the "
                  f"non-transferable arrangement -> ARM X reduced to geometry -> eval ~= GUARD (vs "
                  f"run 58's -8.2pp). The faculty-correctness fix WORKS; geometry is the only "
                  f"transferable fine-separator on mouse AND pen -- concept-participation TERMINUS.")
        elif mc["broken"] > mc["fixed"]:
            print(f"      RESIDUAL HARM ({delta:+.1f}pp): cross-writer precision reduced but did not "
                  f"eliminate the harm (see honest anomalies).")
        else:
            print(f"      NULL (no material change).")
    else:
        print("    (eval not yet run)")
    print(f"\n  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  seeds/stroke_shapes.json md5 (post-run): {_md5(STROKE_SHAPES_SEED)}")
    return 0


STAGES = {"unit_sanity": stage_unit_sanity, "falsifier": stage_falsifier,
          "calibrate": stage_calibrate, "eval": stage_eval, "report": stage_report}


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
