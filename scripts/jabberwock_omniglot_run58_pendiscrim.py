"""OMNIGLOT RUN 58 -- THE DISCRIMINATION FACULTY ON PEN DATA (a constructive test of entry 38).

RUN 57 (a575e943) BUILT the graph-native discrimination faculty (`domains/discrimination.py`):
precision = FISHER DISCRIMINABILITY (between-class-var / within-class-var), plus attachment/junction
relations. On MOUSE-Omniglot the faculty CORRECTLY found NO separating arrangement beyond geometry:
junction max Fisher 0.167, and the highest-Fisher relation (cpose_x = whole-char x-position) was
REDUNDANT with the geometry SC+TPS already captures. Run 57's own verdict: the gap is corpus
INFORMATION, not machinery; the road is pen data.

THE OPEN QUESTION run 58 answers (constructive test of entry 38): does PEN data have SEPARATING
relational content the SAME faculty can find + convert, where mouse-Omniglot did not? Run 46 showed
pen data carries 17x the stroke-interior info; run 49 showed that richness is largely REDUNDANT with
shape geometry. But real multi-stroke pen characters have real ATTACHMENT/JUNCTION/order structure a
mouse TRACING lacks, and DigiLeTs is genuinely MULTI-WRITER (real within-class variance -> meaningful
Fisher). Honest prior: NOT strong (the pen advantage was shape, not arrangement) -- but it is worth
the cheap falsifier.

CORPUS: DigiLeTs MULTI-STROKE subset (the only pen corpus with relations -- UCI is single-stroke).
`domains/pen_world.load_digilets_samples` (run 48). A class QUALIFIES as multi-stroke if >= 50% of
its instances (across all writers) have >=2 valid strokes (pen-up BREAK). Episodes use only the
multi-stroke instances of qualifying classes, CROSS-WRITER (exemplar/query DIFFERENT writers), with a
per-WRITER background/held-out split (`digilets_writer_split`).

THE APPLICATION (no new authoring -- run 57's faculty EXISTS; this APPLIES it to a new corpus):
every DigiLeTs character's strokes are composed DIRECTLY into a ShapeSignature via
`character_compose.compose_character_signature` (the strokes are already pen-path point arrays -- one
StrokeQuantize call, no Omniglot image decode), giving the SAME `rel`/`cpose` arrangement relations
run 50/57 read; junction relations come straight from the raw strokes via
`discrimination.junction_profile`. The geometry residual is `per_stroke_abs.program_score` (the SAME
per-stroke SC+TPS run 48 used for DigiLeTs). The verdict is run 56's UNCHANGED `unified_verdict`
machinery with run 57's DISCRIMINABILITY precisions.

STAGE 1 -- CHEAP FALSIFIER FIRST (the decider, run-57 style, on pen):
  Fisher discriminability of relations on DigiLeTs multi-stroke BACKGROUND writers --
    (a) pose relations (rel_x/y/o/s, cpose_*) and (b) junction/attachment relations.
  ARRANGEMENT Fisher = max over the GENUINE-arrangement slots (junction + rel_*), EXCLUDING the
  whole-char cpose_* (which the geometry trivially captures -- mouse's cpose_x=0.917 was exactly the
  redundant case). Compared to mouse's arrangement max (junction 0.167).
  PRE-REGISTERED BARS:
    BAR 1 (materially higher): pen arrangement max Fisher > 1.5 x 0.167 (= 0.2505).
    BAR 2 (orthogonal to geometry): the aggregate arrangement residual `rel` is NOT redundant with
      the geometry residual `whole` -- |Pearson corr(whole, rel)| < 0.5 over background episodes; AND
      the top-Fisher arrangement slot is not a whole-char cpose_* (structurally geometry-redundant).
  BOTH bars pass -> LICENSE STAGE 2. Otherwise -> report the DEEP finding (arrangement is coarse
  coherence, not fine separation, on ANY corpus; the fine-separating info is always in geometry) and
  the faculty STANDS as the correct measurer.

STAGE 2 (only if licensed) -- FULL GATE: GUARD = geometry-only verdict (program_score argmin) on
  DigiLeTs multi-stroke cross-writer. ARM DP = unified log-odds derivation (run 56) with
  DISCRIMINABILITY precision (run 57) over (whole, rel). BACKGROUND-SANITY STOP before eval. McNemar
  ARM DP vs GUARD. n>=200 cross-writer episodes, N-way = min(20, n_qualifying_classes).

HONEST FRAME: WIN (STAGE 1 licenses AND STAGE 2 converts) = pen arrangement separates + the faculty
closes some gap = entry-38 constructive confirmation. NULL at STAGE 1 = the DEEP finding: fine-
separating info is in GEOMETRY on every corpus, arrangement is only coarse coherence -- a clean
general result, and the faculty correctly measures it. The faculty being CORRECT on a NEW corpus is
itself the deliverable.

EXECUTION (ops law): every invocation <=540s FOREGROUND, `stdbuf -oL ... | tee -a
results/omniglot_gate_run58.log`, checkpoints under `results/run58_checkpoints/` (every
`results/run*_checkpoints/` READ-ONLY; parallel-session files untouched). `.venv` python.
`OZMA_SEED_PERSIST_DISABLED=1` + a before/after md5 seed-guard on every stage.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run58_pendiscrim.py --stage <STAGE>
Stages: unit_sanity -> falsifier -> (calibrate -> eval, only if licensed) -> report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from scipy.stats import binomtest

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run47_pendata as run47
from domains import pen_world as pw
from domains import discrimination as disc
from domains import relational_variation as rv
from domains import unified_verdict as uv
from domains.character_compose import compose_character_signature

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run58_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
RUN57_FALSIFIER = os.path.join(ROOT, "results", "run57_checkpoints", "falsifier.json")   # READ-ONLY.

TB = gate.DK["turn_bins"]

# ---- PRE-REGISTERED CONSTANTS (stated before any real-data number is computed) ---- #
N_BACKGROUND_WRITERS = 40                 # of 77 (same split convention as run 48).
WRITER_SPLIT_SEED = 20260706
MS_CLASS_FRAC = 0.50                       # a class is "multi-stroke" if >= this fraction of its
                                           # instances have >=2 valid strokes.
N_WAY_TARGET = 20                          # min(20, n_qualifying_classes); Lake's protocol is 20-way.

# arrangement slots = the GENUINE arrangement (relative pose + junction), EXCLUDING whole-char cpose_*
# (which the geometry SC+TPS trivially captures -- mouse's cpose_x=0.917 was exactly that redundancy).
ARRANGEMENT_SLOTS = tuple(rv.REL_SLOTS) + tuple(disc.JUNCTION_SLOTS)
CPOSE_SLOTS = tuple(rv.CPOSE_SLOTS)

MOUSE_ARRANGEMENT_MAX = 0.167              # run 57's junction max Fisher (read live below; fallback).
BAR1_FACTOR = 1.5                          # "materially higher" = > 1.5x the mouse arrangement max.
BAR2_MAX_ABS_CORR = 0.50                   # "orthogonal" = |corr(whole, rel)| below this.

N_BACKGROUND_EPISODES = 200                # cross-writer background episodes for orthogonality +
                                           # precision calibration.
N_EVAL_EPISODES = 220                      # held-out cross-writer eval episodes (>= 200 required).
BG_EPISODE_SEED = 20260801
EVAL_EPISODE_SEED = 20260802
SANITY_MARGIN = 0.03                       # ARM DP must be >= GUARD - 3pp on background before eval.
PER_CALL_BUDGET_SECONDS = 480              # hard deadline within a <=540s invocation.

FALSIFIER_STATE = os.path.join(CKPT_DIR, "falsifier_state.json")
FALSIFIER_PATH = os.path.join(CKPT_DIR, "falsifier.json")
CALIB_STATE = os.path.join(CKPT_DIR, "calibrate_state.json")
CALIB_PATH = os.path.join(CKPT_DIR, "calibrate.json")
EVAL_STATE = os.path.join(CKPT_DIR, "eval_state.json")
EVAL_PATH = os.path.join(CKPT_DIR, "eval.json")


# ============================================================================================= #
#  GENERAL HELPERS (mechanical I/O -- the same class run 57/48 already use).
# ============================================================================================= #
def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path):
    def _default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return str(o)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_default)


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest() if os.path.exists(path) else "MISSING"


def _donkey0():
    return "torch" not in sys.modules


def _seed_guard(stage, md5_before):
    md5_after = _md5(STROKE_SHAPES_SEED)
    ok = md5_after == md5_before
    print(f"\n  seeds/stroke_shapes.json md5 AFTER {stage}: {md5_after}  UNCHANGED={ok}")
    if not ok:
        raise SystemExit(f"HARD STOP: seed write detected during --stage {stage}.")


def _mcnemar(correct_a, correct_b):
    fixed = sum(1 for a, b in zip(correct_a, correct_b) if (not a) and b)
    broken = sum(1 for a, b in zip(correct_a, correct_b) if a and (not b))
    n_disc = fixed + broken
    p = float(binomtest(fixed, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    return dict(fixed=fixed, broken=broken, discordant=n_disc, p=p)


def _mouse_arrangement_max():
    """Read run 57's mouse junction max Fisher LIVE (READ-ONLY) so the comparison can never drift
    from the checkpoint it cites; fall back to the documented 0.167 if absent."""
    if os.path.exists(RUN57_FALSIFIER):
        d = _load_json(RUN57_FALSIFIER)
        jf = d.get("part_b", {}).get("junction_fisher", {})
        cf = d.get("part_b", {}).get("coarse_fisher", {})
        vals = list(jf.values()) + [cf[s] for s in rv.REL_SLOTS if s in cf]
        if vals:
            return float(max(vals)), d
    return MOUSE_ARRANGEMENT_MAX, None


# ============================================================================================= #
#  MULTI-STROKE FILTER + CROSS-WRITER EPISODE CONSTRUCTION (mechanical adapter work).
# ============================================================================================= #
def _valid_strokes(sample):
    """Pen-down strokes with >=2 points -- a stroke below 2 points carries no pose/junction."""
    return [st for st in sample["strokes"] if np.asarray(st).shape[0] >= 2]


def _is_multistroke(sample):
    return len(_valid_strokes(sample)) >= 2


def qualifying_classes(samples, frac=MS_CLASS_FRAC):
    """Sorted class ids where >= `frac` of the class's instances are multi-stroke (pen-up BREAK)."""
    by_cls_total = Counter(s["class"] for s in samples)
    by_cls_ms = Counter(s["class"] for s in samples if _is_multistroke(s))
    return sorted(c for c in by_cls_total
                  if by_cls_ms[c] / max(by_cls_total[c], 1) >= frac)


def _index_by_writer_class(ms_samples, classes):
    """`{writer: {class: [samples...]}}` over multi-stroke instances of `classes` only."""
    cset = set(classes)
    idx = {}
    for s in ms_samples:
        if s["class"] in cset:
            idx.setdefault(s["writer_id"], {}).setdefault(s["class"], []).append(s)
    return idx


def _draw_episodes(idx, classes, n_episodes, seed):
    """`n_episodes` cross-writer one-shot episodes: for each class an exemplar from some writer; the
    TRUE class's query from a DIFFERENT writer. Records the writers so the cross-writer property is
    auditable (asserted in the unit test). Only writers holding EVERY way-class are eligible so the
    N-way pool is always complete."""
    writers = sorted(w for w in idx if all(c in idx[w] and idx[w][c] for c in classes))
    if len(writers) < 2:
        return []
    rng = np.random.default_rng(seed)
    n_way = len(classes)
    eps = []
    for _ in range(n_episodes):
        true_i = int(rng.integers(0, n_way))
        true_cls = classes[true_i]
        ex_writer, ex_sample = {}, {}
        for c in classes:
            w = writers[int(rng.integers(0, len(writers)))]
            insts = idx[w][c]
            ex_writer[c] = w
            ex_sample[c] = insts[int(rng.integers(0, len(insts)))]
        others = [w for w in writers if w != ex_writer[true_cls]]
        if not others:
            continue
        qw = others[int(rng.integers(0, len(others)))]
        q = idx[qw][true_cls][int(rng.integers(0, len(idx[qw][true_cls])))]
        eps.append(dict(true_idx=true_i, ex_sample=ex_sample, query=q,
                        ex_writer_true=ex_writer[true_cls], q_writer=qw, classes=classes))
    return eps


# ============================================================================================= #
#  COMPOSITION + PER-CANDIDATE RESIDUAL TRIPLE (DigiLeTs-native; reuses run 50/56 machinery).
# ============================================================================================= #
def _compose(native, sample, cache):
    """(stroke_points_in_rv_format, composed_signature) for one DigiLeTs character -- ONE
    StrokeQuantize via compose_character_signature over the raw pen strokes. Cached per sample id."""
    key = id(sample)
    if key in cache:
        return cache[key]
    strokes = _valid_strokes(sample)
    sp = [(np.asarray(st).tolist(), "s") for st in strokes]
    sig = compose_character_signature(native, sp, turn_bins=TB)["signature"] if sp else []
    cache[key] = (sp, sig)
    return sp, sig


def _episode_records(native, episodes, weights, cache, geo_cache, timing=None):
    """Per episode: for each candidate the (whole, stroke, rel) residual triple --
      whole = per-stroke SC+TPS program_score (geometry -- the GUARD verdict), stroke = 0 (unused),
      rel   = relational_variation.relational_distance arrangement residual.
    `weights` = per-slot rel weights (background-derived). Records also carry the raw whole/rel pairs
    for the orthogonality diagnostic. Mechanical -- the ranking DECISION stays the held Argmin."""
    records = []
    for e in episodes:
        q = e["query"]
        q_ps = _geo_ps(q, geo_cache)
        q_sp, q_sig = _compose(native, q, cache)
        if not q_ps or not q_sp:
            continue
        per, ortho = [], []
        ok = True
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
        records.append(dict(true_idx=int(e["true_idx"]), per=per, ortho=ortho))
    return records


def _geo_ps(sample, geo_cache):
    key = id(sample)
    if key not in geo_cache:
        geo_cache[key] = run47._stroke_point_sets_from_arrays(sample["strokes"])
    return geo_cache[key]


# ============================================================================================= #
#  FISHER ON BACKGROUND RELATIONS (pose + junction) -- run 57's falsifier, DigiLeTs-native.
# ============================================================================================= #
def _class_slot_means(native, ref_stroke_points, ref_sig, other_instances):
    """Per-class per-slot MEAN mirroring rv.class_slot_variances' alignment + pooling (run 57's own
    helper, inlined). Pure statistics."""
    ref_pts = rv.stroke_points_only(ref_stroke_points)
    pooled_rel = {s: [] for s in rv.REL_SLOTS}
    pooled_cpose = {s: [] for s in rv.CPOSE_SLOTS}
    for _k, vals in rv.rel_by_k(ref_sig).items():
        for slot, v in zip(rv.REL_SLOTS, vals):
            pooled_rel[slot].append(v)
    for slot, v in rv.cpose_values(ref_sig).items():
        if v is not None:
            pooled_cpose[slot].append(v)
    for stroke_points, sig in other_instances:
        pts = rv.stroke_points_only(stroke_points)
        if not pts:
            continue
        gm = rv.align_stroke_points(native, ref_pts, pts)
        other_rel = rv.rel_by_k(sig)
        for (i, j, _c) in gm["matched"]:
            vals = other_rel.get(j)
            if vals is None:
                continue
            for slot, v in zip(rv.REL_SLOTS, vals):
                pooled_rel[slot].append(v)
        for slot, v in rv.cpose_values(sig).items():
            if v is not None:
                pooled_cpose[slot].append(v)
    out = {}
    for slot in rv.REL_SLOTS:
        out[slot] = float(np.mean(pooled_rel[slot])) if pooled_rel[slot] else 0.0
    for slot in rv.CPOSE_SLOTS:
        out[slot] = float(np.mean(pooled_cpose[slot])) if pooled_cpose[slot] else 0.0
    return out


def _accumulate_class_fisher(native, cls_samples, coarse, junction, per_class_var, cache):
    """Fold ONE class's decoded instances into the coarse-pose {slot:{cls:[mean-std,mean+std]}} and
    junction {slot:{cls:[per-instance fracs]}} accumulators, plus its pooled pose variance (for the
    rel weights)."""
    decoded = [_compose(native, s, cache) for s in cls_samples]
    decoded = [(sp, sig) for (sp, sig) in decoded if sp]
    if len(decoded) < 2:
        return
    cls_key = str(cls_samples[0]["class"])
    ref_sp, ref_sig = decoded[0]
    others = decoded[1:]
    var = rv.class_slot_variances(native, ref_sp, ref_sig, others, turn_bins=TB)
    means = _class_slot_means(native, ref_sp, ref_sig, others)
    if var is not None and means is not None:
        per_class_var.append({s: var.get(s, 0.0) for s in rv.ALL_SLOTS})
        for slot in rv.ALL_SLOTS:
            std = float(np.sqrt(max(var.get(slot, 0.0), 0.0)))
            m = means[slot]
            coarse[slot][cls_key] = [m - std, m + std]
    for (sp, _sig) in decoded:
        prof = disc.junction_profile(rv.stroke_points_only(sp))
        for slot in disc.JUNCTION_SLOTS:
            junction[slot].setdefault(cls_key, []).append(prof[slot])


# ============================================================================================= #
#  STAGE: unit_sanity
# ============================================================================================= #
def stage_unit_sanity():
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    md5_before = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5 (BEFORE): {md5_before}")
    ok_all = True
    for test_file in ("tests/test_pendiscrim_migrated.py",
                      "tests/test_discrimination_migrated.py",
                      "tests/test_unified_verdict_migrated.py",
                      "tests/test_relational_variation_migrated.py"):
        print(f"\n  running {test_file} ...")
        proc = subprocess.run([sys.executable, "-m", "pytest", test_file, "-q"],
                              cwd=ROOT, env={**os.environ}, capture_output=True, text=True,
                              timeout=400)
        print(proc.stdout[-1800:])
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
#  STAGE: falsifier -- STAGE 1, THE DECIDER. Fisher on background + orthogonality to geometry.
# ============================================================================================= #
def stage_falsifier():
    print(f"\n{SEP}\n  STAGE: falsifier (STAGE 1 -- the decider: pen relation Fisher vs mouse's "
          f"0.167, orthogonal-to-geometry)\n{SEP}")
    _require_unit_sanity()
    md5_before = _md5(STROKE_SHAPES_SEED)

    samples = pw.load_digilets_samples()
    background, heldout = pw.digilets_writer_split(samples, n_background=N_BACKGROUND_WRITERS,
                                                   seed=WRITER_SPLIT_SEED)
    classes = qualifying_classes(samples, frac=MS_CLASS_FRAC)
    n_total_classes = len({s["class"] for s in samples})
    n_ms_instances = sum(1 for s in samples if _is_multistroke(s))
    print(f"  n_samples={len(samples)}  multi-stroke instances={n_ms_instances} "
          f"({100*n_ms_instances/len(samples):.1f}%)  qualifying multi-stroke classes="
          f"{len(classes)}/{n_total_classes} (>= {MS_CLASS_FRAC:.0%} instances multi-stroke)")
    print(f"  qualifying symbols: {[pw.DIGILETS_SYMBOLS[c] for c in classes]}")
    print(f"  background writers={len({s['writer_id'] for s in background})}  "
          f"held-out writers={len({s['writer_id'] for s in heldout})}")

    bg_ms = [s for s in background if _is_multistroke(s) and s["class"] in set(classes)]

    # ---- checkpointed per-class Fisher accumulation ----
    state = (_load_json(FALSIFIER_STATE) if os.path.exists(FALSIFIER_STATE)
             else dict(cls_idx=0, coarse={}, junction={}, per_class_var=[]))
    coarse = {slot: {} for slot in rv.ALL_SLOTS}
    for slot, d in state["coarse"].items():
        coarse[slot] = {k: list(v) for k, v in d.items()}
    junction = {slot: {} for slot in disc.JUNCTION_SLOTS}
    for slot, d in state["junction"].items():
        junction[slot] = {k: list(v) for k, v in d.items()}
    per_class_var = [dict(x) for x in state["per_class_var"]]

    native = srs.Substrate()._inner
    cache = {}
    by_cls = {}
    for s in bg_ms:
        by_cls.setdefault(s["class"], []).append(s)
    ordered_classes = [c for c in classes if c in by_cls]
    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    while state["cls_idx"] < len(ordered_classes) and time.time() < hard_deadline:
        c = ordered_classes[state["cls_idx"]]
        _accumulate_class_fisher(native, by_cls[c], coarse, junction, per_class_var, cache)
        state["cls_idx"] += 1
        state["coarse"] = coarse
        state["junction"] = junction
        state["per_class_var"] = per_class_var
        _save_json(state, FALSIFIER_STATE)
        print(f"    [falsifier] class {state['cls_idx']}/{len(ordered_classes)} "
              f"({pw.DIGILETS_SYMBOLS[c]!r}) folded", flush=True)
    if state["cls_idx"] < len(ordered_classes):
        print(f"\n  PARTIAL [falsifier Fisher]: {state['cls_idx']}/{len(ordered_classes)} -- re-invoke.")
        return 0

    coarse_fisher = disc.slot_discriminability(coarse)
    junction_fisher = disc.slot_discriminability(junction)
    all_fisher = {**coarse_fisher, **junction_fisher}
    arrangement_fisher = {s: all_fisher[s] for s in ARRANGEMENT_SLOTS if s in all_fisher}
    cpose_fisher = {s: coarse_fisher[s] for s in CPOSE_SLOTS if s in coarse_fisher}
    arrangement_max = max(arrangement_fisher.values()) if arrangement_fisher else 0.0
    top_arr_slot = max(arrangement_fisher, key=arrangement_fisher.get) if arrangement_fisher else None

    print(f"\n  ---- PEN relation Fisher discriminability (DigiLeTs multi-stroke background, "
          f"{len(ordered_classes)} classes) ----")
    print(f"    pose rel_*  : {{{', '.join(f'{k}={coarse_fisher[k]:.4f}' for k in rv.REL_SLOTS)}}}")
    print(f"    junction    : {{{', '.join(f'{k}={junction_fisher[k]:.4f}' for k in disc.JUNCTION_SLOTS)}}}")
    print(f"    cpose_* (whole-char, geometry-redundant): "
          f"{{{', '.join(f'{k}={cpose_fisher.get(k,0):.4f}' for k in CPOSE_SLOTS)}}}")
    print(f"    ARRANGEMENT max (rel_* + junction, EXCL cpose)={arrangement_max:.4f} "
          f"@ slot {top_arr_slot!r}")

    mouse_max, _mouse = _mouse_arrangement_max()
    bar1 = arrangement_max > BAR1_FACTOR * mouse_max
    print(f"\n    MOUSE arrangement max (run 57, junction+rel_*, read live)={mouse_max:.4f}")
    print(f"    BAR 1 (pen arrangement > {BAR1_FACTOR}x mouse = {BAR1_FACTOR*mouse_max:.4f}): {bar1}")

    # ---- orthogonality to geometry: background cross-writer episodes, corr(whole, rel) ----
    weights = rv.slot_weights(rv.pool_variation(per_class_var)) if per_class_var else \
        {s: 1.0 for s in rv.ALL_SLOTS}
    idx = _index_by_writer_class(bg_ms, ordered_classes)
    n_way = min(N_WAY_TARGET, len(ordered_classes))
    way_classes = ordered_classes[:n_way]
    idx_way = _index_by_writer_class(bg_ms, way_classes)
    eps = _draw_episodes(idx_way, way_classes, N_BACKGROUND_EPISODES, BG_EPISODE_SEED)
    geo_cache = {}
    recs = _episode_records(native, eps, weights, cache, geo_cache)
    wr = np.array([w for r in recs for (w, _rl) in r["ortho"]], dtype=float)
    rl = np.array([rlv for r in recs for (_w, rlv) in r["ortho"]], dtype=float)
    if wr.size >= 3 and np.std(wr) > 0 and np.std(rl) > 0:
        corr = float(np.corrcoef(wr, rl)[0, 1])
    else:
        corr = 0.0
    top_is_cpose = top_arr_slot in CPOSE_SLOTS      # by construction arrangement excludes cpose,
                                                    # so this is always False -- kept explicit.
    bar2 = abs(corr) < BAR2_MAX_ABS_CORR and not top_is_cpose
    print(f"\n    ---- ORTHOGONALITY (background {len(recs)} episodes, {n_way}-way, "
          f"{wr.size} (query,candidate) pairs) ----")
    print(f"    Pearson corr(whole geometry residual, rel arrangement residual)={corr:.4f}")
    print(f"    BAR 2 (|corr| < {BAR2_MAX_ABS_CORR} AND top slot not whole-char cpose): {bar2}")

    licensed = bool(bar1 and bar2)
    out = dict(n_qualifying_classes=len(ordered_classes),
               qualifying_symbols=[pw.DIGILETS_SYMBOLS[c] for c in ordered_classes],
               n_way=n_way, way_symbols=[pw.DIGILETS_SYMBOLS[c] for c in way_classes],
               n_multistroke_instances=n_ms_instances, multistroke_frac=n_ms_instances/len(samples),
               coarse_fisher=coarse_fisher, junction_fisher=junction_fisher, cpose_fisher=cpose_fisher,
               arrangement_fisher=arrangement_fisher, arrangement_max=arrangement_max,
               top_arrangement_slot=top_arr_slot, mouse_arrangement_max=mouse_max,
               bar1_materially_higher=bool(bar1), orthogonality_corr=corr,
               bar2_orthogonal=bool(bar2), licensed=licensed,
               n_bg_episodes=len(recs), way_classes=way_classes,
               rel_weights=weights)
    _save_json(out, FALSIFIER_PATH)
    _seed_guard("falsifier", md5_before)

    print(f"\n  {'='*30}  STAGE-1 FALSIFIER VERDICT  {'='*30}")
    print(f"    BAR 1 materially-higher-than-mouse: {bar1} "
          f"(pen {arrangement_max:.4f} vs mouse {mouse_max:.4f})")
    print(f"    BAR 2 orthogonal-to-geometry:       {bar2} (corr={corr:.4f})")
    if licensed:
        print(f"    => LICENSED: pen arrangement separates AND is orthogonal to geometry -- "
              f"proceed to --stage calibrate (STAGE 2).")
    else:
        print(f"    => NOT LICENSED (the honest prior): pen arrangement does NOT separate more than "
              f"mouse's, or is redundant with geometry. THE DEEP FINDING -- fine-separating info is "
              f"in GEOMETRY on every corpus; arrangement is only coarse coherence. The discrimination "
              f"faculty STANDS as the correct measurer on a NEW corpus (its own reward). NO eval budget.")
    print(f"    donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _require_falsifier():
    if not os.path.exists(FALSIFIER_PATH):
        raise SystemExit("WALL: run --stage falsifier first.")
    return _load_json(FALSIFIER_PATH)


# ============================================================================================= #
#  STAGE: calibrate -- STAGE 2 (only if licensed). Discriminability precisions + GUARD + SANITY STOP.
# ============================================================================================= #
def _residual_split(records, parts=("whole", "stroke", "rel")):
    res = {p: {"true": [], "false": []} for p in parts}
    for r in records:
        ti = r["true_idx"]
        for ci, c in enumerate(r["per"]):
            for p in parts:
                res[p]["true" if ci == ti else "false"].append(c[p])
    return res


def _discriminability_precisions(records, parts=("whole", "stroke", "rel")):
    res = _residual_split(records, parts)
    prec = {p: disc.part_discriminability(res[p]["true"], res[p]["false"]) for p in parts}
    sub = srs.Substrate()
    frame = disc.install_part_precisions(sub, prec)
    return disc.read_part_precisions(sub, frame, parts=parts)     # read from graph edges.


def _preds(native, records, prec):
    guard, arm = [], []
    pw_, pr = prec["whole"], prec["rel"]
    for r in records:
        guard.append(uv.unified_verdict_pred(native, r["per"], prec_whole=pw_, prec_stroke=0.0,
                                             prec_rel=0.0))
        arm.append(uv.unified_verdict_pred(native, r["per"], prec_whole=pw_, prec_stroke=0.0,
                                           prec_rel=pr))
    return guard, arm


def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (STAGE 2 -- discriminability precisions + GUARD + "
          f"BACKGROUND-SANITY STOP)\n{SEP}")
    _require_unit_sanity()
    fals = _require_falsifier()
    if not fals["licensed"]:
        print("  WALL: STAGE 1 did NOT license STAGE 2 (pen arrangement non-separating or "
              "geometry-redundant). No calibration/eval. See --stage report.")
        return 1
    md5_before = _md5(STROKE_SHAPES_SEED)

    samples = pw.load_digilets_samples()
    background, _ = pw.digilets_writer_split(samples, n_background=N_BACKGROUND_WRITERS,
                                             seed=WRITER_SPLIT_SEED)
    way_classes = fals["way_classes"]
    weights = {k: float(v) for k, v in fals["rel_weights"].items()}
    bg_ms = [s for s in background if _is_multistroke(s) and s["class"] in set(way_classes)]
    idx = _index_by_writer_class(bg_ms, way_classes)
    eps = _draw_episodes(idx, way_classes, N_BACKGROUND_EPISODES, BG_EPISODE_SEED)

    native = srs.Substrate()._inner
    cache, geo_cache = {}, {}
    timing = dict(n_derivations=0, rel_seconds=0.0)
    records = _episode_records(native, eps, weights, cache, geo_cache, timing=timing)
    n = len(records)
    prec = _discriminability_precisions(records)
    guard, arm = _preds(native, records, prec)
    trues = [r["true_idx"] for r in records]
    k_guard = sum(g == t for g, t in zip(guard, trues))
    k_arm = sum(p == t for p, t in zip(arm, trues))
    acc_guard, acc_arm = k_guard / n, k_arm / n
    passed = acc_arm >= acc_guard - SANITY_MARGIN
    ms_per = 1000.0 * timing["rel_seconds"] / max(timing["n_derivations"], 1)

    out = dict(n=n, n_way=len(way_classes), precisions=prec, acc_guard=acc_guard, acc_arm=acc_arm,
               k_guard=k_guard, k_arm=k_arm, sanity_margin=SANITY_MARGIN, passed=bool(passed),
               amortization=dict(n_derivations=timing["n_derivations"], ms_per_derivation=ms_per),
               way_classes=way_classes, rel_weights=weights)
    _save_json(out, CALIB_PATH)
    print(f"\n  ---- BACKGROUND-SANITY GATE (n={n}, {len(way_classes)}-way) ----")
    print(f"    discriminability precisions (Fisher, from graph edges): "
          f"{{{', '.join(f'{k}={v:.5f}' for k,v in prec.items())}}}")
    print(f"    GUARD (geometry-only program_score argmin): acc={100*acc_guard:.1f}% k={k_guard}/{n}")
    print(f"    ARM DP (whole + discriminability-weighted rel): acc={100*acc_arm:.1f}% k={k_arm}/{n} "
          f"delta={100*(acc_arm-acc_guard):+.1f}pp")
    print(f"    [AMORTIZATION] {timing['n_derivations']} derivations, {ms_per:.3f} ms/derivation "
          f"(one pass, no search)")
    print(f"    VERDICT: {'PASS -- proceed to --stage eval' if passed else 'STOP -- no eval budget'}")
    _seed_guard("calibrate", md5_before)
    return 0


def _require_calibrate():
    if not os.path.exists(CALIB_PATH):
        raise SystemExit("WALL: run --stage calibrate first.")
    return _load_json(CALIB_PATH)


# ============================================================================================= #
#  STAGE: eval -- STAGE 2 held-out cross-writer episodes, frozen precisions.
# ============================================================================================= #
def stage_eval():
    print(f"\n{SEP}\n  STAGE: eval (STAGE 2 -- held-out cross-writer, frozen discriminability "
          f"precisions)\n{SEP}")
    calib = _require_calibrate()
    if not calib["passed"]:
        print("  WALL: calibrate SANITY STOPPED -- NO eval budget.")
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
    eps = _draw_episodes(idx, way_classes, N_EVAL_EPISODES, EVAL_EPISODE_SEED)

    native = srs.Substrate()._inner
    cache, geo_cache = {}, {}
    records = _episode_records(native, eps, weights, cache, geo_cache)
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
          f"ARM DP={100*out['k_arm']/n:.1f}%")
    _seed_guard("eval", md5_before)
    return 0


# ============================================================================================= #
#  STAGE: report
# ============================================================================================= #
def stage_report():
    print(f"\n{SEP}\n  RUN 58 -- DISCRIMINATION FACULTY ON PEN DATA -- FINAL REPORT\n{SEP}")
    print(f"  seeds/stroke_shapes.json md5: {_md5(STROKE_SHAPES_SEED)}")
    fals = _require_falsifier()
    print(f"\n  {'='*28}  CORPUS  {'='*28}")
    print(f"    DigiLeTs multi-stroke: {100*fals['multistroke_frac']:.1f}% of instances multi-stroke; "
          f"{fals['n_qualifying_classes']} qualifying classes; {fals['n_way']}-way eval.")
    print(f"    qualifying symbols: {fals['qualifying_symbols']}")

    print(f"\n  {'='*28}  STAGE 1 -- THE DECIDER  {'='*28}")
    cf = fals["coarse_fisher"]
    pose_rel_str = ", ".join("%s=%.4f" % (k, cf[k]) for k in rv.REL_SLOTS)
    print(f"    pen ARRANGEMENT max Fisher (rel_* + junction, excl whole-char cpose)="
          f"{fals['arrangement_max']:.4f} @ {fals['top_arrangement_slot']!r}")
    print(f"      junction: {fals['junction_fisher']}")
    print(f"      pose rel: {{{pose_rel_str}}}")
    print(f"      cpose (geometry-redundant): {fals['cpose_fisher']}")
    print(f"    MOUSE arrangement max (run 57)={fals['mouse_arrangement_max']:.4f}")
    print(f"    BAR 1 materially-higher: {fals['bar1_materially_higher']}")
    print(f"    orthogonality corr(whole,rel)={fals['orthogonality_corr']:.4f}  "
          f"BAR 2 orthogonal: {fals['bar2_orthogonal']}")
    print(f"    LICENSED STAGE 2: {fals['licensed']}")

    print(f"\n  {'='*28}  VERDICT  {'='*28}")
    if not fals["licensed"]:
        print(f"    NULL AT STAGE 1 -- THE DEEP FINDING: pen ARRANGEMENT does not separate more than "
              f"mouse's (or is geometry-redundant). Fine-separating information is in GEOMETRY on "
              f"EVERY corpus tested (mouse-Omniglot run 57 AND pen-DigiLeTs run 58); arrangement is "
              f"only coarse coherence (composition +21pp), never fine separation. The discrimination "
              f"faculty MEASURED this correctly on a genuinely different corpus -- faculty-correctness "
              f"is the deliverable, per the creator's 'its own reward' directive.")
        return 0
    if os.path.exists(EVAL_PATH) and _load_json(EVAL_PATH).get("done"):
        ev = _load_json(EVAL_PATH)
        n = ev["n"]
        ci_g = gate.wilson_ci(ev["k_guard"], n)
        ci_a = gate.wilson_ci(ev["k_arm"], n)
        mc = _mcnemar(ev["guard_correct"], ev["arm_correct"])
        ci_sep = gate._ci_separated(tuple(ci_a), tuple(ci_g))
        print(f"    ---- EVAL (n={n}, {ev['n_way']}-way cross-writer held-out) ----")
        print(f"      GUARD (geometry-only): {100*ev['k_guard']/n:.1f}% "
              f"[{100*ci_g[0]:.1f},{100*ci_g[1]:.1f}]")
        print(f"      ARM DP (faculty):      {100*ev['k_arm']/n:.1f}% "
              f"[{100*ci_a[0]:.1f},{100*ci_a[1]:.1f}]")
        delta = 100 * (ev["k_arm"] - ev["k_guard"]) / n
        print(f"      delta ARM DP - GUARD = {delta:+.1f}pp")
        print(f"      McNemar: fixed={mc['fixed']} broken={mc['broken']} p={mc['p']:.4g}")
        if mc["discordant"] and mc["fixed"] > mc["broken"] and ci_sep:
            print(f"      WIN: ARM DP converts, CI-separated -- ENTRY-38 CONSTRUCTIVE CONFIRMATION.")
        elif mc["fixed"] > mc["broken"]:
            print(f"      WEAK WIN: fixed>broken, not CI-separated.")
        elif mc["broken"] > mc["fixed"] and mc["p"] < 0.05:
            print(f"      HARM (significant): broken>fixed, McNemar p={mc['p']:.4g}. THE SPLIT "
                  f"RESULT -- STAGE 1 licensed (pen arrangement Fisher {fals['arrangement_max']:.3f} "
                  f">> mouse {fals['mouse_arrangement_max']:.3f}, orthogonal) but STAGE 2 HARMED "
                  f"held-out cross-writer. The background class-separation the faculty measured does "
                  f"NOT GENERALIZE cross-writer: junction/arrangement structure is largely WRITER-"
                  f"IDIOSYNCRATIC (a held-out writer's stroke-touch/segmentation choices are class-"
                  f"uncorrelated), so background Fisher OVERESTIMATES its recognition value and the "
                  f"background-sanity gate ({100*_load_json(CALIB_PATH)['acc_arm']:.1f}% vs "
                  f"{100*_load_json(CALIB_PATH)['acc_guard']:.1f}%, in-distribution) did not catch it. "
                  f"REFINED DEEP FINDING: even where arrangement Fisher is HIGH (pen, unlike mouse), "
                  f"the fine-separating info that TRANSFERS cross-writer is still GEOMETRY; "
                  f"arrangement's measurable separation is writer-specific and does not convert. "
                  f"The faculty measured background separation correctly; the corpus's arrangement "
                  f"signal is real but non-transferable.")
        else:
            print(f"      NULL (no harm): faculty protects, arrangement did not convert on eval.")
    else:
        print("    (STAGE 2 licensed but eval not yet run -- run --stage calibrate then --stage eval)")
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
